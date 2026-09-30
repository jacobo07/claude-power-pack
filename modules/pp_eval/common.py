"""Shared paths, git and subprocess helpers for PP Self-Eval (vault/specs/pp-self-eval.md).

Paths are overridable by env so the gates run hermetically:
  PP_EVAL_STATE  hidden state (bank, fingerprints, lock)   default ~/.claude/state/pp-eval
  PP_EVAL_RUNS   throwaway worktrees                       default ~/Apps/pp-eval-runs
  PP_EVAL_VAULT  ledger + report                           default <PP>/vault/eval
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

PP = Path(__file__).resolve().parents[2]
GIT = os.environ.get("CPP_GIT_EXE") or shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"


def state_dir() -> Path:
    p = Path(os.environ.get("PP_EVAL_STATE") or Path.home() / ".claude" / "state" / "pp-eval")
    p.mkdir(parents=True, exist_ok=True)
    return p


def runs_dir() -> Path:
    p = Path(os.environ.get("PP_EVAL_RUNS") or Path.home() / "Apps" / "pp-eval-runs")
    p.mkdir(parents=True, exist_ok=True)
    return p


def vault_dir() -> Path:
    p = Path(os.environ.get("PP_EVAL_VAULT") or PP / "vault" / "eval")
    p.mkdir(parents=True, exist_ok=True)
    return p


def git(repo: Path, *args: str, check: bool = True, timeout: int = 120) -> str:
    r = subprocess.run([GIT, "-C", str(repo), *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args[:3])}: {r.stderr.strip()[:300]}")
    return r.stdout


def run(cmd: list[str], cwd: Path, timeout: int, env: dict | None = None) -> tuple[object, str]:
    """(returncode | 'timeout', combined output tail). Never raises on the child's failure."""
    try:
        r = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout, env=env)
        return r.returncode, (r.stdout + r.stderr)[-2000:]
    except subprocess.TimeoutExpired:
        return "timeout", ""
    except OSError as e:
        return "oserror", str(e)


def add_worktree(repo: Path, commit: str, name: str) -> Path:
    wt = runs_dir() / name
    if wt.exists():
        drop_worktree(repo, wt)
    git(repo, "worktree", "add", "--detach", str(wt), commit, timeout=300)
    return wt


def drop_worktree(repo: Path, wt: Path) -> None:
    """Remove a throwaway worktree this module created under runs_dir() only."""
    if runs_dir().resolve() not in wt.resolve().parents:
        raise RuntimeError(f"refusing to remove a worktree outside runs_dir: {wt}")
    git(repo, "worktree", "remove", "--force", str(wt), check=False, timeout=300)
    if wt.exists():
        shutil.rmtree(wt, ignore_errors=True)
    git(repo, "worktree", "prune", check=False)


class Lock:
    """Kernel byte-range lock, released by the OS when the holder dies (same design as
    tools/gsd_mission.py _Lock, 2026-09-27 T3). The file is never deleted."""

    def __init__(self, path: Path):
        self.path, self.fd = path, None

    def acquire(self) -> bool:
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT)
        try:
            if sys.platform == "win32":
                import msvcrt
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(fd)
            return False
        self.fd = fd
        return True

    def release(self) -> None:
        fd, self.fd = self.fd, None
        if fd is None:
            return
        try:
            if sys.platform == "win32":
                import msvcrt
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        finally:
            os.close(fd)


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
