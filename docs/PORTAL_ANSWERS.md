# Submission portal — ready-to-paste answers

Word counts are approximate, matching the portal's stated limits.

---

**Solution Title**

> Kare — A Code-Switching Voice Health Companion for Nigeria

---

**1. A short description of the problem your app addresses** (~50 words — this
one runs a bit longer to actually sound like a person said it; trim if the
field pushes back)

> Most people in Nigeria don't die because their illness was untreatable —
> they die because help came too late, because they couldn't get a doctor to
> understand what they were feeling, or because they took a drug that clashed
> with something else they were already on. Nigeria has the highest maternal
> death toll in the world — over 28% of all global maternal deaths, mostly
> from delay (WHO). Add 500+ languages where people naturally mix English
> with Yoruba, Hausa, Igbo or Pidgin, and WHO's own estimate that medication
> errors kill about 1 in a million people worldwide, and the real problem
> isn't the disease. It's the delay, the miscommunication, and the wrong
> drug.

<sub>Sources: WHO/UNICEF/UNFPA *Trends in Maternal Mortality* (Nigeria's
28.3% share of global maternal deaths); WHO *Global Burden of Preventable
Medication-Related Harm* (medication-error mortality); academic ASR
literature documenting code-switching's effect on speech recognition in
Nigeria (arXiv:2604.16287).</sub>

---

**2. Describe your target user(s) and the potential number of users it could impact** (~50 words)

> Nigeria's 200M+ population, across 500+ languages where code-switching is
> just how people talk day to day, and maternal mortality is the highest in
> the world. Primary users: pregnant women needing continuous antenatal
> support, and anyone managing an ongoing condition who can't easily reach a
> clinic — realistically tens of millions of smartphone users across West
> Africa's Anglophone corridor.

---

**3. Describe how your app solves the user problem** (~50 words)

> Kare is a voice-first AI assistant that natively understands code-switched
> speech via Sahara, remembers each patient's history between visits,
> proactively decides when to check back in (not just when asked), and runs
> a dedicated week-by-week pregnancy companion — replacing static forms with
> a continuous conversation in the patient's own mixed-language register.

---

**4. Does your solution support code-switching?**

> Yes

---

**5. Does your solution use the Sahara APIs?**

> Yes

---

**6. How is the solution agentic? What downstream task does the code-switched transcript enable?** (~50 words)

> Kare runs a tool-calling agent (OpenAI's open-weight `gpt-oss-120b`, served
> via Groq) that decides on its own when to check drug interactions, score
> triage urgency, update the clinical record, or escalate an emergency. The
> code-switched transcript feeds directly into these tools, so accurately
> capturing embedded English terms determines whether triage and
> interaction-checking are actually safe.

---

**7. High-level technical overview: key design decisions, at least 3 architecture choices and the tradeoffs you considered** (~250 words)

> Three decisions mattered most. **(1) Provider abstraction:**
> `LLMProvider`/`VoiceProvider` ABCs mean the agent never imports Groq or
> Sahara directly — swapping models, or adding a benchmark adapter (5 ASR
> models compared: Sahara, two Groq Whisper variants, a local CPU model, and
> NCAIR/N-ATLaS), required zero changes to business logic. Tradeoff: an
> extra indirection layer for a hackathon timeline — justified because the
> challenge itself requires swapping models to benchmark them.
> **(2) Safety-first concurrency:** every patient turn runs a deterministic
> keyword red-flag check *and* an LLM classifier concurrently with the main
> consultation agent; whichever fires first wins, and the agent is cancelled
> if either flags an emergency. Tradeoff: extra model calls per turn (cost
> and latency) — justified because emergency detection in a health context
> must never depend on one model's judgment alone.
> **(3) Proactive follow-ups as a decided queue, not a blast:** at
> consultation end, the model itself decides whether a follow-up is
> warranted and drafts natural, context-specific language — never a
> template, so two patients with the same condition get different messages.
> A worker processes the due queue respecting quiet hours, a 20-hour
> frequency cap, and stop-after-2-unanswered. Tradeoff: more moving parts
> (scheduler, push subscriptions, a state machine) than a cron reminder —
> justified because generic reminders are what patients already ignore.
> Postgres on Railway (not a managed BaaS) kept infrastructure ownership
> simple and portable; FastAPI + SQLAlchemy 2.0 for a typed,
> migration-safe backend.

---

**8. Ethics/Inclusion: privacy, consent, safety, security, and responsible data use** (~100 words)

> Voice consent is explicit and granular: before a patient's first
> consultation, a two-part consent screen states exactly what happens to
> their audio (sent to Sahara for transcription, then discarded — only text
> is kept). Kare states plainly it is an AI assistant, not a clinician, and
> every emergency-flagged reply leads with local emergency numbers (112,
> plus Lagos-specific lines) rather than a diagnosis. Patients can delete
> their account and all data outright. The benchmark itself is an inclusion
> commitment: it evaluates Igbo and Hausa — the two lowest-resourced
> languages across every model tested — rather than only the languages
> vendors already do well on, so gaps stay visible instead of hidden.

---

**Demo Video URL** — record and paste (max 5 min, must show code-switching)

**Benchmark Report Link (PDF, max 3 pages)**

> https://raw.githubusercontent.com/Vikky-Ajayi/Kare/main/docs/Kare_Benchmark_Report.pdf

**Benchmark Audios Link**

> Listenable samples (8 clips, ~35s, Yoruba/Hausa/Igbo/Pidgin — English
> code-switched, with per-clip metadata: language, duration, transcript,
> English gloss):
>
> https://huggingface.co/datasets/vikkyblacq/kare-codeswitch-samples
>
> These are original sentences we wrote and synthesized via Sahara TTS —
> illustrative of the code-switching pattern, not excerpts from the actual
> benchmark corpus. The 20 conversations actually scored in the benchmark
> come from Intron's own `AfriSwitchCare` (clinical, primary) and
> `AfriSwitch` (general-domain, secondary) datasets, gated on Hugging Face
> under CC BY-NC-SA 4.0:
>
> - https://huggingface.co/datasets/intronhealth/AfriSwitchCare
> - https://huggingface.co/datasets/intronhealth/AfriSwitch
>
> Exact clip IDs, per-clip transcripts and scores are in
> `benchmark/results/summary.json`, reproducible via `make benchmark`.

<sub>Why samples instead of the real clips: both benchmark datasets sit
behind a Hugging Face access gate (AfriSwitchCare requires a click-through +
contact info; AfriSwitch requires manual approval), which signals Intron
wants access tracked per-recipient rather than mirrored elsewhere — even
though the CC BY-NC-SA 4.0 license itself would permit sharing with
attribution. Since Intron is both the data owner and the challenge
organizer, rehosting their gated clips wasn't worth the risk. The 8 sample
clips sidestep that entirely: original text, synthesized audio, no human
speaker involved, so there's no consent/redistribution question at
all.</sub>
