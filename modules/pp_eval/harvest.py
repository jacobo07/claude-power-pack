"""Task harvester (spec §3.1): mine real bug-fix commits into a hidden, validated bank.

A candidate is a non-merge commit whose subject reads as a fix and whose diff touches at
least one source file AND at least one test file. It becomes a task only if, in a fresh
worktree, the fix's test files FAIL at the parent and PASS at the fix, twice. That check is
what rejects the common false positives: a test that already passed before the fix, a
flaky test, and a test that reads the LIVE install through an absolute path instead of the
tree it sits in (it passes at the parent because the live code is already fixed).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from .common import add_worktree, drop_worktree, git, run, state_dir, utc_now

FIX_SUBJECT = re.compile(r"^(fix|bugfix|hotfix)\b|\b(fix(es|ed)?|bug|repair|regression|broken|crash)\b", re.I)
TEST_PATH = re.compile(r"(^|/)(test_[^/]+\.py|[^/]+_test\.py|tests?/[^/]+\.(py|js|mjs|ts)|[^/]+\.test\.(js|mjs|ts))$")
SOURCE_EXT = {".py", ".js", ".mjs", ".ts", ".ex", ".exs", ".go", ".rs", ".java", ".ps1"}
TEST_TIMEOUT_S = 120


def is_test(path: str) -> bool:
    return bool(TEST_PATH.search(path))


def test_command(path: str, text: str) -> list[str] | None:
    """How to run one test file, or None when the harvester cannot run it."""
    if path.endswith(".py"):
        pytest_style = re.search(r"^def test_\w+\(", text, re.M) and "__main__" not in text
        return [sys.executable, "-m", "pytest", "-q", path] if pytest_style else [sys.executable, path]
    if path.endswith((".js", ".mjs")):
        return ["node", path]
    return None


def candidates(repo: Path, limit: int = 1500) -> list[dict]:
    """Fix-shaped commits with source + test changes (no validation yet)."""
    # One git process for the whole history: a diff-tree per commit measured ~1.5 s each on
    # this host (346 fix-shaped commits = ~9 min before any validation started).
    out = []
    log = git(repo, "log", "--no-merges", f"-n{limit}", "--format=%x1e%H%x09%P%x09%s",
              "--name-status", timeout=600)
    for record in log.split("\x1e"):
        lines = [ln for ln in record.splitlines() if ln.strip()]
        if not lines:
            continue
        parts = lines[0].split("\t", 2)
        if len(parts) < 3 or " " in parts[1] or not parts[1]:
            continue
        sha, parent, subject = parts
        if not FIX_SUBJECT.search(subject):
            continue
        names = lines[1:]
        tests, sources = [], []
        for n in names:
            fields = n.split("\t")
            status, path = fields[0], fields[-1]   # a rename is "R100<tab>old<tab>new"
            if status.startswith("D") or not path:
                continue
            if is_test(path):
                tests.append(path)
            elif Path(path).suffix in SOURCE_EXT:
                sources.append(path)
        if tests and sources:
            out.append({"repo": str(repo), "fix": sha, "parent": parent, "subject": subject,
                        "tests": tests, "sources": sources})
    return out


def _run_tests(wt: Path, task: dict, fix_texts: dict[str, str]) -> tuple[bool, str]:
    """(every test file passes in `wt`, detail of the first failure) with the fix's versions."""
    for path in task["tests"]:
        dest = wt / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(fix_texts[path], encoding="utf-8")
        rc, out = run(test_command(path, fix_texts[path]), wt, TEST_TIMEOUT_S)
        if rc != 0:
            tail = " | ".join(ln.strip() for ln in out.strip().splitlines()[-2:])[:160]
            return False, f"{path} rc={rc}: {tail}"
    return True, ""


def validate(task: dict) -> tuple[bool, str]:
    """(valid, reason). Passes at the fix twice, then fails at the parent. The fix is checked
    first because most rejections happen there, which saves the parent worktree."""
    repo = Path(task["repo"])
    fix_texts = {}
    for path in task["tests"]:
        text = git(repo, "show", f"{task['fix']}:{path}")
        if test_command(path, text) is None:
            return False, f"unrunnable test type: {path}"
        fix_texts[path] = text
    tag = task["fix"][:10]
    wt = add_worktree(repo, task["fix"], f"harvest-{tag}-fix")
    try:
        for attempt in (1, 2):
            ok, detail = _run_tests(wt, task, fix_texts)
            if not ok:
                return False, f"test fails at the fix (attempt {attempt}): {detail}"
    finally:
        drop_worktree(repo, wt)
    wt = add_worktree(repo, task["parent"], f"harvest-{tag}-parent")
    try:
        ok, _ = _run_tests(wt, task, fix_texts)
        if ok:
            return False, "test already passes before the fix"
    finally:
        drop_worktree(repo, wt)
    return True, "passes at the fix (x2), fails before it"


def bank_path() -> Path:
    return state_dir() / "bank.json"


def load_bank() -> dict:
    p = bank_path()
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"tasks": {}, "rejected": {}}


def save_bank(bank: dict) -> None:
    tmp = bank_path().with_suffix(".tmp")
    tmp.write_text(json.dumps(bank, indent=1), encoding="utf-8")
    tmp.replace(bank_path())


def harvest(repos: list[Path], max_new: int = 20, limit: int = 1500, log=print) -> dict:
    """Validate up to `max_new` unseen candidates across `repos`; persist after each one."""
    bank = load_bank()
    seen = set(bank["tasks"]) | set(bank["rejected"])
    added = rejected = 0
    for repo in repos:
        for c in candidates(repo, limit):
            if added >= max_new:
                break
            tid = f"{repo.name}:{c['fix'][:12]}"
            if tid in seen:
                continue
            try:
                ok, why = validate(c)
            except (RuntimeError, OSError, UnicodeDecodeError) as e:
                ok, why = False, f"harvest error: {str(e)[:200]}"
            if ok:
                bank["tasks"][tid] = {**c, "id": tid, "validated": utc_now()}
                added += 1
            else:
                bank["rejected"][tid] = {"reason": why, "at": utc_now()}
                rejected += 1
            seen.add(tid)
            save_bank(bank)
            log(f"{'TASK' if ok else 'skip'} {tid} {why}")
    return {"added": added, "rejected": rejected, "total": len(bank["tasks"])}
