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


# Render facts (V-DSR-RENDER-FACTS, 2026-11-22): what the browser itself observed while rendering, so a defect a
# machine can see never depends on the reviewer noticing it in a PNG. Six reviewer "pass" verdicts used to APPROVE a
# page whose images were broken. Images under DUP_MIN_PX wide (icons, logos in a list) do not count as repeats.
FACTS_VERSION = 1
DUP_MIN_PX = 120
OVERFLOW_TOLERANCE_PX = 1
FACTS_JS = """() => {
  const imgs = [...document.images];
  const src = i => i.currentSrc || i.src || '';
  const broken = imgs.filter(i => src(i) && i.complete && i.naturalWidth === 0).map(src);
  const counts = {};
  imgs.filter(i => src(i) && i.naturalWidth > 0 && i.width >= %d).forEach(i => { counts[src(i)] = (counts[src(i)] || 0) + 1; });
  const dup = Object.entries(counts).filter(([s, n]) => n > 1).map(([s, n]) => s + ' x' + n);
  const dead = [...document.querySelectorAll('a')].filter(a => {
    if (a.hasAttribute('onclick') || !(a.textContent || '').trim()) return false;
    const h = (a.getAttribute('href') ?? '').trim();
    return h === '' || h === '#' || /^javascript:/i.test(h);
  }).map(a => (a.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 60));
  const de = document.documentElement;
  return {broken_images: broken, duplicate_images: dup, dead_links: dead,
          overflow_px: Math.max(0, de.scrollWidth - window.innerWidth), viewport_px: window.innerWidth};
}""" % DUP_MIN_PX
_IGNORED_URL = re.compile(r"/favicon\.ico(?:$|\?)", re.I)


def counts_as_failed(url: str, failure: str | None) -> bool:
    """A request the PAGE cancelled is not a failed asset: Next.js aborts its own route prefetches (`?_rsc=`,
    net::ERR_ABORTED). Found on the first live run (portfolio, 2026-11-22), which a fixture could never show."""
    if _IGNORED_URL.search(url or ""):
        return False
    return "ERR_ABORTED" not in (failure or "")


def _observe(page, uri: str) -> dict:
    """Load `uri` in `page` and return what the browser saw. Listeners attach BEFORE navigation."""
    failed, errors = [], []
    page.on("requestfailed", lambda r: failed.append("%s (%s)" % (r.url, r.failure or "failed"))
            if counts_as_failed(r.url, r.failure) else None)
    page.on("response", lambda r: failed.append("%s (HTTP %d)" % (r.url, r.status)) if r.status >= 400 else None)
    # "Failed to load resource" is the console echo of a failed request, already counted above
    page.on("console", lambda m: errors.append(m.text) if m.type == "error"
            and not m.text.startswith("Failed to load resource") else None)
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    page.goto(uri, wait_until="load")
    try:
        page.wait_for_load_state("networkidle", timeout=5000)
    except Exception:  # noqa: BLE001 -- a page that never goes idle is still observed as it stands
        pass
    seen = page.evaluate(FACTS_JS)
    seen["failed_requests"] = [u for u in failed if not _IGNORED_URL.search(u.split(" (")[0])][:20]
    seen["console_errors"] = errors[:20]
    return seen


def facts_verdicts(facts: dict) -> list:
    """Render facts -> scorer verdicts. Pure; every criterion is emitted (pass or fail) so the record shows it ran."""
    from modules.cdio import scorer
    vps = (facts or {}).get("viewports") or {}

    def union(key: str) -> list:
        out = []
        for name in vps:
            for item in vps[name].get(key) or []:
                if item not in out:
                    out.append(item)
        return out

    def v(criterion, dimension, severity, items, what, fix):
        if not items:
            return scorer.Verdict(criterion=criterion, dimension=dimension, status="pass", observed="none observed")
        shown = "; ".join(str(i)[:120] for i in items[:5]) + ("; +%d more" % (len(items) - 5) if len(items) > 5 else "")
        return scorer.Verdict(criterion=criterion, dimension=dimension, status="fail", severity=severity,
                              observed="%d %s: %s" % (len(items), what, shown), recommendation=fix)

    overflow = ["%s: %dpx wider than its %dpx viewport" % (n, x["overflow_px"], x.get("viewport_px", 0))
                for n, x in vps.items() if (x.get("overflow_px") or 0) > OVERFLOW_TOLERANCE_PX]
    return [
        v("RENDER-BROKEN-IMAGE", "visual", "critical", union("broken_images"), "image(s) rendered broken",
          "fix the path or ship the asset; a broken image is visible to every visitor"),
        v("RENDER-ASSET-FAILED", "ux", "major", union("failed_requests"), "request(s) failed",
          "every stylesheet, script, font and image the page asks for must load"),
        v("RENDER-CONSOLE-ERROR", "ux", "major", union("console_errors"), "console/page error(s)",
          "an uncaught error usually means a broken interaction"),
        v("RENDER-DEAD-LINK", "conversion", "major", union("dead_links"), "link(s) going nowhere (href '#', empty or javascript:)",
          "point every link at a real destination or make it a button with a handler"),
        v("RENDER-HORIZONTAL-OVERFLOW", "ux", "major", overflow, "viewport(s) scroll sideways",
          "find the element wider than the viewport (fixed widths, long words, 100vw plus a scrollbar)"),
        v("RENDER-DUPLICATE-IMAGE", "visual", "minor", union("duplicate_images"), "large image(s) shown more than once",
          "a repeated photo reads as a template; use a different asset or drop the repeat"),
    ]


