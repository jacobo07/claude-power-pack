#!/usr/bin/env python3
"""Break each property the goal spine claims, and require the suite to go red.

    python tools/test_gsd_x_goal_mutation.py

Same contract as test_gsd_x_mission_mutation: anchors matched in the file's own
line endings, bytecode disabled, every restore verified by SHA-256, and outcomes
that are never collapsed -- a mutant whose anchor is missing is not a verdict.

Each mutant also names the gate that is SUPPOSED to catch it. A mutant caught
only by some other gate is reported CAUGHT-ELSEWHERE and is not counted: a red
for the wrong reason says nothing about the property the mutant removed.

NOT a mutant here: removing the sequence-gap clause in `read()` is EQUIVALENT.
Any real gap also breaks the hash chain (the next event's prev_digest names the
missing event), so the chain clause raises anyway. Measured 2026-09-22: that
mutant SURVIVED with rc=0. The clause stays for its clearer message and is not
counted as a guarantee.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "modules" / "gsd_x" / "goal" / "log.py"
CONTRACT = ROOT / "modules" / "gsd_x" / "goal" / "contract.py"
STORE = ROOT / "modules" / "gsd_x" / "mission" / "store.py"
SUITE = ROOT / "tools" / "test_gsd_x_goal.py"

# name -> (file, old, new, property removed, gate that must go red)
MUTATIONS: dict[str, tuple[Path, str, str, str, str]] = {
    "link-becomes-overwrite": (
        LOG, "os.link(tmp, target)            # atomic",
        "os.replace(tmp, target)            # atomic",
        "two writers must not both publish the same sequence number",
        "V-GOAL-CAS-TWO-WRITERS"),
    "digest-unchecked": (
        LOG, 'if raw.get("digest") != event_digest(raw):', "if False:",
        "an edited past event must be detected", "V-GOAL-LOG-CHAIN"),
    "permission-is-a-win": (
        LOG, 'raise Inconclusive(f"{target}: sharing violation: {exc}") from exc', "pass",
        "a sharing violation must not be reported as a published event",
        "V-GOAL-CAS-PERMISSION"),
    "budget-moves-revision": (
        CONTRACT, "            st.budget = dict(ev.data)\n",
        "            st.budget = dict(ev.data)\n            st.revision = st.revision + 'b'\n",
        "a budget change must not mint a new revision", "V-GOAL-REV-BUDGET-NEUTRAL"),
    "store-ignores-binding": (
        STORE,
        "def save(root: Path, obligations: list[Obligation]) -> Path:\n    refuse_if_bound(root)\n",
        "def save(root: Path, obligations: list[Obligation]) -> Path:\n",
        "a goal-bound root must refuse per-root obligation writes", "V-GOAL-SINGLE-OWNER"),
}


def main() -> int:
    targets = {m[0] for m in MUTATIONS.values()}
    for p in targets | {SUITE}:
        if not p.is_file():
            print(f"INSTRUMENT_FAILED: missing {p}")
            return 2
    originals = {p: p.read_bytes() for p in targets}
    digests = {p: hashlib.sha256(b).hexdigest() for p, b in originals.items()}
    outcomes: dict[str, object] = {}
    try:
        for name, (path, old, new, prop, gate) in MUTATIONS.items():
            text = originals[path].decode("utf-8")
            if "\r\n" in text:
                old, new = old.replace("\n", "\r\n"), new.replace("\n", "\r\n")
            if old not in text:
                outcomes[name] = ("ANCHOR NOT FOUND -- drill invalid, not a verdict", prop, gate)
                continue
            path.write_bytes(text.replace(old, new, 1).encode("utf-8"))
            try:
                proc = subprocess.run([sys.executable, "-B", str(SUITE)], capture_output=True,
                                      text=True, cwd=str(ROOT), timeout=300,
                                      env={**os.environ, "PYTHONIOENCODING": "utf-8",
                                           "PYTHONDONTWRITEBYTECODE": "1"})
            finally:
                path.write_bytes(originals[path])
            failed = [ln.strip() for ln in proc.stdout.splitlines()
                      if ln.strip().startswith("FAIL")]
            outcomes[name] = ((proc.returncode, failed), prop, gate)
    finally:
        for p, b in originals.items():
            p.write_bytes(b)

    restored = all(hashlib.sha256(p.read_bytes()).hexdigest() == digests[p] for p in targets)
    print(f"restored (sha256, {len(targets)} file(s)): {restored}\n")
    if not restored:
        print("INSTRUMENT_FAILED: a mutated module was not restored")
        return 2
    caught = 0
    for name, (outcome, prop, gate) in outcomes.items():
        if isinstance(outcome, str):
            print(f"  INVALID   {name}: {outcome}")
            continue
        rc, failed = outcome
        names = [f.split(":")[0].replace("FAIL ", "") for f in failed]
        if rc != 0 and not failed:
            print(f"  CRASHED   {name}  rc={rc} with no failing gate -- mutant malformed")
        elif gate in names:
            caught += 1
            print(f"  CAUGHT  {name} by {gate}\n            property: {prop}")
        elif failed:
            print(f"  CAUGHT-ELSEWHERE  {name}: expected {gate}, red: {names}")
        else:
            print(f"  SURVIVED  {name}  rc={rc}\n            property: {prop}")
    print(f"\nGSDX_GOAL_MUTATIONS_CAUGHT={caught}/{len(MUTATIONS)}  "
          f"threshold={len(MUTATIONS)}/{len(MUTATIONS)}")
    return 0 if caught == len(MUTATIONS) else 2


if __name__ == "__main__":
    sys.exit(main())
