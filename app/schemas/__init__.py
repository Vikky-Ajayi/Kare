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
    date_of_birth: date | None = None
    gender: str | None = None
    phone_number: str | None = None
    country: str = "Nigeria"
    state: str | None = None
    blood_group: str | None = "unknown"
    height_cm: float | None = Field(None, ge=50, le=300)
    weight_kg: float | None = Field(None, ge=1, le=500)
    allergies: list[str] = []
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None


class PatientUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    phone_number: str | None = None
    country: str | None = None
    state: str | None = None
    blood_group: str | None = None
    height_cm: float | None = Field(None, ge=50, le=300)
    weight_kg: float | None = Field(None, ge=1, le=500)
    allergies: list[str] | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None


class PatientResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    first_name: str
    last_name: str
    date_of_birth: date | None
    gender: str | None
    phone_number: str | None
    country: str
    state: str | None
    blood_group: str | None
    height_cm: float | None
    weight_kg: float | None
    allergies: list[str]
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    profile_photo_url: str | None
    age: int | None = None
    bmi: float | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# MEDICAL CONDITION SCHEMAS
# ─────────────────────────────────────────────

class MedicalConditionCreate(BaseModel):
    condition_name: str = Field(min_length=1, max_length=200)
    icd10_code: str | None = None
    status: str = "active"
    diagnosed_date: date | None = None
    resolved_date: date | None = None
    notes: str | None = None
    diagnosed_by: str | None = None


class MedicalConditionUpdate(BaseModel):
    condition_name: str | None = None
    icd10_code: str | None = None
    status: str | None = None
    diagnosed_date: date | None = None
    resolved_date: date | None = None
    notes: str | None = None
    diagnosed_by: str | None = None


class MedicalConditionResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    condition_name: str
    icd10_code: str | None
    status: str
    diagnosed_date: date | None
    resolved_date: date | None
    notes: str | None
    diagnosed_by: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# MEDICATION SCHEMAS
# ─────────────────────────────────────────────

class MedicationCreate(BaseModel):
    drug_name: str = Field(min_length=1, max_length=200)
    rxnorm_cui: str | None = None
    dosage: str | None = None
    frequency: str | None = None
    route: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str = "active"
    prescribed_by: str | None = None
    notes: str | None = None


class MedicationUpdate(BaseModel):
    drug_name: str | None = None
    dosage: str | None = None
    frequency: str | None = None
    route: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str | None = None
    prescribed_by: str | None = None
    notes: str | None = None


class MedicationResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    drug_name: str
    rxnorm_cui: str | None
    dosage: str | None
    frequency: str | None
    route: str | None
    start_date: date | None
    end_date: date | None
    status: str
    prescribed_by: str | None
    notes: str | None
    image_url: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# VOICE / STT / TTS SCHEMAS
# ─────────────────────────────────────────────

class TranscribeResponse(BaseModel):
    text: str
    language_detected: str | None
    duration_seconds: float | None


class SynthesizeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    language: str = Field(default="en", max_length=10)


class VoiceChatRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    language: str = Field(default="en")
    conversation_id: str | None = None
    include_audio: bool = True


class VoiceChatResponse(BaseModel):
    conversation_id: str
    user_message: str
    assistant_message: str
    language: str
    audio_base64: str | None = None    # base64-encoded WAV
    triage_level: str | None = None
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
    symptoms_reported: list[str]
    triage_level: str
    triage_explanation: str
    possible_conditions: list[dict[str, Any]]
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
    synonyms: list[str] = []


class DrugInteractionRequest(BaseModel):
    drug_names: list[str] = Field(min_length=2, description="At least 2 drug names to check")


class InteractionDetail(BaseModel):
    drug_1: str
    drug_2: str
    severity: str | None
    description: str
    source: str = "RxNorm / NIH"


class DrugInteractionResponse(BaseModel):
    drugs_checked: list[str]
    interactions_found: int
    interactions: list[InteractionDetail]
    ai_summary: str
    disclaimer: str


# ─────────────────────────────────────────────
# IMAGE ANALYSIS SCHEMAS
# ─────────────────────────────────────────────

class ImageAnalysisResponse(BaseModel):
    analysis_id: uuid.UUID
    image_type: str
    analysis: str
    structured_findings: dict[str, Any] | None
    confidence_note: str
    disclaimer: str


# ─────────────────────────────────────────────
# GENERIC RESPONSE
# ─────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    success: bool = True


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    per_page: int
    pages: int
