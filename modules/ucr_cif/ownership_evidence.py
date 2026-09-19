#!/usr/bin/env python3
"""ownership_evidence.py -- structural ownership signals (UCR-CIF W3, Problem B).

`disposition_ledger.propose` is a CANDIDATE GENERATOR and a good one, but its
evidence is lexical: it accumulates `w * min(n, 8)` over every matching term and
takes an argmax. So an owner with BROADER VOCABULARY wins, whether or not it
owns anything.

Measured on the real ledger, with an instrument independent of the scorer:

    spearman(proposals, distinct vocabulary) = +0.756
    spearman(proposals, bytes)               = +0.735

    modules/governance-overlay        452 proposals, 2677 terms, 118 KB
    agents/oneshot-architect-auditor.md  214 proposals from ONE 36 KB file
    modules/governance-overlay: 81.5 % of its vocabulary is shared with other
    owners -- it carries the estate's general vocabulary, not distinctive
    ownership terms.

That is the T-VOCABULARY-VOLUME-FALSE-OWNERSHIP class, confirmed rather than
suspected.

WHAT THIS MODULE ADDS, AND WHY IT IS NOT MORE SCORING
-----------------------------------------------------
Every signal here is STRUCTURAL: it is a fact about how the repository is built,
and none of them can be won by saying a word more often. A 500 KB document that
mentions `retirement` two thousand times still defines no symbol named
`retirement`, owns no file called `retirement.py`, and is imported by nobody.

  SYMBOL      the owner DEFINES a symbol whose name carries the term (AST for
              Python, declaration patterns otherwise). Definition, never mention.
  FILENAME    the owner has a file or directory named for the term.
  REGISTRY    the term is a KEY or id in a JSON the owner owns -- a registry
              entry is a commitment, prose is not.
  CONSUMER    something else IMPORTS the owner (an inbound edge). An owner
              nobody consumes is a document, whatever it is about.
  DISTINCTIVE the term is rare ACROSS owners. A term two thirds of the estate
              uses cannot select between them, however often it appears.

DISTINCTIVE is the direct antidote to volume: it is computed from how many
owners share a term, so breadth of vocabulary REDUCES a term's weight instead of
raising it.

THE VERDICTS (kept disjoint on purpose)
---------------------------------------
  VERIFY   at least one structural signal AND at least one distinctive term.
  REJECT   positively contradicted -- the candidate is a volume outlier whose
           support is purely lexical. This is not "we are unsure"; it is "this
           particular owner is wrong", and it is what stops a false owner being
           re-proposed forever.
  ABSTAIN  insufficient evidence either way. UNKNOWN is a valid truth state and
           it is NEVER resolved toward the convenient answer to raise coverage.

Nothing here writes a disposition. It produces evidence; promotion is a separate
decision, exactly as `retirement.py` proposes and an Owner retires.

Stdlib-only. Fail-open per candidate: an unreadable file costs that signal, not
the sweep.
"""
from __future__ import annotations

import ast
import json
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]

SCAN_DIRS = ("modules", "tools", "hooks", "commands", "agents", "governance",
             "rules")
CODE_EXT = (".py", ".js", ".ts", ".mjs", ".cjs")
ALL_EXT = CODE_EXT + (".md", ".json", ".ps1")

# How many owners may STRUCTURALLY hold a term before it stops discriminating.
#
# This began as a fraction of the owner population (0.25) and that instrument
# was vacuous, which only showed up on the real estate. Measured over the 2,100
# distinct evidence terms in the live ledger, against 756 owners:
#
#     ceiling 189 (=25 % of owners) admits 1136 of 1137 held terms -- it
#     excludes exactly one term and filters nothing.
#
# The same measurement gives the honest answer. 963 of 2100 terms (45.9 %) have
# ZERO structural holders -- prose vocabulary nobody defines, names or
# registers. Among terms that ARE held, the distribution is sharply skewed:
#
#     median 3   p75 7   p90 15   max 474
#
# So an absolute ceiling at the median is what "few enough owners to select
# between them" actually means here, and a fraction of a large heterogeneous
# owner population never could be. 3 is the measured median, stated as a
# decision so it can be argued with.
DISTINCTIVE_MAX_HOLDERS = 3

# A candidate proposed for more units than this, with no structural signal, is a
# volume outlier rather than an owner. Derived from the measurement above: the
# four volume winners hold 63 % of all proposals.
VOLUME_OUTLIER_PROPOSALS = 100

_DECL_RX = {
    ".js": re.compile(r"(?:function|class|const|let|var)\s+([A-Za-z_$][\w$]*)"),
    ".ts": re.compile(r"(?:function|class|const|let|var|interface|type)\s+([A-Za-z_$][\w$]*)"),
}
_WORD_RX = re.compile(r"[A-Za-z][A-Za-z0-9]{2,}")


