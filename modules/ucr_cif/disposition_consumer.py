#!/usr/bin/env python3
"""Applicability-aware selection over the AUTHORITATIVE disposition ledger.

W3 adjudicated 2,376 corpus units and 996 of them carry an authoritative
disposition naming the owner that already holds the concept. W4 measured what
read that field and found its own producer, its own adjudicator, its own test
and three vault documents. Nothing consulted it to decide anything, so the
corpus was institutional stock rather than institutional capital.

This module is the READ half of the join. It answers one question --

    given this proposal text, which existing owners does the corpus already
    hold authoritative evidence for, and by which units?

-- and it answers it with counts, provenance and refusals, so the CONSUMER
(modules/spec_gate/gate.py, the novelty proof gate) can change an obligation
instead of printing rows. Reading is not consumption; this file only makes
consumption possible.

WHY THE SELECTION EXISTS AT ALL
-------------------------------
The corpus must not be concatenated into a prompt. 996 units is context
explosion, false applicability and latency, and it would make every mission
pay for knowledge that does not apply to it. The desired effect is universal;
the context cost must not be. So a unit reaches a mission only when the
proposal is semantically about it, and even then only its owner, its count
and a few uids travel -- never its text.

THE FOUR REFUSALS (kernel vMAX-NULL-ERROR)
------------------------------------------
An empty answer is not one state, it is four, and collapsing them is how a
silent instrument failure reads as "nothing applies":

  UNREADABLE     the ledger is absent or malformed        -> route nothing, say so
  SCHEMA         the ledger speaks a version we do not    -> route nothing, say so
  POPULATION     fewer authoritative units survived the   -> route nothing, say so
                 filters than the floor; we cannot tell
                 "nothing applies" from "we read nothing"
  (none)         the population was real and no unit was  -> route nothing, no alarm
                 applicable to this proposal

Only the last is an answer about the proposal. The first three are answers
about us, and none of them may be reported as evidence of novelty -- that is
exactly the inversion HR-NOVELTY-001 exists to stop.

AUTHORITY IS NOT APPLICABILITY IS NOT CONSUMPTION
-------------------------------------------------
  authority     `disposition` set by a named reviewer. A proposal carries a
                CANDIDATE (`proposed_disposition`); only review makes it
                authoritative, and 1,162 considered candidates were NOT
                verified. They cannot route.
  lifecycle     the owner the disposition names must still exist. A routing
                to a path that has left the repo is a stale authority, and
                the join must break rather than name a directory nobody has.
  applicability the proposal must actually be about the unit. Measured by
                term overlap against the unit's own adjudicated evidence
                terms, using the producer's tokenizer (`text_terms`), not a
                second one.
  semantics     only disposition classes this module knows how to route are
                routed. A class that is present in the corpus and unsupported
                here is reported as a GAP, never mapped onto a neighbour.
"""
from __future__ import annotations

import json
import os
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from modules.ucr_cif.disposition_ledger import (
    DISPOSITIONS,
    SCHEMA_VERSION,
    text_terms,
)
#: Imported, never redefined and never tuned. How many owners may hold a term
#: before it stops telling you anything is the producer's decision, and W4's
#: standing prohibition is that this number is not a coverage dial.
from modules.ucr_cif.ownership_evidence import DISTINCTIVE_MAX_HOLDERS

#: Repo-relative location of the canonical authoritative store. Read directly
#: rather than through a compiled projection: a second copy keyed by corpus id
#: would be faster and would be one more thing that can silently go stale,
#: which is the disease this whole wave is treating.
LEDGER_REL = "vault/ucr_cif/disposition_ledger.json"

#: Disposition classes this consumer knows how to turn into a downstream
#: obligation. EXTEND_EXISTING_OWNER routes a proposal to the owner that
#: already holds the concept. The other eleven members of the closed set are
#: declared-and-unrouted: see `Selection.classes_unsupported`.
SUPPORTED_CLASSES: tuple[str, ...] = ("EXTEND_EXISTING_OWNER",)

#: A unit is about this proposal when at least this many of its adjudicated
#: evidence terms appear in the proposal. One shared term is a coincidence;
#: two is the same corroboration bar the producer itself uses
#: (MIN_EVIDENCE_FILES).
MIN_TERM_OVERLAP = 2

