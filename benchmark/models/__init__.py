"""
ASR adapters.

Every adapter exposes the same call:

    adapter.transcribe(wav_path: Path, *, language: str) -> Hyp

where ``language`` is the AfriSwitchCare config name (``yoruba`` …) and the
adapter maps it to whatever code its backend wants. ``Hyp`` carries the
text, the wall-clock latency, and the audio duration so the runner can
compute a real-time factor and a cost estimate.
"""

from __future__ import annotations

import importlib
import time
from dataclasses import dataclass, field
from pathlib import Path

from benchmark.config import MODELS


@dataclass
class Hyp:
    text: str
    latency_s: float
    audio_s: float
    ok: bool = True
    error: str | None = None
    raw: dict = field(default_factory=dict)


class Adapter:
    """Base class. Subclasses implement ``_run``."""

    model_id: str = "?"

    def __init__(self, **params):
        self.params = params

    def _run(self, wav_path: Path, *, language: str) -> tuple[str, dict]:
        raise NotImplementedError

    def transcribe(self, wav_path: Path, *, language: str) -> Hyp:
        from benchmark.audio import read_wav

        x, sr = read_wav(wav_path)
        audio_s = len(x) / sr
        t0 = time.perf_counter()
        try:
            text, raw = self._run(wav_path, language=language)
            return Hyp(text=text.strip(), latency_s=time.perf_counter() - t0,
                      audio_s=audio_s, raw=raw)
        except Exception as exc:  # noqa: BLE001
            return Hyp(text="", latency_s=time.perf_counter() - t0, audio_s=audio_s,
                      ok=False, error=f"{type(exc).__name__}: {exc}")

    def warm(self, language: str) -> None:  # optional
        pass


def load(model_id: str) -> Adapter:
    spec = MODELS[model_id]
    mod_name, cls_name = spec["adapter"].split(":")
    cls = getattr(importlib.import_module(mod_name), cls_name)
    inst: Adapter = cls(**spec.get("params", {}))
    inst.model_id = model_id
    return inst
