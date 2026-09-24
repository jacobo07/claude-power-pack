"""Provenance envelope and staleness.

The manifest answers, for one rendered demo: which spec (and its hash), which app
commit, which route and viewport, which capture method and tool versions, the hash
of every captured frame, the time compressions applied, the renderer and encoder,
every output file's hash, and the validation verdict. It records identity at the
moment of capture; nothing is reconstructed later.

Staleness compares a later probe (targets resolved against the live product, no
screenshots) with the manifest: CURRENT, STALE (with reasons), or UNKNOWN when the
probe could not run. UNKNOWN is never reported as CURRENT.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[2]
RENDERER = PP_ROOT / "skills" / "motion-promo" / "scripts" / "render_film.py"
STAGE_ASSET = Path(__file__).with_name("assets") / "stage.template.html"
GEOMETRY_TOLERANCE = 0.08     # target moved by more than 8% of the viewport -> stale


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit(repo: Path | None) -> dict:
    if repo is None:
        return {"commit": None, "state": "UNKNOWN", "reason": "no --app-repo given"}
    git = "git"
    for cand in (r"C:\Program Files\Git\cmd\git.exe",):
        if Path(cand).is_file():
            git = cand
    try:
        head = subprocess.run([git, "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True,
                              timeout=20).stdout.strip()
        dirty = subprocess.run([git, "-C", str(repo), "status", "--porcelain"], capture_output=True, text=True,
                               timeout=60).stdout.strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"commit": None, "state": "UNKNOWN", "reason": f"git failed: {exc}"}
    if not head:
        return {"commit": None, "state": "UNKNOWN", "reason": f"{repo} is not a git checkout"}
    return {"commit": head, "state": "DIRTY" if dirty else "CLEAN",
            "dirty_paths": len(dirty.splitlines()) if dirty else 0}


def tool_versions() -> dict:
    out = {}
    try:
        import importlib.metadata as md
        out["playwright"] = md.version("playwright")
        out["imageio-ffmpeg"] = md.version("imageio-ffmpeg")
    except Exception as exc:
        out["error"] = str(exc)
    try:
        from modules.product_demo.validate import ffmpeg_exe
        first = subprocess.run([ffmpeg_exe(), "-version"], capture_output=True, text=True,
                               timeout=20).stdout.splitlines()[:1]
        out["ffmpeg"] = first[0] if first else None
    except Exception as exc:
        out["ffmpeg_error"] = str(exc)
    return out


def build(*, spec, viewport: str, capture_dir: Path, telemetry: dict, timeline: dict, outputs: dict,
          verdict: dict, app_repo: Path | None, revisions: list) -> dict:
    frames = [fr for s in telemetry["steps"] for fr in s["frames"]]
    frameset = hashlib.sha256("".join(f["sha256"] for f in frames).encode()).hexdigest()
    return {
        "schema": "product-demo-manifest/1",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "spec": {"id": spec.id, "sha256": spec.sha256,
                 "path": str(spec.source_path) if spec.source_path else None},
        "app": {"base_url": spec.base_url, **git_commit(app_repo)},
        "viewport": viewport,
        "capture": {"method": "settled-state screenshots, CSS animations disabled",
                    "started_utc": telemetry.get("started_utc"), "ended_utc": telemetry.get("ended_utc"),
                    "frames": len(frames), "frameset_sha256": frameset,
                    "network_idle_timeouts": telemetry.get("network_idle_timeouts"),
                    "targets": [{"step": s["id"], **s["target"]} for s in telemetry["steps"] if s.get("target")]},
        "presentation": {"duration_ms": timeline["duration_ms"], "compressions": timeline["compressions"],
                         "callouts": [{"n": c["n"], "step": c["step"], "text": c["text"]}
                                      for c in timeline["callouts"]],
                         "revisions": revisions,
                         "overlay_provenance": "cursor, click emphasis, callouts and device frame are "
                                               "presentation; product pixels are captured screenshots"},
        "toolchain": {**tool_versions(), "renderer_sha256": sha256_file(RENDERER),
                      "stage_sha256": sha256_file(STAGE_ASSET)},
        "licensing": "clean-room; no third-party code or assets in the composition",
        "outputs": {k: {"file": Path(p).name, "sha256": sha256_file(Path(p)), "bytes": Path(p).stat().st_size}
                    for k, p in outputs.items()},
        "validation": verdict,
    }


def staleness(manifest: dict, probe: dict) -> dict:
    """Compare a live probe with the manifest's capture. Never guesses CURRENT."""
    reasons: list = []
    if probe.get("outcome") != "ok":
        ref = probe.get("refusal") or {}
        if ref.get("code") in ("BLOCKED_ENV",) or probe.get("outcome") is None:
            return {"state": "UNKNOWN", "reasons": [f"probe could not run: {ref}"]}
        return {"state": "STALE", "reasons": [f"the demo's path no longer runs: {ref.get('code')} "
                                              f"{ref.get('detail')}"]}
    if probe.get("spec_sha256") != manifest["spec"]["sha256"]:
        reasons.append("the spec changed since this demo was rendered")
    vp = probe["viewport"]
    live = {s["id"]: s.get("target") for s in probe["steps"] if s.get("target")}
    for t in manifest["capture"]["targets"]:
        now = live.get(t["step"])
        if now is None:
            reasons.append(f"step {t['step']}: target no longer resolved")
            continue
        if now["text_sha256"] != t["text_sha256"]:
            reasons.append(f"step {t['step']}: target text changed")
        b0, b1 = t["box"], now["box"]
        dx = abs(b0["x"] - b1["x"]) / vp["width"]
        dy = abs(b0["y"] - b1["y"]) / vp["height"]
        dw = abs(b0["width"] - b1["width"]) / vp["width"]
        if max(dx, dy, dw) > GEOMETRY_TOLERANCE:
            reasons.append(f"step {t['step']}: target moved/resized by {max(dx, dy, dw):.0%} of the viewport")
    return {"state": "STALE" if reasons else "CURRENT", "reasons": reasons}


def write(manifest: dict, path: Path) -> None:
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
