"""Pregnancy companion: dating maths, onboarding API, and the mode overlay."""

from __future__ import annotations

from datetime import date, timedelta

import pytest


# ── dating maths (pure) ─────────────────────────────────────────────
def test_edd_from_lmp():
    from app.models import PregnancyProfile

    lmp = date.today() - timedelta(weeks=10)
    p = PregnancyProfile(lmp_date=lmp, edd_source="lmp")
    assert p.estimated_due_date == lmp + timedelta(days=280)
    assert p.gestational_age_days == 70
    assert p.gestational_age_str == "10w0d"
    assert p.trimester == 1


def test_edd_from_known_edd_wins():
    from app.models import PregnancyProfile

    edd = date.today() + timedelta(days=100)
    p = PregnancyProfile(lmp_date=date.today() - timedelta(days=200), edd=edd, edd_source="known_edd")
    assert p.estimated_due_date == edd
    assert p.days_to_edd == 100
    assert p.trimester == 2  # 280-100 = 180 days = ~26w


def test_ultrasound_overrides_lmp():
    from app.models import PregnancyProfile

    scan = date.today() - timedelta(days=30)
    p = PregnancyProfile(
        lmp_date=date.today() - timedelta(days=100),   # would say ~14w
        ultrasound_date=scan, ultrasound_ga_days=8 * 7, edd_source="ultrasound",
    )
    # at the scan she was 8w; +30 days -> ~12w2d, not 14w
    assert 12 * 7 <= p.gestational_age_days <= 13 * 7


def test_weeks_anchor_via_api(auth_client):
    r = auth_client.post("/api/v1/pregnancy", json={"weeks": 24, "days": 3, "baby_sex": "female"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["gestational_age"].startswith("24w")
    assert body["trimester"] == 2
    assert body["baby_sex"] == "female"
    assert body["this_week"]

    r = auth_client.get("/api/v1/pregnancy")
    assert r.json()["gestational_age"].startswith("24w")


def test_pregnancy_requires_an_anchor(auth_client):
    assert auth_client.post("/api/v1/pregnancy", json={"baby_sex": "male"}).status_code == 400


def test_end_pregnancy_loss_is_gentle(auth_client):
    auth_client.post("/api/v1/pregnancy", json={"weeks": 12})
    r = auth_client.post("/api/v1/pregnancy/end", json={"outcome": "loss"})
    assert r.status_code == 200
    assert "sorry for your loss" in r.json()["message"].lower()
    assert auth_client.get("/api/v1/pregnancy").status_code == 404


# ── the consultation overlay ───────────────────────────────────────
@pytest.mark.asyncio
async def test_pregnancy_mode_overlay_and_redflag(db):
    from app.agent import redflags
    from app.models import Patient, User
    from app.services.consultation import _is_pregnant, _system_prompt
    from app.services.pregnancy import create_or_update

    u = User(email="preg@x.c", hashed_password="x", is_active=True)
    db.add(u)
    db.flush()
    p = Patient(user_id=u.id, first_name="Tayo", last_name="A")
    db.add(p)
    db.flush()
    create_or_update(db, p, weeks=30, baby_sex="male")
    db.flush()

    assert _is_pregnant(p) is True
    prompt = _system_prompt(p, "gathering")
    assert "PREGNANCY MODE" in prompt
    assert "our little boy" in prompt
    assert "30w" in prompt

    # pregnancy keyword red flag only bites when the pregnant flag is set
    assert redflags.keyword_check("the baby has not moved all day", pregnant=True) is not None
    assert redflags.keyword_check("the baby has not moved all day", pregnant=False) is None
