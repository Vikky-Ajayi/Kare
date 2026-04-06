"""
All Pydantic schemas for request/response validation.
Single file for simplicity — split into sub-files as project grows.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ─────────────────────────────────────────────
# AUTH SCHEMAS
# ─────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    preferred_language: str = Field(default="en", max_length=10)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    preferred_language: str
    is_verified: bool
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# PATIENT SCHEMAS
# ─────────────────────────────────────────────

class PatientCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    phone_number: Optional[str] = None
    country: str = "Nigeria"
    state: Optional[str] = None
    blood_group: Optional[str] = "unknown"
    height_cm: Optional[float] = Field(None, ge=50, le=300)
    weight_kg: Optional[float] = Field(None, ge=1, le=500)
    allergies: List[str] = []
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    phone_number: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    blood_group: Optional[str] = None
    height_cm: Optional[float] = Field(None, ge=50, le=300)
    weight_kg: Optional[float] = Field(None, ge=1, le=500)
    allergies: Optional[List[str]] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class PatientResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    first_name: str
    last_name: str
    date_of_birth: Optional[date]
    gender: Optional[str]
    phone_number: Optional[str]
    country: str
    state: Optional[str]
    blood_group: Optional[str]
    height_cm: Optional[float]
    weight_kg: Optional[float]
    allergies: List[str]
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    profile_photo_url: Optional[str]
    age: Optional[int] = None
    bmi: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# MEDICAL CONDITION SCHEMAS
# ─────────────────────────────────────────────

class MedicalConditionCreate(BaseModel):
    condition_name: str = Field(min_length=1, max_length=200)
    icd10_code: Optional[str] = None
    status: str = "active"
    diagnosed_date: Optional[date] = None
    resolved_date: Optional[date] = None
    notes: Optional[str] = None
    diagnosed_by: Optional[str] = None


class MedicalConditionUpdate(BaseModel):
    condition_name: Optional[str] = None
    icd10_code: Optional[str] = None
    status: Optional[str] = None
    diagnosed_date: Optional[date] = None
    resolved_date: Optional[date] = None
    notes: Optional[str] = None
    diagnosed_by: Optional[str] = None


class MedicalConditionResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    condition_name: str
    icd10_code: Optional[str]
    status: str
    diagnosed_date: Optional[date]
    resolved_date: Optional[date]
    notes: Optional[str]
    diagnosed_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# MEDICATION SCHEMAS
# ─────────────────────────────────────────────

class MedicationCreate(BaseModel):
    drug_name: str = Field(min_length=1, max_length=200)
    rxnorm_cui: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str = "active"
    prescribed_by: Optional[str] = None
    notes: Optional[str] = None


class MedicationUpdate(BaseModel):
    drug_name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None
    prescribed_by: Optional[str] = None
    notes: Optional[str] = None


class MedicationResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    drug_name: str
    rxnorm_cui: Optional[str]
    dosage: Optional[str]
    frequency: Optional[str]
    route: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    status: str
    prescribed_by: Optional[str]
    notes: Optional[str]
    image_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# VOICE / STT / TTS SCHEMAS
# ─────────────────────────────────────────────

class TranscribeResponse(BaseModel):
    text: str
    language_detected: Optional[str]
    duration_seconds: Optional[float]


class SynthesizeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    language: str = Field(default="en", max_length=10)


class VoiceChatRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    language: str = Field(default="en")
    conversation_id: Optional[uuid.UUID] = None
    include_audio: bool = True


class VoiceChatResponse(BaseModel):
    conversation_id: uuid.UUID
    user_message: str
    assistant_message: str
    language: str
    audio_base64: Optional[str] = None    # base64-encoded MP3
    triage_level: Optional[str] = None
    disclaimer: str


# ─────────────────────────────────────────────
# SYMPTOM CHECK SCHEMAS
# ─────────────────────────────────────────────

class SymptomCheckRequest(BaseModel):
    symptoms: str = Field(
        min_length=5,
        max_length=2000,
        description="Free-text description of symptoms in any supported language"
    )
    language: str = Field(default="en")
    include_patient_history: bool = True   # use patient's stored conditions/meds in analysis


class SymptomCheckResponse(BaseModel):
    check_id: uuid.UUID
    symptoms_reported: List[str]
    triage_level: str
    triage_explanation: str
    possible_conditions: List[Dict[str, Any]]
    recommendations: str
    when_to_seek_emergency: str
    disclaimer: str
    language: str


# ─────────────────────────────────────────────
# DRUG INTERACTION SCHEMAS
# ─────────────────────────────────────────────

class DrugSearchResponse(BaseModel):
    rxcui: str
    name: str
    synonyms: List[str] = []


class DrugInteractionRequest(BaseModel):
    drug_names: List[str] = Field(min_length=2, description="At least 2 drug names to check")


class InteractionDetail(BaseModel):
    drug_1: str
    drug_2: str
    severity: Optional[str]
    description: str
    source: str = "RxNorm / NIH"


class DrugInteractionResponse(BaseModel):
    drugs_checked: List[str]
    interactions_found: int
    interactions: List[InteractionDetail]
    ai_summary: str
    disclaimer: str


# ─────────────────────────────────────────────
# IMAGE ANALYSIS SCHEMAS
# ─────────────────────────────────────────────

class ImageAnalysisResponse(BaseModel):
    analysis_id: uuid.UUID
    image_type: str
    analysis: str
    structured_findings: Optional[Dict[str, Any]]
    confidence_note: str
    disclaimer: str


# ─────────────────────────────────────────────
# GENERIC RESPONSE
# ─────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    success: bool = True


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int
