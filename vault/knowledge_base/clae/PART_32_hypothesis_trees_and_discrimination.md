---
title: "CLAE Part 32 — Hypothesis Trees, Discrimination and the Residual Set"
family: clae
part: 32
depends_on: [XIII, XV, XVI, XXI, XXII, XXIII, XXIV, XXV, 29, 30, 31]
feeds: [31]
status: SEALED
date: 2026-08-19
authorization: UPAC STOP #1, Owner option D (2026-08-19)
---

# Part 32 — Hypothesis Trees, Discrimination and the Residual Set

## 1. Purpose

The estate can do two things at the ends of a diagnosis and nothing in the middle.

At the near end, environment qualification decides whether the product is the suspect at all. Its
Attribution Law is explicit — no product repair may begin until the attribution names the product,
and the attribution names the product only when a discriminating experiment has been run. At the far
end, an execution aligner locates the **earliest divergence** between two runs, which is the sharpest
localization instrument the stack owns.

Between them lies the part of debugging that actually consumes the time: the product is the suspect,
the divergence is localized to a region, and there are four or five different mechanisms that would
each produce exactly what was observed. Nothing governs that set.

> Given several explanations that all fit the evidence, which observation should be made next, and
> what is still standing when the repair is applied?

Debugging in practice terminates when a story fits. A fitting story is not a diagnosis, because
**fit is cheap** — the observation that motivated the search is, by construction, compatible with
every hypothesis that could have produced it. What separates a diagnosis from a story is an
observation that at least one rival did *not* predict.

Six mechanisms: the single-hypothesis trap and why it is structural rather than careless (§2), the
admissibility contract for a hypothesis set (§3), the tree over experiments (§4), discrimination
ranking (§5), the three legitimate terminations (§7), and the residual set that survives the repair
(§8). One discipline keeps it honest: a three-valued experiment (§6).

## 2. The single-hypothesis trap

The first plausible mechanism to arrive becomes the plan. This is not carelessness, and treating it
as carelessness is why it recurs. It has three structural causes.

**Confirmation is cheaper than discrimination.** Testing whether the leading hypothesis is true
requires one observation the hypothesis predicts. Testing which of five hypotheses is true requires
observations that *separate* them, which are harder to find and usually more expensive to make.

**The observation that started the search fits everything.** The failure is the evidence, and every
candidate mechanism was proposed precisely because it explains the failure. The starting evidence
therefore has zero discriminating power, and a search that keeps re-examining it is re-reading a
constant.

**A repair that works is read as a diagnosis that was right.** When the leading hypothesis is
repaired and the failure stops, the case closes. But a repair frequently perturbs several mechanisms
at once, and the failure stopping is compatible with the repair having fixed a *different* mechanism
than the one it was aimed at. The success of the repair is weak evidence about the cause, and it is
routinely treated as conclusive.

The third is the most damaging because it is self-sealing: it produces a record of a correct
diagnosis, and the recurrence six months later reads as a new failure.

## 3. The hypothesis set contract

A hypothesis is admissible to the set when it carries three fields.

| Field | Requirement | Rejects |
|---|---|---|
| **Mechanism** | the specific causal path, stated at the granularity at which it could be observed | restatements of the symptom wearing causal grammar |
| **Discriminating prediction** | at least one observation this hypothesis predicts that **some rival does not** | hypotheses that add nothing to the set |
| **Prior with its basis** | how likely, and *why* — precedent, lineage frequency, recent change proximity | confidence with no source, which cannot be updated because it was never derived |

The second field is the one that makes the set a set rather than a list. Two hypotheses that predict
the same observations under every experiment available here are **one hypothesis with two names**,
and the merge rule applies: collapse them, record the merge, and note that the distinction is
unresolvable with the instruments at hand. Carrying both inflates the apparent thoroughness of the
search and guarantees that whichever name is repaired, the record will claim the other was
eliminated.

The third field earns its place at termination rather than at proposal. A residual set of three
hypotheses whose priors are known is a bet with stated odds; a residual set of three with no priors
is an unstated bet, and Part XVI's oracle boundary applies to the difference.

### 3.1 The null hypothesis

