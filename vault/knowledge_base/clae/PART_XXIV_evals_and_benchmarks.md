---
title: "CLAE Part XXIV — Evals and Benchmarks"
family: clae
part: XXIV
depends_on: [XXIII]
feeds: [XXV, XXVI]
status: SEALED
date: 2026-07-26
---

# Part XXIV — Evals and Benchmarks

## 1. Purpose

Parts I through XXIII seeded roughly one hundred and ten evals. This Part is the eval discipline, and
it rests on one unifying observation that makes everything else follow:

> **An eval is an instrument.** Everything in Part XIII applies to it without modification —
> coverage, envelope, perturbation, three-valued output, and a known-answer case.

That framing produces the Part's central requirement, which is almost never met in practice: an eval
needs a **negative control**, because an eval that has never failed is indistinguishable from an eval
that cannot fail. §5 states it, and §9 reports the result of actually running one against this
build's own gate rather than asserting that it would pass.

## 2. What an eval verifies

A **gate** checks an artifact. An **eval** checks whether a rule is being followed. The subject of a
gate is a product; the subject of an eval is a process.

This makes evals the family's self-measurement. Parts XXI through XXIII produced roots, traps and
rules; if none of them are followed, the evals are the only thing that would detect it. An eval suite
is therefore subject to Part I's trap in the most direct possible way — it is a system measuring its
own compliance against criteria it authored — and §7's benchmark requirement exists specifically to
prevent that.

## 3. The eval record schema

1. **Objective** — which rule this verifies.
2. **Setup** — what must exist for it to run.
3. **Pass criteria** and **fail criteria**, stated separately rather than as each other's negation,
   so that *neither* is a possible outcome and is reported as such.
4. **Adversarial variant** — per §4.
5. **False-positive risk** — per §6.
6. **Cost and tier** — per §8.
7. **Negative control** — per §5.
8. **Output arity** — three-valued, per Part XIII §7.

## 4. The adversarial variant

The field most often missing, and the one that determines whether an eval measures compliance or
measures the appearance of it.

> **How would a system that wanted to pass this eval without complying do so?**

The question is not about malice. Ordinary optimization produces the same result: teams and agents
move toward whatever is measured, and an eval with an unexamined cheap-satisfaction path will be
satisfied that way without anyone intending it. That is Part XXI's L3 metric-theater lineage,
entering through the eval rather than through the proxy.

An eval whose adversarial variant is cheaper than genuine compliance is worse than no eval, because
it certifies the cheap path.

Worked example from this family. *Every instrument declares its coverage* can be satisfied by
attaching a coverage statement that says everything, costs nothing, and is never checked against what
the instrument actually detects. The adversarial variant is therefore obvious, and the eval must
verify the coverage claim against an observed detection boundary rather than verifying that a
coverage field is populated.

## 5. The negative control

The requirement that follows from §1, and the cheapest high-value thing in this Part.

> **Every eval requires a known-noncompliant case: an artifact deliberately violating the rule, which
> the eval must flag.**

Without one, an eval reporting compliance is uninterpretable in exactly the way Part II §P8
established for any zero. It has either found compliance, or it is incapable of finding
non-compliance, and its output cannot distinguish those.

Almost nobody does this. Test suites are checked for passing on correct code; compliance checks are
rarely checked for **failing on incorrect** input. And constructing the violating case is usually
trivial — a few lines, once, at the eval's creation.

The negative control is the eval's own known-answer case in Part XIII §8's sense, and it must be
re-run when the eval or its environment changes, since a check that silently stops matching produces
the same clean output as a check that found nothing.

## 6. False-positive risk

A noisy eval gets muted, and Part XV §8 established that muting is institutionally expensive: one
muted check teaches that checks are mutable, and the authority erodes across the whole suite,
including the sound ones.

False-positive rate is therefore a first-class field rather than a quality note. An eval above a
declared noise threshold is a **liability**, not merely a weak signal, and the correct responses are
to tighten it or remove it — never to leave it firing and ignored, which is muting without the
paperwork.

