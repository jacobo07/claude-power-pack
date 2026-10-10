#!/usr/bin/env python
"""V-NOWORK-* gates for tools/work_proof.py and the NO_WORK verdict in route_admission.

Every NO_WORK has a control that must still run (changed dep, missing dep, unproven claim).
Mutation drill: WORK_PROOF_DRILL_DIR holding a mutated work_proof.py is imported first.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
if os.environ.get("WORK_PROOF_DRILL_DIR"):
    sys.path.insert(0, os.environ["WORK_PROOF_DRILL_DIR"])
sys.path.insert(1 if os.environ.get("WORK_PROOF_DRILL_DIR") else 0, str(HERE))
import route_admission as ra  # noqa: E402
import work_proof as wp  # noqa: E402

passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


FLOORS = {"profiles": {"top-level-worker": {"floor": 100_000}}, "default_min_calls": 1}
ENV = {"target": 5_000_000, "warn": 6_000_000, "stop": 7_000_000, "calls": 20}


def route(proof=None, ledger=None):
    r = {"envelope": ENV, "workers": [{"name": "w", "profile": "top-level-worker", "calls": 5, "packet": 1000}]}
    if proof:
        r["proof"] = proof
    if ledger:
        r["proof_ledger"] = str(ledger)
    return r


with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    (root / "a.txt").write_text("alpha", encoding="utf-8")
    (root / "b.txt").write_text("beta", encoding="utf-8")
    led = root / "ledger.json"
    deps = ["a.txt", "b.txt"]
    proof = {"claim": "C-1", "deps": deps}

    check("V-NOWORK-01 unproven claim runs", ra.admit(route(proof, led), FLOORS, root=root)["verdict"] == ra.ADMISSIBLE)
    wp.record_proof("C-1", deps, root=root, ledger_path=led)
    r = ra.admit(route(proof, led), FLOORS, root=root)
    check("V-NOWORK-02 proven at unchanged fingerprint -> NO_WORK", r["verdict"] == ra.NO_WORK, r["reasons"])
    check("V-NOWORK-03 NO_WORK is known and not launchable",
          ra.NO_WORK in ra.KNOWN_VERDICTS and ra.NO_WORK not in ra.LAUNCHABLE_VERDICTS)
    (root / "b.txt").write_text("beta2", encoding="utf-8")
    check("V-NOWORK-04 changed dependency -> runs", ra.admit(route(proof, led), FLOORS, root=root)["verdict"] == ra.ADMISSIBLE)
    (root / "b.txt").write_text("beta", encoding="utf-8")
    check("V-NOWORK-05 restored dependency -> NO_WORK again", ra.admit(route(proof, led), FLOORS, root=root)["verdict"] == ra.NO_WORK)
    (root / "b.txt").unlink()
    check("V-NOWORK-06 missing dependency -> runs, never NO_WORK",
          ra.admit(route(proof, led), FLOORS, root=root)["verdict"] == ra.ADMISSIBLE)
    check("V-NOWORK-07 empty deps -> runs",
          ra.admit(route({"claim": "C-1", "deps": []}, led), FLOORS, root=root)["verdict"] == ra.ADMISSIBLE)
    (root / "b.txt").write_text("beta", encoding="utf-8")
    d = json.loads(led.read_text(encoding="utf-8"))
    d["claims"]["C-1"]["status"] = "NOT_PROVEN"
    led.write_text(json.dumps(d), encoding="utf-8")
    check("V-NOWORK-08 non-PROVEN status -> runs", ra.admit(route(proof, led), FLOORS, root=root)["verdict"] == ra.ADMISSIBLE)
    led.write_text("{not json", encoding="utf-8")
    check("V-NOWORK-09 corrupt ledger -> runs", ra.admit(route(proof, led), FLOORS, root=root)["verdict"] == ra.ADMISSIBLE)
    try:
        wp.record_proof("C-2", ["nope.txt"], root=root, ledger_path=led)
        check("V-NOWORK-10 cannot prove over a missing dep", False)
    except ValueError:
        check("V-NOWORK-10 cannot prove over a missing dep", True)

    rc = wp.unit_receipt("U-1", calls=25, processed=3_000_000, tier="slim", boundaries=4, lower_bound=1_500_000)
    check("V-RECEIPT-01 overhead multiplier", rc["overhead_multiplier"] == 2.0 and rc["tier"] == "slim", rc)
    check("V-RECEIPT-02 unknown bound -> overhead None, not 1.0",
          wp.unit_receipt("U", calls=1, processed=10, tier="t", boundaries=0, lower_bound=None)["overhead_multiplier"] is None)
    try:
        wp.unit_receipt("U", calls=-1, processed=1, tier="t", boundaries=0, lower_bound=1)
        check("V-RECEIPT-03 negative calls rejected", False)
    except ValueError:
        check("V-RECEIPT-03 negative calls rejected", True)

print(f"{passes} passed, {fails} failed")
sys.exit(1 if fails else 0)
