"""
Pregnancy companion.

POST   /pregnancy         start / onboard (give weeks, or LMP, or a known EDD, or an ultrasound)
GET    /pregnancy         current profile with live gestational age, trimester, EDD countdown
PATCH  /pregnancy         update (add an ultrasound, set baby sex, add history)
POST   /pregnancy/end     mark the pregnancy completed or ended
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth_middleware import get_current_patient_user
from app.models import User
from app.schemas import (
    MessageResponse,
    PregnancyEndRequest,
    PregnancyOnboardRequest,
    PregnancyResponse,
    PregnancyUpdateRequest,
)
from app.services import pregnancy as svc

router = APIRouter(prefix="/pregnancy", tags=["Pregnancy"])


def _serialize(p) -> PregnancyResponse:
    return PregnancyResponse(
        id=p.id,
        status=p.status,
        gestational_age=p.gestational_age_str,
        gestational_age_days=p.gestational_age_days,
        trimester=p.trimester,
        estimated_due_date=p.estimated_due_date,
        days_to_edd=p.days_to_edd,
        edd_source=p.edd_source,
        baby_sex=p.baby_sex,
        gravida=p.gravida,
        para=p.para,
        history_notes=p.history_notes,
        this_week=svc.this_week_note(p),
    )


@router.post("", response_model=PregnancyResponse)
async def start_pregnancy(
    payload: PregnancyOnboardRequest,
    user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    if not any([payload.weeks is not None, payload.lmp_date, payload.edd,
                payload.ultrasound_date and payload.ultrasound_ga_weeks is not None]):
        raise HTTPException(400, "Give at least one of: weeks pregnant, last menstrual period, "
                                 "expected due date, or an ultrasound date + gestational age.")
    profile = svc.create_or_update(
        db, user.patient,
        lmp_date=payload.lmp_date, edd=payload.edd,
        weeks=payload.weeks, days=payload.days,
        ultrasound_date=payload.ultrasound_date, ultrasound_ga_weeks=payload.ultrasound_ga_weeks,
        baby_sex=payload.baby_sex, gravida=payload.gravida, para=payload.para,
        history_notes=payload.history_notes,
    )
    db.commit()
    if profile.gestational_age_days is None:
        db.delete(profile)
        db.commit()
        raise HTTPException(400, "Could not work out the dates from what you gave. "
                                 "Try the first day of your last period, or how many weeks you are.")
    return _serialize(profile)


@router.get("", response_model=PregnancyResponse)
async def get_pregnancy(
    user: User = Depends(get_current_patient_user),
):
    p = user.patient.active_pregnancy
    if not p:
        raise HTTPException(404, "No active pregnancy on file.")
    return _serialize(p)


@router.patch("", response_model=PregnancyResponse)
async def update_pregnancy(
    payload: PregnancyUpdateRequest,
    user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    if not user.patient.active_pregnancy:
        raise HTTPException(404, "No active pregnancy to update.")
    profile = svc.create_or_update(
        db, user.patient,
        lmp_date=payload.lmp_date, edd=payload.edd,
        weeks=payload.weeks, days=payload.days,
        ultrasound_date=payload.ultrasound_date, ultrasound_ga_weeks=payload.ultrasound_ga_weeks,
        baby_sex=payload.baby_sex, gravida=payload.gravida, para=payload.para,
        history_notes=payload.history_notes,
    )
    db.commit()
    return _serialize(profile)


@router.post("/end", response_model=MessageResponse)
async def end_pregnancy(
    payload: PregnancyEndRequest,
    user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    p = user.patient.active_pregnancy
    if not p:
        raise HTTPException(404, "No active pregnancy on file.")
    svc.end_pregnancy(db, p, outcome=payload.outcome)
    db.commit()
    if payload.outcome == "loss":
        return MessageResponse(message="I'm so sorry for your loss. I've closed the pregnancy "
                                       "companion. Please lean on your midwife or doctor, and reach "
                                       "out any time you want to talk.")
    return MessageResponse(message="Pregnancy companion closed. Congratulations.")
