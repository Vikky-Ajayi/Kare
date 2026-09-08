"""
Test fixtures. Uses a temp file SQLite DB (so every connection — including the
ones the WebSocket handler opens directly via SessionLocal — sees the same
schema) and recreates it around each test.
"""

from __future__ import annotations

import os
import tempfile

_DB_PATH = os.path.join(tempfile.gettempdir(), f"kare_test_{os.getpid()}.sqlite3")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_DB_PATH}")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-use-only-abc123")
os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("SAHARA_API_KEY", "test")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.models  # noqa: E402,F401
from app.database import Base, SessionLocal, engine, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client():
    def _override_get_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_client(client):
    email = "pytest.patient@example.com"
    client.post("/api/v1/auth/register", json={
        "email": email, "password": "pytest-strong-pass",
        "first_name": "Pytest", "last_name": "Patient", "preferred_language": "en",
    })
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "pytest-strong-pass"})
    token = r.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


def pytest_sessionfinish(session, exitstatus):
    import contextlib
    with contextlib.suppress(OSError):
        os.remove(_DB_PATH)
