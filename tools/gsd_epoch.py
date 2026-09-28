#!/usr/bin/env python
"""gsd_epoch -- turn continuation is not context rotation (spec vault/specs/parent-context-epoch-rotation.md).

A mission (tools/gsd_mission.py) is carried by `claude --bg` workers. Until 2026-09-28 every turn a
worker ENDED was answered by a FRESH worker: 444 of 499 launches in 43 missions were "owner's turn
ended without completion" and exactly one was the context wall. Each fresh worker pays the startup
floor again (measured: 186,856 tokens resident at call #1, written as a 1-hour cache entry) and
forgets everything it was doing, and none of those launches said WHY it happened -- so a turn end
and a context rotation were indistinguishable in every record.

This module owns the layer between a mission and its turns:

  * CAUSES -- why a worker turn was started. Every launch carries one; UNKNOWN is an answer.
  * decide_turn_end -- when a worker's turn ends and work remains: CONTINUE the same session
    (`claude --bg --resume <id>`, same context epoch), ROTATE to a fresh session (new context
    epoch), or HOLD (children still running, a continuation still in flight).
  * continue_worker -- the same-session continuation effect. Host semantics verified 2026-09-28
    (probe 7a42f96f): after `claude stop`, `claude --bg --resume <sid> "<prompt>"` WITH NO OTHER
    FLAGS wakes the same session id, same transcript, context preserved. With flags the host
    starts a COPY under a new id ("keeps its own saved options, so the flags you passed started
    a copy") -- a copy is a second worker, so it is refused and stopped.
  * child_work -- the background-task barrier (G6): a worker is not stopped while a background
    command or agent it launched has not reported, or while a reported result sits unconsumed.
  * identity_check -- a session that starts as a mission worker must be where the mission is (S7).
  * epochs / census -- per-epoch view (G4) and separated counters built from the ledger, with
    historical launches classified from their recorded reason plus wall evidence.

Economics behind the continuation ceiling (measured, not assumed): a resumed process does NOT
reuse the cached prefix -- probe turn 2 wrote 125,483 tokens and read 33,949, the cache breaking
near the front on every process start. So a continuation costs about the CURRENT context as a
cache write, a fresh worker about the FLOOR plus whatever it must re-read to reconstruct. Below
the ceiling continuing is cost-neutral and keeps the worker's working memory; above it a fresh
context is cheaper. The ceiling is a named, per-mission-overridable number, not a law.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_long_run as lr  # noqa: E402

# ------------------------------------------------------------------------ taxonomy
INITIAL = "INITIAL"                        # first worker of a mission
TURN_CONTINUATION = "TURN_CONTINUATION"    # a turn ended, work remains, no wall
CONTEXT_ROTATION = "CONTEXT_ROTATION"      # the context itself is why a fresh session starts
CONTINUATION_FAILED = "CONTINUATION_FAILED"  # a same-session continuation did not take
PROCESS_RECOVERY = "PROCESS_RECOVERY"      # the owner died
LAUNCH_RETRY = "LAUNCH_RETRY"              # a launched worker never acknowledged
MISSION_RENEWAL = "MISSION_RENEWAL"        # first worker of a renewed (budget) successor
PROVIDER_HOLD = "PROVIDER_HOLD"            # quota refusal: nothing launched (recorded as a hold)
MANUAL_OPERATOR = "MANUAL_OPERATOR"
UNKNOWN = "UNKNOWN"
CAUSES = (INITIAL, TURN_CONTINUATION, CONTEXT_ROTATION, CONTINUATION_FAILED, PROCESS_RECOVERY,
          LAUNCH_RETRY, MISSION_RENEWAL, PROVIDER_HOLD, MANUAL_OPERATOR, UNKNOWN)

RESUME = "resume"   # same session id, same context epoch
FRESH = "fresh"     # new session, new context epoch

CONTINUE, ROTATE, HOLD = "continue", "rotate", "hold"

# Continue in the same session only while the context is below this many tokens (see the module
# docstring: at ~floor+reconstruction a resume stops being cheaper than a fresh worker). Per mission:
# rec["continue_max_tokens"]. The context wall (hooks/mission_wall.js) remains the hard mid-turn stop.
CONTINUE_MAX_TOKENS = 300_000
CONTINUATION_DEADLINE_S = 600   # resume requested -> the transcript shows the new turn
CHILD_WAIT_S = 1800             # longest a relay waits on a pending background child
FINISHED_STATUSES = {"completed", "failed", "killed", "stopped", "cancelled", "canceled", "error"}


def continuation_enabled() -> bool:
    return os.environ.get("CPP_MISSION_CONTINUATION", "").lower() != "off"


# ------------------------------------------------------------------------ transcripts
def _transcript(session_id: str) -> Path | None:
    try:
        return lr.find_transcript(session_id)
    except Exception:  # noqa: BLE001 -- no transcript is its own answer
        return None


def _rows(path: Path) -> list[dict]:
    out = []
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                if isinstance(row, dict):
                    out.append(row)
    except OSError:
        return []
    return out


def _ts(value) -> float | None:
    return lr._parse_iso(value) if value else None


def context_tokens(session_id: str) -> int | None:
    """Tokens resident in the worker's context at its LAST model call: input + cache writes +
    cache reads of the last assistant row carrying usage. None when no transcript or no usage --
    unmeasured, never zero."""
    path = _transcript(session_id)
    if not path:
        return None
    for row in reversed(lr._tail_rows(path)):
        msg = row.get("message") if row.get("type") == "assistant" else None
        u = (msg or {}).get("usage") if isinstance(msg, dict) else None
        if isinstance(u, dict):
            try:
                return int(u.get("input_tokens") or 0) + int(u.get("cache_creation_input_tokens") or 0) \
                    + int(u.get("cache_read_input_tokens") or 0)
            except (TypeError, ValueError):
                return None
    return None


def last_assistant_at(session_id: str) -> float | None:
    """Timestamp of the worker's last assistant row: proof that a turn actually ran."""
    path = _transcript(session_id)
    if not path:
        return None
    for row in reversed(lr._tail_rows(path)):
        if row.get("type") == "assistant":
            return _ts(row.get("timestamp"))
    return None


