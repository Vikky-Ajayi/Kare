"""
Voice Router — full audio consultation system.

POST /voice/chat          — Text in, text + audio out (multi-turn doctor consultation)
POST /voice/chat/audio    — Audio in, audio out (fully hands-free)
POST /voice/transcribe    — Audio → text only
POST /voice/synthesize    — Text → MP3 only
GET  /voice/conversations — List past conversations
GET  /voice/conversations/{id}/messages
GET  /voice/notes         — Get persistent health notes (doctor's file)
DELETE /voice/conversations/{id} — End conversation (triggers note extraction)
"""

import base64
import contextlib
import uuid as uuid_module
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth_middleware import get_current_patient_user
from app.models import Conversation, ConversationMessage, PatientHealthNotes, User
from app.schemas import SynthesizeRequest, TranscribeResponse, VoiceChatRequest, VoiceChatResponse
from app.services.groq_service import (
    build_health_notes_context,
    build_patient_context,
    consult_patient,
    extract_health_notes,
    transcribe_audio,
)
from app.services.tts_service import synthesize_speech
from app.utils.helpers import get_disclaimer

router = APIRouter(prefix="/voice", tags=["Voice"])

ALLOWED_AUDIO_TYPES = {
    "audio/webm", "audio/ogg", "audio/mpeg", "audio/wav",
    "audio/mp4", "audio/m4a", "audio/flac", "audio/x-flac",
    "audio/x-m4a",
}
MAX_AUDIO_SIZE = 25 * 1024 * 1024


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _get_or_create_conversation(
    conversation_id: str | None,
    user_id: str,
    language: str,
    db: Session
) -> Conversation:
    if conversation_id:
        conv = db.query(Conversation).filter(
            Conversation.id == str(conversation_id),
            Conversation.user_id == str(user_id),
        ).first()
        if conv:
            return conv

    conv = Conversation(
        user_id=str(user_id),
        language=language,
        status="active",
    )
    db.add(conv)
    db.flush()
    return conv


def _get_or_create_health_notes(patient_id: str, db: Session) -> PatientHealthNotes:
    notes = db.query(PatientHealthNotes).filter(
        PatientHealthNotes.patient_id == str(patient_id)
    ).first()
    if not notes:
        notes = PatientHealthNotes(patient_id=str(patient_id))
        db.add(notes)
        db.flush()
    return notes


async def _run_consultation(
    text: str,
    language: str,
    conversation: Conversation,
    patient,
    db: Session,
) -> str:
    """Core consultation logic — builds context, calls AI, saves messages."""
    history_records = (
        db.query(ConversationMessage)
        .filter(ConversationMessage.conversation_id == conversation.id)
        .order_by(ConversationMessage.created_at.asc())
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in history_records]

    patient_context = build_patient_context(patient) if patient else ""
    health_notes_context = ""
    if patient:
        notes = _get_or_create_health_notes(patient.id, db)
        health_notes_context = build_health_notes_context(notes)

    ai_response = await consult_patient(
        user_message=text,
        language=language,
        conversation_history=history,
        patient_context=patient_context,
        health_notes=health_notes_context,
    )

    # Save both messages
    db.add(ConversationMessage(
        conversation_id=conversation.id,
        role="user", content=text, language=language,
    ))
    db.add(ConversationMessage(
        conversation_id=conversation.id,
        role="assistant", content=ai_response, language=language,
    ))
    db.commit()

    return ai_response


