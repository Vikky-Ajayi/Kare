"""
Medications Router — CRUD for patient medications.
Includes medication image upload and AI-based drug identification.
"""

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.middleware.auth_middleware import get_current_patient_user
from app.models import Medication, User
from app.schemas import MedicationCreate, MedicationResponse, MedicationUpdate, MessageResponse
from app.services import drug_interaction_service

router = APIRouter(prefix="/medications", tags=["Medications"])

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB


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


@router.post("/{med_id}/image", response_model=MedicationResponse)
async def upload_medication_image(
    med_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    """Upload a photo of the medication/pill for identification."""
    med = _get_medication_or_404(med_id, current_user.patient.id, db)

    # Validate file
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type. Allowed: {ALLOWED_IMAGE_TYPES}",
        )

    contents = await file.read()
    if len(contents) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image too large. Max 5MB.",
        )

    # Upload to Supabase Storage
    try:
        from supabase import create_client
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

        file_path = f"medications/{current_user.id}/{med_id}.jpg"
        supabase.storage.from_(settings.SUPABASE_BUCKET).upload(
            path=file_path,
            file=contents,
            file_options={"content-type": file.content_type, "upsert": "true"},
        )

        public_url = supabase.storage.from_(settings.SUPABASE_BUCKET).get_public_url(file_path)
        med.image_url = public_url
        db.commit()
        db.refresh(med)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image upload failed: {str(e)}",
        )

    return med
