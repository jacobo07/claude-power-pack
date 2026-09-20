#!/usr/bin/env python3
"""Mutation drill for V-RECON-*. Each mutant must kill a NAMED gate.

A suite that has never been driven red could have every clause removed and
report the same green. This file removes one load-bearing property at a time
and requires the gate that claims to protect it -- by name, not merely "some
failure" -- to go red.

INSTRUMENT DISCIPLINE. A mutant that crashes the subject is not a semantic
rejection, so a non-zero exit alone does not count as a kill: the expected gate
token must appear on a FAIL line. Every file is restored from bytes captured
before the mutation and the restore is verified by SHA-256, because a drill that
corrupts the tree it measures is worse than no drill.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
CONTRACT = _PP_ROOT / "vault" / "capability_runtime" / "contracts" / "reconstruction_parity.json"
TIER = _PP_ROOT / "modules" / "gsd_x" / "tier.py"
GATE = _PP_ROOT / "tools" / "test_gsd_x_reconstruction.py"


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _run_gate() -> str:
    proc = subprocess.run(
        [sys.executable, str(GATE)], cwd=str(_PP_ROOT),
        capture_output=True, text=True, timeout=180,
    )
    return proc.stdout + proc.stderr


# --- mutations -------------------------------------------------------------
# Each returns the mutated TEXT for its file, given the original text.

def _drop_anti_triggers(text: str) -> str:
    d = json.loads(text)
    d["anti_triggers"] = []
    return json.dumps(d, indent=2) + "\n"


def _generic_trigger(text: str) -> str:
    """Widen the contract until it fires on ordinary work."""
    d = json.loads(text)
    d["triggers"] = list(d["triggers"]) + ["fix", "add", "update"]
    return json.dumps(d, indent=2) + "\n"


def _weaken_stakes(text: str) -> str:
    """high_stakes needs >=3 AND score>=0.55; 'high' keeps the gate but drops
    risk_reduction 1.0 -> 0.75, which is what carries the natural case."""
    d = json.loads(text)
    d["failure_risk_if_omitted"] = "high"
    return json.dumps(d, indent=2) + "\n"


def _drop_boundary(text: str) -> str:
    d = json.loads(text)
    d["non_scope"] = [s for s in d["non_scope"]
                      if s.strip().lower() != "publishing a fidelity number"]
    return json.dumps(d, indent=2) + "\n"


def _steal_owner(text: str) -> str:
    d = json.loads(text)
    d["owner"] = "modules/gsd_x"
    return json.dumps(d, indent=2) + "\n"


def _second_decider(text: str) -> str:
    """Install exactly the thing tier.py's own docstring forbids."""
    return text.replace(
        "LADDER = (LIGHT, STANDARD, DEEP, FORENSIC)",
        "LADDER = (LIGHT, STANDARD, DEEP, FORENSIC)\n"
        "_RECONSTRUCTION_BUMP = True  # mutant: a second decider",
        1,
    )


MUTATIONS = (
    ("anti-triggers-removed", CONTRACT, _drop_anti_triggers, "V-RECON-ANTI"),
    ("triggers-widened", CONTRACT, _generic_trigger, "V-RECON-NO-GOODHART"),
    ("stakes-weakened", CONTRACT, _weaken_stakes, "V-RECON-NATURAL"),
    ("boundary-dropped", CONTRACT, _drop_boundary, "V-RECON-BOUNDARY"),
    ("owner-stolen", CONTRACT, _steal_owner, "V-RECON-OWNER"),
    ("second-decider", TIER, _second_decider, "V-RECON-NO-DECIDER"),
)


def main() -> int:
    killed, survived, harness = 0, [], []

    baseline = _run_gate()
    if "RECON_PASS=10/10" not in baseline:
        print("HARNESS-FAILED: the gate is not green before mutation; "
              "a drill on a red subject measures nothing.")
        print(baseline)
        return 2
    print("baseline green (10/10) -- proceeding\n")

    for name, path, mutate, expect in MUTATIONS:
        original = path.read_bytes()
        before = hashlib.sha256(original).hexdigest()
        try:
            path.write_text(mutate(original.decode("utf-8")),
                            encoding="utf-8", newline="\n")
            out = _run_gate()
            failed_gates = [ln.split(":")[0].replace("FAIL", "").strip()
                            for ln in out.splitlines() if ln.strip().startswith("FAIL")]
            if expect in failed_gates:
                killed += 1
                print(f"  KILLED  {name:24s} -> {expect} went red")
            elif failed_gates:
                survived.append(name)
                print(f"  WRONG   {name:24s} -> expected {expect}, got {failed_gates}")
            else:
                survived.append(name)
                print(f"  SURVIVED {name:23s} -> nothing went red")
        except Exception as exc:                      # noqa: BLE001
            harness.append(f"{name}: {type(exc).__name__}: {exc}")
            print(f"  HARNESS {name:24s} -> {type(exc).__name__}")
        finally:
            path.write_bytes(original)
            after = _sha(path)
            if after != before:
                print(f"  !! RESTORE FAILED for {path.name}: {before} -> {after}")
                return 2

    total = len(MUTATIONS)
    print(f"\nrestore verified by SHA-256 for every mutant")
    if harness:
        print("HARNESS FAILURES (not findings): " + "; ".join(harness))
    print(f"RECON_MUTATION_KILLED={killed}/{total}  threshold={total}/{total}")
    if survived:
        print("survived: " + ", ".join(survived))
    return 0 if killed == total and not harness else 1


if __name__ == "__main__":
    raise SystemExit(main())