# ------------------------------------------------------------------------ wall evidence
def _marker_dir() -> Path:
    # hooks/mission_wall.js writes its flag here (GSD_AUTORUN_MARKER_DIR or ~/.claude/state).
    d = os.environ.get("GSD_AUTORUN_MARKER_DIR")
    return Path(d) if d else lr.state_dir()


def wall_evidence(session_id: str | None, epoch, events: list[dict] | None = None) -> dict | None:
    """Did THIS worker cross its context wall in THIS epoch? Two independent witnesses:
    the mid-turn flag file hooks/mission_wall.js writes once per (session, epoch), and the
    watchdog's Stop-time ledger row (`handoff_asked` / `handoff_already_asked`). The mission
    record itself never learns of the wall -- which is why 498 of 499 historical launches
    could not be attributed -- so the attribution is made HERE, from the witnesses."""
    if not session_id:
        return None
    flag = _marker_dir() / f"mission-wall-{session_id}-e{epoch}.flag"
    if flag.exists():
        return {"witness": "mission_wall_flag", "path": str(flag)}
    evs = lr.ledger_events(session_id) if events is None else [
        e for e in events if e.get("session_id") == session_id]
    for e in reversed(evs):
        if e.get("event") in ("handoff_asked", "handoff_already_asked"):
            if e.get("epoch") is None or str(e.get("epoch")) == str(epoch):
                return {"witness": f"ledger:{e['event']}", "ts": e.get("ts"),
                        "used_pct": e.get("used_pct")}
    return None


# ------------------------------------------------------------------------ G6 child work
_NOTE_RE = re.compile(r"<tool-use-id>(toolu_[A-Za-z0-9_]+)</tool-use-id>.*?<status>([a-z_]+)</status>", re.S)
_BG_RESULT_RE = re.compile(r"running in (?:the )?background|async agent|launched in the background|"
                           r"agent (?:is )?running|backgrounded", re.I)


