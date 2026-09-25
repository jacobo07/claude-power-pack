"""V-TRAT-* -- a constitutive rule can be weakened only on the record.

A generation is immutable, but a NEW generation can say anything. Without a
ratchet, "make the gate pass" is one raw write away: drop the entry, flip it
to reverted, or turn its check into prose, and the next generation is simply
weaker, with nobody having said why. These gates pin that every weakening
between consecutive generations carries a change record with a reason and an
authority, that improvements need none, and that editing an older generation
after the fact is detected.

Hermetic: every generation is written under a temp root.

Run: python tools/test_tower_ratchet.py     (exit 0 = all gates pass)
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
from modules.tower import ratchet as rt  # noqa: E402

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


def _e(ident, check="file:README.md", req=None):
    return {"id": ident, "requirement": req or ("rule %s must hold" % ident),
            "why": "because", "class": "D", "status": "reviewed", "check": check,
            "origin": {"file": "GOV.md", "line": 1}}


def _kinds(report):
    return sorted((r["id"], r["kind"]) for r in report.regressions)


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="trat_")
    try:
        print("V-TRAT gates")
        fam = "fam"

        def fresh(name):
            root = os.path.join(tmp, name)
            bl.write_generation(fam, [_e("a"), _e("b"), _e("c", check="regex:x.py::y")],
                                "b0", root=root)
            return root

        # --- the recorded paths are clean ---------------------------------
        root = fresh("recorded")
        rt.revert(fam, "a", reason="superseded by b", authority="Owner", root=root)
        rt.promote(fam, [_e("d")], reason="new rule", authority="Owner", root=root)
        rep = rt.verify_chain(fam, root=root)
        _check("V-TRAT-RECORDED-CLEAN", rep.ok and not rep.regressions and not rep.tampered,
               "revert + promote through the API leave a clean chain", rep.as_dict())
        _check("V-TRAT-REVERT-INACTIVE",
               [e["id"] for e in bl.active_entries(fam, root=root)] == ["b", "c", "d"],
               "the reverted entry is inactive, the promoted one active",
               [e["id"] for e in bl.active_entries(fam, root=root)])

        # --- the API refuses an unrecorded or impossible change -------------
        for label, call in (
                ("empty reason", lambda: rt.revert(fam, "b", reason=" ", authority="Owner",
                                                    root=root)),
                ("empty authority", lambda: rt.revert(fam, "b", reason="x", authority="",
                                                       root=root)),
                ("unknown id", lambda: rt.revert(fam, "zzz", reason="x", authority="Owner",
                                                  root=root)),
                ("already reverted", lambda: rt.revert(fam, "a", reason="x", authority="Owner",
                                                        root=root)),
                ("duplicate promote", lambda: rt.promote(fam, [_e("b")], reason="x",
                                                          authority="Owner", root=root)),
                ("malformed promote", lambda: rt.promote(fam, [{"id": "q"}], reason="x",
                                                          authority="Owner", root=root))):
            before = bl.generations(fam, root=root)
            try:
                call()
                refused = False
            except rt.RatchetRefusal:
                refused = True
            _check("V-TRAT-REFUSE-%s" % label.upper().replace(" ", "-"),
                   refused and bl.generations(fam, root=root) == before,
                   "%s -> refused, no generation written" % label,
                   "refused=%s gens %s -> %s" % (refused, before,
                                                  bl.generations(fam, root=root)))

        # --- raw writes that weaken are regressions -------------------------
        root = fresh("withdrawn")
        bl.write_generation(fam, [_e("b"), _e("c", check="regex:x.py::y")], "drop a",
                            root=root)
        _check("V-TRAT-WITHDRAWN", _kinds(rt.verify_chain(fam, root=root))
               == [("a", rt.WITHDRAWN)], "an entry that vanished unrecorded",
               rt.verify_chain(fam, root=root).as_dict())

        root = fresh("reverted-raw")
        g = bl.latest(fam, root=root)["entries"]
        g[0] = dict(g[0], status="reverted")
        bl.write_generation(fam, g, "flip a", root=root)
        _check("V-TRAT-REVERTED-UNRECORDED", _kinds(rt.verify_chain(fam, root=root))
               == [("a", rt.REVERTED)], "a status flip without a record",
               rt.verify_chain(fam, root=root).as_dict())

        root = fresh("weakened")
        g = bl.latest(fam, root=root)["entries"]
        g[2] = dict(g[2], check="look at the code carefully")
        bl.write_generation(fam, g, "soften c", root=root)
        _check("V-TRAT-WEAKENED", _kinds(rt.verify_chain(fam, root=root))
               == [("c", rt.WEAKENED)], "evaluable -> prose is a weakening",
               rt.verify_chain(fam, root=root).as_dict())

        root = fresh("reworded")
        g = bl.latest(fam, root=root)["entries"]
        g[1] = dict(g[1], requirement="rule b should usually hold")
        bl.write_generation(fam, g, "reword b", root=root)
        _check("V-TRAT-REWORDED", _kinds(rt.verify_chain(fam, root=root))
               == [("b", rt.REWORDED)], "a changed requirement needs a record",
               rt.verify_chain(fam, root=root).as_dict())

        # --- a record makes the same change legitimate ----------------------
        root = fresh("reworded-recorded")
        g = bl.latest(fam, root=root)["entries"]
        g[1] = dict(g[1], requirement="rule b must hold for every surface")
        bl.write_generation(fam, g, "reword b", root=root, extra={"changes": {
            "b": {"kind": rt.REWORDED, "reason": "scope widened", "authority": "Owner"}}})
        _check("V-TRAT-RECORD-LEGITIMISES", rt.verify_chain(fam, root=root).ok,
               "the same rewording with reason + authority is clean",
               rt.verify_chain(fam, root=root).as_dict())

        # --- only ADDING is free ---------------------------------------------
        root = fresh("added")
        g = bl.latest(fam, root=root)["entries"]
        g.append(_e("z", check="just words"))
        bl.write_generation(fam, g, "add z", root=root)
        _check("V-TRAT-ADD-FREE", rt.verify_chain(fam, root=root).ok,
               "an added entry needs no record", rt.verify_chain(fam, root=root).as_dict())

        # --- a rung is a KIND, not a strength: same-rung swaps are changes ---
        # Code review 2026-09-25 (HIGH): regex:x.py::y -> regex:x.py::. stays at
        # rung 0 and passes on any file.
        root = fresh("same-rung")
        g = bl.latest(fam, root=root)["entries"]
        g[2] = dict(g[2], check="regex:x.py::.")
        bl.write_generation(fam, g, "loosen c", root=root)
        _check("V-TRAT-SAME-RUNG-SWAP", _kinds(rt.verify_chain(fam, root=root))
               == [("c", rt.CHECK_CHANGED)],
               "a trivially-passing pattern at the same rung is CHECK_CHANGED",
               rt.verify_chain(fam, root=root).as_dict())
        root2 = os.path.join(tmp, "prose-up")
        bl.write_generation(fam, [_e("p", check="look carefully")], "b0", root=root2)
        bl.write_generation(fam, [_e("p", check="glob:**")], "raise", root=root2)
        _check("V-TRAT-RAISE-NEEDS-RECORD", _kinds(rt.verify_chain(fam, root=root2))
               == [("p", rt.CHECK_CHANGED)],
               "prose -> glob:** is a new green nobody earned; it needs a record",
               rt.verify_chain(fam, root=root2).as_dict())
        root3 = os.path.join(tmp, "prose-up-recorded")
        bl.write_generation(fam, [_e("p", check="look carefully")], "b0", root=root3)
        bl.write_generation(fam, [_e("p", check="file:README.md")], "raise", root=root3,
                            extra={"changes": {"p": {"kind": rt.CHECK_CHANGED,
                                                     "reason": "made runnable",
                                                     "authority": "Owner"}}})
        _check("V-TRAT-RAISE-RECORDED-CLEAN", rt.verify_chain(fam, root=root3).ok,
               "the same raise with reason + authority is clean",
               rt.verify_chain(fam, root=root3).as_dict())

        # --- duplicate ids: refused at write, detected if written anyway ------
        root = os.path.join(tmp, "dupes")
        try:
            bl.write_generation(fam, [_e("n"), _e("n", check="words")], "dup", root=root)
            refused = False
        except ValueError:
            refused = True
        os.makedirs(os.path.join(root, fam), exist_ok=True)
        with open(os.path.join(root, fam, "B0.json"), "w", encoding="utf-8") as fh:
            json.dump({"family": fam, "generation": 0, "entries":
                       [_e("n"), _e("n", check="words")]}, fh)
        _check("V-TRAT-DUPLICATE-ID",
               refused and _kinds(rt.verify_chain(fam, root=root))
               == [("n", rt.DUPLICATE_ID)],
               "write_generation refuses; a hand-written duplicate is DUPLICATE_ID",
               "refused=%s %s" % (refused, rt.verify_chain(fam, root=root).as_dict()))

        # --- an older generation edited after the fact is TAMPERED ----------
        root = fresh("tamper")
        rt.promote(fam, [_e("d")], reason="new", authority="Owner", root=root)
        p0 = os.path.join(root, fam, "B0.json")
        with open(p0, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
        doc["entries"] = doc["entries"][1:]
        with open(p0, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)
        rep = rt.verify_chain(fam, root=root)
        _check("V-TRAT-TAMPERED", not rep.ok and rep.tampered == [1],
               "B0 edited after B1 anchored it -> B1 reports TAMPERED", rep.as_dict())

        # --- the CLI, through its real entry point -------------------------
        import family_baseline as fb
        saved = bl.BASELINES_DIR
        bl.BASELINES_DIR = os.path.join(tmp, "cli")
        try:
            bl.write_generation(fam, [_e("a"), _e("b")], "b0")
            rc_clean = fb.main(["verify", fam])
            rc_no_reason = fb.main(["revert", fam, "a", "--authority", "Owner"])
            rc_revert = fb.main(["revert", fam, "a", "--reason", "gone", "--authority",
                                 "Owner"])
            rc_after = fb.main(["review", fam])
            bl.write_generation(fam, [_e("b", check="words only")], "raw weaken")
            rc_regressed = fb.main(["verify", fam])
        finally:
            bl.BASELINES_DIR = saved
        _check("V-TRAT-CLI",
               (rc_clean, rc_no_reason, rc_revert, rc_after, rc_regressed) == (0, 2, 0, 0, 1),
               "verify 0, revert w/o reason 2, revert 0, review 0, raw weaken -> verify 1",
               (rc_clean, rc_no_reason, rc_revert, rc_after, rc_regressed))

        # --- the real families: chain verified, population floored ---------
        seen = 0
        bad = {}
        for f in ("web_surface", "persistent_state", "kobiicraft_mode", "wii_homebrew"):
            if bl.generations(f):
                seen += 1
                r = rt.verify_chain(f)
                if not r.ok:
                    bad[f] = r.as_dict()
        _check("V-TRAT-REAL-CHAINS", seen == 4 and not bad,
               "4 real families verified clean", "seen=%d bad=%s" % (seen, bad))

        print()
        print("TOWER_RATCHET_PASS=%d/%d  threshold=%d/%d"
              % (_PASS, _PASS + _FAIL, _PASS + _FAIL, _PASS + _FAIL))
        return 0 if _FAIL == 0 else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
