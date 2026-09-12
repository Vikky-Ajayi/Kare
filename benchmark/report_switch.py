"""
Turn results_switch/ into report_switch/REPORT.md — the generalisation check.

    python -m benchmark.report_switch

AfriSwitchCare (the primary report) is clinical-domain and Kare's actual use
case. AfriSwitch is the same team's broader, general-domain code-switch
corpus — no clinical script, more languages, one utterance per row instead
of a multi-turn conversation. Running both answers a question the clinical
report alone cannot: does a model's edge on the clinical set hold on
ordinary speech, or was it fitted to that domain?

This report is deliberately smaller than the primary one (one table, one
chart, one comparison) — it reuses `report.py`'s table renderers since both
corpora produce an identically-shaped `summary.json`.
"""

from __future__ import annotations

import json
import sys

from benchmark.config import SWITCH_MANIFEST, SWITCH_REPORT_DIR, SWITCH_RESULTS_DIR
from benchmark.report import (
    LANG_ORDER,
    _incomplete,
    _label,
    _pct,
    _ranked,
    language_scope_note,
    table_by_language,
    table_overall,
)

CHARTS = SWITCH_REPORT_DIR / "charts"
CHARTS.mkdir(parents=True, exist_ok=True)


def _load(results_dir):
    sp = results_dir / "summary.json"
    if not sp.exists():
        sys.exit(f"no {sp} — run `python -m benchmark.run --corpus switch` first")
    return json.loads(sp.read_text())


def chart_wer_by_language(summary: dict) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"figure.dpi": 130, "font.size": 9, "axes.grid": True,
                         "grid.alpha": 0.25, "axes.axisbelow": True})
    models = [mid for mid, _ in _ranked(summary)]
    fig, ax = plt.subplots(figsize=(8, 4))
    w = 0.8 / max(len(models), 1)
    for k, mid in enumerate(models):
        bl = summary["models"][mid]["by_language"]
        ys = [bl.get(lang, {}).get("wer", 0) * 100 for lang in LANG_ORDER]
        xs = [i + k * w for i in range(len(LANG_ORDER))]
        ax.bar(xs, ys, width=w, label=_label(mid))
    ax.set_xticks([i + 0.4 - w / 2 for i in range(len(LANG_ORDER))])
    ax.set_xticklabels([lang.title() for lang in LANG_ORDER])
    ax.set_ylabel("WER (%)")
    ax.set_title("AfriSwitch (general-domain) — WER by language")
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(CHARTS / "wer_by_language.png")
    plt.close(fig)


def table_generalisation(care: dict, switch: dict) -> str:
    """The actual point of this report: did each model's clinical-set ranking
    and error rate survive moving to ordinary, non-clinical speech?"""
    rows = ["| Model | WER · clinical (AfriSwitchCare) | WER · general (AfriSwitch) | Δ (general − clinical) |",
            "|---|--:|--:|--:|"]
    care_wer = {mid: m["overall"]["wer"] for mid, m in care["models"].items()}
    switch_wer = {mid: m["overall"]["wer"] for mid, m in switch["models"].items()
                  if switch["models"][mid].get("complete", True)}
    for mid in sorted(set(care_wer) & set(switch_wer), key=lambda m: switch_wer[m]):
        c, s = care_wer[mid], switch_wer[mid]
        rows.append(f"| {_label(mid)} | {_pct(c)} | {_pct(s)} | {(s - c) * 100:+.1f} |")
    only_switch = set(switch_wer) - set(care_wer)
    for mid in sorted(only_switch, key=lambda m: switch_wer[m]):
        rows.append(f"| {_label(mid)} | — | {_pct(switch_wer[mid])} | — |")
    return "\n".join(rows)


def main() -> int:
    switch = _load(SWITCH_RESULTS_DIR)
    care_path = SWITCH_RESULTS_DIR.parent / "results" / "summary.json"
    care = json.loads(care_path.read_text()) if care_path.exists() else None

    chart_wer_by_language(switch)
    n_conv = len({json.loads(ln)["conv_id"] for ln in SWITCH_MANIFEST.read_text().splitlines()
                  if ln.strip()}) if SWITCH_MANIFEST.exists() else "?"

    parts = [
        "# Kare · generalisation check — AfriSwitch (non-clinical)\n",
        "AfriSwitchCare is clinical-domain and is the primary benchmark "
        "(`../report/REPORT.md`). This is the same 4 STT models run on "
        f"**AfriSwitch** — {n_conv} short, general-domain utterances across "
        "the same 5 languages, no clinical script, sampled from a separate "
        "manual-gated corpus. It answers one question the clinical report "
        "can't: **does a model's edge on scripted clinical consultations "
        "hold on ordinary speech, or was it specific to that domain?**\n",
        "## Headline numbers (AfriSwitch)\n",
        table_overall(switch),
        language_scope_note(switch),
        "\n![WER by language](charts/wer_by_language.png)\n",
        "## By language\n",
        table_by_language(switch),
    ]

    incomplete = _incomplete(switch)
    if incomplete:
        parts.append(
            "\n**Incomplete runs (held out of the tables above):** "
            + ", ".join(f"{_label(mid)} ({m['segments_ok']}/{m['segments_total']})"
                        for mid, m in incomplete) + ".\n"
        )
    if not _ranked(switch):
        parts.append("\n*No model has a complete run on this corpus yet — "
                      "run `make bench-run-switch` without `--limit`.*\n")

    if care:
        parts += [
            "\n## Generalisation: clinical vs. general-domain\n",
            "A small or negative Δ means the model's clinical-set accuracy "
            "was not a fluke of that script — it holds on ordinary speech "
            "too. A large positive Δ means the model (or the harness) was "
            "in some way fitted to the clinical domain.\n",
            table_generalisation(care, switch),
        ]
    else:
        parts.append("\n*(Run the primary benchmark too — `make bench-run` — "
                     "to get the clinical-vs-general comparison table.)*\n")

    parts.append(
        "\n## Caveats\n"
        "- AfriSwitch utterances are much shorter than AfriSwitchCare's "
        "conversations (seconds, not minutes) and are not health-domain, so "
        "medical-term/number recall is less meaningful here — read the WER "
        "columns as the primary signal.\n"
        "- Only shard 0 of each language's parquet was fetched (thousands of "
        "utterances) rather than the full corpus; the frozen subset is a "
        "stratified sample of that shard — see `frozen_manifest_switch.jsonl`.\n"
        "- Reproduce: `make bench-data-switch bench-subset-switch "
        "bench-run-switch bench-report-switch` (needs manual-approved access "
        "to `intronhealth/AfriSwitch` + `HF_TOKEN`).\n"
    )

    (SWITCH_REPORT_DIR / "REPORT.md").write_text("\n".join(parts))
    print(f"wrote {SWITCH_REPORT_DIR / 'REPORT.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
