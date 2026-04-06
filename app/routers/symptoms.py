"""
Symptoms Router — AI-powered symptom checking and triage.

POST /symptoms/check   — Analyze symptoms, return triage + guidance
GET  /symptoms/history — Past symptom checks for the patient
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth_middleware import get_current_patient_user
from app.models import SymptomCheck, User
from app.schemas import SymptomCheckRequest, SymptomCheckResponse
from app.services.groq_service import analyze_symptoms, build_patient_context
from app.utils.helpers import get_disclaimer

router = APIRouter(prefix="/symptoms", tags=["Symptom Checking"])


@router.post("/check", response_model=SymptomCheckResponse)
async def check_symptoms(
    payload: SymptomCheckRequest,
    current_user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    """
    AI-powered symptom analysis with triage.
    
    - Accepts symptom description in any supported language
    - Considers patient's medical history if requested
    - Returns triage level, possible conditions, and recommendations
    - Always includes a medical disclaimer
    """
    from app.config import settings

    if payload.language not in settings.SUPPORTED_LANGUAGES:
        payload.language = "en"

    # Build patient context for personalized analysis
    patient_context = None
    if payload.include_patient_history and current_user.patient:
        patient_context = build_patient_context(current_user.patient)

    # Run AI analysis
    try:
        result = await analyze_symptoms(
            symptoms_text=payload.symptoms,
            language=payload.language,
            patient_context=patient_context,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Symptom analysis failed: {str(e)}",
        )

    # Parse triage level (default to NON_URGENT if not recognized)
    triage_raw = result.get("triage_level", "NON_URGENT").upper()
    valid_levels = {"EMERGENCY", "URGENT", "SEMI_URGENT", "NON_URGENT", "SELF_CARE"}
    triage_level = triage_raw if triage_raw in valid_levels else "NON_URGENT"

    # Save symptom check to DB
    symptom_check = SymptomCheck(
        patient_id=current_user.patient.id,
        symptoms_reported=result.get("symptoms_identified", []),
        language=payload.language,
        input_text=payload.symptoms,
        ai_assessment=result.get("triage_explanation", ""),
        triage_level=triage_level,
        possible_conditions=result.get("possible_conditions", []),
        recommendations=result.get("recommendations", ""),
        disclaimer_shown=True,
    )
    db.add(symptom_check)
    db.commit()
    db.refresh(symptom_check)

    return SymptomCheckResponse(
        check_id=symptom_check.id,
        symptoms_reported=result.get("symptoms_identified", []),
        triage_level=triage_level,
        triage_explanation=result.get("triage_explanation", ""),
        possible_conditions=result.get("possible_conditions", []),
        recommendations=result.get("recommendations", "Please consult a healthcare professional."),
        when_to_seek_emergency=result.get(
            "when_to_seek_emergency",
            "If symptoms worsen significantly or you experience chest pain or difficulty breathing, seek emergency care immediately."
        ),
        disclaimer=get_disclaimer(payload.language),
        language=payload.language,
    )


@router.get("/history")
async def symptom_history(
    limit: int = 20,
    current_user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    """Get the patient's past symptom checks."""
    checks = (
        db.query(SymptomCheck)
        .filter(SymptomCheck.patient_id == current_user.patient.id)
        .order_by(SymptomCheck.created_at.desc())
        .limit(min(limit, 100))
        .all()
    )

    return [
        {
            "id": c.id,
            "symptoms_reported": c.symptoms_reported,
            "triage_level": c.triage_level,
            "recommendations": c.recommendations,
            "language": c.language,
            "created_at": c.created_at,
        }
        for c in checks
    ]


@router.get("/history/{check_id}")
async def get_symptom_check(
    check_id: uuid.UUID,
    current_user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    """Get a specific symptom check result."""
    check = db.query(SymptomCheck).filter(
        SymptomCheck.id == check_id,
        SymptomCheck.patient_id == current_user.patient.id,
    ).first()

    if not check:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Symptom check not found.")

    return {
        "id": check.id,
        "symptoms_reported": check.symptoms_reported,
        "input_text": check.input_text,
        "ai_assessment": check.ai_assessment,
        "triage_level": check.triage_level,
        "possible_conditions": check.possible_conditions,
        "recommendations": check.recommendations,
        "disclaimer": get_disclaimer(check.language or "en"),
        "language": check.language,
        "created_at": check.created_at,
    }
