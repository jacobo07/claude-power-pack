#!/usr/bin/env python
"""gsd_mission -- the mission outlives the session (spec vault/specs/mission-continuity.md).

Until now a long run's only record was ``gsd-autorun-<session_id>.json``: the run
was keyed by the session executing it, so the run died with that session and a
run that was armed and never started looked exactly like a healthy one (measured
2026-09-23: 9 of 9 armed markers on this host at NO_CROSSINGS, 21 ``armed`` rows
against one hand-written ``started``).

This module owns the record ABOVE the session:

  * ``gsd-mission-<mission_id>.json`` -- cwd, resume command, budget, ``state``,
    ``epoch``, ``owner`` (the session currently holding the lease) and ``pending``
    (the one transition we are waiting to see acknowledged, with its deadline);
  * every change is a compare-and-swap on ``epoch`` + ``state`` under an O_EXCL
    lock, so two supervisors racing to replace the same dead worker produce one
    replacement and one refusal, never two workers;
  * ``PREPARED`` is not ``RUNNING``: only an acknowledgement from the launched
    session itself moves the mission to ``RUNNING``;
  * liveness is three-valued plus BLOCKED. ``DEAD`` needs positive evidence
    (the host no longer lists the session AND its recorded process is gone or was
    replaced by another process with the same pid); anything else is ``UNKNOWN``,
    and ``UNKNOWN`` never licenses a replacement.

The decision function ``plan_next`` is pure: it takes the record, the clock and
the host's session list, and returns what the supervisor should do and why.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_long_run as lr  # noqa: E402  (state_dir, ledger, _pid_alive, sessions_dir)

SCHEMA_VERSION = 1
MISSION_TEMPLATE = "gsd-mission-{mission_id}.json"
_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")

# Lifecycle. Terminal states carry no owner obligation.
PREPARED = "PREPARED"            # record exists, nothing launched
LAUNCHING = "LAUNCHING"          # a worker was requested; waiting for ITS ack
RUNNING = "RUNNING"              # the owner acknowledged; heartbeats expected
HANDOFF = "HANDOFF_REQUESTED"    # owner hit the wall, finishing its atomic step
BLOCKED = "BLOCKED"              # owner alive but waiting on a human (permission prompt)
COMPLETED = "COMPLETED"
HALTED = "HALTED"                # budget / freshness / recovery attempts exhausted
ORPHANED = "ORPHANED"            # owner proven dead and replacement not allowed
TERMINAL = {COMPLETED, HALTED, ORPHANED}
STATES = {PREPARED, LAUNCHING, RUNNING, HANDOFF, BLOCKED} | TERMINAL

# Bounds. Each is the answer to "how long before silence becomes a finding".
START_DEADLINE_S = 300        # launch -> first ack from the launched session
HANDOFF_DEADLINE_S = 1800     # hand-off requested -> owner's turn ended
HEARTBEAT_STALE_S = 1800      # RUNNING with no heartbeat -> ask the host
MAX_REPLACEMENTS = 3          # consecutive unacknowledged launches before HALTED
# Hand-off wall, % of context used, in the watchdog's own vocabulary. The same narrowed wall
# /cpp-gsd-long has run on since v2 (crossing at 40 % used), so a worker hands off long
# before native compaction would fire.
DEFAULT_WALL = {"snapshot": 35.0, "advisory": 40.0, "rearm": 30.0}

LIVE = "ALIVE"
DEAD = "DEAD"
UNKNOWN = "UNKNOWN"
WAITING_HUMAN = "BLOCKED"


class MissionError(ValueError):
    pass


class CasConflict(MissionError):
    """The record moved between the caller's observation and its write."""


# --------------------------------------------------------------------------- storage
def mission_path(mission_id: str) -> Path:
    if not _ID_RE.match(mission_id or ""):
        raise MissionError(f"invalid mission id: {mission_id!r}")
    return lr.state_dir() / MISSION_TEMPLATE.format(mission_id=mission_id)


def load(mission_id: str) -> dict | None:
    """The record, or None when absent. A malformed record RAISES: an unreadable
    mission is not an absent one, and treating it as absent would let a
    supervisor launch a second worker for a mission that is running."""
    path = mission_path(mission_id)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("state") not in STATES:
        raise MissionError(f"malformed mission record {path.name}")
    return data


