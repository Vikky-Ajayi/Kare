"""Proactive follow-up: promotion, quiet hours, delivery, answer detection.
Push sending is a no-op without a real browser endpoint; we assert the message
lands in the conversation."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.providers.base import LLMResponse


class FakeLLM:
    name = "fake"

    async def complete(self, messages, **kw):
        system = messages[0]["content"] if messages else ""
        if "reaching out to a patient" in system:
            return _r("Hi Ada 😊 How are you feeling today? Has that headache eased since we spoke?")
        return _r("noted")


def _r(t):
    return LLMResponse(content=t, finish_reason="stop", model="fake", usage={"total_tokens": 5})


@pytest.fixture(autouse=True)
def _fake(monkeypatch):
    from app import providers
    providers.use_test_providers(llm=FakeLLM())
    yield
    providers.use_test_providers(None, None)


def _patient(db, tz="Africa/Lagos", enabled=True):
    from app.models import Patient, User
    from app.utils.security import hash_password
    u = User(email=f"f{datetime.now().timestamp()}@x.c", hashed_password=hash_password("x"), is_active=True)
    db.add(u)
    db.flush()
    p = Patient(user_id=u.id, first_name="Ada", last_name="Obi", timezone=tz, followups_enabled=enabled)
    db.add(p)
    db.flush()
    return u, p


def _conversation(db, user, plan=None):
    from app.models import Conversation, ConversationMessage
    c = Conversation(user_id=user.id, language="en", status="active",
                     started_at=datetime.utcnow() - timedelta(hours=20), followup_plan=plan)
    db.add(c)
    db.flush()
    db.add(ConversationMessage(conversation_id=c.id, role="user", content="I have a headache"))
    db.add(ConversationMessage(conversation_id=c.id, role="assistant", content="How long?"))
    db.flush()
    return c


@pytest.mark.asyncio
async def test_promote_and_deliver(db, monkeypatch):
    from app.models import ConversationMessage, ScheduledFollowUp
    from app.services import followups

    monkeypatch.setattr(followups, "_next_allowed", lambda *a: None)  # always within hours
    user, patient = _patient(db)
    plan = {
        "due_at": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
        "topics": [{"topic": "headache", "why": "was unresolved", "ask": "has it eased"}],
        "language": "en",
    }
    conv = _conversation(db, user, plan)
    db.commit()

    row = followups.promote_from_conversation(db, conv)
    assert row and row.status == "pending"
    db.commit()

    stats = await followups.process_due(db)
    assert stats["sent"] == 1

    row = db.get(ScheduledFollowUp, row.id)
    assert row.status == "sent" and row.generated_message
    last = (
        db.query(ConversationMessage)
        .filter(ConversationMessage.conversation_id == conv.id)
        .order_by(ConversationMessage.created_at.desc())
        .first()
    )
    assert last.role == "assistant" and "how are you" in last.content.lower()


@pytest.mark.asyncio
async def test_quiet_hours_bumps(db, monkeypatch):
    from app.services import followups

    user, patient = _patient(db, tz="Africa/Lagos")
    conv = _conversation(db, user, {"due_at": datetime.utcnow().isoformat(), "topics": [], "language": "en"})
    db.commit()
    row = followups.promote_from_conversation(db, conv)
    db.commit()

    bump_to = datetime.utcnow() + timedelta(hours=6)
    monkeypatch.setattr(followups, "_next_allowed", lambda *a: bump_to)
    stats = await followups.process_due(db)
    assert stats["bumped"] == 1
    assert abs((row.due_at - bump_to).total_seconds()) < 1


def test_real_quiet_hours_math():
    """_next_allowed with real timezone arithmetic."""
    from datetime import UTC

    from app.services.followups import _next_allowed

    class P:
        timezone = "Africa/Lagos"

    # 03:00 UTC == 04:00 Lagos -> before 08:00 -> bump to 07:00 UTC (08:00 Lagos)
    bump = _next_allowed(datetime(2026, 1, 1, 3, 0, tzinfo=UTC), P())
    assert bump is not None and bump.hour == 7
    # 12:00 UTC == 13:00 Lagos -> within hours -> no bump
    assert _next_allowed(datetime(2026, 1, 1, 12, 0, tzinfo=UTC), P()) is None


@pytest.mark.asyncio
async def test_disabled_patient_gets_cancelled(db):
    from app.services import followups

    user, patient = _patient(db, enabled=False)
    conv = _conversation(db, user, {"due_at": datetime.utcnow().isoformat(), "topics": [], "language": "en"})
    db.commit()
    assert followups.promote_from_conversation(db, conv) is None


def test_reply_marks_prior_followup_answered(auth_client, db):
    """End-to-end via the API: a sent follow-up + a patient reply -> answered."""
    from app.models import Conversation, Patient, ScheduledFollowUp, User

    user = db.query(User).filter(User.email == "pytest.patient@example.com").first()
    patient = db.query(Patient).filter(Patient.user_id == user.id).first()
    patient.followups_enabled = True
    conv = Conversation(user_id=user.id, language="en", status="active")
    db.add(conv)
    db.flush()
    fu = ScheduledFollowUp(patient_id=patient.id, conversation_id=conv.id,
                           due_at=datetime.utcnow(), status="sent", language="en",
                           sent_at=datetime.utcnow())
    db.add(fu)
    db.commit()

    r = auth_client.post("/api/v1/voice/chat", json={
        "text": "the headache is better now, thanks", "language": "en",
        "conversation_id": conv.id, "include_audio": False,
    })
    assert r.status_code == 200
    db.refresh(fu)
    assert fu.status == "answered"


# ── notification endpoints ──────────────────────────────────────────
def test_subscribe_opts_in_and_lists(auth_client, db, monkeypatch):
    from app.models import Patient, PushSubscription, User

    r = auth_client.get("/api/v1/notifications/vapid-key")
    assert r.status_code == 200 and r.json()["public_key"]

    r = auth_client.post("/api/v1/notifications/subscribe", json={
        "endpoint": "https://push.example/abc",
        "keys": {"p256dh": "k1", "auth": "k2"},
        "timezone": "Africa/Lagos",
    })
    assert r.status_code == 200
    user = db.query(User).filter(User.email == "pytest.patient@example.com").first()
    patient = db.query(Patient).filter(Patient.user_id == user.id).first()
    assert patient.followups_enabled is True
    assert db.query(PushSubscription).filter(PushSubscription.endpoint == "https://push.example/abc").count() == 1

    r = auth_client.get("/api/v1/notifications/followups")
    assert r.json()["enabled"] is True


def test_preferences_toggle_cancels_pending(auth_client, db):
    from datetime import datetime

    from app.models import Conversation, Patient, ScheduledFollowUp, User

    user = db.query(User).filter(User.email == "pytest.patient@example.com").first()
    patient = db.query(Patient).filter(Patient.user_id == user.id).first()
    patient.followups_enabled = True
    conv = Conversation(user_id=user.id, language="en")
    db.add(conv)
    db.flush()
    db.add(ScheduledFollowUp(patient_id=patient.id, conversation_id=conv.id,
                             due_at=datetime.utcnow(), status="pending"))
    db.commit()

    r = auth_client.patch("/api/v1/notifications/preferences", json={"followups_enabled": False})
    assert r.status_code == 200
    assert db.query(ScheduledFollowUp).filter(
        ScheduledFollowUp.patient_id == patient.id,
        ScheduledFollowUp.status == "cancelled",
    ).count() == 1


def test_test_push_without_subscription_404s(auth_client):
    assert auth_client.post("/api/v1/notifications/test").status_code == 404
