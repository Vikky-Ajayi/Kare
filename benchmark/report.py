"""
Turn results/ into report/REPORT.md + report/charts/*.png + error samples.

    python -m benchmark.report

Every number in the report is read straight from results/summary.json and
results/scores_*.jsonl, so `python -m benchmark.run && python -m benchmark.report`
regenerates it end to end.
"""

from __future__ import annotations

import json
import sys

from benchmark.config import MANIFEST, MODELS, REPORT_DIR, RESULTS_DIR
from benchmark.normalize import normalize

CHARTS = REPORT_DIR / "charts"
CHARTS.mkdir(parents=True, exist_ok=True)

LANG_ORDER = ["yoruba", "hausa", "igbo", "pidgin", "swahili"]


def _load() -> tuple[dict, dict[str, list[dict]]]:
    sp = RESULTS_DIR / "summary.json"
    if not sp.exists():
        sys.exit("no results/summary.json — run `python -m benchmark.run` first")
    summary = json.loads(sp.read_text())
    scores = {}
    for mid in summary["models"]:
        fp = RESULTS_DIR / f"scores_{mid}.jsonl"
        scores[mid] = [json.loads(ln) for ln in fp.read_text().splitlines() if ln.strip()]
    return summary, scores


def _label(mid: str) -> str:
    return MODELS.get(mid, {}).get("label", mid)


def _pct(x: float | None, nd: int = 1) -> str:
    return "—" if x is None else f"{x * 100:.{nd}f}"


def _fnum(x: float | None, nd: int = 1) -> str:
    return "—" if x is None else f"{x:.{nd}f}"


# ── charts ───────────────────────────────────────────────────────────────
def _mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"figure.dpi": 130, "font.size": 9, "axes.grid": True,
                         "grid.alpha": 0.25, "axes.axisbelow": True})
    return plt


def chart_wer_by_language(summary: dict) -> None:
    plt = _mpl()
    models = list(summary["models"])
    fig, ax = plt.subplots(figsize=(8, 4))
    w = 0.8 / len(models)
    for k, mid in enumerate(models):
        bl = summary["models"][mid]["by_language"]
        ys = [bl.get(lang, {}).get("wer", 0) * 100 for lang in LANG_ORDER]
        xs = [i + k * w for i in range(len(LANG_ORDER))]
        ax.bar(xs, ys, width=w, label=_label(mid))
    ax.set_xticks([i + 0.4 - w / 2 for i in range(len(LANG_ORDER))])
    ax.set_xticklabels([lang.title() for lang in LANG_ORDER])
    ax.set_ylabel("WER (%)")
    ax.set_title("Word error rate by matrix language  ·  Swahili = out-of-family control")
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(CHARTS / "wer_by_language.png")
    plt.close(fig)


def chart_wer_by_cmi(summary: dict) -> None:
    plt = _mpl()
    fig, ax = plt.subplots(figsize=(7, 4))
    order = ["low", "mid", "high"]
    for mid in summary["models"]:
        bc = summary["models"][mid]["by_cmi_bucket"]
        ys = [bc.get(b, {}).get("wer", None) for b in order]
        xs = [i for i, y in enumerate(ys) if y is not None]
        ax.plot(xs, [ys[i] * 100 for i in xs], "o-", label=_label(mid))
    ax.set_xticks(range(3))
    ax.set_xticklabels(["low\n(CMI<15)", "mid\n(15–30)", "high\n(CMI≥30)"])
    ax.set_ylabel("WER (%)")
    ax.set_title("Does accuracy fall as code-mixing rises?")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(CHARTS / "wer_by_cmi.png")
    plt.close(fig)


def chart_cost_accuracy(summary: dict) -> None:
    plt = _mpl()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for mid in summary["models"]:
        m = summary["models"][mid]
        wer = m["overall"]["wer"] * 100
        ppm = m.get("usd_per_audio_min")
        x = ppm if ppm else 0.0002            # place "free"/"n/p" at the left edge
        ax.scatter(x, wer, s=60)
        ax.annotate(_label(mid), (x, wer), fontsize=7, xytext=(4, 4),
                    textcoords="offset points")
    ax.set_xscale("log")
    ax.set_xlabel("USD per audio-minute (log; 'free'/'not-published' pinned left)")
    ax.set_ylabel("WER (%)  ·  lower is better")
    ax.set_title("Accuracy vs cost")
    fig.tight_layout()
    fig.savefig(CHARTS / "cost_accuracy.png")
    plt.close(fig)


