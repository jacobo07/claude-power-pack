# DRK-02 — Reversibility, Blast Radius & Architectural Consequence/Entropy Model

> The classification substrate of the Decision axis. DRK-00 fixed the objects and the seven-axis
> taxonomy; DRK-01 built the nine-stage sieve. DRK-02 supplies the three mechanisms the kernel calls
> in **Stage 3 (classify)**: the **reversibility classifier** that assigns Tipo A / Tipo B / Tipo C,
> the **Decision Blast Radius (DBR)** compute that scores the surfaces a decision can touch, and the
> **second/third-order consequence and architectural-entropy model** that judges what a decision does
> to system disorder over time. **Parent it DEEPENs:** SDD-OS Parte V §10 (Reversible/Irreversible
> Tipo A/B/C), §11 (Cost Model), §13 (Blast Radius), §17 (Second Order Effects), §18 (Third Order
> Effects) — each a one-line enumeration there, given mechanism here. **Cross-references (never
> re-narrated):** ACIS epistemic ladder (owns evidence levels `E0…E7`); D2A engine (owns build/
> placement); CO-03 (owns model/cost routing); DRK-04 (owns counterfactual temporal horizons and
> opportunity cost); DRK-05 (owns decision debt and the entropy ledger over time).

---

## PART I — THE REVERSIBILITY CLASSIFIER

### I.1 Why reversibility, not confidence, sets the burden

The single most consequential number DRK computes is not how *confident* the selector is — it is how
*hard the decision is to undo*. DRK-00 §II.4 already sealed the two as separate ledgers: a cheap-to-
undo decision is *allowed* to be low-confidence, because reversibility buys the right to be wrong. The
reversibility classifier is therefore the load-bearing input to the whole pipeline: it sets the
evidence burden (DRK-03 reads the Tipo to decide how much and what-typed evidence is required), it
sets the review tier (DRK-00 §II.3 routes Tipo A → L1, Tipo B → L2, Tipo C → L4), and it is the first
of the two conditions in the block-narrow twin-condition (`Block iff Tipo-C irreversible ∧ evidence <
ACIS E3`). A wrong reversibility classification does not merely mis-label a field — it mis-routes the
entire decision, either taxing a trivial choice with L4 rigor or letting a one-way door swing shut
un-reviewed. The classifier is thus the highest-leverage deterministic function in DRK-02, and it is
`derived`, never author-supplied: an author who could self-declare "Tipo A" would defeat the No-
Autopromotion invariant the same way a self-assigned low review tier would.

### I.2 The three Tipos — the decision rule

The classifier assigns exactly one Tipo by evaluating the decision's **undo path** — the concrete
sequence of actions required to return the system to its pre-decision state, and their cost. The Tipo
is a function of that path, not of the decision's importance:

| Tipo | Undo path | Undo cost signature | Routing floor |
|---|---|---|---|
| **A — reversible** | a local edit / revert / config flip returns the system to its prior state within one session, touching nothing external and nobody downstream | near-zero; no coordination, no data loss, no external notification | L1 (record only) |
| **B — hard to undo** | undo is *possible* but has a real, bounded cost: a migration to reverse, a dependency to swap back, consumers to notify, a deprecation window to run | bounded but non-trivial; requires coordination and/or a reverse-operation with its own risk | L2 (standard) |
| **C — practically irreversible** | there is no undo path that restores the prior state — data was deleted, a public contract was consumed by parties you do not control, a name is in users' heads, a one-way door closed behind the decision | unbounded or infinite; "undo" means building a new forward path, not returning | L4 (foundational) |

The distinction between B and C is the one the classifier must get right, because it is the boundary
the block-gate keys on. The test is **not** "is undo expensive?" (that is the A↔B boundary) but "does
an undo path *exist at all* that restores the prior state?" A Tipo-B decision is one you can walk back
at a price; a Tipo-C decision is one where walking back is a fiction — the only motion available is
forward, into a new decision. This is the mechanical content of the "one-way door" metaphor: a Tipo-C
decision has passed through a door with no handle on the far side.

### I.3 The escalation signals — what pushes a decision up a tier

