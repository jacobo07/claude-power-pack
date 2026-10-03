"""V-UCEP-* -- the constitutive-baseline ratchet cannot be talked past.

UCEP-01 closes three escape routes found by the CBR gap analysis
(wiki/syntheses/cbr-gap-analysis.md, probe wiki/tools/cbr_probe.py):

  H1  any non-empty string counts as an "authority", and the API (`revert`,
      `promote`) accepts one, so "x" withdraws or adds a rule on the record.
  H2  `ratchet.diff` never reads `why`, `origin`, `class` or `propagation_scope`,
      so a generation can rewrite a rule's justification, provenance, class or
      scope with no record at all.
  H3b `ChainReport.ok` ignores `unanchored`, so a child generation with its
      parent anchor removed (after hollowing the parent) reads ok.

Each ATTACK gate is paired with a CONTROL in which the same change, made
properly, is accepted. A refusal gate without a control cannot tell "refuses
the attack" from "refuses everything".

Subject. Every gate runs on a B0-ONLY copy of the real web_surface family,
under a temp root. The real family now has a B1 as well; copying the whole
directory (as the original probe does) makes the next generation drop B1's two
additions, which turns every attack red for the wrong reason. This file never
reads or copies the real second generation. All writes happen under
tempfile.mkdtemp; nothing under vault/tower/baselines is written.

RED then GREEN. Against the ratchet as it stood before UCEP-01 the seven attack
gates FAIL (the attack returns ok=True, so the hole is real) and the five
controls PASS: UCEP_BASELINE_INTEGRITY_PASS=5/12. Plan 01-03 closes the holes
and every gate then passes. The predicates below already state the fixed
behaviour. A diff kind is written as a string literal and every report field is
read with a default, so the RED run fails on predicates and never on an
AttributeError.

Run: python tools/test_ucep_baseline_integrity.py     (exit 0 = all gates pass)
"""
from __future__ import annotations

