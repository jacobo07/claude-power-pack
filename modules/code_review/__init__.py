"""modules.code_review -- ECC code-review doctrine applied as
importable Python helpers.

The principles themselves live in `modules.uqf.principles.*` so they
can be enumerated by the auditor. This module gives review-flow
callers thin wrappers that match the natural shape of a review
pipeline:

  filter_false_positives(findings) -> findings (cleaner list)
  validate_high_critical(finding) -> bool
  pre_report_gate(finding) -> bool

Source: ECC/Affaan Mustafa MIT
       (agents/code-reviewer.md +
        rules/common/code-review.md in this repo)
"""
from __future__ import annotations

from modules.uqf.principles.pre_report_gate import PreReportGate
from modules.uqf.principles.false_positives_catalog import (
    CommonFalsePositivesCatalog,
)
from modules.uqf.principles.proof_triad import HighCriticalProofTriad
from modules.uqf.principles.severity_table import SeverityTableOutput
from modules.uqf.principles.zero_findings_valid import ZeroFindingsValid

_pre_report = PreReportGate()
_fp_catalog = CommonFalsePositivesCatalog()
_proof_triad = HighCriticalProofTriad()
_severity_table = SeverityTableOutput()
_zero_findings = ZeroFindingsValid()


def pre_report_gate(finding: dict) -> bool:
    """Return True iff the finding has all 4 ECC gate keys:
    line / failure_mode / surrounding_context / severity_defensible.
    Findings that fail the gate must be dropped or downgraded.
    """
    return _pre_report.check(finding, "code").passed


def filter_false_positives(findings: list[dict]) -> list[dict]:
    """Return a new list containing only findings whose `text` does
    NOT match the ECC common-FP catalog (e.g. 'consider adding error
    handling', 'magic number', etc.).
    """
    result = []
    for f in findings:
        text = f.get("text") or f.get("message") or ""
        if _fp_catalog.check(text, "code").passed:
            result.append(f)
    return result


def validate_high_critical(finding: dict) -> bool:
    """For HIGH/CRITICAL findings, return True iff the proof triad
    (snippet + scenario + why_guards_fail) is present. LOW/MEDIUM
    findings always pass.
    """
    return _proof_triad.check(finding, "code").passed


def derive_verdict(findings: list[dict]) -> str:
    """Compute verdict APPROVE / WARNING / BLOCK from a list of
    findings (ECC mapping)."""
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for f in findings:
        sev = str(f.get("severity", "")).upper()
        if sev in counts:
            counts[sev] += 1
    return SeverityTableOutput.derive_verdict(counts)


def run_full_review(findings: list[dict]) -> dict:
    """Apply the ECC doctrine end-to-end to a raw findings list.

    Pipeline:
      1. Filter common FPs (catalog)
      2. Drop findings that fail the Pre-Report Gate
      3. Validate HIGH/CRITICAL findings against the proof triad
         (demote those without triad to MEDIUM)
      4. Derive the verdict from the cleaned counts

    Returns:
      {
        "kept": [...],
        "dropped_fp": int,
        "dropped_gate": int,
        "demoted": int,
        "counts": {...},
        "verdict": str,
      }
    """
    raw = list(findings)
    after_fp = filter_false_positives(raw)
    dropped_fp = len(raw) - len(after_fp)

    after_gate = [f for f in after_fp if pre_report_gate(f)]
    dropped_gate = len(after_fp) - len(after_gate)

    demoted = 0
    kept = []
    for f in after_gate:
        sev = str(f.get("severity", "")).upper()
        if sev in ("HIGH", "CRITICAL") and not validate_high_critical(f):
            f = {**f, "severity": "MEDIUM",
                 "demoted_from": sev,
                 "demotion_reason": "missing proof triad"}
            demoted += 1
        kept.append(f)

    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for f in kept:
        sev = str(f.get("severity", "")).upper()
        if sev in counts:
            counts[sev] += 1
    verdict = SeverityTableOutput.derive_verdict(counts)

    return {
        "kept": kept,
        "dropped_fp": dropped_fp,
        "dropped_gate": dropped_gate,
        "demoted": demoted,
        "counts": counts,
        "verdict": verdict,
    }


__all__ = [
    "pre_report_gate",
    "filter_false_positives",
    "validate_high_critical",
    "derive_verdict",
    "run_full_review",
]
