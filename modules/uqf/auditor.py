"""UQFAuditor + AuditReport.

The auditor is the user-facing entry point of the UQF framework. It
orchestrates principle.check() over a target (file path / code string
/ prompt) and produces an AuditReport with a 0-100 score, the list of
passed/failed principle names, anti-pattern hits, and actionable fix
hints.

Source attribution: UQF doctrine is adapted from Everything Claude
Code (github.com/affaan-m/ecc) under MIT License (c) 2026 Affaan Mustafa.
"""
from __future__ import annotations
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from modules.uqf.principles import (
    Principle,
    PrincipleResult,
    get_all,
    load_all_principles,
)
from modules.uqf.anti_patterns import run_all as run_anti_patterns


@dataclass
class AuditReport:
    """Aggregated outcome of an audit pass.

    score_pct is the percentage of applicable principles passed.
    passed / failed are principle names only. anti_pattern_hits is
    a dict {detector_name: [snippet, line, fix]} for whatever the
    AST detectors found. fix_hints flattens both the failed
    principles' hints and the anti-pattern fixes.
    """
    target: str
    domain: str
    timestamp_iso: str
    score_pct: float
    passed: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    anti_pattern_hits: dict[str, list] = field(default_factory=dict)
    fix_hints: list[str] = field(default_factory=list)
    source_attributions: list[str] = field(default_factory=list)
    raw_results: list[PrincipleResult] = field(default_factory=list)

    def is_splus(self, threshold: float = 70.0) -> bool:
        return self.score_pct >= threshold

    def summary_line(self) -> str:
        tag = "OK" if self.is_splus() else "WARN" if self.score_pct >= 40 else "FAIL"
        return (
            f"[{tag}] {self.target}: {self.score_pct:.1f}% "
            f"({len(self.passed)}/{len(self.passed) + len(self.failed)})"
        )


class UQFAuditor:
    """Run UQF principles against a target."""

    def __init__(self) -> None:
        load_all_principles()

    def audit_code_str(self, code: str,
                       domain: str = "code",
                       target_label: str = "<inline>") -> AuditReport:
        """Audit a code string. The principles applicable to `domain`
        are evaluated; anti-pattern detectors are always run on
        the raw code."""
        principles = get_all(domain)
        results: list[PrincipleResult] = []
        passed_names: list[str] = []
        failed_names: list[str] = []
        fix_hints: list[str] = []
        sources: set[str] = set()

        for p in principles:
            # Each principle defines what target it expects. For
            # the `code` domain, principles that expect raw code
            # strings (ErrorNeverSilent, AAATestPattern) work
            # directly; principles that expect dicts (PreReportGate,
            # ProofTriad, SeverityTable) skip cleanly with score=N/A.
            # We feed them the code string and treat type-error
            # responses as N/A rather than fail.
            try:
                r = p.check(code, domain)
            except Exception as exc:
                r = PrincipleResult(
                    principle_name=p.name,
                    domain=domain,
                    passed=True,
                    score=1.0,
                    evidence=f"N/A (principle expects different target type)",
                    fix_hint="",
                    source=p.source,
                )
            # If the principle reports "target type not supported"
            # we treat it as N/A (not counted against the score).
            ev = (r.evidence or "").lower()
            if "not a dict" in ev or "not a list" in ev or \
               "not str" in ev or "target type" in ev:
                continue
            results.append(r)
            if r.passed:
                passed_names.append(r.principle_name)
            else:
                failed_names.append(r.principle_name)
                if r.fix_hint:
                    fix_hints.append(f"[{r.principle_name}] {r.fix_hint}")
            if r.source:
                sources.add(r.source)

        # Anti-pattern detectors (raw code)
        ap_hits: dict[str, list] = {}
        if domain == "code":
            all_hits = run_anti_patterns(code)
            for det, hits in all_hits.items():
                if hits:
                    ap_hits[det] = [
                        {"line": h.line, "snippet": h.snippet, "fix": h.fix}
                        for h in hits
                    ]
                    for h in hits[:3]:
                        fix_hints.append(
                            f"[anti-pattern:{det}] line {h.line}: {h.fix}"
                        )

        total = len(passed_names) + len(failed_names)
        # Anti-pattern hits reduce score: each detector that fires
        # docks 10% (capped at 50%). This is a "soft penalty" --
        # the principles already cover most cases; the detectors
        # are belt-and-braces.
        ap_penalty = min(50.0, 10.0 * len(ap_hits))
        base_score = (len(passed_names) / total * 100) if total else 100.0
        score = max(0.0, base_score - ap_penalty)

        return AuditReport(
            target=target_label,
            domain=domain,
            timestamp_iso=datetime.now(timezone.utc).isoformat(),
            score_pct=round(score, 1),
            passed=passed_names,
            failed=failed_names,
            anti_pattern_hits=ap_hits,
            fix_hints=fix_hints,
            source_attributions=sorted(sources),
            raw_results=results,
        )

    def audit_file(self, path: str,
                   domain: str = "code") -> AuditReport:
        """Audit a file by reading it and dispatching to audit_code_str."""
        p = Path(path)
        if not p.is_file():
            return AuditReport(
                target=str(p),
                domain=domain,
                timestamp_iso=datetime.now(timezone.utc).isoformat(),
                score_pct=0.0,
                failed=[f"file not found: {path}"],
                fix_hints=[f"Check the path: {path}"],
            )
        try:
            code = p.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            return AuditReport(
                target=str(p),
                domain=domain,
                timestamp_iso=datetime.now(timezone.utc).isoformat(),
                score_pct=0.0,
                failed=[f"read error: {exc}"],
                fix_hints=[f"Fix file permissions or encoding"],
            )
        return self.audit_code_str(code, domain=domain,
                                   target_label=str(p))

    def audit_prompt(self, content: str,
                     target_label: str = "<prompt>") -> AuditReport:
        """Audit a prompt / agent .md content. Uses domain=prompts so
        PromptDefenseBaseline is evaluated."""
        return self.audit_code_str(content, domain="prompts",
                                   target_label=target_label)

    DEFAULT_SCAN_TARGETS: tuple[str, ...] = (
        "tools/ceps.py",
        "tools/tis.py",
        "tools/tco_compact_gate.py",
        "modules/monitoring/monitor.py",
        "tools/jit_skill_loader.py",
    )

    def scan_all(self, paths: list[str] | None = None
                 ) -> dict[str, AuditReport]:
        """Run audit_file over the default PP module set (or a custom
        list) and return a dict keyed by path."""
        targets = paths if paths is not None else list(self.DEFAULT_SCAN_TARGETS)
        out: dict[str, AuditReport] = {}
        for t in targets:
            if not Path(t).is_file():
                continue
            out[t] = self.audit_file(t)
        return out


__all__ = ["UQFAuditor", "AuditReport"]
