"""Secret detector -- 9 patterns, never logs raw values."""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Iterable


class Severity(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass(frozen=True)
class Hit:
    pattern_name: str
    severity: Severity
    line_no: int
    match_start: int
    match_end: int

    def redacted_preview(self) -> str:
        return f"[REDACTED {self.pattern_name} severity={self.severity.name}]"


# The literal character-class metasyntax ([, ], \-, _) is NOT itself
# matched by any pattern below, so this file is safe to write through
# the firewall once installed.
PATTERNS: dict[str, tuple[re.Pattern, Severity]] = {
    "anthropic_key": (
        re.compile(r"sk-ant-[A-Za-z0-9_\-]{32,}"),
        Severity.CRITICAL,
    ),
    "openai_key": (
        re.compile(r"\bsk-[A-Za-z0-9]{32,}\b"),
        Severity.CRITICAL,
    ),
    "github_pat": (
        re.compile(r"\bghp_[A-Za-z0-9]{36}\b"),
        Severity.CRITICAL,
    ),
    "aws_access_key": (
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        Severity.CRITICAL,
    ),
    "private_key": (
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
        Severity.CRITICAL,
    ),
    "connection_string": (
        re.compile(
            r"(mongodb|postgresql|postgres|mysql|redis)://"
            r"[^:\s/]+:[^@\s]{4,}@[^\s/]+"
        ),
        Severity.CRITICAL,
    ),
    "jwt_token": (
        re.compile(
            r"\beyJ[A-Za-z0-9_\-]{8,}\."
            r"[A-Za-z0-9_\-]{8,}\."
            r"[A-Za-z0-9_\-]{8,}\b"
        ),
        Severity.HIGH,
    ),
    "bearer_token": (
        re.compile(r"[Bb]earer\s+[A-Za-z0-9_\-\.~+/]{20,}=*"),
        Severity.HIGH,
    ),
    "generic_secret": (
        re.compile(
            r"(?i)\b(secret|password|api[_-]?key|access[_-]?token)"
            r"\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}['\"]?"
        ),
        Severity.MEDIUM,
    ),
}


def scan_text(text: str) -> list[Hit]:
    if not text:
        return []
    line_starts = [0]
    for i, ch in enumerate(text):
        if ch == "\n":
            line_starts.append(i + 1)

    def _line_of(offset: int) -> int:
        lo, hi = 0, len(line_starts) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if line_starts[mid] <= offset:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1

    hits: list[Hit] = []
    for name, (pat, sev) in PATTERNS.items():
        for m in pat.finditer(text):
            hits.append(
                Hit(
                    pattern_name=name,
                    severity=sev,
                    line_no=_line_of(m.start()),
                    match_start=m.start(),
                    match_end=m.end(),
                )
            )
    return hits


def scan_file(path: Path | str) -> list[Hit]:
    p = Path(path)
    try:
        return scan_text(p.read_text(encoding="utf-8", errors="replace"))
    except (FileNotFoundError, PermissionError, IsADirectoryError, OSError):
        return []


def is_critical(hits: Iterable[Hit]) -> bool:
    return any(h.severity == Severity.CRITICAL for h in hits)


def summary(hits: Iterable[Hit]) -> str:
    by_pattern: dict[str, int] = {}
    for h in hits:
        by_pattern[h.pattern_name] = by_pattern.get(h.pattern_name, 0) + 1
    if not by_pattern:
        return "no secrets detected"
    return "; ".join(f"{n}={c}" for n, c in sorted(by_pattern.items()))
