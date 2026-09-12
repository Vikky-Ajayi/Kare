"""NCAIR/N-ATLaS — Nigeria's national ASR effort (NITDA + NCAIR + Awarri).

Not one model: three separate Whisper-small (244M) fine-tunes, one per
language, each gated on HF (auto-approved once you accept the terms on the
model page). There is no Pidgin or Swahili checkpoint — `config.MODELS
["ncair-atlas"]["languages"]` declares that restriction and `run.py` scores
this model only within it, rather than treating the other two languages as
failures.

Runs locally via `transformers` (CPU). Each checkpoint's own model card caps
single-pass context at 30s; passing `chunk_length_s` lets the HF pipeline
handle the >30s AfriSwitchCare segments via its own sliding-window chunking
rather than us reimplementing that.
"""

from __future__ import annotations

from pathlib import Path

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

            self._pipes[lang] = pipeline(
                "automatic-speech-recognition",
                model=_MODEL_FOR_LANG[lang],
                chunk_length_s=28,      # model card: 30s max per inference pass
                stride_length_s=4,
                device=-1,               # CPU — this machine has no CUDA/MPS transformers build
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
