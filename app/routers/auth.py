"""Auth — register, login, refresh, logout, me."""

from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models import Patient, RefreshToken, User
from app.schemas import (
    AuthResponse,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _user_response(user: User) -> UserResponse:
    p = user.patient
    return UserResponse(
        id=user.id, email=user.email, preferred_language=user.preferred_language,
        is_verified=user.is_verified, role=user.role, created_at=user.created_at,
        first_name=p.first_name if p else None,
        last_name=p.last_name if p else None,
        name=f"{p.first_name} {p.last_name}".strip() if p else None,
        has_active_pregnancy=bool(p and p.active_pregnancy),
        followups_enabled=bool(p and p.followups_enabled),
    )


def _issue_tokens(db: Session, user: User) -> AuthResponse:
    access = create_access_token(data={"sub": str(user.id), "email": user.email})
    raw_refresh, hashed_refresh = create_refresh_token()
    db.add(RefreshToken(
        user_id=user.id, token_hash=hashed_refresh,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    ))
    db.commit()
    db.refresh(user)
    return AuthResponse(
        user=_user_response(user),
        access_token=access, refresh_token=raw_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists.")

    lang = payload.preferred_language if payload.preferred_language in settings.SUPPORTED_LANGUAGES else "en"
    user = User(email=payload.email, hashed_password=hash_password(payload.password),
                preferred_language=lang, is_active=True, is_verified=False)
    db.add(user)
    db.flush()
    db.add(Patient(user_id=user.id, first_name=payload.first_name, last_name=payload.last_name))
    db.commit()
    return _issue_tokens(db, user)


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password.")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is deactivated.")
    return _issue_tokens(db, user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    record = db.query(RefreshToken).filter(
        RefreshToken.token_hash == hash_token(payload.refresh_token),
        RefreshToken.is_revoked.is_(False),
        RefreshToken.expires_at > datetime.utcnow(),
    ).first()
    if not record:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token.")
    user = db.query(User).filter(User.id == record.user_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found.")

    record.is_revoked = True
    new_access = create_access_token(data={"sub": str(user.id), "email": user.email})
    raw_refresh, hashed_refresh = create_refresh_token()
    db.add(RefreshToken(
        user_id=user.id, token_hash=hashed_refresh,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    ))
    db.commit()
    return TokenResponse(access_token=new_access, refresh_token=raw_refresh,
                         expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    payload: RefreshRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(RefreshToken).filter(
        RefreshToken.token_hash == hash_token(payload.refresh_token),
        RefreshToken.user_id == current_user.id,
    ).first()
    if record:
        record.is_revoked = True
        db.commit()
    return MessageResponse(message="Logged out successfully.")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return _user_response(current_user)
