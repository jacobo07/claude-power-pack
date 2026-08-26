"""Single-instance lock on the contended resource: the browser profile.

WHY THIS EXISTS
---------------
Found empirically, not anticipated. A `Start-Process` child survived the
PowerShell error that was supposed to abort it, kept running detached, and was
still driving the browser when a second runner launched against the same
Chromium profile. The ledger handled it correctly -- `claim_next` is
transactional, so the two would simply have taken different prompts -- but a
Chromium persistent-context profile cannot be opened twice, so the second run
died on a resource conflict rather than on anything meaningful.

The ledger was never the contended resource. The profile is.

`sleepless_qa.healer.lock` solves the same shape with the `filelock` package
plus that module's own state directory. This is stdlib and keyed on the
profile path, which is what actually collides.

STALENESS
---------
Uses the same lease idea as the job ledger, for the same reason: a process
that is killed cannot release anything, so the lock must expire on its own.
The holder refreshes while it works; a lock whose heartbeat has gone quiet
past the TTL is stolen, and the theft is reported rather than silent.
"""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

#: A lock whose heartbeat is older than this is treated as abandoned. Longer
#: than any single prompt (measured ~14s, budgeted 600s) so a slow generation
#: is never mistaken for a dead process.
DEFAULT_TTL_SECONDS = 900


class LockBusy(Exception):
    """Another live runner holds the profile. Not an error to retry blindly."""


class ProfileLock:
    def __init__(self, profile_dir: Path, *, ttl_seconds: int = DEFAULT_TTL_SECONDS):
        self.profile_dir = Path(profile_dir)
        self.path = self.profile_dir.parent / "runner.lock"
        self.ttl = ttl_seconds
        self._held = False

    # -- inspection ----------------------------------------------------------

    def _read(self) -> dict | None:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def _expired(self, data: dict) -> bool:
        try:
            beat = datetime.fromisoformat(data["heartbeat"])
        except (KeyError, ValueError):
            return True
        return datetime.now(timezone.utc) - beat > timedelta(seconds=self.ttl)

    def holder(self) -> dict | None:
        """Who holds it, or None if free/stale."""
        data = self._read()
        if data is None or self._expired(data):
            return None
        return data

    # -- acquisition ---------------------------------------------------------

    def _payload(self) -> str:
        now = datetime.now(timezone.utc).isoformat()
        return json.dumps(
            {"pid": os.getpid(), "acquired": now, "heartbeat": now,
             "profile": str(self.profile_dir)},
            indent=2,
        )

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            data = self._read()
            if data is not None and not self._expired(data):
                raise LockBusy(
                    f"another runner (pid {data.get('pid')}, last heartbeat "
                    f"{data.get('heartbeat')}) is using this browser profile. "
                    f"Stop it, or wait for its lease to lapse."
                ) from None
            # Stale: steal it, but say so. A silent steal hides a crash.
            stale_pid = (data or {}).get("pid", "unknown")
            print(f"  stealing stale profile lock from pid {stale_pid} "
                  f"(no heartbeat for >{self.ttl}s)")
            self.path.write_text(self._payload(), encoding="utf-8")
            self._held = True
            return

        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(self._payload())
        self._held = True

    def refresh(self) -> None:
        """Prove liveness. Called each loop iteration."""
        if not self._held:
            return
        data = self._read() or {}
        data["heartbeat"] = datetime.now(timezone.utc).isoformat()
        data.setdefault("pid", os.getpid())
        try:
            self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except OSError:
            pass  # a missed heartbeat costs a stolen lease, never correctness

    def release(self) -> None:
        if not self._held:
            return
        self.path.unlink(missing_ok=True)
        self._held = False

    def force_release(self) -> dict | None:
        """Operator escape hatch. Returns whatever holder it displaced.

        A killed process cannot release its lock, and its heartbeat is fresh
        at the moment it dies -- so without this the next run is refused for
        the whole TTL. Over a multi-hour acquisition that turns every crash
        into fifteen minutes of dead time with no obvious remedy, which is a
        worse failure than the crash.

        Deliberately explicit rather than automatic: inferring liveness from a
        PID is unreliable on Windows (PIDs are recycled, and a signal-0 probe
        is not portable), and guessing wrong here means two browsers fighting
        over one profile. The operator knows whether the run is dead.
        """
        previous = self._read()
        self.path.unlink(missing_ok=True)
        self._held = False
        return previous


@contextmanager
def profile_lock(profile_dir: Path, *, ttl_seconds: int = DEFAULT_TTL_SECONDS
                 ) -> Iterator[ProfileLock]:
    lock = ProfileLock(profile_dir, ttl_seconds=ttl_seconds)
    lock.acquire()
    try:
        yield lock
    finally:
        lock.release()


__all__ = ["ProfileLock", "LockBusy", "profile_lock", "DEFAULT_TTL_SECONDS"]
