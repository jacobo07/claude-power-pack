#!/usr/bin/env python3
"""classify_sources.py — measure Engine 2's classifier against real URLs.

WHY THIS EXISTS
---------------
The 2026-08-18 live run classified 14 of 19 fetched pages as UNKNOWN. That
number is the honest output of a classifier calibrated for refusal-correctness
first, but it is not actionable on its own: a run reports "UNKNOWN x14" and
nobody can say WHICH hosts those were, or WHICH rule came closest to firing.
Without that, the only available move is to guess at thresholds — and a
threshold moved by guess is how a gate that refuses too much becomes a gate that
laundres marketing.

This tool fetches a list of URLs, runs the real classifier over them, and prints
what each page scored on every channel. It changes nothing. It is the
measurement that has to precede any calibration change.

Usage:
  python classify_sources.py --report <path-to-run-report.md>
  python classify_sources.py --url https://a.example --url https://b.example
  python classify_sources.py --report <path> --json    # machine-readable

Exit 0 always: this is an instrument, not a gate. A failed fetch is reported as
a row, never as a crash — an unreachable page is data about the landscape too.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_MODULE_DIR = str(Path(__file__).resolve().parent)
if _MODULE_DIR not in sys.path:
    sys.path.insert(0, _MODULE_DIR)

from deep_research import LayerError, fetch_page, html_to_markdown  # noqa: E402
from research_engines import (  # noqa: E402
    FAMILY_UNKNOWN,
    _count_measurables,
    _hits,
    _MEASUREMENT_SIGNALS,
    _PRACTITIONER_TEXT_SIGNALS,
    _VENDOR_TEXT_SIGNALS,
    _ACADEMIC_TEXT_SIGNALS,
    classify_source,
    landscape_verdict,
    propagate_vendor_hosts,
)

# Sources are listed in the report as "- <https://...>" under ## Sources.
_SOURCE_RE = re.compile(r"^-\s*<(https?://[^>]+)>\s*$", re.MULTILINE)


def urls_from_report(path: Path) -> list[str]:
    """Pull the Sources block out of a run report. Empty list if absent."""
    try:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError as e:
        print(f"cannot read {path}: {e}", file=sys.stderr)
        return []
    start = text.find("## Sources")
    if start < 0:
        return []
    end = text.find("\n## ", start + 1)
    block = text[start:end if end > 0 else len(text)]
    return list(dict.fromkeys(_SOURCE_RE.findall(block)))


def near_misses(text: str) -> dict[str, int]:
    """How close each channel came to firing.

    A classifier is tuned by looking at what ALMOST matched, not at what did.
    A page with 1 measurement marker and 2 quantities missed family A by one
    quantity; a page with 0 of everything is genuinely unrecognisable, and the
    two need completely different fixes.
    """
    return {
        "academic_markers": _hits(text, _ACADEMIC_TEXT_SIGNALS),
        "measurement_markers": _hits(text, _MEASUREMENT_SIGNALS),
        "measurables": _count_measurables(text),
        "practitioner_markers": _hits(text, _PRACTITIONER_TEXT_SIGNALS),
        "vendor_phrases": _hits(text, _VENDOR_TEXT_SIGNALS),
    }


def classify_url(url: str) -> dict:
    """Fetch + classify one URL. A fetch failure is a row, never an exception."""
    try:
        page = fetch_page(url)
    except LayerError as e:
        return {"url": url, "family": "FETCH_FAILED", "quality": "-",
                "signals": [str(e)[:120]], "near": {}, "chars": 0}
    md, _layer = html_to_markdown(
        page["html"], base_url=page.get("final_url", url)
    )
    final = page.get("final_url", url)
    cls = classify_source(final, "", "", md)
    cls["near"] = near_misses(f"{md[:6000]}")
    cls["chars"] = len(md)
    return cls


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Measure Engine 2's source classifier against real URLs.")
    ap.add_argument("--report", type=Path,
                    help="run report whose ## Sources block supplies the URLs")
    ap.add_argument("--url", action="append", default=[],
                    help="classify this URL (repeatable)")
    ap.add_argument("--json", action="store_true",
                    help="emit JSON instead of the table")
    args = ap.parse_args(argv)

    urls = list(args.url)
    if args.report:
        urls.extend(u for u in urls_from_report(args.report) if u not in urls)
    if not urls:
        ap.error("no URLs — pass --report and/or --url")

    rows = [classify_url(u) for u in urls]
    # Same host-level pass the live driver runs, or the instrument would report
    # a landscape the pipeline never sees.
    rows = propagate_vendor_hosts(rows)

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0

    print(f"\nclassify_sources — {len(rows)} URL(s)\n")
    for r in rows:
        n = r.get("near") or {}
        print(f"  {r['family']:<16} {r['quality']:<7} {r.get('host') or r['url'][:60]}")
        if n:
            print(f"      near: acad={n['academic_markers']} "
                  f"meas={n['measurement_markers']}/{n['measurables']}q "
                  f"prac={n['practitioner_markers']} "
                  f"vend={n['vendor_phrases']}  ({r['chars']} chars)")
        for s in (r.get("signals") or [])[:3]:
            print(f"      · {s}")

    counts: dict[str, int] = {}
    for r in rows:
        counts[r["family"]] = counts.get(r["family"], 0) + 1
    print("\n  families: " + ", ".join(
        f"{k}×{v}" for k, v in sorted(counts.items())))

    ok = [r for r in rows if r["family"] != "FETCH_FAILED"]
    print("  landscape: " + landscape_verdict(ok)["verdict"])

    unknown = [r for r in ok if r["family"] == FAMILY_UNKNOWN]
    if unknown:
        # The distinction that decides the fix: a page that missed a rule by one
        # signal needs a threshold moved; a page that matched nothing at all
        # needs a rule that does not exist yet.
        one_away = [r for r in unknown
                    if max((r["near"] or {}).values(), default=0) >= 1]
        print(f"  UNKNOWN: {len(unknown)} — {len(one_away)} scored on at least "
              f"one channel, {len(unknown) - len(one_away)} matched nothing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