One member is always present and is nearly always unauthored: **the observation is wrong.** The
instrument mis-reported, the harness serialized something incorrectly, the log line came from a
different run. This hypothesis has an unusual property — it is often the cheapest to test and it
invalidates the entire search when true, which makes it the highest-expected-value first experiment
far more often than its low prior suggests.

## 4. The tree is over experiments, not over causes

The common drawing is a tree of causes, branching into sub-causes. That drawing has no operational
content, because nothing in it says what to do next. The tree this Part specifies is over
**experiments**:

- a **node** is an experiment — an observation that can actually be made here, with its cost;
- an **edge** is one of that experiment's possible outcomes;
- a **leaf** is the hypothesis set still standing after the outcomes along the path.

The tree is built lazily, one node at a time, because each outcome changes which experiment is worth
running next. Building it fully in advance is wasted work: most branches are never entered, and the
cost of enumerating them is paid in full.

The critical property of the node is that it is an experiment **available here**. A hypothesis
distinguished only by an observation the estate cannot make — a timing measurement it has no
instrument for, a production state it cannot reach — does not produce a node. It produces an entry in
the residual set and, if it matters, a request for an instrument, which is Part XIII's territory.

## 5. Discrimination ranking

Experiments are ordered by three factors, in this precedence.

**How evenly the experiment splits current belief.** An experiment whose outcomes divide the
hypotheses' prior mass near-evenly removes the most uncertainty per run. An experiment whose likely
outcome leaves everything standing removes almost none, however interesting it is.

**Cost.** Wall-clock, risk of perturbing the failure, and the cost of the setup the experiment
needs. An even split that requires reproducing a production state is frequently worse than an uneven
split available immediately.

**Reliability of the experiment itself.** An experiment that may not run, or whose result may be
ambiguous, splits nothing in the cases where it fails. This factor is routinely omitted and it is
the one that produces the worst outcome, because an unreliable experiment does not merely waste a
run — it produces an outcome that gets recorded as a pruning.

### 5.1 Why the leading hypothesis is usually the wrong first test

Testing the most likely hypothesis is the greedy move and it is usually inferior. If the leading
hypothesis holds sixty percent of the belief mass, testing it leaves forty percent unresolved on
failure and confirms on success — but "confirms" here means *fits*, and §2 already established that
fit is compatible with the rivals it never touched. An experiment that splits the set near the
middle resolves more, whichever way it comes out.

The exception is precise and worth stating, because the rule is otherwise easy to over-apply: test
the leading hypothesis first when it is **both** cheap to test **and** decisively falsifiable — the
outcome eliminates it outright rather than merely failing to confirm it. Cheap plus decisive beats a
balanced split; cheap alone does not.

### 5.2 The relationship to Part 31's ranking

Part 31 also ranks by discrimination, and the two rankings are over different objects at different
stages of the same pipeline.

| | Part 32 | Part 31 |
|---|---|---|
| Runs | **before** the repair | after the cause is known |
| Ranks | experiments over competing **causes** | sibling inputs over one known cause |
| Resolves | *which* mechanism is broken | *how much* of the input space it breaks |
| Terminates on | one surviving hypothesis, or a named residual set | budget, or a run of consecutive passes |

The pipeline is: attribution names the product · **Part 32 identifies the mechanism** · the repair is
scoped · Part 31 measures its width · Part 30 §5 measures its spread · Part X §7 or Part XV takes the
routing. Running Part 31 before Part 32 has terminated measures the extent of a hypothesis, which is
a well-formed operation with no meaning.

## 6. The three-valued experiment

Per Part XIII §7, an experiment reports **supported**, **contradicted**, or **could not run** — never
two values. The third is not a nicety here; it is the load-bearing case.

An experiment that could not run prunes nothing. A two-valued harness renders it as one of the other
two, and the direction it collapses toward is *contradicted* — the rival is recorded as eliminated,
the search proceeds with a set that is smaller than the evidence supports, and the eliminated
hypothesis is the one nobody will revisit. This is how a diagnosis becomes confidently wrong rather
than honestly uncertain, and the failure is invisible in the record, because the record shows an
experiment and an outcome.

## 7. Termination

