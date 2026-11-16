"""V-ASC-BASE -- Phase 5 gate: Constitutive Promotion Gate + inheritance proof, both poles.

Run: python3 tools/test_asc_baseline.py   (exit 0 = every check passes)
Never calls a model: the fresh-agent pair was recorded once by tools/asc_inherit_run.py and is verified here from disk.
"""
from __future__ import annotations

import copy
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.backlog_autopilot import promotion as P          # noqa: E402
from modules.backlog_autopilot import webslice as W           # noqa: E402
from modules.gsd_x import cli                                  # noqa: E402
from modules.tower import baselines as bl, donegate as dg, ratchet as rt  # noqa: E402

PH = ROOT / "vault/programs/ascension/bcap-1/phase5"
FAM = "web_surface"
NEW = ["web_surface-privacy-page-linked", "web_surface-terms-page-linked"]
_pass = _fail = 0


def check(name: str, cond: bool, evidence: str = "") -> None:
    global _pass, _fail
    if cond:
        _pass += 1
        print("  PASS %-46s %s" % (name, evidence))
    else:
        _fail += 1
        print("  FAIL %-46s %s" % (name, evidence))


def tmp_root(upto: int | None = None) -> str:
    r = tempfile.mkdtemp(prefix="vasc-base-")
    shutil.copytree(ROOT / "vault/tower/baselines" / FAM, Path(r) / FAM)
    if upto is not None:
        for f in (Path(r) / FAM).glob("B*.json"):
            if int(f.stem[1:]) > upto:
                f.unlink()
    return r


def good_evidence() -> dict:
    return json.loads((PH / "evidence.json").read_text(encoding="utf-8"))


DELTAS = P.load_deltas(str(PH / "deltas.json"))
EV = good_evidence()
ACTIVE4 = bl.active_entries(FAM, tmp_root(4))

# ---- 1. classification, every class reachable, refusals named --------------------------------------------------
cls = {d.id: P.classify(d, ACTIVE4) for d in DELTAS}
check("classes: constitutive reachable", cls[NEW[0]].klass == P.CONSTITUTIVE and cls[NEW[1]].klass == P.CONSTITUTIVE)
check("classes: archetype-enhancing reachable", P.classify(P.Delta("x", "every surface states its updated date visibly", "w",
      "regex:index.html::updated"), ACTIVE4).klass == P.ARCHETYPE_ENHANCING)
check("classes: product-specific refused", cls["web_surface-harness-click-attributes"].klass == P.PRODUCT_SPECIFIC
      and cls["web_surface-newsletter-copy-tone"].klass == P.PRODUCT_SPECIFIC)
check("classes: incidental (enforced elsewhere) refused", cls["web_surface-selected-resource-licence-clean"].klass == P.INCIDENTAL)
dup = copy.copy(DELTAS[0]); dup.id = "web_surface-privacy-copy"; dup.requirement = ACTIVE4[0]["requirement"]; dup.check = ""
check("classes: verbatim duplicate of an active entry refused", P.classify(dup, ACTIVE4).duplicate_of == ACTIVE4[0]["id"])
check("classes: only the last two promotable", [k for k, v in cls.items() if v.promotable] == NEW, str([k for k, v in cls.items() if v.promotable]))

# ---- 2. promotion refusals write nothing; the correct promotion writes one generation ---------------------------
def attempt(ds, ev, root=None):
    root = root or tmp_root(4)
    before = bl.generations(FAM, root)
    out = P.promote(FAM, ds, ev, "test-authority", "test reason", root)
    return out, before, bl.generations(FAM, root), root

e = copy.deepcopy(EV); e.pop("reuse")
o, b, a, _ = attempt(DELTAS, e)
check("promote: no reuse evidence -> refused, nothing written", not o.generation and a == b and set(NEW) <= set(o.refused))
e = copy.deepcopy(EV); e["negative_controls"][0]["rc"] = 0
o, b, a, _ = attempt(DELTAS, e)
check("promote: a negative control that passed -> refused", not o.generation and a == b)
e = copy.deepcopy(EV); e["reuse"]["run"] = e["improvement"]["run"]
o, b, a, _ = attempt(DELTAS, e)
check("promote: reuse by the same run -> refused", not o.generation and a == b)
prose = copy.copy(DELTAS[0]); prose.id = "web_surface-prose-only"; prose.check = "looks fine on a phone"; prose.requirement = "zzzz qqqq wwww"
o, b, a, _ = attempt([prose], EV)
check("promote: prose check -> UNCHECKABLE, nothing written", not o.generation and a == b and "UNCHECKABLE" in o.refused.get(prose.id, ""))
o, b, a, _ = attempt([d for d in DELTAS if d.id not in NEW], EV)
check("promote: only non-promotable deltas -> nothing written", not o.generation and a == b and len(o.refused) == 4)
o, b, a, root = attempt(DELTAS, EV)
check("promote: correct batch writes exactly one generation", bool(o.generation) and a == b + [b[-1] + 1] and sorted(o.promoted) == sorted(NEW))
check("promote: chain verifies after promotion", rt.verify_chain(FAM, root).ok)
new_entries = {x["id"]: x for x in bl.active_entries(FAM, root)}
check("promote: evidence written into each entry", all(new_entries[i].get("evidence", {}).get("reuse") for i in NEW))

