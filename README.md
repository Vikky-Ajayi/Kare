# Kare

**A voice-first, memory-keeping, multilingual health companion for Nigeria and West Africa.**

Speak how you actually speak — Yoruba, Hausa, Igbo, Nigerian Pidgin and English,
mixed mid-sentence — and Kare listens, triages, remembers you between visits,
checks back in on its own, and walks a pregnancy week by week. It is an AI
assistant, not a clinician, and it consistently points people toward real care.

*Built for the Sahara CodeSwitch Africa Main Challenge · Category: Health.*

---

## Why

A Nigerian patient describes a symptom like this:

> *"Doctor, the malaria don come back. My body dey hot since morning, and the drugs wey you give me never finish, but I dey feel this sharp pain for my side."*

Pidgin grammar, English clinical terms, one sentence. ~7 in 10 Nigerians speak
English as a second language over a mother tongue and **code-switch inside
almost every clinical utterance** — usually into English for the words that
matter most (drug names, "blood pressure", "twice daily", "no fever").

- **Text-first health apps exclude most people.** Voice removes the barrier —
  but only if the voice layer understands code-switched speech.
- **Off-the-shelf ASR fails exactly there.** It drops or mangles the embedded
  English. A wrong drug name is a safety bug.

And the context is stark: among the world's highest maternal-mortality rates,
~1 doctor per 5,000 people, and almost no continuity of care.

## What Kare does

| | |
|---|---|
| 🎙️ **Code-switch-native voice consultation** | Sahara (Intron) streaming STT + TTS. Kare replies in the *same* mixed register you used, spoken aloud. |
| 🧠 **Remembers you** | After each consult a model extracts structured notes and merges them into a longitudinal record. Next time, Kare already knows your history and says so. |
| 🔔 **Proactive follow-up** | When a consult ends, a model decides *whether / when / about what* to check back in. A fresh, non-templated message arrives as a Web Push — tap it and you're back in the *same* conversation. |
| 🤰 **Pregnancy companion** | A dedicated mode: gestational-age maths, week-by-week check-ins, always-on trimester danger signs, warm "our little one" persona, keeps nudging antenatal attendance. |
| 🛠️ **Agentic** | Every turn runs a tool-calling loop (7 tools: history, drug interactions, triage, memory write, follow-up planning, search, escalation). |
| 🚑 **Deterministic safety** | A red-flag detector (keyword + classifier, tuned for Pidgin) runs *concurrently* with the model and can abort a turn straight to "get to a hospital, call 112". |

## The benchmark (30% of the challenge score)

We didn't pick the speech model on faith. [`/benchmark`](benchmark/README.md)
compares **5 ASR systems** on code-switched clinical audio (Intron
AfriSwitchCare):

- **Sahara (Intron)**, Groq **Whisper-large-v3**, Groq **Whisper-large-v3-turbo**,
  **faster-whisper tiny** (local CPU), OpenAI **gpt-4o-transcribe** (frontier closed)
- Metrics: WER/CER, **medical-term recall**, **number/dosage recall**,
  **Code-Mixing-Index error**, **switch-point error**, RTF, cost/minute
- Per-language, with **Swahili as an out-of-family fairness control**, and
  broken down by code-mixing intensity
- Frozen, seed-deterministic test subset; every number reproducible via
  `make benchmark`

**Early findings** (Sahara + OpenAI passes pending API keys/credit): hosted
Whisper *translates* Yoruba/Pidgin/Swahili into English rather than
transcribing the code-switch — and is markedly better on Swahili, which it has
training data for, than on the Nigerian languages our users actually speak.

Methodology: [`docs/BENCHMARK.md`](docs/BENCHMARK.md) · Results:
[`benchmark/report/REPORT.md`](benchmark/report/REPORT.md)

## Architecture

```
React 19 PWA (Vercel)  ──REST/WSS──►  FastAPI (Railway)  ──►  PostgreSQL (Railway)
  voice · dashboard              │  agent loop + red-flag layer
  pregnancy · push SW            │  memory extraction · follow-up worker (cron)
                                 └──►  providers/ ──►  Sahara Voice API · Groq API
```

Nothing in the agent imports Groq or Sahara directly — everything goes through
`LLMProvider` / `VoiceProvider` interfaces, which is also what makes the
benchmark honest. Full detail: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

**Stack:** FastAPI · SQLAlchemy 2.0 · Alembic · Postgres · Groq
(`gpt-oss-120b` / `gpt-oss-20b`) · Sahara (Intron) Voice · React 19 · Vite ·
Tailwind · Zustand · Web Push (VAPID).

## Run it locally

```bash
make install                       # uv venv on Python 3.12 + deps
cp .env.example .env                # fill DATABASE_URL, GROQ_API_KEY, SAHARA_API_KEY, VAPID_*
make migrate                        # alembic upgrade head
make seed                           # 4 demo patients (password: demo-kare-2026)
make run                            # http://localhost:8000  ·  /docs for Swagger

cd frontend_kare && npm install && npm run dev    # http://localhost:3000
```

Set `INPROCESS_SCHEDULER=True` in `.env` to run the follow-up tick inside the
dev server instead of as a separate cron.

## Tests

```bash
make test        # 57 pytest tests (backend + benchmark harness)
make lint        # ruff
```

## Submission documents

| Deliverable | File |
|---|---|
| Solution Description | [`docs/SOLUTION.md`](docs/SOLUTION.md) |
| Architecture / technical docs | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| Benchmark methodology | [`docs/BENCHMARK.md`](docs/BENCHMARK.md) |
| Benchmark results (generated) | [`benchmark/report/REPORT.md`](benchmark/report/REPORT.md) |
| Ethics / Inclusion note | [`docs/ETHICS.md`](docs/ETHICS.md) |
| Demo video script | [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) |
| Deploy runbook | [`DEPLOY.md`](DEPLOY.md) |

## Disclaimer

Kare is a prototype for first-line health information and continuity. It is
**not a medical device**, does not diagnose or prescribe, and is not a
substitute for a licensed health professional. For emergencies, call **112**
(or **767 / 122** in Lagos).
