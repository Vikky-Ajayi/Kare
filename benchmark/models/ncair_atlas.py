"""NCAIR/N-ATLaS — Nigeria's national ASR effort (NITDA + NCAIR + Awarri).

Not one model: three separate Whisper-small (244M) fine-tunes, one per
language, each gated on HF ("auto" gate — instant once *you personally*
click "Agree and access repository" on each page while logged in as the
account behind HF_TOKEN; listing the repo's files with that token succeeds
even before you've clicked through, which is a red herring — actually
downloading a file 403s until you do:
  https://huggingface.co/NCAIR1/Yoruba-ASR
  https://huggingface.co/NCAIR1/Hausa-ASR
  https://huggingface.co/NCAIR1/Igbo-ASR
There is no Pidgin or Swahili checkpoint — `config.MODELS
["ncair-atlas"]["languages"]` declares that restriction and `run.py` scores
this model only within it, rather than treating the other two languages as
failures.

Runs locally via `transformers` (CPU). Each checkpoint's own model card caps
single-pass context at 30s; passing `chunk_length_s` lets the HF pipeline
handle the >30s AfriSwitchCare segments via its own sliding-window chunking
rather than us reimplementing that.
"""

from __future__ import annotations

import os
from pathlib import Path

# huggingface_hub's default etag/download timeouts (10s) are too short for
# this project's network — the same "resolve stalls" issue _fetch.sh works
# around for dataset parquet, but here it's inside transformers' own model
# download path, so we raise it via env instead. setdefault: don't clobber
# a value the caller deliberately set.
os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "120")
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "120")

from benchmark.config import LOCAL_MODEL_DIR
from benchmark.models import Adapter

_MODEL_FOR_LANG = {
    "yoruba": "NCAIR1/Yoruba-ASR",
    "hausa": "NCAIR1/Hausa-ASR",
    "igbo": "NCAIR1/Igbo-ASR",
}


class NCAIRAdapter(Adapter):
    def __init__(self, **params):
        super().__init__(**params)
        self._pipes: dict[str, object] = {}   # lang -> transformers pipeline, lazy per-language

    def _pipe_for(self, lang: str):
        if lang not in _MODEL_FOR_LANG:
            return None
        if lang not in self._pipes:
            from transformers import pipeline

            # Prefer pre-fetched weights (benchmark/_fetch_ncair.sh) — the HF
            # hub downloader's own snapshot_download stalls silently and
            # never recovers on this network; curl -C - with an outer retry
            # loop does not. NCAIR only publishes pytorch_model.bin, but
            # transformers now refuses to torch.load a .bin file below
            # torch 2.6 (CVE-2025-32434) — converted the local copy to
            # .safetensors once (torch.load(weights_only=True), a trusted
            # one-time conversion of a file already fetched over HTTPS from
            # the official org) rather than force a torch upgrade that had
            # been timing out repeatedly on this network.
            local = LOCAL_MODEL_DIR / f"ncair-{lang}"
            source = str(local) if (local / "model.safetensors").exists() else _MODEL_FOR_LANG[lang]
            self._pipes[lang] = pipeline(
                "automatic-speech-recognition",
                model=source,
                chunk_length_s=28,      # model card: 30s max per inference pass
                stride_length_s=4,
                device=-1,               # CPU — this machine has no CUDA/MPS transformers build
                # Beam search is what made this unusable: a single 110s clip
                # took 90+ minutes on CPU with the model's own default beam
                # count. Greedy decoding brought an 8s clip from that same
                # ballpark down to ~13s (RTF ~1.7). Not forcing `language=`
                # here — Hausa/Igbo extend Whisper's tokenizer with their own
                # added_tokens.json, so "hausa"/"igbo" aren't guaranteed to
                # resolve the way "yoruba" (a native Whisper language) does;
                # auto-detect on a per-language fine-tune is cheap and safe.
                generate_kwargs={"num_beams": 1},
            )
        return self._pipes[lang]

    def _run(self, wav_path: Path, *, language: str) -> tuple[str, dict]:
        pipe = self._pipe_for(language)
        if pipe is None:
            # Should not normally be reached — run.py skips unsupported
            # languages before calling transcribe() at all — but fail loudly
            # if this adapter is ever invoked directly on pcm/sw.
            raise RuntimeError(
                f"NCAIR/N-ATLaS has no {language} model (Nigerian-only: yoruba/hausa/igbo)"
            )
        from benchmark.audio import read_wav

        x, sr = read_wav(wav_path)
        result = pipe({"array": x, "sampling_rate": sr})
        return result["text"], {"model": _MODEL_FOR_LANG[language]}
