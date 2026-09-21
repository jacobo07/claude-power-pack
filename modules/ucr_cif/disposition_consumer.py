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
#: W9. The compiled structural projection -- term -> owners that DEFINE, are
#: NAMED for, or REGISTER that term. Orthogonal to everything above it: the
#: holder map below counts which owners' DOCUMENTS mention a term, this counts
#: which owner BUILDS it, and measured over the 7,785 authoritative
#: (unit, term) pairs the two disagree on 82 % of the distinctive ones.
from modules.ucr_cif import structural_projection as _sp

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
#:
#: W8: this is the FLOOR, not the bar. It is what a SHORT proposal must clear,
#: and it stays 1 so every W5/W6 fixture keeps the behaviour it pinned.
MIN_DISTINCTIVE_OVERLAP = 1

#: W8 -- how many prompt terms buy one additional required distinctive match.
#:
#: An absolute bar is length-blind, and the null expectation it is meant to
#: beat is not: the longer the prompt, the more of a unit's evidence terms it
#: contains by coincidence. W7 measured the consequence directly -- the share
#: of real prompts routing at least one owner climbs 45.8 % (m) -> 89.2 % (l)
#: -> 99.4 % (xl), and 85 % of real Tier >= 2 prompts are xl. A clause whose
#: pass rate rises to ~100 % in the modal bucket is not filtering.
#:
#: 200 is chosen from the measured population, not from taste. Real judgeable
#: prompts have a median of 20,099 chars and this repository's own tokenizer
#: yields 21-40 unique terms per 1k chars, so the modal prompt carries ~600
#: terms and the W5/W6 synthetic fixtures carry 5-20 (s median 122 chars, m
#: median 563). At 200, a fixture stays at the floor of 1 and the modal real
#: prompt is asked for more than coincidence supplies.
PROMPT_TERMS_PER_DISTINCTIVE = 200

#: ...and the requirement may never exceed the corpus's own median supply.
#:
#: Measured over the 996 authoritative units: distinctive terms per unit run
#: min 0, median 3, p75 4, p90 6, max 9. 784 units hold >= 2 and 605 hold
#: >= 3, so a bar of 3 is answerable by most of the population while a bar of
#: 4 is above the median and would refuse on SUPPLY rather than on relevance
#: -- buying precision by routing nothing, which is the failure mode on the
#: other side of saturation. The cap ties the ceiling to a measured
#: distribution exactly as DISTINCTIVE_MAX_HOLDERS ties its own.
MAX_DISTINCTIVE_REQUIRED = 3

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

#: W9. Whether an owner must show at least one STRUCTURALLY ATTRIBUTED
#: distinctive term to be routed at all (mechanism M3).
#:
#: Default OFF, and that is a measured decision rather than caution. Ranking
#: (M2) cannot lose a true positive by construction -- an owner with no
#: structural attribution scores zero and falls back to W8's order among its
#: peers. Admission can, and only 18.0 % of authoritative distinctive
#: (unit, term) pairs carry attribution, so this clause is the one with the
#: power to refuse a real owner. It ships only if the paired measurement says
#: the false owners it removes outnumber the true ones, and it is evaluated as
#: its own arm rather than folded into M2's result.
REQUIRE_STRUCTURAL_ATTRIBUTION = False

#: Escape hatch for the paired evaluation, read once per call so a measurement
#: harness can drive both arms in one process without reimporting. It may only
#: ever turn the clause ON: a released default cannot be weakened by an env
#: var, because an environment that silently disables a filter is how a
#: measured policy becomes untrue in production.
_REQUIRE_ENV = "UCR_CIF_REQUIRE_STRUCTURAL"

_CACHE: dict = {}


def _require_structural() -> bool:
    if REQUIRE_STRUCTURAL_ATTRIBUTION:
        return True
    return os.environ.get(_REQUIRE_ENV, "") == "1"


