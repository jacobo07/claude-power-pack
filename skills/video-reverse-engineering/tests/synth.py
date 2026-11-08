"""Synthetic reference clip with KNOWN ground truth, stored landscape with rotation metadata (like a phone reel).

Ground truth (display 108x192 portrait, 30 fps, 90 frames):
  shot A  frames 0-29   dark navy, a yellow square moving x 8 -> 80 over frames 4..22 with easeOutCubic
  shot B  frames 30-59  light paper, a fixed dark bar
  black   frames 60-63  (fade through black)
  shot C  frames 64-89  teal
  a red 8x8 marker at the display top-left on every frame (orientation check)
  audio clicks at 0.5 s, 1.0 s (cut at frame 30) and 2.0 s (frame 60)
"""

from __future__ import annotations

import subprocess
import wave
from pathlib import Path

import numpy as np

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vre.easing import NAMED, bezier  # noqa: E402

W, H, FPS, N = 108, 192, 30, 90
SQUARE_FROM, SQUARE_TO, MOVE_START, MOVE_END = 8.0, 80.0, 4, 22
TRUE_CUTS = [30, 60, 64]
CLICKS_S = [0.5, 1.0, 2.0]


def square_x(f: int) -> float:
    if f <= MOVE_START:
        return SQUARE_FROM
    if f >= MOVE_END:
        return SQUARE_TO
    u = (f - MOVE_START) / (MOVE_END - MOVE_START)
    return SQUARE_FROM + (SQUARE_TO - SQUARE_FROM) * float(bezier(np.array([u]), *NAMED["easeOutCubic"])[0])


def display_frame(f: int) -> np.ndarray:
    img = np.zeros((H, W, 3), np.uint8)
    if f < 30:
        img[:] = (11, 31, 58)
        x = square_x(f)  # sub-pixel: edge columns get fractional coverage (anti-aliased)
        cols = np.arange(W, dtype=np.float64)
        cov = np.clip(np.minimum(cols + 1, x + 16) - np.maximum(cols, x), 0.0, 1.0)[None, :, None]
        band = (1 - cov) * np.array([11, 31, 58]) + cov * np.array([245, 183, 0])
        img[88:104] = np.round(np.repeat(band, 16, axis=0)).astype(np.uint8)
    elif f < 60:
        img[:] = (244, 241, 234)
        img[120:132, 10:98] = (20, 20, 20)
    elif f < 64:
        img[:] = (0, 0, 0)
    else:
        img[:] = (0, 128, 128)
    img[0:8, 0:8] = (230, 20, 20)
    return img


def _wav(path: Path, sr: int = 22050) -> None:
    y = np.zeros(int(N / FPS * sr), np.float32)
    for t in CLICKS_S:
        i = int(t * sr)
        n = int(0.02 * sr)
        y[i:i + n] += 0.8 * np.sin(2 * np.pi * 1500 * np.arange(n) / sr) * np.hanning(n)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(y, -1, 1) * 32767).astype("<i2").tobytes())


def make(out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    flat, wav, final = out_dir / "flat.mp4", out_dir / "clicks.wav", out_dir / "synth_rotated.mp4"
    if final.exists():
        return final
    # store landscape: rotate the portrait display frame 90 degrees clockwise
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{H}x{W}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-qp", "0", "-pix_fmt", "yuv444p",
                            str(flat)], stdin=subprocess.PIPE)
    assert enc.stdin is not None
    for f in range(N):
        enc.stdin.write(np.ascontiguousarray(np.rot90(display_frame(f), k=-1)).tobytes())
    enc.stdin.close()
    if enc.wait() != 0:
        raise RuntimeError("ffmpeg encode failed")
    _wav(wav)
    # display_rotation is counter-clockwise: +90 turns the stored landscape back into the portrait display
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-display_rotation", "90", "-i", str(flat), "-i", str(wav),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-shortest", str(final)], check=True)
    return final