# ---- 3. real tree holds the promotion, chain intact -------------------------------------------------------------
real = {x["id"]: x for x in bl.active_entries(FAM)}
check("real: both entries active with evidence", all(i in real and real[i].get("evidence", {}).get("improvement") for i in NEW))
check("real: chain ok", rt.verify_chain(FAM).ok, str(bl.generations(FAM)))
check("real: refused deltas are absent", not any(i in real for i in cls if i not in NEW))
check("real: B4 unchanged by the promotion", len(bl.active_entries(FAM, tmp_root(4))) == 24)

# ---- 4. delivery: a later equivalent build receives it, an unrelated one and the pre-promotion baseline do not ---
os.environ["CPP_TOWER_STATE_DIR"] = tempfile.mkdtemp(prefix="vasc-state-")
PROMPT = "Build a small landing page for a harbour newsletter that sends a monthly tide-table digest"
blk = cli.family_block(PROMPT, {"session_id": "v-base-1"})
check("delivery: equivalent web prompt receives both new rules", all("[%s]" % i in blk for i in NEW), "%d chars" % len(blk))
check("delivery: unrelated prompt receives nothing", cli.family_block("fix the python off-by-one in parse_dates", {"session_id": "v-base-2"}) == "")
blk4 = cli.family_block(PROMPT, {"session_id": "v-base-3"}, root=tmp_root(4))
check("delivery: pre-promotion baseline lacks them (negative pole)", blk4 != "" and not any(i in blk4 for i in NEW))

# ---- 5. done-gate poles on built surfaces ------------------------------------------------------------------------
good = Path(tempfile.mkdtemp(prefix="vasc-good-")) / "s"
W.build_site(good)
v = {e_["entry_id"]: e_["verdict"] for e_ in dg.judge(FAM, str(good))["entries"]}
check("gate: complete surface -> both rules APPLIED_VERIFIED", all(v[i] == "APPLIED_VERIFIED" for i in NEW))


def variant(drop: str) -> Path:
    d = Path(tempfile.mkdtemp(prefix="vasc-var-")) / "s"
    shutil.copytree(good, d)
    idx = d / "index.html"
    idx.write_text(re.sub(r'<a href="[^"]*%s[^"]*">[^<]*</a>' % drop, "", idx.read_text(encoding="utf-8")), encoding="utf-8")
    return d


for drop, bad_id, ok_id in (("terms", NEW[1], NEW[0]), ("privacy", NEW[0], NEW[1])):
    vv = {e_["entry_id"]: e_["verdict"] for e_ in dg.judge(FAM, str(variant(drop)))["entries"]}
    check("gate: link to %s dropped -> exactly that rule VIOLATED" % drop, vv[bad_id] == "VIOLATED" and vv[ok_id] == "APPLIED_VERIFIED")

# ---- 6. the recorded fresh-agent pair -----------------------------------------------------------------------------
run = json.loads((PH / "inheritance_run.json").read_text(encoding="utf-8"))
t, c = run["runs"]["treated"], run["runs"]["control"]
check("agent: both runs exited 0 and wrote a page", t["rc"] == 0 and c["rc"] == 0 and "index.html" in t["files"] and "index.html" in c["files"])
check("agent: treated acted on the block (ran the family tools), control did not", run["block_chars"] > 500
      and any("family_baseline.py" in str(x["input"]) for x in t["tool_calls"])
      and not any("family_baseline.py" in str(x["input"]) for x in c["tool_calls"]))
check("agent: task text never asks for legal pages", not re.search(r"privacy|terms|legal", run["task"], re.I))
check("agent: treated never read the promotion inputs", not any(x["tool"] != "Write" and ("bcap-1" in str(x["input"]) or "B5.json" in str(x["input"]) or "deltas.json" in str(x["input"])) for x in t["tool_calls"]))
vt = {e_["entry_id"]: e_["verdict"] for e_ in dg.judge(FAM, str(PH / "inherit/treated"))["entries"]}
vc = {e_["entry_id"]: e_["verdict"] for e_ in dg.judge(FAM, str(PH / "inherit/control"))["entries"]}
check("agent: baseline-fed surface passes the done-gate rules", all(vt[i] == "APPLIED_VERIFIED" for i in NEW))
check("agent: control surface is rejected by the same rules", all(vc[i] == "VIOLATED" for i in NEW))
inc = Path(tempfile.mkdtemp(prefix="vasc-inc-")) / "s"
shutil.copytree(PH / "inherit/treated", inc)
(inc / "index.html").write_text(re.sub(r'<a href="[^"]*terms[^"]*">[^<]*</a>', "", (inc / "index.html").read_text(encoding="utf-8")), encoding="utf-8")
vi = {e_["entry_id"]: e_["verdict"] for e_ in dg.judge(FAM, str(inc))["entries"]}
check("agent: deliberately incomplete variant rejected", vi[NEW[1]] == "VIOLATED" and vi[NEW[0]] == "APPLIED_VERIFIED")
check("agent: stamp recorded matches a generation that held the entries", run["candidate_generation"] == "web_surface/B5")

print("\nV-ASC-BASE: %d passed, %d failed" % (_pass, _fail))
sys.exit(1 if _fail else 0)
