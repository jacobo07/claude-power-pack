---
title: "CLAE Part XVIII — Deviation Governance"
family: clae
part: XVIII
depends_on: [IX]
feeds: [XIX, XX, XXI, XXV]
status: SEALED
date: 2026-07-26
---

# Part XVIII — Deviation Governance

## 1. Purpose

Part X §5 established that a floor without a declared escape route will be defeated rather than
obeyed. This Part is that route, and it is more than a safety valve: it is the general mechanism for
the ordinary situation in which the intended approach could not be taken and something else was
done.

That situation is universal and is almost never recorded. The work proceeds, the substitution is
made, and nothing states what was given up. Over time the artifact diverges from every plan that
described it, in a direction nobody chose and no document reflects.

The Part states the four-part contract a deviation must satisfy, argues the counterintuitive claim
that a zero deviation rate is evidence of a broken record rather than a disciplined team,
establishes that intent preservation **does not compose**, and gives the test that separates a real
deviation from a better idea that should have replaced the plan.

## 2. The four-part contract

> A deviation is a recorded substitution of the intended approach, justified by a **proven
> constraint**, **preserving the original intent**, with the resulting **loss measured**.

Four parts. Missing any one, it is not a deviation:

- Missing the **proven constraint** — a preference, dressed as necessity.
- Missing the **stated intent** — a change of direction, with nothing to check the substitution
  against.
- Missing the **substitution description** — a gap, not a deviation.
- Missing the **measured loss** — an assertion that nothing was given up, per §6.

Part III §7 fixed the vocabulary against its neighbours. A *compromise* has no record. A *shortcut*
has no constraint. A *deferral* substitutes nothing — the work is simply not done. Each of these is
a legitimate thing to do and none of them is a deviation, and calling them one imports a rigour that
was not applied.

## 3. Why a zero deviation rate is a bad sign

A system without a deviation mechanism does not experience fewer deviations. It experiences
**invisible** ones — Part X §5's defeated-not-obeyed failure, generalized beyond floors to every
plan.

This inverts the natural reading of the metric:

> **A deviation rate of zero means either that nothing is being attempted which could fail, or that
> deviations are not being recorded. Neither is discipline.**

Real work under real constraints produces deviations. An engineering effort that encounters no
constraint requiring substitution is either operating far inside its capability — in which case the
absence of deviations is a statement about ambition rather than about rigour — or it is substituting
without recording, which is the state this Part exists to end.

The consequence for reading a deviation ledger is that a *populated* ledger is the healthy
observation and an empty one warrants investigation. This is the opposite of how such records are
usually read, and the misreading is self-reinforcing: a team that believes deviations are failures
will stop recording them, which produces the empty ledger that confirms the belief.

## 4. Proving the constraint

*We could not* is a claim. A deviation requires a proof, and the standard has three elements: **what
was attempted**, **what was observed**, and **why the observation implies a constraint rather than a
defect in the attempt**.

The third element is the one that does the work, and it is what separates a constraint from a
failed attempt. A single failure is evidence of a defect — in the approach, the environment, the
understanding. It becomes evidence of a constraint only when the failure is shown to be a property
of the situation rather than of the attempt.

This stack's existing two-consecutive-failures law supplies the minimum evidentiary bar: the second
failure of the same shape is what converts a defect hypothesis into a constraint candidate. One
failure is not a constraint. Below that bar, the honest record is a failed attempt, and continuing
without the intended approach is a deferral rather than a deviation.

**Constraints have scope and go stale.** A constraint proven in one environment, at one version,
under one configuration, is proven there. Recording the scope alongside the proof is what makes §7's
retirement possible; without it, a constraint proven once is treated as permanent, and the
substitution outlives the reason for it by years.

## 5. Intent preservation does not compose

The requirement is that the substitution serves the *same* purpose, not a nearby one. Locally this
is usually satisfiable and usually satisfied.

The failure is structural rather than local:

