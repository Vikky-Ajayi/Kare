"""
The consultation agent's tools: schemas the model sees, plus executors that run
against the DB and the free medical APIs.

Every executor takes the ToolContext and returns a plain dict that goes back to
the model as the tool result.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.models import AuditLog, Conversation, MedicalCondition, Medication, User
from app.services import drug_interaction_service
from app.services.context import build_health_notes_context, build_patient_context
from app.services.search_service import format_for_prompt, search_medical

log = logging.getLogger("kare.tools")

_TRIAGE = ("emergency", "urgent", "semi_urgent", "routine", "self_care")


@dataclass
class ToolContext:
    db: Session
    user: User
    conversation: Conversation
    language: str

    @property
    def patient(self):
        return self.user.patient


# ── schemas (OpenAI function-calling format) ─────────────────────────
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_patient_history",
            "description": "Re-read the patient's file or your saved notes — conditions, "
                           "medications, allergies, past complaints, flags. Use when you need "
                           "a detail you don't already have in view.",
            "parameters": {
                "type": "object",
                "properties": {
                    "focus": {"type": "string",
                              "enum": ["all", "medications", "conditions", "allergies", "notes"]}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_drug_interactions",
            "description": "Check for interactions between drugs before recommending or "
                           "combining anything. Pass every drug involved, including the "
                           "patient's current medications.",
            "parameters": {
                "type": "object",
                "properties": {
                    "drugs": {"type": "array", "items": {"type": "string"},
                              "description": "Drug names, generic or brand"}
                },
                "required": ["drugs"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "score_triage",
            "description": "Record your triage assessment for this consultation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {"type": "string", "enum": list(_TRIAGE)},
                    "reasoning": {"type": "string"},
                    "warning_signs": {"type": "array", "items": {"type": "string"},
                                      "description": "What should make the patient seek care sooner"},
                },
                "required": ["level", "reasoning"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_health_record",
            "description": "Save something the patient has confirmed: a new condition, a new "
                           "or changed medication, an allergy, or a side effect. Only write "
                           "what the patient actually told you.",
            "parameters": {
                "type": "object",
                "properties": {
                    "kind": {"type": "string",
                             "enum": ["condition", "medication", "allergy", "side_effect"]},
                    "name": {"type": "string"},
                    "detail": {"type": "string",
                               "description": "dose/frequency for a medication; description "
                                              "for a side effect or condition"},
                },
                "required": ["kind", "name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "plan_followup",
            "description": "Decide whether Kare should proactively check in on this patient "
                           "later, when, and about what. Call this once near the end of a turn "
                           "where there is something worth following up (unresolved symptom, "
                           "a medication course, a side effect, a concern raised).",
            "parameters": {
                "type": "object",
                "properties": {
                    "should_follow_up": {"type": "boolean"},
                    "hours_until": {"type": "integer",
                                    "description": "6-12 for concerning-not-emergency, ~16-24 "
                                                   "for next-morning, longer for a med course"},
                    "topics": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "topic": {"type": "string"},
                                "why": {"type": "string"},
                                "ask": {"type": "string", "description": "how to raise it, naturally"},
                            },
                        },
                    },
                },
                "required": ["should_follow_up"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_medical_literature",
            "description": "Look up current guidance — dosing, contraindications, treatment "
                           "guidelines — when you are not certain. Use before giving "
                           "drug-specific advice.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "flag_for_escalation",
            "description": "Escalate: this needs urgent in-person or emergency care. Marks the "
                           "consultation and returns local emergency guidance. Your spoken reply "
                           "must still lead with the warning.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string"},
                    "level": {"type": "string", "enum": ["emergency", "urgent"]},
                },
                "required": ["reason"],
            },
        },
    },
]


def _audit(ctx: ToolContext, action: str, details: dict) -> None:
    ctx.db.add(AuditLog(
        user_id=ctx.user.id, action=action,
        resource_type="conversation", resource_id=ctx.conversation.id,
        details=details,
    ))


# ── executors ───────────────────────────────────────────────────────
async def _get_patient_history(ctx: ToolContext, focus: str = "all") -> dict:
    p = ctx.patient
    if not p:
        return {"error": "no patient profile"}
    out: dict = {}
    if focus in ("all", "conditions"):
        out["conditions"] = [
            {"name": c.condition_name, "status": c.status, "since": str(c.diagnosed_date or "")}
            for c in p.medical_conditions
        ]
    if focus in ("all", "medications"):
        out["medications"] = [
            {"name": m.drug_name, "dose": m.dosage, "frequency": m.frequency, "status": m.status}
            for m in p.medications
        ]
    if focus in ("all", "allergies"):
        out["allergies"] = p.allergies or []
    if focus in ("all", "notes"):
        out["file"] = build_patient_context(p)
        out["notes"] = build_health_notes_context(p.health_notes) if p.health_notes else ""
    return out


async def _check_drug_interactions(ctx: ToolContext, drugs: list[str]) -> dict:
    names = [d.strip() for d in drugs if d and d.strip()]
    if len(names) < 2:
        # still useful: fold in the patient's current meds
        current = [m.drug_name for m in ctx.patient.medications if m.status in ("active", "as_needed")] if ctx.patient else []
        names = list(dict.fromkeys(names + current))
    if len(names) < 2:
        return {"checked": names, "interactions": [], "note": "need at least two drugs"}
    try:
        result = await drug_interaction_service.check_interactions_by_name(names)
    except Exception as exc:  # noqa: BLE001
        return {"checked": names, "error": f"interaction service unavailable: {exc}"}
    _audit(ctx, "drug_interaction_check", {"drugs": names,
                                           "found": result.get("interactions_found", 0)})
    return {
        "checked": names,
        "unresolved": result.get("unresolved", []),
        "interactions": [
            {"a": i.get("drug_1"), "b": i.get("drug_2"),
             "severity": i.get("severity"), "description": i.get("description")}
            for i in result.get("interactions", [])
        ],
    }


async def _score_triage(ctx: ToolContext, level: str, reasoning: str,
                        warning_signs: list[str] | None = None) -> dict:
    level = level if level in _TRIAGE else "routine"
    ctx.conversation.triage_result = level
    _audit(ctx, "triage_scored", {"level": level, "reasoning": reasoning})
    return {"recorded": level, "warning_signs": warning_signs or []}


async def _update_health_record(ctx: ToolContext, kind: str, name: str, detail: str = "") -> dict:
    p = ctx.patient
    if not p:
        return {"error": "no patient profile"}
    if kind == "condition":
        ctx.db.add(MedicalCondition(patient_id=p.id, condition_name=name, status="active",
                                    notes=detail or None, diagnosed_date=date.today()))
    elif kind == "medication":
        dose, freq = (detail.split(",", 1) + [""])[:2] if detail else ("", "")
        ctx.db.add(Medication(patient_id=p.id, drug_name=name, dosage=dose.strip() or None,
                              frequency=freq.strip() or None, status="active",
                              start_date=date.today()))
    elif kind == "allergy":
        p.allergies = list(dict.fromkeys((p.allergies or []) + [name]))
    elif kind == "side_effect":
        notes = p.health_notes
        if notes:
            add = f"{name}: {detail}" if detail else name
            notes.medication_concerns = (
                f"{notes.medication_concerns}\n[reported] {add}" if notes.medication_concerns else add
            )
    else:
        return {"error": f"unknown kind {kind}"}
    _audit(ctx, "health_record_update", {"kind": kind, "name": name})
    return {"saved": kind, "name": name}


async def _plan_followup(ctx: ToolContext, should_follow_up: bool,
                         hours_until: int = 20, topics: list[dict] | None = None) -> dict:
    if not should_follow_up:
        ctx.conversation.followup_plan = None
        return {"scheduled": False}
    hours = max(2, min(int(hours_until or 20), 24 * 14))
    due = datetime.utcnow() + timedelta(hours=hours)
    ctx.conversation.followup_plan = {
        "due_at": due.isoformat(),
        "topics": topics or [],
        "language": ctx.language,
        "created_at": datetime.utcnow().isoformat(),
    }
    _audit(ctx, "followup_planned", {"due_at": due.isoformat(), "topics": len(topics or [])})
    return {"scheduled": True, "due_in_hours": hours,
            "topics": [t.get("topic") for t in (topics or [])]}


async def _search(ctx: ToolContext, query: str) -> dict:
    results = await search_medical(query, max_results=4)
    return {"query": query, "results": format_for_prompt(results)}


async def _flag_for_escalation(ctx: ToolContext, reason: str, level: str = "emergency") -> dict:
    ctx.conversation.triage_result = "emergency" if level == "emergency" else "urgent"
    ctx.conversation.stage = "plan"
    _audit(ctx, "escalation", {"reason": reason, "level": level})
    return {
        "escalated": True,
        "guidance": (
            "Nigeria emergency line: 112 (or 767 / 122 in Lagos). "
            "Tell the patient to go to the nearest hospital or call these now. "
            "If someone can take them, they should not drive themselves."
        ),
    }


EXECUTORS = {
    "get_patient_history": _get_patient_history,
    "check_drug_interactions": _check_drug_interactions,
    "score_triage": _score_triage,
    "update_health_record": _update_health_record,
    "plan_followup": _plan_followup,
    "search_medical_literature": _search,
    "flag_for_escalation": _flag_for_escalation,
}
