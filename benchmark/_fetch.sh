#!/usr/bin/env bash
# Resumable curl fetch of everything the benchmark needs from HuggingFace:
#   - AfriSwitchCare parquet shards (5 languages)
#   - faster-whisper-tiny weights (local ASR baseline)
#
# hf_hub_download stalls on some links; plain curl with resume does not.
# Safe to Ctrl-C and re-run — it resumes each file.
set -u
TOKEN="${HF_TOKEN:?export HF_TOKEN first}"

fetch() {   # url  dest
  local url="$1" dest="$2"
  mkdir -p "$(dirname "$dest")"
  echo ">> $(basename "$dest")"
  for attempt in $(seq 1 10); do
    curl -sL -C - --retry 5 --retry-delay 3 --connect-timeout 30 \
      --speed-time 60 --speed-limit 1024 \
      -H "Authorization: Bearer $TOKEN" -o "$dest" "$url" \
      && { echo "   ok ($(du -h "$dest" | cut -f1))"; return 0; }
    echo "   attempt $attempt stopped at $(du -h "$dest" 2>/dev/null | cut -f1), resuming..."
    sleep 3
  done
  echo "   GAVE UP on $dest"; return 1
}

CARE="https://huggingface.co/datasets/intronhealth/AfriSwitchCare/resolve/main/data"
OUT="benchmark/data/afriswitchcare/data"
for lang in hausa igbo yoruba pidgin swahili; do
  fetch "$CARE/$lang/test-00000-of-00001.parquet" "$OUT/$lang/test-00000-of-00001.parquet"
done

FW="https://huggingface.co/Systran/faster-whisper-tiny/resolve/main"
MOUT="benchmark/data/models/faster-whisper-tiny"
for f in config.json model.bin tokenizer.json vocabulary.txt; do
  fetch "$FW/$f" "$MOUT/$f"
done

echo "ALL DONE"
du -h "$OUT"/*/*.parquet "$MOUT"/model.bin 2>/dev/null
