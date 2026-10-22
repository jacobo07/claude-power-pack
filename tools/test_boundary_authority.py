#!/usr/bin/env python
"""V-BND-* gates for CCR v5 E2: the boundary authority (max_calls in the phase lease) and the boundary
ledger / call-profile PGO (tools/boundary_ledger.py). Hermetic: temp state, injected meters.
Every refusal is paired with a control in which the same input is admitted."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="boundary-authority-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ.pop("CPP_COST_HOLD_STOP", None)
os.environ["CPP_MISSION_RECOVERY"] = "off"
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import boundary_ledger as bl  # noqa: E402
import gsd_mission as gm  # noqa: E402
import mission_spend as ms  # noqa: E402
import phase_lease as pls  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None
passes = fails = 0
NOW = 1_800_000_000.0
TOK_BASE, FORECAST, CALL_BASE, CAP = 5_000_000, 1_000_000, 40, 6
STATE = Path(TMP) / "STATE.md"
TOKENS: dict[str, object] = {}
CALLS: dict[str, object] = {}
gone = lambda pid: False  # noqa: E731
OK_GSD = lambda cwd, workstream=None: {"outcome": "OK"}  # noqa: E731


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


ms.processed_tokens = lambda rec: TOKENS[rec["mission_id"]]
ms.processed_calls = lambda rec: CALLS[rec["mission_id"]]


def lease(**kw):
    return pls.make_lease(phase="1", forecast=FORECAST, base=TOK_BASE, state_file=str(STATE), set_at=NOW,
                          max_calls=CAP, calls_base=CALL_BASE, **kw)


def running(mid: str, max_calls=CAP) -> dict:
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    owner = {"session_id": f"{mid}-w", "pid": None, "proc_start": None, "heartbeat_at": NOW, "epoch": 1,
             "kind": "background"}
    TOKENS[mid], CALLS[mid] = TOK_BASE, CALL_BASE
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW, state=gm.RUNNING,
                  epoch=1, max_hours=100.0, owner=owner, token_estimate=1_000_000_000)
    return gm.set_envelope(mid, phase_lease={"phase": "1", "forecast": FORECAST, "state_file": str(STATE),
                                             "max_calls": max_calls}, now=NOW)


def sweep(mid: str, stops: list):
    rows = gm.supervise(now=NOW + 60, sessions=[{"sessionId": f"{mid}-w", "id": f"{mid}-w"[:8], "kind": "background",
                                                 "state": "running"}], runner=lambda *a, **k: "",
                        stop_runner=lambda a: stops.append(a), pid_alive=gone, gsd_status=OK_GSD,
                        fingerprint=lambda wd: None)
    return gm.load(mid)


def transcript(path: Path, calls: list[list[tuple[str, dict]]]) -> Path:
    rows = []
    for i, tools in enumerate(calls):
        rows.append({"timestamp": f"2026-10-22T10:00:{i:02d}", "uuid": f"u{i}", "message": {
            "id": f"m{i}", "model": "x", "usage": {"input_tokens": 1},
            "content": [{"type": "tool_use", "name": n, "input": inp} for n, inp in tools]}})
        rows.append({"timestamp": f"2026-10-22T10:00:{i:02d}", "uuid": f"d{i}", "message": {
            "id": f"m{i}", "model": "x", "usage": {"input_tokens": 1}, "content": []}})   # same call, second row
    rows.append({"timestamp": "2026-10-22T11:00:00", "uuid": "s", "message": {
        "id": "syn", "model": "<synthetic>", "usage": {"input_tokens": 1}, "content": []}})
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return path


def main() -> int:
    STATE.write_text("---\ncurrent_phase: 1 - test\n---\n", encoding="utf-8")

    # --- pure judge: the boundary authority
    L = lease()
    j = lambda calls, spent=TOK_BASE + 10, now="1", lz=L: pls.judge(lz, spent, now, calls)  # noqa: E731
    check("V-BND-JUDGE-UNDER-CAP-OK", j(CALL_BASE + CAP - 1)["verdict"] == pls.OK, "5 of 6 calls")
    check("V-BND-JUDGE-AT-CAP-OK", j(CALL_BASE + CAP)["verdict"] == pls.OK, "the cap itself is allowed")
    r = j(CALL_BASE + CAP + 1)
    check("V-BND-JUDGE-OVER-CAP-TRIPS", r["verdict"] == pls.TRIP and "max_calls 6" in r["reason"] and r["calls"] == CAP + 1,
          r.get("reason", ""))
    check("V-BND-JUDGE-TOKENS-FINE-STILL-TRIPS", r.get("spend") == 10, "tokens were 10 of a 1,000,000 forecast")
    check("V-BND-JUDGE-UNMEASURED-BLOCKED", j(None)["verdict"] == pls.BLOCKED, "unmeasured is not zero")
    check("V-BND-JUDGE-BELOW-BASE-BLOCKED", j(CALL_BASE - 1)["verdict"] == pls.BLOCKED, "baseline not this lineage's")
    plain = pls.make_lease(phase="1", forecast=FORECAST, base=TOK_BASE, state_file=str(STATE), set_at=NOW)
    check("V-BND-NO-MAX-CALLS-UNCHANGED", pls.judge(plain, TOK_BASE + 10, "1", 10**9)["verdict"] == pls.OK
          and "max_calls" not in plain, "a lease without max_calls ignores the call count")
    tok = pls.judge(L, TOK_BASE + int(FORECAST * 1.6), "1", CALL_BASE + 1)
    check("V-BND-TOKEN-TRIP-KEPT", tok["verdict"] == pls.TRIP and "phase breaker" in tok["reason"], tok["reason"])
    for label, kw in (("zero", {"max_calls": 0, "calls_base": 1}), ("bool", {"max_calls": True, "calls_base": 1}),
                      ("no-base", {"max_calls": 5, "calls_base": None})):
        try:
            pls.make_lease(phase="1", forecast=5, base=0, state_file="s", set_at=NOW, **kw)
            check(f"V-BND-MAKE-REFUSES-{label}", False, "accepted")
        except pls.LeaseError as exc:
            check(f"V-BND-MAKE-REFUSES-{label}", True, str(exc)[:70])

    # --- set_envelope measures the call base; the breaker refuses over the cap and admits under it
    rec = running("m-bnd-set")
    pl = rec.get("phase_lease") or {}
    check("V-BND-SET-MEASURES-CALL-BASE", pl.get("calls_base") == CALL_BASE and pl.get("max_calls") == CAP, str(pl))
    CALLS["m-bnd-set"] = None
    try:
        gm.set_envelope("m-bnd-set", phase_lease={"phase": "1", "forecast": FORECAST, "state_file": str(STATE),
                                                  "max_calls": CAP}, now=NOW)
        check("V-BND-SET-REFUSES-UNMEASURED", False, "accepted")
    except gm.MissionError as exc:
        check("V-BND-SET-REFUSES-UNMEASURED", "unmeasurable" in str(exc), str(exc)[:90])
    CALLS["m-bnd-set"] = CALL_BASE

    stops: list = []
    running("m-bnd-ok")
    CALLS["m-bnd-ok"] = CALL_BASE + CAP
    held = sweep("m-bnd-ok", stops)
    check("V-BND-CONTROL-AT-CAP-RUNS", not held.get("owner_hold") and not stops, "at the cap nothing is held")

    running("m-bnd-trip")
    CALLS["m-bnd-trip"] = CALL_BASE + CAP + 1
    held = sweep("m-bnd-trip", stops)
    oh = held.get("owner_hold") or {}
    check("V-BND-OVER-CAP-HOLDS", oh.get("phase_breaker") is True and "max_calls" in str(oh.get("reason", oh)) and stops,
          str(oh)[:160])

    # --- boundary ledger and PGO
    t = transcript(Path(TMP) / "t.jsonl", [
        [("Read", {"file_path": "a.py"}), ("Read", {"file_path": "b.py"})],
        [("Read", {"file_path": "a.py"})],
        [("Grep", {"pattern": "x"})],
        [("Edit", {"file_path": "a.py"})],
        [("Bash", {"command": "python tools/test_x.py"})],
        [("Read", {"file_path": "a.py"})],
    ])
    calls = bl.read_calls(t)
    lg = bl.ledger(calls)
    check("V-BND-LEDGER-COUNTS-CALLS-NOT-ROWS", lg["calls"] == 6, f"6 calls from 13 rows, synthetic skipped: {lg['calls']}")
    check("V-BND-LEDGER-CLASSES", (lg["discovery_calls"], lg["write_calls"], lg["test_calls"], lg["parallel_calls"])
          == (4, 1, 1, 1), str({k: lg[k] for k in ("discovery_calls", "write_calls", "test_calls", "parallel_calls")}))
    check("V-BND-LEDGER-REREADS", lg["reread_calls"] == 2 and lg["rereads"] == {"a.py": 3}
          and lg["rediscovery_ratio"] == round(2 / 6, 3), str(lg["rereads"]))
    check("V-BND-LEDGER-EMPTY", bl.ledger([])["rediscovery_ratio"] is None, "no calls, no ratio")
    s = bl.suggest_max_calls([10, 12, 20, 40, 15])
    check("V-BND-PGO-P80", s["max_calls"] == 25 and s["p80"] == 20 and s["n"] == 5, "nearest-rank p80 of 5 is the 4th: " + str(s))
    s2 = bl.suggest_max_calls([10, 12])
    check("V-BND-PGO-FEW-SAMPLES-NONE", s2["max_calls"] is None and "no call profile" in s2["reason"], str(s2))
    check("V-BND-PGO-IGNORES-JUNK", bl.suggest_max_calls([10, True, 0, -3, 12, 20])["n"] == 3, "bool/zero/negative dropped")

    print(f"BOUNDARY_PASS={passes}/{passes + fails}  threshold=all")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
