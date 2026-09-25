"""V-BGEN-* -- baseline generations are immutable and every citation is re-read.

Hermetic: a temp root for generations and a temp source file for citations.

Run: python tools/test_baseline_generations.py     (exit 0 = all gates pass)
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_PP_ROOT = os.path.normpath(os.path.join(_HERE, ".."))
for p in (_PP_ROOT, _HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

from modules.tower import baselines as bl  # noqa: E402

_PASS = 0
_FAIL = 0


def _check(gate, cond, evidence, diagnostic):
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print("  PASS %-38s %s" % (gate, evidence))
    else:
        _FAIL += 1
        print("  FAIL %-38s %s" % (gate, diagnostic))


def _entry(src, line, req="Deploy returns HTTP 200 on the real domain before done",
           why="a build that compiles is not a site that serves"):
    return {"id": "web-http200", "requirement": req, "why": why, "class": "D",
            "origin": {"file": src, "line": line}}


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="bgen_gate_")
    try:
        print("V-BGEN gates")
        src = os.path.join(tmp, "GOV.md")
        with open(src, "w", encoding="utf-8") as fh:
            fh.write("# Deploy\n\nintro\n\nDONE means HTTP 200 on the real domain, "
                     "never a build that compiles.\n\nunrelated closing words here\n")

        _check("V-BGEN-VERIFIED", bl.verify_origin(_entry(src, 5)) == bl.VERIFIED,
               "cited line shares the requirement's vocabulary",
               "got %s" % bl.verify_origin(_entry(src, 5)))
        weak = _entry(src, 1, req="Kittens purr loudly", why="zebra patterns vary")
        _check("V-BGEN-WEAK", bl.verify_origin(weak, window=0) == bl.WEAK,
               "a line that says something else is WEAK, not VERIFIED",
               "got %s" % bl.verify_origin(weak, window=0))
        _check("V-BGEN-LINE-MISSING", bl.verify_origin(_entry(src, 999)) == bl.LINE_MISSING,
               "line past EOF", "got %s" % bl.verify_origin(_entry(src, 999)))
        _check("V-BGEN-FILE-MISSING",
               bl.verify_origin(_entry(os.path.join(tmp, "nope.md"), 1)) == bl.FILE_MISSING,
               "absent file", "wrong verdict for absent file")
        _check("V-BGEN-MALFORMED", bl.verify_origin({"id": "x"}) == bl.MALFORMED,
               "missing fields", "a malformed entry verified")

        root = os.path.join(tmp, "baselines")
        p0 = bl.write_generation("web_surface", [_entry(src, 5)], "b0", root=root)
        e2 = dict(_entry(src, 5), id="web-two", status="reverted")
        p1 = bl.write_generation("web_surface", [_entry(src, 5), e2], "b1", root=root)
        g1 = bl.load_generation("web_surface", 1, root=root)
        _check("V-BGEN-APPEND-ONLY",
               bl.generations("web_surface", root=root) == [0, 1]
               and g1["parent"] == 0 and os.path.exists(p0),
               "B1 written beside B0, parent=0, B0 untouched",
               "generations=%s parent=%s" % (bl.generations("web_surface", root=root),
                                             g1.get("parent")))
        _check("V-BGEN-REVERTED-INACTIVE",
               [e["id"] for e in bl.active_entries("web_surface", root=root)]
               == ["web-http200"],
               "a reverted entry is not active",
               "active=%s" % bl.active_entries("web_surface", root=root))
        raised = False
        orig = bl.generations
        bl.generations = lambda f, r=None: [0]       # force a collision on B1
        try:
            bl.write_generation("web_surface", [], "collide", root=root)
        except FileExistsError:
            raised = True
        finally:
            bl.generations = orig
        with open(p1, encoding="utf-8") as fh:
            intact = len(json.load(fh)["entries"]) == 2
        _check("V-BGEN-NO-OVERWRITE", raised and intact,
               "an existing generation is never rewritten",
               "raised=%s intact=%s" % (raised, intact))

        # --- two writers race for the same B<n>: exactly one may publish ----
        # Positioned, not hoped for: both writers are held on a barrier AFTER
        # they have read the generation list and BEFORE either publishes, so
        # the window between "B<n> does not exist" and the write is occupied
        # by the other writer on every run.
        import threading
        race_root = os.path.join(tmp, "race")
        bl.write_generation("race_family", [], "b0", root=race_root)
        barrier = threading.Barrier(2, timeout=10)
        real_dump = bl.json.dump

        def held_dump(*a, **k):
            barrier.wait()
            return real_dump(*a, **k)

        outcomes = {}

        def writer(tag):
            try:
                bl.write_generation("race_family", [{"id": tag}], tag, root=race_root)
                outcomes[tag] = "published"
            except FileExistsError:
                outcomes[tag] = "refused"
            except Exception as exc:  # noqa: BLE001 -- recorded, asserted below
                outcomes[tag] = "error:%s" % type(exc).__name__

        bl.json.dump = held_dump
        try:
            threads = [threading.Thread(target=writer, args=(t,)) for t in ("A", "B")]
            for t in threads:
                t.start()
            for t in threads:
                t.join(15)
        finally:
            bl.json.dump = real_dump
        published = sorted(k for k, v in outcomes.items() if v == "published")
        refused = sorted(k for k, v in outcomes.items() if v == "refused")
        survivor = bl.load_generation("race_family", 1, root=race_root)
        leftovers = [f for f in os.listdir(os.path.join(race_root, "race_family"))
                     if not bl._GEN.match(f)]
        _check("V-BGEN-RACE-ONE-WINNER",
               len(published) == 1 and len(refused) == 1
               and survivor["reason"] == published[0]
               and bl.generations("race_family", root=race_root) == [0, 1]
               and not leftovers,
               "one writer published B1, the other was refused, no temp residue",
               "outcomes=%s survivor=%s leftovers=%s"
               % (outcomes, survivor.get("reason"), leftovers))

        # --- quote anchoring: drift is DETECTED, not averaged away ----------
        q = dict(_entry(src, 5))
        q["origin"] = dict(q["origin"], quote="DONE means HTTP 200 on the real domain")
        _check("V-BGEN-QUOTE-VERIFIED", bl.verify_origin(q) == bl.VERIFIED,
               "quote on the cited line", "got %s" % bl.verify_origin(q))
        with open(src, "w", encoding="utf-8") as fh:        # a section lands above
            fh.write("# Deploy\n\nNEW SECTION\nmore\n\nintro\n\nDONE means HTTP 200 on "
                     "the real domain, never a build that compiles.\n")
        _check("V-BGEN-QUOTE-MOVED", bl.verify_origin(q) == bl.MOVED
               and bl.locate_quote(src, q["origin"]["quote"]) == 8,
               "shifted citation -> MOVED, relocated to line 8",
               "got %s" % bl.verify_origin(q))
        # The failure this replaces: without the quote, +-3 shared words PASS it.
        unanchored = dict(q, origin={"file": src, "line": 5})
        _check("V-BGEN-WINDOW-FALLBACK-IS-WEAK",
               bl.verify_origin(unanchored, window=0) != bl.VERIFIED,
               "the exact-line check refuses the shifted line",
               "window=0 still admitted a line that says something else")
        with open(src, "w", encoding="utf-8") as fh:
            fh.write("# Deploy\n\nthe rule was removed\n")
        _check("V-BGEN-QUOTE-MISSING", bl.verify_origin(q) == bl.QUOTE_MISSING,
               "deleted governance -> QUOTE_MISSING", "got %s" % bl.verify_origin(q))

        # --- build-b0 itself: strict admission + quote anchoring ----------
        import family_baseline as fb
        gov = os.path.join(tmp, "GOV2.md")
        with open(gov, "w", encoding="utf-8") as fh:
            fh.write("# Floors\n\nDeclare the experience contract before building.\n"
                     "Reduced motion equivalence and blocking animation are floors.\n")
        cand = os.path.join(tmp, "cand.jsonl")
        good = {"id": "f-floors", "class": "D", "requirement":
                "Reduced motion equivalence and blocking animation are floors",
                "why": "floors are not arbitrable", "origin": {"file": gov, "line": 4}}
        shifted = {"id": "f-shifted", "class": "D", "requirement":
                   "Reduced motion equivalence and blocking animation are floors",
                   "why": "floors are not arbitrable", "origin": {"file": gov, "line": 3}}
        with open(cand, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(good) + "\n" + json.dumps(shifted) + "\n")
        saved_dir = bl.BASELINES_DIR
        bl.BASELINES_DIR = os.path.join(tmp, "b0root")
        try:
            rc = fb.build_b0("synthetic", cand)
            g0 = bl.latest("synthetic")
        finally:
            bl.BASELINES_DIR = saved_dir
        ids = [e["id"] for e in (g0 or {}).get("entries", [])]
        _check("V-BGEN-BUILD-B0-STRICT", rc == 0 and ids == ["f-floors"],
               "the line-shifted candidate is dropped, the exact one kept",
               "rc=%s kept=%s" % (rc, ids))
        _check("V-BGEN-BUILD-B0-ANCHORS-QUOTE",
               bool(g0) and "blocking animation" in g0["entries"][0]["origin"].get("quote", ""),
               "B0 stores the literal cited line", "no quote stored: %s" % g0)

        # --- the REAL B0s: every stored citation still stands -------------
        real = {}
        for fam in ("web_surface", "persistent_state", "kobiicraft_mode", "wii_homebrew"):
            for e in bl.active_entries(fam):
                real[e["id"]] = bl.verify_origin(e)
        broken = {k: v for k, v in real.items() if v not in (bl.VERIFIED, bl.MOVED)}
        moved = sorted(k for k, v in real.items() if v == bl.MOVED)
        _check("V-BGEN-REAL-B0-CITATIONS-HOLD", len(real) >= 60 and not broken,
               "%d stored entries hold (%d moved: %s)" % (len(real), len(moved), moved[:3]),
               "population=%d broken=%s" % (len(real), broken))

        print()
        print("BASELINE_GENERATIONS_PASS=%d/%d  threshold=%d/%d"
              % (_PASS, _PASS + _FAIL, _PASS + _FAIL, _PASS + _FAIL))
        return 0 if _FAIL == 0 else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
