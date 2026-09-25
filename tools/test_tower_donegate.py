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

        print()
        print("TOWER_DONEGATE_PASS=%d/%d  threshold=%d/%d"
              % (_PASS, _PASS + _FAIL, _PASS + _FAIL, _PASS + _FAIL))
        return 0 if _FAIL == 0 else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
