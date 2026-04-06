"""
Miscellaneous helper utilities.
"""

import re
from datetime import datetime
from typing import Optional


def calculate_age(date_of_birth) -> Optional[int]:
    """Calculate age from date of birth."""
    if not date_of_birth:
        return None
    today = datetime.today().date()
    age = today.year - date_of_birth.year
    if (today.month, today.day) < (date_of_birth.month, date_of_birth.day):
        age -= 1
    return age


def calculate_bmi(height_cm: Optional[float], weight_kg: Optional[float]) -> Optional[float]:
    """Calculate BMI from height (cm) and weight (kg)."""
    if not height_cm or not weight_kg:
        return None
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 1)


def sanitize_text(text: str) -> str:
    """Basic text sanitization — strip extra whitespace."""
    return re.sub(r"\s+", " ", text.strip())


def format_drug_name(name: str) -> str:
    """Normalize drug name for API lookups."""
    return name.strip().lower().replace("-", " ")


MEDICAL_DISCLAIMER = (
    "⚠️ DISCLAIMER: This information is for educational purposes only and does NOT "
    "constitute medical advice. Always consult a qualified healthcare professional "
    "before making any medical decisions. In an emergency, call your local emergency number."
)

LANGUAGE_DISCLAIMERS = {
    "en": MEDICAL_DISCLAIMER,
    "fr": (
        "⚠️ AVERTISSEMENT: Ces informations sont à titre éducatif seulement et ne constituent "
        "PAS un avis médical. Consultez toujours un professionnel de santé qualifié."
    ),
    "yo": (
        "⚠️ IKILO: Alaye yii jẹ fun ẹkọ nikan ko si jẹ imọran iṣoogun. "
        "Jọwọ kan si dokita ṣaaju ṣiṣe ipinnu iṣoogun eyikeyi."
    ),
    "ha": (
        "⚠️ GARGAƊI: Wannan bayani don ilimi ne kawai kuma ba shawara ta likita ba. "
        "Koyaushe tuntuɓi ƙwararren ma'aikacin lafiya."
    ),
    "ig": (
        "⚠️ ỌCHỊCHỌ: Ozi a bụ maka nkuzi naanị ma ọ bụghị ndụmọdụ ọgwụgwọ. "
        "Jide n'aka na ị gakọọ onye ọkachamara ahụike."
    ),
    "pcm": (
        "⚠️ WARNING: Dis information na for learning purpose only, e no be medical advice. "
        "Abeg always see doctor before you do any medical decision."
    ),
}


def get_disclaimer(language: str = "en") -> str:
    return LANGUAGE_DISCLAIMERS.get(language, MEDICAL_DISCLAIMER)
