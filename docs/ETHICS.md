# Kare — Ethics, Safety & Inclusion Note

Kare handles health information, in people's own languages, for a population
that is often underserved and sometimes low-literacy. That raises the bar. This
note covers what we do about privacy, consent, safety and bias, and what we
know we still get wrong.

## Consent

- **Before the first consultation** the user must actively accept a two-point
  consent gate (`components/ConsentGate.tsx`): (1) what happens to voice data —
  "your audio is sent to Sahara to become text, then discarded; only the text
  is kept, so Kare can remember you"; (2) "Kare is an AI assistant, not a
  doctor, nurse or midwife — it can be wrong; for anything urgent see a health
  worker in person." The choice is stored; consultations are blocked until it
  is given.
- **Proactive follow-up is opt-in.** It turns on only when the user enables
  notifications and grants the browser permission. It can be switched off in
  Settings at any time (`/notifications/preferences`), and every follow-up
  message is a channel the user can simply not reply to — after two unanswered
  check-ins Kare stops.
- **Pregnancy mode is entered deliberately** by the user, who supplies the
  dating information themselves.

## Privacy & data minimisation

- **Audio is never stored.** It is streamed to Sahara for transcription and
  dropped. Only the resulting text is persisted.
- **What is stored:** the conversation transcript, the structured health notes
  extracted from it, medications/conditions the user records, and (if used) the
  pregnancy profile — in a single Postgres database, one owner per row.
- **No third-party analytics, no ad SDKs, no tracking pixels** in the PWA.
- **Auth:** passwords bcrypt-hashed; refresh tokens stored only as SHA-256
  hashes; access via short-lived bearer JWT, not cookies (`allow_credentials=
  False`), which also shrinks CSRF surface.
- **PII stays out of URLs.** The follow-up deep link carries opaque
  conversation and follow-up ids, nothing identifying.
- **Account deletion is real:** `DELETE /patients/me?confirm=DELETE` cascade-
  wipes the patient, conversations, notes, pregnancy record and subscriptions,
  and writes one audit row recording that it happened.
- **Audit trail:** every agent tool call is logged (`audit_logs`) with the
  patient id and parameters, so any automated action can be reconstructed.
- **Third parties:** transcribed text and reasoning prompts are sent to Sahara
  (Intron) and Groq under their terms. Users are told the transcription hop
  happens. RxNorm lookups send drug names only. We send the minimum each
  service needs to do its job.

## Safety

- **Emergencies do not depend on the language model.** A deterministic
  red-flag layer — keyword regex plus a fast classifier — runs *concurrently*
  with the assistant and can abort the turn. It is tuned for how symptoms are
  actually said in Nigerian Pidgin and the other languages ("chest dey pain
  me", "e hard for me to breathe", "baby no dey move"), not just textbook
  English.
- **Escalation is unambiguous.** When a red flag fires, the reply leads with
  the action and the correct local numbers — **112**, or **767 / 122** in
  Lagos — before anything else.
- **Scope is stated repeatedly:** in the consent gate, in the persona prompt
  ("you are an assistant, not a clinician; for anything urgent or any decision
  that matters, a health worker in person"), and on the API root. The
  pregnancy persona explicitly keeps "not a replacement for your midwife or
  doctor; keep your antenatal appointments" in every exchange.
- **The assistant is constrained** to short spoken answers, local disease
  context first (malaria/typhoid before rare differentials), and is told to
  recommend in-person care whenever uncertain rather than guess.
- **Medication safety:** the agent checks interactions (RxNorm) against the
  patient's recorded current medicines, not just the drug asked about.
- **No diagnosis claims, no prescriptions.** Kare explains, triages and
  advises seeking care. It does not tell people they "have" a condition or
  what dose to take.

## Bias & inclusion

- **Language is the inclusion story.** Kare works in Yoruba, Hausa, Igbo,
  Nigerian Pidgin and Nigerian-accented English, and — critically — in the
  *code-switched* mix people actually speak. Voice in / voice out means it does
  not require literacy or typing in English.
- **We measured the bias instead of assuming it away.** The benchmark
  (`benchmark/`, `docs/BENCHMARK.md`) compares five ASR systems on
  code-switched clinical audio, reports results **per language**, includes
  **Swahili as an out-of-family control** to expose models that only work on
  data they were tuned on, and breaks accuracy down by code-mixing intensity.
  Igbo and Hausa have the least training data across every model tested and the
  report says so rather than averaging it out.
- **Known gaps:**
  - Coverage is five languages out of the ~500 spoken in Nigeria. Others are
    completely unserved today.
  - The benchmark data is *simulated* consultations by voice artists — cleaner
    than real clinic audio (noise, crosstalk, distress). Real-world accuracy
    will be lower than the report's numbers, which we treat as a floor.
  - TTS has no neutral Nigerian-English voice, so English is spoken with a
    Yoruba-accented voice — fine for many users, not neutral for all.
  - The LLM is not fine-tuned on Nigerian clinical guidelines; it reasons from
    general medical knowledge with prompt-level steering toward local context.
  - Women's health, and pregnancy specifically, is an area where general LLMs
    are known to underperform — hence the dedicated mode with hard-coded danger
    signs rather than trusting the model to remember them.

## Responsible data use

- We do **not** train models on user conversations. Provider APIs are used for
  inference only.
- Benchmark datasets (Intron AfriSwitchCare) are used under their CC BY-NC-SA
  licence, for evaluation only, and are **not redistributed** — the repo
  commits the *selection manifest* and the *scores*, not the audio.
- Any consented demo audio we might submit is de-identified (no names, no
  identifying detail) and shared only with explicit permission from the
  speaker.

## Accountability

- The system is small enough to audit: ~5k lines of backend, every external
  call behind one of two interfaces, every automated action in `audit_logs`.
- Failure modes are explicit: cold-start fallback, agent iteration cap with a
  safe fallback reply, follow-up frequency caps, config validation that
  refuses to start a broken production deploy.
- This is a prototype. It is not a medical device and is not certified as one.
  It is a first-line information and continuity tool that consistently points
  people toward professional care.
