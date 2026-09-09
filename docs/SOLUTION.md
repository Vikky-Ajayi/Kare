# Kare — Solution Description

*Sahara CodeSwitch Africa Main Challenge · Category: Health (community & maternal health, patient intake, clinical documentation)*

---

## The problem

A Nigerian patient describes a symptom like this:

> *"Doctor, the malaria don come back. My body dey hot since morning, and the drugs wey you give me last time, e never finish but I dey feel this sharp pain for my side."*

That is one sentence in **three registers** — Nigerian Pidgin grammar, an
English clinical noun (*malaria*), an English adjective (*sharp*). Nobody in
Lagos, Kano or Onitsha speaks one language at a time. Roughly **7 in 10
Nigerians** use English as a second language layered on top of Yoruba, Hausa,
Igbo or Pidgin, and they **code-switch inside almost every clinical
utterance** — usually dropping into English for exactly the words a clinician
needs most: drug names, body parts, "twice daily", "blood pressure", "no
fever".

Two things follow from this:

1. **Text-first health apps exclude most of the population.** Typing a symptom
   history in fluent English is a literacy and language barrier. Voice removes
   it — but only if the voice layer understands code-switched speech.
2. **Off-the-shelf ASR fails precisely where it matters.** Public speech
   models are benchmarked monolingually. On code-switched clinical audio they
   drop or mangle the embedded English terms — the clinically load-bearing
   ones. A wrong drug name or a dropped "no" is a safety problem, not a typo.

Meanwhile the health context Kare is built for is stark: Nigeria has among the
**highest maternal mortality rates in the world** (~1,000 per 100,000 live
births), a physician-to-population ratio around **1:5,000**, and most people's
contact with the formal system is one rushed visit with no continuity — no one
follows up, nothing is remembered next time.

## Target users

- **Primary:** adults in Nigeria and West Africa seeking first-line health
  guidance in their own mixed language — symptom triage, medication questions,
  understanding a diagnosis, deciding whether something needs a clinic visit.
- **Pregnancy companion:** pregnant women who see a midwife or doctor a
  handful of times across nine months and have questions every week.
