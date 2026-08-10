---
title: "CLAE Part 28 — Freeze and Adversarial Multipass"
family: clae
part: 28
depends_on: [VI, XIII, XV, XIX, XXII, XXV, 27]
feeds: [29, 30]
status: SEALED
date: 2026-08-10
---

# Part 28 — Freeze and Adversarial Multipass

## 1. Purpose

Part 27 gave the prosecutor standing. This Part gives it a procedure: what must be true of the
artifact before a challenge can mean anything (§2), what the challenge is handed (§4), the nine
distinct passes it runs and why they cannot be collapsed into one (§6), how a subset is selected
when running all nine is disproportionate (§8), and the obligation that positive testing
structurally cannot discharge (§7).

One result dominates the Part and it is the reason negative proof gets its own pass:

> **"I did not see it" does not demonstrate absence.**

An absence is a positive claim and requires positive evidence. Every other pass here can be
approximated by a careful executor; this one cannot, because the executor's tests are written
against what the work is *for*, and unreachability is a property of what the work is *not*.

## 2. The freeze

When the executor believes it is finished it declares `REQUEST_CLOSURE` — the only terminal-
adjacent statement its vocabulary contains, per Part 27 §3. At that moment:

- the diff is frozen;
- the current state is captured;
- hashes are stored;
- the inventory is captured;
- tests are recorded;
- observed runtime is collected;
- **further modification is prohibited until the first review completes.**

The last line is the mechanism and the rest are its inputs. Without it:

> **The agent alters the system while trying to demonstrate the system is correct.**

That is not dishonesty; it is the natural motion of a party that finds a problem while looking
for problems. The consequence is specific and severe: the evidence describes a state that no
longer exists, so the prosecutor and the executor are arguing about different artifacts and
neither can tell. Part VI §7's paired-observation requirement is the general form — a comparison
between two observations taken at different times measures the interval as well as the
difference.

The freeze is therefore what makes the challenge a *measurement* rather than a conversation. It
is also the cheapest control in the extension: it costs one state transition and it is the
precondition for every pass below. — Mechanism INFERRED from Part VI; the state's placement
before `READY_FOR_CHALLENGE` is fixed by Part 27 §6.

### 2.1 Freeze is not a code freeze

The prohibition is on modifying **the artifact under challenge**, for the duration of the first
review only. Repairs are expected and are handled by returning to `REPAIR_REQUIRED` and
re-freezing, per Part 29's loop. A freeze that never lifts is a stalled mission, and a freeze
that lifts silently mid-review has produced an uninterpretable result — the two failure modes
sit on either side of the same control.

## 3. The closure pack

Fifteen items. The executor assembles them; the prosecutor does not rely on them, for the reason
in §4.

| | Item | | Item |
|---|---|---|---|
| 1 | initial objective | 9 | positive tests |
| 2 | initial state | 10 | negative tests |
| 3 | changes made | 11 | runtime proof |
| 4 | items withdrawn | 12 | rollback |
| 5 | items quarantined | 13 | outstanding risks |
| 6 | items migrated | 14 | unknowns |
| 7 | manifests modified | 15 | decisions requiring an owner |
| 8 | claims and their evidence | | |

Items 4, 5 and 6 are the ones a conventional completion report omits, and they are precisely
what Pass C and Pass D need. A pack that lists what was *added* and not what was *withdrawn*
cannot support an unreachability claim, because the set to prove unreachable was never written
down.

Item 8's pairing — **claims and their evidence**, not claims — is what lets a pass check a claim
rather than read it. An unpaired claim is inadmissible in the same sense as an unanchored
objection.

## 4. What the prosecutor is handed, and why anchoring is the point

The prosecutor does **not** receive the executor's optimistic summary first. It receives:

mission · initial state · diff · inventories · manifests · logs · results · applicable policies.

The source states the reason in four words — *"this reduces the anchoring"* — and the mechanism
is worth making explicit, because it is the difference between a control and a formality.

An anchored reviewer does not merely agree too readily. It **searches the space the summary
describes**. The summary is a map of what the executor believed it did, so a reviewer anchored to
it can only find errors *within* that map, and the entire class of omission — work that should
have happened and never entered anyone's model — is outside the search space of both parties.
This is Part XIII §9's intersection result appearing as a procedure: two searchers sharing an
anchor have the coverage of one.

> **The summary is the thing under challenge. It is not the input to the challenge.**

The summary is not withheld permanently — it is read *after* the passes, as one more claim to
check. Order is the whole control. — Mechanism INFERRED; the anchoring reduction is asserted by
the source without measurement, and §14 records that as an open question.

