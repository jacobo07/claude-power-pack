"""Phase 4 gates (JDG-01/02): the judge passes a benign re-encode and FAILS each negative control on the dimension
that was broken, with tolerances frozen from the A/A floor and the controls before any candidate is judged."""

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
from vre import judge  # noqa: E402
from vre.pipeline import analyze  # noqa: E402
from vre.track import track  # noqa: E402

pytestmark = pytest.mark.filterwarnings("ignore::RuntimeWarning")

BASE = {"frame_count_frames": 0, "cut_frames": 2, "blank_std": 2.0, "row_start_frames": 2,
        "row_match_window_frames": 12, "av_offset_s": 0.08}


def measure(video: Path, out: Path):
    spec = analyze(str(video), str(out), width=sj.W, words=False, beats=False)
    track(str(out), detector=lambda *_a, **_k: [], text_on=False, flow_on=False)
    spec = json.loads((out / "spec.json").read_text())
    _, gray = judge.gray_frames(str(video), 96)
    return spec, gray


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    base = tmp_path_factory.mktemp("jdg")
    ref = sj.variant(base / "ref.mp4")
    clips = {
        "aa": sj.encode(base / "aa.mp4", (sj.frame(f) for f in range(sj.N)), crf=30),
        "shift_cut": sj.variant(base / "c1.mp4", cuts=(35, 60)),
        "wrong_easing": sj.variant(base / "c2.mp4", easing="easeInCubic"),
        "missing_object": sj.variant(base / "c3.mp4", missing_shot=1),
        "blank": sj.variant(base / "c4.mp4", n_blank=(40, 41, 42)),
        "late_start": sj.variant(base / "c5.mp4", start=12),
        "count_drift": sj.variant(base / "c6.mp4", n=sj.N + 3),
        "landscape": sj.encode(base / "c7.mp4", (np.rot90(sj.frame(f)) for f in range(sj.N)), size=(sj.H, sj.W)),
    }
    r = measure(ref, base / "ref")
    cands = {k: measure(v, base / k) for k, v in clips.items()}
    return base, r, cands


def tolerances(world, tmp_path):
    base, (rspec, rgray), cands = world
    ssims = lambda c: [d["mean"] for d in judge.d_shot_ssim(rspec, rgray, c[1], {"shot_ssim_min": 0})["per_shot"]]  # noqa: E731
    aa = ssims(cands["aa"])
    controls = {k: min(ssims(cands[k])) for k in  # the judge tests the WORST shot, so a control is its worst shot
 ("wrong_easing", "missing_object", "blank")}
    return judge.freeze(tmp_path / "tol.json", aa, controls, BASE)


def test_reference_rows_were_measured(world):
    _, (rspec, _), _ = world
    assert sum(r["evidence"] == "OBSERVED" and r["property"] == "x" for r in rspec["rows"]) >= 2


def test_benign_reencode_is_moves_same_and_looks_same(world, tmp_path):
    _, (rspec, rgray), c = world
    tol = tolerances(world, tmp_path)
    v = judge.judge(rspec, c["aa"][0], rgray, c["aa"][1], tol)
    assert v["level"] in ("MOVES-SAME", "LOOKS-SAME"), v["dimensions"]
    assert not v["critical_failures"]


@pytest.mark.parametrize("name,dim", [
    ("shift_cut", "cuts"), ("missing_object", "missing_objects"), ("blank", "blank_frames"),
    ("count_drift", "frame_count"), ("landscape", "orientation"),
    ("late_start", "row_timing"), ("wrong_easing", "row_easing"),
])
def test_negative_controls_fail_on_their_dimension(world, tmp_path, name, dim):
    _, (rspec, rgray), c = world
    tol = tolerances(world, tmp_path)
    if name == "landscape":  # different frame geometry: ssim is not comparable, orientation must catch it first
        assert judge.d_orientation(rspec, c[name][0])["status"] == "FAIL"
        return
    v = judge.judge(rspec, c[name][0], rgray, c[name][1], tol)
    assert v["dimensions"][dim]["status"] == "FAIL", v["dimensions"][dim]
    assert v["level"] == "FAIL"


def test_freeze_refuses_inseparable_instrument(tmp_path):
    with pytest.raises(ValueError, match="cannot separate"):
        judge.freeze(tmp_path / "t.json", [0.90, 0.95], {"x": 0.93}, BASE)


def test_tampered_tolerances_are_refused(world, tmp_path):
    tol = tolerances(world, tmp_path)
    data = json.loads((tmp_path / "tol.json").read_text())
    data["values"]["cut_frames"] = 99
    (tmp_path / "bad.json").write_text(json.dumps(data))
    assert judge.load_tolerances(tmp_path / "tol.json")["frozen"]["sha256"] == tol["frozen"]["sha256"]
    with pytest.raises(ValueError, match="no longer matches"):
        judge.load_tolerances(tmp_path / "bad.json")


def test_av_offset_pass_and_fail():
    tol = {"av_offset_s": 0.08}
    ref = {"audio": {"status": "OK", "onsets_on_cuts": [{"time_s": 1.0}, {"time_s": 2.0}]}}
    ok = {"audio": {"status": "OK", "onsets_s": [1.03, 2.02]}}
    bad = {"audio": {"status": "OK", "onsets_s": [1.03, 2.30]}}
    none = {"audio": {"status": "NO_AUDIO_STREAM"}}
    assert judge.d_av(ref, ok, tol)["status"] == "PASS"
    assert judge.d_av(ref, bad, tol)["status"] == "FAIL"
    assert judge.d_av(ref, none, tol)["status"] == "FAIL"
    assert judge.d_av({"audio": {"status": "NO_AUDIO_STREAM"}}, ok, tol)["status"] == "UNMEASURED"


def test_rebrand_skips_pixels_but_still_gates_moves(world, tmp_path):
    _, (rspec, rgray), c = world
    tol = tolerances(world, tmp_path)
    v = judge.judge(rspec, c["aa"][0], rgray, c["aa"][1], tol, rebrand=True)
    assert v["level"] == "MOVES-SAME" and "shot_ssim" in v["unmeasured"]