Three legitimate stops, and each licenses a different claim.

| Stop | Condition | Licenses |
|---|---|---|
| **Resolved** | one hypothesis stands, and the repair it predicts works **for the reason it predicted** | a cause claim |
| **Budget** | the declared experiment budget is spent | a repair on the leading hypothesis, labelled as a bet, residual set named |
| **Observationally equivalent** | every remaining rival predicts identically under all available experiments | an instrument request, never a guess |

The first row's qualifier is what separates it from §2's third trap. A repair that works is not
sufficient; the repair must work **in the manner the hypothesis predicted** — the predicted
observation appears, and it appears for the predicted reason. Where the repair works but the
predicted intermediate observation does not appear, the stop is `Budget`, not `Resolved`, and the
distinction is the whole difference between a diagnosis and a coincidence.

The third row is the one most often converted into the second by fatigue. Observational equivalence
is a statement about the instruments, not about the hypotheses, and its correct response is to
acquire an instrument or to route to the human oracle per Part XVI — not to pick the most appealing
rival and record it as the cause.

## 8. The residual set

Whatever survives at termination is recorded with the repair, with each surviving hypothesis's prior
and the experiments that failed to separate them.

A repair applied under a residual set of one is a diagnosis. A repair applied under a residual set of
three is a bet at stated odds. Both are legitimate; only the second is routinely mislabelled as the
first, and the mislabelling has a specific downstream cost: when the failure recurs, a recorded
residual set makes the recurrence immediately interpretable — the bet lost, and the two rivals that
were never separated are now the prime candidates, with their experiments already enumerated. Without
the record, the recurrence starts from nothing and usually re-derives the same leading hypothesis.

This is the same asymmetry Part 31 records for extent, arriving from the other direction: the honest
uncertain state must be **representable**, or the mechanism will always report the confident one.

## 9. Boundary

Environment attribution is not owned here. The environment-qualification discipline decides the axis
— toolchain, dependency, host, fixture, pipeline, hardware, or product — and this Part begins only
once that attribution names the product. Its per-axis discriminating experiments are a sibling
mechanism, not this one: they separate *axes*, while this separates *mechanisms within the product*.
An estate that runs hypothesis trees over an unattributed failure will generate mechanisms that
explain an environmental fault, and every one of them will be wrong in the same direction.

Earliest-divergence alignment is not owned here either; it is an **instrument that populates a node**.
Aligning two executions and reporting where they first differ is frequently the highest-discrimination
experiment available, and this Part's contribution is deciding when it is worth its cost relative to
the alternatives, not performing it.

Ranking candidates by expected information gain appears elsewhere in the estate under two different
subjects — probe selection at ensemble reliability scale, and source-frontier ordering during
discovery. Neither is this. Both rank *what to look at next in a search over a corpus*; this ranks
*which observation separates competing causal claims about one defect*. The shared idea is the same
statistical intuition arriving at three unrelated problems, which is a reason to name the neighbours
explicitly rather than to assume ownership.

Finding disposition within a session (Part 29), cause elevation and the artifact-space campaign (Part
30), and input-space extent (Part 31) are all downstream and separately owned.

## 10. Evidence — discrimination in this stack

**The null hypothesis winning.** A probe reported that a gate produced no output while the gate's own
entry point was firing. Two rivals: the gate was defective, or the probe was mis-reading it. The
probe was rewritten so the gate wrote its own payload rather than having the shell serialize it, and
the output appeared — the observation had been wrong, not the product. The experiment was cheap and
decisive, which is exactly the §5.1 exception, and had it been deferred behind the "real" hypotheses
the search would have proceeded to repair a gate that worked.

**A split that eliminated a whole subtree.** Four of nine gates on a graph module failed against
synthetic roots while the real repository passed. Three rivals stood: the gates were wrong, the module
was wrong, or the root parameter was not honoured. The single observation — real root passes,
synthetic root fails — eliminated "the module is wrong" outright, because a wholly broken module fails
everywhere, and it eliminated "the gates are wrong" for the same reason in reverse. What remained was
a parameter that was silently inert, which is what it was. One observation, two hypotheses removed.

