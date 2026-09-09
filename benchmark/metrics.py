"""
Scoring for the code-switching ASR benchmark.

Headline
    wer / cer            — light normalisation (see normalize.py)
    wer_strict           — + digit spell-out + variant table

Code-switching fidelity (the reason this benchmark exists)
    cmi_ref / cmi_hyp    — Code-Mixing Index, Gambäck & Das (2016), computed
                           from the [[EN]] spans on the reference and from an
                           English-dictionary tag on the hypothesis
    cmi_abs_err          — |cmi_ref - cmi_hyp|
    switch_ref / switch_hyp
    switch_count_err     — |switch_ref - switch_hyp|
    en_recall / en_prec  — token-level: did English words that were spoken
                           survive transcription, and were they really English

Clinical salience
    keyterm_recall       — fraction of medical terms in the reference that
                           appear in the hypothesis
    number_recall        — same for spoken numbers / dosages

All alignment is word-level Levenshtein (jiwer if present, else a local
implementation) on the lightly-normalised token streams.
"""

from __future__ import annotations

import functools
import re
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

from benchmark.normalize import normalize, normalize_strict, strip_tags

# ── English lexicon for hypothesis-side code-switch tagging ───────────────
_DICT_PATHS = ["/usr/share/dict/words", "/usr/share/dict/web2"]
_FUNCTION_WORDS = {
    "the", "a", "an", "and", "or", "but", "if", "so", "of", "to", "in", "on",
    "at", "for", "with", "as", "by", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would", "can",
    "could", "should", "may", "might", "must", "i", "you", "he", "she", "it",
    "we", "they", "me", "him", "her", "us", "them", "my", "your", "his", "our",
    "their", "this", "that", "these", "those", "not", "no", "yes", "ok", "okay",
    "now", "then", "here", "there", "how", "what", "when", "where", "why", "who",
}
# short tokens that also exist as words in other languages — don't treat as EN
_AMBIGUOUS_SHORT = {"a", "i", "o", "e", "so", "no", "we", "he", "me", "to", "in",
                    "on", "an", "as", "at", "be", "by", "do", "go", "is", "it",
                    "of", "or", "up", "us"}


@functools.lru_cache(maxsize=1)
def _english_words() -> frozenset[str]:
    words: set[str] = set(_FUNCTION_WORDS)
    for p in _DICT_PATHS:
        fp = Path(p)
        if fp.exists():
            for line in fp.read_text(errors="ignore").splitlines():
                w = line.strip().lower()
                if w.isalpha():
                    words.add(w)
            break
    return frozenset(words)


def is_english_token(tok: str) -> bool:
    tok = tok.strip("'").lower()
    if not tok or not tok.isalpha():
        return False
    if tok in _AMBIGUOUS_SHORT:
        return False
    if len(tok) <= 2:
        return tok in _FUNCTION_WORDS
    return tok in _english_words()


# ── code-mixing index ────────────────────────────────────────────────────
_EN_SPAN_RE = re.compile(r"\[\[en\]\](.*?)\[\[/en\]\]", re.I | re.S)


def _lang_labels_from_tags(tagged: str) -> list[int]:
    """1 = English, 0 = matrix, for each word of the *reference*."""
    labels: list[int] = []
    pos = 0
    for m in _EN_SPAN_RE.finditer(tagged or ""):
        pre = normalize(tagged[pos:m.start()])
        labels += [0] * len(pre.split())
        en = normalize(m.group(1))
        labels += [1] * len(en.split())
        pos = m.end()
    tail = normalize(tagged[pos:])
    labels += [0] * len(tail.split())
    return labels


def _lang_labels_from_dict(text: str) -> list[int]:
    return [1 if is_english_token(t) else 0 for t in normalize(text).split()]


def cmi(labels: list[int]) -> float:
    """Gambäck & Das (2016), utterance level, binary matrix/embedded case.
    100 * (1 - max(n_matrix, n_en) / n_tokens); 0 for a monolingual utterance."""
    n = len(labels)
    if n == 0:
        return 0.0
    n_en = sum(labels)
    n_mx = n - n_en
    if n_en == 0 or n_mx == 0:
        return 0.0
    return 100.0 * (1.0 - max(n_en, n_mx) / n)


def switch_points(labels: list[int]) -> int:
    return sum(1 for i in range(1, len(labels)) if labels[i] != labels[i - 1])


def cmi_from_tags(tagged: str) -> float:
    """Gold CMI straight from a ``transcription_tagged`` string."""
    return cmi(_lang_labels_from_tags(tagged))


