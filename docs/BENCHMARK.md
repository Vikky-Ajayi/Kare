# Kare — Code-Switching ASR Benchmark: Methodology

**The results, with every number, are in
[`benchmark/report/REPORT.md`](../benchmark/report/REPORT.md)** — regenerated
from the repo by `make benchmark`. This document is the *why*: what we measured,
how, and why it's fair.

Benchmark quality is the highest-weighted judging criterion (30%), so this is
written to be picked apart.

---

## 1. Why a custom benchmark

Kare's users speak Yoruba, Hausa, Igbo and Nigerian Pidgin **with English
clinical terms mixed in**, mid-sentence. Public ASR leaderboards
(Common Voice, FLEURS, OpenASR) are **monolingual** — they score a model on
"clean Yoruba" or "clean English", never on *"ina jin [[EN]]high blood
pressure[[/EN]] tun [[EN]]yesterday[[/EN]]"*. That gap is exactly where a
health voice assistant lives or dies, because the code-switched English words
are the clinically load-bearing ones: drug names, "blood pressure", "twice
daily", "no fever".

So we benchmark on **code-switched clinical speech**, and we score not just
"how many words are wrong" but "did the model keep the medical content and the
code-switch structure".

## 2. Data

**[Intron AfriSwitchCare](https://huggingface.co/datasets/intronhealth/AfriSwitchCare)**
— 108 simulated doctor–patient consultations, 9 languages, the same 12 clinical
conditions each, English code-switched with the matrix language, human-
transcribed. Each row carries the transcription with English spans marked
(`[[EN]]…[[/EN]]`), plus the dataset's own Code-Mixing Index and switch-point
count. Licence CC BY-NC-SA 4.0; evaluation only; **not redistributed** — the
repo commits the *selection*, not the audio.

We use **5 languages**:

| Language | In Kare? | Role |
|---|---|---|
| Yoruba | yes | primary |
| Hausa | yes | primary — least ASR training data of the Nigerian four |
| Igbo | yes | primary — least ASR training data |
| Nigerian Pidgin | yes | primary — no ISO code, hardest to language-hint |
| **Swahili** | **no** | **out-of-family control** |

**Swahili is the fairness instrument.** No Kare user speaks it; it's East
African Bantu, unrelated to the Nigerian four. A model that has genuinely
learned multilingual African speech should handle it comparably. A model that
has merely been tuned on West African data will fall off a cliff. The
"Swahili Δ" column in the report is that test.

### Frozen subset

The full 5-language set is ~6.6 hours — too much for API rate limits and a
reproducible run. We freeze **4 conversations per language** (20 total,
~70 min), chosen **deterministically** (seed `20260915`):

> sort the language's 12 conversations by gold CMI → split into low/mid/high
> thirds → round-robin sample from the thirds with a fixed RNG.

This guarantees every code-mixing difficulty band is represented and removes
cherry-picking. The exact selection is committed as
[`benchmark/frozen_manifest.jsonl`](../benchmark/frozen_manifest.jsonl) — one
line per audio segment, with the reference transcript, gold CMI and gold
switch-point count inline. Anyone with `HF_TOKEN` reconstructs the identical
test set; nobody needs our audio files.

### Segmentation

AfriSwitchCare conversations run 2–8 minutes. Sahara's synchronous endpoint and
the Whisper file APIs all sit around a ~2-minute limit. So **every conversation
is cut into ≤110-second fixed windows before transcription**, the *same* slices
go to *every* model, and the per-segment hypotheses are concatenated before
scoring against the full reference. Boundary word-splits add perhaps 0.5–1 WER
point — **uniformly, to every model**, so rankings are unaffected. This is
stated in the report's "Harness notes".

## 3. Models (≥3 required: a Sahara API + 2 others)

| id | Model | Why it's in |
|---|---|---|
| `sahara` | **Sahara (Intron) STT**, `file_category_telehealth` | The required Sahara API; also the only one built for African code-switch. |
| `groq-whisper-v3` | OpenAI Whisper-large-v3 on Groq | The de-facto open multilingual baseline; what most teams reach for. |
| `groq-whisper-v3-turbo` | Whisper-large-v3-turbo on Groq | Same family, ~3× cheaper/faster — is the accuracy trade worth it? |
| `faster-whisper-tiny` | CTranslate2 Whisper-tiny, **local CPU** | The "runs offline on a clinic laptop, $0/minute" floor. |
| `openai-gpt4o-transcribe` | OpenAI `gpt-4o-transcribe` | A frontier *closed* model — is proprietary scale enough to beat a specialist? Included when `OPENAI_API_KEY` is set; the run is otherwise 4 models (still exceeds the requirement). |

Every model is given its **native ISO-639-1 language hint** where it has one
(`yo`, `ha`, `ig`, `sw`). Pidgin has no code, so Whisper models auto-detect and
Sahara gets `pcm` — this asymmetry is inherent to the languages, not a choice,
and it's disclosed.

All API models get the same retry policy (429/5xx → backoff, so a rate limit
slows a run rather than failing it). Segment hypotheses are cached, so re-runs
only fill gaps.

## 4. Metrics

### Accuracy
- **WER / CER** — word / character error rate after *light* normalisation:
  lower-case, strip punctuation, strip `[Speaker N]` turn markers and the
  dataset's leaked annotator notes (`English>`, `code switch >`, `hausa>` —
  artefacts no ASR model would emit). Corpus-level WER is **pooled over words**,
  not the mean of per-clip WERs.
