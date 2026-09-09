"""
Text normalisation for scoring.

Two levels:

* ``normalize()`` — the light, universally-defensible pass used for the
  headline WER/CER: lower-case, strip the ``[[EN]]`` span tags, drop
  punctuation, collapse whitespace, remove the ``[Speaker N]`` turn markers
  that AfriSwitchCare puts in its reference transcripts (no ASR model is
  expected to emit those).

* ``normalize_strict()`` — additionally spells out digits and maps a small
  table of spelling variants (``bp`` → ``blood pressure`` etc.). Reported
  alongside as "normalised WER" so a reader can see how much of the error is
  formatting vs. genuine mis-recognition.

Nothing here is language-specific — it must treat Yoruba, Hausa, Igbo,
Pidgin and Swahili identically, or the cross-language comparison breaks.
"""

from __future__ import annotations

import re

_SPEAKER_RE = re.compile(r"\[speaker\s*\d+\]", re.I)
_EN_TAG_RE = re.compile(r"\[\[/?en\]\]", re.I)
_TAG_RE = re.compile(r"\[\[/?[a-z]{2,3}\]\]", re.I)

# AfriSwitchCare transcripts carry annotator notes that leaked into the text:
#   "... is it gradual code switch > sudden ...", "Weight loss hausa> din ...",
#   "Gaisuwa English> sir ...". No ASR model emits these, so strip them from
#   the reference before scoring (applied to hypotheses too — harmless there).
_ANNOT_RE = re.compile(
    r"<?\s*/?\s*\b(?:english|eng|hausa|yoruba|yor|igbo|ibo|pidgin|pcm|swahili|swa|french|fra|"
    r"matrix|native|local)\b\s*>",
    re.I,
)
# bare "code switch" / "code-switching" note that leaked in without an angle bracket
_ANNOT_PHRASE_RE = re.compile(r"\bcode[\s-]*switch(?:ing|ed|es)?\b", re.I)
_STRAY_ANGLE_RE = re.compile(r"\s*[<>]+\s*")
_PUNCT_RE = re.compile(r"[^\w\s'̀-ͯɐ-ʯ]", re.U)  # keep combining marks
_WS_RE = re.compile(r"\s+")

_NUM_WORDS = {
    "0": "zero", "1": "one", "2": "two", "3": "three", "4": "four",
    "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine",
    "10": "ten", "11": "eleven", "12": "twelve", "13": "thirteen",
    "14": "fourteen", "15": "fifteen", "16": "sixteen", "17": "seventeen",
    "18": "eighteen", "19": "nineteen", "20": "twenty", "30": "thirty",
    "40": "forty", "50": "fifty", "60": "sixty", "70": "seventy",
    "80": "eighty", "90": "ninety", "100": "hundred", "1000": "thousand",
}

_VARIANTS = {
    "bp": "blood pressure",
    "temp": "temperature",
    "temperature's": "temperature",
    "meds": "medicine",
    "medication": "medicine",
    "medications": "medicine",
    "tabs": "tablets",
    "tab": "tablet",
    "&": "and",
    "o'clock": "oclock",
    "doctor's": "doctor",
    "dont": "do not",
    "don't": "do not",
    "cant": "can not",
    "can't": "can not",
    "wont": "will not",
    "won't": "will not",
    "im": "i am",
    "i'm": "i am",
    "ive": "i have",
    "i've": "i have",
    "youre": "you are",
    "you're": "you are",
    "its": "it is",
    "it's": "it is",
}


def strip_tags(text: str) -> str:
    return _TAG_RE.sub("", text or "")


def normalize(text: str) -> str:
    """Light normalisation — the headline WER/CER pass."""
    t = (text or "").lower()
    t = _EN_TAG_RE.sub(" ", t)
    t = _TAG_RE.sub(" ", t)
    t = _SPEAKER_RE.sub(" ", t)
    t = _ANNOT_RE.sub(" ", t)
    t = _ANNOT_PHRASE_RE.sub(" ", t)
    t = _STRAY_ANGLE_RE.sub(" ", t)
    t = t.replace("’", "'").replace("‘", "'").replace("`", "'")
    t = _PUNCT_RE.sub(" ", t)
    t = _WS_RE.sub(" ", t).strip()
    return t


def _spell_number(tok: str) -> str:
    if tok in _NUM_WORDS:
        return _NUM_WORDS[tok]
    if tok.isdigit() and len(tok) == 2 and tok[1] != "0":
        tens, ones = tok[0] + "0", tok[1]
        if tens in _NUM_WORDS and ones in _NUM_WORDS:
            return f"{_NUM_WORDS[tens]} {_NUM_WORDS[ones]}"
    return tok


def normalize_strict(text: str) -> str:
    """Light pass + digit spell-out + a small variant table."""
    toks = normalize(text).split()
    out: list[str] = []
    for tok in toks:
        tok = _VARIANTS.get(tok, tok)
        if any(ch.isdigit() for ch in tok):
            tok = re.sub(r"\d+", lambda m: _spell_number(m.group()), tok)
        out.extend(tok.split())
    return " ".join(out)


def tokens(text: str, *, strict: bool = False) -> list[str]:
    return (normalize_strict(text) if strict else normalize(text)).split()