**A confirmation that was not a diagnosis.** A duplication gate stayed silent on a proposal. The
leading hypothesis was that the gate did not recognize the proposal as a creation attempt; the
recognizer was instrumented and returned true, which contradicted the leading hypothesis and forced
the search downstream, where the real mechanism was a three-outcome condition collapsed into two.
Had the recognizer been *fixed* rather than *observed* — a plausible move, since it also had a
length cap defect — the gate would have stayed silent and the record would have shown a repair.

## 11. Failure modes

| # | Failure | Why it survives |
|---|---|---|
| 1 | **Single hypothesis** | it fits, and fit is what the evidence was selected to provide |
| 2 | **Confirmation as diagnosis** | the repair works; the record shows a solved case |
| 3 | **Null hypothesis unauthored** | doubting the instrument feels like avoiding the work |
| 4 | **Duplicate hypotheses under two names** | the set looks thorough; whichever is repaired, the other is claimed eliminated |
| 5 | **Greedy testing** | testing the most likely thing first is intuitive and locally reasonable |
| 6 | **Two-valued experiment** | an unrunnable experiment collapses to *contradicted*, pruning a live rival |
| 7 | **Observational equivalence resolved by preference** | a cause is recorded; nothing in the record shows the rivals were indistinguishable |
| 8 | **Residual set discarded** | the repair is applied and the uncertainty is not carried, so recurrence starts from zero |
| 9 | **Tree over causes** | it looks like analysis and never says what to observe next |
| 10 | **Hypotheses over an unattributed failure** | every mechanism proposed explains the symptom, and all of them are about the wrong axis |

## 12. Detection signatures

- A diagnosis record with one hypothesis.
- A hypothesis whose mechanism restates the symptom — the fault is that the value is wrong.
- A hypothesis with no prediction that any rival lacks.
- A diagnosis that never tested the instrument.
- A repair whose predicted intermediate observation was never checked, recorded as `Resolved`.
- An experiment log with only two outcome values.
- A closed diagnosis with no residual set field, or a residual set with no priors.
- Two hypotheses in a set with identical prediction columns.
- Extent measurement (Part 31) begun while the hypothesis set still has more than one member.

## 13. Trap seeds — for Part XXII

- **The repair that worked for another reason.** A perturbing repair frequently touches several
  mechanisms; the failure stopping is compatible with a different one having been fixed.
- **The eliminated rival that was never tested.** A two-valued harness converts *could not run* into
  *contradicted*, and the rival removed this way is the one nobody revisits.
- **The thorough-looking set.** Two names for one mechanism doubles the apparent breadth of the
  search and guarantees a false elimination claim.
- **Equivalence resolved by appeal.** When no available experiment separates the rivals, the most
  articulate hypothesis wins, and the record shows a cause.
- **Diagnosing before attributing.** Mechanisms proposed for a failure whose axis is environmental
  are all internally coherent and all wrong.

## 14. Rule seeds — for Part XXIII

- **A hypothesis set of one is not a set.** Record why the rivals were not enumerated.
- **Every hypothesis carries a prediction some rival does not.** Hypotheses that fail this are merged
  and the merge is recorded.
- **The instrument is a hypothesis.** The observation-is-wrong case is enumerated before the search
  proceeds.
- **Experiments are three-valued.** *Could not run* prunes nothing.
- **`Resolved` requires the predicted intermediate observation, not merely a working repair.**
- **Termination records the residual set with priors**, and a residual set larger than one labels the
  repair a bet.
- **Observational equivalence licenses an instrument request, never a selection.**
- **Extent measurement does not begin while the hypothesis set has more than one member.**

## 15. Eval seeds — for Part XXIV

- Sample closed diagnoses and count the hypotheses each recorded. The proportion at one is the
  single-hypothesis rate and is the number that justifies this Part.
- For each `Resolved` diagnosis, check whether the predicted intermediate observation was recorded.
  The gap is the confirmation-as-diagnosis rate.
- Compare recurrences against residual sets. A recurrence whose cause was in the residual set is a
  bet that lost and is cheap; one whose cause was in neither the resolved hypothesis nor the residual
  set means the set itself was too narrow, which is a different defect and needs different treatment.
