#!/usr/bin/env python3
"""The outcome experiment spawns real model sessions. Can it be refused?

Phase VIII opened by asking the outcome contrast a question nobody had asked it:
what happens when the host cannot support an arm. The answer was that it did not
ask. There was no admission gate at all, and an arm whose session the OS took
away creates no artefact -- which the grader scored FAIL, and a FAIL in the
treatment column is evidence about the treatment. A host death would have
arrived as a finding about USEA.

Both halves of that repair are driven here, both poles each, and none of it
spends a session:

    _teardown   distinguishes an exit a process CHOSE from one the OS imposed.
                The green pole matters as much as the red: a classifier that
                called every non-zero exit a teardown would excuse every real
                defect, and would pass a red-branch-only drill.

    admit       refuses an impossible workload and admits a trivial one on the
                same host, in the same second. One pole alone proves nothing --
                a gate that refuses everything and a gate that refuses nothing
                both pass a single-pole test.

    _summarise  keeps UNMEASURED out of the arithmetic, and says how many
                matched pairs are actually comparable. A table with one
                UNMEASURED cell still reads like a contrast to a human eye.

WHY A SEPARATE FILE
    The contrast's own gate is `--controls-only`, whose subject is the task
    oracles. Its subject is not the harness. These are different claims and a
    green on one has never said anything about the other.
"""
from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools import usea_outcome_contrast as oc  # noqa: E402

PASSES = 0
FAILS = 0


def check(gate: str, cond: bool, evidence: str) -> None:
    global PASSES, FAILS
    if cond:
        PASSES += 1
        print(f"  OK   {gate}  {evidence}")
    else:
        FAILS += 1
        print(f"  FAIL {gate}  {evidence}")


def _row(task: str, arm: str, oracle_pass, cost=0.10):
    """One result row shaped exactly as run_arm returns it."""
    return {"task": task, "arm": arm, "trial": 1,
            "oracle_pass": oracle_pass,
            "oracle_detail": "synthetic",
            "outcome": "UNMEASURED" if oracle_pass is None else "MEASURED",
            "unmeasured_reason": "synthetic teardown" if oracle_pass is None else None,
            "artifact_produced": oracle_pass is True,
            "artifact_source": "", "files_added": [],
            "session_ok": oracle_pass is not None,
            "cost_usd": cost, "turns": 3, "wall_s": 1.0,
            "permission_denials": 0, "leak_markers": [], "note": ""}


