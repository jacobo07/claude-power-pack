# DRK-01 — Review Kernel & Verdict Engine

> The operating heart of the Decision axis. DRK-00 fixed the objects (Decision Object, Record,
> evidence/confidence models), the taxonomy, the ten-verdict ontology, and the L0–Ln routing. DRK-01
> defines the **pipeline** that carries a candidate decision from proposal to recorded verdict, the
> **composition contracts** by which it borrows judgment from the sealed families instead of
> re-deriving it, the **adversarial pass** that tries to destroy the decision before approving it,
> and the **block-gate** — the single narrow point where the authority may refuse rather than
> recommend. **Parent it DEEPENs:** SDD-OS Parte V §16 (Adversarial Review), §29 (Governance
> Pipeline). **Cross-references (never re-narrated):** arch-decision `arch_check`, one_shot
> `compiler`, spec_gate `classify_tier`, d2a_engine, ACIS `epistemic_ladder`, CO-03 router,
> owner_queue.

---

## PART I — THE REVIEW PIPELINE

### I.1 The pipeline is a sieve, not a gate

The most common failure of a decision authority is that it behaves as a gate every decision must
pass through — which makes it either a rubber stamp (if it approves everything) or a bottleneck (if
it blocks). DRK is built as a **sieve**: the overwhelming majority of choices fall through the first
aperture and are never touched, and each subsequent aperture is narrower, so that only the few
decisions that are genuinely consequential reach the expensive stages. Every stage below is
skippable by routing; a Tipo-A, low-impact decision touches stages 1–4 and exits; only a Tipo-C,
public-contract decision traverses all nine. The pipeline's cost is therefore proportional to the
decision's consequence, which is the entire point of risk-based routing (DRK-00 §II.3).

### I.2 The nine stages

**Stage 1 — Scope test.** Apply the five consequence thresholds (DRK-00 §I.2). If the candidate
crosses none, emit `L0 — no review` and stop. No object is instantiated, no Record is written, no
tokens are spent. This stage is the kernel's most-exercised path and its most important: an
authority that cannot cheaply say "this is not my concern" becomes the tax it was built to prevent.

**Stage 2 — Instantiate.** Build the Decision Object from the caller's input, filling the *required*
fields (statement, problem, options, chosen, rationale, accepted_risks, discarded_alternatives,
dependencies, evidence, predicted_consequences). Missing a required field is not an error to raise —
it is a signal: a decision presented with one option and no discarded alternatives is *itself*
evidence of an unconsidered choice, and the kernel records that. The **Default Suspicion Rule** is
enforced here numerically: fewer than two genuine options caps the eventual DCS and biases the
verdict toward `REFRAME` or `REQUEST-EVIDENCE`.

**Stage 3 — Classify.** Score the seven taxonomy axes (DRK-00 §II.1). Reversibility is delegated to
the DRK-02 classifier; blast radius to the DRK-02 compute; task-tier is read from spec_gate
`classify_tier` as one input to the scope/impact axes. The output is a seven-tuple of low/medium/high.

**Stage 4 — Route.** Map the taxonomy maxima to a review tier L1–L4 (DRK-00 §II.3). The tier
determines which of the remaining stages run. At L1 the kernel jumps to Stage 9 (record only). This
is the sieve's second aperture.

**Stage 5 — Evidence & burden.** For L2+, compute the evidence burden required by the reversibility
tier (DRK-03) and compare it to the supplied evidence, reading each item's epistemic level from ACIS.
If the burden is unmet, the verdict is provisionally `REQUEST-EVIDENCE` with the *exact* missing
evidence named; the pipeline still completes so the Record captures the gap.

**Stage 6 — Precedent collision.** For L2+, hand the decision statement to arch-decision `arch_check`.
A `COLLISION` on a veto-class source (a Hard Rule, a sealed "never") drives the verdict toward
`REJECT`; a `WARNING` is attached to the Record as context; a `CLEAR` proceeds. The kernel does not
re-implement precedent search — arch-check owns the vault index and the collision scoring; DRK
consumes its verdict.

**Stage 7 — Placement (build/capability decisions only).** If the decision is "should we build/keep/
generalize capability X", hand it to d2a_engine. Its DUPE VERDICT and recommended operation map
directly to DRK verdicts: a high-coverage duplicate → `CONSOLIDATE`; a premature generalization →
`KEEP-LOCAL`; a `DO_NOT_BUILD`/`RETIRE` → `REMOVE`. DRK does not re-run duplicate detection; it
translates D2A's structured output into the decision verdict ontology. This is the cleanest example
of cross-ref-not-re-narrate: the entire "capability placement" capability the proposal listed is a
one-line delegation here.

**Stage 8 — Adversarial pass (L3+).** Attempt to destroy the decision (Part III). Surviving the pass
is a precondition for `APPROVE` at L3+; failing it drives `REFRAME`, `REQUEST-EVIDENCE`, or
`RUN-EXPERIMENT` depending on *why* it failed.

