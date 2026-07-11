# DRK-05 — Institutional Debt & Decision Memory

> The over-time substrate of the Decision axis. DRK-00 fixed the Decision Object, the append-only
> Decision Registry, the ten-verdict ontology and the Tipo A/B/C reversibility vocabulary; DRK-01
> built the nine-stage sieve whose Stage 6 checks each candidate against precedent; DRK-02 measured
> the per-decision entropy delta and the Tipo-B decay vector but explicitly handed the *running*
> ledger to DRK-05. This dataset supplies the two linked mechanisms that turn a pile of Records into
> an institution: (a) the multi-axis **decision-debt ledger** — a decision made invisibly, without
> recorded reasoning, without alternatives, with no owner, or now invalidated by context, is a
> liability that accrues cost — and (b) the **decision-memory / precedent registry** that makes the
> append-only Registry answer "why did we decide this, five years on" and detect precedent reversals.
> **Parent it DEEPENs:** SDD-OS Parte V §12 (Decision Debt), §22 (Canonical Decision Patterns), §23
> (Anti-Pattern Registry), §24 (Decision Genome), §25 (Future Auditability), §26 (Decision Fitness
> Functions), §27 (Governance KB), §28 (Institutional Memory) — each a two-to-five-line enumeration
> there, given mechanism here. **Cross-references (never re-narrated):** DRK-02 (owns the per-decision
> entropy delta and the reversibility decay vector — DRK-05 only integrates them); the Cognitive Leak
> Taxonomy C70 (owns *cognitive* debt — the non-token drain of stalled/unbounded sessions — which
> decision debt is a sibling of, never a re-statement); UKDL (owns rules and the `T-*` trap registry
> as negative knowledge); the arch-decision skill (owns precedent-collision search, invoked at DRK-01
> Stage 6); ACIS (owns evidence levels `E0…E7`); FD DISCARD (owns the frontier discard ledger).

---

## PART I — DECISION DEBT: THE MULTI-AXIS LEDGER

### I.1 What decision debt is, and what it is not

SDD-OS Parte V §12 names a new category of debt in three example lines — "we don't know why it was
done," "we don't know who decided it," "we don't know what alternative existed" — and stops. DRK-05
gives it a mechanism. **Decision debt is the accrued liability a system carries when the *reasoning*
behind its decisions is missing, weak, unowned, or no longer valid.** It is distinct from every other
debt the stack already tracks, and the distinctions are load-bearing because conflating them is the
E3 Layer-Flattening error DRK-00 warns against:

- **Code debt** is a property of the *artifact* — a shortcut in the implementation. It is repaid by
  editing code.
- **Architectural entropy** (DRK-02 §II.5) is a property of the *structure* — coupling, special-casing,
  surface area, consistency debt rising over time. It is repaid by refactoring structure. DRK-02 owns
  the per-decision entropy delta; DRK-05 integrates the running total (I.4).
- **Cognitive debt** is a property of the *session* — the non-token drain of a stalled or unbounded
  pane, owned end-to-end by the **Cognitive Leak Taxonomy C70**. DRK-05 does not re-narrate it; it
  only observes that decision debt is its sibling on the *decision* axis, not its duplicate.
- **Decision debt** is a property of the *reasoning* — the choice may be perfectly implemented, in a
  clean architecture, made in a healthy session, and *still* be a liability because nobody can
  reconstruct why it was made, what it discarded, who owned it, or whether its premises still hold.

The separation matters operationally: you cannot pay down decision debt by editing code or refactoring
structure. The only repayment is *reconstructing or re-authoring the reasoning* — which for an
orphaned decision may be impossible, making decision debt the one debt class that can become
permanently unpayable. That irreversibility is why the axis exists to *prevent accrual* at Record time
(DRK-01 Stage 2 flags a decision with one option and no discarded alternatives) rather than to
retro-repair it.

### I.2 The taxonomy of decision-debt axes

Decision debt is not a scalar. It accrues along six independent axes, each keyed to a required field
of the Decision Object (DRK-00 §I.3) that is absent, weak, or stale. The kernel measures each axis
per Record; the ledger is the sum over the Registry. Independence matters because a decision can be
perfectly documented yet invalidated-by-context (high on one axis, zero on another), and a single
"debt score" would hide which repayment is even possible.

