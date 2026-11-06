"""V-TDG-* -- the family done-gate (spec S6), report-only, attributable.

The gate judges every ACTIVE entry of a family's newest generation against a
subject repo -- injected into the prompt or not -- and stamps the report with
the generation it was judged under, so evidence stays historically true when a
later generation is stronger.

The discriminating subject is a web_surface-shaped case nothing else in the
estate judges: a button that renders while no handler is wired. The in-game
obligation (R4) and goal convergence's REALITY rule do not cover it, so a
VIOLATED verdict carrying the entry id and `judged_under` can only have come
from the baseline path. The companion drill severs that path and requires this
file to go red with the reason flipped.

Run: python tools/test_tower_donegate.py     (exit 0 = all gates pass)
"""
from __future__ import annotations

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
from modules.tower import donegate as dg  # noqa: E402
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


WIRED = "web-action-wired"
ENTRIES = [
    {"id": WIRED, "class": "D", "status": "reviewed",
     "requirement": "Every rendered action button is wired to a handler that completes it",
     "why": "a button that renders is not an action that happens",
     "origin": {"file": "GOV.md", "line": 1},
     "check": "regex:src/app.js::addEventListener\\(\\s*['\"]click"},
    {"id": "web-has-readme", "class": "D", "status": "reviewed",
     "requirement": "The repo documents how to run it", "why": "handoff",
     "origin": {"file": "GOV.md", "line": 2}, "check": "file:README.md"},
    {"id": "web-prose", "class": "D", "status": "reviewed",
     "requirement": "Copy is humanized", "why": "voice", "origin": {"file": "GOV.md", "line": 3},
     "check": "grep banned terms against production HTML"},
    {"id": "web-registry", "class": "D", "status": "reviewed",
     "requirement": "Deploy verified by the registered verifier", "why": "reality",
     "origin": {"file": "GOV.md", "line": 4}, "check": "registry:web-deploy"},
    {"id": "web-mobile", "class": "C", "status": "reviewed",
     "requirement": "Mobile layout measured at 320px", "why": "phones",
     "origin": {"file": "GOV.md", "line": 5}, "check": "glob:tests/mobile_*.py"},
]


def _repo(root, wired):
    os.makedirs(os.path.join(root, "src"))
    with open(os.path.join(root, "index.html"), "w", encoding="utf-8") as fh:
        fh.write("<button id='buy'>Comprar</button>\n")
    with open(os.path.join(root, "src", "app.js"), "w", encoding="utf-8") as fh:
        fh.write("const b = document.getElementById('buy');\n")
        if wired:
            fh.write("b.addEventListener('click', () => checkout());\n")
    with open(os.path.join(root, "README.md"), "w", encoding="utf-8") as fh:
        fh.write("run it\n")


