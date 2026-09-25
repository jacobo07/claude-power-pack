#!/usr/bin/env python3
"""V-ROUTE-* gates for modules/provider_routing (UWCP assimilation R4).

Every refusal predicate is driven with a candidate that trips exactly it, and a
control candidate in the same chain that must be selected, so a router refusing
everything fails. The ledger race runs in real processes at the cap boundary.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.provider_routing import (AUTH_FAILED, AVAILABLE, FAILED, LEAKED, Budget,  # noqa: E402
                                      Candidate, ConfigError, RouteInput, SpendLedger,
                                      classify_cli, classify_server, decide, read_count)
from modules.keos_qwen.outcome import HARNESS_FAILED, OK, TRUNCATED, UNAVAILABLE  # noqa: E402

passes = fails = 0
NOW = 10_000.0


def check(gate, cond, good, bad):
    global passes, fails
    if cond:
        passes += 1
        print(f"  PASS {gate}: {good}")
    else:
        fails += 1
        print(f"  FAIL {gate}: {bad}")


def cand(name, **kw):
    base = dict(window_group=f"{name}-win", ctx_window=32768, availability=AVAILABLE,
                availability_measured_at=NOW - 10, budget=Budget("acct", 0, 4))
    base.update(kw)
    return Candidate(name, **base)


def route(chain, **kw):
    base = dict(obligation_class="impl", prompt_tokens=6000, chain=tuple(chain), now=NOW,
                max_availability_age_s=300)
    base.update(kw)
    return decide(RouteInput(**base))


def trips(gate, bad, reason, **kw):
    rec = route([bad, cand("control")], **kw)
    row = rec["candidates"][0]
    check(gate, not row["feasible"] and row["refusal_reason"] == reason
          and rec["selected"] == "control" and rec["fallback_depth"] == 1,
          f"refused for {reason}; the next rung is selected", f"{rec}")


def main() -> int:
    trips("V-ROUTE-STALE", cand("a", availability_measured_at=NOW - 301), "stale_availability")
    trips("V-ROUTE-NEVER-MEASURED", cand("a", availability_measured_at=None), "stale_availability")
    trips("V-ROUTE-UNAVAILABLE", cand("a", availability=UNAVAILABLE), "provider_unavailable")
    trips("V-ROUTE-UNKNOWN-AVAIL", cand("a", availability="UNKNOWN"), "provider_unavailable")
    trips("V-ROUTE-AUTH", cand("a", availability=AUTH_FAILED), "auth_failed")
    trips("V-ROUTE-CTX-UNKNOWN", cand("a", ctx_window=None), "unknown_context_window")
    trips("V-ROUTE-OVER-CTX", cand("a", ctx_window=4096), "over_context")
    trips("V-ROUTE-BUDGET-UNKNOWN", cand("a", budget=None), "budget_unknown")
    trips("V-ROUTE-BUDGET-SPENT", cand("a", budget=Budget("acct", 4, 4)), "budget_spent")
    trips("V-ROUTE-SAME-SIG", cand("a", recent_signatures=("x", "y", "y")), "same_signature_twice")
    trips("V-ROUTE-VISITED", cand("a"), "visited_this_epoch", visited=("a",))
    trips("V-ROUTE-WINDOW-TRUNCATED", cand("a", window_group="qwen-32k"),
          "window_truncated_this_epoch", truncated_groups=("qwen-32k",))

    rec = route([cand("harness", window_group="qwen-32k"), cand("codex", window_group="qwen-32k"),
                 cand("frontier", window_group="frontier-200k", ctx_window=200000)],
                truncated_groups=("qwen-32k",))
    check("V-ROUTE-TRUNCATED-SKIPS-SIBLINGS", rec["selected"] == "frontier",
          "TRUNCATED on one qwen rung skips every rung with the same window", f"{rec['selected']}")
    rec = route([cand("unbudgeted", budget=None, budgeted=False)])
    check("V-ROUTE-UNBUDGETED-CONTROL", rec["selected"] == "unbudgeted",
          "a provider with no quota at all is not refused for a missing ledger", f"{rec}")
    rec = route([cand("a", availability=UNAVAILABLE), cand("b", budget=None)])
    check("V-ROUTE-BLOCKED", rec["selected"] is None and rec["blocked"]
          and all(r["refusal_reason"] for r in rec["candidates"]),
          "nothing feasible -> BLOCKED with every reason named, never a default", f"{rec}")
    try:
        route([cand("a"), cand("a")])
        check("V-ROUTE-NO-REVISIT", False, "", "a chain naming a provider twice was accepted")
    except ConfigError:
        check("V-ROUTE-NO-REVISIT", True, "a chain naming one provider twice is refused", "")
    r1 = route([cand("a"), cand("b")])
    r2 = route([cand("a"), cand("b")])
    check("V-ROUTE-REPLAYABLE", json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True)
          and r1["candidates"][0]["ctx_window"] == 32768,
          "same input, byte-identical record carrying every input", "records differ")

    # --- classification ---------------------------------------------------------
    c = classify_cli(0, "Claude AI usage limit reached|1760000000")
    check("V-ROUTE-EXIT0-QUOTA", c.outcome == UNAVAILABLE and c.retries == 0,
          "exit 0 with a limit message is UNAVAILABLE, not OK", f"{c}")
    c = classify_cli(0, "Invalid API key · Please run /login")
    check("V-ROUTE-EXIT0-AUTH", c.outcome == AUTH_FAILED, "exit 0 with an auth message is AUTH_FAILED", f"{c}")
    check("V-ROUTE-CLEAN-OK", classify_cli(0, "All tests pass.").outcome == OK,
          "a clean exit 0 is OK (control)", "clean run misclassified")
    check("V-ROUTE-EXIT-NONZERO", classify_cli(2, "Traceback ...").outcome == FAILED,
          "non-zero exit without limit/auth text is FAILED", "misclassified")
    check("V-ROUTE-NO-EXIT", classify_cli(None, "").outcome == HARNESS_FAILED,
          "no exit status is HARNESS_FAILED (the run was not observed)", "misclassified")
    check("V-ROUTE-GATE-REFUSED", classify_cli(0, "done", gate_passed=False).outcome == FAILED,
          "exit 0 whose result the gate refused is FAILED", "misclassified")
    check("V-ROUTE-SERVER-LENGTH", classify_server("length").outcome == TRUNCATED
          and classify_server("weird").outcome == HARNESS_FAILED and classify_server("stop").outcome == OK,
          "server finish_reason reuses keos_qwen's positive mapping", "server mapping drifted")

    # --- config -------------------------------------------------------------------
    check("V-ROUTE-ZERO-IS-ZERO", read_count("0", "cap") == 0 and read_count(0, "cap") == 0,
          "a configured 0 reads as 0", "0 misread")
    bad = []
    for raw in (None, "", "  ", "-1", "four"):
        try:
            read_count(raw, "cap")
            bad.append(raw)
        except ConfigError:
            pass
    check("V-ROUTE-MISSING-IS-ERROR", not bad, "missing/blank/negative/non-integer caps raise",
          f"accepted {bad}")

    # --- ledger -------------------------------------------------------------------
    class Clock:
        t = 1_760_000_000.0

        def __call__(self):
            return self.t
    clk = Clock()
    L = SpendLedger(tempfile.mkdtemp(prefix="spend-"), caps={"claude-p": 4}, leak_after_s=3600, clock=clk)
    got = [L.reserve(f"r{i}", "claude-p").ok for i in range(5)]
    check("V-LEDGER-CAP", got == [True, True, True, True, False],
          "the fifth reservation in one window is refused at cap 4", f"{got}")
    again = L.reserve("r0", "claude-p")
    check("V-LEDGER-REPLAY", again.ok and again.used == 4,
          "replaying a reservation id returns the original grant without spending again", f"{again}")
    L.release("r3")
    check("V-LEDGER-RELEASE", L.reserve("r5", "claude-p").ok,
          "a released reservation gives the unit back", "released unit not returned")

    clk2 = Clock()
    clk2.t = 1_760_054_399.9                       # 23:59:59.9 UTC on 2025-10-09
    L2 = SpendLedger(tempfile.mkdtemp(prefix="spend-"), caps={"p": 1}, leak_after_s=3600, clock=clk2)
    a = L2.reserve("late", "p")
    clk2.t += 1.0                                   # commit lands on the next UTC day
    L2.commit("late")
    b = L2.reserve("next", "p")
    check("V-LEDGER-WINDOW-AT-RESERVE", a.ok and b.ok and a.window != b.window,
          f"the late spend belongs to {a.window}, not the day it committed on ({b.window})",
          f"a={a} b={b}")

    clk3 = Clock()
    L3 = SpendLedger(tempfile.mkdtemp(prefix="spend-"), caps={"p": 1}, leak_after_s=60, clock=clk3)
    L3.reserve("crashed", "p")                     # reserved, then the spawner died
    clk3.t += 61
    blocked = L3.reserve("next", "p")
    st = L3.state()
    check("V-LEDGER-LEAK-COUNTS", not blocked.ok and st["crashed"]["state"] == LEAKED,
          "an abandoned reservation becomes LEAKED and still counts as spent", f"{blocked} {st}")

    # real processes at the cap boundary: 3 of 4 used, 5 contenders -> exactly one wins
    d = Path(tempfile.mkdtemp(prefix="spend-race-"))
    base = SpendLedger(d, caps={"p": 4}, leak_after_s=3600)
    for i in range(3):
        base.commit(f"pre{i}") if base.reserve(f"pre{i}", "p").ok else None
    code = ("import sys,time,json;sys.path.insert(0,sys.argv[1]);from pathlib import Path;"
            "from modules.provider_routing import SpendLedger;"
            "L=SpendLedger(sys.argv[2],caps={'p':4},leak_after_s=3600);go=Path(sys.argv[2])/'go'\n"
            "while not go.exists(): time.sleep(0.001)\n"
            "print(json.dumps(L.reserve(sys.argv[3],'p').ok))")
    procs = [subprocess.Popen([sys.executable, "-c", code, str(ROOT), str(d), f"c{i}"],
                              stdout=subprocess.PIPE, text=True) for i in range(5)]
    time.sleep(1.5)
    (d / "go").write_text("1")
    wins = sum(json.loads(p.communicate(timeout=60)[0].strip().splitlines()[-1]) for p in procs)
    check("V-LEDGER-RACE", wins == 1, "five processes at 3/4: exactly one reservation wins",
          f"wins={wins}")

    # the race above passed with the lock removed (mutation drill, 2026-09-25): prove the
    # exclusive section deterministically -- a child holds it for 2 s, reserve must wait
    d = Path(tempfile.mkdtemp(prefix="spend-lock-"))
    SpendLedger(d, caps={"p": 4}, leak_after_s=3600)
    hold = ("import sys,time;sys.path.insert(0,sys.argv[1]);from pathlib import Path;"
            "from modules.provider_routing import SpendLedger;"
            "L=SpendLedger(sys.argv[2],caps={'p':4},leak_after_s=3600)\n"
            "with L._lock:\n (Path(sys.argv[2])/'inside').write_text('1'); time.sleep(2.0)\n")
    hp = subprocess.Popen([sys.executable, "-c", hold, str(ROOT), str(d)])
    t0 = time.monotonic()
    while not (d / "inside").exists() and time.monotonic() - t0 < 30:
        time.sleep(0.01)
    t1 = time.monotonic()
    ok = SpendLedger(d, caps={"p": 4}, leak_after_s=3600).reserve("w", "p").ok
    waited = time.monotonic() - t1
    hp.wait(timeout=30)
    check("V-LEDGER-LOCK-BLOCKS", ok and waited >= 1.0,
          f"a reserve while another process holds the ledger waits for it ({waited:.2f}s)",
          f"ok={ok} waited={waited:.2f}s")

    print(f"ROUTE_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