A decision does not announce its Tipo. The classifier detects it by scanning the Decision Object's
`statement`, `chosen`, `dependencies`, and `accepted_risks` fields for **escalation signals** — each
signal is a concrete property that forces the Tipo up from the default. The default for an in-scope
decision is Tipo A; each matched signal ratchets it upward and is recorded on the Record as the
*basis* for the classification (so the reversibility basis can be surfaced verbatim when the block-gate
holds, per DRK-01 §III.2):

| Signal | Detected in | Ratchets to | Why |
|---|---|---|---|
| **Public contract** | statement names an API, endpoint, wire format, or CLI others depend on | C | once consumed by parties you do not control, the contract cannot be un-published |
| **Data schema / migration** | decision alters a persisted schema, runs a migration, or changes a stored representation | B (reversible migration) → C (lossy/destructive migration) | a reversible migration is Tipo B; a migration that drops a column or coerces data is Tipo C |
| **Deleted data** | the operation removes records, drops a table, purges history | C | deletion is the canonical irreversible act; the prior state is unrecoverable |
| **User-visible name** | a name, URL, label, or identifier users will see and memorize | C | a name lives in users' heads and external links; renaming is a new forward migration, not an undo |
| **External dependency** | adopts a third-party service, library, or vendor as a load-bearing dependency | B → C | swapping a wrapped dependency is Tipo B; one whose data model leaks through the codebase is Tipo C |
| **One-way door** | the decision forecloses a set of future options that cannot be reopened | C | irreversibility of *optionality*, not of state — the discarded paths do not return |
| **Cross-repo / platform reach** | the decision's effect crosses a repo or platform boundary | at least B | coordination cost across boundaries makes undo bounded-but-real at minimum |

The signals are evaluated as a **max**, not a sum: the highest Tipo any single signal implies is the
decision's Tipo. Three Tipo-B signals do not compound into Tipo C — a decision with a reversible
migration, a wrapped dependency, and cross-repo reach is Tipo B, because each has a real undo path;
one Tipo-C signal (a single dropped column) alone makes the whole decision Tipo C. This is deliberate:
irreversibility is a property of the *worst* door the decision opens, and the classifier is calibrated
to catch the one destructive signal hiding among reversible ones, which is precisely the case a naïve
"count the risks" scorer misses.

### I.4 The undo-cost model — pricing Tipo B

Tipo A (near-zero undo) and Tipo C (no undo path) need no pricing; the interesting cost model lives
inside Tipo B, where undo is possible but must be *quantified* so DRK-04 can later simulate whether
the undo is worth pre-provisioning and DRK-05 can carry the un-exercised undo as latent debt. The undo
cost of a Tipo-B decision is modelled as a field-list on the Record — not a single number, because
DRK-00's evidence philosophy (preserve the types, do not collapse prematurely) applies to cost too:

- **reverse-operation cost** — the engineering effort of the inverse action (the down-migration, the
  dependency swap-back, the feature-flag rollback path).
- **coordination cost** — how many consumers, agents, or workflows must be notified or re-synchronized
  for the undo to be safe (this is where DBR from Part II feeds back in: a wide blast radius makes even
  a Tipo-B undo expensive to coordinate).
- **decay cost** — how the undo cost *grows with time*: a Tipo-B decision often decays toward Tipo C as
  data accumulates under the new schema, as external parties adopt the new contract, as the deprecation
  window closes. The classifier records the decay direction; DRK-04 simulates its horizon.
- **residual-risk cost** — the risk the reverse operation *itself* carries, since an undo is a
  decision too and can fail (an origin lesson: SDD-OS Parte V §10's rigor mandate exists because
  reverse operations are under-tested relative to forward ones).

The decay cost is the sharpest mechanism here: **reversibility is not static.** A decision correctly
classified Tipo B today can silently become Tipo C in three months as its undo path erodes. DRK-02
records the decay direction at classification time; DRK-05 owns the ledger that tracks whether a
Tipo-B decision has crossed into Tipo C and should be re-reviewed. The classifier's job is to flag the
decay vector, not to track it forever — tracking is DRK-05's institutional-memory concern.

