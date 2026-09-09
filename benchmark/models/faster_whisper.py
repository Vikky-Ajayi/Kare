"""faster-whisper — CTranslate2 Whisper running locally on CPU.

This is the "no cloud, no per-minute cost, runs on a clinic laptop" baseline.
The model is loaded once and reused across the whole run.
"""

from __future__ import annotations

from pathlib import Path

from benchmark.config import LOCAL_MODEL_DIR
from benchmark.models import Adapter

# Whisper's tokenizer has no Igbo token, and no code for Pidgin — both auto-detect.
_LANG = {"yoruba": "yo", "hausa": "ha", "igbo": None, "pidgin": None, "swahili": "sw"}


class FasterWhisperAdapter(Adapter):
    def __init__(self, *, model_size: str = "tiny", compute_type: str = "int8", **params):
        super().__init__(**params)
        from faster_whisper import WhisperModel

        self.model_size = model_size
        # prefer pre-downloaded weights (benchmark/data/models/faster-whisper-<size>)
        local = LOCAL_MODEL_DIR / f"faster-whisper-{model_size}"
        source = str(local) if (local / "model.bin").exists() else model_size
        self._model = WhisperModel(source, device="cpu", compute_type=compute_type)

    def _run(self, wav_path: Path, *, language: str) -> tuple[str, dict]:
        lang = _LANG.get(language)
        segments, info = self._model.transcribe(
            str(wav_path), language=lang, beam_size=5, vad_filter=False,
            condition_on_previous_text=False,
        )
        text = " ".join(s.text.strip() for s in segments)
        return text, {
            "model": self.model_size,
            "detected_language": getattr(info, "language", None),
            "language_probability": round(getattr(info, "language_probability", 0.0), 3),
        }