| Debt axis | Accrues when | How it accrues cost | How it is measured |
|---|---|---|---|
| **Undocumented reasoning** | the `rationale` field is empty, vacuous ("seemed best"), or restates the choice instead of justifying it against the alternatives | every future reader must reverse-engineer intent or re-decide from scratch; the decision cannot be judged proportional (DRK-00 §I.3) or audited (§25) | % of Records whose `rationale` cites at least one discarded alternative by name |
| **Unexplored alternatives** | `options` has fewer than two genuine entries or `discarded_alternatives` is empty — the Default Suspicion Rule violated at Record time | the system cannot know what it gave up; a later "why not X?" has no recorded answer, forcing a full re-litigation | % of Records with ≥2 real options and a reason recorded for each rejection |
| **Unrecorded owner** | no accountable party is attached to the Record — neither an Owner ratification nor a dispatching agent identity | when the decision is questioned, there is no one to ask and no one whose prediction can be scored (Parte VI accountability starves) | % of Records with a non-null owner/ratifier |
| **Invalidated-by-context** | a premise the decision rested on (an `assumption`, a `constraint`, a cited fact) has since changed, but the Record was never re-reviewed | the decision is silently wrong-for-now; its `predicted_consequences` were computed against a world that no longer exists | count of Records whose cited premises have a known contradicting later Record, un-superseded |
| **Unreviewed irreversible** | a Tipo-C (or a Tipo-B that has decayed toward C — DRK-02 §I.4) decision was acted on without reaching its L4 review tier | the highest-cost error class in the axis: a one-way door closed with no recorded evidence burden met | count of Tipo-C Records with review_tier < L4 or evidence < ACIS `E3` |
| **Orphaned decision** | the reasoning is *lost* — the Record exists but its rationale, evidence, or genome fields were never populated, or the dependency chain to its `problem` is broken | the terminal state of undocumented reasoning: not weak but *gone*; the decision now functions as an unexplained constraint on everything downstream | count of Records with a broken provenance chain (Parte V §5 Feature→Requirement→Decision→Evidence→Source) |

Each axis is a *rate* of accrual, not a one-time cost. An undocumented-reasoning Record costs a little
every time it is read and re-puzzled-over; an invalidated-by-context Record costs more the longer its
stale premise propagates through dependent decisions. The ledger's value is that it makes the accrual
*visible before it compounds* — the same reason DRK-02 records the entropy delta of each individually-
cheap reversible decision so the accumulation can later be surfaced.

### I.3 Priced debt is not bad debt — the known gamble

The most important calibration of this axis, and the one that separates it from a naive "all debt is
bad" linter, is that **decision debt taken knowingly is priced debt, and priced debt is a legitimate
engineering instrument.** A decision the kernel emits as `DEFER` (DRK-00 §II.2 — the decision is not
yet forced, deciding now spends optionality for no gain) is *deliberately* incurring a small,
recorded, bounded debt: "we chose not to decide this yet, here is why, here is the trigger that will
force it." That is indistinguishable in the ledger from the healthiest possible state *except* that it
is recorded as a conscious deferral with a repayment condition — exactly the shape of a Tipo-A known
gamble, where reversibility buys the right to be provisionally wrong (DRK-02 §I.1).

The distinction the ledger enforces is therefore not debt-vs-no-debt but **priced-vs-unpriced**:

- **Priced debt** carries a recorded rationale for the deferral *and* a repayment trigger (a date, a
  dependency resolving, a metric crossing). It is a `DEFER` or an `APPROVE-WITH-CONDITIONS` verdict
  whose conditions are on the Record. It is an asset — it preserves optionality at a known,
  monitored cost.
- **Unpriced debt** is a decision made invisibly, with no recorded reasoning and no repayment
  trigger — the §12 "we don't know why" case. It is a pure liability because nobody chose to incur it
  and nobody is watching for the moment it comes due.

The kernel never blocks priced debt — a knowingly-deferred reversible decision is precisely what
`block-narrow, recommend-wide` (DRK-01 §III.2) protects the right to make. It surfaces unpriced debt,
because an unpriced liability that nobody elected is the failure the axis exists to prevent. This is
why the ledger must distinguish a `DEFER` Record (priced) from a missing-rationale Record (unpriced)
even though both technically defer a full justification.

### I.4 The fitness function — debt measured, never asserted, and the running entropy ledger

