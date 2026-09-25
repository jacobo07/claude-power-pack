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
            "state": PREPARED, "epoch": 0, "owner": None, "pending": None,
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
    for tool in rec.get("allowed_tools") or []:
        argv += ["--allowedTools", tool]
    for d in rec.get("add_dirs") or []:
        argv += ["--add-dir", d]
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
                  stop_runner=None, work_dir: str | None = None) -> dict:
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
    if work_dir:
        extra["work_dir"] = work_dir
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
                                     "work_dir": wd}, _git_facts(wd))
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
        f"Resume command: {bind_workstream(rec['resume_command'], rec.get('workstream'))}",
        *([f"WORKSTREAM {rec['workstream']}: before any GSD step run `node "
           f"~/.claude/gsd-core/bin/gsd-tools.cjs query workstream.set {rec['workstream']} --raw "
           f"--cwd .` (session-local pointer; gsd_run calls do not forward --ws). The repo's ROOT "
           f"milestone belongs to another track -- never plan or execute it."]
          if rec.get("workstream") else []),
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
    """Did this transcript line act on `workstream`? Its directory (either separator, JSON-escaped
    or not), its --ws flag, or its workstream.set call."""
    return any(tok in line for tok in (
        f"workstreams/{workstream}", f"workstreams\\\\{workstream}", f"workstreams\\{workstream}",
        f"--ws {workstream}", f"workstream.set {workstream}"))


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
        if workstream and not touched:
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
               runner=None, wait_s: float | None = None) -> tuple[bool, str]:
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
        return False, f"pid {pid} still alive after {int(wait_s)} s"
    return True, "stopped; no pid to wait on"


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


def supervise(now: float | None = None, dry_run: bool = False, sessions=None,
              gsd_status=None, runner=None, stop_runner=None, pid_alive=lr._pid_alive) -> list[dict]:
    """One out-of-band pass over every mission. Each action is ledgered by the
    transition it makes; a pass that decides nothing still returns one row per
    mission, so an empty estate and an unjudged one never look alike."""
    import subprocess
    now = time.time() if now is None else now
    missions = all_missions()
    if not any(_needs_look(m, now) for m in missions):
        # Nothing to supervise: do not ask the host (`claude agents --json` costs seconds,
        # measured > 60 s once under load) on every 5-minute pass of an idle estate.
        return [{"mission_id": m["mission_id"], "state": m["state"], "epoch": m["epoch"],
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
            if plan["action"] in ("none", "await"):
                continue
            act = plan["action"]
            if act == "halt":
                halted = transition(mid, expect_epoch=rec["epoch"], expect_state=rec["state"],
                                    event="mission_halted", now=now, state=HALTED, pending=None,
                                    reason=plan["reason"])
                reap(halted, row)  # a halt changes the record; stop the world to match it
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
                if act in ("relay", "replace") and rec.get("owner"):
                    # A replaced owner is DEAD by the host's word, and its pid can still outlive
                    # that word (W0 E13): wait for it too, or the successor overlaps it.
                    ok, why = stop_owner(rec.get("owner"), sessions, pid_alive=pid_alive,
                                         runner=stop_runner)
                    row["stop"] = why
                    if not ok:
                        continue  # the next pass retries; nothing launched beside a live worker
                note = None
                if act in ("relay", "replace") and rec.get("owner"):
                    # Read BEFORE the launch: the note describes the predecessor's last turn.
                    # An explicit `handoff --note` counts only when THIS owner recorded it
                    # (state HANDOFF); otherwise the record's note is the previous epoch's and
                    # would be handed on as current.
                    explicit = rec.get("note") if rec["state"] == HANDOFF else ""
                    note = explicit or handoff_note_from_transcript(rec["owner"]["session_id"]) or ""
                    row["note_chars"] = len(note)
                row["launch"] = launch_worker(mid, expect_epoch=rec["epoch"],
                                              expect_state=rec["state"], reason=plan["reason"],
                                              runner=runner, now=now, note=note,
                                              work_dir=work_dir)
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
        rec = request_handoff(args.session, args.note)
        print(f"HANDOFF RECORDED mission={rec['mission_id']} epoch={rec['epoch']} -- end your turn now")
        return 0
    if args.cmd == "supervise":
        rows = supervise(dry_run=args.dry_run)
        if args.actions_only:
            rows = [r for r in rows if r.get("action") not in ("none", "await")]
        print(json.dumps(rows))
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
