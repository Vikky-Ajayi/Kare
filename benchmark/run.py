"""
Run the ASR models over the frozen subset and score them.

    python -m benchmark.run                      # every model we have keys for
    python -m benchmark.run --models sahara groq-whisper-v3
    python -m benchmark.run --limit 4            # smoke test: 4 segments/model
    python -m benchmark.run --corpus switch      # the AfriSwitch generalisation check

`--corpus care` (default) is AfriSwitchCare, the clinical primary benchmark.
`--corpus switch` is AfriSwitch, a broader non-clinical set used to check
whether a model's edge on the clinical script holds on ordinary speech (see
`benchmark/subset_switch.py`). They write to separate results/report dirs
and never share a manifest.

Outputs (all committed, all reproducible; `switch` writes to results_switch/):
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

from benchmark.config import (
    MANIFEST,
    MODELS,
    PRICE_PER_MIN,
    RESULTS_DIR,
    SWITCH_MANIFEST,
    SWITCH_RESULTS_DIR,
    default_models,
)
from benchmark.metrics import Score, aggregate, score

CORPORA = {
    "care": {"manifest": MANIFEST, "results_dir": RESULTS_DIR,
              "dataset": "intronhealth/AfriSwitchCare (test split)"},
    "switch": {"manifest": SWITCH_MANIFEST, "results_dir": SWITCH_RESULTS_DIR,
               "dataset": "intronhealth/AfriSwitch (test split)"},
}


def _load_manifest(manifest: Path) -> list[dict]:
    if not manifest.exists():
        sys.exit(f"no {manifest.name} — run `python -m benchmark.subset"
                  f"{'_switch' if manifest.name != 'frozen_manifest.jsonl' else ''}` first")
    return [json.loads(ln) for ln in manifest.read_text().splitlines() if ln.strip()]


def _hyp_path(model_id: str, results_dir: Path) -> Path:
    return results_dir / f"hyp_{model_id}.jsonl"


def _load_hyps(model_id: str, results_dir: Path, *, keep_failed: bool = True) -> dict[str, dict]:
    p = _hyp_path(model_id, results_dir)
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
                   results_dir: Path | None = None, retry_failed: bool = True) -> dict[str, dict]:
    from benchmark.models import load

    if results_dir is None:
        results_dir = RESULTS_DIR   # read fresh, not frozen at def-time — monkeypatch-safe
    cached = _load_hyps(model_id, results_dir)
    if retry_failed:
        failed = {k for k, v in cached.items() if not v.get("ok")}
        if failed:
            done = {k: v for k, v in cached.items() if k not in failed}
            _hyp_path(model_id, results_dir).write_text(
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
    fh = _hyp_path(model_id, results_dir).open("a")
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


def score_model(model_id: str, rows: list[dict], hyps: dict[str, dict],
                results_dir: Path | None = None) -> list[dict]:
    if results_dir is None:
        results_dir = RESULTS_DIR   # read fresh, not frozen at def-time — monkeypatch-safe
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

    (results_dir / f"scores_{model_id}.jsonl").write_text(
        "".join(json.dumps(d, ensure_ascii=False) + "\n" for d in out)
    )
    return out


def summarise(all_scores: dict[str, list[dict]], hyps: dict[str, dict[str, dict]],
              *, seg_total: int = 0, seg_totals: dict[str, int] | None = None) -> dict:
    """`seg_totals` (per-model) takes precedence over the flat `seg_total` —
    a model with a restricted `languages` set (e.g. NCAIR/N-ATLaS) is scored
    against only the segments in its own supported languages, not the full
    manifest, so it isn't marked incomplete for languages it was never meant
    to attempt."""
    seg_totals = seg_totals or {}
    summary: dict = {"models": {}}
    for model_id, scores in all_scores.items():
        objs = [Score(**{k: v for k, v in s.items() if k in Score.__annotations__}) for s in scores]
        overall = aggregate(objs)
        seg_hyps = hyps.get(model_id, {})
        total = seg_totals.get(model_id) or seg_total or len(seg_hyps)
        seg_ok = sum(1 for h in seg_hyps.values() if h.get("ok"))
        # a model that couldn't transcribe most of the *manifest* isn't a real
        # result — the report shows it separately and does not rank it.
        complete = total > 0 and seg_ok / total >= 0.8
        total_for_report = total
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
            "segments_ok": seg_ok,
            "segments_total": total_for_report,
            "complete": complete,
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
    ap.add_argument("--corpus", choices=sorted(CORPORA), default="care",
                    help="'care' = AfriSwitchCare (clinical, primary); "
                         "'switch' = AfriSwitch (general-domain, generalisation check)")
    args = ap.parse_args()

    corpus = CORPORA[args.corpus]
    manifest, results_dir = corpus["manifest"], corpus["results_dir"]

    rows = _load_manifest(manifest)
    models = args.models or default_models()
    convs = len({r["conv_id"] for r in rows})
    audio_s = sum({r["conv_id"]: r["duration_s"] for r in rows}.values())
    print(f"[{args.corpus}] frozen subset: {convs} conversations / {len(rows)} segments / "
          f"{audio_s/60:.1f} min")
    print(f"models: {', '.join(models)}\n")

    all_scores: dict[str, list[dict]] = {}
    all_hyps: dict[str, dict[str, dict]] = {}
    seg_totals: dict[str, int] = {}
    for model_id in models:
        langs = MODELS.get(model_id, {}).get("languages")
        model_rows = rows if not langs else [r for r in rows if r["language"] in langs]
        seg_totals[model_id] = len(model_rows)
        scope_note = "" if not langs else f"  ({', '.join(langs)} only)"
        print(f"== {model_id} =={scope_note}")
        t0 = time.perf_counter()
        if not args.score_only:
            hyps = transcribe_all(model_id, model_rows, limit=args.limit, results_dir=results_dir)
        else:
            hyps = _load_hyps(model_id, results_dir)
            if langs:
                wanted = {r["segment"]["path"] for r in model_rows}
                hyps = {k: v for k, v in hyps.items() if k in wanted}
        all_hyps[model_id] = hyps
        all_scores[model_id] = score_model(model_id, model_rows, hyps, results_dir=results_dir)
        ok = sum(1 for h in hyps.values() if h.get("ok"))
        el = aggregate([Score(**{k: v for k, v in s.items() if k in Score.__annotations__})
                        for s in all_scores[model_id]])
        print(f"  {ok}/{len(hyps)} segments · WER {el.get('wer', 0):.3f} · "
              f"CER {el.get('cer', 0):.3f} · "
              f"keyterm-recall {el.get('keyterm_recall') or 0:.3f} · "
              f"{time.perf_counter() - t0:.0f}s\n")

    summary = summarise(all_scores, all_hyps, seg_totals=seg_totals)
    (results_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    (results_dir / "run_meta.json").write_text(json.dumps({
        "ran_at": datetime.now(UTC).isoformat(),
        "corpus": args.corpus,
        "models": models,
        "n_conversations": convs,
        "n_segments": len(rows),
        "audio_minutes": round(audio_s / 60, 1),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "dataset": corpus["dataset"],
        "limit": args.limit,
    }, indent=2))
    print(f"wrote {results_dir/'summary.json'}")
    print(f"next: python -m benchmark.report{'_switch' if args.corpus == 'switch' else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
