#!/usr/bin/env python3
"""hibernate_runner.py -- FASE A hibernation executor (store -> flag -> kill).

Given a hibernate target chosen by process_governor, this performs the actual
economy in the ONE safe order, extending CO-07's store-then-destroy discipline to
the OS process layer:

  1. CO-07 hibernation.hibernate(sid, cwd)  -- freeze + compress + store + VERIFY
     the context archive. If it REFUSES (missing anchor / store failed) -> ABORT,
     the process is NEVER touched (the pane stays alive, fail-open).
  2. Write the wake FLAG the kclaude wrapper reads, keyed by the wrapper's pid:
        %TEMP%\\claude-hibernate-<wrapper_pid>.flag   (JSON: sid, cwd, ts, archive)
     The flag MUST exist before the kill: the wrapper's blocking `& claude`
     returns the instant the process dies and immediately looks for the flag.
  3. Kill the claude.exe process (reclaim its working set). If the kill FAILS,
     the flag is rolled back so the wrapper never parks on a still-alive claude.

The kill and the flag write are INJECTABLE (kill_fn / flag_dir) so the whole
runner is unit-testable with zero real process/TEMP side effects.

Rehydration + acceptance is the wrapper's + G4's job (see kclaude.ps1 park-and-
resume and modules.session_resilience.acceptance). This module only performs the
sleep half; it never resurrects.
"""
from __future__ import annotations

import json
import os
import signal
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

FLAG_PREFIX = "claude-hibernate-"
FLAG_SUFFIX = ".flag"


@dataclass
class HibernateRun:
    ok: bool
    verdict: str                   # HIBERNATED | REFUSED | KILL_FAILED
    reason: str
    pid: int
    wrapper_pid: int
    sid: str | None = None
    archive_id: str | None = None
    killed: bool = False
    reclaim_mb: float = 0.0
    flag_path: str | None = None


def flag_path_for(wrapper_pid: int, flag_dir) -> Path:
    """The canonical wake-flag path for a wrapper pid. Single source of truth
    shared (by string contract) with kclaude.ps1's ReadKey park."""
    return Path(flag_dir) / f"{FLAG_PREFIX}{wrapper_pid}{FLAG_SUFFIX}"


def _default_kill(pid: int) -> bool:
    """Terminate a pid. On Windows os.kill(pid, SIGTERM) calls TerminateProcess.
    Returns True on a clean terminate, False on any failure (fail-open upstream)."""
    try:
        os.kill(pid, getattr(signal, "SIGTERM", 15))
        return True
    except (OSError, ValueError, ProcessLookupError):
        return False


def hibernate_pane(pane, *, flag_dir, hibernate_fn=None, kill_fn=None,
                   now: datetime | None = None) -> HibernateRun:
    """Execute hibernation for one governor-chosen pane. ``pane`` is a
    process_governor.PaneProc (or any object with the same attributes).

    Order is load-bearing: store+verify -> flag -> kill -> (rollback flag on
    kill failure). Fail-open: any pre-kill failure leaves the process alive."""
    now = now or datetime.now(timezone.utc)
    pid = int(pane.pid)
    wrapper_pid = int(pane.wrapper_pid)
    sid = pane.sid
    cwd = pane.cwd
    transcript = getattr(pane, "transcript_path", None)

    # 1. CO-07 store-and-verify BEFORE any destructive step.
    if hibernate_fn is None:
        from modules.cognitive_os import hibernation
        hibernate_fn = hibernation.hibernate
    hr = hibernate_fn(sid, cwd, transcript_path=transcript, now=now)
    if not getattr(hr, "ok", False):
        return HibernateRun(
            False, "REFUSED",
            f"CO-07 refused ({getattr(hr, 'reason', 'unknown')}) -- process untouched",
            pid, wrapper_pid, sid, killed=False)
    archive_id = getattr(hr, "archive_id", None)

    # 2. Write the wake flag BEFORE the kill (the wrapper looks for it on exit).
    flag = flag_path_for(wrapper_pid, flag_dir)
    payload = {"sid": sid, "cwd": cwd, "archive_id": archive_id,
               "pid": pid, "ts": now.isoformat()}
    try:
        flag.parent.mkdir(parents=True, exist_ok=True)
        # newline="" so Windows text-mode never rewrites the JSON on later reads.
        with flag.open("w", encoding="utf-8", newline="") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False))
    except OSError as exc:
        return HibernateRun(
            False, "REFUSED", f"flag write failed ({exc}) -- process untouched",
            pid, wrapper_pid, sid, archive_id, killed=False)

    # 3. Kill. On failure, roll the flag back so no stale flag traps the wrapper.
    killer = kill_fn or _default_kill
    if not killer(pid):
        try:
            flag.unlink()
        except OSError:
            pass
        return HibernateRun(
            False, "KILL_FAILED",
            "process kill failed -- flag rolled back, pane stays alive",
            pid, wrapper_pid, sid, archive_id, killed=False,
            flag_path=str(flag))

    return HibernateRun(
        True, "HIBERNATED",
        f"stored ({archive_id}) + flag armed + process killed", pid, wrapper_pid,
        sid, archive_id, killed=True, reclaim_mb=float(getattr(pane, "ws_mb", 0.0)),
        flag_path=str(flag))


def run_plan(gp, *, flag_dir, hibernate_fn=None, kill_fn=None,
             now: datetime | None = None) -> list:
    """Execute every HIBERNATE target in a GovernorPlan. Returns the runs."""
    runs = []
    for d in gp.hibernate_targets():
        runs.append(hibernate_pane(d.pane, flag_dir=flag_dir,
                                   hibernate_fn=hibernate_fn, kill_fn=kill_fn,
                                   now=now))
    return runs


def main(argv=None) -> int:  # pragma: no cover - thin CLI; live kill is Windows glue
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--flag-dir", default=os.environ.get("TEMP", "."))
    ap.add_argument("--dry-run", action="store_true",
                    help="never kill; report what would happen")
    ap.add_argument("--panes-json", default=None)
    args = ap.parse_args(argv)
    from modules.cognitive_os import process_governor as pg
    panes = []
    if args.panes_json and Path(args.panes_json).is_file():
        raw = json.loads(Path(args.panes_json).read_text(encoding="utf-8-sig"))
        for r in raw:
            panes.append(pg.PaneProc(
                pid=int(r.get("pid", 0)), wrapper_pid=int(r.get("wrapper_pid", 0)),
                sid=r.get("sid"), cwd=r.get("cwd"), ws_mb=float(r.get("ws_mb", 0.0)),
                idle_min=r.get("idle_min"),
                is_foreground=bool(r.get("is_foreground", False)),
                is_loop=bool(r.get("is_loop", False)),
                wrapper_kind=r.get("wrapper_kind", "none"),
                has_anchor=bool(r.get("has_anchor", True)),
                transcript_path=r.get("transcript_path")))
    gp = pg.plan(panes)
    kill = (lambda _pid: True) if args.dry_run else None
    runs = run_plan(gp, flag_dir=args.flag_dir, kill_fn=kill)
    for rn in runs:
        print(f"{rn.verdict:12} pid={rn.pid} sid={(rn.sid or '?')[:8]} "
              f"killed={rn.killed} {rn.reason}")
    print(f"# {sum(1 for r in runs if r.ok)}/{len(runs)} hibernated "
          f"(dry_run={args.dry_run})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
