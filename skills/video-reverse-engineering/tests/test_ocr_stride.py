"""Sparse detection (--ocr-stride) for slow OCR: fewer detector calls, same tracks, timing within the stride.
Negative control: a stride longer than the track gaps allow breaks the tracks, and the test sees it."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import synth_text as st  # noqa: E402
from vre import text  # noqa: E402


def counted():
    calls = []

    def det(rgb, i):
        calls.append(i)
        return text.detect_ink(rgb, i)

    return det, calls


def test_stride_cuts_detector_calls_and_keeps_tracks():
    frames = st.frames()
    full = text.track_text(frames, st.FPS, detector=text.detect_ink)
    det, calls = counted()
    sparse = text.track_text(frames, st.FPS, detector=det, stride=3)
    assert len(calls) <= len(frames) // 3 + 2
    assert sparse["stride"] == 3
    assert len(sparse["tracks"]) == len(full["tracks"])
    by_first = lambda r: sorted(r["tracks"], key=lambda t: t["first"])  # noqa: E731
    for a, b in zip(by_first(full), by_first(sparse)):
        assert 0 <= b["first"] - a["first"] <= 3 and 0 <= a["last"] - b["last"] <= 3


def test_negative_control_huge_stride_breaks_the_timing_bound():
    """The 3-frame bound of the test above must be sensitive: stride 40 starts a track many frames late."""
    frames = st.frames()
    full = text.track_text(frames, st.FPS, detector=text.detect_ink)
    sparse = text.track_text(frames, st.FPS, detector=text.detect_ink, stride=40)
    late = [b["first"] - a["first"] for a, b in zip(sorted(full["tracks"], key=lambda t: t["first"]),
                                                    sorted(sparse["tracks"], key=lambda t: t["first"]))]
    assert max(late) > 3
