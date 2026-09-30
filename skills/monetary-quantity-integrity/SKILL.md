---
name: monetary-quantity-integrity
description: Money and unit-integrity doctrine. Use when code or analysis adds, subtracts, sums, divides or compares monetary amounts: currency, majors vs cents, basis, date, observed vs derived; field suffixes like _usd or _cents; thresholds compared against amounts; ratios such as ROAS or markup; FX conversion; empty provider reads (not called vs zero vs rejected); requested vs documented vs live-observed provider fields; ratchet gates over monetary columns. Core rule - an amount travels with its qualifiers as fields, or it cannot be combined with another amount.
---

# Monetary Quantity Integrity

A number that cannot say what it measures is not a measurement. For money the
qualifiers are the currency, the unit scale (majors vs cents), the basis it is
charged on, the date it was true, and whether it was observed or derived. Each
one that lives outside the data is a defect waiting for a second producer.

## The rule

**An amount travels with its qualifiers as fields, or it cannot be combined with
another amount.**

Field names do not count. `total_price_usd`, `amount_eur`, `spend_usd` and
`fee_cents` say their denomination to a human reader and nothing at all to the
expression that adds, subtracts or `SUM()`s them. The aggregate is where this
shows: `SUM(total_price_usd)` over rows that each record their own currency in a
column nobody reads is the entire defect in one line.

## Two answers, and they are not the same answer

- **Two known qualifiers that disagree → refuse.** There is nothing to go and
  find out; you have both answers and they cannot be combined. This is a caller
  error, and it raises.
- **A qualifier that is undeclared → report a gap** naming what would close it.
  Absence of a declaration is not evidence of a bad number.

Collapsing these two loses the distinction between "we could not establish this"
and "we established two incompatible things", which need different fixes.

## Do not convert without an authorised source

Conversion needs a rate, a rate date, a provider and provenance. Without all
four you are inventing financial truth, and a rate invented inside a P&L is
indistinguishable afterwards from one that was real. Refusal composes; invention
does not.

Before building conversion, check there is a consumer: grep for `fx`,
`exchange_rate`, `convert`, `to_usd`, `forex`. If the estate has none, what you
need is refusal to mix, not an FX service.

## Qualify at the authority, and check the qualifier was ever asked for

A guard beside the reader protects that reader. The party that knows the
denomination is the one that fetched the value, and every other consumer
downstream of it stays exposed. So the fix belongs at the writer.

**Before designing how to carry a qualifier, check whether the source already
states it.** It usually does, and the loss is nearer than it looks: a scraper's
search path extracted `currencyCode` while its detail path — the one that wrote
the rows — dropped it and renamed the value `price_usd`; an ads integration asked
its endpoint for `campaign_id,spend,impressions,clicks,date_start` when that same
endpoint serves `account_currency`. Neither had lost the denomination in transit.
Neither had asked for it.

Two consequences worth stating separately:

- **A derived value inherits; a supplied value does not.** Scaling a quantity by
  a plain number cannot change its denomination, so a figure computed as
  `cost × 3.3` is denominated in whatever `cost` was. A figure the caller handed
  you carries only what the caller declared. Two fields, even when they look like
  siblings on one row.
- **A threshold is a quantity too.** A constant named `cogs_max_usd` compared
  against an amount of unproven denomination is this defect wearing the costume
  of a business rule. Eighteen euros passed a twenty-dollar ceiling on the
  strength of `18 < 20`. Give the threshold's own denomination a name that the
  comparison reads, not a suffix that a human reads.

## A ratio hides what a sum reveals

A sum of unlike quantities produces a magnitude somebody might question. A
quotient of unlike quantities produces a perfectly ordinary number with no unit
left to contradict it. Revenue in euros over spend in dollars is a ROAS of 2.4;
an operator's retail target over a scraped supplier cost is a markup of 3.2 that
then gates a real sourcing decision.

