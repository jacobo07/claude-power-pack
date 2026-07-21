#!/usr/bin/env python3
"""test_unknown_unknown_generator.py -- V-gates for FIOS II-1 Unknown-Unknown Hunter.

Verifies the engine that finds gaps no record contains, as a structural asymmetry
against a discovered peer cohort. The core discipline is observed to refuse: a
universally-present feature must yield NO finding (no peer lacks it), and a minority
feature's absence must NOT be flagged (its absence is the norm, not a gap) -- these
are the two ways the detector could over-fire, and both are gated.

  V-UUG-MAJORITY-ABSENCE     a feature in 4/5 peers, absent in 1 -> exactly that peer flagged
  V-UUG-UNANIMOUS-SILENT     a feature present in ALL peers -> 0 findings
  V-UUG-MINORITY-NOT-FLAGGED a feature in 2/5 peers -> the 3 lacking it are NOT flagged
  V-UUG-SMALL-COHORT         a cohort below the min size -> [] (majority undefined)
  V-UUG-DISCOVERED-COHORT    cohort_from_paths reads real files; the odd-one-out is flagged
  V-UUG-FAIL-OPEN            a raising feature_fn / a missing path -> [] (never raises)
  V-UUG-QUESTION-SHAPE       a finding is pipeline-shaped (source, source_ref, uu: fp, asdict)
  V-UUG-DETERMINISTIC        identical cohort -> identical findings and order on re-run

Hermetic: the discovered-cohort gate writes to a fresh tempdir -- NO global writes,
identical on re-run (run x3). V-<DOMAIN>-<NAME>; UUG_VERDICT line for the done-gate grep.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.frontier_intelligence import unknown_unknown_generator as UUG  # noqa: E402

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  PASS {gate}: {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    print(f"  FAIL {gate}: {diag}")


def test_majority_absence() -> None:
    # Arrange -- 5 peers; feature 'x' in 4, absent from 'e'.
    cohort = {"a": {"x", "y"}, "b": {"x"}, "c": {"x"}, "d": {"x"}, "e": {"y"}}
    # Act
    absences = UUG.detect_absences(cohort, cohort_name="C")
    # Assert -- exactly one absence, peer 'e', feature 'x', present 4/5.
    xs = [a for a in absences if a.feature == "x"]
    if len(xs) == 1 and xs[0].peer == "e" and xs[0].present == 4 and xs[0].cohort_size == 5:
        _ok("V-UUG-MAJORITY-ABSENCE", "4/5 feature absent from one peer -> flagged")
    else:
        _fail("V-UUG-MAJORITY-ABSENCE", f"expected e/x/4, got {absences}")


def test_unanimous_silent() -> None:
    # Arrange -- feature 'u' present in all 4 peers.
    cohort = {"a": {"u"}, "b": {"u"}, "c": {"u"}, "d": {"u"}}
    # Act
    absences = UUG.detect_absences(cohort)
    # Assert -- no peer lacks a universal feature -> no asymmetry.
    if not absences:
        _ok("V-UUG-UNANIMOUS-SILENT", "universally-present feature yields 0 findings")
    else:
        _fail("V-UUG-UNANIMOUS-SILENT", f"expected 0, got {absences}")


def test_minority_not_flagged() -> None:
    # Arrange -- feature 'r' in only 2/5 peers (below the 0.75 majority).
    cohort = {"a": {"r"}, "b": {"r"}, "c": set(), "d": set(), "e": set()}
    # Act
    absences = UUG.detect_absences(cohort)
    # Assert -- a rare feature's absence is normal, not an unknown-unknown.
    if not any(a.feature == "r" for a in absences):
        _ok("V-UUG-MINORITY-NOT-FLAGGED", "minority feature's absence not flagged")
    else:
        _fail("V-UUG-MINORITY-NOT-FLAGGED", f"minority feature wrongly flagged: {absences}")


def test_small_cohort() -> None:
    # Arrange -- 2 peers; a majority over two is not meaningful.
    cohort = {"a": {"x"}, "b": set()}
    # Act
    absences = UUG.detect_absences(cohort)
    # Assert
    if not absences:
        _ok("V-UUG-SMALL-COHORT", "cohort below min size yields []")
    else:
        _fail("V-UUG-SMALL-COHORT", f"expected [], got {absences}")


def test_discovered_cohort() -> None:
    # Arrange -- 4 real files; three carry a FINAL LAW marker, one does not.
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        for name in ("one.txt", "two.txt", "three.txt"):
            (base / name).write_text("PART I FINAL LAW. body with DERIVED marking.",
                                     encoding="utf-8")
        (base / "four.txt").write_text("body with DERIVED marking but no closing law.",
                                       encoding="utf-8")
        paths = sorted(base.glob("*.txt"))
        # Act
        qs = UUG.generate(paths, cohort_name="tmp")
        # Assert -- 'four.txt' is the only peer missing 'final_law' -> surfaced.
        four = [q for q in qs if "four.txt" in q.source_ref and "final_law" in q.source_ref]
        if len(four) == 1 and four[0].source == "structural_absence":
            _ok("V-UUG-DISCOVERED-COHORT", "odd-one-out file flagged from a real discovered cohort")
        else:
            _fail("V-UUG-DISCOVERED-COHORT", f"expected four.txt/final_law, got {[q.source_ref for q in qs]}")


def test_fail_open() -> None:
    # Arrange -- a feature_fn that raises, and a nonexistent path.
    def boom(_text):
        raise RuntimeError("boom")

    # Act
    r1 = UUG.generate([str(_PP_ROOT / "does_not_exist_xyz.txt")], feature_fn=boom)
    r2 = UUG.detect_absences("not a dict")  # type: ignore[arg-type]
    # Assert -- both fail open to [].
    if r1 == [] and r2 == []:
        _ok("V-UUG-FAIL-OPEN", "raising feature_fn and bad input both fail open to []")
    else:
        _fail("V-UUG-FAIL-OPEN", f"expected [] [], got {r1} {r2}")


def test_question_shape() -> None:
    # Arrange / Act
    qs = UUG.as_questions(UUG.detect_absences(
        {"a": {"x"}, "b": {"x"}, "c": {"x"}, "d": set()}, cohort_name="C"))
    if not qs:
        _fail("V-UUG-QUESTION-SHAPE", "no question produced to inspect")
        return
    q = qs[0]
    d = UUG.as_declaration_questions(qs)[0]
    ok = (q.source == "structural_absence" and q.source_ref.startswith("absence:C:")
          and q.fingerprint.startswith("uu:") and d.get("text") == q.text
          and d.get("expected_asset") == "asset")
    if ok:
        _ok("V-UUG-QUESTION-SHAPE", "pipeline-shaped: source/source_ref/uu: fp/asdict")
    else:
        _fail("V-UUG-QUESTION-SHAPE", f"shape mismatch: {q}")


def test_deterministic() -> None:
    # Arrange
    cohort = {"a": {"x", "z"}, "b": {"x", "z"}, "c": {"x", "z"}, "d": {"z"}, "e": {"x"}}
    # Act -- two independent runs.
    q1 = UUG.as_questions(UUG.detect_absences(cohort, cohort_name="C"))
    q2 = UUG.as_questions(UUG.detect_absences(cohort, cohort_name="C"))
    # Assert -- identical fingerprints in identical order.
    if [q.fingerprint for q in q1] == [q.fingerprint for q in q2] and q1:
        _ok("V-UUG-DETERMINISTIC", f"{len(q1)} findings identical across runs")
    else:
        _fail("V-UUG-DETERMINISTIC", "nondeterministic order/fingerprints")


def main() -> int:
    print("== unknown_unknown_generator (FIOS II-1) ==")
    for t in (test_majority_absence, test_unanimous_silent, test_minority_not_flagged,
              test_small_cohort, test_discovered_cohort, test_fail_open,
              test_question_shape, test_deterministic):
        t()
    total = _passes + _fails
    print(f"\nUUG_PASS={_passes}/{total}  threshold={total}/{total}")
    print(f"UUG_VERDICT={'PASS' if _fails == 0 else 'FAIL'}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