> **Intent preservation is not transitive.** If substitution A preserves the intent of plan B, and
> B preserved the intent of original C, it does not follow that A preserves C.

Each step is a small, justified adjustment. Across a series of them the artifact serves a purpose
that nobody chose and that no single deviation record would reveal, because each record is locally
correct. This is how a system arrives, through entirely defensible decisions, somewhere nobody
intended.

Two controls follow.

**Intent is stated at the original decision, not reconstructed at deviation time.** Part V §3's
perishability applies exactly: an intent reconstructed under the pressure of a constraint will be
reconstructed as something the available substitution happens to satisfy. The reconstruction is
performed by the party whose substitution is in question.

**Each deviation is checked against the original intent, not the immediately preceding plan.** This
is the only defence against composition drift, and it requires the original to still be legible —
which is why the first control is a precondition for the second rather than a separate nicety.

## 6. Measuring the loss, and the zero-loss test

A deviation is a **trade**. Something was given up, or nothing was.

> **If the substitution claims zero loss, one of two things is true: it is strictly better than the
> plan, in which case the plan was wrong and should be revised rather than deviated from; or the
> loss was not measured.**

There is no third case, and applying this test converts a large class of unexamined deviations into
either plan improvements or honest measurements. It also resolves the common situation where a
deviation feels like an obvious improvement: adopt it, update the intent, and record that the
original approach was superseded. That is a better outcome than a permanent deviation record, and it
keeps the plan legible for §5's composition check.

The loss is a residual in Part IX's exact sense, entered in the ledger with the deviation as its
origin. It carries a dimension like any other residual, and the dimensions that recur are:

- **Capability** — something the intended approach would have done is not done.
- **Quality distance** — a larger residual against the reference on some dimension.
- **Reversibility** — the substitution is harder to undo than the plan would have been.
- **Coupling** — the substitution introduces a dependency the plan avoided.
- **Comprehensibility** — the artifact is harder for a later reader to understand.

The last two are the ones most often unrecorded and most often the real cost, because neither shows
up in any functional check.

## 7. The ledger, its trends, and standing deviations

**Deviation density is a design signal, not a discipline signal.** Where deviations cluster in one
area, the intended approach systematically does not fit there. The correct response is to examine
the plan for that area, not the people working in it.

This inverts the usual reading a second time. A high deviation rate in one region means **the plan
is wrong there**, and treating it as a discipline problem produces exactly the suppression that
makes §3's empty ledger.

**Standing deviations are the accumulation failure.** A constraint lifts — a version is upgraded, a
tool becomes available, a dependency is replaced — and nobody returns to the substitution that the
constraint justified. The deviation becomes permanent by default, and its recorded loss continues to
be paid for a reason that no longer exists.

The control is the scope recorded in §4. A deviation whose constraint scope has lapsed is
re-examined: the constraint may still hold and be re-proven, or it has lifted and the substitution
should be unwound. What must not happen is the lapse passing unobserved, which is Part V §6's
horizon failure arriving in the deviation ledger.

## 8. Deviation is one of four responses

When the intended approach cannot be taken, deviation is not the only option and is often not the
best one.

| Response | When correct | Cost |
|---|---|---|
| **Deviate** | The intent is right, the constraint is real, a substitution serves the same purpose | A measured, recorded loss |
| **Block** | The intent is right and no substitution serves it | Progress stops; the constraint becomes visible to whoever can lift it |
| **Reduce scope** | Part of the intent can be served fully | Declared incompleteness, which is honest |
| **Change the intent** | The intent repeatedly cannot be met under proven constraints | The plan is revised |

The fourth is the one rarely considered, because revising an intent feels like conceding. But an
intent that cannot be met under repeatedly-proven constraints is **a wrong intent**, and continuing
to deviate around it accumulates losses in service of a goal the situation has already refused. The
signal that the fourth response is correct is §7's density: repeated deviations in one area, all
preserving the same intent, all incurring loss.

