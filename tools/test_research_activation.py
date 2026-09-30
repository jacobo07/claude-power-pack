"""Deep-research activation and cost gates (V-RID-*, V-DR-*).

Measured 2026-09-30: of 136 auto-spawns in 7 days, 134 came from transcript
entries nobody typed (64 skill expansions, 70 inter-session messages), 12
prompts were researched more than once, and the claude.exe layer inherited the
session model (Opus) because it only passed --model when an env var was set.

The hook is driven as a real process in an isolated HOME whose deep_research.py
is a stub, so a spawn is harmless and observable in .auto-spawned.log. Two
positive controls prove a typed research prompt still spawns.

Usage: python tools/test_research_activation.py [path/to/hook.js]
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PP = Path(__file__).resolve().parent.parent
HOOK = Path(sys.argv[1]) if len(sys.argv) > 1 else PP / "hooks" / "research-intent-detector.js"
DR = PP / "modules" / "deep-research" / "deep_research.py"

passes = fails = 0


def _ok(gate, detail=""):
    global passes
    passes += 1
    print(f"PASS {gate} {detail}")


def _fail(gate, detail=""):
    global fails
    fails += 1
    print(f"FAIL {gate} {detail}")


def check(gate, cond, detail=""):
    (_ok if cond else _fail)(gate, detail)


# --- hook activation -------------------------------------------------------

LONG = "investiga el mercado de " + " ".join(["palabra"] * 90)
LONG2 = "research how does the scheduler " + " ".join(["word"] * 90)


def human(t):
    return {"type": "user", "origin": {"kind": "human"}, "message": {"role": "user", "content": t}}


def meta(t):
    return {"type": "user", "isMeta": True,
            "message": {"role": "user", "content": [{"type": "text", "text": t}]}}


def agent(t):
    return {"type": "user", "message": {"role": "user", "content": t}}


def toolres():
    return {"type": "user",
            "message": {"role": "user", "content": [{"type": "tool_result", "content": "ok"}]}}


def hook_cases():
    home = Path(tempfile.mkdtemp(prefix="rid-"))
    try:
        pp = home / ".claude" / "skills" / "claude-power-pack"
        (pp / "modules" / "deep-research").mkdir(parents=True)
        (pp / "modules" / "deep-research" / "deep_research.py").write_text("pass\n")
        proj = home / ".claude" / "projects" / "p"
        proj.mkdir(parents=True)
        log = pp / "vault" / "research" / ".auto-spawned.log"

        def spawns():
            if not log.exists():
                return 0
            return sum(1 for ln in log.read_text().splitlines() if '"spawned"' in ln)

        def case(gate, sid, entries, expect):
            (proj / f"{sid}.jsonl").write_text("\n".join(json.dumps(e) for e in entries) + "\n")
            env = dict(os.environ, USERPROFILE=str(home), HOME=str(home))
            env.pop("CLAUDEPP_DEEPRESEARCH_RUNNING", None)
            env.pop("CLAUDEPP_DEEPRESEARCH_DISABLE", None)
            before = spawns()
            r = subprocess.run(["node", str(HOOK)], input=json.dumps({"session_id": sid}),
                               capture_output=True, text=True, env=env, timeout=30)
            time.sleep(0.3)
            delta = spawns() - before
            check(gate, r.returncode == 0 and delta == expect,
                  f"rc={r.returncode} delta={delta} expected={expect}")

        case("V-RID-HUMAN-RESEARCH-SPAWNS", "s1", [human(LONG)], 1)  # control
        case("V-RID-SAME-PROMPT-NOT-RESPAWNED", "s2", [human(LONG)], 0)
        case("V-RID-SKILL-EXPANSION-IGNORED", "s3",
             [human("<command-name>/gsd-code-review</command-name>"),
              meta("Base directory for this skill " + LONG2)], 0)
        case("V-RID-AGENT-MESSAGE-IGNORED", "s4",
             [agent("Another Claude session sent a message " + LONG2)], 0)
        case("V-RID-META-ONLY-IGNORED", "s5", [meta(LONG2)], 0)
        case("V-RID-SHORT-HUMAN-IGNORED", "s6", [human(LONG2), toolres(), human("y")], 0)
        case("V-RID-WALKS-PAST-TOOL-RESULTS", "s7", [human(LONG2), toolres(), toolres()], 1)  # control
    finally:
        shutil.rmtree(home, ignore_errors=True)


# --- model -----------------------------------------------------------------

def model_cases():
    spec = importlib.util.spec_from_file_location("deep_research_under_test", DR)
    dr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dr)
    seen = []

    class _R:
        returncode, stdout, stderr = 0, "ok", ""

    real_run = subprocess.run
    subprocess.run = lambda args, **kw: (seen.append(args), _R())[1]
    saved = os.environ.pop("CLAUDEPP_RESEARCH_MODEL", None)
    try:
        def model_of(a):
            return a[a.index("--model") + 1] if "--model" in a else None

        dr._llm_claude_cli("s", "u", None, 5)
        m = model_of(seen[-1])
        check("V-DR-CLI-DEFAULT-CHEAP", m == dr.DEFAULT_RESEARCH_MODEL and "haiku" in m, str(m))
        os.environ["CLAUDEPP_RESEARCH_MODEL"] = "override-model"
        dr._llm_claude_cli("s", "u", None, 5)
        check("V-DR-CLI-ENV-OVERRIDE", model_of(seen[-1]) == "override-model")
        check("V-DR-SDK-SHARES-RESOLVER", dr.research_model() == "override-model")
    finally:
        subprocess.run = real_run
        os.environ.pop("CLAUDEPP_RESEARCH_MODEL", None)
        if saved is not None:
            os.environ["CLAUDEPP_RESEARCH_MODEL"] = saved


def main():
    hook_cases()
    model_cases()
    total = passes + fails
    print(f"RESEARCH_ACTIVATION_PASS={passes}/{total}  threshold=10/10")
    return 0 if fails == 0 and total == 10 else 1


if __name__ == "__main__":
    sys.exit(main())