def _content_text(content) -> str:
    if isinstance(content, str):
        return content
    parts = []
    for b in content or []:
        if isinstance(b, dict):
            if b.get("type") == "text":
                parts.append(b.get("text") or "")
            elif isinstance(b.get("content"), (str, list)):
                parts.append(_content_text(b.get("content")))
    return "\n".join(parts)


def child_work(session_id: str, now: float | None = None, wait_s: float = CHILD_WAIT_S) -> dict:
    """Background work this worker (or any of its subagents) launched and that has not reported.

    Launch: a `tool_use` whose input sets `run_in_background`, or an Agent/Task call whose
    immediate result says it runs in the background. Report: a `<task-notification>` naming that
    tool-use id with a finished status. A notification ENQUEUED and never removed is a result the
    worker has not consumed yet -- the host will wake the worker with it, so stopping now loses it.

    Verdicts: CLEAR (nothing pending) · HOLD (pending, youngest launch within `wait_s`) ·
    EXPIRED (pending but older: proceed, named as lost) · UNKNOWN (no transcript: nothing proves
    there is no child, so the caller records it; it does not hold forever on an absence)."""
    now = time.time() if now is None else now
    main = _transcript(session_id)
    if not main:
        return {"verdict": "UNKNOWN", "reason": "no transcript", "pending": [], "unconsumed": []}
    files = [main] + sorted((main.parent / main.stem / "subagents").glob("*.jsonl"))
    launches: dict[str, dict] = {}
    agent_calls: dict[str, dict] = {}
    finished: set[str] = set()
    queued: dict[str, float | None] = {}
    for f in files:
        for row in _rows(f):
            kind = row.get("type")
            if kind == "queue-operation":
                for tid, status in _NOTE_RE.findall(str(row.get("content") or "")):
                    if status in FINISHED_STATUSES:
                        finished.add(tid)
                    if row.get("operation") == "enqueue":
                        queued[tid] = _ts(row.get("timestamp"))
                    elif row.get("operation") in ("remove", "dequeue"):
                        queued.pop(tid, None)
                continue
            msg = row.get("message")
            if not isinstance(msg, dict):
                continue
            content = msg.get("content")
            if kind == "user":
                text = _content_text(content) if isinstance(content, str) else ""
                for tid, status in _NOTE_RE.findall(text):
                    if status in FINISHED_STATUSES:
                        finished.add(tid)
                    queued.pop(tid, None)   # delivered as a user message: consumed
                for b in content if isinstance(content, list) else []:
                    if isinstance(b, dict) and b.get("type") == "tool_result":
                        tid = b.get("tool_use_id")
                        if tid in agent_calls:
                            if _BG_RESULT_RE.search(_content_text(b.get("content"))):
                                launches[tid] = agent_calls[tid]
                            else:
                                agent_calls.pop(tid, None)   # synchronous agent: its result IS the report
                continue
            if kind != "assistant":
                continue
            for b in content if isinstance(content, list) else []:
                if not (isinstance(b, dict) and b.get("type") == "tool_use"):
                    continue
                inp = b.get("input") if isinstance(b.get("input"), dict) else {}
                entry = {"tool_use_id": b.get("id"), "tool": b.get("name"),
                         "what": str(inp.get("description") or inp.get("command") or "")[:120],
                         "at": _ts(row.get("timestamp")), "file": f.name}
                if inp.get("run_in_background") is True:
                    launches[b.get("id")] = entry
                elif b.get("name") in ("Agent", "Task"):
                    agent_calls[b.get("id")] = entry
    pending = [v for k, v in launches.items() if k not in finished]
    unconsumed = sorted(queued)
    if not pending and not unconsumed:
        return {"verdict": "CLEAR", "pending": [], "unconsumed": []}
    ages = [now - p["at"] for p in pending if p.get("at")] + [now - t for t in queued.values() if t]
    youngest = min(ages) if ages else 0.0
    verdict = "HOLD" if youngest < wait_s else "EXPIRED"
    return {"verdict": verdict, "pending": pending, "unconsumed": unconsumed,
            "youngest_age_s": int(youngest)}


