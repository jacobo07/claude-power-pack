"""A bright shot whose mean luma hovers at the white threshold is not a fade (found by a real Remotion render in
the oneshot loop); a genuine dip through white still is (negative control)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vre.shots import detect  # noqa: E402


def run(luma):
    n = len(luma)
    return detect(np.zeros((n, 16)), np.zeros((n, 64)), np.asarray(luma, float), 30.0)[0]


def test_bright_shot_hovering_at_threshold_has_no_fade_cuts():
    luma = [243.0] * 20 + [241.9, 242.1, 241.9, 242.1, 242.0, 241.8] + [243.0] * 20
    assert run(luma) == []


def test_genuine_dip_through_white_is_still_found():
    luma = [120.0] * 20 + [190.0, 250.0, 252.0, 252.0, 250.0, 190.0] + [120.0] * 20
    kinds = [c.kind for c in run(luma)]
    assert "fade_white" in kinds
