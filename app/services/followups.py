"""
The proactive follow-up loop.

  consultation  --plan_followup-->  conversation.followup_plan
                --promote-->        ScheduledFollowUp (pending)
  worker tick   --due & clear-->    compose natural message
                                    write it into the conversation (assistant turn)
                                    Web Push with a deep link
  patient taps  --resume-->         same conversation; next reply marks it answered

The message is ALWAYS model-generated from the patient's real context — never a
template. Two patients with the same complaint get different messages.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from dateutil import parser as dtparse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.models import (
    Conversation,
    ConversationMessage,
    Patient,
    ScheduledFollowUp,
)
from app.providers import get_llm
from app.services import push
from app.services.context import build_health_notes_context, build_patient_context

log = logging.getLogger("kare.followups")

COMPOSE_SYSTEM = """You are the AI doctor inside Kare, reaching out to a patient you saw earlier —
like a doctor who genuinely remembers the last conversation and wants to know how they are.

Write ONE short message (2-3 sentences, plain spoken text, no markdown) that:
- opens warmly by name, the way a person would ("Hi {name} 😊", "Morning {name},")
- asks how they are, then follows up naturally on the specific things below — weave them
  into the sentence, don't list them
- if a medication or side effect is in the list, ask about it the way a person would
  ("hope you've been taking the tablets", "is that stomach upset any better")
- sounds like it was written just for them, not generated from a database

