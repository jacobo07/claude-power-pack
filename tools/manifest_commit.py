"""Zero-model commit driver: run each manifest entry's tests, then commit exactly its paths.

  manifest_commit.py --manifest vault/plans/ql-econ-commit-manifest.json [--log vault/plans/ql-econ-commit-log.jsonl]

Manifest = ordered list of {repo, paths[], test_cmds[], message}. Per entry: run test_cmds in the repo (the
first failure stops the whole run and nothing is committed for that entry), `git add -- <paths>`, re-read HEAD
(a HEAD that moved since the entry began aborts: someone else committed), then commit pathspec-scoped with the
message from a file. Nothing outside `paths` is ever staged. One JSON log line per step.
Exit: 0 all committed (or nothing to commit), 3 a test failed, 4 HEAD moved / git failure.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

GIT = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"


def _git(repo: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([GIT, "-C", repo, *args], capture_output=True, text=True, encoding="utf-8")


def _log(path: Path | None, **row) -> None:
    row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **row}
    print(json.dumps(row))
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(row) + "\n")


def run_entry(i: int, e: dict, log: Path | None) -> int:
    repo, paths = e["repo"], list(e["paths"])
    if not paths:
        _log(log, step="refused", entry=i, reason="no paths")
        return 4
    head0 = _git(repo, "rev-parse", "HEAD").stdout.strip()
    for cmd in e.get("test_cmds") or []:
        p = subprocess.run(cmd, shell=True, cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace")
        _log(log, step="test", entry=i, cmd=cmd, rc=p.returncode, tail=(p.stdout + p.stderr)[-400:])
        if p.returncode != 0:
            _log(log, step="stopped", entry=i, reason="test failed; nothing committed for this entry")
            return 3
    add = _git(repo, "add", "--", *paths)
    if add.returncode != 0:
        _log(log, step="add_failed", entry=i, err=add.stderr.strip())
        return 4
    if _git(repo, "diff", "--cached", "--quiet", "--", *paths).returncode == 0:
        _log(log, step="nothing_to_commit", entry=i, paths=paths)
        return 0
    head1 = _git(repo, "rev-parse", "HEAD").stdout.strip()
    if head1 != head0:
        _log(log, step="head_moved", entry=i, before=head0, after=head1)
        return 4
    msg = Path(tempfile.mkdtemp(prefix="manifest-commit-")) / "msg.txt"
    msg.write_text(e["message"].rstrip() + "\n", encoding="utf-8", newline="\n")
    c = _git(repo, "commit", "-F", str(msg), "--", *paths)
    if c.returncode != 0:
        _log(log, step="commit_failed", entry=i, err=(c.stdout + c.stderr).strip()[-400:])
        return 4
    subject = _git(repo, "log", "-1", "--format=%s").stdout.strip()
    want = e["message"].strip().splitlines()[0]
    if subject != want:
        _git(repo, "commit", "--amend", "-F", str(msg), "--only", "--", *paths)
        subject = _git(repo, "log", "-1", "--format=%s").stdout.strip()
    _log(log, step="committed", entry=i, head=_git(repo, "rev-parse", "HEAD").stdout.strip(), subject_ok=subject == want,
         paths=paths)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="manifest_commit")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--log")
    args = ap.parse_args(argv)
    entries = json.loads(Path(args.manifest).read_text(encoding="utf-8-sig"))
    log = Path(args.log) if args.log else None
    for i, e in enumerate(entries):
        rc = run_entry(i, e, log)
        if rc:
            return rc
    return 0


if __name__ == "__main__":
    sys.exit(main())
