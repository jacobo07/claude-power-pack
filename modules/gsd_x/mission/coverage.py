"""Required-input closure over a structured facts document (GSDX-M06, F7).

THE DEFECT. A gating fact that NO producer ever tried to establish appears in no
bucket of `FACTS.json` -- not `facts[]`, not `not_held[]`, not `unknown[]`. The
blindness channel added by GSDX-M05 reads the `unknown[]` bucket, so it cannot
see that fact; `_has()` is set-membership, so no obligation derives; and
`project_closure` can only block on obligations that exist. Measured on two
roots with the same INTENT and README:

    prose       -> DO-1 ACCEPTED, check exit 1
    structured  -> derived 0,     check exit 0, unmeasured_facts []

So dropping a `FACTS.json` into a fresh mission root silently deleted every
obligation the prose adapter would have derived, and the gate reported green
while asserting that nothing was unknown. The producer's own docstring already
named the three worlds a single absence collapses -- measured-false, could-not-
measure, and *nobody ever asked*. GSDX-M05 closed the first two. This closes the
third.

WHY THE REQUIRED SET IS THE GATING SET, AND WHY THAT IS NOT "EVERYTHING".

The prose adapter evaluates ALL TEN patterns against the text, every time, by
construction. That is what makes it complete: absence of an obligation there
means ten predicates were asked and none matched. A structured document that
discloses one name out of six gating ones has been asked one question. The
cutover loss is exactly that arithmetic, and the fix is to require the document
to answer the same questions the adapter answers.

`GATING_FACT_NAMES` is that set and nothing wider. The vocabulary's other four
names -- the three ENRICHING reads and the one ORPHAN -- are NOT required:

  * an enriching fact extends an obligation that exists either way, so an
    undisposed one costs a sentence of explanation and never a verdict;
  * an orphan fact is read by no operator at all and can never change one.

Requiring the whole vocabulary would turn a ten-name dictionary into a universal
prerequisite list, which is the ceremony tax `obligation.py` warns about and the
reason RESUMPTION item 11 exists. Requiring none of it leaves F7 open. The line
between them is the gating/enriching distinction the estate already computes.

DEAD OPERATORS REQUIRE NOTHING FURTHER. `_has()` is `all(...)`, so an operator
with any one of its gating facts measured FALSE can never fire. Demanding its
remaining gating facts would be production nobody can act on: the obligation
cannot derive whatever the answer turns out to be. Such an operator is DEAD and
its siblings drop out of the required set.

WHAT THIS DELIBERATELY DOES NOT DO. It does not run the prose extractor as a
coverage oracle over the same text. That was the first design and it is
unsound in the direction that matters: the extractor's documented dominant
failure is a SILENT MISS (`obligation.py:162-170` -- "each new wording has cost
exactly one more verb"), so a miss would leave the operator inactive, require
nothing, and exit 0. The frequent error would have been the fail-open one. And
`README.md`/`INTENT.txt` reach the CLI through `_read()`, which refuses nothing
and returns "" for an absent file, so a terse README would have lowered the
requirement floor with no refusal and no trace in the receipt. A floor an author
can lower by writing less is not a floor.

UNPRODUCED IS NOT UNKNOWN. `unknown` means a producer tried and could not
measure. `UNPRODUCED` means nobody asked. Both block, and they are kept apart
because they need different fixes -- one is a measurement to repair, the other a
producer to write. Collapsing them would commit, inside this module's own
output, the same category error it exists to end.
"""
from __future__ import annotations

# `_READS` is the single declared source of the gating/enriching split, and
# tools/test_gsd_x_facts_v2.py walks obligation.py's AST to prove that table
# equals the source. Importing it here reuses that guarantee rather than
# building a second table nothing reconciles.
from .obligation import _READS

__all__ = ["operator_gating", "dead_operators", "required_facts", "unproduced"]


def operator_gating() -> dict[str, frozenset[str]]:
    """{operator name: the facts it GATES on}. Enriching reads are excluded."""
    return {op: frozenset(gating) for op, (gating, _enriching) in _READS.items()}


def dead_operators(not_held: set[str] | frozenset[str]) -> frozenset[str]:
    """Operators that can never fire because a gating fact was measured FALSE.

    `_has()` is `all(...)`: one false gating read is enough, and no value of the
    remaining reads can revive the operator.
    """
    nh = frozenset(not_held)
    return frozenset(op for op, gating in operator_gating().items() if gating & nh)


def required_facts(not_held: set[str] | frozenset[str] = frozenset()) -> frozenset[str]:
    """Gating facts this mission's document must dispose of.

    Every gating fact of every operator that is still alive. A dead operator
    contributes nothing, because producing its siblings could not change a
    verdict either way.
    """
    dead = dead_operators(not_held)
    return frozenset(
        name
        for op, gating in operator_gating().items()
        if op not in dead
        for name in gating
    )


def unproduced(held: set[str] | frozenset[str],
               not_held: set[str] | frozenset[str],
               unknown: set[str] | frozenset[str]) -> tuple[str, ...]:
    """Required gating facts that appear in NO bucket of the document.

    Sorted, so a receipt and a gate message name them in a stable order and a
    diff of two runs is readable.
    """
    disposed = frozenset(held) | frozenset(not_held) | frozenset(unknown)
    return tuple(sorted(required_facts(not_held) - disposed))


def unproduced_for(factset) -> tuple[str, ...]:
    """`unproduced()` over a loaded `structured_facts.FactSet`."""
    return unproduced(
        held={f.name for f in factset.held},
        not_held={n.name for n in factset.not_held},
        unknown={n.name for n in factset.unknown},
    )
