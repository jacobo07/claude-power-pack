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
additions, which turns every attack red for the wrong reason. No attack gate
reads or copies the real second generation; the one exception is the
V-UCEP-ALLOWLIST control, which only READS the real web_surface B1 `promoted_by`
to prove the allowlist accepts the authority form the real family uses. All
writes happen under tempfile.mkdtemp; nothing under vault/tower/baselines is
written.

RED then GREEN. Against the ratchet as it stood before UCEP-01 the seven attack
gates FAIL (the attack returns ok=True, so the hole is real) and the five
controls PASS: UCEP_BASELINE_INTEGRITY_PASS=5/12 (5/13 once V-UCEP-CLI-UNANCHORED
exists). Plan 01-03 closes the holes and every gate then passes (14/14 with
V-UCEP-ALLOWLIST). The predicates below already state the fixed
behaviour. A diff kind is written as a string literal and every report field is
read with a default, so the RED run fails on predicates and never on an
AttributeError.

UCEP-01 plan 01-04 adds `ratchet.reanchor`, the one operation that moves an
ACTIVE entry's provenance (origin) without touching the rule: V-UCEP-REANCHOR-*
gates run on a synthetic family under a temp root (a B0 whose cited file became a
pointer stub, plus a "skill" file holding the same quotes lower down), and
V-UCEP-REAL-REANCHORED reads the real tree to prove the 9 rotted citations were
re-anchored through recorded generations.

UCEP-01 plan 01-05 adds `baselines.discover_subjects` (D-05, audit G9): the real-tree
gates of test_tower_ratchet.py and test_baseline_generations.py enumerate subjects from
disk instead of a hardcoded family tuple. V-UCEP-DISCOVER-* drive it from both poles on
temp roots (nested axis found, empty/missing root gives [], residue ignored, read at call
time) and on the real tree (population floor 4 subjects / 60 active entries).

