"""
Structured one-shot Groq calls used outside the consultation loop:
symptom triage, medical-image analysis, and translation.

The consultation turn lives in app.services.consultation; context builders live
in app.services.context (re-exported here for existing imports).
"""

from __future__ import annotations

import base64
import json
import logging
import re

from app.config import settings
from app.providers import get_llm
from app.services.context import (  # noqa: F401  (back-compat re-export)
    build_health_notes_context,
    build_patient_context,
)

log = logging.getLogger("kare.groq")

SYMPTOM_CHECK_PROMPT = """You are a medical triage assistant for Nigeria and West Africa.
Analyse the symptoms and return ONLY a JSON object:
{
  "symptoms_identified": ["symptom"],
  "triage_level": "EMERGENCY | URGENT | SEMI_URGENT | NON_URGENT | SELF_CARE",
  "triage_explanation": "one or two plain sentences",
  "possible_conditions": [{"condition": "Name", "likelihood": "high|medium|low", "icd10": "code or null"}],
  "recommendations": "clear, actionable advice",
  "when_to_seek_emergency": "specific warning signs that mean go to hospital now",
  "follow_up_questions": ["question that would sharpen the assessment"]
}
Think malaria, typhoid, TB, sickle cell, hypertension, diabetes, maternal health first.
Return ONLY the JSON."""

IMAGE_PROMPT = """You analyse a medical image. Return ONLY a JSON object:
{
  "image_content": "what is visible",
  "medical_observations": ["observation"],
  "possible_conditions": ["condition"],
  "urgency": "none|low|medium|high|emergency",
  "recommendations": "what the patient should do",
  "confidence": "low|medium|high",
  "limitations": "what cannot be judged from an image"
}
Return ONLY the JSON."""

# Separate from IMAGE_PROMPT: a pill/box/blister-pack photo needs fields that
# map onto an "add medication" form (drug_name, strength -> dosage), not the
# symptom-shaped schema above (urgency/possible_conditions make no sense for
# a photo of packaging).
MEDICATION_IMAGE_PROMPT = """You identify a medication from a photo of the pill, \
blister pack, or box. Return ONLY a JSON object:
{
  "drug_name": "brand name as printed, or null if unreadable",
  "generic_name": "active ingredient / generic name, or null",
  "strength": "e.g. '500mg', or null if not visible",
  "form": "tablet|capsule|syrup|injection|cream|other, or null",
  "common_use": "one plain sentence on what it's typically prescribed for, or null",
  "warnings": "anything notable to flag — e.g. 'packaging partially obscured, verify with a pharmacist' — or null",
  "confidence": "low|medium|high"
}
If you cannot identify the medication with reasonable confidence, set drug_name to null and \
confidence to "low" rather than guessing. Return ONLY the JSON."""


def _loads(raw: str) -> dict:
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        return json.loads(m.group()) if m else {}


async def translate_text(text: str, source: str, target: str) -> str:
    if source == target or not text:
        return text
    names = settings.LANGUAGE_NAMES
    resp = await get_llm().complete(
        [
            {"role": "system", "content": (
                f"Translate from {names.get(source, source)} to {names.get(target, target)}. "
                "Preserve medical meaning exactly. Return ONLY the translation."
            )},
            {"role": "user", "content": text},
        ],
        model=settings.GROQ_LLM_MODEL_FAST,
        temperature=0.1,
        max_tokens=1500,
        reasoning_effort="low",
    )
    return resp.content.strip()


async def analyze_symptoms(symptoms_text: str, language: str = "en", patient_context: str = "") -> dict:
    text = symptoms_text
    if language != "en":
        text = await translate_text(symptoms_text, source=language, target="en")

    system = SYMPTOM_CHECK_PROMPT
    if patient_context:
        system += f"\n\nPATIENT FILE:\n{patient_context}"

    resp = await get_llm().complete(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Symptoms: {text}"},
        ],
        temperature=0.1,
        max_tokens=1200,
        json_mode=True,
        reasoning_effort="low",
    )
    result = _loads(resp.content)

    if language != "en":
        for field in ("recommendations", "triage_explanation", "when_to_seek_emergency"):
            if result.get(field):
                result[field] = await translate_text(result[field], source="en", target=language)
    return result


async def analyze_image(image_bytes: bytes, image_type: str = "symptom") -> dict:
    from groq import AsyncGroq

    client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    b64 = base64.b64encode(image_bytes).decode()
    mime = "image/png" if image_bytes[:8] == b"\x89PNG\r\n\x1a\n" else "image/jpeg"
    ask = {
        "symptom": "Analyse this visible symptom (rash, wound, swelling, eye, skin).",
        "medication": "Identify this medication — name, strength, markings.",
        "document": "Extract and summarise the medical information shown.",
    }.get(image_type, "Analyse this medical image.")
    system_prompt = MEDICATION_IMAGE_PROMPT if image_type == "medication" else IMAGE_PROMPT

    resp = await client.chat.completions.create(
        model=settings.GROQ_VISION_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                {"type": "text", "text": ask},
            ]},
        ],
        temperature=0.1,
        max_tokens=900,
    )
    raw = (resp.choices[0].message.content or "").strip()
    parsed = _loads(raw)
    if parsed:
        return parsed
    if image_type == "medication":
        return {
            "drug_name": None, "generic_name": None, "strength": None, "form": None,
            "common_use": None, "confidence": "low",
            "warnings": raw or "Could not read the image — please enter the details manually.",
        }
    return {
        "medical_observations": [raw] if raw else [],
        "urgency": "low", "confidence": "low",
        "recommendations": "Please see a healthcare professional for proper evaluation.",
        "limitations": "Structured analysis was unavailable.",
    }
