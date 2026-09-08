"""
Kare — FastAPI application entry point.

A voice-first, multilingual, memory-keeping health companion for Nigeria and
West Africa. Speech runs on Sahara (Intron) code-switch models; reasoning on
Groq. See the build plan for architecture.
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import the models package so every ORM class registers on Base.metadata
# (used by Alembic and by any reflective tooling).
import app.models  # noqa: F401
from app.config import settings
from app.database import engine
from app.routers import (
    auth,
    drug_interactions,
    image_analysis,
    medical_history,
    medications,
    patients,
    symptoms,
    voice,
)

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
)
log = logging.getLogger("kare")


@asynccontextmanager
async def lifespan(app: FastAPI):
    problems = settings.validate_runtime()
    for p in problems:
        log.error("CONFIG: %s", p)
    if problems and not settings.DEBUG:
        log.critical("Refusing to start with a broken production config.")
        sys.exit(1)

    # Fail loudly if migrations haven't been applied.
    try:
        from sqlalchemy import inspect
        tables = set(inspect(engine).get_table_names())
        if "alembic_version" not in tables:
            log.warning("No alembic_version table — run `alembic upgrade head`.")
        else:
            log.info("DB reachable, %d tables.", len(tables))
    except Exception as exc:  # noqa: BLE001
        log.error("DB not reachable at startup: %s", exc)

    log.info("%s v%s starting (debug=%s)", settings.APP_NAME, settings.APP_VERSION, settings.DEBUG)
    yield
    log.info("Shutting down.")


app = FastAPI(
    title="Kare API",
    description=(
        "A voice-first, multilingual, memory-keeping health companion for "
        "Nigeria and West Africa. English, Yoruba, Hausa, Igbo, French, and "
        "Nigerian Pidgin — including natural code-switching.\n\n"
        "**Disclaimer:** informational use only. Not a substitute for a "
        "licensed healthcare professional."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=False,   # auth is via Authorization header, not cookies
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.exception("Unhandled error on %s %s", request.method, request.url.path)
    if settings.DEBUG:
        raise exc
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again."},
    )


API_PREFIX = "/api/v1"
for r in (auth, patients, medical_history, medications,
          voice, symptoms, drug_interactions, image_analysis):
    app.include_router(r.router, prefix=API_PREFIX)


@app.get("/", tags=["Health"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "supported_languages": settings.LANGUAGE_NAMES,
        "disclaimer": "Informational use only; not medical advice.",
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
    except Exception:  # noqa: BLE001
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
            {"code": code, "name": settings.LANGUAGE_NAMES.get(code, code),
             "voice": settings.SAHARA_VOICE_MAP.get(code)}
            for code in settings.SUPPORTED_LANGUAGES
        ]
    }
