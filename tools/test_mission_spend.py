#!/usr/bin/env python
"""V-MSPEND-* gates for the mission cost circuit breaker and per-mission model (TOK-18 gen 2 D1/D2).

Hermetic like test_gsd_mission_owner_hold.py: state goes to a temp dir BEFORE import. Every trip has a
paired non-trip control, so a breaker that trips always (or never) cannot go green. The E1 replay row
uses E1's real shape: estimate 17M, spend 141M.

Mutation drill: GSD_MISSION_DRILL_DIR holding mutated copies of gsd_mission.py / mission_spend.py is
imported first, so the live files are never edited to prove the gates can go red.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="mission-spend-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ.pop("CPP_MISSION_RENEW", None)
os.environ["CPP_CLAUDE_EXE"] = "__no_such_claude_in_tests__"   # belt and braces: never a real worker
sys.path.insert(0, str(Path(__file__).resolve().parent))
if os.environ.get("GSD_MISSION_DRILL_DIR"):
    sys.path.insert(0, os.environ["GSD_MISSION_DRILL_DIR"])
# mission_spend first: importing gsd_mission puts its own directory back at sys.path[0], so a drill
# mutant of mission_spend imported afterwards would silently be the real file (drill, 2026-10-05).
import mission_spend as ms  # noqa: E402
import gsd_mission as gm  # noqa: E402
assert gm.__name__ and ms.__file__  # both resolved through the drill dir when one is set

passes = fails = 0
NOW = 1_800_000_000.0
M = 1_000_000


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def _row(mid, ts, inp=0, cr=0, cw=0, out=0, model="claude-sonnet-5-5"):
    return json.dumps({"timestamp": ts, "message": {"id": mid, "model": model, "usage": {
        "input_tokens": inp, "cache_read_input_tokens": cr, "cache_creation_input_tokens": cw,
        "output_tokens": out}}})


def _mission(mid, **fields):
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    return gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW,
                         state=gm.RUNNING, epoch=1, **fields)


def main() -> int:
    # --- measurement ---------------------------------------------------------------------------
    root = Path(TMP) / "proj"
    wd = "/home/kobii/missions/e1"
    enc = ms.encode_cwd(wd)
    for name in (enc, enc + "--claude-worktrees-x", enc + "0"):
        (root / name).mkdir(parents=True)
    rows = [_row("a", "2027-01-15T08:00:00Z", inp=10, cr=100, cw=5, out=1),
            _row("a", "2027-01-15T08:00:00Z", inp=10, cr=100, cw=5, out=1),    # streamed duplicate
            _row("b", "2027-01-15T08:01:00Z", cr=1000),
            _row("s", "2027-01-15T08:02:00Z", inp=999, model="<synthetic>"),   # not a model call
            _row("old", "2020-01-01T00:00:00Z", cr=5000)]                      # before created_at
    (root / enc / "s1.jsonl").write_text("\n".join(rows) + "\n", encoding="utf-8")
    (root / (enc + "--claude-worktrees-x") / "s2.jsonl").write_text(_row("c", "2027-01-15T08:03:00Z", out=7) + "\n",
                                                                    encoding="utf-8")
    (root / (enc + "0") / "s3.jsonl").write_text(_row("z", "2027-01-15T08:03:00Z", cr=10**9) + "\n",
                                                 encoding="utf-8")
    rec = {"work_dir": wd, "created_at": 1_800_000_000.0}   # 2027-01-15T08:00:00Z
    own = ({"s1", "s2", "s3"}, set())     # s3 is named on purpose: the sibling is excluded by DIRECTORY
    cache = {}
    got = ms.processed_tokens(rec, root=root, cache=cache, sessions=own)
    check("V-MSPEND-EXACT-SUM", got == 116 + 1000 + 7, f"got {got}")
    check("V-MSPEND-SIBLING-EXCLUDED", got < 10**9, "a ...-e10 style sibling is not this mission")
    check("V-MSPEND-UNKNOWN-NOT-ZERO", ms.processed_tokens({"work_dir": "/nope"}, root=root, sessions=own) is None)
    with open(root / enc / "s1.jsonl", "a", encoding="utf-8") as fh:
        fh.write(_row("d", "2027-01-15T08:05:00Z", out=3) + "\n")
    check("V-MSPEND-CACHE-SEES-GROWTH", ms.processed_tokens(rec, root=root, cache=cache, sessions=own) == got + 3)
    got += 3

    # --- attribution: the directory is not the mission (m-8bbdf725cd52, 70.7M read vs 53.7M own) ---
    (root / enc / "foreign.jsonl").write_text(_row("f", "2027-01-15T08:04:00Z", cr=17 * M) + "\n", encoding="utf-8")
    (root / enc / "s1" / "subagents").mkdir(parents=True)
    (root / enc / "s1" / "subagents" / "agent-x.jsonl").write_text(_row("g", "2027-01-15T08:04:00Z", out=40) + "\n",
                                                                     encoding="utf-8")
    att = ms.processed_tokens(rec, root=root, sessions=own)
    check("V-MSPEND-FOREIGN-SESSION-EXCLUDED", att == got + 40, f"got {att}, own {got} + subagent 40")
    check("V-MSPEND-FOREIGN-CONTROL-COUNTED",
          ms.processed_tokens(rec, root=root, sessions=(own[0] | {"foreign"}, set())) == got + 40 + 17 * M,
          "the same file IS counted once its session is the mission's: exclusion is by attribution")
    check("V-MSPEND-SUBAGENT-ATTRIBUTED",
          ms.processed_tokens(rec, root=root, sessions=({"s2", "s3"}, set())) == 7,
          "without s1, neither s1 nor its subagent counts")
    check("V-MSPEND-PREFIX-PENDING-WORKER",
          ms.processed_tokens(rec, root=root, sessions=(set(), {"forei"})) == 17 * M,
          "an unacked launch is measured by its bg_id prefix")
    check("V-MSPEND-UNATTRIBUTED-IS-UNKNOWN",
          ms.processed_tokens(rec, root=root, sessions=(set(), set())) is None,
          "no session to attribute -> None, never 0 and never the whole directory")

    # derivation from the record and the mission's OWN ledger rows
    gm.lr.ledger_append("m-attr", "worker_acked", mission_id="m-attr", worker="s1")
    gm.lr.ledger_append("m-attr", "worker_adopted", mission_id="m-attr", worker="s2")
    gm.lr.ledger_append("m-other", "worker_acked", mission_id="m-other", worker="foreign")
    ids, px = ms.mission_sessions({"mission_id": "m-attr", "owner": {"session_id": "s3"},
                                   "pending": {"bg_id": "abc1"}})
    check("V-MSPEND-SESSIONS-DERIVED", ids == {"s1", "s2", "s3"} and px == {"abc1"}, f"{ids} {px}")
    check("V-MSPEND-OTHER-MISSION-WORKER-EXCLUDED", "foreign" not in ids)
    derived = ms.processed_tokens({**rec, "mission_id": "m-attr", "owner": {"session_id": "s3"}}, root=root)
    check("V-MSPEND-DERIVED-END-TO-END", derived == got + 40, f"got {derived}")

    # --- judge: every trip has a control -------------------------------------------------------
    e1 = {"token_estimate": 17 * M}
    check("V-MSPEND-NO-ESTIMATE-NEVER-TRIPS", ms.judge({}, 10**12, "f")["trip"] is None)
    check("V-MSPEND-UNMEASURED-NEVER-TRIPS", ms.judge(e1, None, "f")["trip"] is None)
    check("V-MSPEND-E1-REPLAY-TRIPS", ms.judge(e1, 141 * M, "f")["trip"] is not None, "E1: 141M vs 17M")
    check("V-MSPEND-AT-RATIO-CONTROL", ms.judge(e1, 34 * M, None)["trip"] is None, "exactly 2x does not trip")
    check("V-MSPEND-OVER-RATIO-TRIPS", ms.judge(e1, 34 * M + 1, None)["trip"] is not None)
    first = ms.judge(e1, 5 * M, "fp1")
    check("V-MSPEND-MARK-ON-NEW-FP", first["trip"] is None and first["mark"] == {"fp": "fp1", "tokens": 5 * M})
    marked = {**e1, "cost_mark": first["mark"]}
    check("V-MSPEND-STALL-CONTROL", ms.judge(marked, 5 * M + 8_500_000, "fp1")["trip"] is None,
          "half the estimate since the mark does not trip")
    check("V-MSPEND-STALL-TRIPS", ms.judge(marked, 5 * M + 8_500_001, "fp1")["trip"] is not None)
    check("V-MSPEND-PROGRESS-RESETS-STALL", ms.judge(marked, 20 * M, "fp2")["trip"] is None)

    # --- supervisor wiring: a trip parks with the Owner hold; a control does not ---------------
    _mission("m-trip", token_estimate=17 * M, max_hours=1000.0)
    out = gm._cost_breaker(gm.load("m-trip"), NOW, measure=lambda r: 141 * M, fingerprint=lambda w: "f")
    check("V-MSPEND-TRIP-HOLDS", bool(out.get("owner_hold")) and "cost breaker" in out["owner_hold"]["reason"],
          str(out.get("owner_hold")))
    check("V-MSPEND-HOLD-PLAN-NONE", gm.plan_next(out, NOW, [], pid_alive=lambda p: True)["action"] == "none")
    _mission("m-ok", token_estimate=17 * M, max_hours=1000.0)
    ok = gm._cost_breaker(gm.load("m-ok"), NOW, measure=lambda r: 3 * M, fingerprint=lambda w: "f")
    check("V-MSPEND-CONTROL-NO-HOLD", not ok.get("owner_hold") and ok.get("cost_mark", {}).get("tokens") == 3 * M)
    _mission("m-err", token_estimate=17 * M, max_hours=1000.0)

    def boom(r):
        raise OSError("disk")
    err = gm._cost_breaker(gm.load("m-err"), NOW, measure=boom, fingerprint=lambda w: "f")
    check("V-MSPEND-METER-ERROR-FAILS-OPEN", not err.get("owner_hold"))

    # --- the supervise pass itself calls the breaker (wiring, not only the helper) ------------
    _mission("m-sup", token_estimate=17 * M, max_hours=1000.0)
    real_measure, real_fp = ms.processed_tokens, gm.progress_fingerprint
    ms.processed_tokens, gm.progress_fingerprint = (lambda rec, **k: 141 * M), (lambda w: "f")
    try:
        # No real process may start: launches and stops go to a runner that refuses everything.
        class _Refused:
            returncode, stdout, stderr = 1, "", "refused by test"
        gm.supervise(now=NOW, sessions=[], pid_alive=lambda p: True,
                     runner=lambda *a, **k: _Refused(), stop_runner=lambda *a, **k: _Refused(),
                     gsd_status=lambda *a, **k: None)
    finally:
        ms.processed_tokens, gm.progress_fingerprint = real_measure, real_fp
    check("V-MSPEND-SUPERVISE-WIRED", bool((gm.load("m-sup") or {}).get("owner_hold")))

    # --- D2: the mission's model rides the launch --------------------------------------------
    base = {"mission_id": "m-x", "cwd": TMP, "epoch": 1}
    argv = gm.worker_argv({**base, "model": "sonnet"}, "go")
    check("V-MSPEND-MODEL-PASSED", "--model" in argv and argv[argv.index("--model") + 1] == "sonnet")
    check("V-MSPEND-NO-MODEL-CONTROL", "--model" not in gm.worker_argv(base, "go"))

    print(f"MSPEND_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
