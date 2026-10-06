#!/usr/bin/env python
"""V-CTC-* gates for tools/cost_to_completion.py. Pure function plus the CLI (exit codes).

Mutation drill: COST_TO_COMPLETION_DRILL_DIR holds a mutated copy of cost_to_completion.py, imported and
run instead of the real one.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
MOD_DIR = Path(os.environ.get("COST_TO_COMPLETION_DRILL_DIR") or HERE)
sys.path.insert(0, str(MOD_DIR))
import cost_to_completion as ctc  # noqa: E402
import route_admission as ra  # noqa: E402

passes = fails = 0
FLOORS = ra.load_floors()
WF = FLOORS["profiles"][ra.TOP_LEVEL]["floor"]


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def cli(doc) -> tuple[int, dict]:
    f = Path(tempfile.mkdtemp(prefix="ctc-test-")) / "claims.json"
    f.write_text(json.dumps(doc), encoding="utf-8")
    p = subprocess.run([sys.executable, str(MOD_DIR / "cost_to_completion.py"), "--claims", str(f)],
                       capture_output=True, text=True, encoding="utf-8")
    first = p.stdout.strip()
    try:
        out = json.loads(first)
    except ValueError:
        out = {}
    return p.returncode, out


IR_PATH = Path(os.environ.get("QL_CLAIMS_IR") or r"C:\Users\User\Apps\io-ql-story\17_Businesses\QuickLease"
               r"\docs\plans\ql-story-tour\claims.json")


def refused(doc, **kw):
    try:
        ctc.compile_cost(doc, FLOORS, **kw)
    except ctc.Refused as r:
        return r.reason
    return None


def udoc(est1=2):
    return {"gates": [{"id": "G1"}, {"id": "G2"}],
            "claims": [{"id": "a", "class": "novel", "unit": "U1", "gates": ["G1"]},
                       {"id": "b", "class": "visual", "unit": "U2", "gates": ["G2"]},
                       {"id": "c", "class": "deterministic", "gates": ["G1"]},
                       {"id": "s", "class": "bounded_coding", "status": "sleeping", "unit": "U3", "gates": ["G2"]}],
            "units": [{"id": "U1", "est_calls": est1, "reserve_calls": 1, "profile": "top-level-worker",
                       "ctx_tokens": 140000, "order": 1},
                      {"id": "U2", "est_calls": 1, "reserve_calls": 0, "profile": "Explore", "ctx_tokens": 10000,
                       "order": 2},
                      {"id": "U3", "est_calls": 2, "reserve_calls": 0, "profile": "top-level-worker",
                       "ctx_tokens": 140000, "order": 3}]}


def cli_route(doc, *extra):
    f = Path(tempfile.mkdtemp(prefix="ctc-route-")) / "claims.json"
    f.write_text(json.dumps(doc), encoding="utf-8")
    p = subprocess.run([sys.executable, str(MOD_DIR / "cost_to_completion.py"), "--claims", str(f), "--route", *extra],
                       capture_output=True, text=True, encoding="utf-8")
    try:
        out = json.loads(p.stdout)
    except ValueError:
        out = {}
    return p.returncode, out


def p5_checks() -> None:
    # visual class: prior 4 calls x 150k, deopt applies
    vs = ctc.compile_cost({"claims": [{"id": "v", "class": "visual"}]}, FLOORS)
    check("V-CTC-VISUAL-PRIOR", vs["candidate"] == {"calls": 4, "tokens": 600_000,
                                                    "with_margin": ra._with_margin(600_000, ra.DEFAULT_GROWTH_MARGIN)},
          str(vs["candidate"]))
    check("V-CTC-VISUAL-DEOPT", vs["ceiling"]["tokens"] == 3 * 600_000, str(vs["ceiling"]))
    # shared costs nothing and is counted
    sh = ctc.compile_cost({"claims": [{"id": "a", "class": "bounded_coding"},
                                      {"id": "b", "class": "bounded_coding", "shared_with": "a"}]}, FLOORS)
    one = ctc.compile_cost({"claims": [{"id": "a", "class": "bounded_coding"}]}, FLOORS)
    check("V-CTC-SHARED-COSTS-ZERO", sh["candidate"] == one["candidate"] and sh["counts"]["shared"] == 1
          and sh["o_shared"] == 1 and sh["o_irreducible"] == 1 and sh["o_semantic_consumers"] == 2, str(sh["clean"]))
    check("V-CTC-SHARED-UNKNOWN-REFUSED", refused({"claims": [{"id": "a", "class": "novel", "shared_with": "ghost"}]})
          == "BAD_CLAIM")
    # units path
    d = udoc()
    out = ctc.compile_cost(d, FLOORS)
    pf = FLOORS["profiles"]["Explore"]["floor"]
    cand = 2 * 140000 + 1 * max(10000, pf)
    want_ceil = cand + 140000 + cand + 2 * 2 * 140000 + 2 * max(10000, pf)
    check("V-CTC-UNITS-CANDIDATE", out["candidate"]["tokens"] == cand and out["candidate"]["calls"] == 3,
          str(out["candidate"]))
    check("V-CTC-UNITS-CEILING", out["ceiling"]["tokens"] == want_ceil, f"{out['ceiling']} want {want_ceil}")
    check("V-CTC-UNITS-CLAMP-TO-PROFILE-FLOOR", [u["ctx_eff"] for u in out["units"]] == [140000, pf],
          str(out["units"]))
    check("V-CTC-SLEEPING-OUT-OF-FRONTIER", out["sleeping"] == ["s"] and [u["id"] for u in out["units"]] == ["U1", "U2"])
    d2 = udoc()
    d2["actuals"] = {"U1": {"calls": 2, "ctx_tokens": 140000}, "U2": {"calls": 1, "ctx_tokens": 10000}}
    out2 = ctc.compile_cost(d2, FLOORS)
    check("V-CTC-ALLOWANCE-ZERO-WHEN-MEASURED", out2["unmeasured_allowance"] == 0.0 and out["unmeasured_allowance"] == 1.0
          and out2["ceiling"]["tokens"] == want_ceil - cand, f"{out2['ceiling']}")
    d3 = udoc()
    d3["claims"][0].pop("unit")
    check("V-CTC-MODEL-CLAIM-WITHOUT-UNIT-REFUSED", refused(d3) == "BAD_CLAIM")
    d4 = udoc()
    d4["claims"][0]["unit"] = "NOPE"
    check("V-CTC-UNKNOWN-UNIT-REFUSED", refused(d4) == "BAD_CLAIM")
    d5 = udoc()
    d5["units"].append({"id": "U9", "est_calls": 1, "reserve_calls": 0, "profile": "Explore", "ctx_tokens": 1000})
    check("V-CTC-UNIT-WITHOUT-CLAIMS-REFUSED", refused(d5) == "BAD_CLAIM")
    # scope coverage, red then control
    g = {"gates": [{"id": "G1"}, {"id": "G2"}],
         "claims": [{"id": "x", "class": "deterministic", "gates": ["G1"]},
                    {"id": "y", "class": "deterministic", "gates": ["G1"]}]}
    check("V-CTC-UNCOVERED-GATE-RED", refused(g) == "UNCOVERED_GATE")
    g["claims"][1]["gates"] = ["G2"]
    check("V-CTC-UNCOVERED-GATE-CONTROL-GREEN", refused(g) is None)
    o = {"gates": [{"id": "G1"}], "claims": [{"id": "x", "class": "deterministic", "gates": ["G1"]},
                                               {"id": "y", "class": "deterministic"}]}
    check("V-CTC-ORPHAN-CLAIM-RED", refused(o) == "ORPHAN_CLAIM")
    o["claims"][1]["derived_from"] = "plan section"
    check("V-CTC-ORPHAN-CLAIM-CONTROL-GREEN", refused(o) is None)
    rc, res = cli_route({**g, "gates": [{"id": "G1"}, {"id": "G2"}, {"id": "G3"}]})
    check("V-CTC-CLI-UNCOVERED-EXIT-2", rc == 2 and res.get("verdict") == "REFUSED", f"rc={rc} {res}")
    # route verdict pass-through
    r = ctc.route_verdict(udoc(), FLOORS)
    check("V-CTC-ROUTE-ADMISSIBLE", r["verdict"] == ra.ADMISSIBLE == r["admission"]["verdict"], r["verdict"])
    big = udoc(est1=4)
    big["envelope"] = {"target": 450_000}
    r = ctc.route_verdict(big, FLOORS)
    direct = ra.admit(r["route"], FLOORS)
    check("V-CTC-ROUTE-RECOMPILE-NOT-ADMISSIBLE", direct["verdict"] == ra.RECOMPILE and r["verdict"] == ra.RECOMPILE,
          f"{direct['verdict']} {r['verdict']}")
    stub = ctc.route_verdict(udoc(), FLOORS, admit_fn=lambda *a, **k: {"verdict": ra.RECOMPILE})
    check("V-CTC-ROUTE-OWNERSHIP-STUB", stub["verdict"] == ra.RECOMPILE)
    defer = ctc.route_verdict(udoc(), FLOORS, remaining=1)
    check("V-CTC-ROUTE-DEFER-PASS-THROUGH", defer["verdict"] == ra.DEFER, defer["verdict"])
    rc, res = cli_route(big)
    check("V-CTC-CLI-ROUTE-RECOMPILE-EXIT-3", rc == 3 and res.get("verdict") == ra.RECOMPILE, f"rc={rc}")
    rc, res = cli_route(udoc())
    check("V-CTC-CLI-ROUTE-ADMISSIBLE-EXIT-0", rc == 0 and res.get("verdict") == ra.ADMISSIBLE, f"rc={rc}")
    check("V-CTC-ROUTE-NEEDS-UNITS", refused({"claims": [{"id": "a", "class": "novel"}]}) is None
          and _route_refused({"claims": [{"id": "a", "class": "novel"}]}) == "BAD_CLAIM")
    # the real IR
    check("V-CTC-REAL-IR-EXISTS", IR_PATH.exists(), str(IR_PATH))
    if IR_PATH.exists():
        ir = json.loads(IR_PATH.read_text(encoding="utf-8-sig"))
        real = ctc.compile_cost(ir, FLOORS)
        c = real["clean"]
        check("V-CTC-REAL-IR-CLEAN-COUNTS", c["o_total"] == c["o_zero"] + c["o_shared"] + c["o_irreducible"]
              and (c["o_total"], c["o_zero"], c["o_shared"], c["o_irreducible"]) == (28, 6, 8, 14)
              and c["o_semantic_consumers"] == 22, str(c))
        rr = ctc.route_verdict(ir, FLOORS)
        check("V-CTC-REAL-IR-ROUTE-VERDICT-IS-ADMIT", rr["verdict"] == rr["admission"]["verdict"] == ra.ADMISSIBLE,
              rr["verdict"])
        dropped = json.loads(json.dumps(ir))
        for cl in dropped["claims"]:
            cl["gates"] = [x for x in cl.get("gates", []) if x != "G20"]
        check("V-CTC-REAL-IR-DROPPED-GATE-RED", refused(dropped) == "UNCOVERED_GATE")


def _route_refused(doc):
    try:
        ctc.route_verdict(doc, FLOORS)
    except ctc.Refused as r:
        return r.reason
    return None


def main() -> int:
    claims = [
        {"id": "c1", "class": "satisfied", "status": "satisfied"},
        {"id": "c2", "class": "deterministic", "status": "open"},
        {"id": "c3", "class": "known_transform", "status": "open"},
        {"id": "c4", "class": "bounded_coding", "status": "open", "est_calls": 4},
        {"id": "c5", "class": "novel", "status": "open"},
        {"id": "c6", "class": "owner_reality", "status": "open"},
        {"id": "c7", "class": "sleeping", "status": "sleeping"},
        {"id": "c8", "class": "novel", "status": "satisfied"},       # satisfied beats class: cost 0
    ]
    out = ctc.compile_cost({"claims": claims}, FLOORS)
    kt, bc, nv = (ctc.PRIORS[k] for k in ("known_transform", "bounded_coding", "novel"))
    want = 2 * kt["ctx_tokens"] + 4 * bc["ctx_tokens"] + 15 * nv["ctx_tokens"]
    check("V-CTC-CANDIDATE-EXACT", out["candidate"]["tokens"] == want and out["candidate"]["calls"] == 2 + 4 + 15,
          f"{out['candidate']}")
    check("V-CTC-ZERO-CLASSES-COST-NOTHING", ctc.compile_cost({"claims": claims[:2] + claims[5:7]}, FLOORS)
          ["candidate"]["tokens"] == 0, "satisfied/deterministic/owner/sleeping only")
    check("V-CTC-LISTS", out["sleeping"] == ["c7"] and out["owner_reality"] == ["c6"], str(out["sleeping"]))
    check("V-CTC-COUNTS", out["counts"]["satisfied"] == 2 and out["counts"]["novel"] == 1
          and out["counts"]["deterministic"] == 1, str(out["counts"]))
    check("V-CTC-FLOOR", out["floor"] == {"calls": 3, "tokens": 3 * WF}, str(out["floor"]))
    check("V-CTC-CEILING-NOVEL-DEOPT",
          out["ceiling"]["tokens"] == want + 2 * 15 * nv["ctx_tokens"], f"{out['ceiling']}")
    check("V-CTC-ORDER", out["floor"]["tokens"] <= out["candidate"]["tokens"] <= out["candidate"]["with_margin"]
          and out["candidate"]["tokens"] <= out["ceiling"]["tokens"])
    check("V-CTC-MARGIN", out["candidate"]["with_margin"] == ra._with_margin(want, ra.DEFAULT_GROWTH_MARGIN))

    # a small graph: the floor cannot exceed the candidate (1 call only)
    one = ctc.compile_cost({"claims": [{"id": "x", "class": "known_transform", "est_calls": 1}]}, FLOORS)
    check("V-CTC-FLOOR-CAPPED-BY-CANDIDATE", one["floor"]["calls"] == 1 and one["floor"]["tokens"] <= one["candidate"]["tokens"],
          str(one["floor"]))

    # actuals beat priors, and say so
    act = ctc.compile_cost({"claims": [{"id": "n", "class": "novel"}],
                            "actuals": {"novel": {"calls": 5, "ctx_tokens": 200_000}}}, FLOORS)
    check("V-CTC-ACTUALS-OVERRIDE", act["candidate"]["tokens"] == 1_000_000 and act["profile_source"]["novel"] == "actual"
          and out["profile_source"]["novel"] == "prior", str(act["profile_source"]))
    low = ctc.compile_cost({"claims": [{"id": "n", "class": "novel"}],
                            "actuals": {"novel": {"calls": 1, "ctx_tokens": 1}}}, FLOORS)
    check("V-CTC-CTX-CLAMPED-TO-WORKER-FLOOR", low["candidate"]["tokens"] == WF, str(low["candidate"]))

    # malformed claims refused
    for gate, bad in (("UNKNOWN-CLASS", [{"id": "a", "class": "magic"}]),
                      ("NO-ID", [{"class": "novel"}]),
                      ("DUP-ID", [{"id": "a", "class": "novel"}, {"id": "a", "class": "novel"}])):
        try:
            ctc.compile_cost({"claims": bad}, FLOORS)
            check(f"V-CTC-BAD-CLAIM-{gate}", False, "accepted")
        except ctc.Refused as r:
            check(f"V-CTC-BAD-CLAIM-{gate}", r.reason == "BAD_CLAIM", r.reason)

    # CLI control: a claim graph exits 0 ...
    rc, o = cli({"claims": claims})
    check("V-CTC-CLI-CLAIMS-EXIT-0", rc == 0, f"rc={rc}")
    # ... RED control: a phase list with a phase-average cost, no claims, is REFUSED as PHASE_MULTIPLIER
    rc, o = cli({"phases": [{"name": "p1"}, {"name": "p2"}, {"name": "p3"}], "phase_average_cost": 4_000_000})
    check("V-CTC-PHASE-LIST-REFUSED", rc != 0 and o.get("reason") == "PHASE_MULTIPLIER", f"rc={rc} {o}")
    # phases alongside a claim graph are refused too: the claim graph exists, phase count is forbidden
    rc, o = cli({"claims": claims, "phases": [1, 2, 3], "phase_average_cost": 1})
    check("V-CTC-PHASES-WITH-CLAIMS-REFUSED", rc != 0 and o.get("reason") == "PHASE_MULTIPLIER", f"rc={rc} {o}")
    rc, o = cli({"claims": []})
    check("V-CTC-EMPTY-CLAIMS-REFUSED", rc != 0 and o.get("reason") == "NO_CLAIMS", f"rc={rc} {o}")

    p5_checks()
    print(f"CTC_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
