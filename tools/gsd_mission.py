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


def _code_id() -> str:
    """Identity of the code that is DECIDING, taken at import. The sweep re-imports this file
    every pass and a repo edit is live on the next one (T6, 2026-09-28), so a ledger row that
    does not name its build cannot say which rules produced it."""
    import hashlib
    try:
        return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:12]
    except OSError:
        return "unknown"


CODE_ID = _code_id()
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
    if int(data.get("schema_version") or 1) > SCHEMA_VERSION:
        # Written by a NEWER build: its fields may mean things this code cannot know. Refuse
        # rather than misread and write it back in the old shape (T6 downgrade safety).
        raise MissionError(f"{path.name} has schema {data.get('schema_version')}, "
                           f"this build reads <= {SCHEMA_VERSION}")
    return data


def _write(path: Path, data: dict) -> None:
    """Crash boundary: before the rename the old record is intact; after it the new one is
    complete. The fsync is what makes "complete" true across a power loss or bugcheck -- this
    host's shutdowns are BSODs -- and a rename of unflushed bytes can land a zero-length file."""
    tmp = path.with_suffix(f".json.{os.getpid()}.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(data, indent=2))
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


class _Lock:
    """A kernel byte-range lock on a persistent file: the OS releases it when the holder's
    handle closes, INCLUDING when the holder is hard-killed. Nothing is ever reclaimed by age.

    Replaced 2026-09-27 (T3) an O_EXCL file reclaimed by mtime, measured both ways: a holder
    killed mid-transition blocked every writer for 60 s ("lock busy"), and a LIVE holder whose
    file merely looked old was unlinked under it -- two holders (debt L1). The file is never
    deleted, so there is no create/unlink race left to lose.
    """

    def __init__(self, path: Path, timeout_s: float = 10.0, stale_s: float | None = None):
        self.path, self.timeout_s = path, timeout_s   # stale_s: accepted, unused (no age rule)
        self.fd: int | None = None

    @staticmethod
    def _try(fd: int) -> bool:
        try:
            if sys.platform == "win32":
                import msvcrt
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except OSError:
            return False

    def __enter__(self):
        deadline = time.time() + self.timeout_s
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT)
        while not self._try(fd):
            if time.time() > deadline:
                os.close(fd)
                raise MissionError(f"lock busy: {self.path.name}")
            time.sleep(0.05)
        self.fd = fd
        return self

    def __exit__(self, *exc):
        fd, self.fd = self.fd, None
        if fd is None:
            return
        try:
            if sys.platform == "win32":
                import msvcrt
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        finally:
            os.close(fd)   # closing releases the lock on every platform regardless


_WS_FLAG = re.compile(r"(?:^|\s)--ws(?:=|\s+)(\S+)")


def bind_workstream(command: str, workstream: str | None) -> str:
    """The command a worker actually types, with the mission's workstream IN it.

    The record's `workstream` field is read only by the supervisor (GSD status, finish test).
    The worker's /gsd-* command resolves its roadmap from its own session pointer, which a
    fresh `claude --bg` session never has -- so a bare `/gsd-autonomous` ran the ROOT
    milestone. Measured 2026-09-25: m-1d270cd85220, armed --workstream luckyarena-lobby,
    spent its first worker re-verifying another track's P0-A phases 1-3 and parked on that
    track's Phase 4 question; zero Lobby work. Missions armed with an explicit `--ws` never
    did. A `--ws` naming a DIFFERENT workstream is a contradiction, not a preference."""
    if not workstream or not command.startswith("/gsd-"):
        return command
    m = _WS_FLAG.search(command)
    if m:
        if m.group(1) != workstream:
            raise MissionError(f"command names --ws {m.group(1)} but the mission's workstream "
                               f"is {workstream}")
        return command
    return f"{command} --ws {workstream}"


def create(cwd: str, resume_command: str, *, mission_id: str | None = None,
           workstream: str | None = None, mission_terms=None,
           max_cycles: int | None = None, max_hours: float | None = None,
           mode: str = "ralph", now: float | None = None,
           permission_mode: str | None = None, allowed_tools=None, add_dirs=None,
           wall: dict | None = None) -> dict:
    """A PREPARED mission. Refuses to overwrite an existing, non-terminal one."""
    now = time.time() if now is None else now
    resume_command = bind_workstream(resume_command, workstream)
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
            "state": PREPARED, "epoch": 0, "seq": 0, "owner": None, "pending": None,
            "iterations": 0, "failed_launches": 0, "note": "",
            "created_at": now, "updated_at": now, "last_progress_at": None,
            # How each worker is launched. None -> the host's own defaults for that setting.
            "permission_mode": permission_mode, "allowed_tools": list(allowed_tools or []),
            "add_dirs": [str(Path(d).resolve()) for d in (add_dirs or [])],
            "wall": wall or dict(DEFAULT_WALL),
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
        # Every committed transition has a number, so the ledger's copy of the history can be
        # checked for holes against the record (history_gaps). A record with no seq predates T4.
        rec["seq"] = int(rec.get("seq") or 0) + 1
        rec["code_id"] = CODE_ID
        _write(path, rec)
    extra = {k: v for k, v in (("reason", changes.get("reason")), ("worker", worker)) if v}
    lr.ledger_append(mission_id, event, mission_id=mission_id, epoch=rec["epoch"],
                     state=rec["state"], seq=rec["seq"], code=CODE_ID, **extra)
    return rec


def history_gaps(rec: dict, events: list[dict] | None = None) -> dict:
    """Does the ledger hold a row for every transition the record has committed?

    Numbering starts at 1 with the first transition after T4, for new and older records alike;
    an older record's earlier history carries no numbers and is unjudged, not missing."""
    events = lr.ledger_events(rec["mission_id"]) if events is None else events
    # Only a TRANSITION row witnesses a seq: it always carries `state`. Other rows may quote the
    # record's seq (gsd_epoch's launch_cause does) and would otherwise fill a real hole
    # (adversarial review F2, 2026-09-28).
    seen = sorted({int(e["seq"]) for e in events
                   if e.get("mission_id") == rec["mission_id"] and isinstance(e.get("seq"), int)
                   and "state" in e})
    top = int(rec.get("seq") or 0)
    if not top:
        return {"judged": False, "reason": "no numbered transition yet (T4)", "missing": []}
    missing = [s for s in range(1, top + 1) if s not in set(seen)]
    return {"judged": True, "record_seq": top, "ledger_max_seq": seen[-1] if seen else None,
            "missing": missing}


def _scan() -> tuple[list[dict], list[dict]]:
    """(readable records, unreadable ones). One enumeration, two answers, so nothing a
    reader cannot parse can fall out of the population unseen."""
    good, bad = [], []
    for p in sorted(lr.state_dir().glob(MISSION_TEMPLATE.format(mission_id="*"))):
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001 -- classified below, never dropped
            rec, why = None, f"{type(exc).__name__}: {exc}"
        else:
            try:  # a well-formed JSON of the wrong SHAPE must not take down the whole pass (F5)
                why = None if isinstance(rec, dict) and rec.get("state") in STATES else "not a mission record"
                if why is None and int(rec.get("schema_version") or 1) > SCHEMA_VERSION:
                    why = f"schema {rec.get('schema_version')} is newer than this build ({SCHEMA_VERSION})"
            except Exception as exc:  # noqa: BLE001 -- classified as unreadable, never dropped
                why = f"unclassifiable record: {type(exc).__name__}: {exc}"
        if why:
            try:
                st = p.stat()
                ident = f"{st.st_size}:{int(st.st_mtime)}"
            except OSError:
                ident = "?"
            bad.append({"mission_id": p.name[len("gsd-mission-"):-len(".json")], "path": str(p),
                        "error": why[:200], "file_state": ident})
        else:
            good.append(rec)
    return good, bad


def all_missions() -> list[dict]:
    return _scan()[0]


def unreadable_missions() -> list[dict]:
    """Records that exist and cannot be read. Measured 2026-09-27: all_missions skipped them
    silently, so a torn record took its mission out of supervise AND status while the worker
    ran on unsupervised. Never repaired automatically: nobody can know what state it held."""
    return _scan()[1]


