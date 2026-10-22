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
import math
import os
import re
import sys
import threading
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_long_run as lr  # noqa: E402  (state_dir, ledger, _pid_alive, sessions_dir)
import mission_binding as mb  # noqa: E402  (AMCR: the one execution-root resolver)
import mission_resources as mres  # noqa: E402  (M2: typed resource requirements, probes behind mres.PROBES)
import receipt_judge as rj  # noqa: E402  (one receipt reading for mission, chain and steward)
from route_admission import KNOWN_VERDICTS, LAUNCHABLE_VERDICTS  # noqa: E402  (one verdict contract)

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


# Both spellings /gsd-* accepts. Only `--ws` was matched until 2026-10-11, so a mission armed with
# `--workstream X` (m-cec849fc02b2) kept no workstream and the supervisor asked the ROOT roadmap.
_WS_FLAG = re.compile(r"(?:^|\s)--(?:ws|workstream)(?:=|\s+)(\S+)")


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
               ledger_extra: dict | None = None, touch: bool = True, expect_seq: int | None = None,
               **changes) -> dict:
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

    ``touch=False`` keeps ``updated_at``: plan_next reads it as the owner's last sign of
    life, so a supervisor's own bookkeeping write must not refresh it (an auto envelope
    assigned right before planning hid a stale UNKNOWN owner for a whole stale window).
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
        if expect_seq is not None and int(rec.get("seq") or 0) != int(expect_seq):
            # AMR audit F1: a multi-write transaction (recover_mission) must not overwrite a hold or park
            # written between its reads, which epoch+state alone cannot see.
            raise CasConflict(f"{mission_id}: expected seq {expect_seq}, found {rec.get('seq')} (record moved)")
        new_state = changes.get("state", rec["state"])
        if new_state not in STATES:
            raise MissionError(f"unknown state {new_state!r}")
        rec.update(changes)
        if "sleep" not in changes:
            rec.pop("sleep", None)   # popped, not nulled: a record that never slept keeps its bytes
        if touch or not rec.get("updated_at"):
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
              pid_alive=lr._pid_alive, v2: bool | None = None, blocked_probe=None) -> dict:
    """What the out-of-band supervisor should do for this mission, and why.

    Actions: none · launch · replace · halt · surface_blocked · await.
    Pure except the injected ``pid_alive`` and, for a bare host-`blocked` owner only, ``blocked_probe``
    (default blocked_recovery: reads the job file and the repo's .planning/config.json, may ask git once). ``v2`` is capsule_v2(rec) as the caller read it
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
        # A hold may prevent relaunch; it must not prevent terminal settlement. Measured 2026-10-08
        # (EDD m-4bb8952b2903, m-79f84cdd34dc): a cost-breaker hold set on a worker that then finished
        # left the record RUNNING with its owner gone, and goal singleflight refused every later unit
        # until the Owner closed it by hand. Only positive DEAD evidence settles; UNKNOWN stays parked.
        if state in (RUNNING, BLOCKED) and is_cost_hold(hold):
            # AMR: a cost hold stops the executor, not the goal. Recovery runs until it launches a
            # successor or records a boundary; only then does the hold fall back to parking/settling.
            import mission_recovery as mr
            rstate = (hold.get("recovery") or {}).get("state")
            if mr.mode() != "off" and rstate not in mr.TERMINAL_RECOVERY_STATES and mr.eligible(rec):
                return {"action": "recover",
                        "reason": f"cost hold -> autonomous recovery ({str(hold.get('reason'))[:160]})"}
            if rstate == mr.OWNER_BOUNDARY:
                # Audit F3: a recovery boundary is a PARK with a decision packet, never a settle -- the packet's
                # options (raise authority, extend hours, release) must still apply to a live record.
                return {"action": "none", "reason": f"recovery owner boundary: {str((hold.get('recovery') or {}).get('why'))[:200]}"}
        if hold.get("kind") == "resource":
            # M2: parked for a resource, not for a person. A dead owner is the normal case (its turn is done),
            # so it is NOT settled: the sweep lifts the hold when the requirement is met, then relays.
            return {"action": "none", "reason": f"WAIT_RESOURCE: {str(hold.get('reason'))[:200]}"}
        if state in (RUNNING, BLOCKED) and rec.get("owner"):
            verdict, evidence = liveness(rec.get("owner"), sessions, pid_alive)
            if verdict == DEAD and hold.get("worker_stopped_at"):
                # spec mission-cost-hold-stops-worker: the supervisor stopped this worker for the cost
                # hold, so its death is ours, not the end of the work. Parked; release replaces it.
                return {"action": "none",
                        "reason": f"cost hold, worker stopped ({hold.get('stop')}): parked until release"}
            if verdict == DEAD:
                return {"action": "settle",
                        "reason": f"owner hold, owner DEAD ({evidence}): settled terminal, hold kept "
                                  f"(hold: {str(hold.get('reason'))[:200]})"}
        if state == LAUNCHING:
            # The breaker can park a launch in the pass BEFORE adoption (EDD m-c597a68e7077, 2026-10-08: the
            # worker ran 7 calls and finished; the hold froze the record at LAUNCHING with no owner). The host
            # row for THIS launch's id, listed finished, is the same positive evidence liveness() accepts.
            lrow = launched_row(rec.get("pending"), sessions)
            if lrow is not None and lrow.get("state") in ("stopped", "done", "exited", "failed"):
                return {"action": "settle", "launched": lrow,
                        "reason": f"owner hold, launched worker {lrow.get('id')} host lists {lrow.get('state')}: "
                                  f"settled terminal, hold kept (hold: {str(hold.get('reason'))[:200]})"}
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
        # AMR-X (m-5cd1a041bc0f, 21 h 43 min parked): a bare host `blocked` is also a model that ENDED ITS
        # TURN ON A QUESTION. The Owner Escalation Gate types it from the job's `needs`; a question the
        # repo policy or the recommended option answers is not a human's, so the worker is replaced by a
        # successor that carries the answer. Permission prompts, host gates and Owner-class questions
        # stay surfaced exactly as before; an unjudgeable one (None/UNKNOWN) too.
        # Only a BARE blocked is judged: a host row carrying `waitingFor` is a live permission prompt, whatever the
        # job file says (review F3).
        hrow = _host_row((rec.get("owner") or {}).get("session_id"), sessions)
        b = ((blocked_probe or blocked_recovery)(rec)
             if state in (RUNNING, BLOCKED) and hrow is not None and not hrow.get("waitingFor") else None)
        cls = (b or {}).get("class")
        if cls == "QUESTION_RESOLVABLE":
            if int(rec.get("decision_recoveries") or 0) >= MAX_DECISION_RECOVERIES:
                return {"action": "surface_blocked",
                        "reason": f"OWNER_BOUNDARY: {MAX_DECISION_RECOVERIES} decision recoveries already spent; "
                                  f"worker asks again: {b['why'][:160]}"}
            return {"action": "replace", "decision": b,
                    "reason": f"decision recovery ({b['gate']['result']}): the worker ended on a question the "
                              f"runtime answers: {b['why'][:160]}"}
        if cls == "QUESTION_OWNER":
            return {"action": "surface_blocked",
                    "reason": f"OWNER_BOUNDARY ({b['gate'].get('owner_class')}): {b['why'][:200]}"}
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
# A host row reports `state: done` when the TURN is over while `status: idle` says the session is still
# alive in the background (measured 2026-10-17 GEX44 m-80fd126a23cc: 4 of 7 same-session continuations
# resumed a session that was still "already running", so the host started a copy and a fresh worker
# followed 4 minutes later). Alive is `status`, not `state`.
HOST_LIVE_STATUSES = ("idle", "busy", "waiting")
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


# Per-mission MCP posture of a `--bg` worker (oic-v1 S4). "none" strips MCP for this mission only: a
# project .mcp.json parks an unattended worker on its server-approval dialog (m-c74a2125495b, probe A),
# and the alternative -- pre-approving in ~/.claude.json -- writes host state outside the mission.
WORKER_MCP_MODES = ("inherit", "none")
SLIM_PROFILES = ("slim-t1", "slim-t2")
SLIM_SETTINGS = Path(__file__).resolve().parent.parent / "vault" / "config" / "slim-critical-settings.json"
# PowerShell on Windows: the critical lane's bash-bridge guard blocks git through Bash, and a worker with
# no PowerShell tool edited but could not commit (e2e 2026-10-07, .scratch/e2e_edit.py arm `auto`).
SLIM_DEFAULT_TOOLS = ("Read", "Grep", "Glob", "Bash", "Edit", "Write") + (("PowerShell",) if os.name == "nt" else ())
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
    # 2026-10-06 (m-8bbdf725cd52 W1-staging e5): a `-p` worker with no permission mode had its 4 writes
    # denied and burned to the no-progress breaker. Same pre-approvals and mode as the `--bg` launch;
    # a record without a mode still gets edits (Owner-approved), never a prompt nobody answers.
    for tool in dict.fromkeys([*(rec.get("allowed_tools") or []), "Edit(.planning/**)"]):
        argv.append(f"--allowedTools={tool}")
    argv.append(f"--permission-mode={rec.get('permission_mode') or 'acceptEdits'}")
    if profile == "slim-t1":
        argv.append("--no-session-persistence")
    else:
        argv.append(f"--settings={SLIM_SETTINGS}")
    argv.append(f"--model={rec.get('model') or 'sonnet'}")
    if session_id:
        argv.append(f"--session-id={session_id}")   # the id is OURS: no stdout to parse, budget file keyed to it
    return argv + [prompt]


MAX_DECISION_RECOVERIES = 2   # successors per mission launched to answer a worker's own question


def _decision_recovery_off() -> bool:
    return os.environ.get("CPP_MISSION_DECISION_RECOVERY", "").strip().lower() == "off"


def worker_topology(rec: dict) -> dict:
    """tools/mission_policy.compile_topology for the mission's repo. A policy that cannot be read keeps
    today's topology (worktrees allowed): this gate may only narrow a launch, never break one."""
    if _decision_recovery_off():
        return {"worktrees": True, "disallowed_tools": [], "why": "CPP_MISSION_DECISION_RECOVERY=off"}
    try:
        import mission_policy as mpol
        return mpol.topology_for(rec["cwd"])
    except Exception as exc:  # noqa: BLE001 -- recorded, the launch proceeds as before
        lr.ledger_append(rec.get("mission_id") or "-", "topology_policy_unavailable",
                         mission_id=rec.get("mission_id"), error=f"{type(exc).__name__}: {exc}"[:200])
        return {"worktrees": True, "disallowed_tools": [], "why": "policy unavailable"}


def blocked_recovery(rec: dict) -> dict | None:
    """Type a host-`blocked` BACKGROUND owner from its job's `needs` (tools/mission_policy.classify_blocked).

    None = not judged (kill switch, no background owner, probe failed): the caller keeps today's
    surface_blocked. Only QUESTION_RESOLVABLE ever leads to recovery."""
    owner = rec.get("owner") or {}
    if _decision_recovery_off() or owner.get("kind") != "background" or not owner.get("session_id"):
        return None
    try:
        import mission_policy as mpol
        return mpol.classify_blocked(mpol.job_state(owner["session_id"]),
                                     mpol.repo_policy(rec["cwd"])["values"])
    except Exception:  # noqa: BLE001 -- unknown is never recovered on
        return None


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
    # AMR-X 2026-10-13 (m-5cd1a041bc0f): the repo's own policy decides the topology BEFORE the worker runs.
    # `.planning/config.json` said use_worktrees=false and the two pre-approvals above put the worker in a
    # worktree anyway. A forbidding policy (or an unhealthy EnterWorktree) now drops them and disallows both.
    topo = worker_topology(rec)
    wt_tools = [] if not topo.get("worktrees", True) else ["EnterWorktree", "ExitWorktree"]
    tools = list(dict.fromkeys([*(t for t in (rec.get("allowed_tools") or [])
                                  if t not in topo.get("disallowed_tools", [])), *wt_tools, "Edit(.planning/**)"]))
    for tool in tools:
        argv += ["--allowedTools", tool]
    for d in rec.get("add_dirs") or []:
        argv += ["--add-dir", d]
    # A worker nobody watches must not be able to park on a question (Owner 2026-09-25).
    argv += ["--disallowedTools", "AskUserQuestion"]
    for tool in topo.get("disallowed_tools", []):
        argv += ["--disallowedTools", tool]
    if capsule_v2(rec) or rec.get("worker_mcp") == "none" or worker_mcp_verdict() == "APPLY":
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


def _spawn_detached(argv: list[str], cwd: str, out_path: Path, err_path: Path, env: dict | None = None) -> int:
    """Start `claude -p` DETACHED (it is synchronous: the supervisor must not block on it) with its
    stdout/stderr going to files. Returns the pid. ``env`` None inherits the supervisor's environment."""
    import subprocess
    out_path.parent.mkdir(parents=True, exist_ok=True)
    kw: dict = {}
    if os.name == "nt":
        kw["creationflags"] = 0x00000008 | 0x00000200 | 0x08000000  # DETACHED | NEW_PROCESS_GROUP | NO_WINDOW
    else:
        kw["start_new_session"] = True
    with open(out_path, "wb") as so, open(err_path, "wb") as se:
        proc = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.DEVNULL, stdout=so, stderr=se, env=env, **kw)
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
    wd = mb.execution_root(rec)
    run_dir = wd if wd and Path(wd).is_dir() else rec["cwd"]
    unit_env, drow = deflate_unit(rec)
    if drow:
        lr.ledger_append(mid, "deflate_" + ("applied" if unit_env else "observed"), mission_id=mid, epoch=epoch,
                         **drow, delivered=bool(unit_env))
    try:
        pid = (spawner or _spawn_detached)(argv, run_dir, out_path, err_path,
                                           **({"env": {**os.environ, **unit_env}} if unit_env else {}))
    except Exception as exc:  # the launch itself could not happen
        why = f"{type(exc).__name__}: {exc}"
        lr.ledger_append(mid, "launch_failed", mission_id=mid, epoch=epoch, rc=None, bg_id=sid,
                         why="slim launch refused", detail=why[-300:])
        return {"ok": False, "epoch": epoch, "bg_id": sid, "why": "slim launch refused", "detail": why}
    adm = rec.get("admission") or {}
    used = ({"admission": {**adm, "consumed_epoch": epoch}}
            if rec.get("wu_packet") and adm.get("verdict") in LAUNCHABLE_VERDICTS else {})
    rec = transition(mid, expect_epoch=epoch, expect_state=LAUNCHING, event="launched", now=now,
                     pending={**rec["pending"], "bg_id": sid}, **used)
    owner = {"session_id": sid, "pid": pid, "proc_start": None, "heartbeat_at": now, "epoch": epoch,
             "kind": "slim", "profile": slim_profile(rec), "out_path": str(out_path), "err_path": str(err_path)}
    transition(mid, expect_epoch=epoch, expect_state=LAUNCHING, event="worker_acked", now=now, state=RUNNING,
               pending=None, pending_decision=None, failed_launches=0, iterations=rec.get("iterations", 0) + 1, worker=sid, owner=owner)
    return {"ok": True, "epoch": epoch, "bg_id": sid, "pid": pid, "slim": True}


LEGACY_REASONS = ("host_limitation", "uncertified_work_class", "quality_requirement", "novel_architecture",
                  "safe_deopt")
_BASELINE_FIELDS = ("model", "autocompact", "continue_max_tokens")
# Built-in fallback = the policy values (never Opus / 600k). Evidence: gen3/packets/T1.md + T3.md ran
# `--model sonnet --autocompact 250k`; continuation ceiling kept equal to the compaction line.
_BUILTIN_BASELINE = {"version": "builtin", "classes": {
    c: {"model": "sonnet", "autocompact": "250k", "continue_max_tokens": 250_000}
    for c in ("COMPILED_UNIT", "GSD_RESUME", "OTHER")}}


def baseline_mode() -> str:
    """CPP_CE_BASELINE: shadow (default) | enforce | off."""
    v = str(os.environ.get("CPP_CE_BASELINE") or "shadow").strip().lower()
    return v if v in ("shadow", "enforce", "off") else "shadow"


def work_class(rec: dict) -> str:
    """From the record only: COMPILED_UNIT (has wu_packet), GSD_RESUME (resume_command starts /gsd-), OTHER."""
    if rec.get("wu_packet"):
        return "COMPILED_UNIT"
    if str(rec.get("resume_command") or "").lstrip().startswith("/gsd-"):
        return "GSD_RESUME"
    return "OTHER"


def _baseline_policy() -> tuple[dict, str]:
    """(policy, source) -- source is `policy` or `builtin` (file unreadable or malformed)."""
    try:
        raw = json.loads(_BUDGET_DEFAULTS.read_text(encoding="utf-8-sig"))
        ver = str(raw["baseline_version"])
        classes = {}
        for c in _BUILTIN_BASELINE["classes"]:
            e = raw["baseline_classes"][c]
            classes[c] = {"model": str(e["model"]) or None, "autocompact": str(e["autocompact"]) or None,
                          "continue_max_tokens": int(e["continue_max_tokens"])}
            if not all(classes[c].values()):
                raise ValueError("empty baseline value")
        return {"version": ver, "classes": classes}, "policy"
    except Exception:  # noqa: BLE001 -- unreadable policy answers with the built-in cheap values
        return _BUILTIN_BASELINE, "builtin"


def _tokens_of(v) -> int:
    m = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*([kKmM]?)\s*", str(v or ""))
    return int(float(m.group(1)) * {"": 1, "k": 1000, "m": 1_000_000}[m.group(2).lower()]) if m else 0


def _legacy_combo(rec: dict) -> bool:
    """The final launch is --bg + Opus + >=600k compaction."""
    model = str(rec.get("model") or "").lower()
    return (not slim_profile(rec)) and ("opus" in model or not model) and _tokens_of(rec.get("autocompact")) >= 600_000


def resolve_baseline(rec: dict) -> dict:
    """Absent optimisation fields resolve to the certified baseline, never to the host maximum.
    Returns a NEW record: explicit values kept (src explicit), absent -> policy value (src policy@<v>) or
    builtin. Mode `off` returns the record unchanged."""
    if baseline_mode() == "off":
        return rec
    pol, origin = _baseline_policy()
    cls = work_class(rec)
    base = pol["classes"][cls]
    # A value an earlier resolution wrote is still policy-derived while it is unchanged: re-resolve it, or
    # the next epoch reports it `explicit` and a policy change never reaches the mission. A value an
    # operator set afterwards (envelope --model opus) differs from what was written, so it stays explicit.
    prior = rec.get("baseline") or {}
    written = {f: v for f, v in (prior.get("values") or {}).items()
               if not str((prior.get("src") or {}).get(f, "explicit")).startswith("explicit")}
    out, src, values = dict(rec), {}, {}
    for f in _BASELINE_FIELDS:
        if rec.get(f) and not (f in written and rec.get(f) == written[f]):
            src[f] = "explicit"
        else:
            out[f] = base[f]
            src[f] = f"policy@{pol['version']}" if origin == "policy" else "builtin"
        values[f] = out.get(f)
    out["baseline"] = {"version": pol["version"], "tier": "COMPILED" if rec.get("wu_packet") else "BASIC",
                       "work_class": cls, "src": src, "values": values, "legacy_reason": rec.get("legacy_reason")}
    return out


def baseline_legacy_verdict(rec: dict) -> str | None:
    """Why the resolved record is an unexplained legacy launch, else None."""
    if not _legacy_combo(rec):
        return None
    reason = str(rec.get("legacy_reason") or "").split(":")[0]
    return None if reason in LEGACY_REASONS else (
        "legacy launch (--bg + opus + >=600k) without legacy_reason; fix: `gsd_mission envelope --mission "
        f"{rec.get('mission_id')} --model sonnet --autocompact 250k` or set legacy_reason in {LEGACY_REASONS}")


def launch_worker(mission_id: str, *, expect_epoch: int, expect_state, reason: str,
                  runner=None, now: float | None = None, note: str | None = None,
                  stop_runner=None, work_dir: str | None = None,
                  progress: dict | None = None, packet: dict | None = None, spawner=None,
                  det_runner=None, mem_reader=None, gsd_fact: str = "") -> dict:
    """Claim the next epoch FIRST (CAS), then launch, then bind the host's answer.

    ``work_dir`` is where the predecessor actually worked (a git worktree of the project,
    see effective_workdir). The worker is still LAUNCHED in the mission's cwd -- workspace
    trust is exact-path (W0 E2), a fresh worktree path is never trusted -- and the card tells
    it where the work is.

    Resource admission (tools/resource_admission.py) refuses, before any claim or spawn, when available
    RAM is below the worker profile's floor or unreadable (`launch_refused_resources`). Kill switch:
    CPP_RESOURCE_ADMISSION=off.

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
    pd = rec.get("pending_decision")
    if pd and pd not in (note or ""):
        # AMR-X: a runtime answer not yet delivered to an adopted worker rides every launch until one is adopted.
        note = f"{pd}\n\n{note or ''}"
    try:
        # Asked BEFORE the claim: an unreadable work-unit packet spends no epoch and starts nothing.
        prompt = launch_prompt(rec) + (gsd_fact if not rec.get("wu_packet") else "")
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
    import resource_admission as rsa
    rref = rsa.refusal(slim_profile(rec) or "top-level-worker", reader=mem_reader)
    if rref:
        rwhy = (f"{rref['verdict']}: available_mb={rref['available_mb']} floor_mb={rref['floor_mb']} "
                f"profile={rref['profile']}")
        lr.ledger_append(mission_id, "launch_refused_resources", mission_id=mission_id,
                         epoch=rec.get("epoch"), reading=rref, why=rwhy[:300])
        return {"ok": False, "epoch": rec.get("epoch"), "bg_id": None, "why": rwhy, "detail": ""}
    if rec.get("wu_packet") and _admission_switch_off():
        lr.ledger_append(mission_id, "admission_bypassed", mission_id=mission_id, epoch=rec.get("epoch"),
                         verdict=(rec.get("admission") or {}).get("verdict"))
    # WU-A6 DETERMINISTIC_PATH: a packet that names its script is run, not given to a model. Before the
    # claim: it spends no epoch and launches no worker.
    try:
        det = deterministic_script(rec)
    except MissionError as exc:
        lr.ledger_append(mission_id, "launch_refused_packet", mission_id=mission_id,
                         epoch=rec.get("epoch"), why=str(exc)[:300])
        return {"ok": False, "epoch": rec.get("epoch"), "bg_id": None, "why": str(exc), "detail": ""}
    if det:
        return _run_deterministic(rec, det, now, run=det_runner)   # never `runner`: that one starts claude
    resolved = resolve_baseline(rec)
    baseline_on = resolved is not rec
    legacy_why = baseline_legacy_verdict(resolved) if baseline_mode() != "off" else None
    if legacy_why and baseline_mode() == "enforce":
        lr.ledger_append(mission_id, "launch_refused_baseline", mission_id=mission_id,
                         epoch=rec.get("epoch"), why=legacy_why[:300])
        return {"ok": False, "epoch": rec.get("epoch"), "bg_id": None, "why": legacy_why, "detail": ""}
    epoch = expect_epoch + 1
    failed = rec.get("failed_launches", 0) + (1 if rec.get("state") == LAUNCHING else 0)
    extra = {"note": note} if note is not None else {}
    if baseline_on:
        extra.update({k: resolved[k] for k in (*_BASELINE_FIELDS, "baseline")})
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
        wd = work_dir or mb.execution_root(rec)
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
    if baseline_on:
        lr.ledger_append(mission_id, "baseline_resolved", mission_id=mission_id, epoch=epoch, **rec["baseline"])
        if legacy_why:
            lr.ledger_append(mission_id, "would_refuse_legacy", mission_id=mission_id, epoch=epoch, why=legacy_why[:300])
    if slim_profile(rec):
        return _launch_slim(rec, prompt, epoch, now, spawner=spawner)
    _, drow = deflate_unit(rec, declare=False)
    if drow:
        # `--bg` does not inherit the launcher's environment (W0 E3): a declaration cannot ride this launch.
        lr.ledger_append(mission_id, "deflate_observed", mission_id=mission_id, epoch=epoch, **drow,
                         delivered=False, why="--bg launch does not inherit env (W0 E3)")
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
            if rec.get("wu_packet") and adm.get("verdict") in LAUNCHABLE_VERDICTS else {})
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
                             pending_decision=None, failed_launches=0, iterations=rec.get("iterations", 0) + 1,
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
    if mb.enabled():
        root = (live if live and mb._norm(live) != mb._norm(rec["cwd"]) else None) or mb.execution_root(rec)
    else:
        root = live or mb.legacy_root(rec)
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


def _decision_prompt(d: dict) -> str:
    return (f"OWNER DECISION {d['id']} (binding; it settles any open 'OWNER DECISION NEEDED' on this topic, in "
            f"STATE.md and in a blocked-on-Owner state): {d['text']}\n"
            "Record it as resolved in STATE.md, then continue the mission with the next runnable work. "
            "Do not wait for the Owner again on this point.")


def deliver_decision(mission_id: str, text: str, *, decision_id: str | None = None, supersedes: str | None = None,
                     wake: bool = True, now: float | None = None, sessions: list[dict] | None = None,
                     runner=None, stop_runner=None, pid_alive=lr._pid_alive, host_fetch=None) -> dict:
    """An Owner decision as DURABLE mission state (2026-10-17, TB-FULL: an answer given in chat or written to a
    scratch file never reached a worker that had stopped to ask; a stale 'OWNER DECISION NEEDED' kept winning).

    One atomic record on the mission: a decision id, the text, and the id it supersedes. Every later launch card
    carries the live decisions (a superseded one is dropped, never shown). A live background owner that stopped
    to ask is stopped and RESUMED in the same session with the decision as its prompt; a mission with no live
    owner simply carries it on the next card. Re-sending an id with the same text is a no-op (no second wake);
    the same id with other text is refused. The caller never relays by hand."""
    import gsd_epoch as ge
    now = time.time() if now is None else now
    text = (text or "").strip()
    if not text:
        raise MissionError("empty decision")
    rec = load(mission_id)
    if rec is None:
        raise MissionError(f"no mission {mission_id}")
    if rec["state"] in TERMINAL:
        raise MissionError(f"{mission_id} is {rec['state']}; a decision cannot reach it")
    decisions = [dict(d) for d in (rec.get("decisions") or [])]
    did = (decision_id or f"D{len(decisions) + 1}").strip()
    prior = next((d for d in decisions if d["id"] == did), None)
    if prior is not None:
        if prior["text"] != text[:1000]:
            raise MissionError(f"decision {did} already exists with other text; send a new id with --supersedes {did}")
        return {"decision": prior, "recorded": False, "woke": {"ok": False, "why": "already recorded"}}
    if supersedes:
        old = next((d for d in decisions if d["id"] == supersedes), None)
        if old is None:
            raise MissionError(f"cannot supersede unknown decision {supersedes}")
        old["superseded_by"] = did
    new = {"id": did, "text": text[:1000], "at": now, **({"supersedes": supersedes} if supersedes else {})}
    decisions.append(new)
    legacy = [d for d in (rec.get("directives") or []) if not str(d).startswith("DECISION ")]
    lines = [f"DECISION {d['id']}: {d['text']}" for d in decisions if not d.get("superseded_by")]
    rec = transition(mission_id, expect_epoch=rec["epoch"], expect_state=rec["state"], event="owner_decision",
                     now=now, decisions=decisions, directives=[*legacy, *lines])
    import hashlib
    lr.ledger_append(mission_id, "owner_decision", mission_id=mission_id, epoch=rec["epoch"], decision_id=did,
                     supersedes=supersedes, sha=hashlib.sha256(new["text"].encode("utf-8")).hexdigest()[:16])
    woke: dict = {"ok": False, "why": "wake not requested"}
    if wake:
        owner = rec.get("owner") or {}
        sess = sessions if sessions is not None else host_sessions()
        row = _host_row(owner.get("session_id"), sess) if owner.get("session_id") and sess is not None else None
        if not owner.get("session_id"):
            woke = {"ok": False, "why": "no owner: the next launch card carries the decision"}
        elif owner.get("kind") != "background":
            woke = {"ok": False, "why": "interactive owner: not resumed; the decision is on the mission"}
        elif sess is None:
            woke = {"ok": False, "why": "host unreachable: the next launch card carries the decision"}
        elif row is None or row.get("state") in ("stopped", "failed", "exited"):
            woke = {"ok": False, "why": "owner not live: the next launch card carries the decision"}
        else:
            ok, how = stop_owner(owner, sess, pid_alive=pid_alive, runner=stop_runner, host_fetch=host_fetch)
            if not ok:
                woke = {"ok": False, "why": f"owner did not stop ({how}); the next launch card carries the decision"}
            else:
                woke = ge.continue_worker(
                    mission_id, rec, prompt=_decision_prompt(new),
                    decision={"decision": ge.CONTINUE, "cause": ge.TURN_CONTINUATION, "reason": f"owner decision {did}"},
                    runner=runner, stop_runner=stop_runner, now=now)
    return {"decision": new, "recorded": True, "woke": woke}


def is_cost_hold(hold: dict | None) -> bool:
    """spec mission-cost-hold-stops-worker: a hold the cost breaker set. Records written before `kind`
    existed are recognised by the breaker's own reason prefix."""
    if not hold:
        return False
    return hold.get("kind") == "cost" or str(hold.get("reason") or "").startswith("cost breaker")