SDD-OS Parte V §26 lists five decision fitness percentages with no formula. DRK-05 makes them the
*measurement layer* of the debt ledger — the mechanism that keeps the invariant **debt is measured,
not asserted**. A claim that "our decisions are well-documented" is worthless; the fitness function
computes it from the Registry, the same No-Autopromotion discipline (DRK-00 §I.3) that forbids an
author self-assigning a low review tier:

| Fitness metric (§26) | Derived from | What a low value means |
|---|---|---|
| **% traceable** | Records whose provenance chain (Parte V §5) resolves to a source without a break | orphaned-decision debt is accruing; reasoning is being lost |
| **% reversible** | Records classified Tipo A over all in-scope Records (with the Tipo-B decay vectors flagged) | the system is accumulating one-way doors; future flexibility is eroding |
| **% with alternatives explored** | Records with ≥2 genuine options and recorded rejections | unexplored-alternatives debt; the Default Suspicion Rule is being skipped at scale |
| **% auditable** | Records that answer §25's five-years-later question from their fields alone, no human memory | undocumented-reasoning debt; Future Auditability is failing |
| **% validated** | Records whose `predicted_consequences` were later scored against reality (Parte VI) | the reasoning ledger is never being closed against the outcome ledger |

These are *fitness functions* in the literal sense: they are computed continuously and their trend is
the signal, not any single value. A repo whose % auditable is falling month over month is accruing
undocumented-reasoning debt faster than it is repaying it, and that trend is a finding the ledger
surfaces to the Owner — it never auto-remediates (III.2).

The ledger also owns the one over-time integration DRK-02 explicitly delegated: the **running
architectural-entropy ledger**. DRK-02 §II.5 measures each decision's signed, per-dimension entropy
delta (coupling, special-casing, surface area, consistency debt) but flags that the *accumulation* is
a cross-decision property it does not track. DRK-05 integrates that stream: it sums the per-dimension
deltas across the Registry so it can surface the exact pattern DRK-02 named — "these forty
individually-reversible, individually-cheap decisions each raised special-casing by one, and the
system now has forty branches nobody can hold in their head." Architectural entropy is decision debt's
*cousin*: entropy is disorder in the structure, decision debt is missing reasoning about the
structure, and the accumulation of low-entropy-but-unpriced decisions is where the two axes meet.
DRK-05 never re-derives an entropy delta — it reads DRK-02's and integrates; per Invariant, the
per-decision delta is DRK-02's and the running total is DRK-05's.

---

## PART II — DECISION MEMORY & THE PRECEDENT REGISTRY

### II.1 The append-only Registry as institutional memory

SDD-OS Parte V §28 states the obligation in one line — "the repo must remember, even as developers,
agents, AI models, and teams change." DRK-05 makes the append-only **Decision Registry** the organ
that remembers. The Registry is not a log; it is the institutional-memory substrate, and its
append-only property (DRK-00 §I.5, §III.2 — there is no `DELETED` state) is what makes it trustworthy
as memory: a memory that can be silently edited is not memory, it is a story. Every Decision Record —
the Decision Object plus its review trace plus, later, its accountability fields — is a permanent
entry, and the sum of entries is the answer to §25's **Future Auditability** test: *five years later,
without human memory, it must be possible to answer "why was this decided, what was considered, and
was the reasoning sound."* The append-only Registry is the only structure that can answer it, because
human memory is exactly the thing §28 assumes will be gone.

### II.2 The Decision Genome — the queryable unit of memory

SDD-OS Parte V §24 says "every decision has DNA" and lists seven strands. DRK-05 fixes the **Decision
Genome** as the queryable projection of a Decision Record — the shape institutional memory is
*searched* by, as opposed to the Record, which is the shape it is *stored* by:

| Genome strand (§24) | What it holds | Sourced from |
|---|---|---|
| **Origin** | which agent/Owner/problem first raised the decision; the provenance root | Decision Object `problem` + dispatch identity |
| **Context** | the state of the world the decision was made in — the premises, constraints, and known-unknowns then true | `evidence` items of type `constraint`/`assumption`/`unknown` (DRK-00 §I.4) |
| **Alternatives** | the options considered and the ones discarded, with reasons | `options` + `discarded_alternatives` |
| **Tradeoffs** | what was knowingly given up — the accepted risks and the opportunity cost | `accepted_risks` + DRK-04 opportunity-cost output |
| **Impact** | the blast radius and reversibility the decision carried | DBR + Tipo (DRK-02) |
| **History** | the review trace, any supersessions, any Owner overrides | review trace + `owner_override` + supersession chain |
| **Learnings** | what the outcome taught — the scored prediction and its attribution | Parte VI accountability fields |