Blocking is also undervalued. A constraint that stops progress becomes visible to whoever has the
authority to lift it, whereas a deviation absorbs it silently and no one learns the constraint
exists.

## 9. Boundary

Deviation is not available against **prohibitions** or **invariants**. These admit no partial
satisfaction, and a route around them is not a deviation but a violation, per Part X §8.

Against **safety floors**, the constraint proof must be at least as strong as the consequence the
floor prevents. A floor placed at Part XI's irreversibility threshold cannot be deviated from on a
convenience constraint.

And one that is easy to miss: **a deviation cannot be used to escape an oracle question.** Where a
judgment belongs outside the system per Part XVI, substituting a self-made determination and
recording it as a deviation is self-certification with paperwork. The four-part contract cannot be
satisfied in that case — the constraint being claimed is the unavailability of the oracle, and the
correct responses are to block, reduce scope, or route the question properly.

## 10. Evidence — deviation surfaces in this stack

| Surface | Escape route | Loss recorded? |
|---|---|---|
| Hard rules with an exception clause and a literal authorizing phrase | **Yes** — a well-formed, explicitly declared route, scoped to one turn | **No** |
| Known false positives register | Yes — records that the intended check does not apply and what to do instead | **No** |
| This session: the anti-thrash block on a third write | Applied a documented alternative path | No — none needed; the register named an equivalent route |
| This session: the exhausted trim tool | Reported rather than hand-editing global config | Partially — the blocked done-gate was named |
| This session: the unfilled generated spec skeleton | Reported as a bounded detour, work continued | No |

**The finding: this stack has escape routes without loss accounting.**

The routes themselves are unusually good. Hard rules carry explicit exception clauses with a literal
authorizing phrase and a one-turn scope — that is precisely the declared escape Part X §5 requires,
and most governance systems do not have it. The false-positive register is a second, softer instance
of the same idea.

What none of them records is the **trade**. An exception clause authorizes a bypass and says nothing
about what was given up by taking it. So the deviation happens, correctly and with permission, and
the ledger that would show the accumulated cost of those bypasses does not exist. Under §6's test,
every one of them is currently in the second case: the loss was not measured.

The consequence is that §7's two trend readings are unavailable here. Nobody can see where deviations
cluster, so the design signal is lost; and nobody can see which constraints have lapsed, so standing
deviations persist indefinitely. — Escape-route mechanics OBSERVED from the governance archive and
this session's own record; the loss-accounting assessment INFERRED against §6.

## 11. Failure modes

| Failure | Mechanism |
|---|---|
| **Unproven constraint** | A preference recorded as a necessity; one failure treated as a property of the situation |
| **Reconstructed intent** | Intent written at deviation time, shaped to fit the substitution already chosen |
| **Composition drift** | Each deviation preserves the previous plan's intent; none preserves the original |
| **Unmeasured zero loss** | A trade recorded as free, which is either an unrevised plan or an unmeasured cost |
| **Suppressed ledger** | Deviations read as discipline failures, so they stop being recorded and the ledger empties |
| **Standing deviation** | The constraint lifted; nobody returned; the loss is still being paid |
| **Density read as indiscipline** | Clustered deviations treated as a people problem rather than as evidence the plan is wrong there |
| **Deviation around an oracle** | A judgment the system has no standing to make, self-answered and recorded as a constraint-bounded substitution |
| **Absorbed constraint** | A constraint deviated around silently that blocking would have made visible to whoever could lift it |

## 12. Detection signatures

1. **The empty ledger.** No recorded deviations over a period of substantive work. §3's signature,
   and the most common state.
2. **The single-failure constraint.** Constraint proofs citing one attempt. Below the evidentiary
   bar; these are failed attempts.
3. **The costless deviation.** Loss recorded as none. Either a plan that should have been revised or
   a measurement that was not taken.
4. **The lapsed scope.** Deviations whose constraint scope names an environment or version that no
   longer exists.
