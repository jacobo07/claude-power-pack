"""Independent enumerators for the baseline population (code review WR-05).

`baselines.discover_subjects` walks the baselines tree. A real-tree gate that
checks only its own walk against a floor frozen at today's population measures
nothing the walk did not already say: a subject the walk skipped is, to the walk,
simply absent, and a floor equal to today's count is satisfied by coincidence.

This module enumerates the same population by routes the walk does not share, so
a subject the walk dropped shows up as a DIFFERENCE instead of as silence:

  families   every `vault/tower/families/<id>.json` names a baseline subject that
             must be discovered (the family registry is written by a different
             process than the generations).
  git        every `vault/tower/baselines/**/B<n>.json` the repository TRACKS must
             belong to a discovered subject. One-directional on purpose: a subject
             newly written on disk and not yet committed is legitimate; a tracked
             subject the walk cannot see is not.
  disk       a glob over the tree (a second listing; it shares the filesystem with
             the walk, so it can only catch a walk-logic defect, not an unreadable
             directory -- which `discover_report` reports on its own).

`cross_check` returns what is missing/extra per route; an empty result is the pass
condition, and a route that could not run is named in `unavailable`, never counted
as agreement.

Used by tools/test_tower_ratchet.py, tools/test_baseline_generations.py and
tools/test_ucep_baseline_integrity.py.
"""
from __future__ import annotations

import glob
import json
import os
import re
import shutil
import subprocess

_HERE = os.path.dirname(os.path.abspath(__file__))
_PP_ROOT = os.path.normpath(os.path.join(_HERE, ".."))
_GEN = re.compile(r"^B(\d+)\.json$")


def _git_exe():
    found = shutil.which("git")
    if found:
        return found
    fallback = r"C:\Program Files\Git\cmd\git.exe"
    return fallback if os.path.isfile(fallback) else None


def disk_subjects(root: str) -> list:
    """Subjects by a glob listing: directories (not the root) holding a B<n>.json."""
    found = set()
    for path in glob.glob(os.path.join(glob.escape(root), "**", "B*.json"), recursive=True):
        if not _GEN.match(os.path.basename(path)):
            continue
        parent = os.path.dirname(path)
        if os.path.normpath(parent) == os.path.normpath(root):
            continue
        found.add(os.path.relpath(parent, root).replace(os.sep, "/"))
    return sorted(found)


def git_subjects(root: str, repo: str | None = None):
    """Subjects of the generation files git tracks under `root`, or None if git
    (or the repository) is not available. `root` must live inside `repo`."""
    exe = _git_exe()
    if not exe:
        return None
    repo = repo or _PP_ROOT
    try:
        proc = subprocess.run([exe, "-C", repo, "ls-files", "-z", "--", root],
                              capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    found = set()
    for rel in proc.stdout.decode("utf-8", "replace").split("\0"):
        if not rel or not _GEN.match(os.path.basename(rel)):
            continue
        parent = os.path.join(repo, os.path.dirname(rel))
        if os.path.normpath(parent) == os.path.normpath(root):
            continue
        found.add(os.path.relpath(parent, root).replace(os.sep, "/"))
    return sorted(found)


def family_subjects(directory: str | None = None) -> list:
    from modules.tower import families as fm
    return sorted(f.id for f in fm.load_families(directory))


def active_entry_total(root: str, subjects) -> int:
    """Active (non-reverted) entries of each subject's newest generation, read
    straight from the JSON (no baselines.py reader)."""
    total = 0
    for s in subjects:
        gens = []
        d = os.path.join(root, *s.split("/"))
        for name in os.listdir(d):
            m = _GEN.match(name)
            if m:
                gens.append(int(m.group(1)))
        if not gens:
            continue
        with open(os.path.join(d, "B%d.json" % max(gens)), "r", encoding="utf-8") as fh:
            doc = json.load(fh)
        total += sum(1 for e in doc.get("entries", []) if e.get("status") != "reverted")
    return total


def cross_check(discovered, root: str, families=None, git=True) -> dict:
    """What the independent routes see that `discovered` does not (and the reverse
    for the disk listing). Empty `missing` and `extra` is agreement; `unavailable`
    names a route that could not run (never counted as agreement)."""
    got = set(discovered)
    out = {"missing": {}, "extra": {}, "unavailable": []}
    fams = family_subjects() if families is None else sorted(families)
    gone = sorted(set(fams) - got)
    if gone:
        out["missing"]["families"] = gone
    on_disk = set(disk_subjects(root))
    if on_disk - got:
        out["missing"]["disk"] = sorted(on_disk - got)
    if got - on_disk:
        out["extra"]["disk"] = sorted(got - on_disk)
    if git:
        tracked = git_subjects(root)
        if tracked is None:
            out["unavailable"].append("git")
        elif set(tracked) - got:
            out["missing"]["git"] = sorted(set(tracked) - got)
    return out
