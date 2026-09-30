#!/usr/bin/env python3
"""V-FLOOR gates for modules/pp_eval/floor.py (startup-floor attribution by arm).

Fixture streams copy the shapes of a real `claude -p --output-format stream-json
--include-hook-events` run (2026-09-30, CLI 2.1.286). The end-to-end gate drives run() through a
fake claude that honours the same flags, so every positive control is exercised from both poles.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from modules.pp_eval import floor  # noqa: E402

passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"  [PASS] {gate}: {ev}")
    else:
        fails += 1
        print(f"  [FAIL] {gate}: {ev}")


def stream(first_call=(2, 76872, 15661), hooks=2, skills=206, mcp=8, plugins=("builtin", "C:/p/sp"),
           synthetic=False) -> str:
    rows = [{"type": "system", "subtype": "hook_started", "hook_event": "SessionStart"}] * hooks
    rows += [{"type": "system", "subtype": "hook_response", "hook_event": "SessionStart",
              "output": "You have superpowers " * 10}] * min(hooks, 1)
    rows.append({"type": "system", "subtype": "init", "tools": [1] * 67, "skills": [1] * skills,
                 "agents": [1] * 67, "slash_commands": [], "mcp_servers": [{}] * mcp,
                 "plugins": [{"path": p} for p in plugins]})
    i, c, r = first_call
    rows.append({"type": "assistant", "message": {"model": "<synthetic>" if synthetic else "claude-opus-5-5",
                 "usage": {"input_tokens": i, "cache_creation_input_tokens": c, "cache_read_input_tokens": r}}})
    rows.append({"type": "result", "subtype": "success"})
    return "\n".join(json.dumps(x) for x in rows) + "\nnot json\n"


FAKE = r'''
import json, sys
argv = sys.argv[1:]
settings = json.loads(argv[argv.index("--settings") + 1]) if "--settings" in argv else {}
hooks = 0 if settings.get("disableAllHooks") else 2
skills = 0 if "--disable-slash-commands" in argv else 206
mcp = 1 if "--strict-mcp-config" in argv else 8
plugins = ["builtin"] if settings.get("enabledPlugins") is not None else ["builtin", "C:/p/sp"]
ctx = 92535 - (20000 if settings.get("claudeMdExcludes") is not None else 0) \
      - (7000 if hooks == 0 else 0) - (9000 if skills == 0 else 0) - (3000 if mcp == 1 else 0) \
      - (4000 if len(plugins) == 1 else 0)
rows = [{"type": "system", "subtype": "hook_started"}] * hooks
rows.append({"type": "system", "subtype": "init", "tools": [], "skills": [1] * skills, "agents": [],
             "slash_commands": [], "mcp_servers": [{}] * mcp, "plugins": [{"path": p} for p in plugins]})
rows.append({"type": "assistant", "message": {"model": "m", "usage": {"input_tokens": ctx}}})
rows.append({"type": "result", "subtype": "success"})
print("\n".join(json.dumps(r) for r in rows))
'''


def main() -> int:
    ev = floor.parse(stream())
    check("V-FLOOR-PARSE-FIRST-CALL", ev["state"] == "MEASURED" and ev["first_call"] == 92535, ev["first_call"])
    check("V-FLOOR-PARSE-INIT", ev["init"]["skills"] == 206 and ev["init"]["mcp_servers"] == 8
          and ev["init"]["plugins_non_builtin"] == 1 and ev["hook_started"] == 2 and ev["bad_lines"] == 1,
          ev["init"])
    check("V-FLOOR-INJECTION-CENSUS", ev["injections"] and ev["injections"][0]["chars"] == 210
          and ev["injections"][0]["fingerprint"].startswith("You have superpowers"), ev["injections"])
    syn = floor.parse(stream(synthetic=True))
    check("V-FLOOR-SYNTHETIC-UNMEASURED", syn["state"] == "UNMEASURED" and syn["first_call"] is None, syn["reason"])

    a = floor.arm_args("all")
    s = json.loads(a[a.index("--settings") + 1])
    check("V-FLOOR-ALL-ONE-SETTINGS", a.count("--settings") == 1 and s.get("disableAllHooks") is True
          and "claudeMdExcludes" in s and "enabledPlugins" in s
          and "--strict-mcp-config" in a and "--disable-slash-commands" in a, a[2:])
    check("V-FLOOR-A-IS-UNTOUCHED", floor.arm_args("A") == [], floor.arm_args("A"))
    try:
        floor.arm_args("bogus")
        check("V-FLOOR-UNKNOWN-ARM-REFUSED", False, "no error")
    except ValueError as exc:
        check("V-FLOOR-UNKNOWN-ARM-REFUSED", True, exc)

    base = floor.parse(stream())
    cf = floor.control_fails
    check("V-FLOOR-CTRL-HOOKS", cf("hooks", floor.parse(stream(hooks=2)), base) == "hooks still ran"
          and cf("hooks", floor.parse(stream(hooks=0)), base) is None, "both poles")
    check("V-FLOOR-CTRL-SKILLS", cf("skills", floor.parse(stream(skills=3)), base) == "skills still loaded"
          and cf("skills", floor.parse(stream(skills=0)), base) is None, "both poles")
    check("V-FLOOR-CTRL-PLUGINS", cf("plugins", floor.parse(stream()), base) == "plugins still loaded"
          and cf("plugins", floor.parse(stream(plugins=("builtin",))), base) is None, "both poles")
    check("V-FLOOR-CTRL-MCP", cf("mcp", floor.parse(stream(mcp=8)), base) == "mcp servers not reduced"
          and cf("mcp", floor.parse(stream(mcp=1)), base) is None, "both poles")
    check("V-FLOOR-CTRL-BASELINE-HOOKS", cf("A", floor.parse(stream(hooks=0)), None) is not None, "A without hooks")

    mk = lambda arm, v: {"arm": arm, "void": None, "ev": {"first_call": v}}
    summ = floor.summarize([mk("A", 100_000), mk("A", 100_400), mk("hooks", 90_000), mk("context", 100_100)])
    check("V-FLOOR-ABOVE-NOISE", summ["arms"]["hooks"]["significance"] == "ABOVE_NOISE"
          and summ["arms"]["hooks"]["delta"] == 10_200 and summ["aa_noise"] == 400, summ["arms"]["hooks"])
    check("V-FLOOR-CONTEXT-PAIRWISE-VOID", summ["arms"]["context"]["significance"] == "WITHIN_NOISE"
          and summ["arms"]["context"]["void"], summ["arms"]["context"])
    one = floor.summarize([mk("A", 100_000), mk("hooks", 90_000)])
    check("V-FLOOR-ONE-REP-UNJUDGED", one["arms"]["hooks"]["significance"].startswith("UNJUDGED"), one["arms"]["hooks"])
    none = floor.summarize([{"arm": "A", "void": "x", "ev": {"first_call": 1}}, mk("hooks", 5)])
    check("V-FLOOR-NO-BASELINE-UNMEASURED", none["verdict"] == "UNMEASURED", none)

    with tempfile.TemporaryDirectory() as td:
        fake = Path(td) / "fake_claude.py"
        fake.write_text(FAKE, encoding="utf-8")
        old = os.environ.get("PP_EVAL_CLAUDE_CMD")
        os.environ["PP_EVAL_CLAUDE_CMD"] = json.dumps([sys.executable, str(fake)])
        try:
            rep = floor.run(Path(td), reps=2)
        finally:
            if old is None:
                os.environ.pop("PP_EVAL_CLAUDE_CMD", None)
            else:
                os.environ["PP_EVAL_CLAUDE_CMD"] = old
        arms = rep["summary"]["arms"]
        voids = [r["void"] for r in rep["runs"] if r["void"]]
        check("V-FLOOR-E2E-ALL-CONTROLS-HOLD", rep["summary"]["verdict"] == "MEASURED" and not voids, voids)
        check("V-FLOOR-E2E-DELTAS", arms["context"]["delta"] == 20000 and arms["hooks"]["delta"] == 7000
              and arms["skills"]["delta"] == 9000 and arms["mcp"]["delta"] == 3000
              and arms["plugins"]["delta"] == 4000 and arms["all"]["delta"] == 43000,
              {k: v.get("delta") for k, v in arms.items()})
        check("V-FLOOR-E2E-AA-ZERO-NOISE", rep["summary"]["aa_noise"] == 0
              and arms["hooks"]["significance"] == "ABOVE_NOISE", rep["summary"]["aa_noise"])

    print(f"FLOOR_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
