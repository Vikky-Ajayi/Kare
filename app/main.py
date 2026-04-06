"""
Voice Medical Assistant — FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine, Base

# Import all models so Alembic / SQLAlchemy can discover them
from app.models import (   # noqa: F401
    User, RefreshToken, Patient, MedicalCondition,
    Medication, Conversation, ConversationMessage,
    SymptomCheck, ImageAnalysis, AuditLog,
)

# Routers
from app.routers import (
    auth, patients, medical_history, medications,
    voice, symptoms, drug_interactions, image_analysis
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.DEBUG:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created (DEBUG mode)")
    yield
    print("👋 Shutting down Voice Medical Assistant")


app = FastAPI(
    title="🩺 Voice Medical Assistant API",
    description=(
        "A voice-first, multilingual AI medical assistant for Nigeria and Africa. "
        "Supports English, Yoruba, Hausa, Igbo, French, and Nigerian Pidgin.\n\n"
        "**⚠️ Disclaimer:** This API is for informational purposes only and does NOT "
        "constitute medical advice. Always consult a licensed healthcare professional."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────
# allow_origins=["*"] opens access for local dev and file:// testing.
# IMPORTANT: When deploying to production, replace ["*"] with your
# actual frontend domain e.g. ["https://yourapp.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── GLOBAL ERROR HANDLER ─────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if settings.DEBUG:
        raise exc
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again."},
    )


# ── ROUTES ───────────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(patients.router, prefix=API_PREFIX)
app.include_router(medical_history.router, prefix=API_PREFIX)
app.include_router(medications.router, prefix=API_PREFIX)
app.include_router(voice.router, prefix=API_PREFIX)
app.include_router(symptoms.router, prefix=API_PREFIX)
app.include_router(drug_interactions.router, prefix=API_PREFIX)
app.include_router(image_analysis.router, prefix=API_PREFIX)


# ── HEALTH & ROOT ─────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "supported_languages": settings.LANGUAGE_NAMES,
        "disclaimer": (
            "This service is for informational purposes only "
            "and does not constitute medical advice."
        ),
    }


@app.get("/health", tags=["Health"])
async def health_check():
    from sqlalchemy import text
    from app.database import SessionLocal
    db_status = "ok"
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception:
        db_status = "error"
    return {
        "status": "healthy" if db_status == "ok" else "degraded",
        "database": db_status,
        "version": settings.APP_VERSION,
    }


@app.get("/languages", tags=["Config"])
async def list_languages():
    return {
        "supported_languages": [
            {
                "code": code,
                "name": name,
                "tts_voice": settings.TTS_VOICE_MAP.get(code),
            }
            for code, name in settings.LANGUAGE_NAMES.items()
        ]
    }