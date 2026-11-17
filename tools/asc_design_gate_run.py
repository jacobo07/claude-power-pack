"""Paired measurement of the design surface router + design done-gate (spec vault/specs/design-surface-router.md).

Per task, two fresh `claude -p` agents get the SAME prompt:
  control  -- the task alone.
  treated  -- what the live harness gives a visual prompt: the route block (tools/design_route_prompt.block), the
              routed skills and the cdio-reviewer agent installed as PROJECT skills/commands/agents in its run dir,
              and ONE Stop round: the real tools/design_donegate_stop.decide() judges the arm's own transcript; on a
              block, the arm is resumed once with the block reason (the live gate blocks once per problem set and is
              silent while stop_hook_active).
Judging, per task: the Taste lint on both index.html (deterministic), and a BLIND pairwise judge (`claude -p`, no tools)
run twice with the order swapped; a winner counts only if it wins in both orders.

Output: <out>/<task>/{control,treated}/ + <out>/<task>/*.stream.jsonl + <out>/design_gate_run.json.
`--dry-run` prints the blocks and the planned commands and never calls a model. Run ONCE; reports read the artifact.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
OUT = ROOT / "vault/programs/ascension/design-gate"
_EXE = os.environ.get("CPP_CLAUDE_EXE") or os.path.expanduser("~/.local/claude-lf1/node_modules/.bin/claude")
# a JSON list is accepted too (e.g. ["python", "fake_claude.py"]): the offline drill drives the whole pipeline
CLAUDE = json.loads(_EXE) if _EXE.lstrip().startswith("[") else [_EXE]
TIMEOUT = 1500
_TAIL = ("Static HTML and CSS only (plain JS allowed), no frameworks, no build step, entry file index.html. Write the "
         "files in the current directory, then reply with one line listing the files.")
TASKS = {
    "saas": ("Build the marketing landing page for a small SaaS product that turns meeting recordings into action "
             "items. Hero with a headline and a call to action, a short features section, two customer testimonials, "
             "and a pricing section with two plans. " + _TAIL),
    "clinic": ("Build a single-page admin dashboard for a small physiotherapy clinic: today's appointments, a weekly "
               "room utilisation summary, and a list of patients awaiting a follow-up call, with sample data inline. "
               + _TAIL),
    "yoga": ("Haz la landing page de un estudio de yoga pequeño en Valencia: clases, horarios, precios de los bonos y "
             "un formulario para reservar la primera clase gratis. Todo el texto en español. " + _TAIL),
}
# What the live harness makes loadable, as project-scope copies (a fresh dir has no user skills under
# --setting-sources project). name -> (source in the repo, destination under <run>/.claude)
SKILL_SOURCES = {
    "design-taste-frontend": ("vendor/skills/design-taste-frontend/SKILL.md", "skills/design-taste-frontend/SKILL.md"),
    "frontend-design": ("vendor/skills/frontend-design/SKILL.md", "skills/frontend-design/SKILL.md"),
    "design-md": ("commands/design-md.md", "commands/design-md.md"),
    "ui-ux-pro-max": ("vendor/skills/ui-ux-pro-max/SKILL.md", "skills/ui-ux-pro-max/SKILL.md"),
    "mobile-app-ui-design": ("skills/mobile-app-ui-design/SKILL.md", "skills/mobile-app-ui-design/SKILL.md"),
}
LIVE_PP = r"C:\Users\User\.claude\skills\claude-power-pack"
JUDGE = """You are judging two web pages built from the same brief. You do not know how either was made.
Brief: {brief}

Question: which page reads LESS like generic AI-template output (stock hero + gradient + three icon cards, filler
verbs like "seamless"/"elevate", fake social proof, em-dash rhythm, emoji, interchangeable copy, decorative motion),
and is the more considered, specific, usable design? Judge the source as a designer would picture it rendered.

=== PAGE A ===
{a}
=== PAGE B ===
{b}

