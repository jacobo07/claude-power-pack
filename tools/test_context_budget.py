"""V-CTXB gates: modules/context_budget (native port) against vendor/context-budget (upstream).
    python tools/test_context_budget.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from modules import context_budget as cb  # noqa: E402
from modules.external_assimilation import node_bridge as nb  # noqa: E402

passes = fails = 0


def gate(name, cond, evidence):
    global passes, fails
    passes, fails = (passes + 1, fails) if cond else (passes, fails + 1)
    print(f"{'PASS' if cond else 'FAIL'} {name}: {evidence}")


def main() -> int:
    cases = [(-1, 0, 10, 20), (0, 0, 10, 20), (5, 0, 10, 20), (10, 0, 10, 20), (15, 0, 10, 20),
             (20, 0, 10, 20), (99, 0, 10, 20), (3, 3, 3, 9), (6, 3, 3, 9), (150000, 150000, 240000, 300000),
             (270000, 150000, 240000, 300000)]
    mismatches = []
    for v, c, s, k in cases:
        r = nb.call("contextBudget", "normalize", [v, {"comfortable": c, "stressed": s, "critical": k}],
                    package="context-budget")
        mine = cb.normalize(v, c, s, k)
        if not r.ok or abs(float(r.value) - mine) > 1e-9:
            mismatches.append((v, c, s, k, r.outcome, r.value, mine))
    gate("V-CTXB-PARITY-NORMALIZE", not mismatches, f"{len(cases)} cases vs upstream; mismatches={mismatches}")

    r = nb.call("contextBudget", "estimateTokens", ["x" * 17], package="context-budget")
    gate("V-CTXB-PARITY-ESTIMATE", r.ok and r.value == cb.estimate_tokens("x" * 17) == 5, f"{r.value} vs {cb.estimate_tokens('x' * 17)}")

    def boom():
        raise OSError("probe failed")

    # Upstream: a throwing probe contributes 0 -> a broken meter reads comfortable. Ours: UNMEASURED.
    m = cb.Meter([cb.Signal("only", boom, 0, 1, 2)])
    rd = m.reading()
    gate("V-CTXB-UNKNOWN-NOT-ZERO", rd["state"] == cb.UNMEASURED and rd["pressure"] is None,
         f"{rd['state']} pressure={rd['pressure']} reason={rd['signals'][0].get('reason')}")

    m = cb.Meter([cb.Signal("hi", 2.0, 0, 1, 2, weight=1), cb.Signal("dead", None, 0, 1, 2, weight=3)])
    rd = m.reading()
    gate("V-CTXB-COVERAGE-FLOOR", rd["state"] == cb.UNMEASURED and rd["coverage"] == 0.25,
         f"measured weight 1 of 4 -> {rd['state']} coverage={rd['coverage']}")

    m = cb.Meter([cb.Signal("hi", 2.0, 0, 1, 2, weight=3), cb.Signal("dead", None, 0, 1, 2, weight=1)])
    rd = m.reading()
    gate("V-CTXB-PARTIAL", rd["state"] == cb.PARTIAL and rd["pressure"] == 1.0 and rd["band"] == "critical",
         f"{rd['state']} {rd['pressure']} {rd['band']}")

    lo = cb.epoch_reading(context_tokens=60_000, ceiling=300_000, transcript_bytes=500_000,
                          session_age_s=600, pending_children=0)
    hi = cb.epoch_reading(context_tokens=290_000, ceiling=300_000, transcript_bytes=9_000_000,
                          session_age_s=5 * 3600, pending_children=3)
    gate("V-CTXB-EPOCH-POLES", lo["band"] == "comfortable" and hi["band"] == "critical" and lo["state"] == cb.MEASURED,
         f"lo={lo['pressure']}/{lo['band']} hi={hi['pressure']}/{hi['band']}")

    un = cb.epoch_reading(context_tokens=None, ceiling=300_000)
    gate("V-CTXB-EPOCH-UNMEASURED", un["state"] == cb.UNMEASURED and un["pressure"] is None,
         f"no tokens, no other signals -> {un['state']}")

    b = cb.Budget(10)
    b.spend("x" * 20)
    b.spend(6)
    gate("V-CTXB-BUDGET", b.spent == 11 and b.over() and b.remaining() == 0, f"spent={b.spent} over={b.over()}")

    print(f"CTXB_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
