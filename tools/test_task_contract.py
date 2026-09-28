"""V-TCON-*: tools/task_contract.py -- delegated-work contracts rendered through the vendored kit.

The end-to-end half drives the REAL agent-solo-guard (~/.claude/hooks/agent-solo-guard.js) with a
PreToolUse payload, each call under its own temporary home so the guard's tracker and log never
touch the Owner's state -- and with a control that the guard still blocks a contract lacking the
durable clause, or its "pass" would prove nothing.
    python tools/test_task_contract.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import task_contract as tc  # noqa: E402
from modules.external_assimilation import node_bridge as nb  # noqa: E402

GUARD = Path.home() / ".claude" / "hooks" / "agent-solo-guard.js"
passes = fails = 0


def check(gate: str, cond: bool, ev: object = "") -> None:
    global passes, fails
    if cond:
        passes += 1
        print(f"  PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"  FAIL {gate}: {ev}")


def base(**kw) -> dict:
    args = dict(id="t-1", objective="audit tools/gsd_mission.py for unbounded loops", owner="general-purpose",
                acceptance=["every finding cites file:line"], stop="all loops classified or 30 minutes",
                writes=["_logs/audit.md"], durable_output="_logs/audit.md")
    args.update(kw)
    return tc.build(**args)


def guard(prompt: str) -> tuple[int, str]:
    """Drive the real guard once under a throwaway home. Returns (exit, stdout)."""
    home = Path(tempfile.mkdtemp(prefix="tcon_home_"))
    try:
        (home / ".claude" / "state").mkdir(parents=True)
        env = {**os.environ, "USERPROFILE": str(home), "HOME": str(home)}
        payload = {"tool_name": "Agent", "hook_event_name": "PreToolUse",
                   "tool_input": {"prompt": prompt, "subagent_type": "general-purpose", "description": "x"}}
        p = subprocess.run([nb.node_exe() or "node", str(GUARD)], input=json.dumps(payload).encode("utf-8"),
                           capture_output=True, env=env, timeout=60)
        return p.returncode, p.stdout.decode("utf-8", errors="replace")
    finally:
        shutil.rmtree(home, ignore_errors=True)


def main() -> int:
    print("build: the two CPP clauses")
    c = base()
    check("V-TCON-KEYSET-EXACT", sorted(c) == sorted(["id", "objective", "owner", "inputs", "outputs", "dependencies",
                                                      "constraints", "acceptance", "budget", "stopCondition"]), sorted(c))
    check("V-TCON-DURABLE-CLAUSE", c["outputs"][0] == "_logs/audit.md"
          and any("as you go" in x for x in c["constraints"]), c["constraints"])
    check("V-TCON-WRITE-OWNERSHIP", "Write only: _logs/audit.md" in c["constraints"], c["constraints"])
    ro = base(writes=[], durable_output=None)
    check("V-TCON-READ-ONLY-STATED", "Writes nothing: read-only role" in ro["constraints"] and ro["outputs"] == [], ro)
    for gate, kw, needle in [("V-TCON-UNSTATED-WRITES-REFUSED", {"writes": None}, "must be stated"),
                             ("V-TCON-UNWRITABLE-OUTPUT-REFUSED", {"writes": [], "durable_output": "_logs/a.md"},
                              "not among the paths")]:
        try:
            base(**kw)
            check(gate, False, "built")
        except ValueError as exc:
            check(gate, needle in str(exc), str(exc))

    print("render through the kit: both poles")
    r = tc.render(c)
    check("V-TCON-RENDERED", r.outcome == tc.RENDERED and r.text.startswith("Task t-1: audit")
          and "Stop when: all loops classified" in r.text and "as you go" in r.text, r.text[:120])
    bad = {**c, "acceptance": []}
    rb = tc.render(bad)
    check("V-TCON-KIT-REFUSES-NO-ACCEPTANCE", rb.outcome == tc.REFUSED
          and any("acceptance" in e for e in rb.errors), rb.errors)
    extra = {**c, "surprise": 1}
    re_ = tc.render(extra)
    check("V-TCON-KIT-REFUSES-EXTRA-KEY", re_.outcome == tc.REFUSED, re_.errors)
    saved = os.environ.get("CPP_NODE_EXE")
    os.environ["CPP_NODE_EXE"] = str(Path(tempfile.gettempdir()) / "no-node-here.exe")
    try:
        rd = tc.render(c)
    finally:
        if saved is None:
            os.environ.pop("CPP_NODE_EXE", None)
        else:
            os.environ["CPP_NODE_EXE"] = saved
    check("V-TCON-BRIDGE-DOWN-UNJUDGED", rd.outcome == tc.UNJUDGED and not rd.text, rd.errors)

    print("end to end: the real agent-solo-guard")
    if not GUARD.is_file():
        check("V-TCON-GUARD-PRESENT", False, f"{GUARD} missing; the end-to-end half cannot run")
    else:
        code_ok, out_ok = guard(r.text)
        check("V-TCON-GUARD-PASSES-CONTRACT", code_ok == 0 and '"block"' not in out_ok, (code_ok, out_ok[:160]))
        naked = f"Task t-1: {c['objective']}\nReport what you find when done."
        code_bad, out_bad = guard(naked)
        # CONTROL: without it a guard that allowed everything would make the pass above meaningless.
        check("V-TCON-GUARD-BLOCKS-WITHOUT-CLAUSE", code_bad == 2 and '"block"' in out_bad, (code_bad, out_bad[:160]))

    print("CLI")
    tmp = Path(tempfile.mkdtemp(prefix="tcon_t_"))
    try:
        spec = tmp / "c.json"
        spec.write_text(json.dumps(dict(id="t-2", objective="x", owner="o", acceptance=["a"], stop="s",
                                        writes=[])), encoding="utf-8")
        check("V-TCON-CLI-OK", tc.main(["--spec", str(spec)]) == 0, "exit 0")
        spec.write_text(json.dumps(dict(id="t-2", objective="x", owner="o", acceptance=["a"], stop="s")),
                        encoding="utf-8")
        check("V-TCON-CLI-REFUSES-UNSTATED", tc.main(["--spec", str(spec)]) == 3, "exit 3")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    total = passes + fails
    print(f"TCON_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
