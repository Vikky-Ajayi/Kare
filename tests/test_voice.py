"""Voice + consultation + agent endpoints, with the LLM and voice providers
faked so CI never touches a live API."""

from __future__ import annotations

import base64
import json

import pytest

from app.providers.base import LLMResponse, SynthResult, ToolCall, Transcript


class FakeLLM:
    """Reads the system prompt to decide what kind of call this is."""
    name = "fake"
    calls: list = []

    async def complete(self, messages, *, tools=None, **kw):
        system = messages[0]["content"] if messages and messages[0]["role"] == "system" else ""
        user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        FakeLLM.calls.append({"system": system[:40], "user": user, "had_tools": bool(tools)})

        if "triage safety net" in system:                      # red-flag classifier
            emergency = "cannot breathe" in user.lower() or "not moving" in user.lower()
            return _json({"emergency": emergency, "category": "danger", "reason": "x"})
        if "clinical documentation assistant" in system:       # memory extraction
            return _json({"presenting_complaints": ["headache"], "last_summary": "test session"})
        if "EMERGENCY" in system:                              # escalation reply
            return _text("This could be serious — please get to a hospital now. Who is with you?")
        # normal consultation turn (agent loop). Call a tool on the first pass only
        # if we haven't already (no tool role yet in messages).
        if tools and not any(m["role"] == "tool" for m in messages) and "ibuprofen" in user.lower():
            return LLMResponse(
                content="", finish_reason="tool_calls", model="fake",
                usage={"total_tokens": 10},
                tool_calls=[ToolCall(id="c1", name="check_drug_interactions",
                                     arguments={"drugs": ["ibuprofen", "lisinopril"]})],
            )
        return _text("I hear you. How long has this been going on, and any fever?")


def _text(t: str) -> LLMResponse:
    return LLMResponse(content=t, finish_reason="stop", model="fake", usage={"total_tokens": 20})


def _json(d: dict) -> LLMResponse:
    return LLMResponse(content=json.dumps(d), finish_reason="stop", model="fake",
                       usage={"total_tokens": 20})


class FakeVoice:
    name = "fake"

    async def transcribe(self, audio, *, language="en", filename="a.wav", telehealth=True):
        return Transcript(text="I have had a headache since morning", language=language, duration_s=3.0)

    async def synthesize(self, text, *, language="en"):
        return SynthResult(audio=b"RIFF....WAVEfake", content_type="audio/wav", duration_s=2.0)

    async def synthesize_sentences(self, text, *, language="en", max_lookahead=2):
        for _ in text.split("."):
            yield SynthResult(audio=b"RIFF....WAVEfake")

    def is_warm(self, language):
        return True

    async def warm(self, language, **kw):
        return True

    async def transcribe_stream(self, chunks, **kw):
        async for _ in chunks:
            pass
        yield {"type": "partial", "text": "I have had a headache"}
        yield {"type": "final", "text": "I have had a headache since morning"}


@pytest.fixture(autouse=True)
def _fake_providers():
    from app import providers
    FakeLLM.calls = []
    providers.use_test_providers(llm=FakeLLM(), voice=FakeVoice())
    yield
    providers.use_test_providers(None, None)


def test_text_chat_returns_reply_and_audio(auth_client):
    r = auth_client.post("/api/v1/voice/chat", json={
        "text": "I feel tired all week", "language": "en", "include_audio": True,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["assistant_message"]
    assert base64.b64decode(body["audio_base64"])
    assert body["escalated"] is False


def test_conversation_is_continuous(auth_client):
    r1 = auth_client.post("/api/v1/voice/chat", json={"text": "hello", "language": "en", "include_audio": False})
    cid = r1.json()["conversation_id"]
    r2 = auth_client.post("/api/v1/voice/chat", json={
        "text": "still here", "language": "en", "conversation_id": cid, "include_audio": False,
    })
    assert r2.json()["conversation_id"] == cid
    msgs = auth_client.get(f"/api/v1/voice/conversations/{cid}/messages").json()["messages"]
    assert len(msgs) == 4


def test_emergency_is_escalated_and_upfront(auth_client):
    r = auth_client.post("/api/v1/voice/chat", json={
        "text": "I cannot breathe and my chest is tight", "language": "en", "include_audio": False,
    })
    body = r.json()
    assert body["escalated"] is True
    assert "hospital" in body["assistant_message"].lower()
    assert body["triage_level"] == "emergency"


def test_agent_calls_drug_interaction_tool_unprompted(auth_client):
    r = auth_client.post("/api/v1/voice/chat", json={
        "text": "can I take ibuprofen for my knee pain?", "language": "en", "include_audio": False,
    })
    assert "check_drug_interactions" in r.json()["tool_calls"]


def test_audio_chat_transcribes_then_replies(auth_client):
    r = auth_client.post(
        "/api/v1/voice/chat/audio",
        files={"file": ("turn.wav", b"x" * 500, "audio/wav")},
        data={"language": "en"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["transcription"] == "I have had a headache since morning"


def test_unsupported_language_falls_back_to_en(auth_client):
    r = auth_client.post("/api/v1/voice/chat", json={"text": "hi", "language": "zz", "include_audio": False})
    assert r.json()["language"] == "en"


def test_stream_ws_full_turn(auth_client):
    token = auth_client.headers["Authorization"].split()[1]
    with auth_client.websocket_connect("/api/v1/voice/stream") as ws:
        ws.send_json({"type": "auth", "token": token})
        ws.send_json({"type": "start", "language": "en", "conversation_id": None})
        assert ws.receive_json() == {"type": "ready", "live_transcript": True}
        ws.send_bytes(b"\x00\x01" * 4000)
        ws.send_json({"type": "end_turn"})
        seen = set()
        while "turn_complete" not in seen:
            m = ws.receive()
            if m.get("text"):
                seen.add(json.loads(m["text"])["type"])
        assert {"partial", "final", "reply", "turn_complete"} <= seen


def test_stream_ws_rejects_bad_token(auth_client):
    with auth_client.websocket_connect("/api/v1/voice/stream") as ws:
        ws.send_json({"type": "auth", "token": "garbage"})
        assert ws.receive_json()["type"] == "error"


def test_delete_my_account(auth_client):
    assert auth_client.delete("/api/v1/patients/me").status_code == 400
    r = auth_client.delete("/api/v1/patients/me", params={"confirm": "DELETE"})
    assert r.status_code == 200
    assert auth_client.get("/api/v1/auth/me").status_code == 401
