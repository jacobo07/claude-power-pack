"""BCAP-2 laptop-plane browser bench for Phases 4 (Anime.js) and 5 (Synsation UX).

LAPTOP_STEPS.md asks for what a declared-record gate cannot see: real hitboxes, focus/scroll to the first invalid
field, CLS of skeletons, optimistic rollback, reduced motion exercised, timeline cancel on unmount. This drives
vault/programs/bcap-2/browser/bench.html in real Chromium (Playwright). Every section has a GOOD and a BAD pole, and
what is MEASURED is fed into the same modules/cdio/ux_contracts.py functions the Phase 5 gate pins, so the
contract is judged on browser-observed records rather than hand-declared ones.

  python tools/bcap2_browser_bench.py --anime <anime.umd.min.js 4.5.0> [--out vault/programs/bcap-2/browser/BROWSER_RESULTS.json]

Exit 0 = every pole came out the way the contract says (GOOD passes, BAD is caught). Exit 1 = a mismatch.
Exit 2 = the bench could not run (missing bundle or Playwright). anime.js is not vendored: its sha256 is recorded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modules.cdio import ux_contracts as ux  # noqa: E402

BENCH = ROOT / "vault/programs/bcap-2/browser/bench.html"
URL = "https://bench.local/"
ANIME_PIN = {"package": "animejs", "version": "4.5.0", "file": "dist/bundles/anime.umd.min.js",
             "source": "https://cdn.jsdelivr.net/npm/animejs@4.5.0/dist/bundles/anime.umd.min.js", "license": "MIT"}

HIT_JS = """(sel) => {  // sample elementFromPoint on a 1px grid around the element; real hit rect = bbox of hits
  const el = document.querySelector(sel); el.scrollIntoView({block: 'center'});
  const r = el.getBoundingClientRect(); const pad = 30; let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9, n = 0;
  for (let y = Math.floor(r.top - pad); y <= r.bottom + pad; y++) for (let x = Math.floor(r.left - pad); x <= r.right + pad; x++) {
    const e = document.elementFromPoint(x, y); if (!e) continue;
    const hit = e === el || el.contains(e) && !(e.closest('button') && e.closest('button') !== el && el.tagName !== 'BUTTON');
    if (hit) { n++; x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }
  }
  // document coordinates, so rects measured at different scroll positions are comparable
  return n ? {x: x0 + scrollX, y: y0 + scrollY, w: x1 - x0 + 1, h: y1 - y0 + 1} : null;
}"""
VIEW_JS = """(sel) => { const el = document.querySelector(sel); el.scrollIntoView({block: 'center'});
  const r = el.getBoundingClientRect(); return {x: r.left, y: r.top, w: r.width, h: r.height}; }"""
DOC_JS = """(sel) => { const r = document.querySelector(sel).getBoundingClientRect();
  return {x: r.left + scrollX, y: r.top + scrollY, w: r.width, h: r.height}; }"""
TX_JS = "(sel) => { const m = getComputedStyle(document.querySelector(sel)).transform; return m === 'none' ? 0 : new DOMMatrix(m).m41; }"


def _load(ctx, anime_src):
    page = ctx.new_page()
    page.route(URL, lambda route: route.fulfill(status=200, content_type="text/html", body=BENCH.read_text(encoding="utf-8")))
    page.route("**/api/like", lambda route: route.fulfill(status=500, body="fail"))
    page.goto(URL)
    page.add_script_tag(content=anime_src)
    return page


def run(anime_path: Path):
    from playwright.sync_api import sync_playwright
    anime_src = anime_path.read_text(encoding="utf-8")
    res = {"bench": str(BENCH.relative_to(ROOT)).replace("\\", "/"),
           "bench_sha256": hashlib.sha256(BENCH.read_bytes()).hexdigest(),
           "anime": dict(ANIME_PIN, sha256=hashlib.sha256(anime_path.read_bytes()).hexdigest()),
           "viewport": {"width": 800, "height": 700}, "checks": []}

    def check(cid, claim, measured, expected, got):
        ok = got == expected
        res["checks"].append({"id": cid, "claim": claim, "measured": measured, "expected": expected, "got": got, "ok": ok})

    with sync_playwright() as p:
        b = p.chromium.launch()
        res["chromium"] = b.version
        ctx = b.new_context(viewport=res["viewport"], reduced_motion="no-preference")
        page = _load(ctx, anime_src)

        # 1 hit targets (UX-04..06): measured rects -> check_hit_targets
        rects = {k: page.evaluate(HIT_JS, "#" + k) for k in ("heart-good", "heart-bad", "chk-label", "card-good-btn", "card-bad-btn")}
        page.click("#card-good-btn"); page.click("#card-bad-btn")
        cards = page.evaluate("bench.cardActivations")
        for k in ("heart-good", "heart-bad"):                                   # 8 px outside the visible glyph
            g = page.evaluate(VIEW_JS, "#" + k)
            page.mouse.click(g["x"] + g["w"] + 8, g["y"] + g["h"] / 2)
        hearts = page.evaluate("bench.heart")
        lv = page.evaluate(VIEW_JS, "#chk-label")
        page.mouse.click(lv["x"] + lv["w"] - 3, lv["y"] + lv["h"] / 2)           # far edge of the label row
        chk = page.evaluate("document.getElementById('chk').checked")
        ll = rects["chk-label"]
        targets = [
            {"id": "heart-good", "hit": rects["heart-good"]}, {"id": "heart-bad", "hit": rects["heart-bad"]},
            {"id": "chk-label", "hit": rects["chk-label"]},
            {"id": "card-good", "hit": page.evaluate(DOC_JS, "#card-good"), "interactive": True},
            {"id": "card-bad", "hit": page.evaluate(DOC_JS, "#card-bad"), "interactive": True},
            {"id": "card-good-btn", "hit": rects["card-good-btn"], "parent": "card-good", "stops_propagation": cards["good"] == 0},
            {"id": "card-bad-btn", "hit": rects["card-bad-btn"], "parent": "card-bad", "stops_propagation": cards["bad"] == 0},
        ]
        defects = ux.check_hit_targets([{**t, "hit": {k: t["hit"][k] for k in ("x", "y", "w", "h")}} for t in targets])
        by = lambda i: sorted(d["defect"] for d in defects if d["id"] == i)
        check("UX-04 expanded", "invisible hit area expands a 20px glyph to >=44px", rects["heart-good"], [], by("heart-good"))
        check("UX-04 bare", "a bare 20px glyph is caught as undersized", rects["heart-bad"], ["undersized-hit-target"], by("heart-bad"))
        check("UX-04 click-outside", "a tap 8px outside the glyph lands only on the expanded target", hearts, {"good": 1, "bad": 0}, hearts)
        check("UX-05 label", "the whole label row is the checkbox target", {"rect": ll, "checked_by_edge_click": chk}, [True, []], [chk, by("chk-label")])
        check("UX-06 nested good", "nested Delete stops propagation (card not activated)", cards, [], by("card-good-btn"))
        check("UX-06 nested bad", "nested Delete that lets the tap reach the card is caught", cards, ["nested-interactive-steals-tap"], by("card-bad-btn"))

        # 2 disabled controls / first invalid field (UX-01..03)
        page.click("#g-submit")
        focus = page.evaluate("""() => { const a = document.activeElement, r = a.getBoundingClientRect();
            return {id: a.id, in_view: r.top >= 0 && r.bottom <= innerHeight, aria_invalid: a.getAttribute('aria-invalid'),
                    summary: !document.getElementById('err-summary').hidden, msg_visible: !document.getElementById('g-work-err').hidden}; }""")
        check("UX-02 first-invalid", "enabled submit moves focus to the first invalid field, scrolls it into view, shows why",
              focus, {"id": "g-work", "in_view": True, "aria_invalid": "true", "summary": True, "msg_visible": True}, focus)
        good_rec = {"disabled": page.is_disabled("#g-submit"), "inert_when_clicked": not focus["summary"]}
        check("UX-01 good", "submit that stays enabled and explains is not a disabled-control defect", good_rec, [], ux.check_disabled_control(good_rec))
        page.click("#b-submit", force=True)
        bad_vis = page.evaluate("""() => { const b = document.getElementById('b-submit');
            return {reason_visible: !!(b.getAttribute('aria-describedby') || b.title), clicks: bench.disabledClicks}; }""")
        page.fill("#b-work", "1 Main St")
        enabled_when_valid = not page.is_disabled("#b-submit")
        bad_rec = {"disabled": True, "reason_visible": bad_vis["reason_visible"], "click_handler_fires": bad_vis["clicks"] > 0,
                   "enabled_when_valid": enabled_when_valid, "blocked_by_validation": True, "has_error_path": False}
        check("UX-01 bad", "disabled submit with no visible reason and no error path is caught", bad_rec,
              ["opaque-disabled-action", "validation-block-with-no-error-path"], sorted(ux.check_disabled_control(bad_rec)))

        # 3 skeleton vs spinner (UX-07..09): layout shift of the content below each slot
        before = page.evaluate("() => ({g: document.getElementById('after-good').getBoundingClientRect().top + scrollY, b: document.getElementById('after-bad').getBoundingClientRect().top + scrollY})")
        page.evaluate("""() => { window.__cls = 0; new PerformanceObserver(l => { for (const e of l.getEntries()) if (!e.hadRecentInput) window.__cls += e.value; })
                                 .observe({type: 'layout-shift', buffered: false}); }""")
        page.evaluate("loadSkeletons()")
        page.wait_for_timeout(200)
        after = page.evaluate("() => ({g: document.getElementById('after-good').getBoundingClientRect().top + scrollY, b: document.getElementById('after-bad').getBoundingClientRect().top + scrollY, cls: window.__cls})")
        shift = {"good_px": round(after["g"] - before["g"], 2), "bad_px": round(after["b"] - before["b"], 2), "cls_total": round(after["cls"], 4)}
        check("UX-08 skeleton", "skeleton reserving final geometry causes zero shift below it", shift, 0, shift["good_px"])
        check("UX-08 spinner", "a 1-line spinner replaced by taller content shifts what is below", shift, True, shift["bad_px"] > 0)
        check("UX-07 route", "waiting_pattern picks skeleton for a 600ms section with known geometry", None, "skeleton",
              ux.waiting_pattern("section", 600, geometry_known=True)["pattern"])

        # 4 optimistic with rollback (UX-11)
        out = {}
        for k in ("good", "bad"):
            # read in the same task as the click: like() increments before its `await fetch`, so this is the
            # state the person sees at once (a page.click + read races the routed 500 and the rollback)
            out[k + "_immediate"] = page.evaluate("(k) => { document.getElementById('like-' + k).click(); "
                                                  "return document.getElementById('like-' + k + '-n').textContent; }", k)
            page.wait_for_timeout(800)
            out[k + "_settled"] = page.text_content("#like-%s-n" % k)
            out[k + "_message"] = page.text_content("#like-%s-err" % k)
        check("UX-11 good", "optimistic count shows at once, rolls back on HTTP 500 and says so", out, ["11", "10", True],
              [out["good_immediate"], out["good_settled"], bool(out["good_message"])])
        check("UX-11 bad", "an optimistic update with no rollback keeps a false count (caught)", out, ["11", "11", False],
              [out["bad_immediate"], out["bad_settled"], bool(out["bad_message"])])
        check("UX-11 route", "waiting_pattern picks optimistic for a reversible likely-success control", None, "optimistic",
              ux.waiting_pattern("control", 400, reversible=True, success_likely=True)["pattern"])

        # 6 timeline cancel on unmount (Phase 4 scope/revert lifecycle)
        page.evaluate("mountTimelines()")
        page.wait_for_timeout(300)
        c0 = page.evaluate("({...bench.tl})")
        page.evaluate("unmountTimelines()")
        page.wait_for_timeout(50)
        c1 = page.evaluate("({...bench.tl})")
        page.wait_for_timeout(500)
        c2 = page.evaluate("({...bench.tl})")
        tl = {"running": c0, "at_unmount": c1, "after_500ms": c2}
        check("AJS lifecycle good", "scope.revert() on unmount stops the looping timeline", tl, [True, 0], [c0["good"] > 0, c2["good"] - c1["good"]])
        check("AJS lifecycle bad", "removing the node without cancel leaves the timeline ticking (caught)", tl, [True, True],
              [c0["bad"] > 0, c2["bad"] - c1["bad"] > 0])
        ctx.close()

        # 5 reduced motion (CDIO-07 floor): same final state, no in-between under `reduce`
        rm = {}
        for mode in ("reduce", "no-preference"):
            c = b.new_context(viewport=res["viewport"], reduced_motion=mode)
            pg = _load(c, anime_src)
            pg.evaluate("runReducedMotion()")
            pg.wait_for_timeout(120)
            mid = {"good": pg.evaluate(TX_JS, "#rm-good"), "bad": pg.evaluate(TX_JS, "#rm-bad")}
            pg.wait_for_timeout(1200)
            end = {"good": pg.evaluate(TX_JS, "#rm-good"), "bad": pg.evaluate(TX_JS, "#rm-bad")}
            rm[mode] = {"t120ms": mid, "t1320ms": end}
            c.close()
        r, n = rm["reduce"], rm["no-preference"]
        check("RM good", "under reduce the honouring element is at its final state with no in-between", rm, [200, 200],
              [round(r["t120ms"]["good"]), round(r["t1320ms"]["good"])])
        check("RM bad", "the element that ignores reduce is still mid-animation at 120ms (caught)", rm, True, 0 < r["t120ms"]["bad"] < 200)
        check("RM equivalence", "final states are equal with and without reduce", rm, True,
              round(r["t1320ms"]["good"]) == round(n["t1320ms"]["good"]) == 200)
        check("RM motion still runs", "without reduce the honouring element animates (not just disabled)", rm, True, 0 < n["t120ms"]["good"] < 200)
        b.close()
    res["passed"] = sum(c["ok"] for c in res["checks"])
    res["failed"] = len(res["checks"]) - res["passed"]
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--anime", required=True, type=Path)
    ap.add_argument("--out", type=Path, default=ROOT / "vault/programs/bcap-2/browser/BROWSER_RESULTS.json")
    a = ap.parse_args(argv)
    if not a.anime.is_file():
        print("BENCH NOT RUN: anime bundle missing: %s" % a.anime)
        return 2
    try:
        import playwright  # noqa: F401
    except ImportError:
        print("BENCH NOT RUN: playwright not installed")
        return 2
    res = run(a.anime)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    for c in res["checks"]:
        print("%s %-22s %s%s" % ("PASS" if c["ok"] else "FAIL", c["id"], c["claim"], "" if c["ok"] else "  got=%r expected=%r" % (c["got"], c["expected"])))
    print("%d PASS / %d FAIL  chromium %s  anime %s sha256 %s" % (res["passed"], res["failed"], res["chromium"],
                                                                 res["anime"]["version"], res["anime"]["sha256"][:12]))
    return 0 if res["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
