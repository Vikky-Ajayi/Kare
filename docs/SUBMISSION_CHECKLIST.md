# Kare — Submission Checklist

**Deadline: 15 September 2026, 11:59 pm WAT. One submission per access token
(780826) — no second chances.** Portal: the same one used for the Indaba
challenge, log in with `vikkyoluwabukunmi@gmail.com` + token `780826`.

Judging weights: **Benchmark 30%** · Product & Fit 25% · Real-World Impact 20% ·
Technical Execution 15% · Ethics & Inclusion 10%.

---

## The six required items

| # | Item | Status | Where |
|---|---|---|---|
| 1 | **Solution Description** — problem, users, solution, key technical decisions | ✅ drafted | [`docs/SOLUTION.md`](SOLUTION.md) |
| 2 | **Demo video** — working prototype, unlisted/public YouTube, < 4 min | ⏳ record | script: [`docs/DEMO_SCRIPT.md`](DEMO_SCRIPT.md) |
| 3 | **Docs** — code / technical documentation | ✅ | [`README.md`](../README.md), [`docs/ARCHITECTURE.md`](ARCHITECTURE.md), repo |
| 4 | **Benchmark Report** — 3+ speech models, pros & cons of each | ✅ 4/5 models complete, **Sahara wins WER** (53.1 vs 59.4 best Whisper) | method: [`docs/BENCHMARK.md`](BENCHMARK.md) · results: [`benchmark/report/REPORT.md`](../benchmark/report/REPORT.md) |
| 5 | **Ethics / Inclusion Note** — privacy, consent, safety, responsible data use | ✅ drafted | [`docs/ETHICS.md`](ETHICS.md) |
| 6 | **Benchmark Audios** (optional) — consented, de-identified | ➖ skipping (AfriSwitchCare is not ours to redistribute; we submit the manifest instead) | [`benchmark/frozen_manifest.jsonl`](../benchmark/frozen_manifest.jsonl) |

---

## Blockers to clear before submitting

- [x] ~~Sahara API credits~~ — topped up 11 Sep; full 80/80-segment run
      complete, Sahara has the best WER of the 4 models run so far.
- [ ] **OpenAI API key** for `gpt-4o-transcribe` (the 5th model, optional —
      the required "3+ models" is already met). Add `OPENAI_API_KEY=sk-…` to
      `.env` (~$1 covers the run), then:
      ```bash
      make bench-run && make bench-report   # fills the OpenAI column, keeps the rest cached
      ```
- [ ] **Deploy** (Railway + Vercel) so the demo shows a live URL — follow
      [`DEPLOY.md`](../DEPLOY.md). Needs a Railway account (~$5/mo) + Vercel
      (free).
- [ ] **Record the demo** once deployed — [`docs/DEMO_SCRIPT.md`](DEMO_SCRIPT.md),
      upload unlisted to YouTube.

---

## Pre-submit review pass

- [x] `make test` green · `make lint` clean
- [x] `benchmark/report/REPORT.md` has a real Sahara row (not "incomplete")
- [ ] Live URL loads on a phone; the 4 demo flows all work end to end
- [ ] Consent gate appears before the first consultation
- [ ] A follow-up push actually arrives and its notification reopens the thread
- [ ] Emergency phrase ("chest dey pain me") → immediate escalation with 112 / 767 / 122
- [ ] Every doc link in the submission resolves
- [ ] Solution Description names the category (**Health**) and the population
      size (Nigeria 200M+, ~7 in 10 code-switch, among the world's highest
      maternal mortality)
- [ ] Demo video is under 4:00 and unlisted-accessible (test in an incognito window)
- [ ] Nothing in the repo leaks a live secret (`.env` is gitignored — confirm
      `git ls-files | grep -c '\.env$'` is 0)

---

## What to paste into the portal

- **Solution Description:** the body of [`SOLUTION.md`](SOLUTION.md) (trim to the
  portal's length limit if any; lead with the problem paragraph).
- **Demo:** the YouTube link.
- **Docs:** the GitHub repo URL + a line pointing at `README.md` → `docs/`.
- **Benchmark Report:** link to `benchmark/report/REPORT.md` on GitHub, and
  attach/point to `docs/BENCHMARK.md` for methodology. Mention: 4 models (5th —
  OpenAI — optional), Sahara has the lowest WER (53.1) and wins by the widest
  margin on Hausa and Pidgin — the two languages general Whisper handles worst.
  AfriSwitchCare, frozen seed-deterministic subset, per-language + CMI-bucketed,
  Swahili control, `make benchmark` reproduces every number.
- **Ethics Note:** the body of [`ETHICS.md`](ETHICS.md).

---

## One-line pitch (for the top of the Solution Description)

> Kare is a voice-first health companion for Nigeria that understands
> code-switched Yoruba/Hausa/Igbo/Pidgin-English speech, remembers each patient
> between visits, decides on its own when to check back in, and walks a
> pregnancy week by week — an agent, not a form, built on Sahara voice and
> benchmarked to prove the speech layer works on the language people actually
> speak.
