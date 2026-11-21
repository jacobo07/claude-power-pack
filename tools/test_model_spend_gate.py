#!/usr/bin/env python3
"""V-MSG-* -- BAMR obligation 5: the seven `claude -p` tools ask the account governor before they spawn.

Every tool is driven through its real spawning function with `subprocess.run` replaced by a spy that counts
`claude -p` argvs and never starts a process. The governor reads an EMPTY isolated state dir, which is an unknown
quota, so it must refuse: zero spawns. Each refusal gate fails if that tool's check is removed. Each control runs
the same call with CPP_MODEL_SPEND_ADMISSION=off and must see a spawn, so "zero" is an answer the spy can also
give the other way. No model is called and the real governor ledger is never written.
Run: python tools/test_model_spend_gate.py   (exit 0 = all gates pass)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
os.environ.pop("CPP_GOVERNOR_UNKNOWN", None)          # the fail-open kill switch must not leak in
os.environ.pop("CPP_MODEL_SPEND_ADMISSION", None)
STATE = tempfile.mkdtemp(prefix="v-msg-state-")
os.environ["CPP_MODEL_SPEND_STATE_DIR"] = STATE

import model_spend_gate as G  # noqa: E402

RESULTS: list = []


def ok(name: str, cond: bool, detail="") -> None:
    RESULTS.append((name, bool(cond)))
    print("  %s %-42s %s" % ("PASS" if cond else "FAIL", name, "" if cond else str(detail)[:300]))


class Spy:
    """Counts `claude -p` spawns and starts none; anything else passes through to the real call."""
    def __enter__(self):
        self.real, self.spawns = subprocess.run, 0

        def fake(argv, *a, **kw):
            if isinstance(argv, (list, tuple)) and "-p" in [str(x) for x in argv]:
                self.spawns += 1
                return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
            return self.real(argv, *a, **kw)
        subprocess.run = fake
        return self

    def __exit__(self, *exc):
        subprocess.run = self.real
        return False


class Switch:
    def __init__(self, off: bool):
        self.off = off

    def __enter__(self):
        if self.off:
            os.environ[G.SWITCH] = "off"

    def __exit__(self, *exc):
        os.environ.pop(G.SWITCH, None)
        return False


def drive(call, off: bool):
    """(spawns, returned value or None, exception or None)."""
    with Switch(off), Spy() as spy:
        try:
            val = call()            # first: the count is read AFTER the call
            return spy.spawns, val, None
        except Exception as exc:  # noqa: BLE001 -- the gate's raise, or a post-spawn parse of the spy's empty output
            return spy.spawns, None, exc


def tmp() -> Path:
    return Path(tempfile.mkdtemp(prefix="v-msg-"))


def tool_cases() -> list:
    import agent_carrier_run as acr
    import agent_discovery_curve as adc
    import asc_design_gate_run as adg
    import asc_inherit_run as air
    import ccn_bench as cb
    import compound_unattended as cu
    import exp_successor_packet as esp
    real_which = acr.shutil.which
    acr.shutil.which = lambda name: "claude" if name == "claude" else real_which(name)
    sunk: list = []
    d = tmp()

    def carrier():
        return acr.run("silent-failure-hunter", "check this service for swallowed errors v-msg",
                       sink=lambda k, pl: sunk.append(k) or True, timeout=5)
    # (name, call, how a refusal shows: "raise" -> SpendRefused, else a predicate on the returned value)
    return sunk, [
        ("ASC-DESIGN-GATE-CALL", lambda: adg.call(["claude", "-p", "x"], d, d / "s.jsonl", dict(os.environ)), "raise"),
        ("ASC-DESIGN-GATE-JUDGE", lambda: adg.blind_judge("saas", tmp(), 1), "raise"),
        ("ASC-INHERIT", lambda: air.run("control", None, out=tmp(), task="x"), "raise"),
        ("AGENT-CARRIER", carrier, lambda r: r.get("status") == "UNMEASURED" and r.get("account_refused")),
        ("COMPOUND-UNATTENDED", lambda: cu.run_one(str(tmp()), 5, False),
         lambda r: r.get("verdict") == "REFUSED_ACCOUNT"),
        ("CCN-BENCH", lambda: cb.run_one({"id": "q", "prompt": "x"}, "m", 0, "n", str(tmp())),
         lambda r: bool(r.get("refused")) and "cost_usd" not in r and "passed" not in r),
        ("EXP-SUCCESSOR-PACKET", lambda: esp._run_one("x"), "raise"),
        ("AGENT-DISCOVERY-CURVE", lambda: adc.measure(tmp(), "haiku", 5),
         lambda r: r.get("status") == "UNMEASURED" and r.get("account_refused")),
    ]


def main() -> int:
    print("[gate] the shared check")
    why = G.refusal("t")
    ok("V-MSG-UNKNOWN-REFUSES", why and "REFUSE+UNKNOWN" in why and why.startswith("t: "), why)
    rows = [json.loads(x) for x in Path(STATE, "account-governor-ledger.jsonl").read_text(encoding="utf-8").splitlines()]
    ok("V-MSG-LEDGER-ISOLATED", rows and rows[-1]["action"] == G.ACTION, rows[-1:])
    try:
        G.require("t")
        ok("V-MSG-REQUIRE-RAISES", False, "no raise")
    except G.SpendRefused as exc:
        ok("V-MSG-REQUIRE-RAISES", "REFUSE+UNKNOWN" in str(exc), exc)
    import account_governor as ag
    real_check = ag.check
    try:
        ag.check = lambda *a, **k: (_ for _ in ()).throw(OSError("disk"))
        why = G.refusal("t")
        ok("V-MSG-FAULT-REFUSES", why and "governor fault" in why and "OSError" in why, why)
        ag.check = lambda *a, **k: (0, "ALLOW+OFFICIAL", "official weekly 18.0%", {})
        ok("V-MSG-ALLOW-ADMITS", G.refusal("t") is None)
        ag.check = lambda *a, **k: (3, "REFUSE", "official weekly 91.0% >= 85%", {})
        why = G.refusal("t")
        ok("V-MSG-REFUSE-NAMES-TOOL", why == "t: REFUSE: official weekly 91.0% >= 85%", why)
    finally:
        ag.check = real_check
    with Switch(True):
        ok("V-MSG-KILL-SWITCH", G.refusal("t") is None)

    print("[tools] each spawn is behind the check (empty state = unknown quota)")
    sunk, cases = tool_cases()
    for name, call, refused_shape in cases:
        n, val, exc = drive(call, off=False)
        if refused_shape == "raise":
            shown = isinstance(exc, G.SpendRefused)
        else:
            shown = exc is None and bool(refused_shape(val or {}))
        ok("V-MSG-%s-REFUSED" % name, n == 0 and shown, {"spawns": n, "value": val, "exc": repr(exc)})
        if name == "AGENT-CARRIER":
            ok("V-MSG-AGENT-CARRIER-NO-ACCOUNTING", not sunk, sunk)   # never started -> no agent_run signal
        n, val, exc = drive(call, off=True)
        ok("V-MSG-%s-CONTROL-SPAWNS" % name, n >= 1 and not isinstance(exc, G.SpendRefused),
           {"spawns": n, "exc": repr(exc)})

    print("[ccn_bench] a refusal inside a wave keeps the wave's spent cells")
    import argparse
    import ccn_bench as cb
    import threading
    saved = (cb.run_one, cb.ccn_census.free_ram_mb, cb.RUBRIC, cb.MODES)
    rub = tmp() / "rubric.json"
    rub.write_text(json.dumps({"questions": [{"id": "q%d" % i, "prompt": "x"} for i in range(4)]}), encoding="utf-8")
    first, lock = {}, threading.Lock()

    def fake_one(q, mode, rep, cell, wt):       # one 4-wide wave: exactly one cell refused, three spend
        with lock:
            mine = not first
            if mine:
                first["qid"] = q["id"]
        if mine:
            return {"qid": q["id"], "mode": mode, "repeat": rep, "refused": "ccn_bench: REFUSE: test"}
        return {"qid": q["id"], "mode": mode, "repeat": rep, "rc": 0, "cost_usd": 0.5, "passed": True}
    out = tmp()
    try:
        cb.run_one, cb.ccn_census.free_ram_mb, cb.RUBRIC, cb.MODES = fake_one, (lambda: None), str(rub), (("P4", 4),)
        raised = None
        try:
            cb.cmd_run(argparse.Namespace(out=str(out), worktree=str(ROOT), repeats=1, budget_usd=100.0))
        except G.SpendRefused as exc:
            raised = exc
    finally:
        cb.run_one, cb.ccn_census.free_ram_mb, cb.RUBRIC, cb.MODES = saved
    rows = cb.load_runs(str(out / "runs.jsonl"))
    ok("V-MSG-CCN-WAVE-RAISES", raised is not None, raised)
    ok("V-MSG-CCN-WAVE-KEEPS-SPENT-CELLS", rows and all(r.get("cost_usd") == 0.5 for r in rows), rows)
    ok("V-MSG-CCN-WAVE-REFUSAL-NOT-A-CELL", first and all(r["qid"] != first["qid"] for r in rows), [first, rows])

    failed = [n for n, p in RESULTS if not p]
    print("\n%d/%d passed" % (len(RESULTS) - len(failed), len(RESULTS)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
