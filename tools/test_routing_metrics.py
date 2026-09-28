"""V-ROUTE-* gates for tools/routing_metrics.py (T8 item 29).

Synthetic ledgers drive every classification from both poles; the vendored analyzer is
called for real through the node bridge. One gate reads the REAL ledger read-only.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import routing_metrics as rm  # noqa: E402

passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


def ev(event, t, **kw):
    base = {"ts": f"2026-09-28T10:{t:02d}:00+00:00", "event": event, "mission_id": "m-aaaaaaaaaaaa",
            "session_id": "m-aaaaaaaaaaaa"}
    base.update(kw)
    return base


MEASURED = {"state": "MEASURED", "model": "claude-x", "calls": 3, "tool_calls": 2,
            "input_tokens": 1000, "output_tokens": 50, "cache_read_tokens": 900, "fresh_input_tokens": 100}
IDLE = dict(MEASURED, tool_calls=0)
REFUSED = {"state": "PROVIDER_REFUSED", "reason": "You've hit your limit"}
MISSING = {"state": "UNMEASURED", "reason": "transcript not found"}


def ledger():
    return [
        ev("mission_prepared", 0, command="/gsd-autonomous"),
        ev("launched", 1, epoch=1, code="c0de"), ev("launch_cause", 1, epoch=1, cause="INITIAL", mechanism="fresh"),
        dict(ev("worker_acked", 2, epoch=1, worker="w-ok"), session_id="m-aaaaaaaaaaaa"),
        ev("launch_claimed", 10, epoch=2),
        ev("launched", 11, epoch=2), ev("launch_cause", 11, epoch=2, cause="CONTEXT_ROTATION", mechanism="fresh"),
        ev("worker_acked", 12, epoch=2, worker="w-idle"),
        ev("launched", 20, epoch=3),  # no cause recorded: legacy epoch
        ev("worker_acked", 21, epoch=3, worker="w-refused"),
        ev("launched", 30, epoch=4), ev("launch_cause", 30, epoch=4, cause="PROCESS_RECOVERY", mechanism="fresh"),
        ev("worker_acked", 31, epoch=4, worker="w-missing"),
        ev("launched", 40, epoch=5), ev("launch_cause", 40, epoch=5, cause="INITIAL", mechanism="fresh"),
        ev("launched", 41, epoch=5),  # relaunch inside the epoch
        ev("worker_acked", 42, epoch=5, worker="w-ok"),
        ev("launched", 50, epoch=6), ev("launch_cause", 50, epoch=6, cause="CONTEXT_ROTATION", mechanism="fresh"),
        ev("worker_acked", 51, epoch=6, worker="w-ok"),
        ev("launch_cause", 55, epoch=6, cause="TURN_CONTINUATION", mechanism="resume"),  # same epoch, later
    ]


USAGE = {"w-ok": MEASURED, "w-idle": IDLE, "w-refused": REFUSED, "w-missing": MISSING}


def main() -> int:
    attempts, unjudged = rm.build_attempts(ledger(), usage_of=USAGE.get)
    by_run = {}
    for a in attempts:
        by_run.setdefault(a["runId"], []).append(a)
    e = lambda n: by_run.get(f"m-aaaaaaaaaaaa#e{n}", [])  # noqa: E731

    check("V-ROUTE-PASSED", e(1) and e(1)[-1]["status"] == "passed" and e(1)[0]["route"] == "INITIAL/fresh:claude-x",
          f"worker that acted = passed on its observed route: {e(1)[:1] and e(1)[0]['route']}")
    check("V-ROUTE-IDLE-FAILS", e(2) and e(2)[-1]["status"] == "failed",
          "a worker that made model calls and never acted is failed, not passed")
    check("V-ROUTE-REFUSAL-FAILS", e(3) and e(3)[-1]["status"] == "failed" and e(3)[-1]["usage"] is None,
          "a provider refusal is failed and carries NO usage (never a zero)")
    check("V-ROUTE-LEGACY-INCOMPLETE", e(3) and e(3)[0]["historyComplete"] is False and e(3)[0]["route"].startswith("unknown/"),
          "an epoch with no recorded cause is history-incomplete, route cause = unknown")
    check("V-ROUTE-UNKNOWN-WITHHELD", not e(4) and any(u["runId"].endswith("#e4") for u in unjudged),
          f"a worker with no transcript is withheld and listed, never failed: {unjudged}")
    check("V-ROUTE-RETRY", [a["phase"] for a in e(5)] == ["initial", "retry"] and e(5)[0]["status"] == "failed"
          and e(5)[1]["status"] == "passed" and [a["sequence"] for a in e(5)] == [1, 2],
          "a relaunch inside one epoch is a retry; only the last launch carries the outcome")
    check("V-ROUTE-FOUNDING-CAUSE", e(6) and e(6)[0]["route"] == "CONTEXT_ROTATION/fresh:claude-x",
          f"a later continuation cause does not relabel the epoch: {e(6)[:1] and e(6)[0]['route']}")
    check("V-ROUTE-NO-COST", all((a["usage"] or {}).get("costUsd") is None for a in attempts),
          "no attempt carries an invented price")

    an = rm.analyze(attempts)
    check("V-ROUTE-BRIDGE", an.get("outcome") == "OK", f"vendored analyzer ran: {an.get('outcome')} {an.get('error', '')}")
    if an.get("outcome") == "OK":
        groups = {g["route"]: g for g in an["value"]["groups"]}
        legacy = groups.get("unknown/unknown:unknown") or {}
        tot = (legacy.get("metrics") or {}).get("inputTokens", {}).get("total", "absent")
        check("V-ROUTE-INCOMPLETE-TOTAL-NULL", tot is None,
              f"an incomplete route's total stays null, not the observed sum: {tot}")
        init = groups.get("INITIAL/fresh:claude-x") or {}
        check("V-ROUTE-CACHE-READ", init.get("cacheReadTokensObserved") == 1800,
              f"cache reads are reported beside the vendor schema: {init.get('cacheReadTokensObserved')}")

    real = rm.report(since="2026-09-20")
    ra = real["analysis"]
    check("V-ROUTE-REAL-LEDGER", ra.get("outcome") == "OK" and real["attempts"] > 0,
          f"real ledger analysed: attempts={real['attempts']} unjudged={len(real['unjudged_runs'])}")
    print(f"ROUTE_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
