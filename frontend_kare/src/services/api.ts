import axios from 'axios';
import { useAuthStore } from '../store/useAuthStore';
import type {
  AuthResponse, Conversation, Followup, HealthNotes, LangCode, MedicalCondition,
  Medication, Message, PatientProfile, Pregnancy, SymptomCheckResult, TurnResponse, User,
} from '../types';

const raw = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
export const API_BASE_URL = raw.replace(/\/+$/, '').endsWith('/api/v1')
  ? raw.replace(/\/+$/, '')
  : `${raw.replace(/\/+$/, '')}/api/v1`;

export const WS_BASE_URL = API_BASE_URL.replace(/^http/, 'ws');

export const api = axios.create({ baseURL: API_BASE_URL, headers: { 'Content-Type': 'application/json' } });

api.interceptors.request.use((config) => {
  const { accessToken } = useAuthStore.getState();
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`;
  return config;
});

let refreshing: Promise<string> | null = null;

api.interceptors.response.use(
  (r) => r,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original?._retry) {
      original._retry = true;
      const { refreshToken, setTokens, logout } = useAuthStore.getState();
      if (!refreshToken) { logout(); return Promise.reject(error); }
      try {
        if (!refreshing) {
          refreshing = axios
            .post(`${API_BASE_URL}/auth/refresh`, { refresh_token: refreshToken })
            .then((res) => {
              setTokens(res.data.access_token, res.data.refresh_token);
              return res.data.access_token as string;
            })
            .finally(() => { refreshing = null; });
        }
        const token = await refreshing;
        original.headers.Authorization = `Bearer ${token}`;
        return api(original);
      } catch (e) {
        logout();
        window.location.href = '/login';
        return Promise.reject(e);
      }
    }
    return Promise.reject(error);
  },
);

const errMsg = (e: any, fallback = 'Something went wrong. Please try again.') =>
  e?.response?.data?.detail || e?.response?.data?.message || e?.message || fallback;
export { errMsg };

// ── auth ────────────────────────────────────────────────────────────
export const auth = {
  register: (b: { email: string; password: string; first_name: string; last_name: string; preferred_language: LangCode }) =>
    api.post<AuthResponse>('/auth/register', b).then((r) => r.data),
  login: (b: { email: string; password: string }) =>
    api.post<AuthResponse>('/auth/login', b).then((r) => r.data),
  me: () => api.get<User>('/auth/me').then((r) => r.data),
  logout: (refresh_token: string) => api.post('/auth/logout', { refresh_token }).catch(() => {}),
};

// ── patient ─────────────────────────────────────────────────────────
export const patient = {
  get: () => api.get<PatientProfile>('/patients/me').then((r) => r.data),
  update: (b: Partial<PatientProfile>) => api.put<PatientProfile>('/patients/me', b).then((r) => r.data),
  setLanguage: (language: LangCode) => api.patch(`/patients/me/language?language=${language}`).then((r) => r.data),
  deleteAccount: () => api.delete('/patients/me', { params: { confirm: 'DELETE' } }).then((r) => r.data),
};

// ── medical history + meds ──────────────────────────────────────────
export const history = {
  list: () => api.get<MedicalCondition[]>('/medical-history/').then((r) => r.data),
  add: (b: { condition_name: string; status?: string; diagnosed_date?: string; notes?: string; icd10_code?: string }) =>
    api.post<MedicalCondition>('/medical-history/', b).then((r) => r.data),
  remove: (id: string) => api.delete(`/medical-history/${id}`).then((r) => r.data),
};

export const meds = {
  list: () => api.get<Medication[]>('/medications/').then((r) => r.data),
  add: (b: { drug_name: string; dosage?: string; frequency?: string; start_date?: string; end_date?: string; notes?: string }) =>
    api.post<Medication>('/medications/', b).then((r) => r.data),
  remove: (id: string) => api.delete(`/medications/${id}`).then((r) => r.data),
  myInteractions: (language: LangCode = 'en') =>
    api.get(`/drugs/interactions/my-meds?language=${language}`).then((r) => r.data),
};

// ── voice / consultation ────────────────────────────────────────────
export const voice = {
  chat: (b: { text: string; language: LangCode; conversation_id?: string | null; include_audio?: boolean }) =>
    api.post<TurnResponse>('/voice/chat', b).then((r) => r.data),
  chatAudio: (blob: Blob, language: LangCode, conversation_id?: string | null) => {
    const fd = new FormData();
    fd.append('file', blob, 'turn.webm');
    fd.append('language', language);
    if (conversation_id) fd.append('conversation_id', conversation_id);
    return api.post<TurnResponse>('/voice/chat/audio', fd, { headers: { 'Content-Type': 'multipart/form-data' } }).then((r) => r.data);
  },
  synthesize: (text: string, language: LangCode) =>
    api.post('/voice/synthesize', { text, language }, { responseType: 'blob' }).then((r) => r.data as Blob),
  notes: () => api.get<HealthNotes>('/voice/notes').then((r) => r.data),
  conversations: () => api.get<Conversation[]>('/voice/conversations').then((r) => r.data),
  messages: (id: string) =>
    api.get<{ conversation_id: string; language: string; status: string; messages: Message[] }>(`/voice/conversations/${id}/messages`).then((r) => r.data),
  end: (id: string) => api.delete(`/voice/conversations/${id}`).then((r) => r.data),
};

// ── symptoms ────────────────────────────────────────────────────────
export const symptoms = {
  check: (b: { symptoms: string; language: LangCode; include_patient_history?: boolean }) =>
    api.post<SymptomCheckResult>('/symptoms/check', b).then((r) => r.data),
  historyList: () => api.get('/symptoms/history').then((r) => r.data),
};

// ── pregnancy ───────────────────────────────────────────────────────
export const pregnancy = {
  get: () => api.get<Pregnancy>('/pregnancy').then((r) => r.data),
  start: (b: Record<string, unknown>) => api.post<Pregnancy>('/pregnancy', b).then((r) => r.data),
  update: (b: Record<string, unknown>) => api.patch<Pregnancy>('/pregnancy', b).then((r) => r.data),
  end: (outcome: string) => api.post('/pregnancy/end', { outcome }).then((r) => r.data),
};

// ── notifications ───────────────────────────────────────────────────
export const notifications = {
  vapidKey: () => api.get<{ public_key: string }>('/notifications/vapid-key').then((r) => r.data),
  subscribe: (b: { endpoint: string; keys: { p256dh: string; auth: string }; timezone?: string }) =>
    api.post('/notifications/subscribe', b).then((r) => r.data),
  unsubscribe: (endpoint: string) => api.post('/notifications/unsubscribe', { endpoint }).then((r) => r.data),
  preferences: (followups_enabled: boolean, timezone?: string) =>
    api.patch('/notifications/preferences', { followups_enabled, timezone }).then((r) => r.data),
  followups: () => api.get<{ enabled: boolean; items: Followup[] }>('/notifications/followups').then((r) => r.data),
  markClicked: (id: string) => api.post(`/notifications/followups/${id}/clicked`).catch(() => {}),
  test: () => api.post('/notifications/test').then((r) => r.data),
};
