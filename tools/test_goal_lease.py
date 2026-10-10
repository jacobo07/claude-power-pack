"""V-gates for lease epochs in GoalLedger (dgl W1b). Run: python tools/test_goal_lease.py

Prints GOAL_LEASE_PASS=n/m and exits 1 on any failure. Every test works in its own
GSD_LONG_RUN_STATE_DIR (tempfile.mkdtemp()); nothing touches ~/.claude/state.
"""
from __future__ import annotations

import json
import multiprocessing as mp
import os
import shutil
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from modules.provider_routing.ledger import GoalLedger  # noqa: E402

FIX = REPO / "tools" / "fixtures" / "goal_lease"
SPEND = REPO / "tools" / "mission_spend.py"
M = 1_000_000
RESULTS: list[tuple[str, bool, str]] = []


def _ledger(goal="g", clock=None) -> tuple[GoalLedger, Path]:
    state = Path(tempfile.mkdtemp(prefix="goal-lease-"))
    kw = {"clock": clock} if clock else {}
    return GoalLedger(state / "goal-budget" / goal, goal, **kw), state


def _rows(led, op=None):
    return [r for r in led._read() if op is None or r["op"] == op]


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


def _legacy(name, cap, used):
    led, _ = _ledger(name)
    shutil.copy(FIX / f"{name}.spend.journal.jsonl", led.journal)
    g = led._gfold(led._read())
    assert (g["cap"], g["used"]) == (cap, used), (name, g["cap"], g["used"])
    v = led.lineage()
    assert (v["cap"], v["used"]) == (cap, used) and [x["id"] for x in v["leases"]] == ["L1"], v


@_gate("V-LEASE-LEGACY-FOLD")
def _():
    _legacy("rf-p3b", 2_400_000, 3_318_702)
    _legacy("canary-20261007", 3_000_000, 3_973_468)


@_gate("V-LEASE-CAP-IMMUTABLE")
def _():
    led, _s = _ledger()
    led.declare_cap(4 * M, "t")
    led.set_programme(20 * M, "t", inside_agent=False)
    assert led.lease_open("s1", 4 * M, prev_lease="L1")["ok"]
    out = led.declare_cap(9 * M, "t", inside_agent=False, lease="L1")   # even the Owner
    assert not out["ok"] and "closed" in out["reason"], out
    led._append(led._read(), {"op": "cap", "value": 9 * M, "source": "forged", "lease": "L1"})
    v = led.lineage()
    assert v["cap"] == 4 * M and [x["cap"] for x in v["leases"]] == [4 * M, 4 * M], v