# ------------------------------------------------------------------------ the decision
def decide_turn_end(rec: dict, now: float | None = None, *, events: list[dict] | None = None,
                    tokens=context_tokens, children=child_work, last_turn_at=last_assistant_at) -> dict:
    """The owner's turn ended and GSD says work remains. What starts the next turn?

    Returns {"decision": continue|rotate|hold, "cause", "mechanism", "reason", "evidence"}.
    Order is load-bearing: a child still running beats everything (stopping kills it); the wall is
    stronger evidence than any estimate; a continuation in flight is never doubled; a context we
    cannot measure is not assumed small."""
    now = time.time() if now is None else now
    owner = rec.get("owner") or {}
    sid = owner.get("session_id")
    ev: dict = {}
    kids = children(sid, now) if sid else {"verdict": "UNKNOWN", "reason": "no owner"}
    ev["children"] = kids.get("verdict")
    if kids.get("verdict") == "HOLD":
        return {"decision": HOLD, "cause": None, "mechanism": None, "evidence": {**ev, "child": kids},
                "reason": f"{len(kids.get('pending') or [])} background child(ren) pending, "
                          f"{len(kids.get('unconsumed') or [])} result(s) unconsumed"}
    if kids.get("verdict") == "EXPIRED":
        ev["children_lost"] = [p.get("tool_use_id") for p in kids.get("pending") or []] + list(
            kids.get("unconsumed") or [])
    wall = wall_evidence(sid, rec.get("epoch"), events)
    if wall:
        return {"decision": ROTATE, "cause": CONTEXT_ROTATION, "mechanism": FRESH,
                "reason": f"context wall crossed in epoch {rec.get('epoch')} ({wall['witness']})",
                "evidence": {**ev, "wall": wall, "trigger": "wall"}}
    if rec.get("state") == "HANDOFF_REQUESTED":
        # The owner itself asked for a successor (gsd_mission handoff): a fresh context by request.
        return {"decision": ROTATE, "cause": CONTEXT_ROTATION, "mechanism": FRESH,
                "reason": "owner requested a hand-off", "evidence": {**ev, "trigger": "handoff_requested"}}
    if not continuation_enabled():
        return {"decision": ROTATE, "cause": TURN_CONTINUATION, "mechanism": FRESH,
                "reason": "same-session continuation disabled (CPP_MISSION_CONTINUATION=off)",
                "evidence": ev}
    # `last_continuation_at` survives the ack (which clears `pending`): a resumed worker can read as
    # idle for a moment before its new turn starts -- probe v1 stopped a booting session that way --
    # so a second continuation is refused until the transcript shows the first one's turn.
    req = rec.get("last_continuation_at")
    if req and sid and (rec.get("last_continuation_session") in (None, sid)):
        ran = last_turn_at(sid)
        if not (ran and ran > float(req)):
            if now > float(req) + CONTINUATION_DEADLINE_S:
                return {"decision": ROTATE, "cause": CONTINUATION_FAILED, "mechanism": FRESH,
                        "reason": f"continuation requested at {int(float(req))} produced no turn "
                                  f"within {CONTINUATION_DEADLINE_S} s", "evidence": ev}
            return {"decision": HOLD, "cause": None, "mechanism": None, "evidence": ev,
                    "reason": "continuation in flight: its turn has not appeared in the transcript yet"}
    n = tokens(sid) if sid else None
    ev["context_tokens"] = n
    ceiling = int(rec.get("continue_max_tokens") or CONTINUE_MAX_TOKENS)
    if n is None:
        return {"decision": ROTATE, "cause": TURN_CONTINUATION, "mechanism": FRESH,
                "reason": "context size unmeasured: a fresh worker is the bounded choice",
                "evidence": ev}
    if n >= ceiling:
        return {"decision": ROTATE, "cause": CONTEXT_ROTATION, "mechanism": FRESH,
                "reason": f"context {n} tokens >= continuation ceiling {ceiling}",
                "evidence": {**ev, "trigger": "economic_ceiling", "ceiling": ceiling}}
    return {"decision": CONTINUE, "cause": TURN_CONTINUATION, "mechanism": RESUME,
            "reason": f"turn ended; context {n} < {ceiling} tokens: same session continues",
            "evidence": ev}


