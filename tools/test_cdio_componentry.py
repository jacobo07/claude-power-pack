"""V-CMP-* gate for CDIO-11 (componentry catalogue, absorbed 2026-10-13).

Every check runs on the real vendored source and the real resolver; the synthetic
inputs are limited to the registry-shape checks, where the point is a shape upstream
has not shipped yet. Each discrimination is driven from both poles, and the advisory
bound is also run against a mutant that must turn it red.

    python tools/test_cdio_componentry.py      # exit 0 = all V-CMP-* pass
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from modules.cdio import componentry_catalog as cc  # noqa: E402
from modules.cdio import motion_patterns as mp  # noqa: E402

POPULATION_FLOOR = 54  # sealed 2026-10-13 at upstream b602c28
ADVISORY_MAX_CHARS = 2500  # the pre-absorption line for a landing page was ~1.1 KB

HIGH = {"expressiveness": "high", "motion_budget": "high", "reduced_motion": "equivalent"}
MOD_LOW = {"expressiveness": "moderate", "motion_budget": "low", "reduced_motion": "equivalent"}
NO_RM = {"expressiveness": "high", "motion_budget": "high", "reduced_motion": "absent"}
NONE = {"expressiveness": "none", "motion_budget": "none", "reduced_motion": "equivalent"}
LANDING = "app/landing/hero.tsx"

PASSES = 0
FAILS = 0


def _ok(gate, evidence):
    global PASSES
    PASSES += 1
    print(f"  [PASS] {gate}: {evidence}")


def _fail(gate, diagnostic):
    global FAILS
    FAILS += 1
    print(f"  [FAIL] {gate}: {diagnostic}")


def check(gate, cond, evidence, diagnostic):
    (_ok if cond else _fail)(gate, evidence if cond else diagnostic)


def cmp_ids(r):
    return sorted(p["id"] for p in r.get("patterns", []) if p["id"].startswith(cc.ID_PREFIX))


def main() -> int:
    catalog, errors = cc.build_catalog()
    check("V-CMP-BUILDS", catalog is not None and not errors,
          "catalogue builds with 0 errors", f"errors={errors}")
    if catalog is None:
        print(f"CMP_PASS={PASSES}/{PASSES + FAILS}")
        return 1
    comps = catalog["components"]
    by_slug = {c["slug"]: c for c in comps}

    # -- population: discovered from upstream's registry, floored, cross-counted
    with open(cc.REGISTRY, encoding="utf-8-sig") as fh:
        reg_text = fh.read()
    slug_fields = len(re.findall(r'^\s+slug:\s*"', reg_text, re.MULTILINE))
    check("V-CMP-POPULATION", len(comps) == slug_fields and len(comps) >= POPULATION_FLOOR,
          f"{len(comps)} components == {slug_fields} registry slug fields >= {POPULATION_FLOOR}",
          f"{len(comps)} components, {slug_fields} slug fields, floor {POPULATION_FLOOR}")

    # -- the parser: both key shapes, and an unknown shape is an error, not a skip
    sample = ('export const components = {\n'
              '  "a-b": {\n    title: "A",\n    description: "d",\n'
              '    category: "Components",\n    slug: "a-b",\n  },\n'
              '  bare: {\n    title: "B",\n    description:\n      "d",\n'
              '    category: "Components",\n    slug: "bare",\n  },\n')
    two, e2 = cc.parse_registry(sample)
    odd = sample + "  'single': {\n    title: \"C\",\n    slug: \"single\",\n  },\n"
    _, e3 = cc.parse_registry(odd)
    check("V-CMP-PARSER-SHAPES", [c["slug"] for c in two] == ["a-b", "bare"] and not e2 and e3,
          "quoted and bare keys parse; an unknown shape raises a count error",
          f"parsed={[c['slug'] for c in two]} e2={e2} unknown-shape errors={e3}")

    # -- vendored source is pinned: sha in catalog.json == file on disk
    try:
        with open(cc.CATALOG_JSON, encoding="utf-8") as fh:
            on_disk = json.load(fh)
    except (OSError, ValueError) as exc:
        on_disk = {"components": [], "commit": None, "_err": str(exc)}
    bad = []
    for c in on_disk["components"]:
        path = os.path.join(ROOT, c["source"])
        try:
            with open(path, "rb") as fh:
                if hashlib.sha256(fh.read()).hexdigest() != c["sha256"]:
                    bad.append(c["slug"])
        except OSError:
            bad.append(c["slug"])
    with open(os.path.join(cc.VENDOR_DIR, "LICENSE"), encoding="utf-8") as fh:
        mit = fh.read().startswith("MIT License")
    with open(os.path.join(cc.VENDOR_DIR, "NOTICE.md"), encoding="utf-8") as fh:
        notice_pin = cc.UPSTREAM_COMMIT in fh.read()
    check("V-CMP-VENDOR-PIN",
          len(on_disk["components"]) == len(comps) and not bad and mit and notice_pin
          and on_disk.get("commit") == cc.UPSTREAM_COMMIT,
          f"{len(comps)} sources hash-match catalog.json; MIT licence; NOTICE pins "
          f"{cc.UPSTREAM_COMMIT[:7]}",
          f"mismatch={bad} mit={mit} notice_pin={notice_pin} commit={on_disk.get('commit')}")

    drift = cc.drift(catalog)
    check("V-CMP-NO-DRIFT", not drift, "catalog.json and 54 entries equal scanner output",
          f"drifted: {drift[:6]} (run python -m modules.cdio.componentry_catalog build)")

    # -- every cited line really carries its signal (the instrument, checked per claim)
    miss = []
    for c in comps:
        with open(os.path.join(ROOT, c["source"]), encoding="utf-8-sig") as fh:
            lines = fh.read().splitlines()
        for sig, line in c["signals"].items():
            if line and not cc._SIGNAL_RE[sig].search(lines[line - 1]):
                miss.append(f"{c['slug']}:{sig}@{line}")
    n_claims = sum(1 for c in comps for v in c["signals"].values() if v)
    check("V-CMP-CITED-LINES", not miss and n_claims > 0,
          f"{n_claims} cited lines all carry their signal", f"miss={miss[:6]}")

    # -- the scanner discriminates on real files, from both poles
    rm_yes = by_slug["ascii-effect"]["signals"]["reduced_motion"]
    rm_no = by_slug["circuit-board"]["signals"]["reduced_motion"]  # matchMedia(color-scheme)
    check("V-CMP-RM-POLES", bool(rm_yes) and rm_no is None,
          f"ascii-effect reads reduced motion (line {rm_yes}); circuit-board's "
          "matchMedia(color-scheme) is not credited",
          f"ascii-effect={rm_yes} circuit-board={rm_no}")
    ktr = by_slug["kinetic-text-reveal"]
    canvas = by_slug["matrix-rain"]
    check("V-CMP-LOOP-POLES",
          ktr["signals"]["raf"] and not ktr["signals"]["infinite"]
          and not any("frame" in r for r in ktr["derived"]["raised"])
          and canvas["derived"]["min_expressiveness"] == "high"
          and canvas["derived"]["min_motion_budget"] == "high",
          "one-shot rAF on the DOM raises nothing; per-frame canvas without pause -> high/high",
          f"ktr={ktr['signals']['raf']},{ktr['signals']['infinite']},{ktr['derived']['raised']} "
          f"matrix={canvas['derived']['min_expressiveness']}/{canvas['derived']['min_motion_budget']}")

    # -- derivation only narrows
    widened = [c["slug"] for c in comps
               if cc.EXPRESSIVENESS.index(c["derived"]["min_expressiveness"])
               < cc.EXPRESSIVENESS.index(cc.CATEGORY_BASE[c["category"]][1])
               or cc.MOTION.index(c["derived"]["min_motion_budget"])
               < cc.MOTION.index(cc.CATEGORY_BASE[c["category"]][2])]
    check("V-CMP-ONLY-NARROWS", not widened, "no component below its category minimum",
          f"widened={widened}")

    # -- the live resolver serves and withholds, from both poles
    entries, corpus_errors = mp.load_corpus()
    n_cmp = sum(1 for e in entries if e["id"].startswith(cc.ID_PREFIX))
    check("V-CMP-RESOLVER-LOADS", not corpus_errors and n_cmp == len(comps),
          f"resolver discovers {n_cmp} componentry entries, 0 corpus errors",
          f"n={n_cmp} errors={corpus_errors[:4]}")
    hi = mp.resolve(HIGH, LANDING)
    check("V-CMP-SERVES", len(cmp_ids(hi)) == len(comps),
          f"landing + high/high contract receives all {len(comps)}",
          f"received {len(cmp_ids(hi))} ({hi.get('state')}: {hi.get('reason')})")
    lo = mp.resolve(MOD_LOW, LANDING)
    want_lo = sorted(cc.ID_PREFIX + c["slug"] for c in comps
                     if c["derived"]["min_expressiveness"] in ("restrained", "moderate")
                     and c["derived"]["min_motion_budget"] == "low")
    check("V-CMP-CONTRACT-WITHHOLDS", cmp_ids(lo) == want_lo and 0 < len(want_lo) < len(comps),
          f"moderate/low receives exactly the {len(want_lo)} low-cost entries",
          f"got {len(cmp_ids(lo))}, want {len(want_lo)}")
    co = mp.resolve(HIGH, "app/checkout/page.tsx")
    check("V-CMP-SURFACE-WITHHOLDS", not cmp_ids(co),
          "checkout under a high/high contract receives none", f"got {cmp_ids(co)[:5]}")
    rm = mp.resolve(NO_RM, LANDING)
    check("V-CMP-RM-FLOOR", not cmp_ids(rm),
          "a contract without reduced_motion: equivalent receives none",
          f"got {len(cmp_ids(rm))}")
    ab = mp.resolve(NONE, LANDING)
    check("V-CMP-ABSTAIN", ab["state"] == "abstain" and not ab["patterns"],
          "expressiveness: none abstains", f"state={ab['state']}")

    # -- the advisory line summarises the family; a mutant without the summary goes red
    def bounded(line):
        return (line and cc.ID_PREFIX + "aurora-flow" not in line
                and f"{len(comps)} {cc.ID_PREFIX}*" in line and "CDIO-11" in line
                and len(line) <= ADVISORY_MAX_CHARS)
    line = mp.advisory_line(hi)
    saved = dict(mp.CATALOG_FAMILIES)
    try:
        mp.CATALOG_FAMILIES.clear()
        mutant_line = mp.advisory_line(hi)
    finally:
        mp.CATALOG_FAMILIES.update(saved)
    check("V-CMP-ADVISORY-BOUNDED", bounded(line) and not bounded(mutant_line),
          f"advisory {len(line)} chars with a family count; the unsummarised mutant "
          f"({len(mutant_line)} chars) fails the same predicate",
          f"line={len(line or '')} chars bounded={bounded(line)} "
          f"mutant_bounded={bounded(mutant_line)}")

    # -- wiring: the dataset is reachable from its routers and registered
    def read(*p):
        try:
            with open(os.path.join(*p), encoding="utf-8") as fh:
                return fh.read()
        except OSError:
            return ""
    core = read(ROOT, "vault", "agents", "cdio-core.md")
    rev = read(ROOT, "vault", "agents", "cdio-reviewer.md")
    kernel = read(ROOT, "vault", "knowledge_base", "cdio", "CDIO-00-design-intelligence-kernel.md")
    suite = read(ROOT, "tools", "test_cdio.py")
    live_home = os.path.join(os.path.expanduser("~"), ".claude", "agents")
    live_ok = all(read(live_home, n) == read(ROOT, "vault", "agents", n)
                  for n in ("cdio-core.md", "cdio-reviewer.md")
                  ) if os.path.isdir(live_home) else True
    wired = {"core": "CDIO-11" in core, "reviewer": "CDIO-11 §8" in rev,
             "kernel": re.search(r"^governs:.*CDIO-11", kernel, re.M) is not None,
             "suite": "EXPECTED_DATASETS = 12" in suite, "live-mirror": live_ok,
             "index-doc": os.path.isfile(os.path.join(ROOT, cc.INDEX_DOC))}
    check("V-CMP-WIRING", all(wired.values()), f"wired: {sorted(wired)}",
          f"missing: {[k for k, v in wired.items() if not v]}")

    print(f"CMP_PASS={PASSES}/{PASSES + FAILS}  threshold={PASSES + FAILS}/{PASSES + FAILS}")
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
