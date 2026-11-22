#!/usr/bin/env python3
"""test_cdio_rendered.py -- V-gates for the CDIO rendered-page checks (CANDIDATE, warning-only).

Module: modules/cdio/rendered_checks.py + modules/cdio/rendered_probe.js.
Origin: Bodeguita El Puerto V3 spec, Owner decision 3 (2026-11-22).

  V-CDIO-RENDERED-MOTIF       repeated file+crop is flagged; distinct crops of one file are not
  V-CDIO-RENDERED-PICTOGRAM   >= 4 small SVG pictograms flagged; 3, or large SVG art, are not
  V-CDIO-RENDERED-MONOTONY    two same-shape MEDIA neighbours flagged; text-only runs counted, not judged
  V-CDIO-RENDERED-PROVENANCE  unlabelled art flagged only when the page declares the convention;
                              otherwise the state is not_declared (never reported as clean)
  V-CDIO-RENDERED-WARNONLY    every finding is a warning, blocking is False, the CLI exits 0
  V-CDIO-RENDERED-PROBE       the JS probe, run in real Chromium on built pages, feeds the same
                              verdicts (skipped as NOT MEASURED when Playwright is missing)

Every refusal has a control in which the page is fine and nothing is flagged.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from modules.cdio import rendered_checks as rc  # noqa: E402

PASSES = 0
FAILS = 0


def gate(name: str, ok: bool, detail: str = "") -> None:
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print(f"PASS {name}")
    else:
        FAILS += 1
        print(f"FAIL {name} {detail}")


def art(file: str, w: int = 300, pos: str = "50% 50%", svg: bool = False, kind: str | None = None) -> dict:
    return {"file": file, "position": pos, "w": w, "h": w, "svg": svg, "kind": kind}


def section(label: str, lum: float, cols: int, media: bool, height: int = 600) -> dict:
    return {"label": label, "luminance": lum, "cols": cols, "media": media, "height": height}


def checks_of(report: rc.RenderedReport) -> list[str]:
    return [f.check for f in report.findings]


def v_motif() -> None:
    state, found = rc.check_motif_repetition([art("plate"), art("plate"), art("plate"), art("fish")])
    gate("V-CDIO-RENDERED-MOTIF refuse", state == rc.STATE_MEASURED and len(found) == 1 and "3 times" in found[0].observed, str(found))
    _, found = rc.check_motif_repetition([art("scene", pos="10% 10%"), art("scene", pos="80% 70%"), art("icon", w=20), art("icon", w=20)])
    gate("V-CDIO-RENDERED-MOTIF control", found == [], str(found))


def v_pictogram() -> None:
    small = [art(n, w=56, svg=True) for n in ("a", "b", "c", "d")]
    _, found = rc.check_pictogram_density(small)
    gate("V-CDIO-RENDERED-PICTOGRAM refuse", len(found) == 1 and "4 pictograms" in found[0].observed, str(found))
    _, found = rc.check_pictogram_density(small[:3] + [art("big", w=400, svg=True), art("photo", w=60)])
    gate("V-CDIO-RENDERED-PICTOGRAM control", found == [], str(found))


def v_monotony() -> None:
    state, found = rc.check_section_monotony([section("hero", 0.9, 2, True), section("about", 0.85, 2, True)])
    gate("V-CDIO-RENDERED-MONOTONY refuse", state == rc.STATE_MEASURED and len(found) == 1, str(found))
    _, found = rc.check_section_monotony([section("hero", 0.04, 2, True), section("about", 0.95, 2, True), section("strip", 0.7, 1, True)])
    gate("V-CDIO-RENDERED-MONOTONY control", found == [], str(found))
    state, found = rc.check_section_monotony([section(f"s{i}", 0.02, 1, False) for i in range(4)])
    gate("V-CDIO-RENDERED-MONOTONY text-only counted", found == [] and "3 text-only pair(s) not judged" in state, state)
    state, found = rc.check_section_monotony([section("rule", 0.9, 1, False, height=48), section("only", 0.9, 1, True)])
    gate("V-CDIO-RENDERED-MONOTONY thin dividers ignored", state == rc.STATE_NOTHING and found == [], state)


def v_provenance() -> None:
    state, found = rc.check_art_provenance([art("scene", kind="concept-illustration"), art("stock")], declares=True)
    gate("V-CDIO-RENDERED-PROVENANCE refuse", state == rc.STATE_MEASURED and len(found) == 1 and "stock" in found[0].observed, str(found))
    state, found = rc.check_art_provenance([art("scene", kind="concept-illustration")], declares=True)
    gate("V-CDIO-RENDERED-PROVENANCE control", state == rc.STATE_MEASURED and found == [], str(found))
    state, found = rc.check_art_provenance([art("stock")], declares=False)
    gate("V-CDIO-RENDERED-PROVENANCE not_declared is not clean", state == rc.STATE_NOT_DECLARED and found == [], state)


def v_warn_only() -> None:
    v2_like = {
        "url": "fixture:v2", "viewport": 1440, "declaresProvenance": True,
        "art": [art("plate"), art("plate"), *[art(n, w=56, svg=True) for n in "abcd"]],
        "sections": [section("hero", 0.9, 2, True), section("about", 0.9, 2, True)],
    }
    report = rc.evaluate(v2_like)
    kinds = set(checks_of(report))
    gate("V-CDIO-RENDERED-WARNONLY every check fires on a V2-like page",
         kinds == {"motif-repetition", "pictogram-density", "section-monotony", "art-provenance"}, str(kinds))
    gate("V-CDIO-RENDERED-WARNONLY severity", all(f.severity == "warning" for f in report.findings))
    gate("V-CDIO-RENDERED-WARNONLY never blocking", report.blocking is False and report.to_dict()["blocking"] is False)
    clean = rc.evaluate({"url": "fixture:v3", "viewport": 1440, "declaresProvenance": True,
                         "art": [art("scene", kind="concept-illustration")],
                         "sections": [section("hero", 0.04, 2, True), section("about", 0.95, 2, True)]})
    gate("V-CDIO-RENDERED-WARNONLY control: V3-like page is clean", clean.findings == [], str(clean.findings))


PROBE_PAGE = """<!doctype html><html><body style="margin:0;background:#fff"><main>
<section aria-labelledby="a" style="height:400px;background:#fff"><div style="display:grid;grid-template-columns:1fr 1fr">
  <img src="/plate.svg" width="200" height="200" alt=""><p id="a">A</p></div></section>
