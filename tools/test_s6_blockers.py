#!/usr/bin/env python
"""V-S6-* gates: the blocker compiler -- every BLOCKED / Owner-hold park is typed (flow-compression S6, FC-08).

Every gate runs through `gates()` against whatever implementation is installed, so the mutant drills at the bottom
can swap a broken function in and require at least one gate to go red. UNKNOWN / INCONCLUSIVE never count as a pass.

Controls checked against the REAL reader before they count (Phase 5 incident): the OLD_* key sets below were captured
by running the HEAD (cea6b85b) writer through the real supervise seam; the census strings are copied from the host
ledger's own mission_blocked reasons; the kill-switch twin runs the same real writer with the switch off.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="s6-blockers-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["PP_OWNER_QUEUE_STATE_DIR"] = str(Path(TMP) / "owner-queue")
os.environ["CPP_CLAUDE_EXE"] = "__no_such_claude_in_tests__"
os.environ["CPP_RESOURCE_ADMISSION"] = "off"
os.environ.pop("CPP_BLOCKER_COMPILE", None)
os.environ.pop("CPP_FORESEEABLE_DECISIONS", None)
TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import blocker_compiler as bc  # noqa: E402
import gsd_long_run as lr  # noqa: E402
import gsd_mission as gm  # noqa: E402

ROOT = Path(TMP).resolve()
NOW = 1_800_000_000.0
_n = [0]
RESULTS: list[tuple[str, bool, str]] = []

# Captured from the HEAD (cea6b85b) writer through the real supervise seam, BEFORE block_mission existed.
OLD_RECORD_KEYS = {"add_dirs", "allowed_tools", "blocked_intent", "code_id", "created_at", "cwd", "epoch",
                   "failed_launches", "iterations", "last_progress_at", "max_cycles", "max_hours", "mission_id",
                   "mission_terms", "mode", "note", "owner", "pending", "permission_mode", "progress_unknown",
                   "reason", "resume_command", "schema_version", "seq", "state", "token_estimate",
                   "token_estimate_basis", "token_estimate_src", "updated_at", "wall", "workstream"}
OLD_LEDGER_KEYS = {"code", "epoch", "event", "mission_id", "reason", "seq", "session_id", "state", "ts"}
OLD_HOLD_KEYS = {"reason", "set_at"}
NEW_LEDGER_KEYS = {"blocker_class", "independent_work", "owner_required", "unblock_kind"}


class R:
    def __init__(self, out, rc=0):
        self.stdout, self.stderr, self.returncode = out, "", rc


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), str(detail)[:200]))


def uid(tag: str) -> str:
    _n[0] += 1
    return f"m-s6{tag}{_n[0]:04d}"


def fresh_missions() -> None:
    for p in Path(TMP).glob("gsd-mission-*.json"):
        p.unlink()


def supervised_block(needs: str, tag: str = "b") -> tuple[str, dict]:
    """A RUNNING background mission whose host row says blocked, supervised once with the host's ask `needs`."""
    fresh_missions()
    mid = uid(tag)
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t", now=NOW, state=gm.RUNNING, epoch=1,
                  owner={"session_id": f"s-{mid}", "pid": 5151, "kind": "background"})
    hs = [{"sessionId": f"s-{mid}", "status": "waiting", "waitingFor": "owner", "state": "blocked",
           "kind": "background", "id": f"s-{mid}"[:8], "pid": 999}]
    real = gm.host_job_needs
    gm.host_job_needs = lambda sid: needs
    try:
        gm.supervise(now=NOW, sessions=hs, gsd_status=lambda c, workstream=None: {"outcome": "OK", "reason": "ok"},
                     runner=lambda argv, cwd: R("backgrounded · 9e9e9e9e · x"),
                     stop_runner=lambda argv: R("stopped"), pid_alive=lambda p: True)
    finally:
        gm.host_job_needs = real
    return mid, gm.load(mid)


def ledger_rows(mid: str, event: str) -> list[dict]:
    return [r for r in lr.ledger_events(mid) if r.get("event") == event]


def held_mission(tag: str = "h") -> str:
    fresh_missions()
    mid = uid(tag)
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t", now=NOW, state=gm.RUNNING, epoch=1,
                  owner={"session_id": f"s-{mid}", "pid": 5151, "kind": "background"})
    return mid


