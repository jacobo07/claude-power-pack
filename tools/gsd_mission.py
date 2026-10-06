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
# Consecutive relay passes GSD may refuse (answer not OK) before the mission reads BLOCKED instead
# of RUNNING. Measured 2026-09-28 (T11 smokes m-27f9f1ab9fb6, m-860e4176f1d6): NO_PHASES held the
# relay every pass for 1.5 h while the record said RUNNING. NO_PHASES does not clear by waiting;
# UNAVAILABLE (a loaded host) can, so it gets the longer bound. Blocking never relays: only OK does.
GSD_HOLD_BLOCK_AFTER = {"NO_PHASES": 2, "UNAVAILABLE": 6}
# Hand-off wall, % of context used, in the watchdog's own vocabulary. The same narrowed wall
# /cpp-gsd-long has run on since v2 (crossing at 40 % used), so a worker hands off long
# before native compaction would fire.
DEFAULT_WALL = {"snapshot": 35.0, "advisory": 40.0, "rearm": 30.0}

LIVE = "ALIVE"
DEAD = "DEAD"
UNKNOWN = "UNKNOWN"
WAITING_HUMAN = "BLOCKED"

# capsule-v2 rotation (spec vault/specs/mission-capsule-rollover.md). Set ONLY by
# `arm --rollover-protocol capsule-v2`; a record without the field is legacy and never reaches a
# v2 branch (spec 3.1), which tools/test_gsd_mission_legacy_characterization.py pins.
CAPSULE_V2 = "capsule-v2"
CAPSULE_V2_MODES = ("auto", "bypassPermissions")   # G11: the successor must run its exam in a shell
CAPSULE_CERTIFY_DEADLINE_S = 1800                  # spec 3.5: successor ack -> RESUME_CERTIFIED
MAX_SUCCESSOR_ATTEMPTS = 3                         # spec 11.3: uncertified successors per capsule, then a human


def capsule_v2(rec: dict | None) -> bool:
    """Does capsule-v2 govern this mission's rotation NOW? Only a record armed with the protocol, and
    never while a kill switch is set: the file <rollover state>/capsule-v2.off (G13, read by the
    mutation guard too) or CPP_CAPSULE_ROLLOVER=off. Switched off, a v2 mission rotates the legacy way."""
    if (rec or {}).get("rollover_protocol") != CAPSULE_V2:
        return False
    if (os.environ.get("CPP_CAPSULE_ROLLOVER") or "").strip().lower() == "off":
        return False
    import mission_capsule as mc
    return not (mc.state_dir() / "capsule-v2.off").exists()


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
           wall: dict | None = None, rollover_protocol: str | None = None) -> dict:
    """A PREPARED mission. Refuses to overwrite an existing, non-terminal one."""
    now = time.time() if now is None else now
    if rollover_protocol not in (None, CAPSULE_V2):
        raise MissionError(f"unknown rollover protocol {rollover_protocol!r} (only {CAPSULE_V2})")
    if rollover_protocol == CAPSULE_V2 and permission_mode not in CAPSULE_V2_MODES:
        # G11: a v2 successor certifies by running mission_capsule.py in a shell. A mode that cannot
        # run one would leave every successor without authority for ever.
        raise MissionError(f"{CAPSULE_V2} needs permission mode {' or '.join(CAPSULE_V2_MODES)}, "
                           f"not {permission_mode!r}")
    # A `--ws` in the command IS the workstream; without this the supervisor asks GSD for the
    # root roadmap and parks the mission (2026-09-29, m-bb79185652b1).
    if workstream is None and resume_command.startswith("/gsd-"):
        m = _WS_FLAG.search(resume_command)
        workstream = m.group(1) if m else None
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
        if rollover_protocol:
            # Absent, not null, for a legacy record: its bytes stay those the golden pinned.
            rec["rollover_protocol"] = rollover_protocol
        _write(path, rec)
    lr.ledger_append(mid, "mission_prepared", mission_id=mid, cwd=rec["cwd"],
                     command=resume_command, mode=mode)
    return rec