def cost_hold_stop_enabled() -> bool:
    """Kill switch CPP_COST_HOLD_STOP=off: the worker is still told, but never stopped."""
    return str(os.environ.get("CPP_COST_HOLD_STOP") or "").strip().lower() not in ("0", "off", "false")


def set_owner_hold(mission_id: str, reason: str, now: float | None = None, kind: str | None = None,
                   expect_seq: int | None = None, extra: dict | None = None) -> dict:
    """Park a live mission (spec mission-owner-hold): plan_next answers none and renewal is refused
    until release_owner_hold. The record keeps its identity, epoch and state. kind="cost" (the breaker)
    additionally stops the running worker (spec mission-cost-hold-stops-worker)."""
    reason = (reason or "").strip()
    if not reason:
        raise MissionError("an owner hold needs a reason")
    rec = load(mission_id)
    if rec is None:
        raise MissionError(f"no mission {mission_id}")
    if rec["state"] in TERMINAL:
        raise MissionError(f"{mission_id} is {rec['state']}; there is nothing to hold")
    now = time.time() if now is None else now
    out = transition(mission_id, expect_epoch=rec["epoch"], expect_state=rec["state"], expect_seq=expect_seq,
                     event="owner_hold_set", now=now, reason=f"owner hold: {reason[:300]}",
                     owner_hold={"reason": reason[:1000], "set_at": now, **({"kind": kind} if kind else {}),
                                 **(extra or {})})
    hold_guard_budget(rec, reason)
    if kind == "cost":
        # Economic incident receipt (programme A2): a cost hold is a first-class event with a receipt, never only a
        # ledger row a person has to find. Best effort: the hold above already stands whatever happens here.
        try:
            import econ_incident
            receipt = econ_incident.record(out, reason, now=now)
            lr.ledger_append(mission_id, "economic_incident", mission_id=mission_id, level=receipt.get("level"),
                             spent=receipt.get("spent"), file=receipt.get("file"), error=receipt.get("error"))
        except Exception as exc:  # noqa: BLE001 -- recorded, never silent
            lr.ledger_append(mission_id, "economic_incident_error", mission_id=mission_id,
                             error=f"{type(exc).__name__}: {exc}"[:300])
    return out


def owner_pause(mission_id: str, reason: str, now: float | None = None, sessions=None,
                pid_alive=lr._pid_alive, stop_runner=None) -> dict:
    """An Owner pause that also STOPS the live background worker, through the host (`claude stop` + wait).
    Measured 2026-10-16 (m-f9290d78278f): a plain Owner hold left the worker running, and a raw SIGTERM
    was read by the Claude daemon as a crash and resumed. The stop is recorded as the hold's
    `worker_stopped_at`, so plan_next parks the dead owner instead of recovering or settling it.
    A failed stop leaves the hold standing and returns ok=False; nothing is retried here."""
    now = time.time() if now is None else now
    rec = set_owner_hold(mission_id, reason, now=now, kind="owner_stop")
    if sessions is None:
        sessions = host_sessions()
    ok, how = stop_owner(rec.get("owner"), sessions, pid_alive=pid_alive, runner=stop_runner)
    lr.ledger_append(mission_id, "owner_pause_stopped" if ok else "owner_pause_stop_failed",
                     mission_id=mission_id, ok=ok, how=how)
    if not ok:
        return {"ok": False, "how": how, "record": rec}
    rec = transition(mission_id, expect_epoch=rec["epoch"], expect_state=rec["state"], event="owner_pause_stopped",
                     now=now, reason=f"owner pause: worker stopped ({how})",
                     owner_hold={**rec["owner_hold"], "worker_stopped_at": now, "stop": how})
    return {"ok": True, "how": how, "record": rec}


def hold_guard_budget(rec: dict, reason: str = "") -> list[str]:
    """EVC U5: a hold that only flips the record leaves the live worker burning (it never reads the
    record). Also write a stop=1 session-budget guard file for every session the mission spent
    through, so hooks/session_budget_guard.js refuses that worker's next tool call. Best effort per
    sid: a failure is returned in the list as 'FAIL:<sid>', never raised (the hold itself stands)."""
    import mission_spend as ms
    done = []
    try:
        ids, _prefixes = ms.mission_sessions(rec)
    except Exception as e:  # noqa: BLE001
        return [f"FAIL:mission_sessions:{type(e).__name__}"]
    for sid in sorted(ids):
        try:
            ms.declare(sid, 1, 1, 1, extra={"hold": True, "hold_mission": rec.get("mission_id"),
                                           "hold_reason": reason[:200]})
            done.append(sid)
        except Exception as e:  # noqa: BLE001
            done.append(f"FAIL:{sid}:{type(e).__name__}")
    return done


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


_BUDGET_DEFAULTS = Path(__file__).resolve().parent.parent / "vault" / "config" / "mission-budget-defaults.json"
_BUILTIN_BUDGET = {"headroom_tokens": 15_000_000, "min_headroom_tokens": 1_000_000}


def _budget_defaults() -> tuple[dict, str]:
    """(defaults, source). A missing or unreadable file falls back to the built-in values and says so."""
    try:
        raw = json.loads(_BUDGET_DEFAULTS.read_text(encoding="utf-8"))
        cfg = {k: int(raw.get(k, v)) for k, v in _BUILTIN_BUDGET.items()}
        if not 0 < cfg["min_headroom_tokens"] <= cfg["headroom_tokens"]:
            raise ValueError("need 0 < min_headroom_tokens <= headroom_tokens")
        return cfg, "mission-budget-defaults.json"
    except Exception:  # noqa: BLE001 -- the source string carries the fallback
        return dict(_BUILTIN_BUDGET), "built-in defaults (file missing or unreadable)"


def auto_headroom(spent: int | None, epoch: int, max_cycles: int | None, cfg: dict,
                  claim_cost: dict | None = None) -> tuple[int, str]:
    """When `claim_cost` (a cost_to_completion.compile_cost result) is given it is PRIMARY and
    UNCLAMPED: headroom = its with_margin tokens. The [min, max] clamp below is only the fallback
    for a mission with no claim graph (and loses its upper bound only in the claim path)."""
    if claim_cost:
        wm = int(claim_cost["candidate"]["with_margin"])
        return wm, f"cost_to_completion {wm:,} ({claim_cost.get('confidence', 'UNKNOWN')}, unclamped)"
    return _rate_headroom(spent, epoch, max_cycles, cfg)


def _rate_headroom(spent: int | None, epoch: int, max_cycles: int | None, cfg: dict) -> tuple[int, str]:
    """Headroom from the mission's OWN measured rate when it has one: (spent / epochs started) x
    epochs it may still run (the current one included), clamped to [min_headroom, headroom]. A flat
    15M gave a 300k-per-epoch unit and a 10M-per-epoch unit the same allowance (cep-gen3 T1c).
    Unmeasured spend, no epoch yet or no cycle cap: the configured ceiling, named as such. Pure."""
    lo, hi = cfg["min_headroom_tokens"], cfg["headroom_tokens"]
    if spent is None or spent <= 0 or epoch < 1 or not max_cycles:
        why = ("spend unmeasured" if spent is None else "no spend yet" if spent <= 0
               else "no epoch yet" if epoch < 1 else "no cycle cap")
        return hi, f"ceiling {hi:,} ({why})"
    rate = spent / epoch
    left = max(1, int(max_cycles) - epoch + 1)
    raw = math.ceil(rate * left)
    h = min(hi, max(lo, raw))
    clamp = "" if h == raw else f", clamped to [{lo:,}, {hi:,}]"
    return h, f"rate {round(rate):,}/epoch x {left} epoch(s) left = {raw:,}{clamp}"


def claim_cost_for(rec: dict) -> dict | None:
    """The record's claim_cost: an explicit `claim_cost` wins; else compile the claim graph named by
    `claim_graph` (a JSON path). No graph, unreadable or refused = None (the rate fallback), never 0."""
    if rec.get("claim_cost"):
        return rec["claim_cost"]
    path = rec.get("claim_graph")
    if not path:
        return None
    try:
        import json as _json
        import cost_to_completion as ctc
        import route_admission as ra
        doc = _json.loads(Path(path).read_text(encoding="utf-8-sig"))
        return ctc.compile_cost(doc, ra.load_floors(None))
    except Exception:  # noqa: BLE001 -- no basis is a named fallback, not a zero
        return None


def _auto_budget(rec: dict, now: float, measure=None) -> dict:
    """cep-gen3 T1c: a live mission with no operator envelope gets an estimate so the cost breaker
    has something to judge: ceil((spent + headroom) / ratio), headroom from auto_headroom. An
    unmeasured spend counts as zero in the sum but is named in the basis, never passed off as 0.
    Any failure is a ledger row and the record is returned unchanged."""
    import mission_spend as ms
    mid = rec["mission_id"]
    if rec.get("state") in TERMINAL:
        return rec   # a finished record needs no envelope (and is then judged by no breaker)
    try:
        try:
            spent = (measure or ms.processed_tokens)(rec)
        except Exception:  # noqa: BLE001 -- unmeasured is a named state, not zero
            spent = None
        cfg, src = _budget_defaults()
        headroom, how = auto_headroom(spent, int(rec.get("epoch") or 0), rec.get("max_cycles"), cfg,
                                      claim_cost_for(rec))
        ratio = float(rec.get("token_trip_ratio") or ms.DEFAULT_TRIP_RATIO)
        cap = None
        if rec.get("authority_tokens"):
            # Owner authority is the upper bound of a default envelope: ratio x estimate may not outrun it.
            cap = int(rec["authority_tokens"]) - ms.closeout_reserve(rec)
            headroom = min(headroom, max(1, cap - (spent or 0)))
            how += f"; bounded by Owner authority {int(rec['authority_tokens']):,} less closeout reserve"
        est = math.ceil(((spent or 0) + headroom) / ratio)
        if cap is not None:
            est = max(1, min(est, int(cap // ratio)))
        spent_txt = "spend unmeasured" if spent is None else f"spent {spent:,}"
        basis = (f"auto envelope: ({spent_txt} + headroom {headroom:,} [{how}; {src}]) / trip ratio"
                 f" {ratio:g} = {est:,}")
        return transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                          event="envelope_auto_assigned", now=now, touch=False, token_estimate=est,
                          token_estimate_src="auto", token_estimate_basis=basis, reason=basis)
    except Exception as exc:  # noqa: BLE001 -- recorded, never silent
        lr.ledger_append(mid, "envelope_auto_unassigned", mission_id=mid,
                         error=f"{type(exc).__name__}: {exc}"[:300])
        return rec


def _recompile_forecast(rec: dict, now: float, rc: dict) -> dict:
    """An auto envelope outran its forecast while Owner authority remains: the forecast is invalid, the mission is
    not. Ledger what was spent against what was estimated, then re-assign the envelope inside the authority."""
    lr.ledger_append(rec["mission_id"], "forecast_invalidated", mission_id=rec["mission_id"], spent=rc["spent"],
                     old_estimate=rc["estimate"], authority=rc["authority"], ratio=rc["ratio"])
    return _auto_budget(rec, now, measure=lambda _r: rc["spent"])


def _cost_breaker(rec: dict, now: float, measure=None, fingerprint=None) -> dict:
    """TOK-18 gen 2 D1: judge a mission that carries `token_estimate` against its measured spend
    (tools/mission_spend.py). A trip parks it with the Owner hold -- held, never halted or renewed --
    so the Owner sees estimate, actual and the cause before more is spent. Fail-open on a measuring
    error: the breaker is an extra stop, and a broken meter must not stop missions on its own.
    Returns the record as it now stands."""
    import mission_spend as ms
    mid = rec["mission_id"]
    if rec.get("state") in TERMINAL:
        # A finished record has nothing left to park, and set_owner_hold refuses it: that raise escaped
        # supervise() and crashed EVERY pass for every mission (GEX44: m-da6e925b5092, 264 passes over
        # ~24 h from 2026-10-07; m-79f84cdd34dc, 2026-10-08, a COMPLETED record whose hold was cleared).
        return rec
    rec = _check_wake(rec, now, fingerprint)
    if mb.enabled():
        return _reconciled_breaker(rec, now, measure, fingerprint)
    try:
        spent = (measure or ms.processed_tokens)(rec)
        fp = mission_fingerprint(rec, mb.legacy_root(rec), fingerprint or progress_fingerprint)
        verdict = ms.judge(rec, spent, fp)
    except Exception as exc:  # noqa: BLE001 -- recorded, never silent
        lr.ledger_append(mid, "cost_breaker_unmeasured", mission_id=mid,
                         error=f"{type(exc).__name__}: {exc}"[:300])
        return rec
    if verdict.get("recompile"):
        return _recompile_forecast(rec, now, verdict["recompile"])
    if verdict["trip"]:
        lr.ledger_append(mid, "cost_breaker_tripped", mission_id=mid, spent=spent,
                         estimate=rec.get("token_estimate"), reason=verdict["trip"])
        return set_owner_hold(mid, verdict["trip"], now=now, kind="cost",
                              extra={"authority_kind": ms.authority_kind(rec)})
    if verdict["mark"]:
        return transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                          event="cost_mark", now=now, cost_mark=verdict["mark"],
                          reason=f"progress fingerprint moved at {spent:,} processed")
    return rec


WAKE_GRACE_S = 1800   # a woken worker has this long to move the work tree before the wake is judged a no-op


def judge_wake(expect: dict | None, fp_now: str | None, now: float, grace_s: float = WAKE_GRACE_S) -> str | None:
    """A3: did a wake produce progress? PROGRESS | PENDING | NO_PROGRESS | UNKNOWN, None without a stamp.
    The host's ack proves nothing (TB-FULL, 2026-10-18: a woken worker answered and produced no commit for 75 min
    while 19M tokens went by); the work tree is the evidence. Unmeasurable is UNKNOWN, never NO_PROGRESS. Pure."""
    if not expect:
        return None
    measurable = fp_now is not None and expect.get("fp") is not None
    if measurable and fp_now != expect["fp"]:
        return "PROGRESS"
    if now - float(expect.get("at") or now) < grace_s:
        return "PENDING"
    return "NO_PROGRESS" if measurable else "UNKNOWN"


def _check_wake(rec: dict, now: float, fingerprint=None) -> dict:
    """Judge a stamped wake once its grace has run; the verdict is a ledger row and a record field, then the
    stamp is cleared. Fail-open: a measuring error leaves the stamp for the next pass."""
    exp = rec.get("wake_expect")
    if not exp or rec.get("state") in TERMINAL:
        return rec
    mid = rec["mission_id"]
    try:
        fp = mission_fingerprint(rec, mb.legacy_root(rec), fingerprint or progress_fingerprint)
        verdict = judge_wake(exp, fp, now)
        if verdict in (None, "PENDING"):
            return rec
        lr.ledger_append(mid, {"PROGRESS": "wake_progress", "NO_PROGRESS": "wake_no_progress"}.get(verdict, "wake_unmeasured"),
                         mission_id=mid,
                         verdict=verdict, kind=exp.get("kind"), waited_s=int(now - float(exp.get("at") or now)))
        return transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"], event="wake_judged", now=now,
                          wake_expect=None, wake_last={"verdict": verdict, "at": now, "kind": exp.get("kind")},
                          reason=f"wake {verdict}")
    except Exception as exc:  # noqa: BLE001 -- recorded, the stamp stays for the next pass
        lr.ledger_append(mid, "wake_unjudged", mission_id=mid, error=f"{type(exc).__name__}: {exc}"[:300])
        return rec


def _ledger_has(mid: str, event: str, **match) -> bool:
    try:
        return any(e.get("event") == event and all(e.get(k) == v for k, v in match.items())
                   for e in lr.ledger_events(mid))
    except Exception:  # noqa: BLE001 -- an unreadable ledger repeats a row, never hides a condition
        return False


def _phase_state_file(rec: dict) -> str | None:
    """Where this mission's GSD phase is read: its lease's state file, else the workstream (or root) STATE.md."""
    sf = (rec.get("phase_lease") or {}).get("state_file")
    if sf:
        return str(sf)
    for base in (rec.get("work_dir"), rec.get("cwd")):
        if not base:
            continue
        root = Path(base) / ".planning"
        p = root / "workstreams" / rec["workstream"] / "STATE.md" if rec.get("workstream") else root / "STATE.md"
        if p.is_file():
            return str(p)
    return None


def _settle_completed_phase(rec: dict, now: float, measure=None, phase_fn=None) -> dict:
    """M4 A: when the GSD phase advances, settle the finished phase into the mission's work-class profile
    (tools/work_class_profile.py) BEFORE anything is leased or launched for the next one. processed = measured spend
    since the previous settlement mark; forecast = the phase lease that covered it, else None. Unmeasured spend is
    ledgered and settles nothing (a zero sample would teach the profile that phases are free); the mark stays, so a
    later pass settles the whole span once it can be measured. Returns the record as it now stands."""
    import mission_spend as ms
    import phase_lease as pls
    import work_class_profile as wcp
    mid = rec["mission_id"]
    if rec.get("state") in TERMINAL:
        return rec
    sf = _phase_state_file(rec)
    phase_now = (phase_fn or pls.current_phase)(sf) if sf else None
    if phase_now is None:
        return rec
    phase_now = str(phase_now)
    try:
        spent = (measure or ms.processed_tokens)(rec)
    except Exception:  # noqa: BLE001 -- unmeasured below
        spent = None
    cls = rec.get("work_class") or (rec.get("baseline") or {}).get("work_class") or "GSD_RESUME"
    lease = rec.get("phase_lease") or {}
    mark = rec.get("unit_settlement")
    if not mark:
        # First sight: the lease names where the phase began; without one the phase starts being counted here.
        if lease.get("phase") is not None:
            mark = {"phase": str(lease["phase"]), "processed": int(lease["base"]), "at": lease.get("set_at"),
                    "work_class": cls}
        elif spent is not None:
            return transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"], event="unit_settlement_seeded",
                              now=now, touch=False, unit_settlement={"phase": phase_now, "processed": int(spent),
                                                                      "at": now, "work_class": cls},
                              reason=f"settlement mark seeded at phase {phase_now}")
        else:
            return rec
    finished = str(mark["phase"])
    if phase_now == finished:
        return rec
    delta = None if spent is None else int(spent) - int(mark["processed"])
    if delta is None or delta <= 0:
        if not _ledger_has(mid, "unit_settle_unmeasured", phase=finished, next_phase=phase_now):
            lr.ledger_append(mid, "unit_settle_unmeasured", mission_id=mid, phase=finished, next_phase=phase_now,
                             spent=spent, mark=mark.get("processed"),
                             why="spend unmeasured" if delta is None else f"spend delta {delta} is not positive")
        return rec
    forecast = int(lease["forecast"]) if lease and str(lease.get("phase")) == finished else None
    try:
        receipt = wcp.settle_unit(cls, f"{mid}-phase-{finished}", {"processed": delta, "calls": 0},
                                  forecast=forecast, cause=f"phase {finished} complete")
    except (wcp.ProfileError, OSError) as exc:
        if not _ledger_has(mid, "unit_settle_failed", phase=finished):
            lr.ledger_append(mid, "unit_settle_failed", mission_id=mid, phase=finished,
                             error=f"{type(exc).__name__}: {exc}"[:300])
        return rec
    try:
        next_forecast = wcp.lease_forecast(cls)["forecast"]
    except wcp.ProfileError:
        next_forecast = None
    return transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"], event="unit_settled", now=now,
                      touch=False, reason=f"phase {finished} settled into {cls}: {delta:,} processed",
                      unit_settlement={"phase": phase_now, "processed": int(spent), "at": now, "work_class": cls,
                                       "last": {"phase": finished, "processed": delta, "forecast": forecast,
                                                "idempotent": bool(receipt.get("idempotent"))},
                                       "next_forecast": next_forecast},
                      ledger_extra={"phase": finished, "next_phase": phase_now, "work_class": cls,
                                    "processed": delta, "forecast": forecast, "next_forecast": next_forecast})


def _note_liveness_incident(mid: str, key: str, why: str) -> bool:
    """M4 B: one `liveness_incident` row per blocking condition (key), so a dead worker that cannot be replaced is
    visible where status reads, and an unchanged blocker costs no further rows. True when a row was written."""
    if _ledger_has(mid, "liveness_incident", key=key):
        return False
    lr.ledger_append(mid, "liveness_incident", mission_id=mid, key=key, why=why[:300])
    return True


def _dead_worker_open(rec: dict, sessions, pid_alive) -> bool:
    """An open mission, no hold of any kind, whose worker is positively DEAD (or absent): the ordinary relay/replace
    path owns it. LAUNCHING is excluded (a launch is already pending) and so is UNKNOWN liveness (it never replaces)."""
    if rec.get("state") not in (RUNNING, BLOCKED) or rec.get("owner_hold"):
        return False
    owner = rec.get("owner")
    return not owner or liveness(owner, sessions, pid_alive)[0] == DEAD


