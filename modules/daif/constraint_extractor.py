#!/usr/bin/env python3
"""DAIF-01 constraint extractor — lifts the session's binding constraints out of the estate's law.

A constraint here is a DAIF-01 Part II typed object: eight fields, every one present, unknown
spelled rather than absent (2.6). What makes a constraint HARD is one field and one field only —
Strength. DAIF-01 2.3: hard means the unit may never be silently violated and its Override-policy
defaults to no-silent-override; soft means it may be traded off under record. A process rule is
therefore not a weaker kind of object, it is the SAME object with Strength=soft, and the whole
difference in how a consumer must treat it falls out of that one field.

Provenance has no default (2.4): a constraint with no origin is a rumor, and this module refuses
to emit one. Every constraint carries the file and the line it was read from, so that the
package's claim to hold the estate's law is auditable rather than asserted.

Fail-open: an unreadable or missing source is skipped and recorded as skipped, never raised.

CLI:
  python modules/daif/constraint_extractor.py [project_path] [--out constraints.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# A sealed hard-rule block: a level-3 heading carrying a rule id and a title, followed by the
# TRIGGER / STOP / EVIDENCE / SEVERITY lines that tools/bug_to_hardrule.py writes.
HR_BLOCK_RE = re.compile(
    r"^###\s+(?P<id>(?:HR|PR|T)-[A-Z0-9\-]+)\s*--?\s*(?P<title>.+)$",
    re.IGNORECASE,
)

# DAIF-01 2.3 — the markers of a unit that may never be SILENTLY violated. Their presence is what
# promotes Strength from its safe default (soft) to hard.
HARD_MARKER_RE = re.compile(
    r"\b(?:NEVER|MUST NOT|MUST|MANDATORY|NON-NEGOTIABLE|NUNCA|PROHIBID\w*|FORBIDDEN|BANNED|"
    r"UNIVERSAL LAW|HARD RULE|inviolable|REJECTED|refuse|STOP)\b"
)

# A soft unit: tradeable under record. Counted but not carried, so the package can say how many of
# the estate's rules it left behind and why.
SOFT_MARKER_RE = re.compile(r"\b(?:prefer|default to|should|recommend\w*|advisory|when unsure)\b",
                            re.IGNORECASE)

DEFAULT_SOURCES = [
    "CLAUDE.md",
    "vault/hard_rules/HARD_RULES.md",
]

MAX_TEXT = 600           # a constraint longer than this is a section, not a rule
MIN_RULE_LEN = 16        # shorter than this is a fragment, not a statement
MIN_BODY_LEN = 12
HR_FIELD_LOOKAHEAD = 8   # TRIGGER/STOP/SEVERITY sit within this many lines of the block heading
DEDUP_KEY_LEN = 80


@dataclass
class Constraint:
    """DAIF-01 Part II — eight fields, all present, unknown spelled explicitly."""

    identifier: str
    type: str            # always 'constraint' — the closed taxonomy of DAIF-01 Part III
    text: str
    strength: str        # 'hard' | 'soft' — the field that makes a hard constraint hard
    authority: str
    scope: str
    validity: str
    override_policy: str
    provenance: str      # file:line — no default; a constraint without it is a rumor (2.4)
    confidence: str
    trigger: str = "unknown"
    stop: str = "unknown"
    severity: str = "unknown"

    def is_well_formed(self) -> bool:
        """2.7 — well-formed only when every field carries a legal value or an explicit unknown."""
        return all(bool(str(v).strip()) for v in asdict(self).values()) and \
            self.provenance != "unknown" and self.strength in ("hard", "soft")


def _cid(text: str, provenance: str) -> str:
    return "C-" + hashlib.sha256((provenance + "|" + text).encode("utf-8")).hexdigest()[:12]


def _read(path: Path) -> list[str] | None:
    try:
        return path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    except OSError:
        return None


def _dedup_key(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())[:DEDUP_KEY_LEN]


def _parse_hr_blocks(lines: list[str], rel: str, scope: str) -> list[Constraint]:
    """Sealed rule blocks. Each has an EVIDENCE line behind it — an incident, not an opinion — so
    they carry high confidence."""
    out: list[Constraint] = []
    for i, line in enumerate(lines):
        m = HR_BLOCK_RE.match(line.strip())
        if not m:
            continue
        rid, title = m.group("id").upper(), m.group("title").strip()
        trigger = stop = severity = "unknown"
        for follow in lines[i + 1:i + 1 + HR_FIELD_LOOKAHEAD]:
            s = follow.strip()
            if s.startswith("###"):
                break
            if s.upper().startswith("TRIGGER:"):
                trigger = s.split(":", 1)[1].strip()[:MAX_TEXT] or "unknown"
            elif s.upper().startswith("STOP:"):
                stop = s.split(":", 1)[1].strip()[:MAX_TEXT] or "unknown"
            elif s.upper().startswith("SEVERITY:"):
                severity = s.split(":", 1)[1].strip()[:MAX_TEXT] or "unknown"
        out.append(Constraint(
            identifier=rid,
            type="constraint",
            text=title[:MAX_TEXT],
            strength="hard",          # a sealed rule block is hard by construction
            authority="owner",
            scope=scope,
            validity="active",
            override_policy="no-silent-override",
            provenance=f"{rel}:{i + 1}",
            confidence="high",
            trigger=trigger,
            stop=stop,
            severity=severity,
        ))
    return out


def _parse_marker_rules(lines: list[str], rel: str, scope: str,
                        seen: set[str]) -> tuple[list[Constraint], int]:
    """Rules stated in prose rather than in a sealed block. A heading or bullet carrying a hard
    marker is a hard constraint; one carrying only a soft marker is a process rule — counted, not
    carried."""
    out: list[Constraint] = []
    soft = 0
    for i, raw in enumerate(lines):
        line = raw.strip()
        if not (MIN_RULE_LEN <= len(line) <= MAX_TEXT):
            continue
        if HR_BLOCK_RE.match(line):
            continue    # already carried by _parse_hr_blocks under its own sealed identifier
        is_heading = line.startswith("#")
        is_bullet = bool(re.match(r"^[-*]\s+|^\d+\.\s+", line))
        if not (is_heading or is_bullet):
            continue
        body = re.sub(r"^[#\-*\d.\s]+", "", line).strip()
        if len(body) < MIN_BODY_LEN:
            continue
        if not HARD_MARKER_RE.search(body):
            if SOFT_MARKER_RE.search(body):
                soft += 1
            continue
        key = _dedup_key(body)
        if key in seen:
            continue
        seen.add(key)
        out.append(Constraint(
            identifier=_cid(body, f"{rel}:{i + 1}"),
            type="constraint",
            text=body[:MAX_TEXT],
            strength="hard",
            authority="owner",
            scope=scope,
            validity="active",
            override_policy="no-silent-override",
            provenance=f"{rel}:{i + 1}",
            confidence="medium",     # weaker provenance than a sealed block, and it says so
        ))
    return out, soft


def extract_constraints(project_path: str | Path,
                        include_global: bool = True) -> tuple[list[Constraint], dict[str, Any]]:
    """Return (constraints, report). Hard and soft both returned; the caller selects by Strength."""
    root = Path(project_path).resolve()
    sources: list[tuple[Path, str, str]] = [(root / rel, rel, "project") for rel in DEFAULT_SOURCES]
    if include_global:
        sources.append((Path.home() / ".claude" / "CLAUDE.md", "~/.claude/CLAUDE.md", "universal"))

    constraints: list[Constraint] = []
    read_sources: list[dict[str, Any]] = []
    skipped: list[str] = []
    seen: set[str] = set()
    soft_total = 0

    for path, rel, scope in sources:
        lines = _read(path)
        if lines is None:
            skipped.append(rel)
            continue
        blocks = _parse_hr_blocks(lines, rel, scope)
        for c in blocks:
            seen.add(_dedup_key(c.text))
        marker, soft = _parse_marker_rules(lines, rel, scope, seen)
        soft_total += soft
        constraints.extend(blocks)
        constraints.extend(marker)
        read_sources.append({
            "source": rel,
            "path": str(path),
            # clause 6 of the DAIF-08 11.5 gate rests on this: a source that changed while the
            # session was down must be DETECTED, and a hash is how the far side detects it.
            "sha256": hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest(),
            "lines": len(lines),
            "sealed_blocks": len(blocks),
            "marker_rules": len(marker),
        })

    # A constraint that is not well-formed is a defect, not a weaker constraint (DAIF-01 2.7).
    malformed = [c.identifier for c in constraints if not c.is_well_formed()]
    constraints = [c for c in constraints if c.is_well_formed()]
    constraints.sort(key=lambda c: (c.strength, c.identifier))

    hard = [c for c in constraints if c.strength == "hard"]
    report = {
        "project": str(root),
        "sources_read": read_sources,
        "sources_skipped": skipped,
        "hard_constraints": len(hard),
        "sealed_rule_blocks": sum(s["sealed_blocks"] for s in read_sources),
        "process_rules_seen_not_carried": soft_total,
        "malformed_refused": len(malformed),
    }
    return constraints, report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="DAIF-01 constraint extractor")
    ap.add_argument("project", nargs="?", default=".", help="project root")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    constraints, report = extract_constraints(args.project)
    payload = {"report": report, "constraints": [asdict(c) for c in constraints]}
    if args.out:
        Path(args.out).write_text(json.dumps(payload, indent=2, ensure_ascii=False),
                                  encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    for c in constraints[:15]:
        print(f"  [{c.strength}] {c.identifier}  {c.provenance}  {c.text[:80]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
