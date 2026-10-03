#!/usr/bin/env python
"""Mutation drill on an ISOLATED copy: prove the clean copy passes, then mutate, run the test,
require the named gate to FAIL.

    python tools/mutation_drill.py --spec drill.json
    drill.json: {"file": "tools/x.py", "test": "tools/test_x.py", "gate": "V-X-NAME",
                 "old": "<anchor>" | [...], "new": "<replacement>" | [...],
                 "copy_dirs": ["some/dir"]      (optional: extra repo dirs the suite reads)
                 "repo_root": "<path>"          (optional: else the nearest ancestor holding .git)
                 "root_env": "SDD_OS_PP_ROOT"   (optional: repo-layout copy; the test imports
                                                 through this variable, see _layout)}

Why a copy (2026-09-28, durable-substrate pass): a drill that edits the live file puts the mutant
in production for as long as the drill runs whenever a scheduler, hook or sweep loads that file.
Two such mutants reached the live mission supervisor before a peer pane noticed. The subject's
directory is copied to a temp dir, the mutant is written there, the test runs from there, and the
live file's SHA-256 is asserted unchanged at the end.

Why a control (2026-10-03, plan ccp-s15 C1): without one, a gate already failing on the clean copy
read KILLED for every mutant, and a misspelled gate read SURVIVED for every mutant. The control
runs on its own copy (the mutant never inherits files or bytecode the control left behind) and
must exit 0, print a `*_PASS=` summary and show the named gate passing.

Layout. A test beside its subject gets that directory plus the repo siblings in DEFAULT_SIBLINGS
and `copy_dirs`. A test OUTSIDE the subject's directory gets the repo layout (both top-level dirs
plus the same siblings) and runs from the copy -- before 2026-10-03 it ran the LIVE test against
the LIVE subject and every mutant read SURVIVED. Limit: a suite that reaches its subject by an
absolute live path still never loads the mutant; give it `root_env`.

A gate line is `PASS <gate>`, `[PASS] <gate>` or `<gate> PASS` (FAIL likewise); the gate name
must end there, so V-X never matches V-X-2.

Outcomes, never collapsed:
  KILLED           the named gate printed FAIL                        exit 0
  SURVIVED         the suite completed and the gate did not fail      exit 1
  UNJUDGED         the mutant run never reached a `*_PASS=` line       exit 2 (a crash is not a verdict)
  HARNESS          bad anchor, no-op mutation, no repo root, or the live file changed   exit 3
  CONTROL_INVALID  the CLEAN copy did not show the gate passing; no mutant was run      exit 4
Anchors travel in JSON because PowerShell 5.1 strips double quotes from native argv.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_SIBLINGS = ("modules", "vault/pricing", "vault/config")   # read by tools/* suites
SKIP = shutil.ignore_patterns("__pycache__", "*.pyc", "node_modules")


class HarnessError(Exception):
    pass


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def gate_line(gate: str, word: str, out: str) -> bool:
    """`word` (PASS/FAIL) attached to exactly this gate, in any of the suite formats in use."""
    g, w = re.escape(gate), rf"(?:\[{word}\]|\b{word}\b)"
    return re.search(rf"{w}[\s:]+{g}(?![\w-])|(?<![\w-]){g}\s+{w}", out) is not None


_FAIL_TOKEN = re.compile(r"(?:^|\s)(?:\[FAIL\]|FAIL)(?=[\s:]|$)")


def detail_lines(out: str) -> list[str]:
    """The lines a human needs to see why a drill ended as it did: every FAIL line and the
    `*_PASS=` summary. DETAIL only -- the verdict is decided by gate_line(), never by this.

    Until 2026-10-03 this was `startswith("FAIL")`, which dropped the indented `  FAIL V-X:`
    lines most suites print, so a KILLED drill could show no failing line at all (ACV C4)."""
    return [l for l in out.splitlines() if _FAIL_TOKEN.search(l) or "_PASS=" in l]


def _copy(src: Path, dst: Path) -> None:
    if dst.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst, ignore=SKIP)
    else:
        shutil.copy2(src, dst)


def _repo_root(spec: dict, live: Path, live_test: Path) -> Path:
    if spec.get("repo_root"):
        repo = Path(spec["repo_root"]).resolve()
    else:
        repo = next((p for p in live.parents if (p / ".git").exists()), None)
        if repo is None:
            raise HarnessError("test is outside the subject dir and no repo root (.git) was found")
    if not (live.is_relative_to(repo) and live_test.is_relative_to(repo)):
        raise HarnessError(f"subject and test are not both under the repo root {repo}")
    return repo


def _layout(spec: dict, live: Path, live_test: Path, root: Path) -> tuple[Path, Path, dict]:
    """Where the mutant goes, which test runs, and the env it runs with.

    `root_env`: the repo layout is preserved (`copy_dirs` relative to `repo_root`, default cwd)
    and the named variable points at the temp root, so a test that imports `modules.x.y` through
    that variable loads the MUTANT (task 14 of vault/plans/sdd-os-evolution-2026-10-01.md).
    """
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    root_env = spec.get("root_env")
    if root_env:
        repo = Path(spec.get("repo_root") or Path.cwd()).resolve()
        rel = live.relative_to(repo)
        for d in spec.get("copy_dirs") or [rel.parts[0]]:
            _copy(repo / d, root / d)
        if not (root / rel).exists():
            shutil.copytree(live.parent, root / rel.parent, ignore=SKIP, dirs_exist_ok=True)
        env[root_env] = str(root)
        return root / rel, live_test, env
    if live_test.is_relative_to(live.parent):
        # Beside its subject: that dir, plus the siblings the suite reads through the repo root
        # (2026-09-28: test_gsd_mission reads modules/autonomy_gate/rubric.json; 2026-10-03:
        # test_displacement reads modules/cognitive_os/scheduler.py).
        iso_dir = root / live.parent.name
        _copy(live.parent, iso_dir)
        base = live.parent.parent
        for d in [*DEFAULT_SIBLINGS, *(spec.get("copy_dirs") or [])]:
            if Path(d).parts[0] != live.parent.name and (base / d).exists():
                _copy(base / d, root / d)
        return iso_dir / live.name, iso_dir / live_test.relative_to(live.parent), env
    repo = _repo_root(spec, live, live_test)
    rel, trel = live.relative_to(repo), live_test.relative_to(repo)
    for d in [rel.parts[0], trel.parts[0], *DEFAULT_SIBLINGS, *(spec.get("copy_dirs") or [])]:
        if (repo / d).exists():
            _copy(repo / d, root / d)
    return root / rel, root / trel, env


def _run(spec: dict, live: Path, live_test: Path, mutate, timeout_s: int):
    """One fresh copy, optionally mutated, one test run. Returns (returncode or None, output)."""
    root = Path(tempfile.mkdtemp(prefix="mutdrill-"))
    try:
        subject, test, env = _layout(spec, live, live_test, root)
        if mutate is not None:
            subject.write_text(mutate, encoding="utf-8")
        try:
            r = subprocess.run([sys.executable, str(test)], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=timeout_s, env=env)
            return r.returncode, r.stdout + r.stderr
        except subprocess.TimeoutExpired:
            return None, "TIMEOUT"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def drill(spec: dict, timeout_s: int = 900) -> tuple[str, str]:
    live = Path(spec["file"]).resolve()
    live_test = Path(spec["test"]).resolve()
    gate = spec["gate"]
    live_sha = _sha(live)
    text = live.read_text(encoding="utf-8")
    olds = spec["old"] if isinstance(spec["old"], list) else [spec["old"]]
    news = spec["new"] if isinstance(spec["new"], list) else [spec["new"]]
    for o in olds:
        if text.count(o) != 1:
            return "HARNESS", f"anchor found {text.count(o)}x: {o[:60]!r}"
    mutant = text
    for o, n in zip(olds, news):
        mutant = mutant.replace(o, n)
    if mutant == text:
        return "HARNESS", "the mutation changes nothing"
    try:
        rc, out = _run(spec, live, live_test, None, timeout_s)
        lines = out.splitlines()
        if (rc != 0 or not any("_PASS=" in l for l in lines)
                or gate_line(gate, "FAIL", out) or not gate_line(gate, "PASS", out)):
            return "CONTROL_INVALID", f"clean copy rc={rc}, gate {gate} not shown passing:\n" + \
                "\n".join(lines[-12:])
        rc, out = _run(spec, live, live_test, mutant, timeout_s)
    except HarnessError as e:
        return "HARNESS", str(e)
    if _sha(live) != live_sha:
        return "HARNESS", "the LIVE file changed during the drill"
    lines = out.splitlines()
    tail = "\n".join(detail_lines(out))
    if not any("_PASS=" in l for l in lines):
        return "UNJUDGED", "\n".join(lines[-12:])
    if gate_line(gate, "FAIL", out):
        return "KILLED", tail
    return "SURVIVED", tail


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2 or argv[0] != "--spec":
        print(__doc__)
        return 2
    spec = json.loads(Path(argv[1]).read_text(encoding="utf-8-sig"))
    verdict, detail = drill(spec)
    print(detail)
    print(f"MUTANT {verdict} gate={spec['gate']}")
    return {"KILLED": 0, "SURVIVED": 1, "UNJUDGED": 2, "CONTROL_INVALID": 4}.get(verdict, 3)


if __name__ == "__main__":
    sys.exit(main())
