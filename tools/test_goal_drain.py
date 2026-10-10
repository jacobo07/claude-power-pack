"""V-DRAIN gates for the predictive DRAIN in hooks/session_budget_guard.js and the SessionEnd wake (W4).
Run: python tools/test_goal_drain.py   Prints GOALDRAIN_PASS=n/m and exits 1 on any failure.

Every gate drives the real node hooks in its own GSD_LONG_RUN_STATE_DIR (tempfile.mkdtemp()).
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
from modules.provider_routing.ledger import GoalLedger  # noqa: E402

M = 1_000_000
PER = 50_000
RESULTS: list[tuple[str, bool, str]] = []
GATES: list = []


def _gate(name):
    def deco(fn):
        GATES.append((name, fn))
        return fn
    return deco


_RUN_GUARD = "const g=require(process.argv[1]); let r='';process.stdin.on('data',d=>r+=d).on('end',()=>{" \
             "process.stdout.write(JSON.stringify({out:g.decide(JSON.parse(r))}));});"
_RUN_HOOK = "const g=require(process.argv[1]); let r='';process.stdin.on('data',d=>r+=d).on('end',()=>{" \
            "Promise.resolve(g.run(JSON.parse(r))).then(o=>process.stdout.write(JSON.stringify({out:o})));});"


def _node(code: str, mod: str, event: dict, st: Path, **env_over):
    env = dict(os.environ, GSD_LONG_RUN_STATE_DIR=str(st))
    for k in ("CPP_GOAL", "CPP_SESSION_BUDGET", "CPP_DRAIN"):
        env.pop(k, None)
    env.update(env_over)
    p = subprocess.run(["node", "-e", code, str(REPO / mod)], input=json.dumps(event), capture_output=True,
                       text=True, env=env, timeout=90)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout)["out"]


def _world(cap: int):
    st = Path(tempfile.mkdtemp(prefix="drain-"))
    root = st / "wt"
    root.mkdir()
    (st / "goal-budget").mkdir()
    (st / "goal-budget" / "index.json").write_text(json.dumps({"g": {"roots": [str(root)], "lease_calls": 10}}))
    led = GoalLedger(st / "goal-budget" / "g", "g")
    led.declare_cap(cap, "t")
    led.set_programme(20 * M, "t", inside_agent=False)
    return st, root, led


def _rows(path: Path, n: int, start: int = 0) -> None:
    with open(path, "a", encoding="utf-8") as fh:
        for i in range(start, start + n):
            fh.write(json.dumps({"type": "assistant", "uuid": f"u{i}", "message": {
                "id": f"m{i}", "model": "x", "content": [], "usage": {"input_tokens": PER}}}) + "\n")


def _ev(root: Path, tr: Path, tool: str, **ti) -> dict:
    return {"session_id": "sid-drain-1", "cwd": str(root), "tool_name": tool, "tool_input": ti,
            "transcript_path": str(tr)}


def _reason(out) -> str:
    return ((out or {}).get("hookSpecificOutput") or {}).get("permissionDecisionReason", "")


def _denied(out) -> bool:
    return ((out or {}).get("hookSpecificOutput") or {}).get("permissionDecision") == "deny"


@_gate("V-DRAIN-DENIES-SPAWN-AT-EDGE")
def _():
    st, root, _led = _world(cap=350_000)          # 200K measured, lease = 100K = 2 calls (< 3), nothing beyond it
    tr = st / "t.jsonl"
    _rows(tr, 4)
    out = _node(_RUN_GUARD, "hooks/session_budget_guard.js", _ev(root, tr, "Agent", prompt="x"), st)
    assert _denied(out) and "DRAIN" in _reason(out), out
    bg = _node(_RUN_GUARD, "hooks/session_budget_guard.js", _ev(root, tr, "Bash", command="echo hi", run_in_background=True), st)
    assert _denied(bg) and "DRAIN" in _reason(bg), bg                  # a large spawn is a spawn too


@_gate("V-DRAIN-CLOSEOUT-PATH-OPEN")
def _():
    st, root, _led = _world(cap=350_000)
    tr = st / "t.jsonl"
    _rows(tr, 4)
    for ev in (_ev(root, tr, "Write", file_path=str(root / "vault" / "programs" / "dgl" / "W4-receipt.md"), content="x"),
               _ev(root, tr, "Bash", command="git commit -F msg.txt"),
               _ev(root, tr, "Read", file_path=str(root / "a.txt"))):
        out = _node(_RUN_GUARD, "hooks/session_budget_guard.js", ev, st)
        assert not _denied(out), (ev["tool_name"], out)                 # DRAIN never closes the closeout / settle path


@_gate("V-DRAIN-NO-EDGE-NO-DRAIN")
def _():
    st, root, _led = _world(cap=5 * M)             # control: the lease ends by renewal, the goal has room beyond it
    tr = st / "t.jsonl"
    _rows(tr, 4)
    first = _node(_RUN_GUARD, "hooks/session_budget_guard.js", _ev(root, tr, "Read", file_path=str(root / "a")), st)
    assert not _denied(first), first
    _rows(tr, 8, start=4)                          # 400K into a 500K lease: 2 calls left in the LEASE, 4M left in the GOAL
    out = _node(_RUN_GUARD, "hooks/session_budget_guard.js", _ev(root, tr, "Agent", prompt="x"), st)
    assert "DRAIN" not in _reason(out) and "DRAIN" not in json.dumps(out), out


@_gate("V-DRAIN-FAIL-OPEN-UNMEASURABLE")
def _():
    st, root, _led = _world(cap=350_000)
    tr = st / "empty.jsonl"
    tr.write_text("")                              # no usage rows: the per-call cost is unmeasurable
    out = _node(_RUN_GUARD, "hooks/session_budget_guard.js", _ev(root, tr, "Agent", prompt="x"), st)
    assert "DRAIN" not in json.dumps(out), out
    st2, root2, _l = _world(cap=350_000)
    tr2 = st2 / "t.jsonl"
    _rows(tr2, 4)
    off = _node(_RUN_GUARD, "hooks/session_budget_guard.js", _ev(root2, tr2, "Agent", prompt="x"), st2, CPP_DRAIN="off")
    assert "DRAIN" not in json.dumps(off), off                         # kill switch


def _end_event(sid: str, root: Path) -> dict:
    return {"hook_event_name": "SessionEnd", "session_id": sid, "cwd": str(root), "reason": "other"}


@_gate("V-SESSION-END-WAKE-ROW-ONLY")
def _():
    st, root, led = _world(cap=4 * M)
    assert led.renew("sid-end-1", 300_000, 100_000)["ok"]
    (st / "goal-binding").mkdir()
    (st / "goal-binding" / "sid-end-1.json").write_text(json.dumps({"goal": "g", "since_ts": "2026-10-10T00:00:00", "source": "cwd"}))
    (st / "goal-binding" / "sid-free.json").write_text(json.dumps({"goal": "none", "since_ts": "x", "source": "cwd"}))
    spend = st / "goal-budget" / "g" / "spend.journal.jsonl"
    before = spend.read_bytes()
    _node(_RUN_HOOK, "hooks/goal_session_end.js", _end_event("sid-free", root), st)           # unbound: no row
    assert not (st / "goal-budget" / "g" / "ended.jsonl").exists()
    _node(_RUN_HOOK, "hooks/goal_session_end.js", _end_event("sid-end-1", root), st)
    ended = st / "goal-budget" / "g" / "ended.jsonl"
    rows = [json.loads(x) for x in ended.read_text().splitlines() if x.strip()]
    assert len(rows) == 1 and rows[0]["sid"] == "sid-end-1" and rows[0]["goal"] == "g" and rows[0]["ended_at"], rows
    assert "lease" in rows[0], rows
    assert spend.read_bytes() == before, "SessionEnd settled / wrote the ledger"                # a wake row, never a settle
    assert not (st / "goal-budget" / "g" / "succession.journal.jsonl").exists()


@_gate("V-SESSION-END-DEAD-NEEDS-MEASURE")
def _():
    sys.path.insert(0, str(REPO / "tools"))
    import goal_chain as gc
    st, root, led = _world(cap=4 * M)
    ended = st / "goal-budget" / "g"
    (ended / "ended.jsonl").write_text(json.dumps({"sid": "old", "goal": "g", "lease": "L1", "ended_at": "2026-10-10T00:00:00"}) + "\n")
    assert gc.dead_evidence(st / "goal-budget", "g", "old", measured=None) is False       # a wake alone is no proof
    assert gc.dead_evidence(st / "goal-budget", "g", "old", measured=700_000) is True      # wake + measured value
    assert gc.dead_evidence(st / "goal-budget", "g", "other", measured=700_000) is False   # another sid's wake


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
    print(f"GOALDRAIN_PASS={ok}/{len(RESULTS)}")
    return 0 if ok == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