def transition(mission_id: str, *, expect_epoch: int, expect_state, event: str,
               now: float | None = None, worker: str | None = None,
               ledger_extra: dict | None = None, **changes) -> dict:
    """Compare-and-swap. ``expect_state`` is one state or a set of them.

    Raises CasConflict when the record moved since the caller observed it. The
    caller's observation is the authorization; re-reading and proceeding anyway
    would authorize whatever arrived in between.

    ``worker`` names the session the event concerns, for the ledger only. (The
    ledger is keyed by its own ``session_id`` parameter, which here carries the
    mission id, so the worker cannot travel under that name.)

    ``ledger_extra`` rides on the ledger row only (a hold's typed fields; it cannot
    overwrite the row's own keys). A transition that does not set ``sleep`` ends it
    (GGMC C5): after real movement the next hold is news again.
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
        if "sleep" not in changes:
            rec.pop("sleep", None)   # popped, not nulled: a record that never slept keeps its bytes
        rec["updated_at"] = now
        # Every committed transition has a number, so the ledger's copy of the history can be
        # checked for holes against the record (history_gaps). A record with no seq predates T4.
        rec["seq"] = int(rec.get("seq") or 0) + 1
        rec["code_id"] = CODE_ID
        _write(path, rec)
    core = ("mission_id", "epoch", "state", "seq", "code")
    extra = {k: v for k, v in (ledger_extra or {}).items() if k not in core}
    extra.update({k: v for k, v in (("reason", changes.get("reason")), ("worker", worker)) if v})
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
        if state == "blocked":
            # Measured 2026-09-28 (`claude agents --json --all`, 569 rows): a bare
            # `state:"blocked"` -- no status, no waitingFor, no pid -- is a job whose
            # ~/.claude/jobs/<id>/state.json carries `needs` ("login required", a question, a
            # startup approval). A finished turn reads `done` or `status:"idle"`. Reading this
            # shape as "turn ended" relayed m-66ebaaa0324e 48 times into the same block.
            return WAITING_HUMAN, "host lists session blocked (no waitingFor)"
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
              pid_alive=lr._pid_alive, v2: bool | None = None) -> dict:
    """What the out-of-band supervisor should do for this mission, and why.

    Actions: none · launch · replace · halt · surface_blocked · await.
    Pure: no I/O beyond the injected ``pid_alive``. ``v2`` is capsule_v2(rec) as the caller read it
    (the kill switch is a file); None reads the record's field alone.
    """
    if v2 is None:
        v2 = rec.get("rollover_protocol") == CAPSULE_V2
    state = rec.get("state")
    if state in TERMINAL:
        return {"action": "none", "reason": f"terminal {state}"}
    hold = rec.get("owner_hold")
    if hold:
        # spec mission-owner-hold: an Owner park outranks budget, launch and relay -- nothing is
        # launched, stopped, halted or renewed while it stands. Holding is not halting.
        return {"action": "none", "reason": f"owner hold: {hold.get('reason')}"}
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
    if state == RUNNING and (rec.get("owner") or {}).get("kind") == "slim":
        # A slim (`claude -p`) worker is one synchronous process, never in the host's session list:
        # judged by its own exit + result file. A finished one is complete, not "dead" (no replace).
        s = slim_result(rec.get("owner"), pid_alive)
        if s["status"] == "finished":
            return {"action": "slim_finished", "slim": s,
                    "reason": f"slim worker finished (is_error={s['is_error']}, tokens {s['tokens']:,})"}
        if s["status"] == "failed":
            return {"action": "halt", "reason": f"slim worker failed: {s['why']}"}
        return {"action": "none", "reason": f"slim worker {s['status']}"}
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
            # Nor a block: "could not ask" is not "needs a human". Measured 2026-09-28
            # (m-bcaf08f8d856): parked BLOCKED on "host session list unavailable" while the host,
            # asked moments later, listed the owner busy/working. Ledgered; state unchanged.
            return {"action": "surface_unknown",
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
        chold = (rec.get("capsule_hold") or {}) if v2 else {}
        if chold and state == BLOCKED:
            # G4: a capsule hold sticks like gsd_hold -- a live owner is not an answer to it. A refused
            # seal is re-judged once the owner's turn has ended (the relay path seals again); an
            # uncertified successor is lifted only by its certification (supervise checks the marker).
            if spent and chold.get("kind") == "resume_not_certified":
                # Spec 11.3 (L2): the budget is asked BEFORE the hold. The uncertified successor never had
                # mutation authority, so the halt inherits its capsule; held, it waited for a human for ever.
                return {"action": "halt", "reason": f"budget: {spent}; successor never certified"}
            if chold.get("kind") == "seal_refused" and verdict == LIVE and owner_idle(rec.get("owner"), sessions):
                if spent:
                    return {"action": "halt", "reason": f"turn ended and budget: {spent}"}
                return {"action": "relay", "reason": f"capsule hold: re-judging the seal ({chold.get('reason')})"}
            forced = _budget_forced(rec, now, spent, verdict)
            if forced:
                return {"action": "halt", "reason": forced}
            return {"action": "none", "reason": f"capsule hold {chold.get('kind')}: {chold.get('reason')}"}
        hold = rec.get("gsd_hold") or {}
        if verdict == LIVE and state == BLOCKED and hold and owner_idle(rec.get("owner"), sessions):
            # Blocked on GSD, not on a human: a live idle owner is not an answer. Re-ask GSD
            # through the relay path; only OK leaves BLOCKED (the owner being alive never did).
            if spent:
                return {"action": "halt", "reason": f"turn ended and budget: {spent}"}
            return {"action": "relay",
                    "reason": f"blocked on gsd {hold.get('outcome')}: re-asking GSD (a relay needs OK)"}
        if verdict == LIVE and state == BLOCKED:
            return {"action": "unblock", "reason": why}
        if verdict == LIVE and owner_idle(rec.get("owner"), sessions):
            # Ralph: a worker whose turn ended is finished, whatever it said. The
            # supervisor asks GSD first; only an incomplete mission is relayed -- and never
            # past its budget, or a mission with no completion predicate relays forever.
            if spent:
                return {"action": "halt", "reason": f"turn ended and budget: {spent}"}
            return {"action": "relay", "reason": f"owner's turn ended without completion: {why}"}
        forced = _budget_forced(rec, now, spent, verdict) if v2 else None
        if forced:
            return {"action": "halt", "reason": forced}
        return {"action": "none", "reason": f"owner {verdict}: {why}"}
    return {"action": "none", "reason": f"unhandled state {state}"}


def _budget_forced(rec: dict, now: float, spent: str | None, verdict: str) -> str | None:
    """Spec 11.1 busy-owner bound (capsule-v2 only; callers gate on v2): the budget is soft until the
    turn ends, but not for ever. Past the wall grace after the pass that first saw it spent, the budget
    overrides the busy owner -- the halt enters RECOVERY, never SAFE_TO_FORGET."""
    if not (spent and verdict == LIVE and rec.get("budget_spent_at")):
        return None
    import gsd_epoch as ge
    grace = float((rec.get("wall") or {}).get("grace_s") or ge.WALL_GRACE_S)
    over = now - float(rec["budget_spent_at"])
    if over <= grace:
        return None
    return f"budget: {spent}; owner still busy {int(over)} s after it (grace {int(grace)} s): forced"


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


SLIM_PROFILES = ("slim-t1", "slim-t2")
SLIM_SETTINGS = Path(__file__).resolve().parent.parent / "vault" / "config" / "slim-critical-settings.json"
SLIM_DEFAULT_TOOLS = ("Read", "Grep", "Glob", "Bash", "Edit", "Write")
SLIM_DEFAULT_KERNEL = "You are a terse worker. Use only the tools given. Do exactly what is asked."


def slim_profile(rec: dict) -> str | None:
    """slim-t1 / slim-t2 when the mission asks for a slim worker: `rec["worker_profile"]`, else the
    profile of the first worker of the admitted route. Anything else keeps the `--bg` launch."""
    prof = rec.get("worker_profile")
    if not prof:
        workers = (rec.get("admission") or {}).get("workers") or []
        prof = next((w.get("profile") for w in workers if w.get("profile") in SLIM_PROFILES), None)
    return prof if prof in SLIM_PROFILES else None


def slim_argv(rec: dict, prompt: str, exe: str, profile: str, session_id: str | None = None) -> list[str]:
    """`claude -p` print-mode launch (measured floor 8.8k-13.5k vs 97k default). `=` forms only:
    PowerShell 5.1 drops empty args and --tools is variadic. slim-t2 carries the budget breaker via
    --settings, so it must keep the transcript the guard reads: `--no-session-persistence` there makes
    the guard deny after one grace call (measured 2026-10-06), so only slim-t1 (no hooks) passes it."""
    tools = rec.get("slim_tools") or [t.split("(")[0] for t in rec.get("allowed_tools") or []] or list(SLIM_DEFAULT_TOOLS)
    argv = [exe, "-p", "--setting-sources=local", "--strict-mcp-config", "--disable-slash-commands",
            f"--system-prompt={rec.get('card') or SLIM_DEFAULT_KERNEL}",
            "--exclude-dynamic-system-prompt-sections",
            f"--tools={','.join(dict.fromkeys(tools))}", "--output-format=json"]
    if profile == "slim-t1":
        argv.append("--no-session-persistence")
    else:
        argv.append(f"--settings={SLIM_SETTINGS}")
    argv.append(f"--model={rec.get('model') or 'sonnet'}")
    if session_id:
        argv.append(f"--session-id={session_id}")   # the id is OURS: no stdout to parse, budget file keyed to it
    return argv + [prompt]


def worker_argv(rec: dict, prompt: str, session_id: str | None = None) -> list[str]:
    """The launch command. `--bg` manages the session id (W0 E4) and does not inherit the
    launcher's environment (E3), so identity comes back on stdout (E5), nowhere else.

    ORDER IS LOAD-BEARING. `--add-dir <directories...>` and `--allowedTools <tools...>` are
    variadic: placed last, they swallowed the prompt as one more value and the worker
    started idle (W8, measured). So the variadic options come first and a non-variadic
    option (`--autocompact N`) sits between them and the prompt -- the exact shape W0
    launched successfully."""
    exe = os.environ.get("CPP_CLAUDE_EXE") or "claude"
    slim = slim_profile(rec)
    if slim:
        return slim_argv(rec, prompt, exe, slim, session_id)
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
    if capsule_v2(rec) or worker_mcp_verdict() == "APPLY":
        # Measured, not assumed: only a fresh APPLY from tools/worker_mcp_probe.sh strips MCP.
        # capsule-v2 always strips it (G9): the mutation guard sits on the Bash and Edit chains, so
        # an `mcp__*` tool would be a write path no guard sees before the successor certifies.
        argv += ["--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}']
    mode = rec.get("permission_mode")
    if mode:
        argv += ["--permission-mode", mode]
    if rec.get("model"):
        # TOK-18 gen 2 D2: a mission routes its own model. Without it every epoch inherited the
        # host default, and E1 ran 93 % Opus on mechanical work (gen2/evidence/D1-D2.md).
        argv += ["--model", str(rec["model"])]
    if rec.get("card"):
        # The card rides the launch itself. Measured W8: the worker's SessionStart hub never
        # completed in two of two launches (chain abandoned under starvation once, silent the
        # other), so a card delivered only by that hook would be lost. The launch argument has
        # no deadline and no hook between it and the model.
        argv += ["--append-system-prompt", rec["card"]]
    argv += ["--autocompact", rec.get("autocompact") or AUTOCOMPACT_SAFETY_NET]
    return argv + [prompt]


def slim_job_paths(mission_id: str, sid: str) -> tuple[Path, Path]:
    """Per-worker stdout (the `--output-format=json` result) and stderr files, in the mission store."""
    d = lr.state_dir() / "slim-jobs" / mission_id
    return d / f"{sid}.out.json", d / f"{sid}.err.txt"


def _spawn_detached(argv: list[str], cwd: str, out_path: Path, err_path: Path) -> int:
    """Start `claude -p` DETACHED (it is synchronous: the supervisor must not block on it) with its
    stdout/stderr going to files. Returns the pid."""
    import subprocess
    out_path.parent.mkdir(parents=True, exist_ok=True)
    kw: dict = {}
    if os.name == "nt":
        kw["creationflags"] = 0x00000008 | 0x00000200 | 0x08000000  # DETACHED | NEW_PROCESS_GROUP | NO_WINDOW
    else:
        kw["start_new_session"] = True
    with open(out_path, "wb") as so, open(err_path, "wb") as se:
        proc = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.DEVNULL, stdout=so, stderr=se, **kw)
    return proc.pid


def slim_budget_trip(sid: str | None) -> str | None:
    """Why the breaker stopped this worker, or None. A print-mode worker the breaker stopped still
    exits cleanly with is_error=false (measured 2026-10-06, m-e2e-red3: it obeyed the closeout
    advisory and reported), so a clean exit is not completion. Evidence is the guard's own state
    file: any closeout call spent means it tripped; tokens past stop means it would have.
    Unreadable files answer None here; the envelope was declared at launch, so their absence is
    the declare failure the ledger already records."""
    if not sid:
        return None
    try:
        import mission_spend as ms
        bpath = ms.budget_path(sid)
        budget = json.loads(bpath.read_text(encoding="utf-8-sig"))
        st = json.loads(bpath.with_name(f"session-budget-{sid}.state.json").read_text(encoding="utf-8-sig"))
    except (ImportError, ValueError, OSError):
        return None
    used, tokens, stop = int(st.get("closeout") or 0), int(st.get("tokens") or 0), int(budget.get("stop") or 0)
    if used > 0:
        return f"breaker tripped: {used} closeout call(s) spent at {tokens} processed (stop {stop})"
    if stop and tokens > stop:
        return f"breaker tripped: {tokens} processed > stop {stop}"
    return None


def slim_result(owner: dict | None, pid_alive=lr._pid_alive) -> dict:
    """Is a slim worker finished? `{"status": running|finished|failed|unknown, ...}`.

    Finished = its output file holds the result JSON (print mode writes it once, at the end), whatever
    the pid says: a reused pid must not keep a finished worker "running". No JSON and the process gone
    = failed; no JSON and the process alive = running; an unanswerable pid = unknown (never failed)."""
    owner = owner or {}
    data = None
    try:
        data = json.loads(Path(owner["out_path"]).read_text(encoding="utf-8-sig"))
    except (KeyError, TypeError, OSError, ValueError):
        pass
    if isinstance(data, list):   # `--output-format=json` on some builds: an event array, result last
        data = next((e for e in reversed(data) if isinstance(e, dict) and e.get("type") == "result"), None)
    if isinstance(data, dict) and ("result" in data or "is_error" in data):
        u = data.get("usage") or {}
        tokens = sum(int(u.get(k) or 0) for k in ("input_tokens", "cache_creation_input_tokens",
                                                   "cache_read_input_tokens", "output_tokens"))
        return {"status": "finished", "is_error": bool(data.get("is_error")),
                "session_id": data.get("session_id"), "tokens": tokens,
                "denials": len(data.get("permission_denials") or []),
                "tripped": slim_budget_trip(owner.get("session_id")),
                "result": str(data.get("result") or "")[:500]}
    pid = owner.get("pid")
    if not isinstance(pid, int):
        return {"status": "unknown", "why": "no pid recorded"}
    alive = pid_alive(pid)
    if alive is True:
        return {"status": "running", "pid": pid}
    if alive is None:
        return {"status": "unknown", "why": f"pid {pid} could not be checked"}
    return {"status": "failed", "why": f"pid {pid} exited and {owner.get('out_path')} holds no result JSON"}


def _launch_slim(rec: dict, prompt: str, epoch: int, now: float, spawner=None) -> dict:
    """Launch a slim (`claude -p`) worker and bind it. The session id is generated HERE and passed as
    --session-id, so nothing is parsed from stdout; the budget file is written from the admitted
    envelope BEFORE the process starts, or the breaker would be inert for its first calls."""
    mid = rec["mission_id"]
    sid = str(uuid.uuid4())
    out_path, err_path = slim_job_paths(mid, sid)
    _declare_worker_envelope(rec, sid)
    argv = worker_argv(rec, prompt, session_id=sid)
    # Start where the work lives. A mission armed from the main checkout records that checkout as
    # `cwd` and its worktree as `work_dir`; a print-mode worker's shell starts in whatever directory it
    # is spawned in, so spawning in `cwd` put epoch 4 of m-8bbdf725cd52 (2026-10-06) in a shared
    # checkout on another branch, one `git commit` away from landing there.
    wd = rec.get("work_dir")
    run_dir = wd if wd and Path(wd).is_dir() else rec["cwd"]
    try:
        pid = (spawner or _spawn_detached)(argv, run_dir, out_path, err_path)
    except Exception as exc:  # the launch itself could not happen
        why = f"{type(exc).__name__}: {exc}"
        lr.ledger_append(mid, "launch_failed", mission_id=mid, epoch=epoch, rc=None, bg_id=sid,
                         why="slim launch refused", detail=why[-300:])
        return {"ok": False, "epoch": epoch, "bg_id": sid, "why": "slim launch refused", "detail": why}
    adm = rec.get("admission") or {}
    used = ({"admission": {**adm, "consumed_epoch": epoch}}
            if rec.get("wu_packet") and adm.get("verdict") == "ADMISSIBLE" else {})
    rec = transition(mid, expect_epoch=epoch, expect_state=LAUNCHING, event="launched", now=now,
                     pending={**rec["pending"], "bg_id": sid}, **used)
    owner = {"session_id": sid, "pid": pid, "proc_start": None, "heartbeat_at": now, "epoch": epoch,
             "kind": "slim", "profile": slim_profile(rec), "out_path": str(out_path), "err_path": str(err_path)}
    transition(mid, expect_epoch=epoch, expect_state=LAUNCHING, event="worker_acked", now=now, state=RUNNING,
               pending=None, failed_launches=0, iterations=rec.get("iterations", 0) + 1, worker=sid, owner=owner)
    return {"ok": True, "epoch": epoch, "bg_id": sid, "pid": pid, "slim": True}


def launch_worker(mission_id: str, *, expect_epoch: int, expect_state, reason: str,
                  runner=None, now: float | None = None, note: str | None = None,
                  stop_runner=None, work_dir: str | None = None,
                  progress: dict | None = None, packet: dict | None = None, spawner=None) -> dict:
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
    try:
        # Asked BEFORE the claim: an unreadable work-unit packet spends no epoch and starts nothing.
        prompt = launch_prompt(rec)
    except MissionError as exc:
        lr.ledger_append(mission_id, "launch_refused_packet", mission_id=mission_id,
                         epoch=rec.get("epoch"), why=str(exc)[:300])
        return {"ok": False, "epoch": rec.get("epoch"), "bg_id": None, "why": str(exc), "detail": ""}
    # Route admission, also BEFORE the claim: an unadmitted work unit spends no epoch and starts nothing.
    why = admission_refusal(rec)
    if why:
        lr.ledger_append(mission_id, "launch_refused_admission", mission_id=mission_id,
                         epoch=rec.get("epoch"), why=why[:300])
        return {"ok": False, "epoch": rec.get("epoch"), "bg_id": None, "why": why, "detail": ""}
    why = envelope_refusal(rec)
    if why:
        lr.ledger_append(mission_id, "launch_refused_envelope", mission_id=mission_id,
                         epoch=rec.get("epoch"), why=why[:300])
        return {"ok": False, "epoch": rec.get("epoch"), "bg_id": None, "why": why, "detail": ""}
    if rec.get("wu_packet") and _admission_switch_off():
        lr.ledger_append(mission_id, "admission_bypassed", mission_id=mission_id, epoch=rec.get("epoch"),
                         verdict=(rec.get("admission") or {}).get("verdict"))
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
    if note is not None or rec.get("card") or (rec.get("capsule_key") and capsule_v2(rec)):
        # A capsule-v2 renewal's first worker has no note and no older card, yet it is a successor:
        # its certify instruction must ride the launch, not the SessionStart hook W8 saw fail.
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
    if slim_profile(rec):
        return _launch_slim(rec, prompt, epoch, now, spawner=spawner)
    # `prompt` was bound above (launch_prompt -> bind_workstream), not only at create: a record armed
    # before bind_workstream existed still carries the bare command, and its relay would put the
    # successor on the root milestone.
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
    adm = rec.get("admission") or {}
    # An admission pays for ONE launch (review F3): a successor would otherwise get the full envelope
    # again every epoch, with `remaining` measured only at admit time. The next launch re-admits.
    used = ({"admission": {**adm, "consumed_epoch": epoch}}
            if rec.get("wu_packet") and adm.get("verdict") == "ADMISSIBLE" else {})
    rec = transition(mission_id, expect_epoch=epoch, expect_state=LAUNCHING, event="launched",
                     now=now, pending={**rec["pending"], "bg_id": bg_id}, **used)
    _record_launch_account(bg_id)
    if rec.get("capsule_key") and capsule_v2(rec):
        _capsule_bind(rec, bg_id=bg_id)
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
            v2 = bool(rec.get("capsule_key")) and capsule_v2(rec)
            new = transition(rec["mission_id"], expect_epoch=rec["epoch"], expect_state=LAUNCHING,
                             event="worker_acked", now=now, state=RUNNING, pending=None,
                             failed_launches=0, iterations=rec.get("iterations", 0) + 1,
                             worker=session_id,
                             owner={"session_id": session_id, "pid": pid,
                                    "proc_start": proc_start, "heartbeat_at": now,
                                    "epoch": rec["epoch"], "kind": "background"},
                             # spec 3.5: the certification deadline runs from the successor's ack.
                             **({"capsule_acked_at": now} if v2 else {}))
            # The envelope first: it never raises, and a later step that does must not leave the
            # worker running unmetered (measured 2026-10-06 on adoption, see adopt_launched).
            _declare_worker_envelope(new, session_id)
            if v2:
                _capsule_bind(new, owner_session=session_id)
            return new
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


def set_owner_hold(mission_id: str, reason: str, now: float | None = None) -> dict:
    """Park a live mission (spec mission-owner-hold): plan_next answers none and renewal is refused
    until release_owner_hold. The record keeps its identity, epoch and state."""
    reason = (reason or "").strip()
    if not reason:
        raise MissionError("an owner hold needs a reason")
    rec = load(mission_id)
    if rec is None:
        raise MissionError(f"no mission {mission_id}")
    if rec["state"] in TERMINAL:
        raise MissionError(f"{mission_id} is {rec['state']}; there is nothing to hold")
    now = time.time() if now is None else now
    return transition(mission_id, expect_epoch=rec["epoch"], expect_state=rec["state"],
                      event="owner_hold_set", now=now, reason=f"owner hold: {reason[:300]}",
                      owner_hold={"reason": reason[:1000], "set_at": now})


def set_rollover_protocol(mission_id: str, protocol: str, now: float | None = None,
                          sessions: list[dict] | None = None, pid_alive=lr._pid_alive) -> dict:
    """Set `rollover_protocol` on an EXISTING mission (today only `arm` sets it). Same rules as arm:
    a known protocol and a permission mode that can run the successor's exam. Refused unless the
    mission is under owner hold or its owner is positively DEAD / absent: flipping the protocol under
    a live owner would change how that owner's own rollover is read mid-flight. CAS + ledger event
    through `transition`, exactly as set_owner_hold."""
    if protocol != CAPSULE_V2:
        raise MissionError(f"unknown rollover protocol {protocol!r} (only {CAPSULE_V2})")
    rec = load(mission_id)
    if rec is None:
        raise MissionError(f"no mission {mission_id}")
    if rec["state"] in TERMINAL:
        raise MissionError(f"{mission_id} is {rec['state']}; its protocol cannot change")
    if rec.get("permission_mode") not in CAPSULE_V2_MODES:
        raise MissionError(f"{CAPSULE_V2} needs permission mode {' or '.join(CAPSULE_V2_MODES)}, "
                           f"not {rec.get('permission_mode')!r}")
    if not rec.get("owner_hold") and rec.get("owner"):
        verdict, evidence = liveness(rec["owner"], sessions, pid_alive=pid_alive)
        if verdict != DEAD:
            raise MissionError(f"{mission_id} has a live owner ({verdict}: {evidence}); "
                               f"hold it first (`hold --mission {mission_id} --reason ...`)")
    now = time.time() if now is None else now
    return transition(mission_id, expect_epoch=rec["epoch"], expect_state=rec["state"],
                      event="rollover_protocol_set", now=now, rollover_protocol=protocol,
                      reason=f"rollover protocol set to {protocol}")


def _cost_breaker(rec: dict, now: float, measure=None, fingerprint=None) -> dict:
    """TOK-18 gen 2 D1: judge a mission that carries `token_estimate` against its measured spend
    (tools/mission_spend.py). A trip parks it with the Owner hold -- held, never halted or renewed --
    so the Owner sees estimate, actual and the cause before more is spent. Fail-open on a measuring
    error: the breaker is an extra stop, and a broken meter must not stop missions on its own.
    Returns the record as it now stands."""
    import mission_spend as ms
    mid = rec["mission_id"]
    try:
        spent = (measure or ms.processed_tokens)(rec)
        fp = (fingerprint or progress_fingerprint)(rec.get("work_dir") or rec["cwd"])
        verdict = ms.judge(rec, spent, fp)
    except Exception as exc:  # noqa: BLE001 -- recorded, never silent
        lr.ledger_append(mid, "cost_breaker_unmeasured", mission_id=mid,
                         error=f"{type(exc).__name__}: {exc}"[:300])
        return rec
    if verdict["trip"]:
        lr.ledger_append(mid, "cost_breaker_tripped", mission_id=mid, spent=spent,
                         estimate=rec.get("token_estimate"), reason=verdict["trip"])
        return set_owner_hold(mid, verdict["trip"], now=now)
    if verdict["mark"]:
        return transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                          event="cost_mark", now=now, cost_mark=verdict["mark"],
                          reason=f"progress fingerprint moved at {spent:,} processed")
    return rec


def release_owner_hold(mission_id: str, now: float | None = None) -> dict:
    """Return a held mission to normal supervision. The budget clock is not reset."""
    rec = load(mission_id)
    if rec is None:
        raise MissionError(f"no mission {mission_id}")
    if not rec.get("owner_hold"):
        raise MissionError(f"{mission_id} has no owner hold")
    return transition(mission_id, expect_epoch=rec["epoch"], expect_state=rec["state"],
                      event="owner_hold_released", now=now, owner_hold=None,
                      reason="owner hold released")


_COUNT_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*([kKmM]?)\s*$")
_MODEL_ALIASES = ("sonnet", "opus", "haiku", "fable")
_MODEL_ID_RE = re.compile(r"^claude-[a-z0-9][a-z0-9.\-]*$")


def _token_count(field: str, value) -> int:
    """`16000000`, `16M`, `300k`, `1.5m` -> a positive int; anything else is refused."""
    m = _COUNT_RE.match(str(value))
    n = int(float(m.group(1)) * {"": 1, "k": 1_000, "m": 1_000_000}[m.group(2).lower()]) if m else 0
    if n <= 0:
        raise MissionError(f"{field} must be a positive token count like 16M or 300k, not {value!r}")
    return n


def set_envelope(mission_id: str, *, token_estimate=None, model: str | None = None, autocompact=None,
                 wu_packet: str | None = None, continue_max_tokens=None, now: float | None = None) -> dict:
    """Set the launch envelope of a live mission (spec mission-envelope-and-compiled-wu): the token
    estimate the cost breaker judges, the worker model, its autocompact window, and the compiled
    work-unit packet launch_prompt sends instead of resume_command. Every value is validated before
    anything is written; the budget clock (created_at, cost_mark) is not reset."""
    changes: dict = {}
    if token_estimate is not None:
        changes["token_estimate"] = _token_count("token_estimate", token_estimate)
    if autocompact is not None:
        n = _token_count("autocompact", autocompact)
        changes["autocompact"] = f"{n // 1000}k" if n % 1000 == 0 else str(n)
    if model is not None:
        model = str(model).strip()
        if model not in _MODEL_ALIASES and not _MODEL_ID_RE.match(model):
            raise MissionError(f"model must be one of {', '.join(_MODEL_ALIASES)} or a claude- model id, "
                               f"not {model!r}")
        changes["model"] = model
    if wu_packet is not None:
        p = Path(wu_packet).expanduser().resolve()
        try:
            data = p.read_bytes() if p.is_file() else b""
        except OSError:
            data = b""
        if not data:
            raise MissionError(f"wu_packet {str(p)!r} is not an existing, non-empty file")
        import hashlib
        changes["wu_packet"] = {"path": str(p), "sha256": hashlib.sha256(data).hexdigest(),
                                "bytes": len(data), "set_at": time.time() if now is None else now}
    if continue_max_tokens is not None:
        changes["continue_max_tokens"] = _token_count("continue_max_tokens", continue_max_tokens)
    if not changes:
        raise MissionError("nothing to set: give --token-estimate, --model, --autocompact, --wu-packet "
                           "or --continue-max-tokens")
    rec = load(mission_id)
    if rec is None:
        raise MissionError(f"no mission {mission_id}")
    if rec["state"] in TERMINAL:
        raise MissionError(f"{mission_id} is {rec['state']}; its envelope cannot change")
    if not grammar_legacy() and ("autocompact" in changes or "wu_packet" in changes):
        why = window_refusal({**rec, **changes})
        if why:
            raise MissionError(why)
    shown = {k: (v["path"] if k == "wu_packet" else v) for k, v in changes.items()}
    old = {k: ((rec.get(k) or {}).get("path") if k == "wu_packet" else rec.get(k)) for k in changes}
    # C23b: a CHANGED packet is a new work unit. Record the epoch it was set at, so decide_turn_end can
    # tell an owner that predates it (owner epoch <= this) and start a fresh worker instead of resuming.
    prev = rec.get("wu_packet") or {}
    new = changes.get("wu_packet")
    if new and (prev.get("path"), prev.get("sha256")) != (new["path"], new["sha256"]):
        changes["wu_packet_epoch"] = rec["epoch"]
    return transition(mission_id, expect_epoch=rec["epoch"], expect_state=rec["state"],
                      event="envelope_set", now=now,
                      reason="envelope: " + "; ".join(f"{k} {old[k]} -> {shown[k]}" for k in shown),
                      **changes)


def _admission_switch_off() -> bool:
    return str(os.environ.get("CPP_ROUTE_ADMISSION") or "").strip().lower() in ("0", "off", "false")


# --------------------------------------------------------------------------- compiled grammar default
# spec compiled-grammar-default laws 1-4 and 7. One authority at the effect: launch_worker and
# gsd_epoch.continue_worker both ask envelope_refusal before they claim anything.
GRAMMAR_WINDOW_MARGIN = 40_000   # working margin over floor + packet, spec law 3
PACKET_GATE_TIMEOUT_S = 120
_GATE_RE = re.compile(r"^done_gate:[ \t]*(\S.*?)[ \t]*$", re.MULTILINE)


def grammar_legacy() -> bool:
    """Law 7: CPP_MISSION_GRAMMAR=legacy restores laws 2-5 to the behaviour before the default."""
    return str(os.environ.get("CPP_MISSION_GRAMMAR") or "").strip().lower() == "legacy"


def window_refusal(rec: dict, autocompact=None, *, floors_path: str | None = None) -> str | None:
    """Law 3: an explicit autocompact window must be >= the measured floor of the worker profile
    + the packet's bytes / 4 + a working margin. An unknown floor refuses, never a guess."""
    value = autocompact if autocompact is not None else rec.get("autocompact")
    if value in (None, ""):
        return None
    window = _token_count("autocompact", value)
    profile = rec.get("worker_profile") or "top-level-worker"
    try:
        import route_admission as ra
        floor = ra.load_floors(floors_path)["profiles"].get(profile, {}).get("floor")
    except (OSError, ValueError) as exc:
        return f"autocompact {value}: the floor table is unreadable ({exc}); the window cannot be judged"
    if isinstance(floor, bool) or not isinstance(floor, int) or floor <= 0:
        return f"autocompact {value}: no measured floor for worker profile {profile!r}; the window cannot be judged"
    pkt = rec.get("wu_packet") or {}
    pbytes = int(pkt.get("bytes") or 0)
    packet_tokens = -(-pbytes // 4)
    need = floor + packet_tokens + GRAMMAR_WINDOW_MARGIN
    if window < need:
        return (f"autocompact {value} ({window:,}) is below {need:,} = floor {floor:,} ({profile}) + "
                f"packet {packet_tokens:,} ({pbytes:,} bytes / 4) + margin {GRAMMAR_WINDOW_MARGIN:,}")
    return None


def envelope_refusal(rec: dict) -> str | None:
    """Laws 1-3 at the launch boundary: why this record may not start (or wake) a worker, or None.
    No token_estimate is refused unless the record carries an `unbounded` authority; absent is never
    read as unlimited. Legacy (law 7) bypasses and ledgers the refusal it would have made."""
    why = None
    unb = rec.get("unbounded") or {}
    if not rec.get("token_estimate") and not (unb.get("authority") or "").strip():
        why = ("no token envelope: set one with `envelope --token-estimate`, or arm with "
               "`--unbounded --authority <who decided, where recorded>`")
    if why is None:
        why = window_refusal(rec)
    if why is None:
        if not rec.get("token_estimate"):
            lr.ledger_append(rec["mission_id"], "unbounded_launch", mission_id=rec["mission_id"],
                             epoch=rec.get("epoch"), authority=str(unb.get("authority"))[:300])
        return None
    if grammar_legacy():
        lr.ledger_append(rec["mission_id"], "grammar_legacy_bypass", mission_id=rec["mission_id"],
                         epoch=rec.get("epoch"), law="envelope", why=why[:300])
        return None
    return why


def packet_done_gate(rec: dict) -> str | None:
    """Law 4: the first `done_gate:` line of the mission's compiled packet, or None."""
    pkt = rec.get("wu_packet")
    if not pkt:
        return None
    try:
        text = Path(pkt["path"]).read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return None
    m = _GATE_RE.search(text)
    return m.group(1) if m else None


def packet_gate_passed(rec: dict, now: float, *, gate_runner=None) -> dict | None:
    """Law 4: run the packet's done_gate in the record's work tree, bounded. Exit 0 -> a dict with the
    command and the output tail; a non-zero exit, a timeout or an unrunnable gate -> None (today's path).
    Legacy skips the gate and ledgers it."""
    gate = packet_done_gate(rec)
    if not gate:
        return None
    mid = rec["mission_id"]
    if grammar_legacy():
        lr.ledger_append(mid, "grammar_legacy_bypass", mission_id=mid, epoch=rec.get("epoch"),
                         law="packet_gate", why=f"done_gate not run: {gate[:200]}")
        return None
    import subprocess
    cwd = rec.get("work_dir") or rec["cwd"]
    run = gate_runner or (lambda cmd, wd: subprocess.run(
        cmd, shell=True, cwd=wd, capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=int(os.environ.get("CPP_PACKET_GATE_TIMEOUT") or PACKET_GATE_TIMEOUT_S)))
    try:
        r = run(gate, cwd)
    except Exception as exc:  # noqa: BLE001 -- a timeout or an unrunnable gate is not a pass
        lr.ledger_append(mid, "packet_gate_unanswered", mission_id=mid, epoch=rec.get("epoch"),
                         gate=gate[:200], error=f"{type(exc).__name__}: {exc}"[:300])
        return None
    if r.returncode != 0:
        return None
    tail = ANSI_RE.sub("", (r.stdout or "") + (r.stderr or "")).strip()[-400:]
    lr.ledger_append(mid, "packet_gate_passed", mission_id=mid, epoch=rec.get("epoch"), gate=gate[:200],
                     cwd=cwd, tail=tail)
    return {"gate": gate, "tail": tail}


def admit_route(mission_id: str, route_path: str, *, floors_path: str | None = None,
                now: float | None = None, measure=None) -> dict:
    """Judge the mission's compiled work unit against its route (tools/route_admission.py) and record
    the verdict, bound to the packet's and the route file's sha256. Every verdict is recorded, so a
    refusal is visible; only ADMISSIBLE lets launch_worker start a worker. The budget still remaining
    comes from the cost breaker's own numbers (trip ratio x estimate - attributed spend): a unit that
    cannot finish before the breaker trips is DEFER, never launched to be held halfway."""
    import mission_spend as ms
    import route_admission as ra
    now = time.time() if now is None else now
    rec = load(mission_id)
    if rec is None:
        raise MissionError(f"no mission {mission_id}")
    if rec["state"] in TERMINAL:
        raise MissionError(f"{mission_id} is {rec['state']}; nothing to admit")
    pkt = rec.get("wu_packet")
    if not pkt:
        raise MissionError("admission judges a compiled work unit: set one with `envelope --wu-packet` first")
    pkt_digest = _packet_digest(pkt["path"])
    if pkt_digest is None:
        raise MissionError(f"wu_packet {pkt['path']!r} is missing or empty")
    p = Path(route_path).expanduser().resolve()
    try:
        route = json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise MissionError(f"route {str(p)!r} is unreadable: {exc}") from exc
    remaining = None
    if rec.get("token_estimate"):
        spent = (measure or ms.processed_tokens)(rec)
        if spent is not None:
            ratio = float(rec.get("token_trip_ratio") or ms.DEFAULT_TRIP_RATIO)
            remaining = int(ratio * int(rec["token_estimate"])) - spent
    try:
        res = ra.admit(route, ra.load_floors(floors_path), remaining=remaining)
    except ValueError as exc:
        raise MissionError(f"route {str(p)!r}: {exc}") from exc
    admission = {"verdict": res["verdict"], "route_path": str(p), "route_file_sha256": _packet_digest(str(p)),
                 "packet_sha256": pkt_digest, "envelope": res["envelope"],
                 "need_with_margin": res.get("need_with_margin"), "remaining": remaining,
                 "reasons": res["reasons"][:6], "at": now,
                 "workers": [{k: w.get(k) for k in ("name", "profile", "calls", "floor")}
                             for w in res.get("workers") or []]}
    # The route's worker profile is recorded on the mission, so launch reads one field. Only an
    # admission-set value is ever replaced; a profile an operator set by hand stays.
    slim = next((w["profile"] for w in admission["workers"] if w["profile"] in SLIM_PROFILES), None)
    prof = ({"worker_profile": slim, "worker_profile_src": "admission"} if slim
            else {"worker_profile": None, "worker_profile_src": None} if rec.get("worker_profile_src") == "admission"
            else {})
    return transition(mission_id, expect_epoch=rec["epoch"], expect_state=rec["state"],
                      event="route_admission", now=now, admission=admission, **prof,
                      reason=f"route {res['verdict']}: " + ("; ".join(res["reasons"]) or "fits")[:280])


def admission_refusal(rec: dict, *, for_launch: bool = True) -> str | None:
    """Why this mission's compiled work unit must not be sent, or None. A mission without a packet
    (the GSD resume route) is not judged here. `for_launch` (a new worker) also requires an UNUSED
    admission; continuing the session that admission already launched does not (it runs inside the
    envelope it was declared at ack), but its verdict, packet and route are checked all the same."""
    pkt = rec.get("wu_packet")
    if not pkt or _admission_switch_off():
        return None
    adm = rec.get("admission") or {}
    if adm.get("verdict") != "ADMISSIBLE":
        return (f"work unit not admitted (verdict {adm.get('verdict') or 'none'}): run "
                f"`gsd_mission.py admit --mission {rec['mission_id']} --route <route.json>`")
    if for_launch and adm.get("consumed_epoch") is not None:
        return (f"the admission was used by epoch {adm['consumed_epoch']}: admit again so the remaining "
                f"budget is re-measured (`gsd_mission.py admit --mission {rec['mission_id']} --route ...`)")
    if adm.get("packet_sha256") != _packet_digest(pkt["path"]):
        return "the packet changed since it was admitted: admit it again"
    if adm.get("route_file_sha256") != _packet_digest(adm.get("route_path") or ""):
        return "the route file changed or vanished since admission: admit it again"
    return None


def _declare_worker_envelope(rec: dict, sid: str | None) -> None:
    """The admitted envelope becomes the worker's SESSION envelope, enforced call by call by
    hooks/session_budget_guard.js. Recorded either way, never silent."""
    adm = rec.get("admission") or {}
    if not sid or not rec.get("wu_packet") or adm.get("verdict") != "ADMISSIBLE":
        return
    env = adm.get("envelope") or {}
    mid = rec["mission_id"]
    try:
        import mission_spend as ms
        ms.declare(sid, int(env["target"]), int(env["warn"]), int(env["stop"]), calls_estimate=env.get("calls"))
        lr.ledger_append(mid, "worker_envelope_declared", mission_id=mid, worker=sid,
                         target=env["target"], stop=env["stop"], calls=env.get("calls"))
    except Exception as exc:  # noqa: BLE001 -- recorded, never silent
        lr.ledger_append(mid, "worker_envelope_failed", mission_id=mid, worker=sid,
                         error=f"{type(exc).__name__}: {exc}"[:300])


# Carried into every compiled launch: the three misses of the first packet run (cwops plan, Results).
COMPILED_WU_LESSONS = (
    "1. Derive state from `git log` and the phase directory listing, not STATE.md alone.",
    "2. Decide anything within your authority yourself. Ending your turn on a question is a failure: "
    "write the open point to the progress file named in the packet and continue, or stop.",
    "3. Before any evidence run, check that its scripts await every effect they start.",
)


def _packet_digest(path: str) -> str | None:
    import hashlib
    try:
        data = Path(path).read_bytes()
    except OSError:
        return None
    return hashlib.sha256(data).hexdigest() if data else None


def launch_prompt(rec: dict) -> str:
    """What a launched or continued worker is told. Without a compiled work-unit packet: the bound
    resume command, byte for byte as before. With one: the packet (path + its CURRENT hash) and the
    lessons, and no GSD command -- the GSD re-entry is the overhead the packet exists to skip.
    Raises MissionError when the packet cannot be read: a worker never starts without it."""
    pkt = rec.get("wu_packet")
    if not pkt:
        return bind_workstream(rec["resume_command"], rec.get("workstream"))
    digest = _packet_digest(pkt["path"])
    if digest is None:
        raise MissionError(f"wu_packet {pkt['path']!r} is missing or empty")
    drift = "" if digest == pkt.get("sha256") else f" (changed since it was set: was {str(pkt.get('sha256'))[:12]})"
    return "\n".join([
        f"Execute the compiled work unit in {pkt['path']} (sha256 {digest[:12]}{drift}).",
        "Read that file first and in full; it is your scope, done-gate and budget. Do not run GSD "
        "commands unless the packet names one.",
        *COMPILED_WU_LESSONS,
    ])


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
        (f"Compiled work unit: {rec['wu_packet']['path']} (your launch prompt; not the resume command)"
         if rec.get("wu_packet") else
         f"Resume command: {bind_workstream(rec['resume_command'], rec.get('workstream'))}"),
        *([f"WORKSTREAM {rec['workstream']}: before any GSD step run `node "
           f"~/.claude/gsd-core/bin/gsd-tools.cjs query workstream.set {rec['workstream']} --raw "
           f"--cwd .` (session-local pointer; gsd_run calls do not forward --ws). The repo's ROOT "
           f"milestone belongs to another track -- never plan or execute it."]
          if rec.get("workstream") else []),
        # G22: before the GSD facts and the note, so the byte cap cuts those and never this.
        *_capsule_card_lines(rec),
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
        # 2026-09-30 (m-3e3a400b52d4): the successor obeyed "EnterWorktree path=..." and parked on a
        # permission prompt although EnterWorktree is in --allowedTools -- a worktree outside the
        # launch directory still asks. Worker 1 of the same mission moved with the shell and never
        # prompted, and the supervisor follows the transcript cwd either way. So: shell, never the tool.
        parts[2:2] = [f"WORK TREE: the work is in {wd} -- enter it first with the shell: "
                      f"Set-Location '{wd}' (PowerShell). Do NOT call EnterWorktree: it raises a permission "
                      "prompt nobody is watching.",
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


CWD_ALIGN_BLOCKING = ("behind_dirty", "diverged", "unreadable")


def align_cwd(cwd: str, work_dir: str | None, proven_workstream: str | None = None) -> dict:
    """Make the mission cwd carry the work before a worker is launched in it.

    The worker is LAUNCHED in the cwd (workspace trust is exact-path) and /gsd-autonomous reads
    `.planning/` there, so a cwd that lags its work_dir briefs the successor with a stale roadmap.
    Measured 2026-09-30 (Brand #001, m-cdd8fc64ed65): the 09-28 handback advanced only the
    worktree; the cwd stayed on the seed, and the renewed worker redid Phase 1 on a new worktree
    branched from the seed -- 73 commits of finished work invisible to it, 22 merge conflicts.

    Statuses: same / aligned / ahead (cwd already contains the work) / unrelated (different
    repository: not ours to judge) -> no action; fast_forwarded (cwd was a clean ancestor:
    `merge --ff-only`, nothing can be lost); behind_dirty / diverged / unreadable -> the caller
    must NOT launch (CWD_ALIGN_BLOCKING).

    diverged_followed (not blocking): the caller PROVED the work_dir (`proven_workstream`: the
    predecessor worked there, on that workstream), it is a worktree top of the cwd's repository,
    and it contains the cwd's latest commit to that workstream. The divergence is then a peer's
    history in a shared checkout, not a stale roadmap; nothing is moved. Measured 2026-10-03:
    m-fdefb0fca0c0 and m-876f8b5a904a HELD for good because peers committed to the main checkout."""
    import subprocess
    if not work_dir or os.path.normcase(str(Path(work_dir).resolve())) == os.path.normcase(str(Path(cwd).resolve())):
        return {"status": "same", "detail": ""}
    here, there = _git_toplevel_and_common(cwd), _git_toplevel_and_common(work_dir)
    if not here or not there:
        return {"status": "unreadable", "detail": f"git could not read cwd={cwd} or work_dir={work_dir}"}
    if here[1] != there[1]:
        return {"status": "unrelated", "detail": "work_dir is not a worktree of the cwd's repository"}
    g = os.environ.get("CPP_GIT_EXE") or r"C:\Program Files\Git\cmd\git.exe"
    if not Path(g).exists():
        g = "git"

    def git(path, *args):
        return subprocess.run([g, "-C", path, *args], capture_output=True, text=True, timeout=60)

    try:
        hc = git(cwd, "rev-parse", "HEAD").stdout.strip()
        hw = git(work_dir, "rev-parse", "HEAD").stdout.strip()
        if not hc or not hw:
            return {"status": "unreadable", "detail": "HEAD unreadable"}
        facts = {"cwd_head": hc[:12], "work_dir_head": hw[:12]}
        if hc == hw:
            return {"status": "aligned", "detail": "", **facts}
        if git(cwd, "merge-base", "--is-ancestor", hw, hc).returncode == 0:
            return {"status": "ahead", "detail": "cwd already contains the work_dir head", **facts}
        if git(cwd, "merge-base", "--is-ancestor", hc, hw).returncode != 0:
            if (proven_workstream
                    and there[0] == os.path.normcase(str(Path(work_dir).resolve()))
                    and _worktree_carries_workstream(work_dir, cwd, proven_workstream)):
                return {"status": "diverged_followed", "detail": f"cwd {hc[:12]} and work_dir {hw[:12]}"
                        f" have diverged, but the work_dir is a proven worktree carrying"
                        f" {proven_workstream}'s latest roadmap; following it, nothing moved", **facts}
            return {"status": "diverged", "detail": f"cwd {hc[:12]} and work_dir {hw[:12]} have diverged;"
                    " a worker launched here would branch from a lineage without the work", **facts}
        dirty = git(cwd, "status", "--porcelain", "--untracked-files=no").stdout.strip()
        if dirty:
            return {"status": "behind_dirty", "detail": f"cwd {hc[:12]} is behind work_dir {hw[:12]}"
                    " but has uncommitted tracked changes; not fast-forwarding over them", **facts}
        ff = git(cwd, "merge", "--ff-only", hw)
        if ff.returncode != 0:
            return {"status": "behind_dirty", "detail": "fast-forward refused: "
                    + ((ff.stderr or ff.stdout).strip()[-200:]), **facts}
        return {"status": "fast_forwarded", "detail": f"cwd {hc[:12]} -> {hw[:12]}", **facts}
    except Exception as exc:  # never launch on an unanswered question
        return {"status": "unreadable", "detail": f"{type(exc).__name__}: {exc}"}


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
    v2 = bool(rec.get("capsule_key")) and capsule_v2(rec)
    new = transition(rec["mission_id"], expect_epoch=rec["epoch"], expect_state=LAUNCHING,
                     event="worker_adopted", now=now, state=RUNNING, pending=None,
                     failed_launches=0, iterations=rec.get("iterations", 0) + 1, worker=sid,
                     reason="host witness; worker's own ack absent (no card this epoch)",
                     owner={"session_id": sid, "pid": row.get("pid"), "proc_start": None,
                            "heartbeat_at": now or time.time(), "epoch": rec["epoch"],
                            "kind": "background"},
                     **({"capsule_acked_at": now or time.time()} if v2 else {}))
    # The envelope BEFORE the marker: 2026-10-06 (m-8bbdf725cd52 epoch 2) _arm_worker_marker raised
    # MarkerError on a record whose resume command does not start with '/', and the adopted W0r worker
    # ran with no session envelope until it was declared by hand.
    _declare_worker_envelope(new, sid)
    _arm_worker_marker(new, sid)
    if v2 and sid:
        _capsule_bind(new, owner_session=sid)
    return new


def owner_idle(owner: dict | None, sessions: list[dict] | None) -> bool:
    """True only when the host lists the owner as idle: its turn has ended."""
    if not owner or sessions is None:
        return False
    row = next((s for s in sessions if s.get("sessionId") == owner.get("session_id")), None)
    if not row or row.get("waitingFor") or row.get("state") == "blocked":
        return False
    # A background worker whose turn ended reads `status:"idle"` (and later host `done`, which
    # liveness calls DEAD). A bare `state:"blocked"` is NOT an ended turn: the host job needs
    # something (see liveness); until 2026-09-28 it was read as idle and relayed.
    return row.get("status") == "idle"


def host_job_needs(session_id: str | None) -> str | None:
    """What the host says a blocked job needs, from ~/.claude/jobs/<short id>/state.json
    (`needs`, else `detail`). None when unreadable -- the caller's reason then stands alone.
    Read BEFORE anything stops the worker: a stop overwrites the file with `stopped`, which is
    how the m-66ebaaa0324e evidence was lost."""
    if not session_id:
        return None
    root = Path(os.environ.get("CPP_CLAUDE_JOBS_DIR") or (lr.CLAUDE_HOME / "jobs"))
    try:
        d = json.loads((root / str(session_id)[:8] / "state.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(d, dict):
        return None
    text = d.get("needs") or (d.get("detail") if d.get("state") == "blocked" else None)
    return " ".join(str(text).split())[:300] if text else None


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
            pooled = _daemon_pooled(argv)
            if pooled:
                # 2026-10-05 (GEX44 m-f011d7fdebc9): the daemon hosts background sessions in pooled
                # processes; after host `done` the pid lives on as a spare carrying no --session-id.
                # It is the daemon's, never killed -- and holds nothing of this worker, so it is
                # released. Refusing here blocked the relay on every pass.
                return True, f"host {row.get('state')}; pid {pid} is a daemon {pooled} process, released (not ours)"
            return False, (f"pid {pid} still alive after {int(wait_s)} s; not terminated: "
                           + ("argv unreadable" if not argv else "argv is not this worker"))
        return False, f"pid {pid} still alive after {int(wait_s)} s"
    return True, "stopped; no pid to wait on"


def _daemon_pooled(argv: str | None) -> str | None:
    """The pooled-process kind when argv is the Claude daemon's own process (`claude bg-spare ...`,
    `claude bg-pty-host ...`): the subcommand right after the executable, or the `--bg-spare` flag.
    A word elsewhere in an argv (a prompt, a path) does not count."""
    tokens = (argv or "").split()
    if len(tokens) >= 2 and tokens[1] in ("bg-spare", "bg-pty-host"):
        return tokens[1]
    return "bg-spare" if "--bg-spare" in tokens else None


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
RENEWAL_CARRIED_ENVELOPE = ("token_estimate", "token_trip_ratio", "model", "autocompact",
                            "continue_max_tokens", "wu_packet", "mission_terms", "note", "goal", "unbounded")


def renewal_refusal(rec: dict, halt_reason: str, gsd_outcome: str | None) -> str | None:
    """Why this budget-halted mission must NOT be renewed, or None when it may be.
    Positive test: only a halt the supervisor made for budget, with GSD saying work remains."""
    if os.environ.get("CPP_MISSION_RENEW", "").lower() == "off":
        return "renewal disabled (CPP_MISSION_RENEW=off)"
    if rec.get("owner_hold"):
        return f"owner hold: {rec['owner_hold'].get('reason')}"
    if "budget:" not in (halt_reason or ""):
        return f"halt was not for budget: {halt_reason}"
    if gsd_outcome != "OK":
        return f"GSD answered {gsd_outcome}, not work-remains"
    if int(rec.get("renewal") or 0) >= MAX_RENEWALS:
        return f"renewal cap {MAX_RENEWALS} reached for lineage {rec.get('lineage_id') or rec['mission_id']}"
    if rec.get("epoch") == 0:   # recorded zero only: a record without the field is unknown, not zero
        # spec goal-governed-mission-control C3: no worker ever launched. Measured 2026-10-06
        # (m-8c64d4f52fc9): a cwd divergence held every launch for 23 h (470 rows, 0 launches) and
        # the budget halt renewed it like a mission that had worked. A fresh budget cures nothing.
        return "never launched: every launch of this attempt was held, a fresh budget changes nothing"
    if not rec.get("token_estimate") and bounded_renewal_mode() == "enforce":
        return UNBOUNDED_RENEWAL
    return None


UNBOUNDED_RENEWAL = ("unbounded: no token_estimate, so the successor would launch with no cost breaker "
                     "and no route admission (set one with `envelope --token-estimate`)")


def bounded_renewal_mode() -> str:
    """spec goal-governed-mission-control C2: shadow (default) | enforce | off. Measured 2026-10-05:
    the unbounded budget renewal m-98719dd9d1b1 ran 99 calls / 27.7M processed in 27 min."""
    v = str(os.environ.get("CPP_MISSION_BOUNDED_RENEWAL") or "shadow").strip().lower()
    return v if v in ("shadow", "enforce", "off") else "shadow"


def _renewal_why_not(rec: dict, halt_reason: str, st: dict, halt_wd: str, fingerprint=None) -> str | None:
    """renewal_refusal plus T5's unchanged-tree refusal: the one renewal decision, asked by the legacy
    halt after the HALTED write and by capsule-v2 before anything is sealed (spec 11.1)."""
    why_not = renewal_refusal(rec, halt_reason, st.get("outcome"))
    origin = rec.get("progress_origin")
    if not why_not and origin:
        # T5: all 18 renewals of the 6 capped lineages produced 0 commits. A
        # mission whose tree never moved does not earn a fresh budget. A tree
        # that cannot be measured is not "unchanged": it still renews.
        fp_now = (fingerprint or progress_fingerprint)(halt_wd)
        if fp_now is not None and fp_now == origin:
            why_not = "no progress in this mission (work tree unchanged since its first launch)"
    if not why_not:
        # GGMC C4: a renewal is a new attempt of the same Goal and obeys the same authority as `arm`.
        try:
            key = goal_key(rec.get("cwd") or "", rec.get("workstream"))
            why_not = goal_refusal(goal_conflicts(key, exclude=rec["mission_id"]),
                                   (rec.get("goal") or {}).get("unit"))
        except Exception as exc:  # noqa: BLE001 -- an unanswered goal check never renews
            why_not = f"goal check failed: {type(exc).__name__}: {exc}"[:300]
    return why_not


def renew_mission(rec: dict, now: float | None = None, capsule_key: str | None = None,
                  continuity_from: dict | None = None) -> dict:
    """A PREPARED successor of a budget-halted mission: same work, fresh budget, every Owner
    directive carried. The normal launch path starts it on the next pass.

    capsule-v2 (spec 11.1): `capsule_key` is the capsule the halted mission left, so the renewal's
    first worker is a successor that certifies it -- a renewal is never silently legacy."""
    now = time.time() if now is None else now
    new = create(rec["cwd"], rec["resume_command"], workstream=rec.get("workstream"),
                 max_cycles=rec.get("max_cycles"), max_hours=rec.get("max_hours"),
                 now=now, permission_mode=rec.get("permission_mode"),
                 allowed_tools=rec.get("allowed_tools"), add_dirs=rec.get("add_dirs"),
                 wall=rec.get("wall"),
                 # G20: a renewal keeps the protocol it was armed with, or it would rotate legacy.
                 rollover_protocol=rec.get("rollover_protocol"))
    carried = {"renewed_from": rec["mission_id"],
               "lineage_id": rec.get("lineage_id") or rec["mission_id"],
               "renewal": int(rec.get("renewal") or 0) + 1,
               "directives": list(rec.get("directives") or [])}
    if rec.get("work_dir"):
        carried["work_dir"] = rec["work_dir"]
    # spec goal-governed-mission-control C1: the route travels with the work. Never `admission`:
    # a renewed unit is re-admitted against a re-measured budget.
    for k in RENEWAL_CARRIED_ENVELOPE:
        if rec.get(k) not in (None, "", [], {}):
            carried[k] = rec[k]
    if rec.get("wu_packet"):
        carried["wu_packet_epoch"] = 0
    if not rec.get("token_estimate") and bounded_renewal_mode() == "shadow":
        lr.ledger_append(rec["mission_id"], "renewal_unbounded_shadow", mission_id=rec["mission_id"],
                         reason=UNBOUNDED_RENEWAL)
    v2_carry = {}
    if capsule_key:
        v2_carry["capsule_key"] = capsule_key
    if continuity_from:
        v2_carry["continuity_from"] = continuity_from
    new = transition(new["mission_id"], expect_epoch=new["epoch"], expect_state=PREPARED,
                     event="mission_renewed", now=now, **carried, **v2_carry)
    lr.ledger_append(rec["mission_id"], "mission_renewed", mission_id=rec["mission_id"],
                     successor=new["mission_id"], renewal=carried["renewal"],
                     **({"capsule_key": capsule_key} if capsule_key else {}))
    return new


# --------------------------------------------------------------------------- capsule-v2 (T6)
# Every function here is reached only through a `capsule_v2(rec)` branch (spec 3.1). The adapter
# (tools/mission_capsule.py) owns compile/seal/gate/arm/bind; rollover.py owns the format, the
# marker and "certified". What lives here is WHEN each is asked, and what the mission does with
# the answer (spec sections 8 and 9).
def _capsule_card_lines(rec: dict) -> list[str]:
    """G22: the successor's first duty. Only when a predecessor sealed a capsule for it
    (`capsule_key`): the first worker of a mission has nothing to certify."""
    if rec.get("rollover_protocol") != CAPSULE_V2 or not rec.get("capsule_key"):
        return []
    import mission_capsule as mc
    tool = mc.TOOL   # spec 11.5: the same constant the precert marker carries for the guard's deny text
    return ["",
            f"CAPSULE-V2 SUCCESSOR: your predecessor sealed capsule {rec['capsule_key']}. Until you certify",
            "  it, a guard refuses every edit, write and mutating command. Do this FIRST:",
            f"  1. python {tool} resume --mission {rec['mission_id']}   (prints the bootstrap and an exam)",
            "  2. read the goal file it names, answer from the tree and GSD NOW, run the certify command it prints.",
            "  Only RESUME_CERTIFIED restores your authority; a refusal names what disagreed -- re-read, retry."]


def _capsule_bind(rec: dict, **ids) -> str:
    """G7: name the armed successor as the host reported it (bg id at launch, session at its ack).
    Never raised into a launch or an ack -- the worker exists either way, and the guard still
    matches the launch cwd inside its window -- but always ledgered by name."""
    try:
        import mission_capsule as mc
        mc.bind_successor(rec["mission_id"], worker_name(rec), **ids)
        return "bound"
    except Exception as exc:  # noqa: BLE001 -- see docstring: recorded, never swallowed silently
        why = f"{type(exc).__name__}: {exc}"
        lr.ledger_append(rec["mission_id"], "capsule_bind_failed", mission_id=rec["mission_id"],
                         epoch=rec["epoch"], error=why[:300])
        return why


def _capsule_marker(rec: dict) -> dict | None:
    """The precert marker of THIS epoch's worker, or None (no marker, or one naming another worker)."""
    import mission_capsule as mc
    import rollover as ro
    mk = ro.precert_read(rec["mission_id"], mc.state_dir())
    return mk if mk and mk.get("worker") == worker_name(rec) else None


def _capsule_certify_check(rec: dict, row: dict, now: float, sessions=None, pid_alive=lr._pid_alive,
                           stop_runner=None) -> bool:
    """Spec 3.5 + 11.3: a successor that has not certified within CAPSULE_CERTIFY_DEADLINE_S of its ack
    is STOPPED (it never had mutation authority, so there is nothing to seal) and the next pass replaces
    it on the SAME capsule -- up to MAX_SUCCESSOR_ATTEMPTS per capsule; at the cap the mission parks
    BLOCKED (`resume_not_certified`, a G4 hold) for a human. Certification lifts the hold.
    True when this pass acted for the mission."""
    mid = rec["mission_id"]
    hold = rec.get("capsule_hold") or {}
    mk = _capsule_marker(rec)
    if rec["state"] == BLOCKED and hold.get("kind") == "resume_not_certified":
        if mk and mk.get("certified_at"):
            transition(mid, expect_epoch=rec["epoch"], expect_state=BLOCKED, event="mission_unblocked",
                       now=now, state=RUNNING, capsule_hold=None,
                       reason=f"successor certified {rec.get('capsule_key')}")
            row["action"] = "capsule_certified"
            return True
        return False
    acked = rec.get("capsule_acked_at")
    if (rec["state"] == RUNNING and acked and mk and not mk.get("certified_at")
            and now - float(acked) > CAPSULE_CERTIFY_DEADLINE_S):
        key = rec.get("capsule_key")
        why = (f"resume_not_certified: worker {worker_name(rec)} acked {int(now - float(acked))} s ago "
               f"and has not certified {key}")
        attempts = dict(rec.get("capsule_attempts") or {})
        n = int(attempts.get(key) or 0) + 1
        attempts[key] = n
        if n < MAX_SUCCESSOR_ATTEMPTS:
            ok, how = stop_owner(rec.get("owner"), sessions, pid_alive=pid_alive, runner=stop_runner)
            if not ok:
                # Not counted: the next pass retries the stop of the same successor.
                row["held"] = f"{why}; stop not confirmed ({how}), retried next pass"
                return True
            transition(mid, expect_epoch=rec["epoch"], expect_state=RUNNING, event="capsule_successor_stopped",
                       now=now, capsule_attempts=attempts, capsule_acked_at=None,
                       reason=f"{why}; stopped ({how}), successor {n} of {MAX_SUCCESSOR_ATTEMPTS} on this capsule")
            row["action"], row["reason"], row["stop"] = "capsule_successor_stopped", why, how
            return True
        transition(mid, expect_epoch=rec["epoch"], expect_state=RUNNING, event="mission_blocked",
                   now=now, state=BLOCKED, reason=why, capsule_attempts=attempts,
                   capsule_hold={"kind": "resume_not_certified", "reason": why, "since": now})
        row["action"], row["reason"] = "capsule_blocked", why
        return True
    return False


def _capsule_note_request() -> str:
    """Spec 11.4: the one question asked of an idle owner that left no note (NOTE_TAG is defined below)."""
    return ("capsule-v2: this worker is about to be rotated and left no hand-off note. Do not start new work. "
            f"End this reply with a line starting `{NOTE_TAG}` followed by: what you finished, what is half "
            "done (files, uncommitted changes, background tasks), and the next concrete step.")


def _owner_note(src: dict) -> tuple[str, dict | None]:
    """(note, packet) the owner of `src` left: an explicit `handoff --note` -- while in HANDOFF, or while
    `pending` still names THIS owner's hand-off (a refused seal moves the mission to BLOCKED and must not
    lose the note it was refused for; spec 11.4) -- else its transcript's last hand-off note."""
    owner_sid = (src.get("owner") or {}).get("session_id")
    pend = src.get("pending") or {}
    explicit = src["state"] == HANDOFF or (pend.get("kind") == "handoff" and owner_sid
                                           and pend.get("from") == owner_sid)
    note = ((src.get("note") if explicit else "")
            or (handoff_note_from_transcript(owner_sid) if owner_sid else "") or "")
    return note, (src.get("packet") if explicit else None)


def _capsule_seal(rec: dict, origins: list[str], *, work_dir: str, capsule_io: dict | None = None,
                  gate: bool = True, note_rec: dict | None = None) -> tuple[str | None, dict | None, list[str]]:
    """Seal the capsule of `rec`'s epoch, trying `origins` in order: (origin, seal, reasons) for the
    first SAFE_TO_FORGET -- re-judged by `gate_before_stop` when a stop follows -- else (None, None,
    reasons). The note and packet are the predecessor's own (`note_rec`, default `rec`): an explicit
    `handoff --note` only while THIS owner is in HANDOFF, else its transcript's last hand-off."""
    import mission_capsule as mc
    note, packet = _owner_note(note_rec or rec)
    key = mc.capsule_key(rec)
    reasons: list[str] = []
    for origin in origins:
        # The capsule's times are rollover's own: the seal row is stamped by its ledger's wall clock,
        # and the gate's freshness is judged against that same clock. Passing this pass's `now`
        # mixed two clocks -- harmless only while they happen to agree (measured in T6's suite: an
        # injected now read a fresh seal as 103 days old).
        cap = mc.compile_mission_capsule(rec, origin=origin, note=note, work_dir=work_dir, packet=packet,
                                         **(capsule_io or {}))
        seal = mc.seal_mission(cap)
        if seal["verdict"] != "SAFE_TO_FORGET":
            reasons.append(f"{origin} {seal['verdict']}: {'; '.join(seal.get('reasons') or [])}")
            continue
        if gate:
            # Re-judged immediately before the stop (section 9): the bytes as sealed, fresh, uncertified.
            g = mc.gate_before_stop(key)
            if g["verdict"] != "SAFE_TO_FORGET":
                reasons.append(f"{origin} gate {g['verdict']}: {'; '.join(g.get('reasons') or [])}")
                continue
        return origin, seal, reasons
    return None, None, reasons


def _capsule_authorize_stop(rec: dict, origin: str, seal: dict, now: float) -> dict:
    """G3: the one row that licenses stopping the outgoing worker, bound to the capsule's sha."""
    import mission_capsule as mc
    key = mc.capsule_key(rec)
    return transition(rec["mission_id"], expect_epoch=rec["epoch"], expect_state=rec["state"],
                      event="outgoing_stop_authorized", now=now, capsule_key=key,
                      capsule_stop_authorized={"epoch": rec["epoch"], "origin": origin, "at": now,
                                               "sha256": (seal.get("receipt") or {}).get("sha256")},
                      capsule_first_refused_at=None, capsule_hold=None,
                      reason=f"capsule {key} sealed ({origin}): SAFE_TO_FORGET")


def _halt_continuity(rec: dict, reason: str, st: dict | None, halt_wd: str, sessions, pid_alive,
                     now: float, fingerprint=None, capsule_io: dict | None = None) -> tuple[dict, dict, bool]:
    """Spec 11.1, BEFORE the HALTED write of a capsule-v2 mission: (rec, continuity, renew).

    The Owner's rule (2026-10-05): a resumable halt is a continuity transition, so the outgoing
    worker is sealed before the planned stop; when the budget overrides it the halt enters RECOVERY
    (sealed after the stop, from durable state), never SAFE_TO_FORGET; and a renewal is never
    silently legacy. The renewal decision comes first, so nothing is sealed for a lineage that will
    not renew."""
    import mission_capsule as mc
    why_not = (_renewal_why_not(rec, reason, st, halt_wd, fingerprint) if st is not None
               else f"halt was not for budget: {reason}")
    if why_not:
        return rec, {"kind": "none", "reason": f"no renewal: {why_not}"}, False
    key = rec.get("capsule_key")
    mk = _capsule_marker(rec)
    if (key and not _capsule_retired(key)
            and ((mk is not None and not mk.get("certified_at")) or rec["state"] in (PREPARED, LAUNCHING))):
        # The worker in hand never certified (or never started): nothing of its own to seal. The
        # capsule its predecessor left is still the one to certify -- only while it is NOT retired: a
        # certified key handed on would ask the renewal's successor to certify what can no longer be
        # certified (a budget halt during a same-session continuation, review 2026-10-05).
        return rec, {"kind": "inherited", "capsule_key": key,
                     "reason": f"no certified worker since {key}: the renewal inherits it"}, True
    owner = _halt_owner(rec)
    if not owner:
        return rec, {"kind": "none", "reason": "no worker of this mission ever ran: nothing to carry"}, True
    verdict, why = liveness(owner, sessions, pid_alive)
    if verdict == UNKNOWN:
        # Spec 5: a recovery successor beside a worker that may still run would be two with authority.
        return rec, {"kind": "refused", "reason": f"owner UNKNOWN ({why}): a successor could run beside it"}, False
    if verdict == LIVE and owner_idle(owner, sessions):
        # The turn ended: the hand-off is sealable now, and the budget is the override -- no grace
        # wait before the degraded fallback.
        origin, seal, reasons = _capsule_seal({**rec, "owner": owner}, ["worker_handoff", "supervisor_fallback"],
                                              work_dir=halt_wd, capsule_io=capsule_io)
        if origin:
            rec = _capsule_authorize_stop(rec, origin, seal, now)
            return rec, {"kind": "handoff", "origin": origin, "capsule_key": mc.capsule_key(rec),
                         "reason": f"sealed {origin} before the halt"}, True
        return rec, {"kind": "recovery", "reason": "budget overrides; hand-off seals refused: "
                                                   + " | ".join(reasons)[:400]}, True
    return rec, {"kind": "recovery", "reason": f"budget overrides owner {verdict}: {why}"[:400]}, True


def _capsule_retired(key: str) -> bool:
    """True once rollover has certified (retired) this capsule: it can never be certified again."""
    import mission_capsule as mc
    import rollover as ro
    return ro.capsule_path(key, mc.state_dir()).with_suffix(".certified").exists()


def _halt_owner(rec: dict) -> dict | None:
    """The worker a halt acts on: the owner, or -- while a same-session continuation is LAUNCHING --
    the session being resumed (`previous_owner`; continue_worker clears `owner` on purpose)."""
    if rec.get("owner"):
        return rec["owner"]
    if (rec.get("pending") or {}).get("kind") == "turn_continuation":
        return rec.get("previous_owner")
    return None


def _halt_recover(halted: dict, pre: dict, cont: dict, halt_wd: str, now: float,
                  capsule_io: dict | None = None) -> dict:
    """Spec 11.1 `recovery`, AFTER the stop: a degraded capsule from the halted record's durable
    state. The mission records RECOVERY; rollover's verdict is read as eligibility only. Refused ->
    `refused`, and the renewal is refused with it."""
    import mission_capsule as mc
    mid = halted["mission_id"]
    src = halted if halted.get("owner") else {**halted, "owner": _halt_owner(pre)}
    try:
        origin, seal, reasons = _capsule_seal(src, ["recovery"], work_dir=halt_wd, capsule_io=capsule_io,
                                              gate=False, note_rec=pre)
    except Exception as exc:  # noqa: BLE001 -- the record is already terminal: no later pass revisits it,
        # so an exception left as `recovery` with no key and no renewal would be silent for ever.
        origin, seal, reasons = None, None, [f"recovery seal raised {type(exc).__name__}: {exc}"]
    if origin:
        new = {**cont, "origin": "recovery", "capsule_key": mc.capsule_key(halted),
               "sha256": (seal.get("receipt") or {}).get("sha256")}
        transition(mid, expect_epoch=halted["epoch"], expect_state=HALTED, event="continuity_recovery",
                   now=now, continuity=new, capsule_key=new["capsule_key"],
                   reason=f"RECOVERY capsule {new['capsule_key']} sealed after the halt")
        return new
    new = {"kind": "refused", "reason": f"recovery seal refused: {' | '.join(reasons)}"[:600]}
    transition(mid, expect_epoch=halted["epoch"], expect_state=HALTED, event="continuity_refused",
               now=now, continuity=new, reason=new["reason"])
    return new


def _capsule_ask_note(rec: dict, row: dict, sessions, pid_alive, runner, stop_runner, now: float,
                      progress: dict | None, work_dir: str | None) -> None:
    """Spec 11.4: continue the SAME session once with the hand-off question. The asked-flag is written
    FIRST, so a stop or wake that fails falls through to the degraded fallback on the next turn end
    instead of asking again for ever. A same-session continuation hands nothing over (spec 3.6)."""
    import gsd_epoch as ge
    mid = rec["mission_id"]
    rec = transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"], event="capsule_note_asked",
                     now=now, capsule_note_asked={"epoch": rec["epoch"], "at": now},
                     reason="capsule-v2: no hand-off note at the turn end; asking the worker once")
    ok, how = stop_owner(rec.get("owner"), sessions, pid_alive=pid_alive, runner=stop_runner)
    row["stop"] = how
    if not ok:
        row["held"] = f"capsule-v2 note request: the owner did not stop ({how}); fallback at its next turn end"
        return
    row["continue"] = ge.continue_worker(
        mid, rec, prompt=_capsule_note_request(),
        decision={"decision": ge.CONTINUE, "cause": ge.TURN_CONTINUATION,
                  "reason": "capsule-v2: hand-off note requested before rotation"},
        runner=runner, stop_runner=stop_runner, now=now, progress=progress, work_dir=work_dir)
    row["action"] = "capsule_note_requested"


def _seal_refusal_fp(work_dir: str) -> str | None:
    """Spec 11.2: what a re-judge could see differently -- HEAD and the dirty-path count, from git
    alone (no GSD query). None when git cannot answer: unmeasured, never "unchanged"."""
    import hashlib
    import rollover as ro
    try:
        f = ro.repo_facts(work_dir)
    except Exception:  # noqa: BLE001 -- unmeasured; the time backoff still bounds the re-judges
        return None
    if f.get("state") != "OK" or not f.get("head"):
        return None
    return hashlib.sha256(f"{f['head']}|{len(f.get('dirty') or [])}".encode("utf-8")).hexdigest()[:16]


def _seal_refused_hold(prev: dict, why: str, now: float, work_dir: str) -> dict:
    """The `seal_refused` hold after one more refusal: provider_breaker's backoff model (one source for
    the numbers), counted per fingerprint -- a changed tree starts the count again."""
    import provider_breaker as pb
    fp = _seal_refusal_fp(work_dir)
    n = int(prev.get("retries") or 0) + 1 if fp is not None and prev.get("fingerprint") == fp else 1
    return {"kind": "seal_refused", "reason": why[:300], "since": prev.get("since") or now,
            "retries": n, "next_at": now + min(pb.BACKOFF_BASE_S * 2 ** (n - 1), pb.BACKOFF_CAP_S),
            "quarantined": n >= pb.QUARANTINE_AFTER, "fingerprint": fp, "fp_dir": work_dir}


def _seal_rejudge_wait(rec: dict, now: float) -> str | None:
    """Why an idle owner under a `seal_refused` hold is NOT re-judged on this pass, or None when it is.
    A hold written before 11.2 (no `retries`) is re-judged as T6 did."""
    hold = rec.get("capsule_hold") or {}
    if hold.get("kind") != "seal_refused" or "retries" not in hold:
        return None
    fp = _seal_refusal_fp(hold.get("fp_dir") or rec.get("work_dir") or rec["cwd"])
    if fp is not None and fp != hold.get("fingerprint"):
        return None                                    # the tree moved: what refused may be gone
    n = hold.get("retries")
    if hold.get("quarantined"):
        return (f"capsule-v2 seal re-judge QUARANTINED after {n} refusals on an unchanged tree; "
                f"re-judged when the tree changes: {hold.get('reason')}")
    wait = float(hold.get("next_at") or 0) - now
    if wait > 0:
        return f"capsule-v2 seal re-judge backed off {int(wait)} s more (refusal {n}): {hold.get('reason')}"
    return None


def _capsule_rotate(rec: dict, row: dict, act: str, sessions, pid_alive, now: float,
                    work_dir: str | None, capsule_io: dict | None = None) -> dict | None:
    """The v2 gate between ROTATE and stop_owner (spec 3.3; G3/G5/G6/G21). Returns the record to
    go on with when the outgoing worker may be stopped; None when it may not -- held or BLOCKED, the
    reason in the row and the ledger, NOTHING stopped (spec 5: never a stopped worker without a
    sealed capsule)."""
    import gsd_epoch as ge
    import mission_capsule as mc
    mid = rec["mission_id"]
    verdict, why = liveness(rec.get("owner"), sessions, pid_alive)
    mk = _capsule_marker(rec)
    if mk is not None and not mk.get("certified_at"):
        # This worker was launched for a capsule and never certified it, so the guard kept it from
        # mutating: it has nothing of its own to seal. Dead, its successor inherits the same
        # capsule; alive, nothing rotates and the certification deadline decides.
        if verdict == DEAD:
            row["capsule"] = f"inherited {rec.get('capsule_key')}: worker {worker_name(rec)} died uncertified"
            if rec.get("capsule_hold"):
                rec = transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                                 event="capsule_inherited", now=now, capsule_hold=None, reason=row["capsule"])
            return rec
        row["held"] = f"capsule-v2: worker {worker_name(rec)} has not certified {rec.get('capsule_key')}; no rotation"
        lr.ledger_append(mid, "capsule_rotation_held", mission_id=mid, epoch=rec["epoch"], reason=row["held"])
        return None
    key = mc.capsule_key(rec)
    auth = rec.get("capsule_stop_authorized") or {}
    if rec.get("capsule_key") == key and auth.get("epoch") == rec["epoch"]:
        # G3: a later pass retrying an unfinished stop reuses the authorization; it never re-judges.
        row["capsule"] = f"stop authorized for {key} ({auth.get('origin')}), reused"
        return rec
    idle = verdict == LIVE and owner_idle(rec.get("owner"), sessions)
    done = act == "replace" and verdict == DEAD and ge.turn_ended_as_done(rec, sessions)
    grace = float((rec.get("wall") or {}).get("grace_s") or ge.WALL_GRACE_S)
    first = rec.get("capsule_first_refused_at")
    overdue = first is not None and now - float(first) >= grace
    if idle or done:
        origins = ["worker_handoff"] + (["supervisor_fallback"] if overdue else [])
        if not _owner_note(rec)[0]:
            # Spec 11.4: a turn that ended with no note is asked for one ONCE per epoch, in the same
            # session (nothing sealed, nothing handed over); still none at its next turn end -> the
            # degraded fallback at once, not after a 30-minute grace that cannot produce a note.
            asked = (rec.get("capsule_note_asked") or {}).get("epoch") == rec["epoch"]
            if not asked and ge.continuation_enabled():
                row["capsule_note_request"] = True
                row["held"] = "capsule-v2: the worker left no hand-off note; asking it once (same session)"
                return None
            if asked:
                origins = ["supervisor_fallback"]
    elif verdict == DEAD:
        origins = ["recovery"]                       # G21: a crashed predecessor, degraded
    else:
        # G3: a busy owner's turn has not ended, so no hand-off seal. G5: past the grace, counted
        # from the FIRST refusal, a degraded capsule from durable state stops it anyway.
        origins = ["supervisor_fallback"] if overdue else []
    wd = work_dir or rec.get("work_dir") or rec["cwd"]
    origin, seal, reasons = _capsule_seal(rec, origins, work_dir=wd, capsule_io=capsule_io)
    if not origins:
        reasons = [f"owner {verdict} and its turn has not ended: {why}"]
    if origin:
        rec = _capsule_authorize_stop(rec, origin, seal, now)
        row["capsule"] = f"sealed {key} ({origin})"
        return rec
    reason = " | ".join(reasons)[:600]
    row["capsule"] = f"refused {key}: {reason}"
    if "supervisor_fallback" in origins or "recovery" in origins:
        # Spec 3.5: not even a capsule from durable state is sealable -- BLOCKED, worker NOT stopped.
        why_b = f"capsule-v2 seal impossible for {key}: {reason}"
        prev = rec.get("capsule_hold") or {}
        held = rec["state"] == BLOCKED and prev.get("kind") == "seal_refused"
        # Spec 11.2: the hold carries its own backoff, so the next re-judge waits for a tree change
        # or the backoff instead of costing a GSD query and ledger rows on every pass.
        hold = _seal_refused_hold(prev if held else {}, why_b, now, wd)
        if held:
            transition(mid, expect_epoch=rec["epoch"], expect_state=BLOCKED, event="capsule_seal_refused",
                       now=now, capsule_hold=hold, reason=reason)
        else:
            transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"], event="mission_blocked",
                       now=now, state=BLOCKED, reason=why_b, capsule_hold=hold)
        row["blocked"] = why_b
    elif first is None:
        transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"], event="capsule_seal_refused",
                   now=now, capsule_first_refused_at=now, reason=reason)
        row["held"] = f"capsule-v2 seal refused; fallback clock started (grace {int(grace)} s): {reason}"
    else:
        lr.ledger_append(mid, "capsule_seal_refused", mission_id=mid, epoch=rec["epoch"], reason=reason)
        row["held"] = (f"capsule-v2 seal refused ({int(now - float(first))} of {int(grace)} s to the "
                       f"fallback): {reason}")
    return None