- Replay a diagnosis with the experiment ordering reversed and count the experiments needed. If
  ranked ordering does not reduce the count, the ranking is not earning its overhead.
- Run an experiment with its preconditions deliberately absent and confirm it reports *could not run*.

## 16. Production Reality Gate seed — for Part XXV

A diagnosis may not be closed while its hypothesis field holds fewer than two entries **or** its
residual set field is blank. Both accept explicit honest values — `only one mechanism was
conceivable, and here is why`, and `residual set empty, resolved` — and both reject silence. The gate
does not demand a large search; it demands that the size of the search be stated, because a
diagnosis whose breadth is unrecorded is indistinguishable from one that had none.

## 17. Pseudoflow — from a localized failure to a closed diagnosis

Confirm the attribution names the product; if it does not, stop and hand back to the environment
axis. Enumerate the hypothesis set, including the instrument-is-wrong case, each with a mechanism, a
discriminating prediction and a prior with its basis; merge any pair whose predictions coincide under
every available experiment and record the merge. Declare the experiment budget. Choose the next
experiment by even split, then cost, then reliability — taking the leading hypothesis first only when
it is both cheap and decisively falsifiable. Run it three-valued; prune only on *contradicted*.
Repeat until one hypothesis stands, the budget is spent, or the survivors are observationally
equivalent here. On the first, verify the predicted intermediate observation before claiming
`Resolved`; on the second, repair the leading hypothesis and label the repair a bet; on the third,
request the instrument or route to the oracle. Record the residual set with priors in every case, and
only then hand to Part 31 for the extent.

## 18. Integration

Upstream: the environment attribution that names the product; Part XXI's lineage, which supplies
priors from what this stack has actually failed at; Part 29's disposition, which decides the finding
is being diagnosed at all; the recorded incident corpus, which is where a prior's basis comes from
when it is not a guess. Downstream: Part 31's extent measurement, which begins only after
termination; Part 30's cause-to-protection compiler, which needs the mechanism this Part identifies
and degrades to installing a protection against a symptom without it; Part XIII, which receives the
instrument requests observational equivalence generates; Part XVI, which receives what no instrument
can settle.

## 19. Open questions

- **Priors have no calibration loop here.** A prior's basis is required; whether the basis was any
  good is never scored. The obvious loop — compare stated priors against which hypothesis won — is
  specified nowhere and would require diagnoses to be recorded at a fidelity the estate does not
  currently reach.
- **Even-split ranking assumes the priors are meaningful.** Where every prior is a guess, "splits the
  belief mass evenly" degrades to "splits the count evenly", which is a weaker and unstated rule.
- **The merge rule is relative to available experiments.** Two hypotheses merged here may be
  separable elsewhere, and nothing carries the merge forward as a fact about the instruments rather
  than about the causes.
- **Budget termination has no floor.** A budget of one experiment satisfies every rule in this Part
  and produces a residual set of five, honestly labelled and useless. What minimum makes a diagnosis
  worth recording is unset.

## 20. Institutional writeback

Five trap seeds, eight rule seeds, five eval seeds, one production gate.

Three portable results. **Fit is not evidence** — the observation that started the search was, by
construction, predicted by every hypothesis in the set, and a search that keeps returning to it is
re-reading a constant. **A working repair is weak evidence about the cause**, because repairs perturb
more than they target, and the strongest available upgrade is cheap: check that the *predicted
intermediate observation* appeared, not merely that the symptom stopped. And **the instrument belongs
in the hypothesis set**, where its low prior is outweighed by two properties nothing else has — it is
usually the cheapest test available, and it invalidates the entire search when true.

The structural finding is the residual set. Every mechanism in this Part can be run scrupulously and
still produce a repair applied under genuine uncertainty; that is not a failure, it is the normal
case. What makes it a defect is discarding the uncertainty at closure, because the recurrence then
arrives with no memory of which rivals were never separated and re-derives the same leading
hypothesis for the same reason it was leading the first time. **An uncertainty that is representable
is carried; one that is not is reliably reported as certainty**, and this is the second arrival at
that conclusion in three Parts — Part 31 reached it for extent, from the other end of the same
pipeline.