# ------------------------------------------------------------------------ the effect
_COPY_RE = re.compile(r"started a copy as ([0-9a-f]{8})|starts a copy|started a copy", re.I)


def record_cause(mission_id: str, rec: dict, decision: dict, mechanism: str,
                 worker: str | None = None) -> bool:
    """The one row that says why a worker turn started. `epoch` is the context epoch the turn
    runs in (the claimed epoch for a fresh launch, the unchanged one for a resume)."""
    ev = decision.get("evidence") or {}
    fields = {"mission_id": mission_id, "epoch": rec.get("epoch"), "seq": rec.get("seq"),
              "cause": decision.get("cause") or UNKNOWN, "mechanism": mechanism,
              "reason": decision.get("reason"), "context_tokens": ev.get("context_tokens"),
              "trigger": ev.get("trigger"), "children": ev.get("children")}
    if worker:
        fields["worker"] = worker
    if ev.get("children_lost"):
        fields["children_lost"] = ev["children_lost"]
    return lr.ledger_append(mission_id, "launch_cause", **{k: v for k, v in fields.items() if v is not None})


def cause_for(act: str, plan_reason: str | None, rec: dict, decision: dict | None = None) -> dict:
    """The cause of a FRESH launch the supervisor is about to make, as a decision-shaped dict.
    A relay carries decide_turn_end's own decision; every other act is named from the record."""
    if decision and decision.get("cause"):
        return decision
    pend = rec.get("pending") or {}
    if act == "launch":
        cause = MISSION_RENEWAL if rec.get("renewed_from") else INITIAL
    elif act == "replace" and pend.get("kind") == "turn_continuation":
        cause = CONTINUATION_FAILED
    elif act == "replace" and rec.get("state") == "LAUNCHING":
        cause = LAUNCH_RETRY
    elif act in ("replace", "relay") and _RECOVERY.search(plan_reason or ""):
        cause = PROCESS_RECOVERY
    else:
        cause = UNKNOWN
    return {"cause": cause, "reason": plan_reason, "evidence": {}}


def resume_argv(session_id: str, prompt: str) -> list[str]:
    """NO flags besides --bg/--resume: any other flag makes the host start a COPY (measured)."""
    exe = os.environ.get("CPP_CLAUDE_EXE") or "claude"
    return [exe, "--bg", "--resume", session_id, prompt]