def _capsule_arm(rec: dict, row: dict) -> bool:
    """Spec 3.3: the successor's marker exists BEFORE it is spawned, or it is not spawned (section
    9). The key is the record's own field (G6), never epoch arithmetic."""
    import mission_capsule as mc
    try:
        mc.arm_successor(rec, capsule_key=rec["capsule_key"])
        return True
    except Exception as exc:  # noqa: BLE001 -- refused as a hold, ledgered by name
        why = f"capsule-v2: successor marker not armed ({type(exc).__name__}: {exc}); nothing spawned"
        lr.ledger_append(rec["mission_id"], "capsule_arm_failed", mission_id=rec["mission_id"],
                         epoch=rec["epoch"], error=why[:300])
        row["held"] = why
        return False


def supervise(now: float | None = None, dry_run: bool = False, sessions=None,
              gsd_status=None, runner=None, stop_runner=None, pid_alive=lr._pid_alive,
              fingerprint=None, capsule_io: dict | None = None, gate_runner=None) -> list[dict]:
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
        try:
            v2 = capsule_v2(rec)   # False for every record without the field, before any I/O
        except Exception as exc:  # noqa: BLE001 -- isolated per mission, see below
            # Review M1 (2026-10-03): this ran outside the per-mission isolation, so an import or
            # permission error on ONE v2 record ended the pass for every mission after it. Fail
            # closed for that mission only: undecidable is never "legacy", which would rotate it
            # unsealed. Nothing is done for it this pass; the rest are supervised.
            err = f"capsule-v2 undecidable: {type(exc).__name__}: {exc}"
            out.append({"mission_id": mid, "state": rec["state"], "epoch": rec["epoch"],
                        "action": "none", "reason": err, "error": err})
            try:
                lr.ledger_append(mid, "supervise_error", mission_id=mid, error=err[:300])
            except Exception:  # noqa: BLE001 -- the row still carries the error
                pass
            continue
        if not dry_run and rec.get("token_estimate") and not rec.get("owner_hold"):
            rec = _cost_breaker(rec, now)
        plan = plan_next(rec, now, sessions, pid_alive, v2=v2)
        row = {"mission_id": mid, "state": rec["state"], "epoch": rec["epoch"], **plan}
        out.append(row)
        if dry_run:
            continue
        try:
            reap(rec, row)
            if row.get("orphans_stopped"):
                row["action"] = "reaped" if plan["action"] in ("none", "await") else plan["action"]
            if v2 and rec.get("capsule_key") and _capsule_certify_check(rec, row, now, sessions, pid_alive,
                                                                        stop_runner):
                continue
            if (v2 and plan["action"] == "none" and rec["state"] in (RUNNING, BLOCKED)
                    and not rec.get("budget_spent_at") and budget_exhausted(rec, now)
                    and liveness(rec.get("owner"), sessions, pid_alive)[0] == LIVE):
                # Spec 11.1 busy-owner bound: the first pass that sees the budget spent under a busy
                # owner starts the clock plan_next halts on after the wall grace.
                rec = transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                                 event="budget_spent_noted", now=now, budget_spent_at=now,
                                 reason=f"budget spent ({budget_exhausted(rec, now)}) under a busy owner")
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
            if act in ("relay", "replace", "halt", "launch") and rec.get("wu_packet") and rec.get("epoch"):
                # Law 4: a packet ends its mission. Asked before the supervisor continues, rotates,
                # renews or relaunches it; a pass turns the mission COMPLETED and nothing starts.
                gate = packet_gate_passed(rec, now, gate_runner=gate_runner)
                if gate:
                    done = transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                                      event="mission_completed", now=now, state=COMPLETED, pending=None,
                                      reason=f"packet done_gate passed ({plan['reason']}): {gate['gate']}")
                    reap(done, row)
                    row["action"], row["gate"] = "completed", gate["gate"]
                    continue
            if v2 and act == "relay" and rec["state"] == BLOCKED:
                # Spec 11.2 (L1): asked BEFORE GSD, so a backed-off re-judge costs no query and no row.
                wait = _seal_rejudge_wait(rec, now)
                if wait:
                    row["held"] = wait
                    continue
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
                if v2:
                    # Spec 11.1 (M2): the halt is a continuity transition, decided BEFORE the stop.
                    pre = rec
                    rec, cont, renew = _halt_continuity(rec, plan["reason"], st, halt_wd, sessions, pid_alive,
                                                        now, fingerprint, capsule_io)
                    halted = transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                                        event="mission_halted", now=now, state=HALTED, pending=None,
                                        reason=plan["reason"], continuity=cont)
                    reap(halted, row)  # a halt changes the record; stop the world to match it
                    if cont["kind"] == "recovery":
                        cont = _halt_recover(halted, pre, cont, halt_wd, now, capsule_io)
                        renew = cont["kind"] == "recovery"
                    if cont["kind"] == "refused":
                        lr.ledger_append(mid, "renewal_refused_no_capsule", mission_id=mid, epoch=halted["epoch"],
                                         reason=cont["reason"])
                    row["continuity"] = cont["kind"]
                    if renew:
                        row["renewed_as"] = renew_mission(
                            halted, now=now, capsule_key=cont.get("capsule_key"),
                            continuity_from={"mission_id": mid, "kind": cont["kind"]})["mission_id"]
                    elif st is not None:
                        row["renewal"] = f"not renewed: {cont['reason']}"
                    continue
                halted = transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                                    event="mission_halted", now=now, state=HALTED, pending=None,
                                    reason=plan["reason"])
                reap(halted, row)  # a halt changes the record; stop the world to match it
                if st is not None:
                    why_not = _renewal_why_not(halted, plan["reason"], st, halt_wd, fingerprint)
                    if why_not:
                        row["renewal"] = f"not renewed: {why_not}"
                    else:
                        row["renewed_as"] = renew_mission(halted, now=now)["mission_id"]
            elif act == "slim_finished":
                s = plan["slim"]
                stopped = s.get("tripped") or ("worker reported is_error" if s["is_error"] else None)
                transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                           event="slim_worker_finished", now=now, state=HALTED if stopped else COMPLETED,
                           pending=None, slim_result=s, worker=s.get("session_id"),
                           reason=f"{plan['reason']}; {stopped}" if stopped else plan["reason"])
            elif act == "surface_blocked":
                if rec["state"] != BLOCKED:
                    needs = host_job_needs((rec.get("owner") or {}).get("session_id"))
                    reason = f"{plan['reason']}; host needs: {needs}" if needs else plan["reason"]
                    row["reason"] = reason
                    transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                               event="mission_blocked", now=now, state=BLOCKED,
                               reason=reason)
            elif act == "surface_unknown":
                # Once per epoch: every 5-minute pass would otherwise add the same row.
                if not any(e.get("event") == "owner_unknown" and e.get("epoch") == rec["epoch"]
                           for e in lr.ledger_events(mid)):
                    lr.ledger_append(mid, "owner_unknown", mission_id=mid, epoch=rec["epoch"],
                                     state=rec["state"], reason=plan["reason"])
            elif act == "adopt":
                lrow = launched_row(rec.get("pending"), sessions)
                new = adopt_launched(rec, lrow, now=now)
                if lrow.get("state") == "blocked" or lrow.get("waitingFor"):
                    # The worker exists and is already waiting on something before its first
                    # turn (2026-09-28: every m-66ebaaa0324e worker, 0 transcripts). Surface it
                    # on THIS pass, in the host's words, while its job file still holds them.
                    needs = host_job_needs(lrow.get("sessionId") or lrow.get("id"))
                    reason = (f"launched worker blocked before its first turn: host state "
                              f"{lrow.get('state')}"
                              + (f"; waiting for {lrow['waitingFor']}" if lrow.get("waitingFor") else "")
                              + (f"; host needs: {needs}" if needs else ""))
                    transition(mid, expect_epoch=new["epoch"], expect_state=RUNNING,
                               event="mission_blocked", now=now, state=BLOCKED, reason=reason)
                    row["action"], row["reason"] = "adopted_blocked", reason
            elif act == "unblock":
                transition(mid, expect_epoch=rec["epoch"], expect_state=BLOCKED,
                           event="mission_unblocked", now=now, state=RUNNING, gsd_hold=None,
                           reason=plan["reason"])
            elif act in ("launch", "replace", "relay"):
                # Ask GSD before ANY successor: a background worker that finished its turn reads
                # host `done` (W8), which plans a REPLACE, not a relay -- and a worker that just
                # completed the milestone must not be followed by another one.
                work_dir = None
                proven_ws = None
                if act in ("relay", "replace") and rec.get("owner"):
                    hold = provider_hold(rec, now)
                    if hold:
                        # The successor would meet the same refusal: hold, spending no epoch.
                        # tools/provider_breaker.py: quota keeps this exact row; auth, transient
                        # failures and repeated instant deaths back off or quarantine.
                        # GGMC C5: the row is written when the hold CHANGES, not on every pass.
                        import mission_sleep as ms
                        if hold.get("class", "quota") == "quota":
                            row["held"] = f"provider quota until {int(hold['until'])}: {hold['reason']}"
                            sleep_on_change(rec, "provider_quota", ms.provider_wake(hold), "quota_held", now,
                                            until=hold["until"], reason=hold["reason"])
                        else:
                            until = hold.get("until")
                            row["held"] = (f"provider {hold['class']} "
                                           f"{'QUARANTINED' if hold.get('quarantine') else f'until {int(until)}'}"
                                           f" (streak {hold.get('streak')}): {hold['reason']}")
                            sleep_on_change(rec, f"provider_{hold['class']}", ms.provider_wake(hold),
                                            "provider_held", now, until=until, reason=hold["reason"],
                                            provider_class=hold["class"], streak=hold.get("streak"),
                                            quarantine=bool(hold.get("quarantine")))
                        continue
                if act in ("relay", "replace") and rec.get("owner"):
                    # Judge (and brief) where the predecessor actually worked. Measured M6: the
                    # run lived in a git worktree while the mission's cwd kept a reset roadmap,
                    # so asking GSD there would read 1/8 for ever and never complete.
                    ew = effective_workdir(rec["owner"]["session_id"], rec["cwd"], rec.get("workstream"))
                    work_dir = ew or rec.get("work_dir")
                    # A worktree effective_workdir followed is PROVEN (the predecessor acted on this
                    # workstream there and it carries the roadmap): align_cwd may follow a diverged
                    # cwd then. A recorded work_dir alone proves nothing.
                    if ew and ew != rec["cwd"]:
                        proven_ws = rec.get("workstream")
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
                        outcome = st.get("outcome")
                        row["held"] = f"gsd {outcome}: {st.get('reason')}"
                        prev = rec.get("gsd_hold") or {}
                        same = prev.get("outcome") == outcome
                        hold = {"outcome": outcome, "n": int(prev.get("n") or 0) + 1 if same else 1,
                                "since": prev.get("since") if same else now, "reason": st.get("reason")}
                        bound = GSD_HOLD_BLOCK_AFTER.get(outcome)
                        if bound and hold["n"] >= bound and rec["state"] != BLOCKED:
                            # Bounded silence: RUNNING with an idle owner and a refusal that
                            # waiting has not cleared is not healthy; say so where status reads.
                            why = (f"gsd {outcome} on {hold['n']} consecutive passes "
                                   f"({int(now - float(hold['since'] or now))} s): {st.get('reason')}"
                                   f" -- no relay until GSD answers OK")
                            transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                                       event="mission_blocked", now=now, state=BLOCKED,
                                       gsd_hold=hold, reason=why)
                            row["blocked"] = why
                        else:
                            transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                                       event="relay_held", now=now, gsd_hold=hold,
                                       reason=f"gsd {outcome}: {st.get('reason')}")
                        continue
                    if rec.get("gsd_hold"):
                        # GSD answered OK: the hold is over. Leave BLOCKED (if the bound had
                        # blocked it) before relaying, so every later CAS sees RUNNING.
                        rec = transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                                         event=("mission_unblocked" if rec["state"] == BLOCKED
                                                else "gsd_hold_cleared"),
                                         now=now, state=RUNNING, gsd_hold=None,
                                         reason=f"gsd OK: {st.get('reason')}")
                # The single pre-launch gate (tools/mission_launch_gate.py): a renewed successor
                # inherits its predecessor's provider hold, and on a declared mission plane a
                # measured NOT_READY env refuses. Asked before anything below stops, continues or
                # launches, so a refusal spends no epoch and stops nothing. A gate that cannot run
                # proceeds as before, visibly.
                try:
                    import mission_launch_gate as mlg
                    gate = mlg.refusal(rec, act, now)
                except Exception as exc:  # noqa: BLE001
                    gate = None
                    lr.ledger_append(mid, "launch_gate_unavailable", mission_id=mid,
                                     error=f"{exc.__class__.__name__}: {exc}"[:200])
                if gate:
                    row["launch_gate"] = gate.get("verdict")
                    if gate.get("refuse"):
                        row["held"] = gate.get("reason")
                        s = gate.get("sleep")
                        if s:
                            sleep_on_change(rec, s["cause"], s["wake"], s["event"], now, **s["fields"])
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
                                               f"ended with no commit or work-tree change",
                                        # Spec 11.1: terminal (Invariant 9), and stated as such for v2.
                                        **({"continuity": {"kind": "none", "reason": "no_progress is terminal: "
                                                           "no renewal, nothing carried"}} if v2 else {}))
                    reap(halted, row)
                    row["action"] = "halt"
                    continue
                continuing = turn_end is not None and turn_end["decision"] == "continue"
                # T7 C12 (capsule-v2 only): a same-session continuation that failed leaves LAUNCHING with
                # `owner` None on purpose (continue_worker); the session it tried to resume is still the
                # worker of this epoch. Skipping the seal for it armed the replacement with the OLD key --
                # possibly a capsule already certified, which no successor can ever certify again.
                v2_owner = (rec.get("owner") or _halt_owner(rec)) if v2 else None
                if v2 and act in ("relay", "replace") and v2_owner and not continuing:
                    # capsule-v2 ROTATE: seal, gate, authorize -- or hold with nothing stopped. Same-
                    # session continuation hands nothing over and takes no capsule (spec 3.6).
                    rotated = _capsule_rotate({**rec, "owner": v2_owner}, row, act, sessions, pid_alive, now,
                                              work_dir, capsule_io)
                    if rotated is None:
                        if row.pop("capsule_note_request", None):
                            _capsule_ask_note({**rec, "owner": v2_owner}, row, sessions, pid_alive, runner,
                                              stop_runner, now, progress, work_dir)
                        continue
                    rec = rotated
                stop_target = rec.get("owner") or v2_owner
                if act in ("relay", "replace") and stop_target:
                    # A replaced owner is DEAD by the host's word, and its pid can still outlive
                    # that word (W0 E13): wait for it too, or the successor overlaps it.
                    ok, why = stop_owner(stop_target, sessions, pid_alive=pid_alive,
                                         runner=stop_runner)
                    row["stop"] = why
                    if not ok:
                        continue  # the next pass retries; nothing launched beside a live worker
                if turn_end is not None and turn_end["decision"] == "continue":
                    import gsd_epoch as ge
                    # Review F2: the continuation sends the packet too. A packet edited in place, or a
                    # re-admit that recorded RECOMPILE/DEFER, stops here; no launch either (it would be
                    # refused for the same reason, after align_cwd had already moved the cwd).
                    cwhy = admission_refusal(rec, for_launch=False)
                    if cwhy:
                        lr.ledger_append(mid, "continue_refused_admission", mission_id=mid,
                                         epoch=rec["epoch"], why=cwhy[:300])
                        row["action"], row["why"] = "continue_refused_admission", cwhy
                        continue
                    row["continue"] = ge.continue_worker(
                        mid, rec, prompt=launch_prompt(rec),
                        decision=turn_end, runner=runner, stop_runner=stop_runner, now=now,
                        progress=progress, work_dir=work_dir)
                    row["action"] = "continue"
                    continue
                # The successor is launched in the cwd and reads its roadmap there: the cwd must
                # carry the work first (align_cwd; measured Brand #001 2026-09-30).
                aligned = align_cwd(rec["cwd"], work_dir or rec.get("work_dir"), proven_workstream=proven_ws)
                row["cwd_align"] = aligned["status"]
                if aligned["status"] == "fast_forwarded":
                    lr.ledger_append(mid, "cwd_fast_forwarded", mission_id=mid, epoch=rec["epoch"],
                                     detail=aligned["detail"])
                elif aligned["status"] == "diverged_followed":
                    lr.ledger_append(mid, "cwd_diverged_followed", mission_id=mid, epoch=rec["epoch"],
                                     detail=aligned["detail"])
                elif aligned["status"] in CWD_ALIGN_BLOCKING:
                    why = f"launch held: cwd not aligned with work_dir ({aligned['status']}): {aligned['detail']}"
                    wake = {"kind": "cwd_aligned", "cwd": rec["cwd"], "work_dir": work_dir or rec.get("work_dir"),
                            "status": aligned["status"]}
                    import mission_sleep as ms
                    if not ms.same(rec, ms.entry("launch_cwd", wake, rec["epoch"], why, now)):
                        # GGMC C5: both rows only when the hold changed (1,530 of 1,661 were repeats).
                        lr.ledger_append(mid, "launch_held_cwd", mission_id=mid, epoch=rec["epoch"],
                                         status=aligned["status"], detail=aligned["detail"])
                        sleep_on_change(rec, "launch_cwd", wake, "launch_held", now, set_reason=True, reason=why)
                    row["held"] = why
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
                if (v2 and rec.get("capsule_key") and act in ("relay", "replace", "launch")
                        and not _capsule_arm(rec, row)):
                    # spec 3.3: no marker, no spawn. `launch` too (spec 11.1): a renewal that carries a
                    # capsule starts its first worker as that capsule's successor.
                    continue
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


