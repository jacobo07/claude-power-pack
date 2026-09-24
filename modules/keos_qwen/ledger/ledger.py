#!/usr/bin/env python3
"""The shared-account ledger for one local inference endpoint.

`keos-llm.service` is ONE resident process on a host measured carrying 15
production services, a Paper server, a KME drill, ~3.5 GB of free VRAM of 20,
and a disk at 93 percent that drains on its own. Two panes dispatching batches
at the same time saturate it and contaminate both runs without either knowing.

`providers/codex.py` in the goal-spine engine already paid for this exact shape
and this file reuses its four mechanisms rather than rediscovering them:

  * a kill switch in the ENVIRONMENT, for a caller that has not started yet
  * a kill switch as a FLAG FILE, because a running loop cannot be killed by an
    env var -- the flag stops it without a restart
  * a daily budget counted FROM THE LEDGER, not from a counter in memory that a
    second process cannot see
  * a cross-process LOCK whose holder is checked for liveness, so a crashed
    holder does not wedge the endpoint forever

The Owner's ceiling, authorised 2026-09-24: 200 invocations per UTC day.

One implementation, two callers. The Elixir provider shells out to this module
once per request rather than reimplementing the predicate, because two
implementations of one budget are two answers to "how many calls are left" and
whichever one you consult depends on who wrote the caller.

Every refusal carries its OWN reason. "Budget exhausted", "an operator disabled
this", "another process holds the endpoint" and "we are cooling down after a
failure" need four different reactions, and collapsing them tells the reader
something false about their own system.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ALLOW = "ALLOW"
DISABLED_ENV = "DISABLED_ENV"
DISABLED_FLAG = "DISABLED_FLAG"
BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
COOLDOWN = "COOLDOWN"
LOCK_HELD = "LOCK_HELD"

REFUSALS = (DISABLED_ENV, DISABLED_FLAG, BUDGET_EXHAUSTED, COOLDOWN, LOCK_HELD)
ALL = (ALLOW,) + REFUSALS

DISABLED_ENV_VAR = "KEOS_QWEN_DISABLED"
ROOT_ENV_VAR = "KEOS_QWEN_LEDGER_ROOT"
DEFAULT_ROOT = "/home/kobii/keos/ledger"
DEFAULT_DAILY_BUDGET = 200
LOCK_STALE_S = 900.0


class LedgerError(RuntimeError):
    """The ledger could not answer. Never collapsed into a refusal.

    "We could not read the ledger" and "the ledger says no" are different facts.
    Reading the first as the second would make an unreadable directory look like
    a spent budget, and send an operator to wait for midnight instead of to fix
    a permission.
    """


@dataclass(frozen=True)
class Decision:
    verdict: str
    reason: str
    used_today: int
    budget: int

    @property
    def allowed(self) -> bool:
        return self.verdict == ALLOW

    def to_dict(self) -> dict:
        return {"verdict": self.verdict, "reason": self.reason,
                "used_today": self.used_today, "budget": self.budget}


def root(explicit: str | None = None) -> Path:
    return Path(explicit or os.environ.get(ROOT_ENV_VAR) or DEFAULT_ROOT)


def _utc_day(ts: float | None = None) -> str:
    return datetime.fromtimestamp(ts if ts is not None else time.time(),
                                  tz=timezone.utc).strftime("%Y-%m-%d")


def _calls_path(r: Path) -> Path:
    return r / "calls.jsonl"


def _pid_alive(pid: int) -> bool:
    """Is the recorded lock holder still running?

    A lock with no liveness check is a lock that a crash converts into a
    permanent outage, which is how a safety mechanism becomes the incident.

    The platform branch is NOT portability politeness. On Windows CPython
    implements `os.kill(pid, sig)` as `TerminateProcess(handle, sig)` for every
    signal except CTRL_C_EVENT and CTRL_BREAK_EVENT -- so the POSIX idiom
    `os.kill(pid, 0)`, which asks a question on Linux, KILLS THE PROCESS with
    exit code 0 on Windows. The ledger runs on Linux; its tests run on the
    Owner's Windows host, which is exactly where the idiom would have fired.
    Caught before the first run, 2026-09-24.
    """
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes

        # PROCESS_QUERY_LIMITED_INFORMATION: enough to ask, not enough to act.
        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if not handle:
            return False
        ctypes.windll.kernel32.CloseHandle(handle)
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # It exists and belongs to somebody else. Existing is the question.
        return True
    except OSError as exc:
        raise LedgerError(f"could not test liveness of pid {pid}: {exc}") from exc
    return True


def used_today(r: Path, day: str | None = None) -> int:
    """Calls recorded for the current UTC day.

    A malformed line is SKIPPED and does not raise: a truncated write from a
    killed process must not make the budget unreadable, and a ledger that cannot
    be read refuses everything. It is counted in `_malformed` for anyone who
    wants to know the file is damaged.
    """
    p = _calls_path(r)
    if not p.exists():
        return 0
    target = day or _utc_day()
    n = 0
    try:
        with p.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                if rec.get("day") == target:
                    n += 1
    except OSError as exc:
        raise LedgerError(f"could not read {p}: {exc}") from exc
    return n


def decide(ledger_root: str | None = None, budget: int = DEFAULT_DAILY_BUDGET,
           env: dict | None = None, now: float | None = None) -> Decision:
    """May a call to the shared endpoint proceed?

    Checked in the order a refusal is cheapest and most absolute. The env switch
    first because it needs no filesystem at all; the flag file second because it
    is the one that stops a loop already running; the lock last because it is the
    only one whose answer can change a second later.
    """
    environ = os.environ if env is None else env
    r = root(ledger_root)

    if str(environ.get(DISABLED_ENV_VAR, "")).strip().lower() in ("1", "true", "yes", "on"):
        return Decision(DISABLED_ENV, f"{DISABLED_ENV_VAR} is set", 0, budget)

    flag = r / "DISABLED"
    if flag.exists():
        try:
            why = flag.read_text(encoding="utf-8", errors="replace").strip()
        except OSError as exc:
            raise LedgerError(f"could not read the disable flag {flag}: {exc}") from exc
        return Decision(DISABLED_FLAG,
                        f"{flag} exists: {why or 'no reason recorded in the flag'}", 0, budget)

    cooldown = r / "cooldown"
    if cooldown.exists():
        try:
            until = float(cooldown.read_text(encoding="utf-8").strip() or 0)
        except (OSError, ValueError) as exc:
            raise LedgerError(f"could not read {cooldown}: {exc}") from exc
        t = now if now is not None else time.time()
        if t < until:
            return Decision(COOLDOWN, f"cooling down for another {until - t:.0f}s", 0, budget)

    n = used_today(r, _utc_day(now))
    if n >= budget:
        return Decision(BUDGET_EXHAUSTED,
                        f"{n} calls already made today; the Owner's ceiling is {budget}", n, budget)

    lock = r / "lock.json"
    if lock.exists():
        try:
            held = json.loads(lock.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            held = None
        if held:
            pid = int(held.get("pid", 0))
            age = (now if now is not None else time.time()) - float(held.get("ts", 0))
            if _pid_alive(pid) and age < LOCK_STALE_S:
                return Decision(LOCK_HELD,
                                f"pid {pid} has held the endpoint for {age:.0f}s", n, budget)

    return Decision(ALLOW, f"{n}/{budget} used today", n, budget)


def record(ledger_root: str | None = None, caller: str = "unknown",
           outcome: str = "OK", detail: str = "", now: float | None = None) -> dict:
    """Append one call to the ledger. Called AFTER the effect, never before.

    `outcome` is a member of the keos_qwen outcome vocabulary, so a call the
    endpoint never answered is counted as having been MADE (it consumed the
    endpoint's attention) while remaining unclassifiable as a model failure.
    Those are different questions and the ledger answers only the first.
    """
    r = root(ledger_root)
    try:
        r.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise LedgerError(f"could not create the ledger root {r}: {exc}") from exc

    t = now if now is not None else time.time()
    rec = {"ts": t, "day": _utc_day(t), "caller": caller,
           "outcome": outcome, "detail": detail[:500], "pid": os.getpid()}
    line = json.dumps(rec, ensure_ascii=True) + "\n"
    # O_APPEND with a single small write is atomic on Linux, which is where this
    # runs. Two panes appending concurrently interleave whole lines, never bytes.
    try:
        with _calls_path(r).open("a", encoding="utf-8") as fh:
            fh.write(line)
    except OSError as exc:
        raise LedgerError(f"could not append to {_calls_path(r)}: {exc}") from exc
    return rec


def main(argv=None) -> int:
    """CLI so the Elixir provider can consult the one implementation.

    Prints the decision as JSON on stdout. Exit 0 ALLOW, 3 refused, 4 the ledger
    itself could not answer -- three outcomes, because a caller that cannot tell
    "refused" from "broken" will retry the wrong one.
    """
    import argparse

    ap = argparse.ArgumentParser(description="KEOS-Qwen shared-endpoint ledger")
    ap.add_argument("action", choices=["decide", "record", "status"])
    ap.add_argument("--root", default=None)
    ap.add_argument("--budget", type=int, default=DEFAULT_DAILY_BUDGET)
    ap.add_argument("--caller", default="unknown")
    ap.add_argument("--outcome", default="OK")
    ap.add_argument("--detail", default="")
    args = ap.parse_args(argv)

    try:
        if args.action == "record":
            print(json.dumps(record(args.root, args.caller, args.outcome, args.detail)))
            return 0
        d = decide(args.root, args.budget)
        print(json.dumps(d.to_dict()))
        if args.action == "status":
            return 0
        return 0 if d.allowed else 3
    except LedgerError as exc:
        print(json.dumps({"verdict": "LEDGER_UNREADABLE", "reason": str(exc)}))
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
