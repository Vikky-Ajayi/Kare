"""
Download the Intron code-switch benchmark datasets to benchmark/data/.

  python -m benchmark.download_data                 # AfriSwitchCare (medical, ~9h)
  python -m benchmark.download_data --afriswitch    # + a slice of AfriSwitch

AfriSwitchCare is per-language configs: amharic, french, hausa, kinyarwanda,
pidgin, swahili, igbo, yoruba. We keep the four that map to Kare's languages
plus swahili as an out-of-family control.
"""

from __future__ import annotations

import argparse
import os

from datasets import load_dataset

os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "0")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

CARE_LANGS = ["yoruba", "hausa", "igbo", "pidgin", "swahili"]


GATE_HINT = (
    "\n  This dataset is GATED. Sign in at huggingface.co, open\n"
    "  https://huggingface.co/datasets/{repo}\n"
    "  and click 'Agree and access repository'. Then re-run with HF_TOKEN set.\n"
)


def download_care() -> None:
    from datasets.exceptions import DatasetNotFoundError

    token = os.getenv("HF_TOKEN") or None
    for lang in CARE_LANGS:
        print(f"[AfriSwitchCare] {lang} ...", flush=True)
        try:
            ds = load_dataset(
                "intronhealth/AfriSwitchCare",
                name=lang,
                token=token,
                cache_dir=os.path.join(DATA_DIR, ".hf_cache"),
            )
        except DatasetNotFoundError:
            print(GATE_HINT.format(repo="intronhealth/AfriSwitchCare"))
            raise SystemExit(2) from None
        split = "test" if "test" in ds else list(ds.keys())[0]
        out = os.path.join(DATA_DIR, "afriswitchcare", lang)
        ds[split].save_to_disk(out)
        print(f"  -> {len(ds[split])} rows saved to {out}", flush=True)


def download_afriswitch(max_rows: int = 1200) -> None:
    token = os.getenv("HF_TOKEN") or None
    print(f"[AfriSwitch] streaming first {max_rows} rows ...", flush=True)
    ds = load_dataset("intronhealth/AfriSwitch", token=token, split="test", streaming=True)
    rows = []
    for i, row in enumerate(ds):
        if i >= max_rows:
            break
        rows.append(row)
    from datasets import Dataset
    out = os.path.join(DATA_DIR, "afriswitch", "sample")
    Dataset.from_list(rows).save_to_disk(out)
    print(f"  -> {len(rows)} rows saved to {out}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--afriswitch", action="store_true")
    args = ap.parse_args()
    download_care()
    if args.afriswitch:
        download_afriswitch()
    print("done.")
