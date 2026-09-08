"""
Voice consultation.

POST  /voice/chat                        text in  -> text + audio (base64)
POST  /voice/chat/audio                  audio in -> transcript + text + audio
POST  /voice/transcribe                  audio -> text
POST  /voice/synthesize                  text  -> audio/wav
WS    /voice/stream                      streaming: mic -> partial transcript -> reply -> audio
GET   /voice/notes                       the running health-notes memory
GET   /voice/conversations               list
GET   /voice/conversations/{id}/messages
DELETE /voice/conversations/{id}         end + final memory update
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
from datetime import datetime

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal, get_db
from app.middleware.auth_middleware import get_current_patient_user
from app.models import Conversation, ConversationMessage, PatientHealthNotes, User
from app.providers import get_voice
from app.providers.sahara_voice import SaharaColdStart
from app.schemas import SynthesizeRequest, TranscribeResponse, VoiceChatRequest, VoiceChatResponse
from app.services import consultation, memory
from app.utils.helpers import get_disclaimer
from app.utils.security import decode_access_token

log = logging.getLogger("kare.voice")
router = APIRouter(prefix="/voice", tags=["Voice"])

MAX_AUDIO_SIZE = 25 * 1024 * 1024
_NOTE_EVERY = 4  # messages


async def _extract_notes(conversation_id: str, patient_id: str, *, force: bool = False) -> None:
    """Refresh the memory file on its own DB session. Never raises."""
    db = SessionLocal()
    try:
        if not force:
            count = (
                db.query(ConversationMessage)
                .filter(ConversationMessage.conversation_id == conversation_id)
                .count()
            )
            if count % _NOTE_EVERY != 0:
                return
        await memory.update_health_notes(db, conversation_id, patient_id)
    except Exception as exc:  # noqa: BLE001
        log.warning("note extraction failed: %s", exc)
    finally:
        db.close()


def _extract_notes_sync(conversation_id: str, patient_id: str, *, force: bool = False) -> None:
    """BackgroundTasks entrypoint (runs in a threadpool thread with no loop)."""
    asyncio.run(_extract_notes(conversation_id, patient_id, force=force))


# ── text → text + audio ────────────────────────────────────────────────
@router.post("/chat", response_model=VoiceChatResponse)
async def voice_chat(
    payload: VoiceChatRequest,
    bg: BackgroundTasks,
    user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    try:
        turn = await consultation.run_turn(
            db, user,
            text=payload.text,
            language=payload.language,
            conversation_id=str(payload.conversation_id) if payload.conversation_id else None,
        )
    except Exception as exc:  # noqa: BLE001
        log.exception("consultation failed")
        raise HTTPException(502, f"AI service error: {exc}") from exc

    audio_b64 = None
    if payload.include_audio:
        try:
            syn = await get_voice().synthesize(turn.reply_text, language=turn.language)
            audio_b64 = base64.b64encode(syn.audio).decode()
        except Exception as exc:  # noqa: BLE001
            log.warning("TTS failed (returning text only): %s", exc)

    bg.add_task(_extract_notes_sync, turn.conversation_id, str(user.patient.id))

    return VoiceChatResponse(
        conversation_id=turn.conversation_id,
        user_message=turn.user_text,
        assistant_message=turn.reply_text,
        language=turn.language,
        audio_base64=audio_b64,
        triage_level=turn.triage_level,
        disclaimer=get_disclaimer(turn.language),
    )


# ── audio → transcript + text + audio ─────────────────────────────────
@router.post("/chat/audio")
async def voice_chat_audio(
    bg: BackgroundTasks,
    file: UploadFile = File(...),
    language: str = Form(default="en"),
    conversation_id: str | None = Form(default=None),
    user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    contents = await file.read()
    if len(contents) < 100:
        raise HTTPException(400, "Audio file too small or empty.")
    if len(contents) > MAX_AUDIO_SIZE:
        raise HTTPException(413, "Audio too large. Max 25MB.")

    try:
        tr = await get_voice().transcribe(
            contents, language=language, filename=file.filename or "audio.wav",
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"Transcription failed: {exc}") from exc

    if not tr.text:
        raise HTTPException(400, "Could not make out the audio — please speak clearly and try again.")

    try:
        turn = await consultation.run_turn(
            db, user, text=tr.text, language=language, conversation_id=conversation_id,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"AI consultation failed: {exc}") from exc

    audio_b64 = None
    try:
        syn = await get_voice().synthesize(turn.reply_text, language=turn.language)
        audio_b64 = base64.b64encode(syn.audio).decode()
    except Exception as exc:  # noqa: BLE001
        log.warning("TTS failed: %s", exc)

    bg.add_task(_extract_notes_sync, turn.conversation_id, str(user.patient.id))

    return {
        "conversation_id": turn.conversation_id,
        "transcription": tr.text,
        "language_detected": tr.language,
        "assistant_message": turn.reply_text,
        "audio_base64": audio_b64,
        "latency_ms": turn.latency_ms,
        "disclaimer": get_disclaimer(turn.language),
    }


# ── STT only ─────────────────────────────────────────────────────────
@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    file: UploadFile = File(...),
    language: str = Form(default="en"),
    user: User = Depends(get_current_patient_user),
):
    contents = await file.read()
    if not 100 <= len(contents) <= MAX_AUDIO_SIZE:
        raise HTTPException(400, "Audio too small or too large.")
    try:
        tr = await get_voice().transcribe(
            contents, language=language, filename=file.filename or "audio.wav",
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"Transcription error: {exc}") from exc
    return TranscribeResponse(
        text=tr.text, language_detected=tr.language, duration_seconds=tr.duration_s,
    )


# ── TTS only ─────────────────────────────────────────────────────────
@router.post("/synthesize")
async def synthesize(
    payload: SynthesizeRequest,
    user: User = Depends(get_current_patient_user),
):
    lang = payload.language if payload.language in settings.SUPPORTED_LANGUAGES else "en"
    try:
        syn = await get_voice().synthesize(payload.text, language=lang)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"TTS error: {exc}") from exc
    return Response(
        content=syn.audio,
        media_type=syn.content_type,
        headers={"Content-Disposition": "inline; filename=speech.wav"},
    )


# ── streaming consultation ───────────────────────────────────────────
@router.websocket("/stream")
async def voice_stream(ws: WebSocket):
    """
    Client → server:
      {"type":"auth","token":"<jwt>"}
      {"type":"start","language":"yo","conversation_id":null}
      <binary PCM16-LE 16kHz mono frames>
      {"type":"end_turn"}
    Server → client:
      {"type":"ready"} / {"type":"partial","text":..} / {"type":"final","text":..}
      {"type":"thinking"} / {"type":"reply","text":..,"conversation_id":..}
      <binary WAV frames>  interleaved with  {"type":"audio","seq":n}
      {"type":"turn_complete"} / {"type":"error","detail":..}
    """
    await ws.accept()
    db = SessionLocal()
    try:
        auth = await asyncio.wait_for(ws.receive_json(), timeout=15)
        payload = decode_access_token(auth.get("token", "")) if auth.get("type") == "auth" else None
        if not payload or not payload.get("sub"):
            await ws.send_json({"type": "error", "detail": "auth failed"})
            await ws.close(code=4401)
            return
        user = db.query(User).filter(User.id == payload["sub"], User.is_active.is_(True)).first()
        if not user or not user.patient:
            await ws.send_json({"type": "error", "detail": "no patient profile"})
            await ws.close(code=4404)
            return

        start = await asyncio.wait_for(ws.receive_json(), timeout=30)
        language = start.get("language", "en")
        if language not in settings.SUPPORTED_LANGUAGES:
            language = "en"
        conversation_id = start.get("conversation_id")

        voice = get_voice()
        streaming = voice.is_warm(language)
        if not streaming:
            await ws.send_json({"type": "warming"})
            streaming = await voice.warm(language)
        await ws.send_json({"type": "ready", "live_transcript": streaming})

        while True:
            transcript = await _stream_one_utterance(ws, voice, language, streaming)
            if transcript is None:
                break
            if not transcript.strip():
                await ws.send_json({"type": "error", "detail": "didn't catch that"})
                continue

            await ws.send_json({"type": "thinking"})
            turn = await consultation.run_turn(
                db, user, text=transcript, language=language, conversation_id=conversation_id,
            )
            conversation_id = turn.conversation_id
            await ws.send_json({
                "type": "reply", "text": turn.reply_text,
                "conversation_id": conversation_id, "latency_ms": turn.latency_ms,
            })

            seq = 0
            try:
                async for chunk in voice.synthesize_sentences(turn.reply_text, language=language):
                    seq += 1
                    await ws.send_json({"type": "audio", "seq": seq})
                    await ws.send_bytes(chunk.audio)
            except Exception as exc:  # noqa: BLE001
                log.warning("stream TTS failed: %s", exc)

            await ws.send_json({"type": "turn_complete", "conversation_id": conversation_id})
            asyncio.create_task(_extract_notes(conversation_id, str(user.patient.id)))

    except (TimeoutError, WebSocketDisconnect):
        pass
    except Exception as exc:  # noqa: BLE001
        log.exception("voice stream error")
        with _suppress():
            await ws.send_json({"type": "error", "detail": str(exc)})
    finally:
        db.close()
        with _suppress():
            await ws.close()


class _suppress:
    def __enter__(self): return self
    def __exit__(self, *a): return True


async def _stream_one_utterance(ws, voice, language: str, streaming: bool) -> str | None:
    """Read binary PCM16 frames until end_turn. When `streaming`, relay live
    partials from Sahara; otherwise (or on cold-start) buffer and transcribe the
    whole utterance. Returns the final transcript, or None on disconnect."""
    from app.providers.sahara_voice import pcm_to_wav

    queue: asyncio.Queue = asyncio.Queue()
    buffered = bytearray()

    async def _reader() -> str:
        while True:
            msg = await ws.receive()
            if msg.get("type") == "websocket.disconnect":
                await queue.put(None)
                return "disconnect"
            if msg.get("bytes") is not None:
                buffered.extend(msg["bytes"])
                await queue.put(msg["bytes"])
            elif msg.get("text"):
                data = json.loads(msg["text"])
                if data.get("type") in ("end_turn", "stop"):
                    await queue.put(None)
                    return data.get("type", "end_turn")

    async def _audio_iter():
        while True:
            item = await queue.get()
            if item is None:
                return
            yield item

    reader = asyncio.create_task(_reader())
    final_text = ""

    if streaming:
        try:
            async for ev in voice.transcribe_stream(_audio_iter(), language=language):
                if ev["type"] == "partial":
                    await ws.send_json({"type": "partial", "text": ev["text"]})
                else:
                    final_text = ev["text"]
        except SaharaColdStart:
            streaming = False  # fall through to buffered path

    outcome = await reader
    if outcome == "disconnect":
        return None

    if not final_text and buffered:
        tr = await voice.transcribe(
            pcm_to_wav(bytes(buffered)), language=language, filename="turn.wav",
        )
        final_text = tr.text

    if final_text:
        await ws.send_json({"type": "final", "text": final_text})
    return final_text


# ── health notes (the memory file) ───────────────────────────────────
@router.get("/notes")
async def get_health_notes(
    user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    notes = (
        db.query(PatientHealthNotes)
        .filter(PatientHealthNotes.patient_id == user.patient.id)
        .first()
    )
    if not notes:
        return {"message": "No notes yet — start a conversation to build your health profile.",
                "conversation_count": 0}
    return {
        "conversation_count": notes.conversation_count,
        "presenting_complaints": notes.presenting_complaints or [],
        "suspected_conditions": notes.suspected_conditions or [],
        "lifestyle_notes": notes.lifestyle_notes,
        "family_history_notes": notes.family_history_notes,
        "medication_concerns": notes.medication_concerns,
        "pain_patterns": notes.pain_patterns,
        "mental_health_notes": notes.mental_health_notes,
        "important_flags": notes.important_flags or [],
        "key_concerns": notes.key_concerns,
        "last_summary": notes.last_summary,
        "raw_notes": notes.raw_notes,
        "last_updated": notes.updated_at,
    }


# ── conversations ────────────────────────────────────────────────────
@router.get("/conversations")
async def list_conversations(
    user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    convs = (
        db.query(Conversation)
        .filter(Conversation.user_id == user.id)
        .order_by(Conversation.started_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": c.id, "language": c.language, "status": c.status,
            "started_at": c.started_at, "ended_at": c.ended_at,
            "message_count": len(c.messages),
            "preview": next((m.content for m in c.messages if m.role == "user"), None),
        }
        for c in convs
    ]


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user.id)
        .first()
    )
    if not conv:
        raise HTTPException(404, "Conversation not found.")
    return {
        "conversation_id": conv.id,
        "language": conv.language,
        "status": conv.status,
        "messages": [
            {"id": m.id, "role": m.role, "content": m.content,
             "language": m.language, "created_at": m.created_at}
            for m in sorted(conv.messages, key=lambda m: m.created_at)
        ],
    }


@router.delete("/conversations/{conversation_id}")
async def end_conversation(
    conversation_id: str,
    bg: BackgroundTasks,
    user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user.id)
        .first()
    )
    if not conv:
        raise HTTPException(404, "Conversation not found.")
    conv.status = "completed"
    conv.ended_at = datetime.utcnow()
    db.commit()
    if user.patient:
        bg.add_task(_extract_notes_sync, conversation_id, str(user.patient.id), force=True)
    return {"message": "Conversation ended.", "conversation_id": conversation_id}