def _write(path: Path, data: dict) -> None:
    tmp = path.with_suffix(f".json.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(tmp, path)


class _Lock:
    """O_EXCL lock file. A stale lock (holder gone for > stale_s) is reclaimed."""

    def __init__(self, path: Path, timeout_s: float = 10.0, stale_s: float = 60.0):
        self.path, self.timeout_s, self.stale_s = path, timeout_s, stale_s

    def __enter__(self):
        deadline = time.time() + self.timeout_s
        while True:
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                return self
            except FileExistsError:
                try:
                    if time.time() - self.path.stat().st_mtime > self.stale_s:
                        self.path.unlink(missing_ok=True)
                        continue
                except OSError:
                    continue
                if time.time() > deadline:
                    raise MissionError(f"lock busy: {self.path.name}")
                time.sleep(0.05)

    def __exit__(self, *exc):
        self.path.unlink(missing_ok=True)


def create(cwd: str, resume_command: str, *, mission_id: str | None = None,
           workstream: str | None = None, mission_terms=None,
           max_cycles: int | None = None, max_hours: float | None = None,
           mode: str = "ralph", now: float | None = None) -> dict:
    """A PREPARED mission. Refuses to overwrite an existing, non-terminal one."""
    now = time.time() if now is None else now
    mid = mission_id or f"m-{uuid.uuid4().hex[:12]}"
    path = mission_path(mid)
    with _Lock(path.with_suffix(".lock")):
        if path.exists():
            existing = load(mid)
            if existing and existing["state"] not in TERMINAL:
                raise MissionError(f"mission {mid} already {existing['state']}")
        rec = {
            "schema_version": SCHEMA_VERSION, "mission_id": mid, "mode": mode,
            "cwd": str(Path(cwd).resolve()) if cwd else "",
            "resume_command": resume_command, "workstream": workstream,
            "mission_terms": list(mission_terms or []),
            "max_cycles": max_cycles, "max_hours": max_hours,
            "state": PREPARED, "epoch": 0, "owner": None, "pending": None,
            "iterations": 0, "failed_launches": 0, "note": "",
            "created_at": now, "updated_at": now, "last_progress_at": None,
        }
        _write(path, rec)
    lr.ledger_append(mid, "mission_prepared", mission_id=mid, cwd=rec["cwd"],
                     command=resume_command, mode=mode)
    return rec


def transition(mission_id: str, *, expect_epoch: int, expect_state, event: str,
               now: float | None = None, worker: str | None = None, **changes) -> dict:
    """Compare-and-swap. ``expect_state`` is one state or a set of them.

    Raises CasConflict when the record moved since the caller observed it. The
    caller's observation is the authorization; re-reading and proceeding anyway
    would authorize whatever arrived in between.

    ``worker`` names the session the event concerns, for the ledger only. (The
    ledger is keyed by its own ``session_id`` parameter, which here carries the
    mission id, so the worker cannot travel under that name.)
    """
    now = time.time() if now is None else now
    allowed = {expect_state} if isinstance(expect_state, str) else set(expect_state)
    path = mission_path(mission_id)
    with _Lock(path.with_suffix(".lock")):
        rec = load(mission_id)
        if rec is None:
            raise MissionError(f"no mission {mission_id}")
        if rec["epoch"] != expect_epoch or rec["state"] not in allowed:
            raise CasConflict(f"{mission_id}: expected epoch {expect_epoch} in {sorted(allowed)}, "
                              f"found epoch {rec['epoch']} {rec['state']}")
        new_state = changes.get("state", rec["state"])
        if new_state not in STATES:
            raise MissionError(f"unknown state {new_state!r}")
        rec.update(changes)
        rec["updated_at"] = now
        _write(path, rec)
    extra = {k: v for k, v in (("reason", changes.get("reason")), ("worker", worker)) if v}
    lr.ledger_append(mission_id, event, mission_id=mission_id, epoch=rec["epoch"],
                     state=rec["state"], **extra)
    return rec


def all_missions() -> list[dict]:
    out = []
    for p in sorted(lr.state_dir().glob(MISSION_TEMPLATE.format(mission_id="*"))):
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(rec, dict) and rec.get("state") in STATES:
            out.append(rec)
    return out


# --------------------------------------------------------------------------- liveness
def host_sessions(timeout_s: int = 90) -> list[dict] | None:
    """``claude agents --json``: every active session, interactive and background.

    None means the host could not be asked -- never "no sessions", which would
    read every owner as gone.
    """
    import subprocess
    exe = os.environ.get("CPP_CLAUDE_EXE") or "claude"
    try:
        r = subprocess.run([exe, "agents", "--json", "--all"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout_s)
    except Exception:
        return None
    if r.returncode != 0:
        return None
    try:
        data = json.loads(r.stdout)
    except Exception:
        return None
    return data if isinstance(data, list) else None


def _registry_proc(session_id: str) -> tuple[int | None, str | None]:
    root = lr.sessions_dir()
    try:
        for p in root.glob("*.json"):
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(d, dict) and d.get("sessionId") == session_id:
                return d.get("pid"), d.get("procStart")
    except OSError:
        pass
    return None, None


def liveness(owner: dict | None, sessions: list[dict] | None,
             pid_alive=lr._pid_alive) -> tuple[str, str]:
    """(verdict, evidence). DEAD only on positive evidence.

    * the host lists the session as live -> ALIVE, or BLOCKED when it is waiting
      on a human (``waitingFor``) -- a permission prompt is not a death;
    * the host lists it as stopped/done  -> DEAD (the host says so);
    * the host does not list it at all AND its recorded pid is gone, or the pid
      now belongs to a process that started at another time -> DEAD;
    * the host could not be asked, or the pid question could not be asked -> UNKNOWN.

    A BACKGROUND owner is judged by the host alone. Measured 2026-09-23 (W0, worker
    133c6f91): its process was killed mid-work and the host restarted it by itself
    ("automatically restarted after its process exited unexpectedly"), so a pid that is
    gone says nothing about whether the worker is gone. A replacement launched on that
    reading ran beside the revived worker and wrote a duplicate row.
    """
    if not owner or not owner.get("session_id"):
        return UNKNOWN, "no owner recorded"
    sid = owner["session_id"]
    if sessions is None:
        return UNKNOWN, "host session list unavailable"
    row = next((s for s in sessions if s.get("sessionId") == sid), None)
    if row is not None:
        state = row.get("state")
        if state in ("stopped", "done", "exited", "failed"):
            return DEAD, f"host lists session {state}"
        if row.get("waitingFor"):
            return WAITING_HUMAN, f"host: waiting for {row.get('waitingFor')}"
        return LIVE, f"host lists session {row.get('status') or state or 'active'}"
    if owner.get("kind") == "background":
        return UNKNOWN, "background worker not listed by host (host owns its restarts)"
    pid, proc_start = owner.get("pid"), owner.get("proc_start")
    if not isinstance(pid, int):
        return UNKNOWN, "not listed by host; no pid recorded"
    alive = pid_alive(pid)
    if alive is False:
        return DEAD, f"not listed by host; pid {pid} gone"
    if alive is None:
        return UNKNOWN, f"not listed by host; pid {pid} could not be checked"
    cur_pid, cur_start = _registry_proc(sid)
    if proc_start and cur_start and cur_start != proc_start:
        return DEAD, f"pid {pid} reused (procStart {cur_start} != {proc_start})"
    return UNKNOWN, f"not listed by host but pid {pid} is alive"


# --------------------------------------------------------------------------- decisions
def budget_exhausted(rec: dict, now: float) -> str | None:
    mc = rec.get("max_cycles") or lr.DEFAULT_MAX_CYCLES
    mh = rec.get("max_hours") or lr.DEFAULT_MAX_HOURS
    if rec.get("iterations", 0) >= mc:
        return f"iterations {rec['iterations']} >= max {mc}"
    if now - float(rec.get("created_at") or now) > mh * 3600:
        return f"older than {mh} h"
    return None


def plan_next(rec: dict, now: float, sessions: list[dict] | None,
              pid_alive=lr._pid_alive) -> dict:
    """What the out-of-band supervisor should do for this mission, and why.

    Actions: none · launch · replace · halt · surface_blocked · await.
    Pure: no I/O beyond the injected ``pid_alive``.
    """
    state = rec.get("state")
    if state in TERMINAL:
        return {"action": "none", "reason": f"terminal {state}"}
    spent = budget_exhausted(rec, now)
    if spent and state in (PREPARED, LAUNCHING, HANDOFF):
        return {"action": "halt", "reason": f"budget: {spent}"}
    pending = rec.get("pending") or {}
    if state == PREPARED:
        return {"action": "launch", "reason": "prepared, nothing launched"}
    if state == LAUNCHING:
        deadline = float(pending.get("deadline") or 0)
        if now <= deadline:
            return {"action": "await", "reason": f"start ack due in {int(deadline - now)} s"}
        if rec.get("failed_launches", 0) + 1 >= MAX_REPLACEMENTS:
            return {"action": "halt", "reason": f"{MAX_REPLACEMENTS} launches never acknowledged"}
        return {"action": "replace", "reason": "start ack overdue"}
    verdict, why = liveness(rec.get("owner"), sessions, pid_alive)
    if verdict == WAITING_HUMAN:
        return {"action": "surface_blocked", "reason": why}
    if state == HANDOFF:
        if verdict == DEAD:
            return {"action": "replace", "reason": f"hand-off owner gone: {why}"}
        if verdict == LIVE and owner_idle(rec.get("owner"), sessions):
            # The predecessor's turn has ended: it is idle by the host's own account,
            # so stopping it cannot cut a step in half. Relay now.
            return {"action": "relay", "reason": f"owner finished its step: {why}"}
        deadline = float(pending.get("deadline") or 0)
        if now > deadline:
            return {"action": "surface_blocked",
                    "reason": f"hand-off overdue and owner {verdict}: {why}"}
        return {"action": "await", "reason": f"owner finishing its step ({verdict})"}
    if state in (RUNNING, BLOCKED):
        if verdict == DEAD:
            if spent:
                return {"action": "halt", "reason": f"owner dead and budget: {spent}"}
            return {"action": "replace", "reason": f"owner dead: {why}"}
        if verdict == LIVE and state == BLOCKED:
            return {"action": "unblock", "reason": why}
        if verdict == LIVE and owner_idle(rec.get("owner"), sessions):
            # Ralph: a worker whose turn ended is finished, whatever it said. The
            # supervisor asks GSD first; only an incomplete mission is relayed.
            return {"action": "relay", "reason": f"owner's turn ended without completion: {why}"}
        return {"action": "none", "reason": f"owner {verdict}: {why}"}
    return {"action": "none", "reason": f"unhandled state {state}"}


# --------------------------------------------------------------------------- effects
BG_LINE_RE = re.compile(r"backgrounded\s*\W+\s*([0-9a-f]{8})\b")
CARD_MAX_BYTES = 8000            # claude-code-handoff measured ~9 KB SessionStart truncation
STOP_WAIT_S = 90                 # `claude stop` is asynchronous: the pid outlives the verb
AUTOCOMPACT_SAFETY_NET = "600k"  # native compaction only if the hand-off itself failed


def worker_argv(rec: dict, prompt: str) -> list[str]:
    """The launch command. `--bg` manages the session id (W0 E4) and does not inherit the
    launcher's environment (E3), so identity comes back on stdout (E5), nowhere else."""
    exe = os.environ.get("CPP_CLAUDE_EXE") or "claude"
    argv = [exe, "--bg", "-n", f"{rec['mission_id']}-e{rec['epoch']}",
            "--autocompact", rec.get("autocompact") or AUTOCOMPACT_SAFETY_NET]
    mode = rec.get("permission_mode")
    if mode:
        argv += ["--permission-mode", mode]
    for tool in rec.get("allowed_tools") or []:
        argv += ["--allowedTools", tool]
    return argv + [prompt]


def launch_worker(mission_id: str, *, expect_epoch: int, expect_state, reason: str,
                  runner=None, now: float | None = None) -> dict:
    """Claim the next epoch FIRST (CAS), then launch, then bind the host's answer.

    Claim-before-launch is what makes a duplicate supervisor harmless: the loser
    of the CAS launches nothing. The worker is bound only by the id the host
    printed for THIS launch; an unparseable answer leaves the mission LAUNCHING
    with no owner, and the start deadline turns that into a visible failure.
    """
    import subprocess
    now = time.time() if now is None else now
    rec = load(mission_id)
    if rec is None:
        raise MissionError(f"no mission {mission_id}")
    epoch = expect_epoch + 1
    failed = rec.get("failed_launches", 0) + (1 if rec.get("state") == LAUNCHING else 0)
    rec = transition(mission_id, expect_epoch=expect_epoch, expect_state=expect_state,
                     event="launch_claimed", now=now, state=LAUNCHING, epoch=epoch,
                     failed_launches=failed, reason=reason,
                     pending={"kind": "worker_start", "epoch": epoch,
                              "requested_at": now, "deadline": now + START_DEADLINE_S})
    prompt = rec["resume_command"]
    run = runner or (lambda argv, cwd: subprocess.run(
        argv, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=180))
    try:
        r = run(worker_argv(rec, prompt), rec["cwd"])
        out = (r.stdout or "") + "\n" + (r.stderr or "")
        rc = r.returncode
    except Exception as exc:  # the launch itself could not happen
        out, rc = f"{type(exc).__name__}: {exc}", None
    m = BG_LINE_RE.search(out)
    if rc != 0 or not m:
        lr.ledger_append(mission_id, "launch_failed", mission_id=mission_id, epoch=epoch, rc=rc,
                         detail=out.strip()[-300:])
        return {"ok": False, "epoch": epoch, "detail": out.strip()[-300:]}
    bg_id = m.group(1)
    rec = transition(mission_id, expect_epoch=epoch, expect_state=LAUNCHING, event="launched",
                     now=now, pending={**rec["pending"], "bg_id": bg_id})
    return {"ok": True, "epoch": epoch, "bg_id": bg_id}


def mission_for_session(session_id: str) -> dict | None:
    """The live mission this session owns, or is the pending worker of."""
    for rec in all_missions():
        if rec["state"] in TERMINAL:
            continue
        owner = rec.get("owner") or {}
        pend = rec.get("pending") or {}
        if owner.get("session_id") == session_id:
            return rec
        bg = pend.get("bg_id")
        if rec["state"] == LAUNCHING and bg and session_id.startswith(bg):
            return rec
    return None


def ack_session(session_id: str, *, pid: int | None = None, proc_start: str | None = None,
                now: float | None = None) -> dict | None:
    """Called from the worker's OWN hook. The pending worker becomes the owner (RUNNING);
    the current owner renews its heartbeat. Anyone else changes nothing."""
    now = time.time() if now is None else now
    rec = mission_for_session(session_id)
    if rec is None:
        return None
    try:
        if rec["state"] == LAUNCHING:
            return transition(rec["mission_id"], expect_epoch=rec["epoch"], expect_state=LAUNCHING,
                              event="worker_acked", now=now, state=RUNNING, pending=None,
                              failed_launches=0, iterations=rec.get("iterations", 0) + 1,
                              worker=session_id,
                              owner={"session_id": session_id, "pid": pid,
                                     "proc_start": proc_start, "heartbeat_at": now,
                                     "epoch": rec["epoch"], "kind": "background"})
        owner = dict(rec.get("owner") or {})
        owner["heartbeat_at"] = now
        return transition(rec["mission_id"], expect_epoch=rec["epoch"],
                          expect_state=rec["state"], event="heartbeat", now=now, owner=owner)
    except CasConflict:
        return None


def request_handoff(session_id: str, note: str, now: float | None = None) -> dict:
    """The owner hit its context wall: record what the successor must know, and
    wait for this turn to end. Only the owner may request it."""
    now = time.time() if now is None else now
    rec = mission_for_session(session_id)
    if rec is None or (rec.get("owner") or {}).get("session_id") != session_id:
        raise MissionError(f"session {session_id} owns no running mission")
    return transition(rec["mission_id"], expect_epoch=rec["epoch"], expect_state=RUNNING,
                      event="handoff_requested", now=now, state=HANDOFF,
                      note=(note or "").strip()[:2000],
                      pending={"kind": "handoff", "from": session_id,
                               "requested_at": now, "deadline": now + HANDOFF_DEADLINE_S})


def render_card(rec: dict, git_facts: dict | None = None, gsd_facts: str = "") -> str:
    """The rehydration card for a fresh worker. Mechanical sources only (the mission
    record, git, GSD); the predecessor's note is labelled as a claim, not a fact.
    Hard-capped: a card the host truncates silently is worse than a short one."""
    g = git_facts or {}
    parts = [
        f"MISSION CONTINUITY — you are worker epoch {rec['epoch']} of mission {rec['mission_id']}.",
        "You have no memory of earlier workers. Durable state is the repository and GSD, not this card.",
        f"Project: {rec['cwd']}",
        f"Resume command: {rec['resume_command']}",
        "",
        "RECONCILE BEFORE ACTING (run these first and say what you found):",
        "  git status --short ; git log --oneline -5 ; GSD progress for the active milestone",
        "If they contradict the note below, the repository wins.",
        "",
        f"HEAD at hand-off: {g.get('head') or 'unknown'}",
        f"Dirty paths at hand-off: {g.get('dirty') if g.get('dirty') is not None else 'unknown'}",
    ]
    if g.get("recent"):
        parts += ["Recent commits:"] + [f"  {c}" for c in g["recent"][:5]]
    if gsd_facts:
        parts += ["", "GSD:", gsd_facts[:1500]]
    note = (rec.get("note") or "").strip()
    parts += ["", "Predecessor's note (a claim to verify, not a fact):",
              note if note else "  (none — the predecessor did not hand off; reconstruct from git + GSD)"]
    card = "\n".join(parts)
    raw = card.encode("utf-8")
    if len(raw) > CARD_MAX_BYTES:
        card = raw[:CARD_MAX_BYTES - 40].decode("utf-8", errors="ignore") + "\n[card truncated at cap]"
    return card


def owner_idle(owner: dict | None, sessions: list[dict] | None) -> bool:
    """True only when the host lists the owner as idle: its turn has ended."""
    if not owner or sessions is None:
        return False
    row = next((s for s in sessions if s.get("sessionId") == owner.get("session_id")), None)
    if not row or row.get("waitingFor"):
        return False
    # W0: a background worker whose turn ended reads `status:"idle"` or, later,
    # `state:"blocked"` with no `waitingFor` (awaiting a message nobody will send).
    return row.get("status") == "idle" or (row.get("state") == "blocked" and not row.get("status"))


def _host_row(session_id: str, sessions: list[dict] | None) -> dict | None:
    return next((s for s in (sessions or []) if s.get("sessionId") == session_id), None)


def stop_owner(owner: dict | None, sessions: list[dict] | None, pid_alive=lr._pid_alive,
               runner=None, wait_s: float = STOP_WAIT_S) -> tuple[bool, str]:
    """Stop the predecessor and WAIT until its process is gone (W0: `claude stop` returns
    while the pid still lives). Only a background worker is stopped; an interactive pane
    is the Owner's and is left alone -- it simply no longer holds the lease."""
    import subprocess
    if not owner:
        return True, "no owner"
    row = _host_row(owner.get("session_id"), sessions)
    if row is None or row.get("state") in ("stopped", "done"):
        return True, "not running per host"
    if row.get("kind") != "background":
        return True, "interactive owner left running; lease moves"
    exe = os.environ.get("CPP_CLAUDE_EXE") or "claude"
    run = runner or (lambda argv: subprocess.run(argv, capture_output=True, text=True, timeout=120))
    run([exe, "stop", row.get("id") or owner["session_id"][:8]])
    pid = row.get("pid")
    deadline = time.time() + wait_s
    while isinstance(pid, int) and time.time() < deadline:
        if pid_alive(pid) is False:
            return True, f"stopped; pid {pid} gone"
        time.sleep(1)
    if isinstance(pid, int):
        return False, f"pid {pid} still alive after {int(wait_s)} s"
    return True, "stopped; no pid to wait on"


def supervise(now: float | None = None, dry_run: bool = False, sessions=None,
              gsd_status=None, runner=None, stop_runner=None, pid_alive=lr._pid_alive) -> list[dict]:
    """One out-of-band pass over every mission. Each action is ledgered by the
    transition it makes; a pass that decides nothing still returns one row per
    mission, so an empty estate and an unjudged one never look alike."""
    now = time.time() if now is None else now
    if sessions is None:
        sessions = host_sessions()
    out = []
    for rec in all_missions():
        mid = rec["mission_id"]
        plan = plan_next(rec, now, sessions, pid_alive)
        row = {"mission_id": mid, "state": rec["state"], "epoch": rec["epoch"], **plan}
        out.append(row)
        if dry_run or plan["action"] in ("none", "await"):
            continue
        try:
            act = plan["action"]
            if act == "halt":
                transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                           event="mission_halted", now=now, state=HALTED, pending=None,
                           reason=plan["reason"])
            elif act == "surface_blocked":
                if rec["state"] != BLOCKED:
                    transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                               event="mission_blocked", now=now, state=BLOCKED,
                               reason=plan["reason"])
            elif act == "unblock":
                transition(mid, expect_epoch=rec["epoch"], expect_state=BLOCKED,
                           event="mission_unblocked", now=now, state=RUNNING,
                           reason=plan["reason"])
            elif act in ("launch", "replace", "relay"):
                if act == "relay" and rec["resume_command"].startswith("/gsd-autonomous"):
                    st = (gsd_status or lr.gsd_status)(rec["cwd"], workstream=rec.get("workstream"))
                    row["gsd"] = st.get("outcome")
                    if st.get("outcome") == "ALL_COMPLETE":
                        transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                                   event="mission_completed", now=now, state=COMPLETED,
                                   pending=None, reason=st.get("reason"))
                        continue
                    if st.get("outcome") != "OK":
                        # Positive test: only "work remains" licenses a relay. UNAVAILABLE is
                        # an unanswered question and NO_PHASES a roadmap nobody can run.
                        row["held"] = f"gsd {st.get('outcome')}: {st.get('reason')}"
                        lr.ledger_append(mid, "relay_held", mission_id=mid, epoch=rec["epoch"],
                                         gsd=st.get("outcome"), reason=st.get("reason"))
                        continue
                if act == "relay":
                    ok, why = stop_owner(rec.get("owner"), sessions, pid_alive=pid_alive,
                                         runner=stop_runner)
                    row["stop"] = why
                    if not ok:
                        continue  # the next pass retries; nothing launched beside a live worker
                row["launch"] = launch_worker(mid, expect_epoch=rec["epoch"],
                                              expect_state=rec["state"], reason=plan["reason"],
                                              runner=runner, now=now)
        except CasConflict as exc:
            row["cas"] = str(exc)  # another supervisor acted first: correct, not an error
    return out


