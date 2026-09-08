"""
Patients Router — manage the authenticated user's patient profile.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models import Patient, User
from app.schemas import PatientResponse, PatientUpdate
from app.utils.helpers import calculate_age, calculate_bmi

router = APIRouter(prefix="/patients", tags=["Patient Profile"])


def _serialize_patient(patient: Patient) -> dict:
    """Add computed fields to patient response."""
    data = {
        "id": patient.id,
        "user_id": patient.user_id,
        "first_name": patient.first_name,
        "last_name": patient.last_name,
        "date_of_birth": patient.date_of_birth,
        "gender": patient.gender,
        "phone_number": patient.phone_number,
        "country": patient.country,
        "state": patient.state,
        "blood_group": patient.blood_group,
        "height_cm": patient.height_cm,
        "weight_kg": patient.weight_kg,
        "allergies": patient.allergies or [],
        "emergency_contact_name": patient.emergency_contact_name,
        "emergency_contact_phone": patient.emergency_contact_phone,
        "profile_photo_url": patient.profile_photo_url,
        "age": calculate_age(patient.date_of_birth),
        "bmi": calculate_bmi(patient.height_cm, patient.weight_kg),
        "created_at": patient.created_at,
    }
    return data


@router.get("/me", response_model=PatientResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the current user's patient profile."""
    if not current_user.patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found.",
        )
    return _serialize_patient(current_user.patient)


@router.put("/me", response_model=PatientResponse)
async def update_my_profile(
    payload: PatientUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the current user's patient profile."""
    patient = current_user.patient
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found.")

    # Apply only provided fields
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(patient, field, value)

    db.commit()
    db.refresh(patient)
    return _serialize_patient(patient)


@router.patch("/me/language")
async def update_language(
    language: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the user's preferred language."""
    from app.config import settings
    if language not in settings.SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language. Supported: {settings.SUPPORTED_LANGUAGES}",
        )
    current_user.preferred_language = language
    db.commit()
    return {"message": "Language updated.", "language": language}


@router.delete("/me")
async def delete_my_account(
    confirm: str = "",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Permanently delete this account and everything linked to it — profile,
    conditions, medications, conversations, symptom checks, health notes.
    Requires ?confirm=DELETE. Irreversible.
    """
    if confirm != "DELETE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Add ?confirm=DELETE to permanently delete your account and all data.",
        )
    from app.models import AuditLog

    db.add(AuditLog(user_id=current_user.id, action="account_deleted",
                    resource_type="user", resource_id=current_user.id))
    db.commit()
    # audit_logs.user_id is ON DELETE SET NULL, so the record survives the user
    db.delete(current_user)   # cascades to patient, conversations, etc.
    db.commit()
    return {"message": "Your account and all associated data have been deleted."}