#: ...and at least this many of them must be DISTINCTIVE, i.e. held by few
#: enough owners to say WHICH owner the proposal is about.
#:
#: This clause exists because the first version routed a proposal about an
#: espresso machine to modules/knowledge_acquisition. Measured: all four of
#: its matches were the term pair ('institutional', 'system') -- words that
#: are in this gate's own trigger list, so they are present in EVERY proposal
#: that reaches it. A term shared by the whole population is the population's
#: common denominator and carries no information about membership; `failure`
#: is held by 21 owners, `knowledge` by 12. Filtering on term count alone
#: cannot see that, because two generic terms and two distinctive ones are
#: both "two". 1,242 of 1,498 evidence terms (83%) are distinctive, so this
#: narrows a false pole rather than the true one.
MIN_DISTINCTIVE_OVERLAP = 1

#: An owner must be named by at least this many applicable units before it is
#: worth routing to. A single unit is a lead; it is reported in the counters
#: and does not become an obligation.
MIN_UNITS_PER_OWNER = 2

#: Context economy. The materialization is bounded by construction, so a
#: pathological proposal that matches everything still costs a fixed budget.
MAX_OWNERS = 5
MAX_UIDS_PER_OWNER = 3
MAX_TERMS_PER_OWNER = 6

#: Population floor. Below this, an empty result is uninformative: a filter
#: that silently matched nothing and a corpus with nothing to say are the same
#: observable, and only one of them is safe to report. 996 units are recorded;
#: this floor is a fifth of that, so ordinary lifecycle attrition never trips
#: it and a broken read always does.
MIN_AUTHORITATIVE_POPULATION = 200

_CACHE: dict = {}


@dataclass(frozen=True)
class OwnerRouting:
    """One existing owner the corpus already holds authority about."""
    owner: str
    units: int
    uids: tuple[str, ...]
    terms: tuple[str, ...]
    sample: str | None = None


@dataclass(frozen=True)
class Selection:
    """What was considered, what applied, what did not, and why.

    Reconstructable by contract: every number here is the size of a set the
    caller can re-derive from the ledger and the proposal, so a downstream
    obligation can always be traced back to the corpus units that produced it.
    """
    owners: tuple[OwnerRouting, ...] = ()
    corpus_id: str | None = None
    refusal: str | None = None          # None = a real answer about the proposal
    population: int = 0                 # authoritative units that survived filters
    considered: int = 0                 # rows examined
    excluded_authority: int = 0         # candidate, never reviewed
    excluded_lifecycle: int = 0         # authoritative, owner no longer on disk
    excluded_semantics: int = 0         # authoritative, class not routable here
    rejected_applicability: int = 0     # applicable filter said no
    rejected_generic: int = 0           # overlapped, but on non-distinctive terms only
    applicable_units: int = 0           # applicable before the per-owner floor
    below_owner_floor: int = 0          # applicable units whose owner stayed a lead
    duplicates_suppressed: int = 0      # same owner + same obligation shape
    classes_present: tuple[str, ...] = ()
    classes_unsupported: tuple[str, ...] = ()
    prompt_terms: int = 0

    @property
    def routed(self) -> bool:
        return bool(self.owners)

    def to_dict(self) -> dict:
        d = {k: getattr(self, k) for k in (
            "corpus_id", "refusal", "population", "considered",
            "excluded_authority", "excluded_lifecycle", "excluded_semantics",
            "rejected_applicability", "rejected_generic", "applicable_units",
            "below_owner_floor", "duplicates_suppressed", "prompt_terms")}
        d["classes_present"] = list(self.classes_present)
        d["classes_unsupported"] = list(self.classes_unsupported)
        d["owners"] = [{"owner": o.owner, "units": o.units,
                        "uids": list(o.uids), "terms": list(o.terms),
                        "sample": o.sample} for o in self.owners]
        return d


def repo_root(start=None) -> Path:
    """The Power Pack root this module lives in."""
    return Path(__file__).resolve().parents[2] if start is None else Path(start)


