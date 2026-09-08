"""
TTS Service — gTTS (Google Translate TTS, free, no API key).

gTTS uses Google Translate's audio endpoint — completely free,
no billing, no key, works offline with cached audio.
Supports all 6 languages natively including Yoruba, Hausa, Igbo.

Install: pip install gTTS
"""

import asyncio
import io

# Language code mapping — gTTS uses ISO 639-1 codes
# Reference: https://gtts.readthedocs.io/en/latest/module.html#languages-gtts-lang
GTTS_LANG_MAP = {
    "en":  "en",   # English
    "fr":  "fr",   # French
    "yo":  "yo",   # Yoruba — supported natively by gTTS
    "ha":  "ha",   # Hausa — supported natively by gTTS
    "ig":  "ig",   # Igbo — supported natively by gTTS
    "pcm": "en",   # Nigerian Pidgin — falls back to English
}

# TLD variations give accent differences for English
# com.ng = Nigerian English, co.uk = British, com = American
GTTS_TLD_MAP = {
    "en":  "com.ng",  # Nigerian English accent
    "fr":  "fr",
    "yo":  "com",
    "ha":  "com",
    "ig":  "com",
    "pcm": "com.ng",
}


async def synthesize_speech(text: str, language: str = "en") -> bytes:
    """
    Convert text to MP3 bytes using gTTS (free Google Translate TTS).
    Runs the sync gTTS call in a thread executor to avoid blocking async.
    """
    lang_code = GTTS_LANG_MAP.get(language, "en")
    tld = GTTS_TLD_MAP.get(language, "com")

    def _synthesize():
        from gtts import gTTS
        tts = gTTS(text=text, lang=lang_code, tld=tld, slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.read()

    # Run in thread — gTTS makes HTTP requests synchronously
    loop = asyncio.get_event_loop()
    for attempt in range(3):
        try:
            audio_bytes = await loop.run_in_executor(None, _synthesize)
            if audio_bytes:
                return audio_bytes
        except Exception as e:
            if attempt == 2:
                raise RuntimeError(f"gTTS failed after 3 attempts: {e}")
            await asyncio.sleep(1.0)

    raise RuntimeError("TTS synthesis returned empty audio")
