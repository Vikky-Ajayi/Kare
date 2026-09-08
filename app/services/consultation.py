"""
One consultation turn: build context, ask the model, persist both messages.

P1 keeps this a single grounded LLM call. P2 wraps the model call in the agent
loop (tools + clinical state machine + red-flag interrupt) without changing this
signature, so the routers never need to know which one is running.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Conversation, ConversationMessage, PatientHealthNotes, User
from app.providers import get_llm
from app.services.context import build_health_notes_context, build_patient_context

log = logging.getLogger("kare.consult")

_HISTORY_TURNS = 16  # trailing messages sent back to the model


DOCTOR_SYSTEM = """You are the AI doctor inside Kare, a health companion for Nigeria and West Africa.
You speak like an experienced, warm primary-care doctor who knows this patient.

SAFETY FIRST — before anything else, check for danger signs. If the patient reports any of:
chest pain or tightness, difficulty breathing, severe bleeding, one-sided weakness or
face droop, sudden severe headache, a stiff neck with fever, fainting, a fit/seizure,
severe abdominal pain, thoughts of self-harm, poisoning, a snake bite, or (in pregnancy)
vaginal bleeding, severe headache with blurred vision or swelling, reduced fetal movement,
or fluid leaking — your FIRST sentence must say plainly that this could be serious and
that they should get to a hospital or call emergency services NOW. Only after that may you
ask a question. Never bury an emergency behind history-taking.

HOW YOU TALK
- Reply in the SAME language and the SAME code-switched register the patient used
  (Yoruba-English, Hausa-English, Igbo-English, Nigerian Pidgin, or English). Mixing
  languages is normal speech — never "correct" it.
- This is a SPOKEN conversation. Plain sentences only — no markdown, no lists, no headings.
- Keep replies SHORT: 2-3 sentences, and end with at most one clear question. Only when
  you are giving a considered assessment may you go longer (still no lists).
- Warm, direct, unhurried. You are their doctor, not a search engine.

HOW YOU WORK
- Read the patient's file and your past notes below and use them naturally
  ("last time you mentioned...", "with your blood pressure...").
- Gather before concluding. Ask 1-3 focused questions per turn. For pain, work through
  site, onset, character, radiation, timing, what makes it better or worse, severity.
- Think in the local disease context first: malaria, typhoid, TB, sickle cell,
  hypertension, diabetes, maternal health. Do not assume a Western profile.
- Never say "you have X" early. Say "this could point to X, but I need to understand more".
- If anything suggests an emergency, say so plainly and immediately and tell them to get
  to a hospital now.
- When you give an assessment, end with one short line that this supports but does not
  replace seeing a health worker in person.
"""


@dataclass
class TurnResult:
    conversation_id: str
    user_text: str
    reply_text: str
    language: str
    latency_ms: int
    triage_level: str | None = None


def get_or_create_conversation(
    db: Session, user: User, language: str, conversation_id: str | None
) -> Conversation:
    if conversation_id:
        conv = (
            db.query(Conversation)
            .filter(Conversation.id == str(conversation_id), Conversation.user_id == user.id)
            .first()
        )
        if conv:
            return conv
    conv = Conversation(user_id=user.id, language=language, status="active")
    db.add(conv)
    db.flush()
    return conv


def _history(db: Session, conversation_id: str) -> list[dict]:
    rows = (
        db.query(ConversationMessage)
        .filter(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.created_at.asc())
        .all()
    )
    return [{"role": m.role, "content": m.content} for m in rows[-_HISTORY_TURNS:]]


def _system_prompt(patient) -> str:
    prompt = DOCTOR_SYSTEM
    if patient:
        pc = build_patient_context(patient)
        if pc:
            prompt += f"\n\n=== PATIENT FILE ===\n{pc}"
        notes = patient.health_notes
        nc = build_health_notes_context(notes) if notes else ""
        if nc:
            prompt += f"\n\n=== YOUR NOTES FROM PAST SESSIONS ===\n{nc}"
    return prompt


async def run_turn(
    db: Session,
    user: User,
    *,
    text: str,
    language: str,
    conversation_id: str | None = None,
) -> TurnResult:
    if language not in settings.SUPPORTED_LANGUAGES:
        language = "en"

    patient = user.patient
    conv = get_or_create_conversation(db, user, language, conversation_id)

    messages = [{"role": "system", "content": _system_prompt(patient)}]
    messages += _history(db, conv.id)
    messages.append({"role": "user", "content": text})

    t0 = time.perf_counter()
    resp = await get_llm().complete(
        messages,
        temperature=0.4,
        max_tokens=450,
        reasoning_effort="low",
    )
    latency_ms = int((time.perf_counter() - t0) * 1000)
    reply = resp.content.strip() or "I'm sorry, I didn't catch that — could you say it again?"

    db.add(ConversationMessage(
        conversation_id=conv.id, role="user", content=text, language=language,
    ))
    db.add(ConversationMessage(
        conversation_id=conv.id, role="assistant", content=reply, language=language,
    ))
    conv.language = language
    db.commit()

    log.info("turn conv=%s lang=%s llm=%dms tokens=%s",
             conv.id, language, latency_ms, resp.usage.get("total_tokens"))

    return TurnResult(
        conversation_id=conv.id,
        user_text=text,
        reply_text=reply,
        language=language,
        latency_ms=latency_ms,
    )


def _ensure_notes(db: Session, patient_id: str) -> PatientHealthNotes:
    notes = (
        db.query(PatientHealthNotes)
        .filter(PatientHealthNotes.patient_id == patient_id)
        .first()
    )
    if not notes:
        notes = PatientHealthNotes(patient_id=patient_id)
        db.add(notes)
        db.flush()
    return notes
