"""
Audio helpers: decode a HuggingFace ``Audio`` cell to a mono 16 kHz WAV on
disk, and cut a WAV into fixed windows.

No librosa / numba here — that dependency chain does not build on this
machine. ``datasets`` already resamples to 16 kHz when the feature is cast
with ``Audio(sampling_rate=16000)``, so all we need is a plain WAV writer
and a slicer, both on top of numpy + the stdlib ``wave`` module.
"""

from __future__ import annotations

import io
import wave
from pathlib import Path

import numpy as np

from benchmark.config import SEGMENT_SECONDS, TARGET_SR


def decode_audio_bytes(raw: bytes) -> tuple[np.ndarray, int]:
    """Decode an encoded audio blob (wav / flac / mp3 / ogg / m4a / opus) to
    mono float32 + sample rate. soundfile first, PyAV as the fallback."""
    try:
        import soundfile as sf

        x, sr = sf.read(io.BytesIO(raw), dtype="float32", always_2d=False)
        if x.ndim > 1:
            x = x.mean(axis=1)
        return np.asarray(x, dtype=np.float32), int(sr)
    except Exception:
        pass

    import av

    with av.open(io.BytesIO(raw)) as container:
        stream = container.streams.audio[0]
        sr = stream.codec_context.sample_rate
        chunks = []
        resampler = av.audio.resampler.AudioResampler(format="s16", layout="mono", rate=sr)
        for frame in container.decode(stream):
            for rframe in resampler.resample(frame):
                chunks.append(rframe.to_ndarray().reshape(-1))
    if not chunks:
        return np.zeros(0, dtype=np.float32), sr
    pcm = np.concatenate(chunks).astype(np.float32) / 32768.0
    return pcm, int(sr)


def _to_pcm16(samples: np.ndarray) -> bytes:
    x = np.asarray(samples, dtype=np.float32)
    if x.ndim > 1:                       # stereo -> mono
        x = x.mean(axis=1)
    x = np.clip(x, -1.0, 1.0)
    return (x * 32767.0).astype("<i2").tobytes()


def write_wav(path: Path, samples: np.ndarray, sr: int = TARGET_SR) -> float:
    """Write float samples [-1, 1] as 16-bit mono WAV. Returns duration (s)."""
    pcm = _to_pcm16(samples)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm)
    return len(pcm) / 2 / sr


def read_wav(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as w:
        sr = w.getframerate()
        n = w.getnframes()
        raw = w.readframes(n)
        ch = w.getnchannels()
    x = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    return x, sr


def resample_linear(x: np.ndarray, sr_in: int, sr_out: int = TARGET_SR) -> np.ndarray:
    if sr_in == sr_out:
        return x
    n_out = int(round(len(x) * sr_out / sr_in))
    return np.interp(
        np.linspace(0.0, 1.0, n_out, endpoint=False),
        np.linspace(0.0, 1.0, len(x), endpoint=False),
        x,
    ).astype(np.float32)


def segment_wav(src: Path, out_dir: Path, *, seconds: int = SEGMENT_SECONDS) -> list[dict]:
    """Cut `src` into <=`seconds` windows. Returns [{path, start, end, dur}]."""
    x, sr = read_wav(src)
    win = seconds * sr
    out_dir.mkdir(parents=True, exist_ok=True)
    parts: list[dict] = []
    for i, off in enumerate(range(0, len(x), win)):
        chunk = x[off:off + win]
        if len(chunk) < sr * 0.4:        # ignore a <0.4 s tail
            break
        p = out_dir / f"{src.stem}__seg{i:02d}.wav"
        dur = write_wav(p, chunk, sr)
        parts.append({
            "path": str(p), "index": i,
            "start": round(off / sr, 2), "end": round(off / sr + dur, 2),
            "dur": round(dur, 2),
        })
    return parts