<section aria-labelledby="b" style="height:400px;background:#fafafa"><div style="display:grid;grid-template-columns:1fr 1fr">
  <img src="/plate.svg" width="200" height="200" alt=""><p id="b">B</p></div></section>
<section aria-labelledby="c" style="height:400px;background:#3d2423"><div><p id="c">C</p>
  <img src="/x.png" data-art-kind="ornament" width="300" height="200" alt=""></div></section>
</main></body></html>"""


def v_probe() -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("NOT MEASURED V-CDIO-RENDERED-PROBE (python playwright not installed) -- not counted as a pass")
        return
    script = open(rc.PROBE_JS, encoding="utf-8").read()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 900})
        page.set_content(PROBE_PAGE)
        probe = page.evaluate(script)
        browser.close()
    report = rc.evaluate(probe)
    gate("V-CDIO-RENDERED-PROBE probe shape", len(probe["sections"]) == 3 and len(probe["art"]) == 3 and probe["declaresProvenance"] is True, str(probe)[:300])
    gate("V-CDIO-RENDERED-PROBE real DOM -> motif + monotony + provenance",
         {"motif-repetition", "section-monotony", "art-provenance"} <= set(checks_of(report)), str(checks_of(report)))
    gate("V-CDIO-RENDERED-PROBE dark text section not paired as same shape",
         sum(1 for f in report.findings if f.check == "section-monotony") == 1, str(report.findings))


def main() -> int:
    v_motif()
    v_pictogram()
    v_monotony()
    v_provenance()
    v_warn_only()
    v_probe()
    print(f"V-CDIO-RENDERED-PASS={PASSES}/{PASSES + FAILS}")
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
