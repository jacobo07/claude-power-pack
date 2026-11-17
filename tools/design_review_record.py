#!/usr/bin/env python3
"""Recorder for cdio-reviewer: binds a review verdict to the exact bytes it judged (spec design-surface-router.md).

  render <file.html>...                      headless Chromium, desktop 1440x900 + phone 390x844, full page PNGs;
                                             one renders.jsonl row per file {file, sha, pngs}
  record --verdicts v.json --files f... [--screenshot shot.png]
                                             v.json = [{criterion, dimension, status, severity, observed, recommendation}]
                                             folds the Taste lint of every HTML file in, runs scorer.review_gate, and
                                             appends one reviews.jsonl row {files:{path: sha256}, verdict, score, is_done}

An APPROVE is recorded as done only when the review is not empty (>= MIN_VERDICTS reviewer verdicts over >= 2
dimensions) and every file was rendered for these bytes (HTML: a `render` row; other files: --screenshot, a PNG newer
than the file). Otherwise the row is still written, is_done False, with the refusal named. Exit 0 = is_done.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[1]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.cdio import design_route as dr  # noqa: E402

MIN_VERDICTS = 6
MIN_DIMENSIONS = 2
VIEWPORTS = {"desktop": (1440, 900), "phone": (390, 844)}
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _launch(pw):
    """Playwright's own Chromium first; else an installed Chrome or Edge (Edge ships with Windows 11), so a host that
    never ran `playwright install chromium` can still render. Raises with every attempt named if none starts."""
    errors = []
    for channel in (None, "chrome", "msedge"):
        try:
            return pw.chromium.launch(channel=channel) if channel else pw.chromium.launch()
        except Exception as exc:  # noqa: BLE001 -- try the next engine, report all if none works
            errors.append("%s: %s" % (channel or "playwright-chromium", str(exc).splitlines()[0][:160]))
    raise RuntimeError("no Chromium-family browser could start: " + " | ".join(errors))


def render(files: list) -> int:
    from playwright.sync_api import sync_playwright
    out_dir = dr.state_dir() / "renders"
    out_dir.mkdir(exist_ok=True)
    rc = 0
    with sync_playwright() as pw:
        browser = _launch(pw)
        try:
            for f in files:
                if not f.lower().endswith(dr.HTML_EXT) or not os.path.isfile(f):
                    print("SKIP %s: not an HTML file on disk (use --screenshot for app surfaces)" % f)
                    rc = 1
                    continue
                c, h = dr.canon(f), dr.sha256(f)
                pngs = []
                for name, (w, hgt) in VIEWPORTS.items():
                    page = browser.new_page(viewport={"width": w, "height": hgt})
                    page.goto(Path(c).as_uri(), wait_until="load")
                    png = out_dir / ("%s-%s.png" % (h[:16], name))
                    page.screenshot(path=str(png), full_page=True)
                    page.close()
                    pngs.append(str(png))
                dr.append_row("renders.jsonl", {"file": c, "sha": h, "pngs": pngs})
                print("RENDERED %s -> %s" % (f, " ".join(pngs)))
        finally:
            browser.close()
    print("Look at every PNG (Read tool) before writing verdicts: the review judges what renders, not the source.")
    return rc


MIN_SHOT_PX = 300


def _is_png(p: str) -> bool:
    """A real screenshot: PNG signature AND an IHDR of at least MIN_SHOT_PX on both sides (8 magic bytes alone were
    satisfiable by any stub file; review of a9db1d43, F3)."""
    try:
        with open(p, "rb") as fh:
            head = fh.read(24)
    except OSError:
        return False
    if len(head) < 24 or head[:8] != PNG_MAGIC or head[12:16] != b"IHDR":
        return False
    w, h = int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")
    return w >= MIN_SHOT_PX and h >= MIN_SHOT_PX


_REF = re.compile(r"""(?:href|src)\s*=\s*["']([^"':#?]+\.(?:css|js|mjs))["']""", re.I)


def _covered_by_render(files: list) -> set:
    """Stylesheets/scripts that a page IN THIS RECORD links, when that page was rendered for its current bytes AFTER
    the asset last changed: the page's render already shows them. Measured 2026-11-17 (GEX44 clinic run): the reviewer
    was refused for styles.css and app.js, the two files its own rendered index.html loads."""
    renders = {}
    for r in dr.read_rows("renders.jsonl"):
        if r.get("file") and r.get("sha") and r.get("pngs"):
            k = (r["file"], r["sha"])
            renders[k] = max(renders.get(k, 0), float(r.get("ts") or 0))
    out = set()
    for page in files:
        if not page.endswith(dr.HTML_EXT) or not os.path.isfile(page):
            continue
        when = renders.get((page, dr.sha256(page)))
        if not when:
            continue
        html = Path(page).read_text(encoding="utf-8", errors="replace")
        for ref in _REF.findall(html):
            asset = dr.canon(os.path.join(os.path.dirname(page), ref))
            if asset in files and os.path.isfile(asset) and os.path.getmtime(asset) <= when:
                out.add(asset)
    return out


def record(verdicts_path: str, files: list, screenshot: str | None = None, experience: str | None = None) -> dict:
    from modules.cdio import scorer, taste
    raw = json.loads(Path(verdicts_path).read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise SystemExit("verdicts must be a JSON list of verdict objects")
    fields = ("criterion", "dimension", "status", "severity", "observed", "recommendation")
    mine = [scorer.Verdict(**{k: str(d.get(k, "")) for k in fields}) for d in raw if isinstance(d, dict)]
    refusals = []
    dims = {v.dimension for v in mine if v.is_valid()}
    if sum(1 for v in mine if v.is_valid()) < MIN_VERDICTS or len(dims) < MIN_DIMENSIONS:
        refusals.append("thin review: %d valid reviewer verdicts over %d dimensions (need >= %d over >= %d)"
                        % (sum(1 for v in mine if v.is_valid()), len(dims), MIN_VERDICTS, MIN_DIMENSIONS))
    folded, hashes = list(mine), {}
    seen = dr.rendered()
    for f in files:
        if not os.path.isfile(f):
            raise SystemExit("not a file: %s" % f)
    covered = _covered_by_render([dr.canon(f) for f in files])
    for f in files:
        c, h = dr.canon(f), dr.sha256(f)
        hashes[c] = h
        if c.endswith(dr.HTML_EXT):
            folded += taste.lint(c).verdicts
            if h not in seen.get(c, set()):
                refusals.append("%s: never rendered for these bytes (run `render` first)" % os.path.basename(c))
        elif c in covered:
            continue
        elif not (screenshot and _is_png(screenshot) and os.path.getmtime(screenshot) >= os.path.getmtime(c)):
            refusals.append("%s: no --screenshot PNG newer than the file, and no rendered page in this record links "
                            "it" % os.path.basename(c))
    exp = json.loads(Path(experience).read_text(encoding="utf-8")) if experience else {}
    g = scorer.review_gate(folded, declared_experience=exp.get("declared"), observed_experience=exp.get("observed"))
    row = {"files": hashes, "verdict": g.verdict, "score": g.score, "reason": g.reason,
           "is_done": bool(g.is_done and not refusals), "refused": refusals,
           "experience": "assessed" if exp else "unassessed",
           "reviewer_verdicts": len(mine), "folded_taste": len(folded) - len(mine),
           "critical": [v.criterion for v in folded if v.status == "fail" and v.severity == "critical"],
           # what failed, so the Stop gate can tell the agent what to fix (GEX44 SaaS rerun: "BLOCK 0" alone left two
           # fixable majors open through three re-blocks)
           "failed": [[v.criterion, v.severity, str(v.observed)[:140]] for v in folded if v.status == "fail"]}
    dr.append_row("reviews.jsonl", row)
    return row


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="design_review_record")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render")
    r.add_argument("files", nargs="+")
    rec = sub.add_parser("record")
    rec.add_argument("--verdicts", required=True)
    rec.add_argument("--files", nargs="+", required=True)
    rec.add_argument("--screenshot")
    rec.add_argument("--experience", help="JSON {declared, observed}: the CDIO-07 contract, so a breach withholds done")
    a = ap.parse_args(argv)
    if a.cmd == "render":
        return render(a.files)
    row = record(a.verdicts, a.files, a.screenshot, a.experience)
    print(json.dumps(row, indent=1, ensure_ascii=False))
    return 0 if row["is_done"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