def _dead_worker_authority_guard(rec: dict, now: float, sessions, pid_alive, measure=None) -> dict:
    """M4 B: Owner authority with no room for a minimum lease is CAPITAL_EXHAUSTED, not a reason to launch. The cost
    breaker trips at authority minus the closeout reserve; between that line and the smallest successor lease
    (mission_recovery.MIN_LEASE_TOKENS before its reserve) a dead worker would be replaced by a successor AMR would
    refuse to price. Park it as a cost hold at the Owner boundary instead, and say so once. An unmeasured spend keeps
    today's path (the breaker is fail-open on a broken meter), it does not invent exhaustion."""
    auth = rec.get("authority_tokens")
    if not auth or not _dead_worker_open(rec, sessions, pid_alive):
        return rec
    import mission_recovery as mr
    import mission_spend as ms
    try:
        spent = (measure or ms.processed_tokens)(rec)
    except Exception:  # noqa: BLE001 -- unmeasured keeps the ordinary path
        return rec
    if spent is None:
        return rec
    need = -(-mr.MIN_LEASE_TOKENS * 1000 // int(1000 * (1 - mr.RESERVE_FRACTION)))
    room = int(auth) - int(spent)
    if room >= need:
        return rec
    mid = rec["mission_id"]
    why = (f"cost breaker (mission authority): CAPITAL_EXHAUSTED: {room:,} left of {int(auth):,} authority, below the "
           f"{need:,} a minimum successor lease needs; the dead worker is not replaced, new authority is the Owner's")
    _note_liveness_incident(mid, "CAPITAL_EXHAUSTED", why)
    return set_owner_hold(mid, why, now=now, kind="cost", expect_seq=rec.get("seq"),
                          extra={"authority_kind": ms.authority_kind(rec), "wait_type": "CAPITAL_EXHAUSTED"})


def _dead_worker_visibility(mid: str, row: dict) -> None:
    """M4 B: this pass planned an ordinary launch for a dead worker with actionable work and room. If the row shows
    the launch did not happen, name why (once per condition). A launch that went through writes nothing."""
    launch = row.get("launch")
    if isinstance(launch, dict) and launch.get("ok"):
        return
    if row.get("action") in ("completed", "halted", "halt", "settle", "continue", "slim_finished"):
        return
    blocker = row.get("held") or row.get("blocked")
    if not blocker and isinstance(launch, dict):
        blocker = f"launch failed: {launch.get('error') or launch.get('reason') or launch.get('why') or 'no cause given'}"
    if not blocker and row.get("stop") and row.get("action") in ("relay", "replace", "launch"):
        blocker = f"old worker not stopped: {row['stop']}"
    if not blocker:
        return
    text = str(blocker)
    key = re.sub(r"[0-9]+", "#", text)[:80]
    _note_liveness_incident(mid, key, f"dead worker with actionable work not relaunched: {text}")


def _phase_breaker(rec: dict, now: float, measure=None, phase_fn=None) -> dict:
    """CCR v5 A2: judge the mission's phase lease (tools/phase_lease.py) against measured spend. A TRIP, or an
    ambiguity (BLOCKED: unmeasured spend, unreadable or moved GSD phase), parks the mission with a cost hold
    flagged `phase_breaker`, which supervise stops WITHOUT the cost-hold grace. WARN is ledgered once per lease.
    Unlike _cost_breaker this is not fail-open on a measuring error: a lease exists to be an authority, and an
    unmeasured phase is BLOCKED, never permission. Returns the record as it now stands."""
    import mission_spend as ms
    import phase_lease as pls
    lease = rec.get("phase_lease")
    mid = rec["mission_id"]
    if not lease or rec.get("state") in TERMINAL or rec.get("owner_hold"):
        return rec
    try:
        spent = (measure or ms.processed_tokens)(rec)
    except Exception as exc:  # noqa: BLE001 -- becomes a BLOCKED verdict below
        lr.ledger_append(mid, "phase_breaker_unmeasured", mission_id=mid, error=f"{type(exc).__name__}: {exc}"[:300])
        spent = None
    verdict = pls.judge(lease, spent, (phase_fn or pls.current_phase)(lease["state_file"]))
    if verdict["verdict"] in (pls.TRIP, pls.BLOCKED):
        lr.ledger_append(mid, "phase_breaker_tripped", mission_id=mid, verdict=verdict["verdict"],
                         phase=lease["phase"], spend=verdict.get("spend"), forecast=lease["forecast"],
                         reason=verdict["reason"])
        return set_owner_hold(mid, f"cost breaker (phase lease): {verdict['reason']}", now=now, kind="cost",
                              extra={"phase_breaker": True, "phase": lease["phase"], "verdict": verdict["verdict"],
                                     "resume_with": "reforecast-only: set a new phase lease through envelope, "
                                                    "do not continue the phase's work"})
    if verdict["verdict"] == pls.WARN and rec.get("phase_lease_warned") != lease["set_at"]:
        return transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"], event="phase_warn", now=now,
                          touch=False, phase_lease_warned=lease["set_at"], reason=verdict["reason"])
    return rec


def _last_mark_at(mid: str, before: float) -> float | None:
    """When the breaker last marked progress before `before`, from the ledger (marks written before AMCR
    carry no time of their own). None = no mark: there is no window."""
    import datetime as _d
    best = None
    try:
        for row in lr.ledger_events(mid):
            if row.get("event") != "cost_mark":
                continue
            t = _d.datetime.fromisoformat(str(row.get("ts")).replace("Z", "+00:00")).timestamp()
            if t <= before + 1 and (best is None or t > best):
                best = t
    except Exception:  # noqa: BLE001 -- an unreadable ledger gives no window, never a guessed one
        return None
    return best


def _save_child_obligations(rec: dict, failed_sid: str | None, now: float) -> dict:
    """AMCR: background children the failed worker launched and never got back become durable obligations
    (KILLED_WITH_PARENT) before anything is compiled or relaunched. Idempotent; unknown children add none."""
    if not mb.enabled() or not failed_sid:
        return rec
    import gsd_epoch as ge
    try:
        kids = ge.child_work(failed_sid, now)
        transcript = lr.find_transcript(failed_sid)
    except Exception:  # noqa: BLE001 -- an unreadable transcript invents no obligation
        return rec
    if not kids.get("pending"):
        return rec
    obs = mb.capture_obligations(rec, kids, transcript, "KILLED_WITH_PARENT", now,
                                 lr.state_dir() / "obligations" / rec["mission_id"])
    if obs == (rec.get("obligations") or []):
        return rec
    return transition(rec["mission_id"], expect_epoch=rec["epoch"], expect_state=rec["state"],
                      expect_seq=rec.get("seq"), event="obligations_saved", now=now, touch=False,
                      obligations=obs, reason=f"{len(obs)} child obligation(s) of {failed_sid[:8]} kept")

def _breaker_receipt(mid: str, cls: str, action: str, **fields) -> None:
    lr.ledger_append(mid, "breaker_receipt", mission_id=mid, classification=cls, action=action, **fields)


def _reconciled_breaker(rec: dict, now: float, measure=None, fingerprint=None, child_fn=None,
                        transcript_fn=None) -> dict:
    """AMCR Progress Reconciliation Gate: the breaker never declares zero progress about a tree it has not
    proven to be the mission's. Order: rebind to where the worker actually writes -> fingerprint the
    bound root (plus any ambiguous candidate) -> judge -> before a stall trip, a working child earns a
    bounded extension, an unmeasurable tree never trips, and a binding that moved meanwhile voids the
    sample. Only then the hold, with the pending children saved as obligations first."""
    import gsd_epoch as ge
    import mission_spend as ms
    mid = rec["mission_id"]
    owner_sid = (rec.get("owner") or {}).get("session_id")
    find = transcript_fn or lr.find_transcript
    try:
        transcript = find(owner_sid) if owner_sid else None
    except Exception:  # noqa: BLE001 -- no transcript is "unknown", handled below
        transcript = None
    try:
        spent = (measure or ms.processed_tokens)(rec)
    except Exception as exc:  # noqa: BLE001 -- recorded, never silent
        lr.ledger_append(mid, "cost_breaker_unmeasured", mission_id=mid, error=f"{type(exc).__name__}: {exc}"[:300])
        return rec
    gen0 = mb.generation(rec)
    try:
        det = mb.detect_rebind(rec, transcript)
    except Exception as exc:  # noqa: BLE001 -- topology unknown is not "unchanged"
        det = None
        lr.ledger_append(mid, "rebind_detect_error", mission_id=mid, error=f"{type(exc).__name__}: {exc}"[:300])
    cands = (det or {}).get("candidates") or []
    if len(cands) == 1:
        try:
            nb = mb.new_binding(rec, cands[0], "detected", now)
        except mb.BindError as exc:
            nb = None
            lr.ledger_append(mid, "rebind_refused", mission_id=mid, path=cands[0], why=str(exc)[:300])
        if nb:
            _breaker_receipt(mid, mb.TOPOLOGY_CHANGED, "rebind", gen=nb["gen"], root=nb["root"], spent=spent,
                             previous=nb.get("previous"))
            return transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"], event="workspace_rebound",
                              now=now, touch=False, binding=nb, work_dir=nb["root"], cost_mark=None,
                              reason=f"workspace rebound (detected) gen {nb['gen']}: {nb['root']}")
    root = mb.execution_root(rec)
    fp_fn = fingerprint or progress_fingerprint
    fallback = False
    if mb.binding(rec) and not Path(root).is_dir() and (
            rec.get("binding_invalidated_at")
            or int((rec.get("progress_unknown") or {}).get("streak") or 0) >= mb.UNKNOWN_INCIDENT_STREAK):
        # Review MEDIUM-2: the bound worktree is gone (merged and removed, or deleted). After the unknown
        # streak the breaker judges the cwd -- where such a worker continues -- so a stall is still stopped.
        fallback, root = True, rec["cwd"]
        if not rec.get("binding_invalidated_at"):
            lr.ledger_append(mid, "binding_invalidated", mission_id=mid, gen=gen0,
                             root=(mb.binding(rec) or {}).get("root"), judged=root)
            rec = transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"], event="binding_invalidated_noted",
                             now=now, touch=False, binding_invalidated_at=now,
                             reason=f"bound root {(mb.binding(rec) or {}).get('root')} is gone; the breaker judges the cwd")
    try:
        fp = mission_fingerprint({**rec, "add_dirs": list(rec.get("add_dirs") or []) + cands}, root, fp_fn)
        verdict = ms.judge(rec, spent, fp)
    except Exception as exc:  # noqa: BLE001 -- recorded, never silent
        lr.ledger_append(mid, "cost_breaker_unmeasured", mission_id=mid, error=f"{type(exc).__name__}: {exc}"[:300])
        return rec
    evidence = {"gen": gen0, "root": root, "fp": fp, "candidates": cands, "spent": spent,
                "mark": rec.get("cost_mark"), "topology_judged": det is not None}
    if verdict["mark"]:
        _breaker_receipt(mid, mb.GOOD, "mark", **evidence)
        settled = mb.settle_obligations(rec, root, now)   # a landed artifact closes its child obligation
        return transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"], event="cost_mark", now=now,
                          cost_mark={**verdict["mark"], "at": now, "gen": gen0}, progress_unknown=None,
                          **({"obligations": settled} if settled else {}),
                          reason=f"progress fingerprint moved at {spent:,} processed (gen {gen0}, {root})")
    if verdict.get("recompile"):
        return _recompile_forecast(rec, now, verdict["recompile"])
    if fp is None and not verdict["trip"]:
        streak = int((rec.get("progress_unknown") or {}).get("streak") or 0) + 1
        why = "bound root missing" if not Path(root).is_dir() else "git could not fingerprint the bound root"
        _breaker_receipt(mid, mb.PROGRESS_UNKNOWN, "no_trip", streak=streak, why=why, **evidence)
        if streak == mb.UNKNOWN_INCIDENT_STREAK:
            lr.ledger_append(mid, "progress_unknown_incident", mission_id=mid, why=why, root=root)
        return transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"], event="progress_unknown",
                          now=now, touch=False, progress_unknown={"streak": streak, "why": why, "root": root},
                          reason=(f"INCIDENT: progress unmeasurable {streak} passes ({why}); the breaker will not "
                                  f"call it zero" if streak >= mb.UNKNOWN_INCIDENT_STREAK else
                                  f"progress unknown ({why}): no trip"))
    if not verdict["trip"]:
        return rec
    stall_trip = "since the work tree last changed" in verdict["trip"]
    kids = None
    if owner_sid:
        try:
            kids = (child_fn or ge.child_work)(owner_sid, now)
        except Exception:  # noqa: BLE001 -- unknown children: no extension, no obligation invented
            kids = None
    if stall_trip and kids and mb.child_active(kids, transcript, now):
        est = int(rec["token_estimate"])
        stall = int(rec.get("token_stall_budget") or est * ms.DEFAULT_STALL_FRACTION)
        burned = spent - int((rec.get("cost_mark") or {}).get("tokens") or 0)
        if burned <= stall * (1 + mb.CHILD_EXTRA_STALL_BUDGETS):
            _breaker_receipt(mid, mb.CHILD_ACTIVE, "no_trip", burned=burned,
                             children=[p.get("what") for p in kids.get("pending") or []], **evidence)
            return rec
    current = load(mid) or rec
    if mb.generation(current) != gen0:
        _breaker_receipt(mid, mb.STALE_GENERATION, "no_trip", current_gen=mb.generation(current), **evidence)
        return current
    # Review MEDIUM-1: from the generation check to the hold every write carries the seq it observed, so a
    # bind landing in between (the worker runs `bind` as its card says) voids this sample instead of
    # stopping the worker on it.
    try:
        rec = current
        if kids and kids.get("pending"):
            obs = mb.capture_obligations(rec, kids, transcript, "KILLED_WITH_PARENT", now,
                                         lr.state_dir() / "obligations" / mid)
            rec = transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"], expect_seq=rec.get("seq"),
                             event="obligations_saved", now=now, touch=False, obligations=obs,
                             reason=f"{len(obs)} child obligation(s) saved before the breaker stops the worker")
        held = set_owner_hold(mid, verdict["trip"], now=now, kind="cost", expect_seq=rec.get("seq"),
                              extra={"measured": {"gen": gen0, "root": root, "fallback": fallback},
                                     "authority_kind": ms.authority_kind(rec)})
    except CasConflict:
        now_rec = load(mid) or rec
        _breaker_receipt(mid, mb.STALE_GENERATION, "no_trip", current_gen=mb.generation(now_rec), **evidence)
        return now_rec
    _breaker_receipt(mid, mb.ZERO_CONFIRMED if stall_trip else "BUDGET_EXCEEDED", "trip", reason=verdict["trip"],
                     **evidence)
    lr.ledger_append(mid, "cost_breaker_tripped", mission_id=mid, spent=spent,
                     estimate=rec.get("token_estimate"), reason=verdict["trip"])
    return held


def bind_mission(mission_id: str, path: str, cause: str = "explicit", now: float | None = None) -> dict:
    """AMCR workspace rebind: every observer of the mission (breaker, relay, AMR, card) follows the new root
    from this one write. Refuses a path that is not the top of a worktree of the mission's repository."""
    rec = load(mission_id)
    if rec is None:
        raise MissionError(f"no mission {mission_id}")
    if rec["state"] in TERMINAL:
        raise MissionError(f"{mission_id} is {rec['state']}; nothing to bind")
    now = time.time() if now is None else now
    b = mb.binding(rec)
    if b and Path(path).is_dir() and mb._norm(path) == mb._norm(b["root"]):
        lr.ledger_append(mission_id, "bind_noop", mission_id=mission_id, root=b["root"], gen=b["gen"])
        return rec                     # review LOW-1: re-declaring the same root must not reset the stall clock
    try:
        nb = mb.new_binding(rec, path, cause, now)
    except mb.BindError as exc:
        raise MissionError(f"bind refused: {exc}") from exc
    extra = {}
    hold = rec.get("owner_hold") or {}
    rs = (hold.get("recovery") or {})
    if rs.get("state") in ("NOT_APPLICABLE", "RECOVERY_FAILED", "RECOVERY_EXHAUSTED") and \
            "unreadable" in str(rs.get("why") or ""):
        # The "residual unreadable" verdict was judged on the OLD root; a topology change re-opens it so the
        # next pass recovers on the bound root (m-4e31db7aca3f was parked on exactly that verdict).
        extra["owner_hold"] = {**hold, "recovery": None}
    return transition(mission_id, expect_epoch=rec["epoch"], expect_state=rec["state"], event="workspace_rebound",
                      now=now, touch=False, binding=nb, work_dir=nb["root"], cost_mark=None, **extra,
                      ledger_extra={"gen": nb["gen"], "root": nb["root"], "branch": nb["branch"], "cause": cause},
                      reason=f"workspace rebound ({cause}) gen {nb['gen']}: {nb['root']} [{nb['branch']}]")


def set_obligation(mission_id: str, oid: str, state: str, now: float | None = None) -> dict:
    """Close (or reopen) one durable child obligation. Only a mission transition removes an obligation."""
    if state not in mb.CHILD_STATES:
        raise MissionError(f"unknown obligation state {state!r} (one of {', '.join(mb.CHILD_STATES)})")
    rec = load(mission_id)
    if rec is None:
        raise MissionError(f"no mission {mission_id}")
    obs = [dict(o) for o in rec.get("obligations") or []]
    hit = [o for o in obs if o.get("id") == oid]
    if not hit:
        raise MissionError(f"{mission_id} has no obligation {oid}")
    now = time.time() if now is None else now
    hit[0].update(state=state, updated_at=now)
    return transition(mission_id, expect_epoch=rec["epoch"], expect_state=rec["state"], event="obligation_set",
                      now=now, touch=False, obligations=obs, reason=f"obligation {oid} -> {state}")


def topology(mission_id: str) -> dict:
    """The mission topology receipt: one inspectable answer to where, what and why, read cheaply."""
    import mission_recovery as mr
    rec = load(mission_id)
    if rec is None:
        raise MissionError(f"no mission {mission_id}")
    root = mb.execution_root(rec)
    hold = rec.get("owner_hold") or {}
    try:
        import mission_spend as ms
        spent = ms.processed_tokens(rec)
    except Exception:  # noqa: BLE001 -- unmeasured is shown as such
        spent = None
    mark = rec.get("cost_mark") or {}
    return {
        "goal": f"{rec['cwd']}|{rec.get('workstream') or ''}", "mission": mission_id, "state": rec["state"],
        "epoch": rec["epoch"], "worker": (rec.get("owner") or {}).get("session_id"),
        "binding_generation": mb.generation(rec), "execution_root": root, "root_exists": Path(root).is_dir(),
        "binding": mb.binding(rec), "live_head": (_git_ro(root, "rev-parse", "HEAD") or "").strip() or None,
        "live_branch": (_git_ro(root, "rev-parse", "--abbrev-ref", "HEAD") or "").strip() or None,
        "progress_frontier": mark or None,
        "spend": spent, "spend_since_progress": (spent - int(mark.get("tokens") or 0)) if spent is not None and mark else None,
        "progress_unknown": rec.get("progress_unknown"),
        "obligations": rec.get("obligations") or [],
        "hold": {k: hold.get(k) for k in ("reason", "kind", "set_at", "recovery", "wait")} if hold else None,
        "goal_liveness": mr.goal_liveness(rec), "reason": rec.get("reason"),
    }


def release_owner_hold(mission_id: str, now: float | None = None) -> dict:
    """Return a held mission to normal supervision. The budget clock is not reset."""
    rec = load(mission_id)
    if rec is None:
        raise MissionError(f"no mission {mission_id}")
    if not rec.get("owner_hold"):
        raise MissionError(f"{mission_id} has no owner hold")
    out = transition(mission_id, expect_epoch=rec["epoch"], expect_state=rec["state"],
                     event="owner_hold_released", now=now, owner_hold=None,
                     reason="owner hold released")
    _complete_owner_wait(mission_id)
    return out


# --------------------------------------------------------------------------- M2: typed resource requirements
def _blocking_hold(rec: dict) -> bool:
    """A hold that stops the breakers from judging. A resource hold does not: a cost trip must still be able
    to land over it (and then wins, see resource_gate)."""
    hold = rec.get("owner_hold")
    return bool(hold) and hold.get("kind") != "resource"


def set_requires(mission_id: str, obligation: str, specs: list[tuple[str, object]] | None = None,
                 clear: bool = False, now: float | None = None) -> dict:
    """Set/replace the requirements of ONE obligation (siblings kept), or clear them."""
    rec = load(mission_id)
    if rec is None:
        raise MissionError(f"no mission {mission_id}")
    if rec["state"] in TERMINAL:
        raise MissionError(f"{mission_id} is {rec['state']}; there is nothing to gate")
    if not clear and not specs:
        raise MissionError("give at least one requirement (--ram-free-gb, --path, --no-process) or --clear")
    keep = [r for r in rec.get("requires") or [] if r.get("obligation") != obligation]
    new = [] if clear else [{"id": f"{obligation}-{kind}", "kind": kind, "arg": arg, "obligation": obligation}
                            for kind, arg in specs]
    for r in new:
        if r["kind"] not in mres.KINDS:
            raise MissionError(f"unknown requirement kind {r['kind']!r}")
    allreq = keep + new
    return transition(mission_id, expect_epoch=rec["epoch"], expect_state=rec["state"], event="requires_set",
                      now=now, requires=allreq, reason=f"requires {obligation}: "
                      + ("cleared" if clear else ", ".join(f"{k} {a}" for k, a in specs)))


def resource_gate(rec: dict, now: float, sessions=None, pid_alive=lr._pid_alive, probes: dict | None = None) -> dict:
    """The sweep's resource step, run before plan_next. No model call. Returns the (possibly updated) record.

    Unmet or UNKNOWN for every obligation -> park as owner_hold kind "resource" (WAIT_RESOURCE).
    Any one obligation fully met -> admissible (siblings are independent); a resource hold is lifted with
    RESOURCE_AVAILABLE and the ordinary relay path runs. A cost or Owner hold is never touched here."""
    mid, hold = rec["mission_id"], rec.get("owner_hold") or {}
    if rec["state"] in TERMINAL:
        return rec
    reqs = rec.get("requires")
    if not reqs:
        if hold.get("kind") == "resource":   # the requirements were cleared under a standing resource hold
            return transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"], event="resource_hold_dropped",
                              now=now, owner_hold=None, resource_eval=None, reason="resource requirements cleared")
        return rec
    if hold and hold.get("kind") != "resource":
        return rec   # V-RES-COST-HOLD-WINS: nothing a resource reading says lifts a cost or Owner hold
    ev = mres.evaluate(reqs, probes)
    snap = {**mres.snapshot(ev, now), "key": mres.key(ev)}
    changed = (rec.get("resource_eval") or {}).get("key") != snap["key"]
    errors = [r["error"] for o in ev["obligations"].values() for r in o["requirements"] if r.get("error")]
    if ev["admissible"]:
        if hold:
            lr.ledger_append(mid, "RESOURCE_AVAILABLE", mission_id=mid, actionable=ev["actionable"],
                             waiting=ev["waiting"], waited_s=int(now - float(hold.get("set_at") or now)))
            return transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"], event="resource_available",
                              now=now, owner_hold=None, resource_eval=snap,
                              reason=f"resources available for {', '.join(ev['actionable'])}")
        if changed:
            return transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"], event="resource_evaluated",
                              now=now, touch=False, resource_eval=snap)
        return rec
    event = "RESOURCE_UNKNOWN" if not any(r["status"] == mres.UNMET for o in ev["obligations"].values()
                                          for r in o["requirements"]) else "RESOURCE_WAIT"
    text, extra = mres.reason(ev), {"wait_type": "WAIT_RESOURCE", "resource": snap}
    if hold:   # already parked: rewrite only when the verdict changed, so a drifting reading costs no row
        if not changed:
            return rec
        lr.ledger_append(mid, event, mission_id=mid, waiting=ev["waiting"], errors=errors, reason=text[:400])
        return transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"], event="resource_wait_changed",
                          now=now, owner_hold={**hold, "reason": text[:1000], **extra}, resource_eval=snap,
                          reason=text[:300])
    if rec["state"] == LAUNCHING:
        return rec   # a launch is in flight; the requirement gates the NEXT one
    if rec.get("owner") and liveness(rec.get("owner"), sessions, pid_alive)[0] != DEAD:
        return rec   # a worker that may still be running is not parked under it; its successor is what waits
    lr.ledger_append(mid, event, mission_id=mid, waiting=ev["waiting"], errors=errors, reason=text[:400])
    held = set_owner_hold(mid, text, now=now, kind="resource", expect_seq=rec.get("seq"), extra=extra)
    return transition(mid, expect_epoch=held["epoch"], expect_state=held["state"], event="resource_evaluated",
                      now=now, touch=False, resource_eval=snap)


# --------------------------------------------------------------------------- AMR: autonomous mission recovery
# A cost hold stops the executor, not the goal (plan vault/plans/amr-autonomous-mission-recovery-20261013.md).
# plan_next answers `recover` for a cost hold; recover_mission fences the failed worker, compiles a materially
# different successor (tools/mission_recovery.py), prices a bounded lease inside the remaining authority, admits
# its route, and only then lifts the hold and launches. Any refusal leaves the hold in place with a recorded
# OWNER_BOUNDARY: either the successor becomes authoritative or the safe held state remains.
AMR_LAUNCH_ATTEMPTS = 2