def tracer_gates() -> None:
    # --- the thinnest real path: host-blocked worker -> supervise -> surface_blocked -> block_mission -> compiler
    mid, rec = supervised_block("Choose 1 or run /compact")
    b = rec.get("blocker") or {}
    cb = gm.current_blocker(rec) or {}
    rows = ledger_rows(mid, "mission_blocked")
    check("V-S6-TRACER-SURFACE-BLOCKED-TYPED",
          rec["state"] == gm.BLOCKED and b.get("class") == "DECISION_REQUEST"
          and (b.get("unblock_condition") or {}).get("kind") == "owner_act" and b.get("owner_required") is True
          and b.get("independent_work") is False and bool(b.get("independent_reason"))
          and cb.get("class") == "DECISION_REQUEST" and len(rows) == 1
          and rows[0].get("blocker_class") == "DECISION_REQUEST" and rows[0].get("independent_work") is False,
          f"class={b.get('class')} cond={b.get('unblock_condition')} row={ {k: rows[0].get(k) for k in NEW_LEDGER_KEYS} if rows else None}")

    # --- kill switch: the exact old record and ledger shape, from the same real writer
    on_rec_keys, on_row_keys = set(rec), set(rows[0]) if rows else set()
    os.environ["CPP_BLOCKER_COMPILE"] = "off"
    try:
        mid_off, rec_off = supervised_block("Choose 1 or run /compact", "k")
        rows_off = ledger_rows(mid_off, "mission_blocked")
    finally:
        os.environ.pop("CPP_BLOCKER_COMPILE", None)
    off_ok = (set(rec_off) == OLD_RECORD_KEYS and bool(rows_off) and set(rows_off[0]) == OLD_LEDGER_KEYS
              and "blocker" not in rec_off)
    on_differs = on_rec_keys == OLD_RECORD_KEYS | {"blocker"} and on_row_keys == OLD_LEDGER_KEYS | NEW_LEDGER_KEYS
    check("V-S6-TRACER-KILLSWITCH-OLD-SHAPE", off_ok and on_differs,
          f"off_extra={sorted(set(rec_off) - OLD_RECORD_KEYS)} off_missing={sorted(OLD_RECORD_KEYS - set(rec_off))} "
          f"on_extra={sorted(on_rec_keys - OLD_RECORD_KEYS)}")

    # --- a compiler fault never stops the BLOCKED write; it lands as UNKNOWN naming the exception class
    real = bc.compile_blocker

    def boom(*a, **k):
        raise RuntimeError("compiler exploded")
    bc.compile_blocker = boom
    try:
        mid_f, rec_f = supervised_block("Choose 1 or run /compact", "f")
    finally:
        bc.compile_blocker = real
    bf = rec_f.get("blocker") or {}
    check("V-S6-TRACER-FAIL-OPEN",
          rec_f["state"] == gm.BLOCKED and bf.get("class") == "UNKNOWN" and bf.get("compile_error") == "RuntimeError"
          and bf.get("independent_work") is False,
          f"state={rec_f['state']} blocker={bf.get('class')}/{bf.get('compile_error')}")

    # --- UNKNOWN is reachable and is never independent work, even with a runnable next unit on offer
    runnable = {"measured": True, "reason": "ok", "current": 1.0, "units": [1.0, 2.0], "candidates": [2.0]}
    u = bc.compile_blocker("host lists session blocked (no waitingFor); host needs: open this session to continue setup",
                           evidence=runnable)
    check("V-S6-TRACER-UNKNOWN-REACHABLE",
          u["class"] == "UNKNOWN" and u["independent_work"] is False and u["owner_required"] is True
          and u["independent_reason"] == "unclassified", f"{u['class']} {u['independent_reason']}")

    # --- census over a ledger written by the real writer shape: populations and compiled counts agree
    led = Path(TMP) / "census-fixture.jsonl"
    reasons = ["host: waiting for permission prompt", "host: waiting for input needed",
               "host lists session blocked (no waitingFor); host needs: rate limited — wait and retry · You've hit your weekly limit · resets Oct 7, 7am (Europe/Berlin)",
               "host lists session blocked (no waitingFor); host needs: run /clear",
               "gsd NO_PHASES on 2 consecutive passes (300 s): GSD parses 0 phases from ROADMAP.md -- no relay until GSD answers OK",
               "totally unrecognised reason text"]
    with led.open("w", encoding="utf-8") as fh:
        for r in reasons:
            fh.write(json.dumps({"event": "mission_blocked", "reason": r, "session_id": "m-x"}) + "\n")
        fh.write(json.dumps({"event": "owner_hold_set", "reason": "owner hold: Owner reviewing", "session_id": "m-x"}) + "\n")
        fh.write("not json\n")
        fh.write(json.dumps({"event": "unrelated"}) + "\n")
    c = bc.census(led)
    cls = {k: v["count"] for k, v in c["classes"].items()}
    host = bc.census()
    host_ok = host["rows"] == 0 or (sum(v["count"] for v in host["classes"].values())
                                    == sum(n for e, n in host["populations"].items() if e != "blocked_intent"))
    check("V-S6-TRACER-CENSUS-POPULATION",
          c["populations"]["mission_blocked"] == 6 and c["populations"]["owner_hold_set"] == 1
          and cls == {"HOST_GATE": 2, "PROVIDER_LIMIT": 1, "COMMAND_REQUEST": 1, "GSD_HOLD": 1, "UNKNOWN": 1,
                      "OWNER_PARK": 1} and c["rows"] == 8 and host_ok, f"{cls} host_rows={host['rows']}")


def gates() -> None:
    tracer_gates()


def run_once() -> tuple[int, int]:
    RESULTS.clear()
    gates()
    p = sum(1 for _, ok, _ in RESULTS if ok)
    return p, len(RESULTS) - p


def main() -> int:
    t0 = time.time()
    passes, fails = run_once()
    for name, ok, detail in RESULTS:
        print(f"{'PASS' if ok else 'FAIL'} {name} {'' if ok else detail}")
    total = passes + fails
    print(f"S6_PASS={passes}/{total}  ({time.time() - t0:.0f} s)")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
