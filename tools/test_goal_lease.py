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
    # the reserves are part of the need: cap alone (600k) fits the 1M left, cap + reserves (1.4M) does not
    out = led.lease_open("s2", 600_000, prev_lease="L1", reserves={"proof": 400_000, "closeout": 200_000, "recovery": 200_000})
    assert not out["ok"] and out["need"] == 1_400_000, out


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
    assert not led.set_programme(10 * M, "t", inside_agent=True)["ok"]   # OCA hole: first value, no cap to inherit
    assert led.lineage()["programme"] is None
    led.declare_cap(10 * M, "t")
    assert not led.set_programme(11 * M, "t", inside_agent=True)["ok"]   # first value above the cap: refused
    assert led.set_programme(10 * M, "t", inside_agent=True)["ok"]       # first value inside the cap: inherited
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

    assert run("goal-declare", "--goal", "g", "--cap", str(10 * M), "--source", "t")[0] == 0
    assert run("goal-programme", "--goal", "g", "--value", str(11 * M), "--source", "t")[0] == 3   # OCA hole: above cap
    assert run("goal-programme", "--goal", "g", "--value", str(10 * M), "--source", "t")[0] == 0   # inherits the cap
    rc, out = run("goal-lease-open", "--goal", "g", "--succession-id", "s1", "--cap", str(4 * M),
                  "--prev-lease", "L1", "--proof", "100000", "--closeout", "100000", "--recovery", "100000")
    assert rc == 0 and out["lease"] == "L2", (rc, out)
    rc, out = run("goal-lineage", "--goal", "g")
    assert rc == 0 and [x["id"] for x in out["leases"]] == ["L1", "L2"], out
    rc, out = run("programme-status", "--goal", "g")
    assert rc == 0 and out["programme"] == 10 * M, out
    rc, out = run("goal-lease-open", "--goal", "g", "--succession-id", "s2", "--cap", str(40 * M), "--prev-lease", "L2")
    assert rc == 3 and out["status"] == "AUTHORITY_REQUIRED", (rc, out)


# --- Automatic succession (D28 Ph1b). Regression: tennis-rf L1 cap 55M ran to 64.1M with 25.9M of programme
# executable and no successor; the pane was fenced and a successor had to be opened by hand from another pane.

def _walled(tranche=None, keep=0, programme=20 * M, cap=4 * M):
    led, _s = _ledger()
    led.declare_cap(cap, "t")
    led.set_programme(programme, "t", inside_agent=False)
    if tranche is not None:
        assert led.set_succession(tranche, keep, "t", inside_agent=False)["ok"]
    led.renew("a", cap - 50_000, 100_000)                        # 50k left: less than one call + reply
    return led


@_gate("V-SUCCESSION-OFF-BY-DEFAULT")
def _():
    led = _walled()
    out = led.renew("a", 4 * M - 40_000, 100_000, per_call=60_000)
    assert not out["ok"] and "budget_spent" in out["reason"], out
    assert len(_rows(led, "lease_open")) == 0 and len(_rows(led, "tombstone")) == 1


@_gate("V-SUCCESSION-AUTO-OPEN")
def _():
    led = _walled(tranche=3 * M)
    out = led.renew("a", 4 * M - 40_000, 100_000, per_call=60_000)
    assert out["ok"] and out["lease"]["amount"] == 100_000, out
    v = led.lineage()
    assert [(x["id"], x["cap"], x["succession_id"]) for x in v["leases"]] == \
        [("L1", 4 * M, None), ("L2", 3 * M, "g:auto:L1")], v["leases"]
    assert v["leases"][0]["closed"] and not _rows(led, "tombstone") and not _rows(led, "exhausted")
    assert led.renew("a", 4 * M, 100_000, per_call=60_000)["ok"]    # the pane keeps working inside L2
    assert len(_rows(led, "lease_open")) == 1


