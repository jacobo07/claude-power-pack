"""Session-revival regression gates (PP, sealed 2026-07-19).

Contract: docs/prd/SESSION_REVIVAL_CONTRACT.md
Spec:     docs/specs/REVIVAL_PIPELINE_SPEC.md

Guards the invariants behind "revival opens a new empty session instead of
resuming". Every gate below encodes a defect that was REAL and MEASURED on
2026-07-19, not a hypothetical.

Hermetic: all task/beacon fixtures live in tempfile.mkdtemp(). The only reads
of real state are (a) the source files being asserted about and (b) Cursor's
settings.json for V-SETTINGS-REQUIRED, which is a read-only tripwire against a
Cursor update silently resetting revival config.

    python tools/test_session_revival.py     # exit 0 = all gates pass
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.cpc_os import vscode_autorun as va  # noqa: E402

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  [OK]   {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  [FAIL] {gate}: {diagnostic}")


# ---------------------------------------------------------------------------
# V-REVIVAL-PID-NOT-OPENPROCESS
#   OpenProcess alone succeeds on a TERMINATED process (its handle-table entry
#   survives until all handles close). Measured: an OpenProcess-only helper
#   reported 14 live panes where Get-Process saw 12; both extras were exited.
#   Those corpses would have passed the liveness gate -- the exact sessions it
#   exists to reject. _pid_alive must use a real exit-signalled wait.
# ---------------------------------------------------------------------------
def test_pid_not_openprocess() -> None:
    gate = "V-REVIVAL-PID-NOT-OPENPROCESS"
    if not va._pid_alive(os.getpid()):
        _fail(gate, "own PID reported NOT alive")
        return
    # A process that has definitely exited. Spawn + reap, then assert dead.
    proc = subprocess.Popen([sys.executable, "-c", "pass"])
    proc.wait()
    dead_pid = proc.pid
    if va._pid_alive(dead_pid):
        _fail(gate, f"exited pid {dead_pid} reported alive "
                    "(OpenProcess-style false positive -- corpses would pass)")
        return
    if va._pid_alive(0) or va._pid_alive(-1):
        _fail(gate, "non-positive pid reported alive")
        return
    _ok(gate, f"own pid alive; reaped pid {dead_pid} correctly dead; pid<=0 dead")


# ---------------------------------------------------------------------------
# V-REVIVAL-LIVENESS-IS-PROCESS
#   Open-ness is a process fact, never recency (Owner: "lo que dure Cursor es lo
#   que dura una sesion de los panes que quiero recuperar"). A pane idle for
#   days but ALIVE must be kept; a stale-status pane with a dead PID must go.
# ---------------------------------------------------------------------------
def test_liveness_is_process() -> None:
    gate = "V-REVIVAL-LIVENESS-IS-PROCESS"
    tmp = Path(tempfile.mkdtemp(prefix="pp-revival-"))
    repo = str(tmp / "repo")
    os.makedirs(repo, exist_ok=True)

    live_sid = "11111111-1111-1111-1111-111111111111"
    dead_sid = "22222222-2222-2222-2222-222222222222"
    snap = tmp / "session_snapshot.json"
    snap.write_text(json.dumps([
        # idle for days, but its process is alive -> MUST be kept
        {"cwd": repo, "session_id": live_sid, "status": "stale",
         "resume": f"claude --resume {live_sid}", "repo": "repo",
         "topic": "idle but open"},
        # abandoned, no live process -> MUST be dropped
        {"cwd": repo, "session_id": dead_sid, "status": "stale",
         "resume": f"claude --resume {dead_sid}", "repo": "repo",
         "topic": "corpse"},
    ]), encoding="utf-8")

    res = va.generate_from_snapshot(
        snap, cwds=[repo], dry_run=True, truncate=False,
        keep_sids={live_sid},            # stands in for a verified-live pane
    )
    sids = {t["args"][1] for t in res[0]["doc"]["tasks"]
            if len(t.get("args") or []) > 1}
    if live_sid not in sids:
        _fail(gate, "live pane dropped -- idle-but-open pane would be lost")
        return
    if dead_sid in sids:
        _fail(gate, "corpse kept -- would relaunch a dead session on folderOpen")
        return
    _ok(gate, "live pane kept at any idle age; dead-PID pane dropped")


# ---------------------------------------------------------------------------
# V-REVIVAL-OWN-SESSION-PINNED
#   The live session is routinely marked "stale" and may have NO beacon.
#   Measured 2026-07-19: sid aa863758 was live, stale-marked and beaconless -- a
#   beacon-only gate dropped the pane the Owner was typing in. That IS the
#   reported bug, not a fix for it.
# ---------------------------------------------------------------------------
def test_own_session_pinned() -> None:
    gate = "V-REVIVAL-OWN-SESSION-PINNED"
    tmp = Path(tempfile.mkdtemp(prefix="pp-revival-"))
    repo = str(tmp / "repo")
    os.makedirs(repo, exist_ok=True)
    own = "33333333-3333-3333-3333-333333333333"
    snap = tmp / "session_snapshot.json"
    snap.write_text(json.dumps([
        {"cwd": repo, "session_id": own, "status": "stale",
         "resume": f"claude --resume {own}", "repo": "repo", "topic": "current"},
    ]), encoding="utf-8")

    res = va.generate_from_snapshot(snap, cwds=[repo], dry_run=True,
                                    truncate=False, keep_sids={own})
    sids = {t["args"][1] for t in res[0]["doc"]["tasks"]
            if len(t.get("args") or []) > 1}
    if own not in sids:
        _fail(gate, "own sid dropped despite keep_sids -- the active pane "
                    "would not be restored")
        return

    # And the hub must actually PASS keep_sids, or the guard is dead code.
    hub = (_PP_ROOT / "hooks" / "session_start_hub.js").read_text(encoding="utf-8")
    m = re.search(r"generate_from_snapshot\((.{0,400}?)\)\\n", hub, re.S)
    call = m.group(1) if m else ""
    if "keep_sids" not in call:
        _fail(gate, "SessionStart hub does not pass keep_sids to "
                    "generate_from_snapshot -- guard is unreachable in production")
        return
    _ok(gate, "own sid survives the gate; hub passes keep_sids")


# ---------------------------------------------------------------------------
# V-REVIVAL-FAIL-OPEN
#   Unmeasurable liveness must NOT filter. Losing a pane is worse than keeping
#   a stale one (invariant I7).
# ---------------------------------------------------------------------------
def test_fail_open() -> None:
    gate = "V-REVIVAL-FAIL-OPEN"
    tmp = Path(tempfile.mkdtemp(prefix="pp-revival-"))
    repo = str(tmp / "repo")
    os.makedirs(repo, exist_ok=True)
    sid = "44444444-4444-4444-4444-444444444444"
    snap = tmp / "session_snapshot.json"
    snap.write_text(json.dumps([
        {"cwd": repo, "session_id": sid, "status": "stale",
         "resume": f"claude --resume {sid}", "repo": "repo", "topic": "x"},
    ]), encoding="utf-8")

    original = va.live_beacon_sids
    try:
        va.live_beacon_sids = lambda: set()          # simulate no measurement
        res = va.generate_from_snapshot(snap, cwds=[repo], dry_run=True,
                                        truncate=False)
    finally:
        va.live_beacon_sids = original
    sids = {t["args"][1] for t in res[0]["doc"]["tasks"]
            if len(t.get("args") or []) > 1}
    if sid not in sids:
        _ok_msg = None
        _fail(gate, "pane filtered out when liveness was unmeasurable "
                    "(fail-CLOSED: panes would vanish if %TEMP% were cleared)")
        return
    _ok(gate, "no measurable beacons -> no filtering (fail-open preserved)")


# ---------------------------------------------------------------------------
# V-REVIVAL-NO-DUPLICATE-FOLDEROPEN
#   Cursor fires EVERY folderOpen task. Two tasks for one session = two tabs.
# ---------------------------------------------------------------------------
def test_no_duplicate_folderopen() -> None:
    gate = "V-REVIVAL-NO-DUPLICATE-FOLDEROPEN"
    sid = "55555555-5555-5555-5555-555555555555"
    panes = [
        {"cwd": "/r", "session_id": sid, "resume": f"claude --resume {sid}",
         "repo": "r", "topic": "one"},
        {"cwd": "/r", "session_id": sid, "resume": f"claude --resume {sid}",
         "repo": "r", "topic": "same session, second pane row"},
    ]
    tasks = va.build_cpc_tasks(panes)
    if len(tasks) != 1:
        _fail(gate, f"{len(tasks)} tasks for one session (expected 1)")
        return
    if sum(1 for t in tasks if t.get("runOptions", {}).get("runOn") == "folderOpen") != 1:
        _fail(gate, "task is not a single folderOpen task")
        return
    _ok(gate, "duplicate pane rows for one session collapse to 1 folderOpen task")


# ---------------------------------------------------------------------------
# V-REVIVAL-NO-SILENT-NEW
#   A pane with no resolvable --resume must emit NO task rather than a bare
#   `claude` (which opens an empty session the Owner reads as a lost pane).
# ---------------------------------------------------------------------------
def test_no_silent_new() -> None:
    gate = "V-REVIVAL-NO-SILENT-NEW"
    panes = [{"cwd": "/r", "session_id": None, "resume": 'cd "/r" && claude',
              "repo": "r", "topic": "empty shell"}]
    tasks = va.build_cpc_tasks(panes)
    if tasks:
        _fail(gate, f"emitted {len(tasks)} task(s) for a non-resumable pane "
                    "-- would open a fresh empty session")
        return
    _ok(gate, "non-resumable pane emits no task (no silent new session)")


# ---------------------------------------------------------------------------
# V-REVIVAL-WRITERS-AGREE
#   Both tasks.json writers must share ONE liveness definition. They did not,
#   and merge_tasks replaces all CPC tasks, so the result depended on which
#   writer ran last -- the mechanical source of the inconsistency.
# ---------------------------------------------------------------------------
def test_writers_agree() -> None:
    gate = "V-REVIVAL-WRITERS-AGREE"
    ps = (_PP_ROOT / "tools" / "build_pane_map.ps1").read_text(encoding="utf-8")
    if "kclaude-pane-*.sid" not in ps:
        _fail(gate, "build_pane_map.ps1 does not read kclaude beacons")
        return
    if "$liveSids" not in ps or "$isLivePane" not in ps:
        _fail(gate, "build_pane_map.ps1 does not gate OPEN-NOW on live beacons")
        return
    if re.search(r"if \(\$inSnap -or", ps):
        _fail(gate, "build_pane_map.ps1 still forces OPEN-NOW from snapshot "
                    "membership -- the non-falsifiable proxy is back")
        return
    src = (_PP_ROOT / "modules" / "cpc_os" / "vscode_autorun.py").read_text(encoding="utf-8")
    if "kclaude-pane-*.sid" not in src:
        _fail(gate, "vscode_autorun.py does not read the same beacons")
        return
    if "WaitForSingleObject" not in src:
        _fail(gate, "python liveness lacks the exit-signalled wait "
                    "(OpenProcess-only would admit corpses)")
        return
    _ok(gate, "both writers gate on live kclaude beacons; snapshot-membership "
              "override removed")


# ---------------------------------------------------------------------------
# V-SETTINGS-REQUIRED
#   Tripwire for T-CURSOR-UPDATE-RESETS-AUTOTASKS-001: an update can reset these
#   silently and revival dies with no error. Read-only; skipped off-Windows.
# ---------------------------------------------------------------------------
def _strip_jsonc(raw: str) -> str:
    out, i, n, in_str = [], 0, len(raw), False
    while i < n:
        c = raw[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(raw[i + 1])
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            out.append(c)
            i += 1
            continue
        if c == "/" and i + 1 < n and raw[i + 1] == "/":
            while i < n and raw[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and raw[i + 1] == "*":
            i += 2
            while i + 1 < n and not (raw[i] == "*" and raw[i + 1] == "/"):
                i += 1
            i += 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def test_settings_required() -> None:
    gate = "V-SETTINGS-REQUIRED"
    appdata = os.environ.get("APPDATA")
    if not appdata:
        _ok(gate, "skipped (no APPDATA -- not a Windows Cursor host)")
        return
    p = Path(appdata) / "Cursor" / "User" / "settings.json"
    if not p.is_file():
        _ok(gate, f"skipped (no settings.json at {p})")
        return
    try:
        cfg = json.loads(_strip_jsonc(p.read_text(encoding="utf-8-sig")))
    except ValueError as e:
        _fail(gate, f"settings.json does not parse as JSONC: {e}")
        return

    want = {
        "task.allowAutomaticTasks": "on",
        "terminal.integrated.persistentSessionReviveProcess": "never",
        "terminal.integrated.enablePersistentSessions": True,
        "window.restoreWindows": "all",
    }
    bad = [f"{k}={cfg.get(k, '<ABSENT>')!r} (want {v!r})"
           for k, v in want.items() if cfg.get(k) != v]
    # Not a real Cursor setting: 0 occurrences in workbench.desktop.main.js.
    # Inert, and it masks persistentSessionReviveProcess as if restore were off.
    if "terminal.integrated.restoreTerminals" in cfg:
        bad.append("terminal.integrated.restoreTerminals present "
                   "(not a real Cursor setting -- inert and misleading)")
    if bad:
        _fail(gate, "; ".join(bad))
        return
    _ok(gate, "allowAutomaticTasks=on, reviveProcess=never, "
              "persistentSessions=true, restoreWindows=all, no restoreTerminals")


def main() -> int:
    print("SESSION REVIVAL GATES")
    print("=" * 60)
    for fn in (test_pid_not_openprocess,
               test_liveness_is_process,
               test_own_session_pinned,
               test_fail_open,
               test_no_duplicate_folderopen,
               test_no_silent_new,
               test_writers_agree,
               test_settings_required):
        try:
            fn()
        except Exception as e:  # noqa: BLE001 - a crashing gate is a failing gate
            _fail(fn.__name__, f"raised {type(e).__name__}: {e}")
    total = _passes + _fails
    print("=" * 60)
    print(f"REVIVAL_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
