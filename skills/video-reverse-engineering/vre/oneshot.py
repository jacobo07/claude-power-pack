"""`oneshot`: analyze -> track -> generate -> render -> judge -> fix, capped at 2-5 rounds.

The reference is measured once. Each round the generator's input spec (a COPY of the reference rows, never the
judge's benchmark) is rendered, the candidate video is measured with the same analyze + track stages, and the frozen
judge scores it. Fixes are mechanical and only touch the generator's copy: a row whose measured start differs from
the reference is shifted by the difference. Things the loop cannot fix mechanically (easing family, missing
objects, wrong cuts, orientation, frame count: the generator already emits the reference's values, so a
difference is a generator or render defect) are reported, not papered over. Every round
logs the delta it targeted and the measured effect on the number of failing row checks.
"""

from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable

from . import generate, judge, media
from .pipeline import analyze
from .track import track

Renderer = Callable[[Path, dict, Path], Path]  # (generated tsx dir, composition data, out mp4) -> mp4


def remotion_renderer(project_dir: str | Path, work: Path, *, scale: float = 1.0) -> Renderer:
    """Render with a Remotion project that has node_modules (e.g. a clone of the target repo). A scratch project is
    created under `work` so nothing is written into the target repo."""
    project_dir = Path(project_dir)

    def render(tsx_dir: Path, data: dict, out: Path) -> Path:
        proj = work / "remotion"
        (proj / "src").mkdir(parents=True, exist_ok=True)
        nm = proj / "node_modules"
        if not nm.exists():
            os.symlink(project_dir / "node_modules", nm)
        for name in ("package.json", "tsconfig.json", "remotion.config.ts"):
            if (project_dir / name).exists():
                shutil.copy2(project_dir / name, proj / name)
        shutil.copy2(tsx_dir / "VreComposition.tsx", proj / "src" / "VreComposition.tsx")
        (proj / "src" / "index.ts").write_text(
            "import {registerRoot} from 'remotion';\nimport {VreRoot} from './VreRoot';\nregisterRoot(VreRoot);\n")
        (proj / "src" / "VreRoot.tsx").write_text(
            "import React from 'react';\nimport {Composition} from 'remotion';\n"
            "import {VRE, VreComposition} from './VreComposition';\n"
            "export const VreRoot: React.FC = () => (\n"
            "  <Composition id=\"Vre\" component={VreComposition} width={VRE.width} height={VRE.height}\n"
            "    fps={VRE.fps} durationInFrames={VRE.frames} />\n);\n")
        cmd = ["npx", "remotion", "render", "src/index.ts", "Vre", str(out.resolve()), f"--scale={scale}"]
        proc = subprocess.run(cmd, cwd=proj, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"remotion render failed: {(proc.stderr or proc.stdout)[-800:]}")
        return out

    return render


def _fail_count(v: dict) -> int:
    d = v["dimensions"]
    return (len(d["row_timing"].get("off", [])) + len(d["row_easing"].get("off", []))
            + d["missing_objects"].get("count", 0) + len(d["cuts"].get("missing", []))
            + len(d["cuts"].get("extra", [])) + d["blank_frames"].get("count", 0))


def corrections(verdict: dict, gen_rows: list[dict]) -> list[dict]:
    """Mechanical fixes from the row timing dimension. Returns the log entries; mutates `gen_rows` in place."""
    log = []
    dims = verdict["dimensions"]
    for off in dims["row_timing"].get("off", []):
        delta = off["ref"] - off["cand"]
        for r in gen_rows:
            if r["element"] == off["element"] and r["property"] == off["property"] and r["_ref_start"] == off["ref"]:
                r["start"] = int(r["start"]) + int(delta)  # may go negative: the runtime clamps to its first value
                log.append({"fix": "shift_start", "element": off["element"], "property": off["property"],
                            "delta_frames": int(delta)})
    return log