@dataclass(frozen=True)
class OwnerRouting:
    """One existing owner the corpus already holds authority about.

    `strength` (W8) is why this owner and not another: the summed
    inverse-holder weight of the distinctive terms it matched, so a term only
    this owner holds counts 1.0 and one shared by three counts a third. It
    replaces unit count as the RANK key. `units` is still reported, because
    how much the corpus holds about an owner is worth knowing -- it simply
    stopped being the answer to "which owner is this about".

    `structural_strength` (W9) is the SAME inverse-holder sum, evaluated over
    the subset of those distinctive terms this owner also holds STRUCTURALLY:
    it defines a symbol named for the term, carries a file or directory named
    for it, or registers it as a key. No new weight is invented, so both
    numbers sit on one scale and `structural_strength` is a strict SUB-SUM of
    `strength`. That is what makes the fusion monotone in both directions and
    unable to drop an owner -- one with no structural attribution scores 0.0
    and is ranked by `strength` among its peers, never excluded.

    `attributed` names the terms that earned it, so a rank is reconstructable
    instead of asserted.
    """
    owner: str
    units: int
    uids: tuple[str, ...]
    terms: tuple[str, ...]
    sample: str | None = None
    strength: float = 0.0
    structural_strength: float = 0.0
    attributed: tuple[str, ...] = ()


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
    # W8. The bar THIS prompt had to clear, reported so an empty result stays
    # explainable: "no owner" and "no owner at a required distinctiveness of
    # 3" are different answers, and only the second one names the clause that
    # produced it. Kernel vMAX-NULL-ERROR: an empty result has epistemology.
    distinctive_required: int = MIN_DISTINCTIVE_OVERLAP
    # Units that cleared the term bar and carried SOME distinctive evidence,
    # but fewer distinctive terms than this prompt's length required. Counted
    # apart from `rejected_generic` (which is zero distinctive terms) because
    # they are different refusals: one says the overlap was common vocabulary,
    # the other says it was real but too thin for a prompt this long.
    rejected_below_length_bar: int = 0
    # W9. The structural projection's STANDING, carried on every selection.
    #
    # Reported because zero structural evidence has two causes that demand
    # opposite responses: no owner in this selection happens to build these
    # terms, or the projection could not be consulted at all. Only the first
    # is a fact about owners. A caller reading `structural_strength == 0`
    # without this field cannot tell them apart, which is the collapse the
    # projection module refuses to make and this field is how the refusal
    # reaches the consumer.
    structural_status: str = _sp.ABSENT
    # Owners dropped by the M3 admission clause, when it is enabled. Always
    # reported, and zero when the clause is off, so a run can never be read as
    # having filtered when it did not.
    rejected_no_attribution: int = 0

    @property
    def routed(self) -> bool:
        return bool(self.owners)

    @property
    def structural_usable(self) -> bool:
        return self.structural_status == _sp.LOADED

    def to_dict(self) -> dict:
        d = {k: getattr(self, k) for k in (
            "corpus_id", "refusal", "population", "considered",
            "excluded_authority", "excluded_lifecycle", "excluded_semantics",
            "rejected_applicability", "rejected_generic", "applicable_units",
            "below_owner_floor", "duplicates_suppressed", "prompt_terms",
            "distinctive_required", "rejected_below_length_bar",
            "structural_status", "rejected_no_attribution")}
        d["classes_present"] = list(self.classes_present)
        d["classes_unsupported"] = list(self.classes_unsupported)
        d["owners"] = [{"owner": o.owner, "units": o.units,
                        "uids": list(o.uids), "terms": list(o.terms),
                        "sample": o.sample,
                        "strength": round(o.strength, 4),
                        "structural_strength": round(o.structural_strength, 4),
                        "attributed": list(o.attributed)}
                       for o in self.owners]
        return d


def _rank_key(o: OwnerRouting) -> tuple:
    """Rank: structural evidence first, then W8's lexical strength.

    Kept on ONE line so a mutation can sever it with a single-line anchor --
    see the note at the call site. Removing the first element restores W8's
    ordering exactly, which is the property that makes this wave reversible.
    """
    return (-o.structural_strength, -o.strength, -o.units, o.owner)


