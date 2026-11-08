"""Phase 2 gates (LAY-01/03): layer tracks recovered from a synthetic clip with a known spring, rotation and stagger;
each gate has a negative control observed to fail. SAM 2 runs the same clip when a checkpoint is given."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import synth_layers as sl  # noqa: E402
from vre import layers  # noqa: E402

pytestmark = pytest.mark.filterwarnings("ignore::RuntimeWarning")


def prompts() -> list[layers.Prompt]:
    cw, ch = sl.CARD_WH
    bw, bh = sl.BAR_WH
    x0, y0 = sl.CARD_X[0], sl.CARD_Y
    ps = [layers.Prompt(0, 0, (x0 - 3, y0 - ch / 2 - 3, x0 + cw + 3, y0 + ch / 2 + 3)),
          layers.Prompt(1, sl.BAR_ANGLE[2], (sl.BAR_C[0] - bw / 2, sl.BAR_C[1] - bh / 2, sl.BAR_C[0] + bw / 2,
                                              sl.BAR_C[1] + bh / 2))]
    for k, st in enumerate(sl.DOT_STARTS):
        f = st + sl.DOT_DUR + 2
        ps.append(layers.Prompt(2 + k, f, (sl.DOT_X[k] - 4, sl.DOT_Y[1] - sl.DOT_SIZE / 2 - 4,
                                           sl.DOT_X[k] + sl.DOT_SIZE + 4, sl.DOT_Y[1] + sl.DOT_SIZE / 2 + 4)))
    return ps


def run(provider=None, **kw):
    return layers.track_layers(sl.frames(**kw), sl.FPS, prompts(), provider)


def rows(res, el, prop):
    return [r for r in res["rows"] if r["element"] == f"layer#{el}" and r["property"] == prop]


@pytest.fixture(scope="module")
def res():
    return run()


def check_truth(res):
    # spring: card x
    (r,) = rows(res, 0, "x")
    assert abs(r["start"] - sl.CARD_X[2]) <= 2 and r["easing"] == "spring" and r["overshoot"] > 0.2
    assert abs((r["to"] - r["from"]) - (sl.CARD_X[1] - sl.CARD_X[0])) <= 2.0
    # rotation: bar
    (r,) = rows(res, 1, "rotation")
    assert abs(r["start"] - sl.BAR_ANGLE[2]) <= 2 and abs(r["start"] + r["duration"] - sl.BAR_ANGLE[3]) <= 2
    assert r["easing"] == "easeInOutCubic" and abs((r["to"] - r["from"]) - 60.0) <= 2.0
    # stagger: three dots, same curve, starts 6 frames apart
    starts = []
    for k in range(3):
        (r,) = rows(res, 2 + k, "y")
        assert r["easing"] == "easeOutCubic" and abs((r["to"] - r["from"]) - (sl.DOT_Y[1] - sl.DOT_Y[0])) <= 2.0
        starts.append(r["start"])
    assert all(abs(s - t) <= 2 for s, t in zip(starts, sl.DOT_STARTS))
    assert all(abs((b - a) - 6) <= 2 for a, b in zip(starts, starts[1:]))


def test_spring_rotation_and_stagger_recovered(res):
    assert res["engine"] == "color"
    check_truth(res)


def test_scale_track_of_a_growing_dot(res):
    (r,) = rows(res, 2, "scale")
    assert abs((r["to"] - r["from"]) - (sl.DOT_SCALE[1] / sl.DOT_SCALE[0] - 1.0)) <= 0.08


def test_wrong_easing_is_caught():
    """Negative control: a linear rotation is not reported as easeInOutCubic."""
    (r,) = rows(run(bar_family="linear"), 1, "rotation")
    assert r["easing"] != "easeInOutCubic"


def test_missing_object_is_lost_not_invented():
    r = run(with_bar=False)
    assert next(o for o in r["objects"] if o["element"] == "layer#1")["status"] == "LOST"
    assert rows(r, 1, "rotation") == [] and rows(r, 1, "x") == []


def test_shifted_stagger_is_caught():
    r = run(dot_starts=[12, 24, 36])
    starts = [rows(r, 2 + k, "y")[0]["start"] for k in range(3)]
    assert any(abs((b - a) - 6) > 2 for a, b in zip(starts, starts[1:]))


def test_static_object_has_no_motion_rows():
    r = layers.track_layers(sl.frames(), sl.FPS, [prompts()[1]])  # bar only, rotation exists
    r2 = layers.track_layers(sl.frames(), sl.FPS, [layers.Prompt(9, 0, (300, 20, 340, 60))])  # empty region
    assert r2["objects"][0]["status"] == "LOST" and r2["rows"] == []
    assert any(x["property"] == "rotation" for x in r["rows"])


def test_sam2_matches_the_same_truth():
    ckpt = os.environ.get("VRE_SAM2_CKPT")
    if not ckpt or not layers.available("sam2"):
        pytest.skip("sam2 UNAVAILABLE here (set VRE_SAM2_CKPT to a checkpoint)")
    check_truth(run(layers.Sam2Provider(ckpt)))
