"""OSA NEVER_AGAIN injector with recurrence tracking.

Writes structured entries to:
  vault/osa/never_again_log.jsonl   (append, one JSON line per inject)
  vault/knowledge_base/session_lessons.md  (append, human-readable block)
  vault/knowledge_base/ukdl-universal.md   (append, UKDL row)

Fuzzy-match dedup: if the same issue (first 60 normalized chars)
already exists in never_again_log.jsonl, increment its recurrence
in-place instead of writing a second log entry. The markdown files
are append-only -- they record every observation, the JSONL is the
recurrence-tracked source of truth.

Sealed 2026-05-28.
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

PP_ROOT = Path(__file__).resolve().parents[2]
LOG_PATH = PP_ROOT / "vault" / "osa" / "never_again_log.jsonl"
SESSION_LESSONS = PP_ROOT / "vault" / "knowledge_base" / "session_lessons.md"
UKDL_PATH = PP_ROOT / "vault" / "knowledge_base" / "ukdl-universal.md"

VALID_SEVERITY = ("CRITICAL", "HIGH", "MEDIUM", "LOW")

_WS = re.compile(r"\s+")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z")


def _normalize_for_match(text: str) -> str:
    return _WS.sub(" ", (text or "").strip().lower())[:60]


@dataclass
class NeverAgainEntry:
    iso: str
    project: str
    issue: str
    root_cause: str
    fix: str
    recognizer: str
    severity: str = "HIGH"
    recurrence: int = 1
    tags: list[str] = field(default_factory=list)


def _read_log() -> list[dict]:
    if not LOG_PATH.is_file():
        return []
    out: list[dict] = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def _atomic_overwrite_log(rows: Iterable[dict]) -> None:
    """Replace the entire JSONL atomically. Used only when bumping
    recurrence on an existing row -- append-only writes use _append()."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=LOG_PATH.name + ".", dir=str(LOG_PATH.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, LOG_PATH)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _append_jsonl(entry: NeverAgainEntry) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(entry)) + "\n")


def _append_md(path: Path, block: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        sep = "" if existing.endswith("\n\n") else (
            "\n" if existing.endswith("\n") else "\n\n")
        path.write_text(existing + sep + block + "\n", encoding="utf-8")
    else:
        path.write_text(block + "\n", encoding="utf-8")


def _session_lessons_block(entry: NeverAgainEntry) -> str:
    return (
        f"## NEVER_AGAIN — {entry.iso} — {entry.project} — {entry.severity}\n"
        f"- **Issue**: {entry.issue}\n"
        f"- **Root cause**: {entry.root_cause}\n"
        f"- **Fix**: {entry.fix}\n"
        f"- **Recognizer**: {entry.recognizer}\n"
        f"- **Recurrence**: {entry.recurrence}\n"
    )


def _ukdl_row(entry: NeverAgainEntry) -> str:
    return (
        f"- **UKDL-OSA-{entry.iso}** [{entry.severity}] {entry.project}: "
        f"{entry.issue} -- recognizer: {entry.recognizer}"
    )


def inject(
    issue: str,
    root_cause: str,
    fix: str,
    recognizer: str,
    project: str = "global",
    severity: str = "HIGH",
    tags: list[str] | None = None,
) -> NeverAgainEntry:
    """Record a NEVER_AGAIN observation. Increments recurrence if the
    same issue (normalized first 60 chars) is already in the log."""
    if severity not in VALID_SEVERITY:
        severity = "HIGH"
    entry = NeverAgainEntry(
        iso=_utc_now_iso(),
        project=project,
        issue=(issue or "").strip(),
        root_cause=(root_cause or "").strip(),
        fix=(fix or "").strip(),
        recognizer=(recognizer or "").strip(),
        severity=severity,
        tags=list(tags or []),
    )
    if not entry.issue or not entry.root_cause or not entry.fix:
        raise ValueError("issue/root_cause/fix are mandatory")

    rows = _read_log()
    key = _normalize_for_match(entry.issue)
    matched_idx = None
    for i, row in enumerate(rows):
        if _normalize_for_match(row.get("issue", "")) == key:
            matched_idx = i
            break
    if matched_idx is not None:
        rows[matched_idx]["recurrence"] = int(
            rows[matched_idx].get("recurrence", 1)) + 1
        rows[matched_idx]["iso"] = entry.iso
        entry.recurrence = rows[matched_idx]["recurrence"]
        _atomic_overwrite_log(rows)
    else:
        _append_jsonl(entry)
    _append_md(SESSION_LESSONS, _session_lessons_block(entry))
    _append_md(UKDL_PATH, _ukdl_row(entry))
    return entry


def query(pattern: str) -> list[NeverAgainEntry]:
    """Substring search across issue/root_cause/fix/recognizer."""
    needle = (pattern or "").strip().lower()
    out: list[NeverAgainEntry] = []
    if not needle:
        return out
    for row in _read_log():
        blob = " ".join([
            row.get("issue", ""),
            row.get("root_cause", ""),
            row.get("fix", ""),
            row.get("recognizer", ""),
        ]).lower()
        if needle in blob:
            out.append(NeverAgainEntry(**{
                "iso": row.get("iso", ""),
                "project": row.get("project", "global"),
                "issue": row.get("issue", ""),
                "root_cause": row.get("root_cause", ""),
                "fix": row.get("fix", ""),
                "recognizer": row.get("recognizer", ""),
                "severity": row.get("severity", "HIGH"),
                "recurrence": int(row.get("recurrence", 1)),
                "tags": list(row.get("tags", []) or []),
            }))
    return out


def top_recurring(n: int = 5) -> list[NeverAgainEntry]:
    rows = _read_log()
    rows.sort(key=lambda r: int(r.get("recurrence", 1)), reverse=True)
    out: list[NeverAgainEntry] = []
    for row in rows[:n]:
        out.append(NeverAgainEntry(**{
            "iso": row.get("iso", ""),
            "project": row.get("project", "global"),
            "issue": row.get("issue", ""),
            "root_cause": row.get("root_cause", ""),
            "fix": row.get("fix", ""),
            "recognizer": row.get("recognizer", ""),
            "severity": row.get("severity", "HIGH"),
            "recurrence": int(row.get("recurrence", 1)),
            "tags": list(row.get("tags", []) or []),
        }))
    return out


def _main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="OSA NEVER_AGAIN log")
    ap.add_argument("--list", action="store_true",
                    help="Print top-recurring entries")
    ap.add_argument("--top", type=int, default=5,
                    help="How many entries to print with --list")
    ap.add_argument("--query", metavar="PATTERN",
                    help="Substring search")
    args = ap.parse_args(argv)
    if args.query:
        rows = query(args.query)
        print(json.dumps([asdict(r) for r in rows], indent=2))
        return 0
    rows = top_recurring(args.top)
    print(json.dumps([asdict(r) for r in rows], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