## 5. Passes are not review depth

A single reviewer looking harder does not produce these nine results. Each pass has a different
**question shape**, and a question shape determines what can be found regardless of effort:

- Pass B asks *does the required thing work?* — answerable by exercising the system.
- Pass C asks *is the withdrawn thing unreachable?* — **not** answerable by exercising the
  system, because exercising it demonstrates what happens, not what cannot.
- Pass D asks *what exists that nothing refers to?* — answerable only by enumerating from the
  artifact side rather than the intent side.
- Pass E asks *what is claimed by two owners?* — answerable only by comparing owners to each
  other, which no single-artifact inspection reaches.

Merging passes does not save work; it silently drops the questions the merged form cannot
express. That is the accumulation failure of Part XXV §4 in the opposite direction — there,
nineteen gates collapsed to four *trigger points* while every check survived; here, collapsing
the checks themselves destroys them.

## 6. The nine passes

Generalized to this family's domain. The estate instance that produced each is cited as
evidence, not as the definition.

### Pass A — Contract compliance

*Was exactly the stated objective resolved?* Was anything outside scope modified? Did any part
remain implicit? Are the acceptance conditions satisfied? Were the mode's rules respected?

Catches scope drift in both directions — under-delivery against the contract and the more
common over-delivery that Part XIX §7 identifies as the real autonomy boundary.

### Pass B — Positive reality

*Does the required thing exist and function?* Components present, configuration loaded,
dependencies satisfied, entry points responding, the system starting, principal routes reachable.

This is the pass an executor's own tests approximate best, and therefore the one with the least
marginal value from an independent party. Its role here is to establish the baseline the other
passes are differenced against.

### Pass C — Negative reality

*Is what was prohibited or withdrawn now unreachable?* Not loaded · commands and aliases absent ·
no surface exposes it · permissions do not reactivate it · no data or scheduled task still
executes it · no fallback path returns to the superseded system.

**The source marks this pass fundamental and gives the reason in one sentence: not having seen it
does not demonstrate its absence.** §7 develops the obligation.

### Pass D — Orphan detection

*What exists that nothing refers to, and what refers to something that does not exist?* Both
directions: an artifact with no consumer, and a consumer with no artifact. Configuration without
a reader, a reader without configuration, a directory with no owning component, data with no
owner, a dependency nothing consumes, listeners with no source, residual scheduled tasks, and
files renamed to a disabled or backup suffix rather than removed.

The two-directional form is what makes this a pass rather than a cleanup: a dangling *reference*
and a dangling *artifact* have different causes and different repairs, and a single-direction
sweep finds one class and reports the estate clean.

### Pass E — Capability collision

*Who owns each capability?* For each, is there exactly one owner? Are there duplicate commands?
Do two listeners modify the same action? Is there a second source of truth?

This is the only pass whose unit of analysis is a *relation between components* rather than a
component. Nothing found by inspecting artifacts one at a time will surface it, which is why it
survives reviews that are otherwise thorough. Part XXVI's integration map is the artifact this
pass consumes.

### Pass F — Semantic and constitutional review

*Does a mechanism functionally equivalent to a prohibited one exist under another name?* The pass
searches by **property, not by name**: stake · chance · loss · value transfer · purchased
opportunity · probabilistic rewards carrying value.

Pass F is the answer to the rename. Every name-keyed control is defeated by an author who did not
know the name was controlled, and by one who did. A property-keyed search is the only form that
survives vocabulary change, and it is the same reasoning Part XXII §2 used to key the trap
registry by symptom rather than by name.

### Pass G — Cross-instance purity

*Do artifacts appear where they should not, or identical configurations exist where an overlay
should?* Compare each instance against its siblings and against historical ones.

Both halves matter and the second is counter-intuitive: **identical configuration across
instances that should differ is a finding**, not a sign of health. It means an overlay that was
supposed to specialise the instance was never applied, and the uniformity is concealing it.

### Pass H — Temporal and lifecycle review

*What was valid before and stopped being valid?* Which component was superseded? What remains
disabled rather than removed? What belongs to a withdrawn mode? Which historical decision
invalidates the current state? **Which exception has expired?**

This pass reads the estate against time, and it is the only one that can find a state which was
correct when created and became wrong without anything changing. Part V's horizon machinery is
its instrument; the expired exception is its highest-yield single question.

### Pass I — Production reality

*What does the running system report, rather than what does the expected directory contain?*
Which artifact actually loaded · what the runtime reported · what errors occurred · which
commands registered · which permissions exist · what a user experiences · what data is modified ·
what state survives a restart.

