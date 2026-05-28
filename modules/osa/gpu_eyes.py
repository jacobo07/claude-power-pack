"""OSA GPU Eyes (CaptureBot) — visual QA over SSH+Xvfb+scrot.

GRACEFUL DEGRADATION FIRST. The single most important rule of
this module is the Reality Contract:

  visual_qa_passed is None when no capture was taken.
  NEVER True/False without an actual screenshot path that exists.

If the GPU host is unreachable, the SSH call times out, or scrot
returns a non-zero exit, the result reports status="SKIPPED" or
"CAPTURE_FAILED" and visual_qa_passed=None. Callers MUST NOT
interpret None as PASS.

Config from vault/osa/config.json (gpu_eyes section). Defaults
target the documented gex44 host but everything is overridable.

Sealed 2026-05-28.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PP_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PP_ROOT / "vault" / "osa" / "config.json"

DEFAULT_GPU = {
    "host": "5.9.23.174",
    "ssh_user": "root",
    "ssh_timeout_sec": 5,
    "display": ":98",
    "screen_geometry": "1920x1080x24",
    "graceful_degradation": True,
}


def _load_gpu_config() -> dict:
    if not CONFIG_PATH.is_file():
        return dict(DEFAULT_GPU)
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return dict(DEFAULT_GPU)
    section = data.get("gpu_eyes") if isinstance(data, dict) else None
    if not isinstance(section, dict):
        return dict(DEFAULT_GPU)
    merged = dict(DEFAULT_GPU)
    merged.update({k: v for k, v in section.items() if k in DEFAULT_GPU})
    return merged


def _ssh_path() -> str | None:
    return shutil.which("ssh")


def _ssh_target(cfg: dict) -> str:
    return f"{cfg['ssh_user']}@{cfg['host']}"


def check_availability(cfg: dict | None = None) -> str:
    """Returns one of: GPU_AVAILABLE | GPU_NOT_REACHABLE | GPU_TIMEOUT | NO_SSH."""
    cfg = cfg or _load_gpu_config()
    ssh = _ssh_path()
    if ssh is None:
        return "NO_SSH"
    timeout = int(cfg.get("ssh_timeout_sec", 5))
    try:
        r = subprocess.run(
            [ssh,
             "-o", f"ConnectTimeout={timeout}",
             "-o", "BatchMode=yes",
             "-o", "StrictHostKeyChecking=accept-new",
             _ssh_target(cfg), "echo GPU_REACHABLE"],
            capture_output=True, text=True, timeout=timeout + 2,
        )
    except subprocess.TimeoutExpired:
        return "GPU_TIMEOUT"
    except (OSError, ValueError):
        return "GPU_NOT_REACHABLE"
    if r.returncode == 0 and "GPU_REACHABLE" in (r.stdout or ""):
        return "GPU_AVAILABLE"
    return "GPU_NOT_REACHABLE"


def _ensure_xvfb_remote(cfg: dict) -> bool:
    """Best-effort: start Xvfb on the remote display if not running.

    Returns True if Xvfb is reachable post-call, False on any failure.
    A failure here just degrades capture_screenshot() to None, never
    raises, never blocks.
    """
    ssh = _ssh_path()
    if ssh is None:
        return False
    display = cfg.get("display", ":98")
    geom = cfg.get("screen_geometry", "1920x1080x24")
    cmd = (
        f"pgrep -fa 'Xvfb {display}' >/dev/null 2>&1 || "
        f"nohup Xvfb {display} -screen 0 {geom} >/dev/null 2>&1 &"
    )
    try:
        subprocess.run(
            [ssh, "-o", "BatchMode=yes", _ssh_target(cfg), cmd],
            capture_output=True, text=True, timeout=10,
        )
        return True
    except (subprocess.TimeoutExpired, OSError):
        return False


def capture_screenshot(
    output_local: str | Path = "/tmp/osa_capture.png",
    cfg: dict | None = None,
) -> str | None:
    """SSH -> ensure Xvfb -> scrot -> scp. Returns local path or None."""
    cfg = cfg or _load_gpu_config()
    ssh = _ssh_path()
    scp = shutil.which("scp")
    if ssh is None or scp is None:
        return None
    display = cfg.get("display", ":98")
    remote_path = "/tmp/osa_capture.png"
    if not _ensure_xvfb_remote(cfg):
        return None
    capture_cmd = (
        f"DISPLAY={display} scrot -o {remote_path} 2>/dev/null"
    )
    try:
        cap = subprocess.run(
            [ssh, "-o", "BatchMode=yes", _ssh_target(cfg), capture_cmd],
            capture_output=True, text=True, timeout=15,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if cap.returncode != 0:
        return None
    out_path = Path(str(output_local))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        cp = subprocess.run(
            [scp, "-o", "BatchMode=yes",
             f"{_ssh_target(cfg)}:{remote_path}", str(out_path)],
            capture_output=True, text=True, timeout=15,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if cp.returncode != 0 or not out_path.is_file() or out_path.stat().st_size == 0:
        return None
    return str(out_path)


def run_visual_qa(
    project: str,
    intent: str | None = None,
    cfg: dict | None = None,
) -> dict:
    """Top-level entry point. Always returns a dict, never raises.

    Reality Contract: visual_qa_passed is None unless a real
    screenshot path exists. SKIPPED and CAPTURE_FAILED both
    return None -- callers must NOT treat that as PASS.
    """
    cfg = cfg or _load_gpu_config()
    iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z")
    avail = check_availability(cfg)
    if avail != "GPU_AVAILABLE":
        return {
            "status": "SKIPPED",
            "reason": avail,
            "visual_qa_passed": None,
            "screenshot": None,
            "project": project,
            "intent": intent,
            "iso": iso,
            "note": (
                "Visual QA NOT executed -- GPU host unreachable. "
                "Do not report as PASS. Text-only audit is the "
                "fallback path."
            ),
        }
    shot = capture_screenshot(cfg=cfg)
    if shot is None:
        return {
            "status": "CAPTURE_FAILED",
            "reason": "ssh reachable but Xvfb/scrot/scp produced no file",
            "visual_qa_passed": None,
            "screenshot": None,
            "project": project,
            "intent": intent,
            "iso": iso,
            "note": "Do not report as PASS.",
        }
    return {
        "status": "CAPTURED",
        "visual_qa_passed": None,
        "screenshot": shot,
        "project": project,
        "intent": intent,
        "iso": iso,
        "note": (
            "Screenshot captured. Manual review required for V1. "
            "Automated vision analysis is V2 roadmap."
        ),
    }


def _main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="OSA GPU Eyes (CaptureBot)")
    ap.add_argument("--check", action="store_true",
                    help="Probe GPU availability only")
    ap.add_argument("--project", default="unknown")
    ap.add_argument("--intent", default=None)
    args = ap.parse_args(argv)
    if args.check:
        print(check_availability())
        return 0
    print(json.dumps(run_visual_qa(args.project, args.intent), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
