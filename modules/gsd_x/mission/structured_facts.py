"""Structured reality input -- the second fact source (GSDX-M04).

The derivation operators in `obligation.py` are general over FACTS. The only
source of facts until now was `extract_facts`, a regex vocabulary over prose
that is closed by construction: each unseen wording cost one more verb. This
module reads facts that were DECLARED rather than mined, from a `FACTS.json` in
the mission root, and hands them to the same operators unchanged.

What this does and does not move. It removes the vocabulary ceiling from
DERIVATION: an operator fires on a declared fact however the domain happens to
phrase itself. It does not remove the burden of knowing the fact -- that moves
from a regex to whoever writes the file. Producing FACTS.json from real
artifacts (infrastructure description, runbook, codebase) is the next step, and
until it exists a declared fact is exactly as good as its declarer.

Refusal is the contract, not an inconvenience. Every way a facts document can be
wrong raises `StructuredFactsError`, because each silent alternative produces a
clean gate over a mission that is not clean:

  * an unknown fact name -- a typo would drop an obligation without a trace;
  * a fact with no evidence -- a fact nobody can point at is a guess;
  * a duplicate -- two declarations that may disagree, resolved by list order;
  * no schema, no provenance, or malformed JSON.

Absence of the FILE is not an error: the mission falls back to the prose
adapter, and the caller is told which source it got (`source_of`).
"""
from __future__ import annotations

import json
from pathlib import Path

from .obligation import FACT_NAMES, Fact

SCHEMA = "gsdx-facts/1"
FACTS_FILE = "FACTS.json"
SOURCE = "structured"


class StructuredFactsError(ValueError):
    """A facts document that cannot be trusted. Never a subject verdict."""


def facts_path(root: Path) -> Path:
    return Path(root) / FACTS_FILE


def source_of(root: Path) -> str:
    """Which adapter a mission root will be read with."""
    return SOURCE if facts_path(root).is_file() else "prose"


def load(path: Path) -> list[Fact]:
    path = Path(path)
    try:
        # utf-8-sig: PowerShell 5.1 and spreadsheet exports prepend a BOM, and a
        # parser that dies on it turns a real facts file into an instrument error.
        doc = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError) as exc:
        raise StructuredFactsError(f"{path}: unreadable: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise StructuredFactsError(f"{path}: not valid JSON: {exc}") from exc

    if not isinstance(doc, dict):
        raise StructuredFactsError(f"{path}: top level must be an object")
    if doc.get("schema") != SCHEMA:
        raise StructuredFactsError(
            f"{path}: schema must be {SCHEMA!r}, got {doc.get('schema')!r}")
    prov = doc.get("provenance")
    if not isinstance(prov, str) or not prov.strip():
        raise StructuredFactsError(
            f"{path}: 'provenance' is required -- say who or what established these facts")
    raw = doc.get("facts")
    if not isinstance(raw, list):
        raise StructuredFactsError(f"{path}: 'facts' must be a list")

    out: list[Fact] = []
    seen: set[str] = set()
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise StructuredFactsError(f"{path}: facts[{i}] must be an object")
        name, evidence = item.get("name"), item.get("evidence")
        if name not in FACT_NAMES:
            raise StructuredFactsError(
                f"{path}: facts[{i}] names {name!r}, which no operator reads. "
                f"Known: {sorted(FACT_NAMES)}")
        if not isinstance(evidence, str) or not evidence.strip():
            raise StructuredFactsError(
                f"{path}: facts[{i}] ({name}) carries no evidence")
        if name in seen:
            raise StructuredFactsError(f"{path}: facts[{i}] declares {name!r} twice")
        seen.add(name)
        out.append(Fact(name=name, matched=" ".join(evidence.split())[:160],
                        source=SOURCE))
    return out


def dump(facts: list[Fact], provenance: str) -> dict:
    """Serialize facts to the structured schema.

    Used to derive a structured document MECHANICALLY from an existing source --
    the parity proof in tools/test_gsd_x_structured_facts.py builds its fixture
    this way, from the sealed prose, precisely so nothing is hand-authored with
    the operators in view."""
    return {
        "schema": SCHEMA,
        "provenance": provenance,
        "facts": [{"name": f.name, "evidence": f.matched} for f in facts],
    }
