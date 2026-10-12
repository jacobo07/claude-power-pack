"""7-point crash matrix for atomic succession (W4). Run: python tools/test_goal_crash_matrix.py

Prints GOALCRASH_PASS=n/m and exits 1 on any failure. For each fault point the succession process is killed
(os._exit, no unwinding), the half-state is asserted to be one of the DOCUMENTED ones, and a rerun converges to
the SAME final state as an uncrashed run: settled once, one L2, one claim, one done row.

CLAIM_LOST residue decision (pinned below): a lease that is open but whose workspace is not claimed is resumed by
the SUCCESSION side, by rerunning the same succession id (it adopts the open lease and only claims). The guard
never claims. A rival that won the workspace leaves the residue named by goal_autopsy, never a third lease.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import traceback
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
import goal_succession as gs  # noqa: E402
import test_goal_succession as tgs  # noqa: E402

M = 1_000_000
RESULTS: list[tuple[str, bool, str]] = []
GATES: list = []
FAULT_POINTS = ("before_settle", "after_settle", "after_close", "after_open", "after_claim", "before_done")


def _gate(name):
    def deco(fn):
        GATES.append((name, fn))
        return fn
    return deco


def _crash(st: Path, ws: str, point: str, **over) -> None:
    env = dict(os.environ, GSD_LONG_RUN_STATE_DIR=str(st), GOAL_SUCCESSION_FAULT=point)
    p = subprocess.run([sys.executable, str(REPO / "tools" / "goal_succession.py"), *tgs._cli_argv(ws, **over)],
                       capture_output=True, text=True, env=env, timeout=120)
    assert p.returncode == gs.FAULT_EXIT, (point, p.returncode, p.stdout, p.stderr)


def _rerun_cold(st: Path, ws: str) -> dict:
    """A fresh process holding nothing but the journals."""
    env = dict(os.environ, GSD_LONG_RUN_STATE_DIR=str(st))
    env.pop("GOAL_SUCCESSION_FAULT", None)
    p = subprocess.run([sys.executable, str(REPO / "tools" / "goal_succession.py"), *tgs._cli_argv(ws)],
                       capture_output=True, text=True, env=env, timeout=120)
    assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)
    return json.loads(p.stdout)


def _journal(root: Path, rel: str) -> list[dict]:
    p = root / rel
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.exists() else []


def _final(root: Path, led, reg, ws: str) -> dict:
    lin = led.lineage()
    h = reg.holder(ws)
    spend = _journal(root, "g/spend.journal.jsonl")
    succ = _journal(root, "g/" + gs.JOURNAL)
    return {"leases": [(x["id"], x["closed"]) for x in lin["leases"]], "total_used": lin["total_used"],
            "open": lin["open"], "holder": (h["goal"], h["lease"], h["gen"], h["holder_sid"]),
            "settles_700k": sum(1 for r in spend if r["op"] == "settle" and r["sid"] == "old" and r["measured"] == 700_000),
            "lease_opens": sum(1 for r in spend if r["op"] == "lease_open"),
            "claims": sum(1 for r in _journal(root, "workspace.journal.jsonl") if r["op"] == "claim"),
            "done_rows": sum(1 for r in succ if r["op"] == "done"),
            "authority_rows": sum(1 for r in spend if r["op"] == "authority_required")}


def _baseline() -> dict:
    st, root, led, reg, ws = tgs._world()
    assert gs.succeed(root=root, **tgs._kw(ws))["ok"]
    return _final(root, led, reg, ws)


# Documented half-states: what a crash AT the point leaves behind, before any rerun.
HALF = {
    "before_settle": lambda f, base: f["open"] == 100_000 and f["leases"] == [("L1", False)] and f["holder"][2] == 1,
    "after_settle": lambda f, base: f["open"] == 0 and f["total_used"] == 700_000 and f["leases"] == [("L1", False)]
    and f["holder"][2] == 1,
    "after_close": lambda f, base: f["leases"] == [("L1", True)] and f["lease_opens"] == 0 and f["holder"][2] == 1,
    "after_open": lambda f, base: f["leases"] == [("L1", True), ("L2", False)] and f["holder"][2] == 1,   # CLAIM_LOST residue
    "after_claim": lambda f, base: f["holder"][1:3] == ("L2", 2) and f["done_rows"] == 0,
    "before_done": lambda f, base: f["holder"][1:3] == ("L2", 2) and f["done_rows"] == 0,
}


def _make_point_gate(point: str):
    def gate():
        base = _baseline()
        st, root, led, reg, ws = tgs._world()
        _crash(st, ws, point)
        half = _final(root, led, reg, ws)
        assert HALF[point](half, base), (point, "undocumented half-state", half)
        assert half != base, (point, "the crash left no half-state: the fault point is not on the path")
        out = _rerun_cold(st, ws)
        assert out["ok"] and out["lease"] == "L2" and out["gen"] == 2, (point, out)
        done = _final(root, led, reg, ws)
        assert done == base, (point, "rerun did not converge to the uncrashed final state", done, base)
        assert done["settles_700k"] == 1 and done["lease_opens"] == 1 and done["claims"] == 2 and done["done_rows"] == 1
    return gate


for _p in FAULT_POINTS:
    GATES.append((f"V-CRASH-{_p.upper().replace('_', '-')}", _make_point_gate(_p)))


@_gate("V-CRASH-LOST-TICK-EVENT")
def _():
    import goal_chain as gc
    base = _baseline()
    st, root, led, reg, ws = tgs._world()
    plan = st / "plan.json"
    k = tgs._kw(ws)
    plan.write_text(json.dumps({x: k[x] for x in gc.PLAN_KEYS} | {"old_sid": "old", "dead": True, "measured": 700_000}))
    initial = _final(root, led, reg, ws)
    assert initial["leases"] == [("L1", False)] and initial["holder"][2] == 1                  # the event never arrived
    assert gc.react({"action": "running"}, plan, root=root)["acted"] is False                    # a non-stop row is not the event
    assert _final(root, led, reg, ws) == initial, "an undelivered stop changed state"
    out = gc.react({"action": "stopped_without_done", "unit": "W4"}, plan, root=root)           # the next tick delivers it late
    assert out["acted"] and out["succession"]["ok"], out
    assert _final(root, led, reg, ws) == base


@_gate("V-CRASH-DOUBLE-SUCCESSOR")
def _():
    base = _baseline()
    st, root, led, reg, ws = tgs._world()
    _crash(st, ws, "after_open")                                                               # successor A dies with L2 open
    rival = gs.succeed(root=root, **tgs._kw(ws, succession_id="S-rival", new_sid="rival"))
    assert not rival["ok"] and rival["status"] == "CAS_LOST", rival                              # B loses on the lease CAS
    assert _final(root, led, reg, ws)["leases"] == [("L1", True), ("L2", False)]
    out = _rerun_cold(st, ws)
    assert out["ok"], out
    done = _final(root, led, reg, ws)
    assert done == base and done["holder"][3] == "new", done                                     # A still wins; B left no trace


@_gate("V-CRASH-CONTEXT-LOSS")
def _():
    base = _baseline()
    st, root, led, reg, ws = tgs._world()
    _crash(st, ws, "after_claim")
    # Nothing but the journals survives: a cold process rebuilds from them, with the SAME arguments.
    out = _rerun_cold(st, ws)
    assert out["ok"] and not out["applied"] or out["ok"], out
    assert _final(root, led, reg, ws) == base
    again = _rerun_cold(st, ws)                                                                  # and a second cold rerun is inert
    assert again["ok"] and not again["applied"] and _final(root, led, reg, ws) == base, again


@_gate("V-CRASH-AUTHORITY-EXHAUSTION")
def _():
    st, root, led, reg, ws = tgs._world(programme=4_200_000)
    over = dict(cap=3_900_000)
    for _ in range(2):                                                                           # refused twice: still no half-state
        out = gs.succeed(root=root, **tgs._kw(ws, **over))
        assert not out["ok"] and out["status"] == "AUTHORITY_REQUIRED", out
    f = _final(root, led, reg, ws)
    assert f["leases"] == [("L1", False)] and f["lease_opens"] == 0 and f["claims"] == 1, f      # nothing half
    assert f["holder"][1:3] == ("L1", 1) and f["authority_rows"] == 1, f                         # one authority row


@_gate("V-CRASH-CLAIM-LOST-RESIDUE-PINNED")
def _():
    st, root, led, reg, ws = tgs._world()
    _crash(st, ws, "after_open")
    assert reg.holder(ws)["gen"] == 1 and len(led.lineage()["leases"]) == 2                      # lease open, workspace not claimed
    assert reg.claim(ws, "other", "L1", 1, holder_sid="rival")["ok"]                             # a rival takes gen 2
    out = gs.succeed(root=root, **tgs._kw(ws))
    assert not out["ok"] and out["status"] == "CLAIM_LOST", out                                  # the succession side retries and is refused
    assert len(led.lineage()["leases"]) == 2, "a rerun opened a third lease instead of adopting L2"
    import goal_autopsy
    rep = goal_autopsy.autopsy(root, "g")
    assert rep["unclaimed_leases"] == [{"succession_id": "S1", "lease": "L2"}], rep               # and the residue is named, not hidden
    reg2 = tgs.WorkspaceRegistry(root)
    assert reg2.holder(ws)["goal"] == "other" and reg2.holder(ws)["gen"] == 2


def main() -> int:
    for name, fn in GATES:
        try:
            fn()
            RESULTS.append((name, True, ""))
        except Exception as exc:  # noqa: BLE001
            RESULTS.append((name, False, "".join(traceback.format_exception_only(type(exc), exc)).strip()))
    ok = sum(1 for _n, p, _d in RESULTS if p)
    for name, passed, detail in RESULTS:
        print(("PASS " if passed else "FAIL ") + name + ("" if passed else f"  {detail}"))
    print(f"GOALCRASH_PASS={ok}/{len(RESULTS)}")
    return 0 if ok == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
