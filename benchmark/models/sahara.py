"""Sahara (Intron) STT — synchronous file-upload endpoint.

`POST /file/v1/upload/sync` takes a WAV and returns the full transcript in one
call. (The `stt/v1/stream` WebSocket is what Kare's live consult uses, but for
batch-scoring a frozen test set the sync endpoint is simpler, faster and
doesn't carry per-language cold-start latency — it was the one returning
`400 "insufficient balance"` before the account was topped up.)
"""

from __future__ import annotations

import time
from pathlib import Path

from benchmark.models import Adapter

_LANG = {"yoruba": "yo", "hausa": "ha", "igbo": "ig", "pidgin": "pcm", "swahili": "sw"}


class SaharaAdapter(Adapter):
    def __init__(self, **params):
        super().__init__(**params)
        import os

        if not os.getenv("SAHARA_API_KEY"):
            raise RuntimeError("SAHARA_API_KEY not set")
        from app.providers.sahara_voice import SaharaVoice

        self._voice = SaharaVoice()

    def _run(self, wav_path: Path, *, language: str) -> tuple[str, dict]:
        import asyncio

        lang = _LANG.get(language, "en")
        wav = wav_path.read_bytes()

        last_err = ""
        for attempt in range(6):
            try:
                t = asyncio.run(
                    self._voice.transcribe(wav, language=lang, filename=wav_path.name,
                                            telehealth=True)
                )
                return t.text or "", {"lang": lang}
            except Exception as exc:  # noqa: BLE001
                msg = str(exc)
                last_err = f"{type(exc).__name__}: {msg[:160]}"
                transient = (
                    "insufficient balance" not in msg  # a real balance error won't clear itself
                    and any(k in msg for k in ("429", "rate", "502", "503", "504",
                                                "ConnectError", "ConnectTimeout", "ReadError",
                                                "timeout", "Timeout"))
                )
                if transient and attempt < 5:
                    time.sleep(min(10 * 2 ** attempt, 90))
                    continue
                raise
        raise RuntimeError(f"Sahara sync failed after retries: {last_err}")
