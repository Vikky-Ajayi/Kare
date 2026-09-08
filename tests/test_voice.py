"""Voice + consultation endpoints, with the LLM and voice providers faked so
CI never touches a live API."""

from __future__ import annotations

import base64

import pytest

from app.providers.base import LLMResponse, SynthResult, Transcript


class FakeLLM:
    name = "fake"
    last_messages: list = []

    async def complete(self, messages, **kw):
        FakeLLM.last_messages = messages
        user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        if "chest" in user.lower():
            reply = "This could be serious — please get to a hospital now. When did the pain start?"
        else:
            reply = "I hear you. How long has this been going on, and any fever?"
        return LLMResponse(content=reply, finish_reason="stop",
                           model="fake", usage={"total_tokens": 42})


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
def _fake_providers(monkeypatch):
    from app import providers
    monkeypatch.setattr(providers, "get_llm", lambda: FakeLLM())
    monkeypatch.setattr(providers, "get_voice", lambda: FakeVoice())
    # modules that imported the names directly
    import app.routers.voice as vr
    import app.services.consultation as cs
    import app.services.memory as mem
    monkeypatch.setattr(vr, "get_voice", lambda: FakeVoice())
    monkeypatch.setattr(cs, "get_llm", lambda: FakeLLM())
    monkeypatch.setattr(mem, "get_llm", lambda: FakeLLM())


def test_text_chat_returns_reply_and_audio(auth_client):
    r = auth_client.post("/api/v1/voice/chat", json={
        "text": "I feel tired all week", "language": "en", "include_audio": True,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["assistant_message"]
    assert body["conversation_id"]
    assert base64.b64decode(body["audio_base64"])


def test_conversation_is_continuous(auth_client):
    r1 = auth_client.post("/api/v1/voice/chat", json={"text": "hello", "language": "en", "include_audio": False})
    cid = r1.json()["conversation_id"]
    r2 = auth_client.post("/api/v1/voice/chat", json={
        "text": "still here", "language": "en", "conversation_id": cid, "include_audio": False,
    })
    assert r2.json()["conversation_id"] == cid
    msgs = auth_client.get(f"/api/v1/voice/conversations/{cid}/messages").json()["messages"]
    assert len(msgs) == 4  # 2 user + 2 assistant


def test_emergency_language_is_upfront(auth_client):
    r = auth_client.post("/api/v1/voice/chat", json={
        "text": "my chest is hurting badly", "language": "en", "include_audio": False,
    })
    assert "hospital" in r.json()["assistant_message"].lower()


def test_audio_chat_transcribes_then_replies(auth_client):
    r = auth_client.post(
        "/api/v1/voice/chat/audio",
        files={"file": ("turn.wav", b"x" * 500, "audio/wav")},
        data={"language": "en"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["transcription"] == "I have had a headache since morning"
    assert r.json()["assistant_message"]


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
        seen = {"partial": False, "final": False, "reply": False, "audio": 0, "done": False}
        while not seen["done"]:
            m = ws.receive()
            if m.get("text"):
                import json
                d = json.loads(m["text"])
                if d["type"] in seen:
                    seen[d["type"]] = True
                if d["type"] == "audio":
                    seen["audio"] += 1
                if d["type"] == "turn_complete":
                    seen["done"] = True
            elif m.get("bytes"):
                pass
        assert seen["partial"] and seen["final"] and seen["reply"] and seen["done"]


def test_stream_ws_rejects_bad_token(auth_client):
    with auth_client.websocket_connect("/api/v1/voice/stream") as ws:
        ws.send_json({"type": "auth", "token": "garbage"})
        assert ws.receive_json()["type"] == "error"
