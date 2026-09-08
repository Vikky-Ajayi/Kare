"""
The memory loop: after a conversation, pull structured clinical observations
out of it and merge them into the patient's running health-notes file.

Runs as a background task — it must never fail or slow a consultation.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import settings
from app.models import ConversationMessage, PatientHealthNotes
from app.providers import get_llm

log = logging.getLogger("kare.memory")

_EXTRACT_SYSTEM = """You are a clinical documentation assistant. From the conversation, extract
what is worth remembering for the patient's next visit. Return ONLY a JSON object:
{
  "presenting_complaints": ["symptom or complaint"],
  "suspected_conditions": ["condition the doctor considered (not a diagnosis)"],
  "lifestyle_notes": "diet / sleep / exercise / stress, or null",
  "family_history_notes": "family history mentioned, or null",
  "medication_concerns": "adherence problems or side effects mentioned, or null",
  "pain_patterns": "site / timing / severity of any pain, or null",
  "mental_health_notes": "mood / anxiety / stress, or null",
  "important_flags": ["red flag or thing to actively follow up"],
  "key_concerns": "the single most important thing to check next time, or null",
  "last_summary": "2-3 sentence summary of this session",
  "raw_notes": "any other clinically useful detail, or null"
}
Use null / [] where there is nothing. Return ONLY the JSON."""

_MIN_MESSAGES = 4  # at least two full exchanges


def _merge_list(existing, new_items, cap: int = 20) -> list:
    out = list(existing or [])
    for item in new_items or []:
        if item and item not in out:
            out.append(item)
    return out[:cap]


def _merge_text(existing, new_text) -> str | None:
    if not new_text:
        return existing
    if not existing:
        return new_text
    return f"{existing}\n[update] {new_text}"


async def _extract(messages: list[dict]) -> dict:
    convo = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages)
    resp = await get_llm().complete(
        [
            {"role": "system", "content": _EXTRACT_SYSTEM},
            {"role": "user", "content": convo},
        ],
        model=settings.GROQ_LLM_MODEL_FAST,
        temperature=0.1,
        max_tokens=900,
        json_mode=True,
        reasoning_effort="low",
    )
    raw = resp.content.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        return json.loads(m.group()) if m else {}


async def update_health_notes(db: Session, conversation_id: str, patient_id: str) -> None:
    rows = (
        db.query(ConversationMessage)
        .filter(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.created_at.asc())
        .all()
    )
    if len(rows) < _MIN_MESSAGES:
        return
    messages = [{"role": r.role, "content": r.content} for r in rows]

    try:
        extracted = await _extract(messages)
    except Exception as exc:  # noqa: BLE001
        log.warning("note extraction failed for conv=%s: %s", conversation_id, exc)
        return
    if not extracted:
        return

    notes = (
        db.query(PatientHealthNotes)
        .filter(PatientHealthNotes.patient_id == patient_id)
        .first()
    )
    if not notes:
        notes = PatientHealthNotes(patient_id=patient_id)
        db.add(notes)
        db.flush()

    notes.conversation_count = (notes.conversation_count or 0) + 1
    notes.presenting_complaints = _merge_list(notes.presenting_complaints, extracted.get("presenting_complaints"))
    notes.suspected_conditions = _merge_list(notes.suspected_conditions, extracted.get("suspected_conditions"))
    notes.important_flags = _merge_list(notes.important_flags, extracted.get("important_flags"))
    notes.lifestyle_notes = _merge_text(notes.lifestyle_notes, extracted.get("lifestyle_notes"))
    notes.family_history_notes = _merge_text(notes.family_history_notes, extracted.get("family_history_notes"))
    notes.medication_concerns = _merge_text(notes.medication_concerns, extracted.get("medication_concerns"))
    notes.pain_patterns = _merge_text(notes.pain_patterns, extracted.get("pain_patterns"))
    notes.mental_health_notes = _merge_text(notes.mental_health_notes, extracted.get("mental_health_notes"))
    notes.key_concerns = extracted.get("key_concerns") or notes.key_concerns
    notes.last_summary = extracted.get("last_summary") or notes.last_summary
    notes.raw_notes = _merge_text(notes.raw_notes, extracted.get("raw_notes"))
    notes.updated_at = datetime.utcnow()
    db.commit()
    log.info("health notes updated for patient=%s (conv count %s)", patient_id, notes.conversation_count)