### I.5 How the Tipo sets burden and tier — the coupling

The Tipo is consumed twice. First, DRK-01 Stage 3 writes it into the taxonomy's **Reversibility axis**
(DRK-00 §II.1), and Stage 4 routes on the taxonomy maxima: Tipo C alone is sufficient to force L4
regardless of every other axis being low, because an irreversible-but-otherwise-trivial decision (a
one-line schema drop) is exactly the kind of small-looking, unrecoverable act the axis exists to
catch. Second, DRK-03 reads the Tipo to set the **evidence burden**: Tipo A demands no evidence beyond
the Record itself, Tipo B demands medium-typed evidence (`inference` or better), and Tipo C demands
strong-typed evidence at ACIS `E3` or above — and the *level* of that evidence is read from the ACIS
epistemic ladder, which owns evidence levels; DRK-02 never re-derives them. The coupling is the
mechanical realization of SDD-OS Parte V §10's "mayor irreversibilidad → mayor rigor," now a
deterministic function rather than a slogan.

### I.6 Worked examples

- **Tipo A.** "Rename a private helper function `_fmt` to `_format_row`." No signal matches: no public
  contract (private), no schema, no data, no user-visible name, no external dependency, no foreclosed
  option. Default holds → Tipo A → L1 record, no evidence burden, never blocks. Reviewing this harder
  would be the tax DRK-00 §I.2 forbids.
- **Tipo B.** "Migrate the session store from a JSON file to SQLite, keeping a reversible import/export."
  The schema-change signal fires but the migration is reversible (export back to JSON exists) → Tipo B
  → L2. Undo-cost model: reverse-operation = the export path; decay cost = *rising* (as sessions
  accumulate in SQLite, the export grows and the JSON path bit-rots) → decay vector flagged for DRK-05.
  Evidence burden: medium-typed. Never blocks — an adequately-evidenced Tipo B recommends and the
  caller decides.
- **Tipo C.** "Drop the deprecated `legacy_uuid` column and purge its history." The deleted-data signal
  fires; there is no undo path that restores the purged values → Tipo C → L4. Now the block-gate is
  *eligible*: it fires **only** if the evidence is also below ACIS `E3` (the twin-condition). If a probe
  has verified nothing reads `legacy_uuid` (evidence ≥ E3), the kernel **recommends** and routes to
  owner_queue without blocking; if the "nothing reads it" claim is an untested `assumption` (< E3), the
  kernel **blocks** and returns the twin-condition status plus the exact missing evidence. This example
  is the canonical demonstration that block-narrow is about *both* conditions, never Tipo-C alone.

---

## PART II — BLAST RADIUS AND ARCHITECTURAL CONSEQUENCE

### II.1 The Decision Blast Radius — the surfaces

Reversibility answers "can we undo it?"; **blast radius answers "how far does it reach?"** — an
orthogonal question, because a fully reversible decision can have a huge blast radius (a config flip
that changes every user's experience) and an irreversible one can be narrow (a private schema drop
nobody reads). DBR is the DEEPEN of SDD-OS Parte V §13, which enumerates nine surfaces with no scoring
mechanism. DRK-02 fixes the surfaces and a per-surface magnitude:

| Surface | What a decision touches here | Magnitude scale (0 → 3) |
|---|---|---|
| **Code** | modules, call-sites, interfaces affected | none / one module / a subsystem / cross-cutting |
| **Users** | who sees a behavior or interface change | nobody / internal / a segment / all users |
| **Cost** | compute, token, or infrastructure spend delta (routed through CO-03 for the pricing) | negligible / bounded / recurring / unbounded |
| **Infrastructure** | services, data stores, deploy substrate | none / one service / a tier / the platform |
| **Roadmap** | future work enabled or foreclosed | none / a task / a milestone / a direction |
| **Operations** | on-call, monitoring, runbook, incident surface | none / a runbook line / a new alert / a new failure class |
| **Agents** | which PP agents / hooks / skills change behavior | none / one / a family / the dispatcher |
| **Workflows** | the session flows and Stop-chains affected | none / one flow / a chain / the harness |
| **Data** | records, schemas, retention affected | none / a field / a table / the store |

