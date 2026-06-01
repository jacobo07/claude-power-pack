#!/usr/bin/env python3
"""V-SPRINT1-* gates for the manual-tools -> PP automation wiring.

Empirical: actually runs the hub + Stop hooks via node, deletes then asserts
regeneration of health evidence, dry-runs the daemon installer, and queries the
live Task Scheduler. Reality Contract -- evidence is the run, not the prose.

    python tools/test_manual_tools_automation.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

PP = Path(__file__).resolve().parent.parent
PY = sys.executable
HUB = PP / "hooks" / "session_start_hub.js"
HEALTH = PP / "vault" / "health"

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"OK   {gate}  {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    print(f"FAIL {gate}  {diag}")


def _node(script: Path, timeout: int = 20) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["node", str(script)], input="{}",
                          capture_output=True, text=True, timeout=timeout,
                          cwd=str(PP))


def gate_hub_functions() -> None:
    src = HUB.read_text(encoding="utf-8", errors="ignore")
    need = ["detachedSpawnLogged", "hookCompoundAudit", "hookDriftReport"]
    missing = [n for n in need if n not in src]
    if missing:
        _fail("V-SPRINT1-HUB-FUNCTIONS", f"missing {missing}")
    else:
        _ok("V-SPRINT1-HUB-FUNCTIONS", "all 3 present")


def gate_hub_calls() -> None:
    src = HUB.read_text(encoding="utf-8", errors="ignore")
    # both must be invoked inside main() (after the function defs)
    if "hookCompoundAudit();" in src and "hookDriftReport();" in src:
        _ok("V-SPRINT1-HUB-CALLS", "both wired into main()")
    else:
        _fail("V-SPRINT1-HUB-CALLS", "call site(s) absent")


def gate_hub_runs() -> None:
    # delete evidence, run hub, assert regeneration -> proves THIS run produced it
    ca = HEALTH / "compound_audit.last.txt"
    dr = HEALTH / "drift_report.last.txt"
    for f in (ca, dr):
        try:
            f.unlink()
        except FileNotFoundError:
            pass
    try:
        r = _node(HUB)
    except Exception as e:  # noqa: BLE001
        _fail("V-SPRINT1-HUB-RUNS", f"node error {e}")
        return
    try:
        payload = json.loads(r.stdout.strip())
    except ValueError:
        _fail("V-SPRINT1-HUB-RUNS", f"stdout not JSON: {r.stdout!r}")
        return
    if not payload.get("continue"):
        _fail("V-SPRINT1-HUB-RUNS", f"continue!=true: {payload}")
        return
    # detached children need a moment to flush -- require NON-EMPTY content,
    # not mere existence (openSync creates a 0B file before the tool writes)
    def _both_nonempty() -> bool:
        return (ca.exists() and ca.stat().st_size > 0
                and dr.exists() and dr.stat().st_size > 0)

    for _ in range(40):
        if _both_nonempty():
            break
        time.sleep(0.1)
    if _both_nonempty():
        _ok("V-SPRINT1-HUB-RUNS",
            f"hub JSON ok + health regenerated ({ca.stat().st_size}+"
            f"{dr.stat().st_size}B)")
    else:
        _fail("V-SPRINT1-HUB-RUNS",
              f"health empty/missing ca={ca.stat().st_size if ca.exists() else 'x'}"
              f" dr={dr.stat().st_size if dr.exists() else 'x'}")


def gate_stop_hook(name: str, gate: str) -> None:
    script = PP / "hooks" / name
    if not script.is_file():
        _fail(gate, f"missing {name}")
        return
    try:
        r = _node(script)
    except Exception as e:  # noqa: BLE001
        _fail(gate, f"node error {e}")
        return
    if r.returncode == 0:
        _ok(gate, f"{name} exit 0")
    else:
        _fail(gate, f"{name} exit {r.returncode}")


def gate_daemons_dryrun() -> None:
    try:
        r = subprocess.run(
            [PY, str(PP / "tools" / "install_sprint1_daemons.py"), "--dry-run"],
            capture_output=True, text=True, timeout=30, cwd=str(PP))
    except Exception as e:  # noqa: BLE001
        _fail("V-SPRINT1-DAEMONS-DRYRUN", f"error {e}")
        return
    if r.returncode == 0 and r.stdout.count("[DRYRUN]") == 4:
        _ok("V-SPRINT1-DAEMONS-DRYRUN", "4 daemons previewed, rc 0")
    else:
        _fail("V-SPRINT1-DAEMONS-DRYRUN",
              f"rc={r.returncode} previews={r.stdout.count('[DRYRUN]')}")


def gate_daemons_registered() -> None:
    ps = ("Get-ScheduledTask -TaskName 'PP-*' -ErrorAction SilentlyContinue | "
          "Measure-Object | Select-Object -ExpandProperty Count")
    try:
        r = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps],
            capture_output=True, text=True, timeout=20)
    except Exception as e:  # noqa: BLE001
        _fail("V-SPRINT1-DAEMONS-REGISTERED", f"error {e}")
        return
    try:
        count = int((r.stdout or "0").strip() or "0")
    except ValueError:
        _fail("V-SPRINT1-DAEMONS-REGISTERED", f"non-int {r.stdout!r}")
        return
    if count >= 4:
        _ok("V-SPRINT1-DAEMONS-REGISTERED", f"{count} PP-* tasks Ready")
    else:
        _fail("V-SPRINT1-DAEMONS-REGISTERED", f"only {count} tasks")


def gate_file(gate: str, rel: str, needle: str) -> None:
    f = PP / rel
    if f.is_file() and needle in f.read_text(encoding="utf-8", errors="ignore"):
        _ok(gate, rel)
    else:
        _fail(gate, f"{rel} missing or lacks {needle!r}")


def main() -> int:
    print("=== V-SPRINT1-* manual-tools automation gates ===")
    gate_hub_functions()
    gate_hub_calls()
    gate_hub_runs()
    gate_stop_hook("jit_correlate_stop.js", "V-SPRINT1-STOP-JIT")
    gate_stop_hook("session_snapshot_stop.js", "V-SPRINT1-STOP-SNAPSHOT")
    gate_daemons_dryrun()
    gate_daemons_registered()
    gate_file("V-SPRINT1-AGENT-SPEC",
              "vault/agents_specs/pp-token-auditor.md", "name: pp-token-auditor")
    gate_file("V-SPRINT1-OWNER-DOC",
              "vault/automation/sprint1_owner_registration.md", "Stop hooks")
    total = _passes + _fails
    print(f"\nSPRINT1_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
