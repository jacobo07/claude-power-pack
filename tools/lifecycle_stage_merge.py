"""Deterministic stage merge for a lifecycle live install (zero model).

Builds a stage worktree of the LIVE checkout at its HEAD, then for every file in the install set runs
`git merge-file` on LF-normalised blobs: ours = LIVE HEAD, base = BASE commit on the branch, theirs = THEIRS commit.
New files are copied from THEIRS. Writes the stage-vs-LIVE-HEAD binary diff as the install patch and prints per-file
conflict counts. Any conflict stops it with exit 2 and no patch. CRLF/LF blob differences are why a plain branch diff
does not apply to LIVE; WU-INST2 measured the same thing.

usage: python lifecycle_stage_merge.py --branch-repo DIR --base SHA --theirs SHA --live DIR --stage DIR --out PATCH
       [--path P ...]   (default: every file changed BASE..THEIRS under hooks tools modules vault/config)
"""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

GIT = r"C:\Program Files\Git\cmd\git.exe"
EXCLUDE = {"tools/lifecycle_install_apply.ps1", "tools/lifecycle_stage_merge.py"}


def git(repo: str, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run([GIT, "-C", repo, *args], capture_output=True, check=check)


def blob(repo: str, rev: str, path: str) -> bytes | None:
    r = git(repo, "show", f"{rev}:{path}", check=False)
    return r.stdout.replace(b"\r\n", b"\n") if r.returncode == 0 else None


def main() -> int:
    ap = argparse.ArgumentParser()
    for k in ("branch-repo", "base", "theirs", "live", "stage", "out"):
        ap.add_argument(f"--{k}", required=True)
    ap.add_argument("--path", action="append", default=[])
    a = ap.parse_args()

    paths = a.path or [p for p in git(a.branch_repo, "diff", "--name-only", a.base, a.theirs, "--",
                                      "hooks", "tools", "modules", "vault/config").stdout.decode().split()
                       if p not in EXCLUDE]
    live_head = git(a.live, "rev-parse", "HEAD").stdout.decode().strip()
    if Path(a.stage).exists():
        print(f"stage {a.stage} already exists; refusing", file=sys.stderr)
        return 1
    git(a.live, "worktree", "add", "--detach", a.stage, live_head)
    conflicts = 0
    with tempfile.TemporaryDirectory() as td:
        for p in paths:
            ours, base, theirs = blob(a.live, live_head, p), blob(a.branch_repo, a.base, p), blob(a.branch_repo, a.theirs, p)
            dst = Path(a.stage, p)
            if theirs is None:
                print(f"skip {p}: deleted on the branch (not handled)")
                continue
            if ours is None or base is None:
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(theirs)
                print(f"copy {p} (new)")
                continue
            fo, fb, ft = (Path(td, n) for n in ("o", "b", "t"))
            fo.write_bytes(ours); fb.write_bytes(base); ft.write_bytes(theirs)
            r = subprocess.run([GIT, "merge-file", "-p", str(fo), str(fb), str(ft)], capture_output=True)
            n = r.returncode if r.returncode > 0 else 0
            conflicts += n
            dst.write_bytes(r.stdout)
            print(f"merge {p}: {n} conflict(s)")
    if conflicts:
        print(f"CONFLICTS {conflicts}: no patch written; stage left at {a.stage}")
        return 2
    git(a.stage, "add", "-A", "--", *paths)
    diff = git(a.stage, "diff", "--cached", "--binary", live_head, "--", *paths).stdout
    Path(a.out).write_bytes(diff)
    print(f"live_head {live_head}")
    print(f"patch {a.out} {len(diff)} bytes sha256 {hashlib.sha256(diff).hexdigest().upper()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
