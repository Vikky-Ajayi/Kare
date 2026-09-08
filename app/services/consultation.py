"""
One consultation turn.

  red-flag check  ->  escalation reply     (danger sign detected deterministically)
                  ->  agent loop            (tools + clinical stages, the normal path)

The router-facing signature never changes; TurnResult just gained tool_calls and
escalated so the frontend can show what happened.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.agent import redflags
from app.agent.loop import run_agent
from app.agent.tools import ToolContext
from app.config import settings
from app.models import Conversation, ConversationMessage, User
from app.providers import get_llm
from app.services.context import build_health_notes_context, build_patient_context

log = logging.getLogger("kare.consult")

_HISTORY_TURNS = 16

DOCTOR_SYSTEM = """You are the AI doctor inside Kare, a health companion for Nigeria and West Africa.
You speak like an experienced, warm primary-care doctor who knows this patient.

HOW YOU TALK
- Reply in the SAME language and the SAME code-switched register the patient used
  (Yoruba-English, Hausa-English, Igbo-English, Nigerian Pidgin, or English). Mixing
  languages is normal speech — never "correct" it.
- This is a SPOKEN conversation. Plain sentences only — no markdown, no lists, no headings.
- Keep replies SHORT: 2-3 sentences, ending with at most one clear question. Go longer only
  for a considered assessment (still no lists).
- Warm, direct, unhurried. You are their doctor, not a search engine.

HOW YOU WORK
- The patient's file and your past notes are below — use them naturally
  ("last time you mentioned...", "with your blood pressure...").
- Gather before concluding. 1-3 focused questions per turn. For pain: site, onset,
  character, radiation, timing, better/worse, severity.
- Think local disease context first: malaria, typhoid, TB, sickle cell, hypertension,
  diabetes, maternal health. Never assume a Western profile.
- Use your tools: check drug interactions before advising on medicines; search when you
  are unsure of dosing or guidelines; record what the patient confirms; score the triage
  once you have enough; near the end of a symptomatic turn, plan a follow-up.
- Never say "you have X" early — "this could point to X, but I need to understand more".
- End an assessment with one short line that this supports but does not replace seeing a
  health worker in person.
"""

_STAGE_HINT = {
    "intake": "This is the start — greet warmly, acknowledge the complaint, begin gathering.",
    "gathering": "Keep gathering the history you still need before any assessment.",
    "assessment": "You have enough to give a considered assessment with a likely cause or two.",
    "plan": "Give clear next steps and a plan; plan a follow-up if anything is unresolved.",
}

ESCALATION_SYSTEM = """You are the AI doctor inside Kare. The patient has just described a
possible EMERGENCY ({reason}). Your reply MUST:
1. Open by saying plainly, in their language and register, that this could be serious and
   they should get to the nearest hospital now, or call 112 (or 767/122 in Lagos).
2. Be calm and warm, not alarming. Two or three short spoken sentences.
3. End with ONE question that matters for the next minutes (who is with them / can someone
   take them / when exactly it started).
No markdown, no lists. Reply only in the patient's language and code-switched register.
"""


@dataclass
class TurnResult:
    conversation_id: str
    user_text: str
    reply_text: str
    language: str
    latency_ms: int
    triage_level: str | None = None
    escalated: bool = False
    tool_calls: list[str] = field(default_factory=list)


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
    conv = Conversation(user_id=user.id, language=language, status="active", stage="intake")
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


def _advance_stage(conv: Conversation, n_messages: int, tools_used: list[str]) -> None:
    if "flag_for_escalation" in tools_used or "plan_followup" in tools_used:
        conv.stage = "plan"
    elif "score_triage" in tools_used:
        conv.stage = "assessment"
    elif n_messages <= 2:
        conv.stage = "intake"
    elif conv.stage in (None, "intake"):
        conv.stage = "gathering"


def _system_prompt(patient, stage: str) -> str:
    prompt = DOCTOR_SYSTEM + f"\n\nSTAGE: {_STAGE_HINT.get(stage, _STAGE_HINT['gathering'])}"
    if patient:
        pc = build_patient_context(patient)
        if pc:
            prompt += f"\n\n=== PATIENT FILE ===\n{pc}"
        nc = build_health_notes_context(patient.health_notes) if patient.health_notes else ""
        if nc:
            prompt += f"\n\n=== YOUR NOTES FROM PAST SESSIONS ===\n{nc}"
    return prompt


def _is_pregnant(patient) -> bool:
    if not patient:
        return False
    if any("pregnan" in (c.condition_name or "").lower() for c in patient.medical_conditions):
        return True
    notes = patient.health_notes
    blob = " ".join(str(x) for x in [
        notes and notes.raw_notes, notes and notes.key_concerns,
        notes and " ".join(notes.presenting_complaints or []),
    ] if x)
    return "pregnan" in blob.lower()


async def _escalation_reply(ctx: ToolContext, text: str, reason: str, history: list[dict]) -> str:
    from app.agent.tools import _flag_for_escalation
    await _flag_for_escalation(ctx, reason=reason, level="emergency")
    resp = await get_llm().complete(
        [
            {"role": "system", "content": ESCALATION_SYSTEM.format(reason=reason)},
            *history[-2:],
            {"role": "user", "content": text},
        ],
        model=settings.GROQ_LLM_MODEL_FAST,
        temperature=0.3,
        max_tokens=260,
        reasoning_effort="low",
    )
    return resp.content.strip() or (
        "This could be serious — please get to the nearest hospital now, or call 112. "
        "Is there someone who can take you?"
    )


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
    conv.language = language
    history = _history(db, conv.id)
    n_messages = len(history) + 1

    ctx = ToolContext(db=db, user=user, conversation=conv, language=language)
    t0 = time.perf_counter()
    _advance_stage(conv, n_messages, [])
    pregnant = _is_pregnant(patient)
    escalated = False
    tools_used: list[str] = []

    kw_flag = redflags.keyword_check(text, pregnant=pregnant)
    if kw_flag:
        escalated = True
        reply = await _escalation_reply(ctx, text, kw_flag.category, history)
        tools_used = ["flag_for_escalation"]
        log.info("red flag (keyword/%s) conv=%s", kw_flag.reason, conv.id)
    else:
        # classifier backstop runs concurrently with the agent's first pass
        clf_task = asyncio.create_task(redflags.classifier_check(text))
        agent_task = asyncio.create_task(run_agent(
            ctx,
            system_prompt=_system_prompt(patient, conv.stage or "gathering"),
            history=history,
            user_message=text,
        ))
        flag = await clf_task
        if flag.triggered:
            escalated = True
            agent_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await agent_task
            reply = await _escalation_reply(ctx, text, flag.category, history)
            tools_used = ["flag_for_escalation"]
            log.info("red flag (classifier/%s) conv=%s", flag.category, conv.id)
        else:
            result = await agent_task
            reply = result.reply
            tools_used = result.tool_calls

    latency_ms = int((time.perf_counter() - t0) * 1000)
    _advance_stage(conv, n_messages, tools_used)

    db.add(ConversationMessage(conversation_id=conv.id, role="user", content=text, language=language))
    db.add(ConversationMessage(conversation_id=conv.id, role="assistant", content=reply, language=language))
    db.commit()

    log.info("turn conv=%s lang=%s stage=%s %dms tools=%s escalated=%s",
             conv.id, language, conv.stage, latency_ms, tools_used, escalated)

    return TurnResult(
        conversation_id=conv.id,
        user_text=text,
        reply_text=reply,
        language=language,
        latency_ms=latency_ms,
        triage_level=conv.triage_result,
        escalated=escalated,
        tool_calls=tools_used,
    )