"Dimensionless" is not "always comparable". A ratio of like quantities is
dimensionless *because* the units cancel. If they were never the same, nothing
cancelled.

Check the two qualifiers before the division, never infer validity from the
result. When comparability cannot be established, emit the number with a sibling
flag that says so rather than silently — and prefer the flag to removal when the
value crosses a published contract.

The sharpest version of this is a **guard** built on a comparison. A refund cap
that checks a refund against an order total, across two currencies, does not
report a wrong number: it reports that the cap held while letting through a
refund larger than the order. A guard that cannot evaluate must never return the
same answer as a guard that passed — give it a third outcome.

## Zero has no currency

Zero euros and zero dollars are the same quantity. Demanding a denomination for
it refuses a computation that is correct — over-strict is its own wrong answer.
Exempt zero explicitly, in the code, with the reason.

## Absence is not the ambient default

An empty window has no currency, and that is not USD. A missing declaration does
not inherit the currency of the nearest neighbour, the first marketplace the
system integrated, or the developer's home country. This is `unknown ≠ zero`
applied to a denomination.

## A name that lies is not always renamed

When a misleading field crosses a published contract — a wire format, a client
library, another team's consumer — renaming it turns a local semantic problem
into a cross-domain break. Add the qualifier as a sibling field that states what
the name gets wrong, so a consumer can ask instead of assume. **A correction a
consumer can read beats a correction that breaks a consumer.** Record why the
rename was declined, or someone will "fix" it later without the context.

## Reuse the estate's vocabulary

Before inventing `PROJECTED` / `ACTUAL`, grep for what is already in use —
`OBSERVED` / `INFERRED`, `measured` / `modelled`, `expected` / `realized`. A
third vocabulary for one distinction is worse than the second one.

Use ISO 4217 alpha-3 for currency; if the codebase already uses ISO 3166 for
countries, this is the same convention rather than a new one.

## Enforce with a ratchet, not a clean-bill gate

A gate that is red on arrival gets disabled within a week. When the existing
population is large:

1. Enumerate the population **structurally** — from schema metadata, model
   registries, or type annotations — never by grepping for the qualifier's name.
   Grepping for the name of a thing cannot find the places where it is missing.
2. Freeze the current offenders in an explicit inventory, **one reason per
   entry**. An exemption with no reason cannot be evaluated later.
3. Fail when the population grows. New debt becomes a decision in a diff.
4. Assert the already-qualified stay qualified.
5. **Assert the inventory has no stale entries** — an entry whose table has since
   been fixed must be deleted, or the list becomes a permanent excuse and the
   ratchet stops turning.
6. Ship a positive control: prove the sweep found something, and drive the red
   branch. A detector that stopped detecting reports the same green as one that
   works.

**A red-branch drill decays the moment its example is fixed.** The drill that
proves the ratchet can fail has to name a real current offender. Fix that table
and the drill is asserting about a table that no longer offends — so it must
fail loudly rather than pass vacuously, and be re-pointed with each turn. In one
session the inventory turned three times and the drill went red on the second;
that redness is the feature. A drill aimed at a permanently-safe subject is a
test of nothing that reports green forever.

**Expect the ratchet to turn more often than you plan for.** Qualifying one
table changes what the enumeration finds, so the stale-entry clause fires again
on the next run. That is the mechanism working; budget for it rather than
treating each red as a surprise.

**The resolution to the decaying drill: give it a synthetic subject.** After the
drill had been re-pointed twice — and would have decayed a third time — the fix
is to stop naming a real table at all. Build a throwaway table in a scratch
metadata object carrying a monetary column and no currency, and run the *same
predicates the gate composes* against it. That represents the class rather than
an instance: it cannot be fixed out from under the assertion, it still exercises
the real logic, and it keeps working on the day the last real offender is
qualified — at which point a drill pinned to a real subject would have had
nothing left to assert. Ship the green half beside it (the same synthetic table
*with* a currency), or a predicate that flagged everything would pass the red
branch and look like a working detector.