def _verdicts(rep):
    return {v["entry_id"]: v["verdict"] for v in rep["entries"]}


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="tdg_")
    try:
        print("V-TDG gates")
        gens = os.path.join(tmp, "gens")
        bl.write_generation("web_fixture", ENTRIES, "b0", root=gens)
        broken = os.path.join(tmp, "broken")
        _repo(broken, wired=False)
        fixed = os.path.join(tmp, "fixed")
        _repo(fixed, wired=True)

        rep = dg.judge("web_fixture", broken, root=gens,
                       not_applicable={"web-mobile": "desktop-only admin tool"})
        v = _verdicts(rep)
        finding = next((x for x in rep["entries"] if x["entry_id"] == WIRED), {})
        _check("V-TDG-DISCRIMINATING-VIOLATION",
               v.get(WIRED) == dg.VIOLATED and finding.get("source") == dg.SOURCE
               and finding.get("judged_under") == "web_fixture/B0",
               "unwired button -> VIOLATED, attributed to tower-baseline web_fixture/B0",
               finding)
        _check("V-TDG-STAMPED",
               rep["judged_under"] == "web_fixture/B0"
               and rep["generation_sha256"] == bl.generation_sha256("web_fixture", 0, gens)
               and rep["chain_ok"] is True,
               "report carries generation, its sha256 and the chain verdict",
               {k: rep.get(k) for k in ("judged_under", "generation_sha256", "chain_ok")})
        _check("V-TDG-VERDICT-KINDS",
               v.get("web-has-readme") == dg.APPLIED_VERIFIED
               and v.get("web-prose") == dg.UNJUDGED
               and v.get("web-registry") == dg.UNJUDGED
               and v.get("web-mobile") == dg.NOT_APPLICABLE,
               "static PASS applied; prose unjudged; registry with no registry unjudged; "
               "declared N/A honoured", v)

        rep_fixed = dg.judge("web_fixture", fixed, root=gens,
                             not_applicable={"web-mobile": "desktop-only admin tool"})
        _check("V-TDG-CONTROL-WIRED",
               _verdicts(rep_fixed).get(WIRED) == dg.APPLIED_VERIFIED,
               "the same rule on a wired button is APPLIED_VERIFIED",
               _verdicts(rep_fixed))

        rep_na = dg.judge("web_fixture", broken, root=gens,
                          not_applicable={"web-mobile": "  "})
        _check("V-TDG-NA-NEEDS-REASON", _verdicts(rep_na).get("web-mobile") == dg.UNJUDGED,
               "an N/A with no reason is UNJUDGED, not N/A", _verdicts(rep_na))

        _check("V-TDG-REPORT-ONLY",
               rep["report_only"] is True and rep["would_block"] is True
               and rep_fixed["would_block"] is True,
               "report-only; would_block names what enforcement would do "
               "(fixed still has unjudged prose)",
               {k: rep.get(k) for k in ("report_only", "would_block")})

        _check("V-TDG-NOT-INJECTED-STILL-JUDGED",
               all(x["verdict"] for x in rep["entries"])
               and len(rep["entries"]) == len(ENTRIES)
               and {x["entry_id"] for x in rep["entries"] if not x["injected"]}
               == set(rep["deferred_from_prompt"]),
               "every active entry judged; deferred ones flagged, not skipped",
               rep["deferred_from_prompt"])

        # The fixture above never overflows the prompt, so the gate before this
        # one would hold even if deferred entries were skipped. A real family
        # does overflow: 15 entries, 7-8 injected.
        real = dg.judge("kobiicraft_mode", broken)
        skipped = [x["entry_id"] for x in real["entries"] if not x["verdict"]]
        _check("V-TDG-REAL-DEFERRED-JUDGED",
               len(real["entries"]) == len(bl.active_entries("kobiicraft_mode"))
               and len(real["deferred_from_prompt"]) >= 1 and not skipped
               and real["judged_under"] == "kobiicraft_mode/B0",
               "%d judged, %d of them deferred from the prompt"
               % (len(real["entries"]), len(real["deferred_from_prompt"])),
               {"n": len(real["entries"]), "deferred": real["deferred_from_prompt"],
                "skipped": skipped})

        rt.revert("web_fixture", "web-has-readme", reason="moved to docs site",
                  authority="Owner", root=gens)
        rep1 = dg.judge("web_fixture", broken, root=gens)
        _check("V-TDG-NEWER-GENERATION",
               rep1["judged_under"] == "web_fixture/B1"
               and "web-has-readme" not in _verdicts(rep1)
               and rep["judged_under"] == "web_fixture/B0",
               "B1 judges its own active set; the B0 report still says B0",
               (rep1["judged_under"], sorted(_verdicts(rep1))))

        none = dg.judge("no_such_family", broken, root=gens)
        _check("V-TDG-NO-GENERATION",
               none["judged_under"] is None and none["entries"] == []
               and none["status"] == dg.NO_BASELINE,
               "a family with no generation says so; it does not read as clean", none)

        # The CLI the hook and /family-done-gate name. Before it existed, nothing
        # outside this file ever called dg.judge (liveness: tower/donegate unreachable).
        import json as _json
        import subprocess as _sp
        tool = os.path.join(_HERE, "family_baseline.py")
        first = real["entries"][0]["entry_id"]
        cli = _sp.run([sys.executable, tool, "judge", "kobiicraft_mode", "--repo", broken,
                       "--na", "%s=fixture repo has no plugin" % first, "--json"],
                      capture_output=True, text=True, encoding="utf-8", timeout=60)
        try:
            crep = _json.loads(cli.stdout)
        except ValueError:
            crep = {}
        cv = _verdicts(crep) if crep else {}
        _check("V-TDG-CLI-JUDGES",
               crep.get("judged_under") == "kobiicraft_mode/B0"
               and len(crep.get("entries", [])) == len(real["entries"])
               and cv.get(first) == dg.NOT_APPLICABLE
               and cli.returncode == (1 if crep.get("would_block") else 0),
               "judge CLI: %d entries, --na honoured, exit %d == would_block"
               % (len(crep.get("entries", [])), cli.returncode),
               (cli.returncode, cli.stdout[-300:], cli.stderr[-300:]))
        nob = _sp.run([sys.executable, tool, "judge", "no_such_family"],
                      capture_output=True, text=True, encoding="utf-8", timeout=60)
        _check("V-TDG-CLI-NO-BASELINE",
               nob.returncode == 0 and "no baseline generation" in nob.stdout,
               "unknown family says so and exits 0", (nob.returncode, nob.stdout))

        # spec baseline-rule-content-reachability (S15 XXIX): binary_reconstruction/B1 defers 5 of 12 rules at the
        # ceiling. A deferred NAME is not its content: unread -> KNOWLEDGE UNMET; `rule --deferred` reads + ledgers.
        os.environ["CPP_TOWER_STATE_DIR"] = os.path.join(tmp, "tower-state")
        fam = "binary_reconstruction"
        r0 = dg.judge(fam, broken)
        deferred = set(r0["deferred_from_prompt"])
        content = {x["entry_id"]: x["content"] for x in r0["entries"]}
        prose_deferred = {x["entry_id"] for x in r0["entries"] if not x["injected"]
                          and x["verdict"] not in (dg.APPLIED_VERIFIED, dg.NOT_APPLICABLE)}
        _check("V-TDG-NAME-ONLY-IS-UNMET",
               len(deferred) >= 1 and all(content[i] == dg.NAME_ONLY for i in deferred)
               and all(content[i] == dg.INJECTED for i in content if i not in deferred)
               and set(r0["knowledge_unmet"]) == prose_deferred and prose_deferred,
               "%d deferred, all NAME_ONLY; knowledge_unmet = %d" % (len(deferred), len(r0["knowledge_unmet"])),
               {"deferred": sorted(deferred), "unmet": r0["knowledge_unmet"], "content": content})
        _check("V-TDG-CONTROL-FIT-NO-UNMET",
               rep["knowledge_unmet"] == [] and all(x["content"] == dg.INJECTED for x in rep["entries"]),
               "a family whose rules all fit has no unmet knowledge", rep["knowledge_unmet"])
        rc = _sp.run([sys.executable, tool, "rule", fam, "--deferred"],
                     capture_output=True, text=True, encoding="utf-8", timeout=60, env=dict(os.environ))
        reqs = {x["entry_id"]: x["requirement"] for x in r0["entries"]}
        ledger = bl.consumption_ledger()
        rows = [ln for ln in open(ledger, encoding="utf-8")] if os.path.exists(ledger) else []
        _check("V-TDG-RULE-CLI-PRINTS-CONTENT",
               rc.returncode == 0 and all(reqs[i] in rc.stdout for i in deferred) and len(rows) == 1,
               "rule --deferred printed %d full requirements, 1 ledger row" % len(deferred),
               (rc.returncode, rc.stdout[-300:], rc.stderr[-300:], len(rows)))
        r1 = dg.judge(fam, broken)
        _check("V-TDG-RETRIEVED-CLEARS-UNMET",
               r1["knowledge_unmet"] == []
               and all(x["content"] == dg.RETRIEVED for x in r1["entries"] if x["entry_id"] in deferred),
               "after retrieval: deferred entries RETRIEVED, no unmet knowledge", r1["knowledge_unmet"])
        bad = _sp.run([sys.executable, tool, "rule", fam, "no-such-entry"],
                      capture_output=True, text=True, encoding="utf-8", timeout=60, env=dict(os.environ))
        _check("V-TDG-RULE-CLI-UNKNOWN-ID", bad.returncode == 2 and "UNKNOWN" in bad.stdout,
               "an unknown id is refused, not silently empty", (bad.returncode, bad.stdout))
        from modules.gsd_x import cli as gx
        saved = {k: os.environ.get(k) for k in ("HOME", "USERPROFILE")}
        os.environ["HOME"] = os.environ["USERPROFILE"] = os.path.join(tmp, "home")
        try:
            block = gx.family_block("Build a binary reconstruction pipeline that turns m2c output into exact C",
                                    {"session_id": ""})
        finally:
            for k, val in saved.items():
                if val is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = val
        import re as _re
        m = _re.search(r'`python "([^"]+)" rule (\S+) --deferred`', block)
        _check("V-TDG-BLOCK-NAMES-RUNNABLE-RETRIEVAL",
               bool(m) and os.path.isfile(m.group(1)) and m.group(2) == fam,
               "the injected block carries an absolute, existing retrieval command", block[-400:])
        os.environ.pop("CPP_TOWER_STATE_DIR", None)

        print()
        print("TOWER_DONEGATE_PASS=%d/%d  threshold=%d/%d"
              % (_PASS, _PASS + _FAIL, _PASS + _FAIL, _PASS + _FAIL))
        return 0 if _FAIL == 0 else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