def continue_worker(mission_id: str, rec: dict, *, prompt: str, decision: dict, runner=None,
                    stop_runner=None, now: float | None = None, progress: dict | None = None) -> dict:
    """Claim the continuation (CAS), then wake the SAME session with the prompt. The caller has
    already stopped the owner and waited for its pid (stop_owner).

    The claim moves the mission to LAUNCHING at the SAME epoch with `pending.bg_id` = the
    session's short id, so every existing piece of the launch machinery applies unchanged: the
    resumed session's own SessionStart acks it (mission_for_session matches the bg_id prefix),
    or the host listing it is adoption; the start deadline turns a wake that never happened into
    a replacement. Keeping RUNNING instead would let a second supervisor -- which reads the
    stopped owner as DEAD -- win its CAS on the unchanged (epoch, state) and launch a fresh
    worker BESIDE the resumed one. `iterations` is counted by that ack/adoption, as for any launch."""
    import subprocess
    import gsd_mission as gm
    now = time.time() if now is None else now
    sid = rec["owner"]["session_id"]
    extra = {"progress": progress} if progress is not None else {}
    if progress is not None and not rec.get("progress_origin") and progress.get("measured"):
        extra["progress_origin"] = progress.get("fp")
    claimed = gm.transition(
        mission_id, expect_epoch=rec["epoch"], expect_state=rec["state"], event="turn_continued",
        now=now, state=gm.LAUNCHING, worker=sid, reason=decision.get("reason"),
        owner=None, previous_owner=rec.get("owner"),
        continuations=int(rec.get("continuations") or 0) + 1,
        last_continuation_at=now, last_continuation_session=sid,
        pending={"kind": "turn_continuation", "epoch": rec["epoch"], "bg_id": sid[:8],
                 "session_id": sid, "requested_at": now, "deadline": now + gm.START_DEADLINE_S,
                 "cause": decision.get("cause")},
        **extra)
    record_cause(mission_id, claimed, decision, RESUME, worker=sid)
    run = runner or (lambda argv, cwd: subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                                                      encoding="utf-8", errors="replace", timeout=180))
    try:
        r = run(resume_argv(sid, prompt), rec["cwd"])
        out, rc = gm.ANSI_RE.sub("", (r.stdout or "") + "\n" + (r.stderr or "")), r.returncode
    except Exception as exc:  # noqa: BLE001 -- the wake could not happen
        out, rc = f"{type(exc).__name__}: {exc}", None
    copy = _COPY_RE.search(out)
    ok = rc == 0 and not copy and bool(re.search(rf"\b{re.escape(sid[:8])}\b", out))
    if ok:
        return {"ok": True, "mechanism": RESUME, "session": sid, "epoch": claimed["epoch"]}
    why = "host started a COPY instead of continuing" if copy else f"resume refused (rc={rc})"
    if copy and copy.group(1):
        try:  # a copy is a second worker on the same mission: never leave it running
            (stop_runner or (lambda a: subprocess.run(a, capture_output=True, timeout=120)))(
                [os.environ.get("CPP_CLAUDE_EXE") or "claude", "stop", copy.group(1)])
        except Exception:  # noqa: BLE001 -- the orphan reaper finds it by name
            pass
    lr.ledger_append(mission_id, "continuation_failed", mission_id=mission_id, epoch=claimed["epoch"],
                     worker=sid, why=why, detail=out.strip()[-300:])
    try:  # fail fast: an overdue LAUNCHING is replaced on the next pass (cause CONTINUATION_FAILED)
        gm.transition(mission_id, expect_epoch=claimed["epoch"], expect_state=gm.LAUNCHING,
                      event="continuation_failed", now=now,
                      pending={**claimed["pending"], "failed": why, "deadline": now})
    except gm.CasConflict:
        pass
    return {"ok": False, "mechanism": RESUME, "session": sid, "why": why}


# ------------------------------------------------------------------------ S7 identity
def identity_check(rec: dict, session_id: str, session_cwd: str | None) -> dict:
    """Does the session that just started belong where the mission says? Cheap by design (the
    SessionStart hub has a deadline): string and filesystem checks only, no git subprocess.
    Verdicts: OK · MISMATCH (named) · UNKNOWN (nothing to compare with)."""
    problems = []
    norm = lambda p: os.path.normcase(os.path.abspath(str(p))) if p else None  # noqa: E731
    if session_cwd is None:
        return {"verdict": "UNKNOWN", "reason": "session cwd unrecorded"}
    if norm(session_cwd) != norm(rec.get("cwd")):
        problems.append(f"session cwd {session_cwd} != mission cwd {rec.get('cwd')}")
    wd = rec.get("work_dir") or rec.get("cwd")
    if wd and not (Path(wd) / ".git").exists():
        problems.append(f"work tree {wd} has no .git")
    owner = rec.get("owner") or {}
    pend = rec.get("pending") or {}
    if owner.get("session_id") == session_id and owner.get("epoch") not in (None, rec.get("epoch")):
        problems.append(f"owner lease is for epoch {owner.get('epoch')}, mission is at {rec.get('epoch')}")
    if pend.get("kind") == "worker_start" and pend.get("epoch") not in (None, rec.get("epoch")):
        problems.append(f"pending launch is for epoch {pend.get('epoch')}, mission is at {rec.get('epoch')}")
    return {"verdict": "MISMATCH", "problems": problems} if problems else {"verdict": "OK"}