A drill whose validity depends on a real defect surviving has an interest in that
defect surviving. That is reason enough on its own.

**Then hold the inventory from both directions.** Once the drill no longer
touches the real list, add the mirror of the stale-entry clause: every frozen
entry must name a table that is a genuine current offender. Stale-entry stops the
list rotting; this stops it being padded. Together they mean the inventory can
neither outlive its debts nor acquire imaginary ones.

**And do not put a count of the inventory in the prose beside it.** A docstring
saying "thirteen tables" over a list of seventeen went stale within two sessions
while reading as a measured fact, and nothing re-checks a sentence. The list is
the only place that cannot drift from itself.

## An empty answer must say why it is empty

A provider read that returns nothing has usually collapsed several worlds into
one value: the call was never made (a shadow or dry-run mode), the call was made
and the period genuinely had no activity, or the call was **rejected**. Measured
in two ad-spend adapters, all three returned an empty list, and the rejected case
opened an auth-halt record and then reported through the caller as
`rows: 0, halted: 0` — because the halt counter reflected a check taken *before*
the call.

For money this matters twice over. An unmeasured day surfaces as a zero-spend
day, and every ratio over that window then divides by a denominator nobody
observed — which is the ratio trap above with the missing evidence one level
further back: not a mismatched unit, an absent number.

Return the outcome beside the rows, with one property answering *may I read this
emptiness as a fact?* Keep the container iterable so consumers are unchanged. A
**missing** credential should still raise: nothing was asked and nothing refused
us, so it is configuration, and swallowing it hides an account that quietly
stopped reporting. A **rejected** credential on an auxiliary metadata call —
where the main data call has already succeeded — should not halt ingestion:
losing real amounts to fix a labelling gap trades a known gap for a larger one.
Ingest unqualified and say so.

## Requested is not observed

Track how strongly a provider fact is actually established, and never let the
weaker rung be reported as the stronger one:

**requested** (the field is in the call) → **documented** (the provider's docs
name it) → **fixture-observed** (parsing is driven against a constructed
response) → **live-observed** (a real response from a real account contained it).

Adding a field to a request qualifies nothing until a response comes back with
it. Pin the request itself with a test — the root cause is an unasked question,
so the assertion that the question is still being asked is what stops a silent
regression — and assert the maturity claim too where you can: a test that the
estate holds no credentials for that path turns "not live-observed" from prose
into a fact that has to be deleted deliberately.

Where the field name is documented rather than observed, make the miss honest:
every failure branch returns undeclared, and the log says which branch it took,
so the first real call diagnoses itself instead of silently ingesting a guess.

## DON'T

- **Don't trust an ad-hoc enumeration over the one inside the harness.** Sweeping
  a model registry from a standalone script found 16 tables; the same sweep run
  under the test harness found 17, because the harness imports more modules. The
  one it missed was the most load-bearing in the estate. Enumerate where the code
  under test actually lives.
- **Don't let a suffix stand in for a check.** `_usd`, `_cents`, `_ms`, `_pct` are
  claims. Ask of each: what reads this suffix? If the answer is "a human", the
  qualifier is not in the data.
- **Don't pick a majority value to break a tie.** Choosing the most common
  currency in a mixed window turns an answerable question into a number nobody
  can check.
- **Don't let a name assert an evidence class.** A field called `realized_cost`
  fed by the same estimator as `projected_revenue` is a projection; the two
  subtracted give a modelled margin that reads as a measured one.
- **Don't match on name alone.** Filter by type first: `refunded_at` matches
  "refund" and is a timestamp.

## Source

Incident evidence moved to `~/.claude/knowledge_vault/rules-evidence/monetary-quantity-integrity.md` (2026-09-28) so it is not re-read on every call. The rule text above is unchanged.