def switch_points_from_tags(tagged: str) -> int:
    return switch_points(_lang_labels_from_tags(tagged))


# ── word alignment ───────────────────────────────────────────────────────
@dataclass
class _Align:
    ops: list[tuple[str, str | None, str | None]]  # (op, ref, hyp)
    sub: int
    ins: int
    dele: int
    hits: int


def _align(ref: list[str], hyp: list[str]) -> _Align:
    try:
        import jiwer

        out = jiwer.process_words([" ".join(ref)], [" ".join(hyp)])
        ops: list[tuple[str, str | None, str | None]] = []
        s = i = d = h = 0
        for chunk in out.alignments[0]:
            if chunk.type == "equal":
                for k in range(chunk.ref_end_idx - chunk.ref_start_idx):
                    ops.append(("equal", ref[chunk.ref_start_idx + k], hyp[chunk.hyp_start_idx + k]))
                    h += 1
            elif chunk.type == "substitute":
                for k in range(chunk.ref_end_idx - chunk.ref_start_idx):
                    ops.append(("sub", ref[chunk.ref_start_idx + k], hyp[chunk.hyp_start_idx + k]))
                    s += 1
            elif chunk.type == "delete":
                for k in range(chunk.ref_end_idx - chunk.ref_start_idx):
                    ops.append(("del", ref[chunk.ref_start_idx + k], None))
                    d += 1
            elif chunk.type == "insert":
                for k in range(chunk.hyp_end_idx - chunk.hyp_start_idx):
                    ops.append(("ins", None, hyp[chunk.hyp_start_idx + k]))
                    i += 1
        return _Align(ops, s, i, d, h)
    except Exception:
        return _align_local(ref, hyp)


def _align_local(ref: list[str], hyp: list[str]) -> _Align:
    n, m = len(ref), len(hyp)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for a in range(n + 1):
        dp[a][0] = a
    for b in range(m + 1):
        dp[0][b] = b
    for a in range(1, n + 1):
        for b in range(1, m + 1):
            cost = 0 if ref[a - 1] == hyp[b - 1] else 1
            dp[a][b] = min(dp[a - 1][b] + 1, dp[a][b - 1] + 1, dp[a - 1][b - 1] + cost)
    a, b = n, m
    ops: list[tuple[str, str | None, str | None]] = []
    s = i = d = h = 0
    while a > 0 or b > 0:
        diag = a > 0 and b > 0 and dp[a][b] == dp[a - 1][b - 1] + (
            0 if ref[a - 1] == hyp[b - 1] else 1
        )
        if diag:
            if ref[a - 1] == hyp[b - 1]:
                ops.append(("equal", ref[a - 1], hyp[b - 1]))
                h += 1
            else:
                ops.append(("sub", ref[a - 1], hyp[b - 1]))
                s += 1
            a -= 1
            b -= 1
        elif b > 0 and dp[a][b] == dp[a][b - 1] + 1:
            ops.append(("ins", None, hyp[b - 1]))
            i += 1
            b -= 1
        else:
            ops.append(("del", ref[a - 1], None))
            d += 1
            a -= 1
    ops.reverse()
    return _Align(ops, s, i, d, h)


# ── medical lexicon ──────────────────────────────────────────────────────
_MED_TERMS = {
    # the 12 AfriSwitchCare conditions + common presentation vocabulary
    "appendicitis", "asthma", "bronchopneumonia", "pneumonia", "diabetes",
    "mellitus", "convulsion", "convulsions", "febrile", "hypertension",
    "osteoarthritis", "arthritis", "stroke", "tuberculosis", "depression",
    "psychosis", "malaria", "typhoid", "ulcer", "anaemia", "anemia",
    "hypertensive", "diabetic", "epilepsy", "seizure", "seizures",
    # symptoms
    "fever", "cough", "coughing", "headache", "vomiting", "vomit", "nausea",
    "diarrhoea", "diarrhea", "dizziness", "dizzy", "fatigue", "weakness",
    "swelling", "swollen", "rash", "itching", "bleeding", "pain", "chest",
    "abdomen", "abdominal", "stomach", "breath", "breathing", "breathless",
    "wheezing", "palpitations", "numbness", "blurred", "vision", "weight",
    "loss", "appetite", "night", "sweats", "chills", "jaundice", "urine",
    "constipation", "discharge",
    # anatomy / systems
    "blood", "pressure", "sugar", "heart", "lung", "lungs", "kidney",
    "liver", "brain", "joint", "joints", "bone", "muscle", "nerve",
    "pelvic", "uterus",
    # drugs / management
    "insulin", "metformin", "paracetamol", "ibuprofen", "amoxicillin",
    "antibiotic", "antibiotics", "antimalarial", "antihypertensive",
    "amlodipine", "lisinopril", "salbutamol", "inhaler", "ventolin",
    "steroid", "steroids", "prednisolone", "aspirin", "warfarin",
    "diazepam", "phenobarbitone", "haloperidol", "antidepressant",
    "vaccine", "vaccination", "dose", "dosage", "tablet", "tablets",
    "injection", "drip", "transfusion", "oxygen", "nebuliser", "nebulizer",
    "surgery", "operation", "scan", "x-ray", "ultrasound", "referral",
    "admit", "admitted", "admission", "hospital", "clinic",
    # measurements
    "milligram", "milligrams", "millilitre", "millilitres", "celsius",
    "degrees", "millimetres", "systolic", "diastolic",
}

