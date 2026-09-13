#!/usr/bin/env bash
# One-off: pull NCAIR/N-ATLaS inference weights straight from HF via curl,
# bypassing huggingface_hub's downloader — which stalls silently and never
# recovers on this network (same symptom the AfriSwitch parquet fetch hit).
# curl -C - resumes; the outer retry loop restarts it when a transfer stalls
# instead of trusting curl's own --retry to notice (it often doesn't).
#
# Deliberately skips optimizer.pt/scheduler.pt/rng_state_*/trainer_state.json
# /training_args.bin — training-resumption artifacts, ~1.9GB each, unused by
# from_pretrained() for inference.
#
# File list is hardcoded per language (confirmed via HfApi().model_info())
# rather than probed with curl, because curl without --fail writes a 404's
# HTML body as if it were the file and still exits 0 — bit us once already
# on the AfriSwitch Swahili parquet. Yoruba has no added_tokens.json.
set -euo pipefail
: "${HF_TOKEN:?set HF_TOKEN first}"

OUT="$(dirname "$0")/data/models"
COMMON="config.json generation_config.json preprocessor_config.json special_tokens_map.json
        tokenizer_config.json tokenizer.json normalizer.json vocab.json merges.txt
        pytorch_model.bin"

fetch() {
  local url="$1" dest="$2"
  mkdir -p "$(dirname "$dest")"
  for attempt in $(seq 1 40); do
    curl -sL --fail -C - --retry 5 --retry-delay 3 --connect-timeout 30 \
      --speed-time 20 --speed-limit 1024 \
      -H "Authorization: Bearer $HF_TOKEN" -o "$dest" "$url" \
      && { echo "   ok $(du -h "$dest" | cut -f1)"; return 0; }
    echo "   attempt $attempt stopped at $(du -h "$dest" 2>/dev/null | cut -f1), resuming..."
    sleep 3
  done
  echo "   GAVE UP on $url" >&2
  return 1
}

for pair in "yoruba:NCAIR1/Yoruba-ASR:" \
            "hausa:NCAIR1/Hausa-ASR:added_tokens.json" \
            "igbo:NCAIR1/Igbo-ASR:added_tokens.json"; do
  lang="$(echo "$pair" | cut -d: -f1)"
  repo="$(echo "$pair" | cut -d: -f2)"
  extra="$(echo "$pair" | cut -d: -f3)"
  dest_dir="$OUT/ncair-$lang"
  for f in $COMMON $extra; do
    dest="$dest_dir/$f"
    [ -s "$dest" ] && { echo ">> $lang/$f (cached)"; continue; }
    echo ">> $lang/$f"
    fetch "https://huggingface.co/$repo/resolve/main/$f" "$dest"
  done
done
echo "ALL DONE"
