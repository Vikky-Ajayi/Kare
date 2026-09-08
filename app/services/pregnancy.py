"""
Pregnancy companion: onboarding, the dating maths, and the persona + context
overlays the consultation agent uses when a patient has an active pregnancy.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models import PregnancyProfile

log = logging.getLogger("kare.pregnancy")

_PERSONA = {
    "unknown": "our little one",
    "undisclosed": "our little one",
    "male": "our little boy",
    "female": "our little girl",
}

# Brief, plain "what's happening now" notes by gestational week band.
_WEEK_NOTES = [
    (0, 8, "Very early. Nausea, tiredness and tender breasts are common. Folic acid matters most now."),
    (9, 13, "End of the first trimester. Morning sickness often starts to ease. First scan around now."),
    (14, 19, "Second trimester — usually the most comfortable stretch. You may start to feel flutters."),
    (20, 24, "Anomaly scan window. Movements become more definite. Iron needs rise."),
    (25, 28, "Third trimester begins. Glucose screening around now. Start counting daily movements."),
    (29, 33, "Baby is gaining weight fast. Watch for swelling, headaches, and any change in movements."),
    (34, 37, "Getting ready. Know the signs of labour and the danger signs. Bag packed."),
    (38, 42, "Term. Labour could start any day. Reduced movements, waters breaking, or bleeding — go in."),
]

_ALWAYS_WATCH = (
    "vaginal bleeding, waters breaking or fluid leaking, severe or persistent headache with "
    "blurred vision or swelling of the face and hands, severe abdominal pain, a fever, painful "
    "urination, persistent vomiting, and — from 28 weeks — the baby moving less or not at all"
)


def _resolve_anchor(
    profile: PregnancyProfile,
    *,
    lmp_date: date | None,
    edd: date | None,
    weeks: int | None,
    days: int | None,
    ultrasound_date: date | None,
    ultrasound_ga_weeks: float | None,
) -> None:
    if edd:
        profile.edd = edd
        profile.edd_source = "known_edd"
    if ultrasound_date and ultrasound_ga_weeks is not None:
        profile.ultrasound_date = ultrasound_date
        profile.ultrasound_ga_days = int(round(ultrasound_ga_weeks * 7))
        if not edd:
            profile.edd_source = "ultrasound"
    if lmp_date:
        profile.lmp_date = lmp_date
        if not edd and not (ultrasound_date and ultrasound_ga_weeks is not None):
            profile.edd_source = "lmp"
    if weeks is not None and not any([lmp_date, edd, ultrasound_date]):
        total = weeks * 7 + (days or 0)
        profile.lmp_date = date.today() - timedelta(days=total)
        profile.edd_source = "weeks"


def create_or_update(
    db: Session,
    patient,
    *,
    lmp_date: date | None = None,
    edd: date | None = None,
    weeks: int | None = None,
    days: int | None = None,
    ultrasound_date: date | None = None,
    ultrasound_ga_weeks: float | None = None,
    baby_sex: str | None = None,
    gravida: int | None = None,
    para: int | None = None,
    history_notes: str | None = None,
) -> PregnancyProfile:
    profile = patient.active_pregnancy
    if profile is None:
        profile = PregnancyProfile(status="active")
        patient.pregnancies.append(profile)   # keeps patient.active_pregnancy in sync
        db.add(profile)

    _resolve_anchor(
        profile,
        lmp_date=lmp_date, edd=edd, weeks=weeks, days=days,
        ultrasound_date=ultrasound_date, ultrasound_ga_weeks=ultrasound_ga_weeks,
    )
    if baby_sex in _PERSONA:
        profile.baby_sex = baby_sex
    if gravida is not None:
        profile.gravida = gravida
    if para is not None:
        profile.para = para
    if history_notes is not None:
        profile.history_notes = history_notes

    db.flush()
    return profile


def end_pregnancy(db: Session, profile: PregnancyProfile, *, outcome: str = "completed") -> None:
    from datetime import datetime
    profile.status = "completed" if outcome == "completed" else "ended"
    profile.ended_at = datetime.utcnow()
    if outcome and outcome != "completed":
        profile.history_notes = f"{profile.history_notes or ''}\n[ended: {outcome}]".strip()
    db.flush()


# ── context / persona for the consultation agent ────────────────────
def this_week_note(profile: PregnancyProfile) -> str:
    ga = profile.gestational_age_days
    if ga is None:
        return ""
    w = ga // 7
    for lo, hi, note in _WEEK_NOTES:
        if lo <= w <= hi:
            return note
    return ""


def build_pregnancy_context(profile: PregnancyProfile) -> str:
    if not profile:
        return ""
    lines = [
        f"Pregnancy: {profile.gestational_age_str} "
        f"(trimester {profile.trimester or '?'}), EDD "
        f"{profile.estimated_due_date.isoformat() if profile.estimated_due_date else 'unknown'} "
        f"[{profile.edd_source}].",
    ]
    if profile.days_to_edd is not None:
        lines.append(f"About {profile.days_to_edd} days to go.")
    if profile.baby_sex in ("male", "female"):
        lines.append(f"Expecting a {'boy' if profile.baby_sex == 'male' else 'girl'}.")
    gp = []
    if profile.gravida is not None:
        gp.append(f"G{profile.gravida}")
    if profile.para is not None:
        gp.append(f"P{profile.para}")
    if gp:
        lines.append(" ".join(gp) + ".")
    if profile.history_notes:
        lines.append(f"History: {profile.history_notes}")
    note = this_week_note(profile)
    if note:
        lines.append(f"This week: {note}")
    return "\n".join(lines)


def pregnancy_system_overlay(profile: PregnancyProfile) -> str:
    if not profile:
        return ""
    little_one = _PERSONA.get(profile.baby_sex, "our little one")
    tri = profile.trimester or 2
    tri_focus = {
        1: "early-pregnancy concerns — nausea, tiredness, folic acid, first scan, and any bleeding or cramping",
        2: "the second-trimester check-ins — anomaly scan, iron and diet, fetal movements starting, blood pressure",
        3: "third-trimester monitoring — daily fetal movements, blood pressure and pre-eclampsia signs, "
           "swelling, position, and knowing the signs of labour",
    }[tri]
    return (
        "\n\nPREGNANCY MODE — this patient is pregnant.\n"
        f"- Warm, familiar register. You may refer to the baby as \"{little_one}\".\n"
        f"- Weave in {tri_focus}, naturally — never as a checklist.\n"
        "- Every turn, keep the pregnancy danger signs in mind: "
        f"{_ALWAYS_WATCH}. If any appear, escalate immediately.\n"
        "- Gently encourage keeping antenatal appointments; you supplement them, not replace them.\n"
        "- You are an AI health assistant, not her midwife or doctor — say so if she leans on you for a decision only they should make.\n"
    )


def followup_cadence_hint(profile: PregnancyProfile) -> str:
    tri = profile.trimester if profile else None
    if tri == 1:
        return "She is in the first trimester — a check-in in about 5-7 days is reasonable unless something is unresolved sooner."
    if tri == 2:
        return "She is in the second trimester — a check-in in about 7-14 days, sooner if a symptom is unresolved."
    if tri == 3:
        return "She is in the third trimester — check in within 3-5 days, and sooner as she approaches term."
    return ""
