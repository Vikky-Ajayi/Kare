"""
Sahara (Intron Voice) implementation of VoiceProvider.

REST (fallback / benchmark):
  STT  POST {base}/file/v1/upload/sync   multipart, <=120s, telehealth category
  TTS  POST {base}/tts/v1/generate       JSON -> audio_path URL -> fetch bytes

Streaming (live consultation):
  STT  wss {base}/stt/v1/stream          PCM16 LE chunks -> PARTIAL/COMMITTED transcript
  TTS  we pipeline the REST endpoint per sentence — Sahara's TTS-stream WS is
       under-specified and closes early; sentence-chunked REST gives first audio
       in ~2-3s with none of the fragility.

Cold start: the first STT stream for a language after idle returns
RESOURCE_EXHAUSTED / "wait 30 seconds" while the model loads. `warm()` triggers
that ahead of time; `transcribe_stream` raises SaharaColdStart so the caller can
fall back to the sync endpoint for that turn.
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import re
import wave
from collections.abc import AsyncIterator

import httpx
import websockets
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import settings
from app.providers.base import SynthResult, Transcript, VoiceProvider

log = logging.getLogger("kare.voice")

# Kare code -> Sahara STT code (they line up; this is the allowlist).
_STT_LANG = {"en": "en", "yo": "yo", "ha": "ha", "ig": "ig", "pcm": "pcm"}

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'À-῿])")


def pcm_to_wav(pcm: bytes, sample_rate: int = 16000, channels: int = 1) -> bytes:
    """Wrap raw PCM16-LE in a WAV container so the sync STT endpoint accepts it."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(pcm)
    return buf.getvalue()


class _Retryable(Exception):
    pass


class SaharaColdStart(Exception):
    """Streaming model not loaded yet; caller should fall back or retry later."""


