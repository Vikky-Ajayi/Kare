from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Voice Medical Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "sqlite:///./dev.db"  # fallback for local dev

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_BUCKET: str = "medical-files"

    # Groq (free tier)
    GROQ_API_KEY: str = ""
    GROQ_LLM_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_VISION_MODEL: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    GROQ_WHISPER_MODEL: str = "whisper-large-v3"

    # Free NIH Drug APIs — no key needed
    RXNORM_BASE_URL: str = "https://rxnav.nlm.nih.gov/REST"
    OPENFDA_BASE_URL: str = "https://api.fda.gov"

    # CORS — stored as plain comma-separated string in .env
    ALLOWED_ORIGINS_STR: str = "http://localhost:3000,http://localhost:5173"

    # Supported languages — stored as plain comma-separated string in .env
    SUPPORTED_LANGUAGES_STR: str = "en,yo,ha,ig,fr,pcm"

    # ── Computed properties (NOT read from .env) ─────────────────────────────

    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS_STR.split(",") if o.strip()]

    @property
    def SUPPORTED_LANGUAGES(self) -> List[str]:
        return [l.strip() for l in self.SUPPORTED_LANGUAGES_STR.split(",") if l.strip()]

    @property
    def LANGUAGE_NAMES(self) -> dict:
        return {
            "en": "English",
            "yo": "Yoruba",
            "ha": "Hausa",
            "ig": "Igbo",
            "fr": "French",
            "pcm": "Nigerian Pidgin",
        }

    @property
    def TTS_VOICE_MAP(self) -> dict:
        return {
            "en": "en-NG-EzinneNeural",   # Nigerian English voice
            "fr": "fr-FR-DeniseNeural",
            "yo": "en-NG-EzinneNeural",   # fallback — no Yoruba TTS yet
            "ha": "en-NG-EzinneNeural",   # fallback
            "ig": "en-NG-EzinneNeural",   # fallback
            "pcm": "en-NG-EzinneNeural",  # Nigerian Pidgin → Nigerian English voice
        }

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()