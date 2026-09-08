"""
Build the context strings the model reads before every turn: the patient's
medical file and the running health-notes memory. Kept separate so the
consultation agent, the symptom checker, and the follow-up writer all share
exactly one view of the patient.
"""

from __future__ import annotations

from app.utils.helpers import calculate_age, calculate_bmi


def build_patient_context(patient) -> str:
    if not patient:
        return ""
    age = calculate_age(patient.date_of_birth)
    bmi = calculate_bmi(patient.height_cm, patient.weight_kg)
    lines = [
        f"Name: {patient.first_name} {patient.last_name}",
        f"Age: {age if age is not None else 'unknown'}  |  "
        f"Sex: {patient.gender or 'not specified'}  |  "
        f"Blood group: {patient.blood_group or 'unknown'}  |  "
        f"BMI: {bmi if bmi is not None else 'unknown'}",
        f"Location: {patient.state or 'unknown'}, {patient.country or 'Nigeria'}",
        f"Allergies: {', '.join(patient.allergies) if patient.allergies else 'none reported'}",
    ]
    if patient.medical_conditions:
        conds = [f"{c.condition_name} ({c.status})" for c in patient.medical_conditions]
        lines.append(f"Conditions: {', '.join(conds)}")
    active_meds = [
        f"{m.drug_name} {m.dosage or ''} {m.frequency or ''}".strip()
        for m in patient.medications
        if m.status in ("active", "as_needed")
    ]
    if active_meds:
        lines.append(f"Current medications: {', '.join(active_meds)}")
    return "\n".join(lines)


def build_health_notes_context(notes) -> str:
    if not notes:
        return ""
    lines: list[str] = []
    if notes.conversation_count:
        lines.append(f"Consultations so far: {notes.conversation_count}")
    _list(lines, "Recurring complaints", notes.presenting_complaints)
    _list(lines, "Previously suspected", notes.suspected_conditions)
    _text(lines, "Lifestyle", notes.lifestyle_notes)
    _text(lines, "Family history", notes.family_history_notes)
    _text(lines, "Medication concerns", notes.medication_concerns)
    _text(lines, "Pain patterns", notes.pain_patterns)
    _text(lines, "Mental health", notes.mental_health_notes)
    _list(lines, "⛑ FLAGS", notes.important_flags)
    _text(lines, "Follow up on", notes.key_concerns)
    _text(lines, "Last session", notes.last_summary)
    _text(lines, "Notes", notes.raw_notes)
    return "\n".join(lines)


def _list(acc: list[str], label: str, values) -> None:
    if values:
        acc.append(f"{label}: {', '.join(str(v) for v in values)}")


def _text(acc: list[str], label: str, value) -> None:
    if value:
        acc.append(f"{label}: {value}")