# --------------------------------------------------------------------------- goal authority (GGMC C4)
# spec goal-governed-mission-control C4: the Goal (a workstream of a repository) is the authority; a
# mission is a disposable attempt at it. Measured 2026-10-06: create() refused only a live record with
# the SAME id, so a fresh `arm` on a workstream whose attempt sits under an Owner hold (KSR recon-factory,
# InfinityOps odr-device-trust) would have started a second attempt beside the hold.
def goal_key(cwd: str, workstream: str | None) -> tuple[str, str] | None:
    """(repository identity, workstream), or None for a mission without a workstream (no Goal to guard).
    The repository is the git common dir, so a worktree and its main checkout are one Goal."""
    if not workstream or not cwd:
        return None
    tc = _git_toplevel_and_common(cwd)
    repo = tc[1] if tc else os.path.normcase(str(Path(cwd).resolve()))
    return repo, workstream


def goal_conflicts(key: tuple[str, str] | None, *, exclude: str | None = None,
                   records: list[dict] | None = None) -> list[dict]:
    """Non-terminal attempts of the Goal `key` other than `exclude`, each {mission_id, held, unit}."""
    if key is None:
        return []
    out = []
    for r in (records if records is not None else all_missions()):
        if r["mission_id"] == exclude or r.get("state") in TERMINAL or r.get("workstream") != key[1]:
            continue
        if goal_key(r.get("cwd") or "", r.get("workstream")) != key:
            continue
        out.append({"mission_id": r["mission_id"], "held": bool(r.get("owner_hold")),
                    "unit": (r.get("goal") or {}).get("unit")})
    return out