The Genome is what makes the Registry *answer questions* rather than merely *hold Records*. A query
like "have we decided anything about the session-store format before, and what did we give up?"
resolves against the Alternatives and Tradeoffs strands; "what did we assume when we adopted this
dependency, and is that assumption still true?" resolves against Context and feeds the
invalidated-by-context debt axis (I.2). The genome is the interface between decision memory and every
consumer of it.

### II.3 Matching a new decision against precedent

Institutional memory is inert unless a *new* decision is checked against it. That check already has a
home: **DRK-01 Stage 6 (precedent collision)** hands the candidate decision's statement to the
arch-decision skill's `arch_check`, which owns the vault index and the collision scoring and returns
`COLLISION | WARNING | CLEAR` with cited sources. DRK-05 does not re-implement precedent search — that
would be the parallel-accountant anti-pattern the family forbids. Its contribution is upstream and
downstream of the search: **every Decision Record it writes becomes a future precedent source** (DRK-01
§II.4 — "tomorrow's collision check sees today's decisions"), so the Registry compounds. The memory is
therefore self-feeding: each decision both consults the accumulated precedent and adds to it, and the
arch-check that a fresh candidate hits at Stage 6 is searching, in part, the Records DRK-05 sealed
yesterday.

### II.4 Precedent reversal — the supersession protocol

The sharpest mechanism in this dataset is what happens when a new decision **contradicts a prior
Record** — a precedent reversal, the open question DRK-00 §III.6 and DRK-02 §III.4 both carried
forward. A reversal is detected at Stage 6 as a `COLLISION` against a prior *Decision Record source*
(as opposed to a Hard Rule or a sealed veto, which drive `REJECT`). A collision with a prior decision
is not automatically a rejection — decisions are allowed to be overturned as the world changes — but
it triggers a distinct protocol whose three rules are the constitutional core of decision memory:

1. **The superseding reasoning must be stronger than the reasoning it overturns.** A new decision may
   reverse a precedent only if its evidence burden (DRK-03) and its adversarial-pass survival (DRK-01
   §III.1) are *at least as rigorous* as those of the Record it supersedes — measured by the evidence
   weight-class (DRK-00 §I.4) and ACIS level (`E0…E7`) of the strongest supporting item on each side.
   Overturning an `E3`-evidenced precedent with an `assumption` is refused; the kernel routes it to
   `REQUEST-EVIDENCE` naming the gap. This is the asymmetry that prevents memory from being churned by
   weaker-but-newer opinions: the burden of reversal is on the reverser.
2. **The old Record is superseded, not erased.** Consistent with the append-only invariant (DRK-00
   §III.2), a reversal writes a *new* Record that references and `SUPERSEDES` the old one; the old
   Record remains permanently readable, tagged superseded, with a pointer to its successor. The
   reasoning that was once acted on is part of the permanent trace — because a future reader must be
   able to see not only what is decided now but what was decided before and *why it was changed*,
   which is itself often the most valuable learning.
3. **The Owner ratifies.** A precedent reversal is, by construction, a decision of consequence
   (it changes an established position), so it routes to the Owner via owner_queue like any L4
   escalation, and the reversal is not sealed until the Owner ratifies it with a recorded decision.
   The authority proposes the supersession; it never auto-applies it (the propose-never-apply
   discipline DRK-07 governs).

This protocol is what keeps the Registry from the twin failures of II.5's ossification/amnesia
tension: reversals are *possible* (memory is not a prison) but *costly and recorded* (memory is not
amnesia).

### II.5 Canonical patterns and the anti-pattern registry — memory as reusable knowledge

Institutional memory is not only a record of specific decisions; it distills into reusable knowledge
of two signs. SDD-OS Parte V §22 (**Canonical Decision Patterns**) and §23 (**Anti-Pattern Registry**)
name both; DRK-05 sources them from the Registry rather than authoring them separately:

