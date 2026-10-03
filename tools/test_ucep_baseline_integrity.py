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
              % (_PASS, _PASS + _FAIL, 17, 17))
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
