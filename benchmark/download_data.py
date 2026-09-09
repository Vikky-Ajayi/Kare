"""
Pull the AfriSwitchCare parquet shards into the local HF cache.

    python -m benchmark.download_data                # the 5 benchmarked languages
    python -m benchmark.download_data --all          # all 9 language configs

AfriSwitchCare is gated: sign in at huggingface.co, open
https://huggingface.co/datasets/intronhealth/AfriSwitchCare and click
"Agree and access repository", then export HF_TOKEN before running.

AfriSwitch (the larger non-clinical set) is gated behind *manual* approval.
If/when you are approved, drop its parquet files under
benchmark/data/afriswitch/<lang>/ and the harness will pick them up; there
is no automated download for it here.
"""

from __future__ import annotations

import argparse
import os
import sys

from benchmark.config import BENCH_LANGS, CACHE_DIR, CARE_REPO, LANG_META


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="all 9 configs, not just the 5 benchmarked")
    args = ap.parse_args()

    from datasets import load_dataset
    from datasets.exceptions import DatasetNotFoundError

    token = os.getenv("HF_TOKEN") or None
    langs = list(LANG_META) if args.all else BENCH_LANGS
    if not token:
        print("!  HF_TOKEN not set — this will fail if you have not cached the data before.\n")

    ok = True
    for lang in langs:
        print(f"[AfriSwitchCare] {lang} ...", flush=True)
        try:
            ds = load_dataset(CARE_REPO, name=lang, split="test",
                              cache_dir=str(CACHE_DIR), token=token)
            print(f"   {len(ds)} conversations cached", flush=True)
        except DatasetNotFoundError:
            ok = False
            print(f"   GATED — approve access at https://huggingface.co/datasets/{CARE_REPO}")
        except Exception as exc:  # noqa: BLE001
            ok = False
            print(f"   failed: {exc}")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
