"""OSA dispatcher: decide whether to activate, why, and against
which project.

Triggers (evaluated in order, first hit wins):
  T1_POST_DEPLOY    -- vault/deploys/*.{json,md} newer than 5 min
  T2_POST_ROLLBACK  -- vault/rollbacks/*.{json,md} newer than 5 min
  T3_ERROR_CLUSTER  -- >=N distinct (category|subsystem) CEPS events
                       since session start (N from config.triggers)
  T4_SESSION_TIMER  -- session uptime >= configured minutes
  T5_MANUAL         -- never fires from --check, only via --force

Project resolution: cwd basename matched against the keys of
modules/omnicapture/config.json::project_mapping. Falls back to
the cwd basename verbatim if no match.

CEPS subscription: read tail of vault/ceps/events.jsonl filtered
by timestamp >= session_start. Zero new pub/sub infrastructure.

Sealed 2026-05-28.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

PP_ROOT = Path(__file__).resolve().parents[2]
OMNI_CFG = PP_ROOT / "modules" / "omnicapture" / "config.json"
OSA_CFG = PP_ROOT / "vault" / "osa" / "config.json"
CEPS_EVENTS = PP_ROOT / "vault" / "ceps" / "events.jsonl"
DEPLOYS_DIR = PP_ROOT / "vault" / "deploys"
ROLLBACKS_DIR = PP_ROOT / "vault" / "rollbacks"
SESSION_ID_FILE = PP_ROOT / "vault" / "token_logs" / ".session_id"

RECEIPT_WINDOW_SEC = 5 * 60

DEFAULT_TRIGGERS = {
    "T3_error_cluster_threshold": 3,
    "T4_session_timer_minutes": 120,
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _load_trigger_config() -> dict:
    if not OSA_CFG.is_file():
        return dict(DEFAULT_TRIGGERS)
    try:
        data = json.loads(OSA_CFG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return dict(DEFAULT_TRIGGERS)
    sec = data.get("triggers") if isinstance(data, dict) else None
    if not isinstance(sec, dict):
        return dict(DEFAULT_TRIGGERS)
    merged = dict(DEFAULT_TRIGGERS)
    for k in DEFAULT_TRIGGERS:
        v = sec.get(k)
        if isinstance(v, int) and v > 0:
            merged[k] = v
    return merged


def _resolve_project() -> str:
    """cwd basename -> omnicapture project_mapping key. Fallback: basename."""
    cwd = Path.cwd().name
    cwd_low = cwd.lower()
    if not OMNI_CFG.is_file():
        return cwd
    try:
        mapping = json.loads(
            OMNI_CFG.read_text(encoding="utf-8")
        ).get("project_mapping", {}) or {}
    except (OSError, ValueError):
        return cwd
    if not isinstance(mapping, dict):
        return cwd
    # exact basename match wins
    for proj in mapping.keys():
        if str(proj).lower() == cwd_low:
            return proj
    # substring match (cwd contains project name)
    for proj in mapping.keys():
        if str(proj).lower() in cwd_low:
            return proj
    return cwd


def _session_start_iso() -> datetime:
    """Approximate session start: mtime of token_logs/.session_id, or
    fallback to 12 hours ago (conservative upper bound)."""
    if SESSION_ID_FILE.is_file():
        try:
            return datetime.fromtimestamp(
                SESSION_ID_FILE.stat().st_mtime, tz=timezone.utc)
        except OSError:
            pass
    return _utc_now() - timedelta(hours=12)


def _session_minutes() -> int:
    return int((_utc_now() - _session_start_iso()).total_seconds() // 60)


def _recent_receipt(directory: Path) -> dict | None:
    """Return {path, age_s} for the newest file in *directory* if its
    age is below RECEIPT_WINDOW_SEC. None if dir empty / too old."""
    if not directory.is_dir():
        return None
    newest: Path | None = None
    newest_mtime = 0.0
    for child in directory.iterdir():
        if not child.is_file():
            continue
        try:
            m = child.stat().st_mtime
        except OSError:
            continue
        if m > newest_mtime:
            newest_mtime = m
            newest = child
    if newest is None:
        return None
    age = time.time() - newest_mtime
    if age > RECEIPT_WINDOW_SEC:
        return None
    return {"path": str(newest), "age_s": int(age)}


def _ceps_distinct_errors(threshold: int) -> tuple[bool, int]:
    """Count distinct (category|subsystem) CEPS events since session
    start. Returns (cluster_detected, distinct_count)."""
    if not CEPS_EVENTS.is_file():
        return False, 0
    since = _session_start_iso()
    seen: set[str] = set()
    try:
        for line in CEPS_EVENTS.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            ts_raw = ev.get("timestamp_iso") or ev.get("iso") or ""
            try:
                ts = datetime.fromisoformat(
                    str(ts_raw).replace("Z", "+00:00"))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            if ts < since:
                continue
            key = f"{ev.get('category', '?')}|{ev.get('subsystem', '?')}"
            seen.add(key)
    except OSError:
        return False, 0
    count = len(seen)
    return count >= threshold, count


def evaluate_triggers() -> dict:
    """Returns a dict describing each trigger and which (if any) fired."""
    cfg = _load_trigger_config()
    out: dict[str, Any] = {
        "T1_POST_DEPLOY": _recent_receipt(DEPLOYS_DIR),
        "T2_POST_ROLLBACK": _recent_receipt(ROLLBACKS_DIR),
    }
    cluster, n = _ceps_distinct_errors(cfg["T3_error_cluster_threshold"])
    out["T3_ERROR_CLUSTER"] = {
        "fired": cluster,
        "distinct_count": n,
        "threshold": cfg["T3_error_cluster_threshold"],
    }
    minutes = _session_minutes()
    out["T4_SESSION_TIMER"] = {
        "fired": minutes >= cfg["T4_session_timer_minutes"],
        "minutes": minutes,
        "threshold": cfg["T4_session_timer_minutes"],
    }
    out["T5_MANUAL"] = {"fired": False}
    return out


def _first_fired(triggers: dict) -> str | None:
    if triggers["T1_POST_DEPLOY"] is not None:
        return "T1_POST_DEPLOY"
    if triggers["T2_POST_ROLLBACK"] is not None:
        return "T2_POST_ROLLBACK"
    if triggers["T3_ERROR_CLUSTER"]["fired"]:
        return "T3_ERROR_CLUSTER"
    if triggers["T4_SESSION_TIMER"]["fired"]:
        return "T4_SESSION_TIMER"
    return None


def should_activate(project: str | None = None) -> tuple[bool, str, dict]:
    """Returns (active, reason, payload).

    Honors the throttle gate FIRST: BUDGET_EXHAUSTED / CACHE_HIT /
    COOLDOWN short-circuit the trigger evaluation.
    """
    try:
        from modules.osa import throttle as _throttle
    except (ImportError, ModuleNotFoundError):
        sys.path.insert(0, str(PP_ROOT))
        from modules.osa import throttle as _throttle  # type: ignore
    proj = project or _resolve_project()
    gate = _throttle.check(proj)
    if gate != "GO":
        return False, gate, {
            "project": proj,
            "budget": gate,
            "triggers_evaluated": False,
        }
    triggers = evaluate_triggers()
    fired = _first_fired(triggers)
    if fired is None:
        return False, "sleepy", {
            "project": proj,
            "budget": gate,
            "triggers": triggers,
        }
    return True, fired, {
        "project": proj,
        "budget": gate,
        "trigger": fired,
        "triggers": triggers,
    }


def run_if_warranted(project: str | None = None, force: bool = False) -> dict:
    """Entry point invoked from post-deploy/rollback/backup hooks.

    V1 contract: evaluate, decide, log -- the actual `claude -p`
    invocation is intentionally OUT of V1 scope (avoid burning
    programmatic credits in autonomous mode without explicit Owner
    sign-off). Returns a dict describing what would happen.

    force=True bypasses triggers but still respects throttle.check().
    """
    proj = project or _resolve_project()
    try:
        from modules.osa import throttle as _throttle
    except (ImportError, ModuleNotFoundError):
        sys.path.insert(0, str(PP_ROOT))
        from modules.osa import throttle as _throttle  # type: ignore
    if force:
        gate = _throttle.check(proj)
        if gate != "GO":
            return {"status": "blocked", "project": proj, "budget": gate}
        return {
            "status": "would_invoke",
            "reason": "T5_MANUAL_FORCE",
            "project": proj,
            "budget": gate,
            "note": (
                "V1: dispatcher does NOT spawn claude -p autonomously. "
                "Owner runs `python -m modules.osa.osa_command --audit` "
                "to consume budget intentionally."
            ),
        }
    active, reason, payload = should_activate(proj)
    if not active:
        payload.update({"status": "sleepy"})
        return payload
    return {
        "status": "would_invoke",
        "reason": reason,
        "project": proj,
        "payload": payload,
        "note": (
            "V1: dispatcher detected a high-signal trigger. Owner "
            "runs `/osa --audit` to consume budget intentionally."
        ),
    }


def fire_async(project: str | None = None, kind: str = "post-action") -> None:
    """Fire-and-forget hook for deploy/rollback/backup callsites.

    Runs run_if_warranted() in a daemon thread. Swallows every
    exception -- a proactive auditor that blocks the action it
    audits is the same as no auditor at all.
    """
    import threading
    def _worker():
        try:
            run_if_warranted(project)
        except Exception:
            pass
    try:
        t = threading.Thread(
            target=_worker, name=f"osa-{kind}", daemon=True)
        t.start()
    except Exception:
        pass


def _main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="OSA dispatcher")
    ap.add_argument("--check", action="store_true",
                    help="Evaluate triggers; do not invoke")
    ap.add_argument("--force", action="store_true",
                    help="Override triggers (still respects throttle)")
    ap.add_argument("--project", default=None,
                    help="Override project name resolution")
    args = ap.parse_args(argv)
    if args.check or not args.force:
        active, reason, payload = should_activate(args.project)
        out = {"active": active, "reason": reason, **payload}
        print(json.dumps(out, indent=2, default=str))
        return 0
    print(json.dumps(
        run_if_warranted(args.project, force=args.force),
        indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
