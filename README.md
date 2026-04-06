# 🩺 Voice Medical Assistant — Backend API

A voice-first, multilingual AI medical assistant for Nigeria and Africa.  
Built with **FastAPI + Groq + Supabase** — entirely free to run.

---

## 🌍 Supported Languages
| Code | Language |
|------|----------|
| `en` | English (Nigerian accent TTS) |
| `yo` | Yoruba |
| `ha` | Hausa |
| `ig` | Igbo |
| `fr` | French |
| `pcm` | Nigerian Pidgin English |

---

## 🏗️ Architecture (Zero-Cost Stack)

```
FastAPI (Python)
    ↓
Supabase          — PostgreSQL DB + file storage (free tier)
    ↓
Groq API          — Whisper STT + Llama 3.3 LLM + Llama 4 Vision (free tier)
    ↓
edge-tts          — Microsoft Neural TTS voices (free, no key)
    ↓
NIH RxNorm API    — Drug lookup + interaction checking (free, no key)
OpenFDA API       — Drug warnings / labels (free, no key)
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone <your-repo>
cd medical_voice_assistant

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set Up Environment

```bash
cp .env.example .env
```

Edit `.env` and fill in:

| Variable | Where to get it |
|----------|----------------|
| `SECRET_KEY` | Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` | Supabase → Settings → Database → URI |
| `SUPABASE_URL` | Supabase → Settings → API |
| `SUPABASE_KEY` | Supabase → Settings → API → anon/public key |
| `GROQ_API_KEY` | https://console.groq.com → API Keys |

### 3. Set Up Supabase (Free)

