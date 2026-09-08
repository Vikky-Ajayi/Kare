"""
Test fixtures. An in-memory SQLite database (kept alive by StaticPool) is
created and dropped around every test. Each request gets its own Session from
the test sessionmaker, matching how the real app behaves per request.
"""

from __future__ import annotations

import os

# Must be set before any `app.*` import so settings/engine pick it up.
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-use-only-abc123")
os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("SAHARA_API_KEY", "test")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import app.models  # noqa: E402,F401
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def _schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    """Direct DB access for a test. Separate session from the request path."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client():
    def _override_get_db():
        session = TestingSessionLocal()
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
    """A client already registered and logged in as a fresh patient."""
    email = "pytest.patient@example.com"
    client.post("/api/v1/auth/register", json={
        "email": email, "password": "pytest-strong-pass",
        "first_name": "Pytest", "last_name": "Patient", "preferred_language": "en",
    })
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "pytest-strong-pass"})
    token = r.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