- **WER (normalised)** — additionally spells out digits (`2` → `two`) and
  unifies a small spelling-variant table (`BP` → `blood pressure`). The gap to
  plain WER is *formatting*, not mis-hearing — reported so a reader can see it.

### Code-switching fidelity — the point of the exercise
- **Code-Mixing Index error** — CMI per Gambäck & Das (2016),
  `100·(1 − max(n_matrix, n_en)/n_tokens)`. We compute it on the reference and
  on the hypothesis **with the same English-dictionary tagger both sides**, so
  the tagger's bias cancels and `|CMI_ref − CMI_hyp|` is a fair measure of "did
  the model preserve the bilingual texture". The dataset's gold CMI is carried
  through as context only.
- **Switch-point count error** — `|switches_ref − switches_hyp|`, same tagger
  both sides. A model that collapses code-switched speech into one language
  scores badly here even if its WER looks OK.
- **English-token recall / precision** — via the word alignment: of the English
  words actually spoken, how many survived (recall); of the words the model
  rendered as English, how many really were (precision).

### Clinical salience — what actually matters at the bedside
- **Medical-term recall** — of the ~180-term clinical lexicon
  (the 12 conditions + common symptom / drug / anatomy vocabulary) present in
  the reference, the fraction that appear in the hypothesis. Missing *insulin*
  is not the same as missing *um*.
- **Number / dosage recall** — same, for spoken numbers and frequency words
  (`39`, `twice`, `daily`). "Take it 3 times" vs "take it" is a safety bug.

### Operational
- **Real-time factor** — wall-clock ÷ audio duration. <1 is faster than real
  time.
- **USD per audio-minute** — public list price. Sahara's per-minute price is
  not published, shown as `n/p`; `faster-whisper` is `$0` (local).

## 5. What the report contains

`benchmark/report/REPORT.md`, all generated from `results/`:

- headline table (every metric, models ranked by WER)
- WER by language + the Swahili-Δ fairness column
- WER by code-mixing intensity (low / mid / high CMI bucket) + a chart —
  *does accuracy fall as code-switching rises?*
- cost & speed table + an accuracy-vs-cost chart
- medical-term & number recall chart
- one transcript excerpt per language, all models side by side
- explicit **harness notes** and **fairness & limitations** sections

## 6. Reproduce

```bash
make bench-install                    # datasets, jiwer, faster-whisper, …
export HF_TOKEN=hf_...                # after 'Agree and access' on the dataset page
bash benchmark/_fetch.sh              # curl the parquet + local model (resumable)
make benchmark                        # subset → transcribe → report
```

`benchmark/frozen_manifest.jsonl`, `benchmark/results/*` and
`benchmark/report/*` are committed, so the report is verifiable without
re-running anything.

## 7. Honest limitations

- AfriSwitchCare is **simulated** consultations by voice artists — cleaner
  acoustics than a real clinic. Absolute WERs are a **floor**; field accuracy
  will be worse for everyone.
- 20 conversations rank models; they don't give tight per-language confidence
  intervals. The report says to treat sub-language gaps under ~3 points as
  noise.
- The English-word detector behind the CMI / switch metrics is a dictionary
  lookup — it mislabels proper nouns and loanwords. Applied identically to
  every model, so comparisons are fair, but the *absolute* CMI error carries a
  systematic offset.
- Pidgin's missing language code disadvantages the models that rely on a hint.
  That's a real property of the language and it's disclosed, not corrected
  away.