1. Go to [supabase.com](https://supabase.com) → New Project
2. Copy your **Database URI** and **API keys** into `.env`
3. Go to **Storage** → Create a new bucket named `medical-files`
4. Set bucket to **Public** (for image URLs) or **Private** (and use signed URLs)

### 4. Run Database Migrations

```bash
# Initialize Alembic (first time only)
alembic revision --autogenerate -m "initial schema"

# Apply migrations
alembic upgrade head
```

### 5. Start the Server

```bash
uvicorn app.main:app --reload
```

API is live at: **http://localhost:8000**  
Swagger docs: **http://localhost:8000/docs**

---

## 📡 API Overview

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register a new patient |
| POST | `/api/v1/auth/login` | Login → access + refresh tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Revoke refresh token |
| GET | `/api/v1/auth/me` | Get current user |

### Patient Profile
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/patients/me` | Get my profile |
| PUT | `/api/v1/patients/me` | Update profile |
| PATCH | `/api/v1/patients/me/language` | Change preferred language |

### Medical History
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/medical-history/` | List all conditions |
| POST | `/api/v1/medical-history/` | Add a condition |
| PUT | `/api/v1/medical-history/{id}` | Update a condition |
| DELETE | `/api/v1/medical-history/{id}` | Remove a condition |

### Medications
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/medications/` | List medications |
| POST | `/api/v1/medications/` | Add medication |
| PUT | `/api/v1/medications/{id}` | Update medication |
| DELETE | `/api/v1/medications/{id}` | Remove medication |
| POST | `/api/v1/medications/{id}/image` | Upload medication photo |

### Voice & AI Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/voice/transcribe` | Audio → Text (Whisper) |
| POST | `/api/v1/voice/synthesize` | Text → MP3 audio |
| POST | `/api/v1/voice/chat` | Full voice conversation turn |
| GET | `/api/v1/voice/conversations` | List past conversations |
| GET | `/api/v1/voice/conversations/{id}/messages` | Get conversation messages |

### Symptom Checking
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/symptoms/check` | AI symptom triage |
| GET | `/api/v1/symptoms/history` | Past symptom checks |
| GET | `/api/v1/symptoms/history/{id}` | Get specific check |

### Drug Interactions (Free NIH APIs)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/drugs/search?q=paracetamol` | Search drug by name |
| GET | `/api/v1/drugs/info/{rxcui}` | Drug info by RxCUI |
| POST | `/api/v1/drugs/interactions` | Check interactions |
| GET | `/api/v1/drugs/interactions/my-meds` | Check my active meds |
| GET | `/api/v1/drugs/warnings/{drug_name}` | FDA drug warnings |

### Image Analysis
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/images/analyze` | Analyze medical image |
| GET | `/api/v1/images/history` | Past image analyses |
| GET | `/api/v1/images/{id}` | Get specific analysis |

---

## 🔐 Authentication Flow

```
1. POST /auth/register  →  creates user + patient profile
2. POST /auth/login     →  returns { access_token, refresh_token }
3. All protected routes →  add header: Authorization: Bearer <access_token>
4. POST /auth/refresh   →  when access token expires, get a new one
```

---

## 🎙️ Voice Chat Flow (Frontend Integration)

```
Option A — Text input:
  POST /voice/chat  { text: "I have a headache", language: "en" }
  ← { assistant_message, audio_base64, conversation_id }

Option B — Voice input:
  1. Record audio in browser (MediaRecorder API → webm)
  2. POST /voice/transcribe  (audio file)  →  { text }
  3. POST /voice/chat  { text, conversation_id }  →  { audio_base64 }
  4. Play audio_base64 on frontend (decode base64 → Blob → Audio)
```

---

## 🚢 Free Deployment Options

### Railway (Recommended)
```bash
# Install Railway CLI
npm install -g @railway/cli

railway login
railway init
railway add postgresql    # free PostgreSQL
railway up
```

### Render
1. Connect GitHub repo to [render.com](https://render.com)
2. New Web Service → Python → `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Add environment variables in Render dashboard

---

## 💰 Cost Breakdown (Monthly)

| Service | Free Tier Limits | Cost |
|---------|-----------------|------|
| Groq API | 14,400 req/day Whisper, 30 RPM LLM | $0 |
| Supabase | 500MB DB, 1GB storage, 50MB file uploads | $0 |
| edge-tts | Unlimited (uses Microsoft servers quietly) | $0 |
| NIH RxNorm | Unlimited public API | $0 |
| OpenFDA | 240 req/min | $0 |
| Railway/Render | 500 hours/month free | $0 |
| **Total** | | **$0/month** |

---

## ⚠️ Important Disclaimers

- This system is for **informational purposes only**
- It does **NOT** constitute medical advice
- Always recommend patients see a licensed healthcare professional
- AI triage is **not a substitute** for clinical assessment
- For emergencies, always direct to the nearest hospital

---

## 📁 Project Structure

```
medical_voice_assistant/
├── app/
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Settings (pydantic-settings)
│   ├── database.py                # SQLAlchemy engine + session
│   ├── models/
│   │   └── __init__.py            # All ORM models
│   ├── schemas/
│   │   └── __init__.py            # All Pydantic schemas
│   ├── routers/
│   │   ├── auth.py                # Register / login / tokens
│   │   ├── patients.py            # Patient profile CRUD
│   │   ├── medical_history.py     # Medical conditions CRUD
│   │   ├── medications.py         # Medications CRUD + image upload
│   │   ├── voice.py               # STT / TTS / Voice chat
│   │   ├── symptoms.py            # AI symptom checking
│   │   ├── drug_interactions.py   # NIH drug interaction API
│   │   └── image_analysis.py      # Groq Vision image analysis
│   ├── services/
│   │   ├── groq_service.py        # Whisper + LLM + Vision
│   │   ├── tts_service.py         # edge-tts synthesis
│   │   └── drug_interaction_service.py  # RxNorm + OpenFDA
│   ├── middleware/
│   │   └── auth_middleware.py     # JWT auth dependency
│   └── utils/
│       ├── security.py            # JWT + password hashing
│       └── helpers.py             # BMI, age, disclaimers
├── alembic/                       # Database migrations
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```
