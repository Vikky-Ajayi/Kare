#!/usr/bin/env bash
# Resumable curl fetch of AfriSwitch (the broader, non-clinical corpus) — one
# shard per language, which is thousands of short utterances, plenty for the
# frozen generalisation-check subset. Manually-gated: request access at
# https://huggingface.co/datasets/intronhealth/AfriSwitch first.
#
# hf_hub_download stalls on some links; plain curl with resume does not.
# Safe to Ctrl-C and re-run — it resumes each file. This can take a while on
# a slow link; run it in the background (nohup ... &) rather than foreground.
set -u
TOKEN="${HF_TOKEN:?export HF_TOKEN first}"

fetch() {   # url  dest
  local url="$1" dest="$2"
  mkdir -p "$(dirname "$dest")"
  echo ">> $(basename "$dest")"
  for attempt in $(seq 1 20); do
    curl -sL -C - --retry 5 --retry-delay 3 --connect-timeout 30 \
      --speed-time 30 --speed-limit 512 \
      -H "Authorization: Bearer $TOKEN" -o "$dest" "$url" \
      && { echo "   ok ($(du -h "$dest" | cut -f1))"; return 0; }
    echo "   attempt $attempt stopped at $(du -h "$dest" 2>/dev/null | cut -f1), resuming..."
    sleep 2
  done
  echo "   GAVE UP on $dest"; return 1
}

SW="https://huggingface.co/datasets/intronhealth/AfriSwitch/resolve/main/data"
OUT="benchmark/data/afriswitch/data"
# shard 0 of each of Kare's 5 languages (yoruba/hausa/igbo/pidgin have 4
# shards, swahili has 2 — shard 0 alone is thousands of utterances, far more
# than UTTS_PER_LANG needs).
for lang in yoruba hausa igbo pidgin; do
  fetch "$SW/$lang/test-00000-of-00004.parquet" "$OUT/$lang/test-00000-of-00004.parquet"
done
fetch "$SW/swahili/test-00000-of-00002.parquet" "$OUT/swahili/test-00000-of-00002.parquet"

echo "ALL DONE"
du -h "$OUT"/*/*.parquet 2>/dev/null