def _unreadable_rows(bad: list[dict]) -> list[dict]:
    rows = []
    for b in bad:
        rows.append({"mission_id": b["mission_id"], "state": "UNREADABLE", "epoch": None,
                     "action": "surface_unreadable", "reason": b["error"], "path": b["path"]})
        seen = [e for e in lr.ledger_events(b["mission_id"])
                if e.get("event") == "record_unreadable" and e.get("file_state") == b["file_state"]]
        if not seen:  # once per distinct file state, not every 5-minute pass
            lr.ledger_append(b["mission_id"], "record_unreadable", mission_id=b["mission_id"],
                             path=b["path"], error=b["error"], file_state=b["file_state"])
    return rows


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
        row = launched_row(pending, sessions)
        if row is not None and row.get("state") not in ("stopped", "done", "exited", "failed"):
            # Second witness of the start. The worker's own SessionStart ack can race the
            # launcher writing `bg_id` (the host starts the worker while `claude --bg` is
            # still returning); the host listing THAT id -- the one it printed for this
            # launch -- is independent evidence the worker exists. Never "a new session".
            return {"action": "adopt", "reason": f"host lists launched worker {pending.get('bg_id')}"}
        if now <= deadline:
            return {"action": "await", "reason": f"start ack due in {int(deadline - now)} s"}
        if sessions is None:
            # Overdue, but the host could not be asked: the launched worker may be running
            # and simply unacknowledged (W0 E9 slow host + E20 hub never acking coincide under
            # starvation). UNKNOWN never replaces -- a replacement here runs BESIDE it.
            return {"action": "await", "reason": "start ack overdue but host unanswerable; "
                                                 "UNKNOWN never replaces"}
        if rec.get("failed_launches", 0) + 1 >= MAX_REPLACEMENTS:
            return {"action": "halt", "reason": f"{MAX_REPLACEMENTS} launches never acknowledged"}
        return {"action": "replace", "reason": "start ack overdue"}
    verdict, why = liveness(rec.get("owner"), sessions, pid_alive)
    if spent and state in (RUNNING, BLOCKED) and verdict in (UNKNOWN, WAITING_HUMAN):
        # The budget must bind when the owner can never become DEAD or idle: a background
        # worker the host forgot (reboot) stays UNKNOWN forever, and one parked on a prompt
        # stays BLOCKED forever. Only a LIVE, busy owner is let finish its turn first.
        return {"action": "halt", "reason": f"owner {verdict} and budget: {spent}"}
    if verdict == WAITING_HUMAN:
        return {"action": "surface_blocked", "reason": why}
    if verdict == UNKNOWN and state == RUNNING:
        owner = rec.get("owner") or {}
        seen = max(float(owner.get("heartbeat_at") or 0), float(rec.get("updated_at") or 0))
        if seen and now - seen > HEARTBEAT_STALE_S:
            # Not a death (UNKNOWN never replaces), but never silence either: make it visible.
            return {"action": "surface_blocked",
                    "reason": f"owner UNKNOWN for {int(now - seen)} s: {why}"}
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
            # supervisor asks GSD first; only an incomplete mission is relayed -- and never
            # past its budget, or a mission with no completion predicate relays forever.
            if spent:
                return {"action": "halt", "reason": f"turn ended and budget: {spent}"}
            return {"action": "relay", "reason": f"owner's turn ended without completion: {why}"}
        return {"action": "none", "reason": f"owner {verdict}: {why}"}
    return {"action": "none", "reason": f"unhandled state {state}"}


# --------------------------------------------------------------------------- effects
ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
IDLE_LAUNCH_MARK = "send a prompt to start"   # host's words for a worker that got no prompt
CARD_MAX_BYTES = 8000            # claude-code-handoff measured ~9 KB SessionStart truncation
STOP_WAIT_S = 90                 # `claude stop` is asynchronous: the pid outlives the verb
AUTOCOMPACT_SAFETY_NET = "600k"  # native compaction only if the hand-off itself failed


def worker_name(rec: dict) -> str:
    return f"{rec['mission_id']}-e{rec['epoch']}"


def parse_launch(out: str, name: str) -> tuple[str | None, bool]:
    """(bg_id, started_idle) from the launcher's stdout. The id is anchored to the name WE
    passed with -n, never to "an 8-hex word somewhere". W8 measured two shapes:
    `backgrounded · <id> · <name>` and `<id> · <name> (idle — send a prompt to start)`,
    both wrapped in ANSI colour codes."""
    text = ANSI_RE.sub("", out or "")
    m = re.search(rf"\b([0-9a-f]{{8}})\W+{re.escape(name)}\b", text)
    return (m.group(1) if m else None), IDLE_LAUNCH_MARK in text


MCP_VERDICT_MAX_AGE_S = 30 * 86400


