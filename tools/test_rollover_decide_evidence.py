#!/usr/bin/env python
"""V-DEV-* gates: decide() with remaining-work EVIDENCE instead of HORIZON_CALLS=30 (plan ccp-s16
§16.1 D1a). Pure: evidence is passed in, never loaded here. Both poles are driven, and the cases that
must NOT roll (UNKNOWN, UNDETERMINED, rehydration unknown) are shown against a break-even the old
constant 30 would have accepted -- so a mutant that falls back to 30 goes red."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rollover as ro  # noqa: E402

PASS = FAIL = 0


def ok(gate, cond, ev=""):
    global PASS, FAIL
    PASS += bool(cond)
    FAIL += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def prior(values):
    return {"basis": "MEASURED_PRIOR", "values": sorted(values), "computed_at": 1.0}


def main() -> int:
    usage = {"state": "OK", "floor": 130_000, "resident": 600_000, "model": "claude-opus-5-5", "calls": 50}
    ratio = ro.price_ratio("claude-opus-5-5")
    ok("V-DEV-PRICED", ratio.get("state") == "OK", str(ratio))
    small_c = {"basis": "UPPER_BOUND_P50", "tokens": 10_000}
    ask = lambda h, reh=small_c, boundary=True, used=None: ro.decide(usage, 4000, boundary, used, ratio,
                                                                      horizon=h, rehydration=reh)

    base = ro.decide(usage, 4000, True, None, ratio)                      # int path unchanged
    n_star = base["breakeven_calls"]
    ok("V-DEV-INT-PATH-UNCHANGED", base["would_rollover"] and base["horizon_basis"] == "ESTIMATE"
       and n_star is not None and n_star <= ro.HORIZON_CALLS, f"n*={n_star} {base['reason']}")

    d = ask(prior([200] * 10))
    ok("V-DEV-ROBUST-ROLLOVER", d["would_rollover"] and d["economics"] == "ROBUST_ROLLOVER"
       and d["horizon_basis"] == "MEASURED_PRIOR", d["reason"])
    d = ask(prior([1] * 10))
    ok("V-DEV-ROBUST-CONTINUE", not d["would_rollover"] and d["economics"] == "ROBUST_CONTINUE", d["reason"])
    d = ask(prior([1] * 5 + [200] * 5))
    ok("V-DEV-UNDETERMINED-NO-ASK", not d["would_rollover"] and d["economics"] == "UNDETERMINED", d["reason"])

    edge = prior([int(n_star) + 2] * 10)                                  # pays back only without rehydration
    d = ask(edge, {"basis": "UPPER_BOUND_P50", "tokens": 20_000_000})
    ok("V-DEV-REHYDRATION-COUNTS", not d["would_rollover"] and d["economics"] == "UNDETERMINED"
       and d["breakeven_calls_hi"] > d["breakeven_calls"], d["reason"])
    d = ask(prior([200] * 10), None)
    ok("V-DEV-REHYDRATION-UNKNOWN-NOT-ROBUST", not d["would_rollover"] and d["economics"] == "UNDETERMINED",
       d["reason"])

    d = ask({"basis": "UNKNOWN", "reason": "prior expired"})
    ok("V-DEV-UNKNOWN-STAYS-UNKNOWN", not d["would_rollover"] and d["economics"] == ro.UNKNOWN
       and d["horizon_calls"] is None, f"{d['reason']} (n*={n_star} would pass the old 30)")
    d = ask(prior([200] * 10), boundary=False)
    ok("V-DEV-BOUNDARY-STILL-REQUIRED", not d["would_rollover"] and "boundary" in d["reason"], d["reason"])
    d = ask(prior([1] * 10), used=80.0)
    ok("V-DEV-PRESSURE-STILL-WINS", d["would_rollover"] and d["reason"].startswith("pressure"), d["reason"])
    d = ask(prior([200] * 10))
    ok("V-DEV-RECEIPT-FIELDS", all(k in d for k in ("share_at_breakeven", "share_at_breakeven_hi",
                                                    "rehydration_basis", "horizon_n", "horizon_computed_at")),
       str(sorted(d)))
    print(f"DECIDE_EVIDENCE_PASS={PASS}/{PASS + FAIL}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
