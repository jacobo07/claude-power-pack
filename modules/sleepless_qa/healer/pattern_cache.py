"""
Pattern cache — consults knowledge/self-healing-patterns.md for cached fixes
before invoking the LLM healer.

Very simple signature matcher: given an error string, looks for any cached
pattern whose 'trigger' substring appears in the error. If hit, returns the
'fix_prompt' hint so the healer can apply it without a full LLM round-trip.

For now this is a lightweight reader; the real auto-apply is future work.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class CachedPattern:
    name: str
    trigger: str
    fix_hint: str


def _default_path() -> Path:
    return Path(
        "~/.claude/skills/claude-power-pack/knowledge/self-healing-patterns.md"
    ).expanduser()


def load_patterns(path: Path | None = None) -> list[CachedPattern]:
    """
    Best-effort parse of the self-healing-patterns.md markdown.

    Expected sections look like:
      ## <Name>
      **Trigger:** <string>
      **Fix:** <prompt hint>
    """
    p = path or _default_path()
    if not p.exists():
        logger.info("self-healing-patterns.md not found at %s", p)
        return []

    text = p.read_text(encoding="utf-8", errors="replace")
    patterns: list[CachedPattern] = []

    # Split on level-2 headings
    sections = re.split(r"^##\s+", text, flags=re.MULTILINE)
    for section in sections[1:]:
        lines = section.strip().splitlines()
        if not lines:
            continue
        name = lines[0].strip()
        body = "\n".join(lines[1:])
        trigger_match = re.search(r"\*\*Trigger:?\*\*\s*(.+)", body, re.IGNORECASE)
        fix_match = re.search(r"\*\*Fix:?\*\*\s*(.+)", body, re.IGNORECASE)
        if trigger_match and fix_match:
            patterns.append(CachedPattern(
                name=name,
                trigger=trigger_match.group(1).strip(),
                fix_hint=fix_match.group(1).strip(),
            ))

    logger.info("Loaded %d cached healing patterns from %s", len(patterns), p)
    return patterns


def match(error_signature: str, patterns: list[CachedPattern] | None = None) -> CachedPattern | None:
    """Return the first cached pattern whose trigger appears in the error."""
    patterns = patterns if patterns is not None else load_patterns()
    lowered = error_signature.lower()
    for pattern in patterns:
        if pattern.trigger and pattern.trigger.lower() in lowered:
            return pattern
    return None