def worker_mcp_verdict(now: float | None = None) -> str:
    """APPLY / KEEP / UNJUDGED / NONE from this host's probe (bin/worker_mcp_probe.sh). A missing,
    unreadable or stale verdict is NONE: absence of a measurement never strips a worker's tools."""
    now = time.time() if now is None else now
    try:
        d = json.loads((lr.state_dir() / "worker-mcp-probe.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "NONE"
    if not isinstance(d, dict) or now - float(d.get("measured_at") or 0) > MCP_VERDICT_MAX_AGE_S:
        return "NONE"
    return str(d.get("verdict") or "NONE")


def worker_argv(rec: dict, prompt: str) -> list[str]:
    """The launch command. `--bg` manages the session id (W0 E4) and does not inherit the
    launcher's environment (E3), so identity comes back on stdout (E5), nowhere else.

    ORDER IS LOAD-BEARING. `--add-dir <directories...>` and `--allowedTools <tools...>` are
    variadic: placed last, they swallowed the prompt as one more value and the worker
    started idle (W8, measured). So the variadic options come first and a non-variadic
    option (`--autocompact N`) sits between them and the prompt -- the exact shape W0
    launched successfully."""
    exe = os.environ.get("CPP_CLAUDE_EXE") or "claude"
    argv = [exe, "--bg", "-n", worker_name(rec)]
    # Owner-approved 2026-09-25: two BLOCKED missions (m-2b4b7a36b2c8, m-2be47a186897) were
    # both parked on an EnterWorktree permission prompt -- the card tells a worker to enter
    # the work tree, and an unattended worker cannot answer the prompt that follows. Only the
    # two worktree tools are pre-approved; everything else stays under the permission mode.
    # 2026-09-26 (m-0f1efe5e6174, Orca X P8 on GEX44): the worker's GSD verifier subagent parked
    # at "Do you want to create 02-VERIFICATION.md?" for 45+ min in auto mode, BLOCKED with the
    # phase's whole verdict computed and unwritten. GSD's own planning files are the mission's
    # bookkeeping, so edits under `.planning/` (relative to the worker's cwd) are pre-approved too.
    tools = list(dict.fromkeys([*(rec.get("allowed_tools") or []), "EnterWorktree", "ExitWorktree",
                                "Edit(.planning/**)"]))
    for tool in tools:
        argv += ["--allowedTools", tool]
    for d in rec.get("add_dirs") or []:
        argv += ["--add-dir", d]
    # A worker nobody watches must not be able to park on a question (Owner 2026-09-25).
    argv += ["--disallowedTools", "AskUserQuestion"]
    if worker_mcp_verdict() == "APPLY":
        # Measured, not assumed: only a fresh APPLY from tools/worker_mcp_probe.sh strips MCP.
        argv += ["--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}']
    mode = rec.get("permission_mode")
    if mode:
        argv += ["--permission-mode", mode]
    if rec.get("card"):
        # The card rides the launch itself. Measured W8: the worker's SessionStart hub never
        # completed in two of two launches (chain abandoned under starvation once, silent the
        # other), so a card delivered only by that hook would be lost. The launch argument has
        # no deadline and no hook between it and the model.
        argv += ["--append-system-prompt", rec["card"]]
    argv += ["--autocompact", rec.get("autocompact") or AUTOCOMPACT_SAFETY_NET]
    return argv + [prompt]


def launch_worker(mission_id: str, *, expect_epoch: int, expect_state, reason: str,
                  runner=None, now: float | None = None, note: str | None = None,
                  stop_runner=None, work_dir: str | None = None,
                  progress: dict | None = None, packet: dict | None = None) -> dict:
    """Claim the next epoch FIRST (CAS), then launch, then bind the host's answer.

    ``work_dir`` is where the predecessor actually worked (a git worktree of the project,
    see effective_workdir). The worker is still LAUNCHED in the mission's cwd -- workspace
    trust is exact-path (W0 E2), a fresh worktree path is never trusted -- and the card tells
    it where the work is.

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
    extra = {"note": note} if note is not None else {}
    if note is not None:
        # The packet travels with THIS hand-off's note and is cleared with it, never inherited.
        extra["packet"] = packet
    if work_dir:
        extra["work_dir"] = work_dir
    if progress is not None:
        extra["progress"] = progress
        if not rec.get("progress_origin") and progress.get("measured"):
            extra["progress_origin"] = progress["fp"]   # the tree this mission started from
    if note is not None or rec.get("card"):
        # Pre-render the successor's card NOW: this runs out of band with no deadline, and
        # the git facts are exactly those of the hand-off moment the card claims to show --
        # read where the work IS, not where the worker was launched.
        # Also when there is NO note but an older card exists: worker_argv passes rec["card"],
        # so skipping the render re-sent the PREVIOUS epoch's card. Measured 2026-09-25
        # (m-1d270cd85220): a replace from LAUNCHING (no owner -> no note) briefed epoch 4 as
        # "epoch 3" with a WORK TREE line the record had since corrected; the worker entered it.
        wd = work_dir or rec.get("work_dir") or rec["cwd"]
        extra["card"] = render_card({**rec, "epoch": expect_epoch + 1, "note": note or "",
                                     "packet": packet if note is not None else rec.get("packet"),
                                     "work_dir": wd}, _git_facts(wd), _plan_facts(wd, rec.get("workstream")))
    rec = transition(mission_id, expect_epoch=expect_epoch, expect_state=expect_state,
                     event="launch_claimed", now=now, state=LAUNCHING, epoch=epoch,
                     failed_launches=failed, reason=reason,
                     # The lease leaves the predecessor at the claim, not at the ack: while
                     # LAUNCHING, an old session starting again (host auto-restart, the Owner
                     # reopening it) must not be able to claim the new epoch.
                     owner=None, previous_owner=rec.get("owner"),
                     pending={"kind": "worker_start", "epoch": epoch,
                              "requested_at": now, "deadline": now + START_DEADLINE_S},
                     **extra)
    # Bound here too, not only at create: a record armed before bind_workstream existed still
    # carries the bare command, and its relay would put the successor on the root milestone.
    prompt = bind_workstream(rec["resume_command"], rec.get("workstream"))
    run = runner or (lambda argv, cwd: subprocess.run(
        argv, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=180))
    try:
        r = run(worker_argv(rec, prompt), rec["cwd"])
        out = (r.stdout or "") + "\n" + (r.stderr or "")
        rc = r.returncode
    except Exception as exc:  # the launch itself could not happen
        out, rc = f"{type(exc).__name__}: {exc}", None
    bg_id, started_idle = parse_launch(out, worker_name(rec))
    detail = ANSI_RE.sub("", out).strip()[-300:]
    if rc != 0 or not bg_id or started_idle:
        why = "worker started WITHOUT its prompt" if (bg_id and started_idle) else "launch refused"
        lr.ledger_append(mission_id, "launch_failed", mission_id=mission_id, epoch=epoch, rc=rc,
                         bg_id=bg_id, why=why, detail=detail)
        if bg_id and started_idle:
            # An idle worker is "armed but never started" in its purest form: stop it, so it
            # holds no RAM and can never be mistaken for the run.
            try:
                (stop_runner or (lambda a: subprocess.run(a, capture_output=True, timeout=120)))(
                    [os.environ.get("CPP_CLAUDE_EXE") or "claude", "stop", bg_id])
            except Exception:
                pass
        return {"ok": False, "epoch": epoch, "bg_id": bg_id, "why": why, "detail": detail}
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
        bg = pend.get("bg_id")
        if rec["state"] == LAUNCHING:
            # Only the worker the host printed for THIS launch; never a previous owner.
            if bg and session_id.startswith(bg):
                return rec
            continue
        if owner.get("session_id") == session_id:
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


def handoff_packet(session_id: str, specs: list[str], context: int = 30) -> tuple[dict | None, str]:
    """Build the hand-off's source packet from `PATH::ANCHOR` (the anchor's line with `context`
    lines either side) or `PATH:START-END` specs, rooted where the work IS (work_dir, else cwd).
    Returns (reference, "") or (None, why). Only a COMPLETE packet is attached: a partial one is
    exactly the evidence gap a successor would trust without knowing it."""
    rec = mission_for_session(session_id)
    if rec is None:
        return None, f"session {session_id} owns no mission"
    # Where this session is ACTUALLY working, from its own transcript -- the record's work_dir is
    # refreshed only at relay, so a worker that entered a worktree mid-epoch would otherwise get a
    # packet of the main checkout's stale bytes that still verifies OK against that same root
    # (red team R1, 2026-09-28).
    try:
        live = effective_workdir(session_id, rec["cwd"], rec.get("workstream"))
    except Exception:  # noqa: BLE001 -- a packet is an aid; fall back, never block the hand-off
        live = None
    root = live or rec.get("work_dir") or rec["cwd"]
    paths, selectors = [], []
    for spec in specs:
        if "::" in spec:
            path, anchor = spec.split("::", 1)
            sel = {"path": path, "anchor": anchor, "beforeLines": 0, "afterLines": 0}
            # The vendor refuses a context window that runs past either end of the file instead of
            # clipping it -- so the region most worth handing over (new code at the end of a file)
            # never attached. A unique anchor becomes a clipped line range here; a missing or
            # ambiguous one is left to the vendor, which names the gap.
            try:
                lines = (Path(root) / path).read_text(encoding="utf-8", errors="replace").splitlines()
                hits = [i + 1 for i, line in enumerate(lines) if anchor in line]
                if len(hits) == 1:
                    sel = {"path": path, "startLine": max(1, hits[0] - context),
                           "endLine": min(len(lines), hits[0] + context)}
            except OSError:
                pass
        else:
            m = re.match(r"^(.*):(\d+)-(\d+)$", spec)
            if not m:
                return None, f"unreadable packet spec {spec!r} (want PATH::ANCHOR or PATH:START-END)"
            path = m.group(1)
            sel = {"path": path, "startLine": int(m.group(2)), "endLine": int(m.group(3))}
        if path not in paths:
            paths.append(path)
        selectors.append(sel)
    try:
        import source_packet as sp
        ref = sp.persist(root, paths, selectors=selectors)
    except Exception as exc:
        return None, f"packet could not be built: {type(exc).__name__}: {exc}"
    if ref.get("verdict") != "COMPLETE":
        return None, f"packet is {ref.get('verdict')}: {'; '.join(ref.get('gaps') or [])[:400]}"
    return ref, ""


def request_handoff(session_id: str, note: str, now: float | None = None, packet: dict | None = None) -> dict:
    """The owner hit its context wall: record what the successor must know, and
    wait for this turn to end. Only the owner may request it."""
    now = time.time() if now is None else now
    rec = mission_for_session(session_id)
    if rec is None or (rec.get("owner") or {}).get("session_id") != session_id:
        raise MissionError(f"session {session_id} owns no running mission")
    return transition(rec["mission_id"], expect_epoch=rec["epoch"], expect_state=RUNNING,
                      event="handoff_requested", now=now, state=HANDOFF,
                      note=(note or "").strip()[:2000],
                      # Always written, so a packet from an earlier hand-off never rides along.
                      packet=packet,
                      pending={"kind": "handoff", "from": session_id,
                               "requested_at": now, "deadline": now + HANDOFF_DEADLINE_S})


def add_directive(mission_id: str, text: str, now: float | None = None) -> dict:
    """Record an Owner decision on the mission itself, so EVERY later card carries it -- a
    handoff note reaches one successor only, and needs a RUNNING owner to write it."""
    text = (text or "").strip()
    if not text:
        raise MissionError("empty directive")
    rec = load(mission_id)
    if rec is None:
        raise MissionError(f"no mission {mission_id}")
    if rec["state"] in TERMINAL:
        raise MissionError(f"{mission_id} is {rec['state']}; a directive cannot reach it")
    return transition(mission_id, expect_epoch=rec["epoch"], expect_state=rec["state"],
                      event="directive_added", now=now,
                      directives=[*(rec.get("directives") or []), text[:1000]])


# The autonomy gate's rubric and wake order live in ONE file, read by the classifier
# (modules/autonomy_gate), the Ralph Stop hook and this card, so the three cannot drift.
_RUBRIC_FILE = Path(__file__).resolve().parent.parent / "modules" / "autonomy_gate" / "rubric.json"
_RUBRIC_FALLBACK = ("DECISION GATE: stop only for a resource-blocked, irreversible, outward-facing or "
                    "pure-preference decision; decide everything else yourself and continue.")


def _autonomy_rubric() -> tuple[str, str]:
    try:
        r = json.loads(_RUBRIC_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return _RUBRIC_FALLBACK, ""
    rubric = r.get("rubric") if isinstance(r.get("rubric"), str) and r.get("rubric") else _RUBRIC_FALLBACK
    wake = r.get("wake_order") if isinstance(r.get("wake_order"), str) else ""
    return rubric, wake


def _packet_lines(ref) -> list[str]:
    """The hand-off's source packet as a REFERENCE (vault/experiments/exp-successor-packet-002:
    inlining would have truncated 28 of 32 real cards; a reference fits all of them and cost the
    same as no packet). Re-verified here, at render time: a packet whose bytes or sources moved
    is announced as stale, never presented as evidence. Any failure drops the block, never the
    card. Kill switch CPP_SOURCE_PACKET_CARD=off."""
    if not isinstance(ref, dict) or not ref.get("sha256"):
        return []
    if (os.environ.get("CPP_SOURCE_PACKET_CARD") or "").strip().lower() in ("off", "0", "false"):
        return []
    try:
        import source_packet as sp
        state, why = sp.verify(ref)
        if state == sp.OK:
            return ["", sp.card_reference(ref)]
        return ["", f"SOURCE PACKET from the hand-off is {state} ({why}): do not use it; read the files directly."]
    except Exception as exc:  # the card must never fail for a packet
        return ["", f"SOURCE PACKET from the hand-off could not be checked ({type(exc).__name__}): read the files directly."]


def render_card(rec: dict, git_facts: dict | None = None, gsd_facts: str = "") -> str:
    """The rehydration card for a fresh worker. Mechanical sources only (the mission
    record, git, GSD); the predecessor's note is labelled as a claim, not a fact.
    Hard-capped: a card the host truncates silently is worse than a short one."""
    g = git_facts or {}
    rubric, wake = _autonomy_rubric()
    parts = [
        f"MISSION CONTINUITY — you are worker epoch {rec['epoch']} of mission {rec['mission_id']}.",
        "You have no memory of earlier workers. Durable state is the repository and GSD, not this card.",
        f"Project: {rec['cwd']}",
        f"Resume command: {bind_workstream(rec['resume_command'], rec.get('workstream'))}",
        *([f"WORKSTREAM {rec['workstream']}: before any GSD step run `node "
           f"~/.claude/gsd-core/bin/gsd-tools.cjs query workstream.set {rec['workstream']} --raw "
           f"--cwd .` (session-local pointer; gsd_run calls do not forward --ws). The repo's ROOT "
           f"milestone belongs to another track -- never plan or execute it."]
          if rec.get("workstream") else []),
        "",
        # Owner decision 2026-09-25 (settings.json autoMode.allow entry): four workers sat for
        # hours on an AskUserQuestion / permission prompt nobody watching could answer.
        "UNATTENDED: nobody reads this session and nobody will answer a question or a prompt.",
        "  Never ask the Owner. When a choice is needed, take the option you would recommend",
        "  (the safest one that keeps the mission moving), record it as a decision with its",
        "  reason in the workstream STATE.md, and continue. If a step is genuinely impossible,",
        "  record why, move to the next runnable phase, and keep going.",
        "",
        # Unattended form of the autonomy gate: "ask" cannot reach anyone here, so a gated
        # decision is recorded and skipped, never acted on and never parked on.
        "For a decision the gate below reserves to the Owner: do NOT act on it. Record it in the",
        "  workstream STATE.md as OWNER DECISION NEEDED (the question, the options, your pick),",
        "  then continue with other runnable work.",
        rubric,
        *([wake] if wake else []),
        *(["", "OWNER DIRECTIVES (binding; they override the note below):"]
          + [f"  - {d}" for d in rec.get("directives") or []]
          if rec.get("directives") else []),
        "",
        "RECONCILE BEFORE ACTING (run these first and say what you found):",
        "  git status --short ; git log --oneline -5 ; GSD progress for the active milestone",
        "If they contradict the note below, the repository wins.",
        "",
        f"HEAD at hand-off: {g.get('head') or 'unknown'}",
        f"Dirty paths at hand-off: {g.get('dirty') if g.get('dirty') is not None else 'unknown'}",
    ]
    wd = rec.get("work_dir")
    if wd and os.path.normcase(str(wd)) != os.path.normcase(str(rec.get("cwd") or "")):
        # Measured M6 (2026-09-24): /gsd-autonomous moved into a git worktree and reset the main
        # checkout's planning files, so everything done lives THERE. A successor that starts in
        # the main checkout sees the old roadmap and redoes finished phases.
        parts[2:2] = [f"WORK TREE: the work is in {wd} -- enter it first (EnterWorktree path=\"{wd}\").",
                      "The main checkout below is only where you were launched; its .planning is stale."]
    if g.get("recent"):
        parts += ["Recent commits:"] + [f"  {c}" for c in g["recent"][:5]]
    if gsd_facts:
        parts += ["", "GSD:", gsd_facts[:1500]]
    parts += _packet_lines(rec.get("packet"))
    note = (rec.get("note") or "").strip()
    parts += ["", "Predecessor's note (a claim to verify, not a fact):",
              note if note else "  (none — the predecessor did not hand off; reconstruct from git + GSD)"]
    card = "\n".join(parts)
    raw = card.encode("utf-8")
    if len(raw) > CARD_MAX_BYTES:
        card = raw[:CARD_MAX_BYTES - 40].decode("utf-8", errors="ignore") + "\n[card truncated at cap]"
    return card


def _git_toplevel_and_common(path: str) -> tuple[str, str] | None:
    import subprocess
    g = os.environ.get("CPP_GIT_EXE") or r"C:\Program Files\Git\cmd\git.exe"
    if not Path(g).exists():
        g = "git"
    try:
        r = subprocess.run([g, "-C", path, "rev-parse", "--show-toplevel", "--git-common-dir"],
                           capture_output=True, text=True, timeout=20)
    except Exception:
        return None
    lines = [l.strip() for l in (r.stdout or "").splitlines() if l.strip()]
    if r.returncode != 0 or len(lines) != 2:
        return None
    top = Path(lines[0]).resolve()
    common = Path(lines[1])
    common = (common if common.is_absolute() else Path(path) / common).resolve()
    return os.path.normcase(str(top)), os.path.normcase(str(common))


def _mentions_workstream(line: str, workstream: str) -> bool:
    """Did the WORKER act on `workstream` in this line? Only its own (assistant) lines count:
    the launch arguments (`--ws <ws>`) and the card sit in every worker's transcript as user or
    system text, so counting them would call every worker on-mission."""
    if '"type":"assistant"' not in line and '"type": "assistant"' not in line:
        return False
    return any(tok in line for tok in (
        f"workstreams/{workstream}", f"workstreams\\\\{workstream}", f"workstreams\\{workstream}",
        f"--ws {workstream}", f"workstream.set {workstream}"))


def _worktree_carries_workstream(worktree: str, base_cwd: str, workstream: str) -> bool:
    """A worktree may carry a workstream mission only if it CONTAINS the base checkout's latest
    commit to `.planning/workstreams/<ws>`; otherwise following it regresses the roadmap.

    Measured 2026-09-25: a correctly bound worker placed in another track's worktree mentioned
    its workstream in its own tool calls (it ran workstream.set there), so a textual test alone
    cannot tell a wrong worktree from a right one. Ancestry can: gsd-p0a-autonomous (1ea3dc97)
    does not contain the Lobby roadmap commit 20561b15. Any git failure -> False (stay on the
    mission cwd, where the mission was armed)."""
    import subprocess
    g = os.environ.get("CPP_GIT_EXE") or r"C:\Program Files\Git\cmd\git.exe"
    if not Path(g).exists():
        g = "git"
    try:
        r = subprocess.run([g, "-C", base_cwd, "log", "-1", "--format=%H", "--",
                            f".planning/workstreams/{workstream}"],
                           capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            return False
        last = (r.stdout or "").strip()
        if not last:
            return True   # nothing committed for this workstream on the base: nothing to regress
        a = subprocess.run([g, "-C", worktree, "merge-base", "--is-ancestor", last, "HEAD"],
                           capture_output=True, text=True, timeout=30)
        return a.returncode == 0
    except Exception:
        return False


def effective_workdir(session_id: str, base_cwd: str, workstream: str | None = None) -> str | None:
    """Where the predecessor was ACTUALLY working, from its own transcript's `cwd` field.

    Accepted only when it is the top of a git worktree of the SAME repository as the
    mission's cwd (same common git dir): a worker that wandered into a subdirectory, or into
    another repo, does not move the mission. None = the transcript could not tell us, which
    is never read as "the base directory".

    For a WORKSTREAM mission a worktree is followed only if the predecessor acted on that
    workstream there. Measured 2026-09-25 (m-1d270cd85220): two workers launched with a bare
    /gsd-autonomous ran another track's root milestone inside `gsd-p0a-autonomous`; the
    relay then briefed the next worker to ENTER that worktree and called the main checkout's
    .planning stale -- an off-mission predecessor's directory is not the mission's."""
    path = lr.find_transcript(session_id)
    if not path:
        return None
    last = None
    touched = False
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if workstream and not touched and _mentions_workstream(line, workstream):
                    touched = True
                if '"cwd"' not in line:
                    continue
                try:
                    cwd = json.loads(line).get("cwd")
                except Exception:
                    continue
                if cwd:
                    last = cwd
    except OSError:
        return None
    if not last:
        return None
    if os.path.normcase(str(Path(last).resolve())) == os.path.normcase(str(Path(base_cwd).resolve())):
        return base_cwd
    here, base = _git_toplevel_and_common(last), _git_toplevel_and_common(base_cwd)
    if not here or not base:
        return base_cwd if base else None
    if here[1] == base[1] and here[0] == os.path.normcase(str(Path(last).resolve())):
        if workstream and not (touched and _worktree_carries_workstream(last, base_cwd, workstream)):
            return base_cwd
        return str(Path(last).resolve())
    return base_cwd


def launched_row(pending: dict | None, sessions: list[dict] | None) -> dict | None:
    """The host's row for the worker THIS launch printed, matched by that id only."""
    bg = (pending or {}).get("bg_id")
    if not bg or not sessions:
        return None
    return next((s for s in sessions
                 if s.get("id") == bg or str(s.get("sessionId", "")).startswith(bg)), None)


def adopt_launched(rec: dict, row: dict, now: float | None = None) -> dict:
    """RUNNING from the host's witness when the worker's own ack did not arrive. The worker
    missed its SessionStart, so it gets no card this epoch -- recorded, not hidden."""
    sid = row.get("sessionId")
    new = transition(rec["mission_id"], expect_epoch=rec["epoch"], expect_state=LAUNCHING,
                     event="worker_adopted", now=now, state=RUNNING, pending=None,
                     failed_launches=0, iterations=rec.get("iterations", 0) + 1, worker=sid,
                     reason="host witness; worker's own ack absent (no card this epoch)",
                     owner={"session_id": sid, "pid": row.get("pid"), "proc_start": None,
                            "heartbeat_at": now or time.time(), "epoch": rec["epoch"],
                            "kind": "background"})
    _arm_worker_marker(new, sid)
    return new


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
               runner=None, wait_s: float | None = None, cmdline=None,
               killer=None) -> tuple[bool, str]:
    """Stop the predecessor and WAIT until its process is gone (W0: `claude stop` returns
    while the pid still lives). Only a background worker is stopped; an interactive pane
    is the Owner's and is left alone -- it simply no longer holds the lease."""
    import subprocess
    if not owner:
        return True, "no owner"
    row = _host_row(owner.get("session_id"), sessions)
    if row is None:
        return True, "not listed by host"
    # Our record says how WE launched it; the host row's `kind` is corroboration, not a
    # precondition (it was only ever seen in fixtures).
    if "background" not in (row.get("kind"), owner.get("kind")):
        return True, "interactive owner left running; lease moves"
    exe = os.environ.get("CPP_CLAUDE_EXE") or "claude"
    run = runner or (lambda argv: subprocess.run(argv, capture_output=True, text=True, timeout=120))
    if row.get("state") not in ("stopped", "done", "exited", "failed"):
        run([exe, "stop", row.get("id") or owner["session_id"][:8]])
    # Even a host `stopped`/`done` is waited on: the pid outlives the verdict (W0 E13), and a
    # successor launched before it is gone overlaps it.
    pid = row.get("pid")
    wait_s = STOP_WAIT_S if wait_s is None else wait_s
    deadline = time.time() + wait_s
    while isinstance(pid, int):
        if pid_alive(pid) is False:   # checked at least once, even with no wait budget
            return True, f"stopped; pid {pid} gone"
        if time.time() >= deadline:
            break
        time.sleep(1)
    if isinstance(pid, int):
        # Measured 2026-09-25 (m-3aaa15177f2b): the host listed the worker `done` while its
        # claude.exe idled on for 12 h, and every 5-minute pass waited 90 s and gave up, so
        # the mission never relayed. The host's verdict says the turn is over; the lingering
        # process is holding nothing. Terminate it -- but ONLY when the host already calls it
        # finished AND the process provably is this worker (its argv carries our exact
        # --session-id). Pid reuse or an unreadable argv keeps the old refusal.
        if row.get("state") in ("stopped", "done", "exited", "failed"):
            sid = owner.get("session_id") or ""
            argv = (cmdline or _proc_cmdline)(pid)
            if sid and argv and f"--session-id {sid}" in argv:
                (killer or _kill_tree)(pid)
                for _ in range(15):
                    if pid_alive(pid) is False:
                        return True, f"host {row.get('state')}; lingering pid {pid} terminated"
                    time.sleep(1)
                return False, f"pid {pid} survived termination"
            return False, (f"pid {pid} still alive after {int(wait_s)} s; not terminated: "
                           + ("argv unreadable" if not argv else "argv is not this worker"))
        return False, f"pid {pid} still alive after {int(wait_s)} s"
    return True, "stopped; no pid to wait on"


