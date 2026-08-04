#!/usr/bin/env python3
"""V-gate for the SQI Baseline Ratchet (Ley XV) and the rule counterfactual probe.

The load-bearing test is V-RATCHET-LIVE-NOT-SATURATED: the repository's REAL
baseline (test_file_reach 2.97 %, 86 executed, unchanged since 2026-07-12) must
come back NOT_SATURATED. A detector keyed on staleness reports saturation there
and proposes raising a bar that 3 % of the authored surface currently meets --
benchmark theatre, and the exact pathology this module exists to avoid.

    python tools/test_sqi_ratchet.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.sqi import ratchet                                    # noqa: E402
from modules.rule_compiler import counterfactual as cf             # noqa: E402

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  [PASS] {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  [FAIL] {gate}: {diagnostic}")


def _baseline(*, reach, executed, authored, roots=1, env="E1", oracle="documentation"):
    return {
        "version": 1,
        "commit": "deadbeef",
        "environment_key": env,
        "roots": {
            f"pytest r{i}/": {
                "invocation": f"pytest r{i}/",
                "oracle": oracle,
                "executed_cases": executed // roots,
                "executed_files": [f"r{i}/test_a.py"],
            }
            for i in range(roots)
        },
        "authored_count": authored,
        "authored_identities": [f"f{i}.py" for i in range(authored)],
        "test_file_reach": reach,
    }


def _seed(ledger: Path, base: dict, n: int, verdict="BASELINE_PASS") -> None:
    for _ in range(n):
        ratchet.record(base, verdict, ledger_path=ledger)


def main() -> int:
    print("SQI RATCHET V-GATE (Ley XV enforcement)")

    # --- 1. the live baseline must NOT read as saturated -------------------------------
    live_path = PP_ROOT / "vault" / "audits" / "sqi_baseline.json"
    if not live_path.is_file():
        _fail("V-RATCHET-LIVE-NOT-SATURATED", f"live baseline absent at {live_path}")
    else:
        live = json.loads(live_path.read_text(encoding="utf-8-sig"))
        with tempfile.TemporaryDirectory() as td:
            led = Path(td) / "obs.jsonl"
            _seed(led, live, 5)                      # abundant history, low bar
            v = ratchet.is_saturated(live, ledger_path=led)
            if v.verdict == ratchet.NOT_SATURATED:
                _ok("V-RATCHET-LIVE-NOT-SATURATED",
                    f"reach={live.get('test_file_reach'):.4f} -> {v.verdict}; "
                    f"unmet[0]={v.unmet[0][:70]}")
            else:
                _fail("V-RATCHET-LIVE-NOT-SATURATED",
                      f"live baseline returned {v.verdict}; a 2.97% bar cannot be "
                      f"saturated -- this is benchmark theatre")

            if not ratchet.propose(live, v):
                _ok("V-RATCHET-NO-PROPOSAL-UNLESS-SATURATED",
                    "propose() returned 0 candidates on a NOT_SATURATED verdict")
            else:
                _fail("V-RATCHET-NO-PROPOSAL-UNLESS-SATURATED",
                      "candidates emitted without a saturation licence")

    # --- 2. empty ledger must not be vacuously saturated (all([]) trap) -----------------
    with tempfile.TemporaryDirectory() as td:
        led = Path(td) / "empty.jsonl"
        v = ratchet.is_saturated(_baseline(reach=1.0, executed=500, authored=200),
                                 ledger_path=led)
        if v.verdict == ratchet.INSUFFICIENT_HISTORY:
            _ok("V-RATCHET-EMPTY-HISTORY",
                f"0 observations -> {v.verdict} (never SATURATED)")
        else:
            _fail("V-RATCHET-EMPTY-HISTORY",
                  f"expected INSUFFICIENT_HISTORY, got {v.verdict}")

    # --- 3. a genuinely saturated bar ---------------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        led = Path(td) / "sat.jsonl"
        b = _baseline(reach=0.98, executed=400, authored=150)
        _seed(led, b, 3)
        v = ratchet.evaluate(b, ledger_path=led)
        if v.verdict == ratchet.SATURATED:
            _ok("V-RATCHET-SATURATED",
                f"5/5 conditions met -> {v.verdict}, {len(v.reasons)} reasons")
        else:
            _fail("V-RATCHET-SATURATED",
                  f"expected SATURATED, got {v.verdict}; unmet={v.unmet}")

        if v.candidates:
            _ok("V-RATCHET-PROPOSES", f"{len(v.candidates)} escalation candidate(s)")
        else:
            _fail("V-RATCHET-PROPOSES", "saturated bar produced no candidates")

        missing = [c.axis for c in v.candidates if not c.instrument]
        if not missing:
            _ok("V-RATCHET-INSTRUMENT-REQUIRED",
                f"all {len(v.candidates)} candidates name a measuring instrument")
        else:
            _fail("V-RATCHET-INSTRUMENT-REQUIRED",
                  f"candidates without an instrument: {missing}")

        # hermetic: the same inputs twice, the same verdict
        v2 = ratchet.evaluate(b, ledger_path=led)
        if v2.verdict == v.verdict and len(v2.candidates) == len(v.candidates):
            _ok("V-RATCHET-HERMETIC",
                f"second run identical ({v2.verdict}, {len(v2.candidates)} candidates)")
        else:
            _fail("V-RATCHET-HERMETIC",
                  f"run1={v.verdict}/{len(v.candidates)} run2={v2.verdict}/"
                  f"{len(v2.candidates)}")

    # --- 4. the deletion attack: a ratio alone must not license saturation ---------------
    with tempfile.TemporaryDirectory() as td:
        led = Path(td) / "del.jsonl"
        # every authored file reached (reach 1.0) because the denominator was gutted
        b = _baseline(reach=1.0, executed=6, authored=3)
        _seed(led, b, 3)
        v = ratchet.is_saturated(b, ledger_path=led)
        if v.verdict == ratchet.NOT_SATURATED:
            _ok("V-RATCHET-RATIO-NOT-ALONE",
                f"reach=1.0 with 6 executed/3 authored -> {v.verdict} "
                f"(absolutes gate the ratio)")
        else:
            _fail("V-RATCHET-RATIO-NOT-ALONE",
                  f"a gutted denominator bought saturation: {v.verdict}")

    # --- 5. a regression inside the window means the bar still bites ---------------------
    with tempfile.TemporaryDirectory() as td:
        led = Path(td) / "reg.jsonl"
        b = _baseline(reach=0.99, executed=400, authored=150)
        _seed(led, b, 2)
        ratchet.record(b, "BASELINE_REGRESSION", ledger_path=led)
        v = ratchet.is_saturated(b, ledger_path=led)
        if v.verdict == ratchet.NOT_SATURATED and any("regression" in u for u in v.unmet):
            _ok("V-RATCHET-REGRESSION-IN-WINDOW",
                "a regression verdict in the window blocks saturation")
        else:
            _fail("V-RATCHET-REGRESSION-IN-WINDOW",
                  f"got {v.verdict}, unmet={v.unmet}")

    # --- 6. environment isolation --------------------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        led = Path(td) / "env.jsonl"
        b_e1 = _baseline(reach=0.99, executed=400, authored=150, env="E1")
        b_e2 = _baseline(reach=0.99, executed=400, authored=150, env="E2")
        _seed(led, b_e2, 5)                        # history belongs to another system
        v = ratchet.is_saturated(b_e1, ledger_path=led)
        if v.verdict == ratchet.INSUFFICIENT_HISTORY:
            _ok("V-RATCHET-ENV-ISOLATION",
                "observations under a foreign environment key are dropped, not compared")
        else:
            _fail("V-RATCHET-ENV-ISOLATION",
                  f"foreign-env history was counted: {v.verdict}")

    # --- 7. fail-open absolute ------------------------------------------------------------
    for bad in (None, "not a dict", 42, []):
        v = ratchet.is_saturated(bad)                          # type: ignore[arg-type]
        if v.verdict != ratchet.UNMEASURABLE:
            _fail("V-RATCHET-FAILOPEN", f"{type(bad).__name__} -> {v.verdict}")
            break
    else:
        _ok("V-RATCHET-FAILOPEN",
            "4 malformed baselines -> UNMEASURABLE, no exception, never a pass")

    # --- 8. ledger round-trip + corrupt-line tolerance --------------------------------
    with tempfile.TemporaryDirectory() as td:
        led = Path(td) / "rt.jsonl"
        b = _baseline(reach=0.5, executed=100, authored=50)
        ratchet.record(b, "BASELINE_PASS", ledger_path=led)
        with led.open("a", encoding="utf-8") as fh:
            fh.write("{ this is not json\n")
        ratchet.record(b, "BASELINE_PASS", ledger_path=led)
        obs, err = ratchet.load_observations(ledger_path=led, environment_key="E1")
        if err is None and len(obs) == 2 and obs[0].executed_total == 100:
            _ok("V-RATCHET-LEDGER-ROUNDTRIP",
                "2 observations recovered; 1 corrupt line skipped without disarming")
        else:
            _fail("V-RATCHET-LEDGER-ROUNDTRIP", f"obs={len(obs)} err={err}")

    # --- 9. counterfactual probe ----------------------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        reg = Path(td) / "cf.json"
        detector = Path(td) / "detector.py"
        detector.write_text(
            "import sys\n"
            "data = sys.stdin.read()\n"
            "sys.exit(2 if 'rm -rf /' in data else 0)\n",
            encoding="utf-8",
        )
        reg.write_text(json.dumps({"counterfactuals": [
            {   # the rule fires on the incident that produced it
                "rule_id": "HR-CASCADE-002", "incident_id": "INC-001",
                "incident_input": "rm -rf /home/user/project",
                "probe": ["python", str(detector)], "fires_on_exit": 2,
                "note": "destructive delete without backup",
            },
            {   # the rule does NOT fire on its own origin -- the finding worth having
                "rule_id": "HR-PHANTOM-001", "incident_id": "INC-002",
                "incident_input": "some unrelated incident text",
                "probe": ["python", str(detector)], "fires_on_exit": 2,
            },
            {   # neither pattern nor exit declared -> cannot be judged
                "rule_id": "HR-VAGUE-001", "incident_id": "INC-003",
                "incident_input": "x", "probe": ["python", str(detector)],
            },
            {"rule_id": "HR-BROKEN-001"},          # malformed: must be dropped
        ]}), encoding="utf-8")

        claims = cf.load_claims(reg)
        if len(claims) == 3:
            _ok("V-CF-MALFORMED-DROPPED",
                "3 of 4 rows loaded; the malformed row is absent, not a pass")
        else:
            _fail("V-CF-MALFORMED-DROPPED", f"loaded {len(claims)} rows, expected 3")

        results = {r.claim.rule_id: r.verdict for r in cf.measure_all(reg)}
        if results.get("HR-CASCADE-002") == cf.WOULD_BLOCK:
            _ok("V-CF-WOULD-BLOCK", "detector fired on the incident that produced the rule")
        else:
            _fail("V-CF-WOULD-BLOCK", f"got {results.get('HR-CASCADE-002')}")

        if results.get("HR-PHANTOM-001") == cf.WOULD_NOT_BLOCK:
            _ok("V-CF-WOULD-NOT-BLOCK",
                "a rule that does not fire on its own origin is surfaced, not assumed")
        else:
            _fail("V-CF-WOULD-NOT-BLOCK", f"got {results.get('HR-PHANTOM-001')}")

        if results.get("HR-VAGUE-001") == cf.UNMEASURABLE:
            _ok("V-CF-UNMEASURABLE",
                "a claim declaring no fire condition is UNMEASURABLE, never a default block")
        else:
            _fail("V-CF-UNMEASURABLE", f"got {results.get('HR-VAGUE-001')}")

    total = _passes + _fails
    print(f"\nSQI_RATCHET_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
