"""CDIO rendered-page checks -- CANDIDATE, warning-only (never blocks, no hook).

Origin: Bodeguita El Puerto V3 (docs/specs/v3-mesa-viva.md, Owner decision 3, 2026-11-22).
The V2 page passed every structural gate (axe, contrast, schema) and still looked flat and
repetitive: the same plate engraving drawn three times, rows of small isolated pictograms,
neighbouring bands with the same shape. None of that is visible in source; it is visible in
the rendered DOM. This module judges facts collected by rendered_probe.js in a real browser.

Checks (each returns findings with criterion + observed value; severity is always "warning"):
  motif-repetition   the same image file at the same crop drawn more than once on a page
  pictogram-density  many small isolated SVG pictograms (the V1/V2 "flat icons" failure)
  section-monotony   neighbouring sections with the same ground, column count and media
  art-provenance     pictures without a declared kind -- ONLY when the page uses the
                     data-art-kind convention; otherwise the state is "not_declared",
                     which is a different fact from "measured, clean"

CLI:  python -m modules.cdio.rendered_checks <url-or-dist-dir> [...] [--width 1440] [--json]
"""
from __future__ import annotations

import argparse
import functools
import http.server
import json
import os
import socketserver
import sys
import threading
from collections import Counter
from dataclasses import asdict, dataclass, field

PROBE_JS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rendered_probe.js")

SEVERITY = "warning"            # candidate status: nothing here may block a ship
MOTIF_MIN_PX = 32               # smaller images are icons, not motifs
PICTOGRAM_MAX_PX = 96           # an SVG image rendered at or under this is a pictogram
PICTOGRAM_LIMIT = 4             # this many on one page reads as an icon grid
SECTION_MIN_HEIGHT = 120        # thin dividers (borders, banners) are not layout sections
DARK_BELOW = 0.2
LIGHT_FROM = 0.8

STATE_MEASURED = "measured"
STATE_NOT_DECLARED = "not_declared"   # page does not use the provenance convention
STATE_NOTHING = "nothing_to_measure"  # e.g. no art at all on the page


@dataclass(frozen=True)
class Finding:
    check: str
    criterion: str
    observed: str
    severity: str = SEVERITY


@dataclass
class RenderedReport:
    url: str
    viewport: int
    findings: list[Finding] = field(default_factory=list)
    states: dict[str, str] = field(default_factory=dict)
    blocking: bool = False      # candidate: always False, by contract

    def to_dict(self) -> dict:
        return {**asdict(self), "findings": [asdict(f) for f in self.findings]}


def check_motif_repetition(art: list[dict]) -> tuple[str, list[Finding]]:
    motifs = [a for a in art if max(a.get("w", 0), a.get("h", 0)) >= MOTIF_MIN_PX]
    if not motifs:
        return STATE_NOTHING, []
    counts = Counter((a["file"], a.get("position", "")) for a in motifs)
    return STATE_MEASURED, [
        Finding("motif-repetition", "a motif (file + crop) is drawn at most once per page",
                f"{file} at {pos} drawn {n} times")
        for (file, pos), n in sorted(counts.items()) if n > 1
    ]


def check_pictogram_density(art: list[dict]) -> tuple[str, list[Finding]]:
    picto = [a for a in art if a.get("svg") and 0 < max(a.get("w", 0), a.get("h", 0)) <= PICTOGRAM_MAX_PX]
    if len(picto) < PICTOGRAM_LIMIT:
        return STATE_MEASURED, []
    files = sorted({a["file"] for a in picto})
    return STATE_MEASURED, [Finding(
        "pictogram-density", f"fewer than {PICTOGRAM_LIMIT} isolated SVG pictograms <= {PICTOGRAM_MAX_PX}px per page",
        f"{len(picto)} pictograms ({', '.join(files[:6])}{'...' if len(files) > 6 else ''})")]


def _bucket(lum: float) -> str:
    return "dark" if lum < DARK_BELOW else "light" if lum >= LIGHT_FROM else "mid"


