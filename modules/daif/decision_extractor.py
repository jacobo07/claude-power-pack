#!/usr/bin/env python3
"""DAIF-08 Part XI decision extractor — lifts decisions WITH their justification out of a
real session transcript, for the resume pack's `decisions_with_justifications` slot (11.3).

11.3 is explicit that a decision carried without its reason is worse than not carrying it at
all: the resumed actor will either violate it as arbitrary or obey it as inscrutable. Before
this module, the slot was declared `unknown` because no extractor existed (see
session_continuity_compiler.py's prior docstring). This is that extractor.

Same positioning as obligation_extractor.py, honestly stated: this is ARCHAEOLOGY, not
capture-at-creation. It runs over conversational residue and recovers the sentence, not always
the full deliberation. Every decision it produces carries intake='archaeology' so no consumer
mistakes it for a formally-reviewed DRK DecisionRecord (modules/decision_review/). Where a
formal DRK record exists for the same session window, that record is authoritative and this
extractor's finding is marked superseded rather than duplicated -- composing DRK rather than
forking its schema (DAIF_RESUMPTION.md decision 1: "never fork ... decision verdicts (DRK)").

Fail-open: an unparseable line, an unreadable file, or a turn with an unexpected shape is
skipped, never raised.

CLI:
  python modules/daif/decision_extractor.py <session.jsonl> [--project .] [--out report.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# Decision markers, English + Spanish, each capturing (chosen, rationale). A decision sentence
# names WHAT was chosen and WHY in the same breath -- that is exactly the pair 11.3 requires,
# and a sentence that names one without the other is not a decision this extractor can carry.
DECISION_PATTERNS: list[re.Pattern] = [
    re.compile(
        r"\b(?:decided|chose|opted|went with|settled on)\s+(?:to\s+|for\s+)?(?P<chosen>.+?)"
        r"\s+(?:because|since|as)\s+(?P<rationale>.+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:the (?:right|correct) call|the (?:better|best) (?:option|choice|approach) )"
        r"is\s+(?P<chosen>.+?)\s+(?:because|since)\s+(?P<rationale>.+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bI'?ll\s+go\s+with\s+(?P<chosen>.+?)\s+(?:because|since|rather than)\s+(?P<rationale>.+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:decid(?:í|i)|opt(?:é|e) por|me qued(?:o|é) con)\s+(?P<chosen>.+?)"
        r"\s+(?:porque|ya que|dado que)\s+(?P<rationale>.+)",
        re.IGNORECASE,
    ),
]

# A decision about the CORPUS describing what a decision sentence looks like is not itself a
# decision -- the same false-positive class WISH_RE guards against in obligation_extractor, here
# guarding against meta-discussion of the pattern rather than an instance of it.
META_RE = re.compile(
    r"\b(?:pattern|regex|extractor|heuristic|example sentence|for instance,? the (?:phrase|pattern))\b",
    re.IGNORECASE,
)

MIN_CHOSEN_WORDS = 2
MIN_RATIONALE_WORDS = 3
MAX_FIELD_CHARS = 400
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?;:\n])\s+")

# Recognizable file-path tokens inside chosen/rationale text -- used by the compiler's
# referenced_files existence check, not scanned here, but the pattern is shared so both
# modules recognize the same shape.
_PATH_TOKEN_RE = re.compile(
    r"\b[\w./\\-]+\.(?:py|js|ts|tsx|jsx|json|md|txt|yml|yaml|toml|cfg|ini|ps1|sh)\b"
)


@dataclass
class Decision:
    """A decision with its justification, archaeology-sourced (DAIF-08 11.3)."""

    identifier: str
    chosen: str
    rationale: str
    origin: str                       # session + turn it arose from
    source: list[str]                 # exact pointers; de-dup keeps ALL of them
    referenced_files: list[str] = field(default_factory=list)
    intake: str = "archaeology"       # never 'drk-reviewed' unless matched against the registry
    confidence: str = "low"           # DAIF-01 2.4 — an unqualified claim is trusted least
    drk_record_id: str | None = None  # set when a matching formal DRK record was found


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", text.lower())


def _key(chosen: str) -> str:
    words = [w for w in _norm(chosen).split() if len(w) > 3][:12]
    return hashlib.sha256(" ".join(words).encode("utf-8")).hexdigest()[:12]


def _iter_turns(path: Path) -> Iterable[dict[str, Any]]:
    """Yield {role, text, ts, uuid} per turn. Fail-open on every line."""
    try:
        raw = path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if not isinstance(rec, dict) or rec.get("type") not in ("user", "assistant"):
            continue
        msg = rec.get("message")
        if not isinstance(msg, dict):
            continue
        content = msg.get("content")
        chunks: list[str] = []
        if isinstance(content, str):
            chunks.append(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    t = block.get("text")
                    if isinstance(t, str):
                        chunks.append(t)
        if not chunks:
            continue
        yield {
            "role": rec.get("type"),
            "text": "\n".join(chunks),
            "ts": str(rec.get("timestamp") or "unknown"),
            "uuid": str(rec.get("uuid") or "unknown"),
        }


def _match_decision(sentence: str) -> tuple[str, str] | None:
    for pattern in DECISION_PATTERNS:
        m = pattern.search(sentence)
        if not m:
            continue
        chosen = m.group("chosen").strip(" .,:;")
        rationale = m.group("rationale").strip(" .,:;")
        if len(chosen.split()) < MIN_CHOSEN_WORDS or len(rationale.split()) < MIN_RATIONALE_WORDS:
            continue
        return chosen[:MAX_FIELD_CHARS], rationale[:MAX_FIELD_CHARS]
    return None


def _load_drk_records(project: Path) -> list[dict]:
    """Best-effort read of the DRK Decision Registry (composed, never forked -- DAIF_RESUMPTION.md
    decision 1). Fail-open to an empty list; a missing or unreadable registry is not an error."""
    try:
        from modules.decision_review.decision_record import DEFAULT_REGISTRY, Registry
        registry_path = project / "vault" / "decision_registry" / "records.jsonl"
        reg = Registry(registry_path if registry_path.exists() else DEFAULT_REGISTRY)
        return reg.load()
    except (ImportError, OSError, Exception):
        return []


def extract_decisions(session_path: str | Path,
                       project_path: str | Path | None = None
                       ) -> tuple[list[Decision], dict[str, Any]]:
    """Return (decisions with justification, intake report). Never raises."""
    path = Path(session_path)
    session_id = path.stem
    project = Path(project_path).resolve() if project_path else path.resolve().parents[0]

    candidates: dict[str, Decision] = {}
    refused_meta = 0
    scanned_turns = 0

    for turn in _iter_turns(path):
        scanned_turns += 1
        for sentence in _SENTENCE_SPLIT.split(turn["text"]):
            sentence = sentence.strip()
            if not (20 <= len(sentence) <= 700):
                continue
            if META_RE.search(sentence):
                refused_meta += 1
                continue
            hit = _match_decision(sentence)
            if hit is None:
                continue
            chosen, rationale = hit
            key = _key(chosen)
            pointer = f"{session_id}#{turn['uuid']}"
            existing = candidates.get(key)
            if existing is not None:
                if pointer not in existing.source:
                    existing.source.append(pointer)
                continue
            referenced = sorted(set(_PATH_TOKEN_RE.findall(chosen + " " + rationale)))
            candidates[key] = Decision(
                identifier=f"DEC-ARCH-{key}",
                chosen=chosen,
                rationale=rationale,
                origin=f"session:{session_id} turn:{turn['uuid']} role:{turn['role']}",
                source=[pointer],
                referenced_files=referenced,
            )

    # Cross-check against the formal DRK registry: a decision whose `chosen` text overlaps a
    # registered record's `chosen` field is annotated with that record's id and promoted out of
    # pure archaeology, because the estate already reviewed it and the review is authoritative.
    drk_records = _load_drk_records(project)
    decisions = list(candidates.values())
    for dec in decisions:
        dec_words = set(_norm(dec.chosen).split())
        for rec in drk_records:
            drk_chosen = rec.get("decision", {}).get("chosen", "")
            if not drk_chosen:
                continue
            rec_words = set(_norm(drk_chosen).split())
            if dec_words and rec_words and len(dec_words & rec_words) >= max(3, len(dec_words) // 2):
                dec.drk_record_id = rec.get("id")
                dec.intake = "drk-reviewed"
                break

    decisions.sort(key=lambda d: d.identifier)
    report = {
        "session_id": session_id,
        "session_path": str(path),
        "turns_scanned": scanned_turns,
        "candidates": len(candidates),
        "found": len(decisions),
        "refused_as_meta_discussion": refused_meta,
        "drk_registry_records_checked": len(drk_records),
        "drk_matched": sum(1 for d in decisions if d.drk_record_id),
        "intake": "archaeology",
    }
    return decisions, report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="DAIF-08 Part XI decision extractor")
    ap.add_argument("session", help="path to a Claude Code session .jsonl")
    ap.add_argument("--project", default=".", help="project root (for DRK registry lookup)")
    ap.add_argument("--out", default=None, help="write report here")
    args = ap.parse_args(argv)

    decisions, report = extract_decisions(args.session, args.project)
    payload = {"report": report, "decisions": [asdict(d) for d in decisions]}
    if args.out:
        Path(args.out).write_text(json.dumps(payload, indent=2, ensure_ascii=False),
                                  encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    for d in decisions[:20]:
        print(f"  [{d.intake}] {d.identifier}  {d.chosen[:80]} -- {d.rationale[:80]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
