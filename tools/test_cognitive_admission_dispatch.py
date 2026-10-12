"""CDC C3 gap: cognitive_admission must be callable by the dispatcher's PreToolUse-Agent chain (exports run()).

Drives the REAL hook-dispatcher.js CLI over a temp layout where '../skills/claude-power-pack/hooks' resolves.
Control: first spawn admitted; same prompt again is denied DUPLICATE through the dispatcher. Kill switch admits.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PP = Path(__file__).resolve().parent.parent
NODE = os.environ.get("NODE_BIN") or "node"
passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


def dispatch(root, state, sid, prompt, extra=None):
    env = dict(os.environ, GSD_LONG_RUN_STATE_DIR=str(state), CLAUDE_HOME=str(root / "home"))
    for k in ("CPP_COG_ADMISSION", "CPP_COG_ROUTE", "CPP_COG_UNIT", "CPP_GOAL"):
        env.pop(k, None)
    env.update(extra or {})
    ev = {"session_id": sid, "hook_event_name": "PreToolUse", "tool_name": "Agent", "cwd": str(state),
          "tool_input": {"prompt": prompt, "subagent_type": "general-purpose"}}
    p = subprocess.run([NODE, str(root / "hooks" / "hook-dispatcher.js"), "--event=PreToolUse-Agent-default"],
                       input=json.dumps(ev), capture_output=True, text=True, env=env, timeout=120)
    try:
        out = json.loads(p.stdout or "{}")
    except ValueError:
        out = {"_raw": p.stdout, "_err": p.stderr}
    d = out.get("hookSpecificOutput", {})
    return d.get("permissionDecision") == "deny", d.get("permissionDecisionReason", ""), out


def main():
    with tempfile.TemporaryDirectory() as t:
        root = Path(t) / "layout"
        state = Path(t) / "state"
        state.mkdir()
        shutil.copytree(PP / "hooks", root / "hooks", ignore=shutil.ignore_patterns("_mut_*"))
        shutil.copytree(PP / "hooks", root / "skills" / "claude-power-pack" / "hooks", ignore=shutil.ignore_patterns("_mut_*"))
        for d in ("vault", "tools"):
            if (PP / d).exists():
                try:
                    os.symlink(PP / d, root / "skills" / "claude-power-pack" / d, target_is_directory=True)
                except OSError:
                    pass
        d1, r1, _ = dispatch(root, state, "sid-c3-disp", "audit the widget module please")
        check("C3-disp-first-admitted", not d1, f"deny={d1} {r1[:60]}")
        d2, r2, _ = dispatch(root, state, "sid-c3-disp", "audit the widget module please")
        check("C3-disp-duplicate-denied", d2 and "DUPLICATE" in r2, r2[:90])
        d3, r3, _ = dispatch(root, state, "sid-c3-disp", "audit the widget module please", {"CPP_COG_ADMISSION": "off"})
        check("C3-disp-kill-switch", not d3, f"deny={d3}")
        d4, r4, _ = dispatch(root, state, "sid-c3-disp", "a different prompt entirely")
        check("C3-disp-different-admitted", not d4, f"deny={d4}")
    print(f"{passes} passed, {fails} failed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
