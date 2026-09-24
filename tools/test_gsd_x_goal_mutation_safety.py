#!/usr/bin/env python3
"""V-gates for the goal mutation drill's own safety: a killed drill leaves no mutant.

    python tools/test_gsd_x_goal_mutation_safety.py

Every subject here is a file this test creates; the drill's real targets are never
touched. The hard-kill case runs a child that journals, mutates, and dies with
os._exit -- no `finally`, no handler -- which is what a memory guard does.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRILL = ROOT / "tools" / "test_gsd_x_goal_mutation.py"
GIT = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"   # PATH first: GEX44 (Linux) runs these

spec = importlib.util.spec_from_file_location("goal_mutation_drill", DRILL)
drill = importlib.util.module_from_spec(spec)
spec.loader.exec_module(drill)

KILLED_CHILD = """
import importlib.util, os, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("d", sys.argv[1])
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
target, journal = Path(sys.argv[2]), Path(sys.argv[3])
d.write_journal(journal, {target: target.read_bytes()})
target.write_bytes(b"MUTANT: the guard is gone\\n")
os._exit(9)
"""


def main() -> int:
    passes: list[str] = []
    fails: list[str] = []

    def check(g, cond, ev, why):
        (passes if cond else fails).append(g)
        print(f"  {'PASS' if cond else 'FAIL'} {g}: {ev if cond else why}")

    work = Path(tempfile.mkdtemp(prefix="gsdx_mutsafe_"))
    original = b"def guard():\n    return refuse()\n"

    # --- a hard-killed run leaves a mutant, and the next run's recovery removes it ---
    target, journal = work / "subject.py", work / "journal.json"
    target.write_bytes(original)
    child = subprocess.run([sys.executable, "-B", "-c", KILLED_CHILD, str(DRILL),
                            str(target), str(journal)], capture_output=True, text=True,
                           timeout=120)
    stranded = target.read_bytes() != original and journal.is_file()
    check("V-MUTSAFE-KILL-STRANDS", child.returncode == 9 and stranded,
          "precondition: a hard kill mid-mutant leaves the mutant and its journal",
          f"rc={child.returncode} stranded={stranded} err={child.stderr[-200:]}")
    moved = drill.recover(journal)
    check("V-MUTSAFE-RECOVER", moved == [str(target)] and target.read_bytes() == original
          and not journal.exists(),
          "the next run restores the original bytes and retires the journal",
          f"moved={moved} bytes={target.read_bytes()!r} journal={journal.exists()}")

    # --- control: an intact file is not rewritten, and the journal is still retired ---
    drill.write_journal(journal, {target: original})
    check("V-MUTSAFE-RECOVER-NOOP", drill.recover(journal) == [] and not journal.exists(),
          "a journal over unmutated files moves nothing", "recovery touched an intact file")
    check("V-MUTSAFE-NO-JOURNAL", drill.recover(journal) == [],
          "no journal, nothing to recover", "recovery invented work")

    # --- a damaged journal refuses instead of writing a second unknown state ---
    drill.write_journal(journal, {target: original})
    data = json.loads(journal.read_text(encoding="utf-8"))
    data[str(target)]["sha256"] = "0" * 64
    journal.write_text(json.dumps(data), encoding="utf-8")
    target.write_bytes(b"someone's edit\n")
    try:
        drill.recover(journal)
        check("V-MUTSAFE-CORRUPT-REFUSES", False, "", "a corrupt journal was restored from")
    except RuntimeError as exc:
        check("V-MUTSAFE-CORRUPT-REFUSES",
              "corrupt" in str(exc) and target.read_bytes() == b"someone's edit\n",
              "a journal failing its own digest raises and writes nothing", str(exc))
    journal.unlink()

    # --- the dirty-target refusal, both poles, plus git unable to answer ---
    repo = work / "repo"
    repo.mkdir()
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
    (repo / "mod.py").write_bytes(original)
    subprocess.run([GIT, "init", "-q", str(repo)], check=True, env=env)
    subprocess.run([GIT, "-C", str(repo), "add", "."], check=True, env=env)
    subprocess.run([GIT, "-C", str(repo), "commit", "-qm", "seed"], check=True, env=env)
    mod = repo / "mod.py"
    check("V-MUTSAFE-CLEAN-ADMITS", drill.dirty_targets(repo, {mod}) == [],
          "a committed, unmodified target is admitted", f"{drill.dirty_targets(repo, {mod})}")
    mod.write_bytes(b"def guard():\n    return True\n")
    check("V-MUTSAFE-DIRTY-REFUSES", drill.dirty_targets(repo, {mod}) == ["mod.py"],
          "a modified target is named, so the run refuses",
          f"{drill.dirty_targets(repo, {mod})}")
    plain = work / "plain"
    plain.mkdir()
    (plain / "x.py").write_bytes(original)
    check("V-MUTSAFE-UNANSWERED-IS-NOT-CLEAN",
          drill.dirty_targets(plain, {plain / "x.py"}) is None,
          "outside a repository git cannot answer, and that is None, not clean",
          f"{drill.dirty_targets(plain, {plain / 'x.py'})}")

    total = len(passes) + len(fails)
    print(f"\nGSDX_GOAL_MUTATION_SAFETY_PASS={len(passes)}/{total}  threshold={total}/{total}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
