"""Startup-floor attribution: what each always-on lever adds to a session's FIRST model call.

One headless call per arm, same prompt, same model, same cwd. Arm A is everything on; each lever
arm switches one lever off; `all` switches every lever off. The delta of a lever is
median(A) - median(lever), and it counts only when it exceeds the A/A spread (two replicates of A).

Every lever arm carries a positive control read from the stream itself, so an arm that silently
loaded everything is VOID, never a "0 delta":
  hooks    no hook_started events           skills   init.skills is empty
  mcp      fewer init.mcp_servers than A    plugins  no non-builtin init.plugins
  context  first call lower than A by more than the A/A spread (judged pairwise, as in P3)
A quota refusal or a `<synthetic>` reply is UNMEASURED, never a zero.

This measures REMOVAL. A lever's delta is what switching it off saves; whether its content can be
moved without losing behaviour is a separate claim that needs a load-back path (plan T5).

    python -m modules.pp_eval.floor --cwd <dir> [--reps 2] [--out report.json]
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from pathlib import Path

from .runner import child_env, claude_cmd, context_files, session

PROMPT = "Reply with the single word ok."
MODEL = "claude-opus-5-5"
TIMEOUT_S = 300
LEVERS = ("context", "hooks", "skills", "mcp", "plugins")


def enabled_plugins(settings_path: Path = Path.home() / ".claude" / "settings.json") -> list[str]:
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return []
    return sorted(k for k, v in (data.get("enabledPlugins") or {}).items() if v)


def arm_args(arm: str) -> list[str]:
    """CLI arguments for one arm. `all` merges every lever into ONE --settings object."""
    levers = LEVERS if arm == "all" else (() if arm == "A" else (arm,))
    unknown = [lv for lv in levers if lv not in LEVERS]
    if unknown or (arm not in ("A", "all") and arm not in LEVERS):
        raise ValueError(f"unknown arm {arm!r}")
    settings: dict = {}
    flags: list[str] = []
    for lv in levers:
        if lv == "context":
            # PP_FLOOR_CONTEXT_FILES (JSON list) names the instruction files when they are staged
            # somewhere other than this host's home, e.g. a laptop's CLAUDE.md+rules copied to a probe
            # directory on another host. Unset = this host's own files.
            raw = os.environ.get("PP_FLOOR_CONTEXT_FILES")
            settings["claudeMdExcludes"] = json.loads(raw) if raw else context_files()
        elif lv == "hooks":
            settings["disableAllHooks"] = True
        elif lv == "plugins":
            settings["enabledPlugins"] = {p: False for p in enabled_plugins()}
        elif lv == "skills":
            flags.append("--disable-slash-commands")
        elif lv == "mcp":
            flags.append("--strict-mcp-config")
    return (["--settings", json.dumps(settings)] if settings else []) + flags


def build_cmd(arm: str) -> list[str]:
    return [*claude_cmd(), "-p", PROMPT, "--output-format", "stream-json", "--verbose",
            "--include-hook-events", "--no-session-persistence", "--max-turns", "1",
            "--model", MODEL, *arm_args(arm)]  # tool schemas stay on: they are part of the floor


def parse(text: str) -> dict:
    """Evidence from one stream. First call = input + cache creation + cache read of the first
    assistant usage. Hook injections are recorded by event with size and a short fingerprint: the
    stream carries no script identity, so the fingerprint is the only name a hook has here."""
    ev = {"state": "UNMEASURED", "reason": "no assistant usage", "first_call": None,
          "init": None, "hook_started": 0, "injections": [], "bad_lines": 0}
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            ev["bad_lines"] += 1
            continue
        kind, sub = o.get("type"), o.get("subtype")
        if kind == "system" and sub == "init":
            ev["init"] = {k: len(o.get(k) or []) for k in ("tools", "skills", "agents", "slash_commands")}
            ev["init"]["mcp_servers"] = len(o.get("mcp_servers") or [])
            ev["init"]["plugins_non_builtin"] = sum(
                1 for p in o.get("plugins") or [] if p.get("path") != "builtin")
        elif kind == "system" and sub == "hook_started":
            ev["hook_started"] += 1
        elif kind == "system" and sub == "hook_response":
            out = str(o.get("output") or "")
            if out.strip():
                ev["injections"].append({"event": o.get("hook_event"), "chars": len(out),
                                         "fingerprint": " ".join(out.split())[:80]})
        elif kind == "assistant" and ev["first_call"] is None:
            msg = o.get("message") or {}
            if msg.get("model") == "<synthetic>":
                ev["reason"] = "synthetic reply (quota or API refusal)"
                continue
            u = msg.get("usage") or {}
            ev["first_call"] = (int(u.get("input_tokens") or 0) + int(u.get("cache_creation_input_tokens") or 0)
                                + int(u.get("cache_read_input_tokens") or 0))
            ev["state"], ev["reason"] = "MEASURED", None
    return ev


def control_fails(arm: str, ev: dict, base: dict | None) -> str | None:
    """Why this arm did not remove what it claims to, or None. Context is judged in summarize()."""
    init = ev.get("init")
    if ev["state"] != "MEASURED":
        return ev["reason"]
    if init is None:
        return "no init event"
    if arm in ("hooks", "all") and ev["hook_started"] > 0:
        return "hooks still ran"
    if arm in ("skills", "all") and init["skills"] > 0:
        return "skills still loaded"
    if arm in ("plugins", "all") and init["plugins_non_builtin"] > 0:
        return "plugins still loaded"
    if arm in ("mcp", "all") and base and base.get("init") and init["mcp_servers"] >= base["init"]["mcp_servers"]:
        return "mcp servers not reduced"
    if arm == "A" and ev["hook_started"] == 0:
        return "arm A saw no hooks (baseline is not the real floor)"
    return None


def summarize(runs: list[dict]) -> dict:
    by_arm: dict[str, list[dict]] = {}
    for r in runs:
        by_arm.setdefault(r["arm"], []).append(r)
    a_vals = [r["ev"]["first_call"] for r in by_arm.get("A", []) if not r["void"]]
    if not a_vals:
        return {"verdict": "UNMEASURED", "reason": "no valid baseline run", "arms": {}}
    a_med = statistics.median(a_vals)
    noise = (max(a_vals) - min(a_vals)) if len(a_vals) > 1 else None
    arms = {}
    for arm, rs in sorted(by_arm.items()):
        vals = [r["ev"]["first_call"] for r in rs if not r["void"]]
        row = {"valid": len(vals), "void": [r["void"] for r in rs if r["void"]]}
        if vals:
            med = statistics.median(vals)
            delta = a_med - med
            row.update(median=med, delta=delta)
            if arm != "A":
                if noise is None:
                    row["significance"] = "UNJUDGED (one baseline replicate, no noise floor)"
                elif delta > noise:
                    row["significance"] = "ABOVE_NOISE"
                else:
                    row["significance"] = "WITHIN_NOISE"
                    if arm == "context":
                        row["void"].append("context control: first call not lower than A beyond noise")
        arms[arm] = row
    return {"verdict": "MEASURED", "baseline_median": a_med, "aa_noise": noise, "arms": arms}


def run(cwd: Path, reps: int = 2, arms: tuple[str, ...] = ("A", *LEVERS, "all")) -> dict:
    runs = []
    base = None
    for rep in range(reps):
        for arm in arms:
            t0 = time.time()
            rc, stream = session(build_cmd(arm), cwd, TIMEOUT_S, child_env())
            ev = parse(stream)
            if arm == "A" and base is None and ev["state"] == "MEASURED":
                base = ev
            runs.append({"arm": arm, "rep": rep, "rc": rc, "wall_s": round(time.time() - t0, 1),
                         "ev": ev, "void": control_fails(arm, ev, base)})
    return {"cwd": str(cwd), "model": MODEL, "prompt": PROMPT, "reps": reps,
            "summary": summarize(runs), "runs": runs}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cwd", required=True)
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--arms", default=",".join(("A", *LEVERS, "all")))
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    rep = run(Path(a.cwd), a.reps, tuple(x for x in a.arms.split(",") if x))
    text = json.dumps(rep, indent=1)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    print(json.dumps(rep["summary"], indent=1))
    return 0 if rep["summary"]["verdict"] == "MEASURED" else 3


if __name__ == "__main__":
    sys.exit(main())
