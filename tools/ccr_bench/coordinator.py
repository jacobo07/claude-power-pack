"""Synthetic coordinator profile + call classifier (Tramo A2 Phase 7, A2-17). NOTHING here is read from a real session.

The profile is shaped after the measured coordinator pattern (304 model boundaries, 67.9M carried tokens, p50 214K per boundary,
85 ssh calls) and generated deterministically, so the budget test is repeatable and never touches a live transcript.

classify(tool, tool_input) -> "status" | "relay" | "novel" by the call's INPUT, never by what the model said about it:
  status  a read-only question the providerless console answers from files (mission status, goal status, census, tail/cat/ls/ps)
  relay   moving a decision or a command to another session or host (SendMessage, resume/launch, authority/release/settle writes)
  novel   anything else: the only calls that need a model
"""
from __future__ import annotations

import random
import re

_STATUS = re.compile(r"(gsd_mission\.py\s+(status|show|list)\b|mission_spend\.py\s+goal-(status|lineage|autopsy)\b|"
                     r"ccr_generation_census|mission_console|\b(tail|cat|ls|ps|pgrep|wc|git\s+(log|status))\b)")
_RELAY = re.compile(r"(gsd_mission\.py\s+(authority|release|launch|resume|halt|settle)\b|mission_spend\.py\s+goal-(settle|correct|renew|spawn|lease-open)\b|"
                    r"claude\s+(--resume|-p)\b|kresume|git\s+(commit|push|fetch))")
_WRITE_REDIRECT = re.compile(r"(?<![0-9&])>>?(?!&)|\btee\b|\bsed\s+-i\b|\brm\b|\bmv\b")


def classify(tool: str, tool_input: dict) -> str:
    if tool in ("SendMessage",):
        return "relay"
    cmd = str((tool_input or {}).get("command") or "")
    if tool == "Bash" and cmd:
        if _RELAY.search(cmd) or _WRITE_REDIRECT.search(cmd):
            return "relay" if _RELAY.search(cmd) else "novel"
        if _STATUS.search(cmd):
            return "status"
    if tool == "Read":
        return "status"
    return "novel"


def fixture(seed: int = 5) -> list[dict]:
    """304 boundaries; 85 of them are ssh calls. Each row: {"tool","input","carried"}; carried sums to ~67.9M, p50 within 5% of 214K."""
    rnd = random.Random(seed)
    status_cmds = ["ssh gex44 'python3 tools/gsd_mission.py status'", "ssh gex44 'python3 tools/mission_spend.py goal-status --goal ccr'",
                   "ssh gex44 'tail -n 40 /var/log/mission.log'", "ssh gex44 'pgrep -af claude'", "python3 tools/gsd_mission.py status",
                   "ssh gex44 'ls /home/kobii/missions'", "ssh gex44 'python3 tools/ccr_generation_census.py'"]
    relay_cmds = ["ssh gex44 'python3 tools/gsd_mission.py authority --mission m-x --tokens 9000000'",
                  "ssh gex44 'python3 tools/gsd_mission.py release --mission m-x'", "ssh gex44 'git fetch origin'"]
    novel_cmds = ["python3 -m pytest tools/test_x.py -q", "ssh gex44 'python3 build_capsule.py > /tmp/out.json'", "grep -rn TODO modules/"]
    local_status = [c for c in status_cmds if not c.startswith("ssh")] + ["tail -n 40 mission.log", "ls missions", "cat STATE.md"]
    local_novel = [c for c in novel_cmds if not c.startswith("ssh")]
    rows = []
    for i in range(304):
        r = rnd.random()
        if i < 85:
            cmd = rnd.choice(status_cmds[:4] + status_cmds[5:] + relay_cmds) if r < 0.9 else rnd.choice(novel_cmds[1:2])
            row = {"tool": "Bash", "input": {"command": cmd}}
        elif r < 0.30:
            row = {"tool": "Bash", "input": {"command": rnd.choice(local_status)}}
        elif r < 0.45:
            row = {"tool": "SendMessage", "input": {"to": "worker", "message": "continue"}}
        elif r < 0.55:
            row = {"tool": "Read", "input": {"file_path": "/home/kobii/missions/STATE.md"}}
        else:
            row = {"tool": "Bash", "input": {"command": rnd.choice(local_novel)}}
        rows.append(row)
    # carried grows with the session: a ramp whose median is 214K and whose total is 67.9M (measured profile, not content)
    n = len(rows)
    for i, row in enumerate(rows):
        row["carried"] = int(60_000 + (i / (n - 1)) * 308_000) if n > 1 else 214_000
    scale = 67_900_000 / sum(r["carried"] for r in rows)
    for row in rows:
        row["carried"] = int(row["carried"] * scale)
    return rows


def profile(rows: list[dict], covered: frozenset = frozenset({"status"})) -> dict:
    """Boundaries and carried tokens by class; `covered` classes are answered by the console and cost 0 model boundaries."""
    by = {"status": [0, 0], "relay": [0, 0], "novel": [0, 0]}
    for r in rows:
        k = classify(r["tool"], r["input"])
        by[k][0] += 1
        by[k][1] += r["carried"]
    paid = {k: (0 if k in covered else v[0]) for k, v in by.items()}
    paid_tok = {k: (0 if k in covered else v[1]) for k, v in by.items()}
    return {"by_class": {k: {"calls": v[0], "carried": v[1]} for k, v in by.items()},
            "model_boundaries": sum(paid.values()), "carried_after": sum(paid_tok.values()),
            "status_boundaries": paid["status"]}
