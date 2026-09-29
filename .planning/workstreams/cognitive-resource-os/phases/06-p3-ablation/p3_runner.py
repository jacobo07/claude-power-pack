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
import re
import shutil
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
    drop_tree(wt)  # a run killed mid-`worktree add` leaves it registered AND locked
    git("worktree", "prune", check=False)
    git("worktree", "add", "--detach", str(wt), base)
    return wt


def drop_tree(wt: Path):
    # Twice --force: git refuses a LOCKED worktree with one (measured: an interrupted add left one locked).
    git("worktree", "remove", "--force", "--force", str(wt), check=False)


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
    # Every suite here ends with a `<NAME>_PASS=n/m` line; its n is the count of gates that ran and passed.
    # Counting lines that start with "PASS" read 0 on 7 of 8 suites whose lines are shaped differently.
    m = re.findall(r"\b[A-Z0-9_]+_PASS=(\d+)/(\d+)", out)
    passes = int(m[-1][0]) if m else 0
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
        sid = session(wt, PROMPT.format(test=t["test"]), arm, rec)
        judge(rec, grade(wt, t, base), sid)
        return rec
    finally:
        rec["ended"] = dt.datetime.now(dt.timezone.utc).isoformat()
        drop_tree(wt)


def session(wt: Path, prompt: str, arm: str, rec: dict) -> str:
    """One headless session in `wt`; records rc/wall/turns on rec and returns the session id."""
    cmd = [CLAUDE, "-p", prompt, "--model", MODEL, "--output-format", "json",
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
    return sid


def judge(rec: dict, g: dict, sid: str):
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


# ---- judgement tasks (ADDENDUM-J.md): no pre-existing test; the grader stays outside the worktree ----
JDIR = HERE / "judgement"
JRESULTS = HERE / "results-j.jsonl"
JPROMPT = ("In this repository, `{module}` contains functions whose body is only `...`. Implement them. "
           "The module docstring says who calls them and what the results are used for. Keep the "
           "signatures. Stop when done.")


def jtasks() -> list:
    import importlib.util
    out = []
    sys.path.insert(0, str(JDIR))
    for f in sorted(JDIR.glob("task_*.py")):
        spec = importlib.util.spec_from_file_location(f.stem, f)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        out.append({"id": "J-" + f.stem[5:], "file": f, "module": m.MODULE, "stub": m.STUB})
    return out


def jbase() -> str:
    """A commit that does NOT contain the judgement bank, so no grader or reference sits in the worktree."""
    b = (JDIR / "BASE").read_text(encoding="utf-8").strip()
    if git("ls-tree", "-r", "--name-only", b, "--", ".planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/judgement"):
        raise SystemExit(f"judgement BASE {b} contains the bank: graders would be visible to the agent")
    return b


def jgrade(wt: Path, t: dict) -> dict:
    shutil.copyfile(JDIR / "_p3j_common.py", wt / "_p3j_common.py")
    shutil.copyfile(t["file"], wt / "_p3j_task.py")
    r = subprocess.run([PY, "_p3j_task.py", "grade", t["module"]], cwd=wt, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=300)
    out = r.stdout + r.stderr
    m = re.findall(r"\bP3J_PASS=(\d+)/(\d+)", out)
    fails = [ln[5:60] for ln in out.splitlines() if ln.startswith("FAIL ")]
    return {"rc": r.returncode, "pass_lines": int(m[-1][0]) if m else 0,
            "summary": (m and f"P3J_PASS={m[-1][0]}/{m[-1][1]}" or "no P3J line") + (f" fails={fails}" if fails else "")}


def jprepare(wt: Path, t: dict):
    p = wt / t["module"]
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(t["stub"], encoding="utf-8")


def one_run_j(t: dict, arm: str, rep: int, base: str) -> dict:
    run_id = f"{t['id']}-{arm}-r{rep}"
    rec = {"run_id": run_id, "task": t["id"], "arm": arm, "rep": rep, "base": base,
           "started": dt.datetime.now(dt.timezone.utc).isoformat()}
    wt = fresh_tree(run_id, base)
    try:
        jprepare(wt, t)
        pre = jgrade(wt, t)
        rec["precondition_rc"] = pre["rc"]
        if pre["rc"] == 0:
            rec["valid"], rec["invalid_reason"] = False, "stub already passes its grader"
            return rec
        for f in ("_p3j_common.py", "_p3j_task.py"):  # the precondition grade copied them in
            (wt / f).unlink()
        sid = session(wt, JPROMPT.format(module=t["module"]), arm, rec)
        judge(rec, jgrade(wt, t), sid)
        return rec
    finally:
        rec["ended"] = dt.datetime.now(dt.timezone.utc).isoformat()
        drop_tree(wt)


def cmd_validate_j() -> int:
    base = jbase()
    bad = 0
    for t in jtasks():
        st = subprocess.run([PY, str(t["file"]), "selftest"], capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
        wt = fresh_tree(f"validate-{t['id']}", base)
        try:
            bank = {f.name for f in JDIR.iterdir()}  # exact bank file names, checked before the grade copies any in
            leak = sorted(str(p.relative_to(wt)) for p in wt.rglob("*") if p.name in bank)
            jprepare(wt, t)
            g = jgrade(wt, t)
        finally:
            drop_tree(wt)
        ok = st.returncode == 0 and g["rc"] != 0 and "P3J_PASS=" in g["summary"] and not leak
        bad += not ok
        print(f"{'OK ' if ok else 'BAD'} {t['id']}: selftest_rc={st.returncode} stub_in_tree={g['summary']} "
              f"bank_in_tree={leak or 'none'}", flush=True)
    n = len(jtasks())
    print(f"VALIDATE-J {n - bad}/{n} base={base[:10]}")
    return 1 if bad else 0


def done_ids(results: Path = RESULTS) -> set:
    if not results.exists():
        return set()
    out = set()
    for ln in results.read_text(encoding="utf-8").splitlines():
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


def cmd_run(reps: int, judgement: bool = False, only: str = "", prime: bool = False) -> int:
    """prime: B-prime -- ONE arm "P" = the prefix as it now is (moved rule absent, its skill loadable),
    no claudeMdExcludes, results in their own file. `only` filters task ids by substring."""
    tasks, results, runner = (jtasks(), JRESULTS, one_run_j) if judgement else (TASKS, RESULTS, one_run)
    if prime:
        results = HERE / f"results-jprime-{only or 'all'}.jsonl"
    tasks = [t for t in tasks if only in t["id"]]
    if not tasks:
        raise SystemExit(f"no task id contains {only!r}")
    base = jbase() if judgement else base_commit()
    RUNS.mkdir(parents=True, exist_ok=True)
    done = done_ids(results)
    attempts: dict = {}
    for rep in range(1, reps + 1):
        for i, t in enumerate(tasks):
            order = ("P",) if prime else ("A", "B") if (i + rep) % 2 == 0 else ("B", "A")
            for arm in order:
                rid = f"{t['id']}-{arm}-r{rep}"
                while rid not in done and attempts.get(rid, 0) < 3:  # 1 run + max 2 replacements
                    attempts[rid] = attempts.get(rid, 0) + 1
                    rec = runner(t, arm, rep, base)
                    rec["attempt"] = attempts[rid]
                    with results.open("a", encoding="utf-8") as fh:
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
    if a[:1] == ["validate-j"]:
        raise SystemExit(cmd_validate_j())
    if a[:1] == ["run-j"]:
        raise SystemExit(cmd_run(int(a[a.index("--reps") + 1]) if "--reps" in a else 2, judgement=True))
    if a[:1] == ["run-jprime"]:  # run-jprime --only ibc [--reps 2]
        raise SystemExit(cmd_run(int(a[a.index("--reps") + 1]) if "--reps" in a else 2, judgement=True,
                                 only=a[a.index("--only") + 1] if "--only" in a else "", prime=True))
    raise SystemExit(__doc__)
