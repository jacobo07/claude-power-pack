"""Bug -> Hard Rule extractor (Decision A3).

Reads three bug sources and surfaces candidates whose severity is
CRITICAL or whose recurrence is >= 3. Each candidate is converted
into a hard-rule body with TRIGGER / STOP / EVIDENCE fields by
`propose_hard_rule()`.

Sealed BL-HARDRULE-001 (2026-05-29).
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

PP_ROOT = Path(__file__).resolve().parents[2]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

NEVER_AGAIN_LOG = PP_ROOT / "vault" / "osa" / "never_again_log.jsonl"
UKDL_MD = PP_ROOT / "vault" / "knowledge_base" / "ukdl-universal.md"
SESSION_LESSONS_MD = PP_ROOT / "vault" / "knowledge_base" / "session_lessons.md"

Severity = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]

CRITICAL_KEYWORD_RX = re.compile(
    r"\bdata\s+loss\b|\bproduction\s+down\b|\bdrop\s+table\b|"
    r"\birreversible\b|\bcorrupt(?:ion)?\b|\bspawn[\w\s]*void\b|"
    r"\bauth[\w\s]*broken\b|\bcredentials?\s+leak\b|"
    r"\bsettings\.json\b.*\bcorrupt\b|"
    r"\bdelete[\w\s]*(?:without|no)\s+backup\b|"
    r"\bcascade\b.*\bfailure\b",
    re.IGNORECASE,
)


@dataclass
class BugCandidate:
    source: str
    issue: str
    root_cause: str
    fix: str
    recognizer: str
    severity: Severity = "HIGH"
    recurrence: int = 1
    tags: list[str] | None = None

    def qualifies_for_hard_rule(self) -> bool:
        return self.severity == "CRITICAL" or self.recurrence >= 3


def _load_never_again() -> list[BugCandidate]:
    if not NEVER_AGAIN_LOG.is_file():
        return []
    out: list[BugCandidate] = []
    for line in NEVER_AGAIN_LOG.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        out.append(BugCandidate(
            source="never_again",
            issue=str(entry.get("issue", ""))[:400],
            root_cause=str(entry.get("root_cause", ""))[:400],
            fix=str(entry.get("fix", ""))[:400],
            recognizer=str(entry.get("recognizer", ""))[:400],
            severity=str(entry.get("severity", "HIGH")).upper() or "HIGH",
            recurrence=int(entry.get("recurrence", 1) or 1),
            tags=list(entry.get("tags", []) or []),
        ))
    return out


def _scan_markdown_for_critical(path: Path,
                                source_label: str) -> list[BugCandidate]:
    if not path.is_file():
        return []
    out: list[BugCandidate] = []
    body = path.read_text(encoding="utf-8-sig")
    sections = re.split(r"\n(?=#{1,4}\s)", body)
    for section in sections:
        s = section.strip()
        if not s:
            continue
        if not CRITICAL_KEYWORD_RX.search(s):
            continue
        title_match = re.match(r"^#{1,4}\s+(.+)", s)
        title = title_match.group(1).strip()[:200] if title_match else s[:200]
        trap_match = re.search(
            r"(?:trap|issue|problem)[:\s]+(.+?)(?=(?:fix|recogniz|root[\s_-]?cause|trap|issue|problem|$))",
            s, re.IGNORECASE | re.DOTALL,
        )
        fix_match = re.search(
            r"(?:fix|prevention|solution)[:\s]+(.+?)(?=(?:trap|issue|problem|recogniz|root|$))",
            s, re.IGNORECASE | re.DOTALL,
        )
        recognize_match = re.search(
            r"(?:recogniz|early[\s_-]?warning|detect)[:\s]+(.+?)(?=(?:trap|issue|fix|root|$))",
            s, re.IGNORECASE | re.DOTALL,
        )
        out.append(BugCandidate(
            source=source_label,
            issue=title,
            root_cause=trap_match.group(1).strip()[:300] if trap_match else "",
            fix=fix_match.group(1).strip()[:300] if fix_match else "",
            recognizer=recognize_match.group(1).strip()[:300]
                if recognize_match else "",
            severity="CRITICAL",
            recurrence=1,
        ))
    return out


def load_candidates() -> list[BugCandidate]:
    """Aggregate bug candidates from the three sources.

    A3 gating is applied here: only entries with severity=CRITICAL
    or recurrence >= 3 are returned. Markdown sources are scanned
    for keyword-detected CRITICAL patterns (data loss, irreversible
    delete, auth breach, etc.) and admitted as CRITICAL candidates.
    """
    seen: set[tuple[str, str]] = set()
    out: list[BugCandidate] = []
    for cand in _load_never_again():
        if not cand.qualifies_for_hard_rule():
            continue
        key = (cand.source, cand.issue[:80])
        if key in seen:
            continue
        seen.add(key)
        out.append(cand)
    for cand in _scan_markdown_for_critical(UKDL_MD, "ukdl"):
        key = (cand.source, cand.issue[:80])
        if key in seen:
            continue
        seen.add(key)
        out.append(cand)
    for cand in _scan_markdown_for_critical(
            SESSION_LESSONS_MD, "session_lessons"):
        key = (cand.source, cand.issue[:80])
        if key in seen:
            continue
        seen.add(key)
        out.append(cand)
    return out


def _extract_trigger(bug: BugCandidate) -> str:
    issue_lower = bug.issue.lower()
    rules = [
        (("delet", "drop", "clear", "borr"),
         "Before deleting, dropping, or clearing any persistent data, "
         "file, or database entry"),
        (("backup", "settings.json"),
         "Before writing any file under ~/.claude/ or any agent-owned "
         "global config"),
        (("auth", "login", "token", "credentials", "secret"),
         "Before writing, committing, or deploying any auth or "
         "credential-related code"),
        (("deploy", "release", "production", "vercel", "kubectl"),
         "Before initiating any production deploy or release"),
        (("cascade", "chain error", "downstream"),
         "Before taking an action whose failure could cascade to "
         "other components"),
        (("spawn", "fork", "subprocess"),
         "Before spawning a long-running subprocess, daemon, or "
         "background worker"),
        (("classifier",),
         "Before issuing any tool call that mutates files under "
         "~/.claude/ or other classifier-protected paths"),
        (("pytest", "test_"),
         "Before adding a `def test_*` to a tests/ file that itself "
         "spawns `pytest tests/`"),
    ]
    for keywords, trigger in rules:
        if any(kw in issue_lower for kw in keywords):
            return trigger
    if bug.recognizer:
        return bug.recognizer[:160]
    return f"Before: {bug.issue[:140]}"


def _extract_stop_action(bug: BugCandidate) -> str:
    if bug.fix:
        return bug.fix[:240]
    return ("STOP. Verify preconditions in writing. Document what you "
            "are about to do. Get explicit confirmation if any step "
            "is irreversible.")


def _title(issue: str) -> str:
    words = re.split(r"\s+", issue.strip())[:6]
    cleaned = [re.sub(r"[^A-Za-z0-9-]", "", w) for w in words if w.strip()]
    cleaned = [c for c in cleaned if c]
    return " ".join(c.capitalize() for c in cleaned)[:80] or "Unnamed Rule"


def propose_hard_rule(bug: BugCandidate, rule_id: str) -> str:
    """Render a hard rule block from a bug candidate."""
    trigger = _extract_trigger(bug)
    stop_action = _extract_stop_action(bug)
    title = _title(bug.issue)
    evidence = f"[{bug.source}] {bug.issue[:180]}"
    return (
        f"### {rule_id} -- {title}\n"
        f"TRIGGER: {trigger}\n"
        f"STOP: {stop_action}\n"
        f"EVIDENCE: {evidence}\n"
        f"SEVERITY: {bug.severity} | RECURRENCE: {bug.recurrence}x\n"
    )


__all__ = [
    "BugCandidate",
    "load_candidates",
    "propose_hard_rule",
    "_extract_trigger",
    "_extract_stop_action",
]
