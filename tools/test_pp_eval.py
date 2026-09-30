"""PP Self-Eval gates (V-EVAL-*). Spec: vault/specs/pp-self-eval.md.

Hermetic: every path lives in a temp dir via PP_EVAL_STATE / PP_EVAL_RUNS / PP_EVAL_VAULT,
git repos are synthetic, and the model is a fake `claude` script. No model calls.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PP))

TMP = Path(tempfile.mkdtemp(prefix="pp-eval-test-"))
os.environ["PP_EVAL_STATE"] = str(TMP / "state")
os.environ["PP_EVAL_RUNS"] = str(TMP / "runs")
os.environ["PP_EVAL_VAULT"] = str(TMP / "vault")

from modules.pp_eval import common, harvest  # noqa: E402

passes = fails = 0


def check(gate: str, cond: bool, detail: str = "") -> None:
    global passes, fails
    if cond:
        passes += 1
    else:
        fails += 1
    print(f"{'PASS' if cond else 'FAIL'} {gate} {detail}")


def sh(repo: Path, *args: str) -> str:
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@t")
    return subprocess.run([common.GIT, "-C", str(repo), *args], capture_output=True, text=True,
                          env=env, check=True).stdout


def commit(repo: Path, files: dict[str, str], msg: str) -> str:
    for rel, text in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    sh(repo, "add", "-A")
    sh(repo, "commit", "-q", "-m", msg)
    return sh(repo, "rev-parse", "HEAD").strip()


def make_repo() -> tuple[Path, dict]:
    repo = TMP / "src-repo"
    repo.mkdir()
    sh(repo, "init", "-q")
    ids = {}
    ids["base"] = commit(repo, {"calc.py": "def add(a, b):\n    return a - b\n"}, "initial calc")
    ids["real"] = commit(repo, {
        "calc.py": "def add(a, b):\n    return a + b\n",
        "test_calc.py": "import calc\nassert calc.add(2, 3) == 5, 'add is wrong'\nprint('ok')\n",
    }, "fix: add returns the sum")
    ids["noop"] = commit(repo, {
        "calc.py": "# calculator\ndef add(a, b):\n    return a + b\n",
        "test_noop.py": "print('always fine')\n",
    }, "fix: comment the calculator")
    ids["feat"] = commit(repo, {
        "calc.py": "# calculator\ndef add(a, b):\n    return a + b\n\ndef mul(a, b):\n    return a * b\n",
        "test_mul.py": "import calc\nassert calc.mul(2, 3) == 6\n",
    }, "feat: multiplication")
    return repo, ids


def s1_harvest() -> None:
    repo, ids = make_repo()
    cands = {c["fix"]: c for c in harvest.candidates(repo)}
    check("V-EVAL-HARVEST-FIX-SUBJECTS-ONLY", set(cands) == {ids["real"], ids["noop"]},
          f"got {len(cands)} candidates")
    res = harvest.harvest([repo], log=lambda *_: None)
    bank = harvest.load_bank()
    task_fixes = {t["fix"] for t in bank["tasks"].values()}
    check("V-EVAL-HARVEST-REAL-FIX-BANKED", ids["real"] in task_fixes, str(res))  # control
    reasons = [r["reason"] for r in bank["rejected"].values()]
    check("V-EVAL-HARVEST-PASSING-TEST-REJECTED", ids["noop"] not in task_fixes
          and any("already passes" in r for r in reasons), str(reasons))
    check("V-EVAL-BANK-IS-HIDDEN", harvest.bank_path().parent == Path(os.environ["PP_EVAL_STATE"])
          and not (repo / "bank.json").exists())
    leftovers = [p for p in Path(os.environ["PP_EVAL_RUNS"]).iterdir()]
    wts = sh(repo, "worktree", "list").strip().splitlines()
    check("V-EVAL-NO-WORKTREE-LEFT", not leftovers and len(wts) == 1, f"{leftovers} {wts}")
    again = harvest.harvest([repo], log=lambda *_: None)
    check("V-EVAL-HARVEST-IDEMPOTENT", again["added"] == 0 and again["rejected"] == 0, str(again))


def s1_drop_guard() -> None:
    try:
        common.drop_worktree(TMP, TMP / "elsewhere")
        refused = False
    except RuntimeError:
        refused = True
    check("V-EVAL-DROP-REFUSES-OUTSIDE-RUNS", refused)


FAKE = PP / "tools" / "fixtures" / "pp_eval_fake_claude.py"


def s2_runner() -> None:
    from modules.pp_eval import runner
    os.environ["PP_EVAL_CLAUDE_CMD"] = json.dumps([sys.executable, str(FAKE)])
    task = next(iter(harvest.load_bank()["tasks"].values()))

    a = " ".join(runner.build_cmd("hooks", "A", "p"))
    check("V-EVAL-ARM-FLAGS",
          "disableAllHooks" in " ".join(runner.build_cmd("hooks", "B", "p"))
          and "--disable-slash-commands" in runner.build_cmd("skills", "B", "p")
          and "claudeMdExcludes" in " ".join(runner.build_cmd("context", "B", "p"))
          and not any(x in a for x in ("disableAllHooks", "--disable-slash", "claudeMdExcludes")))

    def go(layer, arm, **env):
        for k in ("FAKE_MODE", "FAKE_IGNORE_ARMS", "FAKE_LEAK"):
            os.environ.pop(k, None)
        os.environ.update(env)
        return runner.one_run(task, layer, arm, 1, str(harvest.bank_path()))

    r = go("hooks", "A", FAKE_MODE="fix")
    check("V-EVAL-RUN-FIX-PASSES", r.get("status") == "VALID" and r.get("task_pass") is True,
          str({k: r.get(k) for k in ("status", "task_pass", "void_reasons", "grade_rcs")}))  # control
    r = go("hooks", "B", FAKE_MODE="nofix")
    check("V-EVAL-RUN-NOFIX-FAILS", r.get("status") == "VALID" and r.get("task_pass") is False,
          str(r.get("status")))
    r = go("hooks", "B", FAKE_MODE="fix", FAKE_IGNORE_ARMS="1")
    check("V-EVAL-HOOKS-CONTROL-VOIDS", r.get("status") == "VOID", str(r.get("void_reasons")))
    r = go("skills", "B", FAKE_MODE="fix", FAKE_IGNORE_ARMS="1")
    check("V-EVAL-SKILLS-CONTROL-VOIDS", r.get("status") == "VOID", str(r.get("void_reasons")))
    r = go("skills", "B", FAKE_MODE="fix")
    check("V-EVAL-SKILLS-ARM-B-VALID", r.get("status") == "VALID", str(r.get("void_reasons")))  # control
    r = go("hooks", "A", FAKE_MODE="quota")
    check("V-EVAL-QUOTA-DEFERS", r.get("status") == "DEFERRED_QUOTA", str(r.get("status")))
    r = go("hooks", "A", FAKE_MODE="leak", FAKE_LEAK=task["fix"])
    check("V-EVAL-BANK-ACCESS-VOIDS", r.get("status") == "VOID"
          and any("hidden bank" in x for x in r.get("void_reasons", [])), str(r.get("void_reasons")))
    left = list(Path(os.environ["PP_EVAL_RUNS"]).iterdir())
    check("V-EVAL-RUN-NO-WORKTREE-LEFT", not left, str(left))
    env = runner.child_env()
    check("V-EVAL-CHILD-ENV-MARKED", env.get("CLAUDEPP_EVAL_CHILD") == "1"
          and not any(k.startswith(("CLAUDECODE", "CLAUDE_CODE_")) for k in env))


def _row(task, layer, arm, rep, ok, fp="fp1", ctx=5000):
    return {"task": task, "layer": layer, "arm": arm, "rep": rep, "status": "VALID", "task_pass": ok,
            "fingerprint": fp, "wall_s": 10.0, "evidence": {"first_call_context": ctx, "total_context": ctx * 3}}


def s4_verdicts() -> None:
    from modules.pp_eval import verdict
    tasks = ["t1", "t2", "t3", "t4"]
    hard = [_row(t, "baseline", "A", 9, False, fp="b") for t in tasks]   # each task failed once somewhere
    both_pass = [_row(t, "hooks", arm, rep, True) for t in tasks for arm in "AB" for rep in (1, 2)]
    check("V-EVAL-VERDICT-NO-LOSS", verdict.judge(hard + both_pass, "hooks", "fp1")["verdict"] == "NO_LOSS")  # control
    v = verdict.judge(both_pass, "hooks", "fp1")
    check("V-EVAL-VERDICT-CEILING-INSUFFICIENT", v["verdict"] == "INSUFFICIENT" and "ceiling" in v["reason"], str(v.get("reason")))
    loss = [r for r in both_pass if not (r["task"] == "t1" and r["arm"] == "B")] + \
        [_row("t1", "hooks", "B", rep, False) for rep in (1, 2)]
    check("V-EVAL-VERDICT-LOSS", verdict.judge(hard + loss, "hooks", "fp1")["verdict"] == "LOSS")
    harm = [r for r in both_pass if not (r["task"] == "t2" and r["arm"] == "A")] + \
        [_row("t2", "hooks", "A", rep, False) for rep in (1, 2)]
    check("V-EVAL-VERDICT-HARM", verdict.judge(hard + harm, "hooks", "fp1")["verdict"] == "HARM")
    once = [r for r in both_pass if not (r["task"] == "t3" and r["arm"] == "B" and r["rep"] == 1)] + \
        [_row("t3", "hooks", "B", 1, False)]
    check("V-EVAL-VERDICT-SINGLE-REGRESSION-BLOCKS-NO-LOSS",
          verdict.judge(hard + once, "hooks", "fp1")["verdict"] == "INSUFFICIENT")
    ctx_same = [_row(t, "context", arm, rep, True) for t in tasks for arm in "AB" for rep in (1, 2)]
    v = verdict.judge(hard + ctx_same, "context", "fp1")
    check("V-EVAL-VERDICT-CONTEXT-CONTROL", v["verdict"] == "INSUFFICIENT" and "context control" in v["reason"], str(v.get("reason")))
    ctx_drop = [_row(t, "context", arm, rep, True, ctx=5000 if arm == "A" else 2000) for t in tasks for arm in "AB" for rep in (1, 2)]
    check("V-EVAL-VERDICT-CONTEXT-DROP-OK", verdict.judge(hard + ctx_drop, "context", "fp1")["verdict"] == "NO_LOSS")  # control
    check("V-EVAL-VERDICT-FINGERPRINT-ISOLATED", verdict.judge(hard + both_pass, "hooks", "fp2")["verdict"] == "INSUFFICIENT")

    from modules.pp_eval import nightly
    from modules.owner_queue import owner_queue
    oq = TMP / "oq"
    oq.mkdir(exist_ok=True)
    os.environ["PP_EVAL_OWNER_QUEUE_DIR"] = str(oq)
    nightly._finalise("hooks", "fp1", hard + both_pass, {})
    nightly._finalise("skills", "fp1", [dict(r, layer="skills") for r in hard + loss], {})
    ids = [r["id"] for r in owner_queue.load(str(oq))]
    check("V-EVAL-PROPOSAL-QUEUED-ONLY-WHEN-ACTIONABLE", ids == ["pp-eval-hooks-fp1"], str(ids))


def s3_nightly(repo: Path) -> None:
    import time
    from modules.pp_eval import common, nightly
    home = TMP / "home"
    for rel, text in {".claude/rules/r.md": "rule", ".claude/CLAUDE.md": "c", ".claude/hooks/h.js": "h",
                      ".claude/skills/x/SKILL.md": "s", ".claude/settings.json": "{}"}.items():
        (home / rel).parent.mkdir(parents=True, exist_ok=True)
        (home / rel).write_text(text, encoding="utf-8")
    (home / ".claude/projects/p").mkdir(parents=True)
    os.environ.update(PP_EVAL_HOME=str(home), PP_EVAL_PROJECTS=str(home / ".claude/projects"),
                      PP_EVAL_FREE_RAM_GB="16", FAKE_MODE="fix")
    for k in ("FAKE_IGNORE_ARMS", "FAKE_LEAK", "FAKE_UTIL"):
        os.environ.pop(k, None)
    state = Path(os.environ["PP_EVAL_STATE"])
    for name in ("runs.jsonl", "nights.jsonl", "evaluated.json", "verdicts.json", "quota.json"):
        (state / name).unlink(missing_ok=True)
    (state / "config.json").write_text(json.dumps({"repos": [str(repo)], "bank_target": 0}), encoding="utf-8")

    before = {l: nightly.fingerprint(l) for l in ("context", "hooks")}
    (home / ".claude/rules/r.md").write_text("rule v2", encoding="utf-8")
    check("V-EVAL-FP-CHANGES-ON-EDIT", nightly.fingerprint("context") != before["context"]
          and nightly.fingerprint("hooks") == before["hooks"])

    now = time.time()
    nightly._save("quota.json", {"windows": {"seven_day": {"utilization": 0.93, "resetsAt": now + 3600}}})
    n = nightly.run_night(now=now, weekday=0, log=lambda *_: None)
    check("V-EVAL-QUOTA-CEILING-SKIPS", n["outcome"].startswith("SKIPPED: quota"), n["outcome"])
    nightly._save("quota.json", {"windows": {"seven_day": {"utilization": 0.93, "resetsAt": now - 60}}})

    t = home / ".claude/projects/p/live.jsonl"
    t.write_text("{}", encoding="utf-8")
    n = nightly.run_night(now=time.time(), weekday=0, log=lambda *_: None)
    check("V-EVAL-OWNER-ACTIVE-SKIPS", "session transcript changed" in n["outcome"], n["outcome"])
    os.utime(t, (now - 7200, now - 7200))

    os.environ["PP_EVAL_FREE_RAM_GB"] = "2"
    n = nightly.run_night(weekday=0, log=lambda *_: None)
    check("V-EVAL-RAM-SKIPS", "free RAM" in n["outcome"], n["outcome"])
    os.environ["PP_EVAL_FREE_RAM_GB"] = "16"

    held = common.Lock(state / "night.lock")
    held.acquire()
    n = nightly.run_night(weekday=0, log=lambda *_: None)
    held.release()
    check("V-EVAL-LOCK-REFUSES-SECOND", "lock" in n["outcome"], n["outcome"])

    n = nightly.run_night(weekday=0, log=lambda *_: None)
    rows = nightly._read_jsonl("runs.jsonl")
    check("V-EVAL-NIGHT-RUNS-AND-LEDGERS", n["outcome"] == "RAN" and n.get("runs") == 4 and len(rows) == 4
          and all(r.get("fingerprint") and r["layer"] == "context" for r in rows)
          and (state / "REPORT.md").exists(), json.dumps({k: n.get(k) for k in ("outcome", "runs", "layer", "stopped")}))  # control
    n = nightly.run_night(weekday=0, log=lambda *_: None)
    ev = nightly._load("evaluated.json", {})
    check("V-EVAL-EXHAUSTED-LAYER-FINALISED", n["outcome"].startswith("NOTHING") and "context" in ev, n["outcome"])

    os.environ["FAKE_UTIL"] = "0.95"
    n = nightly.run_night(weekday=0, log=lambda *_: None)
    check("V-EVAL-QUOTA-STOPS-NIGHT", n.get("runs") == 1 and "quota" in (n.get("stopped") or ""),
          json.dumps({k: n.get(k) for k in ("runs", "stopped", "layer")}))
    n = nightly.run_night(weekday=0, log=lambda *_: None)
    check("V-EVAL-QUOTA-READING-BLOCKS-NEXT", n["outcome"].startswith("SKIPPED: quota"), n["outcome"])
    os.environ.pop("FAKE_UTIL")
    nightly._save("quota.json", {})

    n = nightly.run_night(weekday=6, dry_run=True, log=lambda *_: None)
    check("V-EVAL-BASELINE-ON-SUNDAY", n.get("kind") == "baseline", str(n.get("kind")))
    nights = nightly._read_jsonl("nights.jsonl")
    check("V-EVAL-EVERY-NIGHT-RECORDED", len(nights) == 9, f"{len(nights)} rows")


def main() -> int:
    try:
        s1_harvest()
        s1_drop_guard()
        s2_runner()
        s4_verdicts()
        s3_nightly(TMP / "src-repo")
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    total = passes + fails
    print(f"PP_EVAL_PASS={passes}/{total}")
    return 0 if fails == 0 and total > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
