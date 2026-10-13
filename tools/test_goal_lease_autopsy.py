"""V-AUTOPSY gates for tools/goal_autopsy.py and the pre-W1 migration canary (W4).
Run: python tools/test_goal_lease_autopsy.py   Prints GOALAUTOPSY_PASS=n/m and exits 1 on any failure.

Every gate works in its own GSD_LONG_RUN_STATE_DIR (tempfile.mkdtemp()); nothing touches ~/.claude/state.
"""
from __future__ import annotations

import json
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
import goal_succession as gs  # noqa: E402
import test_goal_succession as tgs  # noqa: E402

M = 1_000_000
RESULTS: list[tuple[str, bool, str]] = []
GATES: list = []


def _gate(name):
    def deco(fn):
        GATES.append((name, fn))
        return fn
    return deco


def _bind(st: Path, sid: str, goal: str = "g") -> None:
    d = st / "goal-binding"
    d.mkdir(exist_ok=True)
    (d / f"{sid}.json").write_text(json.dumps({"goal": goal, "since_ts": "2026-10-10T00:00:00", "source": "cwd"}))


def _snapshot(st: Path) -> dict:
    return {str(p.relative_to(st)): p.read_bytes() for p in sorted(st.rglob("*"))
            if p.is_file() and p.suffix in (".jsonl", ".json")}


def _ap():
    import goal_autopsy
    return goal_autopsy


@_gate("V-AUTOPSY-REPORTS-DISCREPANCIES")
def _():
    st, root, led, reg, ws = tgs._world()                     # sid `old` holds a lease reservation, no binding
    assert led.renew("bound-settled", 300_000, 100_000)["ok"]
    led.settle_stopped("bound-settled", 400_000, "t")
    assert led.renew("bound-open", 0, 100_000)["ok"]
    for sid in ("bound-settled", "bound-open", "bound-nohold"):
        _bind(st, sid)
    _bind(st, "elsewhere", goal="other")
    rep = _ap().autopsy(root, "g")
    assert rep["state"] == "OK", rep
    assert rep["bound_unsettled"] == ["bound-nohold", "bound-open"], rep
    assert rep["holds_no_binding"] == ["old"], rep
    assert rep["bindings_no_hold"] == ["bound-nohold"], rep
    assert "bound-settled" in rep["bound_settled"] and "elsewhere" not in json.dumps(rep), rep
    assert "old" in rep["settled_unbound"], rep               # world() settled `old` at 500K with no binding


@_gate("V-AUTOPSY-UNKNOWN-PAST-TTL")
def _():
    st, root, led, reg, ws = tgs._world()
    gs.reconcile(root, "g", "old", dead=False, measured=None, now=1000.0, ttl=600)
    inside = _ap().autopsy(root, "g", now=1500.0, ttl=600)
    past = _ap().autopsy(root, "g", now=1601.0, ttl=600)
    assert inside["unknown_past_ttl"] == [], inside              # control: inside the TTL nothing is reported
    assert [x["sid"] for x in past["unknown_past_ttl"]] == ["old"], past
    gs.reconcile(root, "g", "old", dead=True, measured=700_000, now=1700.0)
    assert _ap().autopsy(root, "g", now=1800.0, ttl=600)["unknown_past_ttl"] == [], "a settled sid is not unknown"


@_gate("V-AUTOPSY-UNCLAIMED-LEASE")
def _():
    st, root, led, reg, ws = tgs._world()
    assert reg.claim(ws, "other", "L1", 1, holder_sid="rival")["ok"]          # a rival wins the workspace first
    out = gs.succeed(root=root, **tgs._kw(ws))
    assert not out["ok"] and out["status"] == "CLAIM_LOST", out
    rep = _ap().autopsy(root, "g")
    assert rep["unclaimed_leases"] == [{"succession_id": "S1", "lease": "L2"}], rep
    assert [x["succession_id"] for x in rep["incomplete_successions"]] == ["S1"], rep
    st2, root2, led2, reg2, ws2 = tgs._world()
    assert gs.succeed(root=root2, **tgs._kw(ws2))["ok"]
    clean = _ap().autopsy(root2, "g")
    assert clean["unclaimed_leases"] == [] and clean["incomplete_successions"] == [], clean   # control


@_gate("V-AUTOPSY-APPENDS-NOTHING")
def _():
    st, root, led, reg, ws = tgs._world()
    _bind(st, "bound-nohold")
    gs.reconcile(root, "g", "old", dead=False, measured=None, now=1000.0)
    reg.claim(ws, "other", "L1", 1, holder_sid="rival")
    gs.succeed(root=root, **tgs._kw(ws))
    before = _snapshot(st)
    _ap().autopsy(root, "g", now=99999.0)
    env = dict(os.environ, GSD_LONG_RUN_STATE_DIR=str(st))
    p = subprocess.run([sys.executable, str(REPO / "tools" / "goal_autopsy.py"), "--goal", "g"], capture_output=True,
                       text=True, env=env, timeout=120)
    assert p.returncode in (0, 3) and json.loads(p.stdout)["goal"] == "g", (p.returncode, p.stdout, p.stderr)
    assert _snapshot(st) == before, "an autopsy changed a journal or a binding"


@_gate("V-MIGRATION-CANARY-PRE-W1")
def _():
    st = Path(tempfile.mkdtemp(prefix="canary-"))
    root = st / "goal-budget"
    led = GoalLedger(root / "g", "g")
    led.declare_cap(4 * M, "t")                                 # a pre-W1 journal: cap + renew, no programme / lease rows
    assert led.renew("s", 500_000, 100_000)["ok"]
    spend = root / "g" / "spend.journal.jsonl"
    ops = [json.loads(x)["op"] for x in spend.read_text().splitlines() if x.strip()]
    assert "programme" not in ops and "lease_open" not in ops, ops
    lin = led.lineage()
    golden = (lin["cap"], lin["used"], lin["total_used"], lin["open"], [x["id"] for x in lin["leases"]], lin["programme"])
    assert golden == (4 * M, 600_000, 600_000, 100_000, ["L1"], None), golden
    before = spend.read_bytes()
    rep = _ap().autopsy(root, "g")
    assert rep["state"] == "UNKNOWN" and "programme" in rep["reason"], rep
    out = gs.succeed("g", "S1", "L1", 2 * M, {}, str(st / "wt"), 0, "new", root=root)    # no old holder to settle
    assert not out["ok"] and out["status"] == "UNKNOWN" and "programme" in out["reason"], out
    assert spend.read_bytes() == before, "a refusal invented headroom / wrote a row"
    again = led.lineage()
    assert (again["cap"], again["used"], again["total_used"], again["open"], again["programme"]) == golden[:4] + (None,), again
    assert not (root / "workspace.journal.jsonl").exists(), "a refused succession claimed a workspace"


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
    print(f"GOALAUTOPSY_PASS={ok}/{len(RESULTS)}")
    return 0 if ok == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
