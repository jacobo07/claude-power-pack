#!/usr/bin/env python3
"""V-gates for the KEOS-Qwen outcome vocabulary (W1, phase-6 micro-batch 1).

Every verifier is driven at BOTH poles. The audit's gap 18 is that a verifier
which refuses everything passes every refusal assertion and is indistinguishable
from one that works, so each refusal below is paired with an admitted control.

The precondition is asserted rather than assumed. If the package does not
import, this exits 2 as HARNESS-FAILED and never as a finding -- which is the
same three-outcome discipline the module under test implements, applied to the
instrument measuring it. Gap 18's specific trap was that a broken package makes
every generated candidate fail to import, so the verifier reports the model
failing while measuring its own environment.

    python tools/test_keos_qwen_outcome.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from modules.keos_qwen.outcome import (  # noqa: E402
        ALL, HARNESS_FAILED, OK, TRUNCATED, UNAVAILABLE,
        Attempt, OutcomeError, _PRECEDENCE, classifiable, from_finish_reason, worst,
    )
except Exception as exc:  # noqa: BLE001 -- the precondition, not the subject
    print("HARNESS-FAILED: modules.keos_qwen.outcome did not import from "
          f"{ROOT}: {exc.__class__.__name__}: {exc}")
    print("This is an instrument failure, NOT a finding about the subject.")
    raise SystemExit(2)


def main() -> int:
    passes: list = []
    fails: list = []

    def ok(gate, evidence):
        passes.append(gate)
        print(f"  PASS {gate}: {evidence}")

    def bad(gate, why):
        fails.append(gate)
        print(f"  FAIL {gate}: {why}")

    def check(gate, cond, evidence, why):
        (ok if cond else bad)(gate, evidence if cond else why)

    def raises(gate, fn, evidence):
        try:
            got = fn()
            bad(gate, f"accepted, returned {got!r}")
        except OutcomeError:
            ok(gate, evidence)

    # --- classifiable: one predicate, both poles -----------------------------
    check("V-KEOSQ-CLASSIFIABLE-OK", classifiable(OK) is True,
          "OK is classifiable (admitted control)", "OK was refused")
    refused = [o for o in (UNAVAILABLE, TRUNCATED, HARNESS_FAILED) if classifiable(o) is False]
    check("V-KEOSQ-CLASSIFIABLE-NON-OK", len(refused) == 3,
          f"{refused} are all unclassifiable", f"only {refused} refused; expected 3")
    raises("V-KEOSQ-CLASSIFIABLE-UNKNOWN-RAISES", lambda: classifiable("PASS"),
           "an unrecognised outcome raises instead of defaulting to a verdict")

    # --- worst: precedence, and the bug caught before shipping ---------------
    check("V-KEOSQ-WORST-HARNESS-OUTRANKS", worst([OK, UNAVAILABLE, HARNESS_FAILED]) == HARNESS_FAILED,
          "an instrument failure outranks every subject observation in the run",
          f"got {worst([OK, UNAVAILABLE, HARNESS_FAILED])}")
    check("V-KEOSQ-WORST-UNAVAILABLE-OVER-TRUNCATED", worst([OK, TRUNCATED, UNAVAILABLE]) == UNAVAILABLE,
          "never asked outranks asked-but-cut", f"got {worst([OK, TRUNCATED, UNAVAILABLE])}")
    check("V-KEOSQ-WORST-TRUNCATED-OVER-OK", worst([OK, TRUNCATED]) == TRUNCATED,
          "a cut answer governs a clean one", f"got {worst([OK, TRUNCATED])}")
    check("V-KEOSQ-WORST-ALL-OK", worst([OK, OK, OK]) == OK,
          "an all-clean run reports OK (admitted control: a worst() that always "
          "answered HARNESS_FAILED would pass every assertion above)",
          f"got {worst([OK, OK, OK])}")
    check("V-KEOSQ-WORST-EMPTY-IS-HARNESS", worst([]) == HARNESS_FAILED,
          "observing nothing is an instrument failure, not a clean bill",
          f"got {worst([])}")
    raises("V-KEOSQ-WORST-UNKNOWN-WITH-OK", lambda: worst([OK, "BOGUS"]),
           "an unknown outcome beside OK raises; precedence runs AFTER validation")
    check("V-KEOSQ-PRECEDENCE-COVERS-ALL", set(ALL) == set(_PRECEDENCE),
          f"ALL and _PRECEDENCE name the same {len(ALL)} outcomes, so worst() is total",
          f"drift: ALL={set(ALL)} _PRECEDENCE={set(_PRECEDENCE)}")

    # --- from_finish_reason: positive test on observed answers ---------------
    check("V-KEOSQ-FINISH-STOP-OK", from_finish_reason("stop")[0] == OK,
          "finish_reason='stop' is a complete answer", f"got {from_finish_reason('stop')}")
    check("V-KEOSQ-FINISH-TOOLCALLS-OK", from_finish_reason("tool_calls")[0] == OK,
          "finish_reason='tool_calls' is OK -- the value the real 2026-09-24 probe returned",
          f"got {from_finish_reason('tool_calls')}")
    trunc = from_finish_reason("length")
    check("V-KEOSQ-FINISH-LENGTH-TRUNCATED", trunc[0] == TRUNCATED and "ctx" in trunc[1],
          "finish_reason='length' is OUR window, named as such", f"got {trunc}")
    unk = from_finish_reason("content_filter")
    check("V-KEOSQ-FINISH-UNKNOWN-HARNESS", unk[0] == HARNESS_FAILED and "content_filter" in unk[1],
          "an unobserved finish_reason refuses AND carries its raw value so the "
          "first occurrence diagnoses itself", f"got {unk}")
    none = from_finish_reason(None)
    check("V-KEOSQ-FINISH-NONE-HARNESS", none[0] == HARNESS_FAILED and "None" in none[1],
          "an absent finish_reason is refusal, not success", f"got {none}")

    # --- Attempt: a refusal must say what could not be told ------------------
    try:
        a = Attempt(OK, "")
        ok("V-KEOSQ-ATTEMPT-OK-NEEDS-NO-REASON",
           "OK with no reason is admitted (control: an Attempt that refused every "
           "empty reason would pass the two assertions below for the wrong reason)")
    except OutcomeError as exc:
        bad("V-KEOSQ-ATTEMPT-OK-NEEDS-NO-REASON", f"refused a clean OK: {exc}")
    raises("V-KEOSQ-ATTEMPT-NON-OK-NEEDS-REASON", lambda: Attempt(UNAVAILABLE, ""),
           "a non-OK outcome with no reason is refused at construction")
    raises("V-KEOSQ-ATTEMPT-BLANK-REASON", lambda: Attempt(TRUNCATED, "   "),
           "whitespace is not a reason -- blank satisfies a non-empty check and teaches nothing")
    raises("V-KEOSQ-ATTEMPT-UNKNOWN-OUTCOME", lambda: Attempt("PASS", "looks fine"),
           "an outcome outside ALL is refused even with a reason")

    a = Attempt(UNAVAILABLE, "ConnectionRefused on the tunnel", {"port": 8081})
    d = a.to_dict()
    check("V-KEOSQ-ATTEMPT-ROUNDTRIP",
          d["outcome"] == UNAVAILABLE and d["evidence"]["port"] == 8081 and a.classifiable is False,
          "an Attempt survives to_dict with its reason and evidence, and is not classifiable",
          f"got {d}")

    total = len(passes) + len(fails)
    print(f"\nKEOSQ_OUTCOME_PASS={len(passes)}/{total}  threshold={total}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
