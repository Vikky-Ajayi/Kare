"""
Run the ASR models over the frozen subset and score them.

    python -m benchmark.run                      # every model we have keys for
    python -m benchmark.run --models sahara groq-whisper-v3
    python -m benchmark.run --limit 4            # smoke test: 4 segments/model

Outputs (all committed, all reproducible):
    results/hyp_<model>.jsonl       one line per segment: raw hypothesis + timing
    results/scores_<model>.jsonl    one line per conversation: full Score
    results/summary.json            per-model / per-language aggregates
    results/run_meta.json           what ran, when, versions, dataset revision

Segment hypotheses are cached, so a re-run only calls the API for segments
that are missing — safe to Ctrl-C and resume.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from benchmark.config import MANIFEST, PRICE_PER_MIN, RESULTS_DIR, default_models
from benchmark.metrics import Score, aggregate, score


def _load_manifest() -> list[dict]:
    if not MANIFEST.exists():
        sys.exit("no frozen_manifest.jsonl — run `python -m benchmark.subset` first")
    return [json.loads(ln) for ln in MANIFEST.read_text().splitlines() if ln.strip()]


def _hyp_path(model_id: str) -> Path:
    return RESULTS_DIR / f"hyp_{model_id}.jsonl"


def _load_hyps(model_id: str, *, keep_failed: bool = True) -> dict[str, dict]:
    p = _hyp_path(model_id)
    if not p.exists():
        return {}
    out: dict[str, dict] = {}
    for line in p.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if keep_failed or r.get("ok"):
            out[r["seg_path"]] = r
    return out


def transcribe_all(model_id: str, rows: list[dict], *, limit: int | None,
                   retry_failed: bool = True) -> dict[str, dict]:
    from benchmark.models import load

    cached = _load_hyps(model_id)
    if retry_failed:
        failed = {k for k, v in cached.items() if not v.get("ok")}
        if failed:
            done = {k: v for k, v in cached.items() if k not in failed}
            _hyp_path(model_id).write_text(
                "".join(json.dumps(v, ensure_ascii=False) + "\n" for v in done.values())
            )
            print(f"  [{model_id}] retrying {len(failed)} previously-failed segments")
        else:
            done = cached
    else:
        done = cached
    todo = [r for r in rows if r["segment"]["path"] not in done]
    if limit:
        todo = todo[:limit]
    if not todo:
        print(f"  [{model_id}] all {len(done)} segments cached")
        return done

    print(f"  [{model_id}] {len(todo)} segments to transcribe ({len(done)} cached)")
    adapter = load(model_id)
    warmed: set[str] = set()
    fh = _hyp_path(model_id).open("a")
    try:
        for n, r in enumerate(todo, 1):
            seg = r["segment"]
            lang = r["language"]
            if lang not in warmed:
                adapter.warm(lang)
                warmed.add(lang)
            hyp = adapter.transcribe(Path(seg["path"]), language=lang)
            rec = {
                "seg_path": seg["path"], "conv_id": r["conv_id"], "language": lang,
                "seg_index": seg["index"], "audio_s": round(hyp.audio_s, 2),
                "latency_s": round(hyp.latency_s, 2), "ok": hyp.ok,
                "error": hyp.error, "text": hyp.text, "raw": hyp.raw,
            }
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            done[seg["path"]] = rec
            flag = "" if hyp.ok else f"  !! {hyp.error}"
            print(f"    {n:>3}/{len(todo)}  {r['conv_id']} seg{seg['index']:02d}  "
                  f"{hyp.audio_s:5.1f}s -> {hyp.latency_s:5.1f}s  "
                  f"{len(hyp.text):4d} chars{flag}")
    finally:
        fh.close()
    return done


def score_model(model_id: str, rows: list[dict], hyps: dict[str, dict]) -> list[dict]:
    # reassemble conversation-level hypotheses from ordered segments
    by_conv: dict[str, dict] = {}
    seg_by_conv: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_conv[r["conv_id"]] = r
        seg_by_conv[r["conv_id"]].append(r["segment"])

    out: list[dict] = []
    for conv_id, meta in by_conv.items():
        segs = sorted(seg_by_conv[conv_id], key=lambda s: s["index"])
        pieces, lat, adur, missing = [], 0.0, 0.0, 0
        for s in segs:
            h = hyps.get(s["path"])
            if not h or not h["ok"]:
                missing += 1
                continue
            pieces.append(h["text"])
            lat += h["latency_s"]
            adur += h["audio_s"]
        hyp_text = " ".join(p for p in pieces if p)
        sc: Score = score(
            meta["transcription_tagged"], hyp_text,
            cmi_gold=meta.get("cmi_gold"), switch_gold=meta.get("switch_gold"),
        )
        d = sc.as_dict()
        d.update(
            conv_id=conv_id, language=meta["language"], in_family=meta["in_family"],
            diagnosis=meta.get("diagnosis"), cmi_gold=meta.get("cmi_gold"),
            n_segments=len(segs), segments_missing=missing,
            latency_s=round(lat, 1), audio_s=round(adur, 1),
            rtf=round(lat / adur, 3) if adur else None,
            hypothesis=hyp_text,
        )
        out.append(d)

    (RESULTS_DIR / f"scores_{model_id}.jsonl").write_text(
        "".join(json.dumps(d, ensure_ascii=False) + "\n" for d in out)
    )
    return out


def summarise(all_scores: dict[str, list[dict]]) -> dict:
    summary: dict = {"models": {}}
    for model_id, scores in all_scores.items():
        objs = [Score(**{k: v for k, v in s.items() if k in Score.__annotations__}) for s in scores]
        overall = aggregate(objs)
        audio_min = sum(s["audio_s"] for s in scores) / 60
        lat_min = sum(s["latency_s"] for s in scores) / 60
        ppm = PRICE_PER_MIN.get(model_id)
        by_lang = {}
        for lang in sorted({s["language"] for s in scores}):
            grp = [objs[i] for i, s in enumerate(scores) if s["language"] == lang]
            by_lang[lang] = aggregate(grp)
        # CMI-bucketed WER (gold CMI: low<15, mid 15-30, high>=30)
        buckets = {"low": [], "mid": [], "high": []}
        for i, s in enumerate(scores):
            c = s.get("cmi_gold") or 0
            buckets["low" if c < 15 else "mid" if c < 30 else "high"].append(objs[i])
        by_cmi = {k: aggregate(v) for k, v in buckets.items() if v}
        summary["models"][model_id] = {
            "overall": overall,
            "by_language": by_lang,
            "by_cmi_bucket": by_cmi,
            "audio_minutes": round(audio_min, 1),
            "latency_minutes": round(lat_min, 1),
            "rtf": round(lat_min / audio_min, 3) if audio_min else None,
            "usd_per_audio_min": ppm,
            "run_cost_usd": round(ppm * audio_min, 2) if ppm else None,
        }
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=None)
    ap.add_argument("--limit", type=int, default=None, help="max segments per model (smoke test)")
    ap.add_argument("--score-only", action="store_true")
    args = ap.parse_args()

    rows = _load_manifest()
    models = args.models or default_models()
    convs = len({r["conv_id"] for r in rows})
    audio_s = sum({r["conv_id"]: r["duration_s"] for r in rows}.values())
    print(f"frozen subset: {convs} conversations / {len(rows)} segments / {audio_s/60:.1f} min")
    print(f"models: {', '.join(models)}\n")

    all_scores: dict[str, list[dict]] = {}
    for model_id in models:
        print(f"== {model_id} ==")
        t0 = time.perf_counter()
        if not args.score_only:
            hyps = transcribe_all(model_id, rows, limit=args.limit)
        else:
            hyps = _load_hyps(model_id)
        all_scores[model_id] = score_model(model_id, rows, hyps)
        el = aggregate([Score(**{k: v for k, v in s.items() if k in Score.__annotations__})
                        for s in all_scores[model_id]])
        print(f"  WER {el.get('wer', 0):.3f} · CER {el.get('cer', 0):.3f} · "
              f"keyterm-recall {el.get('keyterm_recall') or 0:.3f} · "
              f"{time.perf_counter() - t0:.0f}s\n")

    summary = summarise(all_scores)
    (RESULTS_DIR / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    (RESULTS_DIR / "run_meta.json").write_text(json.dumps({
        "ran_at": datetime.now(UTC).isoformat(),
        "models": models,
        "n_conversations": convs,
        "n_segments": len(rows),
        "audio_minutes": round(audio_s / 60, 1),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "dataset": "intronhealth/AfriSwitchCare (test split)",
        "limit": args.limit,
    }, indent=2))
    print(f"wrote {RESULTS_DIR/'summary.json'}")
    print("next: python -m benchmark.report")
    return 0


if __name__ == "__main__":
    sys.exit(main())
