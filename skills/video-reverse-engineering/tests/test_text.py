"""Phase 1 gates (TXT-01..03): text tracks recovered from a synthetic clip with known truth, and each gate has a
negative control observed to fail."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import synth_text as st  # noqa: E402
from vre import text  # noqa: E402

pytestmark = pytest.mark.filterwarnings("ignore::RuntimeWarning")


def run(frames, detector=text.detect_ink):
    return text.track_text(frames, st.FPS, detector=detector)


def rows_of(res, prop, element=None):
    return [r for r in res["rows"] if r["property"] == prop and (element is None or r["element"] == element)]


def layer_of(res, first_frame):
    """element id of the track whose first frame is `first_frame`."""
    return next(f"text#{t['id']}" for t in res["tracks"] if t["first"] == first_frame)


@pytest.fixture(scope="module")
def res():
    return run(st.frames())


def test_three_layers_become_three_tracks(res):
    assert len(res["tracks"]) == 3
    assert res["engine"] == "ink" and res["status"] == "DEGRADED_NO_OCR"  # explicit, not silent


def test_moving_layer_position_and_easing(res):
    (r,) = [r for r in rows_of(res, "x") if r["element"] == "text#0"]
    assert abs(r["start"] - st.L0_X[2]) <= 2
    assert abs(r["start"] + r["duration"] - st.L0_X[3]) <= 2  # the slow ease-out tail is recovered
    assert abs((r["to"] - r["from"]) - (st.L0_X[1] - st.L0_X[0])) <= 2.0  # px
    assert r["easing"] == "easeOutCubic" and r["evidence"] == "OBSERVED"


def test_scale_track_is_linear_and_matches_an_independent_measure(res):
    (r,) = rows_of(res, "scale", "text#1")
    assert abs(r["start"] - st.L2_SCALE[2]) <= 2 and abs(r["start"] + r["duration"] - st.L2_SCALE[3]) <= 2
    assert r["easing"] == "linear"
    # independent instrument: integer bounding box of the thresholded layer, no sub-pixel code involved

    def box_h(f):
        img = st.frame(f)[430:560]
        ys = np.nonzero((img.astype(int) - np.array(st.BG)).__abs__().sum(axis=2).max(axis=1) > 60)[0]
        return ys.max() - ys.min() + 1

    assert abs(r["to"] - box_h(60) / box_h(0)) <= 2 / box_h(0)  # integer bbox: +-1 px per edge


def test_word_by_word_reveal_frames(res):
    el = layer_of(res, st.L1_REVEAL[0])
    got = [r["start"] for r in rows_of(res, "reveal", el)]
    assert len(got) == len(st.L1_REVEAL)
    assert all(abs(g - t) <= 2 for g, t in zip(got, st.L1_REVEAL))


def test_shifted_reveal_is_caught():
    """Negative control: the same instrument on a clip whose reveals are 6 frames late must NOT match the
    original truth (otherwise the reveal check could never fail)."""
    shifted = run(st.frames(reveal=[26, 41, 56]))
    el = layer_of(shifted, 26)
    got = [r["start"] for r in rows_of(shifted, "reveal", el)]
    assert any(abs(g - t) > 2 for g, t in zip(got, st.L1_REVEAL))
    assert all(abs(g - t) <= 2 for g, t in zip(got, [26, 41, 56]))  # and it does see the real (shifted) times


def test_wrong_easing_is_caught():
    """Negative control: a linear mover is not reported as easeOutCubic."""
    lin = run(st.frames(l0_family="linear"))
    (r,) = [r for r in rows_of(lin, "x") if r["element"] == "text#0"]
    assert r["easing"] != "easeOutCubic"


def test_missing_text_gives_no_tracks_not_an_invented_one():
    blank = run(st.frames(with_text=False))
    assert blank["tracks"] == [] and blank["rows"] == []


def test_recognised_words_never_reach_the_rows():
    """TXT-03: text is alignment input only. A detector that returns a distinctive string must leave no trace."""
    def fake(rgb, f):
        return [text.Detection(f, (20 + f * 0.5, 100, 120 + f * 0.5, 130), "ZEBRAQUOKKA ROCKET")]

    r = run([np.zeros((64, 64, 3), np.uint8)] * 30, detector=fake)
    assert r["rows"], "the fake detector should have produced at least one moving row"
    blob = json.dumps(r).lower()
    assert "zebraquokka" not in blob and "rocket" not in blob


def test_reveal_aligns_to_asr_word_times_and_a_shifted_asr_is_unmatched(res):
    el = layer_of(res, st.L1_REVEAL[0])
    rows = rows_of(res, "reveal", el)
    asr = [{"word": "w", "start": t / st.FPS} for t in st.L1_REVEAL]
    ok = text.align_reveals_to_words(rows, asr, st.FPS)
    assert all(r["asr_aligned"] and abs(r["asr_delta_ms"]) <= 70 for r in ok)
    late = text.align_reveals_to_words(rows, [{"word": "w", "start": t / st.FPS + 0.3} for t in st.L1_REVEAL], st.FPS)
    assert not any(r["asr_aligned"] for r in late)


def test_fade_in_opacity_ramp():
    """Opacity track from a layer whose ink fades in over 10 frames (known linear ramp)."""
    frames = []
    for f in range(40):
        img = np.zeros((120, 200, 3), np.uint8)
        img[:] = (11, 31, 58)
        a = min(1.0, max(0.0, (f - 10) / 10)) if f >= 10 else 0.0
        cv2.putText(img, "FADE", (20, 70), st.FONT, 1.5, tuple(int(11 + (245 - 11) * a) for _ in range(3)), 3,
                    cv2.LINE_AA)
        frames.append(img)
    r = run(frames)
    (row,) = [x for x in r["rows"] if x["property"] == "opacity"]
    assert abs(row["start"] - 10) <= 2 and abs(row["start"] + row["duration"] - 20) <= 2
    assert row["rmse"] < 0.05 and row["from"] < 0.25 and row["to"] > 0.9


def test_ocr_engine_reads_the_layers_when_installed():
    if not text.ocr_available():
        pytest.skip("paddleocr UNAVAILABLE (reported in `vre deps`)")
    det = text.make_ocr_detector()
    got = det(st.frame(89), 89)
    words = " ".join((d.text or "") for d in got).upper()
    assert "ORBIT" in words and "LAUNCH" in words
    for d in got:  # refined boxes sit on the ink: sub-pixel box vs the ink-detector box agree within 3 px
        ink = min(text.detect_ink(st.frame(89), 89), key=lambda i: abs(i.box[1] - d.box[1]))
        assert max(abs(a - b) for a, b in zip(d.box, ink.box)) <= 3.0