- **Canonical decision patterns** are *good* decisions promoted to standards — a decision shape that
  recurred, survived its adversarial pass, and whose predictions scored well (Parte VI) is abstracted
  into a reusable pattern ("prefer contracts over comments," §22's own example) and becomes a positive
  precedent the arch-check surfaces as a `WARNING`-toward-alignment rather than a collision. The
  promotion is evidence-gated: a pattern is canonical only after its instances have a track record in
  the Registry, never on first sight.
- **The anti-pattern registry** is *bad* decisions preserved as **negative knowledge** — the "do not
  do this again" trace. DRK-05 does not own the canonical negative-knowledge stores; it **cross-
  references** them. The **UKDL `T-*` trap registry** owns the rules-and-traps form of negative
  knowledge across the stack, and **FD DISCARD** owns the frontier discard ledger of paths already
  investigated and rejected. DRK-05's anti-pattern entries are *decision-shaped* negative knowledge —
  "deciding to implement before validating," §23's own example — that link to the UKDL trap or FD
  discard they instantiate, rather than re-narrating them. A recorded bad decision is thus as valuable
  as a good one: it is the precedent that makes the same mistake a `REJECT` or `REFRAME` next time it
  is proposed.

The symmetry is the point: an institution that only remembers its successes repeats its failures. The
anti-pattern registry is the half of decision memory that most systems throw away, and preserving it
append-only alongside the canonical patterns is what makes the Registry a *complete* memory rather
than a highlight reel.

---

## PART III — INVARIANTS, FAILURE MODES, INTEGRATION

### III.1 Invariants (the ledger and the memory hold these or they are broken)

1. **Append-only.** The Registry has no `DELETED` state; a retracted or reversed decision is a new
   Record that supersedes, never an edit or erasure. (Memory that can be silently rewritten is not
   memory — DRK-00 §III.2.)
2. **Supersede-not-erase.** A precedent reversal writes a successor Record and tags the predecessor
   `SUPERSEDED` with a pointer; both remain permanently readable. The reasoning once acted on is
   permanent trace.
3. **Debt is measured, not asserted.** Every decision-debt axis and every §26 fitness metric is
   computed from the Registry; no author or agent may self-declare their decisions well-documented or
   low-debt. (No-Autopromotion, inherited from ACIS and DRK-00 §I.3.)
4. **Reversal-burden is on the reverser.** A superseding decision must meet an evidence burden and
   adversarial rigor at least as strong as the Record it overturns, and the Owner ratifies. (II.4.)
5. **Priced debt is protected.** A knowingly-deferred decision with a recorded rationale and a
   repayment trigger is an instrument, never a defect; the ledger surfaces only *unpriced* debt.
   (I.3.)
6. **Cross-ref, not re-narrate.** Cognitive debt is C70's; the per-decision entropy delta and decay
   vector are DRK-02's; precedent-collision search is arch-decision's; evidence levels are ACIS's;
   trap and discard negative-knowledge are UKDL's and FD's. DRK-05 integrates and links; it forks
   none. (GK-00 one-system.)
7. **Propose, never auto-apply.** The ledger and the memory surface findings, promotions, and
   proposed supersessions to the Owner; they never remediate debt, promote a pattern, or seal a
   reversal autonomously. (III.2; the propose-never-apply discipline DRK-07 governs.)

### III.2 States of a Record in memory

A Record is `ACTIVE` (current, un-superseded) → may become `SUPERSEDED` (a stronger later Record
overturned it; both readable) at any time after `REVIEWED`. Orthogonally a Record carries a debt
profile that is `PRICED` (deferral with a repayment trigger), `CLEAN` (all debt axes zero), or
`ACCRUING` (one or more unpriced debt axes non-zero) — and an `ACCRUING` Record may be flagged
`STALE` when the invalidated-by-context axis fires (a cited premise has a contradicting later Record).
There is no state in which a Record leaves the Registry.

### III.3 Failure modes and the guard for each

| Failure mode | Symptom | Guard |
|---|---|---|
| **Memory rot** | Records exist but their genome strands are empty; the Registry holds entries nobody can query | orphaned-decision debt axis (I.2) + % traceable / % auditable fitness (I.4); a falling trend is surfaced to the Owner |
| **Precedent ossification** | no decision can ever be reversed; the Registry becomes a prison of old choices | II.4 makes reversal *possible* under a stronger-reasoning burden; the burden is calibrated, not infinite |
| **Precedent amnesia** | precedents are reversed freely by weaker-but-newer opinions; memory churns | II.4 rule 1 puts the burden on the reverser (≥ prior evidence weight and ACIS level); Owner ratifies |
| **Debt-blindness** | the system accrues unpriced decision debt invisibly until it is unpayable | the six-axis ledger (I.2) measures accrual at Record time, before it compounds; unpriced debt is surfaced |
| **Pattern over-fitting** | a decision shape is promoted to canonical from too few instances and misapplied | II.5 promotion is evidence-gated on a Registry track record + scored predictions (Parte VI); never on first sight |
| **Priced-debt false positive** | a deliberate `DEFER` is flagged as a defect | I.3 / Invariant 5 distinguish priced (rationale + repayment trigger) from unpriced; the ledger surfaces only unpriced |
| **Entropy double-counting** | DRK-05 re-derives an entropy delta DRK-02 already computed | Invariant 6; DRK-05 reads DRK-02's per-decision delta and only integrates the running total (I.4) |

### III.4 Integration with the stack (consumer ↔ provider)

- **Consumes:** DRK-02 (the per-decision entropy delta for the running ledger, and the Tipo-B decay
  vector as the trigger for a reversibility-drift re-review); arch-decision `arch_check` (the
  precedent-collision verdict at DRK-01 Stage 6, including collisions against prior Decision Records);
  ACIS `epistemic_ladder` (the level of the strongest evidence on each side of a precedent reversal);
  Parte VI accountability (the scored-prediction fields that populate the Genome's Learnings strand
  and the % validated fitness metric).
- **Provides:** to **DRK-01 Stage 6**, the accumulated Decision Records as precedent sources, so the
  sieve's precedent check compounds; to **DRK-07**, the precedent-reversal package (predecessor
  Record + successor + the relative-rigor comparison) for the override/reversal evaluation it governs;
  to the **Owner**, the decision-debt ledger, the §26 fitness trend, the running entropy total, and
  every proposed supersession, pattern promotion, and anti-pattern entry — all as recommendations,
  never auto-applied.
