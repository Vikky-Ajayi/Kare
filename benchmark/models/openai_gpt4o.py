"""OpenAI gpt-4o-transcribe — the frontier closed-model comparison point.

Runs automatically once OPENAI_API_KEY is set (config.default_models picks up
any model whose key is present). gpt-4o-transcribe takes a `language` hint
(ISO-639-1) and only `json` / `text` response formats. ~$0.006 / audio-minute,
so a full 128-min run is roughly $0.75.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from benchmark.models import Adapter

# Whisper-family language set has no Igbo; Pidgin has no code. Both auto-detect.
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
        used_hint = lang
        audio = wav_path.read_bytes()
        last = ""
        for attempt in range(8):
            try:
                kw = {
                    "file": (wav_path.name, audio),
                    "model": self.model,
                    "response_format": "text",
                }
                if used_hint:
                    kw["language"] = used_hint
                r = self._client.audio.transcriptions.create(**kw)
                text = r if isinstance(r, str) else getattr(r, "text", "")
                return text or "", {"model": self.model, "lang": used_hint,
                                    "hint_dropped": used_hint != lang}
            except Exception as exc:  # noqa: BLE001
                msg = str(exc)
                last = f"{type(exc).__name__}: {msg[:160]}"
                if ("invalid" in msg.lower() and "language" in msg.lower()) and used_hint:
                    used_hint = None
                    continue
                transient = (
                    "429" in msg or "rate" in msg.lower() or "500" in msg or "503" in msg
                    or "APIConnectionError" in last or "Connection error" in msg
                    or "timeout" in msg.lower()
                )
                if transient and attempt < 7:
                    time.sleep(min(15 * 2 ** attempt, 240))
                    continue
                raise
        raise RuntimeError(f"gpt-4o-transcribe: exhausted retries — {last}")
