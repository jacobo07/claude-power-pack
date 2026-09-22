#!/usr/bin/env python3
"""V-gates for the observe-only /cpp-gsd-long provider (C7).

Driven against the REAL ledger reader (`gsd_long_run.ledger_events`) with its
state directory redirected, so the mapping is proven against the tool's own
vocabulary rather than against a restatement of it.

    python tools/test_gsd_x_goal_long_run_provider.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

STATE = Path(tempfile.mkdtemp(prefix="gsdx_lr_state_"))
os.environ["GSD_LONG_RUN_STATE_DIR"] = str(STATE)      # before the tool is imported

from modules.gsd_x.goal import epoch as ep                        # noqa: E402
from modules.gsd_x.goal.providers.long_run import LongRunProvider  # noqa: E402

LEDGER = STATE / "gsd-autorun-ledger.jsonl"


def write_ledger(rows: list[dict]) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def spec(sid: str, token: str = "tok"):
    return {"epoch_id": "ep-lr", "revision": "rev1", "bind_session": sid,
            "identity": {"run_token": token, "epoch_id": "ep-lr"}}


def main() -> int:
    passes: list[str] = []
    fails: list[str] = []

    def ok(g, ev):
        passes.append(g)
        print(f"  PASS {g}: {ev}")

    def bad(g, why):
        fails.append(g)
        print(f"  FAIL {g}: {why}")

    def check(g, cond, ev, why):
        (ok if cond else bad)(g, ev if cond else why)

    prov = LongRunProvider(Path(tempfile.mkdtemp(prefix="gsdx_lr_runs_")))
    ep.check_provider(prov)
    ok("V-LR-PROVIDER-CONTRACT", "the provider satisfies the contract with a wall bound")

    sid = "11111111-2222-3333-4444-555555555555"
    write_ledger([{"session_id": sid, "event": "armed"},
                  {"session_id": sid, "event": "crossing"},
                  {"session_id": sid, "event": "resume_confirmed"}])

    # --- binding, not starting ------------------------------------------------
    try:
        prov.dispatch({**spec(sid), "bind_session": ""})
        bad("V-LR-CANNOT-START", "the provider claimed to start a run")
    except ep.EpochError as exc:
        check("V-LR-CANNOT-START", "cannot start" in str(exc),
              "starting a run is refused, and the reason names the pane that owns it",
              f"wrong reason: {exc}")
    try:
        prov.dispatch(spec("99999999-0000-0000-0000-000000000000"))
        bad("V-LR-BIND-UNKNOWN", "a session with no ledger rows was bound")
    except ep.EpochError:
        ok("V-LR-BIND-UNKNOWN", "binding a session that does not exist refused")
    handle = prov.dispatch(spec(sid))
    check("V-LR-BIND", handle["session_id"] == sid,
          "an armed session is bound as an epoch handle", f"handle={handle}")

    # --- ledger vocabulary -> epoch endings -------------------------------------
    cases = [
        ([], ep.OBS_UNKNOWN, "", "V-LR-NO-ROWS-UNKNOWN",
         "no ledger rows is UNKNOWN, never LOST -- we could not ask"),
        ([{"session_id": sid, "event": "armed"}], ep.OBS_RUNNING, "",
         "V-LR-RUNNING", "an armed run with no terminal row is running"),
        ([{"session_id": sid, "event": "armed"},
          {"session_id": sid, "event": "finished", "reason": "milestone complete"}],
         ep.OBS_ENDED, ep.COMPLETED, "V-LR-FINISHED", "finished -> completed"),
        ([{"session_id": sid, "event": "halted", "kind": "budget",
           "reason": "cycle budget spent"}],
         ep.OBS_ENDED, ep.EXPIRED, "V-LR-HALTED-BUDGET", "a spent budget -> expired"),
        ([{"session_id": sid, "event": "halted", "kind": "mission",
           "reason": "mission STALE"}],
         ep.OBS_ENDED, ep.STALE_REVISION, "V-LR-HALTED-MISSION",
         "a mission that no longer matches -> stale_revision, not expired"),
        ([{"session_id": sid, "event": "reaped", "reason": "transcript gone"}],
         ep.OBS_ENDED, ep.LOST, "V-LR-REAPED", "reaped -> lost"),
    ]
    for rows, state, outcome, gate, why in cases:
        write_ledger(rows)
        obs = prov.observe(handle)
        check(gate, obs.state == state and obs.outcome == outcome, why,
              f"got state={obs.state} outcome={obs.outcome} detail={obs.detail}")

    # --- harvest ---------------------------------------------------------------
    write_ledger([{"session_id": sid, "event": "armed"},
                  {"session_id": sid, "event": "crossing"},
                  {"session_id": sid, "event": "resume_confirmed"},
                  {"session_id": sid, "event": "crossing"},
                  {"session_id": sid, "event": "resume_confirmed"},
                  {"session_id": sid, "event": "stalled", "reason": "idle 20m"}])
    r = prov.harvest(handle, spec(sid))
    check("V-LR-HARVEST-NO-VERDICT", r.verdicts == [],
          "a long run yields NO verdict: it is work, not proof",
          f"verdicts={r.verdicts}")
    check("V-LR-HARVEST-COUNTS",
          r.cost["crossings"] == 2 and r.cost["resumes_confirmed"] == 2,
          "the receipt carries the run's own crossings and confirmed resumes",
          f"cost={r.cost}")
    check("V-LR-HARVEST-FAILURES",
          any(f["signature"].startswith("longrun-stalled") for f in r.failures),
          "a stall is harvested as a failure with a signature", f"failures={r.failures}")

    # --- cancellation and recovery -----------------------------------------------
    try:
        prov.cancel(handle)
        bad("V-LR-CANCEL-REFUSED", "the provider cleared another pane's run")
    except ep.EpochError:
        ok("V-LR-CANCEL-REFUSED", "stopping a run owned by another pane is refused")
    check("V-LR-PROBE", (prov.probe({"run_token": "tok"}) or {}).get("session_id") == sid,
          "a binding made before a crash is found by its pre-minted token",
          f"probe={prov.probe({'run_token': 'tok'})}")
    check("V-LR-PROBE-NONE", prov.probe({"run_token": "never"}) is None,
          "an unbound token probes to None", "probe invented a binding")

    total = len(passes) + len(fails)
    print(f"\nGSDX_LONGRUN_PROVIDER_PASS={len(passes)}/{total}  threshold={total}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
