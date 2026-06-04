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
import sys
import tempfile
from pathlib import Path

# Thresholds (BL-0033)
THRESHOLD_SNAPSHOT_PCT = 60
THRESHOLD_ADVISORY_PCT = 70

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


def _write_trigger_flag(atomic_write, session_id: str, used_pct, cwd: str):
    """Drop the SendKeys-daemon trigger flag (Owner 1c, zero-keystroke).
    The detached PS daemon polls ~/.claude/hooks/auto-compact-trigger.flag
    and, when Cursor is focused, sends Enter to dispatch the slash command
    the model has just emitted. Honest 1-keystroke fallback when Cursor is
    not focused — daemon promotes the flag to auto-compact-pending.flag.
    """
    now_iso = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
    try:
        flag_dir = Path.home() / ".claude" / "hooks"
        flag_dir.mkdir(parents=True, exist_ok=True)
        flag = flag_dir / "auto-compact-trigger.flag"
        payload = json.dumps({
            "ts": now_iso, "session_id": session_id,
            "used_pct": used_pct, "cwd": cwd,
        })
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
    """Return a Stop decision:block dict when the orchestrator fires, else
    None (fall through to the legacy context_pct tiers). Never raises."""
    session_id = event.get("session_id")
    if not session_id:
        return None
    cwd = event.get("cwd") or os.getcwd()
    try:
        sys.path.insert(0, str(ROOT))
        from modules.cpc_os.auto_reset_orchestrator import orchestrate
    except Exception:
        return None

    forced = os.environ.get("_TEST_ORCH_STATE")
    try:
        if forced:
            def _assess(_c, _s):
                return {"state": forced, "tripped": ["_TEST_ORCH_STATE"],
                        "signals": {}}
            result = orchestrate(cwd, session_id, assess_fn=_assess)
        else:
            if _orch_throttled(session_id):
                return None
            _orch_stamp(session_id)
            result = orchestrate(cwd, session_id)
    except Exception:
        return None

    if result.get("action") in ("compact", "kclear"):
        # decision:block re-invokes the model with the advisory as injected
        # context -- the BL-0033 mechanism; Stop schema forbids
        # hookSpecificOutput.additionalContext here.
        return {"decision": "block", "reason": result["advisory"]}
    return None


def run(event: dict) -> dict:
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
    if not isinstance(used_pct, (int, float)) or used_pct < THRESHOLD_SNAPSHOT_PCT:
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
    if used_pct >= THRESHOLD_ADVISORY_PCT and not _flag_exists(session_id, ADVISORY_FLAG):
        try:
            atomic_write.atomic_append_jsonl(LEDGER_PATH, _ledger_row(session_id, metrics, transcript_path, cwd, "advisory"))
            _set_flag(session_id, ADVISORY_FLAG)
        except Exception:
            pass

        # 1. Save vault BEFORE compact (Owner 2a: save then free).
        kclear_paths = _kclear_equivalent(atomic_write, session_id, used_pct,
                                          cwd, transcript_path)
        # 2. Empirical-evidence telemetry (Owner DONE-gate 6a).
        tel_path = _dump_telemetry(atomic_write, session_id, used_pct, cwd,
                                   transcript_path, kclear_paths)
        # 3. SendKeys-daemon trigger flag (Owner 1c, zero-keystroke).
        flag_path = _write_trigger_flag(atomic_write, session_id, used_pct, cwd)
        # 4. Spawn the daemon immediately (belt+suspenders alongside the
        #    separate Stop-launcher hook). Detached, single-flight on the
        #    daemon side; harmless if a previous one is still running.
        daemon_spawned = _spawn_daemon()

        message = (
            f"CONTEXT THRESHOLD CROSSED — {used_pct}% used (>= 70%). "
            f"Pre-compact vault checkpoint WRITTEN by tier-2 kclear-equivalent: "
            f"handoff={kclear_paths.get('handoff')}; "
            f"lessons={kclear_paths.get('lessons')}; "
            f"insights={kclear_paths.get('insights')}; "
            f"telemetry={tel_path}. "
            f"SendKeys-daemon trigger flag DROPPED at {flag_path} — if Cursor "
            "is the focused window the daemon will press Enter for you "
            "(ZERO-keystroke); if it is not, the daemon promotes the flag to "
            "auto-compact-pending.flag and the dispatch is honest 1-keystroke. "
            "End your next response with a SINGLE trailing line — exactly "
            "`/compact focus on <5-12 word current-task summary>` — no preface, "
            "no markdown. Per BL-0003 the model itself cannot auto-dispatch the "
            "slash command; emitting the pre-filled line is the model's "
            "contribution to the chain. vault/progress.md remains the resume "
            "anchor if compact is interrupted."
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
