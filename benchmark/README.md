# Kare code-switching ASR benchmark

Kare's users speak Yoruba, Hausa, Igbo and Nigerian Pidgin **with English
clinical terms mixed in** — *"the doctor talk say my BP dey high, I dey take
amlodipine"*. The voice layer has to transcribe both the matrix language and
the embedded English, and the English words are usually the ones that matter
clinically. Public ASR leaderboards are monolingual, so this benchmark exists
to pick Kare's STT provider on the axis that actually counts.

## What it does

- **Data** — [Intron AfriSwitchCare](https://huggingface.co/datasets/intronhealth/AfriSwitchCare):
  simulated doctor–patient consultations, English code-switched with an African
  language, human-transcribed with `[[EN]]…[[/EN]]` spans marking the English.
  We use Yoruba, Hausa, Igbo, Pidgin + **Swahili as an out-of-family control**.
- **Frozen subset** — 4 conversations per language, stratified across each
  language's Code-Mixing Index range (seed `20260915`). Frozen to
  [`frozen_manifest.jsonl`](frozen_manifest.jsonl) so the exact test set is
  reproducible; raw audio is not committed.
- **Models (5)** — Sahara (Intron), Groq `whisper-large-v3`, Groq
  `whisper-large-v3-turbo`, `faster-whisper tiny` (local CPU), OpenAI
  `gpt-4o-transcribe`. Any model whose API key is absent is skipped, so a run
  needs `SAHARA_API_KEY`, `GROQ_API_KEY` and `OPENAI_API_KEY` for the full set.
- **Metrics** — WER/CER (two normalisation levels), medical-term recall,
  number/dosage recall, Code-Mixing-Index error, switch-point count error,
  English-token recall/precision, real-time factor, cost per audio-minute.
- **Output** — [`report/REPORT.md`](report/REPORT.md) with tables, charts and
  per-language transcript samples, all regenerated from `results/`.

## Run it

```bash
make bench-install                     # one-time: datasets, jiwer, faster-whisper…
export HF_TOKEN=hf_...                 # needs 'Agree and access' on the dataset page
make bench-data                        # download AfriSwitchCare parquet
make benchmark                         # subset -> transcribe -> report
```

Or step by step:

```bash
python -m benchmark.subset             # build the frozen subset + segment audio
python -m benchmark.run                # every model with a key present
python -m benchmark.run --models sahara groq-whisper-v3-turbo
python -m benchmark.run --limit 4      # smoke test (4 segments/model)
python -m benchmark.report             # REPORT.md + charts/
```

Segment hypotheses are cached under `results/hyp_<model>.jsonl`, so a re-run
only calls the API for what is missing — safe to Ctrl-C and resume.

## Layout

| file | role |
|---|---|
| `config.py` | paths, language maps, model registry, subset params |
| `download_data.py` | pull AfriSwitchCare parquet into the HF cache |
| `subset.py` | freeze the stratified subset, decode + segment audio |
| `audio.py` | WAV read/write, fixed-window segmentation (no librosa) |
| `normalize.py` | text normalisation for scoring |
| `metrics.py` | WER/CER, CMI, switch points, clinical-term recall |
| `models/` | one adapter per ASR system, common `transcribe()` call |
| `run.py` | orchestrate + score → `results/` |
| `report.py` | `results/` → `report/REPORT.md` + charts |

## Notes

- Every conversation is cut into ≤110 s windows before transcription (Sahara's
  sync endpoint and Whisper file limits both sit near there). The same slices
  go to every model; hypotheses are concatenated before scoring.
- `AfriSwitch` (the larger, non-clinical Intron set) is gated behind manual
  approval. If approved, drop its parquet under `benchmark/data/afriswitch/`
  and it can be wired in as a second corpus.
