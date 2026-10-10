"""V-gates for the dgl workspace lease registry + generation CAS (W2). Run: python tools/test_workspace_lease.py

Prints WS_LEASE_PASS=n/m and exits 1 on any failure. Every gate works in its own
GSD_LONG_RUN_STATE_DIR (tempfile.mkdtemp()); nothing touches ~/.claude/state.
"""
from __future__ import annotations

import json
import multiprocessing as mp
import os
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
from modules.provider_routing.ledger import GoalLedger  # noqa: E402
from modules.provider_routing.workspace_registry import WorkspaceRegistry  # noqa: E402

M = 1_000_000
RESULTS: list[tuple[str, bool, str]] = []
GATES: list = []


def _gate(name):
    def deco(fn):
        GATES.append((name, fn))     # run under __main__ only: multiprocessing children re-import this module
        return fn
    return deco


def _run_gates():
    for name, fn in GATES:
        try:
            fn()
            RESULTS.append((name, True, ""))
        except Exception as exc:  # noqa: BLE001 - a gate reports, never raises
            RESULTS.append((name, False, "".join(traceback.format_exception_only(type(exc), exc)).strip()))


def _state() -> Path:
    return Path(tempfile.mkdtemp(prefix="ws-lease-"))


def _reg(state: Path) -> WorkspaceRegistry:
    return WorkspaceRegistry(state / "goal-budget")


def _ledger(state: Path, goal="g") -> GoalLedger:
    led = GoalLedger(state / "goal-budget" / goal, goal)
    led.declare_cap(4 * M, "t")
    led.set_programme(20 * M, "t", inside_agent=False)
    return led


def _race_worker(root: str, ws: str, goal: str, q) -> None:
    q.put((goal, WorkspaceRegistry(root).claim(ws, goal, "L1", 0, holder_sid=goal)["ok"]))


@_gate("V-WS-CLAIM-CAS")
def _():
    r = _reg(_state())
    a = r.claim("C:/w/one", "g1", "L1", 0, holder_sid="s1")
    assert a["ok"] and a["gen"] == 1, a
    b = r.claim("C:/w/one", "g2", "L1", 1, holder_sid="s2")
    assert b["ok"] and b["gen"] == 2, b
    cur = r.holder("C:/w/one")
    assert (cur["goal"], cur["gen"], cur["holder_sid"]) == ("g2", 2, "s2"), cur


@_gate("V-WS-STALE-GEN-REFUSED")
def _():
    r = _reg(_state())
    assert r.claim("C:/w/one", "g1", "L1", 0)["ok"]
    out = r.claim("C:/w/one", "g2", "L1", 0)                 # g2 read gen 0, g1 already won gen 1
    assert not out["ok"] and "g1" in out["reason"] and out["winner"]["goal"] == "g1", out
    assert r.holder("C:/w/one")["goal"] == "g1"


@_gate("V-WS-IDEMPOTENT")
def _():
    r = _reg(_state())
    a = r.claim("C:/w/one", "g1", "L1", 0, holder_sid="s1")
    b = r.claim("C:/w/one", "g1", "L1", 0, holder_sid="s1")
    assert a["ok"] and b["ok"] and not b["applied"] and b["gen"] == 1, (a, b)
    rows = [json.loads(x) for x in r.journal.read_text().splitlines() if x.strip()]
    assert len([x for x in rows if x["op"] == "claim"]) == 1, rows


@_gate("V-WS-DOUBLE-CLAIM-RACE")
def _():
    st = _state()
    root = str(st / "goal-budget")
    ctx = mp.get_context("spawn")
    q = ctx.Queue()
    ps = [ctx.Process(target=_race_worker, args=(root, "C:/w/race", g, q)) for g in ("ga", "gb")]
    for p in ps:
        p.start()
    got = [q.get(timeout=60) for _ in ps]
    for p in ps:
        p.join(30)
    assert sorted(ok for _g, ok in got) == [False, True], got
    winner = next(g for g, ok in got if ok)
    assert _reg(st).holder("C:/w/race")["goal"] == winner


