#!/usr/bin/env python
"""Worker MCP probe, cross-platform twin of worker_mcp_probe.sh (same predeclared rule, 2026-09-27):
APPLY only if every no-MCP run answers OK AND its median input+cache tokens are >= 5% below the
default's; any default failure -> UNJUDGED; otherwise KEEP. Writes ~/.claude/state/worker-mcp-probe.json,
which gsd_mission.worker_mcp_verdict reads.

Why a twin: the .sh is pinned to ~/cavex on the GEX44 VPS, so a Windows host never had a verdict and
its workers always paid for every MCP server. Measured 2026-11-22 (MG demo, this host): 98,321 tokens
with MCP vs 90,967 without on the first call, ~7.5% of every call a mission worker makes.

Usage: python tools/worker_mcp_probe.py --cwd <trusted project dir> [--runs 3] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PROMPT = "Reply with the single word OK."
SAVING_THRESHOLD = 0.05
RUN_TIMEOUT_S = 180


def out_path() -> Path:
    return Path(os.path.expanduser("~")) / ".claude" / "state" / "worker-mcp-probe.json"


def parse_run(raw: str | None, err: str = "") -> dict:
    """One `claude -p --output-format json` result -> {ok, tokens, ...}. Unreadable is a failed run."""
    try:
        d = json.loads(raw or "")
    except ValueError as exc:
        return {"ok": False, "why": f"unreadable: {exc}; stderr={err[:300]}"}
    u = d.get("usage") or {}
    tok = sum(int(u.get(k) or 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
    ok = (not d.get("is_error")) and str(d.get("result", "")).strip().strip(".").upper() == "OK"
    return {"ok": ok, "tokens": tok, "is_error": d.get("is_error"), "status": d.get("api_error_status"),
            "result": str(d.get("result"))[:80]}


def decide(default: list[dict], no_mcp: list[dict]) -> tuple[str, str]:
    """The predeclared rule, unchanged from the .sh."""
    if not default or not all(r["ok"] for r in default):
        return "UNJUDGED", "a default run failed; nothing to compare against"
    if not no_mcp or not all(r["ok"] for r in no_mcp):
        return "KEEP", "a no-MCP run failed"
    md = statistics.median(r["tokens"] for r in default)
    mn = statistics.median(r["tokens"] for r in no_mcp)
    saving = (md - mn) / md if md else 0.0
    verdict = "APPLY" if saving >= SAVING_THRESHOLD else "KEEP"
    return verdict, f"median default={md} no_mcp={mn} saving={saving:.1%} (threshold {SAVING_THRESHOLD:.0%})"


def run_once(exe: str, cwd: str, strip: bool, empty_cfg: Path) -> dict:
    # `--` ends the variadic --mcp-config, which otherwise reads the prompt as a second config (measured).
    mcp = ["--strict-mcp-config", "--mcp-config", str(empty_cfg)] if strip else []
    argv = [exe, "-p", "--output-format", "json", "--no-session-persistence", *mcp, "--", PROMPT]
    try:
        r = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=RUN_TIMEOUT_S)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "why": f"{type(exc).__name__}: {exc}"[:300]}
    return parse_run(r.stdout, r.stderr or "")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cwd", required=True, help="a trusted project directory to run the probe in")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--dry-run", action="store_true", help="print the verdict, write nothing")
    a = ap.parse_args(argv)
    exe = os.environ.get("CPP_CLAUDE_EXE") or "claude"
    with tempfile.TemporaryDirectory(prefix="mcp-probe-") as tmp:
        empty = Path(tmp) / "empty-mcp.json"
        empty.write_text('{"mcpServers":{}}', encoding="utf-8")
        default, no_mcp = [], []
        for _ in range(max(1, a.runs)):
            default.append(run_once(exe, a.cwd, False, empty))
            no_mcp.append(run_once(exe, a.cwd, True, empty))
    verdict, why = decide(default, no_mcp)
    doc = {"verdict": verdict, "why": why, "measured_at": time.time(), "host": sys.platform, "cwd": a.cwd,
           "rule": "APPLY iff all no-MCP runs OK and median saving >= 5%", "default": default, "no_mcp": no_mcp}
    if not a.dry_run:
        p = out_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        fd, t = tempfile.mkstemp(prefix=".worker-mcp-probe.", suffix=".tmp", dir=p.parent)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(doc, indent=2))
        os.replace(t, p)
    print(verdict, why)
    return 0


if __name__ == "__main__":
    sys.exit(main())
