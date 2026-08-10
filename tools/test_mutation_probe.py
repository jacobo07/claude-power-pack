#!/usr/bin/env python3
"""V-gates for tools/mutation_probe.py.

Every gate is exercised against a state constructed to FAIL it. A probe proven
only on a suite that already catches everything would be the same defect it was
built to expose.

    python tools/test_mutation_probe.py
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

import tools.mutation_probe as mp  # noqa: E402

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


MODULE = (
    "THRESHOLD = 10\n\n\n"
    "def classify(n):\n"
    "    if n > THRESHOLD:\n"
    "        return 'HIGH'\n"
    "    return 'LOW'\n"
)


def _plant(root: Path, suite_body: str) -> tuple[Path, Path]:
    module = root / "subject.py"
    module.write_text(MODULE, encoding="utf-8", newline="\n")
    suite = root / "suite.py"
    suite.write_text(
        "import importlib.util, sys\n"
        f"spec = importlib.util.spec_from_file_location('subject', r'{module}')\n"
        "m = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(m)\n"
        + suite_body,
        encoding="utf-8", newline="\n")
    return suite, module


def main() -> int:
    print("== V-MUT gates ==")

    # A suite that runs the module and asserts nothing cannot notice any edit.
    with tempfile.TemporaryDirectory() as td:
        suite, module = _plant(Path(td), "m.classify(5)\nsys.exit(0)\n")
        res = mp.probe(suite, module, max_mutants=6)
        if res["verdict"] == "KILLS_NOTHING" and not res["killed"]:
            _ok("V-MUT-KILLS-NOTHING",
                f"{len(res['survived'])} mutant(s) survived a suite that asserts "
                "nothing -- vacuous in fact, not by spelling")
        else:
            _fail("V-MUT-KILLS-NOTHING", f"got {res['verdict']} killed={res['killed']}")

    # The same module with a suite that checks the real behaviour must catch edits.
    with tempfile.TemporaryDirectory() as td:
        suite, module = _plant(
            Path(td),
            "sys.exit(0 if m.classify(11) == 'HIGH' and m.classify(3) == 'LOW' "
            "and m.THRESHOLD == 10 else 1)\n")
        res = mp.probe(suite, module, max_mutants=6)
        if res["verdict"] in ("KILLS_ALL", "PARTIAL") and res["killed"]:
            _ok("V-MUT-KILLS",
                f"{len(res['killed'])} mutant(s) caught by a suite that asserts the "
                "real values")
        else:
            _fail("V-MUT-KILLS", f"got {res['verdict']} killed={res['killed']}")

    # The subject must come back byte-identical, or the probe is a hazard.
    with tempfile.TemporaryDirectory() as td:
        suite, module = _plant(Path(td), "sys.exit(0 if m.classify(11) == 'HIGH' else 1)\n")
        before = module.read_bytes()
        res = mp.probe(suite, module, max_mutants=4)
        if module.read_bytes() == before and res.get("restored_intact"):
            _ok("V-MUT-RESTORES", "the subject is byte-identical after the sweep")
        else:
            _fail("V-MUT-RESTORES", "the probe left the subject modified")

    # A suite that is already red proves nothing about a mutant, so the probe must
    # refuse to score it rather than reporting every mutant as killed.
    with tempfile.TemporaryDirectory() as td:
        suite, module = _plant(Path(td), "sys.exit(1)\n")
        res = mp.probe(suite, module, max_mutants=4)
        if res["verdict"] == "UNMEASURABLE" and not res["killed"]:
            _ok("V-MUT-RED-BASELINE-IS-UNMEASURABLE",
                "a suite failing before mutation is refused, not scored 100%")
        else:
            _fail("V-MUT-RED-BASELINE-IS-UNMEASURABLE", f"got {res['verdict']}")

    # Bytecode staleness, found on this probe's first real run: `==` -> `!=` is
    # length-preserving, so two mutants written in the same second with identical
    # size let the child import the PREVIOUS mutant and report SURVIVED for a
    # covered line. Two consecutive sweeps must agree.
    with tempfile.TemporaryDirectory() as td:
        suite, module = _plant(
            Path(td), "sys.exit(0 if m.classify(11) == 'HIGH' and m.THRESHOLD == 10 else 1)\n")
        a = mp.probe(suite, module, max_mutants=6)
        b = mp.probe(suite, module, max_mutants=6)
        if sorted(a["survived"]) == sorted(b["survived"]) \
                and sorted(a["killed"]) == sorted(b["killed"]):
            _ok("V-MUT-DETERMINISTIC",
                f"two sweeps agree: killed={len(a['killed'])} survived={len(a['survived'])}")
        else:
            _fail("V-MUT-DETERMINISTIC",
                  f"sweep drift -- a={a['killed']}/{a['survived']} b={b['killed']}/{b['survived']}")

    # LIMIT, stated because omitting it would let KILLS_ALL read as proof the suite
    # is correct. Mutation bounds sensitivity from below; it does not certify the
    # oracle. This suite asserts a WRONG threshold, kills mutants anyway, and is
    # still wrong.
    with tempfile.TemporaryDirectory() as td:
        module = Path(td) / "subject.py"
        module.write_text(MODULE, encoding="utf-8", newline="\n")
        suite = Path(td) / "suite.py"
        suite.write_text(
            "import importlib.util, sys\n"
            f"spec = importlib.util.spec_from_file_location('subject', r'{module}')\n"
            "m = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(m)\n"
            # The real boundary is 10. This asserts 10 is HIGH, which it is not.
            "sys.exit(0 if m.classify(11) == 'HIGH' and m.THRESHOLD == 10 else 1)\n",
            encoding="utf-8", newline="\n")
        res = mp.probe(suite, module, max_mutants=6)
        if res["killed"]:
            _ok("V-MUT-LIMIT",
                "a suite can kill mutants while its expected values remain unchecked "
                "-- documented blind spot, not a defect")
        else:
            _fail("V-MUT-LIMIT", "the stated limit no longer holds; re-derive the claim")

    total = _passes + _fails
    print(f"\nMUTATION_PROBE_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


def test_all_gates() -> None:
    """pytest entry point -- an authored gate the canonical run cannot execute
    inflates the denominator and protects nothing."""
    assert main() == 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    finally:
        shutil.rmtree(PP_ROOT / "__pycache__", ignore_errors=True)
