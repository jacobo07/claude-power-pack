# A Sample Row Is Not a Schema

Two instrument failures from one reality scan of `vault/datasets/gsd_x/claims.jsonl`
(2026-09-19, GSD X wave N3). Both produced a confident, well-formatted, wrong number,
and both were caught only by re-measuring on the next turn — not by re-reading.

## Trap 1 — reading one row's keys and calling it the schema

**What happened.** To report the dataset's schema I read the first row's property
names and published them:

    id, state, claim, evidence, instrument, date

The real union across all 69 rows is **fourteen** fields:

    id, state, claim, date, evidence, instrument, rationale, resolved_by,
    note, revisit_when, contradicted_by, authority, supersedes, owner

**Why it mattered.** The plan built on that reading proposed *adding* a `supersedes`
field. `supersedes` already existed. A design wave would have been spent implementing
a field the corpus had carried since 2026-09-15, and the review that caught it would
have been looking at the wrong diff.

**The mechanism.** In a sparse record format — JSONL, a document store, a wide table
with nullable columns, a protobuf with optional fields — *most rows do not carry most
fields*. Here the best-occupied optional field appears in 51 of 69 rows and the worst
in 1. Sampling any single row therefore under-reports the schema, and it does so
**silently and plausibly**, because what you get back is a real list of real fields.

**The rule.** The schema of a sparse format is the **union over every row**, with an
occupancy count per field. One row is a sample; a sample is not a contract. Print the
occupancy beside each field — `supersedes 1` is the fact that tells you the field
exists *and* that nothing uses it, which is a different and more actionable finding
than either "it exists" or "it is missing".

Classified **CLASE 2** (the plan assumed a repo state that was false) under
`iteracion-avanzada-universal.txt`.

## Trap 2 — PowerShell 5.1 returns no `.Count` for a single match

**What happened.** The occupancy census was computed as:

    ($rows | Where-Object { $_.$k }).Count

For every field matching **two or more** rows this printed a number. For the two
fields matching **exactly one** row — `supersedes` and `owner` — it printed **blank**,
because a PS 5.1 pipeline that yields a single object returns that object rather than
an array, and the object has no `Count`. Blank rendered in a right-aligned numeric
column and read as **zero occupancy**.

So the same census that under-reported the schema also reported the one field that
disproved the plan as absent. Two independent instrument errors pointing the same way
is not bad luck: both were built from the same convenience, which is to ask the data
for a shape instead of constructing the shape and asking the data to fill it.

**The rule.** Wrap every PowerShell pipeline whose cardinality can be 0 or 1 in `@()`
before taking `.Count`:

    @($rows | Where-Object { $_.$k }).Count

And treat a **blank** in a numeric column as an instrument failure, never as a zero.
A count that cannot distinguish "none" from "one" is not a count.

Classified **CLASE 4** (tool call failed silently).

## What the pair generalises to

Both are the same shape one level up, and it is the shape worth carrying:

> **An instrument that answers from whatever the data happened to hand it cannot
> report what the data did not hand it.**

A first row cannot report a field it lacks. A bare `.Count` cannot report a
cardinality its container does not expose. Neither returns an error; both return a
well-formed answer to a question you did not ask.

Ask of any census, before believing it: *could this have returned the other answer?*
A field-occupancy table built from one row can only ever return that row's fields. A
count that renders blank at one can only ever undercount.

## The finding that survived both errors

Measured the same day, and the reason the wave exists. The dataset gate
(`tools/test_gsd_x_dataset.py`) returns:

    GSDX_DATASET_PASS=6/6  threshold=6/6    exit=0

while the corpus it judges is **24 commits behind HEAD**. Every clause is honest —
fields present, vocabulary closed, companions bound, cross-references resolved, no
code fences, and the honesty clause satisfied by 4 contradicted and 9 unproven rows.
Nothing is contradicted, because the missing knowledge was never *asserted falsely*;
it was simply never asserted. A gate that can only detect contradiction is blind to
omission, and a green from such a gate over a stale corpus is indistinguishable from
a green over a current one.

That is the defect N3 exists to close, and this green is its "before" measurement.

## Source

**2026-09-19**, `claude-power-pack` @ `3e56322`, GSD X wave N3 reality scan.
Corrected by the Owner's own instruction to revalidate rather than inherit the prior
pane's numbers — the correction cost one turn; inheriting them would have cost a wave.