def _proc_cmdline(pid: int) -> str | None:
    """The process's command line, or None when it could not be read (never guessed)."""
    import subprocess
    if sys.platform != "win32":
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as fh:
                return fh.read().replace(b"\0", b" ").decode("utf-8", "replace")
        except OSError:
            return None
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command",
                            f"(Get-CimInstance Win32_Process -Filter 'ProcessId={int(pid)}').CommandLine"],
                           capture_output=True, text=True, timeout=30)
        return (r.stdout or "").strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def _kill_tree(pid: int) -> None:
    import subprocess
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/PID", str(int(pid)), "/T", "/F"],
                       capture_output=True, text=True, timeout=30)
    else:
        os.kill(int(pid), 9)


ORPHAN_LOOKBACK_S = 86400   # a terminal mission is re-checked for live workers this long
# The supervisor runs out of band with no deadline, so its GSD question may wait. Measured M6
# (2026-09-24, 1.4 GB free of 32): `gsd-tools query init.manager` took 67.5 s; the arming
# ceiling of 45 s held the relay as UNAVAILABLE on every pass, i.e. until the budget ran out.
SUPERVISE_GSD_TIMEOUT_S = 240


def _supervise_gsd_status(cwd, workstream=None):
    return lr.gsd_status(cwd, timeout=SUPERVISE_GSD_TIMEOUT_S, workstream=workstream)