def arm(cwd: str, resume_command: str, *, launch: bool = True, **kw) -> dict:
    rec = create(cwd, resume_command, **kw)
    if not launch:
        return {"mission": rec}
    res = launch_worker(rec["mission_id"], expect_epoch=0, expect_state=PREPARED,
                        reason="armed")
    return {"mission": load(rec["mission_id"]), "launch": res}


def _git_facts(cwd: str) -> dict:
    import subprocess
    g = os.environ.get("CPP_GIT_EXE") or r"C:\Program Files\Git\cmd\git.exe"
    if not Path(g).exists():
        g = "git"
    facts = {}
    try:
        facts["head"] = subprocess.run([g, "-C", cwd, "rev-parse", "--short", "HEAD"],
                                       capture_output=True, text=True, timeout=20).stdout.strip() or None
        st = subprocess.run([g, "-C", cwd, "status", "--porcelain"], capture_output=True,
                            text=True, timeout=30).stdout
        facts["dirty"] = len([l for l in st.splitlines() if l.strip()])
        facts["recent"] = subprocess.run([g, "-C", cwd, "log", "--oneline", "-5"],
                                         capture_output=True, text=True,
                                         timeout=20).stdout.strip().splitlines()
    except Exception:
        pass
    return facts


def session_start(session_id: str, source: str = "") -> str:
    """SessionStart entry (called by hooks/session_start_hub.js). Acks the worker,
    arms its watchdog marker, and returns the card for a successor. Empty string for
    every session that is not a mission worker -- the ordinary path is unchanged."""
    rec = mission_for_session(session_id)
    if rec is None:
        return ""
    pid, proc_start = _registry_proc(session_id)
    first = rec["state"] == LAUNCHING
    rec = ack_session(session_id, pid=pid, proc_start=proc_start) or rec
    if first:
        _arm_worker_marker(rec, session_id)
    if rec["epoch"] <= 1 and not rec.get("note"):
        return ""
    return render_card(rec, _git_facts(rec["cwd"]))


