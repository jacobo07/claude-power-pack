#!/usr/bin/env python3
"""session-snapshot.py — Layer 3 of SESSION_SAFETY_CONTRACT.md.

Daily zip snapshot of ~/.claude/projects/ to
~/.claude/backups/projects-snapshot-<YYYYMMDD-HHmmss>.zip.

Contract §2 Layer 3: "Full snapshot of ~/.claude/projects/ to
~/.claude/backups/projects-snapshot-YYYY-MM-DD_HHmmss.zip. Retention:
14 days rolling. Idempotent: re-run on same day overwrites."

This script is the canonical implementation. Registered as a daily
Windows Scheduled Task by install-global.ps1 (or by the helper
register-snapshot-task.ps1).

Resource governance (sealed 2026-05-22 after VIDEO_TDR_FAILURE BSOD
0x00000116 on the originating host — see vault/lessons/heavy-io-must-
be-governed.md):
  * SINGLE-INSTANCE LOCK — refuses to start if another instance holds
    the lock; prevents two snapshot runs from piling up on the same
    host and saturating disk + CPU.
  * IDLE PRIORITY — drops process priority to IDLE_PRIORITY_CLASS on
    Windows (and SCHED_IDLE on POSIX) so the snapshot yields to every
    interactive workload. A 60-second snapshot becomes invisible.
  * FAST-COMPRESS (level 1) — uses zlib level-1 compression instead of
    default 6. Empirically: ~3x faster (20-25s vs 57s for ~1.4GB
    source) at the cost of a ~10-15% larger zip (~430MB vs ~380MB).
    Layer 3 prioritizes "snapshot exists" over "snapshot is tightly
    compressed".
  * DISK-SPACE PRECHECK — refuses to start unless free space on the
    backup volume is at least 1.5x the (uncompressed) source size.
    Fail-fast prevents a partial zip from consuming the last gigabyte.

Opt-out: set CLAUDEPP_SNAPSHOT_DISABLE=1 in the environment that
runs the scheduled task — the script then exits 0 with a single
"DISABLED" line and no IO.

Modes:
  --dry-run   list what would be archived + the target path + the
              would-rotate list. Mutate nothing.
  (default)   write the zip, rotate older snapshots beyond N=14.

Exit codes:
  0 = success, OR opt-out, OR dry-run
  3 = source directory missing (~/.claude/projects/ absent — fresh
      install, nothing to snapshot)
  4 = another instance is already running (lock held)
  5 = IO error during zip write or rotation
  6 = disk-space precheck failed

Doctrine alignment:
  - Layer 3 is the LAST-RESORT defense. It runs unconditionally and
    independently of any agent. Even if every Layer 1+2 hook is
    disabled or buggy, this script keeps the user's data recoverable.
  - Idempotent same-day overwrite means a single day's recovery point
    is "the latest state at task-time today". 14-day rolling means
    the user can recover from a same-day corruption (yesterday's zip),
    a same-week pattern (3-7 days back), or a same-fortnight regression
    (8-14 days back).
"""
from __future__ import annotations

import os
import shutil
import sys
import time
import zipfile
from pathlib import Path


HOME = Path.home()
SOURCE = HOME / ".claude" / "projects"
BACKUP_ROOT = HOME / ".claude" / "backups"
LOCK_PATH = BACKUP_ROOT / ".session-snapshot.lock"
LOCK_STALE_SECONDS = 30 * 60  # any lock older than 30 min is presumed crashed
DISK_FREE_HEADROOM = 1.5  # need at least 1.5x source size free
RETENTION = 14  # rolling days
COMPRESS_LEVEL = 1  # 1 = fast, 6 = default, 9 = slow (was 6 pre-2026-05-22)
ZIP_PREFIX = "projects-snapshot-"
TODAY_STAMP = time.strftime("%Y-%m-%d")  # same-day collision key
FULL_STAMP = time.strftime("%Y-%m-%d_%H%M%S")


