# DRK-07 — Governance, Evolution & Authority Limits

> The constitutional dataset of the Decision axis: it governs the governor. Where DRK-00–06 define
> what the authority reviews and how, DRK-07 defines what the authority may and may not do, how it is
> overridden, how it avoids capturing the stack it serves, and how it corrects its own errors. An
> authority without an explicit limit becomes a bureaucracy; an authority that cannot evolve
> ossifies. This dataset is both brakes and steering. **Parent it DEEPENs:** SDD-OS Parte V §15
> (Decision Court), §21 (Governance Tiering), §26 (Fitness Functions). **Cross-references (never
> re-narrated):** one_shot `escalation` (the escalation ladder), owner_queue (the transport), FIOS
> `evolution_engine` (Owner-gated mutation proposals), Parte VI (calibration, the bias detector),
> CO-12 (the instrument).

---

## PART I — THE SCOPE AND LIMITS OF THE AUTHORITY

### VII.1 The constitutional asymmetry

The Decision Review Kernel holds exactly one hard power and it is deliberately narrow. It may
**block** — refuse to let a decision proceed autonomously, holding it for the Owner — only when the
decision is **Tipo-C (practically irreversible) and its evidence is below ACIS E3** (not re-derived
by a probe or a second substrate). This is the L4 twin-condition from DRK-01 §III.2, and DRK-07
elevates it to constitution: it is the *whole* of the authority's coercive power. Everywhere else —
every reversible decision regardless of confidence, every adequately-evidenced decision regardless of
reversibility, every L1–L3 decision — the kernel **recommends**, and the calling agent or the Owner
decides.

The asymmetry is not timidity; it is the only stable configuration. An authority empowered to block
widely would, by the ordinary dynamics of institutions, accrete scope: every incident would justify a
new mandatory review, and the stack would slow under a governance tax that produces the appearance of
safety without its substance. An authority empowered to block nowhere would let an irreversible,
unevidenced mistake through — the one class of error that cannot be walked back. Block-narrow,
recommend-wide is the unique point that prevents both the bureaucratic failure and the negligent one.
It is sealed as `PR-DECISION-AUTHORITY-LIMITS-001` and every other rule in this dataset exists to keep
the authority at that point.

### VII.2 What the authority is explicitly forbidden to do

The limits are stated as prohibitions because a positive grant of power invites expansion while a
prohibition resists it:

| The authority may NOT | Because |
|---|---|
| Block a reversible (Tipo A/B) decision | reversibility is the escape hatch; a cheap-to-undo decision needs no gate |
| Block an adequately-evidenced (≥E3) irreversible decision | the burden was met; the decider earned autonomy |
| Review a choice that crosses no consequence threshold | that is the cognitive tax (DRK-00 §I.2) |
| Auto-apply any change to a sealed dataset, threshold, or rule | evolution is propose-only, Owner-gated (Part III) |
| Certify its own claims | derived fields, No-Autopromotion (DRK-00 §I.3) |
| Overrule a recorded Owner override | the Owner is the final authority; overrides are appended, not reversed |
| Judge a decision by its outcome alone | two-ledger principle (Parte VI) |

### VII.3 The override protocol

The Owner may override any verdict, including a block. An override is never a mutation of the verdict
— the kernel's reasoning stands in the permanent record — but an **appended `owner_override` struct**
on the Decision Record: what was overridden, the Owner's stated reason, the timestamp. The
disagreement between the authority and the Owner is itself institutional knowledge: a pattern of
overrides in one direction is a signal that a threshold is miscalibrated (Part II), and a pattern in
the other is a signal that the authority is drifting toward one of its biases. The override is
evaluated, later, by the same accountability layer that evaluates decisions (Parte VI): was the
overridden verdict or the override the sounder call, judged on reasoning not outcome? An authority
that could not have its overrides evaluated would be claiming infallibility; DRK-07 requires that the
authority's own recommendations enter the calibration population alongside the decisions it reviews.

---

## PART II — ANTI-CAPTURE AND ERROR CORRECTION

### VII.4 The three biases and how they are detected

The prompt names the failure the axis must avoid, and DRK-07 makes it measurable: *an authority that
never rejects anything is theater; one that always rejects is a block; one that always recommends
platform has a complexity bias.* These are not risks to be asserted away — they are **calibration
drifts detectable in the population of Decision Records** (Parte VI §VI.6):

| Bias | Signature in the Record population | The corrective |
|---|---|---|
| **Never-reject** (theater) | APPROVE / APPROVE-WITH-CONDITIONS rate near 100%; adversarial pass never kills | the benchmark's never-reject scenario must yield a non-APPROVE; the adversary is measured by justified kills, not approvals |
| **Always-reject** (block) | REJECT / block rate high; reversible decisions held; override rate high in the permissive direction | Invariant VII.2 (cannot block reversible); a high permissive-override rate flags the drift |
| **Always-platform** (complexity) | CONSOLIDATE / generalize verdicts dominate; KEEP-LOCAL rate near zero | the D2A "temporary duplication acceptable" cases must produce KEEP-LOCAL; the DRK-06 optionality↔simplicity tension is scored |

The three biases are caught by three benchmark scenarios (`V-DRK-3-BIAS`) and, in production, by the
calibration layer watching the verdict distribution. An authority is healthy not when its verdict
distribution is "balanced" — that would be its own bias — but when the distribution *matches the
population of decisions it actually sees*: if the session genuinely proposed ten reversible cheap
decisions, ten APPROVEs is correct, not theater. Calibration measures fit-to-reality, never a target
distribution.