@_gate("V-SUCCESSION-ONE-PER-LEASE")
def _():
    led = _walled(tranche=3 * M)
    assert led.renew("b", 10_000, 100_000, per_call=60_000)["ok"]   # a second pane hits the same wall first
    assert led.renew("a", 4 * M - 40_000, 100_000, per_call=60_000)["ok"]   # a fits the successor b opened
    assert led.renew("b", 20_000, 100_000, per_call=60_000)["ok"]
    assert [r["succession_id"] for r in _rows(led, "lease_open")] == ["g:auto:L1"]
    assert not _rows(led, "tombstone")


@_gate("V-SUCCESSION-TRANCHE-BOUNDED")
def _():
    led = _walled(tranche=8 * M, keep=M, programme=7 * M)        # 3.95M settled; executable 3.05M; keep 1M
    assert led.renew("a", 4 * M - 40_000, 100_000, per_call=60_000)["ok"]
    assert led.lineage()["leases"][-1]["cap"] == 7 * M - (4 * M - 40_000) - M     # never the tranche, never the keep


@_gate("V-SUCCESSION-SHORT-PROGRAMME")
def _():
    led = _walled(tranche=3 * M, keep=M, programme=5 * M)        # executable 1.05M - keep 1M < one call
    outs = [led.renew("a", 4 * M - 40_000 + i, 100_000, per_call=60_000) for i in range(3)]
    assert all(not o["ok"] for o in outs), outs
    assert not _rows(led, "lease_open") and len(_rows(led, "authority_required")) == 1, _rows(led)
    assert led.lineage()["status"] == "AUTHORITY_REQUIRED" and len(_rows(led, "tombstone")) == 1


@_gate("V-SUCCESSION-NO-USELESS-LEASE")
def _():
    # smoke 2026-10-12: a successor of 80k opened for a 50k call + 50k final reply, was refused at once, and the
    # programme shortfall never reached the Owner (status OK, no authority_required row).
    led = _walled(tranche=3 * M, programme=4 * M - 40_000 + 80_000)
    out = led.renew("a", 4 * M - 40_000, 100_000, per_call=50_000)
    assert not out["ok"] and not _rows(led, "lease_open"), (out, _rows(led, "lease_open"))
    assert len(_rows(led, "authority_required")) == 1 and led.lineage()["status"] == "AUTHORITY_REQUIRED"
    # review LOW: the Owner resolves it with a manual lease under another id -> the auto row stops counting
    led.set_programme(20 * M, "t", inside_agent=False)
    assert led.lease_open("owner-fix", 2 * M, prev_lease="L1")["ok"]
    assert led.lineage()["status"] == "OK", led.lineage()


@_gate("V-SUCCESSION-CARRIES-RESERVES")
def _():
    # review MEDIUM: an auto successor opened with {} reserves; a recovery session with 80k still funded on L2
    # was fenced RECOVERY_RESERVE_SPENT on its next renew.
    led, _s = _ledger()
    led.declare_cap(4 * M, "t")
    led.set_programme(20 * M, "t", inside_agent=False)
    led.set_succession(3 * M, 0, "t", inside_agent=False)
    led.lease_open("s1", M, prev_lease="L1", reserves={"recovery": 100_000, "closeout": 50_000})
    led.renew("a", 950_000, 100_000)
    assert led.renew("r", 20_000, 10_000, role="recovery")["ok"]
    assert led.renew("a", 960_000, 100_000, per_call=60_000)["ok"]          # L2 wall -> L3
    v = led.lineage()
    assert v["leases"][-1]["reserves"] == {"recovery": 80_000, "closeout": 50_000}, v["leases"][-1]
    assert v["leases"][-1]["cap"] == 3 * M
    out = led.renew("r", 25_000, 10_000, per_call=10_000, role="recovery")
    assert out["ok"], out