_NUMBER_RE = re.compile(r"^\d+(?:\.\d+)?$")
_NUMBER_WORDS = {
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
    "sixteen", "seventeen", "eighteen", "nineteen", "twenty", "thirty",
    "forty", "fifty", "sixty", "seventy", "eighty", "ninety", "hundred",
    "thousand", "once", "twice", "daily", "weekly", "morning", "evening",
    "night", "hourly",
}


def _recall_of(keep: Callable[[str], bool], align: _Align) -> tuple[int, int]:
    """(#matched, #present-in-reference) for reference tokens matching `keep`."""
    present = matched = 0
    for op, r, _h in align.ops:
        if r is None:
            continue
        if keep(r.strip("'")):
            present += 1
            if op == "equal":
                matched += 1
    return matched, present


# ── public API ───────────────────────────────────────────────────────────
@dataclass
class Score:
    ref_words: int = 0
    hyp_words: int = 0
    ref_chars: int = 0
    char_edits: int = 0
    ref_words_strict: int = 0
    word_edits_strict: int = 0
    wer: float = 0.0
    cer: float = 0.0
    wer_strict: float = 0.0
    sub: int = 0
    ins: int = 0
    dele: int = 0
    cmi_gold: float | None = None      # dataset's own CMI (from the [[EN]] annotation)
    cmi_ref: float = 0.0               # our dictionary tagger on the reference text
    cmi_hyp: float = 0.0               # our dictionary tagger on the hypothesis
    cmi_abs_err: float = 0.0           # |cmi_ref - cmi_hyp| — same estimator both sides
    switch_gold: int | None = None
    switch_ref: int = 0
    switch_hyp: int = 0
    switch_count_err: int = 0
    en_recall: float = 0.0
    en_precision: float = 0.0
    keyterm_recall: float | None = None
    keyterm_n: int = 0
    number_recall: float | None = None
    number_n: int = 0

    def as_dict(self) -> dict:
        return asdict(self)