### VII.5 Institutional capture and conservatism

Two slower failures threaten any governance layer. **Capture** is when the authority begins to serve
its own continuation rather than the stack — measured as review cost (DRK-01 §II.3 self-cost) rising
faster than the value of the decisions reviewed, or as scope creep in what crosses the consequence
threshold. **Conservatism** is when the authority's accumulated precedent makes every new thing look
like a violation of something old — measured as the REJECT/DEFER rate rising over time on decisions
that are not in fact more irreversible than past APPROVEd ones. Both are drifts, both are visible only
in aggregate, and both are surfaced to the Owner as advisories, never self-corrected — because an
authority that could rewrite its own limits to resolve its own capture is no longer limited. When
evidence and precedent conflict — a new decision contradicts a prior Record — the authority does not
default to precedent (that is conservatism) nor to novelty (that is amnesia); it routes the conflict
to a precedent-reversal review (DRK-05) where the superseding reasoning must be stronger than the
reasoning it overturns, and the Owner ratifies.

### VII.6 Correcting a high-confidence error

The hardest correction is a decision the authority was confident was right and that proves wrong for
reasoning reasons (not luck or context — Parte VI attribution isolates this). A high-confidence
reasoning error is the most valuable correction the system can make, because it reveals a systematic
flaw in a threshold or an evidence burden, not a one-off. The protocol: the attributed reasoning-error
is traced to the threshold or burden that licensed the decision (which L-tier routed it, which burden
it met); that specific parameter is flagged for Owner review with the full trace; and — only on Owner
ratification — the parameter is adjusted, with the adjustment recorded as an evolution event (Part
III). The error is not hidden, not blamed on luck, and not fixed silently. This is the fitness
function of the authority itself: `% of high-confidence errors traced to a corrected parameter`.

---

## PART III — SELF-EVOLUTION OF THE AUTHORITY

### VII.7 Propose-never-apply

DRK evolves — thresholds recalibrate, precedents update, incorrect doctrine retires, new adversarial
cases are generated — but it never applies a change to itself autonomously. Every mutation is a
proposal to `pending_mutations`-style Owner review, mirroring the FIOS `evolution_engine` and the
cdio-standards-librarian: the authority may detect that its own L3 evidence burden is too low
(calibration shows systematic over-confidence at that tier) and *propose* raising it, but the Owner
promotes the change. An authority that could re-tune its own gates would drift toward whichever
configuration minimized its own friction, which is the capture failure VII.5 names. Propose-never-apply
is to the authority what No-Autopromotion is to ACIS's epistemic levels: the producer never certifies
its own promotion.

### VII.8 The evolution event record

Every proposed mutation carries a full record, so that a change to the governance layer is itself a
governed decision (the authority obeys its own doctrine):

| Field | Meaning |
|---|---|
| `cause` | the calibration drift, benchmark failure, or traced error that prompted it |
| `evidence` | the population signal supporting it, with its `(metric, source, value)` triple |
| `prior` | the threshold/rule/precedent as it stood |
| `change` | the proposed new value |
| `expected_benefit` | what improves, measurably |
| `cost` | the review friction or false-positive risk it adds |
| `risk` | what could go wrong |
| `reversibility` | can the change itself be rolled back (it must be Tipo A/B) |
| `affected` | which datasets, benchmarks, and downstream verdicts change |
| `rollback_criteria` | the signal that would trigger reverting it |

A mutation whose own reversibility is Tipo C is refused: the authority may not make an irreversible
change to itself. This closes the recursion — the governance layer is subject to the same
reversibility discipline it imposes on every decision it reviews.

### VII.9 Invariants

1. **Block-narrow is constitutional.** The L4 twin-condition is the whole coercive power; any block
   outside it is a defect.
2. **Overrides append, are evaluated, never reverse.** The Owner is final; the disagreement is kept
   and later judged on reasoning.
3. **Biases are measured, not asserted.** The three biases are calibration drifts caught by benchmark
   and population, surfaced as advisories.
4. **Propose-never-apply.** No self-mutation is autonomous; the Owner promotes every change.
5. **The authority obeys its own doctrine.** An evolution event is a governed decision with a full
   record; a self-change may not be Tipo C.
6. **Self-cost-bounded.** The authority's own compute never outruns the value of what it reviews.

### VII.10 Done criteria and open questions

DRK-07 is done when: the block-gate fires only under the L4 twin-condition (asserted by
`V-DRK-BLOCK-GATE`); overrides append and enter the Parte VI calibration population; the three biases
each have a passing benchmark scenario (`V-DRK-3-BIAS`); the evolution path proposes to an Owner queue
and applies nothing autonomously (asserted by an evolution-lock test mirroring `V-FIOS-EVOLUTION-LOCK`);
and the authority's own fitness functions (override-correctness rate, high-confidence-error-traced
rate, self-cost ratio) are computed and fed to CO-12. Open questions for Generation-One: how long a
calibration window balances responsiveness against noise; whether an authority reviewing decisions in
a domain it has no precedent for should widen or narrow its burdens; and whether the Owner-override
evaluator, being itself a decision, needs its own accountability trace or whether that regress
terminates safely at the Owner.
