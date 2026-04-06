export interface User {
  id: string;
  email: string;
  name: string;
  preferred_language: string;
}

export interface PatientProfile {
  name: string;
  date_of_birth: string;
  gender: 'male' | 'female' | 'other';
  blood_group?: string;
  height?: number;
  weight?: number;
  allergies?: string[];
  emergency_contact?: string;
  state?: string;
  country?: string;
  age?: number;
  bmi?: number;
}

export interface MedicalCondition {
  id: string;
  name: string;
  icd10_code?: string;
  status: 'active' | 'resolved' | 'chronic';
  date_diagnosed: string;
  notes?: string;
}

export interface Medication {
  id: string;
  drug_name: string;
  dosage: string;
  frequency: string;
  start_date: string;
  end_date?: string;
  notes?: string;
  rxnorm_cui?: string;
}

export interface Conversation {
  id: string;
  title?: string;
  created_at: string;
  last_message?: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  audio_url?: string;
  created_at: string;
}

export interface SymptomCheckResult {
  triage_level: 'EMERGENCY' | 'URGENT' | 'SEMI_URGENT' | 'NON_URGENT' | 'SELF_CARE';
  triage_explanation: string;
  possible_conditions: string[];
  recommendations: string[];
  when_to_seek_emergency: string;
  disclaimer: string;
}

export interface ClinicalNotes {
  summary: string;
  symptoms: string[];
  potential_diagnosis: string[];
  plan: string[];
  important_flags: string[];
}
