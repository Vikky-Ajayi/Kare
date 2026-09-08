"""
Deterministic danger-sign check that runs BEFORE the consultation agent.

Two stages: a fast multilingual keyword pre-filter (people usually say the
symptom word in English even mid-Yoruba/Hausa/Igbo), then a small-model
classifier for phrasings the keywords miss. Either firing routes the turn to
the escalation response instead of the normal agent loop.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from app.config import settings
from app.providers import get_llm

log = logging.getLogger("kare.redflags")

# ── keyword pre-filter ────────────────────────────────────────────────
# Loose on purpose — matches code-switched / Pidgin phrasing
# ("chest dey pain me", "e hard for me to breathe", "I no fit breathe").
_GENERAL = [
    r"chest\b.{0,20}\b(pain|hurt|tight|heavy|press|dey pain)",
    r"\b(pain|hurt|tight|heavy)\b.{0,15}\bchest",
    r"\bcrush\w*\b.{0,20}chest",
    r"(can'?t|cannot|no fit|hard|difficult|struggl\w*|fail).{0,15}breath",
    r"breath\w*.{0,15}(hard|difficult|fast|heavy|problem)",
    r"short\w*\s+of\s+breath", r"out of breath", r"catch my breath",
    r"\bgasp\w*", r"\bchok\w*", r"not breathing", r"stopped breathing",
    r"turning blue", r"blue lips", r"lips.{0,10}blue",
    r"face\b.{0,15}(droop|drop|twist|crook)", r"one side.{0,20}(weak|numb|droop|paraly)",
    r"can'?t move (my )?(arm|leg|face|one side)", r"slur\w*\s+speech", r"speech.{0,10}slur",
    r"worst headache", r"(sudden|severe).{0,15}headache.{0,15}(ever|life|bad)",
    r"thunderclap", r"stiff neck.{0,20}fever", r"neck.{0,10}stiff.{0,20}fever",
    r"pass\w* out", r"faint\w*", r"black\w* out", r"collaps\w*",
    r"unconscious", r"unresponsive", r"won'?t wake",
    r"seizure", r"convuls\w*", r"fitting", r"\bfit\b.{0,10}(now|just|again)", r"jerking",
    r"cough\w*.{0,10}blood", r"vomit\w*.{0,10}blood", r"blood.{0,10}(vomit|stool|poo|urine|wee)",
    r"throwing up blood", r"spitting blood",
    r"(heavy|severe|serious|plenty).{0,10}bleed", r"bleed\w*.{0,15}(a lot|badly|plenty|won'?t stop|no stop|heavy)",
    r"won'?t stop bleeding", r"blood no dey stop", r"losing (a lot of )?blood",
    r"severe.{0,10}(abdominal|stomach|belly|tummy).{0,5}pain", r"can'?t stop vomiting",
    r"suicid\w*", r"kill myself", r"end (my|it all)", r"harm myself", r"don'?t want to live",
    r"want to die", r"no reason to live",
    r"snake\s?bite", r"bitten by (a )?snake", r"\bpoison\w*", r"overdos\w*", r"took too many",
    r"drank\b.{0,20}(chemical|acid|kerosene|petrol|rat)",
]
_PREGNANCY = [
    r"bleed\w*.{0,25}(pregnan|baby|belly|down there|private)", r"vaginal bleed",
    r"bleeding down there", r"blood.{0,15}(pregnan|baby|vagina)",
    r"(spot\w*|blood|bleed\w*).{0,20}(pant|pad|underwear|knicker|pant\w*|panties)",
    r"(pant|pad|underwear).{0,20}(spot\w*|blood|bleed\w*)",
    r"water\w*.{0,10}(broke|break|burst|comot)", r"fluid.{0,10}(leak|gush|comot)", r"waters broke",
    r"baby\b.{0,25}(not|no|never|hasn.?t|stopped|less|reduced?|isn.?t).{0,12}(mov|kick|active)",
    r"(mov|kick).{0,20}\bbaby",
    r"(not|no|never|can'?t|hasn.?t|reduced?).{0,12}(feel|felt).{0,12}(the )?(baby|kick|movement)",
    r"(no|not|reduced?|less).{0,10}(fetal|baby)\s*(movement|kick)",
    r"baby (is |dey |don )?(too )?(still|quiet)",
    r"blur\w*\s+vision.{0,25}(swell|headache|pregnan)", r"seeing spots",
    r"severe headache.{0,25}(swell|vision|pregnan)",
    r"contraction\w*.{0,20}(early|preterm|weeks|\d)", r"labou?r.{0,15}(early|preterm|too soon)",
]

_GENERAL_RE = re.compile("|".join(f"(?:{p})" for p in _GENERAL), re.IGNORECASE)
_PREGNANCY_RE = re.compile("|".join(f"(?:{p})" for p in _PREGNANCY), re.IGNORECASE)

_CLASSIFIER = """You are a triage safety net. Decide if the patient's latest message describes a
possible MEDICAL EMERGENCY / danger sign that needs same-hour in-person care.
Danger signs include: chest pain or tightness, trouble breathing, one-sided weakness or
face droop, slurred speech, sudden severe headache, stiff neck with fever, fainting,
seizure, coughing/vomiting blood, heavy bleeding, severe abdominal pain, thoughts of
self-harm, poisoning or overdose, snake bite; and in pregnancy: vaginal bleeding, waters
breaking, reduced or absent fetal movement, severe headache with vision changes or
swelling, preterm contractions.
The message may mix English with Yoruba, Hausa, Igbo, or Pidgin — judge the meaning.
Return ONLY JSON: {"emergency": true|false, "category": "short label", "reason": "one short phrase"}"""


@dataclass
class RedFlag:
    triggered: bool
    category: str = ""
    reason: str = ""
    source: str = ""  # "keyword" | "classifier"


def keyword_check(message: str, *, pregnant: bool = False) -> RedFlag | None:
    """Instant, free. Returns a RedFlag on a clear match, else None."""
    m = _GENERAL_RE.search(message)
    if m:
        return RedFlag(True, "general danger sign", m.group(0), "keyword")
    if pregnant:
        m = _PREGNANCY_RE.search(message)
        if m:
            return RedFlag(True, "pregnancy danger sign", m.group(0), "keyword")
    return None


async def classifier_check(message: str) -> RedFlag:
    """The small-model backstop for phrasings the keywords miss."""
    try:
        resp = await get_llm().complete(
            [
                {"role": "system", "content": _CLASSIFIER},
                {"role": "user", "content": message},
            ],
            model=settings.GROQ_LLM_MODEL_FAST,
            temperature=0.0,
            max_tokens=200,
            json_mode=True,
            reasoning_effort="low",
        )
        data = json.loads(resp.content.strip() or "{}")
    except Exception as exc:  # noqa: BLE001
        log.warning("red-flag classifier failed (failing safe = no flag): %s", exc)
        return RedFlag(False)

    if data.get("emergency") is True:
        return RedFlag(True, data.get("category", "danger sign"),
                       data.get("reason", ""), "classifier")
    return RedFlag(False)


async def check(message: str, *, pregnant: bool = False) -> RedFlag:
    """Serial convenience wrapper (keyword then classifier)."""
    return keyword_check(message, pregnant=pregnant) or await classifier_check(message)