def _lower_priority() -> str:
    """Drop this process to IDLE priority so snapshot work yields to
    every interactive workload. Returns a verdict string for logging.

    Win32 ctypes signature note (sealed 2026-05-22 after empirical
    SetPriorityClass-failed regression during the post-BSOD hardening
    pass): GetCurrentProcess returns a HANDLE which is 64-bit on x64
    Windows; without explicit restype/argtypes, ctypes treats it as
    int (32-bit), truncating the pseudo-handle and SetPriorityClass
    returns FALSE. Declaring wintypes.HANDLE + wintypes.DWORD + BOOL
    fixes it. Silent failure here would defeat the entire hardening,
    so any failure path now reports the Win32 last-error code.
    """
    try:
        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes
            IDLE_PRIORITY_CLASS = 0x00000040
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel32.GetCurrentProcess.restype = wintypes.HANDLE
            kernel32.SetPriorityClass.argtypes = [wintypes.HANDLE,
                                                   wintypes.DWORD]
            kernel32.SetPriorityClass.restype = wintypes.BOOL
            handle = kernel32.GetCurrentProcess()
            if kernel32.SetPriorityClass(handle, IDLE_PRIORITY_CLASS):
                return "win32:IDLE_PRIORITY_CLASS"
            err = ctypes.get_last_error()
            return f"win32:SetPriorityClass-failed (GetLastError={err})"
        # POSIX: SCHED_IDLE if available, else os.nice(19)
        try:
            os.sched_setscheduler(0, os.SCHED_IDLE,  # type: ignore[attr-defined]
                                   os.sched_param(0))  # type: ignore[attr-defined]
            return "posix:SCHED_IDLE"
        except (AttributeError, OSError):
            os.nice(19)
            return "posix:nice(19)"
    except Exception as e:  # noqa: BLE001 — never break the snapshot
        return f"priority-noop: {e!r}"


