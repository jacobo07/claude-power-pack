#!/usr/bin/env python3
"""V-gates for the intent-fidelity layer.

Hermetic: every fixture lives in a temp dir and the repo is only ever read.
The observe tier is exercised against real subprocesses writing real output --
a mocked runner would prove the parser works and say nothing about whether
evidence can be collected, which is the exact substitution this layer exists
to refuse.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.intent_verified import (  # noqa: E402
    Criterion, Observed, Reach, blocking_count, decide, parse_criteria,
    parse_results, resolve, standing_gate_targets,
)
from modules.intent_verified.join import (  # noqa: E402
    CriterionResult, is_runnable, observe,
)
from modules.intent_verified.ratchet import compare, snapshot  # noqa: E402
from modules.intent_verified.verdict import Verdict  # noqa: E402

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"PASS  {gate:34s} {evidence}")


def _fail(gate: str, why: str) -> None:
    global _fails
    _fails += 1
    print(f"FAIL  {gate:34s} {why}")


SPEC_TABLE = """---
title: fixture
covers: [fixture]
---

# Spec

## Acceptance criteria

| Gate | Asserts |
|---|---|
| `V-FIX-ONE` | the first thing is true |
| `V-FIX-TWO` | the second thing is true (advisory) |

## Validation

Not part of the acceptance section.
| `V-FIX-NOISE` | must not be collected |
"""

SPEC_PROSE = """---
title: prose
covers: [prose]
---

## Acceptance criteria