@_gate("V-WS-CWD-OBSERVE-ONLY")
def _():
    st = _state()
    r = _reg(st)
    r.claim("C:/w/one", "g1", "L1", 0)
    before = r.journal.read_bytes()
    seen = r.holder_for_cwd("C:/w/one/sub/dir")
    assert seen and seen["goal"] == "g1"
    assert r.holder_for_cwd("C:/w/elsewhere") is None
    assert r.journal.read_bytes() == before, "an observation changed the journal"
    # and the binding resolver: entering a goal root binds nothing and writes no record
    import mission_spend as ms
    os.environ["GSD_LONG_RUN_STATE_DIR"] = str(st)
    root = st / "wt"
    root.mkdir()
    (st / "goal-budget" / "index.json").write_text(json.dumps({"g9": {"roots": [str(root)]}}))
    ev = {"cwd": str(root), "tool_name": "Bash", "tool_input": {"command": "echo hi"}}
    b = ms.resolve_binding(ev, "sid-cwd-1")
    assert b is None or b.get("provisional"), b
    assert not ms.binding_path("sid-cwd-1").exists(), "cwd entry wrote a binding record"
    assert r.journal.read_bytes() == before


@_gate("V-WS-ZOMBIE-FENCED")
def _():
    st = _state()
    r = _reg(st)
    led = _ledger(st)
    assert r.claim("C:/w/one", "g", "L1", 0, holder_sid="old")["ok"]
    assert r.claim("C:/w/one", "g", "L1", 1, holder_sid="new")["ok"]       # gen 2, `old` is now a zombie
    out = r.settle(led, "C:/w/one", "g", "L1", gen=1, sid="old", measured=700_000, lease=100_000)
    assert out["fenced"] and not out["ok"], out
    assert led.lineage()["total_used"] == 700_000, led.lineage()            # booked as spend, never dropped
    assert not r.settle(led, "C:/w/one", "g", "L1", gen=1, sid="old", measured=800_000, lease=100_000)["ok"]
    assert led.lineage()["total_used"] == 800_000
    rows = [json.loads(x) for x in r.journal.read_text().splitlines() if x.strip()]
    assert sum(1 for x in rows if x["op"] == "fenced") == 2, rows
    live = r.settle(led, "C:/w/one", "g", "L1", gen=2, sid="new", measured=0, lease=100_000)
    assert live["ok"] and not live["fenced"], live                         # the holder keeps authority


@_gate("V-WS-CLOSED-LEASE-FENCED")
def _():
    st = _state()
    r = _reg(st)
    led = _ledger(st)
    assert r.claim("C:/w/one", "g", "L1", 0, holder_sid="s1")["ok"]
    assert r.authority("C:/w/one", "g", "L1", 1, ledger=led)["ok"]
    led.lease_close("L1", "done")
    a = r.authority("C:/w/one", "g", "L1", 1, ledger=led)                  # gen is current, lease is closed
    assert not a["ok"] and a["fenced"] and "closed" in a["reason"], a
    out = r.settle(led, "C:/w/one", "g", "L1", gen=1, sid="s1", measured=300_000, lease=100_000)
    assert out["fenced"] and led.lineage()["total_used"] == 300_000, out


@_gate("V-WS-PRECEDENCE")
def _():
    import mission_spend as ms
    st = _state()
    os.environ["GSD_LONG_RUN_STATE_DIR"] = str(st)
    os.environ.pop("CPP_GOAL", None)
    root = st / "wt"
    root.mkdir()
    (st / "goal-budget").mkdir(exist_ok=True)
    (st / "goal-budget" / "index.json").write_text(json.dumps({"g-root": {"roots": [str(root)]}, "g-reg": {"roots": []}}))
    assert _reg(st).claim(str(root), "g-reg", "L1", 0, holder_sid="s1")["ok"]
    ev = {"cwd": str(root), "tool_name": "Bash", "tool_input": {"command": "echo hi"}}
    b = ms.resolve_binding(ev, "sid-prec-1")
    assert b and b["goal"] == "g-reg", b                                   # registry holder beats the root match


def main() -> int:
    _run_gates()
    ok = sum(1 for _n, p, _d in RESULTS if p)
    for name, passed, detail in RESULTS:
        print(("PASS " if passed else "FAIL ") + name + ("" if passed else f"  {detail}"))
    print(f"WS_LEASE_PASS={ok}/{len(RESULTS)}")
    return 0 if ok == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