def score(reference_tagged: str, hypothesis: str, *, cmi_gold: float | None = None,
          switch_gold: int | None = None, clinical: bool = True) -> Score:
    ref_plain = strip_tags(reference_tagged)
    r_tok = normalize(ref_plain).split()
    h_tok = normalize(hypothesis).split()
    al = _align(r_tok, h_tok)

    n_ref = max(len(r_tok), 1)
    ref_n, hyp_n = normalize(ref_plain), normalize(hypothesis)
    char_edits = _char_edits(ref_n, hyp_n)
    s = Score(
        ref_words=len(r_tok),
        hyp_words=len(h_tok),
        ref_chars=len(ref_n.replace(" ", "")),
        char_edits=char_edits,
        wer=(al.sub + al.ins + al.dele) / n_ref,
        cer=char_edits / max(len(ref_n.replace(" ", "")), 1),
        sub=al.sub, ins=al.ins, dele=al.dele,
    )

    rs, hs = normalize_strict(ref_plain).split(), normalize_strict(hypothesis).split()
    al_s = _align(rs, hs)
    s.ref_words_strict = len(rs)
    s.word_edits_strict = al_s.sub + al_s.ins + al_s.dele
    s.wer_strict = s.word_edits_strict / max(len(rs), 1)

    # code-switching ------------------------------------------------------
    # cmi_abs_err / switch_count_err compare the SAME estimator (our English
    # dictionary tagger) on reference vs hypothesis, so its systematic bias
    # cancels. The dataset's gold CMI is carried through untouched as context.
    gold_labels = _lang_labels_from_tags(reference_tagged)
    s.cmi_gold = cmi_gold if cmi_gold is not None else round(cmi(gold_labels), 2)
    s.switch_gold = switch_gold if switch_gold is not None else switch_points(gold_labels)
    ref_labels = _lang_labels_from_dict(ref_plain)
    hyp_labels = _lang_labels_from_dict(hypothesis)
    s.cmi_ref = cmi(ref_labels)
    s.cmi_hyp = cmi(hyp_labels)
    s.cmi_abs_err = abs(s.cmi_ref - s.cmi_hyp)
    s.switch_ref = switch_points(ref_labels)
    s.switch_hyp = switch_points(hyp_labels)
    s.switch_count_err = abs(s.switch_ref - s.switch_hyp)

    # English-token recall / precision via the alignment
    en_ref_present = en_ref_hit = en_hyp_total = en_hyp_true = 0
    for op, r, h in al.ops:
        if r is not None and is_english_token(r):
            en_ref_present += 1
            if op == "equal":
                en_ref_hit += 1
        if h is not None and is_english_token(h):
            en_hyp_total += 1
            if op == "equal" and r is not None and is_english_token(r):
                en_hyp_true += 1
    s.en_recall = en_ref_hit / en_ref_present if en_ref_present else 0.0
    s.en_precision = en_hyp_true / en_hyp_total if en_hyp_total else 0.0

    # clinical salience ---------------------------------------------------
    if clinical:
        m, p = _recall_of(lambda t: t in _MED_TERMS, al)
        s.keyterm_recall = (m / p) if p else None
        s.keyterm_n = p
        m2, p2 = _recall_of(lambda t: t in _NUMBER_WORDS or bool(_NUMBER_RE.match(t)), al)
        s.number_recall = (m2 / p2) if p2 else None
        s.number_n = p2
    return s


def _char_edits(ref: str, hyp: str) -> int:
    """Levenshtein edit distance on characters (spaces removed), O(len) memory."""
    r = ref.replace(" ", "")
    h = hyp.replace(" ", "")
    if not r:
        return len(h)
    prev = list(range(len(h) + 1))
    for a in range(1, len(r) + 1):
        cur = [a] + [0] * len(h)
        for b in range(1, len(h) + 1):
            cost = 0 if r[a - 1] == h[b - 1] else 1
            cur[b] = min(prev[b] + 1, cur[b - 1] + 1, prev[b - 1] + cost)
        prev = cur
    return prev[-1]


def aggregate(scores: list[Score]) -> dict:
    """Corpus-level WER (pooled over words, not the mean of per-clip WERs) + means."""
    if not scores:
        return {}
    n = len(scores)
    tot_ref = sum(s.ref_words for s in scores) or 1
    tot_err = sum(s.sub + s.ins + s.dele for s in scores)
    tot_ref_chars = sum(s.ref_chars for s in scores) or 1
    tot_char_edits = sum(s.char_edits for s in scores)
    tot_ref_strict = sum(s.ref_words_strict for s in scores) or 1
    tot_edits_strict = sum(s.word_edits_strict for s in scores)
    kt = [s.keyterm_recall for s in scores if s.keyterm_recall is not None]
    nr = [s.number_recall for s in scores if s.number_recall is not None]
    gold = [s.cmi_gold for s in scores if s.cmi_gold is not None]
    return {
        "clips": n,
        "ref_words": tot_ref,
        "wer": tot_err / tot_ref,
        "wer_clip_mean": sum(s.wer for s in scores) / n,
        "wer_clip_median": sorted(s.wer for s in scores)[n // 2],
        "wer_strict": tot_edits_strict / tot_ref_strict,
        "cer": tot_char_edits / tot_ref_chars,
        "cmi_gold": (sum(gold) / len(gold)) if gold else None,
        "cmi_ref": sum(s.cmi_ref for s in scores) / n,
        "cmi_hyp": sum(s.cmi_hyp for s in scores) / n,
        "cmi_abs_err": sum(s.cmi_abs_err for s in scores) / n,
        "switch_count_err": sum(s.switch_count_err for s in scores) / n,
        "en_recall": sum(s.en_recall for s in scores) / n,
        "en_precision": sum(s.en_precision for s in scores) / n,
        "keyterm_recall": (sum(kt) / len(kt)) if kt else None,
        "number_recall": (sum(nr) / len(nr)) if nr else None,
        "sub_rate": sum(s.sub for s in scores) / tot_ref,
        "ins_rate": sum(s.ins for s in scores) / tot_ref,
        "del_rate": sum(s.dele for s in scores) / tot_ref,
    }