Reply with ONLY one JSON object, no prose: {{"winner": "A" | "B" | "tie", "slop_markers": {{"A": <int>, "B": <int>}},
"reasons": ["<short reason>", "..."]}}"""


def policy_for(task: str) -> dict:
    from modules.cdio import design_route as dr
    routes = dr.load_routes()
    return dr.policy(dr.classify(task, routes), routes)


def route_block(task: str) -> str:
    import design_route_prompt as drp
    pol = policy_for(task)
    return drp.block(pol) + ("\nPower Pack root (run its tools from there): %s" % ROOT)


def install_kit(run_dir: Path, pol: dict) -> list:
    """Project-scope skills/commands + the cdio-reviewer agent, so the treated arm can do what the block asks."""
    done = []
    for name in pol["required"] + pol["recommended"]:
        if name in SKILL_SOURCES:
            src, dst = SKILL_SOURCES[name]
            if (ROOT / src).is_file():
                p = run_dir / ".claude" / dst
                p.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / src, p)
                done.append(name)
    agent = (ROOT / "vault/agents/cdio-reviewer.md").read_text(encoding="utf-8").replace(LIVE_PP, str(ROOT))
    a = run_dir / ".claude" / "agents" / "cdio-reviewer.md"
    a.parent.mkdir(parents=True, exist_ok=True)
    a.write_text(agent, encoding="utf-8")
    return done + ["agent:cdio-reviewer"]


def claude_cmd(prompt: str, system: str | None, resume: str | None, treated: bool) -> list:
    tools = ["Write", "Edit", "Read", "Glob", "Grep", "Bash"] + (["Skill", "Task"] if treated else [])
    cmd = [*CLAUDE, "-p", prompt, "--setting-sources", "project", "--permission-mode", "acceptEdits",
           "--allowedTools", *tools, "--output-format", "stream-json", "--verbose"]
    if system:
        cmd += ["--append-system-prompt", system]
    if resume:
        cmd += ["--resume", resume]
    return cmd


def call(cmd: list, cwd: Path, stream: Path, env: dict) -> dict:
    t0 = time.time()
    p = subprocess.run(cmd, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=TIMEOUT, env=env)
    with open(stream, "a", encoding="utf-8") as fh:
        fh.write(p.stdout)
    sid, usage, tools, skills = "", {}, [], []
    for line in p.stdout.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        sid = ev.get("session_id") or sid
        if ev.get("type") == "assistant":
            for c in ev["message"].get("content", []):
                if c.get("type") == "tool_use":
                    tools.append(c["name"])
                    if c["name"] == "Skill":
                        skills.append(str((c.get("input") or {}).get("skill")))
        if ev.get("type") == "result":
            usage = ev.get("usage", {})
    return {"rc": p.returncode, "seconds": round(time.time() - t0, 1), "session_id": sid, "usage": usage,
            "tools": tools, "skills": skills, "stderr_tail": p.stderr[-300:]}


def run_arm(task_key: str, label: str, out: Path) -> dict:
    task = TASKS[task_key]
    d = out / task_key / label
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    stream = out / task_key / ("%s.stream.jsonl" % label)
    stream.write_text("", encoding="utf-8")
    treated = label == "treated"
    state = tempfile.mkdtemp(prefix="dsr-arm-")
    env = dict(os.environ, CPP_DESIGN_STATE_DIR=state, PYTHONIOENCODING="utf-8")
    rec = {"label": label, "calls": []}
    if treated:
        pol = policy_for(task)
        rec["kit"] = install_kit(d, pol)
        rec["kinds"] = pol["kinds"]
    first = call(claude_cmd(task, route_block(task) if treated else None, None, treated), d, stream, env)
    rec["calls"].append(first)
    if treated:
        os.environ["CPP_DESIGN_STATE_DIR"] = state          # decide() reads the arm's own state
        import design_route_prompt as drp
        import design_donegate_stop as stop
        drp.run({"session_id": first["session_id"] or "arm", "prompt": task})
        verdict = stop.decide({"session_id": first["session_id"] or "arm", "cwd": str(d),
                               "transcript_path": str(stream)})
        rec["stop_round"] = {"blocked": bool(verdict), "reason": (verdict or {}).get("reason", "")}
        if verdict and first["session_id"]:
            rec["calls"].append(call(claude_cmd("Stop hook feedback:\n" + verdict["reason"], None, first["session_id"],
                                                True), d, stream, env))
        from modules.cdio import design_route as dr
        if verdict and first["session_id"]:
            # judge() directly, not decide(): decide() is silent on a problem set it already blocked once, which would
            # read as "fixed" here.
            st = dr.scan_transcript(str(stream), dr.load_session(first["session_id"]))
            left = dr.judge(st, str(d), dr.load_routes())["problems"]
            rec["after_round"] = {"problems_left": [[p["check"], p.get("key", ""), os.path.basename(p["file"])]
                                                    for p in left]}
        rec["reviews"] = dr.read_rows("reviews.jsonl")
    rec["files"] = sorted(str(f.relative_to(d)).replace("\\", "/") for f in d.rglob("*")
                          if f.is_file() and ".claude" not in f.parts)
    return rec


def page_source(d: Path) -> str:
    """index.html plus every local stylesheet/script it links, so the judge sees what renders."""
    idx = d / "index.html"
    if not idx.is_file():
        return "(no index.html)"
    html = idx.read_text(encoding="utf-8", errors="replace")
    extra = []
    for ref in re.findall(r"""(?:href|src)\s*=\s*["']([^"':]+\.(?:css|js))["']""", html):
        p = d / ref
        if p.is_file():
            extra.append("/* %s */\n%s" % (ref, p.read_text(encoding="utf-8", errors="replace")))
    return html + ("\n" + "\n".join(extra) if extra else "")


def taste_counts(d: Path) -> dict:
    from modules.cdio import taste
    idx = d / "index.html"
    if not idx.is_file():
        return {"missing": True}
    rep = taste.lint(str(idx), site_root=str(d))
    fails = [v for v in rep.verdicts if v.status == "fail"]
    return {"critical": sum(1 for v in fails if v.severity == "critical"),
            "major": sum(1 for v in fails if v.severity == "major"),
            "minor": sum(1 for v in fails if v.severity == "minor"), "ids": [v.criterion for v in fails]}


def blind_judge(task_key: str, out: Path, seed: int) -> dict:
    srcs = {lab: page_source(out / task_key / lab) for lab in ("control", "treated")}
    order = ["control", "treated"]
    random.Random(seed).shuffle(order)
    votes = []
    for o in (order, order[::-1]):
        prompt = JUDGE.format(brief=TASKS[task_key], a=srcs[o[0]][:60000], b=srcs[o[1]][:60000])
        p = subprocess.run([*CLAUDE, "-p", prompt, "--setting-sources", "project", "--output-format", "json"],
                           cwd=tempfile.mkdtemp(prefix="dsr-judge-"), stdin=subprocess.DEVNULL, capture_output=True,
                           text=True, timeout=TIMEOUT)
        try:
            body = json.loads(p.stdout).get("result", "")
            v = json.loads(body[body.find("{"):body.rfind("}") + 1])
            w = {"A": o[0], "B": o[1]}.get(v.get("winner"), "tie")
            votes.append({"order": o, "winner": w, "slop_markers": {o[0]: v.get("slop_markers", {}).get("A"),
                                                                     o[1]: v.get("slop_markers", {}).get("B")},
                          "reasons": v.get("reasons", [])[:5]})
        except (ValueError, AttributeError):
            votes.append({"order": o, "winner": "unreadable", "raw": p.stdout[-300:]})
    ws = {v["winner"] for v in votes}
    return {"votes": votes, "consistent_winner": ws.pop() if len(ws) == 1 and votes[0]["winner"] in
            ("control", "treated") else "none"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="asc_design_gate_run")
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--tasks", nargs="+", default=sorted(TASKS), choices=sorted(TASKS))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    out = Path(a.out)
    if a.dry_run:
        for k in a.tasks:
            pol = policy_for(TASKS[k])
            print("== %s kinds=%s required=%s" % (k, pol["kinds"], pol["required"]))
            print(route_block(TASKS[k]))
            print(" ".join(claude_cmd("<task>", "<block>", None, True)[:3]), "...")
        return 0 if all(policy_for(TASKS[k])["review"] for k in a.tasks) else 2
    out.mkdir(parents=True, exist_ok=True)
    rec = {"claude": CLAUDE, "tasks": {}, "started": time.time()}
    for i, k in enumerate(a.tasks):
        t = {"task": TASKS[k], "control": run_arm(k, "control", out), "treated": run_arm(k, "treated", out)}
        t["taste"] = {lab: taste_counts(out / k / lab) for lab in ("control", "treated")}
        t["judge"] = blind_judge(k, out, seed=i)
        rec["tasks"][k] = t
        (out / "design_gate_run.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
    rec["summary"] = {k: {"taste": v["taste"], "winner": v["judge"]["consistent_winner"],
                          "treated_blocked": v["treated"].get("stop_round", {}).get("blocked"),
                          "treated_review_done": any(r.get("is_done") for r in v["treated"].get("reviews", []))}
                      for k, v in rec["tasks"].items()}
    (out / "design_gate_run.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(rec["summary"], indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