def on_session_start(rec: dict, session_id: str, source: str, session_cwd: str | None,
                     first: bool) -> str:
    """G3 + S7, called from gsd_mission.session_start for a mission worker. Returns a line to put
    in front of the worker's card ('' when there is nothing to say).

    G3: a SessionStart whose source is `compact` is the host's own postcondition that this
    worker's context was compacted. Missions never REQUEST compaction (the wall hands off
    instead; `--autocompact` is only the native safety net), so every observed compaction is an
    unplanned one and is ledgered as `epoch_compacted` -- the epoch is no longer a clean context.
    S7: the first start of a launch or continuation checks the session is where the mission is."""
    line = ""
    if (source or "").lower() == "compact":
        lr.ledger_append(rec["mission_id"], "epoch_compacted", mission_id=rec["mission_id"],
                         epoch=rec.get("epoch"), worker=session_id, requested=False,
                         observed="SessionStart source=compact")
    if first:
        ident = identity_check(rec, session_id, session_cwd)
        if ident["verdict"] == "MISMATCH":
            lr.ledger_append(rec["mission_id"], "rehydration_mismatch", mission_id=rec["mission_id"],
                             epoch=rec.get("epoch"), worker=session_id, problems=ident["problems"])
            line = ("IDENTITY CHECK FAILED -- do not continue this mission from here: "
                    + "; ".join(ident["problems"])
                    + ". End your turn with one line saying so; the supervisor will surface it.")
        elif ident["verdict"] == "OK":
            lr.ledger_append(rec["mission_id"], "rehydration_verified", mission_id=rec["mission_id"],
                             epoch=rec.get("epoch"), worker=session_id, source=source or None)
    return line


# ------------------------------------------------------------------------ G4 view + census
_RECOVERY = re.compile(r"owner dead|hand-off owner gone|owner gone", re.I)
_TURN_END = re.compile(r"turn ended|finished its step", re.I)


def classify_launch(row: dict, prev_owner: str | None, prev_epoch, events: list[dict],
                    renewed: bool) -> tuple[str, str]:
    """(cause, basis) for one `launch_claimed` ledger row. A row written after 2026-09-28 names its
    cause; an older one is classified from its recorded reason plus the wall witnesses."""
    if row.get("cause") in CAUSES:
        return row["cause"], "recorded"
    reason = str(row.get("reason") or "")
    if reason in ("armed", "prepared, nothing launched") or row.get("epoch") == 1:
        return (MISSION_RENEWAL if renewed else INITIAL), "reason"
    if "start ack overdue" in reason or "never acknowledged" in reason:
        return LAUNCH_RETRY, "reason"
    if _RECOVERY.search(reason):
        return PROCESS_RECOVERY, "reason"
    if _TURN_END.search(reason):
        if prev_owner and wall_evidence(prev_owner, prev_epoch, events):
            return CONTEXT_ROTATION, "reason+wall_witness"
        return TURN_CONTINUATION, "reason"
    return UNKNOWN, "reason unrecognised"