def orphan_workers(rec: dict, sessions: list[dict] | None) -> list[dict]:
    """Live host sessions carrying this mission's worker name that the record does not
    own. Identity is exact because WE chose the name (`<mission_id>-e<epoch>`).

    Measured 2026-09-23 (W8): a supervisor pass launched a replacement a moment before the
    mission was halted by hand; the halt changed the record and not the world, and the
    orphan wrote the same progress file as the next mission's worker."""
    prefix = f"{rec['mission_id']}-e"
    owner_sid = (rec.get("owner") or {}).get("session_id") if rec["state"] not in TERMINAL else None
    pend = (rec.get("pending") or {}) if rec["state"] not in TERMINAL else {}
    # A launch in flight has no bg_id yet: its worker is known only by the name of the epoch
    # just claimed. Reaping it would kill the launch another supervisor is making.
    launching = worker_name(rec) if rec["state"] == LAUNCHING else None
    out = []
    for s in sessions or []:
        if not str(s.get("name", "")).startswith(prefix):
            continue
        if launching and s.get("name") == launching:
            continue
        if s.get("state") in ("stopped", "done", "exited", "failed"):
            continue
        if owner_sid and s.get("sessionId") == owner_sid:
            continue
        if pend.get("bg_id") and (s.get("id") == pend["bg_id"]
                                  or str(s.get("sessionId", "")).startswith(pend["bg_id"])):
            continue
        out.append(s)
    return out


def _needs_look(m: dict, now: float) -> bool:
    return m["state"] not in TERMINAL or now - float(m.get("updated_at") or 0) < ORPHAN_LOOKBACK_S


MAX_RENEWALS = 3   # budget renewals per lineage (spec vault/specs/gex44-mission-plane.md, A)


def renewal_refusal(rec: dict, halt_reason: str, gsd_outcome: str | None) -> str | None:
    """Why this budget-halted mission must NOT be renewed, or None when it may be.
    Positive test: only a halt the supervisor made for budget, with GSD saying work remains."""
    if os.environ.get("CPP_MISSION_RENEW", "").lower() == "off":
        return "renewal disabled (CPP_MISSION_RENEW=off)"
    if "budget:" not in (halt_reason or ""):
        return f"halt was not for budget: {halt_reason}"
    if gsd_outcome != "OK":
        return f"GSD answered {gsd_outcome}, not work-remains"
    if int(rec.get("renewal") or 0) >= MAX_RENEWALS:
        return f"renewal cap {MAX_RENEWALS} reached for lineage {rec.get('lineage_id') or rec['mission_id']}"
    return None


def renew_mission(rec: dict, now: float | None = None) -> dict:
    """A PREPARED successor of a budget-halted mission: same work, fresh budget, every Owner
    directive carried. The normal launch path starts it on the next pass."""
    now = time.time() if now is None else now
    new = create(rec["cwd"], rec["resume_command"], workstream=rec.get("workstream"),
                 max_cycles=rec.get("max_cycles"), max_hours=rec.get("max_hours"),
                 now=now, permission_mode=rec.get("permission_mode"),
                 allowed_tools=rec.get("allowed_tools"), add_dirs=rec.get("add_dirs"),
                 wall=rec.get("wall"))
    carried = {"renewed_from": rec["mission_id"],
               "lineage_id": rec.get("lineage_id") or rec["mission_id"],
               "renewal": int(rec.get("renewal") or 0) + 1,
               "directives": list(rec.get("directives") or [])}
    if rec.get("work_dir"):
        carried["work_dir"] = rec["work_dir"]
    new = transition(new["mission_id"], expect_epoch=new["epoch"], expect_state=PREPARED,
                     event="mission_renewed", now=now, **carried)
    lr.ledger_append(rec["mission_id"], "mission_renewed", mission_id=rec["mission_id"],
                     successor=new["mission_id"], renewal=carried["renewal"])
    return new


