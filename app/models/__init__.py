"""
All SQLAlchemy ORM models for the Voice Medical Assistant.
"""

import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, DateTime, Text,
    ForeignKey, Enum, Date, Float, Integer
)
from sqlalchemy.orm import relationship
from app.database import Base

# Use JSON for SQLite compatibility, JSONB for PostgreSQL
try:
    from sqlalchemy.dialects.postgresql import JSONB as JSONType
except ImportError:
    from sqlalchemy import JSON as JSONType

from sqlalchemy import JSON as JSONType   # universal fallback


# ─────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────

class UserRole(str, enum.Enum):
    PATIENT = "patient"
    ADMIN = "admin"

class BloodGroup(str, enum.Enum):
    A_POS = "A+"; A_NEG = "A-"; B_POS = "B+"; B_NEG = "B-"
    AB_POS = "AB+"; AB_NEG = "AB-"; O_POS = "O+"; O_NEG = "O-"
    UNKNOWN = "unknown"

class ConditionStatus(str, enum.Enum):
    ACTIVE = "active"; RESOLVED = "resolved"
    CHRONIC = "chronic"; SUSPECTED = "suspected"

class MedicationStatus(str, enum.Enum):
    ACTIVE = "active"; DISCONTINUED = "discontinued"; AS_NEEDED = "as_needed"

class TriageLevel(str, enum.Enum):
    EMERGENCY = "emergency"; URGENT = "urgent"
    SEMI_URGENT = "semi_urgent"; NON_URGENT = "non_urgent"; SELF_CARE = "self_care"

class ConversationStatus(str, enum.Enum):
    ACTIVE = "active"; COMPLETED = "completed"; ABANDONED = "abandoned"


# ─────────────────────────────────────────────
# USERS
# ─────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    role = Column(String(20), default="patient")
    preferred_language = Column(String(10), default="en")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = relationship("Patient", back_populates="user", uselist=False, cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="refresh_tokens")


# ─────────────────────────────────────────────
# PATIENTS
# ─────────────────────────────────────────────

class Patient(Base):
    __tablename__ = "patients"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    phone_number = Column(String(20), nullable=True)
    country = Column(String(100), default="Nigeria")
    state = Column(String(100), nullable=True)
    blood_group = Column(String(10), default="unknown")
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    allergies = Column(JSONType, default=list)
    emergency_contact_name = Column(String(200), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    profile_photo_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="patient")
    medical_conditions = relationship("MedicalCondition", back_populates="patient", cascade="all, delete-orphan")
    medications = relationship("Medication", back_populates="patient", cascade="all, delete-orphan")
    symptom_checks = relationship("SymptomCheck", back_populates="patient", cascade="all, delete-orphan")
    image_analyses = relationship("ImageAnalysis", back_populates="patient", cascade="all, delete-orphan")
    health_notes = relationship("PatientHealthNotes", back_populates="patient", uselist=False, cascade="all, delete-orphan")


# ─────────────────────────────────────────────
# PATIENT HEALTH NOTES (Doctor's running file)
# ─────────────────────────────────────────────

class PatientHealthNotes(Base):
    """
    The AI doctor's running notes on a patient.
    Updated after every conversation with new observations.
    This is what makes every new conversation feel like
    the doctor already knows the patient.
    """
    __tablename__ = "patient_health_notes"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Clinical observations built up over time
    presenting_complaints = Column(JSONType, default=list)   # recurring symptoms noted
    suspected_conditions = Column(JSONType, default=list)    # AI-suspected (not diagnosed)
    lifestyle_notes = Column(Text, nullable=True)            # diet, exercise, sleep, stress
    family_history_notes = Column(Text, nullable=True)       # mentioned family history
    medication_concerns = Column(Text, nullable=True)        # adherence issues, side effects mentioned
    pain_patterns = Column(Text, nullable=True)              # where, when, how severe
    mental_health_notes = Column(Text, nullable=True)        # mood, anxiety, stress mentioned
    important_flags = Column(JSONType, default=list)         # red flags the AI has noted
    conversation_count = Column(Integer, default=0)          # how many conversations had
    last_summary = Column(Text, nullable=True)               # AI summary of last session
    key_concerns = Column(Text, nullable=True)               # top things to follow up on
    raw_notes = Column(Text, nullable=True)                  # freeform clinical notes

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = relationship("Patient", back_populates="health_notes")


# ─────────────────────────────────────────────
# MEDICAL CONDITIONS
# ─────────────────────────────────────────────

class MedicalCondition(Base):
    __tablename__ = "medical_conditions"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    condition_name = Column(String(200), nullable=False)
    icd10_code = Column(String(20), nullable=True)
    status = Column(String(20), default="active")
    diagnosed_date = Column(Date, nullable=True)
    resolved_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    diagnosed_by = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    patient = relationship("Patient", back_populates="medical_conditions")


# ─────────────────────────────────────────────
# MEDICATIONS
# ─────────────────────────────────────────────

class Medication(Base):
    __tablename__ = "medications"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    drug_name = Column(String(200), nullable=False)
    rxnorm_cui = Column(String(20), nullable=True)
    dosage = Column(String(100), nullable=True)
    frequency = Column(String(100), nullable=True)
    route = Column(String(50), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(String(20), default="active")
    prescribed_by = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    patient = relationship("Patient", back_populates="medications")


# ─────────────────────────────────────────────
# CONVERSATIONS
# ─────────────────────────────────────────────

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    language = Column(String(10), default="en")
    status = Column(String(20), default="active")
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    summary = Column(Text, nullable=True)
    triage_result = Column(String(20), nullable=True)
    user = relationship("User", back_populates="conversations")
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan")


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    audio_url = Column(String(500), nullable=True)
    language = Column(String(10), default="en")
    created_at = Column(DateTime, default=datetime.utcnow)
    conversation = relationship("Conversation", back_populates="messages")


# ─────────────────────────────────────────────
# SYMPTOM CHECKS
# ─────────────────────────────────────────────

class SymptomCheck(Base):
    __tablename__ = "symptom_checks"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    symptoms_reported = Column(JSONType, default=list)
    language = Column(String(10), default="en")
    input_text = Column(Text, nullable=True)
    ai_assessment = Column(Text, nullable=True)
    triage_level = Column(String(20), nullable=True)
    possible_conditions = Column(JSONType, default=list)
    recommendations = Column(Text, nullable=True)
    disclaimer_shown = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    patient = relationship("Patient", back_populates="symptom_checks")


# ─────────────────────────────────────────────
# IMAGE ANALYSES
# ─────────────────────────────────────────────

class ImageAnalysis(Base):
    __tablename__ = "image_analyses"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    image_url = Column(String(500), nullable=False)
    image_type = Column(String(50), nullable=True)
    analysis_result = Column(Text, nullable=True)
    structured_result = Column(JSONType, nullable=True)
    confidence_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    patient = relationship("Patient", back_populates="image_analyses")


# ─────────────────────────────────────────────
# AUDIT LOGS
# ─────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(100), nullable=True)
    details = Column(JSONType, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="audit_logs")