def goal_refusal(conflicts: list[dict], unit: str | None = None) -> str | None:
    """Why a new attempt may not start beside `conflicts`, or None. A Goal hold covers every unit; a live
    attempt without a unit owns the whole Goal; two units may run side by side only when both are named
    and differ."""
    for c in conflicts:
        if c["held"]:
            return f"goal held: {c['mission_id']} is under an Owner hold (release it, or supersede it with authority)"
    for c in conflicts:
        if not unit or not c["unit"] or c["unit"] == unit:
            return (f"singleflight: {c['mission_id']} is a live attempt of this goal"
                    + (f" (unit {c['unit']})" if c["unit"] else "")
                    + "; supersede it with authority, or name a distinct --parallel-unit on both")
    return None


def arm(cwd: str, resume_command: str, *, launch: bool = True, supersedes: str | None = None,
        authority: str | None = None, parallel_unit: str | None = None, unbounded: bool = False,
        **kw) -> dict:
    if unbounded and not (authority or "").strip():
        raise MissionError("--unbounded needs --authority: who decided, and where it is recorded")
    ws = kw.get("workstream")
    if ws is None and resume_command.startswith("/gsd-"):
        m = _WS_FLAG.search(resume_command)
        ws = m.group(1) if m else None
    key = goal_key(cwd, ws)
    conflicts = goal_conflicts(key)
    old = None
    if supersedes:
        if not (authority or "").strip():
            raise MissionError("--supersedes needs --authority: who decided, and where it is recorded")
        old = load(supersedes)
        if old is None or old["state"] in TERMINAL:
            raise MissionError(f"{supersedes} is not a live attempt to supersede")
        if key is None or goal_key(old.get("cwd") or "", old.get("workstream")) != key:
            raise MissionError(f"{supersedes} is not an attempt of this goal")
        conflicts = [c for c in conflicts if c["mission_id"] != supersedes]
    why = goal_refusal(conflicts, parallel_unit)
    if why:
        if key is not None:
            lr.ledger_append(f"goal-{key[1]}", "goal_arm_refused", workstream=key[1], why=why[:300])
        raise MissionError(why)
    rec = create(cwd, resume_command, **kw)
    extra = {}
    if key is not None:
        extra["goal"] = {"repo": key[0], "workstream": key[1], "unit": parallel_unit}
    if supersedes:
        extra.update(supersedes=supersedes, authority=authority.strip()[:1000])
    if unbounded:
        extra["unbounded"] = {"authority": authority.strip()[:1000], "at": time.time()}
    if extra:
        rec = transition(rec["mission_id"], expect_epoch=rec["epoch"], expect_state=PREPARED,
                         event="goal_bound", **extra)
    if old is not None:
        transition(supersedes, expect_epoch=old["epoch"], expect_state=old["state"],
                   event="mission_superseded", state=HALTED, pending=None,
                   reason=f"superseded by {rec['mission_id']}: {authority.strip()[:300]}")
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


