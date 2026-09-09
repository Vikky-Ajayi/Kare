"""Sahara (Intron) STT.

Uses the **streaming WebSocket** endpoint (`wss://…/stt/v1/stream`) — the same
path Kare uses for live consultations. The synchronous file-upload endpoint
(`/file/v1/upload/sync`) is a separately-metered paid product and returns
`400 "insufficient balance"` on the hackathon key, so the benchmark runs the
transcription path the product actually ships.

Audio is sent as 16 kHz mono PCM16 in 0.5 s frames, then COMMIT; we return the
COMMITTED transcript (or the last partial if the socket closes first).
"""

from __future__ import annotations

import asyncio
import contextlib
import time
from pathlib import Path

import numpy as np

from benchmark.audio import read_wav
from benchmark.models import Adapter

_LANG = {"yoruba": "yo", "hausa": "ha", "igbo": "ig", "pidgin": "pcm", "swahili": "sw"}
_FRAME_BYTES = 16_000          # 0.5 s of 16 kHz PCM16


class SaharaAdapter(Adapter):
    def __init__(self, **params):
        super().__init__(**params)
        import os

        if not os.getenv("SAHARA_API_KEY"):
            raise RuntimeError("SAHARA_API_KEY not set")
        from app.providers.sahara_voice import SaharaVoice

        self._voice = SaharaVoice()
        self._warmed: set[str] = set()

    def warm(self, language: str) -> None:
        lang = _LANG.get(language, "en")
        if lang in self._warmed:
            return
        with contextlib.suppress(Exception):
            asyncio.run(self._voice.warm(lang, attempts=3, wait_s=20))
        self._warmed.add(lang)

    def _run(self, wav_path: Path, *, language: str) -> tuple[str, dict]:
        lang = _LANG.get(language, "en")
        x, _sr = read_wav(wav_path)
        pcm = (np.clip(x, -1.0, 1.0) * 32767.0).astype("<i2").tobytes()
        budget = max(120.0, len(pcm) / 32_000 * 3)   # 3x real time, min 2 min

        last_err = ""
        for attempt in range(5):
            try:
                text, kind = asyncio.run(
                    asyncio.wait_for(self._stream(pcm, lang), timeout=budget)
                )
                if text:
                    return text, {"lang": lang, "result": kind, "attempt": attempt}
                last_err = "empty transcript"
                time.sleep(5)
            except Exception as exc:  # noqa: BLE001
                last_err = f"{type(exc).__name__}: {str(exc)[:160]}"
                name = type(exc).__name__
                if name in ("SaharaColdStart", "ConnectError", "ConnectionClosedError",
                            "ConnectionClosedOK", "ReadError", "TimeoutError",
                            "WebSocketException", "InvalidStatusCode"):
                    time.sleep(min(10 * 2 ** attempt, 90))
                    continue
                raise
        raise RuntimeError(f"Sahara stream failed after retries: {last_err}")

    async def _stream(self, pcm: bytes, lang: str) -> tuple[str, str]:
        async def frames():
            for off in range(0, len(pcm), _FRAME_BYTES):
                yield pcm[off:off + _FRAME_BYTES]

        final, last_partial = "", ""
        async for msg in self._voice.transcribe_stream(frames(), language=lang):
            if msg["type"] == "partial":
                last_partial = msg["text"]
            elif msg["type"] == "final":
                final = msg["text"]
        return (final, "committed") if final else (last_partial, "partial")