Reply ONLY in {language_name} and the same code-switched register the patient uses.
Do not give new medical advice here — this is a check-in. Do not mention that you are an AI
or that this is an automated message."""


def _tz(patient: Patient) -> ZoneInfo:
    try:
        return ZoneInfo(patient.timezone or "Africa/Lagos")
    except Exception:  # noqa: BLE001
        return ZoneInfo("Africa/Lagos")


def _next_allowed(now_utc: datetime, patient: Patient) -> datetime | None:
    """Return a bumped due time if `now` is outside the patient's quiet hours,
    else None (meaning: fine to send now)."""
    local = now_utc.astimezone(_tz(patient))
    start, end = settings.FOLLOWUP_QUIET_START, settings.FOLLOWUP_QUIET_END
    if start <= local.hour < end:
        return None
    # bump to the next `start` o'clock, local
    target = local.replace(hour=start, minute=0, second=0, microsecond=0)
    if local.hour >= end:
        target += timedelta(days=1)
    return target.astimezone(UTC).replace(tzinfo=None)


_DECIDE_SYSTEM = """Decide whether Kare should proactively check in on this patient after this
consultation, and if so, when and about what. Consider: unresolved symptoms, a medication
course just started, a side effect mentioned, a concern the patient raised, and how long
until it would be useful to know how they are.
Return ONLY JSON:
{"should_follow_up": true|false,
 "hours_until": 6-336,
 "topics": [{"topic": "...", "why": "...", "ask": "how to raise it naturally"}]}"""


async def decide_and_plan(db: Session, conv: Conversation) -> ScheduledFollowUp | None:
    """One LLM call at consultation end: should we check in, when, about what.
    Sets conv.followup_plan then promotes. Runs regardless of whether the agent
    called plan_followup mid-conversation."""
    patient = conv.user.patient if conv.user else None
    if not patient or not patient.followups_enabled:
        return None

    msgs = (
        db.query(ConversationMessage)
        .filter(ConversationMessage.conversation_id == conv.id)
        .order_by(ConversationMessage.created_at.asc())
        .all()
    )
    if len(msgs) < 4:
        return None
    convo = "\n".join(f"{m.role}: {m.content}" for m in msgs[-16:])

    try:
        resp = await get_llm().complete(
            [
                {"role": "system", "content": _DECIDE_SYSTEM},
                {"role": "user", "content": f"Notes: {build_health_notes_context(patient.health_notes)}\n\n{convo}"},
            ],
            model=settings.GROQ_LLM_MODEL_FAST,
            temperature=0.2, max_tokens=400, json_mode=True, reasoning_effort="low",
        )
        import json
        plan = json.loads(resp.content.strip() or "{}")
    except Exception as exc:  # noqa: BLE001
        log.warning("decide_and_plan failed for conv=%s: %s", conv.id, exc)
        return None

    if not plan.get("should_follow_up"):
        return None
    hours = max(2, min(int(plan.get("hours_until") or 20), 24 * 14))
    conv.followup_plan = {
        "due_at": (datetime.utcnow() + timedelta(hours=hours)).isoformat(),
        "topics": plan.get("topics", []),
        "language": conv.language or "en",
    }
    db.flush()
    return promote_from_conversation(db, conv)


# ── promote / answer ────────────────────────────────────────────────
def promote_from_conversation(db: Session, conv: Conversation) -> ScheduledFollowUp | None:
    plan = conv.followup_plan
    patient = conv.user.patient if conv.user else None
    if not plan or not patient or not patient.followups_enabled:
        return None

    try:
        due_at = dtparse.isoparse(plan["due_at"])
        if due_at.tzinfo:
            due_at = due_at.astimezone(UTC).replace(tzinfo=None)
    except Exception:  # noqa: BLE001
        due_at = datetime.utcnow() + timedelta(hours=20)

    existing = (
        db.query(ScheduledFollowUp)
        .filter(ScheduledFollowUp.conversation_id == conv.id,
                ScheduledFollowUp.status == "pending")
        .first()
    )
    prior_sent = (
        db.query(func.count(ScheduledFollowUp.id))
        .filter(ScheduledFollowUp.conversation_id == conv.id,
                ScheduledFollowUp.status.in_(("sent", "answered")))
        .scalar()
    )
    if prior_sent >= settings.FOLLOWUP_MAX_ATTEMPTS:
        if existing:
            existing.status = "cancelled"
            existing.reason = "max attempts reached"
        return None

    row = existing or ScheduledFollowUp(patient_id=patient.id, conversation_id=conv.id)
    row.due_at = due_at
    row.language = plan.get("language", conv.language or "en")
    row.topics = plan.get("topics", [])
    row.status = "pending"
    row.attempt = prior_sent
    if not existing:
        db.add(row)
    db.flush()
    return row


def mark_answered_if_pending(db: Session, conversation_id: str) -> None:
    (
        db.query(ScheduledFollowUp)
        .filter(ScheduledFollowUp.conversation_id == conversation_id,
                ScheduledFollowUp.status == "sent")
        .update({"status": "answered", "answered_at": datetime.utcnow()},
                synchronize_session=False)
    )


# ── compose + deliver ──────────────────────────────────────────────
async def _compose(db: Session, followup: ScheduledFollowUp) -> str:
    patient = followup.patient
    conv = followup.conversation
    recent = (
        db.query(ConversationMessage)
        .filter(ConversationMessage.conversation_id == conv.id)
        .order_by(ConversationMessage.created_at.desc())
        .limit(6)
        .all()
    )
    recent_text = "\n".join(f"{m.role}: {m.content}" for m in reversed(recent))
    topics = "\n".join(
        f"- {t.get('topic', '')}: {t.get('why', '')}" for t in (followup.topics or [])
    ) or "- how they are doing generally since you spoke"

    hours_ago = int((datetime.utcnow() - conv.started_at).total_seconds() // 3600) if conv.started_at else 0
    lang_name = settings.LANGUAGE_NAMES.get(followup.language, "English")

    system = COMPOSE_SYSTEM.format(name=patient.first_name, language_name=lang_name)
    user_block = (
        f"Patient: {build_patient_context(patient)}\n\n"
        f"Your notes: {build_health_notes_context(patient.health_notes)}\n\n"
        f"Last conversation (about {hours_ago}h ago):\n{recent_text}\n\n"
        f"Follow up on:\n{topics}"
    )
    resp = await get_llm().complete(
        [{"role": "system", "content": system}, {"role": "user", "content": user_block}],
        temperature=0.7,
        max_tokens=220,
        reasoning_effort="low",
    )
    return resp.content.strip() or f"Hi {patient.first_name}, just checking in — how are you feeling today?"


async def deliver(db: Session, followup: ScheduledFollowUp) -> bool:
    conv = followup.conversation
    patient = followup.patient
    try:
        message = await _compose(db, followup)
    except Exception as exc:  # noqa: BLE001
        log.warning("compose failed for followup=%s: %s", followup.id, exc)
        followup.status = "failed"
        followup.reason = f"compose: {exc}"
        db.commit()
        return False

    followup.generated_message = message
    db.add(ConversationMessage(
        conversation_id=conv.id, role="assistant", content=message,
        language=followup.language,
    ))
    conv.status = "active"
    db.flush()

    url = f"{settings.PUBLIC_APP_URL.rstrip('/')}/dashboard/voice?c={conv.id}&f={followup.id}"
    push.send_to_user(
        db, patient.user_id,
        title="Kare", body=message[:180], url=url, tag=f"followup-{conv.id}",
    )

    followup.status = "sent"
    followup.sent_at = datetime.utcnow()
    followup.attempt = (followup.attempt or 0) + 1
    db.commit()
    log.info("followup %s delivered (conv=%s attempt=%s)", followup.id, conv.id, followup.attempt)
    return True


# ── worker entry ───────────────────────────────────────────────────
async def process_due(db: Session, *, limit: int = 50) -> dict:
    now = datetime.utcnow()
    rows = (
        db.query(ScheduledFollowUp)
        .filter(ScheduledFollowUp.status == "pending", ScheduledFollowUp.due_at <= now)
        .order_by(ScheduledFollowUp.due_at.asc())
        .limit(limit)
        .with_for_update(skip_locked=True)
        .all()
    )
    stats = {"considered": len(rows), "sent": 0, "skipped": 0, "bumped": 0, "cancelled": 0}

    for f in rows:
        patient = f.patient
        conv = f.conversation
        if not patient or not patient.followups_enabled:
            f.status = "cancelled"
            f.reason = "follow-ups disabled"
            stats["cancelled"] += 1
            continue

        # already engaged? patient messaged since this was planned
        last_user = (
            db.query(func.max(ConversationMessage.created_at))
            .filter(ConversationMessage.conversation_id == conv.id,
                    ConversationMessage.role == "user")
            .scalar()
        )
        if last_user and last_user > f.created_at:
            f.status = "cancelled"
            f.reason = "patient already messaged"
            stats["cancelled"] += 1
            continue

        # frequency cap — recent proactive push to this patient
        recent_send = (
            db.query(func.max(ScheduledFollowUp.sent_at))
            .filter(ScheduledFollowUp.patient_id == patient.id,
                    ScheduledFollowUp.sent_at.isnot(None))
            .scalar()
        )
        if recent_send and (now - recent_send) < timedelta(hours=settings.FOLLOWUP_MIN_GAP_HOURS):
            f.due_at = recent_send + timedelta(hours=settings.FOLLOWUP_MIN_GAP_HOURS)
            stats["bumped"] += 1
            continue

        # quiet hours
        bump = _next_allowed(now.replace(tzinfo=UTC), patient)
        if bump:
            f.due_at = bump
            stats["bumped"] += 1
            continue

        ok = await deliver(db, f)
        stats["sent" if ok else "skipped"] += 1

    db.commit()
    return stats