def _pid_alive(pid: int) -> bool:
    """True if a process with this pid exists. Unknown -> True (keep)."""
    if pid <= 0:
        return False
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel32.OpenProcess.restype = wintypes.HANDLE
            kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL,
                                             wintypes.DWORD]
            kernel32.GetExitCodeProcess.argtypes = [
                wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
            kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
            handle = kernel32.OpenProcess(0x1000, False, pid)  # QUERY_LIMITED
            if not handle:
                # 87 = ERROR_INVALID_PARAMETER: no such pid. Anything else
                # (e.g. access denied) means it exists.
                return ctypes.get_last_error() != 87
            try:
                code = wintypes.DWORD()
                if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                    return True
                return code.value == 259  # STILL_ACTIVE
            finally:
                kernel32.CloseHandle(handle)
        except Exception:  # noqa: BLE001 — unknown liveness keeps the subject
            return True
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except OSError:
        return True


def _lock_owner_pid() -> int:
    try:
        for line in LOCK_PATH.read_text(encoding="utf-8").splitlines():
            if line.startswith("pid="):
                return int(line[4:])
    except (OSError, ValueError):
        pass
    return -1


def _acquire_lock() -> str:
    """Single-instance lock, created atomically (O_CREAT|O_EXCL).

    The previous exists()-then-write() check let bursts of concurrent
    Stop events all pass it: 3 writers were measured running at once on
    2026-10-01. A lock is stale only when its owner pid is dead, or when
    it is older than LOCK_STALE_SECONDS AND unreadable. A live owner
    always holds it, however slow its IDLE-priority run is.

    Returns "acquired" | "stale-reclaimed" | "held" | "error:<msg>"
    (error is fail-open: caller proceeds).
    """
    try:
        BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return f"error:{e}"
    for attempt in range(2):
        try:
            fd = os.open(str(LOCK_PATH), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            owner = _lock_owner_pid()
            if owner > 0:
                if _pid_alive(owner):
                    return "held"
            else:
                try:
                    age = time.time() - LOCK_PATH.stat().st_mtime
                except OSError:
                    continue  # vanished between open and stat -> retry
                if age < LOCK_STALE_SECONDS:
                    return "held"  # being written right now, or unreadable+fresh
            if attempt:
                return "held"
            try:
                LOCK_PATH.unlink()
            except OSError:
                pass
            continue
        except OSError as e:
            return f"error:{e}"
        host = os.environ.get('COMPUTERNAME', '?')
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(f"pid={os.getpid()}\nts={int(time.time())}\nhost={host}\n")
        return "stale-reclaimed" if attempt else "acquired"
    return "held"


def _release_lock() -> None:
    """Remove the lock only if this process owns it — an unconditional
    unlink let one run delete the lock another run was holding."""
    if _lock_owner_pid() != os.getpid():
        return
    try:
        LOCK_PATH.unlink()
    except OSError:
        pass


def _sweep_orphan_tmps(dry_run: bool) -> list[Path]:
    """Delete <prefix>*.zip.tmp.<pid> files whose writer is dead.

    A run killed mid-write (session end, reaper, BSOD) never reaches the
    tmp.unlink() in _write_zip, and _rotate only globs *.zip, so these were
    never collected: 132 of them = 198 GB on 2026-10-01. Called while
    holding the lock; a tmp whose pid is alive (or unknown) is kept.
    """
    victims = []
    for tmp in BACKUP_ROOT.glob(f"{ZIP_PREFIX}*.zip.tmp.*"):
        try:
            pid = int(tmp.name.rsplit(".", 1)[1])
        except ValueError:
            continue
        if pid == os.getpid() or _pid_alive(pid):
            continue
        victims.append(tmp)
        if not dry_run:
            try:
                tmp.unlink()
            except OSError as e:
                print(f"session-snapshot: failed to sweep {tmp.name}: {e}",
                      file=sys.stderr)
    return victims


def _enumerate_source() -> tuple[int, int]:
    """Return (file_count, total_bytes) of SOURCE/**. Cheap pre-flight
    so the report can show what's being archived without re-walking."""
    count = 0
    size = 0
    for p in SOURCE.rglob("*"):
        if p.is_file():
            count += 1
            try:
                size += p.stat().st_size
            except OSError:
                pass
    return count, size


def _disk_space_check(source_bytes: int) -> tuple[bool, str]:
    """Verify the backup volume has at least DISK_FREE_HEADROOM x
    source_bytes free. Returns (ok, message)."""
    try:
        usage = shutil.disk_usage(str(BACKUP_ROOT))
    except OSError as e:
        return (True, f"disk-check-noop ({e}); proceeding")
    needed = int(source_bytes * DISK_FREE_HEADROOM)
    free_mib = usage.free / 1024 / 1024
    needed_mib = needed / 1024 / 1024
    if usage.free >= needed:
        return (True, f"disk OK: {free_mib:.0f} MiB free, "
                       f"need ~{needed_mib:.0f} MiB ({DISK_FREE_HEADROOM}x source)")
    return (False, f"disk LOW: {free_mib:.0f} MiB free, "
                    f"need ~{needed_mib:.0f} MiB ({DISK_FREE_HEADROOM}x source)")


def _today_target() -> Path:
    """Same-day collision: the most-recent zip whose name starts with
    today's date IS the same-day file. Re-running on the same day
    overwrites it (contract §2 Layer 3 — idempotent)."""
    same_day = sorted(
        BACKUP_ROOT.glob(f"{ZIP_PREFIX}{TODAY_STAMP}_*.zip"),
        key=lambda p: p.stat().st_mtime if p.exists() else 0,
    )
    if same_day:
        return same_day[-1]
    return BACKUP_ROOT / f"{ZIP_PREFIX}{FULL_STAMP}.zip"


def _existing_snapshots() -> list[Path]:
    """All existing snapshot zips, sorted oldest-first."""
    if not BACKUP_ROOT.is_dir():
        return []
    return sorted(
        BACKUP_ROOT.glob(f"{ZIP_PREFIX}*.zip"),
        key=lambda p: p.stat().st_mtime if p.exists() else 0,
    )


def _rotate(existing: list[Path], dry_run: bool) -> list[Path]:
    """Keep at most RETENTION zips. Return list of deletion victims."""
    if len(existing) <= RETENTION:
        return []
    victims = existing[: len(existing) - RETENTION]
    if dry_run:
        return victims
    for v in victims:
        try:
            v.unlink()
        except OSError as e:
            print(f"session-snapshot: failed to rotate {v.name}: {e}",
                  file=sys.stderr)
    return victims


def _write_zip(target: Path, dry_run: bool) -> int:
    """Write the snapshot zip atomically. Returns bytes written or -1."""
    if dry_run:
        return 0
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + f".tmp.{os.getpid()}")
    try:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED,
                              compresslevel=COMPRESS_LEVEL) as zf:
            for path in SOURCE.rglob("*"):
                if not path.is_file():
                    continue
                try:
                    arcname = path.relative_to(HOME / ".claude")
                except ValueError:
                    arcname = path.name
                try:
                    zf.write(path, arcname=str(arcname))
                except OSError as e:
                    print(f"session-snapshot: skip {path.name}: {e}",
                          file=sys.stderr)
        os.replace(tmp, target)
        return target.stat().st_size
    except OSError as e:
        print(f"session-snapshot: zip write failed: {e}", file=sys.stderr)
        try:
            tmp.unlink()
        except OSError:
            pass
        return -1