def supervise(now: float | None = None, dry_run: bool = False, sessions=None,
              gsd_status=None, runner=None, stop_runner=None, pid_alive=lr._pid_alive,
              fingerprint=None) -> list[dict]:
    """One out-of-band pass over every mission. Each action is ledgered by the
    transition it makes; a pass that decides nothing still returns one row per
    mission, so an empty estate and an unjudged one never look alike."""
    import subprocess
    now = time.time() if now is None else now
    missions, bad = _scan()
    # First in every pass, before any early return: an unreadable record is a mission nobody
    # can see, and "nothing to supervise" would otherwise be the answer for it.
    unreadable = _unreadable_rows(bad) if not dry_run else [
        {"mission_id": b["mission_id"], "state": "UNREADABLE", "action": "surface_unreadable",
         "reason": b["error"], "path": b["path"]} for b in bad]
    if not any(_needs_look(m, now) for m in missions):
        # Nothing to supervise: do not ask the host (`claude agents --json` costs seconds,
        # measured > 60 s once under load) on every 5-minute pass of an idle estate.
        return unreadable + [{"mission_id": m["mission_id"], "state": m["state"], "epoch": m["epoch"],
                              "action": "none", "reason": f"terminal {m['state']}"} for m in missions]
    if sessions is None:
        sessions = host_sessions()
    stop_run = stop_runner or (lambda a: subprocess.run(a, capture_output=True, text=True, timeout=120))
    exe = os.environ.get("CPP_CLAUDE_EXE") or "claude"

    def reap(rec: dict, row: dict) -> None:
        # Judge against the record as it is NOW, not as this pass first read it: the host
        # listing was taken earlier, so any worker in it was claimed before this re-read, and
        # a launch another supervisor claimed meanwhile is recognised by its epoch's name.
        rec = load(rec["mission_id"]) or rec
        stray = orphan_workers(rec, sessions)
        for s in stray:
            stop_run([exe, "stop", s.get("id") or str(s.get("sessionId", ""))[:8]])
            lr.ledger_append(rec["mission_id"], "orphan_stopped", mission_id=rec["mission_id"],
                             worker=s.get("sessionId"), name=s.get("name"), mission_state=rec["state"])
        if stray:
            row["orphans_stopped"] = [s.get("name") for s in stray]

    out = []
    for rec in missions:
        if not _needs_look(rec, now):
            continue
        mid = rec["mission_id"]
        plan = plan_next(rec, now, sessions, pid_alive)
        row = {"mission_id": mid, "state": rec["state"], "epoch": rec["epoch"], **plan}
        out.append(row)
        if dry_run:
            continue
        try:
            reap(rec, row)
            if row.get("orphans_stopped"):
                row["action"] = "reaped" if plan["action"] in ("none", "await") else plan["action"]
            if plan["action"] == "none" and rec["state"] == RUNNING:
                # The wall is enforced, not requested. Measured 2026-09-28 (m-916e905e23d4): a worker
                # asked once at 31 % worked on in the same turn for 3.5 h to 49 %. Past the grace after
                # the FIRST notice, a live owner is relayed anyway -- through the relay branch below,
                # so GSD, the child hold, T5 progress and the stall halt all still apply. Only a LIVE
                # owner: an UNKNOWN one may be running, and a replacement would run beside it.
                import gsd_epoch as ge
                over = ge.wall_overdue(rec, now)
                if over and liveness(rec.get("owner"), sessions, pid_alive)[0] == LIVE:
                    plan = {"action": "relay",
                            "reason": f"wall enforced: first notice {over['overdue_s'] + over['grace_s']} s "
                                      f"ago, grace {over['grace_s']} s, {over['notices']} notice(s)"}
                    row.update(plan)
                    row["wall_enforced"] = over
            if plan["action"] in ("none", "await"):
                continue
            act = plan["action"]
            if act == "halt":
                st = None
                # Where the work IS, resolved exactly as the relay path does (adversarial review
                # F1, 2026-09-28): the cwd can hold a reset roadmap while the worker committed in
                # a git worktree, and `work_dir` is saved only by a fresh launch -- a same-session
                # continuation never saves it. Asking the cwd read a finished milestone as
                # "work remains", halted it, and renewed it.
                halt_wd = rec.get("work_dir") or rec["cwd"]
                if rec.get("owner"):
                    try:
                        halt_wd = (effective_workdir(rec["owner"]["session_id"], rec["cwd"],
                                                     rec.get("workstream")) or halt_wd)
                    except Exception:  # noqa: BLE001 -- keep the recorded dir; never guess
                        pass
                row["work_dir"] = halt_wd
                if "budget:" in plan["reason"]:
                    # Asked BEFORE the halt is written: the worker whose turn finished the
                    # milestone is often the last one the budget allows, and a halt written
                    # first recorded a finished mission as HALTED (T1 2026-09-27: 41 missions,
                    # 0 COMPLETED). Owner 2026-09-25: only "work remains" renews.
                    try:
                        st = (gsd_status or _supervise_gsd_status)(
                            halt_wd, workstream=rec.get("workstream"))
                    except Exception as exc:  # noqa: BLE001 -- unanswered, never "complete"
                        st = {"outcome": "UNAVAILABLE", "reason": f"{type(exc).__name__}: {exc}"}
                    row["gsd"] = st.get("outcome")
                    if (st.get("outcome") == "ALL_COMPLETE"
                            and rec["resume_command"].startswith("/gsd-autonomous")):
                        done = transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                                          event="mission_completed", now=now, state=COMPLETED,
                                          pending=None,
                                          reason=f"gsd ALL_COMPLETE at budget ({plan['reason']})")
                        reap(done, row)
                        row["action"] = "completed"
                        continue
                halted = transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                                    event="mission_halted", now=now, state=HALTED, pending=None,
                                    reason=plan["reason"])
                reap(halted, row)  # a halt changes the record; stop the world to match it
                if st is not None:
                    why_not = renewal_refusal(halted, plan["reason"], st.get("outcome"))
                    origin = rec.get("progress_origin")
                    if not why_not and origin:
                        # T5: all 18 renewals of the 6 capped lineages produced 0 commits. A
                        # mission whose tree never moved does not earn a fresh budget. A tree
                        # that cannot be measured is not "unchanged": it still renews.
                        fp_now = (fingerprint or progress_fingerprint)(halt_wd)
                        if fp_now is not None and fp_now == origin:
                            why_not = "no progress in this mission (work tree unchanged since its first launch)"
                    if why_not:
                        row["renewal"] = f"not renewed: {why_not}"
                    else:
                        row["renewed_as"] = renew_mission(halted, now=now)["mission_id"]
            elif act == "surface_blocked":
                if rec["state"] != BLOCKED:
                    transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                               event="mission_blocked", now=now, state=BLOCKED,
                               reason=plan["reason"])
            elif act == "adopt":
                adopt_launched(rec, launched_row(rec.get("pending"), sessions), now=now)
            elif act == "unblock":
                transition(mid, expect_epoch=rec["epoch"], expect_state=BLOCKED,
                           event="mission_unblocked", now=now, state=RUNNING,
                           reason=plan["reason"])
            elif act in ("launch", "replace", "relay"):
                # Ask GSD before ANY successor: a background worker that finished its turn reads
                # host `done` (W8), which plans a REPLACE, not a relay -- and a worker that just
                # completed the milestone must not be followed by another one.
                work_dir = None
                if act in ("relay", "replace") and rec.get("owner"):
                    hold = provider_hold(rec, now)
                    if hold:
                        # The successor would meet the same refusal: hold, spending no epoch.
                        # tools/provider_breaker.py: quota keeps this exact row; auth, transient
                        # failures and repeated instant deaths back off or quarantine.
                        if hold.get("class", "quota") == "quota":
                            row["held"] = f"provider quota until {int(hold['until'])}: {hold['reason']}"
                            lr.ledger_append(mid, "quota_held", mission_id=mid, epoch=rec["epoch"],
                                             until=hold["until"], reason=hold["reason"])
                        else:
                            until = hold.get("until")
                            row["held"] = (f"provider {hold['class']} "
                                           f"{'QUARANTINED' if hold.get('quarantine') else f'until {int(until)}'}"
                                           f" (streak {hold.get('streak')}): {hold['reason']}")
                            lr.ledger_append(mid, "provider_held", mission_id=mid, epoch=rec["epoch"],
                                             until=until, reason=hold["reason"], provider_class=hold["class"],
                                             streak=hold.get("streak"), quarantine=bool(hold.get("quarantine")))
                        continue
                if act in ("relay", "replace") and rec.get("owner"):
                    # Judge (and brief) where the predecessor actually worked. Measured M6: the
                    # run lived in a git worktree while the mission's cwd kept a reset roadmap,
                    # so asking GSD there would read 1/8 for ever and never complete.
                    work_dir = (effective_workdir(rec["owner"]["session_id"], rec["cwd"],
                                                  rec.get("workstream"))
                                or rec.get("work_dir"))
                    if work_dir:
                        row["work_dir"] = work_dir
                if act in ("relay", "replace") and rec["resume_command"].startswith("/gsd-autonomous"):
                    st = (gsd_status or _supervise_gsd_status)(work_dir or rec.get("work_dir") or rec["cwd"],
                                                       workstream=rec.get("workstream"))
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
                turn_end = None
                import gsd_epoch as ge
                if rec.get("owner") and (act == "relay" or (
                        act == "replace" and ge.turn_ended_as_done(rec, sessions))):
                    # A turn that ENDED is not a context that ran out (tools/gsd_epoch.py): 444 of
                    # 499 launches were fresh workers for a turn end, each paying the ~187k-token
                    # startup floor and losing the worker's memory. The same session continues
                    # unless the wall was crossed, the context is past the continuation ceiling,
                    # or a background child of the owner has not reported (then nothing is stopped).
                    # A finished turn the host lists `done` (not `idle`) plans a REPLACE; it is the
                    # same event and is judged the same way (m-47fe0c6cb54a, 2026-09-28).
                    turn_end = ge.decide_turn_end(rec, now)
                    if row.get("wall_enforced") and turn_end["decision"] == ge.ROTATE:
                        turn_end["evidence"] = {**(turn_end.get("evidence") or {}), "trigger": "wall_enforced"}
                        turn_end["reason"] = f"{plan['reason']} -- {turn_end['reason']}"
                    row["turn_end"] = {k: turn_end.get(k) for k in ("decision", "cause", "reason")}
                    if turn_end["decision"] == ge.HOLD:
                        lr.ledger_append(mid, "relay_held", mission_id=mid, epoch=rec["epoch"],
                                         reason=turn_end["reason"])
                        row["held"] = turn_end["reason"]
                        continue
                fp_fn = fingerprint or progress_fingerprint
                progress = next_progress(rec, fp_fn(work_dir or rec.get("work_dir") or rec["cwd"]),
                                         ran=rec["state"] != LAUNCHING)
                row["progress"] = progress
                if act in ("relay", "replace") and progress["stalls"] >= NO_PROGRESS_EPOCHS:
                    # T5: convergence was asked first (above); a mission whose tree has not moved
                    # across NO_PROGRESS_EPOCHS epochs is not relayed again, and -- the reason
                    # carrying no "budget:" -- renewal refuses it too. UNMEASURED never counts.
                    halted = transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                                        event="mission_halted", now=now, state=HALTED, pending=None,
                                        progress=progress,
                                        reason=f"no_progress: {NO_PROGRESS_EPOCHS} consecutive epochs "
                                               f"ended with no commit or work-tree change")
                    reap(halted, row)
                    row["action"] = "halt"
                    continue
                if act in ("relay", "replace") and rec.get("owner"):
                    # A replaced owner is DEAD by the host's word, and its pid can still outlive
                    # that word (W0 E13): wait for it too, or the successor overlaps it.
                    ok, why = stop_owner(rec.get("owner"), sessions, pid_alive=pid_alive,
                                         runner=stop_runner)
                    row["stop"] = why
                    if not ok:
                        continue  # the next pass retries; nothing launched beside a live worker
                if turn_end is not None and turn_end["decision"] == "continue":
                    import gsd_epoch as ge
                    row["continue"] = ge.continue_worker(
                        mid, rec, prompt=bind_workstream(rec["resume_command"], rec.get("workstream")),
                        decision=turn_end, runner=runner, stop_runner=stop_runner, now=now,
                        progress=progress, work_dir=work_dir)
                    row["action"] = "continue"
                    continue
                note = None
                packet = None
                if act in ("relay", "replace") and rec.get("owner"):
                    # Read BEFORE the launch: the note describes the predecessor's last turn.
                    # An explicit `handoff --note` counts only when THIS owner recorded it
                    # (state HANDOFF); otherwise the record's note is the previous epoch's and
                    # would be handed on as current. The same holds for its source packet.
                    explicit = rec.get("note") if rec["state"] == HANDOFF else ""
                    packet = rec.get("packet") if rec["state"] == HANDOFF else None
                    note = explicit or handoff_note_from_transcript(rec["owner"]["session_id"]) or ""
                    row["note_chars"] = len(note)
                row["launch"] = launch_worker(mid, expect_epoch=rec["epoch"],
                                              expect_state=rec["state"], reason=plan["reason"],
                                              runner=runner, now=now, note=note,
                                              work_dir=work_dir, progress=progress, packet=packet)
                if row["launch"].get("ok"):
                    # Every FRESH worker says why it exists: a rotation is certified by its cause,
                    # never by counting fresh sessions (tools/gsd_epoch.py census).
                    import gsd_epoch as ge
                    cause = ge.cause_for(act, plan["reason"], rec, turn_end)
                    row["cause"] = cause.get("cause")
                    ge.record_cause(mid, {"epoch": row["launch"]["epoch"]}, cause, ge.FRESH)
        except CasConflict as exc:
            row["cas"] = str(exc)  # another supervisor acted first: correct, not an error
        except Exception as exc:  # noqa: BLE001 -- one mission's failure must not blind the rest
            # e.g. os.replace refused by a scanner holding the file (Windows), a busy lock, a
            # malformed record. Recorded per mission; the next pass retries from the record.
            row["error"] = f"{type(exc).__name__}: {exc}"
            try:
                lr.ledger_append(mid, "supervise_error", mission_id=mid, error=row["error"])
            except Exception:  # noqa: BLE001 -- the row still carries the error
                pass
    return unreadable + out


