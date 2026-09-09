# Kare — Architecture

## Stack

```
┌───────────────────────────────────────────────────────────────────┐
│  React 19 PWA  (Vercel)                                            │
│  voice screen · dashboard · pregnancy companion · settings         │
│  service worker: Web Push + "reopen this conversation" deep link   │
└──────────────┬────────────────────────────────┬───────────────────┘
     HTTPS / REST                      WSS  /api/v1/voice/stream
               │                                │
┌──────────────▼────────────────────────────────▼───────────────────┐
│  FastAPI  (Railway, europe-west4)                                  │
│                                                                   │
│  routers/ ── auth, patients, history, medications, voice,          │
│              symptoms, drug_interactions, image, notifications,    │
│              pregnancy                                             │
│                                                                   │
│  services/consultation.py  ── the consultation orchestrator        │
│     ├── agent/loop.py       tool-calling loop (≤3 model calls)     │
│     ├── agent/redflags.py   keyword + classifier, runs concurrent  │
│     ├── agent/tools.py      7 tools (history, interactions, …)     │
│     ├── services/memory.py  post-consult structured note extract   │
│     └── services/followups.py  decide → schedule → compose → push  │
│                                                                   │
│  providers/  ── LLMProvider / VoiceProvider abstract interfaces    │
│     ├── groq_llm.py     gpt-oss-120b (consult) · gpt-oss-20b (jobs)│
│     └── sahara_voice.py Sahara STT (stream + REST) · Sahara TTS    │
│                                                                   │
│  worker/followup_tick.py  ── Railway cron, every 15 min           │
└──────────────┬────────────────────────────────────────────────────┘
               │  SQLAlchemy 2.0 + Alembic
┌──────────────▼────────────────────────────────────────────────────┐
│  PostgreSQL  (Railway)                                             │
│  users · patients · conversations · conversation_messages          │
│  patient_health_notes · medical_conditions · medications           │
│  scheduled_followups · push_subscriptions · pregnancy_profiles     │
│  audit_logs                                                        │
└───────────────────────────────────────────────────────────────────┘

External: Sahara (Intron) Voice API · Groq API · NIH RxNorm · (DuckDuckGo search, best-effort)
```

Nothing in `agent/` or `services/` imports Groq or Sahara. They call
`providers.get_llm()` / `providers.get_voice()`, which return objects
implementing `LLMProvider` / `VoiceProvider` (see `providers/base.py`). Tests
inject fakes through `providers.use_test_providers()`. The benchmark drives the
*same* `VoiceProvider` surface the product uses.

## A voice turn, end to end

1. **Client** captures mic audio, downsamples to 16 kHz mono PCM16 in the
   browser (`lib/audio.ts`), streams binary frames over
   `WSS /api/v1/voice/stream`.
2. **Sahara streaming STT** yields partial then committed transcripts. First
   stream per language may cold-start ("wait ~30 s") — the handler falls back
   to the sync REST endpoint for that turn so the user is never stuck.
3. **`consultation.run_turn`**:
   - advances the clinical **state machine** (`intake → gathering → assessment
     → plan → closed`) — count-based, pushed forward when tools fire;
   - starts the **red-flag classifier** (`gpt-oss-20b`) as a concurrent task
     and runs a synchronous **keyword check** (loose regex, tuned for Pidgin);
   - if either red-flag path fires → cancel everything, return an escalation
     reply leading with "get to a hospital now / call 112 (767 or 122 in
     Lagos)";
   - otherwise runs the **agent loop**.
4. **Agent loop** (`agent/loop.py`): up to 3 `gpt-oss-120b` calls. Tools are
   offered on the first two iterations, then a plain answer is forced.
   `reasoning_effort="low"`, `max_tokens=500`, replies constrained to 2–3
   spoken sentences with no markdown, in the caller's code-switched register.
5. **Persist**: two `conversation_messages` rows (user + assistant), the
   `tool_calls` list, triage level, latency.
6. **Sahara TTS** synthesises the reply sentence-by-sentence (REST, pipelined
   with a small concurrency window) so first audio returns in ~2–3 s; frames
   stream back over the same socket.
7. **Background** (`BackgroundTasks`): if ≥4 messages, `memory.update_health_notes`
   extracts structured notes on `gpt-oss-20b` (JSON mode) and merges them.
8. **On `end_conversation`**: `followups.decide_and_plan` runs — a
   `gpt-oss-20b` JSON call returning `{should_follow_up, hours_until, topics}`,
   pregnancy-aware. If yes, a `scheduled_followups` row is queued.

