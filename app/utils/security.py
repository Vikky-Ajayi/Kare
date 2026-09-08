"""
Security utilities: JWT tokens, password hashing, token verification.

Password hashing: SHA-256 pre-hash (base64) -> bcrypt. The pre-hash removes
bcrypt's 72-byte input limit without truncating; base64 keeps the digest free
of NUL bytes. Uses the maintained `bcrypt` package directly (no passlib).
"""

from __future__ import annotations

import base64
import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from app.config import settings

# ─────────────────────────────────────────────
# PASSWORD HASHING
# ─────────────────────────────────────────────

def _prehash(password: str) -> bytes:
    """SHA-256 the password and base64-encode, so bcrypt sees a fixed 44-byte
    input with no NUL bytes regardless of the original password length."""
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    return base64.b64encode(digest)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_prehash(password), bcrypt.gensalt()).decode("ascii")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(_prehash(plain_password), hashed_password.encode("ascii"))
    except (ValueError, TypeError):
        return False


# ─────────────────────────────────────────────
# JWT ACCESS TOKENS
# ─────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
    if payload.get("type") != "access":
        return None
    return payload


# ─────────────────────────────────────────────
# REFRESH TOKENS (opaque, stored hashed)
# ─────────────────────────────────────────────

def create_refresh_token() -> tuple[str, str]:
    """Return (raw_token, sha256_hash). The raw token goes to the client;
    only the hash is persisted."""
    raw = secrets.token_urlsafe(64)
    return raw, hash_token(raw)


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
