"""
Shared configuration for the Kare code-switching ASR benchmark.

Everything the harness needs to be reproducible lives here or in
``frozen_manifest.jsonl``: dataset ids, the languages under test, the
stratified-subset parameters, the segment length, and the model registry.
"""

from __future__ import annotations

import os
from pathlib import Path

# Load the repo .env (GROQ_API_KEY, SAHARA_API_KEY, HF_TOKEN, optional
# OPENAI_API_KEY) so the benchmark can run from a bare shell.
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

# ── paths ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"                      # raw parquet + decoded audio (gitignored)
CACHE_DIR = DATA_DIR / ".hf_cache"
AUDIO_DIR = DATA_DIR / "audio"                # decoded 16 kHz wav, one dir per conversation
SEG_DIR = DATA_DIR / "segments"               # fixed-window slices actually sent to models
MANIFEST = ROOT / "frozen_manifest.jsonl"     # the frozen test subset (committed)
RESULTS_DIR = ROOT / "results"                # per-model hypotheses + scores (committed)
REPORT_DIR = ROOT / "report"                  # REPORT.md, charts, error samples (committed)

for _d in (DATA_DIR, AUDIO_DIR, SEG_DIR, RESULTS_DIR, REPORT_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ── datasets ─────────────────────────────────────────────────────────────
# AfriSwitchCare: 108 simulated doctor–patient conversations, 9 languages,
# 12 clinical conditions each, English code-switched with the matrix language.
# This is the only Intron code-switch set with a *clinical* domain, which is
# exactly Kare's use case, so it is the primary benchmark.
CARE_REPO = "intronhealth/AfriSwitchCare"

# AfriSwitch (16.6 k short utterances, 14 languages) is the secondary,
# *general-domain* corpus — same team/annotation convention as AfriSwitchCare
# (transcription_tagged with [[EN]] spans, cmi, num_switch_points) but no
# clinical script. Used as a generalisation check: does a model's edge on the
# clinical set hold on ordinary speech, or was it fitted to that domain? It is
# access-gated behind manual approval; the harness uses it only if the
# parquet files are already present under data/afriswitch/ (see
# `benchmark/subset_switch.py` / `make bench-subset-switch`).
SWITCH_REPO = "intronhealth/AfriSwitch"
SWITCH_PARQUET_DIR = DATA_DIR / "afriswitch" / "data"
SWITCH_MANIFEST = ROOT / "frozen_manifest_switch.jsonl"     # committed, like MANIFEST
SWITCH_RESULTS_DIR = ROOT / "results_switch"                # committed
SWITCH_REPORT_DIR = ROOT / "report_switch"                  # committed
# Utterances run a few seconds each (vs. AfriSwitchCare's multi-minute
# conversations), so we take more of them per language for a comparable
# amount of test audio without needing the 110s segmentation pass at all.
UTTS_PER_LANG = 25

for _d in (SWITCH_RESULTS_DIR, SWITCH_REPORT_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# Kare speaks en / yo / ha / ig / pcm. We benchmark the four non-English
# matrix languages, plus Swahili as an out-of-family control (a Bantu language
# none of Kare's users speak — it shows whether a model generalises or has
# simply been tuned on West African data).
BENCH_LANGS = ["yoruba", "hausa", "igbo", "pidgin", "swahili"]

# AfriSwitchCare config name -> (Kare code, Sahara STT code, Whisper hint code)
LANG_META = {
    "yoruba":  {"kare": "yo",  "sahara": "yo",  "whisper": "yo", "in_family": True},
    "hausa":   {"kare": "ha",  "sahara": "ha",  "whisper": "ha", "in_family": True},
    "igbo":    {"kare": "ig",  "sahara": "ig",  "whisper": "ig", "in_family": True},
    "pidgin":  {"kare": "pcm", "sahara": "pcm", "whisper": "en", "in_family": True},
    "swahili": {"kare": "sw",  "sahara": "sw",  "whisper": "sw", "in_family": False},
}

# ── frozen subset ────────────────────────────────────────────────────────
# Conversations per language, chosen to span that language's CMI range
# (low / mid / high tertile). Deterministic given SUBSET_SEED.
CONVOS_PER_LANG = 4
SUBSET_SEED = 20260915          # hackathon deadline, so the number is memorable

# Every conversation is cut into fixed windows before transcription. This
# keeps the request well under Sahara's sync-endpoint limit and Whisper's
# file limits, and — because the exact same slices go to every model — keeps
# the comparison apples-to-apples. Boundary word-splits inflate WER a little
# for all models equally; see report/REPORT.md "Harness notes".
SEGMENT_SECONDS = 110
SEGMENT_OVERLAP_SECONDS = 0
TARGET_SR = 16_000

# ── models under test ────────────────────────────────────────────────────
# id -> (adapter module:class, human label, needs_api_key_env)
MODELS: dict[str, dict] = {
    "sahara": {
        "adapter": "benchmark.models.sahara:SaharaAdapter",
        "label": "Sahara (Intron) STT",
        "key_env": "SAHARA_API_KEY",
        "kind": "api",
    },
    "groq-whisper-v3": {
        "adapter": "benchmark.models.groq_whisper:GroqWhisperAdapter",
        "label": "Groq · whisper-large-v3",
        "key_env": "GROQ_API_KEY",
        "kind": "api",
        "params": {"model": "whisper-large-v3"},
    },
    "groq-whisper-v3-turbo": {
        "adapter": "benchmark.models.groq_whisper:GroqWhisperAdapter",
        "label": "Groq · whisper-large-v3-turbo",
        "key_env": "GROQ_API_KEY",
        "kind": "api",
        "params": {"model": "whisper-large-v3-turbo"},
    },
    "faster-whisper-tiny": {
        "adapter": "benchmark.models.faster_whisper:FasterWhisperAdapter",
        "label": "faster-whisper tiny (local CPU)",
        "key_env": None,
        "kind": "local",
        "params": {"model_size": "tiny", "compute_type": "int8"},
    },
    # Frontier closed model. Runs automatically once OPENAI_API_KEY is set
    # (default_models() picks up any model whose key is present).
    "openai-gpt4o-transcribe": {
        "adapter": "benchmark.models.openai_gpt4o:OpenAIGpt4oAdapter",
        "label": "OpenAI · gpt-4o-transcribe",
        "key_env": "OPENAI_API_KEY",
        "kind": "api",
        "params": {"model": "gpt-4o-transcribe"},
    },
    # Nigeria's national ASR effort (NCAIR/NITDA + Awarri, "N-ATLaS"): three
    # separate Whisper-small fine-tunes, one per language, gated on HF (auto-
    # approved). No Pidgin or Swahili checkpoint exists, so this is the one
    # model with a restricted `languages` set — run.py scores and ranks it
    # only within that set rather than penalising it for languages it was
    # never trained on. Local CPU inference (transformers, no API key).
    "ncair-atlas": {
        "adapter": "benchmark.models.ncair_atlas:NCAIRAdapter",
        "label": "NCAIR/N-ATLaS (Whisper-small, per-language)",
        "key_env": None,
        "kind": "local",
        "languages": ["yoruba", "hausa", "igbo"],
    },
}

# Rough public list prices, USD per minute of audio, for the cost column.
# Sahara pricing is not public; left as None and reported as "n/p".
PRICE_PER_MIN = {
    "sahara": None,
    "groq-whisper-v3": 0.111 / 60,          # $0.111 / hour
    "groq-whisper-v3-turbo": 0.04 / 60,     # $0.04 / hour
    "faster-whisper-tiny": 0.0,             # local, electricity only
    "openai-gpt4o-transcribe": 0.006,       # $0.006 / minute
    "ncair-atlas": 0.0,                     # local, electricity only
}

# faster-whisper fetches its weights from the HF hub on first use. In some
# environments that download hangs; if the weights are pre-placed here the
# adapter uses them directly and never touches the network.
LOCAL_MODEL_DIR = DATA_DIR / "models"


def default_models() -> list[str]:
    """Models we have credentials for right now."""
    out = []
    for mid, m in MODELS.items():
        if m["key_env"] is None or os.getenv(m["key_env"]):
            out.append(mid)
    return out