Each surface is scored 0–3. The **composite DBR** is *not* the sum — a sum would let nine 1s (a broad
but shallow decision) outrank a single 3 on Data (a narrow but catastrophic one), inverting the risk.
The composite is the **max magnitude across surfaces, with the count of surfaces at that magnitude as
a tiebreak** — so a decision that hits any single surface at magnitude 3 is a high-DBR decision
regardless of how quiet the other eight are, and among two decisions with the same max, the one
touching more surfaces at that max is higher. This mirrors the Tipo classifier's max-not-sum logic in
I.3 for the same reason: catastrophe is a property of the worst surface, and the score must not let
breadth dilute depth.

### II.2 How DBR feeds the taxonomy and the routing

DBR is consumed at DRK-01 Stage 3 as the taxonomy's **Blast-radius axis** (DRK-00 §II.1): composite
DBR of 0–1 → low, 2 → medium, 3 → high. Stage 4 then routes on the maxima, so a high-DBR decision
reaches at least L3 (deep, with the adversarial pass) even when it is reversible, because a wide-reach
reversible decision still deserves the adversarial pass that forces its second- and third-order effects
(II.4). DBR interacts with reversibility multiplicatively in practice though not in the score: the
worst quadrant is **high-DBR ∧ Tipo-C** (irreversible and far-reaching), which is the archetypal L4
foundational decision; the safest is **low-DBR ∧ Tipo-A**, the L1 record-and-move-on. The two axes are
scored independently and the router reads both, honoring DRK-00's warning against the E3 Layer-
Flattening error of conflating orthogonal axes into one number.

### II.3 The Cost surface is a cross-reference, not a re-implementation

DRK-02 does **not** price compute or tokens. The Cost surface's magnitude is populated from CO-03,
which owns model and cost routing; DBR asks CO-03 "what is the spend delta of this decision?" and
records the returned magnitude. This keeps the single cost instrument authoritative — a DRK that
re-derived token pricing would be the parallel-accountant anti-pattern the family forbids. Likewise the
Cost surface's *self-referential* case — the cost of the *review itself* — is CO-03's self-cost
contract (DRK-01 §II.3), not a DBR concern.

### II.4 Second- and third-order effects — what happens after what happens

SDD-OS Parte V §17–18 states the obligation in three lines: evaluate not "what happens" but "what
happens after what happens, and after that." DRK-02 gives it a mechanism. Every surface scored in II.1
captures the **first-order effect** — the immediate, direct consequence. The consequence model then
propagates each first-order effect one and two hops further:

- **Second-order effect** — the consequence *of the consequence*. A decision to add a cache (first
  order: latency drops) has the second-order effect that a stale cache now becomes a possible failure
  class (a new Operations surface hit that the first-order scoring missed). The model asks, per
  non-trivial first-order effect: *what does this effect cause?*
- **Third-order effect** — the consequence of the second-order effect. The new stale-cache failure
  class (second order) has the third-order effect that on-call must now reason about cache coherence
  during every latency incident, permanently raising the cognitive load of an entire class of
  debugging — a Roadmap-and-Operations cost invisible at first order.

The model does not chase infinite orders; it stops at three, because SDD-OS Parte V §18's own thesis
is that "most systems only consider the first" and forcing the third is where the marginal insight
lives — beyond that, the analysis decays into speculation better handled by DRK-04's explicit temporal
horizons. The division of labour is exact: **DRK-02 owns the causal *depth* (orders of consequence)
at classification time; DRK-04 owns the temporal *horizon* (1 month → 3 years) at simulation time.**
An order is "and then what does that cause"; a horizon is "and where is that in a year." DRK-02 hands
DRK-04 the third-order effect set as the seed for horizon simulation; it does not itself simulate
across time. The adversarial pass (DRK-01 §III.1, question 4 — "what risk are we underestimating?") is
the stage that *forces* the second- and third-order enumeration to actually happen rather than being
skipped, which is why the pass runs at L3+ where DBR is already high.

