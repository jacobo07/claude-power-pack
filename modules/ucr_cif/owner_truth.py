"""UCR-CIF W10 -- arm-independent owner ground truth.

W9 measured rank movement against a truth set derived from the SELECTOR'S
OWN OUTPUT: `label_case(case.owners_routed, touched, ...)` credits an owner
only if that owner was routed. For the activation question W7 built it for,
that is correct -- the question there is "was the thing we said useful".

For a RANKING question it is a leak, and the direction of the leak flatters
the treatment:

    A case whose true owner the treatment DROPS produces no owner hits, so
    the case is re-labelled NOT_RELEVANT and leaves the measured population
    altogether -- instead of counting as the loss it is.

So suppressing a true owner improves the apparent score, which is the exact
failure PR-W10-19 exists to forbid. The truth set must not be a function of
the arm.

WHAT THIS MODULE DOES INSTEAD
The truth set is computed against the full authoritative OWNER UNIVERSE --
every owner the corpus holds an adjudicated disposition about, 40 of them at
the W9 seal -- and never against what any arm proposed:

    truth(case) = { owner in UNIVERSE : the engineer's commits in the window
                    after this prompt touched a path that owner covers }

An owner absent from an arm's list is then a MISS with a name, and an owner
present in one arm and not the other is an eviction or an admission rather
than a case that quietly vanished.

INHERITED LIMITS, NOT REPAIRED HERE. This is still the POST-HOC
git-behaviour proxy of `reach_ground_truth`, with every caveat that module
states: work landing in an owner path does not prove the agent was ignorant
of it, work landing elsewhere does not prove the owner irrelevant, and no
commits is UNLABELLED rather than negative. W10 widens the population and
removes the arm dependence. It does not make the proxy a fact.
"""
from __future__ import annotations

from collections import Counter

#: A row is authoritative when W3's adjudication promoted it. The owner is
#: carried on `proposed_owner`; `disposition` is what makes it authority
#: rather than a candidate, and W2's lesson was that conflating the two is
#: how a candidate becomes a fact.
_AUTHORITATIVE = "EXTEND_EXISTING_OWNER"

#: Below this the universe read is not believable: a sweep that silently
#: matched nothing and a corpus with no authority are the same observable.
#: 40 owners are recorded at the W9 seal; a third of that is loose enough
#: for ordinary attrition and tight enough to catch a broken read.
MIN_OWNER_UNIVERSE = 13


def owner_universe(rows) -> tuple[str, ...]:
    """Every owner the corpus holds adjudicated authority about.

    Sorted for a stable fingerprint. Raises rather than returning a short
    list, because a truncated universe silently shrinks every truth set
    downstream and would read as "the treatment lost fewer owners".
    """
    owners = {r.get("proposed_owner") for r in rows
              if r.get("disposition") == _AUTHORITATIVE}
    owners.discard(None)
    owners.discard("")
    if len(owners) < MIN_OWNER_UNIVERSE:
        raise RuntimeError(
            f"owner universe is {len(owners)}, floor {MIN_OWNER_UNIVERSE} -- "
            "the ledger read is suspect; refusing to compute truth sets "
            "against a population that may have been silently truncated")
    return tuple(sorted(owners))


def owner_units(rows) -> Counter:
    """Authoritative units per owner, for stratified reporting."""
    return Counter(r.get("proposed_owner") for r in rows
                   if r.get("disposition") == _AUTHORITATIVE
                   and r.get("proposed_owner"))


def truth_owners(touched: set[str], universe) -> tuple[str, ...]:
    """Owners whose paths the post-prompt commits actually touched.

    Independent of both arms by construction: nothing here reads a routed
    list, a rank, a structural score or a selector output of any kind.

    An owner recorded as a FILE (`agents/oneshot-architect-auditor.md`,
    `tools/jit_skill_loader.py`) matches on equality; one recorded as a
    DIRECTORY matches on the path separator, never on a bare string prefix
    -- `modules/code-review` must not be credited by `modules/code-reviewer`.
    """
    hits = []
    for owner in universe:
        norm = owner.rstrip("/")
        if any(p == norm or p.startswith(norm + "/") for p in touched):
            hits.append(owner)
    return tuple(hits)


#: Representation modality by structural share. W9's measured reason not to
#: promote is that an owner shipping its capability as MARKDOWN is credited
#: almost nothing by a signal that reads symbols, filenames and registry
#: keys -- `governance-overlay` at 13.7 % against a 23.7 % routing share and
#: a 21.1 % share of oracle hits. A treatment that improves code-owner
#: precision while demoting real prose owners could pass an aggregate test
#: and still be unacceptable, so the effect is reported per modality.
#:
#: The boundary is the corpus's OWN aggregate, 21.0 % of (unit, term) pairs,
#: rather than a number chosen here: an owner credited below the corpus
#: average is under-served by this evidence family BY DEFINITION, which is
#: the property that matters, and it needs no new taxonomy to state.
PROSE_SHARE_MAX = 0.21


def structural_share(rows, projection) -> dict:
    """Per-owner fraction of its (unit, term) pairs held STRUCTURALLY.

    Returns {} when the projection is unusable, never a dict of zeros: an
    owner that builds nothing and a projection that could not be read are
    the same number and opposite facts, and collapsing them would report
    every owner as prose-form the day the projection breaks.
    """
    if projection is None or not projection.usable:
        return {}
    held: dict = {}
    total: dict = {}
    for r in rows:
        if r.get("disposition") != _AUTHORITATIVE:
            continue
        owner = r.get("proposed_owner")
        if not owner:
            continue
        for term in r.get("evidence_terms") or ():
            total[owner] = total.get(owner, 0) + 1
            if projection.holds(owner, term):
                held[owner] = held.get(owner, 0) + 1
    return {o: (held.get(o, 0) / n) for o, n in total.items() if n}


def modality(owner: str, shares: dict) -> str:
    """`code`, `prose` or `unknown` -- never a silent default to one pole."""
    if not shares or owner not in shares:
        return "unknown"
    return "prose" if shares[owner] <= PROSE_SHARE_MAX else "code"


def rank_of(owner: str, ordered) -> int | None:
    """0-based position of `owner`, or None when it is absent.

    None is not a large rank. It is a different outcome -- the owner never
    reached the agent at all -- and the caller must keep it distinct or an
    eviction becomes indistinguishable from a demotion.
    """
    try:
        return list(ordered).index(owner)
    except ValueError:
        return None


__all__ = ["MIN_OWNER_UNIVERSE", "PROSE_SHARE_MAX", "modality",
           "owner_units", "owner_universe", "rank_of", "structural_share",
           "truth_owners"]
