#!/usr/bin/env python3
"""V-ROLLECON-* gates: the economic rollover trigger in context-watchdog.py.

Spec: vault/specs/economic-rollover-trigger.md. Before it, active rollover was asked only at
the 45 % wall (~450k on 1M) and the break-even decider ran once in shadow without a start
head, so 110 of 126 decisions in the 2026-10-02 incident window read "worth it, but not at a
work boundary".

Every refusal is paired with the control in which the trigger DOES ask, so a trigger that
never asks cannot pass. Hermetic: private state dirs, git head and spawn are stubbed in the
watchdog cases; the rollover.py case runs observe() for real against this repo.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WATCHDOG = ROOT / "modules" / "zero-crash" / "hooks" / "context-watchdog.py"

_TMP = Path(tempfile.mkdtemp(prefix="rollecon-"))
os.environ.update({"GSD_LONG_RUN_STATE_DIR": str(_TMP / "state"),
                   "GSD_LONG_RUN_SESSIONS_DIR": str(_TMP / "sessions"),
                   "GSD_AUTORUN_MARKER_DIR": str(_TMP / "state"),
                   "CPP_ROLLOVER_STATE_DIR": str(_TMP / "rollover"),
                   "CTXWD_HEARTBEAT_LOG": str(_TMP / "context-watchdog.log"),
                   "CTXWD_SNAPSHOT_LEDGER": str(_TMP / "context_snapshots.jsonl")})
for _d in ("state", "sessions", "rollover"):
    (_TMP / _d).mkdir()
for _k in ("CPP_ROLLOVER_ACTIVE", "CPP_ROLLOVER_ECONOMIC", "CPP_ROLLOVER_ECON_PCT"):
    os.environ.pop(_k, None)

passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"  PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"  FAIL {gate}: {ev}")


def _load(name, path):
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def sid() -> str:
    return f"rollecon-{uuid.uuid4().hex[:12]}"


def write_decision(s, head, would):
    d = _TMP / "rollover" / "decisions"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{s}.json").write_text(json.dumps(
        {"session_id": s, "head": head, "decision": {"would_rollover": would,
         "reason": "fixture"}}), encoding="utf-8")


def main() -> int:
    wd = _load("ctxwd_rollecon", WATCHDOG)
    head = {"v": "aaa111"}
    spawned: list = []
    wd._git_head = lambda cwd: head["v"]
    wd._econ_spawn = lambda s_, cwd, tp, pct, start_head: \
        spawned.append({"tier": "econ", "start_head": start_head}) or True
    wd._read_autorun_marker = lambda s_: None

    def fresh():
        s = sid()
        for f in (wd.ROLLOVER_ASK_FLAG, wd.ROLLOVER_CLEAR_FLAG, wd.ROLLOVER_WAIT_FLAG,
                  wd.ADVISORY_FLAG, wd.ROLLOVER_ECON_FLAG):
            wd._clear_flag(s, f)
        spawned.clear()
        head["v"] = "aaa111"
        return s

    print("evaluation: once per commit, with the session's start head")
    s = fresh()
    out = wd._econ_rollover(s, str(ROOT), "", 30.0)
    check("V-ROLLECON-FIRST-STOP-RECORDS-ONLY", out is None and spawned == [],
          f"first Stop records the start head, spawns nothing: out={out} spawned={spawned}")
    head["v"] = "bbb222"
    wd._econ_rollover(s, str(ROOT), "", 30.0)
    check("V-ROLLECON-COMMIT-SPAWNS-EVAL",
          len(spawned) == 1 and spawned[0] == {"tier": "econ", "start_head": "aaa111"},
          f"a commit spawns one evaluation carrying the start head: {spawned}")
    wd._econ_rollover(s, str(ROOT), "", 31.0)
    check("V-ROLLECON-NO-COMMIT-NO-SECOND-EVAL", len(spawned) == 1,
          f"same head, no second spawn (cardinality): spawns={len(spawned)}")

    print("acting on the verdict")
    # CONTROL: the trigger asks.
    write_decision(s, "bbb222", True)
    out = wd._econ_rollover(s, str(ROOT), "", 32.0)
    check("V-ROLLECON-ASKS-ON-CURRENT-HEAD",
          (out or {}).get("decision") == "block" and "kclear" in (out or {}).get("reason", "")
          and wd._flag_exists(s, wd.ROLLOVER_ASK_FLAG) and wd._flag_exists(s, wd.ROLLOVER_ECON_FLAG),
          f"block={bool(out)} ask_flag={wd._flag_exists(s, wd.ROLLOVER_ASK_FLAG)}")
    out2 = wd._econ_rollover(s, str(ROOT), "", 32.0)
    check("V-ROLLECON-ASKS-ONCE", out2 is None, f"second Stop while asked: {out2}")

    for gate, setup in [
        ("V-ROLLECON-STALE-HEAD-NO-ASK", lambda s_: write_decision(s_, "old999", True)),
        ("V-ROLLECON-NOT-WORTH-IT-NO-ASK", lambda s_: write_decision(s_, "bbb222", False)),
        ("V-ROLLECON-NO-DECISION-NO-ASK", lambda s_: None),
    ]:
        s = fresh()
        wd._econ_rollover(s, str(ROOT), "", 30.0)
        head["v"] = "bbb222"
        wd._econ_rollover(s, str(ROOT), "", 30.0)
        setup(s)
        out = wd._econ_rollover(s, str(ROOT), "", 32.0)
        check(gate, out is None and not wd._flag_exists(s, wd.ROLLOVER_ASK_FLAG), f"out={out}")

    s = fresh()
    wd._econ_rollover(s, str(ROOT), "", 30.0)
    head["v"] = "bbb222"
    write_decision(s, "bbb222", True)
    out = wd._econ_rollover(s, str(ROOT), "", 10.0)
    check("V-ROLLECON-BELOW-FLOOR-NO-ASK", out is None and spawned == [], f"10 % -> out={out}")

    s = fresh()
    os.environ["CPP_ROLLOVER_ECONOMIC"] = "0"
    wd._econ_rollover(s, str(ROOT), "", 30.0)
    head["v"] = "bbb222"
    write_decision(s, "bbb222", True)
    out = wd._econ_rollover(s, str(ROOT), "", 32.0)
    os.environ.pop("CPP_ROLLOVER_ECONOMIC")
    check("V-ROLLECON-KILL-SWITCH", out is None and spawned == [], f"switch off -> out={out}")

    s = fresh()
    wd._read_autorun_marker = lambda s_: {"mission_id": "m-x"}
    wd._econ_rollover(s, str(ROOT), "", 30.0)
    head["v"] = "bbb222"
    write_decision(s, "bbb222", True)
    out = wd._econ_rollover(s, str(ROOT), "", 32.0)
    wd._read_autorun_marker = lambda s_: None
    check("V-ROLLECON-MISSION-WORKER-EXCLUDED", out is None and spawned == [], f"mission -> out={out}")

    # A Ralph mission worker launched by `claude --bg` carries NO autorun marker; it is known
    # only as the owner of a gsd-mission-*.json (measured 2026-10-02: session 4ec01521,
    # mission m-129ddae5ccf3, mode ralph). The Owner keeps those runs untouched.
    s = fresh()
    mfile = Path(os.environ["GSD_AUTORUN_MARKER_DIR"]) / "gsd-mission-m-test.json"
    mfile.write_text(json.dumps({"mission_id": "m-test", "mode": "ralph", "state": "RUNNING",
                                 "owner": {"session_id": s}}), encoding="utf-8")
    wd._econ_rollover(s, str(ROOT), "", 30.0)
    head["v"] = "bbb222"
    write_decision(s, "bbb222", True)
    out = wd._econ_rollover(s, str(ROOT), "", 32.0)
    mfile.unlink()
    check("V-ROLLECON-MISSION-OWNER-EXCLUDED", out is None and spawned == [],
          f"owner of a mission file, no marker -> out={out} spawned={spawned}")

    s = fresh()
    head["v"] = None
    out = wd._econ_rollover(s, str(ROOT), "", 32.0)
    check("V-ROLLECON-NO-GIT-NO-ASK", out is None and spawned == [], f"no repo -> out={out}")

    print("a capsule that never arrives: the economic ask withdraws, the wall survives")
    s = fresh()
    wd._econ_rollover(s, str(ROOT), "", 30.0)
    head["v"] = "bbb222"
    write_decision(s, "bbb222", True)
    wd._econ_rollover(s, str(ROOT), "", 32.0)
    wd._rollover_gate = lambda s_: {"verdict": "NO_CAPSULE", "reasons": ["none"], "rc": 4}
    wd._set_flag(s, wd.ADVISORY_FLAG)  # pretend the wall already debounced: must stay as it is
    for _ in range(wd.ROLLOVER_MAX_WAIT + 1):
        wd._rollover_step(s, str(ROOT), "", 32.0)
    check("V-ROLLECON-WITHDRAWS-NO-COMPACT",
          not wd._flag_exists(s, wd.ROLLOVER_ASK_FLAG) and not wd._flag_exists(s, wd.ROLLOVER_CLEAR_FLAG)
          and wd._flag_exists(s, wd.ADVISORY_FLAG),
          f"ask={wd._flag_exists(s, wd.ROLLOVER_ASK_FLAG)} clear={wd._flag_exists(s, wd.ROLLOVER_CLEAR_FLAG)} "
          f"advisory={wd._flag_exists(s, wd.ADVISORY_FLAG)}")
    out = wd._econ_rollover(s, str(ROOT), "", 33.0)
    check("V-ROLLECON-DECLINED-HEAD-NOT-REASKED", out is None,
          f"same head after withdrawal -> out={out}")
    # Control for the wall path: a NON-economic ask still falls back to /compact as before.
    s = fresh()
    wd._set_flag(s, wd.ROLLOVER_ASK_FLAG)
    wd._set_flag(s, wd.ADVISORY_FLAG)
    for _ in range(wd.ROLLOVER_MAX_WAIT + 1):
        wd._rollover_step(s, str(ROOT), "", 75.0)
    check("V-ROLLECON-WALL-FALLBACK-UNCHANGED",
          wd._flag_exists(s, wd.ROLLOVER_CLEAR_FLAG) and not wd._flag_exists(s, wd.ADVISORY_FLAG),
          "wall ask without a capsule still hands back to /compact")

    print("rollover_econ.py: the start head reaches at_boundary and the decision is written")
    ro = _load("rollover", ROOT / "tools" / "rollover.py")
    dirty = {"state": "OK", "dirty": ["x.py"], "head": "bbb222"}
    check("V-ROLLECON-SESSION-COMMIT-IS-BOUNDARY",
          ro.at_boundary(dirty, "aaa111") is True and ro.at_boundary(dirty, "bbb222") is False,
          "dirty shared tree: a commit since the start head is a boundary, no commit is not")
    ec = _load("rollover_econ", ROOT / "tools" / "rollover_econ.py")
    s = sid()
    out = ec.evaluate(s, str(ROOT), None, 30.0, "0" * 40)
    dp = _TMP / "rollover" / "decisions" / f"{s}.json"
    got = json.loads(dp.read_text(encoding="utf-8")) if dp.is_file() else {}
    check("V-ROLLECON-DECISION-FILE",
          dp.is_file() and got.get("head") == out.get("head") and isinstance(got.get("head"), str)
          and len(got["head"]) >= 7 and got.get("start_head") == "0" * 40 and "decision" in got,
          f"decision file head={got.get('head')} start_head={str(got.get('start_head'))[:8]}")
    # The watchdog reads the file through its own helper: the two spellings of the path agree.
    check("V-ROLLECON-PATH-AGREES", wd._econ_decision(s).get("head") == got.get("head"),
          f"watchdog sees head={wd._econ_decision(s).get('head')}")

    print(f"ROLLECON_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