Pass I is Part XII's observability precondition applied at closure, and it is the pass that
detects the divergence class Part 27 §3 lists last: declared files versus actual runtime. Every
other pass can be run against a filesystem. This one cannot, and where the runtime is
unreachable the correct output is could-not-assess, never a clean result.

## 7. Negative proof as a first-class obligation

Passes B and C are not symmetrical, and treating them as two halves of the same activity is the
error this section exists to prevent.

| | Positive claim | Negative claim |
|---|---|---|
| Form | *X is present and works* | *Y is absent and unreachable* |
| Discharged by | exercising X | **enumerating every route to Y and showing each is closed** |
| Cost | proportional to X | proportional to the **route space**, not to Y |
| Default failure | the test is missing | the test *passes vacuously* |

The fourth row is the danger. A positive test that was never written is visibly absent from the
suite. A negative test written as *"we did not observe Y"* passes, looks like evidence, and
demonstrates nothing — it reports the coverage of the search, not the state of the estate. This
is `T-CLAE-ZERO-WITHOUT-COVERAGE` reaching the closure record, and it is why Part XIII's
three-valued arity is not optional here: *searched the six known routes and found nothing* and
*could not enumerate the routes* must be different outputs.

An unreachability claim is therefore admissible only with its **route enumeration** attached:
which paths to Y were considered, which were checked, and which were not. A claim of absence with
no route list is recorded as an unknown, not as a negative proof. — Asymmetry INFERRED from
Part II and Part XIII; the estate instance that produced it is OBSERVED in the source, where the
withdrawn mechanic had to be shown unreachable through loading, commands, aliases, interface
surfaces, permissions, persisted data, scheduled tasks and fallback paths — eight routes for one
absence.

**Eight routes for one withdrawal** is the number worth carrying. It is why negative proof is a
pass rather than a test, and why an executor's own suite almost never contains one.

## 8. Selection — which passes run

Running nine passes on every closure is disproportionate and will not survive contact with
delivery pressure. The source does not state a selection rule; this one is derived from Part VII
and Part XIII rather than invented, and is labelled accordingly.

**Three passes are unconditional**, because each answers a question whose omission is
undetectable afterwards:

- **Pass A**, because a closure that resolved a different objective than the one stated is not a
  quality problem but a category error, and nothing downstream detects it.
- **Pass C**, whenever anything was withdrawn, quarantined or migrated — items 4, 5 and 6 of the
  closure pack. If those three are empty, Pass C is *not applicable* and is recorded as such.
- **Pass I**, whenever a runtime exists. Filesystem-only verification is Part XII's failure, and
  its absence is the single most common way a closure is confidently wrong.

**The remaining six are selected by what the mission touched:**

| If the mission… | Run |
|---|---|
| removed or superseded anything | D, H |
| added a capability, or moved one between owners | E |
| touched anything a prohibition governs | F |
| changed one instance of a multi-instance estate | G |
| changed only additive behaviour in one instance | B alone suffices as the baseline |

**A pass not run is recorded as not-run with its reason**, never omitted. The distinction between
*ran and found nothing* and *did not run* is the same distinction Part XIII §7 makes about
instrument arity, arriving at the level of the review programme. A closure reporting "no findings
across the multipass" without a per-pass disposition has reported the reviewer's diligence, not
the estate's state. — Selection rule INFERRED; it has not been operated and §14 records the doubt.

## 9. A count that does not survive checking

The ratified scope for this Part describes *"the 20 passes and their selection"*. The source
supplies **nine**, lettered A through I, and no tenth appears anywhere in the section or after it.

This Part delivers the nine that exist. It does not pad to twenty, and it does not silently
deliver nine under a heading that says twenty. Two candidate explanations were considered — a
miscount, or a count of the passes' constituent questions, of which there are roughly fifty —
and neither is confirmable from the documents, so neither is asserted.

The pattern is the finding rather than the number: **a scope description written outside the
corpus cannot see the corpus, and its counts are hypotheses about the source, not measurements of
it.** Three of the sealed Parts' own counts were found to have the same shape when
`CLAE_PROCESS_RULES.md`, `CLAE_PRODUCTION_GATES.md` and `CLAE_EVALS.md` were built. — OBSERVED by
enumeration of the source section.

## 10. Boundary

- This Part does not decide who runs the passes. Part 27 §13 left the prosecutor's
  implementation open and that stands.
- It does not bound the review's total cost. That is Part 29's review budget, and without it §8's
  selection rule is a preference rather than a constraint.
