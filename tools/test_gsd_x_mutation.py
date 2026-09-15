#!/usr/bin/env python3
"""Revert each fix in turn and require the suite to go red.

A green suite nobody has falsified could have every clause removed and read the
same. These two mutations are not hypothetical: both are bugs this module
actually shipped and both were found by running rather than by reading.

    dormancy-reverted       count every blocked contract, including ones the
                            prompt never addressed. Measured consequence: one
                            contract in this estate requires evidence no prompt
                            can carry, so `que hora es` abstained.

    abstain-gate-reverted   let any evaluable verdict cancel an abstention,
                            rather than only a positive one. Measured
                            consequence: a single dormant NOT_APPLICABLE
                            suppressed the abstention nine blocked contracts
                            had earned, and every prompt bottomed out on the
                            floor.

The drill is worth more than its result. On its first run the second mutation
SURVIVED -- the suite could not tell the two spellings apart, because no corpus
prompt reaches the state where they differ. That is a hole in the suite, not a
property of the code, and V-GSDX-ABSTAIN-DOMINANCE exists because the drill
reported it.

The file is restored in a `finally`, so an exploding suite cannot leave the
module mutated.

    python tools/test_gsd_x_mutation.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TIER = ROOT / "modules" / "gsd_x" / "tier.py"
SUITE = ROOT / "tools" / "test_gsd_x.py"

MUTATIONS = {
    "dormancy-reverted": (
        "    blocked = [r for r in results if r.blocked]\n"
        "    if not blocked:\n        return results",
        "    blocked = [r for r in results if r.blocked]\n"
        "    if True:\n        return results",
    ),
    "abstain-gate-reverted": (
        "if blocked and not positives:",
        "if blocked and not applies:",
    ),
}


def main() -> int:
    if not TIER.is_file() or not SUITE.is_file():
        print(f"INSTRUMENT_FAILED: missing {TIER} or {SUITE}")
        return 2

    original = TIER.read_text(encoding="utf-8")
    outcomes: dict[str, object] = {}
    try:
        for name, (old, new) in MUTATIONS.items():
            if old not in original:
                # The anchor moved. Reporting this as a caught mutation would be
                # a lie, and reporting it as survived would blame the suite.
                outcomes[name] = "ANCHOR NOT FOUND -- drill invalid, not a verdict"
                continue
            TIER.write_text(original.replace(old, new, 1), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(SUITE)],
                capture_output=True, text=True, cwd=str(ROOT),
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
            failed = [
                ln.strip() for ln in proc.stdout.splitlines()
                if ln.strip().startswith("FAIL")
            ]
            outcomes[name] = (proc.returncode, failed)
    finally:
        TIER.write_text(original, encoding="utf-8")

    restored = TIER.read_text(encoding="utf-8") == original
    print(f"restored: {restored}\n")
    if not restored:
        print("INSTRUMENT_FAILED: the module was not restored")
        return 2

    caught = 0
    invalid = 0
    for name, outcome in outcomes.items():
        if isinstance(outcome, str):
            invalid += 1
            print(f"  INVALID   {name}: {outcome}")
            continue
        rc, failed = outcome
        hit = rc == 1 and bool(failed)
        caught += int(hit)
        print(f"  {'CAUGHT' if hit else 'SURVIVED'}  {name}  rc={rc}")
        for line in failed[:3]:
            print(f"            {line[:110]}")

    total = len(MUTATIONS)
    print(f"\nGSDX_MUTATIONS_CAUGHT={caught}/{total}  threshold={total}/{total}")
    if invalid:
        return 2
    return 0 if caught == total else 1


if __name__ == "__main__":
    sys.exit(main())