- **Re-review trigger:** when a Tipo-B decay vector crosses into Tipo C (DRK-02 §I.4) or when an
  invalidated-by-context premise fires (I.2), DRK-05 raises a re-review of the affected Record — a new
  Decision Object routed through the sieve, whose outcome either re-affirms (writing a fresh Record) or
  supersedes (II.4). This closes the loop DRK-02 §III.4 left open: reversibility is not static, and
  the memory is what notices when it has changed.

### III.5 Open questions (carried to DRK-07 / Generation-One)

- At what accumulated entropy-delta or debt-axis threshold should DRK-05 escalate a *cluster* of
  individually-reversible, individually-clean decisions to a single L4 re-review of the pattern they
  jointly created? (The forty-branches case — DRK-02 §III.4 carried the same question.)
- When a precedent reversal's superseding reasoning is *exactly* as strong as the reasoning it
  overturns (a genuine tie in evidence weight and ACIS level), who breaks the tie — the Owner by
  default, or a recorded coin-flip that is itself a priced-debt `DEFER`? (DRK-07 override calibration.)
- Can the invalidated-by-context axis be computed automatically, or does detecting that a premise
  "has changed" always require a human or a probe (RUN-EXPERIMENT) to confirm the contradiction is
  real and not a surface mismatch? (DRK-03 burden × DRK-04 experiment cost.)
- Should a canonical decision pattern, once promoted, itself carry a decay vector — i.e. can a
  standard that was right for years silently become an anti-pattern, and what triggers its demotion?
  (The pattern-over-fitting failure mode's temporal form.)

### III.6 Done criteria for DRK-05

The debt-and-memory layer is complete when: the six decision-debt axes and the five §26 fitness
metrics are computed from the append-only Registry by the kernel (never author-asserted), and a
falling fitness trend is surfaced to the Owner without auto-remediation; the running architectural-
entropy ledger integrates DRK-02's per-decision deltas with zero re-derivation
(`V-DRK-CROSS-REF-NOT-RENARRATE`); the Decision Genome resolves all seven strands from a Record's
fields; a precedent reversal detected at Stage 6 writes a superseding Record that references (never
erases) its predecessor, is gated on a stronger-reasoning burden, and routes to the Owner for
ratification; priced debt (a `DEFER` with a repayment trigger) is provably distinguished from unpriced
debt and never blocked; and the anti-pattern registry links each entry to its UKDL trap or FD discard
rather than re-narrating it. Until the Registry answers a real "why did we decide this, and was the
reasoning sound?" from a superseded Record's genome alone — no human memory — DRK-05 is doctrine, not
an operating floor, which is exactly the state SDD-OS Parte V §25/§28 was found in at STOP #1.
