#!/usr/bin/env python
"""V-DP-* gates for tools/decision_plane.py (spec vault/plans/decision-plane-master-plan-2026-10-17.md).

Hermetic: the state dir is a temp dir. Every refusal has a paired control that must come out the other way,
so a gate that refuses everything (or admits everything) cannot go green.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="decision-plane-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
sys.path.insert(0, str(Path(__file__).resolve().parent))
import decision_plane as dp  # noqa: E402

passes = fails = 0
M = "m-dptest000001"


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def refused(fn, exc=dp.DecisionError):
    try:
        fn()
    except exc as e:
        return str(e)
    return None


def spec(did="B", **over):
    s = {
        "id": did, "class": "CAPITAL", "question": "TB-FULL forecast exceeds the hard ceiling: which authority?",
        "dimensions": [{"name": "capital", "kind": "capital"},
                       {"name": "scope", "kind": "enum", "allowed": ["UNCHANGED", "REDUCED", "REORDERED"]},
                       {"name": "efficiency", "kind": "enum", "allowed": ["CONTINUE_OPTIMIZATION", "OFF"]}],
        "options": [
            {"token": "R-200", "params": {"capital": {"ceiling": 200_000_000, "unit": "processed_tokens"},
                                          "scope": "UNCHANGED", "efficiency": "CONTINUE_OPTIMIZATION"}},
            {"token": "R-REFC", "params": {"capital": {"ceiling": 120_000_000, "unit": "processed_tokens"},
                                           "scope": "UNCHANGED", "efficiency": "CONTINUE_OPTIMIZATION"}}],
        "recommendation": {"token": "R-200", "note": "evidence, not authority"},
        "evidence": {"central_scenario": 196_000_000, "ceiling": 120_000_000, "settled": 11_170_000},
        "consumers": ["m-7e268fc1a6d9"], "wake_policy": "WAKE_EXISTING_EXECUTOR",
    }
    s.update(over)
    return s


def main() -> int:
    # --- Closure Gate: complete option set is shown, an option missing a parameter blocks the whole decision
    d = dp.create(M, spec())
    check("V-DP-COMPLETE-IS-READY", d["status"] == dp.READY and d["problems"] == [], d["problems"])
    s = spec("B2")
    del s["options"][0]["params"]["capital"]["ceiling"]
    d2 = dp.create(M, s)
    check("V-DP-OPTION-WITHOUT-CEILING-IS-INCOMPLETE", d2["status"] == dp.OPEN
          and any("ceiling" in p for p in d2["problems"]), d2["problems"])
    check("V-DP-INCOMPLETE-CANNOT-BE-SHOWN", refused(lambda: dp.surface(M, "B2")) is not None)
    s = spec("B3")
    s["options"][0]["params"]["capital"] = {"ceiling": 200_000_000}
    check("V-DP-AMOUNT-WITHOUT-UNIT-INCOMPLETE", dp.create(M, s)["status"] == dp.OPEN)
    s = spec("B4")
    del s["options"][1]["params"]["efficiency"]
    check("V-DP-MISSING-DIMENSION-INCOMPLETE", dp.create(M, s)["status"] == dp.OPEN)
    s = spec("B5")
    s["options"][0]["params"]["scope"] = "WHATEVER"
    check("V-DP-VALUE-OUTSIDE-ENUM-INCOMPLETE", dp.create(M, s)["status"] == dp.OPEN)
    check("V-DP-RECOMMENDATION-MUST-BE-AN-OPTION",
          dp.create(M, spec("B6", recommendation={"token": "NOPE"}))["status"] == dp.OPEN)
    check("V-DP-NO-CONSUMER-IS-INCOMPLETE", dp.create(M, spec("B7", consumers=[]))["status"] == dp.OPEN)
    check("V-DP-DUPLICATE-ID-REFUSED", refused(lambda: dp.create(M, spec())) is not None)

    # --- Dangling decision: an unknown id is a hard failure, never recovered from prose
    check("V-DP-DANGLING-ID-IS-HARD-FAILURE", refused(lambda: dp.get(M, "ghost"), dp.DanglingDecision) is not None)
    check("V-DP-DANGLING-ON-OTHER-MISSION", refused(lambda: dp.get("m-other00001", "B"), dp.DanglingDecision)
          is not None)

    # --- Surface carries options and a recommendation that is NOT a selection
    sh = dp.surface(M, "B")
    check("V-DP-SURFACE-SHOWS-TOKENS", sh["valid_tokens"] == ["R-200", "R-REFC"] and sh["recommendation"]["token"]
          == "R-200", sh["valid_tokens"])
    check("V-DP-RECOMMENDATION-IS-NOT-RESOLUTION", dp.get(M, "B")["status"] == dp.READY
          and dp.unresolved(M).count("B") == 1)

    # --- Providerless selection: unambiguous maps, ambiguous/empty refuse and list valid tokens
    dec = dp.get(M, "B")
    check("V-DP-SHORT-TOKEN-MAPS", dp.parse_choice(dec, "aprobar DP-1 + B=R-200")[0] == "R-200")
    check("V-DP-CASE-INSENSITIVE", dp.parse_choice(dec, "r-refc")[0] == "R-REFC")
    check("V-DP-BOTH-TOKENS-AMBIGUOUS", dp.parse_choice(dec, "R-200 or R-REFC")[0] is None)
    check("V-DP-NO-TOKEN-AMBIGUOUS", dp.parse_choice(dec, "a")[0] is None)
    msg = refused(lambda: dp.resolve(M, "B", "tal vez"))
    check("V-DP-AMBIGUOUS-LISTS-VALID-TOKENS", msg is not None and "R-200" in msg and "R-REFC" in msg, msg)
    check("V-DP-AMBIGUOUS-DID-NOT-RESOLVE", dp.get(M, "B")["status"] == dp.READY)

    # --- Receipt: typed, hashed, durable, idempotent
    out = dp.resolve(M, "B", "aprobar DP-1 + B=R-200", evidence_now=spec()["evidence"], now=1_800_000_000.0)
    r = out["receipt"]
    check("V-DP-RECEIPT-TYPED", out["recorded"] and r["token"] == "R-200"
          and r["params"]["capital"] == {"ceiling": 200_000_000, "unit": "processed_tokens"}
          and r["params"]["efficiency"] == "CONTINUE_OPTIMIZATION" and len(r["sha"]) == 16, r)
    again = dp.resolve(M, "B", "R-200")
    check("V-DP-REPLAY-IS-NOOP", not again["recorded"] and again["receipt"]["sha"] == r["sha"])
    rows = [json.loads(x) for x in dp.store_path(M).read_text(encoding="utf-8").splitlines()]
    check("V-DP-REPLAY-WROTE-NOTHING", sum(1 for x in rows if x["ev"] == "resolved") == 1)
    check("V-DP-OTHER-CHOICE-AFTER-RESOLVE-REFUSED", refused(lambda: dp.resolve(M, "B", "R-REFC")) is not None)
    check("V-DP-DURABLE-ACROSS-RELOAD", dp.get(M, "B")["receipt"]["sha"] == r["sha"]
          and "B" not in dp.unresolved(M))
    check("V-DP-EFFICIENCY-SURVIVES-CAPITAL", r["params"]["efficiency"] == "CONTINUE_OPTIMIZATION")

    # --- Staleness: evidence changed between packet and answer -> invalidated, nothing applied
    dp.create(M, spec("S1"))
    stale = copy.deepcopy(spec()["evidence"])
    stale["central_scenario"] = 250_000_000
    check("V-DP-STALE-EVIDENCE-REFUSED", refused(lambda: dp.resolve(M, "S1", "R-200", evidence_now=stale)) is not None)
    check("V-DP-STALE-IS-INVALIDATED", dp.get(M, "S1")["status"] == dp.INVALIDATED
          and "receipt" not in dp.get(M, "S1"))
    dp.create(M, spec("S2"))
    ok = dp.resolve(M, "S2", "R-200", evidence_now=spec()["evidence"])
    check("V-DP-FRESH-EVIDENCE-ADMITTED", ok["recorded"])

    # --- Supersession and unreadable store
    dp.create(M, spec("S3"))
    dp.create(M, spec("S4"))
    dp.supersede(M, "S3", "S4")
    check("V-DP-SUPERSEDED", dp.get(M, "S3")["status"] == dp.SUPERSEDED and "S3" not in dp.unresolved(M)
          and "S4" in dp.unresolved(M))
    bad = "m-dptest000002"
    dp.create(bad, spec())
    with open(dp.store_path(bad), "a", encoding="utf-8") as fh:
        fh.write("{not json\n")
    check("V-DP-CORRUPT-STORE-IS-NOT-EMPTY", refused(lambda: dp.get(bad, "B")) is not None)

    # --- The CLI reaches the same code: create from file, show, resolve, replay
    cli_m = "m-dptest000003"
    f = Path(TMP) / "b.json"
    f.write_text(json.dumps(spec()), encoding="utf-8")
    run = lambda *a: subprocess.run([sys.executable, str(Path(dp.__file__)), *a], capture_output=True,  # noqa: E731
                                    text=True, timeout=60)
    c1 = run("create", "--mission", cli_m, "--file", str(f))
    c2 = run("show", "--mission", cli_m, "--decision", "B")
    c3 = run("resolve", "--mission", cli_m, "--decision", "B", "--choice", "R-200")
    c4 = run("resolve", "--mission", cli_m, "--decision", "B", "--choice", "R-200")
    c5 = run("show", "--mission", cli_m, "--decision", "ghost")
    check("V-DP-CLI-ROUNDTRIP", c1.returncode == 0 and c2.returncode == 0 and "R-200" in c2.stdout
          and c3.returncode == 0 and "recorded=True" in c3.stdout and "recorded=False" in c4.stdout,
          (c1.stdout, c3.stdout, c4.stdout))
    check("V-DP-CLI-DANGLING-EXITS-NONZERO", c5.returncode == 2 and "no durable contract" in c5.stderr, c5.stderr)

    print(f"DP_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