def load_ledger(repo=None):
    """(meta, rows) or (None, None) when the store cannot be read.

    Cached on (path, mtime_ns, size) so a mission pays the parse once per
    process and a rebuilt ledger is never served from a stale cache.
    """
    path = repo_root(repo) / LEDGER_REL
    try:
        st = path.stat()
        key = (str(path), st.st_mtime_ns, st.st_size)
    except OSError:
        return None, None
    hit = _CACHE.get("k")
    if hit == key:
        return _CACHE["meta"], _CACHE["rows"]
    try:
        doc = json.loads(path.read_text(encoding="utf-8-sig"))
        rows = doc["rows"]
        if not isinstance(rows, list):
            raise ValueError("rows is not a list")
    except (OSError, ValueError, KeyError, TypeError):
        return None, None
    meta = {k: v for k, v in doc.items() if k != "rows"}
    # Every derived view is dropped with the rows it was derived from. A memo
    # that outlives its source is the same defect this wave exists to close,
    # one altitude down: the holder map and the owner-existence map are both
    # projections of THESE rows and of nothing else.
    _CACHE.update({"k": key, "meta": meta, "rows": rows, "holders": None})
    return meta, rows


def _owner_exists(repo: Path, owner: str, memo: dict) -> bool:
    """Lifecycle/join validity: the named owner is still in this repository.

    Checked with a path JOIN and an existence test, never with a substring --
    the estate has paid twice for identity by path matching
    (T-PATH-SUBSTRING-IDENTITY-001, and its mirror in W4).

    The memo is PER SELECTION, which is both faster and correct: 996
    authoritative rows name 40 distinct owners, so the naive form pays 956
    redundant filesystem calls on a hook path, while a memo cached beside the
    ledger would answer from a reading the ledger's own mtime cannot
    invalidate. The first version did exactly that and reported a deleted
    owner as present; the lifecycle drill is what found it. One selection is
    one consistent view of the repository, and the next selection looks again.
    """
    if not owner or os.path.isabs(owner) or ".." in owner.split("/"):
        return False
    hit = memo.get(owner)
    if hit is None:
        hit = memo[owner] = (repo / owner).exists()
    return hit


def term_holders(rows) -> dict:
    """term -> how many distinct owners the AUTHORITATIVE corpus gives it.

    Derived from the adjudicated rows themselves, not from a fresh repo scan:
    the question is which owner a proposal belongs to, and the population that
    answers it is the population being selected from. Cached per ledger
    generation beside the rows.
    """
    memo = _CACHE.get("holders")
    if memo is not None:
        return memo
    spread: dict = defaultdict(set)
    for r in rows:
        if not r.get("disposition") or not r.get("reviewed_by"):
            continue
        owner = str(r.get("proposed_owner") or "")
        for t in (r.get("evidence_terms") or []):
            spread[str(t).lower()].add(owner)
    memo = {t: len(o) for t, o in spread.items()}
    _CACHE["holders"] = memo
    return memo


