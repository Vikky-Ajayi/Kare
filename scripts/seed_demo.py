"""
Seed four synthetic demo patients with code-switched histories.

Run:  python -m scripts.seed_demo           (idempotent; upserts by email)
      python -m scripts.seed_demo --wipe    (delete demo users first)

These are fictional. Real testing happens on your own account and stays private.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timedelta

from app.database import SessionLocal
from app.models import (
    Conversation,
    ConversationMessage,
    MedicalCondition,
    Medication,
    Patient,
    PatientHealthNotes,
    User,
)
from app.utils.security import hash_password

DEMO_PASSWORD = "demo-kare-2026"
DEMO_DOMAIN = "@demo.kare.health"


def _years_ago(years: int) -> date:
    today = date.today()
    return today.replace(year=today.year - years)


PERSONAS = [
    {
        "email": f"tayo{DEMO_DOMAIN}",
        "first_name": "Tayo", "last_name": "Bello",
        "language": "pcm", "gender": "male", "state": "Lagos",
        "dob": _years_ago(34), "blood_group": "O+",
        "height_cm": 176, "weight_kg": 88, "allergies": [],
        "conditions": [
            {"condition_name": "Hypertension", "status": "chronic",
             "diagnosed_date": _years_ago(3), "icd10_code": "I10"},
        ],
        "medications": [
            {"drug_name": "Amlodipine", "dosage": "5mg", "frequency": "once daily",
             "route": "oral", "status": "active"},
        ],
        "notes": {
            "presenting_complaints": ["tension headache", "fever (malaria, treated)"],
            "suspected_conditions": ["poorly controlled hypertension"],
            "medication_concerns": "Sometimes skips amlodipine on weekends.",
            "pain_patterns": "Band-like headache, worse in the afternoon, both temples.",
            "important_flags": ["BP not checked in 4 months"],
            "key_concerns": "Confirm BP control; headache may be BP-related.",
            "conversation_count": 2,
        },
        "last_convo": [
            ("user", "Doctor, this headache no gree leave me since. My eye dey do me somehow."),
            ("assistant", "Sorry about the headache, Tayo. How long you don dey feel am like this, "
                          "and you don check your blood pressure recently? Any change for your amlodipine?"),
            ("user", "I never check am for like four months. I dey take the medicine but sometimes weekend I forget."),
            ("assistant", "Thank you for being honest. Missing weekend doses fit make the pressure swing, "
                          "and that fit cause this kind headache. Try get your BP checked this week — "
                          "any chemist or clinic near you fit do am. If the headache come with blurred vision, "
                          "chest pain, or weakness for one side of your body, go hospital straight."),
        ],
    },
    {
        "email": f"amina{DEMO_DOMAIN}",
        "first_name": "Amina", "last_name": "Sani",
        "language": "ha", "gender": "female", "state": "Kano",
        "dob": _years_ago(28), "blood_group": "A+",
        "height_cm": 162, "weight_kg": 64, "allergies": ["penicillin"],
        "conditions": [
            {"condition_name": "Iron-deficiency anaemia of pregnancy", "status": "active",
             "diagnosed_date": date.today() - timedelta(days=40), "icd10_code": "O99.01"},
        ],
        "medications": [
            {"drug_name": "Ferrous sulfate", "dosage": "200mg", "frequency": "twice daily",
             "route": "oral", "status": "active"},
            {"drug_name": "Folic acid", "dosage": "5mg", "frequency": "once daily",
             "route": "oral", "status": "active"},
        ],
        "notes": {
            "presenting_complaints": ["light spotting (week 22, resolved)", "lower back pain", "fatigue"],
            "suspected_conditions": ["iron-deficiency anaemia"],
            "lifestyle_notes": "Craving oranges. Sleeping poorly — up several times at night.",
            "medication_concerns": "Ferrous sulfate upsets her stomach; takes it inconsistently.",
            "pain_patterns": "Dull lower-back ache, worse after standing to cook.",
            "important_flags": ["had spotting at ~22 weeks — watch for recurrence"],
            "key_concerns": "Follow up spotting, iron adherence, back pain, and rest.",
            "conversation_count": 3,
        },
        "pregnant": True,
        "last_convo": [
            ("user", "Likita, ina jin zafi a kasan bayana, kuma jiya na ga dan jini kadan."),
            ("assistant", "Na gode da ka gaya mini, Amina. The small bleeding you saw yesterday — how much was it, "
                          "and has it stopped now? Any cramping or pain with it? And how's our baby moving today?"),
            ("user", "Ya tsaya yau. Babu ciwo sosai, kadan kawai. Jaririn yana motsi."),
            ("assistant", "Good — it stopped and the baby is moving, that's reassuring. Still, any spotting in "
                          "pregnancy is worth telling your antenatal clinic, so please mention it at your next visit "
                          "or sooner if it comes back heavier. For the back pain, a warm compress and resting on your "
                          "side can help. Are you managing to take the iron tablets?"),
            ("user", "Iron din yana damun cikina, so ba na sha kullum."),
            ("assistant", "That's common. Try taking it with food and a little orange — the vitamin C helps you "
                          "absorb it, and I know you like oranges. If it still upsets you, tell the clinic; there are "
                          "gentler forms. Watch for: heavier bleeding, strong cramps, fever, or the baby moving less "
                          "than usual — any of those, go to the hospital straight away."),
        ],
    },
    {
        "email": f"chidi{DEMO_DOMAIN}",
        "first_name": "Chidi", "last_name": "Okonkwo",
        "language": "ig", "gender": "male", "state": "Enugu",
        "dob": _years_ago(45), "blood_group": "B+",
        "height_cm": 170, "weight_kg": 79, "allergies": [],
        "conditions": [
            {"condition_name": "Type 2 diabetes mellitus", "status": "chronic",
             "diagnosed_date": _years_ago(6), "icd10_code": "E11"},
            {"condition_name": "Diabetic peripheral neuropathy", "status": "active",
             "diagnosed_date": _years_ago(1), "icd10_code": "E11.42"},
        ],
        "medications": [
            {"drug_name": "Metformin", "dosage": "1000mg", "frequency": "twice daily",
             "route": "oral", "status": "active"},
        ],
        "notes": {
            "presenting_complaints": ["tingling and numbness in both feet", "occasional dizziness"],
            "suspected_conditions": ["worsening diabetic neuropathy", "possible hypoglycaemia episodes"],
            "medication_concerns": "Runs out of metformin before refills; checks sugar rarely.",
            "important_flags": ["numb feet — foot-care and injury-check needed"],
            "key_concerns": "Glycaemic control, metformin supply, foot checks, dizziness cause.",
            "conversation_count": 4,
        },
        "last_convo": [
            ("user", "Dọkịta, ụkwụ m abụọ na-ekpo ọkụ ma na-agba m, ọ na-akawanye njọ n'abalị."),
            ("assistant", "Ndo, Chidi. Burning and tingling in both feet that's worse at night often points to the "
                          "nerve changes from diabetes. When did you last check your blood sugar, and are you getting "
                          "your metformin without gaps?"),
            ("user", "M na-echecha ya mgbe m ga-ahụ ego. Ọ na-agwụ m tupu m enweta ọzọ."),
            ("assistant", "Running out matters — the gaps let your sugar climb and that speeds up the nerve damage. "
                          "Let's fix the supply first. Also check your feet every night for cuts or blisters you can't "
                          "feel, and never walk barefoot. If you see a wound that won't heal, or the dizziness comes "
                          "with sweating and shaking, that could be low sugar — treat it and get seen."),
        ],
    },
    {
        "email": f"ngozi{DEMO_DOMAIN}",
        "first_name": "Ngozi", "last_name": "Eze",
        "language": "en", "gender": "female", "state": "Imo",
        "dob": _years_ago(52), "blood_group": "O-",
        "height_cm": 158, "weight_kg": 82, "allergies": ["sulfa drugs"],
        "conditions": [
            {"condition_name": "Osteoarthritis, both knees", "status": "chronic",
             "diagnosed_date": _years_ago(2), "icd10_code": "M17.0"},
            {"condition_name": "Hypertension", "status": "chronic",
             "diagnosed_date": _years_ago(4), "icd10_code": "I10"},
        ],
        "medications": [
            {"drug_name": "Ibuprofen", "dosage": "400mg", "frequency": "as needed for pain",
             "route": "oral", "status": "as_needed"},
            {"drug_name": "Paracetamol", "dosage": "1g", "frequency": "three times daily",
             "route": "oral", "status": "active"},
            {"drug_name": "Lisinopril", "dosage": "10mg", "frequency": "once daily",
             "route": "oral", "status": "active"},
        ],
        "notes": {
            "presenting_complaints": ["knee pain climbing stairs", "morning stiffness"],
            "suspected_conditions": ["osteoarthritis flare"],
            "medication_concerns": "Uses ibuprofen most days for the knees — also on lisinopril for BP.",
            "family_history_notes": "Mother had a stroke at 60.",
            "important_flags": ["frequent NSAID use with hypertension + ACE inhibitor — interaction risk"],
            "key_concerns": "Review ibuprofen frequency against her BP meds; safer pain plan.",
            "conversation_count": 2,
        },
        "last_convo": [
            ("user", "My knees have been really bad this week, especially on the stairs. I've been taking "
                     "ibuprofen almost every day."),
            ("assistant", "I'm sorry the knees are flaring, Ngozi. Taking ibuprofen most days is the part I want to "
                          "look at — with your blood pressure and the lisinopril, regular ibuprofen can push your "
                          "pressure up and stress your kidneys. How many days this week, and roughly how many tablets "
                          "a day?"),
            ("user", "Maybe five days, two tablets each day. It's the only thing that helps."),
            ("assistant", "Understood — let's get you a plan that works without leaning on it daily. Regular "
                          "paracetamol around the clock, a warm compress, gentle strengthening, and keeping ibuprofen "
                          "for the worst days only. Please have your blood pressure checked this week. If you notice "
                          "swelling in your ankles, much less urine, or stomach pain, stop the ibuprofen and get seen."),
        ],
    },
]


def _upsert(db, p: dict) -> None:
    user = db.query(User).filter(User.email == p["email"]).first()
    if not user:
        user = User(email=p["email"], hashed_password=hash_password(DEMO_PASSWORD),
                    preferred_language=p["language"], is_active=True, is_verified=True)
        db.add(user)
        db.flush()
    patient = db.query(Patient).filter(Patient.user_id == user.id).first()
    if not patient:
        patient = Patient(user_id=user.id, first_name=p["first_name"], last_name=p["last_name"])
        db.add(patient)
        db.flush()

    patient.date_of_birth = p["dob"]
    patient.gender = p["gender"]
    patient.state = p["state"]
    patient.country = "Nigeria"
    patient.blood_group = p["blood_group"]
    patient.height_cm = p["height_cm"]
    patient.weight_kg = p["weight_kg"]
    patient.allergies = p["allergies"]

    # conditions / meds — replace wholesale for idempotency
    db.query(MedicalCondition).filter(MedicalCondition.patient_id == patient.id).delete()
    db.query(Medication).filter(Medication.patient_id == patient.id).delete()
    for c in p["conditions"]:
        db.add(MedicalCondition(patient_id=patient.id, **c))
    for m in p["medications"]:
        db.add(Medication(patient_id=patient.id, **m))

    notes = db.query(PatientHealthNotes).filter(
        PatientHealthNotes.patient_id == patient.id).first()
    if not notes:
        notes = PatientHealthNotes(patient_id=patient.id)
        db.add(notes)
    for k, v in p["notes"].items():
        setattr(notes, k, v)
    notes.updated_at = datetime.utcnow()

    # one prior conversation so "the doctor remembers you" is visible on day one
    db.query(Conversation).filter(
        Conversation.user_id == user.id,
        Conversation.summary == "seed",
    ).delete(synchronize_session=False)
    convo = Conversation(user_id=user.id, language=p["language"],
                         status="completed", summary="seed",
                         started_at=datetime.utcnow() - timedelta(days=1),
                         ended_at=datetime.utcnow() - timedelta(days=1))
    db.add(convo)
    db.flush()
    base = datetime.utcnow() - timedelta(days=1)
    for i, (role, content) in enumerate(p["last_convo"]):
        db.add(ConversationMessage(conversation_id=convo.id, role=role, content=content,
                                   language=p["language"], created_at=base + timedelta(minutes=i)))

    print(f"  seeded {p['first_name']} {p['last_name']} ({p['language']})"
          + ("  [pregnant]" if p.get("pregnant") else ""))


def wipe(db) -> None:
    users = db.query(User).filter(User.email.like(f"%{DEMO_DOMAIN}")).all()
    for u in users:
        db.delete(u)
    db.commit()
    print(f"wiped {len(users)} demo users")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wipe", action="store_true")
    args = ap.parse_args()

    db = SessionLocal()
    try:
        if args.wipe:
            wipe(db)
            return
        print("seeding demo patients:")
        for p in PERSONAS:
            _upsert(db, p)
        db.commit()
        print(f"\ndone. login with any {DEMO_DOMAIN} email, password: {DEMO_PASSWORD}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
