"""W1 gates: every stage must recover the synthetic clip's known truth, and must be able to FAIL."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import synth  # noqa: E402
from vre import audio, deps, easing, media, palette  # noqa: E402
from vre.pipeline import analyze  # noqa: E402

pytestmark = pytest.mark.filterwarnings("ignore::RuntimeWarning")


@pytest.fixture(scope="session")
def clip(tmp_path_factory) -> Path:
    base = os.environ.get("VRE_TEST_CACHE")
    out = Path(base) if base else tmp_path_factory.mktemp("synth")
    return synth.make(out)


@pytest.fixture(scope="session")
def spec(clip, tmp_path_factory) -> dict:
    return analyze(str(clip), str(tmp_path_factory.mktemp("spec")), words=False, beats=False)


def test_probe_display_orientation_and_counted_frames(clip):
    p = media.probe(clip)
    assert (p.stored_width, p.stored_height) == (synth.H, synth.W)  # stored landscape
    assert (p.width, p.height) == (synth.W, synth.H)  # display portrait
    assert abs(p.rotation) == 90
    assert p.packets == synth.N and p.fps_exact == "30/1"


def test_decoded_frames_are_upright(clip):
    p = media.probe(clip)
    first = next(media.iter_frames(p, width=synth.W))
    assert first.shape == (synth.H, synth.W, 3)
    tl, br = first[2:6, 2:6].mean(axis=(0, 1)), first[-6:-2, -6:-2].mean(axis=(0, 1))
    assert tl[0] > 150 and tl[1] < 90, f"red marker not at display top-left: {tl}"
    assert br[0] < 60, "bottom-right should be background, not the marker"


def test_landscape_read_is_caught(clip):
    """Negative control: ignoring rotation puts the marker elsewhere, and the upright check fails."""
    p = media.probe(clip)
    wrong = media.Probe(**{**p.to_dict(), "width": p.stored_width, "height": p.stored_height})
    w, h = media.analysis_size(wrong, synth.H)
    assert (w, h) != (synth.W, synth.H)


def test_cuts_recovered_exactly(spec):
    found = [c["frame"] for c in spec["cuts"]]
    for truth in synth.TRUE_CUTS:
        assert any(abs(f - truth) <= 0 for f in found), f"cut {truth} missing from {found}"
    assert len(found) == len(synth.TRUE_CUTS), f"spurious cuts: {found}"
    assert spec["source"]["decoded_frames"] == synth.N and spec["source"]["frame_count_agrees"]


def test_moving_square_is_not_a_cut(spec):
    assert not [c for c in spec["cuts"] if 0 < c["frame"] < 30]


def test_shift_detected_by_cut_list_diff(spec):
    """Negative control: a cut list shifted by 3 frames must not match the truth within 0 frames."""
    shifted = [c["frame"] + 3 for c in spec["cuts"]]
    assert not all(any(abs(f - t) <= 0 for f in shifted) for t in synth.TRUE_CUTS)


def test_palette_roles_and_polarity(spec):
    a, b = spec["shots"][0]["palette"], spec["shots"][1]["palette"]
    assert a["polarity"] == "dark" and b["polarity"] == "light"
    bg = a["roles"]["background"]
    r, g, bl = int(bg[1:3], 16), int(bg[3:5], 16), int(bg[5:7], 16)
    assert abs(r - 11) <= 6 and abs(g - 31) <= 6 and abs(bl - 58) <= 6, bg
    assert a["roles"]["accent"] is not None  # the yellow square


def test_brand_mapping_by_role():
    roles = {"background": "#0B1F3A", "surface": None, "accent": "#F5B700", "text": "#FFFFFF"}
    brand = {"dark": {"background": "#101820", "accent": "#2EC4B6", "text": "#F7F7F7", "surface": "#1C2833"}}
    mapped = palette.map_to_brand(roles, "dark", brand)
    assert mapped == {"background": "#101820", "surface": None, "accent": "#2EC4B6", "text": "#F7F7F7"}


def test_audio_onsets_land_on_clicks(spec):
    on = spec["audio"]["onsets_s"]
    for t in synth.CLICKS_S:
        assert any(abs(o - t) <= 0.03 for o in on), f"click {t}s missing from {on}"
    paired = {p["frame"] for p in spec["audio"]["onsets_on_cuts"]}
    assert 30 in paired and 60 in paired


def test_silence_has_no_onsets():
    assert audio.onsets(np.zeros(22050, np.float32), 22050) == []


def test_easing_fit_recovers_family_from_the_video(clip):
    p = media.probe(clip)
    xs, fs = [], []
    for f, frame in enumerate(media.iter_frames(p, width=synth.W)):
        if f >= 30:
            break
        row = frame[96, :, 0].astype(np.float64)  # red channel: navy 11 -> yellow 245
        w = np.clip((row - 11) / (245 - 11), 0, 1)
        w[:10] = 0  # ignore the marker column band
        if w.sum() > 4:
            xs.append(float((np.arange(len(w)) * w).sum() / w.sum()) - 7.5)  # centroid -> left edge
            fs.append(f)
    segs = easing.split_motion(np.array(fs), np.array(xs), eps=0.05)
    assert len(segs) == 1
    a, b = segs[0]
    fit = easing.fit_segment(np.array(fs[a:b + 1]), np.array(xs[a:b + 1]), synth.FPS)
    assert fit is not None and abs(fit.start_frame - synth.MOVE_START) <= 1 and abs(fit.end_frame - synth.MOVE_END) <= 1
    assert fit.family in {"easeOutCubic", "easeOutQuart", "easeOutQuad", "bezier"}, fit.candidates
    assert fit.rmse < 0.04


def test_wrong_easing_is_distinguishable():
    """Negative control: linear motion must not fit as easeOutCubic."""
    f = np.arange(0, 21)
    fit = easing.fit_segment(f, 3.0 * f, 30)
    assert fit is not None and fit.family == "linear" and fit.rmse < 1e-3


def test_spring_detected_with_remotion_config():
    t = np.arange(0, 40) / 30
    v = 100 * easing.spring_curve(t, 0.35, 18.0)
    fit = easing.fit_segment(np.arange(0, 40), v, 30)
    assert fit is not None and fit.family == "spring" and fit.overshoot > 0.2
    assert abs(fit.spring["stiffness"] - 324) / 324 < 0.1
    assert "spring(" in fit.remotion()


def test_excluded_engines_refuse():
    with pytest.raises(deps.ExcludedDependency):
        deps.available("cotracker")


def test_gated_engine_needs_flag(monkeypatch):
    monkeypatch.delenv("VRE_ALLOW_SAM3", raising=False)
    assert deps.available("sam3") is False


def test_reverse_ledger_lists_unavailable(spec, tmp_path):
    from vre.pipeline import reverse_ledger

    text = reverse_ledger(spec)
    assert "never copy the source's audio" in text
    assert "not yet tracked" in text
    json.dumps(spec)  # the spec is serialisable


def test_failing_engine_is_failed_not_a_crash(monkeypatch):
    """Regression 2026-11-08: faster-whisper picked CUDA without cuBLAS and killed the whole analysis."""
    def boom(*_a, **_k):
        raise RuntimeError("Library cublas64_12.dll is not found or cannot be loaded")

    monkeypatch.setattr(audio, "_words", boom)
    res = audio.words("any.mp4")
    assert res["status"] == "FAILED" and "cublas" in res["reason"]


def test_device_override(monkeypatch):
    monkeypatch.setenv("VRE_DEVICE", "cpu")
    assert audio._device() == "cpu"
