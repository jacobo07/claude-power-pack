"""Fresh-agent inheritance run (campaign 1): ONE `claude -p` pair, treated vs control.

Both agents get the SAME task prompt (it never names the rule under test). The treated agent additionally receives the
family block exactly as modules.gsd_x.cli.family_block renders it for that prompt from the CANDIDATE root (the current
baseline + the promotable deltas); the control receives nothing. Both run from a fresh directory with
--setting-sources project (the repo CLAUDE.md is the institutional context; user hooks that point at the live tree are
NOT loaded, so the live hook delivery is not exercised here -- that plane is recorded as a residual).

Phase 5 (default): deltas/output under vault/programs/ascension/bcap-1/phase5, the harbour-newsletter task.
B7 (Taste): `--deltas vault/programs/ascension/bcap-1/b7/deltas.json --out vault/programs/ascension/bcap-1/b7 --task saas`.
`--dry-run` builds the candidate and the block and prints them; it never calls a model.

Output: <out>/inherit/{control,treated}/ + <out>/inheritance_run.json (tokens, tool calls).
Run ONCE per pair; the evidence builders and tests read the recorded artifact, they never re-call the model.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "vault/programs/ascension/bcap-1/phase5"
DELTAS = OUT / "deltas.json"
CLAUDE = os.environ.get("CPP_CLAUDE_EXE") or os.path.expanduser("~/.local/claude-lf1/node_modules/.bin/claude")
TASKS = {
    "harbour": ("Build a small landing page for a harbour newsletter that sends a monthly tide-table digest. "
                "Static HTML and CSS only, no frameworks, no build step. One page, one signup button, "
                "plain and quiet. Write the files in the current directory, then reply with one line listing the files."),
    # B7: a brief that invites the anti-slop defaults (hero, social proof, testimonials, pricing) without naming any
    # ban, so a control that ships them and a treated agent that avoids them are both reachable outcomes.
    "saas": ("Build the marketing landing page for a small SaaS product that turns meeting recordings into action "
             "items. Hero with a headline and a call to action, a short features section, two customer testimonials, "
             "and a pricing section with two plans. Static HTML and CSS only (plain JS allowed), no frameworks, no "
             "build step, entry file index.html. Write the files in the current directory, then reply with one line "
             "listing the files."),
}
TASK = TASKS["harbour"]


def candidate_root(deltas: Path | str = DELTAS) -> str:
    from modules.backlog_autopilot import promotion as P
    from modules.tower import baselines as bl, ratchet as rt
    root = tempfile.mkdtemp(prefix="asc-cand-")
    shutil.copytree(ROOT / "vault/tower/baselines/web_surface", Path(root) / "web_surface")
    ds = [d for d in P.load_deltas(str(deltas))
          if P.classify(d, bl.active_entries("web_surface", root)).promotable and not P.check_problem(d)]
    if not ds:          # every delta already active (phase 5 after B5 landed): the candidate IS the baseline
        return root
    rt.promote("web_surface", [{"id": d.id, "requirement": d.requirement, "why": d.why, "origin": d.origin,
                                "class": "C", "check": d.check} for d in ds],
               "candidate for inheritance run", "asc-inherit", root)
    return root


def run(label: str, system: str | None, out: Path = OUT, task: str = TASK) -> dict:
    d = out / "inherit" / label
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    cmd = [CLAUDE, "-p", task, "--setting-sources", "project", "--permission-mode", "acceptEdits",
           "--allowedTools", "Write", "Edit", "Read", "--output-format", "stream-json", "--verbose"]
    if system:
        cmd += ["--append-system-prompt", system]
    import model_spend_gate
    model_spend_gate.require("asc_inherit_run")   # BAMR obligation 5: refused -> the run aborts, nothing spawned
    t0 = time.time()
    p = subprocess.run(cmd, cwd=d, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=900)
    calls, usage, result = [], {}, ""
    for line in p.stdout.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("type") == "assistant":
            for c in ev["message"].get("content", []):
                if c.get("type") == "tool_use":
                    calls.append({"tool": c["name"], "input": {k: str(v)[:120] for k, v in c["input"].items() if k != "content"}})
        if ev.get("type") == "result":
            usage = ev.get("usage", {})
            result = str(ev.get("result", ""))[:300]
    (out / "inherit" / ("%s.stream.jsonl" % label)).write_text(p.stdout, encoding="utf-8")
    files = sorted(str(f.relative_to(d)).replace("\\", "/") for f in d.rglob("*") if f.is_file())
    return {"label": label, "rc": p.returncode, "seconds": round(time.time() - t0, 1), "files": files,
            "tool_calls": calls, "usage": usage, "result": result, "stderr_tail": p.stderr[-300:]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="asc_inherit_run")
    ap.add_argument("--deltas", default=str(DELTAS))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--task", default="harbour", choices=sorted(TASKS))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    out, task = Path(a.out), TASKS[a.task]
    from modules.gsd_x import cli
    from modules.tower import baselines as bl
    cand = candidate_root(a.deltas)
    os.environ["CPP_TOWER_STATE_DIR"] = tempfile.mkdtemp(prefix="asc-state-")
    block = cli.family_block(task, {"session_id": "asc-inherit-%s" % a.task}, root=cand)
    n = bl.generations("web_surface", cand)[-1]
    if n == bl.generations("web_surface")[-1]:
        print("no promotable delta in %s: the candidate equals the live baseline B%d; a pair would test nothing"
              % (a.deltas, n), file=sys.stderr)
        return 3
    rec = {"task": task, "task_key": a.task, "deltas": os.path.relpath(a.deltas, ROOT).replace("\\", "/"),
           "candidate_generation": "web_surface/B%d" % n,
           "candidate_sha256": bl.generation_sha256("web_surface", n, cand), "block_chars": len(block),
           "block_head": block[:300], "runs": {}}
    if not block:
        print("no family block delivered; refusing to run", file=sys.stderr)
        return 2
    if a.dry_run:
        print(json.dumps({k: rec[k] for k in ("candidate_generation", "candidate_sha256", "block_chars", "deltas")}))
        print(block)
        return 0
    (out / "inherit").mkdir(parents=True, exist_ok=True)
    rec["runs"]["control"] = run("control", None, out, task)
    rec["runs"]["treated"] = run("treated", block, out, task)
    (out / "inheritance_run.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    print(json.dumps({k: {"rc": v["rc"], "files": v["files"], "usage": v["usage"]} for k, v in rec["runs"].items()}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
