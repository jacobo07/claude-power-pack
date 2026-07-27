# Cognitive OS — CO-13 — Observed Residency (what the memory hierarchy actually did)

> CO-04 defines the tiers, CO-05 the assets, CO-06 the eviction policy, CO-03 the
> cheapest-first cascade. Every one of them is a *design*. None had ever been placed
> beside a record of what the running system actually loaded, so the family's central
> claim — that the kernel keeps HOT minimal and pages the rest — had never been scored
> against production behaviour.
>
> CO-13 is that record. It is the family's first **measured** dataset: 1,720 residency
> observations drawn from 383 real sessions, the four findings they force, and the one
> production defect they exposed. It introduces no new mechanism. Its entire content is
> the distance between CO-04's doctrine and CO-04's behaviour.
>
> **Non-duplication contract (binding).** CO-12 owns how a metric must be *stated* — the
> Telemetry-Before-Claims triple of metric, source and value. CO-13 composes that contract
> and never restates it. CO-13 owns one thing CO-12 does not: the residency observation
> corpus itself and the findings it forces. CO-04/05/06 keep their mechanisms untouched;
> nothing here re-specifies a tier, an asset or an eviction rule.

---

## Part I — The corpus

### I.1 Where the observations were already being written

The residency observation stream was never missing. It was being produced continuously,
in production, by a surface that does not know the Cognitive OS exists.

| Producer | Destination | Volume measured 2026-07-27 | Fields |
|---|---|---|---|
| `tools/jit_skill_loader.py` telemetry writer | `vault/telemetry/jit_usage_<sid>.jsonl` | **384 files, 339,197 bytes, 1,720 rows, 383 sessions, 0 unparseable** | module · tier · bytes · budget · timestamp · session |
| the same loader's session-state writer | `~/.claude/state/jit-injected-<sid>.json` | **495 files** | the per-session resident set, consulted before every load |

This is the finding that reframes the family. A prior audit recorded that CO-06's
eviction score reads fields no surface writes. Half of that was true: the *fields* are
unwritten, but the *observations* are not missing. The loader's `tier` is CO-04's depth,
its `bytes` is the item size, its timestamp is the last-reference mark, and its resident
set is the working set. The gap is an adapter between two vocabularies for one physics —
not an absent instrument. Cheap to close, and impossible to notice from the code alone.

### I.2 What the corpus says

| Dimension | Observed |
|---|---|
| Loads at `full` depth | **880** of 1,720 |
| Loads at `active` depth (project spec) | 641 |
| Loads at `summary` depth | 195 |
| Loads at `discovery` depth (the 80-token pointer) | **4** |
| Distinct assets ever loaded | **6**, of 13 available |
| Assets never loaded once in 383 sessions | **7** |
| Two dominant assets | 528 loads each, across 303 sessions, ~4.0 MB combined |
| Knowledge-base families ever observed in the stream | **0 of 25** (11.8 MB) |

Every number above is a count over the corpus named in I.1, reproducible by re-reading it.
Per CO-12's contract each carries its metric, its source and its value; none is an estimate.

---

## Part II — The four findings

### II.1 F1 — The tier ladder runs inverted

CO-04's governing rule is that promotion pages in the *minimum depth that satisfies the
need*, and that the cheapest possible presence is a pointer rather than content. Production
does the opposite: `full` is the single most common depth, and the pointer tier was chosen
**four times in 1,720 loads**. The ladder exists in the loader's code and is almost never
descended.

The cause is structural, not careless. Depth is selected from prompt verbs, and the pinned
default is `summary` with `full` on a broad verb class — a policy chosen because `full` was
the pre-retrofit behaviour and therefore the low-regression default. That is a defensible
engineering choice and it is also, measured, a standing inversion of the doctrine the
family declares. Both statements are true, and only the measurement makes the second one
sayable.

CO-04 III.1 already names this failure mode — *over-eager promotion (bloat)*, detected by
HOT content the task never referenced. The detector was never wrong. It had simply never
been run, because nothing was comparing the load record against use.

### II.2 F2 — Admission is decided by vocabulary, not by evidence

The real admission gate on context is not any Cognitive OS module. It is the loader's
trigger table, and it had never been scored.

Replayed over **2,513 real user prompts**, the GraphQL trigger fired **85 times**. Of those,
**76 matched only on a generic engineering word** — `resolver` 40, `mutation` 25,
`subscription` 11 — against 14 that named GraphQL itself. A verbatim firing prompt reads
*"Created InitConfig resolver (Code node)"*: a workflow node, in a repository whose only
GraphQL file sits under a fixtures directory the walk already excludes. Each false firing
force-injected roughly 7.6 KB of Apollo context at `full` depth.

Narrowing the trigger to genuine GraphQL syntax, and keeping the filesystem fallback as the
safety net, moved the same corpus from **85 firings to 22, with zero newly-fired prompts** —
a strict subset, so nothing that used to be admitted for a real reason stopped being
admitted. Roughly **479 KB** of context is no longer injected across that corpus.

The general form matters more than the instance. **An admission gate whose vocabulary is
not domain-specific admits on coincidence.** Every trigger in the table is an unscored
admission gate of the same construction; this one was measured because the residency stream
made its cost visible. The others have not been measured and are not claimed to be clean.

### II.3 F3 — The knowledge corpus is not inside the physics at all

