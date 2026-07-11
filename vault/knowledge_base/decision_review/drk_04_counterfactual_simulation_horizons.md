# DRK-04 — Counterfactual Simulation & Adaptive Temporal Horizons

> The forward-looking mechanism of the Decision axis. DRK-00 fixed the objects and the seven-axis
> taxonomy; DRK-01 built the nine-stage sieve and named this dataset as the thing **Stage 8 invokes
> at L3+**; DRK-02 classified the decision's reversibility, priced its blast radius, and computed its
> second/third-order effect set and entropy delta. DRK-04 takes those classification outputs and
> pushes the decision **forward in time**: it selects the temporal horizons appropriate to the
> decision's *type*, simulates the chosen option *and* the strongest discarded alternative *and* the
> null option across those horizons, prices the opportunity cost of the path foreclosed, and expresses
> the strategic ROI as ranges rather than points — so the review sees not merely "what happens" but
> "what happens after that, and what we gave up to get it." **Parent it DEEPENs:** SDD-OS Parte V §14
> (Decision Simulation Engine, 1mo/3mo/6mo/1yr/3yr), §17–18 (Second/Third Order Effects), §19
> (Opportunity Cost Engine), §20 (Strategic ROI Layer) — each a bare enumeration there, given
> mechanism here. **Cross-references (never re-derived):** DRK-02 owns reversibility (Tipo A/B/C), the
> Decision Blast Radius (DBR), architectural entropy, and the *causal depth* of consequence (orders) —
> DRK-04 consumes them and re-derives none; ACIS owns evidence levels `E0…E7`; CO-01/token_irr own
> token economics; D2A owns capability placement (its counterfactual-spend case is cited once below);
> SDD-OS Parte VI owns prediction→outcome accountability, which DRK-04's horizons feed; DRK-06 owns the
> irreducible optionality tension this dataset presses against.

---

## PART I — ADAPTIVE TEMPORAL HORIZONS

### I.1 The single-horizon error

SDD-OS Parte V §14 mandates simulation at a fixed ladder — one month, three months, six months, one
year, three years — for *every* decision that reaches the engine. That fixed ladder is the shallow
form DRK-04 deepens, and the deepening begins by rejecting the fixity outright. Judging every decision
on the same horizon set is not neutral; it is an error in two opposite directions at once, and the
direction of the error depends on the decision's type.

Judge a fast, cheap, Tipo-A experiment on a three-year horizon and the simulation over-weights a
speculative future that the experiment was explicitly designed to make irrelevant: the whole point of
a probe is that its result arrives in days and supersedes any guess about the year. The three-year
column here manufactures false gravity — it invites REFRAME or DEFER on a decision whose correct
verdict is RUN-EXPERIMENT precisely *because* the long horizon does not bind it. Conversely, judge a
Tipo-C public-contract or data-schema decision on a one-month horizon and the simulation is blind to
the only cost that matters: the irreversible commitment does not bite in the first month — it bites
in the quarters and years after external parties have adopted the contract, after data has
accumulated under the schema, after the name has entered users' heads. A short horizon on a one-way
door hides the entire liability the door represents. The fixed ladder, applied uniformly, systematically
mis-judges both the shortest-lived and the longest-lived decisions, and the two errors do not cancel —
they compound, because the same review pipeline commits both.

The correction is that **the horizon is a function of the decision's type, not a constant.** A
decision's natural evaluation window is set by how long its consequences take to fully express, and
that expression time is itself readable from the DRK-00 taxonomy and the DRK-02 classification the
kernel has already computed. DRK-04 does not ask the author "over what horizon should we judge this?"
— that would violate the No-Autopromotion invariant the same way a self-assigned review tier would.
The horizon set is **derived**.

### I.2 The horizon-by-type mapping

DRK-04 maps the decision — via its reversibility Tipo (DRK-02), its scope and impact axes (DRK-00
§II.1), and its identity/compat axis — to a **horizon set**: the specific windows over which the
counterfactual simulation of Part II is run. The mapping is not "bigger decision, longer horizon" as a
scalar; it is a *set* chosen so that each window lands where the decision's consequences actually
express, and windows where nothing new expresses are omitted so the simulation spends no attention on
dead columns.