@_gate("V-SUCCESSION-UNKNOWN-PROGRAMME")
def _():
    led, _s = _ledger()
    led.declare_cap(4 * M, "t")
    led._append(led._read(), {"op": "succession", "tranche": 3 * M, "keep": 0, "source": "forged"})
    led.renew("a", 4 * M - 50_000, 100_000)
    assert not led.renew("a", 4 * M - 40_000, 100_000, per_call=60_000)["ok"]
    assert not _rows(led, "lease_open")                           # no programme: unknown headroom is not free


@_gate("V-SUCCESSION-RECOVERY-UNTOUCHED")
def _():
    led, _s = _ledger()
    led.declare_cap(4 * M, "t")
    led.set_programme(20 * M, "t", inside_agent=False)
    led.set_succession(3 * M, 0, "t", inside_agent=False)
    led.lease_open("s1", 4 * M, prev_lease="L1", reserves={"recovery": 100_000})
    led.renew("r", 90_000, 10_000, role="recovery")
    assert not led.renew("r", 95_000, 10_000, per_call=10_000, role="recovery")["ok"]
    assert [r["succession_id"] for r in _rows(led, "lease_open")] == ["s1"]


@_gate("V-SUCCESSION-OWNER-ONLY")
def _():
    led, state = _ledger()
    led.declare_cap(4 * M, "t")
    led.set_programme(20 * M, "t", inside_agent=False)
    assert not led.set_succession(3 * M, 0, "t", inside_agent=True)["ok"]       # enabling is authority
    assert led.set_succession(3 * M, M, "t", inside_agent=False)["ok"]
    assert not led.set_succession(5 * M, M, "t", inside_agent=True)["ok"]       # bigger tranche: Owner
    assert not led.set_succession(3 * M, 0, "t", inside_agent=True)["ok"]       # smaller keep: Owner
    assert led.set_succession(2 * M, 2 * M, "t", inside_agent=True)["ok"]       # tighter: admitted
    assert led.set_succession(0, 0, "t", inside_agent=True)["ok"]               # off: admitted
    assert led.lineage()["succession"] is None
    env = {**os.environ, "GSD_LONG_RUN_STATE_DIR": str(state)}
    env.pop("CLAUDECODE", None)
    p = subprocess.run([sys.executable, "-I", str(SPEND), "goal-succession", "--goal", "g", "--tranche", str(3 * M),
                        "--source", "t", "--owner"], capture_output=True, text=True, env=env, stdin=subprocess.DEVNULL)
    assert p.returncode == 3 and led.lineage()["succession"] is None, (p.returncode, p.stdout, p.stderr)
    p = subprocess.run([sys.executable, "-I", str(SPEND), "goal-succession", "--goal", "g", "--tranche", "0",
                        "--source", "t"], capture_output=True, text=True, env=env, stdin=subprocess.DEVNULL)
    assert p.returncode == 0, (p.returncode, p.stdout, p.stderr)


@_gate("V-STATUS-DENOMINATORS-LABELLED")
def _():
    # ctx-rent-a2 2026-10-23: "remaining" (lease) and "executable" (programme) were read as one quantity
    led, _s = _ledger()
    led.declare_cap(4 * M, "t")
    led.set_programme(20 * M, "t", inside_agent=False)
    led.settle_stopped("a", M, "t")
    led.lease_open("s1", 4 * M, prev_lease="L1")
    st, ps = led.status(), led.programme_status()
    assert st["lease"] == ps["lease"] == "L2", (st.get("lease"), ps["lease"])
    assert st["programme_executable"] == ps["executable"] and st["programme"] == 20 * M, st
    assert st["scope"]["remaining"] == "lease" and st["scope"]["settled"] == "goal", st.get("scope")


if __name__ == "__main__":
    mp.freeze_support()
    _run_gates()
    for name, ok, why in RESULTS:
        print(("PASS " if ok else "FAIL ") + name + ("" if ok else f" -- {why}"))
    n = sum(1 for _, ok, _w in RESULTS if ok)
    print(f"GOAL_LEASE_PASS={n}/{len(RESULTS)}")
    raise SystemExit(0 if n == len(RESULTS) else 1)