This stack's known-false-positives register exists precisely because this problem was encountered
and handled well: rather than muting the noisy signals, it documented them with a bounded
investigation cost. That is the mature response and it is the model.

## 7. Evals measure compliance; benchmarks measure level

An eval answers *is the rule being followed*. A benchmark answers *how far along is this*.

A family whose self-assessment is entirely eval-shaped has assessed itself with a pass/fail predicate
— which is Part II's founding critique applied to CLAE itself. The family would be reporting
compliance with its own rules while discarding the magnitude of its own gaps.

**CLAE must therefore be benchmarked, not merely eval'd.** Four benchmarks, each producing a level
rather than a verdict:

| Benchmark | What it reports | Source |
|---|---|---|
| **Lineage position** | Which links of which lineages are in place | Part XXI §12 |
| **Enforcement layer distribution** | What fraction of the doctrine has a mechanism | Part XXIII §12 |
| **Derivation ratio** | Observed versus inferred rule origins | Part XXIII §12 |
| **Measurement debt** | Named dimensions the system cannot see | Part IX §5 |

None of these has a passing value. They are levels, they trend, and they are the honest form of a
family whose whole argument is that a predicate discards what matters.

## 8. Tiering

One hundred and ten evals is a programme, not a check. Three tiers by cost and cadence:

- **Continuous** — cheap, per-cycle, automatable. The arity probe, the count-versus-distance plot,
  the undefined-publication check.
- **Periodic** — moderate cost, run on a schedule. The layer census, the horizon-expiry probe, the
  staleness probe.
- **Audit** — expensive, rare, deliberate. The chain-integrity probe, the overlap-clustering probe,
  the lineage-position walk.

The set worth running first, selected by cost against what it reveals:

1. **Arity probe** — can each instrument report could-not-observe? Expected to fail nearly everywhere
   and it invalidates every clean result beneath it.
2. **Count-versus-distance plot** — the fingerprint of fixability bias, two lines and no machinery.
3. **Negative-control census** — which evals have ever been shown to fail? Cheapest way to find out
   which checks are decorative.
4. **Undefined-publication probe** — do quality summaries state what they could not measure?
5. **Layer census** — what fraction of the rule set has any mechanism at all?

## 9. Evidence — a negative control, run

Rather than assert that this build's gate would detect a violation, it was tested.

A deliberately non-compliant artifact was constructed in an isolated working directory, carrying a
banned-vocabulary token, code fences, and a word count far below the depth floor. The gate's three
content checks were run against it, with the expectation that each would fire.

| Check | Result | Verdict |
|---|---|---|
| Contamination | 1 hit against a deliberate token | **DETECTS** |
| Code fences | 2 fence markers found | **DETECTS** |
| Depth floor | 16 words against a 2,893 floor | **DETECTS** |

All three detect. This is a real and useful result: it means the clean results reported across
twenty-three Parts are **not** the output of a check incapable of failing. Within its declared
coverage, the gate works.

It also **partially discharges** the instrument debt recorded in Parts XIII §11, XIV §11 and XIX §11,
and the qualification matters. Those Parts found the gate two-valued — unable to report
*could-not-observe* — and that finding stands unchanged: if the file were absent or the glob matched
nothing, the gate would still report clean. What the negative control establishes is the separate
property that the checks' **detection capability is real**, which was previously assumed. The two are
different claims and only one has now been tested.

A coverage observation also fell out of the run: the contamination check scans twenty-five files
where twenty-three are Parts, so it also covers the charter and the index. That is correct — both are
dataset artifacts under the FP-05 scoping decision — and it was not verified until now.

This is the Part practising its own §5 on the family's own instrument, at a cost of one temporary
file. — OBSERVED, this session.

The stack's wider eval convention — named gate identifiers, explicit pass and fail counters, a
domain-level pass ratio — is a genuine eval framework and the naming discipline is sound. What it
lacks across the board is negative controls and a false-positive field, which is the same finding as
§5 at stack scale rather than at this family's. — Convention OBSERVED from the testing doctrine; the
gap INFERRED.

