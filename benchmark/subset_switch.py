"""
Freeze the AfriSwitch generalisation-check subset.

AfriSwitch has the same annotation convention as AfriSwitchCare
(``transcription_tagged`` with ``[[EN]]…[[/EN]]`` spans, ``cmi``,
``num_switch_points``) but is structured as short, general-domain
*utterances* (a handful of seconds each), not multi-turn clinical
conversations — no ``diagnosis``, no segmentation needed.

For each of the 5 languages we take ``UTTS_PER_LANG`` utterances from
whichever parquet shard(s) are present under ``data/afriswitch/<lang>/``,
stratified across that language's CMI range the same way `subset.py` does
for AfriSwitchCare. Each row becomes exactly one "segment" (no 110s window
cut — utterances are already well under that).

Writes ``benchmark/frozen_manifest_switch.jsonl`` (committed).

    python -m benchmark.subset_switch            # build it
    python -m benchmark.subset_switch --show      # print what is already frozen
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

from benchmark.audio import resample_linear, write_wav
from benchmark.config import (
    AUDIO_DIR,
    BENCH_LANGS,
    LANG_META,
    SUBSET_SEED,
    SWITCH_MANIFEST,
    SWITCH_PARQUET_DIR,
    TARGET_SR,
    UTTS_PER_LANG,
)
from benchmark.subset import _audio_array, _is_complete_parquet, _pick_indices, _read_rows


def _parquet_files_for(lang: str) -> list[Path]:
    return sorted(p for p in (SWITCH_PARQUET_DIR / lang).glob("*.parquet")
                  if _is_complete_parquet(p))


def build() -> int:
    rng = random.Random(SUBSET_SEED)
    rows_out: list[dict] = []
    summary: list[tuple] = []
    missing = []

    for lang in BENCH_LANGS:
        meta = LANG_META[lang]
        pq_paths = _parquet_files_for(lang)
        if not pq_paths:
            missing.append(lang)
            print(f"[{lang}] no parquet under {SWITCH_PARQUET_DIR / lang} — skipping", flush=True)
            continue
        # one shard is thousands of utterances — plenty; read only the first
        print(f"[{lang}] reading {pq_paths[0].name} ...", flush=True)
        rows = _read_rows(pq_paths[0])
        cmis = [float(r["cmi"]) for r in rows]
        idx = _pick_indices(cmis, UTTS_PER_LANG, rng)
        print(f"   {len(rows)} utterances, CMI {min(cmis):.0f}–{max(cmis):.0f}; "
              f"picked {len(idx)} (CMI {[round(cmis[i]) for i in idx]})")

        for i in idx:
            row = rows[i]
            arr, sr = _audio_array(row["audio"])
            if sr != TARGET_SR:
                arr = resample_linear(arr, sr, TARGET_SR)
                sr = TARGET_SR
            utt_id = f"{lang}-{i:04d}"
            wav = AUDIO_DIR / "switch" / lang / f"{utt_id}.wav"
            dur = write_wav(wav, arr, sr)
            seg = {"path": str(wav), "index": 0, "start": 0.0, "end": round(dur, 2),
                   "dur": round(dur, 2)}

            rows_out.append({
                "conv_id": utt_id,
                "language": lang,
                "kare_code": meta["kare"],
                "sahara_code": meta["sahara"],
                "whisper_code": meta["whisper"],
                "in_family": meta["in_family"],
                "diagnosis": None,           # not a clinical corpus
                "duration_s": round(dur, 2),
                "n_segments": 1,
                "cmi_gold": round(float(row["cmi"]), 2),
                "switch_gold": int(row["num_switch_points"]),
                "num_turns": None,
                "transcription": row["transcription"],
                "transcription_tagged": row["transcription_tagged"],
                "segment": seg,
            })
        summary.append((lang, len(idx), round(sum(r["duration_s"] for r in rows_out
                                                    if r["language"] == lang), 1)))

    SWITCH_MANIFEST.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows_out))
    total_min = sum(r["duration_s"] for r in rows_out) / 60
    print(f"\nfrozen {len(rows_out)} utterances / {total_min:.1f} min audio")
    print(f"  -> {SWITCH_MANIFEST}")
    for lang, n, secs in summary:
        print(f"   {lang:9s} {n:3d} utterances  {secs/60:5.1f} min")
    if missing:
        print(f"\n!  languages skipped (no parquet — run `make bench-data-switch`): "
              f"{', '.join(missing)}")
    return 0


def show() -> int:
    if not SWITCH_MANIFEST.exists():
        print("no frozen switch manifest — run `python -m benchmark.subset_switch` first")
        return 1
    rows = [json.loads(ln) for ln in SWITCH_MANIFEST.read_text().splitlines() if ln.strip()]
    by_lang: dict[str, list] = {}
    for r in rows:
        by_lang.setdefault(r["language"], []).append(r)
    for lang, rs in sorted(by_lang.items()):
        mins = sum(r["duration_s"] for r in rs) / 60
        print(f"{lang:9s}  {len(rs)} utterances  {mins:5.1f} min  "
              f"CMI {sorted(round(r['cmi_gold']) for r in rs)}")
    print(f"total: {len(rows)} utterances, {sum(r['duration_s'] for r in rows) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()
    sys.exit(show() if args.show else build())