- **Deliberately designed for:** low bandwidth (PWA, works on a mid-range
  Android), low literacy (voice in, voice out), and intermittent attention
  (the assistant re-initiates contact; the user doesn't have to remember to).

Kare is positioned throughout as an **AI assistant, not a clinician**. It
triages, explains, remembers, and pushes people toward real care — it never
claims to replace a nurse, midwife or doctor.

## The solution

**Kare is a voice-first, memory-keeping, multilingual health companion.** Four
capabilities, one continuous relationship:

### 1. Code-switch-native voice consultation
Speak in Yoruba/Hausa/Igbo/Pidgin/English, mixed however you naturally mix it.
Sahara (Intron) streams the transcription; the assistant replies in the *same*
register you used, and speaks it back through Sahara TTS. Latency budget is
tuned for a real conversation, not a form.

### 2. An assistant that remembers you
After every consultation a background model extracts structured notes —
conditions, medications, allergies, what was advised, what's still open — and
merges them into a longitudinal record. Next time you open Kare, it already
knows you have hypertension and takes amlodipine, and it says so. Two patients
with a cough get different questions because Kare remembers their histories.

### 3. Proactive follow-up
When a consultation ends, a model decides **whether**, **when**, and **about
what** Kare should check back in — 12 hours for a fever that hasn't broken,
3 days for a medication change, not at all for a resolved query. At that time a
second model composes a *fresh, non-templated* message from that patient's
actual context ("Hi Tayo 😊 how's the body today — has the fever gone down since
we spoke?"), delivers it as a Web Push notification, and **tapping it drops the
patient back into the same conversation**. Quiet hours, frequency caps and a
stop-after-two-unanswered rule keep it humane.

### 4. Dedicated pregnancy care experience
A pregnant user gets a distinct mode. Onboarding captures LMP / EDD /
ultrasound dating and pregnancy history; Kare computes gestational age and
trimester live (known EDD → ultrasound dating → Naegele), tracks the pregnancy
**week by week**, checks in stage-aware, always surfaces the danger signs for
the current trimester (bleeding, reduced fetal movement, severe headache,
swelling), and keeps encouraging antenatal attendance. The persona is warm and
refers to "our little one" — a companion for the nine months between clinic
visits.

### Agentic core
Every consultation runs through a tool-calling agent loop, not a single prompt:

| Tool | What it does |
|---|---|
| `get_patient_history` | pulls the longitudinal record into the reasoning |
| `check_drug_interactions` | folds in current meds, checks via RxNorm |
| `score_triage` | structured urgency assessment |
| `update_health_record` | writes new findings back to memory |
| `plan_followup` | schedules the proactive check-in |
| `search_medical` | grounded lookup for drug/condition facts |
| `flag_for_escalation` | routes emergencies to real care + local emergency numbers |

Running **concurrently** with the agent is a deterministic **red-flag
interrupt**: a keyword layer (tuned for Pidgin — *"chest dey pain me"*, *"e hard
for me to breathe"*, *"baby no dey move"*) plus a fast classifier model. If
either fires, the agent is cancelled mid-turn and the reply becomes "get to a
hospital now, call 112" with the correct local numbers. Safety is not left to
the LLM's discretion.

## Key technical decisions

| Decision | Why |
|---|---|
| **Sahara (Intron) for STT + TTS** | It is the only voice API built and benchmarked for African code-switched speech. Our benchmark (below) is what settled it on the numbers, not the marketing. Streaming STT for live turns; sentence-pipelined REST TTS because the TTS-stream socket is under-specified. |
| **Provider abstraction layer** | The agent talks to `LLMProvider` / `VoiceProvider` interfaces, never to Groq or Sahara directly. Swapping the STT vendor — or A/B-testing two — is a one-file change. This is also what makes the benchmark honest: the same interface the product uses. |
| **Groq `gpt-oss-120b` / `gpt-oss-20b` for the brain** | Free, fast, and open-weight. 120b for consultation reasoning, 20b for the background jobs (note extraction, red-flag classification, follow-up decisions) that need to be cheap and frequent. `reasoning_effort="low"` to keep the hidden-reasoning token spend down. |
| **Deterministic red-flag interrupt beside the LLM** | Emergencies can't depend on the model choosing to call a tool. Keyword regex + a classifier run concurrently and can abort the turn. |
| **Postgres on Railway, migrations on every deploy** | Boring, durable, one `alembic upgrade head` in the start command. No vendor lock beyond SQL. |
| **PWA + Web Push, not native** | Installs from the browser on any Android, no store, works on a poor connection. Web Push is the only way to re-initiate contact without an app the user has to remember to open. |
| **Follow-up composed fresh every time** | Templates read as spam and erode trust. Every check-in message is generated from that patient's context with an explicit anti-robotic instruction. |
| **Timezone-aware quiet hours, frequency caps, opt-out** | A health assistant that pings you at 2 a.m., or twice a day, is a health assistant you uninstall. |

## What's built

- FastAPI backend (~5k lines): auth, patients, history, medications, voice
  (REST + WebSocket streaming), symptom check, drug interactions, image
  analysis, notifications, pregnancy — all on SQLAlchemy 2.0 + Alembic.
- React 19 PWA: voice consultation screen, dashboard, pregnancy companion,
  settings, notification service worker.
- Agent loop, red-flag layer, clinical state machine, memory extraction,
  follow-up scheduler + worker, pregnancy dating engine.
- 57 passing tests; CI on every push.
- The code-switching ASR benchmark in [`/benchmark`](../benchmark/README.md) —
  see [`BENCHMARK.md`](BENCHMARK.md) / `benchmark/report/REPORT.md`.

## Demo

See [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md). The video walks through: a code-switched
voice consultation → Kare extracting and later recalling the patient's history
→ a proactive follow-up push that reopens the conversation → the pregnancy
companion → the agent autonomously checking a drug interaction → an emergency
phrase triggering escalation.

## Links

- Architecture & data flow: [`ARCHITECTURE.md`](ARCHITECTURE.md)
- Benchmark methodology & results: [`BENCHMARK.md`](BENCHMARK.md)
- Ethics, privacy, inclusion: [`ETHICS.md`](ETHICS.md)
- Deploy runbook: [`../DEPLOY.md`](../DEPLOY.md)
