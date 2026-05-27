#!/usr/bin/env python3
"""UQF audit CLI -- score PP modules against the absorbed ECC baseline.

Usage:
  python tools/uqf_audit.py <path>
  python tools/uqf_audit.py <path> --domain prompts
  python tools/uqf_audit.py --scan-all
  python tools/uqf_audit.py <path> --anti-patterns
  python tools/uqf_audit.py <path> --json

Domains: code (default), prompts, docs, tests, workflows.

Score interpretation:
   >= 70%   OK     -- S+++ baseline met
   40-69%  WARN   -- has fix hints, not blocking
   < 40%   FAIL   -- significant gaps, prioritize

Source: ECC absorption baseline (vault/knowledge_base/
ecc-universal-baseline.md), MIT (c) 2026 Affaan Mustafa.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.uqf.auditor import UQFAuditor, AuditReport
from modules.uqf.anti_patterns import run_all as run_anti_patterns


def _status_tag(score: float) -> str:
    if score >= 70.0:
        return "OK"
    if score >= 40.0:
        return "WARN"
    return "FAIL"


def _summary_table(reports: dict[str, AuditReport]) -> str:
    """Render a multi-module ASCII table."""
    if not reports:
        return "(no modules audited)"
    rows = []
    for path, r in reports.items():
        top_issue = ""
        if r.failed:
            top_issue = f"failed: {r.failed[0]}"
        elif r.anti_pattern_hits:
            ap = next(iter(r.anti_pattern_hits.keys()))
            n = len(r.anti_pattern_hits[ap])
            top_issue = f"{ap} x{n}"
        else:
            top_issue = "-"
        rows.append([
            path,
            f"{r.score_pct:.1f}%",
            _status_tag(r.score_pct),
            top_issue[:60],
        ])

    headers = ["MODULE", "SCORE", "STATUS", "TOP ISSUE"]
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    sep = "  "
    out = []
    out.append(sep.join(h.ljust(widths[i]) for i, h in enumerate(headers)))
    out.append(sep.join("-" * widths[i] for i in range(len(headers))))
    for row in rows:
        out.append(sep.join(
            str(cell).ljust(widths[i]) for i, cell in enumerate(row)
        ))
    return "\n".join(out)


def _detail_report(report: AuditReport) -> str:
    """Render a single-target detailed report (human-readable)."""
    lines = []
    lines.append(f"{'=' * 72}")
    lines.append(f"UQF audit: {report.target}")
    lines.append(f"  domain: {report.domain}")
    lines.append(f"  score:  {report.score_pct:.1f}%  "
                 f"[{_status_tag(report.score_pct)}]")
    lines.append(f"  timestamp: {report.timestamp_iso}")
    lines.append(f"{'-' * 72}")

    lines.append(f"PASSED ({len(report.passed)}):")
    for p in report.passed:
        lines.append(f"  [+] {p}")

    lines.append(f"FAILED ({len(report.failed)}):")
    for p in report.failed:
        lines.append(f"  [-] {p}")

    if report.anti_pattern_hits:
        lines.append("ANTI-PATTERN HITS:")
        for det, hits in report.anti_pattern_hits.items():
            lines.append(f"  {det} ({len(hits)} hit(s)):")
            for h in hits[:5]:
                lines.append(f"    line {h.get('line')}: "
                             f"{h.get('snippet')!r}")
            if len(hits) > 5:
                lines.append(f"    ... and {len(hits) - 5} more")

    if report.fix_hints:
        lines.append("FIX HINTS (top 5):")
        for h in report.fix_hints[:5]:
            lines.append(f"  - {h}")

    if report.source_attributions:
        lines.append("SOURCE ATTRIBUTIONS:")
        for s in report.source_attributions:
            lines.append(f"  - {s}")

    lines.append("=" * 72)
    return "\n".join(lines)


def cmd_anti_patterns(path: str) -> int:
    """Run anti-pattern detectors and print results, ignore principles."""
    p = Path(path)
    if not p.is_file():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1
    code = p.read_text(encoding="utf-8", errors="replace")
    hits = run_anti_patterns(code)
    any_hit = False
    for det, hit_list in hits.items():
        if not hit_list:
            continue
        any_hit = True
        print(f"{det}: {len(hit_list)} hit(s)")
        for h in hit_list:
            print(f"  line {h.line}: {h.snippet}")
            print(f"    fix: {h.fix}")
    if not any_hit:
        print(f"No anti-patterns detected in {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?",
                    help="file path to audit (omit with --scan-all)")
    ap.add_argument("--domain", default="code",
                    choices=("code", "prompts", "docs", "tests",
                             "workflows"))
    ap.add_argument("--scan-all", action="store_true",
                    help="audit the default PP module set")
    ap.add_argument("--anti-patterns", action="store_true",
                    help="only run anti-pattern detectors")
    ap.add_argument("--json", action="store_true",
                    help="emit JSON instead of human-readable text")
    args = ap.parse_args(argv)

    if args.scan_all:
        auditor = UQFAuditor()
        reports = auditor.scan_all()
        if args.json:
            print(json.dumps(
                {path: {
                    "score_pct": r.score_pct,
                    "passed": r.passed,
                    "failed": r.failed,
                    "fix_hints": r.fix_hints[:5],
                    "anti_pattern_hits": list(r.anti_pattern_hits.keys()),
                } for path, r in reports.items()},
                indent=2,
            ))
        else:
            print(_summary_table(reports))
        return 0

    if not args.path:
        ap.print_help()
        return 2

    if args.anti_patterns:
        return cmd_anti_patterns(args.path)

    auditor = UQFAuditor()
    if args.domain == "prompts":
        p = Path(args.path)
        if not p.is_file():
            print(f"error: file not found: {args.path}", file=sys.stderr)
            return 1
        content = p.read_text(encoding="utf-8", errors="replace")
        report = auditor.audit_prompt(content, target_label=str(p))
    else:
        report = auditor.audit_file(args.path, domain=args.domain)

    if args.json:
        print(json.dumps({
            "target": report.target,
            "domain": report.domain,
            "score_pct": report.score_pct,
            "passed": report.passed,
            "failed": report.failed,
            "fix_hints": report.fix_hints,
            "anti_pattern_hits": {
                k: [{"line": h["line"], "snippet": h["snippet"]}
                    for h in v]
                for k, v in report.anti_pattern_hits.items()
            },
            "source_attributions": report.source_attributions,
            "timestamp_iso": report.timestamp_iso,
        }, indent=2))
    else:
        print(_detail_report(report))
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    raise SystemExit(main())