def set_authority(mission_id: str, tokens=None, extend_hours: float | None = None,
                  now: float | None = None, reason: str = "") -> dict:
    """Record Owner-granted programme authority on a mission: `authority_tokens` is the processed-token
    ceiling AMR may lease inside; `extend_hours` adds wall time. Both are Owner acts; the reason names it."""
    rec = load(mission_id)
    if rec is None:
        raise MissionError(f"no mission {mission_id}")
    fields = {}
    if tokens is not None:
        fields["authority_tokens"] = _token_count("authority", tokens)
    if extend_hours:
        fields["max_hours"] = float(rec.get("max_hours") or lr.DEFAULT_MAX_HOURS) + float(extend_hours)
    if not fields:
        raise MissionError("nothing to set: give --tokens and/or --extend-hours")
    return transition(mission_id, expect_epoch=rec["epoch"], expect_state=rec["state"],
                      event="authority_set", now=now, reason=f"authority: {fields} ({reason[:200]})", **fields)


def _amr_transcript(rec: dict, sid: str | None) -> Path | None:
    import mission_spend as ms
    if not sid:
        return None
    for base in (rec.get("cwd"), mb.execution_root(rec)):
        for d in (ms.mission_dirs(base, ms.projects_root()) if base else []):
            p = d / f"{sid}.jsonl"
            if p.is_file():
                return p
    return None


def _amr_delta(wd: str, head0: str | None) -> tuple[list[str], list[str], list[str]]:
    """(all changed paths since head0, uncommitted ones, committed ones). git unresolved -> empty lists."""
    porcelain = _git_ro(wd, "status", "--porcelain", "--untracked-files=all") or ""
    dirty = sorted({ln[3:].strip().strip('"') for ln in porcelain.splitlines() if len(ln) > 3})
    committed = []
    if head0:
        committed = [ln.strip() for ln in (_git_ro(wd, "diff", "--name-only", f"{head0}..HEAD") or "").splitlines()
                     if ln.strip()]
    return sorted(set(dirty) | set(committed)), dirty, sorted(set(committed))


def _amr_head(wd: str) -> str | None:
    h = (_git_ro(wd, "rev-parse", "HEAD") or "").strip()
    return h or None


def amr_compile(rec: dict, *, failed_sid: str | None, hold_reason: str, cause: str, now: float) -> dict:
    """Compile the successor of a failed (or finished) executor. Pure decisions live in mission_recovery;
    this gathers evidence and writes the packet, route and semantic delta under the state dir (never into
    the mission's work tree, whose fingerprint they would move). Returns {ok, ...} or {ok: False, boundary}.

    cause: "breaker" (a cost hold) or "unit_closed" (an AMR successor closed its receipt). A breaker on an
    AMR successor that COMMITTED work since its lease began is a productive lease running out, not a failed
    strategy: it renews the same strategy (law 2 forbids renewing only a zero-progress strategy) and is
    neither fenced nor counted against the recursion cap. Its ceiling is still the authority."""
    import mission_recovery as mr
    import mission_spend as ms
    import route_admission as ra
    mid = rec["mission_id"]
    wd = mb.execution_root(rec)
    amr = dict(rec.get("amr") or {})
    goal = f"{rec['cwd']}|{rec.get('workstream') or ''}"
    unit = mr.gsd_unit(wd, rec.get("workstream"))
    unit_id = (unit or {}).get("unit") or "unknown-unit"
    ev = mr.window_evidence(_amr_transcript(rec, failed_sid), wd)
    old_agents = [a["type"] for a in ev["agents"]]
    was_successor = bool(amr.get("launched") and amr.get("packet")
                         and (rec.get("wu_packet") or {}).get("path") == amr["packet"])
    head0 = (amr.get("lease_head") if was_successor else None) or amr.get("head") or \
        (re.search(r"HEAD at hand-off: ([0-9a-f]{7,40})", rec.get("card") or "") or [None, None])[1]
    delta, dirty, committed = _amr_delta(wd, head0)
    capital = [p for p in dirty if mr.path_class(p) in (mr.PLAN, mr.KNOWLEDGE)]
    planner_ran = any("plan" in a.lower() for a in old_agents)
    progress = mr.classify_progress(delta, ev, bool(unit) and not unit.get("plans") and planner_ran)
    if was_successor:
        old_strategy = amr["strategy"]          # the failed executor ran an AMR packet: it WAS the successor strategy
    else:
        old_strategy = mr.strategy_identity(goal, unit_id, mr.topology_of(old_agents), old_agents, "")
    fenced = list(amr.get("fenced") or [])
    renewal = cause == "breaker" and was_successor and any(mr.path_class(p) for p in committed)
    if renewal:
        failure = mr.LEASE_EXHAUSTED_WITH_PROGRESS
    elif cause == "breaker":
        failure = mr.classify_failure(hold_reason, ev, progress, old_strategy, fenced)
    else:
        failure = "UNIT_CLOSED"
    history = list(amr.get("history") or [])
    base = {"unit": unit_id, "failure": failure, "progress": progress, "failed_strategy": old_strategy,
            "evidence": {k: (len(v) if isinstance(v, list) else v) for k, v in ev.items()},
            "cause": "renewal" if renewal else cause}
    if not unit:
        return {"ok": False, **base, "not_applicable": True,
                "boundary": "residual UNKNOWN: GSD state of the work tree is unreadable"}
    if cause == "breaker" and not renewal and sum(
            1 for h in history if h.get("unit") == unit_id and h.get("cause") == "breaker") >= mr.MAX_RECOVERIES_PER_UNIT:
        return {"ok": False, **base, "boundary": f"recursion cap: {mr.MAX_RECOVERIES_PER_UNIT} recoveries of "
                                                 f"{unit_id} already ran; a third needs a new strategy from the Owner"}
    if cause == "breaker" and not renewal:
        topo = mr.recompile_topology(failure, unit_id, goal, old_agents, fenced + [old_strategy])
        if topo is None:
            return {"ok": False, **base, "boundary": f"no materially different strategy known for {failure}"}
        fenced = sorted(set(fenced) | {old_strategy})
    else:
        prev = amr.get("topology") or {}
        topo = {**prev, "strategy": mr.strategy_identity(goal, unit_id, prev.get("topology", mr.MAIN_THREAD), (),
                                                         prev.get("decomposition", ""))}
    residual = mr.compile_residual(unit, capital)
    spent = ms.processed_tokens(rec)
    ratio = float(rec.get("token_trip_ratio") or ms.DEFAULT_TRIP_RATIO)
    ceiling = rec.get("authority_tokens") or (int(ratio * int(rec["token_estimate"])) if rec.get("token_estimate") else None)
    lease = mr.price_lease(spent, ceiling, residual, ceiling_kind=ms.authority_kind(rec))
    base.update(topology=topo, residual=residual, spent=spent, ceiling=ceiling, ceiling_kind=lease.get("ceiling_kind"))
    if not lease["ok"]:
        return {"ok": False, **base, "boundary": lease["why"]}
    n = len(history) + 1
    d = ms.state_dir() / "recovery" / mid / f"r{n}"
    d.mkdir(parents=True, exist_ok=True)
    delta_path = None
    if ev["handbacks"] or capital:
        delta_path = d / "semantic_delta.md"
        delta_path.write_text("# Capitalized semantic delta of the failed attempt\n\n"
                              + "".join(f"- uncommitted capital: `{p}`\n" for p in capital)
                              + "\n" + "\n\n---\n\n".join(ev["handbacks"]) + "\n", encoding="utf-8")
    elif was_successor and amr.get("delta_path"):
        delta_path = Path(amr["delta_path"])     # still the paid-for design of this unit
    packet = d / "successor-packet.md"
    receipt = packet.with_name(packet.stem + "-receipt.md")
    packet.write_text(mr.render_packet(
        mission_id=mid, goal=goal, unit=unit, residual=residual, topology=topo, failure=failure, progress=progress,
        failed_strategy=old_strategy, delta_path=str(delta_path) if delta_path else None, lease=lease,
        receipt=str(receipt), work_dir=wd, workstream=rec.get("workstream")), encoding="utf-8")
    route = d / "route.json"
    route.write_text(json.dumps(mr.route_for(lease["envelope"], ra.load_floors()), indent=1), encoding="utf-8")
    (d / "evidence.json").write_text(json.dumps({**base, "lease": lease, "delta": delta, "capital": capital,
                                                 "committed": committed,
                                                 "handback_chars": [len(h) for h in ev["handbacks"]]},
                                                indent=1, default=str), encoding="utf-8")
    return {"ok": True, **base, "lease": lease, "fenced": fenced, "packet": str(packet), "route": str(route),
            "receipt": str(receipt), "dir": str(d), "n": n, "head": head0, "lease_head": _amr_head(wd),
            "ratio": ratio, "delta_path": str(delta_path) if delta_path else None}


# --------------------------------------------------------------------------- Owner waits are typed and delivered
# A parked wait is only valid if it has a known type, real figures from the hold, a queue row that skips the 24 h
# grace, and the exact resume command. m-4e31db7aca3f sat 8.5 h and m-28ab89fff085 ~20 h as an invisible OWNER_BOUNDARY.
OWNER_WAIT_TYPES = ("CAPITAL_EXHAUSTED", "OWNER_PRODUCT_DECISION", "SECURITY_BOUNDARY", "IRREVERSIBLE_ACTION",
                    "EXTERNAL_AUTHORITY_REQUIRED", "RESOURCE_POLICY_DECISION", "UNKNOWN")
# A wait the sweep resolves by itself. Not an Owner wait: it has no queue row and no economic incident.
NON_OWNER_WAIT_TYPES = ("WAIT_RESOURCE",)
WAIT_TYPES = OWNER_WAIT_TYPES + NON_OWNER_WAIT_TYPES
_WAIT_CAPITAL_RE = re.compile(r"cost breaker|mission budget|authority|ceiling|processed|iterations \d+ >= max|older than",
                              re.I)
_WAIT_SECURITY_RE = re.compile(r"trust dialog|security boundary|credential|permission boundary", re.I)
_FIG_SPENT_RE = re.compile(r"(?:processed (\d[\d,]{4,})|(\d[\d,]{4,}) processed)")
_FIG_CEIL_RE = re.compile(r"(?:authority|ceiling|stall budget|budget) (\d[\d,]{4,})")


def owner_wait_type(*texts) -> str:
    """Deterministic classifier for why a mission parks on the Owner. Anything unrecognised is UNKNOWN (and is
    reported as a failure to learn from, never silently parked)."""
    blob = " ".join(str(t or "") for t in texts)
    if _WAIT_SECURITY_RE.search(blob):
        return "SECURITY_BOUNDARY"
    if _WAIT_CAPITAL_RE.search(blob):
        return "CAPITAL_EXHAUSTED"
    return "UNKNOWN"


def owner_wait_figures(hold_reason, c: dict | None = None) -> dict:
    """Real spend/ceiling figures: parsed from the hold's own reason (OBSERVED there), else from the compile result,
    else absent. Never the string "None"."""
    c = c or {}
    out: dict = {}
    m = _FIG_SPENT_RE.search(str(hold_reason or ""))
    if m:
        out["spent"] = int((m.group(1) or m.group(2)).replace(",", ""))
    elif isinstance(c.get("spent"), (int, float)):
        out["spent"] = int(c["spent"])
    m = _FIG_CEIL_RE.search(str(hold_reason or ""))
    if m:
        out["ceiling"] = int(m.group(1).replace(",", ""))
    elif isinstance(c.get("ceiling"), (int, float)):
        out["ceiling"] = int(c["ceiling"])
    return out


def _owner_queue():
    root = str(Path(__file__).resolve().parents[1])
    if root not in sys.path:
        sys.path.insert(0, root)
    from modules.owner_queue import owner_queue as oq
    return oq


def _enqueue_owner_wait(mid: str, wait: dict) -> str | None:
    """Deliver the wait to the canonical Owner Queue as an urgent row (no grace). Fail-open: a queue fault must not
    stop the park itself, but it is ledgered so the invisibility is at least recorded."""
    try:
        return _owner_queue().append(
            f"Mission {mid} waits on the Owner: {wait['type']}", wait["resume"],
            unblocks=f"mission {mid}", source="amr_boundary", row_id=f"q-wait-{mid}", urgent=True,
            state_dir=os.environ.get("PP_OWNER_QUEUE_STATE_DIR") or None)
    except Exception as exc:  # noqa: BLE001 -- park proceeds; the failure is the record
        lr.ledger_append(mid, "owner_wait_enqueue_failed", mission_id=mid, why=f"{type(exc).__name__}: {exc}"[:200])
        return None


def _complete_owner_wait(mid: str) -> None:
    try:
        _owner_queue().complete(f"q-wait-{mid}", by="release_owner_hold",
                                state_dir=os.environ.get("PP_OWNER_QUEUE_STATE_DIR") or None)
    except Exception:  # noqa: BLE001 -- a stale row is visible noise, never a blocked release
        pass


def _amr_boundary(rec: dict, c: dict, now: float, hold: dict | None = None) -> dict:
    """Recovery cannot proceed safely: keep (or set) a cost-kind hold marked OWNER_BOUNDARY with ONE decision
    packet. plan_next parks on it -- never settles it -- so the packet's options stay real."""
    import mission_recovery as mr
    import mission_spend as ms
    mid = rec["mission_id"]
    d = ms.state_dir() / "recovery" / mid
    d.mkdir(parents=True, exist_ok=True)
    pkt = d / "owner-decision.md"
    base_hold = hold or rec.get("owner_hold") or {"reason": f"amr: {str(c.get('boundary'))[:200]}",
                                                  "set_at": now, "kind": "cost"}
    wtype = owner_wait_type(c.get("boundary"), base_hold.get("reason"))
    figs = owner_wait_figures(base_hold.get("reason"), c)
    gm_py = Path(__file__).resolve()
    resume = (f'python "{gm_py}" authority --mission {mid} --tokens <NEW_TOTAL> ; '
              f'python "{gm_py}" release --mission {mid}')
    fig_txt = (f"spent {figs['spent']:,}" if "spent" in figs else "spend not recorded in the hold") + \
        (f" of ceiling {figs['ceiling']:,}" if "ceiling" in figs else "; ceiling not recorded in the hold")
    akind = base_hold.get("authority_kind") or ms.authority_kind(rec)
    akind_txt = {"DEFAULT_POLICY": "DEFAULT_POLICY (no Owner authority was ever declared; the default allowance ran out)",
                 "OWNER": "OWNER (the Owner's declared authority)"}.get(akind, akind)
    pkt.write_text(
        f"# Owner decision -- mission {mid}\n\nWAIT TYPE: {wtype}\n\nAUTHORITY KIND: {akind_txt}\n\nThe cost breaker stopped the executor and "
        f"autonomous recovery stopped at a genuine boundary:\n\n> {c.get('boundary')}\n\nFailure "
        f"{c.get('failure') or 'n/a'}, progress {(c.get('progress') or {}).get('class') or 'n/a'}, "
        f"unit {c.get('unit') or 'n/a'}, "
        f"{fig_txt}.\n\nOptions: raise authority (`gsd_mission.py authority --mission {mid} --tokens N` "
        "or `--extend-hours H`, then `release`), name a new strategy as a directive, or close the mission. "
        f"The mission stays parked (not settled) until then.\n\nResume command:\n\n    {resume}\n", encoding="utf-8")
    wait = {"type": wtype, "figures": figs, "resume": resume, "packet": str(pkt), "at": now, "authority_kind": akind}
    wait["queue_id"] = _enqueue_owner_wait(mid, wait)
    if wtype == "UNKNOWN":
        lr.ledger_append(mid, "owner_wait_unknown", mission_id=mid, why=str(c.get("boundary"))[:300],
                         fios="failure: unclassified Owner wait")
    new_hold = {**base_hold, "wait": wait, "recovery": {"state": mr.OWNER_BOUNDARY, "why": c.get("boundary"),
                                                        "decision_packet": str(pkt), "at": now}}
    lr.ledger_append(mid, "recovery_owner_boundary", mission_id=mid, why=str(c.get("boundary"))[:300],
                     failure=c.get("failure"), wait_type=wtype, queue_id=wait["queue_id"])
    mr.pgo_append({"mission_id": mid, "result": "OWNER_BOUNDARY", "failure": c.get("failure"),
                   "progress": (c.get("progress") or {}).get("class"), "why": c.get("boundary")},
                  ms.state_dir() / "recovery" / "pgo.jsonl")
    return transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"], expect_seq=rec.get("seq"),
                      event="recovery_boundary", now=now, owner_hold=new_hold,
                      reason=f"recovery owner boundary: {str(c.get('boundary'))[:240]}")


def _amr_mark(rec: dict, hold: dict, state: str, why: str, now: float, event: str) -> dict:
    import mission_recovery as mr  # noqa: F401 -- state names live there
    return transition(rec["mission_id"], expect_epoch=rec["epoch"], expect_state=rec["state"],
                      expect_seq=rec.get("seq"), event=event, now=now,
                      owner_hold={**hold, "recovery": {**(hold.get("recovery") or {}), "state": state, "at": now,
                                                       "why": why[:300]}},
                      reason=f"recovery {state}: {why[:200]}")


def recover_mission(rec: dict, sessions, now: float, *, pid_alive=lr._pid_alive, runner=None,
                    stop_runner=None, launch=None, gsd_status=None) -> dict:
    """The `recover` action, a transaction over ONE observed record (seq-CAS on every write, audit F1):
    gates -> fence -> compile -> lease+settle -> admit -> commit (re-verify the hold, lift it) -> launch.
    Any refusal before commit leaves the hold; a wait writes nothing. Returns the supervise row fields."""
    import mission_recovery as mr
    import mission_spend as ms
    mid = rec["mission_id"]
    hold = dict(rec.get("owner_hold") or {})
    owner = rec.get("owner")
    failed_sid = (owner or {}).get("session_id") or (rec.get("previous_owner") or {}).get("session_id")
    wd = mb.execution_root(rec)
    try:
        st = (gsd_status or _supervise_gsd_status)(wd, workstream=rec.get("workstream"))
    except Exception as exc:  # noqa: BLE001 -- unanswered is not "work remains"
        st = {"outcome": "UNAVAILABLE", "reason": f"{type(exc).__name__}: {exc}"}
    outcome = st.get("outcome")
    if outcome in ("ALL_COMPLETE", "NO_PHASES"):
        # Nothing remains to recover: the legacy settle/park path decides, exactly as before AMR.
        _amr_mark(rec, hold, mr.NOT_APPLICABLE, f"gsd {outcome}: {st.get('reason')}", now, "recovery_not_applicable")
        return {"action": "recover_not_applicable", "reason": f"gsd {outcome}"}
    if outcome != "OK":
        return {"action": "recover_wait_gsd", "reason": f"gsd {outcome}: {st.get('reason')}"}   # F6: no write
    # F4: the same pre-launch gates the relay path applies, BEFORE anything is stopped or written.
    spent_cap = budget_exhausted(rec, now)
    if spent_cap:
        _amr_boundary(rec, {"boundary": f"mission budget: {spent_cap}", "unit": None, "failure": None}, now, hold)
        return {"action": "recover_boundary", "reason": f"budget: {spent_cap}"}
    ph = provider_hold(rec, now)
    if ph:
        return {"action": "recover_wait_provider", "reason": f"provider {ph.get('class', 'quota')}: {ph.get('reason')}"}
    try:
        import mission_launch_gate as mlg
        gate = mlg.refusal(rec, "replace", now)
    except Exception:  # noqa: BLE001 -- the relay path proceeds visibly on an unavailable gate; so does this
        gate = None
    if gate and gate.get("refuse"):
        return {"action": "recover_wait_gate", "reason": str(gate.get("reason"))[:300]}
    if owner:
        verdict, _ev = liveness(owner, sessions, pid_alive)
        if verdict == UNKNOWN:
            # The host could not be asked: the old worker may still be running, so no successor may start
            # beside it. Nothing is written; the next pass asks again.
            return {"action": "recover_wait_liveness", "reason": f"old worker liveness UNKNOWN: {_ev}"}
        if verdict != DEAD:
            ok, how = stop_owner(owner, sessions, pid_alive=pid_alive, runner=stop_runner)
            lr.ledger_append(mid, "recovery_fenced" if ok else "recovery_fence_failed", mission_id=mid,
                             worker=failed_sid, how=how)
            if not ok:
                return {"action": "recover_wait_fence", "reason": f"old worker not stopped yet: {how}"}
            hold = {**hold, "worker_stopped_at": now, "stop": how}   # F3: our stop is recorded with the hold
    rec = _save_child_obligations(rec, failed_sid, now)
    fs = mb.false_stall(rec, hold, mark_at=_last_mark_at(mid, float(hold.get("set_at") or now)))
    if fs:
        # AMCR: the hold said "nothing changed" about a tree that was not the mission's; the bound root
        # committed inside that window. Not a failed strategy -- nothing is fenced, nothing re-planned: lift
        # the hold and let the ordinary relay continue the residual (no Owner release).
        lr.ledger_append(mid, "false_stall_reconciled", mission_id=mid, root=fs["root"], commits=fs["commits"][:10],
                         gen=mb.generation(rec), hold=str(hold.get("reason"))[:300])
        transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"], expect_seq=rec.get("seq"),
                   event="false_stall_reconciled", now=now, owner_hold=None, cost_mark=None,
                   reason=f"false stall: {len(fs['commits'])} commit(s) in the bound root {fs['root']} inside the "
                          f"breaker's window; hold lifted, residual continues")
        return {"action": "recover_false_stall", "reason": f"{len(fs['commits'])} commit(s) in {fs['root']}"}
    c = amr_compile(rec, failed_sid=failed_sid, hold_reason=str(hold.get("reason") or ""), cause="breaker", now=now)
    lr.ledger_append(mid, "recovery_compiled", mission_id=mid, ok=c["ok"], failure=c.get("failure"),
                     progress=(c.get("progress") or {}).get("class"), unit=c.get("unit"),
                     failed_strategy=c.get("failed_strategy"),
                     successor_strategy=(c.get("topology") or {}).get("strategy"),
                     lease=(c.get("lease") or {}).get("lease"), why=c.get("boundary"))
    if not c["ok"] and c.get("not_applicable"):
        if not mb.enabled():
            _amr_mark(rec, hold, mr.NOT_APPLICABLE, str(c.get("boundary")), now, "recovery_not_applicable")
            return {"action": "recover_not_applicable", "reason": str(c.get("boundary"))[:300]}
        # AMCR: an unreadable residual is a recovery failure, not "nothing to recover" and not an Owner
        # wait (m-4e31db7aca3f sat 8.5 h as OWNER_BOUNDARY on a parser defect). Retried every pass; after
        # MAX_RECOVERY_FAILURES it is a surfaced liveness incident with its exact reason.
        n = int(((hold.get("recovery") or {}).get("failures") or 0)) + 1
        state = mr.RECOVERY_EXHAUSTED if n >= mr.MAX_RECOVERY_FAILURES else mr.RECOVERY_FAILED
        why = f"{c.get('boundary')} (attempt {n}/{mr.MAX_RECOVERY_FAILURES}; root {wd})"
        _amr_mark(rec, {**hold, "recovery": {"failures": n}}, state, why, now,
                  "recovery_incident" if state == mr.RECOVERY_EXHAUSTED else "recovery_failed")
        if state == mr.RECOVERY_EXHAUSTED:
            lr.ledger_append(mid, "liveness_incident", mission_id=mid, why=why[:300])
        return {"action": "recover_failed", "reason": why[:300]}
    if not c["ok"]:
        _amr_boundary(rec, c, now, hold)
        return {"action": "recover_boundary", "reason": str(c.get("boundary"))[:300]}
    if mr.mode() == "shadow":
        _amr_mark(rec, {**hold, "recovery_dir": c["dir"]}, mr.SHADOW_COMPILED, c["dir"], now, "recovery_shadow")
        return {"action": "recover_shadow", "reason": c["dir"]}
    spent = c["spent"]
    fp_now = mission_fingerprint(rec, wd, progress_fingerprint)
    prev = rec.get("amr") or {}
    entry = {"n": c["n"], "cause": c["cause"], "unit": c["unit"], "failure": c["failure"],
             "progress": c["progress"]["class"], "failed_strategy": c["failed_strategy"],
             "strategy": c["topology"]["strategy"], "lease": c["lease"]["lease"], "spent": spent,
             "breaker_at": hold.get("set_at"), "compiled_at": now, "dir": c["dir"]}
    amr = {**prev, "fenced": c["fenced"], "topology": c["topology"], "strategy": c["topology"]["strategy"],
           "packet": c["packet"], "unit": c["unit"], "head": prev.get("head") or c.get("head"),
           "lease_head": c.get("lease_head"), "delta_path": c.get("delta_path") or prev.get("delta_path"),
           "deny_agent_types": c["topology"]["deny_agent_types"], "launched": False,
           "history": [*(prev.get("history") or []), entry]}
    # Settle: the old attempt's spend is closed at `spent`; the successor is judged from here. wu_packet_epoch
    # (F2) makes decide_turn_end start a FRESH worker, never continue the fenced session.
    rec = transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"], expect_seq=rec.get("seq"),
                     event="recovery_leased", now=now,
                     wu_packet={"path": c["packet"], "sha256": _packet_digest(c["packet"])},
                     wu_packet_epoch=rec["epoch"],
                     token_estimate=mr.lease_estimate(spent, c["lease"]["lease"], c["ratio"]),
                     token_estimate_src="amr", token_stall_budget=int(c["lease"]["lease"] * 0.5),
                     cost_mark={"fp": fp_now, "tokens": spent}, amr=amr,
                     owner_hold={**hold, "recovery": {"state": "SUCCESSOR_LEASED", "dir": c["dir"], "at": now}},
                     reason=f"recovery lease {c['lease']['lease']:,} for {c['unit']} ({c['failure']} -> "
                            f"{c['topology']['topology']})")
    rec = admit_route(mid, c["route"], now=now)
    verdict = (rec.get("admission") or {}).get("verdict")
    if verdict not in LAUNCHABLE_VERDICTS:
        _amr_boundary(rec, {**c, "boundary": f"successor route not admitted: {verdict} "
                                             f"{(rec.get('admission') or {}).get('reasons')}"}, now)
        return {"action": "recover_boundary", "reason": f"route {verdict}"}
    # Commit. admit_route re-read the record, so seq alone cannot prove the hold is still ours: re-verify its
    # identity (same breaker hold, our lease, our packet) and CAS the lift on the seq we just verified.
    cur = rec.get("owner_hold") or {}
    if (cur.get("set_at") != hold.get("set_at") or (cur.get("recovery") or {}).get("state") != "SUCCESSOR_LEASED"
            or (rec.get("amr") or {}).get("packet") != c["packet"]):
        lr.ledger_append(mid, "recovery_commit_refused", mission_id=mid, why="hold changed under recovery")
        return {"action": "recover_conflict", "reason": "the hold changed during recovery; nothing launched"}
    rec = transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"], expect_seq=rec.get("seq"),
                     event="recovery_committed", now=now, owner_hold=None,
                     amr={**rec["amr"], "launched": True},
                     last_recovery={"n": c["n"], "hold": hold, "at": now},
                     reason=f"hold superseded by recovery r{c['n']} (fence kept on {failed_sid})")
    # The failed worker's stop=1 session guard is NOT touched: it is the fence that keeps that session from
    # spending again whatever happens to this record.
    res = (launch or launch_worker)(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                                    reason=f"AMR successor r{c['n']}: {c['failure']} -> {c['topology']['topology']}",
                                    runner=runner, now=now, note="", work_dir=rec.get("work_dir"))
    mr.pgo_append({"mission_id": mid, "result": "LAUNCHED" if res.get("ok") else "LAUNCH_FAILED", "n": c["n"],
                   "cause": c["cause"], "failure": c["failure"], "progress": c["progress"]["class"],
                   "old": c["failed_strategy"], "new": c["topology"]["strategy"], "topology": c["topology"]["topology"],
                   "lease": c["lease"]["lease"], "spent": spent,
                   "breaker_to_launch_s": round(now - float(hold.get("set_at") or now))},
                  ms.state_dir() / "recovery" / "pgo.jsonl")
    return {"action": "recovered" if res.get("ok") else "recover_launch_failed", "launch": res,
            "reason": f"r{c['n']} {c['failure']} -> {c['topology']['topology']} lease {c['lease']['lease']:,}"}


