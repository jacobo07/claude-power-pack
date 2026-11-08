"""`vre generate`: rows become interpolate/Easing/spring code, copy only from the copy file, deterministic."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from vre import generate as gen  # noqa: E402


def spec() -> dict:
    return {
        "source": {"width": 720, "height": 1280, "fps": 30.0}, "analysis": {"width": 360, "height": 640},
        "shots": [{"index": 0, "start": 0, "end": 59, "palette": {"polarity": "dark", "roles": {
            "background": "#101010", "accent": "#20b8a6", "surface": "#303030", "text": "#f0f0f0"}}},
                  {"index": 1, "start": 60, "end": 89, "palette": {"polarity": "light", "roles": {
                      "background": "#f0f0f0", "accent": "#f05a50", "surface": "#c0c0c0", "text": "#101010"}}}],
        "text_tracks": {"width": 360, "tracks": [
            {"element": "s0.text#0", "shot": 0, "first": 5, "last": 55, "frames": 51, "box": [20, 100, 200, 130]}]},
        "layer_tracks": {"width": 360, "objects": [
            {"element": "s1.layer#0", "shot": 1, "status": "OK", "first": 60, "last": 89, "frames": 30,
             "box": [100, 200, 160, 260], "rgb": [240, 90, 80]},
            {"element": "s1.layer#1", "shot": 1, "status": "LOST", "frames": 0}]},
        "rows": [
            {"element": "s0.text#0", "property": "x", "start": 10, "duration": 12, "from": 20, "to": 60,
             "easing": "easeOutCubic", "bezier": [0.33, 1, 0.68, 1], "spring": None},
            {"element": "s0.text#0", "property": "reveal", "start": 20, "duration": 0, "from": 0, "to": 1,
             "easing": "step", "bezier": None, "spring": None},
            {"element": "s1.layer#0", "property": "x", "start": 64, "duration": 10, "from": 130, "to": 200,
             "easing": "spring", "bezier": None, "spring": {"mass": 1, "damping": 12.6, "stiffness": 324}},
        ]}


def test_rows_become_easing_and_spring_code_with_brand_colours():
    data, rep = gen.build(spec(), None, {"s0.text#0": "Hello there world"})
    tsx = gen.render_tsx(data)
    assert tsx.count("<Sequence") == 1 and '"e": "easeOutCubic"' in tsx and '"e": "spring"' in tsx
    assert "Easing.bezier" in tsx and "spring({frame" in tsx and "interpolate(" in tsx
    els = {e["id"]: e for s in data["shots"] for e in s["els"]}
    assert els["s0.text#0"]["fill"] == gen.DEFAULT_BRAND["dark"]["text"]
    assert els["s1.layer#0"]["fill"] == gen.DEFAULT_BRAND["light"]["accent"]  # nearest source role = accent
    assert "s1.layer#1" not in els  # a LOST object is not rendered
    assert els["s0.text#0"]["rows"][0]["a"] == 40.0 and els["s0.text#0"]["x"] == 40.0  # px scaled 360 -> 720


def test_text_comes_only_from_the_copy_file():
    data, rep = gen.build(spec(), None, {})
    assert rep["unfilled_text"] == ["s0.text#0"]
    el = next(e for s in data["shots"] for e in s["els"] if e["id"] == "s0.text#0")
    assert el["text"] is None
    data2, rep2 = gen.build(spec(), None, {"s0.text#0": "Original line", "s9.text#9": "stray"})
    assert rep2["unused_copy"] == ["s9.text#9"] and "Original line" in gen.render_tsx(data2)


def test_strict_refuses_a_missing_slot_and_output_is_deterministic(tmp_path):
    (tmp_path / "s").mkdir()
    (tmp_path / "s" / "spec.json").write_text(json.dumps(spec()), encoding="utf-8")
    with pytest.raises(ValueError):
        gen.generate(str(tmp_path / "s"), str(tmp_path / "o"), strict=True)
    (tmp_path / "c.json").write_text(json.dumps({"s0.text#0": "Line"}), encoding="utf-8")
    gen.generate(str(tmp_path / "s"), str(tmp_path / "o1"), copy=str(tmp_path / "c.json"))
    gen.generate(str(tmp_path / "s"), str(tmp_path / "o2"), copy=str(tmp_path / "c.json"))
    a, b = (tmp_path / n / "VreComposition.tsx" for n in ("o1", "o2"))
    assert a.read_bytes() == b.read_bytes()


def test_generated_tsx_typechecks_when_a_remotion_project_is_given(tmp_path):
    proj = os.environ.get("VRE_TSC_DIR")
    if not proj or not (Path(proj) / "node_modules" / ".bin" / "tsc").exists():
        pytest.skip("tsc UNAVAILABLE here (set VRE_TSC_DIR to a Remotion project with node_modules)")
    data, _ = gen.build(spec(), None, {"s0.text#0": "Hello there"})
    d = Path(proj) / ".vre-tsc-check"
    d.mkdir(exist_ok=True)
    try:
        (d / "VreComposition.tsx").write_text(gen.render_tsx(data), encoding="utf-8")
        r = subprocess.run([str(Path(proj) / "node_modules" / ".bin" / "tsc"), "--noEmit", "--jsx", "react-jsx",
                            "--strict", "--skipLibCheck", "--moduleResolution", "bundler", "--module", "esnext",
                            "--target", "es2020", str(d / "VreComposition.tsx")], capture_output=True, text=True,
                           cwd=proj)
        assert r.returncode == 0, r.stdout + r.stderr
        bad = (d / "Bad.tsx")
        bad.write_text("export const x: number = 'no';\n", encoding="utf-8")
        r2 = subprocess.run([str(Path(proj) / "node_modules" / ".bin" / "tsc"), "--noEmit", "--strict",
                             str(bad)], capture_output=True, text=True, cwd=proj)
        assert r2.returncode != 0  # negative control: the checker does fail on bad code
    finally:
        shutil.rmtree(d, ignore_errors=True)