def chart_keyterm_recall(summary: dict) -> None:
    plt = _mpl()
    fig, ax = plt.subplots(figsize=(7, 4))
    mids = list(summary["models"])
    kt = [(summary["models"][m]["overall"].get("keyterm_recall") or 0) * 100 for m in mids]
    nr = [(summary["models"][m]["overall"].get("number_recall") or 0) * 100 for m in mids]
    x = range(len(mids))
    ax.bar([i - 0.2 for i in x], kt, width=0.4, label="medical term recall")
    ax.bar([i + 0.2 for i in x], nr, width=0.4, label="number / dosage recall")
    ax.set_xticks(list(x))
    ax.set_xticklabels([_label(m) for m in mids], rotation=20, ha="right", fontsize=7)
    ax.set_ylabel("recall (%)")
    ax.set_title("Clinically salient tokens preserved")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(CHARTS / "keyterm_recall.png")
    plt.close(fig)


# ── tables ───────────────────────────────────────────────────────────────
def table_overall(summary: dict) -> str:
    rows = [
        "| Model | WER | WER (norm) | CER | Med-term recall | Number recall | CMI err | Switch err | RTF | $/audio-min |",
        "|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|",
    ]
    ranked = sorted(summary["models"].items(), key=lambda kv: kv[1]["overall"]["wer"])
    for mid, m in ranked:
        o = m["overall"]
        ppm = m.get("usd_per_audio_min")
        rows.append(
            f"| {_label(mid)} | {_pct(o['wer'])} | {_pct(o['wer_strict'])} | {_pct(o['cer'])} "
            f"| {_pct(o.get('keyterm_recall'))} | {_pct(o.get('number_recall'))} "
            f"| {_fnum(o.get('cmi_abs_err'))} | {_fnum(o.get('switch_count_err'), 2)} "
            f"| {_fnum(m.get('rtf'), 2)} | {'n/p' if ppm is None else f'${ppm:.4f}'} |"
        )
    return "\n".join(rows)


def table_by_language(summary: dict) -> str:
    rows = ["| Model | " + " | ".join(x.title() for x in LANG_ORDER) + " | in-family avg | Swahili Δ |",
            "|---|" + "--:|" * (len(LANG_ORDER) + 2)]
    for mid, m in sorted(summary["models"].items(), key=lambda kv: kv[1]["overall"]["wer"]):
        bl = m["by_language"]
        cells = [_pct(bl.get(x, {}).get("wer")) for x in LANG_ORDER]
        infam = [bl[x]["wer"] for x in LANG_ORDER[:-1] if x in bl]
        avg = sum(infam) / len(infam) if infam else None
        sw = bl.get("swahili", {}).get("wer")
        delta = (sw - avg) if (sw is not None and avg is not None) else None
        rows.append(f"| {_label(mid)} | " + " | ".join(cells) +
                    f" | {_pct(avg)} | {'—' if delta is None else f'{delta*100:+.1f}'} |")
    return "\n".join(rows)


def table_cmi(summary: dict) -> str:
    rows = ["| Model | low CMI (<15) | mid (15–30) | high (≥30) | high − low |",
            "|---|--:|--:|--:|--:|"]
    for mid, m in sorted(summary["models"].items(), key=lambda kv: kv[1]["overall"]["wer"]):
        bc = m["by_cmi_bucket"]
        lo, mi, hi = (bc.get(b, {}).get("wer") for b in ("low", "mid", "high"))
        d = (hi - lo) if (hi is not None and lo is not None) else None
        rows.append(f"| {_label(mid)} | {_pct(lo)} | {_pct(mi)} | {_pct(hi)} | "
                    f"{'—' if d is None else f'{d*100:+.1f}'} |")
    return "\n".join(rows)