def epochs(mission_id: str, events: list[dict] | None = None) -> list[dict]:
    """One row per CONTEXT EPOCH of a mission (a fresh worker session), with the turns it carried."""
    events = lr.ledger_events() if events is None else events
    mine = [e for e in events if e.get("mission_id") == mission_id]
    renewed = any(e.get("event") == "mission_renewed" and e.get("session_id") == mission_id
                  and "successor" not in e for e in mine)
    causes = {}
    for e in mine:
        if e.get("event") == "launch_cause" and e.get("mechanism") == FRESH:
            causes[e.get("epoch")] = e
    out: list[dict] = []
    cur = None
    for e in mine:
        ev = e.get("event")
        if ev == "launch_claimed":
            prev_owner = cur.get("session") if cur else None
            prev_epoch = cur.get("epoch") if cur else None
            rec_cause = causes.get(e.get("epoch"))
            cause, basis = classify_launch({**e, **({"cause": rec_cause["cause"]} if rec_cause else {})},
                                           prev_owner, prev_epoch, events, renewed)
            if cur:
                cur["end"] = e.get("ts")
                cur["end_cause"] = cause
            cur = {"epoch": e.get("epoch"), "start": e.get("ts"), "start_cause": cause,
                   "basis": basis, "reason": e.get("reason"), "session": None, "turns": 0,
                   "continuations": 0, "compactions": 0, "wall": False, "end": None, "end_cause": None}
            out.append(cur)
        elif cur is None:
            continue
        elif ev in ("worker_acked", "worker_adopted"):
            # The first ack of an epoch is its first turn; a later ack is a continued turn's
            # restart, already counted at `turn_continued`.
            if not cur.get("ack"):
                cur["turns"] += 1
                cur["ack"] = ev
            cur["session"] = cur["session"] or e.get("worker")
        elif ev == "turn_continued":
            cur["turns"] += 1
            cur["continuations"] += 1
            cur["session"] = cur["session"] or e.get("worker")
        elif ev == "epoch_compacted":
            cur["compactions"] += 1
        elif ev in ("mission_halted", "mission_completed"):
            cur["end"], cur["end_cause"] = e.get("ts"), ev.replace("mission_", "").upper()
    for c in out:
        if c["session"] and wall_evidence(c["session"], c["epoch"], events):
            c["wall"] = True
    return out


def census(events: list[dict] | None = None) -> dict:
    """Separated counters across every mission on this host. No counter stands in for another:
    a fresh launch is not a rotation, a rotation is not progress, a session is not an epoch."""
    import gsd_mission as gm
    events = lr.ledger_events() if events is None else events
    missions = gm.all_missions()
    # The population is DISCOVERED from both sources: a mission whose record is gone (or never
    # parsed) but whose launches are in the ledger still launched workers, and must be counted.
    ids = {m["mission_id"] for m in missions} | {
        e["mission_id"] for e in events if e.get("event") == "launch_claimed" and e.get("mission_id")}
    lineage = {m["mission_id"]: m.get("lineage_id") or m["mission_id"] for m in missions}
    lineages = {lineage.get(i, i) for i in ids}
    by_cause: dict[str, int] = {c: 0 for c in CAUSES}
    rotation_triggers: dict[str, int] = {}
    fresh = continuations = compactions = zero_turn_epochs = 0
    for mid in sorted(ids):
        for ep in epochs(mid, events):
            fresh += 1
            by_cause[ep["start_cause"]] = by_cause.get(ep["start_cause"], 0) + 1
            continuations += ep["continuations"]
            compactions += ep["compactions"]
            if ep["turns"] == 0:
                zero_turn_epochs += 1
    for e in events:
        if e.get("event") == "launch_cause" and e.get("cause") == CONTEXT_ROTATION:
            t = e.get("trigger") or "unrecorded"
            rotation_triggers[t] = rotation_triggers.get(t, 0) + 1
    holds = sum(1 for e in events if e.get("event") == "quota_held")
    return {"logical_runs": len(lineages), "missions": len(ids), "fresh_worker_sessions": fresh,
            "fresh_by_cause": by_cause, "context_rotations": by_cause[CONTEXT_ROTATION],
            "rotation_triggers_recorded": rotation_triggers, "same_session_continuations": continuations,
            "compactions_observed": compactions, "provider_holds": holds,
            "epochs_never_acknowledged": zero_turn_epochs,
            "note": "historical launches are classified from their recorded reason plus wall witnesses; "
                    "`basis` per epoch says which (tools/gsd_epoch.py epochs --mission <id>)"}


def _cli(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="context epochs of GSD missions")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("census")
    e = sub.add_parser("epochs")
    e.add_argument("--mission", required=True)
    c = sub.add_parser("children")
    c.add_argument("--session", required=True)
    t = sub.add_parser("context")
    t.add_argument("--session", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "census":
        out = census()
    elif a.cmd == "epochs":
        out = epochs(a.mission)
    elif a.cmd == "children":
        out = child_work(a.session)
    else:
        out = {"session": a.session, "context_tokens": context_tokens(a.session)}
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
