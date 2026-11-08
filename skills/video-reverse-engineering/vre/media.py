"""Probe and decode a video once, in DISPLAY orientation, with a counted frame total.

Rules carried from an earlier private forensics harness and HeyGen's reverse-any-video workflow:
- fps, size and duration come from the video stream and its counted frames, never from audio length;
- rotation metadata is applied once here, so no later stage can read a portrait reel as landscape;
- the decoded frame count is authoritative and is compared with the container's packet count.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path
from typing import Iterator

import numpy as np


class MediaError(RuntimeError):
    """ffmpeg/ffprobe failed or the file is not a usable video."""


@dataclass(frozen=True)
class Probe:
    path: str
    stored_width: int
    stored_height: int
    rotation: int  # side-data convention (counter-clockwise degrees, e.g. -90)
    width: int  # display width after rotation
    height: int  # display height after rotation
    fps: float
    fps_exact: str
    packets: int  # container packet count (one per frame for the usual codecs)
    duration_s: float  # packets / fps
    has_audio: bool
    audio_duration_s: float | None

    def to_dict(self) -> dict:
        return asdict(self)


def _run(cmd: list[str]) -> bytes:
    proc = subprocess.run(cmd, capture_output=True, check=False)
    if proc.returncode != 0:
        tail = proc.stderr.decode(errors="replace")[-600:]
        raise MediaError(f"{cmd[0]} exited {proc.returncode}: {tail}")
    return proc.stdout


def _rotation(stream: dict) -> int:
    for side in stream.get("side_data_list") or []:
        if "rotation" in side:
            return int(round(float(side["rotation"])))
    tag = (stream.get("tags") or {}).get("rotate")
    if tag is not None:  # legacy tag is clockwise; side data is counter-clockwise
        return -int(round(float(tag)))
    return 0


def _fps(stream: dict) -> Fraction:
    for key in ("avg_frame_rate", "r_frame_rate"):
        raw = stream.get(key) or "0/0"
        num, _, den = raw.partition("/")
        if den and int(den) != 0 and int(num) != 0:
            return Fraction(int(num), int(den))
    raise MediaError("video stream reports no frame rate")


def probe(path: str | Path) -> Probe:
    path = str(path)
    info = json.loads(_run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", path]))
    streams = info.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if video is None:
        raise MediaError(f"no video stream in {path}")
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    counted = _run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
         "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", path]
    ).decode().strip().strip(",")
    packets = int(counted) if counted.isdigit() else 0
    if packets <= 0:
        raise MediaError(f"could not count video packets in {path}")
    rot = _rotation(video)
    sw, sh = int(video["width"]), int(video["height"])
    dw, dh = (sh, sw) if abs(rot) % 180 == 90 else (sw, sh)
    fps = _fps(video)
    audio_dur = None
    if audio is not None and audio.get("duration") not in (None, "N/A"):
        audio_dur = float(audio["duration"])
    return Probe(
        path=path, stored_width=sw, stored_height=sh, rotation=rot, width=dw, height=dh,
        fps=float(fps), fps_exact=f"{fps.numerator}/{fps.denominator}", packets=packets,
        duration_s=packets / float(fps), has_audio=audio is not None, audio_duration_s=audio_dur,
    )


def analysis_size(p: Probe, width: int) -> tuple[int, int]:
    """Analysis frame size keeping the display aspect; both sides even."""
    w = max(2, width - width % 2)
    h = max(2, int(round(w * p.height / p.width / 2.0)) * 2)
    return w, h


def iter_frames(p: Probe, width: int = 144) -> Iterator[np.ndarray]:
    """Yield every decoded frame as RGB uint8 (H, W, 3) in display orientation.

    `-fps_mode passthrough` keeps exactly the decoded frames (no duplication or drop to a CFR grid).
    ffmpeg applies the rotation side data itself (autorotate is on by default).
    """
    w, h = analysis_size(p, width)
    cmd = ["ffmpeg", "-v", "error", "-nostdin", "-i", p.path, "-map", "0:v:0", "-fps_mode", "passthrough",
           "-vf", f"scale={w}:{h}:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    size = w * h * 3
    assert proc.stdout is not None
    try:
        while True:
            buf = proc.stdout.read(size)
            if len(buf) < size:
                break
            yield np.frombuffer(buf, np.uint8).reshape(h, w, 3)
    finally:
        proc.stdout.close()
        err = proc.stderr.read().decode(errors="replace") if proc.stderr else ""
        code = proc.wait()
    if code != 0:
        raise MediaError(f"ffmpeg decode exited {code}: {err[-600:]}")


def read_window(p: Probe, start: int, end: int, width: int = 360) -> np.ndarray:
    """Decode frames [start, end] inclusive at a higher resolution (for tracking and frame reads)."""
    out = []
    for i, frame in enumerate(iter_frames(p, width)):
        if i > end:
            break
        if i >= start:
            out.append(frame.copy())
    if not out:
        raise MediaError(f"window {start}-{end} is outside the decoded frames")
    return np.stack(out)
