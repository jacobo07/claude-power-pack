"""Flow summaries recover a known translation, rotation and zoom from RAFT; static and wrong-sign controls fail."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import synth_flow as sf  # noqa: E402
from vre import flow  # noqa: E402

torch = pytest.importorskip("torch")
pytest.importorskip("torchvision")


def med(kind, amount):
    s = flow.shot_flow(sf.clip(kind, amount))
    assert s["status"] == "OK" and s["pairs"] == sf.N - 1
    return s["median"]


def test_translation_is_recovered():
    m = med("translate", 3.0)
    assert abs(m["mean_dx"] + 3.0) < 0.4 and abs(m["mean_dy"] + 1.5) < 0.4  # content moves -x,-y


def test_rotation_rate_is_recovered_with_its_sign():
    cw, ccw = med("rotate", 2.0), med("rotate", -2.0)
    assert abs(abs(cw["rotation_deg"]) - 2.0) < 0.7 and abs(abs(ccw["rotation_deg"]) - 2.0) < 0.7
    assert cw["rotation_deg"] * ccw["rotation_deg"] < 0  # opposite senses read as opposite signs


def test_zoom_rate_is_recovered():
    m = med("zoom", 0.02)
    assert abs(m["zoom_rate"] - 0.02) < 0.01


def test_static_clip_reads_still_and_a_moving_clip_does_not():
    still = flow.shot_flow(np.stack([sf.clip("translate", 0.0)[0]] * 4))["median"]
    assert still["speed_p90"] < 0.1 and still["moving_frac"] < 0.05
    assert med("translate", 3.0)["speed_p50"] > 2.0  # negative control: the instrument can say "moving"