### II.5 Architectural entropy — the disorder ledger

Reversibility and blast radius are both *point-in-time* properties. The third mechanism DRK-02
supplies is a *rate* property: **architectural entropy** — whether a decision raises or lowers the
system's disorder and coupling over time. This is the concept SDD-OS Parte V gestures at with
"complejidad aceptada" (§4) and "decision debt" (§12) but never mechanizes. DRK-02 models a decision's
entropy delta as the signed change it makes to four disorder dimensions:

| Entropy dimension | Raised by | Lowered by |
|---|---|---|
| **Coupling** | adds a new dependency edge between previously independent modules | removes an edge; introduces a boundary/interface |
| **Special-casing** | adds a branch, exception, or "except when…" to a general rule | collapses N special cases into one general rule |
| **Surface area** | adds a new public contract, flag, or config knob to maintain | retires a contract, flag, or knob |
| **Consistency debt** | introduces a second way to do a thing the system already does one way (a D2A concern — placement is D2A's, but the *entropy cost* of the duplication is DRK's) | unifies two ways into one |

The entropy delta is signed and per-dimension, not a scalar, so a decision can be entropy-lowering on
coupling (it removes a dependency) while entropy-raising on surface-area (it adds a flag) — and the
model preserves both, because collapsing them would hide the trade. The critical case this mechanism
exists to catch is the **reversible-but-entropy-raising decision**: a Tipo-A decision (trivially
undone) that nonetheless *raises entropy* — a new special-case branch, a new config flag, a fourth way
to format a row. Its reversibility makes it look free; its entropy delta makes it a slow tax. Each such
decision is individually cheap and individually reversible, so no single review blocks it, yet their
accumulation is exactly how a system rots. DRK-02 flags the entropy delta at classification time;
because the *accumulation* is a cross-decision, over-time property, the running entropy ledger is owned
by **DRK-05** (decision debt / institutional memory) — DRK-02 supplies the per-decision delta, DRK-05
integrates it. A positive-entropy Tipo-A decision therefore never blocks, but it is recorded with its
entropy delta so the debt ledger can later surface "these forty reversible decisions each raised
special-casing by one, and the system now has forty branches nobody can hold in their head."

---

## PART III — INVARIANTS, FAILURE MODES, INTEGRATION

### III.1 Invariants

1. **Tipo is derived, max-not-sum.** The reversibility classifier assigns Tipo A/B/C as the max Tipo
   any single escalation signal implies, never a sum of signals, and never author-supplied. (No-
   Autopromotion; catches the one destructive signal among reversible ones.)
2. **Reversibility ≠ confidence.** The Tipo is computed independently of the DCS; a reversible decision
   may be low-confidence and a high-confidence decision may still be Tipo C. (DRK-00 §II.4, sealed.)
3. **DBR is max-with-tiebreak, not sum.** The composite blast radius is the max surface magnitude with
   surface-count as tiebreak; breadth never dilutes depth. (Catastrophe is a property of the worst
   surface.)
4. **Orders stop at three; horizons belong to DRK-04.** DRK-02 owns causal depth to the third order at
   classification time and hands the third-order set to DRK-04; it never simulates across time itself.
5. **Cost is cross-referenced.** The Cost surface magnitude comes from CO-03; DRK-02 prices nothing.
6. **Entropy delta is signed and per-dimension.** Never a scalar; the running ledger is DRK-05's, not
   DRK-02's.
7. **Reversibility can decay.** A Tipo-B decision carries a decay vector; DRK-02 flags it, DRK-05
   tracks whether it has crossed into Tipo C and warrants re-review.

### III.2 Failure modes and guards