@dataclass
class OwnerEvidence:
    owner: str
    symbols: list = field(default_factory=list)
    filenames: list = field(default_factory=list)
    registry_keys: list = field(default_factory=list)
    inbound_imports: int = 0
    distinctive_terms: list = field(default_factory=list)

    @property
    def structural(self) -> list:
        """Signals present, strongest first.

        CONSUMER is listed but is NOT term-specific: inbound imports are a fact
        about the OWNER, not about this capability. Measured in the adversarial
        gate -- an owner with one inbound edge 'verified' for a term belonging to
        a different module, because CONSUMER fired for every term it was ever
        asked about. It is corroboration; `attributing` is what may promote.
        """
        out = []
        if self.symbols:
            out.append("SYMBOL")
        if self.filenames:
            out.append("FILENAME")
        if self.registry_keys:
            out.append("REGISTRY")
        if self.inbound_imports:
            out.append("CONSUMER")
        return out

    @property
    def attributing(self) -> list:
        """The signals that tie THIS owner to THESE terms. Only these promote."""
        return [s for s in self.structural if s != "CONSUMER"]

    def to_dict(self) -> dict:
        return {"owner": self.owner, "structural": self.structural,
                "symbols": self.symbols[:8], "filenames": self.filenames[:8],
                "registry_keys": self.registry_keys[:8],
                "inbound_imports": self.inbound_imports,
                "distinctive_terms": self.distinctive_terms[:8]}


@dataclass
class Adjudication:
    unit_uid: str
    candidate: str
    verdict: str            # VERIFY | REJECT | ABSTAIN
    reason: str
    evidence: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"unit_uid": self.unit_uid, "candidate": self.candidate,
                "verdict": self.verdict, "reason": self.reason,
                "evidence": self.evidence}


def _owner_of(rel: str) -> str:
    parts = rel.split("/")
    return "/".join(parts[:2]) if len(parts) > 2 else rel


def _split_identifier(name: str) -> set:
    """snake_case, camelCase and kebab-case into lowercase words."""
    s = re.sub(r"[-_./]+", " ", name)
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", s)
    return {w.lower() for w in _WORD_RX.findall(s) if len(w) >= 4}


def build_structural_index(repo=None) -> dict:
    """One pass over the estate. Returns the structural facts, not scores.

    `defined`   term -> {owner}    a symbol DEFINITION carrying that term
    `named`     term -> {owner}    a file or directory named for the term
    `registry`  term -> {owner}    a JSON key or id
    `inbound`   owner -> int       modules importing this owner
    `owner_terms` owner -> {term}  for distinctiveness
    """
    root = Path(repo) if repo is not None else _PP_ROOT
    defined: dict = defaultdict(set)
    named: dict = defaultdict(set)
    registry: dict = defaultdict(set)
    inbound: Counter = Counter()
    owner_terms: dict = defaultdict(set)
    owners: set = set()
    files_seen = 0

    for d in SCAN_DIRS:
        base = root / d
        if not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [x for x in dirnames
                           if x not in (".git", "__pycache__", "node_modules")]
            for fn in filenames:
                if not fn.endswith(ALL_EXT):
                    continue
                path = Path(dirpath) / fn
                rel = str(path.relative_to(root)).replace("\\", "/")
                owner = _owner_of(rel)
                owners.add(owner)
                files_seen += 1

                # FILENAME -- the path's own words, owner prefix included.
                for term in _split_identifier(rel):
                    named[term].add(owner)

                try:
                    blob = path.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue

                for w in _WORD_RX.findall(blob):
                    if len(w) >= 4:
                        owner_terms[owner].add(w.lower())

                ext = path.suffix
                if ext == ".py":
                    try:
                        tree = ast.parse(blob)
                    except (SyntaxError, ValueError):
                        tree = None
                    if tree is not None:
                        for node in ast.walk(tree):
                            if isinstance(node, (ast.FunctionDef,
                                                 ast.AsyncFunctionDef,
                                                 ast.ClassDef)):
                                for term in _split_identifier(node.name):
                                    defined[term].add(owner)
                            # CONSUMER -- an inbound import edge.
                            mod = None
                            if isinstance(node, ast.ImportFrom):
                                mod = node.module or ""
                            elif isinstance(node, ast.Import):
                                mod = ",".join(a.name for a in node.names)
                            if mod:
                                for other in _module_owners(mod):
                                    if other != owner:
                                        inbound[other] += 1
                elif ext in _DECL_RX:
                    for m in _DECL_RX[ext].finditer(blob):
                        for term in _split_identifier(m.group(1)):
                            defined[term].add(owner)
                elif ext == ".json":
                    try:
                        data = json.loads(blob)
                    except (json.JSONDecodeError, ValueError):
                        data = None
                    for key in _json_keys(data):
                        for term in _split_identifier(key):
                            registry[term].add(owner)

    return {"defined": defined, "named": named, "registry": registry,
            "inbound": inbound, "owner_terms": owner_terms,
            "owners": owners, "files_seen": files_seen}


