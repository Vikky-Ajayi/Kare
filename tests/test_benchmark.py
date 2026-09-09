"""
Benchmark harness unit tests — no network, no models.

Covers the parts that must not silently drift: text normalisation, the
WER/alignment maths, the code-mixing metrics, WAV round-tripping and fixed
-window segmentation, and one full offline pipeline pass
(parquet -> subset -> a fake adapter -> score -> summary) so run.py and
report.py stay wired together.
"""

from __future__ import annotations

import io
import json

import numpy as np
import pytest

from benchmark import metrics, normalize
from benchmark.audio import decode_audio_bytes, read_wav, segment_wav, write_wav


# ── normalisation ────────────────────────────────────────────────────────
def test_normalize_strips_tags_speakers_punct():
    raw = "[Speaker 1] The doctor said my [[EN]]blood pressure[[/EN]] dey high!!"
    assert normalize.normalize(raw) == "the doctor said my blood pressure dey high"


def test_normalize_strict_spells_numbers_and_variants():
    assert "two" in normalize.normalize_strict("take 2 tablets").split()
    assert normalize.normalize_strict("my BP is high") == "my blood pressure is high"


# ── WER / alignment ──────────────────────────────────────────────────────
def test_perfect_transcription_is_zero_wer():
    ref = "Likita ina jin ciwo a kirji da [[EN]]high blood pressure[[/EN]]"
    hyp = "likita ina jin ciwo a kirji da high blood pressure"
    s = metrics.score(ref, hyp)
    assert s.wer == 0.0
    assert s.cer == 0.0
    assert s.keyterm_recall == 1.0            # "blood", "pressure"


def test_wer_counts_sub_ins_del():
    s = metrics.score("one two three four five", "one two threex four six")
    # sub three->threex, sub five->six  => 2 / 5
    assert round(s.wer, 3) == 0.4
    assert s.sub == 2 and s.ins == 0 and s.dele == 0

    s2 = metrics.score("one two three four five", "one two three four")
    assert s2.dele == 1 and round(s2.wer, 2) == 0.2


def test_missing_medical_term_drops_recall():
    ref = "she has [[EN]]asthma[[/EN]] and needs [[EN]]salbutamol[[/EN]]"
    hyp = "she has and needs"
    s = metrics.score(ref, hyp)
    assert s.keyterm_recall == 0.0
    assert s.keyterm_n == 2


# ── code-mixing metrics ──────────────────────────────────────────────────
def test_cmi_zero_for_monolingual():
    assert metrics.cmi([0, 0, 0, 0]) == 0.0
    assert metrics.cmi([1, 1, 1]) == 0.0


def test_cmi_and_switch_points_from_tags():
    tagged = "ina jin [[EN]]fever[[/EN]] da [[EN]]headache[[/EN]] tun jiya"
    # labels: 0 0 1 0 1 0 0  -> 2 english of 7, 4 switches
    assert metrics.switch_points_from_tags(tagged) == 4
    assert 0 < metrics.cmi_from_tags(tagged) < 50


def test_same_estimator_both_sides_for_cmi_error():
    ref = "the patient has [[EN]]high blood pressure[[/EN]] since [[EN]]yesterday[[/EN]]"
    s = metrics.score(ref, "the patient has high blood pressure since yesterday")
    # identical words on both sides -> dictionary tagger agrees -> ~0 error
    assert s.cmi_abs_err < 1e-6
    assert s.switch_count_err == 0


# ── audio ────────────────────────────────────────────────────────────────
def _flac_bytes(seconds: float, sr: int = 16000) -> bytes:
    import soundfile as sf

    x = (np.sin(np.linspace(0, 200, int(seconds * sr))) * 0.1).astype(np.float32)
    buf = io.BytesIO()
    sf.write(buf, x, sr, format="FLAC")
    return buf.getvalue()


def test_decode_and_wav_roundtrip(tmp_path):
    x, sr = decode_audio_bytes(_flac_bytes(1.5))
    assert sr == 16000
    p = tmp_path / "a.wav"
    dur = write_wav(p, x, sr)
    assert abs(dur - 1.5) < 0.05
    y, sr2 = read_wav(p)
    assert sr2 == 16000 and abs(len(y) - len(x)) <= 1