5. **The drifted artifact.** A system whose current behaviour cannot be derived from its original
   intent through the recorded deviations. Composition drift, visible only when the whole chain is
   read at once.
6. **The cluster.** Deviations concentrated in one area, all preserving the same intent, all
   incurring loss — §8's signal that the intent itself is wrong.

## 13. Trap seeds — for Part XXII

- **T-CLAE-PREFERENCE-AS-CONSTRAINT** — a substitution justified by a single failed attempt recorded
  as a proven constraint.
- **T-CLAE-RECONSTRUCTED-INTENT** — intent written at deviation time by the party whose substitution
  is in question, shaped to be satisfied by it.
- **T-CLAE-COMPOSITION-DRIFT** — a chain of locally-correct deviations producing an artifact that
  serves a purpose nobody chose, invisible in every individual record.
- **T-CLAE-COSTLESS-DEVIATION** — a trade recorded as free, concealing either an unrevised plan or
  an unmeasured loss.
- **T-CLAE-STANDING-DEVIATION** — a constraint that lifted silently, with the substitution and its
  loss persisting for a reason that no longer exists.
- **T-CLAE-DEVIATION-AROUND-ORACLE** — a judgment belonging outside the system, self-answered and
  recorded as a constraint-bounded substitution.

## 14. Rule seeds — for Part XXIII

- **PR-CLAE-FOUR-PART-DEVIATION** — a deviation records the proven constraint, the original intent,
  the substitution and the measured loss. Missing any part, it is recorded as a compromise, shortcut
  or deferral by its correct name.
- **PR-CLAE-PROVE-BEFORE-DEVIATING** — a constraint proof states what was attempted, what was
  observed, and why the observation implies a property of the situation. A single failure is a
  defect, not a constraint.
- **PR-CLAE-INTENT-AT-ORIGIN** — intent is recorded when the approach is chosen. Deviations are
  checked against the original intent, never against the immediately preceding plan.
- **PR-CLAE-ZERO-LOSS-REVISES-THE-PLAN** — a substitution with no loss is adopted as an improvement
  and the plan updated, or its loss is measured. It is not recorded as a costless deviation.
- **PR-CLAE-SCOPE-THE-CONSTRAINT** — every constraint records the environment, version and
  configuration it was proven under, and is re-examined when that scope lapses.
- **PR-CLAE-DENSITY-EXAMINES-THE-PLAN** — clustered deviations trigger review of the plan for that
  area, not of the people working in it.
- **PR-CLAE-NO-DEVIATION-AROUND-JUDGMENT** — where the blocker is an unavailable oracle, the
  responses are block, reduce scope, or route properly. Substituting a self-made determination is
  self-certification.

## 15. Eval seeds — for Part XXIV

- **Ledger-population probe.** Count deviations over a period of substantive work. Zero or near-zero
  warrants investigation of the recording, not congratulation.
- **Constraint-evidence probe.** For each recorded constraint, count the attempts cited. Single-
  attempt constraints are below the bar and their deviations are deferrals.
- **Zero-loss census.** Count deviations recording no loss. Each is a plan-revision candidate or an
  unmeasured cost, and both are actionable.
- **Chain-integrity probe.** For a sample of areas, read the full deviation chain and ask whether the
  current behaviour is derivable from the original intent. Composition drift is invisible in any
  single record and obvious across the chain.
- **Scope-lapse probe.** List deviations whose constraint scope names an environment or version no
  longer in use. Each is a standing deviation still charging its loss.
- **Density probe.** Plot deviations by area. Clusters locate wrong plans.

## 16. Production Reality Gate seed — for Part XXV

**Deviation Integrity Gate.** Work performed below a floor, or diverging from a recorded plan, may
be admitted only when a deviation record exists carrying a constraint proof citing at least two
attempts of the same shape, the intent as stated at the original decision, the substitution, the
measured loss entered as a ledger residual, and the constraint's scope. Deviations recording zero
loss are returned as plan-revision candidates. Deviations whose claimed constraint is the
unavailability of an oracle are refused, since that is a routing failure and not a constraint.

