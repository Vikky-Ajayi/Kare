"""
Application settings, loaded from environment / .env (pydantic-settings v2).

Only scalars are read from the environment. Anything derived (lists, maps) is a
computed property so the .env stays flat and copy-pasteable.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── App ────────────────────────────────────────────────────────────────
    APP_NAME: str = "Kare"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    # ── Security ───────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Database ───────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./dev.db"  # local fallback only
    DB_ECHO: bool = False  # SQL statement logging (noisy; separate from DEBUG)

    # ── Groq (reasoning brain + benchmark Whisper) ─────────────────────────
    GROQ_API_KEY: str = ""
    GROQ_LLM_MODEL: str = "openai/gpt-oss-120b"
    GROQ_LLM_MODEL_FAST: str = "openai/gpt-oss-20b"
    GROQ_VISION_MODEL: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    GROQ_WHISPER_MODEL: str = "whisper-large-v3"
    GROQ_WHISPER_MODEL_TURBO: str = "whisper-large-v3-turbo"

    # ── Sahara / Intron Voice (STT + TTS) ──────────────────────────────────
    SAHARA_API_KEY: str = ""
    SAHARA_INFER_BASE_URL: str = "https://infer.voice.intron.io"
    SAHARA_STT_STREAM_URL: str = "wss://infer.voice.intron.io/stt/v1/stream"
    SAHARA_TTS_STREAM_URL: str = "wss://infer.voice.intron.io/tts/v1/stream"
    SAHARA_STT_CATEGORY: str = "file_category_telehealth"

    # ── Web Push + proactive follow-up ────────────────────────────────────
    VAPID_PUBLIC_KEY: str = ""
    VAPID_PRIVATE_KEY: str = ""
    VAPID_SUBJECT: str = "mailto:admin@kare.health"
    PUBLIC_APP_URL: str = "http://localhost:3000"   # base for notification deep links
    FOLLOWUP_QUIET_START: int = 8    # local hour — no check-ins before this
    FOLLOWUP_QUIET_END: int = 20     # local hour — no check-ins after this
    FOLLOWUP_MIN_GAP_HOURS: int = 20  # min hours between two proactive pushes to one patient
    FOLLOWUP_MAX_ATTEMPTS: int = 2   # stop after this many unanswered check-ins on a thread
    INPROCESS_SCHEDULER: bool = False  # local dev: run the follow-up tick in-app (prod: Railway cron)
    INPROCESS_SCHEDULER_MINUTES: int = 15

    # ── Optional / benchmark ──────────────────────────────────────────────
    HF_TOKEN: str = ""
    OPENAI_API_KEY: str = ""

    # ── Free public APIs (no key) ─────────────────────────────────────────
    RXNORM_BASE_URL: str = "https://rxnav.nlm.nih.gov/REST"
    OPENFDA_BASE_URL: str = "https://api.fda.gov"

    # ── Comma-separated strings in .env ───────────────────────────────────
    ALLOWED_ORIGINS_STR: str = "http://localhost:3000,http://localhost:5173"
    SUPPORTED_LANGUAGES_STR: str = "en,yo,ha,ig,pcm"

    # ── Derived ───────────────────────────────────────────────────────────

    @property
    def ALLOWED_ORIGINS(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS_STR.split(",") if o.strip()]

    @property
    def SUPPORTED_LANGUAGES(self) -> list[str]:
        return [x.strip() for x in self.SUPPORTED_LANGUAGES_STR.split(",") if x.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def LANGUAGE_NAMES(self) -> dict:
        return {
            "en": "English",
            "yo": "Yoruba",
            "ha": "Hausa",
            "ig": "Igbo",
            "pcm": "Nigerian Pidgin",
        }

    @property
    def SAHARA_VOICE_MAP(self) -> dict:
        """Kare language code -> Sahara TTS params, verified against the live API.
        Sahara TTS speaks English only *with* an African accent (there is no
        neutral 'en'); we route Kare's 'en' through the Yoruba English accent.
        French has no Sahara TTS voice, so 'fr' is not an offered UI language."""
        return {
            "en":  {"voice_language": "en",  "voice_accent": "yoruba", "voice_gender": "female"},
            "yo":  {"voice_language": "yo",  "voice_accent": "yoruba", "voice_gender": "female"},
            "ha":  {"voice_language": "ha",  "voice_accent": "hausa",  "voice_gender": "female"},
            "ig":  {"voice_language": "ig",  "voice_accent": "igbo",   "voice_gender": "female"},
            "pcm": {"voice_language": "pcm", "voice_accent": "pidgin", "voice_gender": "female"},
        }

    def validate_runtime(self) -> list[str]:
        """Return a list of fatal misconfigurations. Empty = OK. Called at
        app startup (see app.main), not at import time."""
        problems: list[str] = []
        if not self.DEBUG:
            if self.SECRET_KEY == "change-me-in-production" or len(self.SECRET_KEY) < 32:
                problems.append("SECRET_KEY must be a strong value (>=32 chars) when DEBUG=False")
            if self.is_sqlite:
                problems.append("DATABASE_URL still points at SQLite; set the Postgres URL")
            if not self.GROQ_API_KEY:
                problems.append("GROQ_API_KEY is not set")
            if not self.SAHARA_API_KEY:
                problems.append("SAHARA_API_KEY is not set")
        return problems


settings = Settings()