import copy
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
_PP_ROOT = os.path.normpath(os.path.join(_HERE, ".."))
for p in (_PP_ROOT, _HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

from modules.tower import baselines as bl  # noqa: E402
from modules.tower import ratchet as rt  # noqa: E402

FAMILY = "web_surface"

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


def _dict(rep):
    """The chain report as a plain dict, for diagnostics."""
    return rep.as_dict() if hasattr(rep, "as_dict") else repr(rep)


def _ok(rep):
    return getattr(rep, "ok", None)


def _kinds(rep):
    return sorted((r["id"], r["kind"]) for r in getattr(rep, "regressions", []))


def _raises(fn):
    """(refused?, message): did the call raise the ratchet's refusal?"""
    try:
        fn()
    except rt.RatchetRefusal as exc:
        return True, str(exc)
    return False, ""


def _flip_class(value):
    return "C" if value == "D" else "D"


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="ucep_bi_")
    saved_env = {k: os.environ.get(k) for k in ("HOME", "USERPROFILE")}
    try:
        # Hermetic HOME (pattern of tools/test_family_injection.py): nothing here
        # may reach a ledger under the real home.
        home = os.path.join(tmp, "home")
        os.makedirs(home)
        os.environ["HOME"] = home
        os.environ["USERPROFILE"] = home
        if Path.home() != Path(home):
            raise RuntimeError("hermetic HOME did not take: %s" % Path.home())

        print("V-UCEP baseline integrity gates (B0-only copy of %s)" % FAMILY)
        source_b0 = os.path.join(bl.BASELINES_DIR, FAMILY, "B0.json")

        def b0_copy(label):
            """A temp root holding ONLY the real B0 of the family."""
            root = os.path.join(tmp, label)
            os.makedirs(os.path.join(root, FAMILY))
            shutil.copyfile(source_b0, os.path.join(root, FAMILY, "B0.json"))
            return root

        def child(root, mutate=None, changes=None):
            """Write the next generation from the latest, after `mutate(entries)`."""
            entries = copy.deepcopy(bl.latest(FAMILY, root)["entries"])
            if mutate:
                mutate(entries)
            return bl.write_generation(FAMILY, entries, "ucep attack", root=root,
                                       extra=({"changes": changes} if changes else None))

        b0_entries = bl.latest(FAMILY, b0_copy("probe"))["entries"]
        id0, id1 = b0_entries[0]["id"], b0_entries[1]["id"]
        if len(b0_entries) < 4:
            raise RuntimeError("source family too small for the hollowing attack")

        # --- H1: authority is any non-empty string -------------------------
        def drop_first(entries):
            del entries[0]

        root = b0_copy("h1-raw")
        child(root, drop_first, {id0: {"kind": "WITHDRAWN", "reason": "x",
                                       "authority": "x"}})
        rep = rt.verify_chain(FAMILY, root=root)
        _check("V-UCEP-H1-RAW", _ok(rep) is False,
               "a withdrawal recorded with authority 'x' is a regression",
               "H1 attack accepted: %s" % _dict(rep))

        root = b0_copy("h1-raw-control")
        child(root, drop_first, {id0: {"kind": "WITHDRAWN",
                                       "reason": "withdrawn by attack-test control",
                                       "authority": "Owner"}})
        rep = rt.verify_chain(FAMILY, root=root)
        _check("V-UCEP-H1-RAW-CONTROL", _ok(rep) is True,
               "the same withdrawal with reason + authority 'Owner' is clean",
               _dict(rep))

        root = b0_copy("h1-api")
        new_entry = {"id": "ucep-probe-new", "requirement": "probe rule must hold",
                     "why": "attack test", "class": "D",
                     "origin": {"file": "nowhere.md", "line": 1}}
        missing = [k for k in bl.REQUIRED if k not in new_entry]
        refused_revert, msg_revert = _raises(lambda: rt.revert(
            FAMILY, id1, reason="retired by attack test", authority="x", root=root))
        refused_promote, msg_promote = _raises(lambda: rt.promote(
            FAMILY, [new_entry], reason="added by attack test", authority="x",
            root=root))
        gens = bl.generations(FAMILY, root)
        _check("V-UCEP-H1-API",
               not missing and refused_revert and refused_promote and gens == [0],
               "revert + promote with authority 'x' both refused, no generation",
               "H1 API attack accepted: revert refused=%s promote refused=%s "
               "generations=%s (written: %s) missing_keys=%s"
               % (refused_revert, refused_promote, gens,
                  ["B%d" % g for g in gens[1:]], missing))

        root = b0_copy("h1-api-control")
        refused_ctl, msg_ctl = _raises(lambda: rt.revert(
            FAMILY, id1, reason="retired by attack-test control",
            authority="Owner (approved by attack-test control)", root=root))
        rep = rt.verify_chain(FAMILY, root=root)
        gens = bl.generations(FAMILY, root)
        _check("V-UCEP-H1-API-CONTROL",
               not refused_ctl and gens == [0, 1] and _ok(rep) is True,
               "revert with authority 'Owner (...)' writes B1 and the chain is ok",
               "refused=%s (%s) generations=%s %s"
               % (refused_ctl, msg_ctl, gens, _dict(rep)))

        # --- H2: diff is blind to why / origin / class / propagation_scope ---
        def edit_why(entries):
            entries[0]["why"] = "rewritten by attack test: this rule no longer matters"

        def edit_origin(entries):
            entries[0]["origin"] = {"file": "nowhere.md", "line": 1}

        def edit_class(entries):
            entries[0]["class"] = _flip_class(entries[0].get("class"))

        def edit_scope(entries):
            entries[0]["propagation_scope"] = "universal"

        for gate, edit, kind in (
                ("V-UCEP-H2-WHY", edit_why, "WHY_CHANGED"),
                ("V-UCEP-H2-ORIGIN", edit_origin, "REANCHORED"),
                ("V-UCEP-H2-CLASS", edit_class, "CLASS_CHANGED"),
                ("V-UCEP-H2-SCOPE", edit_scope, "SCOPE_CHANGED")):
            root = b0_copy(gate.lower())
            child(root, edit)
            rep = rt.verify_chain(FAMILY, root=root)
            _check(gate, _ok(rep) is False and (id0, kind) in _kinds(rep),
                   "an unrecorded edit is a %s regression" % kind,
                   "H2 attack accepted (want %s): %s" % (kind, _dict(rep)))

        def edit_all(entries):
            edit_why(entries)
            edit_origin(entries)
            edit_class(entries)
            edit_scope(entries)

        root = b0_copy("h2-control")
        child(root, edit_all, {id0: {
            "kind": ["WHY_CHANGED", "REANCHORED", "CLASS_CHANGED", "SCOPE_CHANGED"],
            "reason": "recorded rewrite control", "authority": "Owner"}})
        rep = rt.verify_chain(FAMILY, root=root)
        _check("V-UCEP-H2-CONTROL", _ok(rep) is True,
               "the same four edits recorded with reason + authority are clean",
               _dict(rep))

        # --- H3b: an unanchored child must not be ok -----------------------
        def hollow(root, keep_anchor):
            """Keep 3 entries in BOTH generations; optionally drop B1's anchor."""
            child(root)                                   # B1 identical to B0, anchored
            for name in ("B0.json", "B1.json"):
                path = os.path.join(root, FAMILY, name)
                with open(path, "r", encoding="utf-8") as fh:
                    doc = json.load(fh)
                doc["entries"] = doc["entries"][:3]
                if name == "B1.json" and not keep_anchor:
                    doc["parent_sha256"] = None
                with open(path, "w", encoding="utf-8", newline="\n") as fh:
                    json.dump(doc, fh, indent=2, ensure_ascii=False)
                    fh.write("\n")

        root = b0_copy("h3b")
        hollow(root, keep_anchor=False)
        rep = rt.verify_chain(FAMILY, root=root)
        _check("V-UCEP-H3B",
               _ok(rep) is False and getattr(rep, "unanchored", None) == [1],
               "a hollowed chain with B1's anchor removed is not ok (unanchored=[1])",
               "H3b attack accepted: %s" % _dict(rep))

        root = b0_copy("h3b-control")
        hollow(root, keep_anchor=True)
        rep = rt.verify_chain(FAMILY, root=root)
        _check("V-UCEP-H3B-CONTROL-TAMPER",
               _ok(rep) is False and getattr(rep, "tampered", None) == [1],
               "the same hollowing with the anchor intact reads TAMPERED at B1",
               _dict(rep))

        # --- control: ok is not "refuse everything" -------------------------
        root = b0_copy("clean")
        child(root)
        rep = rt.verify_chain(FAMILY, root=root)
        _check("V-UCEP-CLEAN-CONTROL",
               _ok(rep) is True and not getattr(rep, "regressions", None)
               and not getattr(rep, "unanchored", None),
               "an anchored B1 identical to B0 is clean; absent scope is not churn",
               _dict(rep))

        print()
        print("UCEP_BASELINE_INTEGRITY_PASS=%d/%d  threshold=%d/%d"
              % (_PASS, _PASS + _FAIL, 12, 12))
        return 0 if _FAIL == 0 else 1
    finally:
        for k, v in saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
