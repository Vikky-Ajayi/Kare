"""
Freeze the benchmark's test subset.

For each of the 5 languages we take ``CONVOS_PER_LANG`` conversations from
AfriSwitchCare, chosen to span that language's Code-Mixing Index range: the
12 conversations are sorted by gold CMI and split into low / mid / high
thirds, then sampled round-robin from the thirds with a fixed RNG. Every
difficulty band is represented without hand-picking.

Each chosen conversation is decoded to a 16 kHz mono WAV and cut into
<=110 s windows (see audio.py). The result is written to
``benchmark/frozen_manifest.jsonl`` — one line per **segment** — and
committed, so the exact test set is reproducible without re-downloading.

Reads the parquet shards directly (pyarrow); it does not go through
``datasets.load_dataset`` streaming, which stalls on a slow link.

    python -m benchmark.subset            # build it
    python -m benchmark.subset --show     # print what is already frozen
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np

from benchmark.audio import decode_audio_bytes, resample_linear, segment_wav, write_wav
from benchmark.config import (
    AUDIO_DIR,
    BENCH_LANGS,
    CONVOS_PER_LANG,
    DATA_DIR,
    LANG_META,
    MANIFEST,
    SEG_DIR,
    SEGMENT_SECONDS,
    SUBSET_SEED,
    TARGET_SR,
)
from benchmark.metrics import cmi_from_tags, switch_points_from_tags

PARQUET_DIR = DATA_DIR / "afriswitchcare" / "data"


def _is_complete_parquet(p: Path) -> bool:
    """A finished parquet file starts and ends with the magic bytes b'PAR1'."""
    if p.stat().st_size < 8:
        return False
    with p.open("rb") as fh:
        head = fh.read(4)
        fh.seek(-4, 2)
        return head == b"PAR1" and fh.read(4) == b"PAR1"


def _parquet_for(lang: str) -> Path | None:
    cands = sorted(p for p in (PARQUET_DIR / lang).glob("*.parquet") if _is_complete_parquet(p))
    return cands[0] if cands else None


def _read_rows(path: Path) -> list[dict]:
    import pyarrow.parquet as pq

    tbl = pq.read_table(path)
    cols = tbl.column_names
    n = tbl.num_rows
    rows = []
    for i in range(n):
        rows.append({c: tbl.column(c)[i].as_py() for c in cols})
    return rows


def _pick_indices(cmis: list[float], k: int, rng: random.Random) -> list[int]:
    order = sorted(range(len(cmis)), key=lambda i: cmis[i])
    n = len(order)
    thirds = [order[: n // 3], order[n // 3: 2 * n // 3], order[2 * n // 3:]]
    for t in thirds:
        rng.shuffle(t)
    picked: list[int] = []
    b = 0
    while len(picked) < k and any(thirds):
        t = thirds[b % 3]
        if t:
            picked.append(t.pop())
        b += 1
    return sorted(picked)


def _audio_array(cell) -> tuple[np.ndarray, int]:
    """A HF Audio parquet cell is {'bytes': <encoded>, 'path': str} or already
    {'array': [...], 'sampling_rate': int}."""
    if isinstance(cell, dict) and cell.get("array") is not None:
        return np.asarray(cell["array"], dtype=np.float32), int(cell["sampling_rate"])
    if isinstance(cell, dict) and cell.get("bytes"):
        return decode_audio_bytes(cell["bytes"])
    if isinstance(cell, bytes | bytearray):
        return decode_audio_bytes(bytes(cell))
    raise TypeError(f"unrecognised audio cell: {type(cell)}")


def build() -> int:
    rng = random.Random(SUBSET_SEED)
    rows_out: list[dict] = []
    summary: list[tuple] = []

    missing = []
    for lang in BENCH_LANGS:
        meta = LANG_META[lang]
        pq_path = _parquet_for(lang)
        if pq_path is None:
            missing.append(lang)
            print(f"[{lang}] no parquet under {PARQUET_DIR / lang} — skipping", flush=True)
            continue
        print(f"[{lang}] reading {pq_path.name} ...", flush=True)
        rows = _read_rows(pq_path)

        gold_cmi = [
            float(r["cmi"]) if r.get("cmi") is not None else cmi_from_tags(r["transcription_tagged"])
            for r in rows
        ]
        idx = _pick_indices(gold_cmi, CONVOS_PER_LANG, rng)
        print(f"   {len(rows)} conversations, CMI {min(gold_cmi):.0f}–{max(gold_cmi):.0f}; "
              f"picked {idx} (CMI {[round(gold_cmi[i]) for i in idx]})")

        for i in idx:
            row = rows[i]
            arr, sr = _audio_array(row["audio"])
            if sr != TARGET_SR:
                arr = resample_linear(arr, sr, TARGET_SR)
                sr = TARGET_SR
            conv_id = f"{lang}-{i:02d}"
            wav = AUDIO_DIR / lang / f"{conv_id}.wav"
            dur = write_wav(wav, arr, sr)
            segs = segment_wav(wav, SEG_DIR / lang, seconds=SEGMENT_SECONDS)

            sw_gold = row.get("num_switch_points")
            base = {
                "conv_id": conv_id,
                "language": lang,
                "kare_code": meta["kare"],
                "sahara_code": meta["sahara"],
                "whisper_code": meta["whisper"],
                "in_family": meta["in_family"],
                "diagnosis": row.get("diagnosis"),
                "duration_s": round(dur, 2),
                "n_segments": len(segs),
                "cmi_gold": round(gold_cmi[i], 2),
                "switch_gold": int(sw_gold) if sw_gold is not None
                else switch_points_from_tags(row["transcription_tagged"]),
                "num_turns": row.get("num_turns"),
                "transcription": row["transcription"],
                "transcription_tagged": row["transcription_tagged"],
            }
            for seg in segs:
                rows_out.append({**base, "segment": seg})
            summary.append((conv_id, row.get("diagnosis"), round(dur, 1), len(segs), round(gold_cmi[i])))

    MANIFEST.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows_out))
    per_conv = {r["conv_id"]: r["duration_s"] for r in rows_out}
    print(f"\nfrozen {len(per_conv)} conversations / {len(rows_out)} segments / "
          f"{sum(per_conv.values()) / 60:.1f} min audio")
    print(f"  -> {MANIFEST}")
    for r in summary:
        print("   %-12s %-26s %6.1fs  %dseg  CMI%3d" % r)
    if missing:
        print(f"\n!  languages skipped (no parquet): {', '.join(missing)}")
    return 0


def show() -> int:
    if not MANIFEST.exists():
        print("no frozen manifest — run `python -m benchmark.subset` first")
        return 1
    convs: dict[str, dict] = {}
    for line in MANIFEST.read_text().splitlines():
        r = json.loads(line)
        convs.setdefault(r["conv_id"], r)
    by_lang: dict[str, list] = {}
    for c in convs.values():
        by_lang.setdefault(c["language"], []).append(c)
    for lang, cs in sorted(by_lang.items()):
        mins = sum(c["duration_s"] for c in cs) / 60
        print(f"{lang:9s}  {len(cs)} conv  {mins:5.1f} min  "
              f"CMI {sorted(c['cmi_gold'] for c in cs)}")
    print(f"total: {len(convs)} conversations, "
          f"{sum(c['duration_s'] for c in convs.values()) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()
    sys.exit(show() if args.show else build())