def required_distinctive(n_prompt_terms: int) -> int:
    """How many distinctive matches a unit must show for a prompt this long.

    Monotone by construction -- a longer prompt never asks for less -- and
    bounded at both ends: it starts at the floor a short proposal has always
    faced, so every W5/W6 fixture keeps its pinned behaviour, and it stops at
    the corpus's own median distinctive supply, so it can never refuse a unit
    for holding less evidence than the median unit holds.

    The bar is a property of the PROMPT, not of the unit, which is the whole
    point: the same unit is a coincidence in a 20,000-character prompt and a
    real match in a sentence.
    """
    if n_prompt_terms <= 0:
        return MIN_DISTINCTIVE_OVERLAP
    scaled = MIN_DISTINCTIVE_OVERLAP + n_prompt_terms // PROMPT_TERMS_PER_DISTINCTIVE
    return min(scaled, MAX_DISTINCTIVE_REQUIRED)


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
    # W9. Loaded ONCE per selection, before any row is examined, so every
    # owner in one selection is judged against one consistent view of the
    # repository -- the same discipline `_owner_exists` applies to lifecycle.
    # An unusable projection contributes nothing and says so; it never becomes
    # a negative verdict about an owner.
    # `corpus_id` is already parsed above, so the binding check costs a stat
    # rather than a second 1.9 MB read. Measured: passing it took the first
    # load from 70.8 ms to the projection's own parse cost.
    proj = _sp.load(root, corpus_id=corpus_id)
    require_structural = _require_structural()
    # W8. The applicability bar is a function of THIS prompt's length, decided
    # once, before any row is examined, so every unit in one selection faces
    # the same bar and the decision is reportable rather than emergent.
    need_distinct = required_distinctive(len(terms))
    owner_memo: dict = {}
    classes: set[str] = set()
    excl_auth = excl_life = excl_sem = rejected = generic = 0
    below_bar = 0
    no_attribution = 0
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
        # Two refusals, kept apart. No distinctive term at all means the
        # overlap was the population's common vocabulary and says nothing
        # about WHICH owner -- that is the W5 espresso-machine failure and it
        # is length-independent. Some distinctive evidence but less than this
        # prompt's length demands is a different statement: the match is real
        # and too thin to beat coincidence at 20,000 characters.
        if not distinct:
            generic += 1
            continue
        if len(distinct) < need_distinct:
            below_bar += 1
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
            distinctive_required=need_distinct,
            rejected_below_length_bar=below_bar,
            structural_status=proj.status,
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
        # W8. Evidence strength: the summed inverse-holder weight of the
        # DISTINCTIVE terms this owner actually matched. A term only this
        # owner holds contributes 1.0; one shared by the DISTINCTIVE_MAX
        # ceiling of three contributes a third. Generic terms contribute
        # nothing at all, so an owner cannot climb the ranking by sharing the
        # population's common vocabulary -- which is exactly how the three
        # largest owners came to be the three most-routed.
        matched_distinctive = [t for t in (merged & terms)
                               if holders.get(t, 1) <= DISTINCTIVE_MAX_HOLDERS]
        strength = sum(1.0 / holders.get(t, 1) for t in matched_distinctive)
        # W9. The same sum over the terms this owner also holds STRUCTURALLY.
        # A strict sub-sum, which is the whole design: it can never exceed
        # `strength`, so it cannot invent support, and an owner with none
        # scores 0.0 and keeps its W8 position relative to its peers rather
        # than being demoted below them for lacking a signal.
        #
        # Measured on this corpus: only 18.0 % of authoritative distinctive
        # (unit, term) pairs carry attribution, and the terms that fail are
        # prose -- `failure`, `capability`, `institutional`, `evidence`. Those
        # are corpus-distinctive and structurally unowned, which is precisely
        # the coincidence a 20,000-character prompt supplies for free.
        attributed = sorted((t for t in matched_distinctive
                             if proj.holds(owner, t)),
                            key=lambda t: (holders.get(t, 1), t))
        structural = sum(1.0 / holders.get(t, 1) for t in attributed)
        if require_structural and not attributed:
            # M3, off by default. Counted separately from every other refusal
            # so the arm that used it is visible in the numbers it produced.
            no_attribution += 1
            continue
        owners.append(OwnerRouting(
            owner=owner,
            units=len(uniq),
            uids=tuple(sorted(str(r.get("uid")) for r in uniq)
                       )[:MAX_UIDS_PER_OWNER],
            terms=tuple(shown[:MAX_TERMS_PER_OWNER]),
            sample=(str(best.get("name") or "").strip() or None),
            strength=strength,
            structural_strength=structural,
            attributed=tuple(attributed[:MAX_TERMS_PER_OWNER])))

    # W8. Rank by evidence strength, not by volume. The old key was -units,
    # which asked "which owner does the corpus hold most about" -- a question
    # whose answer is the same for nearly every prompt, and W3 measured the
    # consequence as a +0.756 rank correlation between unit count and routing
    # frequency. Units remain the tie-break and remain reported.
    #
    # W9 puts STRUCTURAL strength ahead of lexical strength, and the order is
    # the claim: an owner that BUILDS one of the matched terms outranks one
    # that merely shares vocabulary with the prompt, however much of it. The
    # lexical key is untouched behind it, so owners with equal structural
    # support (including the very common case of none at all, when the
    # projection is unusable) keep exactly W8's ordering. That is what makes
    # this reversible: delete the first element of the key and the selector is
    # W8 again, byte for byte.
    #
    # The key lives in `_rank_key` as ONE line rather than inline across two.
    # That is not style: a mutation anchor is a contract with the source, and
    # this estate has already measured that a two-line anchor cannot be
    # matched reliably on a CRLF checkout. W9's own edit rotted two W8 anchors
    # here, and a one-line key is what stops the next edit doing it again.
    owners.sort(key=_rank_key)
    return Selection(
        owners=tuple(owners[:MAX_OWNERS]), corpus_id=corpus_id,
        population=population, considered=len(rows),
        excluded_authority=excl_auth, excluded_lifecycle=excl_life,
        excluded_semantics=excl_sem, rejected_applicability=rejected,
        rejected_generic=generic,
        applicable_units=applicable, below_owner_floor=below_floor,
        duplicates_suppressed=dup, prompt_terms=len(terms),
        distinctive_required=need_distinct,
        rejected_below_length_bar=below_bar,
        structural_status=proj.status,
        rejected_no_attribution=no_attribution,
        classes_present=tuple(sorted(classes)),
        classes_unsupported=tuple(sorted(classes - set(SUPPORTED_CLASSES))))


