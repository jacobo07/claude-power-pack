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