Run: python tools/test_ucep_baseline_integrity.py     (exit 0 = all gates pass)
"""
from __future__ import annotations

import contextlib
import copy
import io
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

        # --- WR-02: a missing ROOT is not a chain (delete B0 instead of nulling) --
        def _write_doc(path, mutate):
            with open(path, "r", encoding="utf-8") as fh:
                doc = json.load(fh)
            mutate(doc)
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(doc, fh, indent=2, ensure_ascii=False)
                fh.write("\n")

        def regress_kinds(rep):
            return sorted({r["kind"] for r in getattr(rep, "regressions", [])})

        root = b0_copy("wr02-delete-b0")
        child(root)                                       # B1, anchored to B0
        os.remove(os.path.join(root, FAMILY, "B0.json"))  # the root is gone
        _write_doc(os.path.join(root, FAMILY, "B1.json"),
                   lambda d: d.update(entries=d["entries"][:3]))   # hollow B1, keep parent 0
        rep = rt.verify_chain(FAMILY, root=root)
        _check("V-UCEP-H3B-DELETE-B0",
               _ok(rep) is False and "MISSING_ROOT" in regress_kinds(rep)
               and getattr(rep, "generations", None) == [1],
               "B0 deleted + B1 hollowed (generations=[1]) is not ok: MISSING_ROOT",
               "WR-02 attack accepted: %s" % _dict(rep))

        root = b0_copy("wr02-gap")
        child(root)                                       # B1
        child(root)                                       # B2, anchored to B1
        os.remove(os.path.join(root, FAMILY, "B1.json"))  # the middle is gone
        sha_b0 = bl.generation_sha256(FAMILY, 0, root)
        _write_doc(os.path.join(root, FAMILY, "B2.json"),
                   lambda d: d.update(parent_sha256=sha_b0))       # re-anchor B2 on B0
        rep = rt.verify_chain(FAMILY, root=root)
        _check("V-UCEP-H3B-GAP",
               _ok(rep) is False and "GAP" in regress_kinds(rep)
               and getattr(rep, "generations", None) == [0, 2],
               "B1 deleted and B2 re-anchored on B0 (generations=[0, 2]) is not ok: GAP",
               "WR-02 gap attack accepted: %s" % _dict(rep))

        root = b0_copy("wr02-parent-field")
        child(root)
        _write_doc(os.path.join(root, FAMILY, "B1.json"),
                   lambda d: d.update(parent=7))                   # a parent that is not B0
        rep = rt.verify_chain(FAMILY, root=root)
        _check("V-UCEP-H3B-PARENT-FIELD",
               _ok(rep) is False and "PARENT_MISMATCH" in regress_kinds(rep),
               "B1 claiming parent 7 over a B0 predecessor is not ok: PARENT_MISMATCH",
               "WR-02 parent attack accepted: %s" % _dict(rep))

        root = b0_copy("wr02-control-b0only")
        rep_b0 = rt.verify_chain(FAMILY, root=root)
        root = b0_copy("wr02-control-b2")
        child(root)
        child(root)
        rep_b2 = rt.verify_chain(FAMILY, root=root)
        _check("V-UCEP-H3B-ROOT-CONTROL",
               _ok(rep_b0) is True and _ok(rep_b2) is True
               and getattr(rep_b2, "generations", None) == [0, 1, 2],
               "an intact B0-only chain and an intact B0..B2 chain are still ok",
               "b0only=%s b2=%s" % (_dict(rep_b0), _dict(rep_b2)))

        # --- the allowlist itself, with a control from the real family -------
        is_auth = getattr(rt, "is_authorized", None)
        accepted = ("Owner", "Owner (approved 'both', 2026-10-01)",
                    "Owner: plan of record")
        refused = ("x", "", "   ", None, "owner", "Ownerx", "Owner's cat",
                   "Bot Owner")
        real_b1 = bl.load_generation(FAMILY, 1)
        real_authority = (real_b1 or {}).get("promoted_by")
        if callable(is_auth):
            wrong_accept = [a for a in accepted if is_auth(a) is not True]
            wrong_refuse = [a for a in refused if is_auth(a) is not False]
            real_ok = is_auth(real_authority) is True
        else:
            wrong_accept, wrong_refuse, real_ok = list(accepted), list(refused), False
        _check("V-UCEP-ALLOWLIST",
               callable(is_auth) and not wrong_accept and not wrong_refuse and real_ok,
               "is_authorized accepts Owner forms (incl. the real B1 promoted_by), "
               "refuses x, blank, None, wrong case and look-alikes",
               "is_authorized=%s wrongly refused=%r wrongly accepted=%r real %r ok=%s"
               % (callable(is_auth), wrong_accept, wrong_refuse, real_authority,
                  real_ok))

        # --- the CLI reports an unanchored child and exits 1 ----------------
        import family_baseline as fb
        saved_dir = bl.BASELINES_DIR
        buf = io.StringIO()
        buf_ctl = io.StringIO()
        try:
            root = b0_copy("cli-unanchored")
            child(root)
            p1 = os.path.join(root, FAMILY, "B1.json")
            with open(p1, "r", encoding="utf-8") as fh:
                doc = json.load(fh)
            doc["parent_sha256"] = None
            with open(p1, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(doc, fh, indent=2, ensure_ascii=False)
                fh.write("\n")
            bl.BASELINES_DIR = root
            with contextlib.redirect_stdout(buf):
                rc_unanchored = fb.main(["verify", FAMILY])
            root = b0_copy("cli-anchored")
            child(root)
            bl.BASELINES_DIR = root
            with contextlib.redirect_stdout(buf_ctl):
                rc_anchored = fb.main(["verify", FAMILY])
        finally:
            bl.BASELINES_DIR = saved_dir
        _check("V-UCEP-CLI-UNANCHORED",
               rc_unanchored == 1 and "UNANCHORED B1" in buf.getvalue()
               and rc_anchored == 0 and "UNANCHORED" not in buf_ctl.getvalue(),
               "verify exits 1 and prints UNANCHORED B1 for a child with no anchor; "
               "the anchored chain exits 0",
               "unanchored rc=%s out=%r; anchored rc=%s out=%r"
               % (rc_unanchored, buf.getvalue(), rc_anchored, buf_ctl.getvalue()))

        # --- reanchor: provenance moves on the record, rule text does not ----
        # Synthetic family under a temp root: a B0 of three entries whose cited
        # file was then rewritten as a pointer stub (every quote QUOTE_MISSING,
        # the real situation of the 9 rotted citations) and a "skill" file that
        # holds the same quotes five lines lower. Nothing here touches the real
        # baselines.
        sfam = "synth_family"
        quotes = ("Rule alpha: a claim names the plane that observed it.",
                  "Rule beta: every batch item is re-authorized on its own.",
                  "Rule gamma: nothing converts without an authorized source.")
        old_lines = ["# old rules", quotes[0], "", quotes[1], "", quotes[2]]
        q_line = (2, 4, 6)

        def synth(label, canon_rel="canon"):
            base = os.path.join(tmp, label)
            root = os.path.join(base, "root")
            old = os.path.join(base, "old.md")
            canon_dir = os.path.join(base, *canon_rel.split("/"))
            os.makedirs(canon_dir)
            canon = os.path.join(canon_dir, "SKILL.md")
            with open(old, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("\n".join(old_lines) + "\n")
            with open(canon, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("\n".join(["# skill", "f1", "f2", "f3", "f4"] + old_lines) + "\n")
            ents = [{"id": "r%d" % (i + 1), "requirement": "requirement %d" % (i + 1),
                     "why": "because %d" % (i + 1), "class": "D", "check": "",
                     "status": "reviewed",
                     "origin": {"file": old, "line": q_line[i], "quote": quotes[i]}}
                    for i in range(3)]
            bl.write_generation(sfam, ents, "B0 synth", root=root)
            with open(old, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("# pointer stub\nthe rules moved to their skill\n")
            return {"root": root, "old": old, "canon": canon, "entries": ents}

        def new_origin(s, i, **over):
            o = {"file": s["canon"], "line": q_line[i] + 5, "quote": quotes[i]}
            o.update(over)
            return o

        def attempt(fn):
            """(refusal message or None, other exception text or None)."""
            try:
                fn()
            except rt.RatchetRefusal as exc:
                return str(exc), None
            except Exception as exc:  # noqa: BLE001 -- RED must fail on predicates
                return None, "%s: %s" % (type(exc).__name__, exc)
            return None, None

        def call(name, *a, **k):
            fn = getattr(rt, name, None)
            if fn is None:
                raise AttributeError("ratchet.%s does not exist" % name)
            return fn(*a, **k)

        s = synth("ra-one")
        try:
            call("reanchor", sfam, {"r1": new_origin(s, 0), "r2": new_origin(s, 1)},
                 reason="rule moved to its skill", authority="Owner", root=s["root"])
            err1 = None
        except Exception as exc:  # noqa: BLE001
            err1 = "%s: %s" % (type(exc).__name__, exc)
        gens = bl.generations(sfam, s["root"])
        if gens == [0, 1] and err1 is None:
            g0 = bl.load_generation(sfam, 0, s["root"])
            g1 = bl.load_generation(sfam, 1, s["root"])
            e0 = {e["id"]: e for e in g0["entries"]}
            e1 = {e["id"]: e for e in g1["entries"]}
            order_ok = [e["id"] for e in g1["entries"]] == [e["id"] for e in g0["entries"]]
            moved_ok = all(e1[i]["origin"] == new_origin(s, n)
                           and {k: v for k, v in e1[i].items() if k != "origin"}
                           == {k: v for k, v in e0[i].items() if k != "origin"}
                           for n, i in ((0, "r1"), (1, "r2")))
            r3_ok = e1["r3"] == e0["r3"]
            ch = g1.get("changes") or {}
            rec_ok = sorted(ch) == ["r1", "r2"] and all(
                ch[i].get("kind") == "REANCHORED"
                and ch[i].get("reason") == "rule moved to its skill"
                and ch[i].get("authority") == "Owner"
                and ch[i].get("from") == e0[i]["origin"]
                and ch[i].get("to") == e1[i]["origin"] for i in ch)
            chain_ok = _ok(rt.verify_chain(sfam, root=s["root"])) is True
            ver_ok = all(bl.verify_origin(e1[i]) == bl.VERIFIED for i in ("r1", "r2"))
            one_ok = order_ok and moved_ok and r3_ok and rec_ok and chain_ok and ver_ok
            one_diag = ("order=%s moved=%s r3=%s record=%s chain=%s verified=%s changes=%s"
                        % (order_ok, moved_ok, r3_ok, rec_ok, chain_ok, ver_ok, ch))
        else:
            one_ok, one_diag = False, "generations=%s error=%s" % (gens, err1)
        _check("V-UCEP-REANCHOR-ONE-GENERATION", one_ok,
               "one call = exactly one generation; r1/r2 REANCHORED on the record, "
               "ids/order/other fields and r3 unchanged, chain ok, both VERIFIED",
               one_diag)

        s = synth("ra-qm")
        elsewhere = os.path.join(os.path.dirname(s["canon"]), "other.md")
        with open(elsewhere, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(["# other", "nothing relevant", ""] * 4) + "\n")
        msg, other = attempt(lambda: call(
            "reanchor", sfam, {"r1": new_origin(s, 0, file=elsewhere, line=2)},
            reason="rule moved", authority="Owner", root=s["root"]))
        gens = bl.generations(sfam, s["root"])
        _check("V-UCEP-REANCHOR-REFUSES-QUOTE-MISSING",
               msg is not None and "r1" in msg and "QUOTE_MISSING" in msg and gens == [0],
               "a new origin whose file lacks the quote is refused (names r1 and "
               "QUOTE_MISSING), nothing written",
               "refusal=%r other=%r generations=%s" % (msg, other, gens))

        s = synth("ra-cli")
        mpath = os.path.join(os.path.dirname(s["old"]), "map.json")
        with open(mpath, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({sfam: {"r1": new_origin(s, 0)}}, fh)
        saved_dir = bl.BASELINES_DIR
        argv = ["reanchor", sfam, "--map", mpath, "--reason", "rule moved",
                "--authority", "Owner"]
        out = io.StringIO()
        try:
            bl.BASELINES_DIR = s["root"]
            with contextlib.redirect_stdout(out):
                rc_dry = fb.main(argv + ["--dry-run"])
            gens_dry = bl.generations(sfam)
            with contextlib.redirect_stdout(out):
                rc_real = fb.main(argv)
            gens_real = bl.generations(sfam)
            bad = synth("ra-cli-bad")
            bl.BASELINES_DIR = bad["root"]
            with contextlib.redirect_stdout(out):
                rc_bad = fb.main(["reanchor", sfam, "--map", mpath, "--reason",
                                  "rule moved", "--authority", "x"])
            gens_bad = bl.generations(sfam)
        finally:
            bl.BASELINES_DIR = saved_dir
        _check("V-UCEP-REANCHOR-CLI",
               rc_dry == 0 and gens_dry == [0] and rc_real == 0 and gens_real == [0, 1]
               and rc_bad == 2 and gens_bad == [0],
               "--dry-run exits 0 and writes nothing; the real call adds one generation; "
               "authority 'x' exits 2 and writes nothing",
               "dry rc=%s gens=%s; real rc=%s gens=%s; bad rc=%s gens=%s; out=%r"
               % (rc_dry, gens_dry, rc_real, gens_real, rc_bad, gens_bad, out.getvalue()))

        # --- reanchor refusal matrix: every laundering and rot path ----------
        def refuse_gate(gate, label, build, needle, evidence, setup=None,
                        authority="Owner", expect_gens=None):
            """Fresh synthetic root; the call must raise RatchetRefusal naming
            `needle`, and the generations must be what `expect_gens` says."""
            s = synth(label, canon_rel=(setup or {}).get("canon_rel", "canon"))
            if setup and setup.get("before"):
                setup["before"](s)
            before = bl.generations(sfam, s["root"])
            ids_map = build(s)
            msg, other = attempt(lambda: call(
                "reanchor", sfam, ids_map, reason="rule moved", authority=authority,
                root=s["root"]))
            gens = bl.generations(sfam, s["root"])
            want = before if expect_gens is None else expect_gens
            _check(gate, msg is not None and all(n in msg for n in needle)
                   and gens == want,
                   evidence,
                   "refusal=%r other=%r generations=%s (want %s)"
                   % (msg, other, gens, want))
            return s

        refuse_gate("V-UCEP-REANCHOR-REFUSES-MOVED", "ra-moved",
                    lambda s: {"r1": new_origin(s, 0, line=q_line[0] + 6)}, ("r1", "MOVED"),
                    "a quote that exists in the new file but not on the cited line is "
                    "refused (MOVED), nothing written")
        refuse_gate("V-UCEP-REANCHOR-REFUSES-CHANGED-QUOTE", "ra-cq",
                    lambda s: {"r1": new_origin(s, 0, quote="a claim names the plane")},
                    ("r1", "quote"),
                    "a different quote that IS on the cited line is refused: a changed "
                    "rule text is not a provenance move")
        refuse_gate("V-UCEP-REANCHOR-REFUSES-EMPTY-QUOTE", "ra-eq",
                    lambda s: {"r1": new_origin(s, 0, quote="")}, ("r1",),
                    "an empty quote is refused, never the weak-vocabulary fallback")

        s = synth("ra-rel")
        saved_cwd = os.getcwd()
        try:
            os.chdir(os.path.dirname(s["canon"]))
            msg, other = attempt(lambda: call(
                "reanchor", sfam, {"r1": new_origin(s, 0, file="SKILL.md")},
                reason="rule moved", authority="Owner", root=s["root"]))
        finally:
            os.chdir(saved_cwd)
        gens = bl.generations(sfam, s["root"])
        _check("V-UCEP-REANCHOR-REFUSES-RELATIVE-PATH",
               msg is not None and "r1" in msg and "absolute" in msg and gens == [0],
               "a relative path (which resolves from the cwd, so verify_origin alone "
               "would accept it) is refused, nothing written",
               "refusal=%r other=%r generations=%s" % (msg, other, gens))

        s = synth("ra-wt", canon_rel=".claude/worktrees/x")
        msg, other = attempt(lambda: call(
            "reanchor", sfam, {"r1": new_origin(s, 0)}, reason="rule moved",
            authority="Owner", root=s["root"]))
        gens = bl.generations(sfam, s["root"])
        # Control in the same gate: the identical bytes outside a worktrees segment
        # are accepted, so the refusal is the path rule and not a broken fixture.
        sc = synth("ra-wt-ctl", canon_rel="canon2")
        msg_c, other_c = attempt(lambda: call(
            "plan_reanchor", sfam, {"r1": new_origin(sc, 0)}, "rule moved", "Owner",
            root=sc["root"]))
        _check("V-UCEP-REANCHOR-REFUSES-WORKTREE-PATH",
               msg is not None and "r1" in msg and "worktrees" in msg and gens == [0]
               and msg_c is None and other_c is None,
               "a file under .claude/worktrees/ is refused (nothing written); the same "
               "bytes at canon2/ are accepted by plan_reanchor",
               "refusal=%r other=%r generations=%s; control refusal=%r other=%r"
               % (msg, other, gens, msg_c, other_c))

        refuse_gate("V-UCEP-REANCHOR-REFUSES-BAD-AUTHORITY", "ra-auth",
                    lambda s: {"r1": new_origin(s, 0)}, ("allowlist",),
                    "authority 'x' is refused, nothing written", authority="x")
        refuse_gate("V-UCEP-REANCHOR-REFUSES-UNKNOWN-ID", "ra-unk",
                    lambda s: {"nope": new_origin(s, 0)}, ("nope",),
                    "an id the generation does not hold is refused, nothing written")

        s = synth("ra-rev")
        call_rev = attempt(lambda: rt.revert(sfam, "r3", reason="retired for the test",
                                             authority="Owner", root=s["root"]))
        msg, other = attempt(lambda: call(
            "reanchor", sfam, {"r3": new_origin(s, 2)}, reason="rule moved",
            authority="Owner", root=s["root"]))
        gens = bl.generations(sfam, s["root"])
        _check("V-UCEP-REANCHOR-REFUSES-REVERTED-ID",
               call_rev == (None, None) and msg is not None and "r3" in msg
               and "active" in msg and gens == [0, 1],
               "a reverted entry cannot be re-anchored (only the revert generation exists)",
               "revert=%r refusal=%r other=%r generations=%s"
               % (call_rev, msg, other, gens))

        def noop_before(s):
            with open(s["old"], "w", encoding="utf-8", newline="\n") as fh:
                fh.write("\n".join(old_lines) + "\n")     # r1's current origin verifies

        refuse_gate("V-UCEP-REANCHOR-REFUSES-NOOP", "ra-noop",
                    lambda s: {"r1": {"file": s["old"], "line": q_line[0],
                                      "quote": quotes[0]}},
                    ("r1", "no-op"),
                    "a new origin equal to the current (VERIFIED) origin is refused",
                    setup={"before": noop_before})
        s = refuse_gate("V-UCEP-REANCHOR-ALL-OR-NOTHING", "ra-aon",
                        lambda s: {"r1": new_origin(s, 0),
                                   "r2": new_origin(s, 1, file=os.path.join(
                                       os.path.dirname(s["canon"]), "absent.md"))},
                        ("r2: ",), "r1 valid + r2 at a missing file: refused naming r2, "
                        "and r1 is NOT written either")

        # --- the real tree: 9 rotted citations re-anchored on the record ------
        real_ids = {
            "persistent_state": {
                "persistent_state-destructive-op-authorizes-exact-state-seen",
                "persistent_state-destructive-identity-falsification-test",
                "persistent_state-absence-of-identity-refuses",
                "persistent_state-precondition-window-must-be-closed",
                "persistent_state-batch-reauthorize-per-item",
                "persistent_state-monetary-qualifiers-travel-with-amount",
                "persistent_state-monetary-conflicting-qualifiers-refuse",
                "persistent_state-monetary-no-conversion-without-authorized-source"},
            "wii_homebrew": {"wii_homebrew-claim-must-name-observing-plane"}}
        f0 = {"persistent_state":
              "bcb20d37f568a8873710990e4e43351010e882ac6fcd0f38b1e387a1d674dc64",
              "wii_homebrew":
              "2603cf39889cb421c9fd31968b706d68a79aa7f14539173a4eb669761a4bc1bd"}
        real_diag, real_ok = [], True
        union = set()
        for fam in real_ids:
            gens = bl.generations(fam)
            g1 = bl.load_generation(fam, 1) if 1 in gens else {}
            ch = g1.get("changes") or {}
            union |= set(ch)
            kinds_ok = bool(ch) and all(
                v.get("kind") == "REANCHORED" and rt.is_authorized(v.get("authority"))
                for v in ch.values())
            broken = sorted(e["id"] for e in bl.active_entries(fam)
                            if bl.verify_origin(e) != bl.VERIFIED)
            chain = rt.verify_chain(fam)
            sha0 = bl.generation_sha256(fam, 0) if 0 in gens else None
            fam_ok = (gens == [0, 1] and kinds_ok and not broken and chain.ok
                      and sha0 == f0[fam])
            real_ok = real_ok and fam_ok
            real_diag.append("%s: gens=%s kinds_ok=%s broken=%s chain_ok=%s b0_sha_ok=%s"
                             % (fam, gens, kinds_ok, broken, chain.ok, sha0 == f0[fam]))
        want_union = real_ids["persistent_state"] | real_ids["wii_homebrew"]
        real_ok = real_ok and union == want_union
        real_diag.append("union==9 ids: %s" % (union == want_union))
        _check("V-UCEP-REAL-REANCHORED", real_ok,
               "real tree: both families [0, 1], the 9 ids REANCHORED by an allowlisted "
               "authority, every active entry VERIFIED, chains ok, B0 bytes = F0 blobs",
               "; ".join(real_diag))

        # --- discovery: the real-tree gates must not curate their subjects ---
        # `getattr` keeps the RED run on predicates, never on an AttributeError.
        disc = getattr(bl, "discover_subjects", None)

        def discover(*args):
            """(subjects, error): what discover_subjects returned, or why it could not."""
            if disc is None:
                return None, "baselines.discover_subjects does not exist"
            try:
                return disc(*args), ""
            except Exception as exc:  # noqa: BLE001 -- the diagnostic names it
                return None, "%s: %s" % (type(exc).__name__, exc)

        def touch(path, text="{}\n"):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)

        r_nested = os.path.join(tmp, "disc_nested")
        bl.write_generation("archetype/X", [{"id": "e1"}], "b0", root=r_nested)
        bl.write_generation("fam", [{"id": "e1"}], "b0", root=r_nested)
        got, err = discover(r_nested)
        _check("V-UCEP-DISCOVER-NESTED", got == ["archetype/X", "fam"],
               "a nested axis is found with a forward-slash id, sorted: %s" % got,
               "got=%s err=%s (want ['archetype/X', 'fam'])" % (got, err))

        r_empty = os.path.join(tmp, "disc_empty")
        os.makedirs(r_empty)
        got_empty, err_a = discover(r_empty)
        got_absent, err_b = discover(os.path.join(tmp, "disc_absent"))
        # The floors of the two real-tree gates (4 subjects) must fail on these.
        _check("V-UCEP-DISCOVER-EMPTY",
               got_empty == [] and got_absent == []
               and not (len(got_empty or []) >= 4) and not (len(got_absent or []) >= 4),
               "an empty root and a missing root both give [] without raising, so a "
               "floor of 4 subjects is red on an empty walk",
               "empty=%s (%s) absent=%s (%s)" % (got_empty, err_a, got_absent, err_b))

        r_res = os.path.join(tmp, "disc_residue")
        touch(os.path.join(r_res, "a", "B9.json.tmp"))
        touch(os.path.join(r_res, "b", ".B1.123.tmp"))
        touch(os.path.join(r_res, "c", "notes.json"))
        touch(os.path.join(r_res, "B3.json"))          # a generation file AT the root
        got_res, err_c = discover(r_res)
        touch(os.path.join(r_res, "d", "B0.json"))     # control: a real generation is seen
        got_ctl, err_d = discover(r_res)
        _check("V-UCEP-DISCOVER-RESIDUE", got_res == [] and got_ctl == ["d"],
               "temp residue, a non-generation json and a root-level B<n>.json are not "
               "subjects; the same root with d/B0.json gives ['d']",
               "residue=%s (%s) control=%s (%s)" % (got_res, err_c, got_ctl, err_d))

        r_call = os.path.join(tmp, "disc_calltime")
        bl.write_generation("only", [{"id": "e1"}], "b0", root=r_call)
        saved_dir = bl.BASELINES_DIR
        bl.BASELINES_DIR = r_call
        try:
            got_call, err_e = discover()
        finally:
            bl.BASELINES_DIR = saved_dir
        _check("V-UCEP-DISCOVER-CALL-TIME", got_call == ["only"],
               "with no argument it reads bl.BASELINES_DIR at call time (monkeypatched)",
               "got=%s err=%s (want ['only'])" % (got_call, err_e))

        subjects, err_f = discover()
        total = 0
        starts_at_zero = bool(subjects)
        for s in subjects or []:
            total += len(bl.active_entries(s))
            starts_at_zero = starts_at_zero and bl.generations(s)[:1] == [0]
        _check("V-UCEP-DISCOVER-REAL",
               subjects is not None and len(subjects) >= 4 and starts_at_zero and total >= 60,
               "%d subjects, %d active entries, floor 4/60" % (len(subjects or []), total),
               "subjects=%s total_active=%d starts_at_zero=%s err=%s"
               % (subjects, total, starts_at_zero, err_f))

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
              % (_PASS, _PASS + _FAIL, 33, 33))
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