def _manifest_refs() -> dict[str, dict]:
    refs: dict[str, dict] = {}
    for line in MANIFEST.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            refs.setdefault(r["conv_id"], r)
    return refs


def error_samples(scores: dict[str, list[dict]]) -> str:
    """One conversation per language: reference head + every model's hypothesis head."""
    refs = _manifest_refs()
    out = ["## Transcript samples\n",
           "First ~45 words of one conversation per language, all models. "
           "`[[EN]]…[[/EN]]` spans in the reference mark the human code-switch annotation "
           "(stripped in the excerpt); the English words are what a clinician needs.\n"]
    any_model = next(iter(scores))
    for lang in LANG_ORDER:
        conv = next((s for s in scores[any_model] if s["language"] == lang), None)
        if not conv:
            continue
        ref = refs.get(conv["conv_id"], {})
        out.append(f"\n### {lang.title()} — {ref.get('diagnosis') or '?'} "
                   f"(gold CMI {ref.get('cmi_gold')})\n")
        out.append(f"**Reference** · {_head(ref.get('transcription_tagged', ''), 45)}\n")
        for mid in scores:
            c = next((s for s in scores[mid] if s["conv_id"] == conv["conv_id"]), None)
            if not c:
                continue
            out.append(f"- **{_label(mid)}** (WER {c['wer'] * 100:.0f}, "
                       f"keyterm {(_safe(c.get('keyterm_recall')) * 100):.0f}) · "
                       f"{_head(c['hypothesis'], 45)}")
    return "\n".join(out)


def _safe(x) -> float:
    return 0.0 if x is None else x


def _head(text: str, n: int) -> str:
    toks = normalize(text).split()
    return " ".join(toks[:n]) + (" …" if len(toks) > n else "")


