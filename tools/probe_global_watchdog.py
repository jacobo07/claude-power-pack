#!/usr/bin/env python
"""BL-0046 — Empirical probe: confirm context-watchdog.py snapshots
land in <project>/vault/progress.md (or .claude/progress.md fallback)
when invoked with cwd= a project that is NOT power-pack.

Per memory `feedback_verify_state_before_destructive_ops` we don't trust
recent commit messages — we generate live evidence by feeding the
watchdog a synthetic Stop event + synthetic metrics file and
verifying output on disk in two scratch projects:

  scratch_A/  — has vault/ subdir → expect snapshot in vault/progress.md
  scratch_B/  — bare project      → expect snapshot in .claude/progress.md

Output: vault/audits/probe_global_watchdog.json with PASS/FAIL per case
and the actual progress.md hash before/after to make tampering obvious.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WATCHDOG = ROOT / "modules" / "zero-crash" / "hooks" / "context-watchdog.py"
OUT = ROOT / "vault" / "audits" / "probe_global_watchdog.json"


def _sha256(p: Path) -> str:
    if not p.exists():
        return "<absent>"
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def _write_metrics(session_id: str, used_pct: float) -> Path:
    metrics = {
        "used_pct": used_pct,
        "remaining_percentage": 100 - used_pct,
        "tokens_used": int(200000 * used_pct / 100),
        "tokens_total": 200000,
    }
    p = Path(tempfile.gettempdir()) / f"claude-ctx-{session_id}.json"
    p.write_text(json.dumps(metrics), encoding="utf-8")
    return p


def _run_watchdog(session_id: str, cwd: Path) -> dict:
    event = {
        "session_id": session_id,
        "transcript_path": f"<probe>/{session_id}.jsonl",
        "cwd": str(cwd),
        "stop_hook_active": False,
    }
    proc = subprocess.run(
        [sys.executable, str(WATCHDOG)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        timeout=10,
    )
    try:
        return json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return {"_raw_stdout": proc.stdout, "_stderr": proc.stderr}


def _cleanup_flags(session_id: str) -> None:
    tmp = Path(tempfile.gettempdir())
    for name in (
        f"claude-ctxwd-snap-{session_id}.flag",
        f"claude-ctxwd-adv-{session_id}.flag",
        f"claude-ctx-{session_id}.json",
    ):
        try:
            (tmp / name).unlink(missing_ok=True)
        except Exception:
            pass


def case(name: str, project_dir: Path, has_vault: bool) -> dict:
    if has_vault:
        (project_dir / "vault").mkdir(parents=True, exist_ok=True)
        expected = project_dir / "vault" / "progress.md"
    else:
        expected = project_dir / ".claude" / "progress.md"

    sid_t1 = f"probe-bl46-{name}-t1-{uuid.uuid4().hex[:6]}"
    sid_t2 = f"probe-bl46-{name}-t2-{uuid.uuid4().hex[:6]}"

    pre_hash = _sha256(expected)

    _write_metrics(sid_t1, 65)
    out_t1 = _run_watchdog(sid_t1, project_dir)
    t1_hash = _sha256(expected)
    t1_landed = expected.exists() and t1_hash != pre_hash
    t1_silent = out_t1 == {}

    _write_metrics(sid_t2, 72)
    out_t2 = _run_watchdog(sid_t2, project_dir)
    t2_hash = _sha256(expected)
    t2_landed = expected.exists() and t2_hash != t1_hash
    t2_advisory = (
        isinstance(out_t2, dict)
        and "hookSpecificOutput" in out_t2
        and "additionalContext" in out_t2.get("hookSpecificOutput", {})
        and "CONTEXT THRESHOLD CROSSED" in out_t2["hookSpecificOutput"]["additionalContext"]
    )

    snippet = ""
    if expected.exists():
        body = expected.read_text(encoding="utf-8", errors="replace")
        snippet = body[-400:]

    _cleanup_flags(sid_t1)
    _cleanup_flags(sid_t2)

    return {
        "case": name,
        "project_dir": str(project_dir),
        "has_vault": has_vault,
        "expected_path": str(expected),
        "tier1_landed": t1_landed,
        "tier1_silent_stdout": t1_silent,
        "tier2_landed": t2_landed,
        "tier2_advisory_emitted": t2_advisory,
        "pre_sha256": pre_hash,
        "t1_sha256": t1_hash,
        "t2_sha256": t2_hash,
        "tail_snippet": snippet,
        "pass": all([t1_landed, t1_silent, t2_landed, t2_advisory]),
    }


def main() -> int:
    if not WATCHDOG.exists():
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({"error": f"watchdog not found at {WATCHDOG}"}, indent=2))
        print(f"FAIL: watchdog absent at {WATCHDOG}", file=sys.stderr)
        return 2

    work = Path(tempfile.mkdtemp(prefix="bl46-probe-"))
    try:
        a = work / "scratch_A"
        b = work / "scratch_B"
        a.mkdir()
        b.mkdir()

        results = [
            case("A_with_vault", a, True),
            case("B_bare_project", b, False),
        ]

        verdict = {
            "probe": "BL-0046 / MC-SYS-94 — global watchdog cross-project snapshot",
            "iso_ts": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
            "watchdog_path": str(WATCHDOG),
            "cases": results,
            "all_pass": all(r["pass"] for r in results),
        }
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(verdict, indent=2), encoding="utf-8")
        print(json.dumps({"all_pass": verdict["all_pass"], "out": str(OUT)}))
        return 0 if verdict["all_pass"] else 1
    finally:
        try:
            shutil.rmtree(work, ignore_errors=True)
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
