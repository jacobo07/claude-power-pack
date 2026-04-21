"""
Per-repo file lock — prevents concurrent healing dispatches against the same
target repository.

Uses the `filelock` library for cross-platform advisory locks.
"""

from __future__ import annotations

import hashlib
import logging
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .. import STATE_DIR_DEFAULT

logger = logging.getLogger(__name__)


def _lock_dir() -> Path:
    override = os.environ.get("QA_STATE_DIR")
    base = Path(override).expanduser() if override else STATE_DIR_DEFAULT
    d = base / "locks"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _lock_path_for(repo_path: Path) -> Path:
    resolved = str(Path(repo_path).resolve())
    digest = hashlib.sha256(resolved.encode("utf-8")).hexdigest()[:16]
    return _lock_dir() / f"{digest}.lock"


@contextmanager
def repo_lock(repo_path: Path, timeout_seconds: float = 1.0) -> Iterator[Path]:
    """
    Acquire an exclusive lock for the given repo. Non-blocking by default
    (timeout=1s) so stacked runs fail fast rather than queuing silently.
    """
    try:
        from filelock import FileLock, Timeout  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "filelock not installed. Run: pip install filelock"
        ) from exc

    lock_path = _lock_path_for(repo_path)
    fl = FileLock(str(lock_path))
    try:
        fl.acquire(timeout=timeout_seconds)
    except Timeout as exc:
        raise RuntimeError(
            f"Another sleepless-qa run is already holding the lock for {repo_path}. "
            f"Lock file: {lock_path}"
        ) from exc
    logger.info("Acquired repo lock %s", lock_path)
    try:
        yield lock_path
    finally:
        try:
            fl.release()
            logger.info("Released repo lock %s", lock_path)
        except Exception:
            logger.exception("Failed to release lock %s", lock_path)