class SaharaVoice(VoiceProvider):
    name = "sahara"

    def __init__(self) -> None:
        self._base = settings.SAHARA_INFER_BASE_URL.rstrip("/")
        self._headers = {"Authorization": f"Bearer {settings.SAHARA_API_KEY}"}
        self._stt_ws = settings.SAHARA_STT_STREAM_URL
        self._warmed: set[str] = set()

    def _lang(self, code: str) -> str:
        return _STT_LANG.get(code, "en")

    # ── STT (sync, REST) ─────────────────────────────────────────────────
    @retry(
        retry=retry_if_exception_type(_Retryable),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=15),
        reraise=True,
    )
    async def transcribe(
        self,
        audio: bytes,
        *,
        language: str = "en",
        filename: str = "audio.wav",
        telehealth: bool = True,
    ) -> Transcript:
        data = {
            "audio_file_name": filename.rsplit(".", 1)[0] or "audio",
            "use_language_asr_input": self._lang(language),
        }
        if telehealth:
            data["use_category"] = settings.SAHARA_STT_CATEGORY

        async with httpx.AsyncClient(timeout=130.0) as client:
            resp = await client.post(
                f"{self._base}/file/v1/upload/sync",
                headers=self._headers,
                data=data,
                files={"audio_file_blob": (filename, audio)},
            )
        if resp.status_code in (429, 500, 502, 503, 504):
            raise _Retryable(f"Sahara STT {resp.status_code}: {resp.text[:200]}")
        resp.raise_for_status()

        payload = resp.json().get("data", {})
        return Transcript(
            text=(payload.get("audio_transcript") or "").strip(),
            language=data["use_language_asr_input"],
            duration_s=payload.get("processed_audio_duration_in_seconds"),
            raw=payload,
        )

    # ── STT (streaming, WebSocket) ──────────────────────────────────────
    async def warm(self, language: str, *, attempts: int = 3, wait_s: float = 12.0) -> bool:
        """Open a stream and drop it so the language model becomes resident.
        Retries through the cold-start ("wait 30 seconds") window."""
        lang = self._lang(language)
        url = (
            f"{self._stt_ws}?sample_rate=16000&bit_rate=16&num_channels=1"
            f"&use_language_asr_input={lang}"
        )
        for i in range(attempts):
            try:
                async with websockets.connect(
                    url, additional_headers=self._headers, max_size=None,
                    open_timeout=15, close_timeout=5,
                ) as ws:
                    first = json.loads(await asyncio.wait_for(ws.recv(), timeout=15))
                    if first.get("message_type") == "SESSION_CREATED":
                        self._warmed.add(lang)
                        return True
                    log.info("Sahara STT warm(%s) attempt %d: %s", lang, i + 1,
                             first.get("message", ""))
            except Exception as exc:  # noqa: BLE001
                log.warning("Sahara STT warm(%s) attempt %d failed: %s", lang, i + 1, exc)
            if i < attempts - 1:
                await asyncio.sleep(wait_s)
        return False

    def is_warm(self, language: str) -> bool:
        return self._lang(language) in self._warmed

    async def transcribe_stream(
        self,
        audio_chunks: AsyncIterator[bytes],
        *,
        language: str = "en",
        sample_rate: int = 16000,
        num_channels: int = 1,
    ) -> AsyncIterator[dict]:
        """Yield {"type": "partial"|"final", "text": str} as PCM16-LE audio is fed in.
        Raises SaharaColdStart if the model is still loading."""
        lang = self._lang(language)
        url = (
            f"{self._stt_ws}?sample_rate={sample_rate}&bit_rate=16"
            f"&num_channels={num_channels}&use_language_asr_input={lang}"
        )
        async with websockets.connect(
            url, additional_headers=self._headers, max_size=None,
            open_timeout=15, ping_interval=20,
        ) as ws:
            first = json.loads(await asyncio.wait_for(ws.recv(), timeout=15))
            if first.get("message_type") != "SESSION_CREATED":
                raise SaharaColdStart(first.get("message", "stream not ready"))
            self._warmed.add(lang)

            last_partial = ""
            ack = 0

            async def _pump() -> None:
                nonlocal ack
                async for chunk in audio_chunks:
                    for off in range(0, len(chunk), 16000):
                        ack += 1
                        await ws.send(json.dumps({
                            "message_type": "INPUT_AUDIO_CHUNK",
                            "audio_base_64": base64.b64encode(chunk[off:off + 16000]).decode(),
                            "ack_id": ack,
                        }))
                await ws.send(json.dumps({"message_type": "COMMIT"}))

            pump = asyncio.create_task(_pump())
            try:
                while True:
                    raw = await asyncio.wait_for(ws.recv(), timeout=30)
                    msg = json.loads(raw)
                    mt = msg.get("message_type")
                    if mt == "PARTIAL_TRANSCRIPT":
                        txt = (msg.get("transcript") or "").strip()
                        if txt and txt != last_partial:
                            last_partial = txt
                            yield {"type": "partial", "text": txt}
                    elif mt == "COMMITTED_TRANSCRIPT":
                        final = (msg.get("transcript") or last_partial or "").strip()
                        yield {"type": "final", "text": final}
                        return
                    elif mt in ("ERROR", "RESOURCE_EXHAUSTED"):
                        raise SaharaColdStart(msg.get("message", mt))
            finally:
                pump.cancel()

    # ── TTS (non-streaming, REST) ──────────────────────────────────────
    @retry(
        retry=retry_if_exception_type(_Retryable),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=15),
        reraise=True,
    )
    async def synthesize(self, text: str, *, language: str = "en") -> SynthResult:
        return await self._synth_one(text[:4096], language)

    async def _synth_one(self, text: str, language: str) -> SynthResult:
        voice = settings.SAHARA_VOICE_MAP.get(language, settings.SAHARA_VOICE_MAP["en"])
        body = {
            "text": text,
            "voice_language": voice["voice_language"],
            "voice_accent": voice["voice_accent"],
            "voice_gender": voice["voice_gender"],
            "output_audio_format": "wav",
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self._base}/tts/v1/generate",
                headers={**self._headers, "Content-Type": "application/json"},
                json=body,
            )
            if resp.status_code in (429, 500, 502, 503, 504):
                raise _Retryable(f"Sahara TTS {resp.status_code}: {resp.text[:200]}")
            resp.raise_for_status()
            data = resp.json().get("data", {})
            audio_url = data.get("audio_path")
            if not audio_url:
                raise RuntimeError(f"Sahara TTS returned no audio_path: {resp.text[:200]}")
            audio_resp = await client.get(audio_url)
            audio_resp.raise_for_status()

        return SynthResult(
            audio=audio_resp.content,
            content_type="audio/wav",
            duration_s=data.get("audio_duration_in_seconds"),
        )

    async def synthesize_sentences(
        self, text: str, *, language: str = "en", max_lookahead: int = 2,
    ) -> AsyncIterator[SynthResult]:
        """Split the reply into sentences and yield audio for each as it is
        ready, running up to `max_lookahead` syntheses concurrently. First
        audio lands in ~2-3s instead of waiting for the whole reply."""
        sentences = [s.strip() for s in _SENTENCE_RE.split(text.strip()) if s.strip()]
        if not sentences:
            return
        sem = asyncio.Semaphore(max_lookahead)

        async def _one(s: str) -> SynthResult:
            async with sem:
                return await self._synth_one(s[:4096], language)

        tasks = [asyncio.create_task(_one(s)) for s in sentences]
        for t in tasks:
            try:
                yield await t
            except Exception as exc:  # noqa: BLE001
                log.warning("sentence TTS failed, skipping: %s", exc)