def amr_advance(rec: dict, now: float) -> tuple[dict, bool]:
    """An AMR successor closed its unit's receipt: compile the next unit with the same deflated topology
    (the fence stays). The mission's own GSD check has already said work remains. Returns (record, launch_ok):
    a refusal parks the mission at an OWNER_BOUNDARY hold and the caller must not relaunch the closed packet (F5)."""
    import mission_recovery as mr
    c = amr_compile(rec, failed_sid=None, hold_reason="", cause="unit_closed", now=now)
    lr.ledger_append(rec["mission_id"], "recovery_unit_advanced" if c["ok"] else "recovery_advance_refused",
                     mission_id=rec["mission_id"], unit=c.get("unit"), why=c.get("boundary"))
    if not c["ok"]:
        return _amr_boundary(rec, {**c, "boundary": f"next unit not compiled: {c.get('boundary')}"}, now), False
    prev = rec.get("amr") or {}
    last = (prev.get("history") or [{}])[-1]
    if last.get("cause") == "unit_closed" and last.get("unit") == c["unit"]:
        # The unit an advance already moved into closed again and GSD still lists it: its packet's done does
        # not match GSD's, and a third compile is a loop (m-0a2b4dad289b r3: ~13M on phase 1 of 4).
        return _amr_boundary(rec, {**c, "boundary": f"same unit {c['unit']} closed twice and GSD still lists "
                                                    "it; its packet's done criteria do not match GSD's"}, now), False
    amr = {**prev, "unit": c["unit"], "packet": c["packet"], "strategy": c["topology"]["strategy"],
           "lease_head": c.get("lease_head"), "delta_path": None, "launched": True,
           "history": [*(prev.get("history") or []),
                       {"n": c["n"], "cause": "unit_closed", "unit": c["unit"], "strategy": c["topology"]["strategy"],
                        "lease": c["lease"]["lease"], "spent": c["spent"], "compiled_at": now, "dir": c["dir"]}]}
    rec = transition(rec["mission_id"], expect_epoch=rec["epoch"], expect_state=rec["state"],
                     expect_seq=rec.get("seq"), event="recovery_unit_leased", now=now,
                     wu_packet={"path": c["packet"], "sha256": _packet_digest(c["packet"])},
                     wu_packet_epoch=rec["epoch"],
                     token_estimate=mr.lease_estimate(c["spent"], c["lease"]["lease"], c["ratio"]),
                     token_stall_budget=int(c["lease"]["lease"] * 0.5), amr=amr,
                     reason=f"next unit {c['unit']} lease {c['lease']['lease']:,}")
    rec = admit_route(rec["mission_id"], c["route"], now=now)
    if (rec.get("admission") or {}).get("verdict") not in LAUNCHABLE_VERDICTS:
        return _amr_boundary(rec, {**c, "boundary": f"next unit route not admitted: "
                                                    f"{(rec.get('admission') or {}).get('verdict')}"}, now), False
    return rec, True


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


CALIBRATION_FLOOR = 0.5   # an estimate under this share of the lineage's measured cost needs a basis
CALIBRATION_LINEAGE_MAX = 6


def estimate_calibration(rec: dict, estimate: int, measure=None) -> dict:
    """spec mission-cost-hold-stops-worker: compare a hand-set estimate with what this mission's
    `supersedes` chain measurably cost. Measured 2026-10-10: m-560939805e63 was armed at 36M while its
    lineage had spent ~243M over ~24 h; it reached 265.5M. A predecessor whose spend or lifetime cannot
    be measured contributes nothing (never a zero rate); none measurable -> verdict no_history."""
    import mission_spend as ms
    measure = measure or ms.processed_tokens
    tokens, hours, used, seen = 0, 0.0, [], set()
    pid = rec.get("supersedes")
    while pid and pid not in seen and len(seen) < CALIBRATION_LINEAGE_MAX:
        seen.add(pid)
        try:
            p = load(pid)
        except (MissionError, ValueError, OSError):   # a corrupt predecessor is unmeasurable, not fatal
            p = None
        if p is None:
            break
        try:
            spent = measure(p)
        except Exception:  # noqa: BLE001 -- unmeasurable is skipped and named, never zero
            spent = None
        life = float(p.get("updated_at") or 0) - float(p.get("created_at") or 0)
        if spent and life > 0:
            tokens += int(spent)
            hours += life / 3600.0
            used.append(pid)
        pid = p.get("supersedes")
    if not used:
        return {"verdict": "no_history", "line": "no lineage history (nothing measurable to compare)"}
    max_h = float(rec.get("max_hours") or 24)
    rate = tokens / hours
    expected = int(rate * max_h)
    line = (f"lineage {','.join(used)}: {tokens:,} processed over {hours:.1f} h = {int(rate):,}/h "
            f"x {max_h:g} h budget = {expected:,} expected")
    return {"verdict": "low" if estimate < CALIBRATION_FLOOR * expected else "ok", "line": line,
            "expected": expected}


def set_envelope(mission_id: str, *, token_estimate=None, model: str | None = None, autocompact=None,
                 wu_packet: str | None = None, continue_max_tokens=None, worker_mcp: str | None = None,
                 ccr_class: str | None = None, now: float | None = None, estimate_basis: str | None = None, measure=None,
                 phase_lease: dict | None = None) -> dict:
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
    if worker_mcp is not None:
        if worker_mcp not in WORKER_MCP_MODES:
            raise MissionError(f"worker_mcp must be one of {', '.join(WORKER_MCP_MODES)}, not {worker_mcp!r}")
        changes["worker_mcp"] = worker_mcp
    if ccr_class is not None:
        ccr_class = str(ccr_class).strip()
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", ccr_class):
            raise MissionError(f"ccr_class must be a plain class name, not {ccr_class!r}")
        changes["ccr_class"] = ccr_class
    if not changes and phase_lease is None:
        raise MissionError("nothing to set: give --token-estimate, --model, --autocompact, --wu-packet, "
                           "--continue-max-tokens, --worker-mcp, --ccr-class or --phase-lease")
    rec = load(mission_id)
    if rec is None:
        raise MissionError(f"no mission {mission_id}")
    if rec["state"] in TERMINAL:
        raise MissionError(f"{mission_id} is {rec['state']}; its envelope cannot change")
    if phase_lease is not None:
        # A phase lease is the stop-loss the model cannot read past (CCR v5 A2). Its base is MEASURED here,
        # at the phase start, never supplied: a caller-chosen base would let the lease be pre-spent or pre-credited.
        import phase_lease as pls
        import mission_spend as ms
        try:
            base = (measure or ms.processed_tokens)(rec)
        except Exception as exc:  # noqa: BLE001 -- refused with the cause, never a guessed base
            raise MissionError(f"phase lease refused: cannot measure the lease base ({type(exc).__name__}: {exc})")
        try:
            changes["phase_lease"] = pls.make_lease(
                phase=phase_lease.get("phase"), forecast=phase_lease.get("forecast"), base=int(base),
                state_file=phase_lease.get("state_file"), reserve=phase_lease.get("reserve", 0),
                set_at=time.time() if now is None else now)
        except pls.LeaseError as exc:
            raise MissionError(f"phase lease refused: {exc}")
        changes["phase_lease_warned"] = None
    if "token_estimate" in changes:
        cal = estimate_calibration(rec, changes["token_estimate"], measure=measure)
        basis = (estimate_basis or "").strip()
        if cal["verdict"] == "low" and not basis:
            raise MissionError(f"token_estimate {changes['token_estimate']:,} is below {CALIBRATION_FLOOR:g} x what "
                               f"this lineage measurably costs ({cal['line']}); raise it, or give "
                               f"--estimate-basis saying why this run is cheaper")
        changes["token_estimate_calibration"] = cal["line"]
        changes["token_estimate_src"] = None   # operator-set = no src (an earlier "auto" no longer applies)
        if basis:
            changes["token_estimate_basis"] = basis[:500]
    shown = {k: (v["path"] if k == "wu_packet" else v) for k, v in changes.items()
             if k not in ("token_estimate_calibration", "token_estimate_src", "token_estimate_basis")}
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


def _ccr_contract(rec: dict, pkt_path: str, cap) -> dict:
    """WU-W1: the pre-launch cost contract (tools/ccr_pgo.py) for the mission's CCR work class. No class,
    no PGO file or any failure -> UNFORECAST; this never raises. WU-A6: a `pgo-classes.json` (WU-A3 class
    models) in the PGO dir wins; it classifies the packet itself and carries the class confidence."""
    cls = rec.get("ccr_class")
    d = os.environ.get("CPP_CCR_PGO_DIR") or str(Path.home() / ".claude" / "ccr" / "state" / "pgo")
    if not cls and not (Path(d) / "pgo-classes.json").is_file():
        return {"verdict": "UNFORECAST"}
    try:
        import ccr_pgo
        f = Path(d) / "pgo-classes.json"
        if not f.is_file():
            f = Path(d) / f"{cls}.json"
        if not f.is_file():
            return {"verdict": "UNFORECAST", "work_class": cls}
        pgo = json.loads(f.read_text(encoding="utf-8-sig"))
        image = Path(pkt_path)
        first = next((ln.strip() for ln in image.read_text(encoding="utf-8", errors="replace").splitlines()
                      if ln.strip()), "")
        return ccr_pgo.contract(pgo, first, image, cap)
    except Exception as exc:  # noqa: BLE001 -- the forecast never stops an admission
        return {"verdict": "UNFORECAST", "work_class": cls, "error": f"{type(exc).__name__}: {exc}"[:200]}


def _admission_switch_off() -> bool:
    return str(os.environ.get("CPP_ROUTE_ADMISSION") or "").strip().lower() in ("0", "off", "false")


# WU-A6: a CCR contract acts only where its class model earned it. A3 confidence: MEDIUM/HIGH act, LOW observes.
# A W1 single-class file carries no confidence and keeps the W1 behaviour.
def _ccr_enforceable(contract: dict) -> bool:
    return contract.get("confidence") in (None, "MEDIUM", "HIGH")


# WU-A6 DEFLATE: the CCR mod's unit class (mods/cpp-cognitive-runtime/hooks/policy.ts WORK_CLASSES) for each
# A3 work class. generic and multimodal have no closure the mod knows, so they are never declared.
UNIT_FOR_CLASS = {"bounded-code": "bounded-code-worker", "long-textual": "bounded-code-worker",
                  "lookup": "read-only-reviewer"}


def deflate_unit(rec: dict, environ=None, declare: bool = True) -> tuple[dict, dict]:
    """(env to add, ledger row) for a Work Unit launch. A launch that already declares CCR_WORK_UNIT, or is no
    Work Unit, is left alone. A class the mod knows, at confidence MEDIUM or better, gets the unit declared
    (a declaration file in the mission store, its path in CCR_WORK_UNIT); LOW only records would_deflate.
    CPP_CCR_DEFLATE=off records and declares nothing. ``declare`` False (a launch that cannot carry the env)
    records would_deflate and writes no file."""
    environ = os.environ if environ is None else environ
    if not rec.get("wu_packet") or environ.get("CCR_WORK_UNIT"):
        return {}, {}
    if str(environ.get("CPP_CCR_DEFLATE") or "").strip().lower() in ("0", "off", "false"):
        return {}, {}
    contract = (rec.get("admission") or {}).get("ccr_contract") or {}
    cls, conf = contract.get("work_class"), contract.get("confidence")
    unit = UNIT_FOR_CLASS.get(cls)
    row = {"work_class": cls, "confidence": conf, "unit": unit}
    if not unit:
        return {}, {**row, "action": "no_unit_class"}
    if conf not in ("MEDIUM", "HIGH") or not declare:
        return {}, {**row, "action": "would_deflate"}
    path = lr.state_dir() / "units" / f"{rec['mission_id']}-e{rec.get('epoch')}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"class": unit, "id": rec["mission_id"]}), encoding="utf-8")
    return {"CCR_WORK_UNIT": str(path)}, {**row, "action": "deflated", "declared": str(path)}


_DETERMINISTIC_RE = re.compile(r"^\s*deterministic:\s*(\S.*?)\s*$", re.MULTILINE)


def deterministic_script(rec: dict) -> list[str] | None:
    """The argv a packet's `deterministic: <script> [args]` line names, or None. The script must be a .py or
    .sh file inside the mission's work tree; a line naming anything else raises MissionError."""
    import shlex
    pkt = rec.get("wu_packet")
    if not pkt:
        return None
    try:
        text = Path(pkt["path"]).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = _DETERMINISTIC_RE.search(text)
    if not m:
        return None
    args = shlex.split(m.group(1))
    root = Path(rec.get("work_dir") or rec["cwd"]).resolve()
    script = (root / args[0]).resolve()
    if not script.is_relative_to(root) or not script.is_file() or script.suffix not in (".py", ".sh"):
        raise MissionError(f"deterministic: {args[0]!r} is not a .py/.sh file inside {root}")
    return [sys.executable if script.suffix == ".py" else "bash", str(script), *args[1:]]


def _run_deterministic(rec: dict, argv: list[str], now: float, run=None) -> dict:
    """DETERMINISTIC_PATH: run the packet's script instead of a worker. No epoch is claimed and no model is
    called. Exit 0 completes the mission with the output's sha256 on the record; anything else leaves the
    mission where it was, ledgered, and never falls back to a model."""
    import hashlib
    import subprocess
    mid = rec["mission_id"]
    cwd = rec.get("work_dir") or rec["cwd"]
    try:
        r = (run or (lambda a, c: subprocess.run(a, cwd=c, capture_output=True, text=True, encoding="utf-8",
                                                  errors="replace", timeout=600)))(argv, cwd)
        rc, out, err = r.returncode, r.stdout or "", r.stderr or ""
    except Exception as exc:  # noqa: BLE001 -- the script could not run: recorded, never retried by a model
        rc, out, err = None, "", f"{type(exc).__name__}: {exc}"
    out_path = lr.state_dir() / "deterministic" / mid / f"e{rec.get('epoch')}.out"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out, encoding="utf-8")
    res = {"argv": argv[1:], "rc": rc, "model_calls": 0, "out_path": str(out_path),
           "stdout_sha256": hashlib.sha256(out.encode("utf-8")).hexdigest(), "at": now}
    if rc != 0:
        lr.ledger_append(mid, "deterministic_failed", mission_id=mid, epoch=rec.get("epoch"),
                         **res, stderr=err[-300:])
        return {"ok": False, "deterministic": True, "epoch": rec.get("epoch"), "bg_id": None,
                "why": f"deterministic script exited {rc}", "detail": err[-300:], **res}
    transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"], event="deterministic_completed",
               now=now, state=COMPLETED, pending=None, deterministic=res,
               reason=f"deterministic path: {Path(argv[1]).name} exit 0, 0 model calls")
    return {"ok": True, "deterministic": True, "epoch": rec.get("epoch"), "bg_id": None, "stdout": out[-4000:], **res}


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
    # WU-ADV2a: the mission's spend goal bounds admission too. No goal / unmeasurable keeps the above.
    goal_rem = halt_authority(rec)
    if goal_rem is not None:
        remaining = goal_rem if remaining is None else min(remaining, goal_rem)
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
    # WU-W1: CCR pre-launch cost contract. Observe records; CPP_CCR_ADMISSION=enforce refuses SPLIT/DEFLATE.
    contract = _ccr_contract(rec, pkt["path"], (res.get("envelope") or {}).get("stop"))
    admission["ccr_contract"] = contract
    if (str(os.environ.get("CPP_CCR_ADMISSION") or "").strip().lower() == "enforce"
            and contract.get("verdict") in ("SPLIT", "DEFLATE") and _ccr_enforceable(contract)):
        admission["verdict"] = "RECOMPILE"   # known and not launchable
        admission["reasons"] = ([f"ccr_contract:{contract['verdict']}"] + admission["reasons"])[:6]
        res = {**res, "verdict": "RECOMPILE", "reasons": admission["reasons"]}
    # The route's worker profile is recorded on the mission, so launch reads one field. Only an
    # admission-set value is ever replaced; a profile an operator set by hand stays.
    slim = next((w["profile"] for w in admission["workers"] if w["profile"] in SLIM_PROFILES), None)
    prof = ({"worker_profile": slim, "worker_profile_src": "admission"} if slim
            else {"worker_profile": None, "worker_profile_src": None} if rec.get("worker_profile_src") == "admission"
            else {})
    try:   # CDC C3: the worker-launch edge leaves the same capability row as the Agent spawn edge
        import cognitive_admission as _ca
        import cognitive_effects as _ce
        _ca.record(None, mission_id, res.get("effect") or _ce.normalize(route.get("effect")) or _ce.BOUNDED_COGNITION,
                   f"route {res['verdict']}", decision="allow" if res["verdict"] in ("ADMISSIBLE", "WATCHED") else "refuse",
                   edge="launch")
    except Exception:  # noqa: BLE001 -- the capability log never stops an admission
        pass
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
    if adm.get("verdict") is not None and adm.get("verdict") not in KNOWN_VERDICTS:
        return (f"verdict_unknown: {adm.get('verdict')!r} is not a verdict this build knows "
                f"(record code_id {rec.get('code_id')}, this CODE_ID {CODE_ID}): admit again with this build")
    if adm.get("verdict") not in LAUNCHABLE_VERDICTS:
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


def readmit_for_relay(rec: dict, *, now: float | None = None, measure=None) -> dict:
    """A3-chain: the supervisor relays a packet mission with no resident orchestrator, so nobody runs
    `admit` between epochs. An admission pays for ONE launch (review F3); when the ONLY thing refusing
    the successor is that it was consumed, the supervisor re-admits it deterministically from the
    route file the Owner-admitted verdict recorded: same route, remaining budget re-measured. Anything
    else (never admitted, non-ADMISSIBLE, packet or route changed, switch off) is left to
    `admission_refusal`, so a RECOMPILE/DEFER verdict still stops the launch. Returns the (re)loaded
    record and never raises: a failed re-admission leaves the refusal in place."""
    mid = rec["mission_id"]
    adm = rec.get("admission") or {}
    if (not rec.get("wu_packet") or _admission_switch_off() or adm.get("verdict") != "ADMISSIBLE"
            or adm.get("consumed_epoch") is None or not adm.get("route_path")):
        return {"readmitted": False, "rec": rec}
    if (adm.get("packet_sha256") != _packet_digest(rec["wu_packet"]["path"])
            or adm.get("route_file_sha256") != _packet_digest(adm["route_path"])):
        return {"readmitted": False, "rec": rec}   # changed under us: a human decision, not a relay
    try:
        new = admit_route(mid, adm["route_path"], now=now, measure=measure)
    except Exception as exc:  # noqa: BLE001 -- the refusal stays; recorded, not raised
        lr.ledger_append(mid, "relay_readmit_failed", mission_id=mid, epoch=rec["epoch"],
                         error=f"{type(exc).__name__}: {exc}"[:300])
        return {"readmitted": False, "rec": rec}
    lr.ledger_append(mid, "relay_readmitted", mission_id=mid, epoch=new["epoch"],
                     verdict=(new.get("admission") or {}).get("verdict"), route=adm["route_path"],
                     remaining=(new.get("admission") or {}).get("remaining"))
    return {"readmitted": True, "rec": new}


def _declare_worker_envelope(rec: dict, sid: str | None) -> None:
    """The admitted envelope becomes the worker's SESSION envelope, enforced call by call by
    hooks/session_budget_guard.js. Recorded either way, never silent."""
    adm = rec.get("admission") or {}
    if not sid or not rec.get("wu_packet") or adm.get("verdict") not in LAUNCHABLE_VERDICTS:
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


