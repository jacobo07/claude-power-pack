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


def main():
    g_transport()
    print(f"{passes} pass, {fails} fail")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
