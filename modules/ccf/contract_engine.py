"""Creative Contract Engine (CCF component #1).

human brief -> Creative Specification, per vault/plans/CCF_ARCHITECTURE.md §1.

Deterministic field extraction (labeled-line parsing, no LLM call) covers the
same ground `prd_parser.py`'s S1-S5 shape covers for PRDs: tokenize -> classify
-> extract -> schema_map. Mood-axis / aesthetic interpretation is intentionally
left as a pluggable `mood_extractor` hook -- that step needs real judgment, not
regex, per the architecture doc's gap analysis vs. prd_parser.

Ambiguity is mandatory: a brief missing a required field never produces a
silently-guessed spec. It returns a blocking questions list instead.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Callable, Optional

REQUIRED_FIELDS = ("brand_name", "industry", "audience")

_LABEL_PATTERNS = {
    "brand_name": re.compile(r"(?:brand|company|name)\s*:\s*(.+)", re.IGNORECASE),
    "industry": re.compile(r"industry\s*:\s*(.+)", re.IGNORECASE),
    "audience": re.compile(r"audience\s*:\s*(.+)", re.IGNORECASE),
    "deadline": re.compile(r"deadline\s*:\s*(.+)", re.IGNORECASE),
}

_MUST_PATTERN = re.compile(r"^\s*must\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
_MUST_NOT_PATTERN = re.compile(r"^\s*must[\s_-]?not\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
_VALUES_PATTERN = re.compile(r"^\s*values\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
_REFS_PATTERN = re.compile(r"^\s*(?:reference|ref)s?\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE)


@dataclass
class CreativeSpecification:
    brand_name: Optional[str] = None
    industry: Optional[str] = None
    audience: Optional[str] = None
    values: list = field(default_factory=list)
    constraints: dict = field(default_factory=lambda: {"must": [], "must_not": []})
    visual_references: list = field(default_factory=list)
    mood_axis: dict = field(default_factory=dict)
    deadline: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


def _split_list(raw: str) -> list:
    return [item.strip() for item in re.split(r"[,;]", raw) if item.strip()]


def _extract_labeled_fields(brief_text: str) -> dict:
    fields = {}
    for name, pattern in _LABEL_PATTERNS.items():
        match = pattern.search(brief_text)
        if match:
            fields[name] = match.group(1).strip().splitlines()[0].strip()
    must = _MUST_PATTERN.findall(brief_text)
    must_not = _MUST_NOT_PATTERN.findall(brief_text)
    values = _VALUES_PATTERN.findall(brief_text)
    refs = _REFS_PATTERN.findall(brief_text)
    fields["constraints"] = {
        "must": [m.strip() for m in must],
        "must_not": [m.strip() for m in must_not],
    }
    fields["values"] = _split_list(values[0]) if values else []
    fields["visual_references"] = _split_list(refs[0]) if refs else []
    return fields


def detect_ambiguity(fields: dict) -> list:
    """Return blocking questions for every required field that is missing or empty."""
    questions = []
    for name in REQUIRED_FIELDS:
        value = fields.get(name)
        if not value or not str(value).strip():
            questions.append({
                "field": name,
                "question": f"What is the {name.replace('_', ' ')} for this brief?",
            })
    return questions


def compile_spec(
    brief_text: str,
    extra_answers: Optional[dict] = None,
    mood_extractor: Optional[Callable[[str], dict]] = None,
) -> tuple:
    """Compile a brief into a CreativeSpecification.

    Returns (spec, questions). If questions is non-empty, spec is None -- the
    caller (CLI `compile` subcommand) must resolve them via `extra_answers` and
    re-invoke before a spec is produced. Never returns a spec with a blank
    required field.
    """
    fields = _extract_labeled_fields(brief_text or "")
    if extra_answers:
        fields.update({k: v for k, v in extra_answers.items() if v})

    questions = detect_ambiguity(fields)
    if questions:
        return None, questions

    mood_axis = mood_extractor(brief_text) if mood_extractor else {}
    spec = CreativeSpecification(
        brand_name=fields["brand_name"],
        industry=fields["industry"],
        audience=fields["audience"],
        values=fields.get("values", []),
        constraints=fields.get("constraints", {"must": [], "must_not": []}),
        visual_references=fields.get("visual_references", []),
        mood_axis=mood_axis,
        deadline=fields.get("deadline"),
    )
    return spec, []
