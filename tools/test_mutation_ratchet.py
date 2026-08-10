#!/usr/bin/env python3
"""V-gates for tools/mutation_ratchet.py.

The probe itself is covered by test_mutation_probe.py. What is exercised here is
the JUDGEMENT: which kill counts are a regression, which are a shifted sample,
and which are not a measurement at all. Each gate is run against a state
constructed to fail it -- a ratchet proven only on a passing pair would be the
vacuity its own subject exists to catch.

The probe is stubbed rather than run, so these gates cost milliseconds instead of
the 38s a real push-tier sweep takes.

    python tools/test_mutation_ratchet.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

import tools.mutation_ratchet as mr  # noqa: E402

_passes = 0
_fails = 0

# Any pair of files that exist, so the absent-file branch is not what is tested.
REAL_PAIR = "tools/mutation_ratchet.py::modules/ias_c2/opportunity_cost.py"


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  [PASS] {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    global _fails
    _fails += 1
    print(f"  [FAIL] {gate}: {diagnostic}")


class _Stub:
    """Rebinds probe/module_hash so a verdict can be forced without a sweep."""

    def __init__(self, killed: int, sampled: int = 6, digest: str = "SAME") -> None:
        self.killed, self.sampled, self.digest = killed, sampled, digest

    def __enter__(self):
        self._probe, self._hash = mr.probe, mr.module_hash
        mr.probe = lambda s, m, n: {
            "verdict": "PARTIAL", "killed": ["m"] * self.killed,
            "survived": [], "sampled": self.sampled, "restored_intact": True}
        mr.module_hash = lambda p: self.digest
        return self

    def __exit__(self, *exc: object) -> None:
        mr.probe, mr.module_hash = self._probe, self._hash


def main() -> int:
    print("== V-RATCHET gates ==")
    floor = {"tier": "push", "min_kill": 3, "module_hash": "SAME"}

    with _Stub(killed=4):
        r = mr.measure(REAL_PAIR, dict(floor))
        _ok("V-RATCHET-PASS", f"4 >= floor 3 -> {r['verdict']}") \
            if r["verdict"] == mr.PASS else \
            _fail("V-RATCHET-PASS", f"got {r['verdict']}")

    # The load-bearing direction: fewer defects caught, module untouched.
    with _Stub(killed=1):
        r = mr.measure(REAL_PAIR, dict(floor))
        _ok("V-RATCHET-DROP-UNCHANGED-FAILS",
            "a suite catching fewer injected defects against an unchanged module "
            "is a FAIL") \
            if r["verdict"] == mr.FAIL else \
            _fail("V-RATCHET-DROP-UNCHANGED-FAILS", f"got {r['verdict']}: {r['reason']}")

    # Editing the module shifts which constructs are sampled, so the same drop is
    # not evidence of a weakened suite. Pinning a number that moves for someone
    # else's correct commit is how a gate earns its uninstall.
    with _Stub(killed=1, digest="DIFFERENT"):
        r = mr.measure(REAL_PAIR, dict(floor))
        _ok("V-RATCHET-DROP-CHANGED-WARNS",
            "the same drop against a changed module is a WARN naming the re-baseline") \
            if r["verdict"] == mr.WARN else \
            _fail("V-RATCHET-DROP-CHANGED-WARNS", f"got {r['verdict']}")

    # A pair with no recorded floor has not been measured. Calling that PASS would
    # let an unbaselined pair read as healthy.
    with _Stub(killed=0):
        r = mr.measure(REAL_PAIR, {"tier": "push"})
        _ok("V-RATCHET-NO-FLOOR-IS-UNMEASURABLE", "an unbaselined pair is not a pass") \
            if r["verdict"] == mr.UNMEASURABLE else \
            _fail("V-RATCHET-NO-FLOOR-IS-UNMEASURABLE", f"got {r['verdict']}")

    # An absent file is unmeasurable, never a regression: a partial checkout would
    # otherwise fail the build for the wrong reason.
    with _Stub(killed=0):
        r = mr.measure("tools/no_such_suite.py::modules/no_such_module.py", dict(floor))
        _ok("V-RATCHET-ABSENT-IS-UNMEASURABLE", "a missing file is not a failure") \
            if r["verdict"] == mr.UNMEASURABLE else \
            _fail("V-RATCHET-ABSENT-IS-UNMEASURABLE", f"got {r['verdict']}")

    # An empty tier checks nothing, and silence would read as health.
    with tempfile.TemporaryDirectory() as td:
        empty = Path(td) / "ratchet.json"
        empty.write_text(json.dumps({"pairs": {}}), encoding="utf-8")
        real_cfg, mr.CONFIG = mr.CONFIG, empty
        try:
            code = mr.main(["--tier", "push"])
        finally:
            mr.CONFIG = real_cfg
        _ok("V-RATCHET-EMPTY-TIER-NOT-SILENT", f"an empty tier exits {code}, not 0") \
            if code != 0 else \
            _fail("V-RATCHET-EMPTY-TIER-NOT-SILENT", "an empty tier passed silently")

    # Every floor in the live config must carry the evidence it was measured. A
    # floor typed by hand measures memory, and would sit above or below the real
    # kill count with nothing to say which.
    cfg = mr.load_config()
    unmeasured = [k for k, v in cfg.get("pairs", {}).items()
                  if "min_kill" in v and not (v.get("module_hash") and v.get("measured_at"))]
    _check_pairs = len(cfg.get("pairs", {}))
    _ok("V-RATCHET-FLOORS-ARE-MEASURED",
        f"all {_check_pairs} configured pair(s) carry a hash and a timestamp, or no floor") \
        if not unmeasured else \
        _fail("V-RATCHET-FLOORS-ARE-MEASURED", f"hand-set floors: {unmeasured}")

    total = _passes + _fails
    print(f"\nMUTATION_RATCHET_TESTS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


def test_all_gates() -> None:
    """pytest entry point -- an authored gate the canonical run cannot execute
    inflates the denominator and protects nothing."""
    assert main() == 0


if __name__ == "__main__":
    raise SystemExit(main())
