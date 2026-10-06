"""V-ADMIT-* gates: session envelope admission (mission_spend.feasibility) and the guard's closeout
allowance (hooks/session_budget_guard.js). TOK-18 Slice A2 + closeout, 2026-10-06.

Origin: session 1fd598fe declared stop 800K right after /kresume at ~110K context per call; the
breaker tripped on the next call with zero work done, and then denied even Read, so the pane could
not record its spend or write a handoff. Every gate here is driven from both poles.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOL = REPO / "tools" / "mission_spend.py"
GUARD = REPO / "hooks" / "session_budget_guard.js"
sys.path.insert(0, str(REPO / "tools"))
import mission_spend as ms  # noqa: E402

passes = fails = 0


def _ok(gate: str, ev: str) -> None:
    global passes
    passes += 1
    print(f"PASS {gate}: {ev}")


def _fail(gate: str, ev: str) -> None:
    global fails
    fails += 1
    print(f"FAIL {gate}: {ev}")


def _check(gate: str, cond: bool, ev: str) -> None:
    (_ok if cond else _fail)(gate, ev)


def _transcript(path: Path, contexts: list[int], tool_calls: int = 0) -> None:
    rows = []
    for i, c in enumerate(contexts):
        content = [{"type": "tool_use", "name": "Read", "input": {}}] if i < tool_calls else []
        rows.append({"type": "assistant", "timestamp": f"2026-10-06T10:00:{i:02d}",
                     "message": {"id": f"m{i}", "model": "claude-opus", "content": content,
                                 "usage": {"input_tokens": 0, "cache_creation_input_tokens": 0,
                                           "cache_read_input_tokens": c, "output_tokens": 0}}})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def _cli(env: dict, cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOL), "session-declare", *args], cwd=cwd, env=env,
                          capture_output=True, text=True, timeout=60)


def admission(tmp: Path) -> None:
    cfg, state, work = tmp / "cfg", tmp / "state", tmp / "work"
    work.mkdir()
    env = dict(os.environ, CLAUDE_CONFIG_DIR=str(cfg), GSD_LONG_RUN_STATE_DIR=str(state))
    proj = cfg / "projects" / ms.encode_cwd(str(work))
    sid = "s-admit"
    _transcript(proj / f"{sid}.jsonl", [100_000] * 7)        # 700K spent, 100K per call

    # The incident's shape: 0.8M stop, 15 calls at 100K -> refused, no budget file written.
    r = _cli(env, work, "--session", sid, "--target", "600000", "--warn", "700000", "--stop", "800000",
             "--calls-estimate", "15")
    _check("V-ADMIT-REFUSE", r.returncode == 3 and "REFUSED" in r.stderr
           and not (state / f"session-budget-{sid}.json").exists(),
           f"rc={r.returncode} stderr={r.stderr.strip()[:160]}")

    # Control: a stop that covers the projection is admitted and records the projection.
    r = _cli(env, work, "--session", sid, "--target", "3000000", "--warn", "3500000", "--stop", "4000000",
             "--calls-estimate", "15")
    rec = json.loads((state / f"session-budget-{sid}.json").read_text(encoding="utf-8")) if r.returncode == 0 else {}
    f = rec.get("feasibility") or {}
    exp = 700_000 + 17 * 100_000 + ms.DEFAULT_GROWTH_PER_CALL * 17 * 18 // 2
    _check("V-ADMIT-ADMIT", r.returncode == 0 and f.get("feasible") is True and f.get("projected") == exp,
           f"rc={r.returncode} projected={f.get('projected')} expected={exp}")

    # No call count -> refused (cannot project).
    r = _cli(env, work, "--session", sid, "--target", "3000000", "--warn", "3500000", "--stop", "4000000")
    _check("V-ADMIT-NO-CALLS", r.returncode == 3 and "calls-estimate" in r.stderr, f"rc={r.returncode}")

    # Fresh session, no own transcript: the floor comes from recent same-cwd sessions (median).
    # Four sessions share the dir: s-admit's first call (100K) plus these three -> median 110K.
    for i, c in enumerate([90_000, 120_000, 150_000]):
        _transcript(proj / f"other{i}.jsonl", [c, c + 5_000])
    f = ms.feasibility("s-fresh", 10_000_000, 5, cwd=str(work), root=cfg / "projects")
    _check("V-ADMIT-FALLBACK", f["feasible"] and f["per_call"] == 110_000 and "median" in (f["source"] or ""),
           f"per_call={f['per_call']} source={f['source']}")

    # Unknown cost: no transcript and an empty cwd directory -> refused, never admitted.
    empty = tmp / "empty-cwd"
    empty.mkdir()
    f = ms.feasibility("s-none", 10 ** 12, 5, cwd=str(empty), root=cfg / "projects")
    _check("V-ADMIT-UNKNOWN", f["feasible"] is False and "unknown" in (f["reason"] or ""), f["reason"] or "")

    # Explicit override is admitted AND recorded.
    r = _cli(env, empty, "--session", "s-skip", "--target", "1", "--warn", "1", "--stop", "1", "--skip-feasibility")
    rec = json.loads((state / "session-budget-s-skip.json").read_text(encoding="utf-8")) if r.returncode == 0 else {}
    _check("V-ADMIT-SKIP-RECORDED", rec.get("feasibility") == {"skipped": True}, f"rc={r.returncode} rec={rec.get('feasibility')}")


DRIVER = r"""
const g = require(process.argv[1]);
const events = JSON.parse(process.argv[2]);
const out = events.map(e => { const v = g.decide(e); return v && v.hookSpecificOutput
  ? (v.hookSpecificOutput.permissionDecision || 'advise') : 'allow'; });
console.log(JSON.stringify(out));
"""


def closeout(tmp: Path) -> None:
    node = shutil.which("node")
    if not node:
        _fail("V-ADMIT-CLOSEOUT", "node not found: closeout cannot be measured (UNKNOWN is not a pass)")
        return
    state = tmp / "cstate"
    state.mkdir()
    sid = "s-close"
    tr = tmp / "close.jsonl"
    _transcript(tr, [5_000] * 2, tool_calls=2)
    (state / f"session-budget-{sid}.json").write_text(json.dumps(
        {"target": 100, "warn": 200, "stop": 1000, "noprogress_calls": 999}), encoding="utf-8")

    def ev(tool: str, fp: str = "") -> dict:
        return {"session_id": sid, "transcript_path": str(tr), "tool_name": tool, "tool_input": {"file_path": fp}}

    seq = [ev("Edit", str(tmp / "tools" / "x.py")),                    # not closeout -> deny
           ev("Read", "a.py"),                                          # 1/4
           ev("Write", str(tmp / "vault" / "plans" / "card.md")),       # 2/4
           ev("Edit", str(tmp / "memory" / "handoffs" / "h.md")),       # 3/4
           ev("Grep"),                                                  # 4/4
           ev("Read", "b.py")]                                          # allowance spent -> deny
    env = dict(os.environ, GSD_LONG_RUN_STATE_DIR=str(state))
    env.pop("CPP_SESSION_BUDGET", None)
    r = subprocess.run([node, "-e", DRIVER, str(GUARD), json.dumps(seq)], env=env,
                       capture_output=True, text=True, timeout=60)
    try:
        got = json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        _fail("V-ADMIT-CLOSEOUT", f"driver output unreadable rc={r.returncode} err={r.stderr[:200]}")
        return
    want = ["deny", "advise", "advise", "advise", "advise", "deny"]
    _check("V-ADMIT-CLOSEOUT", got == want, f"got={got} want={want}")


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        admission(Path(td))
        closeout(Path(td))
    print(f"ADMIT_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
