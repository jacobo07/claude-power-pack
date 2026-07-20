# Dataset Contract — Crawl OS #02: Crawl Intent and Mission Compilation

Created 2026-07-20, before Part I is drafted, per `CRAWLOS_RESUMPTION.md` action 4 and the
PASO -1 requirement that an L/XL Crawl OS dataset establish its contract before any Part body.

## Ownership

This dataset elaborates the Crawl Intent Compiler engine chartered in Dataset #01's Part V
(the first of the fourteen engines), operationally: the mechanics of converting an
underspecified natural-language request — "read this repository," "research this market,"
"extract every function," "compare these competitors," "watch for when it changes," "build a
dataset from every source" — into a fully populated Crawl Mission Contract. It owns: the Crawl
Mission Contract schema itself (sixteen fields: objective, entities, expected sources, depth,
breadth, freshness, required evidence, permitted domains, authorized authentication, maximum
cost, maximum time, stop conditions, output schema, confidence-level requirement, update
policy, preservation obligation); the objective/entity extraction discipline; source
prediction; depth/breadth calibration; the compilation state machine from raw request to
validated contract; ambiguity and underspecification handling; mission templates for the six
canonical request shapes; mission revision/amendment; the compiler's own rejection taxonomy;
multi-source/multi-entity disambiguation; the handoff interface to downstream engines; mission
auditing and traceability; and this dataset's own failure taxonomy.

## Non-ownership (explicit, checked against Dataset #01 Part IV's test)

Does not own: general cost/token/resource accounting language — CO-01 (per Dataset #01's
composition point list and `CONSUMER_DECLARATIONS.md`'s Composition Points section) owns that
territory; this dataset's cost-ceiling and time-ceiling fields are declared inputs a mission
carries downstream, never a costing engine reimplemented here. Does not own: confidence
computation or the CONNECT sufficiency scale — DRK-03 owns that (per Dataset #01 Part XVII);
this dataset's confidence-level-requirement field declares a required threshold a mission
carries, never computes or redefines the scale itself — the same composition boundary Dataset
#01 already drew, not re-litigated here, and the STOP #1 finding that a prior D2A family-sizing
FOLD verdict against DRK-03 was a false positive on the shared word "evidence" appearing in
field names, not a real overlap (`wiggly-sparking-dolphin.md`), stands. Does not own: the
Evidence Object schema or its lifecycle (Dataset #01 Part VII / Dataset #10 own that; this
dataset's required-evidence field is a mission-level declaration consumed by, not duplicating,
that machinery). Does not own: authorization or domain-permission logic (the future Dataset
#16 Authorization, Compliance and Safety owns deciding whether a domain or authentication
method is permitted; this dataset owns only populating the mission's declared fields for that
future engine to evaluate). Does not own: routing tool selection or the cost ladder (the future
Dataset #03 Acquisition Strategy Router owns that; this dataset hands off a compiled contract,
never selects a fetch strategy itself). Does not own: retention/freshness mechanics once
acquisition is underway (Dataset #10 Part XII owns the freshness window in operation; this
dataset's freshness field is the mission's initial declaration that Part XII's machinery later
operates against).

## Consumers

Primary: graphify, permanent, per `CONSUMER_DECLARATIONS.md`'s Tier 1 model — this dataset's
`.txt` file is indexed identically to every other Crawl OS dataset. Downstream execution
consumer: PLANNED `modules/crawl_os/mission_compiler.py`, per `CONSUMER_DECLARATIONS.md` row 2.
Secondary interface consumers, all PLANNED and stated honestly: the future Dataset #03
Acquisition Strategy Router (consumes the compiled contract as its routing input), the future
Dataset #16 Authorization engine (consumes the permitted-domains and authorized-authentication
fields), and Dataset #10's Evidence Provenance and Integrity Fabric (consumes the
required-evidence and preservation-obligation fields as inputs to its own already-sealed
lifecycle).

## Dependencies

Dataset #01 (all Parts, especially II, III, IV, V) — binding, sealed, cited throughout rather
than restated. Dataset #10 (Parts VIII, XII especially) — binding, sealed, cited for the
preservation-obligation and freshness-field composition points. DRK-03 (CONNECT vocabulary) —
composed with, not owned, per the same boundary Dataset #01 Part XVII already drew. CO-01 —
composed with for the cost/time-ceiling fields, per the family's Composition Points list; this
dataset never reimplements CO-01's budget accounting.

## Inputs / Outputs

Inputs: the Owner's or an upstream system's raw natural-language mission request; site memory's
prior knowledge of a target, when one exists (informing source prediction and depth/breadth
defaults); the estate's declared cost/time policy from CO-01 (as an external ceiling reference,
not recomputed here). Outputs: a fully populated, internally consistent Crawl Mission Contract
in the sixteen-field schema this dataset owns; a compilation audit trail recording which fields
were extracted directly, defaulted, or escalated for clarification; a rejection record when a
request cannot be compiled into a viable contract.

## Invariants

No Mission Contract field is ever silently fabricated in place of an actual extraction, a
declared default, or an explicit escalation (the same discipline Dataset #01 Part VII §7.9 and
Dataset #10 hold for the Evidence Object, applied here to the Mission Contract). No contract is
marked validated while a required field remains unpopulated. No contract is dispatched to a
downstream engine while it fails its own internal consistency check (for example, a maximum
cost below the floor a requested depth/breadth combination could possibly complete within). A
superseded contract, on revision, is retained in the mission's own change history, never
overwritten in place. A rejected request is recorded with its rejection reason, never silently
dropped.

## Failure taxonomy (this dataset's own, distinct from Dataset #01 Part XXII's family-wide catalog)

Silent field fabrication (inventing a plausible value instead of extracting, defaulting
explicitly, or escalating); over-eager default substitution (defaulting a field that should
have escalated for clarification); entity misresolution (compiling a contract against the
wrong real-world entity); missing stop-condition (a contract dispatched with no termination
trigger, risking an unbounded mission); authorization-field omission (dispatching without a
populated permitted-domains or authorized-authentication field); cost-ceiling omission
(dispatching with no maximum-cost field, an unbounded-spend risk;) and orphaned contract (a
contract compiled and validated but never actually dispatched to a downstream engine).

## Test strategy

Mirrors `tools/test_crawl_os.py`'s per-Part word-count-floor and FINAL LAW presence gates,
extended to this dataset's own 25 Parts, plus the same contamination-baseline discipline
already covering Dataset #01 and Dataset #10. No dedicated schema-citation check is required
the way Dataset #10 needed one, because this dataset owns its schema outright rather than
elaborating a schema Dataset #01 already owns — the citation discipline that matters here runs
the other direction, toward not reimplementing CO-01's or DRK-03's owned vocabulary.

## Completion contract

SEALED requires: 25/25 Parts at or above the 1,200-word floor; every Part closing with its own
PART N FINAL LAW; zero contamination hits beyond the audited estate-wide baseline; all
forward-references resolved; zero reimplementation of CO-01's cost/token accounting or DRK-03's
CONNECT confidence scale; this dataset's row already present and accurate in
`CONSUMER_DECLARATIONS.md` (verified, not re-written, since row 2 already exists and is
accurate); `CRAWLOS_RESUMPTION.md` updated with the sealed state; REMOTE_DELTA = 0 0 after a
pathspec-scoped commit.
