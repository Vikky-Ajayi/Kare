"""Groq-hosted Whisper (whisper-large-v3 and -turbo).

Groq's audio endpoint is OpenAI-compatible. Free tier has an audio-seconds
per-hour cap; on 429 we back off and retry so a full run just runs slower
rather than failing.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from benchmark.models import Adapter

# AfriSwitchCare config -> Whisper ISO-639-1 hint.
#  - Pidgin has no code; auto-detect beats forcing "en".
#  - Igbo is NOT in Whisper's language set at all (the API 400s on "ig"), so it
#    also auto-detects. That inability is itself a benchmark finding.
_LANG = {"yoruba": "yo", "hausa": "ha", "igbo": None, "pidgin": None, "swahili": "sw"}


class GroqWhisperAdapter(Adapter):
    def __init__(self, *, model: str = "whisper-large-v3", **params):
        super().__init__(**params)
        from groq import Groq

        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise RuntimeError("GROQ_API_KEY not set")
        self.model = model
        self._client = Groq(api_key=key, timeout=120.0, max_retries=0)

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
                    "response_format": "verbose_json",
                    "temperature": 0.0,
                }
                if used_hint:
                    kw["language"] = used_hint
                r = self._client.audio.transcriptions.create(**kw)
                return r.text or "", {"model": self.model, "lang": used_hint,
                                      "hint_dropped": used_hint != lang}
            except Exception as exc:  # noqa: BLE001
                msg = str(exc)
                last = f"{type(exc).__name__}: {msg[:160]}"
                if "invalid_language" in msg or "unsupported language" in msg:
                    used_hint = None          # retry on auto-detect
                    continue
                transient = (
                    "429" in msg or "rate" in msg.lower() or "503" in msg or "502" in msg
                    or "APIConnectionError" in last or "Connection error" in msg
                    or "timeout" in msg.lower()
                )
                if transient and attempt < 7:
                    time.sleep(_retry_after(msg, default=min(15 * 2 ** attempt, 240)))
                    continue
                raise
        raise RuntimeError(f"Groq Whisper: exhausted retries — {last}")


def _retry_after(msg: str, *, default: float) -> float:
    import re

    m = re.search(r"try again in ([\d.]+)s", msg)
    if m:
        return min(float(m.group(1)) + 1.0, 90.0)
    return default
