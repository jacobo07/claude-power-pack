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

    print(f"CTC_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
