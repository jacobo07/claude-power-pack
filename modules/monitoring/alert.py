"""Alert emitter -- state-transition receipt writer.

When the monitor engine flips a project's status (UP <-> DOWN), this
module persists the event in two places:

  1. vault/alerts/<ISO>_<project>_<event>.md  -- durable receipt,
     same markdown shape as backup / rollback receipts.
  2. stdout (single-line tagged [ALERT] ts | project | transition)
     so a tail -f on the watch loop surfaces it in real time.

list_alerts / purge_old_alerts let observe.py read the receipt
store and enforce retention.

NO rollback dispatcher invocation here. The whole point of the
sec 10 invariant established by the Rollback Axis is that alerts
suggest, never fire. observe.py routes alerts to the Owner, full
stop.
"""

from __future__ import annotations

import datetime as _dt
import os
import re
from pathlib import Path
from typing import Any

THIS_DIR = Path(__file__).resolve().parent
PP_ROOT = THIS_DIR.parent.parent

ALERT_FILE_RE = re.compile(
    r"^(?P<ts>\d{8}T\d{6}Z)_(?P<project>[^_]+(?:_[^_]+)*?)_(?P<event>UP_TO_DOWN|DOWN_TO_UP)\.md$"
)


def _iso_compact() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _iso_readable() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _alerts_dir(repo_root: Path | None = None) -> Path:
    base = Path(repo_root) if repo_root else PP_ROOT
    return base / "vault" / "alerts"


def emit_alert(
    project: str,
    transition: str,
    evidence: str,
    config: dict[str, Any],
    repo_root: Path | None = None,
    *,
    print_stdout: bool = True,
    _now_iso: str | None = None,
) -> Path:
    """Write the receipt to disk + print a single tagged line.

    Returns the absolute path to the written markdown receipt. The
    atomic-write contract (SCS C6) is honored even though the file
    is brand-new (the receipt MUST be visible only after it is fully
    written to disk -- a partial file is worse than none).

    print_stdout defaults to True; tests pass False to keep STDOUT
    clean. _now_iso lets the V-block pin a deterministic timestamp.
    """
    adir = _alerts_dir(repo_root)
    adir.mkdir(parents=True, exist_ok=True)

    ts_compact = _now_iso or _iso_compact()
    ts_readable = (
        f"{ts_compact[0:4]}-{ts_compact[4:6]}-{ts_compact[6:8]}T"
        f"{ts_compact[9:11]}:{ts_compact[11:13]}:{ts_compact[13:15]}Z"
    ) if re.fullmatch(r"\d{8}T\d{6}Z", ts_compact) else _iso_readable()

    fname = f"{ts_compact}_{project}_{transition}.md"
    fpath = adir / fname

    interval = config.get("interval_sec", "")
    deb_f = config.get("debounce_consecutive_failures", "")
    deb_s = config.get("debounce_consecutive_successes", "")

    body = (
        f"## Alert: {project} {transition}\n\n"
        f"**Timestamp:** {ts_readable}\n"
        f"**Project:** {project}\n"
        f"**Transition:** {transition}\n"
        f"**Evidence:** {evidence}\n"
        f"**Config:** interval_sec={interval}, "
        f"debounces={deb_f}/{deb_s}\n"
        f"\n"
        f"To roll back if this is an outage: /rollback --project "
        f"{project}   (NOT auto-invoked; Owner decides)\n"
    )

    tmp = fpath.with_suffix(fpath.suffix + ".tmp")
    tmp.write_bytes(body.encode("utf-8"))
    os.replace(tmp, fpath)

    if print_stdout:
        print(
            f"[ALERT] {ts_readable} | {project:<14} | {transition:<12} | "
            f"{evidence[:80]}"
        )

    return fpath


def list_alerts(
    project: str | None = None,
    since_iso: str | None = None,
    repo_root: Path | None = None,
    *,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Glob vault/alerts/*.md, parse the timestamp + project + event
    out of each filename, optionally filter by project / since_iso,
    return newest-first.
    """
    adir = _alerts_dir(repo_root)
    if not adir.is_dir():
        return []
    entries: list[dict[str, Any]] = []
    since_compact = None
    if since_iso:
        norm = since_iso.replace("-", "").replace(":", "")
        since_compact = norm if "T" in norm and norm.endswith("Z") else None

    for f in adir.glob("*.md"):
        m = ALERT_FILE_RE.match(f.name)
        if not m:
            continue
        if project and m.group("project") != project:
            continue
        ts = m.group("ts")
        if since_compact and ts < since_compact:
            continue
        entries.append(
            {
                "path": str(f),
                "ts_compact": ts,
                "project": m.group("project"),
                "event": m.group("event"),
            }
        )

    entries.sort(key=lambda e: e["ts_compact"], reverse=True)
    if limit is not None:
        entries = entries[: int(limit)]
    return entries


def purge_old_alerts(
    retention_days: int,
    project: str | None = None,
    repo_root: Path | None = None,
    *,
    _now_compact: str | None = None,
) -> dict[str, Any]:
    """Delete any alert receipt older than retention_days. Optionally
    scoped to a project. Returns a summary {dropped, dropped_files}.

    The retention spec lives in vault/monitor/<project>.json; the
    observe layer reads that and calls this with the right value.
    """
    if retention_days <= 0:
        return {"dropped": 0, "dropped_files": []}

    adir = _alerts_dir(repo_root)
    if not adir.is_dir():
        return {"dropped": 0, "dropped_files": []}

    now = (
        _dt.datetime.strptime(_now_compact, "%Y%m%dT%H%M%SZ").replace(tzinfo=_dt.timezone.utc)
        if _now_compact
        else _dt.datetime.now(_dt.timezone.utc)
    )
    cutoff = now - _dt.timedelta(days=retention_days)

    dropped_files: list[str] = []
    for f in list(adir.glob("*.md")):
        m = ALERT_FILE_RE.match(f.name)
        if not m:
            continue
        if project and m.group("project") != project:
            continue
        ts = m.group("ts")
        try:
            ts_dt = _dt.datetime.strptime(ts, "%Y%m%dT%H%M%SZ").replace(
                tzinfo=_dt.timezone.utc
            )
        except ValueError:
            continue
        if ts_dt < cutoff:
            try:
                f.unlink()
                dropped_files.append(f.name)
            except OSError:
                continue

    return {"dropped": len(dropped_files), "dropped_files": dropped_files}