def _module_owners(mod: str) -> set:
    """`modules.capability_runtime.contract` -> {'modules/capability_runtime'}."""
    out = set()
    for piece in str(mod).split(","):
        parts = piece.strip().replace("/", ".").split(".")
        if len(parts) >= 2 and parts[0] in SCAN_DIRS:
            out.add(f"{parts[0]}/{parts[1]}")
    return out


def _json_keys(data, depth=0) -> list:
    if depth > 4:
        return []
    out = []
    if isinstance(data, dict):
        for k, v in data.items():
            out.append(str(k))
            out.extend(_json_keys(v, depth + 1))
    elif isinstance(data, list):
        for v in data[:200]:
            out.extend(_json_keys(v, depth + 1))
    return out


def structural_holders(term: str, index) -> set:
    """Owners that STRUCTURALLY hold a term -- define it, are named for it, or
    register it. Mentions are excluded on purpose; a mention is the lexical
    channel this module exists to escape."""
    t = str(term).lower()
    return (index["defined"].get(t, set())
            | index["named"].get(t, set())
            | index["registry"].get(t, set()))


def distinctive(terms, index, max_holders=DISTINCTIVE_MAX_HOLDERS) -> list:
    """Terms that can actually select between owners.

    Distinctiveness is measured over STRUCTURAL holders, not over mentions, and
    the first version of this function got that wrong in a way the adversarial
    gate caught immediately. Counting mentions means a decoy can DILUTE a real
    owner's distinctiveness simply by talking about its capability -- the volume
    attack winning through the back door -- while filler words unique to one big
    document score as maximally distinctive, which is backwards: they are rare
    and meaningless.

    Over structural holders both failures vanish. A document that mentions
    `quarantine` ten thousand times is not a holder, so it cannot dilute; and a
    filler word no module defines has zero holders, so it is not distinctive at
    all. `0 < len(...)` is what excludes it -- an unheld term is unowned, never
    distinctive.
    """
    out = []
    for t in terms:
        holders = structural_holders(t, index)
        if 0 < len(holders) <= max_holders:
            out.append(str(t).lower())
    return sorted(set(out))


def evidence_for(owner: str, terms, index) -> OwnerEvidence:
    """Structural signals tying ONE owner to a set of terms."""
    terms_l = {str(t).lower() for t in terms}
    ev = OwnerEvidence(owner=owner)
    for t in sorted(terms_l):
        if owner in index["defined"].get(t, ()):
            ev.symbols.append(t)
        if owner in index["named"].get(t, ()):
            ev.filenames.append(t)
        if owner in index["registry"].get(t, ()):
            ev.registry_keys.append(t)
    ev.inbound_imports = int(index["inbound"].get(owner, 0))
    ev.distinctive_terms = distinctive(terms_l, index)
    return ev


def adjudicate(unit_uid: str, candidate: str, terms, index,
               proposal_counts=None) -> Adjudication:
    """VERIFY / REJECT / ABSTAIN for one proposed owner.

    Never promotes on lexical evidence. `proposal_counts` (owner -> how many
    units it was proposed for) is what identifies a volume outlier; without it
    the function still works and simply cannot say REJECT for that reason.
    """
    if not candidate:
        return Adjudication(unit_uid, "", "ABSTAIN",
                            "no candidate owner was proposed")

    ev = evidence_for(candidate, terms, index)
    # Only term-attributing signals may promote. CONSUMER is about the owner.
    attributing = ev.attributing
    n_proposed = int((proposal_counts or {}).get(candidate, 0))

    if attributing and ev.distinctive_terms:
        return Adjudication(
            unit_uid, candidate, "VERIFY",
            f"structural signal(s) {', '.join(attributing)} on distinctive "
            f"term(s) {', '.join(ev.distinctive_terms[:4])}",
            ev.to_dict())

    if not attributing and n_proposed >= VOLUME_OUTLIER_PROPOSALS:
        return Adjudication(
            unit_uid, candidate, "REJECT",
            f"candidate holds {n_proposed} proposals and shows NO attributing "
            "signal here -- vocabulary volume, not ownership",
            ev.to_dict())

    if attributing and not ev.distinctive_terms:
        return Adjudication(
            unit_uid, candidate, "ABSTAIN",
            f"structural signal(s) {', '.join(attributing)} but only on terms "
            "the whole estate shares -- cannot select between owners",
            ev.to_dict())

    return Adjudication(
        unit_uid, candidate, "ABSTAIN",
        "no structural signal and not a volume outlier -- insufficient "
        "evidence either way", ev.to_dict())


__all__ = [
    "Adjudication", "OwnerEvidence", "DISTINCTIVE_MAX_HOLDERS",
    "VOLUME_OUTLIER_PROPOSALS", "adjudicate", "build_structural_index",
    "distinctive", "evidence_for", "structural_holders",
]