def main() -> int:
    summary, scores = _load()
    meta = json.loads((RESULTS_DIR / "run_meta.json").read_text())

    chart_wer_by_language(summary)
    chart_wer_by_cmi(summary)
    chart_cost_accuracy(summary)
    chart_keyterm_recall(summary)

    ranked = sorted(summary["models"].items(), key=lambda kv: kv[1]["overall"]["wer"])
    winner = _label(ranked[0][0])
    n_frozen = len(scores[ranked[0][0]])
    seed_note = "SMOKE RUN" if meta.get("limit") else "seed 20260915"

    md = f"""# Kare · code-switching ASR benchmark

*Generated by `python -m benchmark.report` from `results/`. Ran
{meta['ran_at'][:16].replace('T', ' ')} UTC on {meta['python']} / {meta['platform']}.*

**What this measures.** Nigerian patients do not speak one language at a time.
They say *"the doctor talk say my BP dey high"* — Yoruba/Pidgin grammar with
English clinical terms dropped in. Kare's voice layer has to get **both** the
matrix language **and** the embedded English right, because the English words
are usually the clinically load-bearing ones (drug names, "blood pressure",
"twice daily"). Standard ASR leaderboards are monolingual and miss this
entirely, so we built our own.

**Data.** {meta['n_conversations']} conversations
({meta['audio_minutes']} min) from **Intron's AfriSwitchCare** — simulated
doctor–patient consultations, English code-switched with Yoruba, Hausa, Igbo
and Nigerian Pidgin, plus **Swahili as an out-of-family control** (a language
none of Kare's users speak; it shows whether a model has learned West-African
speech or merely memorised it). The exact clips are frozen in
[`frozen_manifest.jsonl`](../frozen_manifest.jsonl) ({seed_note}).

**Verdict: {winner}** has the lowest word error rate on this set. Full picture
below — cost, latency and clinical-term recall pull in different directions.

## Headline numbers

{table_overall(summary)}

- **WER** — light normalisation (lower-case, punctuation & speaker tags removed).
- **WER (norm)** — additionally spells out digits and unifies a few spelling
  variants; the gap to plain WER is formatting, not mis-hearing.
- **Med-term / Number recall** — of the medical terms (resp. spoken numbers &
  dosages) in the reference, the fraction that survive into the transcript.
  This is the metric that matters most clinically.
- **CMI err** — absolute error in the Code-Mixing Index between reference and
  hypothesis (same English-dictionary estimator on both sides, so its bias
  cancels). **Switch err** — mean error in the count of language-switch points.
- **RTF** — real-time factor, wall-clock ÷ audio. <1 is faster than real time.

![WER by language](charts/wer_by_language.png)

## By language

{table_by_language(summary)}

*"Swahili Δ" is Swahili WER minus the mean of the four Nigerian languages. A
large positive Δ means the model leans on West-African-specific training and
generalises poorly; a small Δ means it is broadly multilingual.*

## Accuracy vs code-mixing intensity

{table_cmi(summary)}

![WER by CMI](charts/wer_by_cmi.png)

If a model's "high − low" is strongly positive, dense code-switching breaks it —
exactly the utterances Kare sees most. A flat line is what we want.

## Cost and speed

![Accuracy vs cost](charts/cost_accuracy.png)

{_cost_table(summary)}

## Clinically salient tokens

![Keyterm recall](charts/keyterm_recall.png)

A transcript can have a respectable WER and still drop the one word that
matters. Med-term and number recall isolate that: they only score tokens like
*insulin*, *39 degrees*, *twice daily*, *no fever*.

{error_samples(scores)}

## Harness notes

- **Segmentation.** Every conversation is cut into ≤110 s windows before
  transcription (Sahara's sync endpoint and Whisper's file limits both sit
  around there). The *same* slices go to every model, and hypotheses are
  concatenated back before scoring against the full reference. Boundary
  word-splits add perhaps 0.5–1 WER point uniformly across models.
- **Language hint.** Each model is given its native language code where it has
  one (`yo`, `ha`, `ig`, `sw`); Pidgin has no ISO code so Whisper models
  auto-detect and Sahara gets `pcm`.
- **Retries.** 429/5xx are retried with backoff, so rate limits slow a run
  rather than failing it. Segments are cached — a re-run only fills gaps.
- **Reproduce.** `make benchmark` (or `python -m benchmark.subset &&
  python -m benchmark.run && python -m benchmark.report`). Raw audio is not
  committed; the manifest + `HF_TOKEN` reconstructs it.

## Fairness & limitations

- AfriSwitchCare is **simulated** consultations read by voice artists, not
  real clinic audio — cleaner acoustics, less crosstalk and background noise
  than Kare will meet in the field. Absolute WERs here are a **floor**.
- {n_frozen} conversations in the frozen subset ({meta['n_segments']} segments) —
  enough to rank models, not enough for tight per-language confidence
  intervals. Treat sub-language differences under ~3 points as noise.
- The English-word detector behind the CMI / switch metrics is a dictionary
  lookup; it mislabels proper nouns and loanwords. It is applied identically
  to every model, so comparisons are fair, but the absolute CMI error has a
  systematic offset.
- Two of Kare's languages (Igbo, Hausa) have the least training data across
  every model — the benchmark makes that gap visible rather than hiding it.
"""

    (REPORT_DIR / "REPORT.md").write_text(md)
    print(f"wrote {REPORT_DIR / 'REPORT.md'}")
    print(f"charts in {CHARTS}/")
    return 0


def _cost_table(summary: dict) -> str:
    rows = ["| Model | audio min | wall-clock min | RTF | run cost | notes |",
            "|---|--:|--:|--:|--:|---|"]
    notes = {
        "sahara": "clinical model; per-minute price not published",
        "groq-whisper-v3": "free tier rate-limited; price shown is paid tier",
        "groq-whisper-v3-turbo": "fastest hosted option",
        "faster-whisper-base": "runs on a CPU laptop, no network",
        "openai-gpt4o-transcribe": "frontier closed model",
    }
    for mid, m in sorted(summary["models"].items(), key=lambda kv: kv[1]["overall"]["wer"]):
        rc = m.get("run_cost_usd")
        rows.append(f"| {_label(mid)} | {m['audio_minutes']} | {m['latency_minutes']} "
                    f"| {_fnum(m.get('rtf'), 2)} | {'—' if rc is None else f'${rc:.2f}'} "
                    f"| {notes.get(mid, '')} |")
    return "\n".join(rows)


if __name__ == "__main__":
    sys.exit(main())