It should feel right and be reasonably fast.
"""


def t_parse() -> None:
    cs = parse_criteria(SPEC_TABLE, "fixture.md")
    ids = [c.id for c in cs]
    if ids == ["V-FIX-ONE", "V-FIX-TWO"]:
        _ok("V-IV-CRITERIA-FROM-TABLE", f"collected {ids} and stopped at the "
                                        "next heading")
    else:
        _fail("V-IV-CRITERIA-FROM-TABLE", f"collected {ids}")

    if cs and cs[0].critical and "first thing" in cs[0].assertion:
        _ok("V-IV-CRITICAL-DEFAULT", f"unmarked row -> critical, assertion="
                                     f"{cs[0].assertion!r}")
    else:
        _fail("V-IV-CRITICAL-DEFAULT", f"got {cs[:1]}")

    if len(cs) > 1 and not cs[1].critical:
        _ok("V-IV-ADVISORY-MARK", "row marked advisory -> not critical")
    else:
        _fail("V-IV-ADVISORY-MARK", "advisory row still counted as critical")

    if parse_criteria(SPEC_PROSE, "prose.md") == []:
        _ok("V-IV-PROSE-NOT-INVENTED", "a prose acceptance section yields no "
                                       "criterion rather than a guessed one")
    else:
        _fail("V-IV-PROSE-NOT-INVENTED", "prose produced criteria")


def t_resolve(tmp: Path) -> None:
    (tmp / "tools").mkdir(parents=True, exist_ok=True)
    (tmp / "tools" / "verify_spp.py").write_text(
        'rows_spec = [\n ("row", [PY, "runner_in_gate.py"], 10),\n    ]\n',
        encoding="utf-8")
    (tmp / "runner_in_gate.py").write_text(
        'print("PASS V-T-IN evidence")\n', encoding="utf-8")
    (tmp / "runner_outside.py").write_text(
        'print("PASS V-T-OUT evidence")\n', encoding="utf-8")

    cs = [Criterion("V-T-IN", "in the gate", True, "s.md"),
          Criterion("V-T-OUT", "outside the gate", True, "s.md"),
          Criterion("V-T-NOWHERE", "emitted by nothing", True, "s.md")]
    got = {r.criterion.id: r.reach for r in resolve(cs, tmp)}
    want = {"V-T-IN": Reach.REACHABLE, "V-T-OUT": Reach.UNJOINED,
            "V-T-NOWHERE": Reach.UNVERIFIABLE}
    if got == want:
        _ok("V-IV-UNVERIFIABLE-VS-UNJOINED",
            "no-emitter, emitter-outside-gate and emitter-in-gate are three "
            "distinct verdicts")
    else:
        _fail("V-IV-UNVERIFIABLE-VS-UNJOINED", f"got {got}")

    targets = standing_gate_targets(PP_ROOT)
    if "test_capture_liveness.py" in targets and len(targets) > 20:
        _ok("V-IV-TARGETS-FROM-SOURCE",
            f"{len(targets)} standing-gate targets parsed from the real "
            "verify_spp row table")
    else:
        _fail("V-IV-TARGETS-FROM-SOURCE", f"parsed {len(targets)} targets")


def t_parse_results() -> None:
    out = ("PASS  V-A  fine\n"
           "PASS V-B: fine\n"
           "FAIL  V-B  broke later\n"
           "[OK] V-C ok\n")
    got = {k: v[0] for k, v in parse_results(out).items()}
    if got == {"V-A": "PASS", "V-B": "FAIL", "V-C": "PASS"}:
        _ok("V-IV-FAIL-BEATS-PASS",
            "an id reported both PASS and FAIL resolves to FAIL, so line "
            "order cannot decide correctness")
    else:
        _fail("V-IV-FAIL-BEATS-PASS", f"got {got}")

    # Regression: a verdict-first-only parser read this layout as "never
    # emitted" and reported 9 false ABSENT verdicts against a passing suite.
    table = ("TEST                EXPECTED   ACTUAL   OK\n"
             "V-BLOCK-SECRET      block      block    PASS\n"
             "V-WARN-LENGTH       warn       block    FAIL\n")
    got2 = {k: v[0] for k, v in parse_results(table).items()}
    if got2 == {"V-BLOCK-SECRET": "PASS", "V-WARN-LENGTH": "FAIL"}:
        _ok("V-IV-ID-FIRST-LAYOUT",
            "id-first / verdict-last table rows are read; an unrecognised "
            "layout must not read as unobserved")
    else:
        _fail("V-IV-ID-FIRST-LAYOUT", f"got {got2}")

    if not is_runnable("tools/normalize_paths.py") and \
            is_runnable("modules\\code-review\\test_v_block.py") and \
            is_runnable("tools/verify_tco.py"):
        _ok("V-IV-ONLY-VERIFIERS-RUN",
            "an emitter that is not a verifier is never executed; "
            "normalize_paths.py names a V-id and rewrites paths when run")
    else:
        _fail("V-IV-ONLY-VERIFIERS-RUN", "runnable classification is wrong")


def t_observe(tmp: Path) -> None:
    (tmp / "test_owner_ok.py").write_text(
        'print("PASS  V-O-GOOD  observed")\n', encoding="utf-8")
    (tmp / "test_owner_bad.py").write_text(
        'print("FAIL  V-O-BAD  observed failure")\n', encoding="utf-8")
    (tmp / "test_owner_silent.py").write_text(
        'print("nothing about any gate")\n', encoding="utf-8")

    def rr(vid: str, owner: str, critical: bool = True) -> CriterionResult:
        return CriterionResult(Criterion(vid, "a", critical, "s.md"),
                               Reach.UNJOINED, (owner,))

    res = observe([rr("V-O-GOOD", "test_owner_ok.py"),
                   rr("V-O-BAD", "test_owner_bad.py"),
                   rr("V-O-MISSING", "test_owner_silent.py")], tmp)
    got = {r.criterion.id: r.observed for r in res}
    if got == {"V-O-GOOD": Observed.PASS, "V-O-BAD": Observed.FAIL,
               "V-O-MISSING": Observed.ABSENT}:
        _ok("V-IV-ABSENT-IS-NOT-PASS",
            "real subprocesses: a gate the owner never emitted is ABSENT, "
            "not satisfied")
    else:
        _fail("V-IV-ABSENT-IS-NOT-PASS", f"got {got}")

    v = decide([res[1]], "s.md")
    if v.verdict is Verdict.BLOCKED and not v.passed:
        _ok("V-IV-BLOCKED-ON-CRITICAL-FAIL",
            f"observed critical failure -> {v.verdict.value}, passed=False")
    else:
        _fail("V-IV-BLOCKED-ON-CRITICAL-FAIL", f"got {v.verdict.value}")

    v2 = decide([res[2]], "s.md")
    if v2.verdict is Verdict.EVIDENCE_INCOMPLETE and not v2.passed:
        _ok("V-IV-EVIDENCE-INCOMPLETE-DISTINCT",
            "unobserved critical is EVIDENCE_INCOMPLETE, a different claim "
            "from BLOCKED")
    else:
        _fail("V-IV-EVIDENCE-INCOMPLETE-DISTINCT", f"got {v2.verdict.value}")

    adv = rr("V-O-ADV", "test_owner_silent.py", critical=False)
    v3 = decide(observe([rr("V-O-GOOD", "test_owner_ok.py"), adv], tmp), "s.md")
    if v3.verdict is Verdict.PARTIAL_VERIFIED and v3.passed:
        _ok("V-IV-PARTIAL-ON-ADVISORY",
            "critical satisfied + advisory unmet -> PARTIAL_VERIFIED, which "
            "permits a done claim and still names the gap")
    else:
        _fail("V-IV-PARTIAL-ON-ADVISORY", f"got {v3.verdict.value}")


def t_absolute() -> None:
    bad = CriterionResult(Criterion("V-X", "a", True, "s.md"), Reach.UNJOINED,
                          ("o.py",), Observed.FAIL, "e")
    good = [CriterionResult(Criterion(f"V-G{i}", "a", True, "s.md"),
                            Reach.REACHABLE, ("o.py",), Observed.PASS, "e")
            for i in range(99)]
    small, large = blocking_count(decide([bad])), blocking_count(
        decide([bad] + good))
    if small == large == 1:
        _ok("V-IV-ABSOLUTE-NOT-RATIO",
            f"blocking count is {small} against 1 criterion and {large} "
            "against 100 -- independent of the denominator")
    else:
        _fail("V-IV-ABSOLUTE-NOT-RATIO", f"{small} vs {large}")

    d = decide([bad] + good).as_dict()
    floats = [k for k, val in d.items() if isinstance(val, float)]
    if not floats:
        _ok("V-IV-NO-RATIO-EMITTED", "no float key in the emitted verdict")
    else:
        _fail("V-IV-NO-RATIO-EMITTED", f"float keys: {floats}")

    v = decide([], "", "no spec declares coverage", bound=False)
    if (v.verdict is Verdict.INTENT_NOT_CAPTURED and v.passed
            and blocking_count(v) == 0):
        _ok("V-IV-NOT-CAPTURED-DOES-NOT-BLOCK",
            "an unbound task is visible debt, not a block (Owner decision "
            "2026-08-14)")
    else:
        _fail("V-IV-NOT-CAPTURED-DOES-NOT-BLOCK", f"got {v.verdict.value}")

    if decide([], "s.md").verdict is Verdict.CRITERIA_NOT_MECHANICAL:
        _ok("V-IV-NO-CRITERIA-IS-NOT-DONE",
            "a bound spec naming no criterion cannot report DONE_VERIFIED")
    else:
        _fail("V-IV-NO-CRITERIA-IS-NOT-DONE", "empty criteria read as done")


def t_ratchet() -> None:
    def res(vid: str, reach: Reach, spec: str = "s.md") -> CriterionResult:
        return CriterionResult(Criterion(vid, "a", True, spec), reach)

    base = snapshot([res("V-K", Reach.REACHABLE), res("V-U", Reach.UNJOINED)])
    gone = compare(base, snapshot([res("V-K", Reach.REACHABLE)]))
    if gone.withdrawn == ["V-U"] and gone.regressed:
        _ok("V-IV-RATCHET-WITHDRAWN",
            "a criterion deleted from the spec is named, not absorbed into a "
            "smaller denominator")
    else:
        _fail("V-IV-RATCHET-WITHDRAWN", f"got {gone.as_dict()}")

    back = compare(base, snapshot([res("V-K", Reach.UNJOINED),
                                   res("V-U", Reach.UNJOINED)]))
    if back.unjoined_back == ["V-K"] and back.regressed:
        _ok("V-IV-RATCHET-UNJOINED-BACK",
            "coverage lost on a still-declared criterion is a regression")
    else:
        _fail("V-IV-RATCHET-UNJOINED-BACK", f"got {back.as_dict()}")

    fixed = compare(base, snapshot([res("V-K", Reach.REACHABLE),
                                    res("V-U", Reach.REACHABLE)]))
    if fixed.repaired == ["V-U"] and not fixed.regressed:
        _ok("V-IV-RATCHET-REPAIR-ALLOWED",
            "debt falling by name is never a regression")
    else:
        _fail("V-IV-RATCHET-REPAIR-ALLOWED", f"got {fixed.as_dict()}")


def main() -> int:
    t_parse()
    t_parse_results()
    t_absolute()
    t_ratchet()
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        t_resolve(tmp)
        t_observe(tmp)
    total = _passes + _fails
    print(f"\nINTENT_VERIFIED_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