def gsd_fact_line(st: dict | None) -> str:
    """GSD's own next action, appended to a /gsd-autonomous wake. m-b8541432cbf9 (2026-10-18): GSD
    answered "phase 1: 3 plans, 0 summaries -> /gsd-execute-phase 1" on every pass while the worker,
    woken with the bare command, read one phase directory as "the milestone's only phase" and halted
    no_progress. Empty when GSD named nothing. Kill switch: CPP_GSD_FACT_PROMPT=off."""
    if (os.environ.get("CPP_GSD_FACT_PROMPT") or "").strip().lower() == "off":
        return ""
    nxt = (st or {}).get("next") or {}
    if (st or {}).get("outcome") != "OK" or not nxt.get("command"):
        return ""
    return ("\n\nSUPERVISOR FACT (asked GSD this pass): "
            f"{(st or {}).get('reason') or 'work remains'}; next = {nxt['command']} "
            f"(phase {nxt.get('phase')}: {nxt.get('phase_name')}; {nxt.get('reason')}). "
            "Run it. Your own reading of the work tree does not override GSD's answer: a phase is done "
            "only when GSD says so (every plan has its SUMMARY and the phase its VERIFICATION).")


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
    cap = (rec.get("continuity_from") or {}).get("capsule_path")
    return "\n".join([
        *([f"FAULT CAPSULE: your predecessor stopped without its receipt. Start from {cap} "
           "(DONE = committed, SALVAGE = uncommitted); do not redo DONE."] if cap else []),
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
    wd = mb.execution_root(rec) if mb.binding(rec) else rec.get("work_dir")
    parts += mb.card_lines(rec)
    parts += mres.card_lines(rec)   # [] for a mission without `requires`
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
    g = resolve_exe("git") or "git"
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
    g = resolve_exe("git") or "git"
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
    g = resolve_exe("git") or "git"

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
            # Behind is milder than diverged: a proven worktree is followed the same way, and the
            # dirty files (a peer's, in a shared checkout) are left alone. Measured 2026-10-22:
            # m-188e06ee9603 held on every pass by another pane's uncommitted edits.
            if (proven_workstream
                    and there[0] == os.path.normcase(str(Path(work_dir).resolve()))
                    and _worktree_carries_workstream(work_dir, cwd, proven_workstream)):
                return {"status": "behind_followed", "detail": f"cwd {hc[:12]} is behind work_dir"
                        f" {hw[:12]} and dirty, but the work_dir is a proven worktree carrying"
                        f" {proven_workstream}'s latest roadmap; following it, nothing moved", **facts}
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


def live_root(rec: dict) -> str:
    """AMCR: the execution root, overridden by the owner's transcript only when that names ANOTHER worktree
    of the repository. effective_workdir answers the cwd itself for a worker that moved with Set-Location
    (its transcript cwd never changes), and `ew or recorded` then discarded a binding that knew better."""
    root = mb.execution_root(rec)
    if not rec.get("owner"):
        return root
    try:
        ew = effective_workdir(rec["owner"]["session_id"], rec["cwd"], rec.get("workstream"))
    except Exception:  # noqa: BLE001 -- keep the bound dir; never guess
        return root
    if not mb.enabled():
        return ew or root
    return ew if ew and mb._norm(ew) != mb._norm(rec["cwd"]) else root


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
                     pending_decision=None, failed_launches=0, iterations=rec.get("iterations", 0) + 1, worker=sid,
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


def _wait_host_released(session_id: str, fetch, wait_s: float) -> bool:
    """True once the host no longer lists the session as live. An unanswerable host is not a release."""
    deadline = time.time() + wait_s
    while True:
        rows = fetch()
        if rows is not None:
            row = _host_row(session_id, rows)
            if row is None or row.get("status") not in HOST_LIVE_STATUSES:
                return True
        if time.time() >= deadline:
            return False
        time.sleep(1)


def stop_owner(owner: dict | None, sessions: list[dict] | None, pid_alive=lr._pid_alive,
               runner=None, wait_s: float | None = None, cmdline=None,
               killer=None, host_fetch=None) -> tuple[bool, str]:
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
    live = row.get("status") in HOST_LIVE_STATUSES
    if row.get("state") not in ("stopped", "done", "exited", "failed") or live:
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
    # An injected stop runner means an injected world (tests, dry runs): there is no real host to poll.
    fetch = host_fetch or (host_sessions if runner is None else None)
    if live and fetch is not None:
        # No pid, but the host still lists the session alive: resuming now makes the host start a COPY
        # ("session X is already running in the background"). Wait for the host to release it.
        if _wait_host_released(owner["session_id"], fetch, wait_s):
            return True, "stopped; host no longer lists it as live"
        return False, f"host still lists {owner['session_id'][:8]} as {row.get('status')} after {int(wait_s)} s"
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
                            "continue_max_tokens", "wu_packet", "mission_terms", "note", "goal",
                            "amr", "authority_tokens")   # AMR audit F9: the fence and authority travel with the work


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
        fp_now = mission_fingerprint(rec, halt_wd, fingerprint or progress_fingerprint)
        if fp_now is not None and fp_now == origin:
            why_not = "no progress in this mission (work tree unchanged since its first launch)"
    if not why_not and (rec.get("token_estimate") or rec.get("lineage_token_budget")):
        # UCDA A2: an exhausted lineage budget earns no renewal. Unmeasured is not exhausted.
        try:
            import mission_spend as ms
            lr_ = ms.lineage_remaining(rec)
            if lr_.get("remaining") is not None and lr_["remaining"] <= 0:
                why_not = (f"lineage budget exhausted: {lr_['spent']:,} processed of {lr_['budget']:,} "
                           f"across lineage {rec.get('lineage_id') or rec['mission_id']}")
        except Exception:  # noqa: BLE001
            pass
    if not why_not and rec.get("authority_tokens"):
        try:
            import mission_spend as ms
            sp = ms.lineage_spend(rec["mission_id"], extra=rec)
            base = int(rec.get("lineage_authority_tokens") or rec["authority_tokens"])
            left = base - ms.closeout_reserve(rec) - int(sp["processed"])
            if not sp["unmeasured"] and left <= 0:
                why_not = (f"Owner authority exhausted: {sp['processed']:,} processed of {base:,} "
                           f"across lineage {rec.get('lineage_id') or rec['mission_id']}")
        except Exception:  # noqa: BLE001 -- an unanswered meter never refuses
            pass
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
    # UCDA A2: the lineage owns the budget; the successor inherits what REMAINS, not a fresh estimate.
    if rec.get("token_estimate") or rec.get("lineage_token_budget"):
        import mission_spend as ms
        try:
            lr_ = ms.lineage_remaining(rec)
        except Exception:  # noqa: BLE001 -- an unanswered meter is unknown, never zero
            lr_ = {"budget": rec.get("lineage_token_budget") or rec.get("token_estimate"),
                   "remaining": None}
        if lr_.get("budget"):
            carried["lineage_token_budget"] = lr_["budget"]
            if lr_.get("remaining") is None:
                carried["lineage_spend_unknown"] = True
            else:
                carried["token_estimate"] = max(int(lr_["remaining"]), 1)
    # The Owner's authority is a ceiling on the lineage, not a fresh grant per link: the successor's meter starts at 0,
    # so carrying `authority_tokens` unchanged let each iteration-cap renewal spend the full ceiling again
    # (m-c63384bde9d0, 2026-10-18: ceiling 260M, the renewal inherited an unbounded envelope).
    if rec.get("authority_tokens"):
        import mission_spend as ms
        try:
            sp = ms.lineage_spend(rec["mission_id"], extra=rec)
        except Exception:  # noqa: BLE001 -- an unanswered meter is unknown, never zero
            sp = {"processed": 0, "unmeasured": [rec["mission_id"]]}
        # the lineage keeps the ORIGINAL grant: the record's own `authority_tokens` is already net of earlier links
        base = int(rec.get("lineage_authority_tokens") or rec["authority_tokens"])
        carried["lineage_authority_tokens"] = base
        if sp["unmeasured"]:
            carried["lineage_spend_unknown"] = True
        else:
            carried["authority_tokens"] = max(base - int(sp["processed"]), 1)
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


# --------------------------------------------------------------------------- halt-continue (WU-1H)
# A worker that stops without its receipt (breaker trip, dead pid, success without a receipt) leaves a
# fault capsule and one bounded renewal of the same packet. CPP_HALT_CONTINUE=off restores the old halt.
HALT_CONTINUE_MAX_RENEWAL = 2


def halt_continue_on() -> bool:
    return os.environ.get("CPP_HALT_CONTINUE", "").lower() != "off"


def resolve_exe(name: str) -> str | None:
    """Certified executable resolver: CPP_EXE_<NAME> override, shutil.which, known Windows paths.
    None only when every source fails."""
    import shutil
    import subprocess
    key = name.lower()
    cands = [os.environ.get(f"CPP_EXE_{key.upper()}")]
    if key == "git":
        cands.append(os.environ.get("CPP_GIT_EXE"))
    for c in cands:
        if c and Path(c).exists():
            return c
    w = shutil.which(name)
    if w:
        return w
    known = {"git": [r"C:\Program Files\Git\cmd\git.exe"], "python": [sys.executable]}.get(key, [])
    for c in known:
        if c and Path(c).exists():
            return c
    if key == "node":
        try:
            r = subprocess.run([os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "where.exe"),
                                "node"], capture_output=True, text=True, timeout=15)
            for ln in r.stdout.splitlines():
                if ln.strip() and Path(ln.strip()).exists():
                    return ln.strip()
        except Exception:  # noqa: BLE001
            pass
    return None


def _git_ro(wd: str, *args: str) -> str | None:
    """None = git UNRESOLVED (distinct from "" = git ran and printed nothing)."""
    import subprocess
    git = resolve_exe("git")
    if not git:
        return None
    try:
        p = subprocess.run([git, "-C", wd, *args], capture_output=True, text=True, timeout=30)
        return p.stdout if p.returncode == 0 else ""
    except Exception:  # noqa: BLE001 -- a capsule never fails for a missing git
        return ""


def write_fault_capsule(rec: dict, wd: str, result_text: str, slim: dict | None) -> str | None:
    """`<state>/fault-capsules/<mission>-e<epoch>.json`, opened "x": existing = already written, never
    rewritten. Read-only git. Returns the path (new or existing), None when it cannot be written."""
    mid, epoch = rec["mission_id"], rec.get("epoch")
    path = lr.state_dir() / "fault-capsules" / f"{mid}-e{epoch}.json"
    text = result_text or ""
    unresolved = _git_ro(wd, "rev-parse", "HEAD") is None
    dirty = [ln for ln in (_git_ro(wd, "status", "--porcelain") or "").splitlines() if ln.strip()]
    if rec.get("created_at"):
        # F4: only this mission's commits, not the branch history (steward helper owns the since-log).
        import mission_steward as _stw
        log = _stw._git_log(wd, float(rec["created_at"]))
    else:
        log = [ln for ln in (_git_ro(wd, "log", "--oneline", "-n", "20") or "").splitlines() if ln.strip()]
    data = {"mission_id": mid, "epoch": epoch, "written_at": time.time(),
            "git": "UNRESOLVED" if unresolved else "ok",
            "head": "UNRESOLVED" if unresolved else (_git_ro(wd, "rev-parse", "HEAD") or "").strip(),
            "commits": log if not unresolved else "UNRESOLVED",
            "dirty": dirty if not unresolved else "UNRESOLVED",
            "diff_stat": "UNRESOLVED" if unresolved else (_git_ro(wd, "diff", "--stat") or ""),
            "gate_lines": [ln for ln in text.splitlines()
                           if re.match(r"^(PASS|FAIL|[A-Z_]+_PASS=)", ln)][-20:],
            "spend": {"slim_tokens": (slim or {}).get("tokens"), "tripped": (slim or {}).get("tripped"),
                      "token_estimate": rec.get("token_estimate")},
            "result": text[:2000],
            "partial_receipt": {"DONE": log, "SALVAGE": dirty}}
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "x", encoding="utf-8") as fh:
            json.dump(data, fh, indent=1)
    except FileExistsError:
        pass
    except OSError:
        return None
    return str(path)


def _receipt_path(pkt, programs_dir=None) -> Path:
    """Where the receipt of the unit that owns `pkt` is. A residual packet (X.md.residual.md) belongs to the unit of X.md:
    the receipt is the chain unit's own (APR-7 A8: the stem rule read 'X.md.residual-receipt.md' and said 'no receipt'
    for a closed receipt, so a duplicate worker ran). No chain unit -> the stem convention on the base packet."""
    pk = str(pkt)
    base = pk[:-len(".residual.md")] if pk.endswith(".residual.md") else pk
    try:
        import gsdx_chain  # noqa: E402 -- same tools dir
        for cp in gsdx_chain.discover_chains(base, programs_dir):
            if isinstance(cp, tuple):
                continue
            u = next((x for x in (gsdx_chain._jload(cp) or {}).get("units", [])
                      if gsdx_chain._norm(x.get("packet", "")) == gsdx_chain._norm(base)), None)
            if u and u.get("receipt"):
                return Path(u["receipt"])
    except Exception:  # noqa: BLE001 -- a chain read must never hide the stem fallback
        pass
    p = Path(base)
    return p.with_name(p.stem + "-receipt.md")


def _receipt_present(rec: dict, programs_dir=None) -> bool:
    pkt = (rec.get("wu_packet") or {}).get("path")
    if not pkt:
        return True   # no packet = nothing to continue
    return _receipt_body_ok(_receipt_path(pkt, programs_dir))


def _receipt_body_ok(path) -> bool:
    """The worker closed the unit with an explicit verdict. A stub, PARTIAL, IN PROGRESS -- or a receipt with NO
    status at all -- is not a close: before APR-1 a Status-less receipt counted as present here while the chain read
    it UNREADABLE, so the mission COMPLETED, halt-continue was skipped and the chain halted (EWC K5)."""
    return rj.is_closed(path)


_TREE_RE = re.compile(r"^work_tree:[ \t]*(\S.*?)[ \t]*$", re.MULTILINE)
_RECEIPT_RE = re.compile(r"^receipt:[ \t]*(\S.*?)[ \t]*$", re.MULTILINE)


def _packet_text(rec: dict) -> str | None:
    pkt = rec.get("wu_packet")
    if not pkt:
        return None
    try:
        return Path(pkt["path"]).read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return None


def _tree_inside_repo(tree: str, base_cwd: str) -> str | None:
    """The packet's `work_tree:` only when it is an absolute directory inside the record's repository."""
    p = Path(tree)
    if not p.is_absolute() or not p.is_dir():
        return None
    p = p.resolve()
    base = Path(base_cwd).resolve()
    if p == base or base in p.parents:
        return str(p)
    here, root = _git_toplevel_and_common(str(p)), _git_toplevel_and_common(str(base))
    return str(p) if here and root and here[1] == root[1] else None


def packet_gate_dir(rec: dict, text: str | None = None) -> tuple[str | None, str]:
    """The tree the packet's work happens in: `work_tree:` line, else the owner's effective workdir, else cwd."""
    text = _packet_text(rec) if text is None else text
    m = _TREE_RE.search(text or "")
    if m:
        t = _tree_inside_repo(m.group(1), rec["cwd"])
        return t, "packet work_tree" if t else f"work_tree {m.group(1)[:200]!r} is not inside the repo"
    return live_root(rec), "worker tree"


def packet_receipt_path(rec: dict) -> str | None:
    """The packet's `receipt:` line resolved to one absolute path inside the work tree, or None."""
    text = _packet_text(rec)
    m = _RECEIPT_RE.search(text) if text else None
    if not m or Path(m.group(1)).is_absolute():
        return None
    tree, _ = packet_gate_dir(rec, text)
    if not tree:
        return None
    root = Path(tree).resolve()
    p = (root / m.group(1)).resolve()
    return str(p) if root in p.parents else None


def spend_goal(rec: dict) -> str | None:
    """The CE goal that pays for this mission. A sweep-armed record carries neither `goal.ce_goal` nor a
    workstream, so the cwd binding in the goal index (the same one the session guard uses) decides."""
    g = rec.get("goal")
    named = (g.get("ce_goal") if isinstance(g, dict) else None) or os.environ.get("CPP_CE_GOAL")
    if named:
        return named
    try:
        import mission_spend as ms
        wd = ms._norm(mb.execution_root(rec))
        hits = [goal for goal, e in ms.read_index().items()
                if any(wd == r or wd.startswith(r + os.sep) for r in (e.get("roots") or []))]
    except Exception:  # noqa: BLE001 -- unmeasurable is None, never a guess
        return None
    return hits[0] if len(hits) == 1 else None


def halt_authority(rec: dict) -> int | None:
    """`remaining` of the mission's CE goal, None when unmeasurable (never renews). The current lease's open holds
    are already inside its `used`; a closed lease's leaked holds are the programme's (executable), not this lease's.
    Subtracting `open` again counted every hold twice (D28 D1d DEFER, V-LIFE-HALT-OPEN-COUNTED-ONCE)."""
    goal = spend_goal(rec)
    if not goal:
        return None
    try:
        import mission_spend as ms
        return int(ms._goal_ledger(goal).status()["remaining"])
    except Exception:  # noqa: BLE001
        return None


def _chain_try_seal(packet: str) -> dict:
    import gsdx_chain  # noqa: E402 -- APR-2's zero-model finalizer, same tools dir
    return gsdx_chain.try_seal(packet)


def _seal_instead_of_renew(rec: dict, row: dict) -> bool:
    """APR-3: an unclosed receipt (not a missing one) is first offered to the zero-model finalizer. A seal costs no
    model call; a worker relaunch costs ~100k+ tokens. Fail-isolated: any error -> renew as before."""
    pkt = (rec.get("wu_packet") or {}).get("path")
    if not pkt:
        return False
    if rj.receipt_status(_receipt_path(pkt)) is None:
        return False
    try:
        res = _chain_try_seal(pkt)
    except Exception as exc:  # noqa: BLE001
        row["seal_attempt"] = f"{type(exc).__name__}: {exc}"[:200]
        return False
    row["seal_attempt"] = res.get("result") or res.get("reason") or ("sealed" if res.get("sealed") else "not sealed")
    if res.get("sealed"):
        row["renewal"] = "not renewed: sealed by finalizer"
        return True
    return False


def halt_continue(rec: dict, wd: str, result_text: str, slim: dict | None, row: dict, now: float) -> None:
    """rec = the mission as it stands after the stop. Fills row['capsule'] / row['renewed_as'] / row['renewal']."""
    if not halt_continue_on():
        row.setdefault("renewal", "not renewed: halt-continue off")
        return
    if not (rec.get("wu_packet") or {}).get("path"):
        row.setdefault("renewal", "not renewed: no work-unit packet")
        return
    if _receipt_present(rec):
        row.setdefault("renewal", "not renewed: receipt present")
        return
    if _seal_instead_of_renew(rec, row):
        return
    try:
        _halt_continue_body(rec, wd, result_text, slim, row, now)
    except Exception as exc:  # noqa: BLE001 -- F5: a non-renewal always leaves its reason on the row
        row.setdefault("renewal", f"not renewed: halt-continue raised {type(exc).__name__}: {exc}"[:600])


def _halt_continue_body(rec: dict, wd: str, result_text: str, slim: dict | None, row: dict, now: float) -> None:
    mid = rec["mission_id"]
    cap = write_fault_capsule(rec, wd, result_text, slim)
    row["capsule"] = cap
    why = None
    if rec.get("owner_hold"):
        why = "owner hold"
    elif any(e.get("event") == "mission_renewed" for e in lr.ledger_events(mid)):
        why = "already renewed"
    elif int(rec.get("renewal") or 0) >= HALT_CONTINUE_MAX_RENEWAL:
        why = "max renewal reached"
    elif not cap:
        why = "no capsule"
    else:
        need = int(rec.get("token_estimate") or 0)
        auth = halt_authority(rec)
        if auth is None:
            why = "authority unmeasurable"
        elif auth < need:
            why = f"authority {auth} < token_estimate {need}"
    if why:
        row["renewal"] = f"not renewed: {why}"
        return
    new_id = renew_mission(rec, now=now, continuity_from={
        "mission_id": mid, "kind": "fault_capsule", "capsule_path": cap})["mission_id"]
    row["renewed_as"] = new_id
    # renew_mission never carries `admission`, and launch refuses a packet unit without one: re-admit
    # against the predecessor's route, or hold with the reason. A successor never waits unexplained.
    route = ((rec.get("admission") or {}).get("route_path"))
    try:
        if not route:
            raise MissionError("predecessor has no admitted route")
        admit_route(new_id, route, now=now)
        refusal = admission_refusal(load(new_id))
        if refusal:
            raise MissionError(refusal)
        row["readmitted"] = True
    except Exception as exc:  # noqa: BLE001
        why = f"halt-continue re-admission failed: {type(exc).__name__}: {exc}"[:900]
        set_owner_hold(new_id, why)
        row["renewal"] = f"renewed but held: {why}"


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
    fp = _seal_refusal_fp(hold.get("fp_dir") or mb.execution_root(rec))
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
    wd = work_dir or mb.execution_root(rec)
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


def _unit_done(rec: dict) -> dict:
    """Run the unit's own done-check: an argv list the arming tool stored on the record (never a shell string).
    rc 0 = DONE, rc 1 = NOT_DONE, anything else (or no answer within 60 s) = UNANSWERED."""
    import subprocess
    argv = rec.get("done_check")
    if not isinstance(argv, list) or not argv or not all(isinstance(a, str) for a in argv):
        return {"outcome": "UNANSWERED", "detail": f"done_check is not an argv list: {argv!r}"[:200]}
    try:
        r = subprocess.run(argv, cwd=rec.get("cwd") or None, capture_output=True, text=True, timeout=60,
                           stdin=subprocess.DEVNULL)
    except Exception as exc:  # noqa: BLE001 -- unanswered, never "done"
        return {"outcome": "UNANSWERED", "detail": f"{type(exc).__name__}: {exc}"[:200]}
    detail = ((r.stdout or "") + (r.stderr or "")).strip()[-200:]
    return {"outcome": {0: "DONE", 1: "NOT_DONE"}.get(r.returncode, "UNANSWERED"), "detail": detail or f"rc {r.returncode}"}


def settle_stopped_worker(rec: dict, settle=None) -> dict:
    """Book a worker the supervisor just stopped: its whole session tree (main + subagents, one message-id
    dedup set) through goal_settle, tagged mission/epoch. Idempotent (a second call books nothing new).
    A mission with no ledger goal, or a settle that fails, is ledgered as `worker_unbooked` -- never silent:
    the 2026-10-14 breaker stop left 25.1M booked as 4.4M short because nothing settled the stopped session."""
    mid, sid = rec["mission_id"], (rec.get("owner") or {}).get("session_id")
    goal = rec.get("ledger_goal")
    why = None
    if not sid:
        why = "owner has no session id"
    elif not goal:
        why = "mission has no ledger_goal (armed outside a declared goal root)"
    out: dict = {}
    if not why:
        try:
            import mission_spend as ms
            out = (settle or ms.goal_settle)(goal, sid, None, f"mission {mid} epoch {rec['epoch']} stopped", tree=True)
            if not out.get("ok"):
                why = str(out.get("reason") or "settle refused")[:200]
        except Exception as exc:  # noqa: BLE001 -- ledgered below, the stop itself must still complete
            why = f"{type(exc).__name__}: {exc}"[:200]
    if why:
        lr.ledger_append(mid, "worker_unbooked", mission_id=mid, worker=sid, goal=goal, why=why)
        return {"booked": False, "why": why}
    lr.ledger_append(mid, "worker_settled", mission_id=mid, worker=sid, goal=goal, epoch=rec["epoch"],
                     closed=out.get("closed"), used=out.get("used"))
    return {"booked": True, "goal": goal, "worker": sid, "closed": out.get("closed")}


def _judge_pre_plan(rec: dict, now: float) -> dict:
    """Everything the supervisor decides about a mission's money before it plans anything, in one fixed order:
    settle a finished phase, give an unbudgeted mission an estimate, judge its phase lease, judge its cost.
    One function for both callers (_breaker_first and the main loop), so the early pass cannot drift from it."""
    mid = rec["mission_id"]
    # M4 A: a finished phase is settled before any lease, breaker or relaunch for the next one.
    try:
        rec = _settle_completed_phase(rec, now)
    except CasConflict:
        raise
    except Exception as exc:  # noqa: BLE001 -- a profile fault must not stop the mission; it is the row
        lr.ledger_append(mid, "unit_settle_failed", mission_id=mid, error=f"{type(exc).__name__}: {exc}"[:300])
    if rec.get("token_estimate") is None and not _blocking_hold(rec):
        rec = _auto_budget(rec, now)
    if rec.get("phase_lease") and not _blocking_hold(rec):
        rec = _phase_breaker(rec, now)
    if (rec.get("token_estimate") or rec.get("authority_tokens")) and not _blocking_hold(rec):
        rec = _cost_breaker(rec, now)
    return rec


def _breaker_first(missions: list[dict], now: float) -> tuple[dict, set]:
    """CCR v5 kernel-u1 task 3. Judge the phase and cost breakers of every live mission BEFORE the host is asked
    for its sessions: `claude agents --json` was measured over 60 s under load, and a 600 s stage timeout on it
    skipped the breakers three times on 2026-10-15 (11:31, 11:47, 12:01 UTC). Each mission runs under its own
    thread timeout (CPP_SWEEP_BREAKER_MISSION_S, default 60), so one slow meter cannot starve the rest.
    Returns (judged records by mission id, ids that timed out). A timed-out mission is skipped for the rest of
    this pass: its thread may still finish and hold it, and a second concurrent judgement could double-hold."""
    try:
        limit = float(os.environ.get("CPP_SWEEP_BREAKER_MISSION_S", "60"))
    except ValueError:
        limit = 60.0
    judged: dict[str, dict] = {}
    timed_out: set[str] = set()
    for rec in missions:
        if rec.get("state") != RUNNING or _blocking_hold(rec) or not _needs_look(rec, now):
            continue
        mid = rec["mission_id"]
        box: dict = {}

        def judge(r=rec, out=box):
            try:
                out["rec"] = _judge_pre_plan(r, now)
            except Exception as exc:  # noqa: BLE001 -- left for the per-mission isolation in the main loop
                out["err"] = f"{type(exc).__name__}: {exc}"

        worker = threading.Thread(target=judge, name=f"breaker-{mid}", daemon=True)
        worker.start()
        worker.join(limit)
        if worker.is_alive():
            timed_out.add(mid)
            try:
                lr.ledger_append(mid, "breaker_timeout", mission_id=mid, limit_s=limit)
            except Exception:  # noqa: BLE001 -- the returned set still carries the skip
                pass
        elif "rec" in box:
            judged[mid] = box["rec"]
    return judged, timed_out


