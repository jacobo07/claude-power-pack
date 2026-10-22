#!/usr/bin/env python
"""V-ACC-* gates: a worker the supervisor stops is booked to its goal ledger, once, subagents included.

CCR v5 Stage A, Phase 2. Measured 2026-10-14/15: the epoch-1 worker af436132 was stopped by a breaker and its
real usage (29.5M) stayed 4.4M above what the ledger held, because nothing settled a stopped session. These
gates drive the real supervise stop path, the real goal ledger and real transcript files in a temp state dir.
Each refusal has a paired control.
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="accounting-authority-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["CLAUDE_CONFIG_DIR"] = str(Path(TMP) / "cfg")
os.environ.pop("CPP_COST_HOLD_STOP", None)
os.environ.pop("CLAUDECODE", None)
os.environ.pop("CPP_GOAL", None)
os.environ["CPP_MISSION_RECOVERY"] = "off"
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import gsd_mission as gm  # noqa: E402
import mission_spend as ms  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None

passes = fails = 0
NOW = 1_800_000_000.0
BASE = 5_000_000
FORECAST = 1_000_000
HOST = socket.gethostname()
STATE = Path(TMP) / "STATE.md"
SPEND: dict[str, int] = {}
PROJ = Path(TMP) / "cfg" / "projects" / "p"
gone = lambda pid: False  # noqa: E731
OK_GSD = lambda cwd, workstream=None: {"outcome": "OK"}  # noqa: E731


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


ms.processed_tokens = lambda rec: SPEND[rec["mission_id"]]


def _row(mid, n, idx):
    u = {"input_tokens": n, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": 0}
    return json.dumps({"type": "assistant", "uuid": f"u-{mid}-{idx}", "message": {
        "id": mid, "model": "claude-opus-5-5", "usage": u, "content": [{"type": "text", "text": "x"}]}}) + "\n"


def transcript(sid, main, subs=None):
    """main: [(message id, tokens)]; subs: {agent id: [(message id, tokens)]}."""
    PROJ.mkdir(parents=True, exist_ok=True)
    (PROJ / f"{sid}.jsonl").write_text("".join(_row(m, n, i) for i, (m, n) in enumerate(main)), encoding="utf-8")
    for aid, rows in (subs or {}).items():
        d = PROJ / sid / "subagents"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"agent-{aid}.jsonl").write_text("".join(_row(m, n, i) for i, (m, n) in enumerate(rows)),
                                              encoding="utf-8")


def ledger_state():
    led = ms._goal_ledger("ccr")
    with led._lock:
        g = led._gfold(led._read())
    return g, sum(1 for r in led._read() if r.get("op") == "settle" and r.get("stopped"))


def worker(mid, goal="ccr"):
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    sid = f"{mid}-w"
    owner = {"session_id": sid, "pid": None, "proc_start": None, "heartbeat_at": NOW, "epoch": 1, "kind": "background"}
    SPEND[mid] = BASE
    extra = {"ledger_goal": goal} if goal else {}
    gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW, state=gm.RUNNING,
                  epoch=1, max_hours=100.0, owner=owner, token_estimate=1_000_000_000, **extra)
    gm.set_envelope(mid, phase_lease={"phase": "1", "forecast": FORECAST, "state_file": str(STATE)}, now=NOW)
    return sid


def sweep(mid, stops):
    rows = gm.supervise(now=NOW + 60, sessions=[{"sessionId": f"{mid}-w", "id": f"{mid}-w"[:8],
                                                  "kind": "background", "state": "running"}],
                        runner=lambda *a, **k: "", stop_runner=lambda a: stops.append(a), pid_alive=gone,
                        gsd_status=OK_GSD, fingerprint=lambda wd: None)
    return {x["mission_id"]: x for x in rows}.get(mid), gm.load(mid)


def events(mid, kind):
    return [e for e in gm.lr.ledger_events(mid) if e.get("event") == kind] if hasattr(gm.lr, "ledger_events") else []


def main() -> int:
    STATE.write_text("---\ncurrent_phase: 1 - test\n---\n", encoding="utf-8")
    root = Path(TMP) / "goalroot"
    root.mkdir()
    ms.goal_declare("ccr", 50_000_000, "test", [str(root)], None, 1, owner=True)

    # 1. a breaker-stopped worker: main 1,000 + subagent 900 where msg m2 appears in BOTH files -> 1,500 counted once.
    sid = worker("m-acc-stop")
    ms.goal_renew("ccr", sid, 0, 1000, HOST)               # the guard's lease: an open hold for this session
    transcript(sid, [("m1", 600), ("m2", 400)], {"a1": [("m2", 400), ("m3", 500)]})
    SPEND["m-acc-stop"] = BASE + int(FORECAST * 1.5) + 1
    stops: list = []
    row, r = sweep("m-acc-stop", stops)
    g, nsettle = ledger_state()
    check("V-ACC-STOP-BOOKS-TREE-ONCE-BY-MESSAGE-ID", g["marks"].get(sid) == 1500,
          f"mark={g['marks'].get(sid)} (main 1,000 + subagent 500 new; duplicate m2 not recounted)")
    check("V-ACC-STOP-CLOSES-HOLDS", not [x for x in g["res"].values() if x["sid"] == sid and x["state"] in
                                          ("RESERVED", "LEAKED")], "no open hold for the stopped session")
    check("V-ACC-ROW-REPORTS-SETTLED", (row or {}).get("settled", {}).get("booked") is True
          and r.get("owner_hold", {}).get("worker_stopped_at"), str((row or {}).get("settled")))
    check("V-ACC-LEDGER-ROW-WORKER-SETTLED", len(events("m-acc-stop", "worker_settled")) == 1,
          "one worker_settled row on the mission ledger")

    # 2. booked exactly once: settling the same worker again, and sweeping again, add nothing.
    again = gm.settle_stopped_worker(gm.load("m-acc-stop"))
    row2, _ = sweep("m-acc-stop", stops)
    g2, nsettle2 = ledger_state()
    check("V-ACC-SECOND-SETTLE-BOOKS-NOTHING", g2["marks"].get(sid) == 1500 and nsettle2 == nsettle
          and again.get("booked") is True, f"mark={g2['marks'].get(sid)} stopped-settle rows {nsettle}->{nsettle2}")
    check("V-ACC-ONE-STOP-ONE-SETTLE", len(stops) == 1, f"stops={len(stops)}")

    # 3. no double charge: the coordinator is a different session on the same goal; each is booked once.
    coord = "coord-d124ce03"
    ms.goal_renew("ccr", coord, 0, 1000, HOST)
    transcript(coord, [("c1", 700)])
    ms.goal_settle("ccr", coord, None, "coordinator share", tree=True)
    ms.goal_settle("ccr", coord, None, "coordinator share", tree=True)
    g3, _ = ledger_state()
    check("V-ACC-NO-DOUBLE-CHARGE", g3["marks"].get(coord) == 700 and g3["marks"].get(sid) == 1500
          and g3["used"] == 2200, f"coord={g3['marks'].get(coord)} worker={g3['marks'].get(sid)} used={g3['used']}")

    # 4. controls: an unstopped worker books nothing; a mission outside any goal is ledgered unbooked, not silent.
    under = worker("m-acc-under")
    transcript(under, [("u1", 123)])
    SPEND["m-acc-under"] = BASE + int(FORECAST * 0.5)
    stops = []
    sweep("m-acc-under", stops)
    g4, _ = ledger_state()
    check("V-ACC-CONTROL-RUNNING-WORKER-NOT-BOOKED", not stops and under not in g4["marks"], f"stops={len(stops)}")
    orphan = worker("m-acc-nogoal", goal=None)
    transcript(orphan, [("o1", 321)])
    SPEND["m-acc-nogoal"] = BASE + int(FORECAST * 1.5) + 1
    stops = []
    row, _ = sweep("m-acc-nogoal", stops)
    g5, _ = ledger_state()
    check("V-ACC-NO-GOAL-IS-LEDGERED-NOT-SILENT", (row or {}).get("settled", {}).get("booked") is False
          and len(events("m-acc-nogoal", "worker_unbooked")) == 1 and orphan not in g5["marks"],
          str((row or {}).get("settled")))
    blind = worker("m-acc-blind")
    SPEND["m-acc-blind"] = BASE + int(FORECAST * 1.5) + 1
    stops = []
    row, _ = sweep("m-acc-blind", stops)          # no transcript on disk: settle refuses blind
    check("V-ACC-BLIND-SETTLE-IS-LEDGERED", (row or {}).get("settled", {}).get("booked") is False
          and len(events("m-acc-blind", "worker_unbooked")) == 1 and blind not in ledger_state()[0]["marks"],
          str((row or {}).get("settled")))

    # 5. derived estimate: arm/envelope read the open routes off the roadmap, they are not chosen by the caller.
    rm = Path(TMP) / "ROADMAP.md"
    rm.write_text("### Phase 1: Done one (route 4.5M) — DONE 2026-10-15\n### Phase 2: A (route 2.0M)\n"
                  "### Phase 3: B, C (route 2.0M)\n### Phase 4: D (route 1.5M)\n### Phase 5: E (no figure)\n",
                  encoding="utf-8")
    d = gm.derive_estimate_from_roadmap(str(rm))
    check("V-ACC-DERIVE-SUMS-OPEN-ROUTES-ONLY", d["total"] == 5_500_000 and d["unrouted"] == ["Phase 5"]
          and [n for n, _ in d["open"]] == ["Phase 2", "Phase 3", "Phase 4"], f"{d}")
    big = worker("m-acc-derive")
    rec = gm.set_envelope("m-acc-derive", roadmap=str(rm), now=NOW)
    check("V-ACC-ENVELOPE-USES-DERIVED", rec["token_estimate"] == 5_500_000
          and "derived from 3 open roadmap route" in str(rec.get("token_estimate_basis")), str(rec.get("token_estimate_basis")))
    try:
        gm.set_envelope("m-acc-derive", roadmap=str(rm), token_estimate=9_000_000, now=NOW)
        check("V-ACC-DERIVED-AND-CHOSEN-REFUSED", False, "accepted both")
    except gm.MissionError as exc:
        check("V-ACC-DERIVED-AND-CHOSEN-REFUSED", "not both" in str(exc), str(exc)[:80])
    rm2 = Path(TMP) / "ROADMAP-done.md"
    rm2.write_text("### Phase 1: x (route 1.0M) — DONE\n", encoding="utf-8")
    try:
        gm.derive_estimate_from_roadmap(str(rm2))
        check("V-ACC-ALL-DONE-ROADMAP-REFUSED", False, "derived 0")
    except gm.MissionError as exc:
        check("V-ACC-ALL-DONE-ROADMAP-REFUSED", "no open phase" in str(exc), str(exc)[:80])

    # 6. authority: an estimate above remaining - open - unused recovery reserve is refused; below is admitted.
    troot = Path(TMP) / "tightroot"
    troot.mkdir()
    ms.goal_declare("tight", 8_000_000, "test", [str(troot)], None, 1, owner=True)
    tled = ms._goal_ledger("tight")
    tled.set_programme(8_000_000, "test", inside_agent=False)
    lo = tled.lease_open("s-lease", 2_000_000, prev_lease="L1", reserves={"recovery": 500_000})
    auth = gm.goal_authority("tight")
    check("V-ACC-AUTHORITY-SUBTRACTS-RECOVERY-RESERVE", auth is not None and auth["reserve"] == 500_000
          and auth["available"] == auth["remaining"] - auth["open"] - 500_000 and lo.get("ok"), f"{auth}")
    tgt = worker("m-acc-over", goal="tight")
    try:
        gm.set_envelope("m-acc-over", token_estimate=auth["available"] + 1, now=NOW)
        check("V-ACC-OVER-AUTHORITY-REFUSED", False, "accepted")
    except gm.MissionError as exc:
        check("V-ACC-OVER-AUTHORITY-REFUSED", "exceeds goal tight authority" in str(exc), str(exc)[:110])
    rec = gm.set_envelope("m-acc-over", token_estimate=auth["available"], now=NOW)
    check("V-ACC-CONTROL-AT-AUTHORITY-ADMITTED", rec["token_estimate"] == auth["available"], f"{rec['token_estimate']:,}")
    check("V-ACC-CONTROL-NO-GOAL-NOT-JUDGED", gm.goal_authority("no-such-goal") is None, "unmeasurable is None, not 0")

    print(f"ACCOUNTING_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    shutil.rmtree(TMP, ignore_errors=True)
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
