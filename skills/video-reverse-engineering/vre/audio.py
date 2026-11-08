"""Audio: onsets (SFX hits), loudness, and optional words / beats, paired with visual events.

The onset detector is numpy-only (spectral flux with an adaptive threshold) so it always runs.
Words use whisperX when installed (forced alignment), else faster-whisper word timestamps; beats use
beat_this (MIT) when installed. Anything missing is reported UNAVAILABLE, never as an empty result.
Never reuse the source's audio or voice in a deliverable: these are timings only.
"""

from __future__ import annotations

import os
import subprocess

import numpy as np

from .deps import available


def load_mono(path: str, sr: int = 22050) -> np.ndarray | None:
    cmd = ["ffmpeg", "-v", "error", "-nostdin", "-i", path, "-map", "0:a:0?", "-ac", "1", "-ar", str(sr),
           "-f", "f32le", "-"]
    proc = subprocess.run(cmd, capture_output=True, check=False)
    if proc.returncode != 0 or not proc.stdout:
        return None
    return np.frombuffer(proc.stdout, dtype=np.float32).copy()


def _db(v: float) -> float | None:
    return round(float(20 * np.log10(v)), 2) if v > 0 else None  # silence is absent, not 0 dB


def loudness(y: np.ndarray) -> dict:
    rms = float(np.sqrt(np.mean(y.astype(np.float64) ** 2))) if y.size else 0.0
    peak = float(np.max(np.abs(y))) if y.size else 0.0
    db = _db
    return {"rms_dbfs": db(rms), "sample_peak_dbfs": db(peak),
            "note": "sample peak, not true peak; use ffmpeg ebur128 for LUFS / true peak"}


def onset_envelope(y: np.ndarray, sr: int, hop: int = 256, n_fft: int = 1024) -> np.ndarray:
    if len(y) < n_fft:
        return np.zeros(0)
    count = 1 + (len(y) - n_fft) // hop
    idx = np.arange(n_fft)[None, :] + hop * np.arange(count)[:, None]
    mag = np.abs(np.fft.rfft(y[idx] * np.hanning(n_fft)[None, :], axis=1))
    logmag = np.log1p(100.0 * mag)
    flux = np.maximum(0.0, np.diff(logmag, axis=0)).sum(axis=1)
    return np.concatenate([[0.0], flux])


def onsets(y: np.ndarray, sr: int, hop: int = 256, n_fft: int = 1024, min_gap_s: float = 0.06,
           k: float = 1.5) -> list[float]:
    """Onset times in seconds. Frame i of the envelope covers samples [i*hop, i*hop + n_fft), so its time is
    the window CENTRE (i*hop + n_fft/2) / sr; stamping the window start reads every hit early."""
    env = onset_envelope(y, sr, hop, n_fft)
    if env.size == 0 or env.max() <= 0:
        return []
    win = max(3, int(0.25 * sr / hop))
    pad = np.pad(env, (win, win), mode="edge")
    local_mean = np.convolve(pad, np.ones(2 * win + 1) / (2 * win + 1), mode="same")[win:-win]
    local_std = np.sqrt(np.maximum(0.0, np.convolve(pad ** 2, np.ones(2 * win + 1) / (2 * win + 1),
                                                      mode="same")[win:-win]
                                   - local_mean ** 2))
    thresh = local_mean + k * local_std + 0.05 * env.max()
    gap = max(1, int(min_gap_s * sr / hop))
    times, last = [], -gap
    for i in range(1, len(env) - 1):
        if env[i] >= thresh[i] and env[i] >= env[i - 1] and env[i] >= env[i + 1] and i - last >= gap:
            times.append(round((i * hop + n_fft / 2) / sr, 4))
            last = i
    return times


def _device() -> str:
    """VRE_DEVICE overrides; otherwise CUDA only when torch says it is usable. faster-whisper's own 'auto'
    picks CUDA on a host without cuBLAS and crashes mid-transcription (observed 2026-11-08, Windows laptop)."""
    forced = os.environ.get("VRE_DEVICE")
    if forced in ("cpu", "cuda"):
        return forced
    try:
        return "cuda" if available("torch") and __import__("torch").cuda.is_available() else "cpu"
    except Exception:  # a broken torch install means CPU, and the reason is not needed downstream
        return "cpu"


def _guarded(stage: str, fn) -> dict:
    """An optional engine that raises is FAILED with its error, never a crash of the whole analysis and
    never an empty result that reads as 'nothing there'."""
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 - reported verbatim in the spec and REVERSE.md
        return {"status": "FAILED", "reason": f"{stage}: {type(exc).__name__}: {str(exc)[:300]}"}


def words(path: str, language: str | None = None) -> dict:
    return _guarded("words", lambda: _words(path, language))


def beats(path: str) -> dict:
    return _guarded("beats", lambda: _beats(path))


def _words(path: str, language: str | None) -> dict:
    if available("whisperx"):
        import whisperx  # type: ignore

        device = _device()
        model = whisperx.load_model("small", device, compute_type="float16" if device == "cuda" else "int8")
        audio = whisperx.load_audio(path)
        res = model.transcribe(audio, language=language)
        align, meta = whisperx.load_align_model(language_code=res["language"], device=device)
        res = whisperx.align(res["segments"], align, meta, audio, device)
        out = [{"word": w["word"], "start": w.get("start"), "end": w.get("end")} for s in res["segments"]
               for w in s.get("words", [])]
        return {"status": "OK", "engine": "whisperx", "language": res.get("language"), "words": out}
    if available("faster_whisper"):
        from faster_whisper import WhisperModel  # type: ignore

        device = _device()
        model = WhisperModel("small", device=device, compute_type="float16" if device == "cuda" else "int8")
        segs, info = model.transcribe(path, language=language, word_timestamps=True)
        out = [{"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)} for s in segs
               for w in (s.words or [])]
        return {"status": "OK", "engine": "faster-whisper", "language": info.language, "words": out}
    return {"status": "UNAVAILABLE", "reason": "install whisperx or faster-whisper", "words": None}


def _beats(path: str) -> dict:
    if not available("beat_this"):
        return {"status": "UNAVAILABLE", "reason": "pip install beat_this (MIT); never --dbn (madmom is NC)"}
    from beat_this.inference import File2Beats  # type: ignore

    beat, down = File2Beats(device=_device(), dbn=False)(path)
    return {"status": "OK", "engine": "beat_this", "beats": [round(float(b), 4) for b in beat],
            "downbeats": [round(float(d), 4) for d in down]}


def pair_with_frames(times_s: list[float], frames: list[int], fps: float, tol_frames: int = 2) -> list[dict]:
    """For each audio time, the nearest visual event frame within +-tol_frames (AV sync)."""
    out = []
    for t in times_s:
        f = t * fps
        near = min(frames, key=lambda x: abs(x - f)) if frames else None
        if near is not None and abs(near - f) <= tol_frames:
            out.append({"time_s": t, "frame": near, "offset_frames": round(f - near, 2)})
    return out
