# SDD-OS PARTE VI — DECISION ACCOUNTABILITY & ATTRIBUTION

> The sixth Part of SDD-OS, and the one concept the Decision OS (Parte V) named nowhere: after a
> decision is acted on, its predicted consequences are scored against what actually happened, and the
> *reasoning* that produced it is judged separately from the *outcome* it received. Parte V made the
> decision an auditable asset *before* action; Parte VI closes the loop *after* it — the difference
> between a system that records decisions and a system that learns from them. **Home:** the SDD-OS
> family (Owner-chosen, STOP #1 2026-07-11), consumed by the Decision Review Kernel (DRK) as the
> `OBSERVED → ATTRIBUTED` states of a Decision Record. **Cross-references (never re-narrated):**
> `fd_04_prover` (the prediction-proving pattern), `modules/liveness/` (outcome observation, D1),
> CO-12 (the single readiness instrument this feeds), ACIS (evidence levels).

---

## PART I — THE TWO-LEDGER PRINCIPLE AND THE PREDICTION RECORD

### VI.1 Why outcome is not the measure of a decision

The most seductive error in decision-making is to judge a decision by its result. It is seductive
because the result is visible and the reasoning is not; it is an error because the result is a
convolution of four things, only one of which the decider controlled. A decision can be excellent and
end badly (a well-priced risk that landed on the wrong side of its variance); it can be terrible and
end well (an unconsidered gamble the world happened to reward). A system that counts the second as a
win and the first as a failure will, over time, train itself toward confident gambling and away from
careful reasoning — it will learn exactly the wrong lesson, and it will learn it with the full
authority of "the data." SDD-OS Parte V built the machinery to record *why* a decision was made;
Parte VI exists to ensure that record is judged on its own terms, so the stack learns to reason well
rather than to be lucky.

This produces the founding rule of the accountability layer: **reasoning quality and outcome quality
are two separate ledgers, scored independently, and never collapsed into one number.** The reasoning
ledger asks: given what was knowable at the time, was this the right decision? The outcome ledger
asks: what actually happened? The two are compared, but a divergence between them is not an error to
reconcile — it is the most valuable signal the system produces, because it is where luck and
context-change live, and those are precisely the things a decider must learn to distinguish from
their own judgment.

### VI.2 The Prediction Record

Every Decision Object carries a required `predicted_consequences` field (DRK-00 §I.3): what the
decider expects to happen, each with a horizon (DRK-04 defines the adaptive horizon per decision
type — an experiment is judged in days, a platform choice in quarters). Parte VI turns this field
into a falsifiable **Prediction Record**, structured so that "did it come true" is answerable without
interpretation:

| Field | Meaning |
|---|---|
| `claim` | the specific predicted consequence, stated so it can be checked |
| `horizon` | when it should be observable (from DRK-04) |
| `observable` | the concrete signal that would confirm or refute it — the metric, the state, the event |
| `confidence_at_decision` | the DCS the decider held when predicting (DRK-00 §II.4) |
| `realized` | filled at the horizon: what actually happened on that observable |
| `error` | the divergence between claim and realized |

The discipline mirrors ACIS falsifiability: a prediction without a named `observable` is not a weak
prediction but a **non-prediction** — it cannot be scored, so it cannot teach. The kernel refuses to
mark a Decision Record's `predicted_consequences` complete unless each claim has an observable, the
same way ACIS refuses to promote a claim without a falsifier. This is not re-deriving ACIS; it is
applying its one governing idea — *a claim you cannot check is not a claim* — to the decision surface.

### VI.3 Scoring prediction against reality

At each prediction's horizon, `modules/liveness/` (which already observes whether shipped work is
actually live and used) supplies the realized signal, and the accountability engine computes the
`error`: the gap between predicted and realized on the named observable. The proving mechanism reuses
the `fd_04_prover` pattern — a probe that re-checks a claim on a schedule doubles as the regression
test for it — so a decision's predictions become, over their horizons, a stream of scored proofs. The
engine never invents the realized value; if the observable cannot be measured at the horizon, the
prediction is marked `unobservable`, not silently passed. An unobservable prediction is itself a
finding: it means the decider predicted something that could not be checked, which is a reasoning
defect the next decision should avoid.

The scored predictions feed **CO-12** — the single readiness instrument the whole stack reports
through — as one more producer, never a parallel accountant (the FD-07 invariant every family
obeys). A decider whose predictions are systematically well-calibrated is a readiness signal; one
whose predictions systematically miss is a signal that its evidence burdens (DRK-03) are set too low.

---

## PART II — THE ATTRIBUTION MODEL

### VI.4 Decomposing an outcome into its four sources

When a decision's outcome is known and its predictions scored, the accountability engine performs the
act Parte V could not: it **attributes** the outcome to its sources. Every outcome is a sum of four
contributions, and the entire purpose of attribution is to separate the one the decider controlled
from the three they did not:

| Source | Question it answers | What it teaches |
|---|---|---|
| **Reasoning quality** | Given what was knowable, was the decision sound? | the only source the decider controls; the thing to improve |
| **Execution quality** | Was the decision implemented as decided? | a good decision badly executed is an execution defect, not a decision defect |
| **Luck (variance)** | Did a genuinely unpredictable factor swing the result? | a well-priced risk that landed badly is not a reasoning error |
| **Context change** | Did the world shift after the decision such that the reasoning no longer applied? | a right-at-the-time decision the world invalidated is not a reasoning error |