- It does not define repair. A sustained objection routes to `REPAIR_REQUIRED`, and what happens
  there is Part 29.
- Pass F identifies functional equivalence to a *prohibited* mechanism. It does not decide what
  is prohibited — that is an estate's own constitutional question and CLAE takes it as an input.

## 11. Failure modes

| Failure | Mechanism |
|---|---|
| **Review before freeze** | evidence describes a state that no longer exists; the two parties argue about different artifacts |
| **Freeze that never lifts** | the mission stalls inside a control designed to be temporary |
| **Summary handed first** | the reviewer searches the space the summary describes; omission is outside both parties' search |
| **Passes merged** | the questions the merged form cannot express are dropped silently |
| **Absence asserted from non-observation** | a vacuously passing negative test that looks like evidence |
| **Unreachability without a route list** | the claim's cost was proportional to the artifact, not to the route space |
| **Name-keyed constitutional review** | defeated by a rename, including an innocent one |
| **Uniformity read as health** | identical configuration where an overlay should exist, concealing the unapplied overlay |
| **Filesystem read as runtime** | Pass I approximated by Pass B; the divergence class is structurally invisible |
| **Passes silently not run** | no per-pass disposition, so diligence is reported instead of coverage |

## 12. Detection signatures

1. **A closure pack with no withdrawn/quarantined/migrated items but a mission that removed
   something.** The set Pass C must prove unreachable was never written down.
2. **Negative tests phrased as observations.** Read them: any that says *not seen* rather than
   *route enumerated and closed* is vacuous.
3. **A multipass result with one verdict.** No per-pass disposition means selection and coverage
   are both unrecorded.
4. **Reviews whose findings all lie inside the summary's topics.** The signature of anchoring.
5. **Identical configuration files across instances that have different roles.** Pass G's finding,
   visible with a hash comparison and almost never run.
6. **Exceptions with no expiry field.** Pass H cannot ask its highest-yield question, so the
   estate accumulates permanently-valid temporary decisions.

## 13. Trap seeds — for Part XXII

- **T-CLAE-EVIDENCE-AFTER-DRIFT** — evidence gathered while the artifact is still moving, so the
  record describes a state that no longer exists and the discrepancy is unattributable.
- **T-CLAE-SUMMARY-ANCHORED-REVIEW** — the challenge searches the space the executor's summary
  describes, so omitted work is outside the search of both parties.
- **T-CLAE-VACUOUS-NEGATIVE-PROOF** — an absence claim discharged by non-observation, which passes
  and demonstrates nothing.
- **T-CLAE-UNENUMERATED-ROUTE-SPACE** — unreachability asserted after checking the obvious path,
  with the remaining routes neither checked nor listed.
- **T-CLAE-NAME-KEYED-PROHIBITION** — a prohibition enforced by name, defeated by any rename
  including an unintentional one.
- **T-CLAE-UNIFORMITY-AS-HEALTH** — identical configuration across instances that should differ,
  read as consistency rather than as an unapplied overlay.
- **T-CLAE-PASS-MERGE-LOSS** — distinct question shapes collapsed into one review, dropping the
  questions the merged form cannot express.

## 14. Rule seeds — for Part XXIII

- **PR-CLAE-FREEZE-BEFORE-EVIDENCE** — the artifact is frozen before the closure pack is
  assembled, and modification is prohibited until the first review completes.
- **PR-CLAE-WITHHOLD-THE-SUMMARY** — the challenge receives primary materials first; the
  executor's summary is read afterwards as one more claim to check.
- **PR-CLAE-ABSENCE-REQUIRES-ROUTES** — an unreachability claim carries its route enumeration:
  routes considered, checked, and not checked. Without it the claim is recorded as an unknown.
- **PR-CLAE-SEARCH-BY-PROPERTY-NOT-NAME** — constitutional review searches for the governed
  properties, never for the governed names.
- **PR-CLAE-PER-PASS-DISPOSITION** — every pass records ran-and-found, ran-and-clean, not-
  applicable, or not-run-with-reason. A single aggregate verdict is inadmissible.
- **PR-CLAE-CLOSURE-PACK-LISTS-REMOVALS** — withdrawn, quarantined and migrated items are
  enumerated, because they are the input to the negative pass.

## 15. Eval seeds — for Part XXIV

- **Freeze-integrity probe.** Hash the artifact at `CHANGE_FROZEN` and again at verdict. Any
  difference means the review's subject changed underneath it.
- **Anchoring probe.** Run the challenge twice, once with the summary and once without, and
  compare the finding sets. A large difference measures the anchoring the source asserts without
  measuring.
