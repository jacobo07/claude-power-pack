#!/usr/bin/env python3
"""Recorder for cdio-reviewer: binds a review verdict to the exact bytes it judged (spec design-surface-router.md).

  render <file.html>...                      headless Chromium, desktop 1440x900 + phone 390x844, full page PNGs;
                                             one renders.jsonl row per file {file, sha, pngs}
  render-url --url http://host/route --files src...
                                             app surfaces: renders the RUNNING route at desktop/tablet/phone with the
                                             same runtime facts (+ HTTP status) and binds them to every listed file
  record --verdicts v.json --files f... [--screenshot shot.png (accepted, no longer proof)]
                                             v.json = [{criterion, dimension, status, severity, observed, recommendation}]
                                             folds the Taste lint of every HTML file in, runs scorer.review_gate, and
                                             appends one reviews.jsonl row {files:{path: sha256}, verdict, score, is_done}

An APPROVE is recorded as done only when the review is not empty (>= MIN_VERDICTS reviewer verdicts over >= 2
dimensions) and every file was rendered for these bytes (HTML: a `render` row; css/js an HTML page in the record links:
that page's render; app source: a `render-url` row). Otherwise the row is still written, is_done False, with the
refusal named. Exit 0 = is_done.
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
FACTS_VERSION = 3   # 2: dead_links lists links to missing local files (B-1); 3: accessibility + page weight (gates 6, 7)
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
  const local = [...document.querySelectorAll('a[href]')].filter(a => a.protocol === 'file:' && (a.textContent || '').trim())
    .map(a => [(a.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 60), a.href]);
  const de = document.documentElement;
  // v3 (tranche 3, gates 6 and 7): accessibility and weight facts a browser can observe without judgement
  const vis = el => el.checkVisibility ? el.checkVisibility({checkVisibilityCSS: true}) : !!el.offsetParent;
  const txt = s => (s || '').trim().replace(/\\s+/g, ' ');
  const byIds = el => (el.getAttribute('aria-labelledby') || '').split(/\\s+/)
      .some(id => id && txt((document.getElementById(id) || {}).textContent));
  const named = el => !!(txt(el.getAttribute('aria-label')) || txt(el.getAttribute('title')) || byIds(el)
      || txt(el.textContent) || [...el.querySelectorAll('img[alt]')].some(i => txt(i.getAttribute('alt'))));
  const decorative = el => el.getAttribute('aria-hidden') === 'true' || /^(presentation|none)$/.test(el.getAttribute('role') || '');
  const no_alt = imgs.filter(i => vis(i) && !i.hasAttribute('alt') && !decorative(i)).map(src);
  const nameless = [...document.querySelectorAll('a[href],button,[role="button"]')].filter(e => vis(e) && !named(e))
      .map(e => e.tagName.toLowerCase() + ' ' + (e.getAttribute('href') || e.id || e.className || '').toString().slice(0, 60));
  // A field needs a label, aria-label/labelledby or title. Hint text alone does not count: it vanishes on input.
  const unlabelled = [...document.querySelectorAll('input,select,textarea')].filter(e => vis(e)
      && !/^(hidden|submit|button|image|reset)$/i.test(e.type || '')
      && !(e.labels && [...e.labels].some(l => txt(l.textContent))) && !txt(e.getAttribute('aria-label'))
      && !txt(e.getAttribute('title')) && !byIds(e))
      .map(e => String(e.name || e.id || e.type || e.tagName).slice(0, 40));
  const vpm = document.querySelector('meta[name="viewport"]');
  const vpc = vpm ? (vpm.getAttribute('content') || '').toLowerCase() : '';
  const maxs = vpc.match(/maximum-scale\\s*=\\s*([\\d.]+)/);
  const zoom_blocked = /user-scalable\\s*=\\s*(no|0)\\b/.test(vpc) || (!!maxs && parseFloat(maxs[1]) < 2);
  const oversized = imgs.filter(i => i.naturalWidth >= 1200 && i.width > 0
      && i.naturalWidth > 2.5 * i.width * window.devicePixelRatio)
      .map(i => src(i) + ' ' + i.naturalWidth + 'px shown at ' + i.width + 'px');
  const resources = performance.getEntriesByType('resource').map(e => [e.name, e.encodedBodySize || 0]);
  return {broken_images: broken, duplicate_images: dup, dead_links: dead, local_links: local,
          overflow_px: Math.max(0, de.scrollWidth - window.innerWidth), viewport_px: window.innerWidth,
          img_no_alt: no_alt, nameless_controls: nameless, unlabelled_fields: unlabelled,
          lang: de.getAttribute('lang') || '', zoom_blocked: zoom_blocked, oversized_images: oversized,
          resources: resources, doc_url: location.href};
}""" % DUP_MIN_PX
PAGE_WEIGHT_BUDGET = 2_000_000   # bytes; compressed bytes over HTTP, file size on a file:// render


