#!/usr/bin/env python3
"""Break each property the mission vertical claims, and require it to go red.

Every mutation here removes a REQUIRED SEMANTIC PROPERTY -- not a line, not a
constant, not a spelling. A mutant that cannot change what the system decides is
not evidence about the suite, and counting one is how a drill comes to report a
number nobody should trust (see GSDX-U08, an equivalent mutant that sat in a
1/2 score until it was traced to its producers).

    python tools/test_gsd_x_mission_mutation.py

Files are restored in a finally and every restore is verified by SHA-256.
Bytecode writing is disabled: mutating a predicate can leave byte counts
unchanged, and a stale .pyc satisfies every freshness check a drill makes while
the process runs the code the drill thinks it replaced (GSDX-C20).
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBLIG = ROOT / "modules" / "gsd_x" / "mission" / "obligation.py"
CLOSURE = ROOT / "modules" / "gsd_x" / "mission" / "closure.py"
SUITE = ROOT / "tools" / "test_gsd_x_mission.py"

# name -> (file, old, new, the property being removed)
MUTATIONS: dict[str, tuple[Path, str, str, str]] = {
    "candidate-auto-accepted": (
        OBLIG,
        '    if not ob.consequence.strip():',
        '    if False:',
        "a candidate with no named consequence must not reach ACCEPTED",
    ),
    "evidence-not-required": (
        OBLIG,
        '    if not ob.evidence:',
        '    if False:',
        "an obligation unsupported by this project's reality must not be ACCEPTED",
    ),
    "stale-parent-ignored": (
        OBLIG,
        '    if gone:',
        '    if False:',
        "an obligation whose causal parent stopped holding must not stay current",
    ),
    # Precise: the narrative BECOMES authority. The first version of this mutant
    # deleted the `verdict is None` guard, which made the next line dereference
    # None -- a crash, not a semantic change. The suite exited 1 with no FAIL
    # line, and the harness read that as SURVIVED, i.e. it blamed the suite for a
    # malformed mutant. Both were fixed: this mutant now expresses the property,
    # and a non-zero exit with no failing gate is classified CRASHED rather than
    # counted either way.
    "narrative-is-authority": (
        CLOSURE,
        '        return TransitionResult(REFUSED,\n'
        '                                f"{ob.identifier} requires {ob.done_gate!r} and no "',
        '        return TransitionResult(ALLOWED if narrative else REFUSED,\n'
        '                                f"{ob.identifier} requires {ob.done_gate!r} and no "',
        "an executor's own account of completion must not close an obligation",
    ),
    "failed-gate-accepted": (
        CLOSURE,
        '    if not verdict.passed:',
        '    if False:',
        "a gate that ran and FAILED must not satisfy the obligation it judged",
    ),
    "open-obligation-does-not-block": (
        CLOSURE,
        '    for o in accepted:\n        blocking.append(',
        '    for o in []:\n        blocking.append(',
        "an empty explicit backlog must not close a mission with derived work open",
    ),
}


def main() -> int:
    for p in (OBLIG, CLOSURE, SUITE):
        if not p.is_file():
            print(f"INSTRUMENT_FAILED: missing {p}")
            return 2

    targets = {f for f, _, _, _ in MUTATIONS.values()}
    originals = {p: p.read_bytes() for p in targets}
    digests = {p: hashlib.sha256(b).hexdigest() for p, b in originals.items()}
    outcomes: dict[str, object] = {}

    try:
        for name, (path, old, new, prop) in MUTATIONS.items():
            text = originals[path].decode("utf-8")
            if old not in text:
                outcomes[name] = ("ANCHOR NOT FOUND -- drill invalid, not a verdict",
                                  prop)
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
                path.write_bytes(originals[path])
            failed = [ln.strip() for ln in proc.stdout.splitlines()
                      if ln.strip().startswith("FAIL")]
            outcomes[name] = ((proc.returncode, failed), prop)
    finally:
        for p, b in originals.items():
            p.write_bytes(b)

    restored = all(hashlib.sha256(p.read_bytes()).hexdigest() == digests[p]
                   for p in targets)
    print(f"restored (sha256, {len(targets)} file(s)): {restored}\n")
    if not restored:
        print("INSTRUMENT_FAILED: a mutated module was not restored")
        return 2

    caught = invalid = 0
    for name, (outcome, prop) in outcomes.items():
        if isinstance(outcome, str):
            invalid += 1
            print(f"  INVALID   {name}: {outcome}")
            continue
        rc, failed = outcome
        # Three outcomes, never two. A mutated suite that exits non-zero without
        # naming a failing gate did not detect anything -- it fell over, and
        # calling that CAUGHT rewards a drill for breaking the code it measures
        # while calling it SURVIVED blames the suite for a malformed mutant.
        if rc != 0 and not failed:
            invalid += 1
            print(f"  CRASHED   {name}  rc={rc} with no failing gate -- the mutant "
                  "is malformed, not the suite")
            print(f"            property: {prop}")
            continue
        hit = rc == 1 and bool(failed)
        caught += int(hit)
        print(f"  {'CAUGHT' if hit else 'SURVIVED'}  {name}  rc={rc}")
        print(f"            property: {prop}")
        for line in failed[:2]:
            print(f"            {line[:104]}")

    total = len(MUTATIONS)
    print(f"\nGSDX_MISSION_MUTATIONS_CAUGHT={caught}/{total}  threshold={total}/{total}")
    if invalid:
        return 2
    return 0 if caught == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
