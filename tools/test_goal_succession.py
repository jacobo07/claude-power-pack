"""V-gates for dgl terminal reconciliation + atomic succession (W3). Run: python tools/test_goal_succession.py

Prints SUCCESSION_PASS=n/m and exits 1 on any failure. Every gate works in its own
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
import goal_succession as gs  # noqa: E402

M = 1_000_000
RESULTS: list[tuple[str, bool, str]] = []
GATES: list = []
PY = sys.executable


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


def _world(programme: int = 20 * M):
    """Goal g, lease L1 (cap 4M), `old` holds an open lease reservation and holds the workspace at gen 1."""
    st = Path(tempfile.mkdtemp(prefix="succ-"))
    root = st / "goal-budget"
    led = GoalLedger(root / "g", "g")
    led.declare_cap(4 * M, "t")
    led.set_programme(programme, "t", inside_agent=False)
    assert led.renew("old", 500_000, 100_000)["ok"]
    ws = str(st / "wt")
    reg = WorkspaceRegistry(root)
    assert reg.claim(ws, "g", "L1", 0, holder_sid="old")["ok"]
    return st, root, led, reg, ws


def _kw(ws: str, **over) -> dict:
    base = dict(goal="g", succession_id="S1", prev_lease="L1", cap=2 * M, reserves={"proof": 100_000},
                workspace=ws, expect_gen=1, new_sid="new", old_sid="old", dead=True, measured=700_000)
    base.update(over)
    return base


def _bytes(root: Path) -> tuple:
    files = [root / "g" / "spend.journal.jsonl", root / "workspace.journal.jsonl", root / "g" / gs.JOURNAL]
    return tuple(p.read_bytes() if p.exists() else b"" for p in files)


def _race_worker(root: str, ws: str, sid: str, q) -> None:
    out = gs.succeed(root=root, **_kw(ws, succession_id=sid, new_sid="new-" + sid))
    q.put((sid, out["ok"], out["status"]))


@_gate("V-SUCC-TERMINAL-SETTLED")
def _():
    st, root, led, reg, ws = _world()
    out = gs.succeed(root=root, **_kw(ws))
    assert out["ok"] and out["status"] == "SUCCEEDED" and out["applied"] and out["lease"] == "L2", out
    assert out["reconcile"]["state"] == "TERMINAL_PROVEN", out
    lin = led.lineage()
    assert lin["total_used"] == 700_000 and lin["open"] == 0, lin           # measured booked, every hold closed
    assert [x["closed"] for x in lin["leases"]] == [True, False], lin["leases"]
    h = reg.holder(ws)
    assert (h["lease"], h["gen"], h["holder_sid"]) == ("L2", 2, "new"), h


@_gate("V-SUCC-UNKNOWN-RESERVED-HOLDS")
def _():
    for over in (dict(dead=False), dict(dead=True, measured=None)):          # not proven / spend not measured
        st, root, led, reg, ws = _world()
        out = gs.succeed(root=root, **_kw(ws, **over))
        assert not out["ok"] and out["status"] == "UNKNOWN_RESERVED", out
        lin = led.lineage()
        assert lin["open"] == 100_000 and lin["total_used"] == 600_000, lin   # the hold stays reserved, unknown is not free
        assert not lin["leases"][0]["closed"] and len(lin["leases"]) == 1, lin
        h = reg.holder(ws)
        assert (h["lease"], h["gen"]) == ("L1", 1), h                         # the old holder still holds
    ctl = gs.reconcile(root, "g", "old", dead=True, measured=700_000, now=1000.0)   # control: proof => terminal
    assert ctl["state"] == "TERMINAL_PROVEN" and led.lineage()["open"] == 0, ctl


@_gate("V-SUCC-TTL-SWEEP-MEASURED-ONLY")
def _():
    st, root, led, reg, ws = _world()
    t0, ttl = 10_000.0, 600
    r0 = gs.reconcile(root, "g", "old", dead=False, measured=None, now=t0, ttl=ttl)
    assert r0["state"] == "UNKNOWN_RESERVED" and led.lineage()["open"] > 0, r0
    for when, measured, why in ((t0 + ttl - 1, 700_000, "inside the TTL, even with a measure"),
                                (t0 + ttl + 1, None, "past the TTL but nothing measured")):
        s = gs.sweep_unknown(root, "g", "old", measured=measured, now=when, ttl=ttl)
        assert s["state"] == "UNKNOWN_RESERVED", (why, s)
        lin = led.lineage()
        assert lin["open"] == 100_000 and lin["total_used"] == 600_000, (why, lin)   # never freed on a clock alone
    s = gs.sweep_unknown(root, "g", "old", measured=700_000, now=t0 + ttl + 1, ttl=ttl)
    assert s["state"] == "SWEPT_MEASURED", s
    lin = led.lineage()
    assert lin["open"] == 0 and lin["total_used"] == 700_000, lin             # converted by the measured value only


@_gate("V-SUCC-IDEMPOTENT")
def _():
    st, root, led, reg, ws = _world()
    a = gs.succeed(root=root, **_kw(ws))
    before = _bytes(root)
    b = gs.succeed(root=root, **_kw(ws))
    assert a["ok"] and b["ok"] and a["applied"] and not b["applied"], (a, b)
    assert (a["lease"], a["gen"]) == (b["lease"], b["gen"]) == ("L2", 2), (a, b)
    assert _bytes(root) == before, "a repeated succession id changed a journal"
    assert len(led.lineage()["leases"]) == 2 and led.lineage()["total_used"] == 700_000


@_gate("V-SUCC-RESUME-AFTER-CRASH")
def _():
    st, root, led, reg, ws = _world()
    env = dict(os.environ, GSD_LONG_RUN_STATE_DIR=str(st), GOAL_SUCCESSION_FAULT="after_close")
    argv = _cli_argv(ws)
    p = subprocess.run([PY, str(REPO / "tools" / "goal_succession.py"), *argv], capture_output=True, text=True,
                       env=env, timeout=120)
    assert p.returncode == gs.FAULT_EXIT, (p.returncode, p.stdout, p.stderr)  # killed between close and open
    lin = led.lineage()
    assert [x["closed"] for x in lin["leases"]] == [True] and lin["open"] == 0, lin   # close landed, open did not
    assert reg.holder(ws)["gen"] == 1
    out = gs.succeed(root=root, **_kw(ws))                                    # same id, no fault: converges
    assert out["ok"] and out["lease"] == "L2" and reg.holder(ws)["gen"] == 2, out
    lin = led.lineage()
    assert len(lin["leases"]) == 2 and lin["total_used"] == 700_000, lin       # settled once, opened once


@_gate("V-SUCC-DOUBLE-SUCCESSOR-RACE")
def _():
    st, root, led, reg, ws = _world()
    ctx = mp.get_context("spawn")
    q = ctx.Queue()
    ps = [ctx.Process(target=_race_worker, args=(str(root), ws, sid, q)) for sid in ("ra", "rb")]
    for p in ps:
        p.start()
    got = [q.get(timeout=90) for _ in ps]
    for p in ps:
        p.join(30)
    assert sorted(ok for _s, ok, _st in got) == [False, True], got
    win = next(s for s, ok, _st in got if ok)
    h = reg.holder(ws)
    assert h["gen"] == 2 and h["holder_sid"] == "new-" + win and h["lease"] == "L2", (h, got)
    lin = led.lineage()
    assert len(lin["leases"]) == 2 and lin["total_used"] == 700_000, lin


@_gate("V-SUCC-AUTHORITY-REQUIRED-NO-HALF")
def _():
    st, root, led, reg, ws = _world(programme=4_200_000)                      # 4.2M - 0.7M settled < cap 2M + ... see below
    out = gs.succeed(root=root, **_kw(ws, cap=3_900_000))                     # need 4.0M > executable 3.5M
    assert not out["ok"] and out["status"] == "AUTHORITY_REQUIRED", out
    h = reg.holder(ws)
    assert (h["lease"], h["gen"], h["holder_sid"]) == ("L1", 1, "old"), h      # the old holder keeps the workspace
    lin = led.lineage()
    assert len(lin["leases"]) == 1 and not lin["leases"][0]["closed"], lin     # and its lease is still open
    assert reg.authority(ws, "g", "L1", 1, ledger=led)["ok"], "old holder lost authority in a refused succession"
    again = gs.succeed(root=root, **_kw(ws, cap=3_900_000))
    assert not again["ok"] and len(led.lineage()["authority_required"]) == 1, again   # one row per succession


def _cli_argv(ws: str, **over) -> list[str]:
    k = _kw(ws, **over)
    argv = ["succeed", "--goal", k["goal"], "--succession-id", k["succession_id"], "--prev-lease", k["prev_lease"],
            "--cap", str(k["cap"]), "--workspace", k["workspace"], "--expect-gen", str(k["expect_gen"]),
            "--new-sid", k["new_sid"], "--old-sid", k["old_sid"]]
    for name, v in k["reserves"].items():
        argv += ["--reserve", f"{name}={v}"]
    if k["dead"]:
        argv.append("--dead")
    if k["measured"] is not None:
        argv += ["--measured", str(k["measured"])]
    return argv


@_gate("V-SUCC-CLI")
def _():
    st, root, led, reg, ws = _world()
    env = dict(os.environ, GSD_LONG_RUN_STATE_DIR=str(st))
    env.pop("GOAL_SUCCESSION_FAULT", None)

    def run(argv):
        p = subprocess.run([PY, str(REPO / "tools" / "goal_succession.py"), *argv], capture_output=True, text=True,
                           env=env, timeout=120)
        return p.returncode, (json.loads(p.stdout) if p.stdout.strip() else {}), p.stderr

    rc, out, err = run(_cli_argv(ws))
    assert rc == 0 and out["ok"] and out["applied"] and out["lease"] == "L2", (rc, out, err)
    rc, out, err = run(_cli_argv(ws))
    assert rc == 0 and out["ok"] and not out["applied"], (rc, out, err)
    rc, out, err = run(_cli_argv(ws, succession_id="S2", prev_lease="L1", expect_gen=2, new_sid="n2"))
    assert rc == 3 and not out["ok"] and out["status"] == "CAS_LOST", (rc, out, err)   # L1 is no longer the latest
    rc, out, err = run(["reconcile", "--goal", "g", "--sid", "ghost"])
    assert rc == 3 and out["state"] == "UNKNOWN_RESERVED", (rc, out, err)             # no proof => never free


@_gate("V-SUCC-CHAIN-HOOK")
def _():
    import goal_chain as gc
    st, root, led, reg, ws = _world()
    plan = st / "plan.json"
    k = _kw(ws)
    plan.write_text(json.dumps({x: k[x] for x in gc.PLAN_KEYS} | {"old_sid": "old", "dead": True, "measured": 700_000}))
    for action in ("running", "arm", "complete", None):                     # control: only a stop acts
        assert not gc.react({"action": action}, plan, root=root)["acted"], action
    assert len(led.lineage()["leases"]) == 1 and reg.holder(ws)["gen"] == 1
    assert not gc.react({"action": "stopped_without_done"}, st / "absent.json", root=root)["acted"]   # no plan, no effect
    out = gc.react({"action": "stopped_without_done", "unit": "W3"}, plan, root=root)
    assert out["acted"] and out["succession"]["ok"] and reg.holder(ws)["gen"] == 2, out
    out = gc.react({"action": "refuse_envelope", "unit": "W3"}, plan, root=root)       # the budget halt, replayed
    assert out["acted"] and out["succession"]["ok"] and not out["succession"]["applied"], out


def main() -> int:
    _run_gates()
    ok = sum(1 for _n, p, _d in RESULTS if p)
    for name, passed, detail in RESULTS:
        print(("PASS " if passed else "FAIL ") + name + ("" if passed else f"  {detail}"))
    print(f"SUCCESSION_PASS={ok}/{len(RESULTS)}")
    return 0 if ok == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