#: The lead sentence of the novelty gate's obligation. It is that consumer's
#: frame -- "question 4 of the novelty proof" -- and was the only frame when
#: there was only one consumer. W6 added a second, where there is no question
#: 4, so the lead became a parameter rather than a constant. The SELECTION is
#: not consumer-specific and is not parameterised; only the sentence that
#: introduces it is, which is rendering, not authority.
NOVELTY_LEAD = ("UCR-CIF holds ADJUDICATED evidence that this is already "
                "owned. Question 4 of the novelty proof is therefore not "
                "open -- it is named, per owner, and the burden is to REFUTE "
                "these with file:line evidence, not to assert novelty:")


def routing_obligation(sel: Selection, lead: str | None = None) -> str | None:
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
    lines = [lead or NOVELTY_LEAD]
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


def main() -> int:
    """Explain a selection: why these owners, and what happened to the rest.

    Observability without a second store. A mission must be able to say which
    dispositions were considered, which applied, which did not and why -- and
    because selection is deterministic over (proposal, corpus), re-running
    this reconstructs any obligation the gate ever emitted. Persisting a
    decision log instead would create exactly what this wave exists to close:
    durable state whose only claimed consumer is a future reader.
    """
    import argparse

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--explain", metavar="TEXT",
                    help="the proposal text to select against")
    ap.add_argument("--explain-file", metavar="PATH",
                    help="read the proposal text from a file instead")
    ap.add_argument("--json", action="store_true",
                    help="emit the selection as JSON and nothing else")
    a = ap.parse_args()
    if a.explain_file:
        text = Path(a.explain_file).read_text(encoding="utf-8-sig")
    elif a.explain is not None:
        text = a.explain
    else:
        ap.error("one of --explain / --explain-file is required")
        return 2

    sel = select_for(text)
    if a.json:
        print(json.dumps(sel.to_dict(), indent=2, ensure_ascii=False))
        return 0

    print(f"corpus        {sel.corpus_id or '(unknown)'}")
    if sel.refusal:
        print(f"REFUSED       {sel.refusal}")
        print("              nothing was routed, and this is a statement "
              "about the store, not about the proposal.")
        return 1
    print(f"considered    {sel.considered} rows")
    print(f"  authority   -{sel.excluded_authority}  not reviewed "
          "(candidate, refuted, abstained or unresolved)")
    print(f"  semantics   -{sel.excluded_semantics}  class not routable here"
          + (f" {list(sel.classes_unsupported)}" if sel.classes_unsupported
             else ""))
    print(f"  lifecycle   -{sel.excluded_lifecycle}  named owner no longer "
          "in this repository")
    print(f"  population   {sel.population} authoritative units survived "
          f"(floor {MIN_AUTHORITATIVE_POPULATION})")
    print(f"  not about    -{sel.rejected_applicability}  fewer than "
          f"{MIN_TERM_OVERLAP} shared terms")
    print(f"  too generic  -{sel.rejected_generic}  shared terms, none "
          f"distinctive (<= {DISTINCTIVE_MAX_HOLDERS} owners)")
    print(f"  too thin     -{sel.rejected_below_length_bar}  distinctive "
          f"evidence, but fewer than {sel.distinctive_required} for a prompt "
          f"of {sel.prompt_terms} terms")
    print(f"  applicable   {sel.applicable_units}  "
          f"({sel.below_owner_floor} below the per-owner floor of "
          f"{MIN_UNITS_PER_OWNER}, {sel.duplicates_suppressed} duplicate)")
    if sel.rejected_no_attribution:
        print(f"  no structure -{sel.rejected_no_attribution}  owner holds no "
              "matched term structurally (M3 clause ENABLED)")
    print(f"prompt terms  {sel.prompt_terms}")
    # W9. The projection's standing is printed whatever it is, because a run
    # with no structural contribution and a run that could not consult the
    # projection produce the same-looking owner list.
    print(f"structural    {sel.structural_status}"
          + ("" if sel.structural_usable
             else "  -- structural evidence UNAVAILABLE this run; ranking "
                  "fell back to W8 lexical order. This is not a statement "
                  "that these owners lack structure."))
    if not sel.owners:
        print("\nno owner routed. The population was real, so this is an "
              "answer about the proposal.")
        return 0
    print("")
    for o in sel.owners:
        print(f"  {o.owner}")
        print(f"      structural {o.structural_strength:.2f} (rank key) | "
              f"lexical {o.strength:.2f} | units {o.units}")
        print(f"      terms {', '.join(o.terms)}")
        if o.attributed:
            print(f"      BUILDS  {', '.join(o.attributed)}  "
                  "(defines / is named for / registers)")
        elif sel.structural_usable:
            print("      BUILDS  nothing it matched on -- lexical support "
                  "only")
        print(f"      uids  {', '.join(o.uids)}")
        if o.sample:
            print(f"      e.g.  {o.sample}")
    print("\n" + (routing_obligation(sel) or ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
