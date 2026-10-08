"""V-LIFE-* gates: process lifecycle (vault/plans/ce-lifecycle-master-plan-2026-10-08.md).

L1: pre-model admission on UserPromptSubmit. Every refusal is paired with a control that is admitted.
Hermetic: temp state dir, a copied dispatcher for planted entries, no ~/.claude writes.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PP = HERE.parent
HOOKS = PP / "hooks"
NODE = shutil.which("node") or "node"
PYEXE = sys.executable
# Mutation drills point these at a mutant copy.
DISPATCHER = Path(os.environ.get("LIFE_DISPATCHER", HOOKS / "hook-dispatcher.js"))
GATE = Path(os.environ.get("LIFE_GATE", HOOKS / "premodel_gate.js"))

passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


def run_node(script, payload, env_extra=None, cwd=None, timeout=60):
    env = {k: v for k, v in os.environ.items() if k not in ("CPP_GOAL", "CPP_PREMODEL_GATE", "CLAUDECODE")}
    env.update(env_extra or {})
    return subprocess.run([NODE, str(script)] + (env_extra or {}).get("_ARGS", "").split(),
                          input=json.dumps(payload), capture_output=True, text=True, env=env,
                          cwd=cwd, timeout=timeout)


def parse(out):
    try:
        return json.loads(out) if out.strip() else {}
    except ValueError:
        return {"_unparseable": out[:200]}


def planted_dispatcher(tmp: Path, entry_json: str):
    """Copy the REAL dispatcher next to a planted chain member; the entry is injected as the first
    UserPromptSubmit-chain step. The rest of the chain is absent, so those steps are skipped."""
    d = tmp / "hooks"
    d.mkdir()
    src = DISPATCHER.read_text(encoding="utf-8")
    marker = "'UserPromptSubmit-chain': ["
    idx = src.index(marker)
    src = src[:idx + len(marker)] + "\n    { exe: NODE_EXE, script: './planted.js', timeoutMs: 5000 }," + src[idx + len(marker):]
    (d / "hook-dispatcher.js").write_text(src, encoding="utf-8")
    (d / "planted.js").write_text(
        "process.stdin.resume();process.stdin.on('data',()=>{});process.stdin.on('end',()=>{});"
        f"process.stdout.write({json.dumps(entry_json)});", encoding="utf-8")
    return d / "hook-dispatcher.js"


def g_transport():
    tmp = Path(tempfile.mkdtemp(prefix="life_tr_"))
    try:
        ups = {"hook_event_name": "UserPromptSubmit", "session_id": "s-tr", "prompt": "hi", "cwd": str(tmp)}
        blk = '{"decision":"block","reason":"x"}'
        disp = planted_dispatcher(tmp, blk)
        r = subprocess.run([NODE, str(disp), "--event=UserPromptSubmit-chain"], input=json.dumps(ups),
                           capture_output=True, text=True, timeout=60,
                           env={**os.environ, "CLAUDE_STATE_DIR": str(tmp / "cs")})
        out = parse(r.stdout)
        check("V-LIFE-PREMODEL-TRANSPORT", out.get("decision") == "block" and out.get("reason") == "x",
              f"planted block survives the real dispatcher: {r.stdout[:160]!r}")
        tmp2 = Path(tempfile.mkdtemp(prefix="life_tc_"))
        try:
            disp2 = planted_dispatcher(tmp2, "{}")
            r2 = subprocess.run([NODE, str(disp2), "--event=UserPromptSubmit-chain"], input=json.dumps(ups),
                                capture_output=True, text=True, timeout=60,
                                env={**os.environ, "CLAUDE_STATE_DIR": str(tmp2 / "cs")})
            check("V-LIFE-PREMODEL-TRANSPORT-CONTROL", parse(r2.stdout).get("decision") is None,
                  f"a non-blocking planted entry yields no decision: {r2.stdout[:120]!r}")
        finally:
            shutil.rmtree(tmp2, ignore_errors=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --- WU-1B: prospective goal binding (hooks/lib/goal_binding.js, tools/mission_spend.py) -------------

GUARD = HOOKS / "session_budget_guard.js"
RUNNER = ("const g=require(process.argv[1]);let raw='';process.stdin.on('data',d=>raw+=d).on('end',()=>{"
          "process.stdout.write(JSON.stringify({out:g.decide(JSON.parse(raw))}));});")
PRE_TS, POST_TS = "2026-02-01T00:00:00.000Z", "2099-01-01T00:00:00.000Z"
PRE_N, POST_N = 6_000_000, 1_000_000


def _row(mid, n, ts):
    u = {"input_tokens": n, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": 0}
    return json.dumps({"type": "assistant", "timestamp": ts, "uuid": "u-" + mid,
                       "message": {"id": mid, "model": "claude-opus-5-5", "usage": u,
                                   "content": [{"type": "text", "text": "x"}]}}) + "\n"


def _guard(state, sid, tx, cwd, tool, tool_input, env_extra=None):
    env = {k: v for k, v in os.environ.items() if k not in ("CPP_GOAL", "CPP_SESSION_BUDGET", "CLAUDECODE",
                                                            "CPP_PROSPECTIVE_BIND")}
    env["GSD_LONG_RUN_STATE_DIR"] = str(state)
    env.update(env_extra or {})
    ev = {"session_id": sid, "transcript_path": str(tx), "cwd": str(cwd), "tool_name": tool, "tool_input": tool_input}
    p = subprocess.run([NODE, "-e", RUNNER, str(GUARD)], input=json.dumps(ev), capture_output=True, text=True,
                       env=env, timeout=120)
    return p


def _bind_world(prefix):
    """Goal `lb` (cap 100M, since 2026-01-01) rooted at work/; a transcript with 6M BEFORE binding and 1M after."""
    root = Path(tempfile.mkdtemp(prefix=prefix))
    state, work = root / "state", root / "work"
    state.mkdir()
    work.mkdir()
    (state / "goal-budget").mkdir()
    ix = {"lb": {"since": "2026-01-01T00:00:00", "roots": [str(work)], "hosts": [], "lease_calls": 5}}
    (state / "goal-budget" / "index.json").write_text(json.dumps(ix), encoding="utf-8")
    env = dict(os.environ, GSD_LONG_RUN_STATE_DIR=str(state))
    env.pop("CLAUDECODE", None)
    env.pop("CPP_GOAL", None)
    r = subprocess.run([PYEXE, str(HERE / "mission_spend.py"), "goal-declare", "--goal", "lb", "--cap", "100000000",
                        "--source", "test", "--root", str(work)], capture_output=True, text=True, env=env, timeout=60)
    # goal-declare keeps the since written above only if the entry already exists; restore it explicitly
    ix2 = json.loads((state / "goal-budget" / "index.json").read_text(encoding="utf-8-sig"))
    ix2["lb"]["since"] = "2026-01-01T00:00:00"
    (state / "goal-budget" / "index.json").write_text(json.dumps(ix2), encoding="utf-8")
    tx = root / "t.jsonl"
    tx.write_text(_row("pre1", PRE_N, PRE_TS) + _row("post1", POST_N, POST_TS), encoding="utf-8")
    return root, state, work, tx, r.returncode


def _goal_state(state, sid):
    p = state / f"session-budget-{sid}.goal.json"
    return json.loads(p.read_text(encoding="utf-8-sig")) if p.exists() else None


def g_binding():
    mut = {"tool": "Bash", "tool_input": {"command": "python big_job.py"}}
    root, state, work, tx, rc = _bind_world("life_bind_")
    try:
        _guard(state, "s-retro", tx, work, mut["tool"], mut["tool_input"])
        gs, rec = _goal_state(state, "s-retro"), state / "goal-binding" / "s-retro.json"
        got = json.loads(rec.read_text(encoding="utf-8")) if rec.exists() else {}
        led = list((state / "goal-budget" / "lb").glob("*.jsonl"))
        jtxt = "".join(p.read_text(encoding="utf-8") for p in led)
        check("V-LIFE-BIND-RETRO",
              gs is not None and gs["tokens"] == POST_N and gs.get("prebind") == PRE_N
              and got.get("source") == "cwd" and got.get("goal") == "lb"
              and f'"measured": {PRE_N}' in jtxt and '"op": "prebind"' in jtxt,
              f"bound by cwd at first mutating call; charged {gs and gs['tokens']} (want {POST_N}), "
              f"pre-binding {gs and gs.get('prebind')} booked as prebind op, record {got.get('source')}")
        # twin: the Python resolver reads the SAME record and agrees on the goal
        os.environ["GSD_LONG_RUN_STATE_DIR"] = str(state)
        try:
            sys.path.insert(0, str(HERE))
            import mission_spend as ms
            b = ms.resolve_binding({"cwd": str(work), "tool_name": "Bash",
                                    "tool_input": {"command": "x"}}, "s-retro")
            ob = ms.resolve_binding({"cwd": str(work), "tool_name": "Read", "tool_input": {}}, "s-twin-ro")
            check("V-LIFE-BIND-TWIN", b and b["goal"] == "lb" and b["record"]["since_ts"] == got.get("since_ts")
                  and ob and ob.get("provisional") and not (state / "goal-binding" / "s-twin-ro.json").exists(),
                  "resolve_binding reads the JS record (same goal, since_ts) and leaves no record for a read")
        finally:
            os.environ.pop("GSD_LONG_RUN_STATE_DIR", None)
    finally:
        shutil.rmtree(root, ignore_errors=True)

    root, state, work, tx, rc = _bind_world("life_ctl_")
    try:
        _guard(state, "s-ctl", tx, work, mut["tool"], mut["tool_input"], {"CPP_PROSPECTIVE_BIND": "0"})
        gs = _goal_state(state, "s-ctl")
        check("V-LIFE-BIND-CONTROL",
              gs is not None and gs["tokens"] == PRE_N + POST_N and not (state / "goal-binding" / "s-ctl.json").exists(),
              f"kill switch CPP_PROSPECTIVE_BIND=0: retroactive charge {gs and gs['tokens']} (want {PRE_N + POST_N}), no record")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    root, state, work, tx, rc = _bind_world("life_obs_")
    try:
        _guard(state, "s-obs", tx, work, "Read", {"file_path": str(work / "f.txt")})
        _guard(state, "s-obs", tx, work, "Bash", {"command": "git status"})
        quiet = not (state / "goal-binding" / "s-obs.json").exists()
        _guard(state, "s-obs", tx, work, "Bash", {"command": "python big_job.py"})
        check("V-LIFE-OBSERVER", quiet and (state / "goal-binding" / "s-obs.json").exists(),
              f"Read and git status in a goal root write no record (quiet={quiet}); the first mutating call does")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main():
    g_transport()
    g_binding()
    print(f"LIFE_PASS={passes} LIFE_FAIL={fails}")
    print(f"{passes} pass, {fails} fail")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
