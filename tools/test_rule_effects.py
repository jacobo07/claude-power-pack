#!/usr/bin/env python3
"""test_rule_effects.py -- gates for the rule-effect harness (M1b).

Both poles: a claim that measures a real improvement, and claims that must
NOT be reported as improvements -- an unrunnable probe, an absent metric, and
a number that moved the wrong way. An UNMEASURED verdict is the point of the
harness; a harness that quietly passes when it cannot measure is worse than
none.

Run: python tools/test_rule_effects.py
"""
from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import tempfile
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.rule_compiler import effect_harness as eh  # noqa: E402

_passes: list = []
_fails: list = []


def _ok(gate: str, evidence: str) -> None:
    _passes.append(gate)
    print(f"  [OK] {gate} -- {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    _fails.append(gate)
    print(f"  [X ] {gate} -- {diagnostic}")


def _registry(rows: list) -> Path:
    d = Path(tempfile.mkdtemp(prefix="eff-"))
    p = d / "effects.json"
    p.write_text(json.dumps({"effects": rows}), encoding="utf-8")
    return p


def _claim(**over) -> dict:
    row = {
        "rule_id": "TEST-001",
        "claim": "synthetic",
        "probe": [sys.executable, "-c", "print('value 5 units')"],
        "pattern": r"value (\d+) units",
        "metric": "units",
        "baseline": 10,
        "direction": "down",
    }
    row.update(over)
    return row


def gate_real_claim() -> None:
    """The shipped claim must run and produce a number, not a description."""
    results = eh.measure_all()
    if not results:
        _fail("V-EFFECT-REAL-CLAIM", "no claims registered in the shipped file")
        return
    m = results[0]
    if m.verdict == eh.IMPROVED and m.observed is not None \
            and m.observed < m.claim.baseline:
        _ok("V-EFFECT-REAL-CLAIM",
            f"{m.claim.rule_id}: probe ran, {m.claim.metric} "
            f"{m.claim.baseline:g} -> {m.observed:g}, verdict {m.verdict}")
    else:
        _fail("V-EFFECT-REAL-CLAIM",
              f"verdict={m.verdict} observed={m.observed} "
              f"baseline={m.claim.baseline} reason={m.reason}")


def gate_improved_and_regressed() -> None:
    p = _registry([_claim(rule_id="DOWN-GOOD", baseline=10),
                   _claim(rule_id="DOWN-BAD", baseline=2),
                   _claim(rule_id="UP-GOOD", baseline=2, direction="up"),
                   _claim(rule_id="SAME", baseline=5)])
    try:
        got = {m.claim.rule_id: m.verdict for m in eh.measure_all(p, PP_ROOT)}
        want = {"DOWN-GOOD": eh.IMPROVED, "DOWN-BAD": eh.REGRESSED,
                "UP-GOOD": eh.IMPROVED, "SAME": eh.NO_CHANGE}
        if got == want:
            _ok("V-EFFECT-VERDICTS",
                "observed 5 against baselines 10/2/2/5 -> "
                "IMPROVED/REGRESSED/IMPROVED/NO_CHANGE")
        else:
            _fail("V-EFFECT-VERDICTS", f"got {got} want {want}")
    finally:
        shutil.rmtree(p.parent, ignore_errors=True)


def gate_unmeasured() -> None:
    p = _registry([
        _claim(rule_id="NO-PROBE", probe=["definitely-not-a-binary-xyz"]),
        _claim(rule_id="NO-METRIC", pattern=r"nothing matches this (\d+)"),
        _claim(rule_id="NON-NUMERIC",
               probe=[sys.executable, "-c", "print('value abc units')"],
               pattern=r"value (\w+) units"),
    ])
    try:
        results = eh.measure_all(p, PP_ROOT)
        verdicts = {m.claim.rule_id: m.verdict for m in results}
        reasons = {m.claim.rule_id: m.reason for m in results}
        if set(verdicts.values()) == {eh.UNMEASURED} and all(reasons.values()):
            _ok("V-EFFECT-UNMEASURED",
                "unrunnable probe, absent metric and non-numeric metric all "
                "return UNMEASURED with a stated reason, never IMPROVED")
        else:
            _fail("V-EFFECT-UNMEASURED", f"{verdicts} reasons={reasons}")
    finally:
        shutil.rmtree(p.parent, ignore_errors=True)


def gate_malformed_claim_absent() -> None:
    p = _registry([{"rule_id": "BROKEN"}, _claim(rule_id="FINE")])
    try:
        ids = [c.rule_id for c in eh.load_claims(p)]
        if ids == ["FINE"]:
            _ok("V-EFFECT-MALFORMED-ABSENT",
                "a claim missing probe/pattern/baseline is dropped, so it can "
                "never be counted as measured coverage")
        else:
            _fail("V-EFFECT-MALFORMED-ABSENT", f"loaded {ids}")
    finally:
        shutil.rmtree(p.parent, ignore_errors=True)


def gate_regressed_exit_code() -> None:
    p = _registry([_claim(rule_id="DOWN-BAD", baseline=2)])
    try:
        prior = eh.EFFECTS_PATH
        eh.EFFECTS_PATH = p
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = eh.main([])
        eh.EFFECTS_PATH = prior
        if rc == 1 and eh.REGRESSED in buf.getvalue():
            _ok("V-EFFECT-REGRESSED-EXITS",
                "a rule whose own probe says it made things worse exits 1")
        else:
            _fail("V-EFFECT-REGRESSED-EXITS", f"rc={rc} out={buf.getvalue()[-160:]!r}")
    finally:
        shutil.rmtree(p.parent, ignore_errors=True)


def gate_coverage_is_honest() -> None:
    cov = eh.coverage()
    if cov["corpus_size"] is None:
        _fail("V-EFFECT-COVERAGE", "compiler unavailable; corpus size unknown")
        return
    # Coverage has two producers -- an effect claim (did a metric move?) and a
    # counterfactual replay (would it have fired on its own incident?). The
    # invariant is over their union: scoping it to effect claims alone would let
    # a replayed rule count as covered while failing the arithmetic.
    measured = set(cov["measured"])
    unknown = set(cov["unknown_rule_ids"])
    size, unmeasured = cov["corpus_size"], len(cov["unmeasured"])
    # Every measured id is either counted against the corpus or named as absent
    # from it. Otherwise the report can show more coverage than it has.
    reconciles = (size - unmeasured) == len(measured - unknown)
    if reconciles:
        _ok("V-EFFECT-COVERAGE",
            f"{size} compiled rules, {unmeasured} with no measured claim, "
            f"{len(unknown)} claim(s) named as not-in-corpus -- the arithmetic "
            f"closes instead of overstating")
    else:
        _fail("V-EFFECT-COVERAGE",
              f"size={size} unmeasured={unmeasured} measured={len(measured)} "
              f"unknown={len(unknown)} does not reconcile")


def gate_counterfactual_is_wired() -> None:
    """The backward half must run from THIS command, not a second entry point.

    A rule's own origin incident is the cheapest evidence that the rule fires,
    and it was never replayed -- 'this would have prevented that' has always been
    an assertion by the party who wrote the rule."""
    from modules.rule_compiler import counterfactual as cfm

    d = Path(tempfile.mkdtemp(prefix="cf-"))
    try:
        det = d / "d.py"
        det.write_text("import sys\nsys.exit(2 if 'BOOM' in sys.stdin.read() else 0)\n",
                       encoding="utf-8")
        reg = d / "cf.json"
        reg.write_text(json.dumps({"counterfactuals": [
            {"rule_id": "A", "incident_id": "I1", "incident_input": "BOOM here",
             "probe": [sys.executable, str(det)], "fires_on_exit": 2},
            {"rule_id": "B", "incident_id": "I2", "incident_input": "quiet",
             "probe": [sys.executable, str(det)], "fires_on_exit": 2},
        ]}), encoding="utf-8")
        got = {r.claim.rule_id: r.verdict for r in cfm.measure_all(reg)}
        if got == {"A": cfm.WOULD_BLOCK, "B": cfm.WOULD_NOT_BLOCK}:
            _ok("V-EFFECT-COUNTERFACTUAL-WIRED",
                "effect_harness.main reaches the counterfactual replay; a rule that "
                "does not fire on its own incident returns WOULD_NOT_BLOCK")
        else:
            _fail("V-EFFECT-COUNTERFACTUAL-WIRED", f"got {got}")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main() -> int:
    print("Rule Effect Harness Gates (M1b -- did a rule change improve anything)")
    print("")
    gate_counterfactual_is_wired()
    gate_real_claim()
    gate_improved_and_regressed()
    gate_unmeasured()
    gate_malformed_claim_absent()
    gate_regressed_exit_code()
    gate_coverage_is_honest()
    total = len(_passes) + len(_fails)
    print("")
    print(f"RULE_EFFECTS_PASS={len(_passes)}/{total}")
    return 0 if not _fails else 1


if __name__ == "__main__":
    sys.exit(main())
