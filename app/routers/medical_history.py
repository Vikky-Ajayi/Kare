"""
Medical History Router — CRUD for patient medical conditions.
"""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import MedicalCondition, User
from app.schemas import MedicalConditionCreate, MedicalConditionResponse, MedicalConditionUpdate, MessageResponse
from app.middleware.auth_middleware import get_current_patient_user

router = APIRouter(prefix="/medical-history", tags=["Medical History"])


def _get_condition_or_404(condition_id: uuid.UUID, patient_id: uuid.UUID, db: Session) -> MedicalCondition:
    condition = db.query(MedicalCondition).filter(
        MedicalCondition.id == condition_id,
        MedicalCondition.patient_id == patient_id,
    ).first()
    if not condition:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Condition not found.")
    return condition


@router.get("/", response_model=List[MedicalConditionResponse])
async def list_conditions(
    status_filter: str = None,
    current_user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    """List all medical conditions for the current patient."""
    query = db.query(MedicalCondition).filter(
        MedicalCondition.patient_id == current_user.patient.id
    )
    if status_filter:
        query = query.filter(MedicalCondition.status == status_filter)

    return query.order_by(MedicalCondition.created_at.desc()).all()


@router.post("/", response_model=MedicalConditionResponse, status_code=status.HTTP_201_CREATED)
async def add_condition(
    payload: MedicalConditionCreate,
    current_user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    """Add a new medical condition to the patient's history."""
    condition = MedicalCondition(
        patient_id=current_user.patient.id,
        **payload.model_dump(),
    )
    db.add(condition)
    db.commit()
    db.refresh(condition)
    return condition


@router.get("/{condition_id}", response_model=MedicalConditionResponse)
async def get_condition(
    condition_id: uuid.UUID,
    current_user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    return _get_condition_or_404(condition_id, current_user.patient.id, db)


@router.put("/{condition_id}", response_model=MedicalConditionResponse)
async def update_condition(
    condition_id: uuid.UUID,
    payload: MedicalConditionUpdate,
    current_user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    condition = _get_condition_or_404(condition_id, current_user.patient.id, db)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(condition, field, value)

    db.commit()
    db.refresh(condition)
    return condition


@router.delete("/{condition_id}", response_model=MessageResponse)
async def delete_condition(
    condition_id: uuid.UUID,
    current_user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    condition = _get_condition_or_404(condition_id, current_user.patient.id, db)
    db.delete(condition)
    db.commit()
    return MessageResponse(message="Condition removed from medical history.")