def _arm_worker_marker(rec: dict, session_id: str) -> None:
    """The watchdog keys crossings on a per-session marker; the worker gets one that
    names its mission, so its wall produces a hand-off rather than a /compact."""
    import gsd_autorun_marker as mk
    path = mk.write_marker(session_id, rec["resume_command"], rec["cwd"],
                           max_cycles=rec.get("max_cycles"), max_hours=rec.get("max_hours"))
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update({"mission_id": rec["mission_id"], "epoch": rec["epoch"], "mode": rec.get("mode")})
    if rec.get("workstream"):
        data["workstream"] = rec["workstream"]
    # The watchdog reads the wall from the marker's `wall` key
    # (context-watchdog._thresholds_from_marker); any other key is silently ignored and
    # the worker would run on the production constants.
    data["wall"] = rec.get("wall") or dict(DEFAULT_WALL)
    mk._save(path, data)
    lr.ledger_append(session_id, "armed", command=rec["resume_command"], cwd=rec["cwd"],
                     mission_id=rec["mission_id"], epoch=rec["epoch"], via="mission")


def handoff_instruction(marker: dict, used_pct) -> str:
    sid = marker.get("session_id", "<sid>")
    return (
        f"CONTEXT WALL — {used_pct}% used. This mission continues in a FRESH session; this one "
        f"ends here (mission {marker.get('mission_id')}, epoch {marker.get('epoch')}). Do exactly this, "
        "then stop: (1) finish ONLY the atomic step in progress and commit it — start nothing new; "
        "(2) record the hand-off: `python \"%USERPROFILE%\\.claude\\skills\\claude-power-pack\\tools"
        f"\\gsd_mission.py\" handoff --session {sid} --note \"<next exact action; open facts the "
        "repository does not record>\"`; (3) end your response. Do NOT run /compact and do NOT "
        "re-issue the run command: the supervisor starts the next worker once this turn ends."
    )


