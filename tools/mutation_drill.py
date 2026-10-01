#!/usr/bin/env python
"""Mutation drill on an ISOLATED copy: mutate, run the test, require the named gate to FAIL.

    python tools/mutation_drill.py --spec drill.json
    drill.json: {"file": "tools/x.py", "test": "tools/test_x.py", "gate": "V-X-NAME",
                 "old": "<anchor>" | [...], "new": "<replacement>" | [...],
                 "root_env": "SDD_OS_PP_ROOT"   (optional: repo-layout copy; the test imports
                                                 through this variable, see _layout)}

Why a copy (2026-09-28, durable-substrate pass): a drill that edits the live file puts the mutant
in production for as long as the drill runs whenever a scheduler, hook or sweep loads that file.
Two such mutants reached the live mission supervisor before a peer pane noticed. The subject's
directory is copied to a temp dir, the mutant is written there, the test runs from there, and the
live file's SHA-256 is asserted unchanged at the end.

Outcomes, never collapsed:
  KILLED    the named gate printed `FAIL <gate>`             exit 0
  SURVIVED  the suite completed and the gate did not fail    exit 1
  UNJUDGED  the suite never reached a `*_PASS=` summary line exit 2 (a crash is not a verdict)
  HARNESS   an anchor did not match exactly once, or the live file changed   exit 3
Anchors travel in JSON because PowerShell 5.1 strips double quotes from native argv.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _layout(spec: dict, live: Path, live_test: Path, root: Path, skip) -> tuple[Path, Path, dict]:
    """Where the mutant goes, which test runs, and the env it runs with.

    Default (no `root_env`): the subject's directory is copied flat into the temp root -- right
    when the test sits beside its subject. With `root_env`, the repo layout is preserved
    (`copy_dirs` relative to `repo_root`, default cwd) and the named variable points at the temp
    root, so a test that imports `modules.x.y` through that variable loads the MUTANT. Without
    this, a test that imports through the live repo root drilled the live module and every
    mutant read SURVIVED (task 14 of vault/plans/sdd-os-evolution-2026-10-01.md).
    """
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    root_env = spec.get("root_env")
    if not root_env:
        iso_dir = root / live.parent.name
        shutil.copytree(live.parent, iso_dir, ignore=skip)
        # Siblings the suite reads through the repo root (`copy_dirs`: ["modules"]). Without them
        # the suite crashes before its summary and the verdict is UNJUDGED -- honest, but no drill
        # at all (2026-09-28: test_gsd_mission reads modules/autonomy_gate/rubric.json).
        for d in spec.get("copy_dirs") or []:
            shutil.copytree(live.parent.parent / d, root / d, ignore=skip)
        test = iso_dir / live_test.relative_to(live.parent) if live_test.is_relative_to(live.parent) \
            else live_test
        return iso_dir / live.name, test, env
    repo = Path(spec.get("repo_root") or Path.cwd()).resolve()
    rel = live.relative_to(repo)
    for d in spec.get("copy_dirs") or [rel.parts[0]]:
        shutil.copytree(repo / d, root / d, ignore=skip)
    if not (root / rel).exists():
        shutil.copytree(live.parent, root / rel.parent, ignore=skip, dirs_exist_ok=True)
    env[root_env] = str(root)
    return root / rel, live_test, env


def drill(spec: dict, timeout_s: int = 900) -> tuple[str, str]:
    live = Path(spec["file"]).resolve()
    live_test = Path(spec["test"]).resolve()
    live_sha = _sha(live)
    root = Path(tempfile.mkdtemp(prefix="mutdrill-"))
    skip = shutil.ignore_patterns("__pycache__", "*.pyc", "node_modules")
    subject, test, env = _layout(spec, live, live_test, root, skip)
    text = subject.read_text(encoding="utf-8")
    olds = spec["old"] if isinstance(spec["old"], list) else [spec["old"]]
    news = spec["new"] if isinstance(spec["new"], list) else [spec["new"]]
    for o in olds:
        if text.count(o) != 1:
            return "HARNESS", f"anchor found {text.count(o)}x: {o[:60]!r}"
    for o, n in zip(olds, news):
        text = text.replace(o, n)
    subject.write_text(text, encoding="utf-8")
    try:
        r = subprocess.run([sys.executable, str(test)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout_s, env=env)
        out = r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        out = "TIMEOUT"
    finally:
        shutil.rmtree(root, ignore_errors=True)
    if _sha(live) != live_sha:
        return "HARNESS", "the LIVE file changed during the drill"
    tail = "\n".join(l for l in out.splitlines() if l.startswith("FAIL") or "_PASS=" in l)
    if not any("_PASS=" in l for l in out.splitlines()):
        return "UNJUDGED", "\n".join(out.splitlines()[-12:])
    if f"FAIL {spec['gate']}" in out:
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
    return {"KILLED": 0, "SURVIVED": 1, "UNJUDGED": 2}.get(verdict, 3)


if __name__ == "__main__":
    sys.exit(main())
