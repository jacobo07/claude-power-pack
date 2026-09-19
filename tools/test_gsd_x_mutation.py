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

import hashlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TIER = ROOT / "modules" / "gsd_x" / "tier.py"
APPLICABILITY = ROOT / "modules" / "capability_runtime" / "applicability.py"
SUITE = ROOT / "tools" / "test_gsd_x.py"

# Each mutation names the FILE it mutates, because the property a mutant tests
# belongs to whoever owns it, and for the ordering mutation below that is the
# Capability Runtime rather than GSD X.
MUTATIONS = {
    "abstain-gate-reverted": (
        TIER,
        "if blocked and not positives:",
        "if blocked and not applies:",
    ),
    # Replaces `dormancy-reverted`, retired 2026-09-20 as EQUIVALENT. That mutant
    # disabled `_silence_dormant`, a GSD X filter written to compensate for the
    # Capability Runtime evaluating its evidence gate before its dormancy gate.
    # The Runtime has since fixed that at source -- gate 1 returns NOT_APPLICABLE
    # for an untriggered contract before gate 3 is reached (applicability.py,
    # citing the same measured symptom) -- so with upstream correct the engine
    # produces blocked=0 on every prompt in every evidence configuration
    # (measured: evidence=['source','tests'], ['source'] and [] all give 0). The
    # filter then has nothing to filter and the mutant changes no observable, so
    # no test could catch it and writing one would mean constructing a state no
    # producer can produce. Scoring that as an uncaught regression was a vanity
    # metric on a 1/2.
    #
    # The property is real, so it is now mutated at its owner. Disabling gate 1
    # reproduces the original defect exactly -- cdicf-installer returns
    # BLOCKED_BY_MISSING_EVIDENCE for `que hora es`, as it historically did -- and
    # `_silence_dormant` is measurably still a LIVE BACKSTOP: it removes that
    # verdict (blocked 1 -> 0). What the backstop cannot repair is the tier: with
    # dormancy off, every contract passes to scoring and the trivial prompt climbs
    # to FORENSIC. V-GSDX-TRIVIAL-CEILING is what observes that, and it exists
    # because this mutation was driven.
    "ordering-reverted": (
        APPLICABILITY,
        "    trig = _hits(text, c.triggers)\n    if not trig:",
        "    trig = _hits(text, c.triggers)\n    if False:",
    ),
}


def main() -> int:
    targets = {t for t, _, _ in MUTATIONS.values()}
    for path in (SUITE, *targets):
        if not path.is_file():
            print(f"INSTRUMENT_FAILED: missing {path}")
            return 2

    # Bytes, not text: one of these modules is owned by another part of the
    # estate, and a restore that rewrites line endings has silently modified a
    # file it only meant to read.
    originals = {p: p.read_bytes() for p in targets}
    digests = {p: hashlib.sha256(b).hexdigest() for p, b in originals.items()}

    outcomes: dict[str, object] = {}
    try:
        for name, (path, old, new) in MUTATIONS.items():
            text = originals[path].decode("utf-8")
            if old not in text:
                # The anchor moved. Reporting this as a caught mutation would be
                # a lie, and reporting it as survived would blame the suite.
                outcomes[name] = "ANCHOR NOT FOUND -- drill invalid, not a verdict"
                continue
            path.write_bytes(text.replace(old, new, 1).encode("utf-8"))
            try:
                proc = subprocess.run(
                    [sys.executable, "-B", str(SUITE)],
                    capture_output=True, text=True, cwd=str(ROOT),
                    env={**os.environ, "PYTHONIOENCODING": "utf-8",
                         "PYTHONDONTWRITEBYTECODE": "1"},
                )
            finally:
                path.write_bytes(originals[path])      # restore between mutants
            failed = [
                ln.strip() for ln in proc.stdout.splitlines()
                if ln.strip().startswith("FAIL")
            ]
            outcomes[name] = (proc.returncode, failed)
    finally:
        for p, b in originals.items():
            p.write_bytes(b)

    restored = all(
        hashlib.sha256(p.read_bytes()).hexdigest() == digests[p] for p in targets
    )
    print(f"restored (sha256, {len(targets)} file(s)): {restored}\n")
    if not restored:
        print("INSTRUMENT_FAILED: a mutated module was not restored")
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
