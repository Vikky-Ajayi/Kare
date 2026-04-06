"""
Image Analysis Router — AI-powered medical image analysis using Groq Vision.

POST /images/analyze          — Upload & analyze any medical image
GET  /images/history          — Past image analyses for the patient
GET  /images/{analysis_id}    — Get a specific analysis result
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.middleware.auth_middleware import get_current_patient_user
from app.models import ImageAnalysis, User
from app.schemas import ImageAnalysisResponse
from app.services.groq_service import analyze_image
from app.utils.helpers import get_disclaimer

router = APIRouter(prefix="/images", tags=["Image Analysis"])

ALLOWED_IMAGE_TYPES = {
    "image/jpeg", "image/jpg", "image/png",
    "image/webp", "image/gif", "image/bmp",
}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB

IMAGE_TYPES = {
    "symptom": "Visible symptom (rash, wound, swelling, skin condition, eye, etc.)",
    "medication": "Medication / pill / packaging photo for drug identification",
    "document": "Medical document, lab result, prescription, or report",
}


@router.post("/analyze", response_model=ImageAnalysisResponse)
async def analyze_medical_image(
    file: UploadFile = File(..., description="Medical image to analyze"),
    image_type: str = Form(default="symptom", description="Type: symptom | medication | document"),
    language: str = Form(default="en"),
    current_user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    """
    Analyze a medical image using Groq Vision AI (llama-4-scout).

    Supported image types:
    - **symptom**: Rashes, wounds, skin conditions, eye infections, swelling, etc.
    - **medication**: Drug/pill photos — AI tries to identify the medication
    - **document**: Lab results, prescriptions, medical reports (OCR + summary)

    Returns structured medical observations with appropriate disclaimers.
    ⚠️ This is NOT a diagnostic tool. Always consult a healthcare professional.
    """
    # Validate image type
    if image_type not in IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image_type. Choose from: {list(IMAGE_TYPES.keys())}",
        )

    # Validate file format
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported image format. Allowed: jpeg, png, webp, gif, bmp.",
        )

    contents = await file.read()

    # Validate file size
    if len(contents) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image too large. Maximum size is 10MB.",
        )

    if len(contents) < 500:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image appears to be empty or corrupted.",
        )

    # Run AI analysis
    try:
        result = await analyze_image(contents, image_type=image_type)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Image analysis failed: {str(e)}",
        )

    # Upload image to Supabase Storage
    image_url = ""
    try:
        from supabase import create_client
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

        analysis_id = uuid.uuid4()
        ext = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "jpg"
        file_path = f"analyses/{current_user.id}/{analysis_id}.{ext}"

        supabase.storage.from_(settings.SUPABASE_BUCKET).upload(
            path=file_path,
            file=contents,
            file_options={"content-type": file.content_type, "upsert": "true"},
        )
        image_url = supabase.storage.from_(settings.SUPABASE_BUCKET).get_public_url(file_path)
    except Exception:
        # Storage failure is non-critical — analysis still succeeds
        image_url = ""

    # Build confidence disclaimer
    confidence = result.get("confidence", "low")
    confidence_note = {
        "high": "AI confidence is relatively high, but this is NOT a medical diagnosis.",
        "medium": "AI confidence is moderate. Results should be interpreted with caution.",
        "low": "AI confidence is low. Please consult a healthcare professional for proper evaluation.",
    }.get(confidence, "AI confidence is limited. Always consult a healthcare professional.")

    # Save analysis record to DB
    analysis_record = ImageAnalysis(
        patient_id=current_user.patient.id,
        image_url=image_url,
        image_type=image_type,
        analysis_result=str(result.get("medical_observations", [])),
        structured_result=result,
        confidence_note=confidence_note,
    )
    db.add(analysis_record)
    db.commit()
    db.refresh(analysis_record)

    return ImageAnalysisResponse(
        analysis_id=analysis_record.id,
        image_type=image_type,
        analysis="\n".join(result.get("medical_observations", ["No observations available."])),
        structured_findings={
            "image_content": result.get("image_content"),
            "possible_conditions": result.get("possible_conditions", []),
            "urgency": result.get("urgency", "unknown"),
            "recommendations": result.get("recommendations", ""),
            "limitations": result.get("limitations", ""),
        },
        confidence_note=confidence_note,
        disclaimer=get_disclaimer(language),
    )


@router.get("/history")
async def image_analysis_history(
    limit: int = 20,
    current_user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    """Get the patient's past image analyses."""
    analyses = (
        db.query(ImageAnalysis)
        .filter(ImageAnalysis.patient_id == current_user.patient.id)
        .order_by(ImageAnalysis.created_at.desc())
        .limit(min(limit, 100))
        .all()
    )

    return [
        {
            "id": a.id,
            "image_type": a.image_type,
            "image_url": a.image_url,
            "confidence_note": a.confidence_note,
            "created_at": a.created_at,
        }
        for a in analyses
    ]


@router.get("/{analysis_id}", response_model=ImageAnalysisResponse)
async def get_image_analysis(
    analysis_id: uuid.UUID,
    language: str = "en",
    current_user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    """Get a specific image analysis result."""
    analysis = db.query(ImageAnalysis).filter(
        ImageAnalysis.id == analysis_id,
        ImageAnalysis.patient_id == current_user.patient.id,
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image analysis not found.",
        )

    return ImageAnalysisResponse(
        analysis_id=analysis.id,
        image_type=analysis.image_type or "symptom",
        analysis=analysis.analysis_result or "",
        structured_findings=analysis.structured_result,
        confidence_note=analysis.confidence_note or "",
        disclaimer=get_disclaimer(language),
    )
