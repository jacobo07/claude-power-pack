#!/usr/bin/env python
"""V-MG-* gates for hooks/lib/mission_gate.js, driven through node the way the registered hook is.

CCR v5 Stage A, A3/A4. Measured 2026-10-15: a cost hold reached the worker only as a PostToolUse notice, a worker
could write its own record, and one gsd-planner subagent spent 24.0M in 157 calls with no cap. Each denial has a
paired control that is admitted. Hermetic: temp state dir, mission records made by the real gsd_mission.create.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="mission-gate-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_MISSION_RECOVERY"] = "off"
HERE = Path(__file__).resolve().parent
HOOKS = HERE.parent / "hooks"
sys.path.insert(0, str(HERE))
import gsd_mission as gm  # noqa: E402

NOW = 1_800_000_000.0
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def node(module: str, fn: str, event: dict, env: dict | None = None):
    js = (f"const m=require({json.dumps(str(HOOKS / module))});"
          f"Promise.resolve(m.{fn}({json.dumps(event)})).then(r=>process.stdout.write(JSON.stringify(r)))")
    out = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60,
                         env={**os.environ, "GSD_AUTORUN_MARKER_DIR": TMP, "GSD_LONG_RUN_STATE_DIR": TMP,
                              **(env or {})})
    return json.loads(out.stdout or "null")


def gate(event: dict, env: dict | None = None):
    return node("lib/mission_gate.js", "run", {"cwd": TMP, **event}, env)


def denied(r) -> str:
    return ((r or {}).get("hookSpecificOutput") or {}).get("permissionDecisionReason", "") if r else ""


def worker(mid: str) -> str:
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    sid = f"{mid}-w"
    owner = {"session_id": sid, "pid": None, "proc_start": None, "heartbeat_at": NOW, "epoch": 1, "kind": "background"}
    rec = gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW, state=gm.RUNNING,
                        epoch=1, max_hours=100.0, owner=owner)
    gm.write_worker_index(rec, sid)
    return sid


def main() -> int:
    # 1. cost hold: every tool refused for the worker; Owner hold, no hold and a stranger are untouched.
    held = worker("m-a00001")
    gm.set_owner_hold("m-a00001", "cost breaker: processed 9 > 2 x estimate 3", now=NOW, kind="cost")
    for tool in ("Bash", "Read", "Edit", "Grep"):
        r = gate({"session_id": held, "tool_name": tool, "tool_input": {"command": "git status", "file_path": "x"}})
        check(f"V-MG-COST-HOLD-DENIES-{tool}", "MISSION COST HOLD" in denied(r), denied(r)[:90])
    legacy = worker("m-a00002")
    gm.set_owner_hold("m-a00002", "cost breaker: old record without kind", now=NOW)
    check("V-MG-COST-HOLD-LEGACY-PREFIX", "MISSION COST HOLD" in denied(gate({"session_id": legacy, "tool_name": "Bash",
          "tool_input": {"command": "ls"}})), "reason prefix recognised")
    owner = worker("m-a00003")
    gm.set_owner_hold("m-a00003", "Owner park for review", now=NOW)
    check("V-MG-CONTROL-OWNER-HOLD-ALLOWED", gate({"session_id": owner, "tool_name": "Bash",
          "tool_input": {"command": "git status"}}) is None, "an Owner park is not a cost hold")
    free = worker("m-a00004")
    check("V-MG-CONTROL-UNHELD-ALLOWED", gate({"session_id": free, "tool_name": "Bash",
          "tool_input": {"command": "git status"}}) is None)
    check("V-MG-CONTROL-STRANGER-ALLOWED", gate({"session_id": "not-a-worker", "tool_name": "Bash",
          "tool_input": {"command": "ls"}}) is None)
    check("V-MG-KILL-SWITCH", gate({"session_id": held, "tool_name": "Bash", "tool_input": {"command": "ls"}},
                                   {"CPP_MISSION_GATE": "off"}) is None, "CPP_MISSION_GATE=off")

    # 2. authority: a worker may not write its own record or run a state-changing verb.
    rec_path = str(Path(TMP) / "gsd-mission-m-aaaaaa.json")
    for label, ev in (
        ("ENVELOPE-VERB", {"tool_name": "Bash", "tool_input": {"command": "python tools/gsd_mission.py envelope m-1 --phase-forecast 90M"}}),
        ("HOLD-RELEASE", {"tool_name": "Bash", "tool_input": {"command": "python gsd_mission.py release m-1"}}),
        ("EDIT-RECORD", {"tool_name": "Edit", "tool_input": {"file_path": rec_path}}),
        ("WRITE-RECORD", {"tool_name": "Write", "tool_input": {"file_path": rec_path}}),
        ("BASH-RECORD", {"tool_name": "Bash", "tool_input": {"command": f"python -c \"open(r'{rec_path}','w')\""}}),
        ("POWERSHELL-MARKER", {"tool_name": "PowerShell", "tool_input": {"command": "Remove-Item $env:TEMP\\mission-worker-x.json"}}),
    ):
        check(f"V-MG-AUTHORITY-DENIES-{label}", "MISSION AUTHORITY" in denied(gate({"session_id": free, **ev})), label)
    for label, ev in (
        ("STATUS-VERB", {"tool_name": "Bash", "tool_input": {"command": "python tools/gsd_mission.py status m-1"}}),
        ("READ-RECORD", {"tool_name": "Read", "tool_input": {"file_path": rec_path}}),
        ("ORDINARY-EDIT", {"tool_name": "Edit", "tool_input": {"file_path": "tools/phase_lease.py"}}),
        ("GIT", {"tool_name": "Bash", "tool_input": {"command": "git commit -m x"}}),
    ):
        check(f"V-MG-CONTROL-ALLOWS-{label}", gate({"session_id": free, **ev}) is None, label)
    check("V-MG-AUTHORITY-STRANGER-UNTOUCHED", gate({"session_id": "not-a-worker", "tool_name": "Edit",
          "tool_input": {"file_path": rec_path}}) is None, "only a mission worker is fenced")

    # 3. subagent call cap: per agent id, the cap-th call passes and the next is refused; others unaffected.
    cap3 = {"CPP_SUBAGENT_CAP_CALLS": "3"}
    sub = lambda aid, **k: {"session_id": free, "tool_name": "Read", "agent_id": aid, "agent_type": "gsd-planner",  # noqa: E731
                            "tool_input": {"file_path": "a"}, **k}
    results = [gate(sub("a1"), cap3) for _ in range(4)]
    check("V-MG-SUBAGENT-CAP-ALLOWS-UP-TO-CAP", all(r is None for r in results[:3]), "calls 1-3 admitted")
    check("V-MG-SUBAGENT-CAP-DENIES-PAST", "SUBAGENT CAP" in denied(results[3]) and "call 4" in denied(results[3]),
          denied(results[3])[:80])
    check("V-MG-CONTROL-OTHER-AGENT-OWN-COUNT", gate(sub("a9"), cap3) is None, "a second agent starts at 0")
    check("V-MG-CONTROL-MAIN-THREAD-UNCOUNTED", all(gate({"session_id": free, "tool_name": "Read",
          "tool_input": {"file_path": "a"}}, cap3) is None for _ in range(6)), "no agent_id/agent_type -> not capped")
    gm.transition("m-a00004", expect_epoch=1, expect_state=gm.RUNNING, event="t_caps",
                  subagent_caps={"gsd-planner": {"calls": 1}})
    r = [gate(sub("a2"), cap3) for _ in range(2)]
    check("V-MG-RECORD-CAP-WINS-OVER-ENV", r[0] is None and "SUBAGENT CAP" in denied(r[1]), "record calls=1 beats env 3")
    r = [gate(sub("a3", agent_type="gsd-executor"), cap3) for _ in range(2)]
    check("V-MG-CONTROL-OTHER-TYPE-USES-ENV", all(x is None for x in r), "record cap is per type")

    # 4. subagent token cap read from <sid>/subagents/agent-<id>.jsonl, deduped by message id.
    proj = Path(TMP) / "proj"
    sdir = proj / free / "subagents"
    sdir.mkdir(parents=True)
    row = lambda i, n: json.dumps({"uuid": f"u{i}", "message": {"id": f"msg-{i}", "model": "claude", "usage": {  # noqa: E731
        "input_tokens": n, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": 0}}})
    (sdir / "agent-t1.jsonl").write_text("\n".join([row(1, 600), row(1, 600), row(2, 600)]) + "\n", encoding="utf-8")
    tp = str(proj / f"{free}.jsonl")
    tok = {"CPP_SUBAGENT_CAP_TOKENS": "1000", "CPP_SUBAGENT_CAP_CALLS": "99"}
    r = gate({**sub("t1"), "transcript_path": tp}, tok)
    check("V-MG-SUBAGENT-TOKENS-DENIES", "SUBAGENT CAP" in denied(r) and "1,200" in denied(r),
          denied(r)[:110] + "  (msg-1 counted once: 1,200 not 1,800)")
    (sdir / "agent-t2.jsonl").write_text(row(1, 400) + "\n", encoding="utf-8")
    check("V-MG-CONTROL-SUBAGENT-UNDER-TOKEN-CAP", gate({**sub("t2"), "transcript_path": tp}, tok) is None, "400 < 1000")
    check("V-MG-CONTROL-NO-TRANSCRIPT-NOT-A-TOKEN-DENY", gate({**sub("t3"), "transcript_path": tp}, tok) is None,
          "an absent subagent file is unmeasured here; the call cap still governs")

    # 4b. next-call exposure: used + last-call context past the hard cap is refused; under the cap is admitted.
    cx = worker("m-a00005")
    cproj = Path(TMP) / "cproj"
    cproj.mkdir()
    ctp = cproj / f"{cx}.jsonl"
    ctp.write_text("\n".join([row(1, 400_000), row(2, 500_000)]) + "\n", encoding="utf-8")
    gm.transition("m-a00005", expect_epoch=1, expect_state=gm.RUNNING, event="t_cap", authority_tokens=1_000_000)
    r = gate({"session_id": cx, "tool_name": "Read", "tool_input": {"file_path": "a"}, "transcript_path": str(ctp)})
    check("V-MG-NEXT-CALL-DENIES-NEAR-CAP", "MISSION CAP" in denied(r) and "authority hard cap 1,000,000" in denied(r),
          denied(r)[:120] + "  (900,000 used + 500,000 next > 1,000,000)")
    gm.transition("m-a00005", expect_epoch=1, expect_state=gm.RUNNING, event="t_cap2", authority_tokens=2_000_000)
    check("V-MG-CONTROL-NEXT-CALL-UNDER-CAP-ALLOWED", gate({"session_id": cx, "tool_name": "Read",
          "tool_input": {"file_path": "a"}, "transcript_path": str(ctp)}) is None, "1,400,000 <= 2,000,000")
    check("V-MG-CONTROL-NEXT-CALL-NO-TRANSCRIPT-ALLOWED", gate({"session_id": cx, "tool_name": "Read",
          "tool_input": {"file_path": "a"}}) is None, "unmeasured is not a deny here")

    # 5. wired through the registered guard: the same refusal comes out of session_budget_guard.decide.
    out = node("session_budget_guard.js", "decide", {"session_id": held, "tool_name": "Bash",
                                                       "tool_input": {"command": "ls"}, "cwd": TMP})
    check("V-MG-GUARD-DELEGATES-COST-HOLD", "MISSION COST HOLD" in denied(out), denied(out)[:90])
    out = node("session_budget_guard.js", "decide", {"session_id": "not-a-worker", "tool_name": "Bash",
                                                       "tool_input": {"command": "ls"}, "cwd": TMP})
    check("V-MG-CONTROL-GUARD-STRANGER-NULL", out is None, str(out))

    # 6. T1 F1: the standalone hold gate, driven through its stdin entrypoint the way a direct "*" registration
    # runs it (GEX44 has no dispatcher lane). Hold-only: it never bumps a subagent counter.
    def stdin_gate(event: dict, env: dict | None = None, raw: str | None = None):
        out = subprocess.run(["node", str(HOOKS / "mission_hold_gate.js")], capture_output=True, text=True, timeout=60,
                             input=raw if raw is not None else json.dumps(event),
                             env={**os.environ, "GSD_AUTORUN_MARKER_DIR": TMP, "GSD_LONG_RUN_STATE_DIR": TMP, **(env or {})})
        return out.returncode, json.loads(out.stdout) if out.stdout.strip() else None
    counters = Path(TMP) / f"mission-subagents-{held}.json"
    before = counters.read_text(encoding="utf-8") if counters.exists() else None
    for tool in ("Glob", "WebFetch", "mcp__x__y", "Skill"):
        rc, r = stdin_gate({"session_id": held, "tool_name": tool, "tool_input": {}})
        check(f"V-MG-HOLDGATE-DENIES-{tool}", rc == 0 and "MISSION COST HOLD" in denied(r), denied(r)[:80])
    rc, r = stdin_gate({"session_id": held, "tool_name": "Read", "agent_id": "s1", "agent_type": "gsd-executor",
                        "tool_input": {"file_path": "a"}})
    check("V-MG-HOLDGATE-DENIES-SUBAGENT", "MISSION COST HOLD" in denied(r), "subagent carries the parent's session_id")
    after = counters.read_text(encoding="utf-8") if counters.exists() else None
    check("V-MG-HOLDGATE-BUMPS-NO-COUNTER", before == after, "hold-only: safe beside the dispatcher lane")
    authority = worker("m-a00006")
    gm.set_owner_hold("m-a00006", "cost breaker (mission authority): processed 152,641,947 >= authority 80,000,000",
                      now=NOW, kind="cost")
    check("V-MG-HOLDGATE-DENIES-AUTHORITY-HOLD", "MISSION COST HOLD" in denied(stdin_gate(
          {"session_id": authority, "tool_name": "Bash", "tool_input": {"command": "ls"}})[1]))
    for label, ev, env, raw in (
        ("OWNER-HOLD", {"session_id": owner, "tool_name": "Bash"}, None, None),
        ("UNHELD", {"session_id": free, "tool_name": "Bash"}, None, None),
        ("STRANGER", {"session_id": "not-a-worker", "tool_name": "Bash"}, None, None),
        ("KILL-SWITCH", {"session_id": held, "tool_name": "Bash"}, {"CPP_MISSION_GATE": "off"}, None),
        ("GARBAGE-STDIN", {}, None, "not json"),
        ("EMPTY-STDIN", {}, None, ""),
    ):
        rc, r = stdin_gate(ev, env, raw)
        check(f"V-MG-CONTROL-HOLDGATE-{label}-ALLOWED", rc == 0 and r is None, f"rc={rc} out={r}")

    print(f"MISSION_GATE_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    shutil.rmtree(TMP, ignore_errors=True)
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