def _facts_for(c: str, h: str) -> dict | None:
    """The facts of the latest render of these exact bytes, or None when that render collected none."""
    last = None
    for r in dr.read_rows("renders.jsonl"):
        if r.get("file") == c and r.get("sha") == h and r.get("pngs"):
            last = r
    facts = (last or {}).get("facts")
    return facts if isinstance(facts, dict) and facts.get("collected") is True else None


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
                pngs, facts = [], {"collected": True, "version": FACTS_VERSION, "viewports": {}}
                for name, (w, hgt) in VIEWPORTS.items():
                    page = browser.new_page(viewport={"width": w, "height": hgt})
                    facts["viewports"][name] = _observe(page, Path(c).as_uri())
                    png = out_dir / ("%s-%s.png" % (h[:16], name))
                    page.screenshot(path=str(png), full_page=True)
                    page.close()
                    pngs.append(str(png))
                dr.append_row("renders.jsonl", {"file": c, "sha": h, "pngs": pngs, "facts": facts})
                print("RENDERED %s -> %s" % (f, " ".join(pngs)))
                for vd in facts_verdicts(facts):
                    if vd.status == "fail":
                        print("  DEFECT %s [%s] %s" % (vd.criterion, vd.severity, vd.observed))
        finally:
            browser.close()
    print("Look at every PNG (Read tool) before writing verdicts: the review judges what renders, not the source.")
    print("DEFECT lines are folded into the record as verdicts; a reviewer pass cannot override them.")
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


LEGAL_FLOOR = ("legal-page-present", "legal-fields-filled", "legal-page-linked")
_TREE_SKIP = {".git", ".claude", ".review", "node_modules", "__pycache__"}


def is_single_page(files: list) -> bool:
    """Every file sits in one directory tree that holds exactly one html page and no package.json: a page, not a site.
    Its legal floor is held by the publish gate (spec cdio-10-publish-gate.md), not by the design review."""
    try:
        root = os.path.commonpath([os.path.dirname(dr.canon(f)) for f in files])
    except ValueError:
        return False
    html = 0
    for dirpath, dirnames, names in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _TREE_SKIP]
        if "package.json" in names:
            return False
        html += sum(1 for n in names if n.lower().endswith(dr.HTML_EXT))
        if html > 1:
            return False
    return html == 1


def record(verdicts_path: str, files: list, screenshot: str | None = None, experience: str | None = None) -> dict:
    from modules.cdio import scorer, taste
    raw = json.loads(Path(verdicts_path).read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise SystemExit("verdicts must be a JSON list of verdict objects")
    fields = ("criterion", "dimension", "status", "severity", "observed", "recommendation")
    mine = [scorer.Verdict(**{k: str(d.get(k, "")) for k in fields}) for d in raw if isinstance(d, dict)]
    demoted = []
    floor = lambda v: v.criterion in LEGAL_FLOOR and v.status == "fail" and v.severity == "critical"  # noqa: E731
    if files and any(floor(v) for v in mine) and is_single_page(files):
        import dataclasses
        demoted = [v.criterion for v in mine if floor(v)]
        mine = [dataclasses.replace(v, severity="major") if floor(v) else v for v in mine]
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
            else:
                facts = _facts_for(c, h)
                if facts is None:   # absent is not clean: a render without facts proves nothing about the page
                    refusals.append("%s: rendered without runtime facts (run `render` again)" % os.path.basename(c))
                else:
                    folded += facts_verdicts(facts)
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
           "failed": [[v.criterion, v.severity, str(v.observed)[:140]] for v in folded if v.status == "fail"],
           # single page: CDIO-10 legal criticals recorded as major; tools/legal_deploy_gate.py holds them at publish
           "legal_demoted": demoted}
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