def _weigh(seen: dict) -> dict:
    """Gate 7: page weight from what the browser loaded. A file:// resource is weighed on disk; an HTTP one by its
    encoded body. A resource the browser would not size (cross-origin without Timing-Allow-Origin reports 0) is
    COUNTED as unsized, never weighed as 0. The raw list is not kept in the facts."""
    from urllib.parse import urlsplit
    from urllib.request import url2pathname
    total, fonts, unsized, heavy, names = 0, 0, 0, [], set()
    for name, size in [[seen.pop("doc_url", ""), 0]] + (seen.pop("resources", None) or []):
        if not name or name in names or name.startswith(("data:", "blob:")):
            continue
        names.add(name)
        u = urlsplit(name)
        if u.scheme == "file":
            p = url2pathname(u.path)
            size = os.path.getsize(p) if os.path.isfile(p) else 0
        if not size:
            unsized += 1
            continue
        total += size
        if re.search(r"\.(woff2?|ttf|otf)$", u.path, re.I):
            fonts += size
        heavy.append((size, os.path.basename(u.path) or name[:60]))
    seen.update(page_bytes=total, font_bytes=fonts, unsized_resources=unsized,
                heaviest=["%s %d KB" % (n, s // 1024) for s, n in sorted(heavy, reverse=True)[:3]])
    return seen


def _missing_local_links(seen: dict) -> dict:
    """B-1 (benchmark 2026-11-22): on a file:// render a link to a local file that does not exist goes nowhere, but
    the browser never requests it, so no fact saw it (reports.html, servicios.html were caught only by a reviewer).
    Each file: link is checked on disk; a missing target joins dead_links. The raw list is not kept in the facts.
    Both render paths post-process FACTS_JS through here, so the page is weighed here too (_weigh, v3)."""
    from urllib.parse import urlsplit
    from urllib.request import url2pathname
    for text, href in seen.pop("local_links", None) or []:
        path = url2pathname(urlsplit(href).path)
        if path and not os.path.exists(path):
            entry = "%s -> %s (missing file)" % (text, os.path.basename(path.rstrip("\\/")) or path)
            if entry not in seen.setdefault("dead_links", []):
                seen["dead_links"].append(entry)
    return _weigh(seen)
_IGNORED_URL = re.compile(r"/favicon\.ico(?:$|\?)", re.I)

# One-file apps swap sibling screens by JS state (cross-sector benchmark 2026-11-22, B-8: the nurse app's onboarding
# 2-3 and its home screen were <section hidden>; the render showed screen 1 only and the APPROVE bound all of it).
# A screen is a section / [data-screen] / [role=tabpanel] with real content, hidden while a sibling screen is shown,
# under a visible parent, never inside a dialog (sheets and toasts are overlays, not screens). Each one is revealed
# ALONE (siblings hidden), captured and observed. A forced reveal, not a navigation: JS that runs on entry did not run.
MAX_SCREENS = 8
SCREEN_SEL = 'section, [data-screen], [role="tabpanel"]'
SCREENS_JS = """() => {
  const sel = %s;
  const vis = el => el.checkVisibility ? el.checkVisibility({checkOpacity: false, checkVisibilityCSS: true})
                                       : !!el.offsetParent;
  const real = el => !el.closest('[role="dialog"],[aria-modal="true"],dialog')
      && ((el.textContent || '').trim().length >= 40 || el.querySelector('button,a[href],input,select,textarea'));
  const groups = new Map();
  for (const el of document.querySelectorAll(sel)) {
    const p = el.parentElement;
    if (!p || !real(el) || !vis(p)) continue;
    if (!groups.has(p)) groups.set(p, []);
    groups.get(p).push(el);
  }
  const out = [];
  for (const kids of groups.values()) {
    if (kids.length < 2 || !kids.some(vis)) continue;
    for (const el of kids) {
      if (vis(el)) continue;
      el.setAttribute('data-cdio-screen', String(out.length));
      out.push(el.id || el.getAttribute('data-screen') || el.getAttribute('aria-label') || ('screen' + out.length));
    }
  }
  return out;
}""" % json.dumps(SCREEN_SEL)
REVEAL_JS = """(i) => {
  const t = document.querySelector('[data-cdio-screen="' + i + '"]');
  if (!t) return false;
  for (const s of t.parentElement.children)
    if (s !== t && s.matches(%s)) { s.hidden = true; s.style.setProperty('display', 'none', 'important'); }
  t.hidden = false;
  t.style.removeProperty('display');
  if (getComputedStyle(t).display === 'none') t.style.setProperty('display', 'block', 'important');
  window.scrollTo(0, 0);
  return t.checkVisibility ? t.checkVisibility() : !!t.offsetParent;
}""" % json.dumps(SCREEN_SEL)


def _render_screens(page, out_dir: Path, stem: str) -> tuple:
    """Reveal, capture and observe every hidden screen of the loaded page. -> (screens, unrendered labels)."""
    labels = page.evaluate(SCREENS_JS)
    screens, unrendered = [], [l for l in labels[MAX_SCREENS:]]
    for i, label in enumerate(labels[:MAX_SCREENS]):
        try:
            if not page.evaluate(REVEAL_JS, i):
                unrendered.append(label)
                continue
            page.wait_for_timeout(150)
            png = out_dir / ("%s-screen-%d.png" % (stem, i))
            page.screenshot(path=str(png), full_page=True)
            seen = _missing_local_links(page.evaluate(FACTS_JS))
        except Exception:  # noqa: BLE001 -- a screen the browser could not show is reported, never skipped silently
            unrendered.append(label)
            continue
        seen.update(label=str(label), png=str(png))
        screens.append(seen)
    return screens, [str(l) for l in unrendered]
MAX_SCROLL_STEPS = 60


def counts_as_failed(url: str, failure: str | None) -> bool:
    """A request the PAGE cancelled is not a failed asset: Next.js aborts its own route prefetches (`?_rsc=`,
    net::ERR_ABORTED). Found on the first live run (portfolio, 2026-11-22), which a fixture could never show."""
    if _IGNORED_URL.search(url or ""):
        return False
    return "ERR_ABORTED" not in (failure or "")


def _observe(page, uri: str) -> dict:
    """Load `uri` in `page` and return what the browser saw. Listeners attach BEFORE navigation."""
    failed, errors, loaded = [], [], []
    # Chromium keeps no resource timing for file:// loads (probe 2026-11-27: getEntriesByType('resource') == []), so
    # _weigh would see only the document. Playwright still reports each finished request; file ones are weighed on disk.
    page.on("requestfinished", lambda r: loaded.append([r.url, 0]) if r.url.startswith("file:") else None)
    page.on("requestfailed", lambda r: failed.append("%s (%s)" % (r.url, r.failure or "failed"))
            if counts_as_failed(r.url, r.failure) else None)
    page.on("response", lambda r: failed.append("%s (HTTP %d)" % (r.url, r.status)) if r.status >= 400 else None)
    # "Failed to load resource" is the console echo of a failed request, already counted above
    page.on("console", lambda m: errors.append(m.text) if m.type == "error"
            and not m.text.startswith("Failed to load resource") else None)
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    resp = page.goto(uri, wait_until="load")
    # A route that answers 404/500 still "renders" (an error page has pixels); render-url must see the status.
    doc_status = resp.status if resp is not None else None
    try:
        page.wait_for_load_state("networkidle", timeout=5000)
    except Exception:  # noqa: BLE001 -- a page that never goes idle is still observed as it stands
        pass
    # Scroll through once before observing: a full-page screenshot never scrolls, so scroll-reveal sections stayed at
    # opacity 0 and lazy images never loaded (first live render of bodeguita, 2026-11-22: sections 01-03 rendered
    # nearly invisible). The review must judge what a visitor sees after scrolling, not the pre-reveal state.
    # Capped: an infinite-scroll route grows scrollHeight on every step (review of render-url, LOW).
    page.evaluate("""async () => {
      const step = Math.max(200, Math.floor(window.innerHeight * 0.8));
      for (let y = 0, i = 0; y < document.documentElement.scrollHeight && i < %d; y += step, i++) {
        window.scrollTo(0, y);
        await new Promise(r => setTimeout(r, 120));
      }
      window.scrollTo(0, 0);
    }""" % MAX_SCROLL_STEPS)
    page.wait_for_timeout(800)
    # Scroll-DRIVEN animations (animation-timeline: view()/scroll()) depend on the current scroll position, so a
    # full-page capture taken at the top shows every one of them before entry -- no scrolling can fix that (probe of
    # bodeguita's `.reveal`: opacity 0.15 at top, 1 in view, 0.15 again back at top). Move each one to the document
    # timeline and FINISH it, so the element shows the animation's end keyframe. `animation: none` showed the base style
    # instead, which for the common `.reveal{opacity:0}` is invisible (review of render-url, MEDIUM). Elements still
    # under half opacity afterwards are counted, so a reveal the capture could not finish is reported, never hidden.
    neut = page.evaluate("""() => {
      let n = 0;
      const touched = new Set();
      for (const a of document.getAnimations()) {
        if (!a.timeline || a.timeline === document.timeline) continue;
        const el = a.effect && a.effect.target;
        try { a.timeline = document.timeline; a.finish(); }
        catch (e) { if (el) el.style.setProperty('animation', 'none', 'important'); }
        if (el) touched.add(el);
        n++;
      }
      const faint = [...touched].filter(el => parseFloat(getComputedStyle(el).opacity) < 0.5).length;
      return {n, faint};
    }""")
    raw = page.evaluate(FACTS_JS)
    raw["resources"] = (raw.get("resources") or []) + loaded
    seen = _missing_local_links(raw)
    seen["scroll_animations_neutralised"] = neut["n"]
    seen["scroll_animations_still_faint"] = neut["faint"]
    seen["failed_requests"] = [u for u in failed if not _IGNORED_URL.search(u.split(" (")[0])][:20]
    seen["console_errors"] = errors[:20]
    if isinstance(doc_status, int) and doc_status > 0:   # file:// navigations report no HTTP status
        seen["document_status"] = doc_status
    return seen


def facts_verdicts(facts: dict) -> list:
    """Render facts -> scorer verdicts. Pure; every criterion is emitted (pass or fail) so the record shows it ran."""
    from modules.cdio import scorer
    top = (facts or {}).get("viewports") or {}
    vps = dict(top)
    for name, x in top.items():   # each revealed screen is judged like a viewport of its own, named phone#<screen>
        for s in x.get("screens") or []:
            vps["%s#%s" % (name, s.get("label"))] = s
    unrendered = ["%s: %s" % (n, s) for n, x in top.items() for s in x.get("screens_unrendered") or []]

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
        v("RENDER-DEAD-LINK", "conversion", "major", union("dead_links"), "link(s) going nowhere (href '#', empty, javascript: or a missing local file)",
          "point every link at a real destination or make it a button with a handler"),
        v("RENDER-HORIZONTAL-OVERFLOW", "ux", "major", overflow, "viewport(s) scroll sideways",
          "find the element wider than the viewport (fixed widths, long words, 100vw plus a scrollbar)"),
        v("RENDER-DUPLICATE-IMAGE", "visual", "minor", union("duplicate_images"), "large image(s) shown more than once",
          "a repeated photo reads as a template; use a different asset or drop the repeat"),
        v("RENDER-UNRENDERED-SCREEN", "ux", "major", unrendered, "hidden screen(s) no render could show",
          "the review cannot judge a screen nobody saw: render it (at most %d screens per page, or split the page)"
          % MAX_SCREENS),
    ] + ([
        # Facts v3 (tranche 3, gates 6 and 7). Emitted only when the render collected them: an older render
        # measured none of this, and absent is not a pass.
        v("RENDER-IMG-NO-ALT", "ux", "major", union("img_no_alt"), "visible image(s) with no alt attribute",
          "give every image an alt: the words it stands for, or alt=\"\" when it is decoration"),
        v("RENDER-NAMELESS-CONTROL", "ux", "major", union("nameless_controls"),
          "link(s)/button(s) with no accessible name", "an icon-only control needs aria-label or an img alt"),
        v("RENDER-UNLABELLED-FIELD", "ux", "major", union("unlabelled_fields"), "form field(s) with no label",
          "tie a <label for> (or aria-label) to each field; hint text vanishes as soon as someone types"),
        v("RENDER-ZOOM-BLOCKED", "ux", "major", [n for n, x in vps.items() if x.get("zoom_blocked")],
          "viewport(s) forbid pinch zoom", "drop user-scalable=no and any maximum-scale under 2"),
        v("RENDER-NO-LANG", "ux", "minor", ["<html> has no lang"] if any(not x.get("lang") for x in vps.values()) else [],
          "page language undeclared", "set <html lang> so screen readers pronounce the copy right"),
        v("RENDER-OVERSIZED-IMAGE", "ux", "minor", union("oversized_images"),
          "image(s) over 2.5x the pixels they are shown at", "export at display size x2 at most, or use srcset"),
        v("RENDER-PAGE-WEIGHT", "ux", "minor",
          ["%s: %d KB (fonts %d KB; heaviest %s)" % (n, x["page_bytes"] // 1024, x.get("font_bytes", 0) // 1024,
                                                     ", ".join(x.get("heaviest") or []))
           for n, x in top.items() if (x.get("page_bytes") or 0) > PAGE_WEIGHT_BUDGET],
          "viewport(s) over the %d KB page budget" % (PAGE_WEIGHT_BUDGET // 1024),
          "compress or resize the heaviest assets, subset fonts, lazy-load below the fold"),
    ] if any("lang" in x for x in vps.values()) else []) + ([v("RENDER-DOCUMENT-STATUS", "ux", "critical",
            ["%s: HTTP %d" % (n, x["document_status"]) for n, x in top.items()
             if (x.get("document_status") or 0) >= 400],
            "viewport(s) served an error page", "the route itself fails; an error page is not the surface")]
         # emitted only by an HTTP render (render-url); a file:// render has no document status to judge
         if any("document_status" in x for x in vps.values()) else [])


def _facts_for(c: str, h: str) -> dict | None:
    """The facts of the latest render of these exact bytes, or None when that render collected none."""
    last = None
    for r in dr.read_rows("renders.jsonl"):
        if r.get("file") == c and r.get("sha") == h and r.get("pngs"):
            last = r
    facts = (last or {}).get("facts")
    return facts if isinstance(facts, dict) and facts.get("collected") is True else None


# Brand assets (2026-11-22, Owner "rec": CCF produces, CDIO judges). A logo is judged where it will live: on light
# and on dark, at favicon, UI and hero size. The frame is generated next to the renders and is what gets rendered;
# the row is bound to the ASSET's bytes. The frame repeats the asset on purpose, so its repeat count is not a defect.
ASSET_EXT = (".svg", ".png")
ASSET_SIZES = (32, 96, 320)


def _frame(asset: str, sha: str, out_dir: Path) -> Path:
    uri = Path(asset).as_uri()
    name = os.path.basename(asset)
    rows = "".join(
        '<section class="%s">%s</section>' % (bg, "".join(
            '<img src="%s" alt="%s on %s at %dpx" style="width:%dpx;height:auto">' % (uri, name, bg, s, s)
            for s in ASSET_SIZES)) for bg in ("light", "dark"))
    html = ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><title>%s</title><style>"
            "body{margin:0;font-family:system-ui,sans-serif}section{display:flex;flex-wrap:wrap;gap:32px;"
            "align-items:center;padding:32px}.light{background:#f7f7f5}.dark{background:#151515}"
            "</style></head><body>%s</body></html>") % (name, rows)
    p = out_dir / ("frame-%s.html" % sha[:16])
    p.write_text(html, encoding="utf-8")
    return p


def render(files: list) -> int:
    from playwright.sync_api import sync_playwright
    out_dir = dr.state_dir() / "renders"
    out_dir.mkdir(exist_ok=True)
    rc = 0
    with sync_playwright() as pw:
        browser = _launch(pw)
        try:
            for f in files:
                low = f.lower()
                if not (low.endswith(dr.HTML_EXT) or low.endswith(ASSET_EXT)) or not os.path.isfile(f):
                    print("SKIP %s: not an HTML page or a brand asset (.svg/.png) on disk; app source renders "
                          "through `render-url`" % f)
                    rc = 1
                    continue
                c, h = dr.canon(f), dr.sha256(f)
                asset = low.endswith(ASSET_EXT)
                target = _frame(c, h, out_dir) if asset else Path(c)
                pngs, facts = [], {"collected": True, "version": FACTS_VERSION, "viewports": {}}
                if asset:
                    facts["frame"] = True
                for name, (w, hgt) in VIEWPORTS.items():
                    page = browser.new_page(viewport={"width": w, "height": hgt})
                    facts["viewports"][name] = _observe(page, target.as_uri())
                    if asset:
                        facts["viewports"][name]["duplicate_images"] = []
                    png = out_dir / ("%s-%s.png" % (h[:16], name))
                    page.screenshot(path=str(png), full_page=True)
                    pngs.append(str(png))
                    if not asset:   # a brand frame has no screens; a page may hide some behind JS state (B-8)
                        scr, lost = _render_screens(page, out_dir, "%s-%s" % (h[:16], name))
                        facts["viewports"][name].update(screens=scr, screens_unrendered=lost)
                        pngs += [s["png"] for s in scr]
                    page.close()
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


# App surfaces (tsx/jsx/vue/svelte/css inside an app) render only through the running app. Measured 2026-11-22: most
# of the 28 live APPROVEs were .tsx files admitted by ANY >= 300x300 PNG newer than the file -- no route, no viewport,
# no runtime facts. render-url renders the route the files build at three widths, collects the same facts as `render`
# and binds them to the bytes of every listed file (V-DRU-*).
URL_VIEWPORTS = {"desktop": (1440, 900), "tablet": (820, 1180), "phone": (390, 844)}
_URL_RX = re.compile(r"^https?://[^\s/]+", re.I)


def render_url(url: str, files: list) -> int:
    if not _URL_RX.match(url or ""):
        print("REFUSED: --url must be an http(s) URL of the running app (dev server, preview or production)")
        return 2
    missing = [f for f in files if not os.path.isfile(f)]
    if missing:
        print("REFUSED: not a file: %s" % ", ".join(missing))
        return 2
    from playwright.sync_api import sync_playwright
    out_dir = dr.state_dir() / "renders"
    out_dir.mkdir(exist_ok=True)
    bound = [(dr.canon(f), dr.sha256(f)) for f in files]   # hashed BEFORE the render: the bytes the route was built from
    tag = __import__("hashlib").sha256(("%s|%s" % (url, "|".join(h for _, h in bound))).encode()).hexdigest()[:16]
    pngs, screen_pngs, facts = [], [], {"collected": True, "version": FACTS_VERSION, "url": url, "viewports": {}}
    with sync_playwright() as pw:
        browser = _launch(pw)
        try:
            for name, (w, hgt) in URL_VIEWPORTS.items():
                page = browser.new_page(viewport={"width": w, "height": hgt})
                try:
                    facts["viewports"][name] = _observe(page, url)
                except Exception as exc:  # noqa: BLE001 -- an unreachable route is a recorded fact, never a skip
                    facts["viewports"][name] = {"document_status": 599, "console_errors": [
                        "navigation failed: %s" % str(exc).splitlines()[0][:200]]}
                    page.close()
                    continue
                png = out_dir / ("url-%s-%s.png" % (tag, name))
                page.screenshot(path=str(png), full_page=True)
                scr, lost = _render_screens(page, out_dir, "url-%s-%s" % (tag, name))
                facts["viewports"][name].update(screens=scr, screens_unrendered=lost)
                page.close()
                pngs.append(str(png))
                screen_pngs += [s["png"] for s in scr]
        finally:
            browser.close()
    changed = [os.path.basename(c) for c, h in bound if dr.sha256(c) != h]
    if changed:   # the files moved under the render: it shows neither the old bytes nor the new ones for sure
        print("REFUSED: changed during the render, render again: %s" % ", ".join(changed))
        return 2
    for c, h in bound:
        dr.append_row("renders.jsonl", {"file": c, "sha": h, "pngs": pngs + screen_pngs, "facts": facts, "url": url})
    print("RENDERED %s (%d viewports) for %d file(s) -> %s" % (url, len(pngs), len(bound), " ".join(pngs + screen_pngs)))
    for vd in facts_verdicts(facts):
        if vd.status == "fail":
            print("  DEFECT %s [%s] %s" % (vd.criterion, vd.severity, vd.observed))
    print("Look at every PNG (Read tool) before writing verdicts: the review judges what renders, not the source.")
    return 0 if len(pngs) == len(URL_VIEWPORTS) else 1


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
    url_folded: set = set()
    _ = screenshot   # accepted for old callers; it no longer admits anything (see the app-source branch below)
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
        elif c.lower().endswith(ASSET_EXT):
            # A brand asset counts only through its framed render (light/dark, 32/96/320 px) for these exact bytes.
            facts = _facts_for(c, h)
            if facts is None or not facts.get("frame"):
                refusals.append("%s: brand asset never rendered for these bytes (run `render %s`)"
                                % (os.path.basename(c), os.path.basename(c)))
            else:
                folded += facts_verdicts(facts)
        elif c in covered:
            continue
        else:
            # App source: only a render-url row for these exact bytes counts. A bare --screenshot proved a PNG existed,
            # not that it showed this route or these bytes, and it carried no runtime facts (V-DRU-SCREENSHOT-RETIRED).
            facts = _facts_for(c, h)
            if facts is None or not facts.get("url"):
                refusals.append("%s: app source never rendered for these bytes: run `render-url --url <running route> "
                                "--files <files>` (a bare --screenshot PNG is no longer proof)" % os.path.basename(c))
            else:
                # One render bound to N files is ONE observation, not N deductions. The key is the observation itself,
                # never the URL: two renders of one URL (a clean one for b.tsx, a later broken one for a.tsx) are two
                # observations, and keying on the URL dropped the broken one (review of render-url, HIGH).
                key = json.dumps(facts, sort_keys=True)
                if key not in url_folded:
                    url_folded.add(key)
                    folded += facts_verdicts(facts)
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
    ru = sub.add_parser("render-url")
    ru.add_argument("--url", required=True)
    ru.add_argument("--files", nargs="+", required=True)
    rec = sub.add_parser("record")
    rec.add_argument("--verdicts", required=True)
    rec.add_argument("--files", nargs="+", required=True)
    rec.add_argument("--screenshot")
    rec.add_argument("--experience", help="JSON {declared, observed}: the CDIO-07 contract, so a breach withholds done")
    a = ap.parse_args(argv)
    if a.cmd == "render":
        return render(a.files)
    if a.cmd == "render-url":
        return render_url(a.url, a.files)
    row = record(a.verdicts, a.files, a.screenshot, a.experience)
    print(json.dumps(row, indent=1, ensure_ascii=False))
    return 0 if row["is_done"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
