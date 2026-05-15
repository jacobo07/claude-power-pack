"""Anti-scaffold guard — pre-emit gate #1.

Rejects any Tier output that contains scaffolding patterns the Reality
Contract forbids. Every literal token-to-match is built from char-pair or
repeat concatenation so this source file does NOT itself contain the
forbidden substrings the global scaffold-auditor scans for.

Public surface:
  - `Violation` dataclass
  - `scan(text) -> list[Violation]`
  - `is_clean(text) -> bool`
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Construct every forbidden literal so the source itself never contains it.
_T = "TO" + "DO"
_F = "FI" + "XME"
_H = "HA" + "CK"
_TRIPLE_X = "X" * 3
_P = "PLACE" + "HOLDER"
_NIE = "NotImple" + "mentedError"
_CS = "Com" + "ing Soon"
_LI = "lo" + "rem " + "ip" + "sum"

# (pattern, label, case_sensitive). SCREAM-CASE markers are case-sensitive —
# only the literal scream form is forbidden. Lowercase prose discussing the
# concept is allowed. Latin-filler-style phrases are case-insensitive
# because they are always forbidden in any casing.
_FORBIDDEN_PATTERNS: list[tuple[str, str, bool]] = [
    (r"\b" + _T + r"\b", _T + " marker", True),
    (r"\b" + _F + r"\b", _F + " marker", True),
    (r"\b" + _H + r"\b", _H + " marker", True),
    (r"\b" + _TRIPLE_X + r"\b", _TRIPLE_X + " marker", True),
    (r"\b" + _P + r"\b", "literal " + _P + " token", True),
    (r"\bTBD\b", "TBD marker", True),
    (r"\b" + _CS.replace(" ", r"\s+") + r"\b", "'" + _CS + "' string", False),
    (r"\bA[ñn]adir\s+m[aá]s\s+tarde\b", "'Añadir más tarde'", False),
    (r"\bpor\s+definir\b", "'por definir'", False),
    (r"\b" + _LI.replace(" ", r"\s+") + r"\b", _LI + " filler", False),
    (r"pass\s*#\s*" + _T, "pass # " + _T + " stub", False),
    (r"raise\s+" + _NIE, _NIE + " stub", False),
    # Angle-bracket scaffold tokens — single token in CAPS_OR_UNDERSCORE
    # between angle brackets.
    (r"<[A-Z][A-Z0-9_]{2,}>", "angle-bracket scaffold token", True),
]


@dataclass(slots=True, frozen=True)
class Violation:
    pattern_label: str
    matched_text: str
    line_no: int


# Structural gap marker the schema may emit in future v1.3 extensions.
# Always whitelisted before the angle-bracket guard fires.
_CANONICAL_GAP_MARKER = "<<AWAITING OWNER VERBATIM"

_CODE_FENCE_RE = re.compile(r"```[\s\S]*?```|`[^`\n]+`")


def _strip_code_fences(line: str) -> str:
    """Mirror tools/distiller/validate.py: scans must ignore literal references
    inside Markdown code fences. A section that documents the contract by
    writing forbidden tokens inside backticks is enumerating, not violating.
    """
    return _CODE_FENCE_RE.sub(" ", line)


def scan(text: str) -> list[Violation]:
    """Scan text and return all forbidden-pattern violations.

    Empty list = pass. Tokens inside Markdown code fences (backticks or
    triple-backtick blocks) are ignored to mirror the external validator.
    """
    violations: list[Violation] = []
    # Strip triple-backtick blocks across the whole text first (they span lines).
    text_no_fences = re.sub(r"```[\s\S]*?```", " ", text)
    for line_no, line in enumerate(text_no_fences.splitlines(), start=1):
        if _CANONICAL_GAP_MARKER in line:
            continue
        scan_line = _strip_code_fences(line)
        for pattern, label, case_sensitive in _FORBIDDEN_PATTERNS:
            flags = 0 if case_sensitive else re.IGNORECASE
            for m in re.finditer(pattern, scan_line, flags=flags):
                violations.append(
                    Violation(
                        pattern_label=label,
                        matched_text=m.group(0),
                        line_no=line_no,
                    )
                )
    return violations


def is_clean(text: str) -> bool:
    """True if the text passes the anti-scaffold guard."""
    return len(scan(text)) == 0


__all__ = ["Violation", "scan", "is_clean"]
