"""Structured reality input -- the second fact source (GSDX-M04, GSDX-M05).

The derivation operators in `obligation.py` are general over FACTS. The only
source of facts until GSDX-M04 was `extract_facts`, a regex vocabulary over
prose that is closed by construction: each unseen wording cost one more verb.
This module reads facts that were DECLARED or PRODUCED rather than mined, and
hands them to the same operators unchanged.

TWO SCHEMAS, AND WHY THE SECOND ONE EXISTS (GSDX-M05).

`gsdx-facts/1` carries one bucket, `facts[]`, and its consumer reads PRESENCE AS
HOLDS. That makes absence ambiguous in the one direction that matters, because
three different worlds collapse into it:

    the fact was measured and does NOT hold
    the fact could not be measured
    nobody ever asked

Only the first is safe to act on. A mission whose closure receipt says
"complete" because a fact it could not measure produced no obligation is not
reporting completeness -- it is reporting its own blindness in the costume of
success.

`gsdx-facts/2` therefore carries three buckets -- `facts[]`, `not_held[]`,
`unknown[]` -- and every entry states HOW it is known (`state`) and WHAT it was
computed from (`depends_on`). `tools/gsd_x_fact_producer.py` emits it.

REFUSAL IS THE CONTRACT, NOT AN INCONVENIENCE. Every way a facts document can be
wrong raises `StructuredFactsError`, because each silent alternative produces a
clean gate over a mission that is not clean:

  * an unknown fact name -- a typo would drop an obligation without a trace;
  * a fact with no evidence -- a fact nobody can point at is a guess;
  * a duplicate -- two declarations that may disagree, resolved by list order;
  * ONE NAME IN TWO BUCKETS -- a document asserting that a fact both holds and
    could not be measured is not a fact source, it is a contradiction, and
    picking a winner here would be this module inventing the answer;
  * a v2 document missing `state` or `depends_on` -- without them the richer
    document means exactly as little as the old one, which is the whole reason
    the old loader refused it rather than accepting it and ignoring the fields;
  * an unsupported future version -- refused BY NAME, so the message says which
    version arrived rather than "malformed";
  * no schema, no provenance, or malformed JSON.

Absence of the FILE is not an error: the mission falls back to the prose
adapter, and the caller is told which source it got (`source_of`).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .obligation import DECLARED, FACT_NAMES, FACT_STATES, UNKNOWN, Fact

SCHEMA_V1 = "gsdx-facts/1"
SCHEMA_V2 = "gsdx-facts/2"
SUPPORTED = (SCHEMA_V1, SCHEMA_V2)

# Kept as a LIVE alias, not renamed. `dump()` and the sealed parity proof in
# tools/test_gsd_x_structured_facts.py read `sf.SCHEMA` in six places; renaming
# it would turn that suite's 15 green gates into an AttributeError, which is a
# harness failure wearing a regression's clothes.
SCHEMA = SCHEMA_V1

FACTS_FILE = "FACTS.json"
SOURCE = "structured"


class StructuredFactsError(ValueError):
    """A facts document that cannot be trusted. Never a subject verdict."""


@dataclass(frozen=True)
class FactNote:
    """A fact that is NOT being asserted: measured-false, or unmeasurable.

    It carries `depends_on` for the same reason a held fact does -- a note whose
    sources have moved is no more current than a held fact whose sources moved.
    """
    name: str
    state: str
    why: str
    depends_on: tuple = ()


@dataclass
class FactSet:
    """Everything a facts document says, including what it could not say."""
    schema: str
    provenance: str
    held: list[Fact] = field(default_factory=list)
    not_held: list[FactNote] = field(default_factory=list)
    unknown: list[FactNote] = field(default_factory=list)

    @property
    def is_v2(self) -> bool:
        return self.schema == SCHEMA_V2

    @property
    def unknown_names(self) -> list[str]:
        return [n.name for n in self.unknown]


def facts_path(root: Path) -> Path:
    return Path(root) / FACTS_FILE


def source_of(root: Path) -> str:
    """Which adapter a mission root will be read with."""
    return SOURCE if facts_path(root).is_file() else "prose"


def _read_doc(path: Path) -> dict:
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
    return doc


def _require_name(path: Path, where: str, i: int, item) -> str:
    if not isinstance(item, dict):
        raise StructuredFactsError(f"{path}: {where}[{i}] must be an object")
    name = item.get("name")
    if name not in FACT_NAMES:
        raise StructuredFactsError(
            f"{path}: {where}[{i}] names {name!r}, which no operator reads. "
            f"Known: {sorted(FACT_NAMES)}")
    return name


def _require_state(path: Path, where: str, i: int, item, name: str) -> str:
    state = item.get("state")
    if not isinstance(state, str) or not state.strip():
        raise StructuredFactsError(
            f"{path}: {where}[{i}] ({name}) carries no 'state'. A {SCHEMA_V2} "
            "entry must say HOW it is known; without it this document means no "
            "more than a v1 one and the extra buckets are decoration.")
    if state not in FACT_STATES:
        raise StructuredFactsError(
            f"{path}: {where}[{i}] ({name}) has state {state!r}; known states "
            f"are {sorted(FACT_STATES)}")
    return state


def _require_depends_on(path: Path, where: str, i: int, item, name: str) -> tuple:
    dep = item.get("depends_on")
    if not isinstance(dep, list):
        raise StructuredFactsError(
            f"{path}: {where}[{i}] ({name}) carries no 'depends_on' list. "
            "Freshness here is dependency-driven and has no clock, so an entry "
            "that names no sources can never be re-checked -- it would be "
            "permanently, silently FRESH.")
    return tuple(dep)


def load_document(path: Path) -> FactSet:
    """Read a facts document of either schema, whole.

    This is the richer entry point and the one the mission path uses. `load()`
    returns only the held facts, which is all a v1 document ever had.
    """
    path = Path(path)
    doc = _read_doc(path)

    schema = doc.get("schema")
    if schema not in SUPPORTED:
        raise StructuredFactsError(
            f"{path}: schema {schema!r} is not supported; this loader reads "
            f"{list(SUPPORTED)}. A newer document is refused by name rather "
            "than read permissively: silently ignoring fields it does not "
            "understand is how a richer document becomes a poorer one.")
    v2 = schema == SCHEMA_V2

    prov = doc.get("provenance")
    if not isinstance(prov, str) or not prov.strip():
        raise StructuredFactsError(
            f"{path}: 'provenance' is required -- say who or what established "
            "these facts")

    raw = doc.get("facts")
    if not isinstance(raw, list):
        raise StructuredFactsError(f"{path}: 'facts' must be a list")

    # One name may appear in ONE bucket. Checked across all three, not per
    # bucket: a name in both facts[] and unknown[] is a contradiction, and
    # resolving it here would be this module deciding what the document meant.
    seen: dict[str, str] = {}

    def claim(name: str, bucket: str, where: str, i: int) -> None:
        prior = seen.get(name)
        if prior is None:
            seen[name] = bucket
            return
        if prior == bucket:
            raise StructuredFactsError(
                f"{path}: {where}[{i}] declares {name!r} twice")
        raise StructuredFactsError(
            f"{path}: {name!r} appears in both {prior!r} and {bucket!r}. A fact "
            "cannot both hold and be unmeasured; nothing here may choose which "
            "one the author meant.")

    held: list[Fact] = []
    for i, item in enumerate(raw):
        name = _require_name(path, "facts", i, item)
        evidence = item.get("evidence")
        if not isinstance(evidence, str) or not evidence.strip():
            raise StructuredFactsError(
                f"{path}: facts[{i}] ({name}) carries no evidence")
        claim(name, "facts", "facts", i)
        state = _require_state(path, "facts", i, item, name) if v2 else DECLARED
        if v2:
            _require_depends_on(path, "facts", i, item, name)
        if state == UNKNOWN:
            raise StructuredFactsError(
                f"{path}: facts[{i}] ({name}) is in the HELD bucket with state "
                "UNKNOWN. A fact that could not be measured is not a fact that "
                "holds; it belongs in 'unknown'.")
        held.append(Fact(name=name, matched=" ".join(evidence.split())[:160],
                         source=SOURCE, state=state))

    def notes(key: str) -> list[FactNote]:
        rows = doc.get(key, [])
        if not isinstance(rows, list):
            raise StructuredFactsError(f"{path}: {key!r} must be a list")
        if rows and not v2:
            raise StructuredFactsError(
                f"{path}: {key!r} is a {SCHEMA_V2} bucket and this document "
                f"declares {schema!r}")
        out = []
        for i, item in enumerate(rows):
            name = _require_name(path, key, i, item)
            claim(name, key, key, i)
            state = _require_state(path, key, i, item, name)
            dep = _require_depends_on(path, key, i, item, name)
            why = item.get("why")
            if not isinstance(why, str) or not why.strip():
                raise StructuredFactsError(
                    f"{path}: {key}[{i}] ({name}) carries no 'why'. An absence "
                    "nobody explained is the thing this bucket exists to stop.")
            out.append(FactNote(name=name, state=state,
                                why=" ".join(why.split())[:240], depends_on=dep))
        return out

    return FactSet(schema=schema, provenance=prov, held=held,
                   not_held=notes("not_held"), unknown=notes("unknown"))


def load(path: Path) -> list[Fact]:
    """The held facts, for callers that only ever had those.

    Kept because the sealed parity proof round-trips v1 documents through
    `dump()` and back through here. It accepts v2 as well -- refusing it would
    make every producer-emitted document unreadable -- but a v2 document read
    this way DROPS `not_held` and `unknown`, which is precisely the blindness
    this wave exists to surface. So the mission path uses `load_document()`,
    and a gate asserts this function has no production caller.
    """
    return load_document(path).held


def dump(facts: list[Fact], provenance: str) -> dict:
    """Serialize facts to the V1 schema.

    Pinned to SCHEMA_V1 explicitly rather than to the `SCHEMA` alias, so that a
    later change of the alias cannot silently move the sealed parity fixture to
    a schema it was never derived under.

    Used to derive a structured document MECHANICALLY from an existing source --
    the parity proof in tools/test_gsd_x_structured_facts.py builds its fixture
    this way, from the sealed prose, precisely so nothing is hand-authored with
    the operators in view. It does NOT serialize `state`: v1 has no such field,
    so a dump()->load() round trip returns DECLARED rather than what went in.
    That is v1 being v1, and the suite asserts it rather than leaving a reader
    to discover it.
    """
    return {
        "schema": SCHEMA_V1,
        "provenance": provenance,
        "facts": [{"name": f.name, "evidence": f.matched} for f in facts],
    }