def oneshot(video: str, out_dir: str, *, brand: str | None = None, copy_file: str | None = None,
            renderer: Renderer, tolerances: str, rounds: int = 3, width: int = 360, detector=None,
            provider=None, text_on: bool = True, rebrand: bool = False, flow_on: bool = False) -> dict:
    """Run the loop. `rounds` is clamped to 2..5. Returns the report (also written to delta_report.json)."""
    rounds = max(2, min(5, rounds))
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    tol = judge.load_tolerances(tolerances)
    ref_dir = out / "reference"
    analyze(video, str(ref_dir), width=144)
    track(str(ref_dir), width=width, detector=detector, provider=provider, text_on=text_on, flow_on=flow_on)
    ref_spec = json.loads((ref_dir / "spec.json").read_text(encoding="utf-8"))
    ref_probe, ref_gray = judge.gray_frames(video, 96)
    gen_dir = out / "gen_spec"
    gen_dir.mkdir(exist_ok=True)
    gen_spec = copy.deepcopy(ref_spec)
    for r in gen_spec["rows"]:
        r["_ref_start"] = r["start"]
    history, final = [], None
    for k in range(1, rounds + 1):
        rd = out / f"round{k}"
        rd.mkdir(exist_ok=True)
        (gen_dir / "spec.json").write_text(json.dumps(gen_spec, ensure_ascii=False), encoding="utf-8")
        generate.generate(str(gen_dir), str(rd / "tsx"), brand=brand, copy=copy_file)
        data, _ = generate.build(gen_spec, json.loads(Path(brand).read_text()) if brand else None,
                                 json.loads(Path(copy_file).read_text()) if copy_file else {})
        cand = renderer(rd / "tsx", data, rd / "candidate.mp4")
        cand_dir = rd / "measure"
        analyze(str(cand), str(cand_dir), width=144, words=False, beats=False)
        track(str(cand_dir), width=width, detector=detector, provider=provider, text_on=text_on, flow_on=flow_on)
        cand_spec = json.loads((cand_dir / "spec.json").read_text(encoding="utf-8"))
        _, cand_gray = judge.gray_frames(str(cand), 96)
        verdict = judge.judge(ref_spec, cand_spec, ref_gray, cand_gray, tol, rebrand=rebrand)
        (rd / "verdict.json").write_text(json.dumps(verdict, indent=2), encoding="utf-8")
        entry = {"round": k, "level": verdict["level"], "critical": verdict["critical_failures"],
                 "fail_count": _fail_count(verdict), "targeted": [], "effect": None}
        if history:
            prev = history[-1]
            prev["effect"] = {"fail_count_before": prev["fail_count"], "fail_count_after": entry["fail_count"]}
        history.append(entry)
        final = verdict
        if verdict["level"] != "FAIL":
            break
        log = corrections(verdict, gen_spec["rows"])
        entry["targeted"] = log
        if not log:  # nothing the loop can fix mechanically: stop and report instead of spinning
            break
    report = {"video_frames": ref_probe.packets, "rounds_run": len(history), "cap": rounds, "history": history,
              "final_level": final["level"] if final else None, "critical_failures": final["critical_failures"],
              "unmeasured": final["unmeasured"], "tolerances_sha256": tol["frozen"]["sha256"],
              "claim": final["claim"] if final else None}
    (out / "delta_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def side_by_side(reference: str, candidate: str, out: str, height: int = 640) -> Path:
    """Reference | candidate in one video, display orientation, for the person who reviews the delta."""
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", reference, "-i", candidate, "-filter_complex",
           f"[0:v]scale=-2:{height}[a];[1:v]scale=-2:{height}[b];[a][b]hstack=inputs=2", "-an",
           "-c:v", "libx264", "-crf", "23", "-pix_fmt", "yuv420p", out]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise media.MediaError(f"ffmpeg side-by-side failed: {proc.stderr[-400:]}")
    return Path(out)
