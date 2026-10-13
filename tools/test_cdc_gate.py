#!/usr/bin/env python3
"""Tests for cdc_gate.py / cdc_handoff.py (CDC C11). Run: python tools/test_cdc_gate.py"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cdc_gate as G  # noqa: E402
import cdc_handoff as H  # noqa: E402

fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


def mk_home(tmp, dispatcher):
    h = tmp
    (h / "hooks").mkdir(parents=True)
    (h / "hooks" / "hook-dispatcher.js").write_text(dispatcher, encoding="utf-8")
    return h


tmp = Path(tempfile.mkdtemp(prefix="tcdcgate-"))
try:
    base = tmp / "r"
    shutil.copytree(G.ROOT / G.PROG, base / G.PROG, ignore=shutil.ignore_patterns("*.log"))
    for f in ("tools", "hooks", "vault/config", "vault/lessons"):
        shutil.copytree(G.ROOT / f, base / f, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "_tests"))
    home_bad = mk_home(tmp / "hb", "// nothing")
    res = G.evaluate(base, home_bad)
    gates = {g["gate"]: g for g in res["gates"]}
    check("24 gates", len(res["gates"]) == 24 and sorted(gates) == list(range(1, 25)))
    check("2/4/5 external limitation", all(gates[n]["status"] == G.EXT for n in (2, 4, 5)))
    check("9/17/22 unknown, never pass", all(gates[n]["status"] == G.UNKNOWN for n in (9, 17, 22)))
    check("unknown not counted pass", res["summary"][G.PASS] == sum(1 for g in res["gates"] if g["status"] == G.PASS))
    check("not all_pass with unknowns", res["all_pass"] is False)
    check("16 FAIL out of scope when dispatcher lacks guards", gates[16]["status"] == G.FAIL and gates[16]["in_scope"] is False)
    home_ok = mk_home(tmp / "ho", "// cognitive_admission semantic_breaker")
    check("16 flips on deployed dispatcher", {g["gate"]: g for g in G.evaluate(base, home_ok)["gates"]}[16]["status"] == G.PASS)

    # planted missing artifacts flip to FAIL (control above is not FAIL)
    for gate_n, rel in ((12, G.EV / "cognitive-pgo.json"), (8, G.EV / "C6-proof.jsonl"), (3, Path("tools/cognitive_effects.py")),
                        (14, G.EV / "holdouts.json"), (19, G.EV / "C9-retirements.md")):
        before = {g["gate"]: g for g in G.evaluate(base, home_bad)["gates"]}[gate_n]["status"]
        p = base / rel
        bak = p.read_bytes()
        p.unlink()
        after = {g["gate"]: g for g in G.evaluate(base, home_bad)["gates"]}[gate_n]
        p.write_bytes(bak)
        check(f"gate {gate_n}: {before} -> FAIL on missing {rel.name}", before != G.FAIL and after["status"] == G.FAIL and "missing" in after["reason"])

    # receipt not DONE -> FAIL
    rp = base / G.PROG / "WU-C7-receipt.md"
    orig = rp.read_text(encoding="utf-8")
    rp.write_text(orig.replace("Status: DONE", "Status: PARTIAL"), encoding="utf-8")
    check("receipt not DONE -> gate 10 FAIL", {g["gate"]: g for g in G.evaluate(base, home_bad)["gates"]}[10]["status"] == G.FAIL)
    rp.write_text(orig, encoding="utf-8")

    # marker removed -> UNKNOWN, not PASS
    rp.write_text(orig.replace("land_worktree refuses COGNITIVE_REGRESSION", "x"), encoding="utf-8")
    check("missing PROVEN marker -> UNKNOWN", {g["gate"]: g for g in G.evaluate(base, home_bad)["gates"]}[10]["status"] == G.UNKNOWN)
    rp.write_text(orig, encoding="utf-8")

    # kill switch name removed -> gate 21 FAIL
    kp = base / "hooks/semantic_breaker.js"
    ko = kp.read_text(encoding="utf-8")
    kp.write_text(ko.replace("CPP_SEM_BREAKER", "XX"), encoding="utf-8")
    check("kill switch gone -> gate 21 FAIL", {g["gate"]: g for g in G.evaluate(base, home_bad)["gates"]}[21]["status"] == G.FAIL)
    kp.write_text(ko, encoding="utf-8")

    # lesson missing -> 23 FAIL
    lp = base / "vault/lessons/cdc-hub-closure-not-local.md"
    lb = lp.read_bytes()
    lp.unlink()
    check("lesson missing -> gate 23 FAIL", {g["gate"]: g for g in G.evaluate(base, home_bad)["gates"]}[23]["status"] == G.FAIL)
    lp.write_bytes(lb)

    # handoff: deterministic, stamped, gate 24 reads it
    (base / G.EV / "cdc-gate.json").write_text(json.dumps(G.evaluate(base, home_bad)), encoding="utf-8")
    a = H.render(base)
    check("handoff deterministic", a == H.render(base))
    check("handoff stamped", "rendered by tools/cdc_handoff.py" in a and "| C10 | DONE |" in a)
    hp = base / G.PROG / "HANDOFF.md"
    hp.write_text("hand written", encoding="utf-8")
    check("hand-written handoff -> gate 24 FAIL", {g["gate"]: g for g in G.evaluate(base, home_bad)["gates"]}[24]["status"] == G.FAIL)
    hp.write_text(a, encoding="utf-8")
    check("rendered handoff -> gate 24 PASS", {g["gate"]: g for g in G.evaluate(base, home_bad)["gates"]}[24]["status"] == G.PASS)

    check("selftest passes", G.selftest() == 0)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print(f"{'FAILED' if fails else 'all passed'}: {len(fails)} failed")
sys.exit(1 if fails else 0)