**Stage 9 — Verdict & record.** Emit exactly one verdict from the ten-item ontology, resolving any
provisional verdicts from stages 5–8 by precedence (REJECT > REFRAME > REQUEST-EVIDENCE >
RUN-EXPERIMENT > the placement verdicts > DEFER > APPROVE-WITH-CONDITIONS > APPROVE). Write the
Decision Record to the append-only Registry. At L4, route the Record to owner_queue and apply the
block-gate (Part III.2) before returning.

### I.3 Precedence resolution — why the order is fixed

Stages 5–8 can each propose a provisional verdict; Stage 9 must collapse them to one. The precedence
order is not arbitrary — it encodes the axis's values. `REJECT` (a cited contradiction) outranks
everything because a decision that violates a sealed invariant cannot be salvaged by more evidence.
`REFRAME` outranks the evidence verdicts because there is no point gathering evidence for the wrong
problem. `RUN-EXPERIMENT` outranks `DEFER` because cheaply resolvable uncertainty should be resolved,
not deferred. `APPROVE` is last because it is the claim that must survive every other check. A kernel
that resolved these in a different order would encode different values; the order is therefore part
of the doctrine, not an implementation detail.

---

## PART II — COMPOSITION CONTRACTS

### II.1 The contract discipline

DRK's authority is almost entirely *borrowed*. It does not know whether `redis` was already rejected
— arch-check does. It does not know whether capability X duplicates an existing module — d2a does. It
does not know the epistemic level of a measurement — ACIS does. DRK's genuine contribution is the
*composition*: it assembles these judgments into one verdict about one decision and records it. This
section fixes each contract as `provider → what DRK receives → how DRK uses it`, so that a change in a
provider's output is a detectable contract break, not a silent behavior drift.

### II.2 The seven contracts

| Provider | DRK receives | DRK use |
|---|---|---|
| **arch-decision `arch_check`** (STDIN: decision statement) | `verdict ∈ {COLLISION, WARNING, CLEAR}` + cited sources | Stage 6: COLLISION-on-veto → REJECT; WARNING → Record context; CLEAR → proceed |
| **d2a_engine** (build/keep/generalize decisions) | DUPE VERDICT + coverage% + recommended operation (of the 15) | Stage 7: map operation → CONSOLIDATE / KEEP-LOCAL / REMOVE |
| **ACIS `epistemic_ladder`** (each Evidence item) | level `E0…E7` | Stage 5: burden check counts strong-typed evidence at ≥E3; L4 requires ≥E3 from a second substrate |
| **spec_gate `classify_tier`** (task description) | task tier `0…3` | Stage 3: one input to the impact/scope axes |
| **one_shot `compiler`** (for build decisions with a contract) | scope / out_of_scope / done_gate / budget | Stage 7: an APPROVE-WITH-CONDITIONS may bind the one_shot done_gate as its condition |
| **CO-03 router** (the review itself) | recommended model / deterministic rung | meta: how much the *review* should cost — a Tipo-A review runs deterministic, never on Opus |
| **owner_queue** (L4 decisions) | escalation receipt | Stage 9: L4 Records are queued for Owner; the block-gate awaits Owner or the twin-condition |

### II.3 The self-cost contract (CO-03) — the authority must not be a burn

A decision authority that spends more compute reviewing a decision than the decision is worth is a
net loss, and would violate the CO-01 Work-Units-per-MToken metric the whole stack answers to. DRK
therefore routes *its own* review cost through CO-03: L1 records are pure deterministic writes; L2/L3
classification and burden checks are deterministic or Haiku; only the L3+ adversarial pass and the L4
multi-perspective review may justify Sonnet, and Opus is reserved for the rare L4 decision whose
irreversibility genuinely warrants it (HR-COST-001 applies to the authority itself). The kernel that
reviews a rename on Opus has committed the exact anti-pattern DRK-07 calls out as the complexity
bias. Self-cost discipline is a first-class contract, not an afterthought.

### II.4 What DRK provides back

- To the **calling agent**: the Verdict + a human-readable rationale (≤200 words, mirroring
  arch-check's advisory cap) + the Decision Record id.
- To **CO-12**: a readiness signal each time a decision's prediction is later scored (DRK feeds the
  single instrument; it never stands up a parallel accountant — FD-07 Invariant 1).
- To **arch-decision**: each new Decision Record becomes a future precedent source, so the axis
  compounds — tomorrow's collision check sees today's decisions.
- To **the Owner**: at L4, an escalation with the twin-condition status made explicit.

---

## PART III — ADVERSARIAL PASS, BLOCK-GATE, INVARIANTS

### III.1 The adversarial pass

At L3+ the kernel does not ask "is this decision good?" — a question that invites confirmation. It
asks four destructive questions (the DEEPEN of SDD-OS Parte V §16), each of which must be answered
from the Decision Object, not hand-waved:

1. **Why is this wrong?** Name the strongest concrete failure mode of the chosen option. If none can
   be named, the options were not genuinely explored (→ REFRAME).
2. **What are we ignoring?** Name the reasonable alternative the rationale does not address (the
   Default Suspicion Rule made adversarial). A decision that ignores an obvious alternative is
   under-considered (→ REFRAME or REQUEST-EVIDENCE).
3. **What evidence is missing?** Name the observation that would most change the verdict if it
   existed. If it is cheap to obtain and the decision is Tipo-B/C, the verdict is RUN-EXPERIMENT.
4. **What risk are we underestimating?** Name the second- and third-order effect (SDD-OS Parte V
   §17–18): what happens *after* what happens. Most reviews evaluate only the first-order effect; the
   adversarial pass is where the later orders are forced.

The pass is adversarial in the ACIS sense — it defaults to *refuted* and requires the decision to
survive, rather than defaulting to *approved* and requiring an objection. A decision that survives
all four with cited answers is eligible for APPROVE; one that cannot is routed to the verdict its
weakest answer implies. Crucially, the adversarial pass is run by an actor whose success is measured
by decisions-killed-that-should-have-been, not decisions-approved — the incentive is set so the pass
does not become theater.

### III.2 The block-gate — the one place the authority refuses

At L4, and only at L4, the kernel may **block**: refuse to let the decision proceed autonomously,
holding it for the Owner. The block fires under a single twin-condition, and the narrowness is
constitutional, not conservative:

> **Block iff the decision is Tipo-C (practically irreversible) AND its evidence is below ACIS E3
> (not yet re-derived by a probe or a second substrate).**

Everywhere else — every L1–L3 decision, and every L4 decision that is either reversible *or*
adequately evidenced — the kernel **recommends** and the calling agent or Owner decides. The
asymmetry is the answer to the axis's own central risk (`T-DECISION-AUTHORITY-CAPTURE-001`): an
authority that could block widely would accrete into a bureaucracy that slows the stack; an authority
that could never block would let an irreversible, unevidenced mistake through. Block-narrow,
recommend-wide is the only configuration that avoids both failures, and it is sealed in
`PR-DECISION-AUTHORITY-LIMITS-001`. The block is never silent: it returns the twin-condition status,
the exact missing evidence (from Stage 5), and the reversibility basis (from DRK-02), so the Owner
sees precisely why the gate held and can override with a recorded `owner_override`.

### III.3 Invariants specific to the kernel

1. **Sieve-first.** Stage 1 runs before any instantiation; L0 is free.
2. **Borrowed judgment is cited.** Every provider verdict used in a decision is recorded on the
   Record with its source, so a wrong verdict can be traced to the provider that supplied it.
3. **One verdict.** Stage 9 emits exactly one verdict; provisional verdicts are resolved by the fixed
   precedence, never averaged.
4. **Block-narrow.** The block-gate fires only under the L4 twin-condition; a block anywhere else is a
   defect.
5. **Adversary defaults to refuted.** The L3+ pass requires survival, not objection.
6. **Self-cost-bounded.** The review's own compute is routed through CO-03; the authority never
   burns more than the decision is worth.
7. **Fail-open to DEFER.** Any internal failure (a provider unreachable, an unparseable object)
   yields DEFER with the reason, never a raise and never a default APPROVE.

### III.4 Failure modes and guards

| Failure mode | Symptom | Guard |
|---|---|---|
| Rubber stamp | Adversarial pass always survives | `V-DRK-3-BIAS` never-reject scenario; adversary incentive (III.1) |
| Bottleneck | Kernel blocks or defers widely | Invariant 4 block-narrow; `V-DRK-BLOCK-GATE` |
| Provider drift | A provider changes output, DRK silently mis-uses it | Invariant 2 cited contracts; contract-break test in `tools/test_decision_review.py` |
| Self-burn | Review costs more than the decision | Invariant 6; CO-03 self-cost contract; HR-COST-001 |
| Averaged verdict | Kernel emits a blended/ambiguous outcome | Invariant 3; closed ontology; `V-DRK-VERDICT-ONTOLOGY` |
| Adversary theater | Pass runs but always passes | adversary measured by kills-that-should-be, not approvals |

### III.5 Done criteria for DRK-01

The kernel is complete when `decision_kernel.py` implements the nine-stage sieve with the fixed
precedence; every composition contract in II.2 is wired and covered by a contract-break test; the
adversarial pass runs at L3+ and its four questions are answerable from the Record; the block-gate
fires under exactly the L4 twin-condition and nowhere else (asserted by `V-DRK-BLOCK-GATE`); and the
self-cost routing through CO-03 is observable (an L1 review spends zero model tokens). Until the
kernel refuses a real Tipo-C-∧-<E3 decision and recommends on a reversible one in the same run, the
block-narrow invariant is asserted but not demonstrated.