## 17. Pseudoflow — recording a deviation

When the intended approach fails, do not substitute yet. Establish first whether this is a defect in
the attempt or a property of the situation. A single failure is a defect; attempt again, differently,
and only a second failure of the same shape supports a constraint.

Write the constraint proof: what was attempted, what was observed, and why the observation implies
the situation rather than the attempt. Record the scope — the environment, version and configuration
this was proven under.

Retrieve the intent as stated when the approach was originally chosen. Do not restate it now. If the
original intent was never recorded, that is the finding: record the deviation as an unverifiable
substitution, because there is nothing to check it against.

Consider all four responses before choosing deviation. Blocking makes the constraint visible to
whoever can lift it. Reducing scope is honest incompleteness. Changing the intent is correct when
this area has already produced deviations preserving the same intent — the situation has refused the
goal, and more substitutions will accumulate more loss in its service.

If deviating, describe the substitution and check it against the **original** intent rather than the
most recent plan. This is the only defence against composition drift.

Measure the loss along its dimension and enter it in the ledger with the deviation as its origin. If
the loss appears to be zero, apply the test: either this is better than the plan, in which case
revise the plan and record the supersession, or the loss is real and has not been found. Look
specifically at reversibility, coupling and comprehensibility, which no functional check will
surface.

When the constraint's scope lapses, re-examine. Re-prove the constraint or unwind the substitution.
A deviation that outlives its constraint is paying for nothing.

## 18. Integration

Part X §5 requires this route to exist; without it, floors are defeated silently. Part XI's
derivation is what makes a deviation against a floor arguable — a floor with an unrecorded
derivation cannot support a statement of what the deviation cost. Part IX receives measured losses
as ledger residuals with deviation origins, which is what makes §7's trends computable. Part XVI's
boundary is what §9 protects: a deviation cannot substitute for a judgment the system lacks standing
to make. Part XIX's evidence-gated autonomy consumes the deviation record as evidence, and an
autonomous agent's deviations are the primary artifact by which its judgment is later assessed.

Outside the family, the hard-rule exception clauses are endorsed as a well-formed declared escape and
identified as the natural host for a loss field. The false-positive register is the softer instance
of the same pattern.

## 19. Open questions

1. Can composition drift be detected without reading the whole chain? §5 establishes the failure and
   §12 detects it by reading every deviation in an area at once, which does not scale. A
   chain-summary that preserves the intent relationship is not obviously constructible. — UNKNOWN.
2. Is two attempts the right evidentiary bar for a constraint? It is inherited from this stack's
   existing law, which was derived for tool-failure loops rather than for constraint proof, and the
   transfer is argued rather than demonstrated. — HYPOTHESIS.
3. How is comprehensibility loss measured? §6 names it as one of the two most frequently real and
   unrecorded costs, and it is the dimension least amenable to any instrument in Part XIII's
   taxonomy — most likely an oracle question, which makes it expensive exactly where it is common. —
   UNKNOWN.

## 20. Institutional writeback

Six trap seeds, seven process-rule seeds, six eval seeds and one production gate.

Three portable results. **A zero deviation rate is evidence of a broken record, not of discipline** —
real work under real constraints produces deviations, and a team that reads them as failures will
stop recording them, producing the empty ledger that appears to confirm the reading. **Intent
preservation does not compose** — each substitution can honestly preserve the intent of the plan it
replaced while the chain arrives somewhere nobody chose, which is why every deviation must be checked
against the original intent rather than the preceding one. And **the zero-loss test**: a deviation
claiming no cost is either a better idea that should have replaced the plan, or a cost that was not
measured, with no third case.

The finding that generalizes furthest: a governance system can have genuinely well-formed escape
routes — explicit, scoped, authorized — and still have no idea what those escapes have cost it,
because the route was designed as a permission and never as a trade.