def _cli(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="GSD mission (Ralph-style continuation)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("arm")
    a.add_argument("--cwd", required=True)
    a.add_argument("--command", required=True)
    a.add_argument("--workstream")
    a.add_argument("--max-cycles", type=int)
    a.add_argument("--max-hours", type=float)
    a.add_argument("--no-launch", action="store_true")
    s = sub.add_parser("session-start")
    s.add_argument("--session", required=True)
    s.add_argument("--source", default="")
    h = sub.add_parser("handoff")
    h.add_argument("--session", required=True)
    h.add_argument("--note", default="")
    v = sub.add_parser("supervise")
    v.add_argument("--dry-run", action="store_true")
    sub.add_parser("status")
    args = ap.parse_args(argv)
    if args.cmd == "arm":
        res = arm(args.cwd, args.command, launch=not args.no_launch, workstream=args.workstream,
                  max_cycles=args.max_cycles, max_hours=args.max_hours)
        print(json.dumps(res, indent=2))
        return 0 if args.no_launch or res.get("launch", {}).get("ok") else 1
    if args.cmd == "session-start":
        card = session_start(args.session, args.source)
        if card:
            sys.stdout.write(card)
        return 0
    if args.cmd == "handoff":
        rec = request_handoff(args.session, args.note)
        print(f"HANDOFF RECORDED mission={rec['mission_id']} epoch={rec['epoch']} -- end your turn now")
        return 0
    if args.cmd == "supervise":
        print(json.dumps(supervise(dry_run=args.dry_run), indent=2))
        return 0
    rows = []
    sessions = host_sessions()
    for m in all_missions():
        v_, why = liveness(m.get("owner"), sessions)
        rows.append({"mission_id": m["mission_id"], "state": m["state"], "epoch": m["epoch"],
                     "iterations": m.get("iterations"), "owner": (m.get("owner") or {}).get("session_id"),
                     "liveness": v_, "evidence": why, "pending": m.get("pending"),
                     "plan": plan_next(m, time.time(), sessions)})
    print(json.dumps(rows, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