def check_section_monotony(sections: list[dict]) -> tuple[str, list[Finding]]:
    """Neighbouring sections that SHOW MEDIA must not repeat the same shape.

    Scope set by the first transfer run (2026-11-22): judging every pair flagged a deliberately
    single-ground, text-led portfolio five times, while the defect this check exists for is media
    bands repeating one layout (Bodeguita V2: picture + text, twice). A run of text-only sections
    is prose flow, not monotony, so text-only pairs are counted in the state but not judged.
    """
    real = [s for s in sections if s.get("height", 0) >= SECTION_MIN_HEIGHT]
    if len(real) < 2:
        return STATE_NOTHING, []
    sig = [(_bucket(s["luminance"]), s["cols"], bool(s["media"])) for s in real]
    findings, text_pairs = [], 0
    for prev, cur, a, b in zip(real, real[1:], sig, sig[1:]):
        if not (a[2] or b[2]):
            text_pairs += 1
            continue
        if a == b:
            findings.append(Finding(
                "section-monotony", "neighbouring media sections differ in ground, columns or media",
                f"{prev['label']} ~ {cur['label']}: both {a[0]} ground, {a[1]} column(s), media"))
    state = STATE_MEASURED if not text_pairs else f"{STATE_MEASURED}; {text_pairs} text-only pair(s) not judged"
    return state, findings


def check_art_provenance(art: list[dict], declares: bool) -> tuple[str, list[Finding]]:
    if not declares:
        return STATE_NOT_DECLARED, []
    missing = [a for a in art if not a.get("kind")]
    return STATE_MEASURED, [
        Finding("art-provenance", "every picture declares its provenance kind (data-art-kind)",
                f"{a['file']} ({a.get('w')}x{a.get('h')}px) has no data-art-kind")
        for a in missing
    ]


def evaluate(probe: dict) -> RenderedReport:
    """Judge one probe result. Pure: same probe -> same report."""
    report = RenderedReport(url=probe.get("url", ""), viewport=int(probe.get("viewport", 0)))
    art = probe.get("art", [])
    for name, (state, found) in (
        ("motif-repetition", check_motif_repetition(art)),
        ("pictogram-density", check_pictogram_density(art)),
        ("section-monotony", check_section_monotony(probe.get("sections", []))),
        ("art-provenance", check_art_provenance(art, bool(probe.get("declaresProvenance")))),
    ):
        report.states[name] = state
        report.findings.extend(found)
    return report


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args) -> None:  # noqa: D401 -- silence per-request access logs
        return


def _serve(directory: str) -> tuple[socketserver.TCPServer, str]:
    handler = functools.partial(_QuietHandler, directory=directory)
    server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}/"


def probe_pages(targets: list[str], width: int = 1440, height: int = 900) -> list[dict]:
    """Render each target (URL or built static directory) in Chromium and run the probe."""
    from playwright.sync_api import sync_playwright  # optional dependency, imported on use

    script = open(PROBE_JS, encoding="utf-8").read()
    servers, results = [], []
    try:
        urls = []
        for t in targets:
            directory, _, sub = t.partition("::")   # "<dist-dir>::/es/" probes a sub-path of a build
            if os.path.isdir(directory):
                server, url = _serve(directory)
                servers.append(server)
                urls.append(url + sub.lstrip("/"))
            else:
                urls.append(t)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": height})
            for url in urls:
                page.goto(url, wait_until="networkidle", timeout=60_000)
                # Off-screen lazy images never load, so their rendered size would read as 0.
                page.evaluate("() => Promise.all([...document.images].map(i => { i.loading = 'eager'; return i.decode().catch(() => null); }))")
                results.append(page.evaluate(script))
            browser.close()
    finally:
        for s in servers:
            s.shutdown()
    return results


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="CDIO rendered-page checks (candidate, warning-only)")
    ap.add_argument("targets", nargs="+", help="URLs, built static directories, or <dir>::<path>")
    ap.add_argument("--width", type=int, default=1440)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    reports = [evaluate(p) for p in probe_pages(args.targets, width=args.width)]
    if args.json:
        print(json.dumps([r.to_dict() for r in reports], indent=2, ensure_ascii=False))
    else:
        for r in reports:
            print(f"{r.url} @{r.viewport}: {len(r.findings)} warning(s)  states={r.states}")
            for f in r.findings:
                print(f"  [{f.severity}] {f.check}: {f.observed}")
    return 0  # warning-only by contract: never a failing exit code


if __name__ == "__main__":
    sys.exit(main())
