"""Parse the hard-rule corpora into Rule records.

Two corpora, three shapes. The global archive
(~/.claude/knowledge_vault/core/HARD-RULES.md) carries both a fielded
form (TRIGGER/ACCION/EXCEPCION/ORIGEN) and an older imperative-prose
form ('### HR-4 -- Never write vault files with cat >> file <<EOF').
The PP archive (vault/hard_rules/HARD_RULES.md) uses
TRIGGER/STOP/EVIDENCE/SEVERITY.

Field names are normalised on the way in so the gate judges one shape.
"""
from __future__ import annotations

import re
from pathlib import Path

from .schema import Form, Rule

HOME = Path.home()
GLOBAL_ARCHIVE = HOME / ".claude" / "knowledge_vault" / "core" / "HARD-RULES.md"
PP_ROOT = Path(__file__).resolve().parents[2]
PP_ARCHIVE = PP_ROOT / "vault" / "hard_rules" / "HARD_RULES.md"

# '### HR-001 -- Title' / '### HR-1 - Title' / '### HR-KARMA-AUTONOMY -- Title'
# The id may contain internal hyphens (HR-SECRET-001, HR-KARMA-AUTONOMY), so
# the separator must be surrounded by whitespace -- otherwise the id is
# truncated at its first hyphen and every body below it is mis-sliced.
_HEADING_RE = re.compile(
    r"^#{3,4}\s+(?P<id>HR-[A-Z0-9]+(?:-[A-Z0-9]+)*)"
    r"(?:\s+(?:--|—|–|-)\s+(?P<title>.+?))?\s*$",
    re.M,
)

# Accent-tolerant field names. ACCION == ACCIÓN == STOP; ORIGEN == EVIDENCE.
_FIELD_ALIASES: dict[str, str] = {
    "TRIGGER": "trigger",
    "ACCION": "stop",
    "ACCIÓN": "stop",
    "STOP": "stop",
    "ORIGEN": "evidence",
    "EVIDENCE": "evidence",
    "EXCEPCION": "exception",
    "EXCEPCIÓN": "exception",
    "EXCEPTION": "exception",
    "SEVERITY": "severity",
}
# The corpus writes fields as 'TRIGGER:', '**ACCION**:', '- ORIGEN:' and
# -- the one that bit -- 'ACCION (STOP):' with a parenthetical qualifier
# between the name and the colon. Without the optional (...) group, every
# ACCION line silently fails to match and its body is swallowed into the
# preceding TRIGGER, making ~75 well-formed rules look like stop_missing.
_FIELD_RE = re.compile(
    r"^[-*_`\s]*(" + "|".join(_FIELD_ALIASES) + r")"
    r"\s*(?:\([^)]*\))?[*_`\s]*:\s*(.*)$",
    re.I,
)


def _parse_body(body: str) -> dict[str, str]:
    """Pull TRIGGER/ACCION/... out of a rule body. Multi-line safe:
    a field owns every line until the next field name."""
    fields: dict[str, list[str]] = {}
    current: str | None = None
    for line in body.splitlines():
        m = _FIELD_RE.match(line)
        if m:
            key = _FIELD_ALIASES[m.group(1).upper()]
            current = key
            fields.setdefault(key, []).append(m.group(2))
        elif current is not None:
            fields[current].append(line)
    return {k: "\n".join(v).strip() for k, v in fields.items()}


def _strip_digest_comment(body: str) -> str:
    return re.sub(r"<!--.*?-->", "", body, flags=re.S)


def parse_archive(path: Path, source: str) -> list[Rule]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    marks = list(_HEADING_RE.finditer(text))
    rules: list[Rule] = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        raw = _strip_digest_comment(text[m.end():end]).strip()
        fields = _parse_body(raw)
        has_fielded = "trigger" in fields or "stop" in fields
        if has_fielded:
            form = Form.FIELDED
        elif raw:
            form = Form.IMPERATIVE
        else:
            form = Form.UNKNOWN
        rules.append(Rule(
            rule_id=m.group("id").strip(),
            title=(m.group("title") or "").strip(),
            form=form,
            source=source,
            trigger=fields.get("trigger", ""),
            stop=fields.get("stop", ""),
            evidence=fields.get("evidence", ""),
            exception=fields.get("exception", ""),
            severity=fields.get("severity", ""),
            body=raw,
        ))
    return rules


def load_corpus() -> list[Rule]:
    """Every hard rule the agent is nominally bound by, both archives."""
    return (
        parse_archive(GLOBAL_ARCHIVE, "global:core/HARD-RULES.md")
        + parse_archive(PP_ARCHIVE, "pp:vault/hard_rules/HARD_RULES.md")
    )
