"""V-gates for lease attribution (Tramo A2 Phase 7, A2-18). Run: python tools/test_lease_consumers.py

Prints LEASE_CONSUMERS_PASS=n/m and exits 1 on any failure. Own temp state dir per test; ~/.claude/state untouched.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from modules.provider_routing.ledger import GoalLedger, lease_contention  # noqa: E402

M = 1_000_000
GATES: list = []


def _gate(name):
    def deco(fn):
        GATES.append((name, fn))
        return fn
    return deco


def _led(clock):
    state = Path(tempfile.mkdtemp(prefix="lease-cons-"))
    led = GoalLedger(state / "goal-budget" / "g", "g", clock=clock)
    led.declare_cap(10 * M, "t")
    return led, state


@_gate("V-CONS-SHARE-AND-BURN")
def _():
    t = [1_000_000.0]
    led, _s = _led(lambda: t[0])
    led.renew("a", M, 100_000)           # a settles 1M
    t[0] += 60
    led.renew("b", 3 * M, 100_000)       # b settles 3M a minute later
    c = led.consumers(now=t[0] + 60)
    rows = {r["sid"]: r for r in c["consumers"]}
    assert rows["a"]["share"] == 0.25 and rows["b"]["share"] == 0.75, rows
    assert rows["b"]["burn_per_hour"] == 3 * M and rows["b"]["live"], rows
    assert c["lease"] == "L1" and c["used"] >= 4 * M, c
    assert [r["sid"] for r in c["consumers"]] == ["b", "a"], "sorted by spend"


@_gate("V-CONS-LIVE-WINDOW")
def _():
    t = [2_000_000.0]
    led, _s = _led(lambda: t[0])
    led.renew("a", M, 100_000)
    c = led.consumers(now=t[0] + 7200)    # two hours later: not live, no burn in the 1h window
    r = c["consumers"][0]
    assert not r["live"] and r["burn_per_hour"] == 0 and c["live_burn_per_hour"] == 0, c


@_gate("V-CONS-READ-ONLY")
def _():
    t = [3_000_000.0]
    led, _s = _led(lambda: t[0])
    led.renew("a", M, 100_000)
    before = led._read()
    led.consumers(now=t[0] + 10)
    assert led._read() == before, "consumers() must not append"


@_gate("V-CONS-EMPTY-NOT-ZERO-SHARE")
def _():
    led, _s = _led(lambda: 4_000_000.0)
    c = led.consumers()
    assert c["consumers"] == [] and c["live_burn_per_hour"] == 0 and c["remaining"] == 10 * M, c


@_gate("V-CONTENTION-BOTH-POLES")
def _():
    w = lease_contention(5 * M, 6 * M, 500_000, 4)           # 6M - 2M = 4M < 5M authority
    assert w and w["code"] == "SHARED_LEASE_CONTENTION" and w["left_after_siblings"] == 4 * M, w
    assert lease_contention(3 * M, 6 * M, 500_000, 4) is None       # control: envelope survives
    assert lease_contention(5 * M, 6 * M, 0, 4) is None              # no siblings, no warning
    assert lease_contention(None, 6 * M, 9 * M, 4) is None and lease_contention(5 * M, None, 9 * M, 4) is None


@_gate("V-CONS-CLI")
def _():
    t = [5_000_000.0]
    led, state = _led(lambda: t[0])
    led.renew("a", M, 100_000)
    env = dict(os.environ, GSD_LONG_RUN_STATE_DIR=str(state))
    out = subprocess.run([sys.executable, str(REPO / "tools" / "mission_spend.py"), "goal-status", "--goal", "g", "--consumers"],
                         env=env, capture_output=True, text=True, timeout=60)
    d = json.loads(out.stdout)
    assert out.returncode == 0 and d["ok"] and d["consumers"][0]["sid"] == "a" and d["consumers"][0]["share"] == 1.0, out.stdout + out.stderr


if __name__ == "__main__":
    res = []
    for name, fn in GATES:
        try:
            fn()
            res.append((name, True, ""))
        except Exception as exc:  # noqa: BLE001 -- a failing gate is reported by name
            res.append((name, False, f"{type(exc).__name__}: {exc}"))
    for name, ok, why in res:
        print(("PASS " if ok else "FAIL ") + name + ("" if ok else f" -- {why}"))
    n = sum(1 for _, ok, _w in res if ok)
    print(f"LEASE_CONSUMERS_PASS={n}/{len(res)}")
    raise SystemExit(0 if n == len(res) else 1)
