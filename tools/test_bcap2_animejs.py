"""test_bcap2_animejs.py -- BCAP2-04 Anime.js absorption gate (V-AJS-*). Run: python3 tools/test_bcap2_animejs.py ; exit 0 iff all pass.

Poles: the resolver must propose the new VP-AJS patterns on a permissive landing contract and withhold them on
checkout / `none` budgets; a copy of a pattern with the reduced-motion floor removed or the "when NOT to use" section
emptied must be REJECTED by the corpus parser (seeded red); disposition ledger integrity (closed vocabulary, owner paths
exist, pin matches NOTICE); motion prompts route to the frontend domain without naming a library, and unrelated prompts
do not; no Anime.js runtime dependency was added to any package manifest.
Scope honesty: real-browser behaviour (reduced-motion exercised, timeline cancel, unmount cleanup) is NOT verified here.
"""
from __future__ import annotations

import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modules.cdio import motion_patterns as mp  # noqa: E402
from modules.skill_router.intent_classifier import classify_intent  # noqa: E402
from modules.skill_router.skill_index import build_index  # noqa: E402

P = F = 0
PIN = "01b81be1df6843ccfe0a71c0699a746bf740dd77"
NEW_IDS = {"VP-AJS-001", "VP-AJS-002", "VP-AJS-003"}
VOCAB = {"ALREADY OWNED", "EXTEND", "IMPL-PRIMITIVE", "HEURISTIC", "UPSTREAM-ONLY", "REJECT", "UNVERIFIED"}
HI = {"expressiveness": "high", "motion_budget": "high", "reduced_motion": "equivalent"}
NONE = {"expressiveness": "none", "motion_budget": "none", "reduced_motion": "equivalent"}


def check(name, cond, detail=""):
    global P, F
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}: {detail}")
    if cond:
        P += 1
    else:
        F += 1


def ids(res):
    return {p["id"] for p in res["patterns"]}


def test_corpus():
    print("test_corpus")
    entries, errs = mp.load_corpus()
    found = {e["id"] for e in entries}
    check("V-AJS-CORPUS-CLEAN", not errs, f"{len(entries)} entries, errors={errs}")
    check("V-AJS-ENTRIES-DISCOVERED", NEW_IDS <= found, f"missing={sorted(NEW_IDS - found)}")
    for e in entries:
        if e["id"] in NEW_IDS:
            check(f"V-AJS-EVIDENCE-HONEST[{e['id']}]", e["evidence_level"] == "research" and "01b81be1" in e["provenance"],
                  f"{e['evidence_level']} / {e['provenance'][:40]}")


def test_resolver_poles():
    print("test_resolver_poles")
    hero = mp.resolve(HI, "app/landing/hero.tsx")
    check("V-AJS-POS-LANDING", NEW_IDS <= ids(hero), f"got={sorted(NEW_IDS & ids(hero))}")
    solo = mp.resolve(HI, "app/hero.tsx")
    check("V-AJS-DISCRIMINATES-HERO-ONLY", NEW_IDS & ids(solo) == {"VP-AJS-001", "VP-AJS-003"},
          f"hero-only surface must not get draggable; got={sorted(NEW_IDS & ids(solo))}")
    tour = mp.resolve(HI, "app/product-tour/page.tsx")
    check("V-AJS-POS-DRAGGABLE-ON-TOUR", "VP-AJS-002" in ids(tour), "draggable allowed on a product tour")
    pay = mp.resolve(HI, "app/onboarding/payment/page.tsx")
    check("V-AJS-NEG-CHECKOUT", not (NEW_IDS & ids(pay)), f"leaked={sorted(NEW_IDS & ids(pay))}")
    dash = mp.resolve(HI, "app/dashboard/orders.tsx")
    check("V-AJS-NEG-DASHBOARD", not (NEW_IDS & ids(dash)), f"leaked={sorted(NEW_IDS & ids(dash))}")
    none = mp.resolve(NONE, "app/landing/hero.tsx")
    check("V-AJS-ABSTAIN-NONE", none["state"] == "abstain" and not none["patterns"], none["state"])
    lo = mp.resolve({"expressiveness": "restrained", "motion_budget": "low", "reduced_motion": "equivalent"}, "app/landing/hero.tsx")
    check("V-AJS-NEG-LOW-BUDGET", not (NEW_IDS & ids(lo)), "low budget never receives them")


def _seeded(mutator):
    """Copy the corpus pattern into a temp corpus after mutating it; return (entries, errors)."""
    src = ROOT / "vault/knowledge_base/visual-patterns/staggered-timeline-choreography.md"
    d = Path(tempfile.mkdtemp(prefix="ajs_"))
    try:
        (d / "x.md").write_text(mutator(src.read_text(encoding="utf-8")), encoding="utf-8")
        return mp.load_corpus(str(d))
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_seeded_red():
    print("test_seeded_red")
    e, errs = _seeded(lambda t: t)
    check("V-AJS-CLEAN-TWIN-PASSES", len(e) == 1 and not errs, f"entries={len(e)} errs={errs}")
    e, errs = _seeded(lambda t: t.replace("requires_reduced_motion: equivalent", "requires_reduced_motion: none"))
    check("V-AJS-RED-NO-REDUCED-MOTION-FLOOR", not e and any("reduced_motion" in x for x in errs), str(errs))
    e, errs = _seeded(lambda t: re.sub(r"(## Cuando NO usar\n).*?(?=\n## )", r"\1\n- x\n", t, flags=re.S))
    check("V-AJS-RED-EMPTY-WHEN-NOT", not e and any("Cuando NO usar" in x for x in errs), str(errs))
    e, errs = _seeded(lambda t: t.replace("evidence_level: research", "evidence_level: certified"))
    check("V-AJS-RED-BAD-EVIDENCE-LEVEL", not e and bool(errs), str(errs))
    e, errs = _seeded(lambda t: t.replace("[landing, hero, product-tour, onboarding]", "[landing, nonsense]", 1))
    check("V-AJS-RED-UNKNOWN-SURFACE", not e and bool(errs), str(errs))


