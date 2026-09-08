"""
Web Push subscriptions + the patient's proactive check-in feed.

GET   /notifications/vapid-key       public key for the browser
POST  /notifications/subscribe       register a push endpoint (opts into check-ins)
POST  /notifications/unsubscribe     drop an endpoint
PATCH /notifications/preferences     toggle proactive check-ins / set timezone
GET   /notifications/followups       list this patient's check-ins
POST  /notifications/test            send a test push now
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.middleware.auth_middleware import get_current_patient_user, get_current_user
from app.models import PushSubscription, ScheduledFollowUp, User
from app.schemas import (
    FollowupPreferences,
    MessageResponse,
    PushSubscribeRequest,
    PushUnsubscribeRequest,
)
from app.services import push

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/vapid-key")
async def vapid_key():
    if not settings.VAPID_PUBLIC_KEY:
        raise HTTPException(503, "Push notifications are not configured.")
    return {"public_key": settings.VAPID_PUBLIC_KEY}


@router.post("/subscribe", response_model=MessageResponse)
async def subscribe(
    payload: PushSubscribeRequest,
    user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    sub = (
        db.query(PushSubscription)
        .filter(PushSubscription.endpoint == payload.endpoint)
        .first()
    )
    if sub and sub.user_id != user.id:
        sub.user_id = user.id   # endpoint moved to this account
    if not sub:
        sub = PushSubscription(user_id=user.id, endpoint=payload.endpoint,
                               p256dh=payload.keys.p256dh, auth=payload.keys.auth)
        db.add(sub)
    sub.p256dh = payload.keys.p256dh
    sub.auth = payload.keys.auth
    sub.is_active = True
    sub.last_used_at = datetime.utcnow()
    if payload.timezone:
        sub.timezone = payload.timezone
        user.patient.timezone = payload.timezone

    # subscribing is the opt-in to proactive check-ins
    user.patient.followups_enabled = True
    db.commit()
    return MessageResponse(message="Subscribed. Kare can now check in on you.")


@router.post("/unsubscribe", response_model=MessageResponse)
async def unsubscribe(
    payload: PushUnsubscribeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(PushSubscription).filter(
        PushSubscription.endpoint == payload.endpoint,
        PushSubscription.user_id == user.id,
    ).update({"is_active": False})
    db.commit()
    return MessageResponse(message="Unsubscribed on this device.")


@router.patch("/preferences", response_model=MessageResponse)
async def preferences(
    payload: FollowupPreferences,
    user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    user.patient.followups_enabled = payload.followups_enabled
    if payload.timezone:
        user.patient.timezone = payload.timezone
    if not payload.followups_enabled:
        db.query(ScheduledFollowUp).filter(
            ScheduledFollowUp.patient_id == user.patient.id,
            ScheduledFollowUp.status == "pending",
        ).update({"status": "cancelled", "reason": "patient opted out"})
    db.commit()
    return MessageResponse(
        message="Check-ins turned on." if payload.followups_enabled else "Check-ins turned off."
    )


@router.get("/followups")
async def list_followups(
    user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(ScheduledFollowUp)
        .filter(ScheduledFollowUp.patient_id == user.patient.id)
        .order_by(ScheduledFollowUp.created_at.desc())
        .limit(50)
        .all()
    )
    return {
        "enabled": user.patient.followups_enabled,
        "items": [
            {
                "id": f.id, "conversation_id": f.conversation_id, "status": f.status,
                "due_at": f.due_at, "sent_at": f.sent_at, "answered_at": f.answered_at,
                "message": f.generated_message,
                "topics": [t.get("topic") for t in (f.topics or [])],
            }
            for f in rows
        ],
    }


@router.post("/followups/{followup_id}/clicked", response_model=MessageResponse)
async def mark_clicked(
    followup_id: str,
    user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(ScheduledFollowUp)
        .filter(ScheduledFollowUp.id == followup_id,
                ScheduledFollowUp.patient_id == user.patient.id)
        .first()
    )
    if row and not row.clicked_at:
        row.clicked_at = datetime.utcnow()
        db.commit()
    return MessageResponse(message="ok")


@router.post("/test", response_model=MessageResponse)
async def test_push(
    user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    n = push.send_to_user(
        db, user.id,
        title="Kare",
        body=f"Hi {user.patient.first_name} — this is a test check-in. Everything's working.",
        url=f"{settings.PUBLIC_APP_URL.rstrip('/')}/dashboard",
        tag="kare-test",
    )
    if not n:
        raise HTTPException(404, "No active push subscription on any device.")
    return MessageResponse(message=f"Sent to {n} device(s).")