def _supervise_core(now: float | None = None, dry_run: bool = False, sessions=None,
              gsd_status=None, runner=None, stop_runner=None, pid_alive=lr._pid_alive,
              fingerprint=None, capsule_io: dict | None = None) -> list[dict]:
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
                              "action": "none", "reason": f"terminal {m['state']}"} for m in missions] \
            + _steward_rows(missions, now, sessions, pid_alive, dry_run)
    judged, timed_out = ({}, set()) if dry_run else _breaker_first(missions, now)
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
        dead_open = False
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
        try:
            if mid in judged:
                rec = judged[mid]   # settled, budgeted and breaker-judged by _breaker_first, before the host was asked
            elif not dry_run and mid not in timed_out:
                rec = _judge_pre_plan(rec, now)
            if not dry_run and (rec.get("requires") or (rec.get("owner_hold") or {}).get("kind") == "resource"):
                rec = resource_gate(rec, now, sessions, pid_alive)   # M2: no model call; absent field never gets here
            if not dry_run:
                rec = _dead_worker_authority_guard(rec, now, sessions, pid_alive)   # M4 B: CAPITAL_EXHAUSTED, no launch
                dead_open = _dead_worker_open(rec, sessions, pid_alive)
            plan = plan_next(rec, now, sessions, pid_alive, v2=v2)
        except Exception as exc:  # noqa: BLE001 -- isolated per mission, like capsule_v2 above
            # GEX44 2026-10-07/08: a breaker raise here (set_owner_hold on a terminal record) ended EVERY pass
            # for EVERY mission, 264 passes over ~24 h and ~12 more the next day. Nothing is done for this
            # mission this pass; the rest are supervised and the error is ledgered where status reads.
            err = f"pre-plan: {type(exc).__name__}: {exc}"
            out.append({"mission_id": mid, "state": rec["state"], "epoch": rec["epoch"],
                        "action": "none", "reason": err, "error": err})
            try:
                lr.ledger_append(mid, "supervise_error", mission_id=mid, error=err[:300])
            except Exception:  # noqa: BLE001 -- the row still carries the error
                pass
            continue
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
            if (plan["action"] == "none" and rec["state"] == RUNNING and is_cost_hold(rec.get("owner_hold"))
                    and not rec["owner_hold"].get("worker_stopped_at") and cost_hold_stop_enabled()):
                # spec mission-cost-hold-stops-worker. Measured 2026-10-11 (m-560939805e63): held at 74.5M,
                # the busy worker autocompacted on in one turn to 265.5M. The hook asks it to stop; past
                # the grace a LIVE owner is stopped here. Only a LIVE one: UNKNOWN may be anything.
                import gsd_epoch as ge
                over = ge.cost_hold_overdue(rec, now)
                if not over and rec["owner_hold"].get("phase_breaker"):
                    # A phase-lease trip has no grace: the phase's authority is spent, the worker is stopped now.
                    over = {"overdue_s": 0, "grace_s": 0, "phase_breaker": True}
                if over and liveness(rec.get("owner"), sessions, pid_alive)[0] == LIVE:
                    ok, how = stop_owner(rec.get("owner"), sessions, pid_alive=pid_alive, runner=stop_runner)
                    lr.ledger_append(mid, "cost_hold_worker_stopped" if ok else "cost_hold_stop_failed",
                                     mission_id=mid, ok=ok, how=how, overdue_s=over["overdue_s"])
                    row.update({"action": "cost_hold_stop", "reason": f"cost hold enforced: {how}",
                                "cost_hold_enforced": over})
                    if ok:
                        row["settled"] = settle_stopped_worker(rec)
                        transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                                   event="cost_hold_worker_stopped", now=now,
                                   reason=f"cost hold: worker stopped ({how})",
                                   owner_hold={**rec["owner_hold"], "worker_stopped_at": now, "stop": how})
                    continue
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
                halt_wd = live_root(rec)
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
                if (plan["reason"] or "").startswith("slim worker failed") and halt_continue_on():
                    halt_continue(halted, halt_wd, "", None, row, now)
                    continue
                if st is not None:
                    why_not = _renewal_why_not(halted, plan["reason"], st, halt_wd, fingerprint)
                    if why_not:
                        row["renewal"] = f"not renewed: {why_not}"
                    else:
                        row["renewed_as"] = renew_mission(halted, now=now)["mission_id"]
            elif act == "slim_finished":
                s = plan["slim"]
                stopped = s.get("tripped") or ("worker reported is_error" if s["is_error"] else None)
                if not stopped and halt_continue_on() and (rec.get("wu_packet") or {}).get("path") \
                        and not _receipt_present(rec):
                    # F1: a clean finish without its receipt is a fault, not done. Name WHY (APR-1): a receipt that
                    # exists but carries no closing Status is the K5 case, and the renewed worker must be told so.
                    _st = rj.receipt_status(_receipt_path(rec["wu_packet"]["path"]))
                    stopped = "no receipt" if _st is None else f"receipt not closed (status {_st})"
                fin = transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                                 event="slim_worker_finished", now=now, state=HALTED if stopped else COMPLETED,
                                 pending=None, slim_result=s, worker=s.get("session_id"),
                                 reason=f"{plan['reason']}; {stopped}" if stopped else plan["reason"])
                if halt_continue_on() and stopped:
                    halt_continue(fin, mb.execution_root(fin), s.get("result") or "", s, row, now)
            elif act == "settle":
                # Terminal, never relaunched: HALTED keeps owner_hold, so renewal_refusal still refuses it,
                # and leaves goal_conflicts because the state is terminal.
                lrow = plan.get("launched")
                # A never-adopted launch records who ran (spend attribution reads owner.session_id), without
                # adopt_launched's envelope/marker/capsule arming, which only a live worker needs.
                who = {"worker": lrow.get("sessionId"),
                       "owner": {"session_id": lrow.get("sessionId"), "pid": lrow.get("pid"), "proc_start": None,
                                 "heartbeat_at": now, "epoch": rec["epoch"], "kind": "background"}} if lrow else {}
                settled = transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                                     event="hold_settled", now=now, state=HALTED, pending=None,
                                     reason=plan["reason"], **who)
                reap(settled, row)
            elif act == "surface_blocked":
                if rec["state"] != BLOCKED:
                    needs = host_job_needs((rec.get("owner") or {}).get("session_id"))
                    reason = f"{plan['reason']}; host needs: {needs}" if needs else plan["reason"]
                    row["reason"] = reason
                    # A2: the ask is typed, so the consumer reads an intent, not a sentence (2026-10-18: four
                    # blocks asked for a command, a decision or already-supplied files; nothing read them).
                    import blocked_intent as bint
                    bi_ = bint.intent(needs, rec.get("directives"))
                    row["blocked_intent"] = bi_["kind"], bi_["action"]
                    transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                               event="mission_blocked", now=now, state=BLOCKED,
                               reason=reason, blocked_intent=bi_)
                    lr.ledger_append(mid, "blocked_intent", mission_id=mid, epoch=rec["epoch"],
                                     kind=bi_["kind"], action=bi_["action"])
                    if bi_["action"] == "ANSWER_STANDING":
                        # A command ask is the one block answered without the Owner: nobody will type it. The wake
                        # stamps the tree, so a worker that acks and stays silent is judged later (judge_wake).
                        try:
                            import decision_plane as dplane
                            row["standing_answer"] = dplane._wake(
                                mid, bi_["answer"], sessions=sessions, runner=runner, stop_runner=stop_runner,
                                pid_alive=pid_alive, host_fetch=None, now=now)
                        except Exception as exc:  # noqa: BLE001 -- the BLOCKED row stands; the failure is on it
                            row["standing_answer"] = f"{type(exc).__name__}: {exc}"[:200]
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
            elif act == "recover":
                row.update(recover_mission(rec, sessions, now, pid_alive=pid_alive, runner=runner,
                                           stop_runner=stop_runner, gsd_status=gsd_status))
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
                    # Only an explicit policy refuses to follow: following uses Set-Location, not EnterWorktree,
                    # so an unhealthy EnterWorktree (git off PATH) is no reason to strand a worktree's work.
                    if ew and ew != rec["cwd"] and worker_topology(rec).get("policy_forbids"):
                        # AMR-X: a predecessor that wandered into a worktree its repo forbids is not followed;
                        # the successor works where the policy says (the mission's own cwd).
                        lr.ledger_append(mid, "worktree_not_followed", mission_id=mid, epoch=rec["epoch"],
                                         work_dir=ew, why="use_worktrees=false")
                        ew = None
                    if mb.enabled() and ew and mb._norm(ew) == mb._norm(rec["cwd"]):
                        # AMCR: a transcript still in the cwd (the worker moved with Set-Location) proves no move;
                        # the binding, not the launch directory, says where the work is.
                        ew = None
                    work_dir = ew or (mb.execution_root(rec) if mb.binding(rec) else rec.get("work_dir"))
                    # A worktree effective_workdir followed is PROVEN (the predecessor acted on this
                    # workstream there and it carries the roadmap): align_cwd may follow a diverged
                    # cwd then. A recorded work_dir alone proves nothing.
                    if ew and ew != rec["cwd"]:
                        proven_ws = rec.get("workstream")
                    if work_dir:
                        row["work_dir"] = work_dir
                if act in ("relay", "replace") and rec.get("done_check"):
                    # A packet unit is done when ITS packet says so, asked before GSD and before any continuation,
                    # capsule ritual or successor. GSD answers for the whole workstream: EDD P2-B finished in 8 calls,
                    # GSD said "work remains" (phases 2-7), and the successor spent 20 calls / 2,130,930 re-certifying
                    # a finished unit (2026-10-08; REFORECAST UC-19 measured the same tax at 21.5%). Only DONE acts:
                    # NOT_DONE and UNANSWERED keep the existing path, so a broken check can never complete a unit.
                    done = _unit_done(rec)
                    row["unit_done"] = done["outcome"]
                    if done["outcome"] == "DONE":
                        completed = transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                                               event="unit_completed", now=now, state=COMPLETED, pending=None,
                                               reason=f"unit done-check passed: {done['detail']}")
                        reap(completed, row)
                        row["action"] = "completed"
                        continue
                unit_rst = None
                gsd_fact = ""
                pkt = (rec.get("wu_packet") or {}).get("path")
                # An AMR successor's packet is one unit of the mission, not the mission: its receipt is read
                # after GSD (amr_advance below). m-b968b2afdca4 2026-10-17: phase 1 of 4 completed the mission.
                amr_pkt = bool(pkt and (rec.get("amr") or {}).get("packet") == pkt)
                if act in ("relay", "replace") and pkt and not rec.get("done_check") and not amr_pkt:
                    # A packet unit armed without a done_check (every chain-armed unit) is closed by its own receipt,
                    # written after the mission began. Measured 2026-10-14, gsdx-pcc P52a: receipt DONE, worker done, GSD
                    # NO_PHASES on that roadmap, so the record sat BLOCKED 2.5 h and the chain waited on it (wait_writer).
                    rp = _receipt_path(pkt)
                    rst = rj.receipt_status(rp)
                    try:
                        if rst is not None and rp.stat().st_mtime >= float(rec.get("created_at") or 0):
                            unit_rst = rst
                    except OSError:
                        unit_rst = None
                    if unit_rst == "DONE":
                        completed = transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                                               event="unit_completed", now=now, state=COMPLETED, pending=None,
                                               reason=f"unit receipt DONE: {rp}")
                        reap(completed, row)
                        row["action"] = "completed"
                        row["unit_done"] = "RECEIPT_DONE"
                        continue
                if act in ("relay", "replace") and rec["resume_command"].startswith("/gsd-autonomous"):
                    st = (gsd_status or _supervise_gsd_status)(work_dir or mb.execution_root(rec),
                                                       workstream=rec.get("workstream"))
                    row["gsd"] = st.get("outcome")
                    gsd_fact = gsd_fact_line(st)
                    if st.get("outcome") == "ALL_COMPLETE":
                        transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                                   event="mission_completed", now=now, state=COMPLETED,
                                   pending=None, reason=st.get("reason"))
                        continue
                    if st.get("outcome") != "OK":
                        # Positive test: only "work remains" licenses a relay. UNAVAILABLE is
                        # an unanswered question and NO_PHASES a roadmap nobody can run.
                        outcome = st.get("outcome")
                        if outcome == "NO_PHASES" and unit_rst not in (None, "DONE", "UNREADABLE"):
                            # No relay can ever run this roadmap, and the unit's own receipt says it stopped short
                            # (gsdx-pcc P52b, 2026-10-14: PARTIAL, held 2.5 h). Halt it so the owner of the
                            # continuation (the chain's residual, or a person) sees a terminal record.
                            halted = transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                                                event="unit_receipt_open", now=now, state=HALTED, pending=None,
                                                reason=f"unit receipt {unit_rst}; gsd NO_PHASES: no relay can run it")
                            reap(halted, row)
                            row["action"] = "halted"
                            continue
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
                if (act in ("relay", "replace") and rec.get("amr") and rec.get("wu_packet")
                        and _receipt_present(rec)):
                    # AMR: the successor closed its unit and GSD says work remains. The next unit keeps the
                    # deflated topology and the fence; a fresh packet, lease and admission replace the old.
                    rec, advanced = amr_advance(rec, now)
                    row["amr_unit"] = (rec.get("amr") or {}).get("unit")
                    if not advanced:
                        row["held"] = "AMR: next unit not compiled; parked at an Owner boundary"
                        continue
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
                    # CCR A4: the break-even rule's shadow verdict beside the ceiling's decision (observe only).
                    sb = (turn_end.get("evidence") or {}).get("shadow_breakeven")
                    if sb:
                        row["turn_end"]["shadow_breakeven"] = sb
                    if turn_end["decision"] == ge.HOLD:
                        lr.ledger_append(mid, "relay_held", mission_id=mid, epoch=rec["epoch"],
                                         reason=turn_end["reason"])
                        row["held"] = turn_end["reason"]
                        continue
                fp_fn = fingerprint or progress_fingerprint
                progress = next_progress(rec, mission_fingerprint(rec, work_dir or mb.execution_root(rec),
                                                                  fp_fn),
                                         ran=rec["state"] != LAUNCHING)
                row["progress"] = progress
                if (turn_end is not None and turn_end["decision"] == ge.CONTINUE and progress.get("measured")
                        and progress["stalls"] >= 1 and ge.stalled_fresh_enabled()):
                    # m-b8541432cbf9: a resumed session keeps the belief that made it stop; three resumes of it
                    # answered "nothing to run" and the mission halted no_progress. A continuation that moved
                    # nothing is followed by a fresh worker, which reads the card and GSD's answer.
                    turn_end = {**turn_end, "decision": ge.ROTATE, "mechanism": ge.FRESH,
                                "reason": f"the last continuation changed nothing (stalls {progress['stalls']}): "
                                          f"fresh worker -- {turn_end['reason']}",
                                "evidence": {**(turn_end.get("evidence") or {}), "trigger": "stalled_continuation"}}
                    row["turn_end"] = {k: turn_end.get(k) for k in ("decision", "cause", "reason")}
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
                        mid, rec, prompt=launch_prompt(rec) + gsd_fact,
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
                elif aligned["status"] in ("diverged_followed", "behind_followed"):
                    lr.ledger_append(mid, f"cwd_{aligned['status']}", mission_id=mid, epoch=rec["epoch"],
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
                    if plan.get("decision"):
                        # AMR-X: the predecessor's open question is answered here, by the runtime, with the
                        # gate's provenance -- the successor must not ask it again.
                        d = plan["decision"]
                        answer = (f"RUNTIME ANSWER to the predecessor's question ({d['gate']['result']}): "
                                  f"{d['gate']['resolution']}\nThe question was: {d['why']}\n"
                                  f"Do not end a turn on a question the repo policy or your own recommended option "
                                  f"answers; Owner-only classes: deploy/push/live write, credentials, external "
                                  f"properties, irreversible actions, product scope, authority.")
                        note = f"{answer}\n\n{note}"
                        # Persisted with the counter (review F2): the predecessor's job file is overwritten by its
                        # stop, so a launch that fails after this point would otherwise lose the answer for good.
                        # launch_worker re-injects it on every retry; adoption clears it.
                        rec = transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                                         event="decision_recovered", now=now, pending_decision=answer,
                                         decision_recoveries=int(rec.get("decision_recoveries") or 0) + 1,
                                         ledger_extra={"gate": d["gate"]["result"], "question": d["why"][:200]})
                        row["decision_recovery"] = d["gate"]["result"]
                    row["note_chars"] = len(note)
                if (v2 and rec.get("capsule_key") and act in ("relay", "replace", "launch")
                        and not _capsule_arm(rec, row)):
                    # spec 3.3: no marker, no spawn. `launch` too (spec 11.1): a renewal that carries a
                    # capsule starts its first worker as that capsule's successor.
                    continue
                if act in ("relay", "replace", "launch"):
                    ra_res = readmit_for_relay(rec, now=now)
                    if ra_res["readmitted"]:
                        rec = ra_res["rec"]
                        row["readmitted"] = True
                row["launch"] = launch_worker(mid, expect_epoch=rec["epoch"],
                                              expect_state=rec["state"], reason=plan["reason"],
                                              runner=runner, now=now, note=note,
                                              work_dir=work_dir, progress=progress, packet=packet,
                                              gsd_fact=gsd_fact)
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
        finally:
            if dead_open:
                # M4 B: a dead worker with no hold was planned for the ordinary launch; if it did not happen, say why.
                try:
                    _dead_worker_visibility(mid, row)
                except Exception:  # noqa: BLE001 -- visibility must never fail the pass
                    pass
    return unreadable + out + _steward_rows(missions, now, sessions, pid_alive, dry_run)


def _steward_rows(missions, now, sessions, pid_alive, dry_run) -> list[dict]:
    """The mission steward (tools/mission_steward.py), isolated: any failure is ONE row, never a failed sweep."""
    if dry_run:
        return []
    try:
        import mission_steward
        if sessions is None and any(m["state"] in (HALTED, BLOCKED) and m.get("wu_packet") and m.get("goal")
                                    and not (m.get("steward") or {}).get("done") for m in missions):
            sessions = host_sessions()     # a stopped worker is judged against the host, not guessed
        return mission_steward.steward_pass(missions, now, sessions=sessions, pid_alive=pid_alive)
    except Exception as exc:  # noqa: BLE001
        return [{"action": "steward_error", "error": f"{type(exc).__name__}: {exc}"[:300]}]

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


def worker_arm_refusal(sid: str | None) -> str | None:
    """A mission worker must not launch another mission (A4-P5). Any state: a worker can outlive its done."""
    if not sid or os.environ.get("CPP_ARM_WORKER_GUARD", "").strip().lower() == "off":
        return None
    for r in all_missions():
        if (r.get("owner") or {}).get("session_id") == sid:
            return (f"worker_arm_launch_refused: session {sid[:8]} is the worker of "
                    f"{r.get('mission_id')} ({r.get('state')}); a worker arms only with --no-launch")
    return None


def planning_admission(resume_command: str, cwd: str, unit_path: str | None, override: str | None) -> dict:
    """Planning Necessity at arm time (tools/planning_gate.py). A `/gsd-*` command runs plan-phase (planner,
    checker, replanner); measured 2026-10-16 (m-f9290d78278f) that loop spent 29.9M on a work class with three
    executed precedents. When the unit's gate answers DIRECT_TEMPLATE or DELTA_PLAN, a `/gsd-*` arm is refused
    unless `override` states why. No unit = UNASSESSED: reported, never read as admitted-by-gate."""
    if not unit_path:
        return {"admitted": True, "gate": "UNASSESSED"}
    import planning_gate as pg
    d = pg.decide(json.loads(Path(unit_path).read_text(encoding="utf-8")), Path(cwd))
    planning_route = resume_command.lstrip().startswith("/gsd-")
    if planning_route and d["mode"] in ("DIRECT_TEMPLATE", "DELTA_PLAN") and not (override or "").strip():
        return {"admitted": False, "gate": d["mode"], "decision": d,
                "reason": f"planning gate {d['mode']} ({d['why']}): arm the compiled unit (--wu-packet / a "
                          f"non-/gsd- command), or pass --planning-override with the reason"}
    return {"admitted": True, "gate": d["mode"], "decision": d, "override": (override or None)}


def arm(cwd: str, resume_command: str, *, launch: bool = True, supersedes: str | None = None,
        authority: str | None = None, parallel_unit: str | None = None, **kw) -> dict:
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
    if launch:
        why = worker_arm_refusal(os.environ.get("CLAUDE_CODE_SESSION_ID"))
        if why:
            lr.ledger_append("arm-guard", "worker_arm_refused", why=why[:300])
            raise MissionError(why)
    rec = create(cwd, resume_command, **kw)
    extra = {}
    try:   # plain arm under a declared goal root binds to that goal's ledger: no new capital per mission id
        import mission_spend as _ms
        lg = _ms.goal_for_cwd(cwd)
        if lg:
            extra["ledger_goal"] = lg
    except Exception:  # noqa: BLE001 -- unbound is reported by programme-spend, never fatal at arm
        pass
    if key is not None:
        extra["goal"] = {"repo": key[0], "workstream": key[1], "unit": parallel_unit}
    if supersedes:
        extra.update(supersedes=supersedes, authority=authority.strip()[:1000])
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
                        reason="armed", progress=next_progress(rec, mission_fingerprint(rec, rec["cwd"])))
    if res.get("ok"):
        import gsd_epoch as ge
        ge.record_cause(rec["mission_id"], {"epoch": res["epoch"]},
                        {"cause": ge.INITIAL, "reason": "armed"}, ge.FRESH)
    return {"mission": load(rec["mission_id"]), "launch": res}


def arm_chain(cwd: str, resume_command: str, *, wu_packet: str, token_estimate, route: str,
              floors_path: str | None = None, **kw) -> dict:
    """Atomic arm (WU-1H addendum C): arm --no-launch, envelope, admit. Any failure holds the armed
    mission with the reason; a mission is never launched here, and never without a packet."""
    kw.pop("launch", None)
    # The worker model rides the same atomic step: without it the launch inherits the host default (Opus
    # here), and a chain armed unattended has no later moment to set it before the sweep launches.
    model = kw.pop("model", None)
    rec = arm(cwd, resume_command, launch=False, **kw)["mission"]
    mid = rec["mission_id"]
    try:
        set_envelope(mid, wu_packet=wu_packet, token_estimate=token_estimate, model=model)
        adm = admit_route(mid, route, floors_path=floors_path)["admission"]
        if adm["verdict"] != "ADMISSIBLE":
            raise MissionError(f"route {adm['verdict']}: {'; '.join(adm.get('reasons') or [])}"[:600])
    except Exception as exc:  # noqa: BLE001 -- hold with the reason, then report
        why = f"arm-chain failed: {type(exc).__name__}: {exc}"[:900]
        set_owner_hold(mid, why)
        return {"ok": False, "mission_id": mid, "held": True, "why": why}
    return {"ok": True, "mission_id": mid, "mission": load(mid)}



# --------------------------------------------------------------------------- advance (WU-ADV2b)
# Approval record -> goal authority -> armed next unit, by the sweep. CPP_SWEEP_ADVANCE=off disables.
def advance_on() -> bool:
    return (os.environ.get("CPP_SWEEP_ADVANCE") or "").strip().lower() != "off"


def parse_plan(path) -> dict:
    """Front matter of an approved plan: status, units (ordered), packet_dir."""
    text = Path(path).read_text(encoding="utf-8-sig")
    m = re.match(r"\A---\s*\r?\n(.*?)\r?\n---", text, re.S)
    if not m:
        raise MissionError(f"plan {path} has no front matter")
    fm = {}
    for ln in m.group(1).splitlines():
        k, sep, v = ln.partition(":")
        if sep:
            fm[k.strip()] = v.strip()
    units = [u.strip() for u in re.sub(r"[\[\]]", "", fm.get("units", "")).split(",") if u.strip()]
    return {"status": fm.get("status", ""), "units": units, "packet_dir": fm.get("packet_dir", "")}


def receipt_complete(path) -> bool:
    """Status: DONE and not a stub/partial/in-progress receipt (the same rule as _receipt_present)."""
    return rj.is_done(path)


def goal_headroom(goal) -> int | None:
    """remaining - open of an EXISTING capped goal ledger; None when unmeasurable (never creates one)."""
    if not goal:
        return None
    try:
        import mission_spend as ms
        if not (ms.goal_root() / goal).exists():
            return None
        st = ms._goal_ledger(goal).status()
        if st.get("remaining") is None:
            return None
        return int(st["remaining"]) - int(st.get("open") or 0)
    except Exception:  # noqa: BLE001
        return None


def _adv_status(plan_path: Path, status: str, why: str) -> None:
    sp = plan_path.with_name(plan_path.name + ".status")
    sp.write_text(f"{status}\n{why}\n", encoding="utf-8")


def apply_approval(rec: dict, ledger=None) -> dict:
    """cap_delta once, through the consume-once declare_cap (approval_id names the source)."""
    delta = int(rec.get("cap_delta") or 0)
    if delta <= 0:
        return {"applied": False, "why": "no cap_delta"}
    if ledger is None:
        import mission_spend as ms
        ledger = ms._goal_ledger(rec["goal"])
    cur = ledger.status().get("cap")
    if cur is None:
        return {"applied": False, "why": "goal has no cap"}
    res = ledger.declare_cap(int(cur) + delta, f"approval {rec['approval_id']}", approval_id=rec["approval_id"])
    return {"applied": bool(res.get("ok")) and "already consumed" not in str(res.get("reason", "")),
            "why": res.get("reason", ""), "cap": res.get("cap")}


