#!/usr/bin/env python
"""V-CWIRE-* -- every automated keystroke the watchdog causes goes through one door.

Spec: vault/specs/exact-target-continuation.md (C4).

Drives the REAL `_dispatch_continuation`, the REAL `_route_for`, the real
watchdog `run()` and the real stall sweep. Only process-spawning edges are
recorded: the Orca transport's `spawn_delivery`, and the daemon flag+spawn pair
that feeds the terminal inbox. Two exact providers, never a focused window:

  * Orca-hosted session (ORCA_PANE_KEY)  -> continuation_transport
  * anything else                        -> terminal inbox via the daemon, which
                                            refuses by default when no extension
                                            owns the terminal (daemon suite).
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import time
import uuid
from pathlib import Path

os.environ["GSD_LONG_RUN_STATE_DIR"] = tempfile.mkdtemp(prefix="cwire-state-")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = tempfile.mkdtemp(prefix="cwire-proj-")
# The sweep ends by spawning the REAL SendKeys daemon if the hooks dir holds
# pending flags; redirect it, and forbid spawns outright as a second fence.
os.environ["GSD_LONG_RUN_HOOKS_DIR"] = tempfile.mkdtemp(prefix="cwire-hooks-")
os.environ["GSD_LONG_RUN_NO_SPAWN"] = "1"
for var in ("ORCA_PANE_KEY", "CPP_CONTINUATION_TRANSPORT", "CPP_LEGACY_FOREGROUND_SENDKEYS"):
    os.environ.pop(var, None)

ROOT = Path(__file__).resolve().parents[1]
WATCHDOG = ROOT / "modules" / "zero-crash" / "hooks" / "context-watchdog.py"
TOOLS = ROOT / "tools"
TMP = Path(tempfile.mkdtemp(prefix="cwire-"))
PANE = f"{uuid.uuid4()}:{uuid.uuid4()}"

passes = 0
fails = 0


def check(gate: str, cond: bool, ev: str) -> None:
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


def load(path: Path, name: str):
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


lr = load(TOOLS / "gsd_long_run.py", "gsd_long_run")
mk = load(TOOLS / "gsd_autorun_marker.py", "gsd_autorun_marker")
wd = load(WATCHDOG, "ctxwd_cwire")
ct = wd._load_tool("continuation_transport")
if ct is None:
    print("FAIL V-CWIRE-TRANSPORT-LOADS: the watchdog cannot load continuation_transport")
    print("CWIRE_PASS=0/1  threshold=1/1")
    sys.exit(1)

spawned: list = []     # Orca transport deliveries
inbox: list = []       # daemon flag+spawn (terminal inbox)
spawn_result = {"ok": True}
ct.spawn_delivery = lambda *a, **k: spawned.append(a) or spawn_result["ok"]
wd._write_trigger_flag = lambda *a, **k: inbox.append(("flag", k)) or "flag"
wd._spawn_daemon = lambda *a, **k: inbox.append(("daemon",)) or True


def sid() -> str:
    return f"cwire-{uuid.uuid4().hex[:10]}"


def events(s: str) -> list[dict]:
    return lr.ledger_events(s)


def door(s: str, **env) -> dict:
    saved = {k: os.environ.get(k) for k in env}
    os.environ.update({k: v for k, v in env.items() if v is not None})
    try:
        return wd._dispatch_continuation(s, "resume", transcript="", cwd=str(ROOT), used_pct=20,
                                         cid=f"{s}:resume:1", expect_line="/d1-continue")
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def reset() -> None:
    spawned.clear()
    inbox.clear()
    spawn_result["ok"] = True


def gates_door() -> None:
    reset(); s = sid()
    r = door(s, ORCA_PANE_KEY=PANE)
    check("V-CWIRE-ORCA-ROUTES-EXACT",
          r.get("route") == "orca-exact" and len(spawned) == 1 and spawned[0][1] == "resume"
          and spawned[0][2] == "/d1-continue" and spawned[0][5] == f"{s}:resume:1" and not inbox,
          f"route={r} spawned={spawned} inbox={inbox}")
    check("V-CWIRE-ORCA-ENDPOINT-CAPTURED",
          (ct.read_endpoint(s) or {}).get("pane_key") == PANE, f"{ct.read_endpoint(s)}")

    reset(); s = sid()
    r = door(s)
    flag_kw = inbox[0][1] if inbox and inbox[0][0] == "flag" else {}
    check("V-CWIRE-NO-KEY-GOES-TO-INBOX",
          r.get("route") == "terminal-inbox" and not spawned and len(inbox) == 2
          and flag_kw.get("expect_line") == "/d1-continue"
          and "delivery_inbox_requested" in [e["event"] for e in events(s)]
          and r.get("legacy_foreground") is False,
          f"route={r} spawned={len(spawned)} inbox={inbox}")

    reset(); s = sid()
    r = door(s, CPP_LEGACY_FOREGROUND_SENDKEYS="1")
    check("V-CWIRE-LEGACY-OPT-IN-IS-LABELLED",
          r.get("route") == "terminal-inbox" and r.get("legacy_foreground") is True,
          f"route={r}")

    reset(); s = sid()
    r = door(s, ORCA_PANE_KEY=PANE, CPP_LEGACY_FOREGROUND_SENDKEYS="1")
    check("V-CWIRE-EXACT-BEATS-LEGACY", r.get("route") == "orca-exact" and not inbox, f"route={r}")

    reset(); s = sid()
    r = door(s, ORCA_PANE_KEY=PANE, CPP_CONTINUATION_TRANSPORT="off")
    check("V-CWIRE-KILL-SWITCH-MANUAL", r.get("route") == "manual" and not spawned and not inbox,
          f"route={r}")

    reset(); s = sid()
    spawn_result["ok"] = False
    r = door(s, ORCA_PANE_KEY=PANE)
    check("V-CWIRE-SPAWN-FAILURE-IS-MANUAL",
          r.get("route") == "manual" and "failed to start" in r.get("why", "") and not inbox,
          f"route={r}")


def boundary_tx(s: str) -> Path:
    t = TMP / f"{s}.jsonl"
    iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() + 2)) + ".000Z"
    rows = [{"type": "system", "cwd": str(ROOT)},
            {"type": "system", "subtype": "compact_boundary", "uuid": uuid.uuid4().hex,
             "timestamp": iso, "compactMetadata": {"trigger": "auto"}}]
    t.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return t


def stop(s: str, pct: float, tp: Path) -> dict:
    (Path(tempfile.gettempdir()) / wd.ORCH_THROTTLE_FLAG.format(session_id=s)).write_text(
        str(time.time()), encoding="utf-8")
    os.environ["_TEST_CONTEXT_PCT"] = str(pct)
    try:
        return wd.run({"session_id": s, "cwd": str(ROOT), "transcript_path": str(tp)}) or {}
    finally:
        os.environ.pop("_TEST_CONTEXT_PCT", None)


def clear(s: str) -> None:
    for f in (wd.RESUME_ARMED_FLAG, wd.RESUME_DONE_FLAG, wd.RESUME_CONFIRMED_FLAG,
              wd.ADVISORY_FLAG, wd.SNAPSHOT_FLAG):
        wd._clear_flag(s, f)
    mk.clear_marker(s)


def gates_watchdog_end_to_end() -> None:
    reset(); s = sid()
    os.environ["ORCA_PANE_KEY"] = PANE
    try:
        mk.write_marker(s, "/d1-continue", cwd=str(ROOT))
        tp = boundary_tx(s)
        out_a = stop(s, 20.0, tp)
        reason = out_a.get("reason", "")
        check("V-CWIRE-STOP-A-NAMES-EXACT-ROUTE",
              "Orca terminal (pane" in reason and PANE in reason and "Enter will be pressed" not in reason
              and not spawned, f"reason={reason[-200:]!r}")
        stop(s, 20.0, tp)
        check("V-CWIRE-STOP-B-DELIVERS-THROUGH-DOOR",
              len(spawned) == 1 and spawned[0][1] == "resume" and spawned[0][2] == "/d1-continue"
              and spawned[0][4] == str(tp) and not inbox,
              f"spawned={spawned} inbox={inbox}")
        disp = [e for e in events(s) if e["event"] == "resume_dispatched"]
        check("V-CWIRE-DISPATCH-LEDGER-NAMES-ROUTE",
              disp and disp[-1].get("route") == "orca-exact", f"{disp}")
    finally:
        os.environ.pop("ORCA_PANE_KEY", None)
        clear(s)

    reset(); s = sid()
    try:
        mk.write_marker(s, "/d1-continue", cwd=str(ROOT))
        tp = boundary_tx(s)
        out_a = stop(s, 20.0, tp)
        reason = out_a.get("reason", "")
        check("V-CWIRE-STOP-A-INBOX-SAYS-REFUSAL",
              "terminal inbox" in reason and "REFUSED" in reason and "LEGACY" not in reason,
              f"{reason[-220:]!r}")
        stop(s, 20.0, tp)
        kw = inbox[0][1] if inbox and inbox[0][0] == "flag" else {}
        check("V-CWIRE-STOP-B-NON-ORCA-USES-INBOX",
              not spawned and len(inbox) == 2 and kw.get("expect_line") == "/d1-continue"
              and kw.get("transcript") == str(tp), f"spawned={spawned} inbox={inbox}")
    finally:
        clear(s)


def gates_sweep() -> None:
    """The stall sweep recovers by SESSION: recorded Orca endpoint, else inbox."""
    reset()
    s = sid()
    proj = Path(os.environ["GSD_LONG_RUN_PROJECTS_DIR"]) / "p"
    proj.mkdir(exist_ok=True)
    tx = proj / f"{s}.jsonl"
    rows = [{"type": "system", "cwd": str(ROOT)},
            {"type": "assistant", "message": {"role": "assistant",
                                              "content": [{"type": "text", "text": "/absw2-continue"}]}}]
    tx.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    old = time.time() - 30 * 60
    os.utime(tx, (old, old))
    # The sweep reads markers from state_dir() (redirected above); the marker
    # module writes to its own STATE_DIR. Point it at the same place for this
    # gate only. And the sweep imports the transport lazily BY NAME: register
    # the recorded instance under that name, or it would import a fresh copy
    # whose spawn is real.
    real_state = mk.STATE_DIR
    mk.STATE_DIR = lr.state_dir()
    sys.modules["continuation_transport"] = ct
    mk.write_marker(s, "/absw2-continue", cwd=str(ROOT))
    written = []
    real_trigger = lr.write_trigger
    lr.write_trigger = lambda *a, **k: written.append(a)
    try:
        lr.sweep()
        rec = [e for e in events(s) if e["event"] == "recovered"]
        check("V-CWIRE-SWEEP-NON-ORCA-VIA-INBOX",
              rec and rec[-1].get("route") == "terminal-inbox" and len(written) == 1
              and written[0][0] == s and not spawned,
              f"recovered={rec} triggers={written} spawned={spawned}")
        ct.capture_endpoint(s, env={"ORCA_PANE_KEY": PANE})
        os.utime(tx, (old - 60, old - 60))
        lr.sweep()
        rec = [e for e in events(s) if e["event"] == "recovered"]
        check("V-CWIRE-SWEEP-USES-RECORDED-ENDPOINT",
              rec and rec[-1].get("route") == "orca-exact" and len(spawned) == 1
              and spawned[0][2] == "/absw2-continue" and len(written) == 1,
              f"recovered={rec[-1:]} spawned={spawned} triggers={written}")
    finally:
        lr.write_trigger = real_trigger
        mk.clear_marker(s)
        mk.STATE_DIR = real_state


def main() -> int:
    print("V-CWIRE -- one door for every automated keystroke")
    gates_door()
    gates_watchdog_end_to_end()
    gates_sweep()
    total = passes + fails
    print(f"CWIRE_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
