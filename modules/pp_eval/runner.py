"""One eval run (spec §3.4): a fresh worktree at the task's parent, one headless session with
the layer's arm applied, then the fix's hidden tests copied in and run as the grade.

Every run records the evidence its positive control needs, so a verdict can refuse runs
where the arm did not actually remove what it claims to (the P3 lesson: prove arm B differs).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path

from .common import add_worktree, drop_worktree, git, run, utc_now
from .harvest import test_command

LAYERS = ("context", "hooks", "skills")
TIMEOUT_S = 1500
MAX_TURNS = "40"
ALLOWED = "Read,Edit,Write,Grep,Glob,Bash,PowerShell"
QUOTA_TEXT = re.compile(r"usage limit|rate.?limit|limit reached|quota", re.I)


def claude_cmd() -> list[str]:
    """The claude executable, overridable (as a JSON argv prefix) for the fake used in gates."""
    raw = os.environ.get("PP_EVAL_CLAUDE_CMD")
    if raw:
        return json.loads(raw)
    return [str(Path.home() / ".local" / "bin" / "claude.exe")]


def context_files() -> list[str]:
    """Always-loaded context the context arm excludes: every rules file plus CLAUDE.md files."""
    home = Path.home()
    files = sorted((home / ".claude" / "rules").rglob("*.md"))
    files += [home / ".claude" / "CLAUDE.md", home / "CLAUDE.md"]
    return [str(p).replace("\\", "/") for p in files if p.exists()]


def arm_args(layer: str, arm: str) -> list[str]:
    if arm == "A":
        return []
    if layer == "context":
        return ["--settings", json.dumps({"claudeMdExcludes": context_files()})]
    if layer == "hooks":
        return ["--settings", json.dumps({"disableAllHooks": True})]
    if layer == "skills":
        return ["--disable-slash-commands"]
    raise ValueError(f"unknown layer {layer!r}")


def build_cmd(layer: str, arm: str, prompt: str) -> list[str]:
    return [*claude_cmd(), "-p", prompt, "--output-format", "stream-json", "--verbose",
            "--include-hook-events", "--no-session-persistence", "--max-turns", MAX_TURNS,
            "--permission-mode", "acceptEdits", "--allowedTools", ALLOWED, *arm_args(layer, arm)]


def prompt_for(task: dict) -> str:
    tests = ", ".join(f"`{t}`" for t in task["tests"])
    return (f"In this repository the following is broken: \"{task['subject']}\". Fix it in the "
            f"source code. After you finish, {tests} will be run to check the fix; the version "
            "that checks it is not in the tree. Stop when the fix is done.")


def child_env() -> dict:
    env = {k: v for k, v in os.environ.items()
           if not (k.startswith("CLAUDECODE") or k.startswith("CLAUDE_CODE_"))}
    env["CLAUDEPP_EVAL_CHILD"] = "1"
    return env


def parse_stream(text: str, task: dict, bank_marker: str) -> dict:
    """Evidence from the stream-json transcript. Unparseable lines are counted, not dropped."""
    ev = {"hook_events": 0, "skills_loaded": None, "first_call_context": None, "total_context": 0,
          "output_tokens": 0, "calls": 0, "result": None, "num_turns": None, "is_error": None,
          "api_error_status": None, "max_utilization": 0.0, "bank_access": False, "bad_lines": 0}
    secrets = [bank_marker, task["fix"][:12], *(f"{task['fix']}:{t}" for t in task["tests"])]
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            ev["bad_lines"] += 1
            continue
        kind, sub = o.get("type"), o.get("subtype")
        if kind == "system" and sub == "hook_started":
            ev["hook_events"] += 1
        elif kind == "system" and sub == "init":
            ev["skills_loaded"] = len(o.get("skills") or [])
        elif kind == "rate_limit_event":
            info = o.get("rate_limit_info") or {}
            for name, win in (info.get("unifiedWindows") or {}).items():
                util = float(win.get("utilization") or 0)
                ev["max_utilization"] = max(ev["max_utilization"], util)
                ev.setdefault("windows", {})[name] = {"utilization": util, "resetsAt": win.get("resetsAt")}
        elif kind == "assistant":
            msg = o.get("message") or {}
            u = msg.get("usage") or {}
            ctx = (u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0)
                   + u.get("cache_creation_input_tokens", 0))
            if ev["first_call_context"] is None:
                ev["first_call_context"] = ctx
            ev["total_context"] += ctx
            ev["output_tokens"] += u.get("output_tokens", 0)
            ev["calls"] += 1
            for part in msg.get("content") or []:
                if part.get("type") == "tool_use":
                    blob = json.dumps(part.get("input", {}))
                    if any(s and s in blob for s in secrets):
                        ev["bank_access"] = True
        elif kind == "result":
            ev.update(result=sub, num_turns=o.get("num_turns"), is_error=o.get("is_error"),
                      api_error_status=o.get("api_error_status"))
            ev["result_text"] = str(o.get("result") or "")[:300]
    return ev


def quota_hit(ev: dict, rc) -> bool:
    if ev.get("api_error_status") == 429:
        return True
    return bool(ev.get("is_error") or rc not in (0, None)) and bool(
        QUOTA_TEXT.search(ev.get("result_text") or ""))


def void_reasons(layer: str, arm: str, ev: dict, rc) -> list[str]:
    """Per-run validity. The context control is pairwise and is judged in the verdict."""
    r = []
    if rc == "timeout":
        r.append("session timeout")
    if ev["result"] is None:
        r.append("no result event")
    if ev["bank_access"]:
        r.append("agent touched the hidden bank or fix")
    if layer == "hooks" and arm == "A" and ev["hook_events"] == 0:
        r.append("hooks control: arm A saw no hook events")
    if layer == "hooks" and arm == "B" and ev["hook_events"] > 0:
        r.append("hooks control: arm B still ran hooks")
    if layer == "skills" and arm == "B" and (ev["skills_loaded"] or 0) > 0:
        r.append("skills control: arm B still loaded skills")
    if layer == "skills" and arm == "A" and not ev["skills_loaded"]:
        r.append("skills control: arm A loaded no skills")
    return r


def grade(wt: Path, task: dict) -> tuple[bool, list]:
    repo = Path(task["repo"])
    rcs = []
    for path in task["tests"]:
        text = git(repo, "show", f"{task['fix']}:{path}")
        dest = wt / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
        rc, _ = run(test_command(path, text), wt, 120)
        rcs.append(rc)
    return all(rc == 0 for rc in rcs), rcs


def session(cmd: list[str], cwd: Path, timeout: int, env: dict) -> tuple[object, str]:
    """(returncode | 'timeout' | 'oserror', full stdout). The whole stream is evidence, so it
    is never truncated; a timeout keeps whatever was streamed before it."""
    try:
        r = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout, env=env)
        return r.returncode, r.stdout
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        return "timeout", out
    except OSError:
        return "oserror", ""


def one_run(task: dict, layer: str, arm: str, rep: int, bank_marker: str) -> dict:
    rec = {"run_id": f"{task['id']}|{layer}|{arm}|r{rep}", "task": task["id"], "layer": layer,
           "arm": arm, "rep": rep, "started": utc_now()}
    repo = Path(task["repo"])
    wt = add_worktree(repo, task["parent"], f"run-{task['fix'][:8]}-{layer}-{arm}-{rep}")
    try:
        t0 = time.time()
        rc, stream = session(build_cmd(layer, arm, prompt_for(task)), wt, TIMEOUT_S, child_env())
        rec["wall_s"] = round(time.time() - t0, 1)
        ev = parse_stream(stream, task, bank_marker)
        rec.update(claude_rc=rc, evidence=ev)
        if quota_hit(ev, rc):
            rec["status"] = "DEFERRED_QUOTA"
            return rec
        reasons = void_reasons(layer, arm, ev, rc)
        if reasons:
            rec["status"], rec["void_reasons"] = "VOID", reasons
            return rec
        ok, rcs = grade(wt, task)
        rec.update(status="VALID", task_pass=ok, grade_rcs=rcs)
        return rec
    finally:
        rec["ended"] = utc_now()
        drop_worktree(repo, wt)