## Memory model

`patient_health_notes` is one row per patient holding merged lists (conditions,
medications, allergies, ongoing concerns — capped, de-duplicated) and free-text
summaries (appended with `[update]` markers). `services/context.py` renders it
into the system prompt for every future consultation, so the assistant opens
already knowing the patient. Extraction is conservative: minimum 4 messages,
low temperature, explicit "only what was actually said" instruction.

## Proactive follow-up

```
consult ends ──► followups.decide_and_plan  (gpt-oss-20b: when? about what?)
                        │
                        ▼
               scheduled_followups  (due_at, topics, status=pending, attempt)
                        │
        Railway cron every 15 min ──► worker/followup_tick.run_once
                        │
                        ▼
               followups.process_due
                 • skip if the patient has messaged since it was queued
                 • _next_allowed(): bump out of 08:00–20:00-local quiet hours
                   (timezone from the push subscription, via zoneinfo)
                 • enforce 20 h min gap; stop after 2 unanswered
                        │
                        ▼
               followups.deliver
                 • _compose(): gpt-oss-20b writes a fresh, non-templated
                   message from this patient's notes + open topics
                   ("anti-robotic rule" in the system prompt)
                 • write it into the conversation as an assistant turn
                 • Web Push (VAPID / pywebpush) with url = /dashboard/voice?c=<id>&f=<fid>
                 • status = sent
```

The push notification's `url` reopens the *exact* conversation. `?f=<fid>`
marks the follow-up clicked (engagement signal + stops re-nagging). Reply and
the thread just continues.

## Pregnancy engine

`pregnancy_profiles` stores whatever anchor the user gave — LMP, known EDD,
ultrasound date + GA-at-scan. `estimated_due_date` is computed live with a
priority cascade: **known EDD → ultrasound dating → Naegele (LMP + 280 d)**.
From EDD: `gestational_age_days = 280 − (edd − today).days` (clamped),
`trimester`, `days_to_edd`. Nothing is stored stale — open the app in week 25
and it says week 25. `services/pregnancy.pregnancy_system_overlay()` adds the
warm persona + trimester-specific focus + always-on danger-sign list to the
consultation system prompt whenever `patient.active_pregnancy` is set.

## Safety layer

- **Red-flag interrupt** is deterministic and concurrent — never gated on the
  LLM deciding to act. Keyword list matches Pidgin/Yoruba/Hausa phrasings
  ("chest dey pain me", "e hard for me to breathe", "baby no dey move").
- **Escalation reply** is generated by a separate constrained prompt and
  always leads with the action + the correct Nigerian emergency numbers.
- **`flag_for_escalation`** tool exists for the agent to call proactively too.
- **Consent gate** in the UI before the first consultation (voice-data
  handling + "this is an AI, not a clinician").
- **`audit_logs`** records every tool invocation with patient id and details.
- Disclaimer on the API root, in the consent gate, and in the persona prompt.

## Data & infra

- **Migrations** run via `alembic upgrade head` in the Railway start command,
  every deploy. Four migrations: baseline (12 tables) → conversation
  stage/plan → push + follow-ups + patient timezone → pregnancy profiles.
- **Auth**: JWT access + rotating refresh tokens (sha256-hashed at rest);
  bcrypt password hashing (sha256 pre-hash to dodge the 72-byte limit).
- **CORS**: `allow_credentials=False` — the client sends a bearer header, not
  cookies.
- **Config** validated at startup (`settings.validate_runtime()`); the app
  refuses to boot on a broken production config.
- **CI**: ruff + 57 pytest tests on every push.

## Repository map

| Path | What |
|---|---|
| `app/providers/` | LLM + Voice provider interfaces and implementations |
| `app/agent/` | tool-calling loop, tool executors, red-flag layer |
| `app/services/consultation.py` | the turn orchestrator |
| `app/services/memory.py` | structured health-note extraction |
| `app/services/followups.py` | decide / schedule / compose / deliver |
| `app/services/pregnancy.py` | dating maths + persona overlay |
| `app/worker/followup_tick.py` | cron entrypoint |
| `app/routers/` | HTTP + WebSocket endpoints |
| `frontend_kare/src/hooks/useVoiceConsult.ts` | client streaming state machine |
| `frontend_kare/public/sw.js` | push + notification-click deep link |
| `benchmark/` | the code-switching ASR benchmark (own README) |
