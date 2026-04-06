"""
Drug Interactions Router — powered by free NIH RxNorm & OpenFDA APIs.

GET  /drugs/search                    — Search drugs by name
GET  /drugs/info/{rxcui}              — Drug info by RxCUI
POST /drugs/interactions              — Check interactions between multiple drugs
GET  /drugs/interactions/my-meds      — Check interactions among patient's active meds
GET  /drugs/warnings/{drug_name}      — Get drug warnings from OpenFDA
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth_middleware import get_current_patient_user, get_current_user
from app.models import User
from app.schemas import DrugInteractionRequest, DrugInteractionResponse, DrugSearchResponse
from app.services import drug_interaction_service
from app.services.groq_service import consult_patient
from app.utils.helpers import get_disclaimer

router = APIRouter(prefix="/drugs", tags=["Drug Interactions"])


@router.get("/search", response_model=List[DrugSearchResponse])
async def search_drugs(
    q: str = Query(min_length=2, description="Drug name to search"),
    current_user: User = Depends(get_current_user),
):
    """
    Search for a drug by name using RxNorm (free NIH API).
    Returns matching drugs with their RxCUI codes.
    Useful for autocomplete in the frontend.
    """
    try:
        results = await drug_interaction_service.search_drugs(q)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Drug search failed: {str(e)}",
        )

    return [
        DrugSearchResponse(
            rxcui=r.get("rxcui", ""),
            name=r.get("name", ""),
            synonyms=[],
        )
        for r in results
    ]


@router.get("/info/{rxcui}")
async def get_drug_info(
    rxcui: str,
    current_user: User = Depends(get_current_user),
):
    """Get drug details by RxNorm CUI."""
    try:
        info = await drug_interaction_service.get_drug_info(rxcui)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    if not info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Drug not found.")

    return info


@router.post("/interactions", response_model=DrugInteractionResponse)
async def check_drug_interactions(
    payload: DrugInteractionRequest,
    language: str = Query(default="en"),
    current_user: User = Depends(get_current_user),
):
    """
    Check for drug interactions between 2+ drugs.
    Uses NIH RxNav Interaction API (free, no key needed).
    Returns interactions with AI-generated plain-language summary.
    """
    if len(payload.drug_names) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide at least 2 drug names to check.",
        )

    if len(payload.drug_names) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 drugs at a time.",
        )

    try:
        result = await drug_interaction_service.check_interactions_by_name(payload.drug_names)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Drug interaction check failed: {str(e)}",
        )

    interactions = result.get("interactions", [])

    # Build AI summary of findings in user's language
    if interactions:
        interaction_text = "\n".join(
            f"- {i['drug_1']} + {i['drug_2']}: {i['description']} (Severity: {i['severity']})"
            for i in interactions
        )
        ai_prompt = (
            f"Summarize these drug interactions in simple, patient-friendly language:\n{interaction_text}\n"
            f"Keep it under 150 words. No markdown. Be clear about what the patient should do."
        )
    else:
        ai_prompt = (
            f"The following drugs were checked for interactions and no major interactions were found: "
            f"{', '.join(payload.drug_names)}. Write a brief, reassuring patient-friendly message in 2 sentences."
        )

    try:
        ai_summary = await consult_patient(
            user_message=ai_prompt,
            language=language,
        )
    except Exception:
        ai_summary = (
            f"Found {len(interactions)} interaction(s) between the checked medications. "
            "Please consult your pharmacist or doctor before combining these medications."
        )

    return DrugInteractionResponse(
        drugs_checked=payload.drug_names,
        interactions_found=len(interactions),
        interactions=[
            {
                "drug_1": i.get("drug_1", ""),
                "drug_2": i.get("drug_2", ""),
                "severity": i.get("severity"),
                "description": i.get("description", ""),
                "source": i.get("source", "NIH RxNav"),
            }
            for i in interactions
        ],
        ai_summary=ai_summary,
        disclaimer=get_disclaimer(language),
    )


@router.get("/interactions/my-meds")
async def check_my_medication_interactions(
    language: str = Query(default="en"),
    current_user: User = Depends(get_current_patient_user),
    db: Session = Depends(get_db),
):
    """
    Check interactions between ALL of the patient's currently active medications.
    Useful for a patient to run a safety check on their full medication list.
    """
    patient = current_user.patient
    active_meds = [m.drug_name for m in patient.medications if m.status == "active"]

    if len(active_meds) < 2:
        return {
            "message": "You need at least 2 active medications to check for interactions.",
            "active_medications": active_meds,
        }

    try:
        result = await drug_interaction_service.check_interactions_by_name(active_meds)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    return {
        "active_medications": active_meds,
        "interactions_found": result.get("interactions_found", 0),
        "interactions": result.get("interactions", []),
        "unresolved_drugs": result.get("unresolved", []),
        "disclaimer": get_disclaimer(language),
    }


@router.get("/warnings/{drug_name}")
async def get_drug_warnings(
    drug_name: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get FDA drug warnings, contraindications, and adverse reactions.
    Data sourced from OpenFDA (free, no key needed).
    """
    try:
        warnings = await drug_interaction_service.get_drug_warnings(drug_name)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    if not warnings:
        return {
            "drug_name": drug_name,
            "message": "No FDA label information found for this drug.",
            "disclaimer": get_disclaimer(),
        }

    return {**warnings, "disclaimer": get_disclaimer()}