## 9a. Boundary — when an eval should not exist

Not every rule warrants an eval, and a suite that tries to cover all of them reaches the untiered
state of §8 where none of it runs.

**Where the rule is enforced structurally.** A violation that is unrepresentable — Part XXIII's layer
one — needs no eval, because there is nothing to detect. Writing one anyway produces a check that can
only ever pass, which is §5's blind eval by a different route.

**Where the eval costs more than the violation.** An eval is an economic object exactly as a floor
and an instrument are. A costly check for a cheap, recoverable violation is a net loss however sound
its reasoning, and its cost is paid every cycle while the violation's cost is paid rarely.

**Where the subject is a judgment.** A rule requiring a value-laden determination cannot be verified
by a procedure, per Part XVI's four marks. An eval built against it will verify the *presence* of a
determination rather than its correctness — §10's field-presence failure — and will report compliance
whenever the field is filled.

**Where the negative control cannot be constructed.** Per §17's first open question, some rules about
absence admit no violating artifact, only a violating history. Shipping an eval for one of these
without acknowledging that its detection is untested puts an unverified check into the suite with the
same standing as verified ones — which is Part XI's credibility-borrowing failure arriving among the
evals.

In each case the honest output is a recorded decision not to build the eval, with the reason. An
unbuilt eval that was deliberately declined is a different state from one that was never considered,
and only the first can be revisited when the reasoning changes.

## 10. Failure modes

| Failure | Mechanism |
|---|---|
| **No negative control** | An eval that has never failed, indistinguishable from one that cannot |
| **Cheap adversarial path** | An eval satisfiable more cheaply than compliance, certifying the cheap path |
| **Two-valued eval** | A suite reporting green when it did not run — L6 applied to the family's own verification |
| **Field-presence checking** | Verifying that a declaration exists rather than that it is true |
| **Noisy eval left firing** | Muting without the paperwork; authority erodes across the suite |
| **Eval-only self-assessment** | The family assessing itself with a predicate, which is its own founding critique |
| **Untiered suite** | A hundred-plus evals treated as a check, so none of them runs |

## 11. Detection signatures

1. **The never-red suite.** No eval has failed in memory. Either everything complies or nothing can
   detect otherwise.
2. **The populated field.** Evals verifying that a declaration exists rather than that it corresponds
   to anything.
3. **The ignored red.** An eval that fires routinely and changes nothing.
4. **The pass-rate self-report.** A family reporting its own compliance percentage and no levels.
5. **The unrun suite.** A large eval set with no tiering and no execution record.

## 12. Rule seeds — for Part XXIII

- **PR-CLAE-NEGATIVE-CONTROL** — every eval carries a known-noncompliant case it is shown to flag,
  re-run when the eval or its environment changes. An eval without one is recorded as unverified.
- **PR-CLAE-ADVERSARIAL-VARIANT** — every eval records how it could be satisfied without compliance.
  Where that path is cheaper than compliance, the eval is redesigned.
- **PR-CLAE-EVALS-ARE-INSTRUMENTS** — evals declare coverage, envelope and three-valued output, and
  are subject to every instrument rule.
- **PR-CLAE-VERIFY-THE-CLAIM-NOT-THE-FIELD** — an eval checks that a declaration corresponds to
  observed behaviour, not that a field is populated.
- **PR-CLAE-BENCHMARK-THE-FAMILY** — CLAE's self-assessment reports levels, not compliance. A
  pass/fail self-report is the family's own founding critique, self-inflicted.
- **PR-CLAE-TIER-THE-SUITE** — evals are assigned continuous, periodic or audit tiers. An untiered
  suite of this size does not run.

## 13. Eval seeds — for this Part itself

- **Negative-control census.** For every eval, look for a known-noncompliant case and the date it
  last flagged. This is the cheapest way to find decorative checks and is expected to find many.
- **Adversarial-path probe.** For each eval, attempt the cheapest satisfaction that does not comply.
  Success identifies an eval certifying the wrong thing.
- **Eval-arity probe.** Verify each eval can report could-not-run. An eval suite is the last place a
  two-valued instrument should be, and is a common place to find one.