def main(argv: list[str]) -> int:
    dry_run = "--dry-run" in argv

    if os.environ.get("CLAUDEPP_SNAPSHOT_DISABLE") == "1":
        print("session-snapshot: DISABLED (CLAUDEPP_SNAPSHOT_DISABLE=1)")
        return 0

    if not SOURCE.is_dir():
        print(f"session-snapshot: source missing ({SOURCE}) — nothing to "
              f"archive, exiting 3", file=sys.stderr)
        return 3

    # Resource governance — happens BEFORE any heavy work.
    priority_verdict = _lower_priority()
    print(f"session-snapshot: priority   {priority_verdict}")

    if not dry_run:
        lock_verdict = _acquire_lock()
        print(f"session-snapshot: lock       {lock_verdict}")
        if lock_verdict == "held":
            print("session-snapshot: another instance is running — "
                  "refusing to pile up. Exit 4.", file=sys.stderr)
            return 4
    else:
        print("session-snapshot: lock       skipped (dry-run)")

    try:
        swept = _sweep_orphan_tmps(dry_run=dry_run)
        if swept:
            print(f"session-snapshot: {'would sweep' if dry_run else 'swept'}"
                  f"      {len(swept)} orphan .zip.tmp file(s)")
        file_count, total_bytes = _enumerate_source()
        target = _today_target()
        existing = _existing_snapshots()
        victims = _rotate(existing, dry_run=True)  # preview rotation

        # Disk-space precheck.
        space_ok, space_msg = _disk_space_check(total_bytes)
        print(f"session-snapshot: {space_msg}")
        if not space_ok:
            print("session-snapshot: aborting — refuse to write "
                  "snapshot with insufficient headroom. Exit 6.",
                  file=sys.stderr)
            return 6

        print(f"session-snapshot: source     {SOURCE}")
        print(f"session-snapshot: files      {file_count} "
              f"({total_bytes/1024/1024:.1f} MiB uncompressed)")
        print(f"session-snapshot: target     {target.name}"
              + (" (overwrites today's existing zip)"
                 if target.exists() else ""))
        print(f"session-snapshot: existing   {len(existing)} zips "
              f"(retention {RETENTION})")
        if victims:
            print(f"session-snapshot: rotating  {len(victims)} oldest zip(s):")
            for v in victims:
                print(f"  - {v.name}")

        if dry_run:
            print("session-snapshot: DRY-RUN — no zip written, no rotation done.")
            return 0

        bytes_out = _write_zip(target, dry_run=False)
        if bytes_out < 0:
            return 5
        print(f"session-snapshot: wrote      {target} "
              f"({bytes_out/1024/1024:.1f} MiB, "
              f"compress-level {COMPRESS_LEVEL})")
        _rotate(existing, dry_run=False)
        print("session-snapshot: OK")
        return 0
    finally:
        if not dry_run:
            _release_lock()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