- **Vacuous-negative census.** Classify every negative test as route-enumerated or
  non-observation. The second class is the estate's false confidence, counted.
- **Route-space probe.** For one withdrawal, independently enumerate the routes and compare
  against the closure's list. The delta is the negative pass's real coverage.
- **Rename probe.** Rename a governed mechanism and re-run Pass F. If it is no longer found, the
  review is name-keyed.
- **Selection-audit probe.** Over a period, count closures where an unconditional pass was
  recorded not-run. Each is a gate that did not fire.

## 16. Production Reality Gate seed — for Part XXV

**Multipass Integrity Gate.** A multipass result is admissible as evidence only when the artifact
was frozen before the pack was assembled and unchanged at verdict, each of the nine passes carries
a disposition, the three unconditional passes are ran or explicitly not-applicable, every
unreachability claim carries a route enumeration, and Pass I reports could-not-assess rather than
clean where no runtime was reachable. Results failing this are recorded as a **review**, correctly
labelled, rather than as verified closure evidence.

## 17. Pseudoflow — running the challenge

The executor declares `REQUEST_CLOSURE`. The artifact freezes; hashes, inventory, tests and
observed runtime are captured. The pack is assembled with its fifteen items, and every claim is
paired with its evidence.

The prosecutor receives the primary materials — mission, initial state, diff, inventories,
manifests, logs, results, policies — and not the summary. It selects passes per §8, recording the
selection and the reason before running anything, so the selection cannot be adjusted afterwards
to match what was found.

It runs the selected passes. For each: a disposition. For each finding: an objection anchored per
Part 27 §5, carrying its discharge condition. For each unreachability claim it encounters in the
pack, it checks the route enumeration and treats an absent one as an unknown rather than a
falsehood — the claim may well be true, and that is exactly why it must be labelled rather than
either accepted or rejected.

It reads the summary last, as a claim.

Where the runtime could not be reached, Pass I emits could-not-assess and the closure cannot reach
`CLOSURE_CANDIDATE` on filesystem evidence alone.

## 18. Integration

Part VI supplies paired observation, which is why the freeze exists. Part XII supplies the
observability precondition that Pass I enforces at closure. Part XIII supplies three-valued arity,
without which Pass C and Pass I both report vacuous cleans. Part XV converts a sustained objection
into a durable probe rather than a one-time fix. Part XXII §2's symptom-keying is the same
reasoning as Pass F's property-keying, arrived at independently in a different domain. Part 27
supplies the standing, the anchors and the state machine; this Part supplies the procedure between
`CHANGE_FROZEN` and `CLOSURE_CANDIDATE`.

Forward: Part 29 bounds the loop this Part can otherwise run indefinitely; Part 30 takes each
sustained objection from a local repair to an institutional cause.

## 19. Open questions

1. How much anchoring does withholding the summary actually remove? The source asserts the
   reduction and this Part builds a procedure on it, but no measurement exists — and the two-run
   probe in §15 is cheap. Until it runs, the ordering is a well-motivated hypothesis. —
   HYPOTHESIS, and the load-bearing one in this Part.
2. Is the route space of a withdrawal ever fully enumerable? Eight routes were found for one
   estate withdrawal; whether that set is complete or merely the routes someone thought of is
   unknown, and an unreachability proof over an incomplete route space is a bounded claim
   presented as an absolute one. — UNKNOWN.
3. Does the §8 selection rule survive delivery pressure? A selection rule that is itself selected
   by the party under pressure is not a constraint. The unconditional three are the hedge; whether
   three is the right number is unmeasured. — UNKNOWN.

## 20. Institutional writeback

Seven trap seeds, six rule seeds, six eval seeds, one production gate.

Three portable results. **Freeze before you gather evidence**, because a party looking for
problems will fix them while looking, and the resulting record describes a state that no longer
exists. **An absence is a positive claim** — discharged by enumerating the routes and closing
each, never by not having seen it; the cost of a negative proof is proportional to the route
space, and eight routes for one withdrawal is the number that makes this concrete. And **search by
property, not by name**, because every name-keyed prohibition is defeated by a rename, which is
the same result Part XXII reached about trap registries from an entirely different direction.

The structural finding: **the nine passes are nine question shapes, not nine degrees of care.** A
reviewer looking harder produces more Pass B; it never produces Pass C, D or E, because those
questions cannot be asked from the position a single artifact-facing inspection occupies. That is
why the multipass is a structure rather than an instruction to be thorough — and it is why
merging passes to save time deletes findings rather than deferring them.
