"""Phase 4 gate (ONE-01): the loop converges on a fixable defect and stops, reporting, on one it cannot fix.
The renderer is pure Python (draws the composition data), so nothing here needs node."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import synth_judge as sj  # noqa: E402
from vre import judge, oneshot  # noqa: E402
from vre.easing import NAMED, bezier  # noqa: E402

pytestmark = pytest.mark.filterwarnings("ignore::RuntimeWarning")

BASE = {"frame_count_frames": 0, "cut_frames": 2, "blank_std": 2.0, "row_start_frames": 2,
        "row_match_window_frames": 12, "av_offset_s": 0.08, "shot_ssim_min": 0.5}


def _hex(h: str) -> tuple:
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def make_renderer(lag: int = 0, drop_shot: int | None = None, seen: list | None = None):
    """Draws data['shots'][*].els[*].rows (x sliding) the way the TSX runtime would; `lag` delays every row start
    (a render defect the loop must learn to compensate), `drop_shot` omits that shot's object (unfixable)."""

    def render(tsx_dir: Path, data: dict, out: Path) -> Path:
        if seen is not None:
            seen.append([r["s"] for s in data["shots"] for e in s["els"] for r in e["rows"]])
        frames = []
        for f in range(data["frames"]):
            sh = [s for s in data["shots"] if s["from"] <= f][-1]
            img = np.zeros((data["height"], data["width"], 3), np.uint8)
            img[:] = _hex(sh["bg"])
            if sh["index"] != drop_shot:
                for el in sh["els"]:
                    for r in el["rows"]:
                        if r["p"] != "x":
                            continue
                        u = (f - (r["s"] + lag)) / max(1, r["d"])
                        e = float(bezier(np.array([min(1.0, max(0.0, u))]), *(r["bz"] or NAMED["linear"]))[0])
                        x = r["a"] + (r["b"] - r["a"]) * e
                        x0 = int(np.floor(x - el["w"] / 2 + 0.5 + 1e-6))
                        y0 = int(np.floor(el["y"] - el["h"] / 2 + 0.5 + 1e-6))
                        img[max(0, y0):max(0, y0) + int(el["h"]), max(0, x0):max(0, x0) + int(el["w"])] = \
                            _hex(el["fill"])
            frames.append(img)
        return sj.encode(out, frames)

    return render


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    base = tmp_path_factory.mktemp("one")
    ref = sj.variant(base / "ref.mp4")
    tol = judge.write_frozen(base / "tol.json", BASE, {"synthetic": True})
    return base, ref, tol


def run(world, name, renderer, rounds=3):
    base, ref, _ = world
    return oneshot.oneshot(str(ref), str(base / name), renderer=renderer, tolerances=str(base / "tol.json"),
                           rounds=rounds, width=sj.W, text_on=False, rebrand=True)


def test_late_render_converges_within_three_rounds(world):
    seen: list = []
    rep = run(world, "late", make_renderer(lag=7, seen=seen))
    h = rep["history"]
    assert h[0]["level"] == "FAIL" and h[0]["targeted"], h[0]
    assert rep["final_level"] in ("MOVES-SAME", "LOOKS-SAME"), rep
    assert rep["rounds_run"] <= 3
    assert h[0]["effect"]["fail_count_after"] < h[0]["effect"]["fail_count_before"]
    assert seen[1] != seen[0], "round 2 must feed the generator corrected starts"
    assert "pixel" in rep["claim"]


def test_negative_control_without_the_loop_stays_failing(world):
    rep = run(world, "late_norf", make_renderer(lag=7), rounds=2)
    first = rep["history"][0]
    assert first["level"] == "FAIL"  # the defect is real before any fix: the converging run is not a vacuous pass


def test_unfixable_defect_stops_early_and_reports(world):
    rep = run(world, "gone", make_renderer(drop_shot=1), rounds=5)
    assert rep["final_level"] == "FAIL"
    assert rep["rounds_run"] < 5
    assert "missing_objects" in rep["critical_failures"]
    assert json.loads((world[0] / "gone" / "delta_report.json").read_text())["final_level"] == "FAIL"


def test_reference_spec_is_reused_not_remeasured(world, tmp_path):
    base, ref, _ = world
    first = run(world, "late_src", make_renderer(), rounds=2)
    assert first["final_level"] in ("MOVES-SAME", "LOOKS-SAME")
    calls: list = []

    def boom(*_a, **_k):  # a detector reached for the reference would be a re-measure
        calls.append(1)
        return []

    rep = oneshot.oneshot(str(ref), str(tmp_path / "re"), renderer=make_renderer(), tolerances=str(base / "tol.json"),
                          rounds=2, width=sj.W, text_on=False, rebrand=True, detector=boom,
                          reference_spec=str(base / "late_src" / "reference"))
    assert rep["final_level"] in ("MOVES-SAME", "LOOKS-SAME") and not calls
    with pytest.raises(FileNotFoundError):  # negative control: a dir without a spec is refused, not guessed
        oneshot.oneshot(str(ref), str(tmp_path / "bad"), renderer=make_renderer(), tolerances=str(base / "tol.json"),
                        width=sj.W, text_on=False, rebrand=True, reference_spec=str(tmp_path))
