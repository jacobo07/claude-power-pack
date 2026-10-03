"""V-UCEP-* -- the two done-gate exits the CBR probe found (UCEP-01, audit G13).

H6: a baseline entry whose check is `test:<file>` resolved to DELEGATED, never
blocked, and was never run -- a failing named test read as handled.
H5: every entry declared not-applicable with a free-text reason read as a clean
gate, because a reason of any text was accepted.

The gate must now (a) report a `test:` check as UNJUDGED (`test-not-run`),
counted apart from VIOLATED, and prove it never executes the file; (b) accept
an N/A only with a reason carrying a token from the closed vocabulary
`donegate.NA_REASONS`, and only up to `NA_SHARE_CAP_PERCENT` of the family.

Every attack gate is paired with a control that can fire: the marker the test
file would write is proven writable by running it by hand, the no-exec scanner
is proven to flag a fixture that does exec, and a within-cap N/A is proven to
still be honoured. Everything runs against temp directories; nothing reaches
the production ledger.

Run: python tools/test_ucep_donegate_exits.py     (exit 0 = all gates pass)
"""
from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_PP_ROOT = os.path.normpath(os.path.join(_HERE, ".."))
for p in (_PP_ROOT, _HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

from modules.tower import baselines as bl  # noqa: E402
from modules.tower import donegate as dg  # noqa: E402

_PASS = 0
_FAIL = 0
# The gate count is a literal: deleting a gate (or one that never runs) must not
# print a satisfied N/N. Update it in the same commit that adds or removes a gate.
EXPECTED = 17
_MARKER = ""
_EXECUTED_AFTER = []  # judge() calls after which the marker existed


def _check(gate, cond, evidence, diagnostic):
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print("  PASS %-40s %s" % (gate, evidence))
    else:
        _FAIL += 1
        print("  FAIL %-40s %s" % (gate, diagnostic))


def _entry(ident, check, n=0):
    return {"id": ident, "class": "D", "status": "reviewed",
            "requirement": "requirement %s" % ident, "why": "fixture",
            "origin": {"file": "GOV.md", "line": n + 1}, "check": check}


_FAMILY_N = [0]


def _family(gens, entries):
    _FAMILY_N[0] += 1
    name = "ucep_dg_%d" % _FAMILY_N[0]
    bl.write_generation(name, entries, "b0", root=gens)
    return name


def _judge(name, repo, gens, **kw):
    """judge() plus the never-executed observation, taken after EVERY call."""
    rep = dg.judge(name, repo, root=gens, **kw)
    if os.path.exists(_MARKER):
        _EXECUTED_AFTER.append(name)
    return rep


def _rows(rep):
    return {r["entry_id"]: r for r in rep.get("entries", [])}


def _exec_findings(source):
    """Import / call sites that execute a process or foreign code."""
    bad_mods = {"subprocess", "runpy", "importlib", "multiprocessing", "pty", "ctypes"}
    bad_builtins = {"exec", "eval", "compile", "__import__"}
    found = []

    def bad_os(attr):
        return attr in ("system", "popen") or attr.startswith(("exec", "spawn"))

    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] in bad_mods:
                    found.append("import %s (line %d)" % (a.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            top = (node.module or "").split(".")[0]
            if top in bad_mods:
                found.append("from %s import (line %d)" % (node.module, node.lineno))
            elif top == "os":
                for a in node.names:
                    if bad_os(a.name):
                        found.append("from os import %s (line %d)" % (a.name, node.lineno))
        elif isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) \
                    and f.value.id == "os" and bad_os(f.attr):
                found.append("os.%s() (line %d)" % (f.attr, node.lineno))
            elif isinstance(f, ast.Name) and f.id in bad_builtins:
                found.append("%s() (line %d)" % (f.id, node.lineno))
    return found


def _subject(tmp):
    """A subject repo: a README, and a test file that writes the marker then fails."""
    repo = os.path.join(tmp, "subject")
    os.makedirs(os.path.join(repo, "tests"))
    with open(os.path.join(repo, "README.md"), "w", encoding="utf-8") as fh:
        fh.write("run it\n")
    with open(os.path.join(repo, "tests", "test_x.py"), "w", encoding="utf-8") as fh:
        fh.write("with open(%r, 'w') as fh:\n    fh.write('ran')\nassert False\n" % _MARKER)
    return repo


def main() -> int:
    global _MARKER
    tmp = tempfile.mkdtemp(prefix="ucep_dg_")
    home = os.path.join(tmp, "home")
    os.makedirs(home)
    saved_env = {k: os.environ.get(k) for k in ("HOME", "USERPROFILE")}
    os.environ.update(HOME=home, USERPROFILE=home)
    try:
        _MARKER = os.path.join(tmp, "marker.flag")
        gens = os.path.join(tmp, "gens")
        repo = _subject(tmp)
        print("V-UCEP donegate exit gates")

        # 1 -- H6: an existing test: check is UNJUDGED, counted apart from VIOLATED
        fam1 = _family(gens, [_entry("has-test", "test:tests/test_x.py"),
                              _entry("has-readme", "file:README.md", 1)])
        rep = _judge(fam1, repo, gens)
        row = _rows(rep).get("has-test", {})
        _check("V-UCEP-H6-TEST-UNJUDGED",
               row.get("verdict") == dg.UNJUDGED
               and row.get("unjudged_reason") == "test-not-run"
               and "has-test" in rep.get("unjudged_tests", [])
               and rep.get("counts", {}).get("violated", -1) == 0
               and rep.get("would_block") is True
               and rep.get("would_block_on_violated") is False,
               "test: file -> UNJUDGED/test-not-run, listed in unjudged_tests, "
               "violated=0, would_block True, would_block_on_violated False",
               {"row": row, "unjudged_tests": rep.get("unjudged_tests"),
                "counts": rep.get("counts"), "would_block": rep.get("would_block"),
                "would_block_on_violated": rep.get("would_block_on_violated")})

        # 4 -- a missing test file is still VIOLATED and not listed as unjudged
        fam4 = _family(gens, [_entry("no-test", "test:tests/nope.py")])
        rep4 = _judge(fam4, repo, gens)
        _check("V-UCEP-H6-MISSING-TEST-STILL-VIOLATED",
               _rows(rep4).get("no-test", {}).get("verdict") == dg.VIOLATED
               and "no-test" not in rep4.get("unjudged_tests", []),
               "missing test file -> VIOLATED, not in unjudged_tests",
               _rows(rep4).get("no-test"))

        # 5 -- registry: stays DELEGATED
        reg = os.path.join(tmp, "registry.json")
        with open(reg, "w", encoding="utf-8") as fh:
            json.dump({"verifiers": [{"id": "fixture-gate"}]}, fh)
        fam5 = _family(gens, [_entry("reg", "registry:fixture-gate")])
        rep5 = _judge(fam5, repo, gens, registry=reg)
        _check("V-UCEP-REGISTRY-STILL-DELEGATED",
               _rows(rep5).get("reg", {}).get("verdict") == dg.DELEGATED,
               "registry: with a registered verifier -> DELEGATED (the remap is test:-only)",
               _rows(rep5).get("reg"))

        # 8 -- report counts on a mixed family
        mixed = [_entry("m-pass", "file:README.md"),
                 _entry("m-fail", "file:missing.txt", 1),
                 _entry("m-prose", "grep banned terms against production HTML", 2),
                 _entry("m-test", "test:tests/test_x.py", 3),
                 _entry("m-reg", "registry:fixture-gate", 4)]
        fam8 = _family(gens, mixed)
        rep8 = _judge(fam8, repo, gens, registry=reg)
        counts = rep8.get("counts", {})
        keys = ("applied", "violated", "delegated", "not_applicable", "unjudged",
                "unjudged_tests")
        total = sum(counts.get(k, 0) for k in keys[:5])
        _check("V-UCEP-REPORT-COUNTS",
               all(k in counts for k in keys) and total == len(mixed)
               and counts.get("unjudged_tests") == 1 and counts.get("unjudged", 0) >= 2,
               "counts %s sum to %d entries; unjudged apart from violated" % (counts, total),
               {"counts": counts, "sum": total, "entries": len(mixed)})

        # 3 -- control: the harness, not the module, runs the test file by hand
        if os.path.exists(_MARKER):
            os.remove(_MARKER)
        proc = subprocess.run([sys.executable, os.path.join(repo, "tests", "test_x.py")],
                              capture_output=True, text=True)
        wrote = os.path.exists(_MARKER)
        _check("V-UCEP-H6-MARKER-CONTROL", wrote and proc.returncode != 0,
               "running the file by hand writes the marker (rc=%d): the instrument can fire"
               % proc.returncode,
               {"marker": wrote, "rc": proc.returncode})
        if wrote:
            os.remove(_MARKER)

        # 6/7 -- no process- or code-execution facility in the check path
        scan = {}
        # every module judge() runs: checks, donegate, and (IN-03) the chain, the
        # baseline reader and the selector it calls
        for rel in ("modules/tower/checks.py", "modules/tower/donegate.py",
                    "modules/tower/ratchet.py", "modules/tower/baselines.py",
                    "modules/tower/select.py"):
            with open(os.path.join(_PP_ROOT, rel), "r", encoding="utf-8") as fh:
                scan[rel] = _exec_findings(fh.read())
        _check("V-UCEP-NO-EXEC-IMPORTS", all(v == [] for v in scan.values()),
               "the 5 modules judge() runs import/call no exec facility (AST scan)", scan)
        control = _exec_findings("import subprocess\nimport os\nos.system('x')\n")
        _check("V-UCEP-NO-EXEC-SCAN-CONTROL", len(control) == 2,
               "scanner flags a fixture with one forbidden import and one os.system", control)

        # -- H5: N/A needs a closed-vocabulary reason, within a share cap ------------
        # 10 entries whose file: check PASSes: only the N/A handling can set would_block.
        ids = ["n%d" % i for i in range(10)]
        fam10 = _family(gens, [_entry(i, "file:README.md", k) for k, i in enumerate(ids)])
        TOKEN = "no-money"

        # 9 -- free text is not a reason
        rep9 = _judge(fam10, repo, gens, not_applicable={i: "n/a" for i in ids})
        r9 = _rows(rep9)
        _check("V-UCEP-H5-FREE-TEXT",
               len(r9) == 10
               and all(r["verdict"] == dg.UNJUDGED
                       and r.get("unjudged_reason") == "na-not-in-vocabulary"
                       for r in r9.values())
               and rep9.get("would_block") is True,
               "10/10 declared N/A with free text -> all UNJUDGED/na-not-in-vocabulary, "
               "would_block True",
               {"verdicts": sorted({(r["verdict"], r.get("unjudged_reason"))
                                    for r in r9.values()}),
                "would_block": rep9.get("would_block")})

        # 10 -- every entry N/A with valid tokens is over the cap
        rep10 = _judge(fam10, repo, gens, not_applicable={i: TOKEN for i in ids})
        r10 = _rows(rep10)
        _check("V-UCEP-H5-OVER-CAP",
               rep10.get("na_cap") == 3 and rep10.get("na_over_cap") is True
               and len(r10) == 10
               and all(r["verdict"] == dg.UNJUDGED and r.get("unjudged_reason") == "na-over-cap"
                       for r in r10.values())
               and rep10.get("would_block") is True,
               "10/10 valid-token N/A: cap 3, over cap -> every claim voided "
               "(UNJUDGED/na-over-cap), would_block True",
               {"na_cap": rep10.get("na_cap"), "na_over_cap": rep10.get("na_over_cap"),
                "verdicts": sorted({(r["verdict"], r.get("unjudged_reason"))
                                    for r in r10.values()}),
                "would_block": rep10.get("would_block")})

        # 11 -- control: a within-cap N/A is still honoured
        three = ids[:3]
        rep11 = _judge(fam10, repo, gens, not_applicable={i: TOKEN for i in three})
        r11 = _rows(rep11)
        _check("V-UCEP-H5-WITHIN-CAP-CONTROL",
               all(r11[i]["verdict"] == dg.NOT_APPLICABLE for i in three)
               and all(r11[i]["verdict"] == dg.APPLIED_VERIFIED for i in ids[3:])
               and rep11.get("would_block") is False,
               "3/10 valid-token N/A -> NOT_APPLICABLE, other 7 APPLIED_VERIFIED, would_block "
               "False (na_count=%s na_cap=%s)" % (rep11.get("na_count"), rep11.get("na_cap")),
               {"verdicts": {i: r["verdict"] for i, r in r11.items()},
                "would_block": rep11.get("would_block")})

        # 12 -- control: a token may carry a free-text note
        note = "internal tool has no billing"
        rep12 = _judge(fam10, repo, gens, not_applicable={ids[0]: "%s: %s" % (TOKEN, note)})
        row12 = _rows(rep12).get(ids[0], {})
        _check("V-UCEP-H5-TOKEN-WITH-NOTE-CONTROL",
               row12.get("verdict") == dg.NOT_APPLICABLE
               and TOKEN in str(row12.get("detail")) and note in str(row12.get("detail")),
               "token plus note -> NOT_APPLICABLE; detail keeps both", row12)

        # 13 -- a blank reason names no reason at all
        rep13 = _judge(fam10, repo, gens, not_applicable={ids[0]: "  "})
        row13 = _rows(rep13).get(ids[0], {})
        _check("V-UCEP-H5-NO-REASON",
               row13.get("verdict") == dg.UNJUDGED
               and row13.get("unjudged_reason") == "na-no-reason",
               "blank reason -> UNJUDGED/na-no-reason", row13)

        # -- WR-04: an N/A claim must not hide a failing runnable check -----------
        # A valid, within-cap N/A claim is HONOURED (verdict NOT_APPLICABLE): the
        # existing "declared N/A honoured" case (test_tower_donegate V-TDG-VERDICT-
        # KINDS) is exactly an N/A over a `glob:` check that fails because the surface
        # does not exist. What it may not do is make the failure invisible: the check
        # is evaluated anyway and a failure is reported per row, in `counts` and in a
        # named list.
        fam_m = _family(gens, [_entry("mk0", "file:README.md", 0),
                               _entry("mk1", "file:README.md", 1),
                               _entry("mk2", "file:missing.txt", 2),
                               _entry("mk3", "file:README.md", 3)])
        rep_m = _judge(fam_m, repo, gens,
                       not_applicable={"mk2": "platform-not-targeted: desktop only"})
        row_m = _rows(rep_m).get("mk2", {})
        _check("V-UCEP-WR04-NA-MASKS-FAILING-CHECK",
               row_m.get("verdict") == dg.NOT_APPLICABLE
               and row_m.get("na_masked_violation") is True
               and row_m.get("check_outcome") == "FAIL"
               and rep_m.get("na_masked_violations") == ["mk2"]
               and rep_m.get("counts", {}).get("na_over_failing_check") == 1
               and rep_m.get("would_block_on_masked_na") is True,
               "N/A over a failing file: check -> still NOT_APPLICABLE but flagged: row "
               "na_masked_violation, na_masked_violations=['mk2'], counts "
               "na_over_failing_check=1, would_block_on_masked_na True",
               {"row": row_m, "na_masked_violations": rep_m.get("na_masked_violations"),
                "counts": rep_m.get("counts"),
                "would_block_on_masked_na": rep_m.get("would_block_on_masked_na")})
        rep_mc = _judge(fam_m, repo, gens,
                        not_applicable={"mk0": "platform-not-targeted: desktop only"})
        row_mc = _rows(rep_mc).get("mk0", {})
        _check("V-UCEP-WR04-NA-OVER-PASSING-CONTROL",
               row_mc.get("verdict") == dg.NOT_APPLICABLE
               and row_mc.get("na_masked_violation") is False
               and rep_mc.get("na_masked_violations") == []
               and rep_mc.get("counts", {}).get("na_over_failing_check") == 0
               and rep_mc.get("would_block_on_masked_na") is False
               and _rows(rep_mc).get("mk2", {}).get("verdict") == dg.VIOLATED
               and _rows(rep_mc).get("mk2", {}).get("na_masked_violation") is False,
               "N/A over a passing check is not flagged; the unclaimed failing entry is "
               "VIOLATED, not 'masked' (the flag means a CLAIM hid it)",
               {"row": row_mc, "na_masked_violations": rep_mc.get("na_masked_violations"),
                "counts": rep_mc.get("counts"),
                "mk2": _rows(rep_mc).get("mk2")})

        # -- WR-03: the chain verdict must reach would_block ---------------------
        # Every entry PASSes, so only the chain can set would_block. The attack is a
        # TAMPERED chain (B0 edited after B1 anchored it); the control is the same
        # fixture untouched (chain ok -> would_block False).
        def two_gens(label_entries):
            fam = _family(gens, label_entries)
            bl.write_generation(fam, label_entries, "b1", root=gens)
            return fam

        passing = [_entry("c%d" % i, "file:README.md", i) for i in range(4)]
        fam_ok = two_gens(passing)
        rep_ok = _judge(fam_ok, repo, gens)
        fam_bad = two_gens(passing)
        b0_path = os.path.join(gens, fam_bad, "B0.json")
        with open(b0_path, "r", encoding="utf-8") as fh:
            doc0 = json.load(fh)
        doc0["reason"] = "edited after B1 anchored it"
        with open(b0_path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc0, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        rep_bad = _judge(fam_bad, repo, gens)
        all_pass = all(r["verdict"] == dg.APPLIED_VERIFIED
                       for r in _rows(rep_bad).values())
        _check("V-UCEP-WR03-CHAIN-BLOCKS",
               rep_bad.get("chain_ok") is False and all_pass
               and rep_bad.get("would_block") is True
               and rep_bad.get("would_block_on_chain") is True
               and rep_bad.get("would_block_on_violated") is False,
               "a TAMPERED chain whose entries all PASS -> would_block True "
               "(on_chain True, on_violated False)",
               {"chain_ok": rep_bad.get("chain_ok"), "all_pass": all_pass,
                "would_block": rep_bad.get("would_block"),
                "would_block_on_chain": rep_bad.get("would_block_on_chain"),
                "would_block_on_violated": rep_bad.get("would_block_on_violated")})
        _check("V-UCEP-WR03-CLEAN-CHAIN-CONTROL",
               rep_ok.get("chain_ok") is True
               and all(r["verdict"] == dg.APPLIED_VERIFIED
                       for r in _rows(rep_ok).values())
               and rep_ok.get("would_block") is False
               and rep_ok.get("would_block_on_chain") is False,
               "the same fixture with an intact chain -> would_block False "
               "(a gate that always blocks cannot pass this)",
               {"chain_ok": rep_ok.get("chain_ok"), "would_block": rep_ok.get("would_block"),
                "would_block_on_chain": rep_ok.get("would_block_on_chain")})

        # 2 -- never executed: observed after EVERY judge() call in this file
        _check("V-UCEP-H6-NOT-EXECUTED", _EXECUTED_AFTER == [],
               "marker absent after every judge() call (control: by-hand run writes it)",
               {"marker_present_after": _EXECUTED_AFTER})

        print()
        print("UCEP_DONEGATE_EXITS_PASS=%d/%d  threshold=%d/%d"
              % (_PASS, _PASS + _FAIL, EXPECTED, EXPECTED))
        return 0 if _FAIL == 0 and _PASS == EXPECTED else 1
    finally:
        for k, v in saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
