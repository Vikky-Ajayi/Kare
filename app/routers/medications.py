"""
Medications Router — CRUD for patient medications + interaction checks.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth_middleware import get_current_patient_user
from app.models import Medication, User
from app.schemas import MedicationCreate, MedicationResponse, MedicationUpdate, MessageResponse
from app.services import drug_interaction_service

router = APIRouter(prefix="/medications", tags=["Medications"])


def _get_medication_or_404(med_id: uuid.UUID, patient_id: uuid.UUID, db: Session) -> Medication:
    med = db.query(Medication).filter(
        Medication.id == med_id,
        Medication.patient_id == patient_id,
    ).first()
    if not med:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found.")
    return med


@router.get("/", response_model=list[MedicationResponse])
async def list_medications(
    status_filter: str | None = Query(None, alias="status"),
    current_user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    """List all medications for the current patient."""
    query = db.query(Medication).filter(Medication.patient_id == current_user.patient.id)

    if status_filter:
        query = query.filter(Medication.status == status_filter)

    return query.order_by(Medication.created_at.desc()).all()


@router.post("/", response_model=MedicationResponse, status_code=status.HTTP_201_CREATED)
async def add_medication(
    payload: MedicationCreate,
    current_user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    """Add a new medication. Auto-resolves RxNorm CUI if not provided."""
    # Try to resolve RxCUI from drug name (for interaction checking later)
    rxcui = payload.rxnorm_cui
    if not rxcui and payload.drug_name:
        try:
            rxcui = await drug_interaction_service.get_rxcui(payload.drug_name)
        except Exception:
            pass  # Non-critical — skip if API is down

    medication = Medication(
        patient_id=current_user.patient.id,
        rxnorm_cui=rxcui,
        **payload.model_dump(exclude={"rxnorm_cui"}),
    )
    medication.rxnorm_cui = rxcui

    db.add(medication)
    db.commit()
    db.refresh(medication)
    return medication


@router.get("/{med_id}", response_model=MedicationResponse)
async def get_medication(
    med_id: uuid.UUID,
    current_user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    return _get_medication_or_404(med_id, current_user.patient.id, db)


@router.put("/{med_id}", response_model=MedicationResponse)
async def update_medication(
    med_id: uuid.UUID,
    payload: MedicationUpdate,
    current_user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    med = _get_medication_or_404(med_id, current_user.patient.id, db)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(med, field, value)

    db.commit()
    db.refresh(med)
    return med


@router.delete("/{med_id}", response_model=MessageResponse)
async def delete_medication(
    med_id: uuid.UUID,
    current_user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    med = _get_medication_or_404(med_id, current_user.patient.id, db)
    db.delete(med)
    db.commit()
    return MessageResponse(message="Medication removed.")