@_gate("V-LEASE-SUCCESSOR-IN-ENVELOPE")
def _():
    led, _s = _ledger()
    led.declare_cap(4 * M, "t")
    led.set_programme(10 * M, "t", inside_agent=False)
    led.renew("a", M, 100_000)                                   # 1M settled under L1
    out = led.lease_open("s1", 4 * M, prev_lease="L1", reserves={"proof": M // 2, "closeout": M // 2, "recovery": M // 2})
    assert out["ok"] and out["lease"] == "L2", out
    v = led.lineage()
    assert [x["id"] for x in v["leases"]] == ["L1", "L2"] and v["leases"][0]["closed"] and not v["leases"][1]["closed"]
    assert v["cap"] == 4 * M and v["leases"][1]["used"] == 0, v     # a fresh lease starts at zero used


@_gate("V-LEASE-ENVELOPE-EXHAUSTED")
def _():
    led, _s = _ledger()
    led.declare_cap(4 * M, "t")
    led.set_programme(5 * M, "t", inside_agent=False)
    led.renew("a", 4 * M, 100_000)                               # executable = 1M < cap 2M
    outs = [led.lease_open("s1", 2 * M, prev_lease="L1") for _ in range(4)]
    assert all(not o["ok"] for o in outs), outs
    assert len(_rows(led, "authority_required")) == 1, _rows(led, "authority_required")
    assert len(_rows(led, "lease_open")) == 0
    assert led.lineage()["status"] == "AUTHORITY_REQUIRED"


@_gate("V-LEASE-IDEMPOTENT")
def _():
    led, _s = _ledger()
    led.declare_cap(4 * M, "t")
    led.set_programme(20 * M, "t", inside_agent=False)
    a = led.lease_open("s1", 4 * M, prev_lease="L1")
    b = led.lease_open("s1", 4 * M, prev_lease="L1")
    assert a["ok"] and b["ok"] and a["lease"] == b["lease"] == "L2" and not b.get("applied", True), (a, b)
    assert len(_rows(led, "lease_open")) == 1


def _racer(args):
    root, goal, sid = args
    led = GoalLedger(Path(root), goal)
    return led.lease_open(sid, 2 * M, prev_lease="L1")


@_gate("V-LEASE-DOUBLE-RACE")
def _():
    led, _s = _ledger()
    led.declare_cap(4 * M, "t")
    led.set_programme(40 * M, "t", inside_agent=False)
    with mp.Pool(2) as pool:
        outs = pool.map(_racer, [(str(led.root), "g", "sA"), (str(led.root), "g", "sB")])
    assert sorted(o["ok"] for o in outs) == [False, True], outs
    loser = next(o for o in outs if not o["ok"])
    assert "L2" in loser["reason"], loser
    assert len(_rows(led, "lease_open")) == 1


@_gate("V-LEASE-UNKNOWN-NOT-FREE")
def _():
    led, _s = _ledger()
    led.declare_cap(3 * M, "t")
    out = led.lease_open("s1", M, prev_lease="L1")               # no programme: unknown, not unlimited
    assert not out["ok"] and "UNKNOWN" in out["reason"], out
    led.set_programme(5 * M, "t", inside_agent=False)
    led.spawn("child", 3 * M)                                    # an open hold counts against the envelope
    g = led._gfold(led._read())
    for r in g["res"].values():
        led._append(led._read(), {"op": "leak", "id": r["id"]})   # LEAKED still counts
    out = led.lease_open("s2", 3 * M, prev_lease="L1")           # executable 2M < 3M
    assert not out["ok"], out


@_gate("V-PROGRAMME-OWNER-ONLY")
def _():
    led, state = _ledger()
    assert led.set_programme(10 * M, "t", inside_agent=True)["ok"]       # first value: admitted
    assert not led.set_programme(20 * M, "t", inside_agent=True)["ok"]   # agent raise: refused
    assert led.set_programme(5 * M, "t", inside_agent=True)["ok"]        # lowering: admitted
    assert led.set_programme(20 * M, "t", inside_agent=False)["ok"]      # Owner raise
    assert led.lineage()["programme"] == 20 * M
    env = {**os.environ, "GSD_LONG_RUN_STATE_DIR": str(state)}
    env.pop("CLAUDECODE", None)
    p = subprocess.run([sys.executable, "-I", str(SPEND), "goal-programme", "--goal", "g", "--value", str(30 * M),
                        "--source", "t", "--owner"], capture_output=True, text=True, env=env, stdin=subprocess.DEVNULL)
    assert p.returncode == 3 and led.lineage()["programme"] == 20 * M, (p.returncode, p.stdout)


@_gate("V-LINEAGE-READONLY")
def _():
    led, state = _ledger(clock=lambda: 1000.0)
    led.declare_cap(4 * M, "t")
    led.set_programme(10 * M, "t", inside_agent=False)
    led.spawn("child", M)                                        # ts=1000: long past the leak window
    before = led.journal.read_bytes()
    env = {**os.environ, "GSD_LONG_RUN_STATE_DIR": str(state)}
    for cmd in ("goal-lineage", "programme-status"):
        p = subprocess.run([sys.executable, "-I", str(SPEND), cmd, "--goal", "g"], capture_output=True, text=True, env=env)
        assert p.returncode == 0, (cmd, p.returncode, p.stdout, p.stderr)
        json.loads(p.stdout)
    assert led.journal.read_bytes() == before, "a read-only command appended to the journal"
    p = subprocess.run([sys.executable, "-I", str(SPEND), "goal-status", "--goal", "g"], capture_output=True, text=True, env=env)
    assert led.journal.read_bytes() != before, "control: goal-status is expected to append a leak row"


@_gate("V-LEASE-CLI")
def _():
    state = Path(tempfile.mkdtemp(prefix="goal-lease-cli-"))
    env = {**os.environ, "GSD_LONG_RUN_STATE_DIR": str(state)}
    env.pop("CLAUDECODE", None)

    def run(*a):
        p = subprocess.run([sys.executable, "-I", str(SPEND), *a], capture_output=True, text=True, env=env,
                           stdin=subprocess.DEVNULL)
        return p.returncode, (json.loads(p.stdout) if p.stdout.strip().startswith("{") else p.stdout)

    assert run("goal-declare", "--goal", "g", "--cap", str(4 * M), "--source", "t")[0] == 0
    assert run("goal-programme", "--goal", "g", "--value", str(10 * M), "--source", "t")[0] == 0
    rc, out = run("goal-lease-open", "--goal", "g", "--succession-id", "s1", "--cap", str(4 * M),
                  "--prev-lease", "L1", "--proof", "100000", "--closeout", "100000", "--recovery", "100000")
    assert rc == 0 and out["lease"] == "L2", (rc, out)
    rc, out = run("goal-lineage", "--goal", "g")
    assert rc == 0 and [x["id"] for x in out["leases"]] == ["L1", "L2"], out
    rc, out = run("programme-status", "--goal", "g")
    assert rc == 0 and out["programme"] == 10 * M, out
    rc, out = run("goal-lease-open", "--goal", "g", "--succession-id", "s2", "--cap", str(40 * M), "--prev-lease", "L2")
    assert rc == 3 and out["status"] == "AUTHORITY_REQUIRED", (rc, out)


if __name__ == "__main__":
    mp.freeze_support()
    _run_gates()
    for name, ok, why in RESULTS:
        print(("PASS " if ok else "FAIL ") + name + ("" if ok else f" -- {why}"))
    n = sum(1 for _, ok, _w in RESULTS if ok)
    print(f"GOAL_LEASE_PASS={n}/{len(RESULTS)}")
    raise SystemExit(0 if n == len(RESULTS) else 1)
