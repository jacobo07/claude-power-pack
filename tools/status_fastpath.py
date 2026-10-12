#!/usr/bin/env python3
"""Zero-model status answer for UserPromptSubmit (ctx-same-pane S4).

A prompt that is ONLY a status question ("estado", "como va", "status", ...) is answered by this hook with
decision=block + reason: the host shows the reason and no model turn runs (probe 2026-10-13: num_turns 0,
total_cost_usd 0). Anything else passes through untouched.

Fail-open: any error, an unknown session, or a projection slower than the deadline prints nothing and exits 0,
so the prompt reaches the model as usual. Kill switch: CPP_STATUS_FASTPATH=off.

    stdin : the UserPromptSubmit hook JSON (session_id, cwd, prompt)
    stdout: {"decision": "block", "reason": "<projection>"} or nothing
"""
from __future__ import annotations

import glob
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

DEADLINE_S = 3.0
STATE = Path(os.environ.get("CPP_STATUS_STATE_DIR") or Path.home() / ".claude" / "state")
GIT = os.environ.get("CPP_STATUS_GIT") or r"C:\Program Files\Git\cmd\git.exe"
LIVE_TOOLS = Path.home() / ".claude" / "skills" / "claude-power-pack" / "tools"

# Exact phrases after normalisation. A prompt with anything beyond one of these passes through.
STATUS_PHRASES = frozenset({
    "status", "estado", "como va", "como vamos", "como van", "que tal va", "en que estamos",
    "how is it going", "hows it going", "how are we doing", "progress", "progreso",
})


def normalise(prompt: str) -> str:
    s = unicodedata.normalize("NFKD", prompt or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = s.replace("'", "").replace("\u2019", "")
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return " ".join(s.split())


def is_status(prompt: str) -> bool:
    return normalise(prompt) in STATUS_PHRASES


def _same_dir(a: str, b: str) -> bool:
    return os.path.normcase(os.path.normpath(a or "")) == os.path.normcase(os.path.normpath(b or ""))


def missions_for(cwd: str) -> list[dict]:
    out = []
    for f in glob.glob(str(STATE / "gsd-mission-m-*.json")):
        try:
            d = json.loads(Path(f).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if _same_dir(d.get("cwd", ""), cwd):
            out.append({"id": d.get("mission_id"), "state": d.get("state"), "epoch": d.get("epoch"),
                        "updated_at": d.get("updated_at") or 0})
    return sorted(out, key=lambda m: m["updated_at"], reverse=True)[:3]


def bound_goal(session_id: str) -> str | None:
    f = STATE / "goal-binding" / f"{session_id}.json"
    try:
        return json.loads(f.read_text(encoding="utf-8")).get("goal")
    except (OSError, ValueError):
        return None


def goal_line(goal: str) -> str:
    # The ledger's owner is the LIVE Power Pack copy; a worktree's older mission_spend folds leases differently.
    sys.path.insert(0, os.environ.get("CPP_STATUS_LEDGER_TOOLS") or str(LIVE_TOOLS))
    import mission_spend as ms  # noqa: E402 -- deferred: only a status prompt pays the import
    s = ms._goal_ledger(goal).status()
    return (f"goal {goal}: lease used {s.get('used', 0):,} of {s.get('cap', 0):,}, open {s.get('open', 0):,}, "
            f"settled {s.get('settled', 0):,}" + (" (EXHAUSTED)" if s.get("exhausted") else ""))


def head_of(cwd: str) -> tuple[str, str] | None:
    """(branch, sha) read from the .git files: spawning git costs 1-2 s on a loaded host."""
    d = Path(cwd).resolve()
    for p in (d, *d.parents):
        g = p / ".git"
        if g.is_file():
            g = (p / g.read_text(encoding="utf-8").split("gitdir:", 1)[1].strip()).resolve()
        if g.is_dir():
            break
    else:
        return None
    common = g
    if (g / "commondir").is_file():
        common = (g / (g / "commondir").read_text(encoding="utf-8").strip()).resolve()
    head = (g / "HEAD").read_text(encoding="utf-8").strip()
    if not head.startswith("ref:"):
        return "(detached)", head[:8]
    ref = head.split(":", 1)[1].strip()
    branch = ref.removeprefix("refs/heads/")
    for base in (g, common):
        f = base / ref
        if f.is_file():
            return branch, f.read_text(encoding="utf-8").strip()[:8]
    packed = common / "packed-refs"
    if packed.is_file():
        for ln in packed.read_text(encoding="utf-8").splitlines():
            if ln.endswith(" " + ref):
                return branch, ln[:8]
    return branch, "(unborn)"


def git_line(cwd: str, timeout: float) -> str:
    h = head_of(cwd)
    if h is None:
        return "git: not a repository"
    try:
        st = subprocess.run([GIT, "-C", cwd, "status", "--porcelain", "-uno"], capture_output=True, text=True,
                            timeout=timeout, encoding="utf-8", errors="replace")
        dirty = str(len([ln for ln in st.stdout.splitlines() if ln])) if st.returncode == 0 else "unknown (git failed)"
    except subprocess.TimeoutExpired:
        dirty = "unknown (git status over the deadline)"
    return f"{h[0]} @ {h[1]} | dirty tracked {dirty}"


def project(event: dict, deadline: float) -> str:
    cwd = event.get("cwd") or os.getcwd()
    lines = [f"[status fast path: no model turn] {cwd}"]
    for m in missions_for(cwd):
        lines.append(f"mission {m['id']}: {m['state']} epoch {m['epoch']}")
    goal = bound_goal(event.get("session_id", ""))
    if goal:
        lines.append(goal_line(goal))
    left = deadline - time.monotonic()
    if left <= 0:
        raise TimeoutError("deadline before git")
    lines.append(git_line(cwd, left))
    if time.monotonic() > deadline:
        raise TimeoutError("deadline exceeded")
    lines.append("Ask anything else and it goes to the model as usual.")
    return "\n".join(lines)


def decide(event: dict, now=time.monotonic) -> dict | None:
    if os.environ.get("CPP_STATUS_FASTPATH", "").lower() == "off":
        return None
    if not is_status(event.get("prompt", "")):
        return None
    try:
        return {"decision": "block", "reason": project(event, now() + DEADLINE_S)}
    except Exception:  # fail-open: the prompt reaches the model unchanged
        return None


def main() -> int:
    try:
        event = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0
    out = decide(event)
    if out:
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