LAUNCH_ACCOUNTS_KEEP = 500


def _account_id() -> str | None:
    """The logged-in Claude account (`oauthAccount.accountUuid` in .claude.json), or None.
    CPP_CLAUDE_ACCOUNT_FILE overrides the path (tests). Unreadable is None, never a guess."""
    try:
        p = os.environ.get("CPP_CLAUDE_ACCOUNT_FILE")
        if not p:
            cfg = os.environ.get("CLAUDE_CONFIG_DIR")
            p = os.path.join(cfg, ".claude.json") if cfg else os.path.join(os.path.expanduser("~"), ".claude.json")
        with open(p, encoding="utf-8-sig") as fh:
            uuid = (json.load(fh).get("oauthAccount") or {}).get("accountUuid")
        return str(uuid) if uuid else None
    except Exception:  # noqa: BLE001
        return None


def _launch_accounts_path() -> Path:
    return lr.state_dir() / "launch-accounts.json"


def _record_launch_account(bg_id: str) -> None:
    """Which account a worker was launched as, keyed by its host id (a renewal inherits the
    previous mission's worker, so the mission id would not find it). Best effort: a lost write
    only means the quota hold behaves as before."""
    acct = _account_id()
    if not bg_id or not acct:
        return
    try:
        p = _launch_accounts_path()
        try:
            seen = json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            seen = {}
        seen.pop(bg_id, None)
        seen[bg_id] = acct
        seen = dict(list(seen.items())[-LAUNCH_ACCOUNTS_KEEP:])
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(seen), encoding="utf-8")
        os.replace(tmp, p)
    except Exception:  # noqa: BLE001
        pass