def arm(cwd: str, resume_command: str, *, launch: bool = True, **kw) -> dict:
    rec = create(cwd, resume_command, **kw)
    if not launch:
        return {"mission": rec}
    # The origin is the tree BEFORE epoch 1 works (review F6): measured here, at arm, it makes
    # "unchanged since its first launch" true and credits epoch 1's own progress.
    res = launch_worker(rec["mission_id"], expect_epoch=0, expect_state=PREPARED,
                        reason="armed", progress=next_progress(rec, progress_fingerprint(rec["cwd"])))
    if res.get("ok"):
        import gsd_epoch as ge
        ge.record_cause(rec["mission_id"], {"epoch": res["epoch"]},
                        {"cause": ge.INITIAL, "reason": "armed"}, ge.FRESH)
    return {"mission": load(rec["mission_id"]), "launch": res}


NO_PROGRESS_EPOCHS = 3   # consecutive relays with an unchanged work tree before HALTED


def progress_fingerprint(work_dir: str) -> str | None:
    """A hash of what a worker can change in its work tree: HEAD, the dirty-path set, and the
    size of the uncommitted diff. None when git cannot answer -- unmeasured, never "no change".

    Why (T5, measured 2026-09-27): all 18 renewed missions across the 6 lineages that hit the
    renewal cap produced 0 commits, while each lineage's first mission made 3-137; 444 of 499
    relays were "turn ended without completion". Nothing compared one epoch's tree to the next,
    so a lineage that had stopped progressing was relayed and renewed until its caps ran out.
    A commit is the unit of work GSD and the hand-off card both ask a worker to leave behind."""
    import hashlib
    import subprocess
    g = os.environ.get("CPP_GIT_EXE") or r"C:\Program Files\Git\cmd\git.exe"
    if not Path(g).exists():
        g = "git"
    parts = []
    try:
        for args in (["rev-parse", "HEAD"], ["status", "--porcelain"], ["diff", "HEAD", "--shortstat"]):
            r = subprocess.run([g, "-C", work_dir, *args], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=30)
            if r.returncode != 0:
                return None
            parts.append(r.stdout)
    except Exception:  # noqa: BLE001 -- unmeasured is its own answer
        return None
    return hashlib.sha256("\x00".join(parts).encode("utf-8")).hexdigest()[:16]


def next_progress(rec: dict, fp: str | None, ran: bool = True) -> dict:
    """The progress entry a relay records: stalls count up only on a MEASURED unchanged tree,
    and only for an epoch whose worker actually ran. A launch that was never acknowledged left
    the tree unchanged by construction; counting it made "3 epochs ended with no commit" false
    (adversarial review F4, 2026-09-28)."""
    prev = rec.get("progress") or {}
    stalls = int(prev.get("stalls") or 0)
    if ran and fp is not None and prev.get("fp") is not None:
        stalls = stalls + 1 if fp == prev["fp"] else 0
    return {"fp": fp if fp is not None else prev.get("fp"), "stalls": stalls,
            "measured": fp is not None}


def _plan_facts(work_dir: str, workstream: str | None = None) -> str:
    """Plan-graph verdict for the successor card (assimilation item 18). GSD runs one wave's plans
    in parallel; two of them writing the same file are two writers in one tree. Runs at relay
    time, out of band, like _git_facts. A check that could not run says so -- never silence,
    which would read as "no overlap". Kill switch: CPP_PLAN_GRAPH_CARD=off."""
    if (os.environ.get("CPP_PLAN_GRAPH_CARD") or "").strip().lower() == "off":
        return ""
    try:
        import plan_graph_check as pg
        return pg.card_lines(pg.check_tree(work_dir, workstream))
    except Exception as exc:  # noqa: BLE001 -- the card must still ship; the gap is named on it
        return f"PLAN GRAPH: the check could not run ({exc.__class__.__name__}); same-wave overlap is UNJUDGED."


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
    try:
        # G3: an observed compaction is ledgered against the epoch; S7: the first start of a launch
        # or continuation checks it is where the mission is. A mismatch is the one line returned.
        import gsd_epoch as ge
        stop_line = ge.on_session_start(rec, session_id, source, ge.registry_cwd(session_id), first)
    except Exception:  # noqa: BLE001 -- fail-open: the hub runs under a deadline
        stop_line = ""
    if stop_line:
        return stop_line
    if rec["epoch"] <= 1 and not rec.get("note"):
        return ""
    # The card was rendered at RELAY time by the supervisor (out of band, no deadline), so
    # this path reads JSON and spawns nothing. Rendering it here -- git status on the
    # project -- timed out at 5 s on a loaded host (measured: ETIMEDOUT) and cost the
    # successor its card exactly when the host was under pressure. The fallback renders
    # without git facts, which the card then reports as unknown.
    if rec.get("card"):
        return ""  # already delivered through --append-system-prompt at launch; never twice
    return render_card(rec, None)


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


NOTE_TAG = "HANDOFF NOTE:"
NOTE_MAX_CHARS = 2000


def handoff_instruction(marker: dict, used_pct) -> str:
    """What the worker is told at its wall. It needs NO tool to hand off: a worker in
    acceptEdits cannot run a shell command on this host (W0 E8), so a hand-off that required
    one would leave it parked on a permission prompt exactly at the wall. The note travels
    as the last text of its response, which the supervisor reads from the transcript."""
    return (
        f"CONTEXT WALL — {used_pct}% used. This mission continues in a FRESH session; this one "
        f"ends here (mission {marker.get('mission_id')}, epoch {marker.get('epoch')}). Do exactly "
        "this: (1) finish ONLY the atomic step in progress and make it durable (commit / save) — "
        "start nothing new; (2) end your response with a paragraph that begins "
        f"`{NOTE_TAG}` stating the next exact action and any fact the repository does not "
        "record. Do NOT run /compact and do NOT re-issue the run command: the supervisor "
        "starts the next worker once this turn ends."
    )


def handoff_note_from_transcript(session_id: str) -> str:
    """The predecessor's hand-off note: the text after the LAST ``HANDOFF NOTE:`` in its last
    assistant message. Empty when absent -- the successor then reconstructs from durable
    state, and the card says so. A claim, never a fact: the card labels it as such."""
    try:
        t = lr.find_transcript(session_id)
        text = lr.last_assistant_text(t) if t else None
    except Exception:
        return ""
    if not text or NOTE_TAG not in text:
        return ""
    return text.rsplit(NOTE_TAG, 1)[1].strip()[:NOTE_MAX_CHARS]


# A worker whose only reply is the provider refusing it did no work: relaunching burns an
# iteration into the same refusal. Measured 2026-09-26, m-075bb211b830: 8 epochs, every
# reply "You've hit your weekly limit · resets Sep 30, 7pm (Europe/Madrid)", budget spent,
# zero work. A settled turn is not an answered turn.
QUOTA_RE = re.compile(r"hit your (?:weekly |usage |session |daily )?limit"
                      r"|usage limit (?:reached|exceeded)", re.I)
RESETS_RE = re.compile(r"resets\s+(?:(?P<mon>[A-Z][a-z]{2})\s+(?P<day>\d{1,2}),?\s+)?"
                       r"(?P<h>\d{1,2})(?::(?P<m>\d{2}))?\s*(?P<ap>am|pm)"
                       r"(?:\s*\((?P<tz>[^)]+)\))?", re.I)
