"""Test gaps on the user's code -- which changed lines would no test notice breaking?

Spec: vault/specs/test-gaps.md (Gap 3 v1). For a Python project tested with pytest:

    python tools/test_gaps.py --repo <project> [--base HEAD] [--files a.py b.py] [--json]

reports, for the lines changed since --base (plus untracked .py files):

    UNCOVERED  no test executes the line
    SURVIVED   a test executes the line, but breaking it fails no test; the tests that ran
               it are named, so the agent knows which one to strengthen

Everything runs in an isolated copy of the project. The mutator is mutation_probe's, imported
unchanged. Exit 0 = measured (gaps are information), 2 = unmeasurable or harness failure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mutation_probe import count_candidates, mutate  # noqa: E402

DEFAULT_MAX_MUTANTS = 20
# The baseline runs every test under coverage (subprocesses included) and is the slowest run; a
# real CLI project took ~100 s on a RAM-starved host. Each mutant run then gets 3x the measured
# baseline, never less than RUN_TIMEOUT_S.
BASELINE_TIMEOUT_S = 600
RUN_TIMEOUT_S = 120
SKIP_DIRS = {".git", ".hg", ".venv", "venv", "env", "node_modules", "__pycache__", ".tox", ".nox",
             ".mypy_cache", ".pytest_cache", ".ruff_cache", "build", "dist", ".eggs", "htmlcov"}
LABEL_LINE = re.compile(r"^line (\d+):")
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def _git() -> str:
    found = shutil.which("git")
    if found:
        return found
    # git is not on PowerShell's PATH on this host (vault/lessons/powershell-git-path-gap.md).
    win = Path(r"C:\Program Files\Git\cmd\git.exe")
    return str(win) if win.is_file() else "git"


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def is_test_path(rel: str) -> bool:
    parts = Path(rel).parts
    name = parts[-1]
    return (name.startswith("test_") or name.endswith("_test.py") or name == "conftest.py"
            or any(p in ("tests", "test") for p in parts[:-1]))


def changed_lines(repo: Path, base: str) -> dict[str, set[int]]:
    """{posix relpath: changed line numbers} for non-test .py files, tracked and untracked."""
    git = _git()
    out = subprocess.run([git, "-C", str(repo), "diff", "-U0", "--no-color", "--no-ext-diff",
                          base, "--", "*.py"], capture_output=True, text=True, encoding="utf-8",
                         errors="replace", check=True).stdout
    result: dict[str, set[int]] = {}
    current = None
    for line in out.splitlines():
        if line.startswith("+++ "):
            target = line[4:].strip()
            current = None if target == "/dev/null" else target[2:] if target.startswith("b/") else target
            continue
        m = HUNK.match(line)
        if m and current:
            start, count = int(m.group(1)), int(m.group(2) or 1)
            if count:
                result.setdefault(current, set()).update(range(start, start + count))
    untracked = subprocess.run([git, "-C", str(repo), "ls-files", "--others", "--exclude-standard",
                                "--", "*.py"], capture_output=True, text=True, encoding="utf-8",
                               errors="replace", check=True).stdout
    for rel in untracked.splitlines():
        rel = rel.strip()
        if rel:
            n = len((repo / rel).read_text(encoding="utf-8-sig").splitlines())
            result[rel] = set(range(1, n + 1))
    return {k: v for k, v in result.items() if not is_test_path(k) and (repo / k).is_file()}


def _detect_python(repo: Path) -> str:
    for rel in (".venv/Scripts/python.exe", "venv/Scripts/python.exe", ".venv/bin/python",
                "venv/bin/python"):
        if (repo / rel).is_file():
            return str(repo / rel)
    return sys.executable


def _pytest(python: str, root: Path, args: list[str], extra_env: dict | None = None,
            timeout: float = RUN_TIMEOUT_S):
    """(exit code | 'TIMEOUT', output tail)."""
    pypath = [str(root)] + ([str(root / "src")] if (root / "src").is_dir() else [])
    # PYTHONPATH is inherited by subprocesses the tests spawn, so a CLI test's child imports the
    # copy too, not an editable install of the original.
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
               PYTHONPATH=os.pathsep.join(pypath + [os.environ.get("PYTHONPATH", "")]).rstrip(os.pathsep))
    env.update(extra_env or {})
    try:
        p = subprocess.run([python, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--rootdir",
                            str(root), *args], cwd=str(root), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return "TIMEOUT", ""
    return p.returncode, "\n".join((p.stdout + p.stderr).splitlines()[-15:])


def _ranges(lines: list[int]) -> list[str]:
    out, start, prev = [], None, None
    for n in lines:
        if start is None:
            start = prev = n
        elif n == prev + 1:
            prev = n
        else:
            out.append(f"{start}" if start == prev else f"{start}-{prev}")
            start = prev = n
    if start is not None:
        out.append(f"{start}" if start == prev else f"{start}-{prev}")
    return out


def analyse(repo: Path, base: str = "HEAD", files: list[str] | None = None,
            max_mutants: int = DEFAULT_MAX_MUTANTS, python: str | None = None,
            baseline_timeout: float = BASELINE_TIMEOUT_S) -> dict:
    repo = repo.resolve()
    python = python or _detect_python(repo)
    res: dict = {"repo": str(repo), "base": base, "python": python, "uncovered": {},
                 "not_measured": [], "killed": [], "survived": [], "timeout": [], "errors": []}
    if files:
        targets = {}
        for f in files:
            rel = Path(f).as_posix()
            if not is_test_path(rel):
                targets[rel] = set(range(1, len((repo / rel).read_text(encoding="utf-8-sig").splitlines()) + 1))
    else:
        targets = changed_lines(repo, base)
    res["changed"] = {k: len(v) for k, v in sorted(targets.items())}
    if not targets:
        res["verdict"], res["reason"] = "NO_CHANGES", "no changed non-test .py lines"
        return res

    before = {rel: _sha(repo / rel) for rel in targets}
    tmp = Path(tempfile.mkdtemp(prefix="test-gaps-"))
    copy = tmp / "proj"
    try:
        shutil.copytree(repo, copy, ignore=lambda _d, names: [n for n in names if n in SKIP_DIRS
                                                              or n.endswith((".pyc", ".pyo"))])
        if subprocess.run([python, "-c", "import pytest, pytest_cov, coverage"],
                          capture_output=True).returncode != 0:
            res["verdict"] = "UNMEASURABLE"
            res["reason"] = f"pytest, pytest-cov and coverage must be importable by {python}"
            return res

        cov_env = {"COVERAGE_FILE": str(tmp / ".coverage")}
        # `patch = subprocess` (coverage >= 7.10): a test that drives the code through
        # `subprocess.run([sys.executable, "-m", pkg])` is measured too. Without it, measured on a
        # real project 2026-10-01, every CLI line those tests exercise was reported UNCOVERED.
        rc = tmp / "coveragerc"
        rc.write_text("[run]\npatch = subprocess\n", encoding="utf-8")
        t0 = time.monotonic()
        code, tail = _pytest(python, copy, ["--cov", str(copy), f"--cov-config={rc}",
                                            "--cov-context=test", "--cov-report="], cov_env,
                             timeout=baseline_timeout)
        res["baseline_s"] = round(time.monotonic() - t0, 1)
        if code != 0:
            res["verdict"] = "UNMEASURABLE"
            res["reason"] = (f"the clean suite does not pass in the copy (exit {code}), so a red "
                             f"run would prove nothing about a mutant")
            res["baseline_tail"] = tail
            return res
        mutant_timeout = max(RUN_TIMEOUT_S, 3 * res["baseline_s"])
        cov_cmd_env = dict(os.environ, **cov_env)
        # Subprocess data lands in per-process files beside COVERAGE_FILE. "No data to combine"
        # (nothing spawned) is a normal outcome, so the exit code is not checked here.
        subprocess.run([python, "-m", "coverage", "combine", "--append", "-q", f"--rcfile={rc}"],
                       cwd=str(copy), env=cov_cmd_env, capture_output=True)
        subprocess.run([python, "-m", "coverage", "json", "--show-contexts", "-q", "-o",
                        str(tmp / "cov.json"), f"--rcfile={rc}"], cwd=str(copy), env=cov_cmd_env,
                       capture_output=True, check=True)
        cov = {Path(k).as_posix(): v for k, v in
               json.loads((tmp / "cov.json").read_text(encoding="utf-8"))["files"].items()}

        candidates = []   # (rel, index, label, line, node ids)
        for rel, lines in sorted(targets.items()):
            data = cov.get(rel)
            if data is None:
                res["not_measured"].append(rel)
                continue
            executed = set(data["executed_lines"])
            unc = sorted(lines & set(data["missing_lines"]))
            if unc:
                res["uncovered"][rel] = unc
            ctx = data.get("contexts") or {}
            src = (copy / rel).read_text(encoding="utf-8-sig")
            baseline = mutate(src, -1)[0]
            for i in range(count_candidates(src)):
                mutated, label = mutate(src, i)
                m = LABEL_LINE.match(label)
                if not m or mutated == baseline:
                    continue
                line = int(m.group(1))
                # Node ids of the tests that ran this line. Empty when it ran only with no test
                # context -- in a subprocess a test spawned, or at import time. No single test
                # can be credited then, so the mutant is judged by the whole suite rather than
                # skipped (skipping is what left a real CLI project with 0 candidates).
                nodes = sorted({c.split("|")[0] for c in ctx.get(str(line), []) if c})
                if line in lines and line in executed:
                    candidates.append((rel, i, label, line, nodes))

        res["candidates"] = len(candidates)
        step = max(1, -(-len(candidates) // max_mutants)) if candidates else 1
        picks = candidates[::step][:max_mutants]
        res["sampled"] = len(picks)
        for rel, i, label, line, nodes in picks:
            target = copy / rel
            original = target.read_bytes()
            mutated, _ = mutate(original.decode("utf-8-sig"), i)
            target.write_text(mutated, encoding="utf-8")
            try:
                code, tail = _pytest(python, copy, nodes, timeout=mutant_timeout)
            finally:
                target.write_bytes(original)
            row = {"file": rel, "line": line, "mutation": label.split(": ", 1)[1], "tests": nodes}
            if code == "TIMEOUT":
                res["timeout"].append(row)
            elif code in (1, 2):
                res["killed"].append(row)
            elif code == 0:
                res["survived"].append(row)
            else:
                res["errors"].append(dict(row, exit=code, tail=tail))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        changed_live = [rel for rel, h in before.items() if not (repo / rel).is_file()
                        or _sha(repo / rel) != h]
        if changed_live:
            # The run never writes to the project; a moved file means someone else did, and
            # the measurement no longer describes what is on disk.
            res["verdict"] = "UNMEASURABLE"
            res["reason"] = f"project files changed during the run: {changed_live}"
    if "verdict" not in res:
        res["verdict"] = "MEASURED"
    return res


def render(res: dict) -> str:
    out = [f"TEST_GAPS repo={res['repo']} base={res['base']}",
           f"  verdict={res['verdict']}  {res.get('reason', '')}".rstrip()]
    if res["verdict"] != "MEASURED":
        if res.get("baseline_tail"):
            out += ["  " + ln for ln in res["baseline_tail"].splitlines()]
        return "\n".join(out)
    out.append(f"  changed files={len(res['changed'])}  mutants: killed={len(res['killed'])} "
               f"survived={len(res['survived'])} timeout={len(res['timeout'])} "
               f"error={len(res['errors'])}  (sampled {res['sampled']} of {res['candidates']})")
    for rel, lines in res["uncovered"].items():
        out.append(f"  UNCOVERED  {rel}:{','.join(_ranges(lines))}")
    for rel in res["not_measured"]:
        out.append(f"  NOT_MEASURED {rel} (no coverage data: never imported from this project)")
    for r in res["survived"]:
        ran_by = (", ".join(r["tests"]) if r["tests"]
                  else "(whole suite: line ran in a subprocess or at import, no single test)")
        out.append(f"  SURVIVED   {r['file']}:{r['line']}  {r['mutation']}  ran by: {ran_by}")
    for r in res["timeout"]:
        out.append(f"  TIMEOUT    {r['file']}:{r['line']}  {r['mutation']}")
    for r in res["errors"]:
        out.append(f"  ERROR      {r['file']}:{r['line']}  {r['mutation']}  pytest exit {r['exit']}")
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Which changed lines would no test notice breaking?")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--base", default="HEAD")
    ap.add_argument("--files", nargs="*")
    ap.add_argument("--max-mutants", type=int, default=DEFAULT_MAX_MUTANTS)
    ap.add_argument("--timeout", type=float, default=BASELINE_TIMEOUT_S,
                    help="seconds for the coverage baseline run")
    ap.add_argument("--python")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        res = analyse(Path(a.repo), a.base, a.files, a.max_mutants, a.python, a.timeout)
    except subprocess.CalledProcessError as exc:
        res = {"repo": a.repo, "base": a.base, "verdict": "UNMEASURABLE",
               "reason": f"{Path(exc.cmd[0]).name} failed (exit {exc.returncode})"}
    print(json.dumps(res, indent=1) if a.json else render(res))
    return 0 if res["verdict"] in ("MEASURED", "NO_CHANGES") else 2


if __name__ == "__main__":
    sys.exit(main())