def _launched_as(session_id: str | None) -> str | None:
    if not session_id:
        return None
    try:
        seen = json.loads(_launch_accounts_path().read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
    for bg, acct in seen.items():
        if session_id.startswith(bg):
            return acct
    return None


def _quota_released_by_relogin(rec: dict, hold: dict | None) -> bool:
    """A quota hold is evidence about the account the refused worker ran as. Measured 2026-10-04
    (GEX44 m-a828e0f4feb9): after the Owner logged in with another account, the hold re-read
    the old refusal and would have held three days. Release only on a KNOWN different account;
    a credentials timestamp would not do, token refreshes rewrite that file every few hours."""
    if not hold or hold.get("class", "quota") != "quota":
        return False
    sid = (rec.get("owner") or {}).get("session_id")
    was, now_acct = _launched_as(sid), _account_id()
    if not was or not now_acct or was == now_acct:
        return False
    lr.ledger_append(rec.get("mission_id"), "quota_hold_released", mission_id=rec.get("mission_id"),
                     reason="a different account is logged in than the refused worker ran as",
                     refused_session=sid, until=hold.get("until"))
    return True


def sleep_on_change(rec: dict, cause: str, wake: dict, event: str, now: float, *,
                    set_reason: bool = False, **fields) -> bool:
    """GGMC C5: announce a hold and persist it as the record's `sleep` -- only when it changed. True when
    written. An unchanged hold writes nothing: the pass still holds, it just has nothing new to say.
    `set_reason` also records the reason on the record (launch_held always did); a provider hold must
    not, because renewal reads the record's reason for "budget:"."""
    import mission_sleep as ms
    new = ms.entry(cause, wake, rec["epoch"], fields.get("reason"), now)
    if ms.same(rec, new):
        return False
    changes = {"reason": fields["reason"]} if set_reason and fields.get("reason") else {}
    transition(rec["mission_id"], expect_epoch=rec["epoch"], expect_state=rec["state"], event=event,
               now=now, sleep=new, ledger_extra=fields, **changes)
    return True


def status_surface(rows: list[dict], missions: list[dict], now: float) -> dict:
    """GGMC C6: the attempts that are not terminal, HOT first, each with its class, waker and Owner-only
    flag, plus the estate KPIs. `rows` are status rows (plan already computed); unreadable rows are COLD."""
    import mission_surface as msf
    by_id = {m["mission_id"]: m for m in missions}
    out = []
    for row in rows:
        m = by_id.get(row["mission_id"])
        c = msf.classify(m, row.get("plan"), now, TERMINAL)
        out.append({"mission_id": row["mission_id"], "state": row.get("state"), "epoch": row.get("epoch"),
                    **c, "sleep_cause": ((m or {}).get("sleep") or {}).get("cause"),
                    "cwd": (m or {}).get("cwd")})
    order = {msf.HOT: 0, msf.COLD: 1, msf.WARM: 2}
    live = sorted((r for r in out if r["class"] != msf.TERMINAL), key=lambda r: (order[r["class"]], r["mission_id"]))
    return {"attempts": live, "kpi": msf.kpis(out)}


def provider_hold(rec: dict, now: float) -> dict | None:
    """The hold for this mission's next successor (tools/provider_breaker.py). If the breaker
    itself cannot run, fall back to the pre-breaker quota check -- and say so in the ledger:
    a missing breaker must not read as a provider that is fine."""
    try:
        import provider_breaker as pb
        hold = pb.hold_for(rec, now)
        return None if _quota_released_by_relogin(rec, hold) else hold
    except Exception as exc:  # noqa: BLE001 -- degrade to the previous behaviour, visibly
        lr.ledger_append(rec.get("mission_id"), "provider_breaker_unavailable",
                         mission_id=rec.get("mission_id"), error=f"{exc.__class__.__name__}: {exc}"[:200])
        sid = (rec.get("owner") or {}).get("session_id")
        h = quota_hold_from_transcript(sid, now)
        return _auth_hold_without_breaker(sid, now) if h is None else {**h, "class": "quota"}


# Copy of provider_breaker.AUTH_RE for the degraded path (the breaker is what cannot be imported
# there). V-PFP-AUTH-PARITY pins pattern and flags equal, so the two cannot drift apart silently.
AUTH_FALLBACK_RE = re.compile(r"invalid api key|please run /login|not logged in|oauth token (?:has )?expired|"
                              r"authentication[_ ](?:error|failed)|\b401\b|unauthori[sz]ed|credit balance is too low",
                              re.I)


def _credentials_usable_without_breaker(now: float) -> bool:
    """The degraded-mode twin of `provider_breaker.credentials_expired(...) is False`: True only when the
    credentials file shows a usable login -- an access token still valid, or a lapsed one whose refresh token
    has a KNOWN future expiry. Reads the expiry keys and the mere presence of `refreshToken`, never a token.
    Unreadable, absent, expiresAt 0, a lapsed token with no refresh token, or an unknown refresh expiry are all
    False: unmeasurable never releases a park. V-PFP-FALLBACK-CRED-PARITY pins it equal to the breaker's judgement."""
    try:
        oauth = json.loads((Path.home() / ".claude" / ".credentials.json").read_text(encoding="utf-8"))["claudeAiOauth"]

        def secs(value):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return None
            return value / 1000.0 if value > 1e11 else float(value)
        exp = secs(oauth.get("expiresAt"))
        if exp is None or exp <= 0:
            return False
        if exp > now:
            return True
        if "refreshToken" not in oauth:
            return False
        rexp = secs(oauth.get("refreshTokenExpiresAt"))
        return rexp is not None and rexp > now
    except Exception:  # noqa: BLE001 -- unreadable is unmeasured, and unmeasured keeps the park
        return False


def _auth_hold_without_breaker(session_id: str | None, now: float) -> dict | None:
    """Breaker-less park of an authorization refusal. Only a HOST-written reply (model "<synthetic>")
    is evidence, never a model quoting it. The qualifying precondition change in this degraded mode is a
    credentials file rewritten after the refusal AND showing a usable login (the same evidence the breaker
    path requires; see _credentials_usable_without_breaker). No evidence of a refusal is not a refusal -> None."""
    try:
        t = lr.find_transcript(session_id) if session_id else None
        if not t:
            return None
        for row in reversed(lr._tail_rows(t)):
            if row.get("type") != "assistant":
                continue
            msg = row.get("message") if isinstance(row.get("message"), dict) else {}
            text = " ".join(lr._text_of(msg).split())
            if msg.get("model") != "<synthetic>" or not AUTH_FALLBACK_RE.search(text):
                return None
            evidence_at = lr._parse_iso(row.get("timestamp")) or os.path.getmtime(t)
            try:
                if (Path.home() / ".claude" / ".credentials.json").stat().st_mtime > evidence_at \
                        and _credentials_usable_without_breaker(now):
                    return None
            except OSError:
                pass  # no credentials file to compare: the refusal stands
            return {"until": None, "reason": "QUARANTINE (credentials; breaker unavailable) -- auth: " + text[:200],
                    "class": "auth", "streak": 1, "quarantine": True}
        return None
    except Exception:  # noqa: BLE001 -- no evidence of a refusal is not a refusal
        return None


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
    a.add_argument("--rollover-protocol", choices=(CAPSULE_V2,), default=None,
                   help="rotate through a sealed, certified capsule (spec mission-capsule-rollover); "
                        "needs --permission-mode auto or bypassPermissions. Omitted: legacy.")
    a.add_argument("--supersedes", help="the live attempt of this goal this one replaces (spec "
                                        "goal-governed-mission-control C4); needs --authority")
    a.add_argument("--authority", help="who decided the supersession (or --unbounded) and where it is recorded")
    a.add_argument("--unbounded", action="store_true",
                   help="launch with no token envelope (spec compiled-grammar-default law 2); needs --authority")
    a.add_argument("--parallel-unit", help="a named work unit that may run beside other named units "
                                           "of the same goal")
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
    oh = sub.add_parser("hold", help="park a live mission: no launch, halt or renewal (spec mission-owner-hold)")
    oh.add_argument("--mission", required=True)
    oh.add_argument("--reason", required=True)
    orl = sub.add_parser("release", help="lift an owner hold; the budget clock is not reset")
    orl.add_argument("--mission", required=True)
    pr = sub.add_parser("protocol", help="set the rollover protocol on an existing mission "
                                         "(held or owner-less only; same permission-mode rule as arm)")
    pr.add_argument("--mission", required=True)
    pr.add_argument("--rollover-protocol", required=True,
                    help=f"only {CAPSULE_V2}; anything else is refused")
    en = sub.add_parser("envelope", help="set token estimate / model / autocompact / compiled work-unit "
                                         "packet on a live mission (spec mission-envelope-and-compiled-wu)")
    en.add_argument("--mission", required=True)
    en.add_argument("--token-estimate", help="processed tokens the cost breaker judges, e.g. 16M")
    en.add_argument("--model", help="worker model: sonnet, opus, haiku, fable or a claude- model id")
    en.add_argument("--autocompact", help="worker autocompact window, e.g. 300k")
    en.add_argument("--wu-packet", help="compiled work-unit file sent instead of the resume command")
    en.add_argument("--continue-max-tokens",
                    help="per-mission context ceiling for continuing the same session, e.g. 200k")
    ad = sub.add_parser("admit", help="judge the compiled work unit's route against its envelope "
                                      "(tools/route_admission.py); only ADMISSIBLE may launch")
    ad.add_argument("--mission", required=True)
    ad.add_argument("--route", required=True, help="route JSON: envelope + workers (profile, calls, packet)")
    ad.add_argument("--floors", help="floor table (default vault/config/route-floors.json)")
    v = sub.add_parser("supervise")
    v.add_argument("--dry-run", action="store_true")
    v.add_argument("--actions-only", action="store_true",
                   help="print only rows where the pass acted (the sweep logs nothing otherwise)")
    st = sub.add_parser("status")
    st.add_argument("--surface", action="store_true",
                    help="exception surface: non-terminal attempts as HOT/WARM/COLD + KPIs (GGMC C6)")
    args = ap.parse_args(argv)
    if args.cmd == "arm":
        wall = None
        if args.wall:
            snap, adv, rearm = (float(x) for x in args.wall.split(","))
            wall = {"snapshot": snap, "advisory": adv, "rearm": rearm}
        res = arm(args.cwd, args.command, launch=not args.no_launch, workstream=args.workstream,
                  max_cycles=args.max_cycles, max_hours=args.max_hours,
                  permission_mode=args.permission_mode, allowed_tools=args.allowed_tools,
                  add_dirs=args.add_dir, wall=wall, rollover_protocol=args.rollover_protocol,
                  supersedes=args.supersedes, authority=args.authority, parallel_unit=args.parallel_unit,
                  unbounded=args.unbounded)
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
    if args.cmd == "hold":
        rec = set_owner_hold(args.mission, args.reason)
        print(f"OWNER HOLD SET mission={rec['mission_id']} state={rec['state']} epoch={rec['epoch']}")
        return 0
    if args.cmd == "release":
        rec = release_owner_hold(args.mission)
        print(f"OWNER HOLD RELEASED mission={rec['mission_id']} state={rec['state']} epoch={rec['epoch']}")
        return 0
    if args.cmd == "protocol":
        rec = set_rollover_protocol(args.mission, args.rollover_protocol)
        print(f"ROLLOVER PROTOCOL SET mission={rec['mission_id']} protocol={rec['rollover_protocol']} "
              f"state={rec['state']} epoch={rec['epoch']}")
        return 0
    if args.cmd == "envelope":
        rec = set_envelope(args.mission, token_estimate=args.token_estimate, model=args.model,
                           autocompact=args.autocompact, wu_packet=args.wu_packet,
                           continue_max_tokens=args.continue_max_tokens)
        pkt = (rec.get("wu_packet") or {}).get("path")
        print(f"ENVELOPE SET mission={rec['mission_id']} token_estimate={rec.get('token_estimate')} "
              f"model={rec.get('model')} autocompact={rec.get('autocompact')} wu_packet={pkt} "
              f"wu_packet_epoch={rec.get('wu_packet_epoch')} continue_max_tokens={rec.get('continue_max_tokens')}")
        return 0
    if args.cmd == "admit":
        adm = admit_route(args.mission, args.route, floors_path=args.floors)["admission"]
        print(f"ROUTE {adm['verdict']} mission={args.mission} need={adm.get('need_with_margin')} "
              f"target={adm['envelope']['target']} remaining={adm.get('remaining')}")
        for r in adm["reasons"]:
            print(f"  - {r}")
        return 0 if adm["verdict"] == "ADMISSIBLE" else 3
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
    if getattr(args, "surface", False):
        print(json.dumps(status_surface(rows, missions, time.time()), indent=2))
        return 0
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
