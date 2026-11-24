"""Browser QA for the CDIO-13 recipe-02 demo: measure each criterion in a real Chromium.

usage: python qa_site.py <site dir> <out dir>
Writes screenshots + qa.json into <out dir>; prints one line per measurement.
"""
import json, os, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

SITE, OUT = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
OUT.mkdir(parents=True, exist_ok=True)
URL = (SITE / "index.html").as_uri()
VIEWPORTS = {"desktop": (1440, 900), "mobile": (390, 844)}
CLS_JS = """() => new Promise(res => { let v = 0; new PerformanceObserver(l => { for (const e of l.getEntries())
  if (!e.hadRecentInput) v += e.value; }).observe({type: 'layout-shift', buffered: true});
  setTimeout(() => res(v), 1500); })"""
ARCH_JS = "() => [...document.querySelectorAll('[data-arch]')].map(e => getComputedStyle(e).clipPath)"
r = {}


def rec(key, value):
    r[key] = value
    print(f"{key}: {value}")


with sync_playwright() as p:
    b = p.chromium.launch()
    for vname, (w, h) in VIEWPORTS.items():
        # 1. Normal: motion allowed.
        ctx = b.new_context(viewport={"width": w, "height": h}, reduced_motion="no-preference")
        pg = ctx.new_page()
        errors = []
        pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(URL, wait_until="networkidle")
        pg.evaluate("document.fonts.ready")
        rec(f"{vname}.cls", round(pg.evaluate(CLS_JS), 4))
        h1 = pg.locator("h1").bounding_box()
        cta = pg.locator(".hero .cta").bounding_box()
        rec(f"{vname}.hero_h1_bottom", round(h1["y"] + h1["height"]))
        rec(f"{vname}.hero_cta_bottom", round(cta["y"] + cta["height"]))
        rec(f"{vname}.hero_fits", (cta["y"] + cta["height"]) <= h)
        rec(f"{vname}.overflow_x", pg.evaluate("document.documentElement.scrollWidth") > w)
        rec(f"{vname}.gsap_loaded", pg.evaluate("!!(window.gsap && window.ScrollTrigger)"))
        rec(f"{vname}.scrolltriggers", pg.evaluate("window.ScrollTrigger ? ScrollTrigger.getAll().length : -1"))
        rec(f"{vname}.arches_before_scroll", pg.evaluate(ARCH_JS))
        pg.screenshot(path=str(OUT / f"{vname}-first-viewport.png"))
        for _ in range(12):
            pg.mouse.wheel(0, h * 0.6)
            time.sleep(0.25)
        time.sleep(1.8)
        rec(f"{vname}.arches_after_scroll", pg.evaluate(ARCH_JS))
        pg.evaluate("window.scrollTo(0, 0)")
        time.sleep(0.4)
        pg.screenshot(path=str(OUT / f"{vname}-full.png"), full_page=True)
        rec(f"{vname}.cta_target_exists", pg.evaluate("!!document.querySelector('#enquire')"))
        rec(f"{vname}.mailto", pg.locator("#enquire a.cta").get_attribute("href"))
        rec(f"{vname}.small_text_px", pg.evaluate(
            "Math.min(...[...document.querySelectorAll('p,dd,dt,li,a,figcaption')].map(e => parseFloat(getComputedStyle(e).fontSize)))"))
        # Tap targets: every link/button that is not inline inside running text.
        rec(f"{vname}.tap_targets_under_44", pg.evaluate("""() => [...document.querySelectorAll('a,button')]
          .filter(e => !e.closest('p,dd,li p') && getComputedStyle(e).position !== 'absolute')
          .map(e => { const b = e.getBoundingClientRect(); return [e.textContent.trim().slice(0, 30),
                      Math.round(b.width), Math.round(b.height)]; })
          .filter(([, w, h]) => w < 44 || h < 44)"""))
        rec(f"{vname}.hero_cta_bottom_after_fix", round(pg.locator(".hero .cta").bounding_box()["y"]
                                                          + pg.locator(".hero .cta").bounding_box()["height"]))
        rec(f"{vname}.console_errors", errors)
        ctx.close()

        # Throttled profile (slow 4G, CPU x4) for CLS while fonts and GSAP arrive late.
        ctx = b.new_context(viewport={"width": w, "height": h}, reduced_motion="no-preference")
        pg = ctx.new_page()
        cdp = ctx.new_cdp_session(pg)
        cdp.send("Network.enable")
        cdp.send("Network.emulateNetworkConditions", {"offline": False, "latency": 150,
                 "downloadThroughput": 1_600_000 / 8, "uploadThroughput": 750_000 / 8})
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
        pg.goto(URL, wait_until="load")
        rec(f"{vname}.throttled.cls", round(pg.evaluate(CLS_JS.replace("1500", "4000")), 4))
        ctx.close()

        # 2. Reduced motion: nothing animates, every arch open.
        ctx = b.new_context(viewport={"width": w, "height": h}, reduced_motion="reduce")
        pg = ctx.new_page()
        pg.goto(URL, wait_until="networkidle")
        rec(f"{vname}.reduced.arches", pg.evaluate(ARCH_JS))
        rec(f"{vname}.reduced.scrolltriggers", pg.evaluate("window.ScrollTrigger ? ScrollTrigger.getAll().length : -1"))
        ctx.close()

        # 3. No JavaScript: layout and navigation work before motion.
        ctx = b.new_context(viewport={"width": w, "height": h}, java_script_enabled=False)
        pg = ctx.new_page()
        pg.goto(URL, wait_until="networkidle")
        rec(f"{vname}.nojs.arches", pg.evaluate(ARCH_JS) if False else
            [pg.locator("[data-arch]").nth(i).evaluate("e => getComputedStyle(e).clipPath")
             for i in range(pg.locator("[data-arch]").count())])
        rec(f"{vname}.nojs.sections_visible", all(
            pg.locator(s).is_visible() for s in ["h1", "#rooms", "#stay", "#enquire", "footer"]))
        pg.click("nav >> text=Stay")
        rec(f"{vname}.nojs.nav_stay_scrolls", pg.evaluate("window.scrollY") > 0)
        pg.screenshot(path=str(OUT / f"{vname}-nojs-full.png"), full_page=True)
        ctx.close()
    b.close()
json.dump(r, open(OUT / "qa.json", "w", encoding="utf-8"), indent=2)