def test_segmentation_windows(tmp_path):
    x, sr = decode_audio_bytes(_flac_bytes(5.0))
    src = tmp_path / "long.wav"
    write_wav(src, x, sr)
    segs = segment_wav(src, tmp_path / "seg", seconds=2)
    assert [s["index"] for s in segs] == [0, 1, 2]
    assert segs[0]["dur"] == pytest.approx(2.0, abs=0.05)
    assert segs[-1]["dur"] == pytest.approx(1.0, abs=0.05)


# ── full offline pipeline ────────────────────────────────────────────────
def test_pipeline_end_to_end(tmp_path, monkeypatch):
    import pyarrow as pa
    import pyarrow.parquet as pq

    from benchmark import config, subset

    # a 1-language, 3-conversation parquet
    langdir = tmp_path / "afriswitchcare" / "data" / "hausa"
    langdir.mkdir(parents=True)
    tbl = pa.table({
        "audio": [{"bytes": _flac_bytes(3), "path": f"{i}.flac"} for i in range(3)],
        "language": ["hausa"] * 3,
        "diagnosis": ["Asthma", "Hypertension", "Stroke"],
        "transcription": [
            "likita ina jin ciwo a kirji", "ina bukatar insulin sau biyu",
            "ba ni da lafiya tun da safe",
        ],
        "transcription_tagged": [
            "likita ina jin ciwo a [[EN]]chest[[/EN]]",
            "ina bukatar [[EN]]insulin[[/EN]] sau biyu",
            "ba ni da lafiya tun da safe",
        ],
        "num_turns": [2, 2, 2], "cmi": [10.0, 20.0, 0.0],
        "num_switch_points": [1, 2, 0], "duration": [3.0, 3.0, 3.0],
    })
    pq.write_table(tbl, langdir / "test-00000-of-00001.parquet")

    monkeypatch.setattr(config, "BENCH_LANGS", ["hausa"])
    monkeypatch.setattr(config, "CONVOS_PER_LANG", 2)
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "AUDIO_DIR", tmp_path / "audio")
    monkeypatch.setattr(config, "SEG_DIR", tmp_path / "seg")
    monkeypatch.setattr(config, "MANIFEST", tmp_path / "frozen_manifest.jsonl")
    monkeypatch.setattr(config, "RESULTS_DIR", tmp_path / "results")
    (tmp_path / "results").mkdir()
    for mod in (subset,):
        monkeypatch.setattr(mod, "BENCH_LANGS", ["hausa"], raising=False)
        monkeypatch.setattr(mod, "CONVOS_PER_LANG", 2, raising=False)
        monkeypatch.setattr(mod, "AUDIO_DIR", tmp_path / "audio", raising=False)
        monkeypatch.setattr(mod, "SEG_DIR", tmp_path / "seg", raising=False)
        monkeypatch.setattr(mod, "MANIFEST", tmp_path / "frozen_manifest.jsonl", raising=False)
        monkeypatch.setattr(mod, "PARQUET_DIR", tmp_path / "afriswitchcare" / "data", raising=False)

    assert subset.build() == 0
    lines = (tmp_path / "frozen_manifest.jsonl").read_text().splitlines()
    assert len(lines) == 2                     # 2 conversations, 1 segment each (3 s < 110 s)
    row = json.loads(lines[0])
    assert row["language"] == "hausa" and row["segment"]["dur"] == pytest.approx(3.0, abs=0.1)

    # a fake adapter that "hears" the reference perfectly
    from benchmark import run

    manifest_rows = [json.loads(x) for x in lines]
    hyps = {
        r["segment"]["path"]: {
            "seg_path": r["segment"]["path"], "conv_id": r["conv_id"],
            "ok": True, "text": normalize.normalize(r["transcription_tagged"]),
            "latency_s": 0.5, "audio_s": r["segment"]["dur"], "error": None,
        }
        for r in manifest_rows
    }
    monkeypatch.setattr(run, "RESULTS_DIR", tmp_path / "results")
    scored = run.score_model("fake", manifest_rows, hyps)
    assert len(scored) == 2
    assert all(s["wer"] == 0.0 for s in scored)
    summary = run.summarise({"fake": scored}, {"fake": hyps}, seg_total=len(manifest_rows))
    assert summary["models"]["fake"]["overall"]["wer"] == 0.0
    assert summary["models"]["fake"]["complete"] is True
    assert summary["models"]["fake"]["segments_ok"] == 2

    # a model that only managed a fraction of the manifest is held out
    partial = run.summarise({"fake": scored}, {"fake": dict(list(hyps.items())[:1])},
                            seg_total=10)
    assert partial["models"]["fake"]["complete"] is False
