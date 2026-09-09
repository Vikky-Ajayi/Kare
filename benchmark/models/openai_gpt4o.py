"""OpenAI gpt-4o-transcribe — a strong closed frontier baseline.

Skipped automatically when OPENAI_API_KEY is not set (see config.default_models).
gpt-4o-transcribe accepts a `language` hint (ISO-639-1) and no `temperature`.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from benchmark.models import Adapter

_LANG = {"yoruba": "yo", "hausa": "ha", "igbo": None, "pidgin": None, "swahili": "sw"}


class OpenAIGpt4oAdapter(Adapter):
    def __init__(self, *, model: str = "gpt-4o-transcribe", **params):
        super().__init__(**params)
        from openai import OpenAI

        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY not set")
        self.model = model
        self._client = OpenAI(api_key=key, timeout=120.0, max_retries=0)

    def _run(self, wav_path: Path, *, language: str) -> tuple[str, dict]:
        lang = _LANG.get(language)
        for attempt in range(6):
            try:
                with wav_path.open("rb") as fh:
                    kw = {"file": fh, "model": self.model, "response_format": "text"}
                    if lang:
                        kw["language"] = lang
                    r = self._client.audio.transcriptions.create(**kw)
                text = r if isinstance(r, str) else getattr(r, "text", "")
                return text or "", {"model": self.model, "lang": lang}
            except Exception as exc:  # noqa: BLE001
                msg = str(exc)
                if ("429" in msg or "rate" in msg.lower()) and attempt < 5:
                    time.sleep(15 * (attempt + 1))
                    continue
                raise
        raise RuntimeError("gpt-4o-transcribe: exhausted retries")
