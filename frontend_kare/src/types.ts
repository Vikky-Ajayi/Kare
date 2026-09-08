export type LangCode = 'en' | 'yo' | 'ha' | 'ig' | 'pcm';

export const LANGUAGES: { code: LangCode; label: string }[] = [
  { code: 'en', label: 'English' },
  { code: 'yo', label: 'Yorùbá' },
  { code: 'ha', label: 'Hausa' },
  { code: 'ig', label: 'Igbo' },
  { code: 'pcm', label: 'Nigerian Pidgin' },
];

export interface User {
  id: string;
  email: string;
  preferred_language: LangCode;
  is_verified: boolean;
  role: string;
  first_name?: string;
  last_name?: string;
  name?: string;
  has_active_pregnancy: boolean;
  followups_enabled: boolean;
}

export interface AuthResponse {
  user: User;
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

export interface PatientProfile {
  id: string;
  first_name: string;
  last_name: string;
  date_of_birth?: string;
  gender?: string;
  phone_number?: string;
  country: string;
  state?: string;
  blood_group?: string;
  height_cm?: number;
  weight_kg?: number;
  allergies: string[];
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  age?: number;
  bmi?: number;
}

export interface MedicalCondition {
  id: string;
  condition_name: string;
  icd10_code?: string;
  status: string;
  diagnosed_date?: string;
  notes?: string;
}

export interface Medication {
  id: string;
  drug_name: string;
  dosage?: string;
  frequency?: string;
  route?: string;
  start_date?: string;
  end_date?: string;
  status: string;
  notes?: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  language?: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  language: string;
  status: string;
  started_at: string;
  ended_at?: string;
  message_count: number;
  preview?: string;
}

export interface HealthNotes {
  conversation_count: number;
  presenting_complaints: string[];
  suspected_conditions: string[];
  lifestyle_notes?: string;
  family_history_notes?: string;
  medication_concerns?: string;
  pain_patterns?: string;
  mental_health_notes?: string;
  important_flags: string[];
  key_concerns?: string;
  last_summary?: string;
  raw_notes?: string;
  last_updated?: string;
}

export interface TurnResponse {
  conversation_id: string;
  user_message?: string;
  assistant_message: string;
  transcription?: string;
  language: string;
  audio_base64?: string | null;
  triage_level?: string | null;
  escalated?: boolean;
  tool_calls?: string[];
  latency_ms?: number;
  disclaimer: string;
}

export interface SymptomCheckResult {
  check_id: string;
  symptoms_reported: string[];
  triage_level: 'EMERGENCY' | 'URGENT' | 'SEMI_URGENT' | 'NON_URGENT' | 'SELF_CARE';
  triage_explanation: string;
  possible_conditions: Array<{ condition: string; likelihood?: string; icd10?: string | null }>;
  recommendations: string;
  when_to_seek_emergency: string;
  disclaimer: string;
  language: string;
}

export interface Pregnancy {
  id: string;
  status: string;
  gestational_age: string;
  gestational_age_days?: number;
  trimester?: number;
  estimated_due_date?: string;
  days_to_edd?: number;
  edd_source: string;
  baby_sex: string;
  gravida?: number;
  para?: number;
  history_notes?: string;
  this_week: string;
}

export interface Followup {
  id: string;
  conversation_id: string;
  status: string;
  due_at: string;
  sent_at?: string;
  answered_at?: string;
  message?: string;
  topics: string[];
}