| Decision type | Signature (taxonomy / Tipo) | Horizon set | Why these windows |
|---|---|---|---|
| **Experiment / probe / spike** | RUN-EXPERIMENT candidate; Tipo A; uncertainty-resolving | hours → days (result-time); a single "after we know" checkpoint | the decision exists to be superseded by its own result; longer windows are noise |
| **Local change** | Tipo A; impact cosmetic/low; scope one-file | days → weeks | a reversible local edit fully expresses within a working cycle; nothing new at 1yr |
| **Feature** | Tipo A/B; module scope; impact medium | one release cycle → one quarter | a feature's real cost (maintenance, operations, entropy) appears across a release and the quarter after |
| **Dependency adoption** | Tipo B→C signal (DRK-02 I.3); external | one quarter → one year, with a **decay checkpoint** | adoption cost is bounded early but its Tipo-B→C decay (DRK-02 I.4) expresses over quarters |
| **Data schema / migration** | Tipo B (reversible) or C (lossy) | one quarter → one year → three years | accumulation under the schema is the liability; it grows monotonically with time |
| **Public contract / API / user-visible name** | Tipo C; identity/compat high | one year → three years (plus a near-term adoption checkpoint) | the commitment barely bites early and bites hardest after external adoption is irreversible |
| **Platform / architectural direction** | Tipo C; cross-repo/platform; foundational | one year → three years → "structural" (beyond simulation, flagged) | a direction forecloses optionality whose absence is only felt across years |

The `Ln`-style openness of DRK-00's routing carries here: a project with a decision class whose
consequences express on an unusual clock (a regulated-retention decision judged on a seven-year
window) names the window and adds it, without disturbing the seven rows above. The mapping is a lookup
over classification outputs the kernel already holds — it computes no new classification of its own,
and it re-derives no reversibility, DBR, or entropy value (DRK-02 owns all three; DRK-04 reads them).

### I.3 The near-far pairing and the "structural" ceiling

Two structural rules govern every horizon set. First, **near-far pairing**: an irreversible decision
always carries at least one *near* checkpoint alongside its *far* windows, because the near checkpoint
is where a Tipo-C decision's adoption becomes irreversible — the moment after which the far cost is
locked in. A public-contract decision judged only at three years would miss the adoption checkpoint at
which walking back is still possible; pairing the far window with the near one lets the simulation
locate the point of no return, not merely the eventual bill. Second, the **structural ceiling**: DRK-04
stops simulating at three years for the same reason DRK-02 stops causal depth at the third order —
beyond that, the projection decays into speculation with no marginal insight, and honesty demands the
model say so rather than fabricate a five-year number. A consequence that genuinely expresses only
beyond three years is flagged `structural` and handed to the Owner as a named unknown, never
simulated as if it were knowable. This is the temporal analogue of the DRK-02 rule that the third
order is the last order worth forcing.

### I.4 How horizons feed Parte VI prediction observables

