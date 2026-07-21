"""ledger.py -- append-only JSONL Repair Transaction ledger.

Mirrors modules.decision_review.decision_record.Registry's exact append-only
discipline: O_APPEND|O_BINARY with an explicit LF (avoids Windows text-mode CRLF
compounding, feedback_windows_text_mode_compounding), fail-open on any OSError,
never raises.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LEDGER = PP_ROOT / "vault" / "craif_registry" / "transactions.jsonl"


class Ledger:
    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else DEFAULT_LEDGER

    def next_id(self) -> str:
        return f"CRAIF-{self.count() + 1:04d}"

    def count(self) -> int:
        try:
            if not self.path.exists():
                return 0
            with self.path.open("r", encoding="utf-8") as fh:
                return sum(1 for line in fh if line.strip())
        except OSError:
            return 0

    def append(self, record: dict) -> bool:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            line = json.dumps(record, ensure_ascii=False)
            flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_BINARY", 0)
            fd = os.open(str(self.path), flags, 0o644)
            try:
                os.write(fd, (line + "\n").encode("utf-8"))
            finally:
                os.close(fd)
            return True
        except (OSError, TypeError, ValueError, AttributeError):
            return False

    def load(self) -> list[dict]:
        out: list[dict] = []
        try:
            if not self.path.exists():
                return out
            with self.path.open("r", encoding="utf-8-sig") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        out.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except OSError:
            return out
        return out
