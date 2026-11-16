"""Phase 5 inheritance run (campaign 1): ONE `claude -p` pair, treated vs control.

Both agents get the SAME task prompt (it never mentions legal pages). The treated agent additionally receives the
family block exactly as modules.gsd_x.cli.family_block renders it for that prompt from the CANDIDATE B5 root; the
control receives nothing. Both run from a fresh directory inside the worktree with --setting-sources project (the
repo CLAUDE.md is the institutional context; user hooks that point at the live tree are NOT loaded, so the live
hook delivery is not exercised here -- that plane is recorded as a residual).

Output: vault/programs/ascension/bcap-1/phase5/inherit/{control,treated}/ + inheritance_run.json (tokens, tool calls).
Run ONCE; tools/test_asc_baseline.py verifies the recorded artifact, it never re-calls the model.
"""
from __future__ import annotations

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
CLAUDE = os.path.expanduser("~/.local/claude-lf1/node_modules/.bin/claude")
TASK = ("Build a small landing page for a harbour newsletter that sends a monthly tide-table digest. "
        "Static HTML and CSS only, no frameworks, no build step. One page, one signup button, "
        "plain and quiet. Write the files in the current directory, then reply with one line listing the files.")


def candidate_root() -> str:
    from modules.backlog_autopilot import promotion as P
    from modules.tower import baselines as bl, ratchet as rt
    root = tempfile.mkdtemp(prefix="asc-cand-")
    shutil.copytree(ROOT / "vault/tower/baselines/web_surface", Path(root) / "web_surface")
    ds = [d for d in P.load_deltas(str(OUT / "deltas.json"))
          if P.classify(d, bl.active_entries("web_surface", root)).promotable and not P.check_problem(d)]
    rt.promote("web_surface", [{"id": d.id, "requirement": d.requirement, "why": d.why, "origin": d.origin,
                                "class": "C", "check": d.check} for d in ds],
               "candidate for inheritance run", "asc-p5", root)
    return root


def run(label: str, system: str | None) -> dict:
    d = OUT / "inherit" / label
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    cmd = [CLAUDE, "-p", TASK, "--setting-sources", "project", "--permission-mode", "acceptEdits",
           "--allowedTools", "Write", "Edit", "Read", "--output-format", "stream-json", "--verbose"]
    if system:
        cmd += ["--append-system-prompt", system]
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
    (OUT / "inherit" / ("%s.stream.jsonl" % label)).write_text(p.stdout, encoding="utf-8")
    files = sorted(str(f.relative_to(d)) for f in d.rglob("*") if f.is_file())
    return {"label": label, "rc": p.returncode, "seconds": round(time.time() - t0, 1), "files": files,
            "tool_calls": calls, "usage": usage, "result": result, "stderr_tail": p.stderr[-300:]}


def main() -> int:
    from modules.gsd_x import cli
    from modules.tower import baselines as bl
    cand = candidate_root()
    os.environ["CPP_TOWER_STATE_DIR"] = tempfile.mkdtemp(prefix="asc-state-")
    block = cli.family_block(TASK, {"session_id": "asc-p5-inherit"}, root=cand)
    n = bl.generations("web_surface", cand)[-1]
    rec = {"task": TASK, "candidate_generation": "web_surface/B%d" % n,
           "candidate_sha256": bl.generation_sha256("web_surface", n, cand), "block_chars": len(block),
           "block_head": block[:300], "runs": {}}
    if not block:
        print("no family block delivered; refusing to run", file=sys.stderr)
        return 2
    (OUT / "inherit").mkdir(parents=True, exist_ok=True)
    rec["runs"]["control"] = run("control", None)
    rec["runs"]["treated"] = run("treated", block)
    (OUT / "inheritance_run.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    print(json.dumps({k: {"rc": v["rc"], "files": v["files"], "usage": v["usage"]} for k, v in rec["runs"].items()}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