async def _update_health_notes(conversation: Conversation, patient_id: str, db: Session):
    """Extract and persist clinical notes after a conversation turn."""
    messages = (
        db.query(ConversationMessage)
        .filter(ConversationMessage.conversation_id == conversation.id)
        .order_by(ConversationMessage.created_at.asc())
        .all()
    )
    if len(messages) < 4:  # Only extract after meaningful exchange (2+ turns)
        return

    msg_list = [{"role": m.role, "content": m.content} for m in messages]

    try:
        extracted = await extract_health_notes(msg_list)
        if not extracted:
            return

        notes = _get_or_create_health_notes(patient_id, db)
        notes.conversation_count = (notes.conversation_count or 0) + 1

        # Merge new observations into existing notes
        def merge_list(existing, new_items):
            if not new_items:
                return existing or []
            existing = existing or []
            for item in new_items:
                if item and item not in existing:
                    existing.append(item)
            return existing[:20]  # cap at 20 items

        def merge_text(existing, new_text):
            if not new_text:
                return existing
            if not existing:
                return new_text
            return f"{existing}\n[Update]: {new_text}"

        notes.presenting_complaints = merge_list(
            notes.presenting_complaints, extracted.get("presenting_complaints"))
        notes.suspected_conditions = merge_list(
            notes.suspected_conditions, extracted.get("suspected_conditions"))
        notes.important_flags = merge_list(
            notes.important_flags, extracted.get("important_flags"))
        notes.lifestyle_notes = merge_text(
            notes.lifestyle_notes, extracted.get("lifestyle_notes"))
        notes.family_history_notes = merge_text(
            notes.family_history_notes, extracted.get("family_history_notes"))
        notes.medication_concerns = merge_text(
            notes.medication_concerns, extracted.get("medication_concerns"))
        notes.pain_patterns = merge_text(
            notes.pain_patterns, extracted.get("pain_patterns"))
        notes.mental_health_notes = merge_text(
            notes.mental_health_notes, extracted.get("mental_health_notes"))
        notes.key_concerns = extracted.get("key_concerns") or notes.key_concerns
        notes.raw_notes = merge_text(notes.raw_notes, extracted.get("raw_notes"))
        notes.updated_at = datetime.utcnow()

        db.commit()
    except Exception:
        pass  # Note extraction is non-critical — never fail consultation for it


# ─────────────────────────────────────────────
# TEXT CHAT (returns text + optional audio)
# ─────────────────────────────────────────────

@router.post("/chat", response_model=VoiceChatResponse)
async def voice_chat(
    payload: VoiceChatRequest,
    current_user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    """
    Full doctor consultation — text in, text + audio out.
    AI reads patient's medical file + past session notes before responding.
    Asks thorough questions before drawing conclusions.
    """
    patient = current_user.patient
    conversation = _get_or_create_conversation(
        payload.conversation_id, current_user.id, payload.language, db
    )

    try:
        ai_response = await _run_consultation(
            payload.text, payload.language, conversation, patient, db
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI service error: {str(e)}")

    # Async note extraction (fire and forget after every 2 turns)
    msg_count = db.query(ConversationMessage).filter(
        ConversationMessage.conversation_id == conversation.id
    ).count()
    if msg_count % 4 == 0 and patient:
        with contextlib.suppress(Exception):
            await _update_health_notes(conversation, str(patient.id), db)

    # Generate TTS audio
    audio_b64 = None
    if payload.include_audio:
        try:
            audio_bytes = await synthesize_speech(ai_response, language=payload.language)
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        except Exception:
            pass

    return VoiceChatResponse(
        conversation_id=uuid_module.UUID(conversation.id),
        user_message=payload.text,
        assistant_message=ai_response,
        language=payload.language,
        audio_base64=audio_b64,
        disclaimer=get_disclaimer(payload.language),
    )


# ─────────────────────────────────────────────
# FULL AUDIO CHAT (audio in → audio out)
# ─────────────────────────────────────────────

@router.post("/chat/audio")
async def voice_chat_audio(
    file: UploadFile = File(..., description="Audio recording from patient"),
    language: str = Form(default="en"),
    conversation_id: str | None = Form(default=None),
    current_user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    """
    Fully hands-free audio consultation.
    Patient sends audio → AI transcribes → consults → responds with audio.
    Returns JSON with: transcription, text response, base64 audio, conversation_id.
    """
    # Validate audio
    contents = await file.read()
    if len(contents) < 100:
        raise HTTPException(status_code=400, detail="Audio file too small or empty.")
    if len(contents) > MAX_AUDIO_SIZE:
        raise HTTPException(status_code=413, detail="Audio too large. Max 25MB.")

    # Step 1: Transcribe
    try:
        transcription = await transcribe_audio(contents, filename=file.filename or "audio.webm")
        user_text = transcription["text"].strip()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Transcription failed: {str(e)}")

    if not user_text:
        raise HTTPException(status_code=400, detail="Could not transcribe audio. Please speak clearly.")

    # Step 2: Consult
    patient = current_user.patient
    conversation = _get_or_create_conversation(
        conversation_id, current_user.id, language, db
    )

    try:
        ai_response = await _run_consultation(
            user_text, language, conversation, patient, db
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI consultation failed: {str(e)}")

    # Step 3: Synthesize speech
    audio_b64 = None
    try:
        audio_bytes = await synthesize_speech(ai_response, language=language)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    except Exception:
        pass  # Audio is optional

    # Background note extraction
    msg_count = db.query(ConversationMessage).filter(
        ConversationMessage.conversation_id == conversation.id
    ).count()
    if msg_count % 4 == 0 and patient:
        with contextlib.suppress(Exception):
            await _update_health_notes(conversation, str(patient.id), db)

    return {
        "conversation_id": conversation.id,
        "transcription": user_text,
        "language_detected": transcription.get("language_detected"),
        "assistant_message": ai_response,
        "audio_base64": audio_b64,
        "disclaimer": get_disclaimer(language),
    }


# ─────────────────────────────────────────────
# STT ONLY
# ─────────────────────────────────────────────

@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_patient_user),
):
    contents = await file.read()
    if len(contents) > MAX_AUDIO_SIZE:
        raise HTTPException(status_code=413, detail="Audio too large. Max 25MB.")
    if len(contents) < 100:
        raise HTTPException(status_code=400, detail="Audio too small or empty.")
    try:
        result = await transcribe_audio(contents, filename=file.filename or "audio.webm")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Transcription error: {str(e)}")
    return TranscribeResponse(
        text=result["text"],
        language_detected=result.get("language_detected"),
        duration_seconds=result.get("duration_seconds"),
    )


# ─────────────────────────────────────────────
# TTS ONLY
# ─────────────────────────────────────────────

@router.post("/synthesize")
async def synthesize(
    payload: SynthesizeRequest,
    current_user: User = Depends(get_current_patient_user),
):
    from app.config import settings
    if payload.language not in settings.SUPPORTED_LANGUAGES:
        payload.language = "en"
    try:
        audio_bytes = await synthesize_speech(payload.text, language=payload.language)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"TTS error: {str(e)}")
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={"Content-Disposition": "inline; filename=speech.mp3"},
    )


