"""Dangerous command registry -- BL-DATASET-BUILD M11.

Pattern set of shell / SQL / git / network commands that warrant
Cascade C4 block. Patterns are checked against a single command
string via is_dangerous / reasons.
"""
from __future__ import annotations

import re

# Each entry: (compiled pattern, short human-readable reason).
DANGEROUS_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"^\s*rm\s+-r?f+\s+/", re.IGNORECASE),
     "rm -rf on absolute path"),
    (re.compile(r"\bRemove-Item\b.*\b-Recurse\b.*\b-Force\b",
                re.IGNORECASE),
     "Remove-Item -Recurse -Force"),
    (re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", re.IGNORECASE),
     "destructive SQL DROP"),
    (re.compile(r"\bTRUNCATE\s+TABLE\b", re.IGNORECASE),
     "destructive SQL TRUNCATE"),
    (re.compile(r"\bgit\s+push\s+.*--force(?!-with-lease)",
                re.IGNORECASE),
     "git push --force without --force-with-lease"),
    (re.compile(r"\bgit\s+reset\s+--hard\b", re.IGNORECASE),
     "git reset --hard"),
    (re.compile(r"\bgit\s+clean\s+-[a-z]*fdx?", re.IGNORECASE),
     "git clean -fdx"),
    (re.compile(r":\(\)\s*\{[^}]*&\s*\}\s*;"),
     "fork bomb"),
    (re.compile(r"\bchmod\s+-R\s+777\b"),
     "chmod -R 777"),
    (re.compile(
        r"\b(curl|wget|iwr|Invoke-WebRequest)\b[^|\n]*\|\s*"
        r"(bash|sh|zsh|powershell|pwsh)\b"
    ),
     "pipe-to-shell from network"),
    (re.compile(r"\beval\s*\(", re.IGNORECASE),
     "eval() of dynamic content"),
]


def is_dangerous(command: str) -> bool:
    """Return True iff `command` matches any DANGEROUS_PATTERNS entry."""
    if not command:
        return False
    return any(pat.search(command) for pat, _ in DANGEROUS_PATTERNS)


def reasons(command: str) -> list[str]:
    """Return the list of reasons that match. Empty -> safe."""
    if not command:
        return []
    return [reason for pat, reason in DANGEROUS_PATTERNS
            if pat.search(command)]
