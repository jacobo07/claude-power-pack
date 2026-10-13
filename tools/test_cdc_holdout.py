#!/usr/bin/env python3
"""Tests for cdc_holdout.summarise incl. mutants (unknown-as-zero, waste dropped)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cdc_holdout as h

PART = {
    "calls": [("READ", 100), ("REREAD", 50), ("PLAN", 50), ("READ", 800)],
    "unprod": [{"tokens": 50, "cause": "REREAD", "tools": [], "run": 2},
               {"tokens": 800, "cause": "NO_PROGRESS_RUN:READ", "tools": [], "run": 30}],
    "seq": [("Read", 100), ("PowerShell:proof", 50), ("Read", 50)],
    "progress": 2, "transitions": 3,
}


def run():
    fails = []
    s = h.summarise([PART])
    if s["tokens"] != 1000:
        fails.append("tokens")
    if s["avoidable_tokens"] != 850 or abs(s["avoidable_share"] - 0.85) > 1e-9:
        fails.append("avoidable")
    if s["breaker_trip_calls_after_25"] != 1 or s["breaker_trip_tokens"] != 800:
        fails.append("trip")
    if s["tokens_per_progress"] != 500:
        fails.append("norm")
    if s["proof_then_other_pairs"] != 1:
        fails.append("proof pairs")
    if not str(s["admission_denials"]).startswith("UNKNOWN"):
        fails.append("denials must be UNKNOWN not 0")
    e = h.summarise([{"calls": [], "unprod": [], "seq": [], "progress": 0, "transitions": 0}])
    if e["avoidable_share"] is not None or e["tokens_per_progress"] is not None:
        fails.append("empty must be None")
    # mutant: drop waste -> must differ from expected
    m = dict(PART, unprod=[])
    if h.summarise([m])["avoidable_tokens"] == 850:
        fails.append("mutant not detected")
    return fails


if __name__ == "__main__":
    f = run()
    print("FAIL " + ",".join(f) if f else "ok 7/7")
    sys.exit(1 if f else 0)