def select_for(text: str, repo=None) -> Selection:
    """Select the authoritative dispositions applicable to a proposal."""
    root = repo_root(repo)
    meta, rows = load_ledger(root)
    if rows is None:
        return Selection(refusal="ledger unreadable: " + str(root / LEDGER_REL))
    corpus_id = str(meta.get("compiled_corpus_id") or "") or None
    if meta.get("schema_version") != SCHEMA_VERSION:
        return Selection(
            corpus_id=corpus_id,
            refusal="ledger schema_version=%r, this consumer speaks %r"
                    % (meta.get("schema_version"), SCHEMA_VERSION))

    terms = set(text_terms(text))
    holders = term_holders(rows)
    owner_memo: dict = {}
    classes: set[str] = set()
    excl_auth = excl_life = excl_sem = rejected = generic = 0
    population = 0
    by_owner: dict[str, list[dict]] = defaultdict(list)

    for r in rows:
        disp = r.get("disposition")
        # AUTHORITY. A candidate is not an authority; only review makes one.
        if not disp or disp not in DISPOSITIONS or not r.get("reviewed_by"):
            excl_auth += 1
            continue
        classes.add(disp)
        # SEMANTICS. An unsupported class is a gap, never a neighbour's meaning.
        if disp not in SUPPORTED_CLASSES:
            excl_sem += 1
            continue
        owner = r.get("proposed_owner")
        # LIFECYCLE. A disposition naming an owner that left is not current.
        if not _owner_exists(root, str(owner or ""), owner_memo):
            excl_life += 1
            continue
        population += 1
        # APPLICABILITY.
        ev = {str(t).lower() for t in (r.get("evidence_terms") or [])}
        overlap = ev & terms
        if len(overlap) < MIN_TERM_OVERLAP:
            rejected += 1
            continue
        distinct = {t for t in overlap
                    if holders.get(t, 1) <= DISTINCTIVE_MAX_HOLDERS}
        if len(distinct) < MIN_DISTINCTIVE_OVERLAP:
            generic += 1
            continue
        by_owner[str(owner)].append(r)

    if population < MIN_AUTHORITATIVE_POPULATION:
        # An empty selection over an empty population says nothing about the
        # proposal, so it must not be reported as one.
        return Selection(
            corpus_id=corpus_id, population=population, considered=len(rows),
            excluded_authority=excl_auth, excluded_lifecycle=excl_life,
            excluded_semantics=excl_sem, prompt_terms=len(terms),
            rejected_applicability=rejected, rejected_generic=generic,
            classes_present=tuple(sorted(classes)),
            refusal="authoritative population %d below floor %d"
                    % (population, MIN_AUTHORITATIVE_POPULATION))

    applicable = sum(len(v) for v in by_owner.values())
    below_floor = sum(len(v) for v in by_owner.values()
                      if len(v) < MIN_UNITS_PER_OWNER)
    dup = 0
    owners: list[OwnerRouting] = []
    for owner, hits in by_owner.items():
        if len(hits) < MIN_UNITS_PER_OWNER:
            continue
        # DUPLICATE SUPPRESSION. Two units that name one owner through the same
        # evidence terms are one obligation; the corpus indexes a concept from
        # several documents and would otherwise bill a mission once per copy.
        seen: set[tuple] = set()
        uniq = []
        for r in hits:
            sig = (tuple(sorted(str(t).lower()
                                for t in (r.get("evidence_terms") or []))),
                   str(r.get("name") or "").strip().lower())
            if sig in seen:
                dup += 1
                continue
            seen.add(sig)
            uniq.append(r)
        merged: set[str] = set()
        for r in uniq:
            merged |= {str(t).lower() for t in (r.get("evidence_terms") or [])}
        best = max(uniq, key=lambda r: (float(r.get("confidence") or 0.0),
                                        str(r.get("uid"))))
        # Most distinctive first: those are the terms that say WHY this owner
        # and not another, which is the whole content of the obligation.
        shown = sorted(merged & terms, key=lambda t: (holders.get(t, 1), t))
        owners.append(OwnerRouting(
            owner=owner,
            units=len(uniq),
            uids=tuple(sorted(str(r.get("uid")) for r in uniq)
                       )[:MAX_UIDS_PER_OWNER],
            terms=tuple(shown[:MAX_TERMS_PER_OWNER]),
            sample=(str(best.get("name") or "").strip() or None)))

    owners.sort(key=lambda o: (-o.units, o.owner))
    return Selection(
        owners=tuple(owners[:MAX_OWNERS]), corpus_id=corpus_id,
        population=population, considered=len(rows),
        excluded_authority=excl_auth, excluded_lifecycle=excl_life,
        excluded_semantics=excl_sem, rejected_applicability=rejected,
        rejected_generic=generic,
        applicable_units=applicable, below_owner_floor=below_floor,
        duplicates_suppressed=dup, prompt_terms=len(terms),
        classes_present=tuple(sorted(classes)),
        classes_unsupported=tuple(sorted(classes - set(SUPPORTED_CLASSES))))


def routing_obligation(sel: Selection) -> str | None:
    """The obligation text a routed selection imposes, or None.

    This is the behavioural payload: it replaces "go and run a discovered
    sweep" with the sweep's adjudicated result, and it inverts the burden of
    proof from asserting novelty to refuting a named owner. It stays ADVISORY
    -- a research frontier does not block like an architecture requirement,
    and turning every disposition into a hard gate is the failure mode on the
    other side of this one.
    """
    if not sel.routed:
        return None
    lines = ["UCR-CIF holds ADJUDICATED evidence that this is already owned. "
             "Question 4 of the novelty proof is therefore not open -- it is "
             "named, per owner, and the burden is to REFUTE these with "
             "file:line evidence, not to assert novelty:"]
    for o in sel.owners:
        lines.append(
            "  - %s -- %d authoritative unit(s) (e.g. %s; terms: %s; uid %s). "
            "Why is extending it insufficient?"
            % (o.owner, o.units, o.sample or "unnamed",
               ", ".join(o.terms) or "n/a", o.uids[0] if o.uids else "n/a"))
    lines.append(
        "  Provenance: %s, corpus %s. These are AUTHORITATIVE dispositions "
        "(reviewed); candidates, rejections and abstentions were excluded."
        % (LEDGER_REL, (sel.corpus_id or "unknown")[:12]))
    return "\n".join(lines)
