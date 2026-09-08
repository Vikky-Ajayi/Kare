"""
SQLAlchemy engine + session factory.

Handles both the local SQLite fallback and Railway Postgres (public proxy or
internal network) from a single DATABASE_URL, normalising the scheme and adding
sslmode only where it belongs.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

Base = declarative_base()


def _normalize_db_url(raw: str) -> str:
    url = raw.strip()

    # Heroku/Railway sometimes hand out the bare "postgres://" scheme.
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]

    # Pin the driver so we don't depend on what's importable.
    if url.startswith("postgresql://") and "+psycopg2" not in url:
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]

    # Require TLS for remote Postgres; skip it for local sockets and SQLite.
    if url.startswith("postgresql") and "sslmode=" not in url:
        is_local = "@localhost" in url or "@127.0.0.1" in url
        if not is_local:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}sslmode=require"

    return url


DB_URL = _normalize_db_url(settings.DATABASE_URL)

if DB_URL.startswith("sqlite"):
    engine = create_engine(
        DB_URL,
        connect_args={"check_same_thread": False},
        echo=settings.DB_ECHO,
    )
else:
    engine = create_engine(
        DB_URL,
        pool_pre_ping=True,   # Railway's proxy drops idle connections
        pool_size=5,
        max_overflow=10,
        pool_recycle=1800,
        echo=settings.DB_ECHO,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
