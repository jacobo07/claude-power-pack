"""V-SWEEP-RALPH-* gates: the retired v2 marker stage must not work on Ralph markers.

Incident 2026-09-27 (spec vault/specs/parent-context-epoch-rotation.md, G0): the sweep's
first stage walked every `gsd-autorun-*.json` marker and asked `gsd-tools` about each one.
Mission workers write markers of the same name (`mode: ralph`), and nothing deleted them
when their mission ended: 403 markers, 399 of terminal missions. On a starved host each
query ran for tens of seconds, passes outlived the 5-minute schedule, the task limit did not
reap the python grandchild, and 7 sweeps piled up. The mission supervisor -- the stage that
rotates workers and enforces budgets -- runs after this one and never got its turn.

A Ralph marker belongs to `gsd_mission.supervise`. The v2 stage may only retire it once its
mission is terminal, and must never ask GSD about it. Everything is redirected to temp dirs.
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
TMP = Path(tempfile.mkdtemp(prefix="sweep-ralph-"))
STATE, HOOKS, PROJECTS, SESSIONS = (TMP / n for n in ("state", "hooks", "projects", "sessions"))
for d in (STATE, HOOKS, PROJECTS, SESSIONS):
    d.mkdir(parents=True)
os.environ.update({"GSD_LONG_RUN_STATE_DIR": str(STATE), "GSD_LONG_RUN_HOOKS_DIR": str(HOOKS),
                   "GSD_LONG_RUN_PROJECTS_DIR": str(PROJECTS), "GSD_LONG_RUN_NO_SPAWN": "1",
                   "GSD_LONG_RUN_SESSIONS_DIR": str(SESSIONS)})
os.environ.pop("_TEST_GSD_STATUS", None)

sys.path.insert(0, str(ROOT / "tools"))
_spec = importlib.util.spec_from_file_location("gsd_long_run", ROOT / "tools" / "gsd_long_run.py")
lr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lr)

passes = fails = 0
gsd_calls: list[str] = []


def check(gate, cond, ev):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate}: {ev}")


def fake_gsd_status(project, timeout=45, workstream=None):
    gsd_calls.append(str(workstream))
    return {"outcome": "OK", "reason": "fake"}


lr.gsd_status = fake_gsd_status


def marker(mission_id: str | None, mode: str | None = "ralph", project: Path | None = None) -> tuple[str, Path]:
    sid = f"swr-{uuid.uuid4()}"
    body = {"session_id": sid, "resume_command": "/gsd-autonomous --ws w",
            "cwd": str(project or PROJECTS), "cycles": 0, "workstream": "w"}
    if mode:
        body["mode"] = mode
    if mission_id:
        body["mission_id"] = mission_id
    p = STATE / f"gsd-autorun-{sid}.json"
    p.write_text(json.dumps(body), encoding="utf-8")
    return sid, p


def mission(mid: str, state: str | None, raw: str | None = None) -> None:
    p = STATE / f"gsd-mission-{mid}.json"
    p.write_text(raw if raw is not None else json.dumps({"mission_id": mid, "state": state, "epoch": 1}),
                 encoding="utf-8")


def transcript(sid: str, project: Path) -> None:
    # A fresh transcript so the clock clause holds every marker: the only way out of
    # this stage for a Ralph marker must be the new mission-state clause.
    d = PROJECTS / "p"
    d.mkdir(exist_ok=True)
    (d / f"{sid}.jsonl").write_text(json.dumps({"type": "user", "cwd": str(project)}) + "\n",
                                    encoding="utf-8")


def main() -> int:
    proj = PROJECTS / "proj"
    proj.mkdir()
    mission("m-halted", "HALTED")
    mission("m-running", "RUNNING")
    mission("m-bad", None, raw="{not json")
    s_term, p_term = marker("m-halted", project=proj)
    s_live, p_live = marker("m-running", project=proj)
    s_none, p_none = marker("m-missing", project=proj)
    s_bad, p_bad = marker("m-bad", project=proj)
    s_ctl, p_ctl = marker(None, mode=None, project=proj)          # a v2-shaped marker: control
    for s in (s_term, s_live, s_none, s_bad, s_ctl):
        transcript(s, proj)

    # Dry run first: it must report the retirement and delete nothing.
    gsd_calls.clear()
    dry = lr.sweep(dry_run=True, explain=True)
    by = {(a.get("session_id"), a.get("action")) for a in dry}
    check("V-SWEEP-RALPH-DRY-REPORTS", (s_term, "retired") in by, f"{sorted(a for _, a in by)}")
    check("V-SWEEP-RALPH-DRY-DELETES-NOTHING", all(p.exists() for p in (p_term, p_live, p_none, p_bad)),
          "all ralph markers still on disk")

    gsd_calls.clear()
    acts = lr.sweep(explain=True)
    by = {(a.get("session_id"), a.get("action")): a for a in acts}
    check("V-SWEEP-RALPH-TERMINAL-RETIRED", (s_term, "retired") in by and not p_term.exists(),
          f"exists={p_term.exists()} row={by.get((s_term, 'retired'))}")
    check("V-SWEEP-RALPH-LIVE-KEPT", p_live.exists() and (s_live, "kept") in by,
          f"row={by.get((s_live, 'kept'))}")
    check("V-SWEEP-RALPH-MISSING-RECORD-KEPT", p_none.exists(),
          "a marker whose mission record is absent is UNKNOWN, never retired")
    check("V-SWEEP-RALPH-UNREADABLE-RECORD-KEPT", p_bad.exists(),
          "an unreadable mission record is UNKNOWN, never retired")
    check("V-SWEEP-RALPH-NO-GSD-QUERY", len(gsd_calls) <= 1,
          f"4 ralph markers + 1 v2 marker -> {len(gsd_calls)} gsd calls")
    # Positive control: the counter sees the v2 marker's query, so the zero contributed by
    # the ralph markers is a measurement and not a patch that failed to bind.
    check("V-SWEEP-RALPH-CONTROL-V2-STILL-ASKS", len(gsd_calls) >= 1,
          f"the v2 marker still asked GSD: {gsd_calls}")
    held = by.get((s_live, "kept"), {}).get("held_by", "")
    check("V-SWEEP-RALPH-KEPT-NAMES-OWNER", "gsd_mission" in held, held)
    ledger = lr.ledger_events(s_term)
    check("V-SWEEP-RALPH-RETIRE-LEDGERED",
          any(e.get("event") == "retired" and e.get("mission_state") == "HALTED" for e in ledger),
          f"{[e.get('event') for e in ledger]}")

    print(f"SWEEP_RALPH_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