# ─────────────────────────────────────────────
# HEALTH NOTES (Doctor's file)
# ─────────────────────────────────────────────

@router.get("/notes")
async def get_health_notes(
    current_user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    """Get the AI doctor's persistent notes about this patient."""
    notes = db.query(PatientHealthNotes).filter(
        PatientHealthNotes.patient_id == str(current_user.patient.id)
    ).first()
    if not notes:
        return {"message": "No notes yet. Start a conversation to build your health profile."}
    return {
        "conversation_count": notes.conversation_count,
        "presenting_complaints": notes.presenting_complaints,
        "suspected_conditions": notes.suspected_conditions,
        "lifestyle_notes": notes.lifestyle_notes,
        "family_history_notes": notes.family_history_notes,
        "medication_concerns": notes.medication_concerns,
        "pain_patterns": notes.pain_patterns,
        "mental_health_notes": notes.mental_health_notes,
        "important_flags": notes.important_flags,
        "key_concerns": notes.key_concerns,
        "last_summary": notes.last_summary,
        "raw_notes": notes.raw_notes,
        "last_updated": notes.updated_at,
    }


# ─────────────────────────────────────────────
# CONVERSATIONS
# ─────────────────────────────────────────────

@router.get("/conversations")
async def list_conversations(
    current_user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    convs = (
        db.query(Conversation)
        .filter(Conversation.user_id == str(current_user.id))
        .order_by(Conversation.started_at.desc())
        .limit(50)
        .all()
    )
    return [{
        "id": c.id, "language": c.language, "status": c.status,
        "started_at": c.started_at, "ended_at": c.ended_at,
        "message_count": len(c.messages),
    } for c in convs]


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == str(current_user.id),
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {
        "conversation_id": conv.id,
        "language": conv.language,
        "messages": [
            {"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at}
            for m in conv.messages
        ],
    }


@router.delete("/conversations/{conversation_id}")
async def end_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    """End conversation and trigger final note extraction."""
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == str(current_user.id),
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    conv.status = "completed"
    conv.ended_at = datetime.utcnow()
    db.commit()

    # Final note extraction on conversation end
    if current_user.patient:
        with contextlib.suppress(Exception):
            await _update_health_notes(conv, str(current_user.patient.id), db)

    return {"message": "Conversation ended.", "conversation_id": conversation_id}