def unverified_rows(rows):
    return [r[0] for r in rows if r[2] == "UNVERIFIED"]


def test_ledger():
    print("test_ledger")
    d = ROOT / "vault/programs/bcap-2/animejs"
    text = (d / "DISPOSITIONS.md").read_text(encoding="utf-8")
    notice = (d / "NOTICE.md").read_text(encoding="utf-8")
    rows = [[c.strip() for c in ln.strip("|").split("|")] for ln in text.splitlines()
            if ln.startswith("|") and not ln.startswith("|---") and not ln.startswith("| capability")]
    check("V-AJS-LEDGER-ROWS", len(rows) >= 20 and all(len(r) == 5 for r in rows), f"{len(rows)} rows")
    check("V-AJS-LEDGER-VOCAB", all(r[2] in VOCAB for r in rows), str(sorted({r[2] for r in rows} - VOCAB)))
    check("V-AJS-LEDGER-NO-UNVERIFIED-LEFT", not unverified_rows(rows), "every capability row was read at the pin")
    check("V-AJS-LEDGER-UNVERIFIED-POLE", unverified_rows([["a", "p", "UNVERIFIED"], ["b", "p", "EXTEND"]]) == ["a"], "pole: the predicate sees an UNVERIFIED row")
    check("V-AJS-LEDGER-UNIQUE", len({r[0] for r in rows}) == len(rows), "unique capability names")
    missing = [r[3] for r in rows if not (ROOT / r[3]).exists()]
    check("V-AJS-LEDGER-OWNERS-EXIST", not missing, f"missing={missing}")
    inv = ["Animation", "Timer", "Timeline", "Stagger", "Animatable", "Draggable", "Scope", "Scroll", "SVG line", "SVG morph",
           "SVG motion", "WAAPI", "Easings", "Reduced-motion"]
    gaps = [k for k in inv if not any(k.lower() in r[0].lower() for r in rows)]
    check("V-AJS-LEDGER-COVERS-BACKLOG-INVENTORY", not gaps, f"uncovered={gaps}")
    extend_targets = [r[3] for r in rows if r[2] == "EXTEND" and "visual-patterns" in r[3]]
    check("V-AJS-EXTEND-HAS-PATTERN", {Path(t).name for t in extend_targets} >= {
        "staggered-timeline-choreography.md", "draggable-snap-with-alternative.md", "svg-shape-morph.md"}, str(len(extend_targets)))
    check("V-AJS-PIN-LICENCE", PIN in text and PIN in notice and "MIT" in notice and "Julian Garnier" in notice, "pin+MIT+author")
    doc = (ROOT / "vault/knowledge_base/visual-patterns/motion-library-selection.md").read_text(encoding="utf-8")
    check("V-AJS-DOCTRINE-LADDER", "No animation" in doc and "Lifecycle contract" in doc and "no `prefers-reduced-motion`" in doc,
          "ladder + lifecycle + upstream-fact present")


def test_routing():
    print("test_routing")
    idx = build_index()
    pos = ["animate this hero", "create a scroll-driven product story", "draw this SVG path",
           "build a draggable interaction", "choreograph these states"]
    neg = ["fix the database migration", "write a unit test for the parser", "fix a typo in the readme"]
    for q in pos:
        r = classify_intent(q, idx)
        check(f"V-AJS-ROUTE[{q[:30]}]", r.domain == "frontend", r.domain)
    for q in neg:
        r = classify_intent(q, idx)
        check(f"V-AJS-ROUTE-NEG[{q[:30]}]", r.domain != "frontend", r.domain)
    check("V-AJS-ROUTE-DIAGNOSE-INTACT", classify_intent("the login keeps failing", idx).domain == "diagnose", "diagnose")


def test_no_dependency():
    print("test_no_dependency")
    hits = []
    for pj in list(ROOT.glob("package.json")) + list(ROOT.glob("*/package.json")):
        if "animejs" in pj.read_text(encoding="utf-8", errors="ignore").lower():
            hits.append(str(pj.relative_to(ROOT)))
    check("V-AJS-NO-RUNTIME-DEPENDENCY", not hits, f"manifests naming animejs={hits}")


if __name__ == "__main__":
    for t in (test_corpus, test_resolver_poles, test_seeded_red, test_ledger, test_routing, test_no_dependency):
        t()
    print(f"\nAnime.js gate: {P} PASS / {F} FAIL")
    sys.exit(0 if F == 0 else 1)