The hypothesis under test was that the 25 knowledge-base families are not tiered by heat.
The measurement answers it, and answers it in the negative direction: **they are not tiered
because they are never loaded by this mechanism.** Zero of 25 appear anywhere in 1,720
observations. The loader's denominator is a set of thirteen skill files; the 11.8 MB corpus
is reached, when it is reached at all, by an agent reading a file — an act this stream does
not observe.

The correct conclusion is therefore *not* to build dataset tiering. Tiering them would
optimise a context cost the system is not currently paying, which is the most expensive
kind of improvement: real work, real complexity, zero recovered tokens. The honest residual
is smaller and different — **the observation stream has no visibility into agent-initiated
reads**, so the true residency of the knowledge corpus remains unmeasured rather than
measured-and-fine. That is recorded here as an open question, not closed as health.

### II.4 F4 — Seven assets have never been loaded

Seven of thirteen available skill files were loaded zero times across 383 sessions. Under
CO-05's freshness discipline an asset that is never retrieved is a prune candidate; under
CO-06's conservative prune rule it is retained because dropping a useful asset costs a
re-derivation while keeping a dead one costs index space. Both rules are right, and neither
had the retrieval count that decides between them. It now exists.

---

## Part III — Contracts, failure modes, rollback, anti-patterns

### III.1 The adapter contract (what CO-06 needs, and from where)

Stated so it can be built once, correctly, rather than rediscovered. A residency item is
derivable from one telemetry row plus the session state file: the item identity is the
module name; the depth is the row's tier; the size is the row's bytes; the last-reference
mark is the row's timestamp, ordered within its session; and membership in the working set
is presence in that session's resident set. Nothing else is required, and nothing in the
producer needs to change.

The adapter is deliberately **not** built by this dataset. CO-06's eviction candidate list
has no live consumer, so an adapter shipped now would feed a reader that nothing calls —
the mirror image of the defect this dataset documents. The adapter lands when the CO-04 and
CO-06 composition lands, in that order, per the dependency chain the OWNER_QUEUE records.

### III.2 Failure modes of this dataset

- **Sample bias.** The corpus is one operator's sessions on Windows. A different fleet may
  invert none of these findings or all of them. Every number here is a measurement of this
  installation, never a general law about loaders.
- **Load is not use.** The stream records what was injected, not what was referenced. F1's
  claim is that the ladder is descended rarely, which the data supports; the stronger claim
  that the injected context went unused is **not** supported here and is not made.
- **A measured mechanism becomes a targeted one.** Once loads are counted, the count can be
  optimised. The countermetric is CO-01's work-per-cost: fewer loads is only an improvement
  if verified work holds.
- **Freezing the corpus.** These findings decay. A re-run that reproduces them is evidence;
  citing today's numbers a year from now is not.

### III.3 Rollback protocol

CO-13 is an observation record and has nothing to roll back. The one behavioural change it
motivated — the narrowed trigger — reverts in a single commit, and its safety net is the
filesystem fallback that already catches a genuine project by its files rather than by its
words. The fail-safe direction is the pre-existing one: admit more, spend more.

### III.4 Integration contract

- **CO-04** — supplies the depth ladder this dataset scores; receives F1, its first
  behavioural evidence, and III.1's adapter shape.
- **CO-05** — receives the retrieval counts in F4 that its freshness rules presuppose.
- **CO-06** — receives the field mapping in III.1; unchanged until composed.
- **CO-01** — the countermetric for every reduction claimed here.
- **CO-12** — owns the statement contract; CO-13 supplies triples that satisfy it.
- **PM-05** — its net-positive ledger is the same shape as F2's admission scoring, one
  layer up: prefetch scores its own guesses, and triggers should score theirs.
- **`tools/jit_skill_loader.py`** — the producer. It is not asked to change; only to be read.

### III.5 Anti-patterns (forbidden)

- **Scoring a mechanism by whether it could work.** A passing unit test proves capability
  when invoked, never behaviour in production. The family held eleven designs and zero
  observations for a month.
- **Building the optimisation before the measurement.** Dataset tiering was a reasonable
  proposal until the stream showed the cost was not being paid.
- **Reading an admission gate's vocabulary as its specificity.** A word that occurs in the
  target domain is not thereby evidence *of* that domain.
- **Treating a wrong hypothesis as a wasted one.** F3 is a negative result and it prevented
  a build; that is the highest return this dataset produced.
- **Citing these numbers without re-running them.** They are a snapshot, and they are dated.

---

### CO-13 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| Every figure is a count over `vault/telemetry/jit_usage_*.jsonl`, reproducible by re-reading it | As of 2026-07-27 | That the figures still hold later — re-run, do not cite |
| The residency producer is named, live, and requires no change to be consumed | Always | That an adapter exists — deliberately not built (III.1) |
| The dataset-tiering hypothesis is answered with evidence, in the negative | Measured, 0 of 25 families observed | That the knowledge corpus is *not* being read — only that this stream cannot see it |
| The trigger narrowing is a strict subset: 85 firings to 22, zero newly fired | Same 2,513-prompt corpus | That the other triggers are clean — they are unmeasured |
| Load is recorded; use is not | Always | Any claim that injected context went unreferenced |

**Guarantee level (honest):** CO-13 is an **observation layer** — rung-1. It enforces
nothing, blocks nothing and changes no runtime behaviour by itself. Its whole authority is
that it replaces assertion with a count, on one installation, on one date. Two of its four
findings (F3, F4) are negative results that stopped work rather than starting it, which is
the outcome this dataset was written to make possible.