QUOTA_UNPARSED_HOLD_S = 3600
_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def quota_reset_at(text: str, now: float, anchor: float | None = None) -> float | None:
    """Epoch seconds at which the refusal says the limit resets; None when unparseable.

    ``anchor`` is when the refusal was WRITTEN. A time-only reset ("resets 4pm") is the next
    4pm after that moment, not after ``now``: resolved against ``now``, every pass later than
    4pm rolled it to tomorrow. Measured 2026-09-28, m-d82c7cb6b87e: refused 15:51 Madrid,
    "resets 4pm", held until 16:00 the NEXT day -- a quota that had reset nine minutes after
    the refusal parked the mission for 24 h."""
    import datetime as _dt
    m = RESETS_RE.search(text or "")
    if not m:
        return None
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(m.group("tz").strip()) if m.group("tz") else None
    except Exception:  # noqa: BLE001 -- unknown zone: fall back to the host's local time
        tz = None
    now = float(anchor) if anchor else now
    base = _dt.datetime.fromtimestamp(now, tz)
    hour = int(m.group("h")) % 12 + (12 if m.group("ap").lower() == "pm" else 0)
    minute = int(m.group("m") or 0)
    if m.group("mon"):
        mon = _MONTHS.get(m.group("mon").lower())
        if not mon:
            return None
        cand = base.replace(month=mon, day=int(m.group("day")), hour=hour, minute=minute,
                            second=0, microsecond=0)
        if cand.timestamp() < now - 180 * 86400:
            cand = cand.replace(year=cand.year + 1)
    else:
        cand = base.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if cand.timestamp() <= now:
            cand += _dt.timedelta(days=1)
    return cand.timestamp()


def quota_hold(text: str | None, replied_at: float | None, now: float) -> dict | None:
    """{"until", "reason"} while the predecessor's last reply is a provider quota refusal and
    its reset has not passed; None otherwise. Pure. An unparseable reset holds one hour from
    the reply, so the supervisor probes at most hourly instead of every pass."""
    if not text or not QUOTA_RE.search(text):
        return None
    until = quota_reset_at(text, now, anchor=replied_at)
    if until is None:
        until = (replied_at or now) + QUOTA_UNPARSED_HOLD_S
    if now >= until:
        return None
    return {"until": until, "reason": " ".join(text.split())[:200]}


def provider_hold(rec: dict, now: float) -> dict | None:
    """The hold for this mission's next successor (tools/provider_breaker.py). If the breaker
    itself cannot run, fall back to the pre-breaker quota check -- and say so in the ledger:
    a missing breaker must not read as a provider that is fine."""
    try:
        import provider_breaker as pb
        return pb.hold_for(rec, now)
    except Exception as exc:  # noqa: BLE001 -- degrade to the previous behaviour, visibly
        lr.ledger_append(rec.get("mission_id"), "provider_breaker_unavailable",
                         mission_id=rec.get("mission_id"), error=f"{exc.__class__.__name__}: {exc}"[:200])
        h = quota_hold_from_transcript((rec.get("owner") or {}).get("session_id"), now)
        return None if h is None else {**h, "class": "quota"}


def last_assistant_at(transcript) -> float | None:
    """The LAST assistant row's own ``timestamp``; None when it carries none. Not the file's
    mtime: the host appends cost/prompt rows after a refusal (measured: refusal 13:51Z, mtime
    14:52Z), and a later anchor pushes a time-only reset past the day it named."""
    for row in reversed(lr._tail_rows(transcript)):
        if row.get("type") == "assistant":
            return lr._parse_iso(row.get("timestamp"))
    return None


def quota_hold_from_transcript(session_id: str, now: float) -> dict | None:
    try:
        t = lr.find_transcript(session_id)
        text = lr.last_assistant_text(t) if t else None
        replied_at = (last_assistant_at(t) or os.path.getmtime(t)) if t else None
    except Exception:  # noqa: BLE001 -- no evidence of a refusal is not a refusal
        return None
    return quota_hold(text, replied_at, now)


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
    # Owner decision 2026-09-24: real mission workers run `auto`. Pinned here rather than left
    # to the host's settings default, so a settings change cannot silently turn an unattended
    # worker into one that stops on every prompt (acceptEdits cannot run git here, T-CONT-16).
    a.add_argument("--permission-mode", default="auto",
                   help="worker permission mode (default auto, Owner decision 2026-09-24)")
    a.add_argument("--allowed-tools", nargs="*", default=None)
    a.add_argument("--add-dir", action="append", default=None)
    a.add_argument("--wall", default=None,
                   help="snapshot,advisory,rearm in %% of context (default 35,40,30)")
    s = sub.add_parser("session-start")
    s.add_argument("--session", required=True)
    s.add_argument("--source", default="")
    h = sub.add_parser("handoff")
    h.add_argument("--session", required=True)
    h.add_argument("--note", default="")
    h.add_argument("--packet", action="append", default=[], metavar="PATH::ANCHOR|PATH:START-END",
                   help="hand the successor the exact region you were working on, as a hash-bound "
                        "source packet referenced from its card (repeatable; never inlined)")
    d = sub.add_parser("directive")
    d.add_argument("--mission", required=True)
    d.add_argument("--text", required=True)
    v = sub.add_parser("supervise")
    v.add_argument("--dry-run", action="store_true")
    v.add_argument("--actions-only", action="store_true",
                   help="print only rows where the pass acted (the sweep logs nothing otherwise)")
    sub.add_parser("status")
    args = ap.parse_args(argv)
    if args.cmd == "arm":
        wall = None
        if args.wall:
            snap, adv, rearm = (float(x) for x in args.wall.split(","))
            wall = {"snapshot": snap, "advisory": adv, "rearm": rearm}
        res = arm(args.cwd, args.command, launch=not args.no_launch, workstream=args.workstream,
                  max_cycles=args.max_cycles, max_hours=args.max_hours,
                  permission_mode=args.permission_mode, allowed_tools=args.allowed_tools,
                  add_dirs=args.add_dir, wall=wall)
        print(json.dumps(res, indent=2))
        return 0 if args.no_launch or res.get("launch", {}).get("ok") else 1
    if args.cmd == "session-start":
        card = session_start(args.session, args.source)
        if card:
            sys.stdout.write(card)
        return 0
    if args.cmd == "handoff":
        packet = None
        if args.packet:
            packet, why = handoff_packet(args.session, args.packet)
            if packet is None:
                # A packet is an aid, never a precondition: the hand-off is recorded without it.
                print(f"SOURCE PACKET NOT ATTACHED: {why}")
        rec = request_handoff(args.session, args.note, packet=packet)
        extra = f" packet={packet['sha256'][:12]} ({packet['bytes']} bytes)" if packet else ""
        print(f"HANDOFF RECORDED mission={rec['mission_id']} epoch={rec['epoch']}{extra} -- end your turn now")
        return 0
    if args.cmd == "directive":
        rec = add_directive(args.mission, args.text)
        print(f"DIRECTIVE RECORDED mission={rec['mission_id']} total={len(rec['directives'])}")
        return 0
    if args.cmd == "supervise":
        rows = supervise(dry_run=args.dry_run)
        if args.actions_only:
            rows = [r for r in rows if r.get("action") not in ("none", "await")]
        print(json.dumps(rows))
        return 0
    missions, bad = _scan()
    rows = [{"mission_id": b["mission_id"], "state": "UNREADABLE", "error": b["error"],
             "path": b["path"], "plan": {"action": "surface_unreadable",
                                         "reason": "record cannot be read; inspect it by hand"}}
            for b in bad]
    sessions = host_sessions()
    for m in missions:
        v_, why = liveness(m.get("owner"), sessions)
        rows.append({"mission_id": m["mission_id"], "state": m["state"], "epoch": m["epoch"],
                     "iterations": m.get("iterations"), "owner": (m.get("owner") or {}).get("session_id"),
                     "liveness": v_, "evidence": why, "pending": m.get("pending"),
                     "plan": plan_next(m, time.time(), sessions)})
    events = lr.ledger_events()   # once, not per mission (~1 MB on this host)
    for row in rows:
        m = next((x for x in missions if x["mission_id"] == row["mission_id"]), None)
        if m is not None:
            row["history"] = history_gaps(m, events)
            row["code_id"] = m.get("code_id")
    print(json.dumps(rows, indent=2))
    # On stderr so the stdout JSON keeps its shape for every existing consumer.
    h = sweep_health()
    print(f"SWEEP {h['verdict']}: {h['detail']}", file=sys.stderr)
    drift = [r["mission_id"] for r in rows if r.get("state") not in TERMINAL | {"UNREADABLE"}
             and r.get("code_id") and r["code_id"] != CODE_ID]
    if drift:
        print(f"CODE DRIFT: live missions last written by another build than {CODE_ID}: "
              f"{', '.join(drift)}", file=sys.stderr)
    return 0


SWEEP_STALE_S = 900   # 3 missed 5-minute passes


def sweep_health(now: float | None = None) -> dict:
    """The supervisor's liveness, judged from evidence the supervisor does not write about
    itself on success alone: the sweep script's per-pass heartbeat (T7). Absent heartbeat is
    NOT_OBSERVED, never healthy."""
    now = time.time() if now is None else now
    p = lr.state_dir() / "gsd-sweep-heartbeat.json"
    try:
        b = json.loads(p.read_text(encoding="utf-8-sig"))
        age = now - p.stat().st_mtime
    except (OSError, ValueError):
        return {"verdict": "NOT_OBSERVED", "detail": f"no readable heartbeat at {p}"}
    timed = [s["name"] for s in b.get("stages", []) if s.get("timed_out")]
    if b.get("outcome") == "running" and age > SWEEP_STALE_S:
        # A pass is bounded at 840 s by its own stage deadlines; running past that is a pass
        # that escaped its bounds, not merely a missed schedule.
        return {"verdict": "STUCK", "detail": f"pass running for {int(age)} s"}
    if age > SWEEP_STALE_S:
        return {"verdict": "STALE", "detail": f"last pass {int(age)} s ago ({b.get('outcome')})"}
    if timed:
        return {"verdict": "DEGRADED", "detail": f"stages timed out last pass: {timed}"}
    return {"verdict": "OK", "detail": f"{b.get('outcome')} {int(age)} s ago"}


if __name__ == "__main__":
    sys.exit(_cli())