The horizon set is not consumed only inside DRK-04; it is the clock that makes the decision's
`predicted_consequences` (DRK-00 §I.3, a required field) *checkable* later. Each element of
`predicted_consequences` carries a horizon (DRK-00 fixed the field as "what the selector expects to
happen, with horizon"). DRK-04's horizon set fixes *which* horizons those predictions must be pinned
to, and thereby fixes the schedule on which SDD-OS Parte VI's accountability layer will later score
prediction against realized outcome. A prediction with no horizon is unscoreable — you cannot say it
was right or wrong without a date on which to check — so DRK-04's adaptive horizon is the upstream
mechanism that makes the downstream two-ledger accountability possible. A Tipo-C decision whose far
window is three years generates a three-year prediction observable that Parte VI will hold open and
score; a probe whose window is "days" generates an observable checked almost immediately, and its
outcome feeds back fastest. In this sense the horizon set is the join between the *before* half of the
Decision axis (simulation) and the *after* half (attribution): the same window that bounds the
simulation bounds the eventual scoring. DRK-04 owns the projection; Parte VI owns the settlement;
they share the clock.

---

## PART II — COUNTERFACTUAL SIMULATION

### II.1 Three trajectories, not one

The word *counterfactual* is load-bearing and is the reason this dataset is not merely a "simulate the
plan" step. A simulation of only the chosen option answers "what happens if we do this?" — a question
that invites confirmation, the same trap the DRK-01 §III.1 adversarial pass exists to break. DRK-04
therefore simulates **three trajectories** across the horizon set, and the decision must survive the
comparison, not merely the projection of itself:

1. **The chosen option** — the path in the Decision Object's `chosen` field, projected forward.
2. **The strongest discarded alternative** — the best of the `discarded_alternatives` (DRK-00 §I.3),
   projected forward on the *same* horizons. This is the counterfactual proper: "what would have
   happened had we chosen otherwise?" A decision cannot claim superiority it never tested against its
   own best rejected option, and the Default Suspicion Rule (fewer than two genuine options caps the
   DCS) has already guaranteed such an option exists to simulate.
3. **The null option** — do nothing; make no change; let the current state run forward untouched. The
   null trajectory is the one most systems omit and the one that most often wins: a great many
   decisions are worse than their own null, because the problem they solve was not forced (DEFER
   territory) or was already tolerable. Omitting the null is how a review approves motion for its own
   sake.

Each trajectory is projected across every window in the horizon set from I.2, producing a
trajectory-by-horizon grid. The chosen option "survives its own simulation" only if it dominates *both*
the strongest discarded alternative and the null across the horizons that matter for its type — not on
a single favorable window, and not against a strawman alternative.

### II.2 Second- and third-order effects are the simulation's later steps

DRK-02 §II.4 sealed the division of labour precisely: **DRK-02 owns the causal *depth* — orders of
consequence, "and then what does that cause" — at classification time; DRK-04 owns the temporal
*horizon* — "and where is that in a year" — at simulation time.** DRK-04 does not re-enumerate the
second- and third-order effects; it *receives the third-order effect set from DRK-02 as the seed* and
places each effect on the timeline. The relationship is that an order is a step *outward* in causation
and a horizon is a step *forward* in time, and a decision's real cost lives where the two intersect: a
third-order effect that DRK-02 identified (the stale-cache example's "on-call must now reason about
cache coherence during every latency incident") is not a first-month cost — it expresses only after the
cache has been live long enough to accumulate incidents. DRK-04's job is to answer "*at which horizon*
does this third-order effect actually bite?" For the chosen trajectory this converts DRK-02's static
causal chain into a dated liability schedule; for the discarded and null trajectories it does the same,
so the comparison is order-for-order and horizon-for-horizon. A decision whose first-order effect is
attractive but whose third-order effect (seeded by DRK-02) lands as a permanent operations tax at the
one-year horizon is a decision that wins the near column and loses the far one — the exact shape §II.5
routes away from APPROVE.

### II.3 Opportunity cost — the value of the foregone path

SDD-OS Parte V §19 states the obligation in one line: every decision means giving up others; ask what
we stop being able to do. DRK-04 mechanizes it as a direct read of the trajectory grid rather than a
separate analysis. **Opportunity cost is the value of the best foregone alternative** — concretely, the
delta between the strongest-discarded trajectory (II.1 #2) and the chosen trajectory at each horizon,
*plus* the optionality the chosen path forecloses that the alternatives would have preserved. The first
term is already computed by the counterfactual comparison; the second term is where opportunity cost
becomes sharp, because a Tipo-C choice does not merely forgo the value of one alternative — it forgoes
the *entire set* of futures the one-way door closes (DRK-02 I.3's "one-way door" signal is exactly an
optionality forfeiture). The capability-placement flavor of this cost — the spend committed to building
X instead of reinforcing an adjacent existing capability — is owned and quantified by the D2A engine,
whose counterfactual-spend case DRK-04 cites rather than re-derives; DRK-04 consumes D2A's placement
verdict (via DRK-01 Stage 7) and folds its foregone-spend figure into the opportunity-cost term. The
point DRK-04 adds over Parte V's one line is that opportunity cost is *horizon-dependent*: a path that
forgoes little at one quarter may forgo an entire strategic direction at three years, and the
adaptive horizon is what makes that visible.

### II.4 Strategic ROI as ranges, never points

SDD-OS Parte V §20 assigns each decision an Expected ROI, Expected Cost, Expected Complexity, and
Expected Risk. DRK-04's deepening of that layer is a single discipline that changes everything: **each
of the four is a range, never a point.** A point estimate of ROI is a false precision that launders an
assumption into a number — the optimistic-ROI-inflation failure mode (Part III) is precisely the habit
of reporting the best-case point as *the* estimate. DRK-04 requires each of the four to be expressed as
a low–high band whose *width* is itself information: a wide band signals high uncertainty and, when the
decision is also Tipo-B/C, is a direct RUN-EXPERIMENT trigger (narrow the band cheaply before committing
the irreversible path). The four bands are read against the horizon set — expected cost at one quarter
differs from expected cost at three years for a schema decision whose accumulation grows monotonically —
so the ROI layer is not a single verdict but a banded profile across time.

| Strategic-ROI dimension | Expressed as | Read against | What a wide band means |
|---|---|---|---|
| **Expected ROI** | low–high band | each horizon in the set | uncertain payoff; if Tipo-B/C → RUN-EXPERIMENT to narrow before commit |
| **Expected Cost** | low–high band | each horizon (accumulation-aware) | cost that grows with time (schema/dependency decay) shows as a widening far band |
| **Expected Complexity** | low–high band | fed by DRK-02 entropy delta (per-dimension) | entropy-raising decisions carry a rising complexity band even when reversible |
| **Expected Risk** | low–high band | fed by DRK-02 Tipo + DBR + accepted_risks | a Tipo-C high-DBR decision cannot honestly show a narrow low-risk band |

Crucially DRK-04 does **not** collapse the four bands into a single scalar score. Collapsing them would
be the E3 Layer-Flattening error DRK-00 warns against and would let a high ROI band paper over a
high-risk band — exactly the arithmetic that approves a lucrative one-way door. The bands are carried
separately onto the Decision Record, and the DCS (DRK-00 §II.4) remains a *proxy* that routes attention,
never a certification derived by averaging these ranges. Token and compute economics inside any of these
bands are priced by CO-01/token_irr, not re-derived here (the Cost surface's spend delta already
delegated to CO-03 at DRK-02 §II.3); DRK-04 consumes those figures and never stands up a parallel
accountant.

### II.5 The routing rule — when a first-order/short-horizon winner loses

The output of Part II is not a verdict; DRK-04 is a mechanism the DRK-01 Stage 8 adversarial pass
*invokes*, and Stage 9 owns the final verdict via the fixed precedence. But the simulation produces a
sharp routing *signal* that Stage 8 consumes, and it is the whole reason the dataset exists: **a decision
that wins only on the first-order effect and the short horizon, but loses on the third-order effect or
the long horizon, is not an APPROVE.** The trajectory grid makes this mechanical rather than a matter of
taste — the chosen option's dominance is read column by column:

- Wins the near columns, loses the far columns to the **null** option → the decision is not yet forced;
  deciding now spends optionality for no gain → **DEFER**.
- Wins the near columns, loses the far columns to the **strongest discarded alternative** → the framing
  or the option choice is wrong; the review returns the corrected framing, not a yes/no → **REFRAME**.
- Loses a far column because a *cheaply resolvable* uncertainty (a wide ROI/Risk band, II.4) drives the
  divergence, and the decision is Tipo-B/C → resolve the band before committing → **RUN-EXPERIMENT**.
- Dominates both counterfactuals across the horizons that matter for its type, with bands whose widths
  are proportionate to its reversibility → eligible for **APPROVE** (or APPROVE-WITH-CONDITIONS if the
  dominance is contingent on a monitor or a rollback path binding the far-horizon risk).

The rule encodes the axis's core insight about time: reversibility buys the right to be wrong *cheaply*,
so a Tipo-A decision that wins the near columns is allowed to APPROVE even with an unexamined far column
(there is no far liability to examine — it can be undone). A Tipo-C decision is not, because its far
column *is* the liability, and a short-horizon win is exactly the illusion the fixed-ladder error of I.1
produces. The simulation is thus the temporal enforcement of block-narrow/recommend-wide: it never
blocks (blocking is the L4 Tipo-C-∧-<E3 twin-condition, owned by DRK-01 §III.2), but it supplies the
signal that keeps a far-horizon-losing irreversible decision from reaching APPROVE unexamined.

---

## PART III — INVARIANTS, FAILURE MODES, INTEGRATION

### III.1 Invariants

1. **Horizon is derived, by type.** The horizon set is a function of the DRK-02 Tipo and the DRK-00
   taxonomy, never author-supplied and never the fixed ladder applied uniformly. (No-Autopromotion;
   corrects the single-horizon error of I.1.)
2. **Three trajectories, always.** Every L3+ simulation runs the chosen option, the strongest discarded
   alternative, and the null option across the same horizons. Omitting any of the three is a defect —
   the null in particular is never optional.
3. **Depth is DRK-02's, horizon is DRK-04's.** DRK-04 receives the third-order effect set as a seed and
   dates it; it never re-enumerates causal orders and never re-derives reversibility, DBR, or entropy.
4. **ROI is banded, never a point, never collapsed.** Each of the four strategic-ROI dimensions is a
   low–high band read against the horizon set; the four are carried separately and never averaged into a
   scalar. (Anti-Layer-Flattening.)
5. **Structural ceiling at three years.** A consequence expressing only beyond three years is flagged
   `structural` and handed to the Owner as a named unknown, never simulated as knowable. (Temporal
   analogue of DRK-02's third-order stop.)
6. **Simulation signals, never blocks.** DRK-04 produces a routing signal for DRK-01 Stage 8/9; the
   verdict is Stage 9's by fixed precedence, and the only block is DRK-01's L4 twin-condition.
7. **Cross-ref, not re-derive.** Reversibility/DBR/entropy from DRK-02, evidence levels from ACIS,
   token/compute economics from CO-01/token_irr, placement/foregone-spend from D2A. DRK-04 composes; it
   forks none. (GK-00 one-system.)

### III.2 Failure modes and guards

| Failure mode | Symptom | Guard |
|---|---|---|
| Single-horizon bias | Every decision judged on the fixed 1mo–3yr ladder; probes over-weighted, one-way doors under-weighted | I.2 horizon-by-type mapping derived from Tipo/taxonomy; `V-DRK-DEPTH` scenario over an experiment vs a public contract |
| Simulation theater | The chosen option is projected forward alone and "survives" trivially | II.1 three-trajectory rule; the strongest-discarded and null trajectories must be run on the same grid |
| Ignoring the null option | Motion approved for its own sake against a tolerable status quo | Invariant 2; the null trajectory is mandatory and DEFER is reachable when null wins the far columns |
| Optimistic-ROI inflation | Best-case point reported as *the* ROI estimate | Invariant 4 banded ROI; a point estimate is a rejected input; wide Tipo-B/C bands trigger RUN-EXPERIMENT |
| Strawman counterfactual | A weak discarded alternative simulated so the chosen option wins | II.1 #2 requires the *strongest* discarded alternative; Default Suspicion Rule guarantees a genuine one exists |
| Depth/horizon confusion | DRK-04 re-enumerates causal orders; DRK-02 attempts a 1-year projection | Invariant 3; the seed-and-date contract with DRK-02 §II.4 is explicit |
| False far-horizon precision | A five-year number fabricated as if knowable | Invariant 5 structural ceiling; beyond-3yr consequences flagged, not simulated |
| Scalar ROI collapse | Four bands averaged into one score that hides a high-risk band | Invariant 4; bands carried separately; DCS stays a proxy, never a certification |

### III.3 Integration — providers and consumers

- **Consumes from DRK-02:** the Tipo (sets the horizon set and the far-column liability weight), the
  composite DBR (widens the Expected-Risk band and the number of surfaces whose trajectories are
  tracked), the per-dimension entropy delta (feeds the Expected-Complexity band), the Tipo-B decay
  vector (becomes the dependency/schema decay checkpoint in the horizon set), and — the load-bearing
  input — the **third-order effect set** as the seed dated across horizons.
- **Consumes from D2A / ACIS / CO:** D2A's placement verdict and foregone-spend figure (opportunity-cost
  term, via DRK-01 Stage 7); ACIS evidence levels (a wide band on under-evidenced input is the
  RUN-EXPERIMENT trigger, gated at ACIS `E3` for Tipo-C); CO-01/token_irr for any token/compute figure
  inside the four bands.
- **Feeds DRK-01 Stage 8 (adversarial pass):** the trajectory grid is the material question 4 ("what
  risk are we underestimating?") interrogates, and the §II.5 routing signal (DEFER/REFRAME/RUN-EXPERIMENT/
  APPROVE-eligible) is handed to Stage 9's precedence resolution.
- **Feeds SDD-OS Parte VI:** the horizon set fixes the schedule of `predicted_consequences`
  observables that Parte VI later scores against realized outcome — DRK-04 owns the projection, Parte VI
  the settlement, sharing the clock (I.4).
- **Relationship to DRK-06:** the opportunity-cost and optionality-forfeiture terms (II.3) are where
  this dataset presses on the **irreducible optionality tension** DRK-06 owns — the standing conflict
  between committing now (buying progress, spending optionality) and deferring (preserving optionality,
  spending time). DRK-04 *quantifies* the two sides of that tension across horizons; it does not
  *resolve* it — DRK-06 holds it as irreducible and DRK-04 supplies the priced trajectory that lets the
  Owner see the trade rather than have it hidden. A simulation that pretended to dissolve the tension by
  producing a single "optimal" horizon would be violating DRK-06's separation.

### III.4 Open questions (carried to DRK-06 / Generation-One)

- When the strongest-discarded trajectory and the null trajectory *both* beat the chosen option but on
  *different* horizons (null wins near, alternative wins far), which routing signal dominates — DEFER or
  REFRAME? The §II.5 rules treat them separately; a genuine split needs a precedence DRK-06 tension
  analysis may own.
- How is the width of an ROI/Risk band itself evidenced? A band is only as honest as the reasoning that
  set its edges; does a suspiciously narrow band on a high-uncertainty decision warrant its own
  REQUEST-EVIDENCE, and at what ACIS level? (DRK-03 burden × DRK-04 band.)
- Does a `structural`-flagged beyond-3yr consequence ever justify escalating an otherwise-L3 decision to
  L4, on the grounds that an un-simulatable long-horizon liability is itself a foundational-tier signal?
  (DRK-00 §II.3 routing × the structural ceiling.)
- For a cluster of individually-reversible decisions whose *combined* far-horizon trajectory is
  entropy-catastrophic though each alone is benign, does DRK-04 simulate the cluster, or is that
  strictly DRK-05's over-time debt integration? (DRK-02 II.5 entropy accumulation × DRK-05.)

### III.5 Done criteria for DRK-04

The simulation layer is complete when: `decision_kernel.py` Stage 8 selects a horizon set by decision
type from the Tipo and taxonomy (never the uniform fixed ladder), and `V-DRK-DEPTH`'s experiment-vs-
public-contract scenario proves the two receive different horizon sets; the counterfactual simulation
runs all three trajectories (chosen, strongest-discarded, null) across the horizon set and a scenario
proves the null trajectory can win the far columns and route to DEFER; the strategic-ROI profile is
emitted as four separate bands read against the horizons, and a point-estimate input is rejected; the
third-order effect set is consumed from DRK-02 and dated rather than re-enumerated
(`V-DRK-CROSS-REF-NOT-RENARRATE`); the §II.5 routing signal reaches Stage 9 and a first-order-winning /
third-order-losing decision is shown routing to REFRAME or DEFER rather than APPROVE; and the horizon
set is written onto `predicted_consequences` so Parte VI can later score them. Until the kernel judges a
real probe on a days horizon and a real public-contract decision on a three-year horizon *in the same
run*, DRK-04 is doctrine, not an operating floor — the exact state SDD-OS Parte V §14 was found in at
STOP #1.