| Failure mode | Symptom | Guard |
|---|---|---|
| Destructive signal masked | A schema drop hidden among reversible changes is scored Tipo B | I.3 max-not-sum; `V-DRK-REVERSIBILITY` asserts a single Tipo-C signal forces Tipo C |
| Breadth dilutes depth | Nine shallow surfaces outrank one catastrophic surface | II.1 max-with-tiebreak composite; never a sum |
| Reversibility conflated with confidence | A high-DCS Tipo-C decision skips L4 | Invariant 2; router reads Tipo independently of DCS |
| Order/horizon confusion | DRK-02 attempts 1-year simulation; DRK-04 re-does causal depth | Invariant 4; the depth/horizon boundary is explicit |
| Cost re-implementation | DBR prices tokens itself | Invariant 5; Cost surface delegates to CO-03 |
| Entropy creep | Forty reversible positive-entropy decisions rot the system unblocked | II.5 per-decision delta recorded; DRK-05 integrates and surfaces the accumulation |
| Static reversibility | A Tipo-B decision silently becomes Tipo C and is never re-reviewed | Invariant 7 decay vector; DRK-05 re-review trigger |
| Entropy used to block | The kernel blocks a reversible entropy-raising decision | Block-narrow invariant (DRK-00 §II.3, DRK-01 §III.2): entropy never blocks, only records — block is Tipo-C ∧ <E3 only |

### III.3 Integration — which DRK-01 stage consumes each output

- **Consumed by DRK-01 Stage 3 (classify):** the reversibility classifier's Tipo populates the
  taxonomy Reversibility axis; the DBR compute populates the Blast-radius axis; the entropy delta and
  the second/third-order effect set are attached to the Decision Object for the adversarial pass.
- **Consumed by DRK-01 Stage 4 (route):** the Tipo and composite DBR are the two dominant maxima the
  L0–Ln router keys on — Tipo C forces L4, high DBR forces at least L3.
- **Consumed by DRK-01 Stage 5 (evidence burden):** the Tipo is the input DRK-03 reads to set how much
  and what-typed evidence is required, and it is the first half of the block-gate twin-condition.
- **Consumed by DRK-01 Stage 8 (adversarial pass):** the second/third-order effect set is the material
  question 4 ("what risk are we underestimating?") interrogates.
- **Provided to DRK-04:** the third-order effect set as the seed for temporal-horizon counterfactual
  simulation, and the Tipo-B decay vector as the thing whose horizon DRK-04 projects.
- **Provided to DRK-05:** the per-decision entropy delta for the running disorder ledger, and the
  decay vector for the reversibility-drift re-review trigger — the two over-time properties DRK-02
  measures but does not itself track.

### III.4 Open questions (carried to DRK-04 / DRK-05 / Generation-One)

- What is the confidence of the classifier's own Tipo assignment when the escalation signals are
  ambiguous (a dependency that *might* leak its data model)? A mis-classification here is the highest-
  cost error in the axis; does an ambiguous signal warrant a probe (RUN-EXPERIMENT) to resolve the
  Tipo before routing? (DRK-03 burden × DRK-04 experiment cost.)
- At what entropy-delta accumulation threshold should DRK-05 escalate a *cluster* of individually-
  reversible decisions to a single L4 re-review of the pattern they created? (DRK-05 debt integration.)
- When a Tipo-B decision's decay vector crosses into Tipo C, is the re-review a new Decision Object or
  a supersession of the original Record? (DRK-05 precedent registry + DRK-00 §III.2 append-only.)

### III.5 Done criteria for DRK-02

The models are complete when: the reversibility classifier assigns Tipo A/B/C by the max-not-sum
signal rule in `decision_kernel.py` Stage 3 and `V-DRK-REVERSIBILITY` proves a single destructive
signal forces Tipo C and that rigor scales with the Tipo; the DBR compute scores all nine surfaces and
composites them max-with-tiebreak, feeding the taxonomy Blast-radius axis; the second/third-order and
entropy models attach their outputs to the Decision Object and are exercised by the L3+ adversarial
pass; the Cost surface delegates to CO-03 and the evidence level to ACIS with no re-derivation
(`V-DRK-CROSS-REF-NOT-RENARRATE`); and the reversibility basis and DBR are surfaced verbatim by the
block-gate when it holds (DRK-01 §III.2). Until the classifier labels a real destructive migration
Tipo C and the router forces it to L4 in the same run, DRK-02 is doctrine, not an operating floor —
the exact state SDD-OS Parte V §10 was found in at STOP #1.
