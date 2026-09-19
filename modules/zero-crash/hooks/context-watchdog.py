#!/usr/bin/env python
"""Stop-hook: context-watchdog (BL-0015 + BL-0033 dual-threshold).

Two-tier context-pressure response on Stop event:

  Tier 1 — SNAPSHOT (used_pct >= 60):
    Append session snapshot to vault/sleepy/context_snapshots.jsonl
    AND a human-readable section to vault/progress.md.
    Silent (no advisory). Per-session debounced via tmp flag.

  Tier 2 — ADVISORY (used_pct >= 70):
    Above PLUS inject hookSpecificOutput.additionalContext telling the
    model to ASK the user to type `/compact focus on <current task>`.
    Per BL-0003 hooks CANNOT auto-fire slash commands; this advises
    the model, which advises the user, who types the command.
    Per-session debounced via separate tmp flag.

Reads metrics from /tmp/claude-ctx-<session_id>.json written by
gsd-statusline.js. Writes via lib/atomic_write.py (BL-0014/0018).

Complements gsd-context-monitor.js (PostToolUse, fires mid-turn at
35% remaining for pre-compact vault dump). This hook fires turn-end
and survives mid-turn crash.

Hook contract (Stop event):
  stdin JSON: {"session_id":"...","transcript_path":"...","cwd":"...",
                "stop_hook_active":bool}
  stdout: {} OR {"hookSpecificOutput":{...}} when advisory tier hit
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import re
import sys
import tempfile
from pathlib import Path

# Thresholds (BL-0033)
THRESHOLD_SNAPSHOT_PCT = 60
THRESHOLD_ADVISORY_PCT = 70
# Rearm floor (spec vault/specs/gsd-autonomous-autocompact.md, gap B). Tier 2
# is debounced once per session; a long unattended run needs it to fire at
# EVERY crossing, not the first. A reading this far below the advisory
# threshold is only reachable through a compaction or a fresh context, so it
# is the signal that the debounce may be cleared. Kept well under
# THRESHOLD_SNAPSHOT_PCT so the rearm band and the snapshot band cannot touch.
THRESHOLD_REARM_PCT = 45


THRESHOLDS_FILE = "ctxwd-thresholds-{session_id}.json"


def valid_thresholds(snap, adv, rearm):
    """The ONE rule. (snap, adv, rearm) as floats, or None.

    rearm < snapshot <= advisory, all within 5..95. Anything else is refused,
    so a typo can never switch the watchdog off -- it falls back to the next
    source and ultimately to the constants.
    """
    try:
        snap, adv, rearm = float(snap), float(adv), float(rearm)
    except (TypeError, ValueError):
        return None
    return (snap, adv, rearm) if 5 <= rearm < snap <= adv <= 95 else None


def _thresholds_from_file(session_id: str):
    """Thresholds THIS session asked for while already running, or None.

    Why a file at all: CTXWD_TEST_THRESHOLDS is read from the env of the
    Claude Code process, which is fixed at launch. /cpp-gsd-long is invoked
    from INSIDE a session that is already running ("Open the session IN the
    project you want to run"), so the env knob was unreachable from the only
    place the command is ever used -- the narrow-wall smoke test could be
    described but not performed. Written by
    `tools/gsd_long_run.py thresholds --set`, keyed by session id, and
    validated on read as well as on write: an unreadable or malformed file is
    not a licence, it is simply not an answer.
    """
    try:
        # Same directory the writer uses, including its GSD_LONG_RUN_STATE_DIR
        # relocation -- reader and writer must never disagree about where the
        # answer lives, and a gate that cannot redirect both writes into the
        # Owner's real state directory to test itself.
        base = os.environ.get("GSD_LONG_RUN_STATE_DIR") or (Path.home() / ".claude" / "state")
        p = Path(base) / THRESHOLDS_FILE.format(session_id=session_id)
        data = json.loads(p.read_text(encoding="utf-8"))
        return valid_thresholds(data.get("snapshot"), data.get("advisory"), data.get("rearm"))
    except Exception:
        return None


def _thresholds(session_id: str = "") -> tuple:
    """(snapshot, advisory, rearm) for THIS session.

    Three sources, most specific first:
      1. the per-session file, which a running session can write to itself;
      2. `CTXWD_TEST_THRESHOLDS="31,36,30"` in the launching process's env, so
         a /cpp-gsd-long smoke test crosses the wall at ~360k tokens instead
         of ~700k;
      3. the production constants.
    The file wins over the env because it is the only one that can change
    during a run, which is the whole reason it exists. Measured baseline on
    this host: a fresh session already reads 15-23% used, so a rearm below
    ~28 would never be reached after a compaction.
    """
    from_file = _thresholds_from_file(session_id) if session_id else None
    if from_file is not None:
        return from_file
    raw = os.environ.get("CTXWD_TEST_THRESHOLDS", "")
    if raw:
        try:
            snap, adv, rearm = raw.split(",")
        except ValueError:
            snap = adv = rearm = None
        checked = valid_thresholds(snap, adv, rearm)
        if checked is not None:
            return checked
    return THRESHOLD_SNAPSHOT_PCT, THRESHOLD_ADVISORY_PCT, THRESHOLD_REARM_PCT

# Post-compaction resume (gap C; Owner-authorised 2026-09-15 via settings
# autoMode.allow). Two flags because the dispatch is two-phase, and the reason
# is a race measured in the existing daemon's own source: it polls every 500 ms
# and presses Enter the moment it sees a trigger flag with Cursor in front.
# Dropping that flag in the same Stop that ASKS the model for the resume line
# would fire Enter while the model is still generating -- into an empty input
# box, consuming the flag for nothing.
#   Stop A: arm, and ask the model to end its turn with the command.
#   Stop B: the turn has ended, so the line is sitting there -- drop the flag
#           and let the daemon press Enter on what the model itself wrote.
# Both are cleared at tier 2, so each compaction cycle gets exactly one resume.
RESUME_ARMED_FLAG = "claude-ctxwd-resumearm-{session_id}.flag"
RESUME_DONE_FLAG = "claude-ctxwd-resumedone-{session_id}.flag"
# Set once the transcript shows the resume command was actually submitted
# (spec gsd-long-run-v2.md, gap 1). Cleared with the other two at tier 2.
RESUME_CONFIRMED_FLAG = "claude-ctxwd-resumeok-{session_id}.flag"

ROOT = Path.home() / ".claude" / "skills" / "claude-power-pack"
LEDGER_PATH = ROOT / "vault" / "sleepy" / "context_snapshots.jsonl"
ATOMIC_WRITE_DIR = ROOT / "lib"
# PROGRESS_PATH is now derived per-project from cwd (BL-0043 globalization).
# Fallback to power-pack vault when cwd is missing or unwriteable.
FALLBACK_PROGRESS_PATH = ROOT / "vault" / "progress.md"


def _resolve_progress_path(cwd: str) -> Path:
    """Return the per-project progress.md path. Per BL-0043:
      1. <cwd>/vault/progress.md     (project has a vault/)
      2. <cwd>/.claude/progress.md   (project has or can have a .claude/)
      3. FALLBACK_PROGRESS_PATH      (power-pack root — last resort)
    """
    if not cwd:
        return FALLBACK_PROGRESS_PATH
    try:
        cwd_path = Path(cwd)
        if not cwd_path.is_dir():
            return FALLBACK_PROGRESS_PATH
        vault_dir = cwd_path / "vault"
        if vault_dir.is_dir():
            return vault_dir / "progress.md"
        dotclaude = cwd_path / ".claude"
        try:
            dotclaude.mkdir(parents=True, exist_ok=True)
            return dotclaude / "progress.md"
        except Exception:
            return FALLBACK_PROGRESS_PATH
    except Exception:
        return FALLBACK_PROGRESS_PATH

SNAPSHOT_FLAG = "claude-ctxwd-snap-{session_id}.flag"
ADVISORY_FLAG = "claude-ctxwd-adv-{session_id}.flag"


def _import_atomic_write():
    sys.path.insert(0, str(ATOMIC_WRITE_DIR))
    try:
        import atomic_write  # type: ignore
        return atomic_write
    finally:
        try:
            sys.path.remove(str(ATOMIC_WRITE_DIR))
        except ValueError:
            pass


def _read_metrics(session_id: str) -> dict | None:
    metrics_path = Path(tempfile.gettempdir()) / f"claude-ctx-{session_id}.json"
    if not metrics_path.exists():
        return None
    try:
        # utf-8-sig tolerates BOM written by PowerShell Out-File / WriteAllText
        return json.loads(metrics_path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _flag_exists(session_id: str, template: str) -> bool:
    flag = Path(tempfile.gettempdir()) / template.format(session_id=session_id)
    return flag.exists()


def _clear_flag(session_id: str, template: str) -> bool:
    """Delete a debounce flag. True when one was actually removed.

    Returning the outcome rather than None keeps "rearmed" distinguishable
    from "there was nothing to rearm" — the gate asserts on the difference.
    """
    flag = Path(tempfile.gettempdir()) / template.format(session_id=session_id)
    try:
        flag.unlink()
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False


def _set_flag(session_id: str, template: str) -> None:
    flag = Path(tempfile.gettempdir()) / template.format(session_id=session_id)
    try:
        flag.write_text("1", encoding="utf-8")
    except Exception:
        pass


def _append_progress_md(atomic_write, session_id: str, used_pct: float, remaining_pct, cwd: str, transcript_path: str) -> None:
    """Append a markdown section for this session to the per-project progress.md (BL-0043)."""
    target = _resolve_progress_path(cwd)
    now = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
    section = (
        f"\n## {now} — session {session_id[:8]}\n"
        f"- used: **{used_pct}%** | remaining: {remaining_pct}%\n"
        f"- cwd: `{cwd}`\n"
        f"- transcript: `{transcript_path}`\n"
    )
    existing = b""
    if target.exists():
        try:
            existing = target.read_bytes()
            if existing and not existing.endswith(b"\n"):
                existing += b"\n"
        except Exception:
            existing = b""
    if not existing:
        existing = b"# progress.md\n\nRoll-up of context-watchdog snapshots (BL-0033 / BL-0043 per-project).\nAppend-only; rotate manually after `/kclear` or `/compact`.\n"
    try:
        atomic_write.atomic_write_bytes(target, existing + section.encode("utf-8"))
    except Exception:
        pass


def _ledger_row(session_id: str, metrics: dict, transcript_path: str, cwd: str, tier: str) -> dict:
    return {
        "iso_ts": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "kind": "context_snapshot",
        "tier": tier,
        "session_id": session_id,
        "used_pct": metrics.get("used_pct"),
        "remaining_pct": metrics.get("remaining_percentage"),
        "tokens_used": metrics.get("tokens_used"),
        "tokens_total": metrics.get("tokens_total"),
        "transcript_path": transcript_path,
        "cwd": cwd,
        "trigger": "stop-watchdog",
        "ledger_law_ref": "BL-0033",
        "schema_version": 2,
    }


def _kclear_equivalent(atomic_write, session_id: str, used_pct, cwd: str,
                       transcript_path: str) -> dict:
    """Tier-2 mechanical kclear-equivalent (sealed 2026-05-20, Owner 2a/3a).
    Runs INSIDE a Stop hook — no LLM available, only structural extraction.
    Writes the same artefacts as /kclear v3 would, with mechanical content:
      <cwd>/memory/project_session_handoff.md           (atomic replace)
      <cwd>/vault/knowledge_base/session_lessons.md     (atomic append)
      <cwd>/_audit_cache/insights.json                  (atomic update)
    Returns a dict of the paths actually written (None on per-file failure).
    """
    now_iso = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
    cwd_p = Path(cwd) if cwd else Path.cwd()
    paths = {"handoff": None, "lessons": None, "insights": None}

    last_user: list[str] = []
    last_assistant_summary = ""
    try:
        tp = Path(transcript_path) if transcript_path else None
        if tp and tp.is_file():
            with tp.open("rb") as fh:
                size = tp.stat().st_size
                if size > 60_000:
                    fh.seek(-60_000, 2)
                    fh.readline()
                lines = fh.read().decode("utf-8", errors="replace").splitlines()
            for ln in reversed(lines):
                if not ln.strip():
                    continue
                try:
                    e = json.loads(ln)
                except Exception:
                    continue
                t = e.get("type") or e.get("role")
                msg = e.get("message") or e
                if t == "user":
                    content = msg.get("content") if isinstance(msg, dict) else ""
                    if isinstance(content, list):
                        content = " ".join(
                            c.get("text", "") for c in content
                            if isinstance(c, dict) and c.get("type") == "text"
                        )
                    if content and len(last_user) < 5:
                        last_user.append(str(content)[:200])
                elif t == "assistant" and not last_assistant_summary:
                    content = msg.get("content") if isinstance(msg, dict) else ""
                    if isinstance(content, list):
                        for c in content:
                            if isinstance(c, dict) and c.get("type") == "text":
                                content = c.get("text", "")
                                break
                    first_line = str(content).splitlines()[0] if content else ""
                    last_assistant_summary = first_line[:400]
                if len(last_user) >= 5 and last_assistant_summary:
                    break
            last_user.reverse()
    except Exception:
        pass

    summary = (last_assistant_summary
               or f"tier-2 checkpoint at {used_pct}% — no transcript summary"
               )[:400]

    try:
        handoff_dir = cwd_p / "memory"
        handoff_dir.mkdir(parents=True, exist_ok=True)
        handoff_path = handoff_dir / "project_session_handoff.md"
        body = (
            f"# Session Handoff (auto, tier-2 kclear-equivalent)\n\n"
            f"- session_id: {session_id}\n"
            f"- ts: {now_iso}\n"
            f"- used_pct: {used_pct}\n"
            f"- cwd: {cwd}\n\n"
            f"## summary\n{summary}\n\n"
            f"## pending (last user prompts)\n"
            + ("\n".join(f"- {p}" for p in last_user)
               if last_user else "- (none extracted)")
            + f"\n\n## transcript\n`{transcript_path}`\n"
        )
        atomic_write.atomic_write_bytes(handoff_path, body.encode("utf-8"))
        paths["handoff"] = str(handoff_path)
    except Exception:
        pass

    try:
        lessons_dir = cwd_p / "vault" / "knowledge_base"
        lessons_dir.mkdir(parents=True, exist_ok=True)
        lessons_path = lessons_dir / "session_lessons.md"
        section = (
            f"\n## {now_iso} — tier-2 auto-checkpoint @ {used_pct}% "
            f"({session_id[:8]})\n{summary}\n"
        )
        existing = lessons_path.read_bytes() if lessons_path.exists() else b""
        if existing and not existing.endswith(b"\n"):
            existing += b"\n"
        atomic_write.atomic_write_bytes(lessons_path,
                                        existing + section.encode("utf-8"))
        paths["lessons"] = str(lessons_path)
    except Exception:
        pass

    try:
        ic_dir = cwd_p / "_audit_cache"
        ic_dir.mkdir(parents=True, exist_ok=True)
        ic_path = ic_dir / "insights.json"
        data: dict = {"insights": []}
        if ic_path.exists():
            try:
                loaded = json.loads(ic_path.read_text(encoding="utf-8-sig"))
                if isinstance(loaded, dict) and "insights" in loaded:
                    data = loaded
            except Exception:
                pass
        data["insights"].append({
            "ts": now_iso,
            "category": "context-watchdog",
            "title": f"tier-2 checkpoint at {used_pct}%",
            "session_id": session_id,
            "summary": summary,
            "tags": ["tier-2", "auto-checkpoint", "BL-0033"],
        })
        atomic_write.atomic_write_bytes(
            ic_path,
            json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        )
        paths["insights"] = str(ic_path)
    except Exception:
        pass

    return paths


def _dump_telemetry(atomic_write, session_id: str, used_pct, cwd: str,
                    transcript_path: str, kclear_paths: dict):
    """Empirical-evidence artefact (Owner DONE-gate 6a, 2026-05-20)."""
    now_iso = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
    cwd_p = Path(cwd) if cwd else Path.cwd()
    try:
        tel_dir = cwd_p / "vault" / "telemetry" / "context_watchdog"
        tel_dir.mkdir(parents=True, exist_ok=True)
        safe_ts = now_iso.replace(":", "-")
        tel_path = tel_dir / f"{safe_ts}_{session_id[:8]}.json"
        record = {
            "ts": now_iso,
            "session_id": session_id,
            "used_pct": used_pct,
            "cwd": cwd,
            "transcript_path": transcript_path,
            "kclear_paths": kclear_paths,
            "trigger": "tier-2-auto",
            "schema_version": 1,
        }
        atomic_write.atomic_write_bytes(
            tel_path, json.dumps(record, indent=2).encode("utf-8")
        )
        return str(tel_path)
    except Exception:
        return None


def _read_autorun_marker(session_id: str):
    """Return the autonomous-run marker for this session, or None.

    Spec vault/specs/gsd-autonomous-autocompact.md. The marker is written by
    the launcher and names the command to re-issue after a compaction, so a
    long unattended run continues instead of ending at the compact.

    The marker's contract lives in tools/gsd_autorun_marker.py and is IMPORTED,
    never re-implemented here: a second copy of validate_command() would be
    correct the day it was written and wrong the day either side moved. Fully
    fail-open -- any resolution or parse failure yields None, and tier 2 then
    behaves exactly as it did before this clause existed.
    """
    try:
        mod = _load_tool("gsd_autorun_marker")
        if mod is not None:
            return mod.read_marker(session_id)
    except Exception:
        pass
    return None


_TOOL_CACHE: dict = {}


def _load_tool(name: str):
    """Import a Power Pack tool module by file, or None. Fail-open by contract."""
    if name in _TOOL_CACHE:
        return _TOOL_CACHE[name]
    mod = None
    try:
        import importlib.util
        here = Path(__file__).resolve()
        for path in (here.parents[3] / "tools" / f"{name}.py",
                     Path.home() / ".claude" / "skills" / "claude-power-pack" / "tools"
                     / f"{name}.py"):
            if not path.is_file():
                continue
            tools_dir = str(path.parent)
            if tools_dir not in sys.path:
                sys.path.insert(0, tools_dir)
            spec = importlib.util.spec_from_file_location(f"_ctxwd_{name}", path)
            if spec is None or spec.loader is None:
                continue
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            break
    except Exception:
        mod = None
    _TOOL_CACHE[name] = mod
    return mod


def _ledger(session_id: str, event: str, **fields) -> None:
    lr = _load_tool("gsd_long_run")
    if lr is not None:
        lr.ledger_append(session_id, event, **fields)


def _resume_clause(marker) -> str:
    """The tier-2 sentence that keeps an autonomous run going, or "".

    Pure by design. The full tier-2 path writes checkpoints, drops the
    SendKeys trigger flag and spawns the daemon, so a gate cannot drive it
    without dispatching a real compaction into the Owner's session -- the
    instrument would consume the system it measures. Keeping the clause here,
    free of side effects, is what makes both poles testable: no marker returns
    the empty string, so the message stays byte-identical for an ordinary
    session, and that negative control is the pinned one.
    """
    if not marker:
        return ""
    return (
        " AN AUTONOMOUS RUN IS IN FLIGHT for this session "
        f"(phase={marker.get('phase')}). Compacting is the correct move -- do "
        "NOT wrap up and do NOT stop. After the compaction lands, your FIRST "
        "action is to re-issue the run by emitting exactly "
        f"`{marker.get('resume_command')}` as a single trailing line, so the "
        "remaining phases continue. Clear the marker with "
        "tools/gsd_autorun_marker.py --clear when the run finishes."
    )


def _observe_compaction(session_id: str, marker, event: dict) -> dict:
    """C1: did a compaction actually happen this cycle? Never raises.

    Fails CLOSED. A resume is an effect, and before 2026-09-18 this branch
    claimed "COMPACTION LANDED" from a context reading alone; a module that
    cannot be loaded is an observer that cannot observe, not a licence. Every
    non-observation is ledgered once per cycle reference, so a run that never
    resumes says why instead of going quiet.
    """
    lr = _load_tool("gsd_long_run")
    if lr is None:
        return {"state": "unobservable", "reason": "gsd_long_run unavailable"}
    try:
        ref = lr.resume_reference(session_id, marker)
        obs = dict(lr.compaction_observed(event.get("transcript_path") or "", ref))
    except Exception as exc:
        return {"state": "unobservable", "reason": f"observer error {exc.__class__.__name__}"}
    if obs.get("state") != "observed":
        try:
            seen = any(r.get("event") == "compaction_unobserved" and r.get("reference") == ref
                       for r in lr.ledger_events(session_id))
            if not seen:
                lr.ledger_append(session_id, "compaction_unobserved", reference=ref,
                                 state=obs.get("state"), reason=obs.get("reason"),
                                 latest_boundary_ts=obs.get("boundary_ts"))
        except Exception:
            pass
    return obs


def _route_for(session_id: str) -> dict:
    """Where an automated continuation for THIS session can go. Never raises.

    Captures the endpoint from this hook's own environment first (the hook is
    a child of the session's Claude process, so ORCA_PANE_KEY names its own
    terminal). Two exact providers, never a focused window:
      * "orca-exact"     -- ORCA_PANE_KEY present: continuation_transport.
      * "terminal-inbox" -- anything else: the daemon resolves the session's
        claude.exe chain and the PP Sessions extension that OWNS that terminal
        types it (commit e5ed2d3). No owner answers -> refused, not typed.
      * "manual"         -- kill switch, or the machinery could not be loaded.
    """
    if (os.environ.get("CPP_CONTINUATION_TRANSPORT") or "").lower() == "off":
        return {"route": "manual", "why": "continuation transport disabled (kill switch)"}
    ct = _load_tool("continuation_transport")
    if ct is None:
        return {"route": "manual", "why": "continuation transport unavailable"}
    try:
        ep = ct.capture_endpoint(session_id)
    except Exception as exc:
        return {"route": "manual", "why": f"endpoint capture failed ({exc.__class__.__name__})"}
    if ep.get("host") == "orca":
        return {"route": "orca-exact", "pane_key": ep.get("pane_key")}
    return {"route": "terminal-inbox",
            "legacy_foreground": os.environ.get("CPP_LEGACY_FOREGROUND_SENDKEYS") == "1"}


def _dispatch_continuation(session_id: str, kind: str, *, transcript: str, cwd: str,
                           used_pct, cid: str, expect_line=None, expect_prefix=None) -> dict:
    """C4: the ONE door for every keystroke this hook causes. Never raises.

    Before 2026-09-18 both call sites dropped a flag for a SendKeys daemon that
    typed into whichever Cursor window had focus; it typed `/d1-continue` and
    `/absw2-continue` into sessions that were not theirs. Now each route is
    exact or refuses: Orca's own terminal, or the terminal-inbox owner of the
    session's terminal (the daemon refuses by default when nobody answers; its
    foreground fallback needs CPP_LEGACY_FOREGROUND_SENDKEYS=1).
    """
    route = _route_for(session_id)
    try:
        if route["route"] == "orca-exact":
            ct = _load_tool("continuation_transport")
            ok = bool(ct and ct.spawn_delivery(session_id, kind, expect_line, expect_prefix,
                                               transcript, cid))
            _ledger(session_id, "delivery_spawned" if ok else "delivery_blocked", cid=cid,
                    kind=kind, route=route["route"], pane_key=route.get("pane_key"),
                    **({} if ok else {"outcome": "WORKER_SPAWN_FAILED"}))
            if not ok:
                route = {"route": "manual", "why": "delivery worker failed to start"}
        elif route["route"] == "terminal-inbox":
            _write_trigger_flag(_import_atomic_write(), session_id, used_pct, cwd,
                                transcript=transcript, expect_line=expect_line,
                                expect_prefix=expect_prefix)
            _spawn_daemon()
            _ledger(session_id, "delivery_inbox_requested", cid=cid, kind=kind,
                    legacy_foreground=route.get("legacy_foreground"))
        else:
            _ledger(session_id, "delivery_blocked", cid=cid, kind=kind,
                    outcome="EXACT_SESSION_ROUTING_UNSUPPORTED", why=route.get("why"))
    except Exception as exc:
        route = {"route": "manual", "why": f"dispatch error {exc.__class__.__name__}"}
    return route


def _route_sentence(route: dict, what: str) -> str:
    """Tell the model (and through it the Owner) what will actually happen."""
    if route.get("route") == "orca-exact":
        return (f"Delivery: the continuation transport will submit {what} into THIS "
                f"session's own Orca terminal (pane {route.get('pane_key')}) once this "
                "turn ends, and records a receipt only when the transcript shows it "
                "arrived. The trailing line is the visible record, not the delivery.")
    if route.get("route") == "terminal-inbox":
        tail = (" LEGACY foreground SendKeys is opted in as a fallback (manual-class)."
                if route.get("legacy_foreground") else
                " If no extension owns this terminal the request is REFUSED and "
                "ledgered -- nothing is typed into a focused window -- and the Owner "
                "submits it in this pane.")
        return (f"Delivery: the PP Sessions terminal inbox types {what} into THIS "
                "session's own terminal only if the extension that owns it accepts "
                "(no focus needed)." + tail)
    return (f"Delivery: MANUAL -- {route.get('why')}. Nothing will type {what} for you; "
            "say plainly that the run is paused until the Owner submits it in this pane.")


def _resume_dispatch_message(marker, observed=None, route=None) -> str:
    """Stop A's ask: the exact line, and nothing after it.

    Pure, so the gate can drive both poles without running the tier-2 path.
    The compaction claim names its evidence (the boundary row), and the
    delivery sentence names the route that will actually be used -- the old
    text promised an Enter that a foreground daemon delivered to other panes.
    """
    cmd = (marker or {}).get("resume_command")
    where = (observed or {}).get("boundary_ts") or "unknown"
    return (
        f"COMPACTION OBSERVED (transcript compact_boundary at {where}) — the "
        "autonomous run must re-enter itself. "
        f"End this response with a SINGLE trailing line, exactly `{cmd}`, "
        "no preface and no markdown. "
        + _route_sentence(route or {"route": "manual", "why": "route not computed"}, f"`{cmd}`")
    )


def _ram_note(free_mb, session_id: str) -> str:
    """Gap 12: a resume on a starved host is what tips it into the hang."""
    return (
        f" HOST MEMORY IS LOW ({free_mb:.0f} MB free). BEFORE the trailing line, run "
        "in the foreground: `python "
        f"{Path.home() / '.claude' / 'skills' / 'claude-power-pack' / 'tools' / 'gsd_long_run.py'}"
        f" wait-ram --timeout 600 --session {session_id}`. If it prints RAM TIMEOUT, "
        "do NOT emit the line: say so to the Owner and stop."
    )


def _halt_message(marker, reason: str) -> str:
    """Gaps 7 + 11: the run ends here, deliberately, and says why."""
    return (
        "AUTONOMOUS RUN HALTED by the resume gate — "
        f"{reason}. The marker for `{(marker or {}).get('resume_command')}` has "
        "been cleared, so nothing will re-issue the run. Do NOT re-issue it. "
        "Summarise where the run stopped (last phase finished, what is next) for "
        "the Owner and end the turn."
    )


def _request_resume(session_id: str, marker: dict, observed=None) -> dict:
    """Stop A of a resume cycle: gate it (budget, mission), then ask for the line.

    A halt clears the marker AND sets DONE, so neither this cycle nor any later
    tier-2 crossing can re-issue a run the gate stopped. If the gate module
    cannot be loaded the resume proceeds exactly as before v2 (fail-open), and
    the absence of ledger rows is what shows it.
    """
    lr = _load_tool("gsd_long_run")
    gate = {"halt": False, "reason": "gate unavailable"}
    if lr is not None:
        try:
            gate = lr.resume_gate(marker)
        except Exception as exc:
            gate = {"halt": False, "reason": f"gate error {exc.__class__.__name__}"}
    if gate.get("halt"):
        _set_flag(session_id, RESUME_DONE_FLAG)
        mk = _load_tool("gsd_autorun_marker")
        if mk is not None:
            mk.clear_marker(session_id)
        _ledger(session_id, "halted", kind=gate.get("kind"), reason=gate.get("reason"))
        return {"decision": "block", "reason": _halt_message(marker, gate.get("reason", ""))}

    _set_flag(session_id, RESUME_ARMED_FLAG)
    mk = _load_tool("gsd_autorun_marker")
    cycles = mk.bump_cycles(session_id) if mk is not None else None
    free = lr.free_ram_mb() if lr is not None else None
    low = free is not None and lr is not None and free < lr.RAM_FLOOR_MB
    _ledger(session_id, "resume_requested", cycles=cycles,
            free_mb=None if free is None else round(free), ram_low=low,
            gate=gate.get("reason"),
            boundary_ts=(observed or {}).get("boundary_ts"),
            boundary_uuid=(observed or {}).get("boundary_uuid"))
    reason = _resume_dispatch_message(marker, observed, _route_for(session_id))
    if low:
        reason += _ram_note(free, session_id)
    return {"decision": "block", "reason": reason}


def _confirm_resume(session_id: str, event: dict) -> None:
    """Record resume_confirmed once the transcript shows the command submitted."""
    try:
        marker = _read_autorun_marker(session_id)
        lr = _load_tool("gsd_long_run")
        transcript = event.get("transcript_path") or ""
        if not marker or lr is None or not transcript:
            return
        done = Path(tempfile.gettempdir()) / RESUME_DONE_FLAG.format(session_id=session_id)
        since = done.stat().st_mtime - 5
        if lr.user_issued_command_since(Path(transcript), marker.get("resume_command"), since):
            _set_flag(session_id, RESUME_CONFIRMED_FLAG)
            _ledger(session_id, "resume_confirmed", command=marker.get("resume_command"))
    except Exception:
        pass


def _write_trigger_flag(atomic_write, session_id: str, used_pct, cwd: str,
                        transcript: str = "", expect_line: str | None = None,
                        expect_prefix: str | None = None):
    """Drop the SendKeys-daemon trigger flag (Owner 1c, zero-keystroke).
    The detached PS daemon polls ~/.claude/hooks/auto-compact-trigger.flag
    and, when Cursor is focused, sends Enter to dispatch the slash command
    the model has just emitted. Honest 1-keystroke fallback when Cursor is
    not focused — daemon promotes the flag to auto-compact-pending-<sid>.flag.

    One flag PER SESSION (2026-09-18, vault/specs/autocompact-per-session-flags.md):
    the single global name let a second concurrent /cpp-gsd-long run overwrite
    or be discarded against the first, so one run never got its Enter.
    """
    now_iso = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
    try:
        flag_dir = Path.home() / ".claude" / "hooks"
        flag_dir.mkdir(parents=True, exist_ok=True)
        safe_sid = re.sub(r"[^A-Za-z0-9-]", "", str(session_id or ""))[:64] or "unknown"
        flag = flag_dir / f"auto-compact-trigger-{safe_sid}.flag"
        body = {"ts": now_iso, "session_id": session_id,
                "used_pct": used_pct, "cwd": cwd}
        # Gap 3 (spec gsd-long-run-v2.md): the daemon presses Enter only when
        # the transcript's last assistant line is what this flag expects, so a
        # sentence added after the command -- or a half-typed prompt -- is
        # never what gets submitted.
        if transcript and (expect_line or expect_prefix):
            body["transcript"] = transcript
            if expect_line:
                body["expect_line"] = expect_line
            if expect_prefix:
                body["expect_prefix"] = expect_prefix
        payload = json.dumps(body)
        atomic_write.atomic_write_bytes(flag, (payload + "\n").encode("utf-8"))
        return str(flag)
    except Exception:
        return None


def _spawn_daemon() -> bool:
    """Spawn the SendKeys daemon detached (Owner PASO 3, 2026-05-20).
    Belt+suspenders: watchdog drops the trigger flag AND launches the
    consumer immediately, instead of waiting for the next Stop to spawn it
    via the separate auto-compact-stop-launcher.ps1 hook. Daemon enforces
    its own single-flight; duplicate spawn is a no-op. Returns True on
    successful Popen, False on any failure (fail-open).
    """
    try:
        import subprocess
        daemon = Path.home() / ".claude" / "hooks" / "auto-compact-sendkeys-daemon.ps1"
        if not daemon.is_file():
            return False
        # Empirical fix (2026-05-20): a direct subprocess.Popen with
        # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
        # from inside this Python Stop hook silently NO-OPS in the
        # chained-detach context (no log file, trigger flag never consumed).
        # Verified by manual powershell spawn of the same command which DOES
        # work. Vaccine: use the textbook Windows fire-and-forget pattern
        # `cmd.exe /c start "" /B powershell ...`. The intermediate cmd exits
        # immediately; the started powershell survives independently.
        CREATE_NO_WINDOW = 0x08000000
        subprocess.Popen(
            ["cmd.exe", "/c", "start", "", "/B",
             "powershell.exe", "-NoProfile", "-WindowStyle", "Hidden",
             "-ExecutionPolicy", "Bypass", "-File", str(daemon)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=CREATE_NO_WINDOW,
        )
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Auto-Reset Orchestrator overlay (M4, 2026-06-04, BL-AUTO-RESET-001)
#   Runs the multi-proxy context_monitor (RAM via ram_guard + active-jsonl
#   bytes + turn count) BEFORE the legacy context_pct tiers. On COMPACT/
#   KCLEAR it SAVES structured work_state (task + last_commit + last_file +
#   pending) and emits a resume-injectable advisory -- strictly richer than
#   the plain context_pct advisory, so it supersedes it. The RAM probe spawns
#   PowerShell, so it is THROTTLED (every ORCH_THROTTLE_S); between checks the
#   legacy context_pct tiers still run every Stop. Fail-open: any error falls
#   through to the legacy path. _TEST_ORCH_STATE forces a state (hermetic E2E).
# ---------------------------------------------------------------------------
ORCH_THROTTLE_S = 180
ORCH_THROTTLE_FLAG = "claude-orch-{session_id}.ts"
# No-nag (2026-06-05): emit the auto-reset advisory ONCE per session, like the
# legacy tier-2 ADVISORY_FLAG. The 180s throttle still bounds the RAM probe.
ORCH_ADVISORY_FLAG = "claude-orch-adv-{session_id}.flag"


def _now_ts() -> float:
    return _dt.datetime.now(_dt.timezone.utc).timestamp()


def _orch_throttled(session_id: str) -> bool:
    flag = Path(tempfile.gettempdir()) / ORCH_THROTTLE_FLAG.format(
        session_id=session_id)
    try:
        return (_now_ts() - float(flag.read_text())) < ORCH_THROTTLE_S
    except Exception:
        return False


def _orch_stamp(session_id: str) -> None:
    flag = Path(tempfile.gettempdir()) / ORCH_THROTTLE_FLAG.format(
        session_id=session_id)
    try:
        flag.write_text(str(_now_ts()), encoding="utf-8")
    except Exception:
        pass


def _orchestrator_overlay(event: dict) -> dict | None:
    """Return a Stop {systemMessage: advisory} dict when the orchestrator
    fires, else None (fall through to the legacy context_pct tiers). Never
    raises.

    Softened 2026-06-05 (BL-AUTO-RESET): non-blocking + once-per-session.
    Previously returned decision:block, which the harness renders as a "Stop
    hook error" and which re-invokes the model every throttle window. Now it
    surfaces a single non-blocking systemMessage; the Owner runs /kclear or
    /compact at will. The work-state is still saved (accurate resume)."""
    session_id = event.get("session_id")
    if not session_id:
        return None
    cwd = event.get("cwd") or os.getcwd()
    forced = os.environ.get("_TEST_ORCH_STATE")

    # GUARDS BEFORE THE IMPORT (2026-09-19). They used to sit BELOW it, so a
    # throttled or already-advised Stop still paid `sys.path.insert` plus the
    # auto_reset_orchestrator import chain -- work standing in front of its own
    # guard, on every Stop, forever, including long after the once-per-session
    # advisory had fired. Measured from logs/context-watchdog.log across 256
    # real rows (synthetic gsdac-/gsdlr- drivers and the 09-16..09-18 dark
    # window excluded): ordinary `pass` Stops ran a median 1,555 ms against
    # `block`'s 233 ms, 92 of them multi-second with no crossing to justify the
    # cost. Hoisting cannot change WHEN the overlay fires: `forced` still
    # bypasses both guards, the stamp still precedes orchestrate(), and an
    # import failure still returns None without stamping. It only stops the
    # import from running when the answer is already None. Line 854 was the
    # file's only `sys.path.insert(0, ROOT)` and 855 its only `from modules.`
    # import, so skipping them removes no dependency for later code.
    # Pinned by tools/test_context_watchdog_overlay_guard.py (count-based: it
    # asserts on sys.modules, never on a clock, so it is valid on a host with
    # no memory headroom).
    if not forced:
        if _orch_throttled(session_id):
            return None
        # No-nag: emit the advisory ONCE per session, not every window.
        if _flag_exists(session_id, ORCH_ADVISORY_FLAG):
            return None

    try:
        sys.path.insert(0, str(ROOT))
        from modules.cpc_os.auto_reset_orchestrator import orchestrate
    except Exception:
        return None

    try:
        if forced:
            def _assess(_c, _s):
                return {"state": forced, "tripped": ["_TEST_ORCH_STATE"],
                        "signals": {}}
            result = orchestrate(cwd, session_id, assess_fn=_assess)
        else:
            _orch_stamp(session_id)
            result = orchestrate(cwd, session_id)
    except Exception:
        return None

    if result.get("action") in ("compact", "kclear"):
        if not forced:
            _set_flag(session_id, ORCH_ADVISORY_FLAG)
        # Non-blocking advisory. Stop schema accepts `systemMessage` (NOT
        # hookSpecificOutput.additionalContext -- that is gated to
        # UPS/PostToolUse; verified hook-dispatcher.js:275). systemMessage
        # surfaces the advisory to the Owner WITHOUT blocking the stop, WITHOUT
        # the "Stop hook error" framing, and WITHOUT re-invoking the model.
        return {"systemMessage": result["advisory"]}
    return None


HEARTBEAT_LOG = Path.home() / ".claude" / "logs" / "context-watchdog.log"
_LAST = {}


def _heartbeat(session_id, outcome: str, ms: float) -> None:
    """One line per JUDGEMENT, not per block. Never raises.

    WHY THIS EXISTS. Before it, this hook wrote nothing anywhere -- no log, no
    counter, no state file it did not also consume. So "did the auto-compact
    chain run?" was unanswerable from outside, which is the same observable as
    "it ran and decided not to fire" AND the same observable as "the dispatcher
    killed it at its timeout and discarded its stdout". Three states, one
    appearance, and the third is the one that silently cancels a multi-hour
    unattended run (rules/guard-event-reachability.md).

    MEASURED 2026-09-16, and this is why the line is worth its cost: a real
    tier-2 crossing takes a median 4026 ms (3987 / 4026 / 4635) of a 6000 ms
    budget -- 67% -- with the daemon spawn EXCLUDED and the host at a
    comparatively idle 2781 MB free. This dispatcher's own notes record hooks
    with 4x headroom dying under Stop-chain fan-out; this one has 1.5x. When it
    loses that race the compaction simply does not happen, and without this line
    nothing anywhere says so.

    Records EVERY outcome so a run of `pass` lines with no `block` at a known
    crossing is itself readable evidence, and so a gap in the timestamps names
    the turns where the hook never reported at all.
    """
    try:
        import datetime
        HEARTBEAT_LOG.parent.mkdir(parents=True, exist_ok=True)
        pct = _LAST.get("used_pct")
        with open(HEARTBEAT_LOG, "a", encoding="utf-8") as fh:
            fh.write(
                f"{datetime.datetime.now(datetime.timezone.utc).isoformat()}"
                f" session={session_id}"
                f" used_pct={'?' if pct is None else f'{pct:.1f}'}"
                f" outcome={outcome}"
                f" ms={ms:.0f}\n"
            )
    except Exception:
        pass


def run(event: dict) -> dict:
    """Heartbeat wrapper. The judgement itself is `_run_inner`.

    A wrapper rather than a line at each exit because `_run_inner` returns from
    eight places and the ones that matter most are the early ones -- a missing
    session id, absent metrics, a non-numeric percentage. Those are exactly the
    silent no-ops that need to be visible, and they are exactly the ones a
    hand-placed log line gets left out of.
    """
    import time as _time
    t0 = _time.perf_counter()
    _LAST.clear()
    outcome = "error"
    try:
        out = _run_inner(event) or {}
        outcome = out.get("decision") or "pass"
        return out
    finally:
        _heartbeat(event.get("session_id"), outcome,
                   (_time.perf_counter() - t0) * 1000.0)


def _run_inner(event: dict) -> dict:
    session_id = event.get("session_id")
    if not session_id:
        return {}

    # Auto-Reset Orchestrator overlay (M4): multi-proxy RAM/jsonl/turns check
    # that saves work_state + emits a resume-injectable advisory. Runs first;
    # supersedes the plain context_pct advisory. Throttled + fail-open.
    try:
        overlay = _orchestrator_overlay(event)
        if overlay:
            return overlay
    except Exception:
        pass

    # Empirical-test override (Owner DONE-gate 6a, 2026-05-20):
    # `_TEST_CONTEXT_PCT=<n>` forces a used_pct value so a synthetic Stop
    # payload can exercise the full Tier-2 chain end-to-end without needing
    # a live session to be near 70%. Bypasses the /tmp metrics file.
    test_pct = os.environ.get("_TEST_CONTEXT_PCT")
    if test_pct:
        try:
            forced = float(test_pct)
            metrics = {
                "used_pct": forced,
                "remaining_percentage": max(0.0, 100.0 - forced),
                "tokens_used": None,
                "tokens_total": None,
            }
        except ValueError:
            metrics = _read_metrics(session_id)
    else:
        metrics = _read_metrics(session_id)
    if not metrics:
        return {}

    used_pct = metrics.get("used_pct")
    if not isinstance(used_pct, (int, float)):
        return {}
    # Stashed for the heartbeat. Without the percentage the line can say the
    # hook ran and not whether it SHOULD have fired, which is half an answer:
    # a `pass` at 74% and a `pass` at 12% are different facts about this chain.
    _LAST["used_pct"] = float(used_pct)

    # C2: an autonomous run's endpoint is refreshed on EVERY Stop, from this
    # hook's own env, so the stall sweep (which runs outside the session) and a
    # replaced worker always resolve the session's CURRENT terminal.
    if _read_autorun_marker(session_id):
        _route_for(session_id)

    # Rearm (spec gsd-autonomous-autocompact.md, gap B). MUST run before the
    # snapshot-threshold return below: a post-compaction reading is by
    # definition under that floor, so a rearm placed after it could never fire
    # and tier 2 would stay debounced for the rest of the session, which is
    # exactly the single-cycle behaviour this closes.
    # Gap 1 (spec gsd-long-run-v2.md): an Enter that was pressed is not a
    # resume that happened. Confirm it from the transcript, once per cycle.
    # Placed before every early return: the resumed turn's Stop may land at
    # any context level.
    if _flag_exists(session_id, RESUME_DONE_FLAG) \
            and not _flag_exists(session_id, RESUME_CONFIRMED_FLAG):
        _confirm_resume(session_id, event)

    snap_pct, adv_pct, rearm_pct = _thresholds(session_id)
    if used_pct < rearm_pct:
        _clear_flag(session_id, ADVISORY_FLAG)

        # Post-compaction resume (gap C). Same low-context window as the rearm,
        # and it must sit here for the same reason: below the snapshot floor.
        # Gated on a marker the Owner's launcher wrote, so an ordinary session
        # never enters this branch at all.
        if not _flag_exists(session_id, RESUME_DONE_FLAG):
            marker = _read_autorun_marker(session_id)
            if marker:
                if not _flag_exists(session_id, RESUME_ARMED_FLAG):
                    # C1 (spec exact-target-continuation.md): a low reading is
                    # not a compaction -- a restarted session reads ~17% too.
                    # Only a transcript boundary newer than this cycle licenses
                    # a resume, and "could not observe" refuses.
                    observed = _observe_compaction(session_id, marker, event)
                    if observed.get("state") != "observed":
                        return {}
                    return _request_resume(session_id, marker, observed)
                # The turn that carried the line has ended: dispatch it. Marked
                # done FIRST -- a failure past this point must not leave the
                # branch re-entrant, or every later Stop dispatches again.
                # C4: through the one door, to this session's own terminal or
                # to nobody; `resume_dispatched` now names the route taken.
                _set_flag(session_id, RESUME_DONE_FLAG)
                route = _dispatch_continuation(
                    session_id, "resume",
                    transcript=event.get("transcript_path") or "",
                    cwd=event.get("cwd") or os.getcwd(), used_pct=used_pct,
                    cid=f"{session_id}:resume:{marker.get('cycles')}",
                    expect_line=marker.get("resume_command"))
                _ledger(session_id, "resume_dispatched",
                        command=marker.get("resume_command"), route=route.get("route"),
                        why=route.get("why"))
                return {}

    if used_pct < snap_pct:
        return {}

    try:
        atomic_write = _import_atomic_write()
    except Exception:
        return {}

    transcript_path = event.get("transcript_path") or ""
    cwd = event.get("cwd") or os.getcwd()

    # Tier 1 (>= 60%) — snapshot, once per session
    if not _flag_exists(session_id, SNAPSHOT_FLAG):
        try:
            atomic_write.atomic_append_jsonl(LEDGER_PATH, _ledger_row(session_id, metrics, transcript_path, cwd, "snapshot"))
            _append_progress_md(atomic_write, session_id, used_pct, metrics.get("remaining_percentage"), cwd, transcript_path)
            _set_flag(session_id, SNAPSHOT_FLAG)
        except Exception:
            pass

    # Tier 2 (>= 70%) — kclear-equivalent + zero-keystroke compact dispatch
    if used_pct >= adv_pct and not _flag_exists(session_id, ADVISORY_FLAG):
        try:
            atomic_write.atomic_append_jsonl(LEDGER_PATH, _ledger_row(session_id, metrics, transcript_path, cwd, "advisory"))
            _set_flag(session_id, ADVISORY_FLAG)
            # A new compaction cycle begins: re-arm the resume machine, or the
            # run resumes once and every later crossing leaves it stranded.
            _clear_flag(session_id, RESUME_ARMED_FLAG)
            _clear_flag(session_id, RESUME_DONE_FLAG)
            _clear_flag(session_id, RESUME_CONFIRMED_FLAG)
        except Exception:
            pass

        crossing_marker = _read_autorun_marker(session_id)
        if crossing_marker:
            _ledger(session_id, "crossing", used_pct=used_pct,
                    cycles=crossing_marker.get("cycles"))

        # 1. Save vault BEFORE compact (Owner 2a: save then free).
        kclear_paths = _kclear_equivalent(atomic_write, session_id, used_pct,
                                          cwd, transcript_path)
        # 2. Empirical-evidence telemetry (Owner DONE-gate 6a).
        tel_path = _dump_telemetry(atomic_write, session_id, used_pct, cwd,
                                   transcript_path, kclear_paths)
        # 3. Compact dispatch (C4, spec exact-target-continuation.md). The
        #    transport waits for this turn to end, reads the model's own
        #    trailing `/compact ...` line, and submits it into THIS session's
        #    Orca terminal. No exact route -> manual, never the focused window.
        compact_route = _dispatch_continuation(
            session_id, "compact", transcript=transcript_path, cwd=cwd,
            used_pct=used_pct, cid=f"{session_id}:compact:{int(_now_ts())}",
            expect_prefix="/compact")

        # Autonomous-run awareness (spec gsd-autonomous-autocompact.md, gap C).
        # Without a marker this is the empty string and the message below is
        # byte-identical to what it has always been -- the negative control the
        # gate pins, so an ordinary session cannot be changed by this clause.
        resume_clause = _resume_clause(_read_autorun_marker(session_id))

        message = (
            f"CONTEXT THRESHOLD CROSSED — {used_pct}% used (>= {adv_pct:g}%). "
            f"Pre-compact vault checkpoint WRITTEN by tier-2 kclear-equivalent: "
            f"handoff={kclear_paths.get('handoff')}; "
            f"lessons={kclear_paths.get('lessons')}; "
            f"insights={kclear_paths.get('insights')}; "
            f"telemetry={tel_path}. "
            + _route_sentence(compact_route, "your trailing `/compact ...` line") + " "
            "End your next response with a SINGLE trailing line — exactly "
            "`/compact focus on <5-12 word current-task summary>` — no preface, "
            "no markdown. Per BL-0003 the model itself cannot auto-dispatch the "
            "slash command; emitting the pre-filled line is the model's "
            "contribution to the chain. vault/progress.md remains the resume "
            "anchor if compact is interrupted." + resume_clause
        )
        # decision="block" + reason re-invokes the model with reason as injected
        # context — the BL-0033 mechanism; Stop schema forbids
        # hookSpecificOutput.additionalContext here.
        return {
            "decision": "block",
            "reason": message,
        }

    return {}


def main() -> int:
    try:
        raw = sys.stdin.read()
        event = json.loads(raw) if raw.strip() else {}
    except Exception:
        event = {}
    try:
        out = run(event) or {}
    except Exception:
        out = {}
    try:
        sys.stdout.write(json.dumps(out))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
