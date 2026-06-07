#!/usr/bin/env python3
"""Automation ROI Analyzer -- CPP Setup OS Pillar 2 (Sprint 3 / M12).

Reads a ProjectProfile and produces a prioritized list of automation
Recommendations. Each carries impact, effort, risk, an ROI score, the
install mode, and an explicit "when NOT to install" (source: Dataset CPP
Setup 1.txt secs. 10 AUTOMATION CANDIDATE MODEL, 11 ROI RANKING MODEL,
27 ANTI-OVERRECOMMENDATION GATE). The Secret Firewall is pinned first
(sec. 3 "Secret Firewall primero", sec. 31 PHASE 1 DOCTRINE).

Pure function over the profile; stdlib-only.
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field

from .scanner import ProjectProfile, scan

# Ordinal weights for the ROI score. ROI = impact / effort, risk-damped.
_IMPACT = {"High": 3, "Medium": 2, "Low": 1}
_EFFORT = {"S": 1, "M": 2, "L": 3}
_RISK_DAMP = {"Low": 1.0, "Medium": 0.75, "High": 0.5}


@dataclass
class Recommendation:
    id: str
    title: str
    category: str          # secret | hook | ci | skill | mcp | command | docs
    impact: str            # High | Medium | Low
    effort: str            # S | M | L
    risk: str              # Low | Medium | High
    install_mode: str      # local | owner-side | dry-run-only
    rationale: str
    when_not_to_install: str
    roi_score: float = 0.0

    def _score(self) -> float:
        return round(
            (_IMPACT[self.impact] / _EFFORT[self.effort])
            * _RISK_DAMP[self.risk], 3)


def _val(p: ProjectProfile, name: str):
    return getattr(p, name).value


def analyze(profile: ProjectProfile) -> list[Recommendation]:
    """Generate + rank automation recommendations for a scanned repo."""
    recs: list[Recommendation] = []

    secret_risk = bool(_val(profile, "secret_sensitive_files_presence"))
    if secret_risk:
        recs.append(Recommendation(
            id="secret-firewall", title="Install local Secret Firewall",
            category="secret", impact="High", effort="S", risk="Low",
            install_mode="local",
            rationale="Secret-sensitive files present; the firewall blocks "
                      "credential writes/leaks before any other automation.",
            when_not_to_install="Never skip when secret files exist; this "
                                "is Phase 1 (Secret Firewall first)."))

    if not _val(profile, "env_example_presence") and secret_risk:
        recs.append(Recommendation(
            id="env-example", title="Add a .env.example template",
            category="docs", impact="Medium", effort="S", risk="Low",
            install_mode="local",
            rationale="Secret files exist with no .env.example -- onboarding "
                      "leaks the real .env shape.",
            when_not_to_install="If the repo intentionally ships no secrets."))

    if not _val(profile, "test_coverage_signal"):
        recs.append(Recommendation(
            id="test-harness", title="Add a test harness + happy/edge tests",
            category="command", impact="High", effort="M", risk="Low",
            install_mode="local",
            rationale="No test signal detected; untested code blocks the "
                      "Reality Contract done-gate.",
            when_not_to_install="If this is a docs-only or spike repo."))

    if not _val(profile, "ci_cd"):
        recs.append(Recommendation(
            id="ci-workflow", title="Add a CI workflow (test + lint on push)",
            category="ci", impact="Medium", effort="M", risk="Low",
            install_mode="owner-side",
            rationale="No CI detected; regressions reach main unguarded.",
            when_not_to_install="If the repo is local-only / never pushed."))

    if not _val(profile, "existing_claude_md"):
        recs.append(Recommendation(
            id="claude-onboarding", title="Add CLAUDE.md + PP onboarding",
            category="docs", impact="Medium", effort="S", risk="Low",
            install_mode="local",
            rationale="No CLAUDE.md; the agent starts every session without "
                      "project doctrine.",
            when_not_to_install="If a parent CLAUDE.md already governs this "
                                "path."))

    if not _val(profile, "existing_hooks"):
        recs.append(Recommendation(
            id="lint-test-hooks", title="Add lint/test PreToolUse hooks",
            category="hook", impact="Medium", effort="M", risk="Medium",
            install_mode="owner-side",
            rationale="No hooks; quality gates are advisory-only.",
            when_not_to_install="Until the Owner reviews hook scope (global "
                                "config = Owner-side action)."))

    if _val(profile, "external_api_presence"):
        recs.append(Recommendation(
            id="api-mcp-governance", title="Add governed MCP for external APIs",
            category="mcp", impact="Medium", effort="M", risk="Medium",
            install_mode="dry-run-only",
            rationale="External API clients detected; an MCP with permission "
                      "boundaries beats ad-hoc calls.",
            when_not_to_install="If the API is touched rarely; MCP costs "
                                "13-14% context per call."))

    if _val(profile, "frontend_presence"):
        recs.append(Recommendation(
            id="frontend-design-skill", title="Enable frontend-design skill",
            category="skill", impact="Medium", effort="S", risk="Low",
            install_mode="local",
            rationale="Frontend surface detected; the design skill raises UI "
                      "quality without bespoke prompting.",
            when_not_to_install="If the UI is throwaway/internal-only."))

    for r in recs:
        r.roi_score = r._score()
    # Secret firewall pinned first; then by ROI desc, then lower effort.
    recs.sort(key=lambda r: (r.category != "secret", -r.roi_score,
                             _EFFORT[r.effort]))
    return recs


def analyze_path(path: str | None = None) -> list[Recommendation]:
    """Convenience: scan a repo then rank recommendations."""
    return analyze(scan(path))


def render(recs: list[Recommendation]) -> str:
    lines = [f"Automation ROI: {len(recs)} recommendation(s) "
             "(secret firewall first, then ROI desc)\n"]
    for i, r in enumerate(recs, 1):
        lines.append(
            f"{i}. [{r.category}] {r.title}\n"
            f"   impact={r.impact} effort={r.effort} risk={r.risk} "
            f"ROI={r.roi_score} mode={r.install_mode}\n"
            f"   why: {r.rationale}\n"
            f"   not-yet: {r.when_not_to_install}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Automation ROI Analyzer")
    ap.add_argument("--path", default=".")
    args = ap.parse_args(argv)
    print(render(analyze_path(args.path)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