- **Red-response probe.** For evals that have fired, check whether anything changed. Firing without
  response is muting without the record.
- **Level-versus-verdict probe.** Examine the family's self-reports for levels. Compliance-only
  self-assessment is the failure this Part exists to prevent.

## 14. Production Reality Gate seed — for Part XXV

**Eval Integrity Gate.** An eval result may be cited as evidence only when the eval carries a
negative control demonstrated within the re-validation interval, an adversarial variant that is not
cheaper than compliance, a declared false-positive risk below the muting threshold, and three-valued
output. Results from evals lacking a negative control are recorded as unverified — they may be
correct, and nothing has shown they could have been otherwise.

## 15. Pseudoflow — building an eval

Start from the rule it verifies and state the objective as that rule, not as a general quality aim.

Write pass and fail criteria separately rather than as negations of each other. Two independently
stated criteria leave room for a third outcome — could-not-run — which is the arity requirement in
practice.

Before running it against anything real, construct the negative control: an artifact that
deliberately violates the rule. Run the eval against it and confirm it flags. If it does not, the
eval is blind and every future clean result from it means nothing. This step costs minutes and is
the difference between a check and a decoration.

Write the adversarial variant. Ask how a system optimizing for this eval could satisfy it without
complying, and compare that path's cost against genuine compliance. If the cheap path is cheaper,
redesign — the eval will otherwise certify it, without anyone intending that.

Estimate the false-positive risk. An eval expected to fire spuriously above the muting threshold is a
liability; tighten it or do not ship it.

Assign a tier by cost and cadence. Continuous evals must be cheap enough to run every cycle, or they
will quietly stop running and nothing will say so.

Re-run the negative control whenever the eval, its dependencies or its environment change. A check
that silently stops matching produces exactly the same output as a check that found nothing.

## 16. Integration

Part XIII supplies the instrument contract that §1 applies wholesale. Part XXIII supplies the rules
each eval verifies and receives §12's six rules in return. Part XXII's detection checks are eval
bodies. Part XXV's gates consume eval results, and §14 bounds when they may. Part XXVI records the
family's benchmark levels rather than a compliance figure, per §7.

Outside the family, the stack's gate-naming convention with explicit pass and fail counters is
endorsed as sound, and negative controls plus a false-positive field are the two additions that would
make its clean results interpretable.

## 17. Open questions

1. Can a negative control be constructed for every rule? Rules about absence — record intent at
   origin, declare the boundary — may have no constructible violating artifact, only a violating
   history, which is far more expensive to stage. — HYPOTHESIS; likely a minority but not empty.
2. Does the adversarial variant need re-derivation as systems change? A satisfaction path that was
   expensive when the eval was written may become cheap later, silently converting a sound eval into
   a certifying one. — UNKNOWN, and it implies adversarial variants need horizons.
3. Is three-valued output achievable for evals whose failure mode is not running at all? An eval that
   is never invoked cannot report that it was not invoked; that detection belongs to the harness, not
   the eval, which pushes the arity requirement one level out. — HYPOTHESIS, and it means the suite
   runner needs the property as much as its members do.

## 18. Institutional writeback

Six rule seeds, five eval seeds and one production gate.

Three portable results. **An eval is an instrument**, so coverage, envelope, arity and a known-answer
case all apply — which turns a large body of Part XIII's work into eval discipline at no extra cost.
**Every eval needs a negative control**, because a check that has never failed is indistinguishable
from one that cannot, and constructing the violating case is usually trivial while the ambiguity it
removes is permanent. And **benchmark the family, do not merely eval it** — a compliance-only
self-assessment would be this family's own founding critique, self-inflicted at the last step.

The demonstration in §9 is the Part's own evidence: rather than claiming this build's gate works, a
deliberately non-compliant artifact was constructed and the gate was observed to flag all three
checks. That result partially discharges an instrument debt recorded three Parts earlier, and it
sharpens what remains — detection capability is now tested; the inability to report could-not-observe
is not, and stands.
