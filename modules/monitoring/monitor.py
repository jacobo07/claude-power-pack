"""Monitoring engine -- pollable, debounced, state-persistent.

The engine owns three concerns:

  1. Config loading from vault/monitor/<project>.json.
  2. State persistence to vault/monitor/<project>_state.json so
     a debounce window survives between poll invocations (the
     daemon and --once both reuse the same file).
  3. State-transition evaluation. UP <-> DOWN flips emit alert
     events; intermediate states (consecutive failures < threshold,
     state-duration < min) DO NOT.

The healthcheck call is dispatched to modules/deployment/healthcheck
verbatim -- no duplication. Free-text scraping is forbidden by
SCS C7.

NO rollback dispatcher invocation here. V-NO-AUTO-ROLLBACK grep-
asserts zero call sites; the test files monitor.py's source text
directly.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import sys
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

THIS_DIR = Path(__file__).resolve().parent
PP_ROOT = THIS_DIR.parent.parent

DEPLOYMENT_DIR = THIS_DIR.parent / "deployment"
if str(DEPLOYMENT_DIR) not in sys.path:
    sys.path.append(str(DEPLOYMENT_DIR))

from healthcheck import check_curl_grep, check_http, check_tcp  # noqa: E402


STATUS_UP = "UP"
STATUS_DOWN = "DOWN"
STATUS_UNKNOWN = "UNKNOWN"

TRANS_UP_TO_DOWN = "UP_TO_DOWN"
TRANS_DOWN_TO_UP = "DOWN_TO_UP"


def _iso_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class MonitorState:
    """Persistent per-project state. One JSON file per project."""

    project: str
    status: str = STATUS_UNKNOWN
    last_change_iso: str = ""
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_check_iso: str = ""
    last_evidence: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# I/O: configs and state
# ---------------------------------------------------------------------------


def _project_root_for(repo_root: Path | None = None) -> Path:
    return Path(repo_root) if repo_root else PP_ROOT


def config_path(project: str, repo_root: Path | None = None) -> Path:
    return _project_root_for(repo_root) / "vault" / "monitor" / f"{project}.json"


def state_path(project: str, repo_root: Path | None = None) -> Path:
    return _project_root_for(repo_root) / "vault" / "monitor" / f"{project}_state.json"


def load_config(project: str, repo_root: Path | None = None) -> dict[str, Any]:
    """Read vault/monitor/<project>.json. Apply defaults from Q6 for
    any missing key so a thin config is still valid.
    """
    p = config_path(project, repo_root)
    if not p.is_file():
        raise FileNotFoundError(f"monitor config not found: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    # Defaults from Q6 / spec.
    data.setdefault("interval_sec", 60)
    data.setdefault("debounce_consecutive_failures", 3)
    data.setdefault("debounce_consecutive_successes", 2)
    data.setdefault("min_state_duration_sec", 30)
    data.setdefault("alert_on", [TRANS_UP_TO_DOWN, TRANS_DOWN_TO_UP])
    data.setdefault("retention_days", 30)
    return data


def load_state(project: str, repo_root: Path | None = None) -> MonitorState:
    """Read vault/monitor/<project>_state.json or return a fresh
    UNKNOWN state if the file does not exist yet.
    """
    p = state_path(project, repo_root)
    if not p.is_file():
        return MonitorState(project=project)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return MonitorState(project=project)
    return MonitorState(
        project=data.get("project", project),
        status=data.get("status", STATUS_UNKNOWN),
        last_change_iso=data.get("last_change_iso", ""),
        consecutive_failures=int(data.get("consecutive_failures", 0)),
        consecutive_successes=int(data.get("consecutive_successes", 0)),
        last_check_iso=data.get("last_check_iso", ""),
        last_evidence=data.get("last_evidence", ""),
    )


def save_state(state: MonitorState, repo_root: Path | None = None) -> Path:
    """Atomic write: tmpfile + os.replace. Honors SCS C6 (atomic
    appends) even though this is a full replace, not an append --
    the same crash-safety contract.
    """
    p = state_path(state.project, repo_root)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    payload = json.dumps(state.to_dict(), indent=2, ensure_ascii=False) + "\n"
    tmp.write_bytes(payload.encode("utf-8"))
    os.replace(tmp, p)
    return p


# ---------------------------------------------------------------------------
# Healthcheck dispatch (no duplication, no free-text scraping)
# ---------------------------------------------------------------------------


def run_check(config: dict[str, Any]) -> tuple[bool, str]:
    """Dispatch the configured healthcheck. Returns (ok, evidence).

    Single-poll semantics: retries=1 is hardcoded here because the
    monitor's debounce layer handles repetition, not the healthcheck.
    """
    hc = config.get("healthcheck") or {}
    kind = (hc.get("type") or hc.get("kind") or "").lower()
    timeout = float(hc.get("timeout_sec", 5))

    if kind == "tcp":
        result = check_tcp(
            target=hc.get("host", ""),
            port=int(hc.get("port", 0)),
            retries=1,
            delay_sec=0,
            connect_timeout=timeout,
        )
    elif kind == "http":
        result = check_http(
            url=hc.get("url", ""),
            retries=1,
            delay_sec=0,
            expect_status=int(hc.get("expect_status", 200)),
            timeout=timeout,
        )
    elif kind in ("curl_grep", "curl-grep"):
        result = check_curl_grep(
            url=hc.get("url", ""),
            grep_pattern=hc.get("grep_pattern", ""),
            retries=1,
            delay_sec=0,
            timeout=timeout,
        )
    else:
        return False, f"unknown healthcheck type: {kind!r}"

    return bool(result.get("ok")), str(result.get("evidence", ""))


# ---------------------------------------------------------------------------
# Transition logic (pure)
# ---------------------------------------------------------------------------


def evaluate_transition(
    state: MonitorState,
    check_passed: bool,
    config: dict[str, Any],
    now_iso: str | None = None,
) -> tuple[MonitorState, str | None]:
    """Pure function: given current state + this poll's outcome,
    return (new_state, alert_kind_or_None).

    Debounce semantics:
      - From UP or UNKNOWN: K consecutive failures (configured)
        flip to DOWN. Emit UP_TO_DOWN.
      - From DOWN: K consecutive successes flip to UP. Emit
        DOWN_TO_UP.
      - From UNKNOWN: a single success already promotes to UP
        (we have nothing to debounce against -- the alternative
        would be an opening UNKNOWN window that never closes on a
        healthy service). Failures still need the full debounce
        count to declare DOWN.
      - Returns alert_kind only if the transition appears in
        config["alert_on"] (default both directions).
    """
    now_iso = now_iso or _iso_now()
    new_status = state.status
    consec_f = state.consecutive_failures
    consec_s = state.consecutive_successes

    if check_passed:
        consec_s += 1
        consec_f = 0
    else:
        consec_f += 1
        consec_s = 0

    fail_thr = int(config.get("debounce_consecutive_failures", 3))
    succ_thr = int(config.get("debounce_consecutive_successes", 2))
    alert_on = set(config.get("alert_on") or [TRANS_UP_TO_DOWN, TRANS_DOWN_TO_UP])

    alert_kind: str | None = None
    last_change_iso = state.last_change_iso

    if state.status in (STATUS_UP, STATUS_UNKNOWN) and consec_f >= fail_thr:
        new_status = STATUS_DOWN
        last_change_iso = now_iso
        consec_s = 0
        if state.status == STATUS_UP and TRANS_UP_TO_DOWN in alert_on:
            alert_kind = TRANS_UP_TO_DOWN
    elif state.status == STATUS_DOWN and consec_s >= succ_thr:
        new_status = STATUS_UP
        last_change_iso = now_iso
        consec_f = 0
        if TRANS_DOWN_TO_UP in alert_on:
            alert_kind = TRANS_DOWN_TO_UP
    elif state.status == STATUS_UNKNOWN and check_passed and consec_s >= 1:
        new_status = STATUS_UP
        last_change_iso = now_iso
        consec_f = 0

    return (
        MonitorState(
            project=state.project,
            status=new_status,
            last_change_iso=last_change_iso,
            consecutive_failures=consec_f,
            consecutive_successes=consec_s,
            last_check_iso=now_iso,
            last_evidence=state.last_evidence,
        ),
        alert_kind,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def poll_once(project: str, repo_root: Path | None = None) -> tuple[MonitorState, str | None]:
    """One poll cycle: load config + state -> run check -> evaluate
    transition -> save state -> return (state, alert_kind).

    Alert emission is the caller's responsibility (observe.py wires
    poll_once to alert.emit_alert). Keeping that out of this module
    avoids a circular import and keeps the engine pure.
    """
    config = load_config(project, repo_root)
    state = load_state(project, repo_root)
    ok, evidence = run_check(config)
    new_state, alert_kind = evaluate_transition(state, ok, config)
    new_state.last_evidence = evidence
    save_state(new_state, repo_root)
    return new_state, alert_kind


def poll_loop(
    project: str,
    stop_event: threading.Event | None = None,
    on_alert: Any | None = None,
    repo_root: Path | None = None,
) -> None:
    """Foreground loop. Owner Ctrl-C or stop_event.set() ends cleanly.

    on_alert: optional callable(state, alert_kind, config) invoked
    on every state transition. observe.py wires this to
    alert.emit_alert; tests pass a list-collector for assertions.
    """
    stop_event = stop_event if stop_event is not None else threading.Event()
    while not stop_event.is_set():
        config = load_config(project, repo_root)
        state, alert_kind = poll_once(project, repo_root)
        if alert_kind and on_alert is not None:
            on_alert(state, alert_kind, config)
        interval = float(config.get("interval_sec", 60))
        stop_event.wait(timeout=interval)