The four-way separation is the intellectual core of Parte VI and the answer to the prompt's demand
for "mecanismos de atribución correcta (calidad del razonamiento vs calidad de ejecución vs suerte vs
cambios de contexto)." Without it, every retrospective collapses to "it worked / it didn't," which
teaches the stack nothing about *why* and trains it toward the outcome bias VI.1 warns against.

### VI.5 How the separation is performed

The engine does not guess the split; it derives it from evidence already on the Decision Record and
its downstream trace:

- **Execution isolation.** Compare the decision as decided (the Decision Object's `chosen` + its
  conditions) against what was actually built (the commits, the DRK `APPROVE-WITH-CONDITIONS`
  conditions, whether they held). A gap here attributes outcome to execution, not reasoning. This
  reuses `modules/liveness/` (was it actually shipped as decided) rather than re-deriving it.
- **Luck isolation.** A decision's `accepted_risks` field (DRK-00 §I.3) is the decider's own
  ex-ante statement of what could go wrong by chance. If the realized failure matches an
  `accepted_risk` that was correctly priced, the outcome is attributed to variance — the decider saw
  it, priced it, and it landed the wrong way. This is why the accepted-risks field is required: it is
  the only way to distinguish a priced risk (luck) from an unconsidered one (reasoning defect).
- **Context isolation.** Compare the decision's `evidence` and `constraints` at decision time against
  the world at outcome time. If a `fact` the decision rested on became false through no fault of the
  reasoning — a dependency changed, a requirement shifted — the outcome is attributed to context
  change. A precedent reversal (DRK-05) is the archetypal context-change signal.
- **Reasoning residual.** What remains after execution, luck, and context are removed is the
  reasoning contribution — the part the decider owns. This residual, not the raw outcome, is what
  updates the decider's calibration.

### VI.6 Calibration — the long game

A single attributed decision teaches little; the value compounds across many. The calibration layer
tracks, over the population of scored decisions, whether the decider's `confidence_at_decision`
matches its realized reasoning-residual accuracy — the classic calibration question: *when you were
80% confident, were you right 80% of the time?* Systematic over-confidence, under-confidence, or a
directional bias (always too optimistic about reversible decisions, always too pessimistic about
platform decisions) becomes visible only in aggregate, and only once luck and context are stripped
out — which is why attribution must precede calibration. The three anti-capture biases DRK-07 guards
against (never-reject, always-reject, always-platform) are detected *here*, as calibration drifts in
the population of Decision Records, not asserted as opinions. Calibration is the mechanism by which
the authority audits *its own* judgment with the same rigor it applies to others' — the closing
clause of `PR-DECISION-AUTHORITY-LIMITS-001`.

---

## PART III — INVARIANTS, INTEGRATION, DONE CRITERIA

### VI.7 Invariants

1. **Two ledgers, never one.** Reasoning quality and outcome quality are scored separately; no metric
   collapses them. A lucky bad decision is never recorded as a good one.
2. **No prediction without an observable.** A predicted consequence lacking a checkable observable is
   a non-prediction and blocks Record completion (falsifiability, applied to decisions).
3. **Realized values are observed, never invented.** Unmeasurable-at-horizon predictions are marked
   `unobservable`; the engine never fabricates a realized value or silently passes.
4. **Attribution precedes calibration.** Bias is detected only after execution, luck, and context are
   isolated; raw outcomes never update calibration directly.
5. **Feed the one instrument.** Scored predictions and calibration drifts feed CO-12; no parallel
   accountant is created.
6. **Append-only.** Accountability fields are appended to the existing Decision Record; the original
   reasoning trace is never rewritten in light of the outcome (that would erase the very divergence
   that teaches).

### VI.8 Failure modes and guards

| Failure mode | Symptom | Guard |
|---|---|---|
| Outcome bias | Lucky bad decisions praised, unlucky good ones blamed | two-ledger invariant; luck isolation via accepted_risks |
| Hindsight rewrite | Reasoning trace edited to match the outcome | invariant 6 append-only |
| Vague prediction | "It'll be better" — unscorable | invariant 2, required observable |
| Attribution laundering | Every failure blamed on luck/context | requires the risk to have been PRICED ex-ante; unpriced failure = reasoning defect |
| Calibration on noise | Bias claimed from too few decisions | population threshold before a bias is reported (telemetry-before-claims) |

### VI.9 Integration and done criteria

`modules/decision_review/accountability.py` implements the Prediction Record scoring, the four-way
attribution, and the calibration aggregation, consuming `modules/liveness/` for realized signals and
the `fd_04_prover` proving pattern for scheduled re-checks, and feeding CO-12. Parte VI is done when a
Decision Record can transition `OBSERVED → ATTRIBUTED` with each prediction scored (or honestly marked
`unobservable`), the outcome decomposed into the four sources, and the reasoning-residual — not the
raw outcome — recorded as the calibration update; and when `V-DRK-ACCOUNTABILITY` (prediction scored
vs outcome) and `V-DRK-ATTRIBUTION` (the four sources separated) pass ×3 hermetic. Until a real
decision's prediction is scored and its outcome attributed, the loop Parte V opened remains open — the
stack records decisions but does not yet learn from them, which is the exact gap this Part closes.

### VI.10 Open questions (Generation-One)

- How many scored decisions are enough before a calibration bias is actionable rather than noise?
- When attribution assigns an outcome to context-change, should the superseding context automatically
  open a precedent-reversal Record in DRK-05, or wait for a human to ratify the shift?
- Can execution-quality be isolated cleanly when the same agent both decides and executes, or does
  honest attribution require the decider and executor to be different actors (the ACIS
  model-consensus concern, applied to decisions)?
