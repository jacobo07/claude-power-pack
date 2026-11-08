"""`vre track`: text rows written into spec.json from a real encoded file, deterministic, with controls."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import synth_text as st  # noqa: E402
from vre import media  # noqa: E402
from vre.pipeline import analyze  # noqa: E402
from vre import text  # noqa: E402
from vre.track import track as _track  # noqa: E402

pytestmark = pytest.mark.filterwarnings("ignore::RuntimeWarning")


def encode(path: Path, frames) -> Path:
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{st.W}x{st.H}", "-r", str(st.FPS), "-i", "-", "-c:v", "libx264", "-qp", "0",
                            "-pix_fmt", "yuv444p", str(path)], stdin=subprocess.PIPE)
    for f in frames:
        enc.stdin.write(f.tobytes())
    enc.stdin.close()
    assert enc.wait() == 0
    return path


@pytest.fixture(scope="module")
def spec_dir(tmp_path_factory) -> Path:
    base = tmp_path_factory.mktemp("trk")
    video = encode(base / "t.mp4", st.frames())
    out = base / "spec"
    analyze(str(video), str(out), width=st.W, words=False, beats=False)
    return out


def track(d, **kw):
    kw.setdefault("layers_on", False)
    kw.setdefault("flow_on", False)
    return _track(d, detector=text.detect_ink, **kw)  # fast, model-free; the OCR path is the phase gate


def load(d: Path) -> dict:
    return json.loads((d / "spec.json").read_text(encoding="utf-8"))


def test_track_fills_text_rows_in_the_spec(spec_dir):
    assert load(spec_dir)["rows"] == []
    info = track(str(spec_dir), width=st.W)
    spec = load(spec_dir)
    assert info["status"] == "DEGRADED_NO_OCR" or info["engine"] == "paddleocr"
    assert len(info["tracks"]) == 3
    xs = [r for r in spec["rows"] if r["property"] == "x"]
    assert len(xs) == 1 and abs(xs[0]["start"] - st.L0_X[2]) <= 2 and xs[0]["easing"] == "easeOutCubic"
    assert all(r["source"] == "text" and r["element"].startswith("s0.text#") for r in spec["rows"])
    rev = [r for r in spec["rows"] if r["property"] == "reveal"]
    assert sorted(r["start"] for r in rev) and len(rev) == len(st.L1_REVEAL)
    assert all(abs(g - t) <= 2 for g, t in zip(sorted(r["start"] for r in rev), st.L1_REVEAL))


def test_two_runs_are_identical_and_rerun_does_not_duplicate(spec_dir):
    track(str(spec_dir), width=st.W)
    a = (spec_dir / "spec.json").read_bytes()
    track(str(spec_dir), width=st.W)
    assert (spec_dir / "spec.json").read_bytes() == a


def test_foreign_rows_survive_a_rerun(spec_dir):
    spec = load(spec_dir)
    spec["rows"].append({"element": "card#0", "property": "x", "start": 5, "source": "layer"})
    (spec_dir / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
    track(str(spec_dir), width=st.W)
    assert any(r.get("source") == "layer" for r in load(spec_dir)["rows"])


def test_wrong_video_is_refused(spec_dir, tmp_path):
    """Negative control: a clip of another size must not be tracked against this spec."""
    import numpy as np

    other = encode(tmp_path / "o.mp4", [np.zeros((st.H, st.W, 3), np.uint8)] * 10)
    spec = load(spec_dir)
    spec["source"]["width"] = 999
    (spec_dir / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
    with pytest.raises(media.MediaError):
        track(str(spec_dir), video=str(other), width=st.W)


# ---- layers + flow through the same command (synthetic layers clip, known truth in synth_layers)
import synth_layers as sl  # noqa: E402


@pytest.fixture(scope="module")
def layer_spec_dir(tmp_path_factory) -> Path:
    base = tmp_path_factory.mktemp("lyr")
    video = encode(base / "l.mp4", sl.frames())
    out = base / "spec"
    analyze(str(video), str(out), width=sl.W, words=False, beats=False)
    return out


def test_track_fills_layer_rows_deterministically(layer_spec_dir):
    track(str(layer_spec_dir), width=sl.W, layers_on=True, text_on=False)
    a = (layer_spec_dir / "spec.json").read_bytes()
    spec = load(layer_spec_dir)
    lay = [r for r in spec["rows"] if r["source"] == "layer"]
    assert spec["layer_tracks"]["engine"] == "color" and lay
    assert all(r["element"].startswith("s0.layer#") for r in lay)
    rot = [r for r in lay if r["property"] == "rotation"]
    assert len(rot) == 1 and abs(rot[0]["start"] - sl.BAR_ANGLE[2]) <= 3 and rot[0]["easing"] == "easeInOutCubic"
    track(str(layer_spec_dir), width=sl.W, layers_on=True, text_on=False)
    assert (layer_spec_dir / "spec.json").read_bytes() == a  # two runs identical, no duplicated rows


def test_empty_clip_yields_no_layer_rows(tmp_path):
    """Negative control: a blank clip has nothing to prompt, so no objects and no rows."""
    import numpy as np

    video = encode(tmp_path / "e.mp4", [np.full((sl.H, sl.W, 3), sl.BG, np.uint8)] * 30)
    analyze(str(video), str(tmp_path / "s"), width=sl.W, words=False, beats=False)
    track(str(tmp_path / "s"), width=sl.W, layers_on=True, text_on=False)
    spec = load(tmp_path / "s")
    assert spec["layer_tracks"]["objects"] == [] and not [r for r in spec["rows"] if r["source"] == "layer"]


def test_flow_block_is_written_per_shot(layer_spec_dir):
    from vre.deps import available

    if not available("torch"):
        pytest.skip("torch UNAVAILABLE here")
    track(str(layer_spec_dir), width=sl.W, layers_on=False, text_on=False, flow_on=True)
    fl = load(layer_spec_dir)["flow_tracks"]["shots"]["0"]
    assert fl["status"] in ("OK", "UNAVAILABLE")
