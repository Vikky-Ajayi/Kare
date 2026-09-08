"""
Sahara (Intron Voice) implementation of VoiceProvider.

STT  : POST {base}/file/v1/upload/sync   (multipart, <=120s audio, telehealth category)
TTS  : POST {base}/tts/v1/generate       (JSON -> audio_path URL -> fetch bytes)

Streaming (WebSocket) transcribe/synthesize land in P1; the REST paths here are
the fallback and what the benchmark harness calls.
"""

from __future__ import annotations

import logging

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import settings
from app.providers.base import SynthResult, Transcript, VoiceProvider

log = logging.getLogger("kare.voice")

# Kare code -> Sahara STT language code. Sahara's code-switch codes match ours.
_STT_LANG = {"en": "en", "yo": "yo", "ha": "ha", "ig": "ig", "pcm": "pcm", "fr": "fr"}


class _Retryable(Exception):
    pass


class SaharaVoice(VoiceProvider):
    name = "sahara"

    def __init__(self) -> None:
        self._base = settings.SAHARA_INFER_BASE_URL.rstrip("/")
        self._headers = {"Authorization": f"Bearer {settings.SAHARA_API_KEY}"}

    # ── STT ───────────────────────────────────────────────────────────────
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
            "use_language_asr_input": _STT_LANG.get(language, "en"),
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
        text = (payload.get("audio_transcript") or "").strip()
        return Transcript(
            text=text,
            language=data["use_language_asr_input"],
            duration_s=payload.get("processed_audio_duration_in_seconds"),
            raw=payload,
        )

    # ── TTS ───────────────────────────────────────────────────────────────
    @retry(
        retry=retry_if_exception_type(_Retryable),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=15),
        reraise=True,
    )
    async def synthesize(self, text: str, *, language: str = "en") -> SynthResult:
        voice = settings.SAHARA_VOICE_MAP.get(language, settings.SAHARA_VOICE_MAP["en"])
        body = {
            "text": text[:4096],
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
