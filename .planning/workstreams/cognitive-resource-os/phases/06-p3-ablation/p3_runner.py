#!/usr/bin/env python
"""P3 instruction ablation runner (cognitive-resource-os, protocol in
vault/plans/cognitive-resource-os-P3-ablation-protocol.md + ADDENDUM.md beside this file).

    python p3_runner.py validate          # no model calls: each mutant must turn its test red
    python p3_runner.py run [--reps 2]    # counted runs, resumable (skips run ids already valid in results)

One run = a fresh detached worktree at the frozen BASE commit, the task's mutant applied, one
`claude -p` session told to make the test pass, then the ORIGINAL test file restored from BASE and
run as the grade. Arm A = current prefix. Arm B = same, plus --settings claudeMdExcludes naming the
three R1 rule files. Arms alternate per task so host drift lands on both.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
TASKS = json.loads((HERE / "p3-tasks.json").read_text(encoding="utf-8"))["tasks"]
RESULTS = HERE / "results.jsonl"
RUNS = Path(r"C:\Users\User\Apps\p3-runs")
GIT = r"C:\Program Files\Git\cmd\git.exe"
PY = sys.executable
CLAUDE = r"C:\Users\User\.local\bin\claude.exe"
MODEL = "claude-opus-5-5"
RULES = Path.home() / ".claude" / "rules"
R1 = [str(RULES / n).replace("\\", "/") for n in (
    "instrument-before-claim.md", "destructive-state-authorization.md", "real-context-reachability.md")]
PROMPT = ("The test `python {test}` fails. Find the defect in the source it exercises and fix it. "
          "Do not edit the test file. Run the test to confirm it passes, then stop.")

sys.path.insert(0, str(REPO / "tools"))
import tis_observed as tob  # noqa: E402


def git(*a, cwd=REPO, check=True):
    r = subprocess.run([GIT, *a], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(a)} -> {r.returncode}: {r.stderr.strip()}")
    return r.stdout.strip()


def base_commit() -> str:
    """BASE = the last commit touching p3-tasks.json, never a moving HEAD."""
    b = git("log", "-1", "--format=%H", "--", str(HERE / "p3-tasks.json"))
    if not b:
        raise SystemExit("p3-tasks.json is not committed: freeze it before any run")
    return b


def fresh_tree(run_id: str, base: str) -> Path:
    wt = RUNS / run_id
    if wt.exists():
        git("worktree", "remove", "--force", str(wt), check=False)
    git("worktree", "add", "--detach", str(wt), base)
    return wt


def drop_tree(wt: Path):
    git("worktree", "remove", "--force", str(wt), check=False)


def apply_mutant(wt: Path, t: dict):
    f = wt / t["file"]
    src = f.read_bytes().decode("utf-8")
    nl = "\r\n" if "\r\n" in src else "\n"
    old, new = t["old"].replace("\n", nl), t["new"].replace("\n", nl)
    if src.count(old) != 1:
        raise RuntimeError(f"{t['id']}: anchor matches {src.count(old)} times")
    f.write_bytes(src.replace(old, new).encode("utf-8"))


def grade(wt: Path, t: dict, base: str) -> dict:
    git("checkout", base, "--", t["test"], cwd=wt)  # the grade is the frozen test, whatever the agent did
    r = subprocess.run([PY, t["test"]], cwd=wt, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=900)
    out = r.stdout + r.stderr
    passes = sum(1 for ln in out.splitlines() if ln.lstrip().startswith("PASS"))
    tail = [ln for ln in out.splitlines() if ln.strip()][-1:] or [""]
    return {"rc": r.returncode, "pass_lines": passes, "summary": tail[0][:200]}


def child_env() -> dict:
    return {k: v for k, v in os.environ.items()
            if not (k.startswith("CLAUDECODE") or k.startswith("CLAUDE_CODE_"))}


def transcript(session_id: str) -> Path | None:
    hits = list((Path.home() / ".claude" / "projects").glob(f"*/{session_id}.jsonl"))
    return hits[0] if hits else None


def metrics(session_id: str) -> dict:
    p = transcript(session_id) if session_id else None
    if not p:
        return {"state": "UNMEASURED", "reason": "no transcript"}
    calls, usage_lines, synthetic, bad = tob._calls_in(p)
    if not calls:
        return {"state": "UNMEASURED", "reason": "no calls", "transcript": str(p)}

    def ctx(u):
        return (u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0)
                + u.get("cache_creation_input_tokens", 0))

    return {"state": "MEASURED", "transcript": str(p), "entrypoint": calls[0].get("entrypoint"),
            "calls": len(calls), "first_call_context": ctx(calls[0]["usage"]),
            "total_context": sum(ctx(c["usage"]) for c in calls),
            "output_tokens": sum(c["usage"].get("output_tokens", 0) for c in calls),
            "models": sorted({c["model"] for c in calls})}


def one_run(t: dict, arm: str, rep: int, base: str) -> dict:
    run_id = f"{t['id']}-{arm}-r{rep}"
    rec = {"run_id": run_id, "task": t["id"], "arm": arm, "rep": rep, "base": base,
           "started": dt.datetime.now(dt.timezone.utc).isoformat()}
    wt = fresh_tree(run_id, base)
    try:
        apply_mutant(wt, t)
        pre = grade(wt, t, base)
        rec["precondition_rc"] = pre["rc"]
        if pre["rc"] == 0:
            rec["valid"], rec["invalid_reason"] = False, "mutant did not turn the test red"
            return rec
        cmd = [CLAUDE, "-p", PROMPT.format(test=t["test"]), "--model", MODEL, "--output-format", "json",
               "--max-turns", "40", "--permission-mode", "acceptEdits",
               "--allowedTools", "Read,Edit,Write,Grep,Glob,Bash,PowerShell"]
        if arm == "B":
            cmd += ["--settings", json.dumps({"claudeMdExcludes": R1})]
        t0 = time.time()
        try:
            r = subprocess.run(cmd, cwd=wt, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=1500, env=child_env())
            rec["claude_rc"], raw = r.returncode, r.stdout
        except subprocess.TimeoutExpired:
            rec["claude_rc"], raw = "timeout", ""
        rec["wall_s"] = round(time.time() - t0, 1)
        sid = ""
        try:
            j = json.loads(raw.strip().splitlines()[-1]) if raw.strip() else {}
            sid = j.get("session_id", "")
            rec["num_turns"], rec["is_error"] = j.get("num_turns"), j.get("is_error")
        except (json.JSONDecodeError, IndexError):
            rec["stdout_tail"] = raw[-300:]
        rec["session_id"] = sid
        g = grade(wt, t, base)
        rec.update(grade_rc=g["rc"], grade_pass_lines=g["pass_lines"], grade_summary=g["summary"],
                   task_pass=(g["rc"] == 0))
        rec["metrics"] = metrics(sid)
        reasons = []
        if rec["metrics"].get("state") != "MEASURED":
            reasons.append("transcript UNMEASURED")
        elif rec["metrics"].get("entrypoint") != "sdk-cli":
            reasons.append(f"entrypoint {rec['metrics'].get('entrypoint')}")
        if g["pass_lines"] == 0 and g["rc"] == 0:
            reasons.append("gate printed no PASS line")
        rec["valid"] = not reasons
        if reasons:
            rec["invalid_reason"] = "; ".join(reasons)
        return rec
    finally:
        rec["ended"] = dt.datetime.now(dt.timezone.utc).isoformat()
        drop_tree(wt)


def done_ids() -> set:
    if not RESULTS.exists():
        return set()
    out = set()
    for ln in RESULTS.read_text(encoding="utf-8").splitlines():
        if ln.strip():
            r = json.loads(ln)
            if r.get("valid"):
                out.add(r["run_id"])
    return out


def cmd_validate() -> int:
    base = base_commit()
    bad = 0
    for t in TASKS:
        wt = fresh_tree(f"validate-{t['id']}", base)
        try:
            clean = grade(wt, t, base)
            apply_mutant(wt, t)
            mut = grade(wt, t, base)
            ok = clean["rc"] == 0 and clean["pass_lines"] > 0 and mut["rc"] != 0
            bad += not ok
            print(f"{'OK ' if ok else 'BAD'} {t['id']}: clean_rc={clean['rc']} clean_pass={clean['pass_lines']} "
                  f"mutant_rc={mut['rc']} | {mut['summary'][:90]}", flush=True)
        finally:
            drop_tree(wt)
    print(f"VALIDATE {len(TASKS) - bad}/{len(TASKS)} base={base[:10]}")
    return 1 if bad else 0


def cmd_run(reps: int) -> int:
    base = base_commit()
    RUNS.mkdir(parents=True, exist_ok=True)
    done = done_ids()
    attempts: dict = {}
    for rep in range(1, reps + 1):
        for i, t in enumerate(TASKS):
            order = ("A", "B") if (i + rep) % 2 == 0 else ("B", "A")
            for arm in order:
                rid = f"{t['id']}-{arm}-r{rep}"
                while rid not in done and attempts.get(rid, 0) < 3:  # 1 run + max 2 replacements
                    attempts[rid] = attempts.get(rid, 0) + 1
                    rec = one_run(t, arm, rep, base)
                    rec["attempt"] = attempts[rid]
                    with RESULTS.open("a", encoding="utf-8") as fh:
                        fh.write(json.dumps(rec) + "\n")
                    print(f"{rid} attempt={rec['attempt']} valid={rec.get('valid')} pass={rec.get('task_pass')} "
                          f"first_ctx={rec.get('metrics', {}).get('first_call_context')} "
                          f"{rec.get('invalid_reason', '')}", flush=True)
                    if rec.get("valid"):
                        done.add(rid)
                if rid not in done:
                    print(f"STOP: {rid} invalid 3 times -- instrument unreliable (protocol)", flush=True)
                    return 2
    print("RUN COMPLETE", flush=True)
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["validate"]:
        raise SystemExit(cmd_validate())
    if a[:1] == ["run"]:
        raise SystemExit(cmd_run(int(a[a.index("--reps") + 1]) if "--reps" in a else 2))
    raise SystemExit(__doc__)