def main() -> int:
    # --- teardown classifier, both poles -----------------------------------
    killed = {-9: "signal", 0xC0000017: "STATUS_NO_MEMORY",
              0xC0000005: "access violation", 0xC000013A: "control-C"}
    missed = [hex(rc) for rc in killed if oc._teardown(rc) is None]
    check("V-ADMIT-TEARDOWN-RED",
          not missed,
          f"{len(killed)} teardown shapes recognised"
          f"{'' if not missed else '; missed ' + ', '.join(missed)}")

    # An honest CLI failure must NOT be excused as a teardown, or the gate
    # launders every real defect into 'the machine did it'.
    honest = [0, 1, 2, 3, 127]
    excused = [rc for rc in honest if oc._teardown(rc) is not None]
    check("V-ADMIT-TEARDOWN-GREEN",
          not excused,
          f"{len(honest)} exit codes a process could choose are left alone"
          f"{'' if not excused else '; wrongly excused ' + str(excused)}")

    check("V-ADMIT-TEARDOWN-UNKNOWN-RC",
          oc._teardown(None) is None,
          "a missing exit code is not asserted to be a teardown")

    # --- admission, both poles, same host, same second ----------------------
    refused = oc.admit(peak_mb=10_000_000, reserve_mb=1024, samples=1)
    check("V-ADMIT-REFUSES-IMPOSSIBLE",
          refused["state"] == "BLOCKED" and bool(refused["blocker"]),
          f"an impossible workload is refused: {refused['state']}"
          f" ({refused['blocker']})")

    admitted = oc.admit(peak_mb=1, reserve_mb=1, samples=1)
    check("V-ADMIT-ADMITS-TRIVIAL",
          admitted["state"] == "QUALIFIED",
          f"a trivial workload is admitted on the same host: "
          f"{admitted['state']} ({admitted['available_mb']} MB available)")

    # Without this the two poles above could both be produced by a gate that
    # reads no host at all.
    check("V-ADMIT-READ-THE-HOST",
          isinstance(admitted["available_mb"], int)
          and admitted["available_mb"] > 0
          and admitted["required_mb"] == 2,
          f"the probe reported a real reading ({admitted['available_mb']} MB) "
          f"and the declared requirement ({admitted['required_mb']} MB)")

    multi = oc.admit(peak_mb=1, reserve_mb=1, samples=3)
    check("V-ADMIT-KEEPS-THE-WORST",
          len(multi["samples"]) >= 1
          and multi["available_mb"] == min(multi["samples"]),
          f"admission reports the worst of {len(multi['samples'])} sample(s), "
          f"not the last: {multi['samples']} -> {multi['available_mb']}")

    check("V-ADMIT-NEVER-RAISES",
          oc.admit(peak_mb=-1, reserve_mb=-1, samples=1)["state"] in {
              "QUALIFIED", "BLOCKED", "PARTIALLY_QUALIFIED", "UNKNOWN"},
          "a nonsense workload resolves to a state rather than an exception")

    # --- the arithmetic -----------------------------------------------------
    # One graded pass and one arm the host took away. The denominator must be
    # what was measured; 1/2 would report the machine's interruption as a
    # treatment that failed half its tasks.
    report = {"runs": [_row("A", "treatment", True),
                       _row("B", "treatment", None),
                       _row("A", "control", False),
                       _row("B", "control", True)],
              "status": "COMPLETE", "arms_intended": 4}
    buf = io.StringIO()
    with redirect_stdout(buf):
        oc._summarise(report)
    out = buf.getvalue()
    check("V-ADMIT-UNMEASURED-OUT-OF-DENOMINATOR",
          "treatment first-attempt oracle 1/1" in out
          and "1 UNMEASURED" in out,
          "the treatment row reads 1/1 with the taken arm named, not 1/2")
    check("V-ADMIT-GRADED-ARM-UNAFFECTED",
          "control   first-attempt oracle 1/2" in out,
          "the fully graded arm still divides by everything it ran")
    check("V-ADMIT-PAIR-NOT-COMPARABLE",
          "comparable matched pairs: 1/2" in out,
          "a pair with one UNMEASURED half is not counted as a comparison")

    partial = {"runs": [_row("A", "treatment", True)],
               "status": "PARTIAL", "arms_intended": 8,
               "stopped_because": "host stopped qualifying"}
    buf = io.StringIO()
    with redirect_stdout(buf):
        oc._summarise(partial)
    check("V-ADMIT-PARTIAL-SAYS-SO",
          "PARTIAL" in buf.getvalue()
          and "not the authorized experiment" in buf.getvalue(),
          "a stopped run states it is not the authorized experiment")

    # --- exit codes are distinguishable -------------------------------------
    codes = {"OK": oc.EXIT_OK, "VOID": oc.EXIT_VOID,
             "NO_PAYLOAD": oc.EXIT_NO_PAYLOAD, "BLOCKED": oc.EXIT_BLOCKED,
             "PARTIAL": oc.EXIT_PARTIAL}
    check("V-ADMIT-EXIT-CODES-DISTINCT",
          len(set(codes.values())) == len(codes),
          f"a refused run, a void run and a partial run carry different "
          f"codes: {codes}")

    total = PASSES + FAILS
    print(f"ADMISSION_PASS={PASSES}/{total}  threshold={total}/{total}")
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