def advance_unit(rec: dict, plan: dict, unit: str, repo: Path, *, arm_fn=None, headroom=None) -> dict:
    goal = rec["goal"]
    if unit not in plan["units"]:
        return {"status": "NOT_LISTED", "why": f"{unit} is not in the plan's units"}
    i = plan["units"].index(unit)
    pdir = repo / plan["packet_dir"]
    if i > 0 and not receipt_complete(pdir / f"{plan['units'][i - 1]}-receipt.md"):
        return {"status": "WAITING_FOR_RECEIPT", "why": f"predecessor {plan['units'][i - 1]} has no complete receipt"}
    own = pdir / f"{unit}-receipt.md"
    if own.exists() and not receipt_complete(own):
        return {"status": "WAITING_FOR_RECEIPT", "why": f"{unit} has a stub/partial receipt; a worker owns it"}
    packet, route = pdir / f"{unit}.md", pdir / f"route-{unit}.json"
    if not packet.exists() or not route.exists():
        return {"status": "WAITING_FOR_PACKET", "why": f"{packet.name} or {route.name} missing"}
    try:
        est = int(json.loads(route.read_text(encoding="utf-8-sig"))["envelope"]["target"])
    except Exception as exc:  # noqa: BLE001
        return {"status": "WAITING_FOR_PACKET", "why": f"route has no envelope target ({type(exc).__name__})"}
    room = (headroom or goal_headroom)(goal)
    if room is None or room < est:
        return {"status": "WAITING_FOR_AUTHORITY", "why": f"goal {goal} headroom {room} < estimate {est}"}
    import hashlib
    key = hashlib.sha256(f"{rec['plan_path']}|{unit}".encode()).hexdigest()[:24]
    kp = lr.state_dir() / "advance" / "keys" / f"{key}.json"
    kp.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(kp, "x", encoding="utf-8") as fh:   # persisted BEFORE the arm: a second pass is a no-op
            json.dump({"goal": goal, "unit": unit, "at": time.time()}, fh)
    except FileExistsError:
        return {"status": "ALREADY_ARMED", "why": f"singleflight key {key} present"}
    # The goal is not passed: it resolves from the cwd binding (_mission_goal), as for a hand-armed unit.
    try:
        res = (arm_fn or arm_chain)(str(repo), "/gsd-autonomous", wu_packet=str(packet), token_estimate=est,
                                    route=str(route), parallel_unit=f"lc-{unit}", max_cycles=3,
                                    rollover_protocol=CAPSULE_V2, permission_mode="auto")  # = the CLI default
    except Exception as exc:  # noqa: BLE001 -- no mission was armed, so the key must not claim one
        kp.unlink(missing_ok=True)
        return {"status": "ARM_FAILED", "why": f"{type(exc).__name__}: {exc}"[:300], "mission_id": None}
    # A held arm keeps its key: that mission exists and is the Owner's to release, never armed a second time.
    return {"status": "ARMED" if res.get("ok") else "ARM_FAILED", "why": res.get("why") or "",
            "mission_id": res.get("mission_id"), "key": key}


def advance_pass(*, arm_fn=None, headroom=None, ledger_for=None) -> list[dict]:
    rows = []
    adir = lr.state_dir() / "approvals"
    if not advance_on() or not adir.is_dir():
        return rows
    for ap in sorted(adir.glob("*.json")):
        try:
            rec = json.loads(ap.read_text(encoding="utf-8-sig"))
            repo = Path(rec.get("repo") or ".")
            plan_path = Path(rec["plan_path"])
            if not plan_path.is_absolute():
                plan_path = repo / plan_path
            plan = parse_plan(plan_path)
            if not plan["status"].upper().startswith("APPROVED"):
                row = {"unit": None, "status": "WAITING_FOR_AUTHORITY", "why": f"plan status {plan['status']!r}"}
            else:
                if rec.get("cap_delta"):
                    apply_approval(rec, ledger_for(rec["goal"]) if ledger_for else None)
                pdir = repo / plan["packet_dir"]
                row = {"unit": None, "status": "PLAN_COMPLETE", "why": "every unit has a receipt"}
                for u in plan["units"]:
                    if not receipt_complete(pdir / f"{u}-receipt.md"):
                        row = {"unit": u, **advance_unit(rec, plan, u, repo, arm_fn=arm_fn, headroom=headroom)}
                        break
                if row["status"] in ("WAITING_FOR_AUTHORITY", "WAITING_FOR_PACKET"):
                    _adv_status(plan_path, row["status"], row["why"])
            rows.append({"mission_id": f"advance:{ap.stem}", "action": "advance", **row})
        except Exception as exc:  # noqa: BLE001 -- one bad record never stops the pass
            rows.append({"mission_id": f"advance:{ap.stem}", "action": "advance", "status": "ERROR",
                         "error": f"{type(exc).__name__}: {exc}"[:300]})
    return rows


def _packet_states() -> dict:
    return {m["mission_id"]: (m["state"], (m["wu_packet"] or {}).get("path")) for m in _scan()[0] if m.get("wu_packet")}


def event_chain_ticks(before: dict, after: dict, ticker=None) -> list[dict]:
    """APR-3: a packet mission that became COMPLETED/HALTED in this pass ticks its owning chain(s) at once.
    Fail-isolated (an exception is a row), once per packet, off with CPP_GSDX_CHAIN_EVENT=off."""
    if os.environ.get("CPP_GSDX_CHAIN_EVENT", "").lower() == "off":
        return []
    rows, seen = [], set()
    for mid, (st, pkt) in after.items():
        if st not in (COMPLETED, HALTED) or not pkt or pkt in seen or (before.get(mid) or (None,))[0] == st:
            continue
        seen.add(pkt)
        try:
            if ticker is None:
                import gsdx_chain  # noqa: E402
                ticker = gsdx_chain.tick_for_packet
            for r in ticker(pkt):
                rows.append({"mission_id": mid, "action": "chain_event", "status": r.get("action"), **{
                    k: r[k] for k in ("unit", "trigger", "chain", "error") if k in r}})
        except Exception as exc:  # noqa: BLE001
            rows.append({"mission_id": mid, "action": "chain_event", "status": "ERROR",
                         "error": f"{type(exc).__name__}: {exc}"[:300]})
    return rows


def supervise(*args, **kw) -> list[dict]:
    dry = kw.get("dry_run", args[1] if len(args) > 1 else False)
    try:
        before = {} if dry else _packet_states()
    except Exception:  # noqa: BLE001
        before = None
    rows = _supervise_core(*args, **kw)
    if not dry:
        try:
            rows = rows + advance_pass()
        except Exception as exc:  # noqa: BLE001
            rows = rows + [{"mission_id": "advance", "action": "advance", "status": "ERROR",
                            "error": f"{type(exc).__name__}: {exc}"[:300]}]
        if before is not None:
            try:
                rows = rows + event_chain_ticks(before, _packet_states())
            except Exception as exc:  # noqa: BLE001
                rows = rows + [{"mission_id": "chain_event", "action": "chain_event", "status": "ERROR",
                                "error": f"{type(exc).__name__}: {exc}"[:300]}]
    return rows


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
    g = resolve_exe("git") or "git"
    parts = []
    try:
        # HEAD's TREE, not its commit (AMCR anti-gaming): an empty or amend-only commit changes no content.
        for args in (["rev-parse", "HEAD^{tree}"], ["status", "--porcelain"], ["diff", "HEAD", "--shortstat"]):
            r = subprocess.run([g, "-C", work_dir, *args], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=30)
            if r.returncode != 0:
                return None
            parts.append(r.stdout)
    except Exception:  # noqa: BLE001 -- unmeasured is its own answer
        return None
    planning = _planning_artifacts(work_dir)
    if planning:
        parts.append(planning)
    return hashlib.sha256("\x00".join(parts).encode("utf-8")).hexdigest()[:16]


def _planning_artifacts(work_dir: str) -> str:
    """Names and sizes of GSD artifacts under `.planning/`, STATE.md excluded.

    Measured 2026-10-15 (m-07a78fbae3c7, GEX44 dws-exec/rb): `.planning/` was git-excluded so the
    product branch stays clean, phase 1 wrote only there, and the cost breaker held a working mission
    at 5.36M "since the work tree last changed". git cannot see an excluded dir, and porcelain folds an
    untracked one to a single line. STATE.md is left out because a worker rewrites it every turn: a
    looping worker must still read as stalled. Empty when there is no `.planning/`."""
    root = Path(work_dir) / ".planning"
    if not root.is_dir():
        return ""
    rows = []
    try:
        for dirpath, _dirs, files in os.walk(root):
            for name in files:
                if name == "STATE.md":
                    continue
                p = Path(dirpath) / name
                rows.append(f"{p.relative_to(root).as_posix()}:{p.stat().st_size}")
    except OSError:
        return ""
    return "\n".join(sorted(rows))


def mission_fingerprint(rec: dict, base_dir: str, fp_fn=None) -> str | None:
    """progress_fingerprint over every tree the worker may write: base_dir plus the mission's
    `add_dirs`. Measured 2026-10-11 (m-4a0f39b59a60, cwd InfinityOps, --add-dir io-sidecar-fbig):
    22 commits landed in the add-dir while the cwd fingerprint never moved, so the stall breaker
    read "151M processed since the work tree last changed". No add_dirs -> the base fingerprint,
    unchanged. Every tree unmeasured -> None (unmeasured, never "no change")."""
    fp_fn = fp_fn or progress_fingerprint
    extra = [d for d in (rec.get("add_dirs") or []) if d and d != base_dir]
    if not extra:
        return fp_fn(base_dir)
    import hashlib
    fps = [fp_fn(base_dir)] + [fp_fn(d) for d in extra]
    if all(f is None for f in fps):
        return None
    return hashlib.sha256("|".join(f or "?" for f in fps).encode("utf-8")).hexdigest()[:16]


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
    g = resolve_exe("git") or "git"
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
    write_worker_index(rec, session_id)
    if first:
        try:
            _arm_worker_marker(rec, session_id)
        except Exception as exc:  # noqa: BLE001 -- recorded; the worker index still reaches the hooks
            # Measured 2026-10-11 (m-560939805e63, m-4a0f39b59a60): a resume command over the marker's
            # 200-char typing limit raised MarkerError here, no marker was written, and mission_wall.js --
            # keyed on the marker -- never judged that worker: no wall, no cost-hold notice, 191M spent
            # after the breaker tripped. Nothing recorded the refusal.
            lr.ledger_append(session_id, "worker_marker_refused", mission_id=rec["mission_id"],
                             epoch=rec["epoch"], error=f"{type(exc).__name__}: {exc}"[:300])
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


WORKER_INDEX_TEMPLATE = "mission-worker-{session_id}.json"


def write_worker_index(rec: dict, session_id: str) -> Path | None:
    """spec mission-cost-hold-stops-worker: name this session's mission for the mid-turn hooks
    (mission_wall.js) independently of the v2 typing marker, which refuses a resume command it could
    not type. Carries only identity and wall -- no command, so nothing can ever type it. Fail-open:
    a write failure is a ledger row, never a broken SessionStart."""
    try:
        d = lr.state_dir() if not os.environ.get("GSD_AUTORUN_MARKER_DIR") else Path(os.environ["GSD_AUTORUN_MARKER_DIR"])
        p = d / WORKER_INDEX_TEMPLATE.format(session_id=session_id)
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps({"session_id": session_id, "mission_id": rec["mission_id"],
                                   "epoch": rec["epoch"], "wall": rec.get("wall") or dict(DEFAULT_WALL)}),
                       encoding="utf-8")
        tmp.replace(p)
        return p
    except Exception as exc:  # noqa: BLE001 -- recorded, never silent
        lr.ledger_append(session_id, "worker_index_unwritten", mission_id=rec.get("mission_id"),
                         error=f"{type(exc).__name__}: {exc}"[:300])
        return None


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
    a.add_argument("--work-unit", help="unit JSON for tools/planning_gate.py; a DIRECT/DELTA verdict refuses a "
                                       "/gsd-* (full planning) command")
    a.add_argument("--planning-override", help="why full planning is needed despite the gate")
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
    a.add_argument("--authority", help="who decided the supersession and where it is recorded")
    a.add_argument("--parallel-unit", help="a named work unit that may run beside other named units "
                                           "of the same goal")
    ac = sub.add_parser("arm-chain", help="atomic arm: --no-launch + envelope + admit; hold on any failure")
    ac.add_argument("--cwd", required=True)
    ac.add_argument("--command", required=True)
    ac.add_argument("--wu-packet", required=True)
    ac.add_argument("--token-estimate", required=True)
    ac.add_argument("--route", required=True)
    ac.add_argument("--floors")
    ac.add_argument("--workstream")
    ac.add_argument("--max-cycles", type=int)
    ac.add_argument("--permission-mode", default="auto")
    ac.add_argument("--rollover-protocol", choices=(CAPSULE_V2,), default=None)
    ac.add_argument("--parallel-unit")
    ac.add_argument("--model", help="worker model set in the atomic envelope step (else the host default)")
    ac.add_argument("--supersedes", help="the live attempt of this goal this one replaces (e.g. a failed-arm "
                                         "stub); needs --authority")
    ac.add_argument("--authority", help="who decided the supersession and where it is recorded")
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
    dc = sub.add_parser("decide", help="record an Owner decision as durable mission state and resume a blocked "
                                       "background owner with it")
    dc.add_argument("--mission", required=True)
    dc.add_argument("--text", required=True)
    dc.add_argument("--id", default=None, help="decision id (default D<n>)")
    dc.add_argument("--supersedes", default=None, help="id of an earlier decision this one replaces")
    dc.add_argument("--no-wake", action="store_true", help="record only; do not stop and resume the owner")
    oh = sub.add_parser("hold", help="park a live mission: no launch, halt or renewal (spec mission-owner-hold)")
    oh.add_argument("--mission", required=True)
    oh.add_argument("--reason", required=True)
    oh.add_argument("--stop", action="store_true",
                    help="also stop the live background worker through the host (claude stop + wait); "
                         "never kill the pid by hand: the daemon resumes a killed session")
    orl = sub.add_parser("release", help="lift an owner hold; the budget clock is not reset")
    orl.add_argument("--mission", required=True)
    rq = sub.add_parser("requires", help="M2: typed resource requirements for ONE obligation; the sweep parks the "
                                         "mission as WAIT_RESOURCE until they are met (no model call)")
    rq.add_argument("--mission", required=True)
    rq.add_argument("--obligation", help="the obligation these requirements gate, e.g. O-70")
    rq.add_argument("--ram-free-gb", type=float, default=None)
    rq.add_argument("--path", default=None, help="a path that must exist, e.g. R:\\hwf")
    rq.add_argument("--no-process", default=None, help="an image name that must not be running, e.g. electron")
    rq.add_argument("--clear", metavar="OBLIGATION", default=None, help="remove that obligation's requirements")
    bd = sub.add_parser("bind", help="AMCR: bind the mission to the git worktree its worker now writes "
                                     "(every observer follows it)")
    bd.add_argument("--mission", required=True)
    bd.add_argument("--path", required=True)
    bd.add_argument("--cause", default="explicit")
    ob = sub.add_parser("obligation", help="AMCR: set a durable child obligation's state")
    ob.add_argument("--mission", required=True)
    ob.add_argument("--id", required=True)
    ob.add_argument("--state", required=True)
    tp = sub.add_parser("topology", help="AMCR: the mission's execution topology receipt (JSON)")
    tp.add_argument("--mission", required=True)
    au = sub.add_parser("authority", help="record Owner programme authority: token ceiling AMR leases inside, "
                                          "and/or extra wall hours")
    au.add_argument("--mission", required=True)
    au.add_argument("--tokens", help="processed-token ceiling for the whole mission, e.g. 66M")
    au.add_argument("--extend-hours", type=float)
    au.add_argument("--reason", default="", help="the Owner act this records")
    pr = sub.add_parser("protocol", help="set the rollover protocol on an existing mission "
                                         "(held or owner-less only; same permission-mode rule as arm)")
    pr.add_argument("--mission", required=True)
    pr.add_argument("--rollover-protocol", required=True,
                    help=f"only {CAPSULE_V2}; anything else is refused")
    en = sub.add_parser("envelope", help="set token estimate / model / autocompact / compiled work-unit "
                                         "packet on a live mission (spec mission-envelope-and-compiled-wu)")
    en.add_argument("--mission", required=True)
    en.add_argument("--token-estimate", help="processed tokens the cost breaker judges, e.g. 16M")
    en.add_argument("--estimate-basis", help="why an estimate below half the lineage's measured cost is right "
                                             "(spec mission-cost-hold-stops-worker)")
    en.add_argument("--model", help="worker model: sonnet, opus, haiku, fable or a claude- model id")
    en.add_argument("--autocompact", help="worker autocompact window, e.g. 300k")
    en.add_argument("--wu-packet", help="compiled work-unit file sent instead of the resume command")
    en.add_argument("--continue-max-tokens",
                    help="per-mission context ceiling for continuing the same session, e.g. 200k")
    en.add_argument("--ccr-class", help="CCR work class; admit then records the PGO cost contract "
                                        "(CPP_CCR_ADMISSION=enforce makes SPLIT/DEFLATE refuse)")
    en.add_argument("--phase-lease", help="GSD phase number to lease (needs --phase-forecast and --phase-state); "
                                          "the base is measured now, at the phase start")
    en.add_argument("--phase-forecast", help="the phase's token forecast, e.g. 4.5M; warn 1.2x, hard 1.5x")
    en.add_argument("--phase-state", help="the workstream STATE.md the current GSD phase is read from")
    en.add_argument("--worker-mcp", choices=WORKER_MCP_MODES,
                    help="none = launch this mission's worker with --strict-mcp-config and no servers")
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
        adm = planning_admission(args.command, args.cwd, args.work_unit, args.planning_override)
        if not adm["admitted"]:
            print(f"REFUSED: {adm['reason']}")
            return 4
        res = arm(args.cwd, args.command, launch=not args.no_launch, workstream=args.workstream,
                  max_cycles=args.max_cycles, max_hours=args.max_hours,
                  permission_mode=args.permission_mode, allowed_tools=args.allowed_tools,
                  add_dirs=args.add_dir, wall=wall, rollover_protocol=args.rollover_protocol,
                  supersedes=args.supersedes, authority=args.authority, parallel_unit=args.parallel_unit)
        mid = (res.get("mission") or res).get("mission_id")
        if mid:
            lr.ledger_append(mid, "planning_gate", mission_id=mid, gate=adm["gate"], override=adm.get("override"),
                             why=(adm.get("decision") or {}).get("why"))
        res["planning_gate"] = adm["gate"]
        print(json.dumps(res, indent=2))
        return 0 if args.no_launch or res.get("launch", {}).get("ok") else 1
    if args.cmd == "arm-chain":
        res = arm_chain(args.cwd, args.command, wu_packet=args.wu_packet, token_estimate=args.token_estimate,
                        route=args.route, floors_path=args.floors, workstream=args.workstream,
                        max_cycles=args.max_cycles, permission_mode=args.permission_mode,
                        rollover_protocol=args.rollover_protocol, parallel_unit=args.parallel_unit,
                        model=args.model, supersedes=args.supersedes, authority=args.authority)
        print(json.dumps({k: v for k, v in res.items() if k != "mission"}, indent=2))
        return 0 if res["ok"] else 1
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
    if args.cmd == "decide":
        out = deliver_decision(args.mission, args.text, decision_id=args.id, supersedes=args.supersedes,
                               wake=not args.no_wake)
        w = out["woke"]
        print(f"DECISION {'RECORDED' if out['recorded'] else 'UNCHANGED'} mission={args.mission} "
              f"id={out['decision']['id']} woke={bool(w.get('ok'))} why={w.get('why', 'resumed')}")
        return 0
    if args.cmd == "hold" and args.stop:
        out = owner_pause(args.mission, args.reason)
        rec = out["record"]
        print(f"OWNER PAUSE {'STOPPED' if out['ok'] else 'HELD, STOP FAILED'} mission={rec['mission_id']} "
              f"state={rec['state']} epoch={rec['epoch']} stop={out['how']}")
        return 0 if out["ok"] else 1
    if args.cmd == "hold":
        rec = set_owner_hold(args.mission, args.reason)
        print(f"OWNER HOLD SET mission={rec['mission_id']} state={rec['state']} epoch={rec['epoch']}")
        return 0
    if args.cmd == "requires":
        if args.clear:
            rec = set_requires(args.mission, args.clear, clear=True)
            print(f"REQUIRES CLEARED mission={rec['mission_id']} obligation={args.clear} left={len(rec['requires'])}")
            return 0
        if not args.obligation:
            raise MissionError("--obligation is required (or --clear <obligation>)")
        specs = [(k, v) for k, v in (("ram_free_gb", args.ram_free_gb), ("path_exists", args.path),
                                     ("no_process", args.no_process)) if v is not None]
        rec = set_requires(args.mission, args.obligation, specs)
        print(f"REQUIRES SET mission={rec['mission_id']} obligation={args.obligation} total={len(rec['requires'])}")
        return 0
    if args.cmd == "authority":
        rec = set_authority(args.mission, args.tokens, args.extend_hours, reason=args.reason)
        print(f"AUTHORITY SET mission={rec['mission_id']} authority_tokens={rec.get('authority_tokens')} "
              f"max_hours={rec.get('max_hours')}")
        return 0
    if args.cmd == "bind":
        rec = bind_mission(args.mission, args.path, args.cause)
        b = rec["binding"]
        print(f"BOUND mission={rec['mission_id']} gen={b['gen']} root={b['root']} branch={b['branch']} head={b['head']}")
        return 0
    if args.cmd == "obligation":
        rec = set_obligation(args.mission, args.id, args.state)
        print(f"OBLIGATION SET mission={rec['mission_id']} id={args.id} state={args.state}")
        return 0
    if args.cmd == "topology":
        print(json.dumps(topology(args.mission), indent=1, default=str))
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
                           continue_max_tokens=args.continue_max_tokens, worker_mcp=args.worker_mcp,
                           ccr_class=args.ccr_class, estimate_basis=args.estimate_basis,
                           phase_lease=(None if args.phase_lease is None else
                                        {"phase": args.phase_lease, "state_file": args.phase_state,
                                         "forecast": _token_count("phase_forecast", args.phase_forecast)
                                         if args.phase_forecast else None}))
        pkt =(rec.get("wu_packet") or {}).get("path")
        print(f"ENVELOPE SET mission={rec['mission_id']} token_estimate={rec.get('token_estimate')} "
              f"model={rec.get('model')} autocompact={rec.get('autocompact')} wu_packet={pkt} "
              f"wu_packet_epoch={rec.get('wu_packet_epoch')} continue_max_tokens={rec.get('continue_max_tokens')} "
              f"worker_mcp={rec.get('worker_mcp') or 'inherit'}")
        return 0
    if args.cmd == "admit":
        adm = admit_route(args.mission, args.route, floors_path=args.floors)["admission"]
        print(f"ROUTE {adm['verdict']} mission={args.mission} need={adm.get('need_with_margin')} "
              f"target={adm['envelope']['target']} remaining={adm.get('remaining')}")
        for r in adm["reasons"]:
            print(f"  - {r}")
        return 0 if adm["verdict"] in LAUNCHABLE_VERDICTS else 3
    if args.cmd == "supervise":
        rows = supervise(dry_run=args.dry_run)
        failed = [r for r in rows if r.get("error")]
        if args.actions_only:
            # An isolated per-mission error has action "none"; filtering it out made it invisible in the sweep log.
            rows = [r for r in rows if r.get("action") not in ("none", "await") or r.get("error")]
        print(json.dumps(rows))
        # Non-zero so the sweep heartbeat records the failure and sweep_health reads FAILING (264 crashed passes
        # read OK on 2026-10-07 because only age and timeouts were judged).
        return 3 if failed else 0
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
    try:
        import econ_incident
        for line in econ_incident.status_lines():
            print(line, file=sys.stderr)
    except Exception as exc:  # noqa: BLE001 -- an unreadable incident store is itself reported
        print(f"ECONOMIC INCIDENTS UNREADABLE: {type(exc).__name__}: {exc}", file=sys.stderr)
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
    # A pass that runs on time and crashes every time is not healthy: GEX44 2026-10-07, 264 passes rc=1 read OK.
    failing = [f"{s['name']} rc={s['rc']}" for s in b.get("stages", [])
               if not s.get("timed_out") and s.get("rc") not in (0, None)]
    if b.get("outcome") == "running" and age > SWEEP_STALE_S:
        # A pass is bounded at 840 s by its own stage deadlines; running past that is a pass
        # that escaped its bounds, not merely a missed schedule.
        return {"verdict": "STUCK", "detail": f"pass running for {int(age)} s"}
    if age > SWEEP_STALE_S:
        return {"verdict": "STALE", "detail": f"last pass {int(age)} s ago ({b.get('outcome')})"}
    if failing:
        streak = b.get("fail_streak")
        return {"verdict": "FAILING", "detail": f"stages failed last pass: {failing}"
                + (f"; {streak} consecutive failed passes" if streak else "")}
    if timed:
        return {"verdict": "DEGRADED", "detail": f"stages timed out last pass: {timed}"}
    return {"verdict": "OK", "detail": f"{b.get('outcome')} {int(age)} s ago"}


if __name__ == "__main__":
    sys.exit(_cli())
