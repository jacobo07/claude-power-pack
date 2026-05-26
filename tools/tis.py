#!/usr/bin/env python3
"""Token Intelligence System (TIS) -- core logger (Capa 1).

Sealed 2026-05-26 as the regression-prevention foundation for cost
visibility. JSONL append-only at vault/token_logs/YYYY-MM-DD.jsonl;
no third-party deps; persistent per-session id at .session_id sidecar.

Reality Contract: zero placeholders, zero silenced exceptions, every
field declared and present. If `usage` from a model response is
absent, we record explicit zeros AND a `call_label` that surfaces the
gap to the analytics layer -- never invent.

Companion modules:
  - tools/tis_report.py    Capa 2 -- analytics CLI.
  - tools/tis_handoff.py   Capa 3 -- handoff summarizer.
  - tools/jit_skill_loader.py::run -- carries the @tis_log_call hook.
"""
from __future__ import annotations
import json
import os
import tempfile
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve().parent
PP_ROOT = HERE.parent
LOGS_DIR = PP_ROOT / "vault" / "token_logs"
SESSION_FILE = LOGS_DIR / ".session_id"
HANDOFF_GLOB = "handoff_*.md"


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

@dataclass
class TokenEvent:
    """Single token-accounting event.

    Fields are intentionally explicit (no defaultdicts). Each numeric
    field defaults to 0 when missing from the upstream response so
    the analytics layer can detect zero-runs as a data-quality signal
    rather than a silent gap.
    """
    session_id: str
    timestamp_iso: str
    skill_name: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    call_label: str = ""
    project: str = ""


# ---------------------------------------------------------------------------
# Session id (persistent within a session, regenerated when sidecar reset)
# ---------------------------------------------------------------------------

def get_session_id() -> str:
    """Return the active session id, persisting it across calls.

    The sidecar lives in LOGS_DIR/.session_id so multiple tools in the
    same shell session share the same id. Owner can rotate by deleting
    that file (Cold-boot pattern at M10)."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    if SESSION_FILE.exists():
        sid = SESSION_FILE.read_text(encoding="utf-8").strip()
        if sid:
            return sid
    sid = str(uuid.uuid4())[:8]
    _atomic_write_text(SESSION_FILE, sid)
    return sid


def _atomic_write_text(path: Path, text: str) -> None:
    """tempfile + os.replace per SCS C6 (no shell `cat >>`)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp",
                               dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# Append-only log (JSONL, UTC-dated)
# ---------------------------------------------------------------------------

def _log_path_for_today() -> Path:
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return LOGS_DIR / f"{date_str}.jsonl"


def append_log(event: TokenEvent) -> Path:
    """Append the event as one JSON line. Returns the file path written.

    Per SCS C10 (idempotency-by-default): callers wishing to dedup
    must check `read_log()` first; `append_log` is the primitive and
    accepts duplicates by design (so a retried call records both
    attempts -- forensic signal, not noise)."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = _log_path_for_today()
    payload = json.dumps(asdict(event), ensure_ascii=False)
    with open(log_file, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(payload + "\n")
    return log_file


def read_log(
    since_date: Optional[str] = None,
    session_id: Optional[str] = None,
) -> list[dict]:
    """Read all entries, optionally filtered by date or session.

    `since_date` filters by the YYYY-MM-DD stem of the log file
    (inclusive). `session_id` filters by exact match on the event's
    `session_id` field. Errors-per-line are skipped silently so a
    single bad line does not poison the whole read; the count of
    skipped lines is NOT logged (this is the read path, not a
    writer). Callers needing strict parsing should call
    `iter_log_strict()` instead."""
    if not LOGS_DIR.is_dir():
        return []
    entries = []
    for fp in sorted(LOGS_DIR.glob("*.jsonl")):
        if since_date and fp.stem < since_date:
            continue
        try:
            for line in fp.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if session_id and obj.get("session_id") != session_id:
                    continue
                entries.append(obj)
        except OSError:
            continue
    return entries


def iter_log_strict():
    """Yield each entry with the source file path. Raises on malformed
    JSON so the caller can decide treatment. Used by tests that need
    to assert data quality, not just compute aggregates."""
    if not LOGS_DIR.is_dir():
        return
    for fp in sorted(LOGS_DIR.glob("*.jsonl")):
        for ln, line in enumerate(fp.read_text(encoding="utf-8").splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            yield fp, ln, json.loads(line)


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------

__all__ = [
    "TokenEvent", "append_log", "read_log", "iter_log_strict",
    "get_session_id", "LOGS_DIR", "SESSION_FILE",
]


if __name__ == "__main__":
    # Sanity probe -- M1 done-gate. Writes one synthetic event with
    # input_tokens=100 and reads it back to prove the round-trip.
    sid = get_session_id()
    ev = TokenEvent(
        session_id=sid,
        timestamp_iso=datetime.now(timezone.utc).isoformat(),
        skill_name="tis-self-probe",
        model="claude-sonnet-4-6",
        input_tokens=100, output_tokens=50,
        cache_read_tokens=0, cache_creation_tokens=0,
        call_label="M1-cli-probe",
        project="claude-power-pack",
    )
    path = append_log(ev)
    entries = read_log(session_id=sid)
    last = entries[-1] if entries else None
    assert last is not None, "no entries read back -- log path mismatch"
    assert last["input_tokens"] == 100, "round-trip lost input_tokens"
    print(f"M1 PASS log={path} entries_for_session={len(entries)} "
          f"last_input_tokens={last['input_tokens']}")
