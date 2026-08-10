---
title: "CLAE Part 30 — Root-Cause Elevation, Sibling Campaigns and Failure-to-Immunity"
family: clae
part: 30
depends_on: [X, XI, XV, XXI, XXII, XXIII, XXV, 27, 28, 29]
feeds: []
status: SEALED
date: 2026-08-10
---

# Part 30 — Root-Cause Elevation, Sibling Campaigns and Failure-to-Immunity

## 1. Purpose

Part 29 disposed of a finding. This Part decides **how far up** to treat it, **how wide** to search
for its relatives, and **what protection** to install so it cannot return — then bounds all three so
that the answer is not always "everything".

The question it answers is the one that separates a maintained estate from a repaired one:

> Given a defect, what stops the system from finding the *same* defect again next quarter under a
> different name?

Four mechanisms: the elevation ladder and its stopping rule (§2–§3), the test that assigns a level
(§4), the same-session sibling search (§5), and the compiler from cause to protection (§6–§7). Two
disciplines keep them from producing disconnected bureaucracy: no orphan closure (§8) and prudent
promotion (§9).

## 2. The root-cause elevation ladder

Six levels. The example is one artifact found where it did not belong; the ladder is general.

| Level | Cause | Sufficient response at this level |
|---|---|---|
| **1** | **Symptom** — this artifact does not belong here | *(none — deleting it is insufficient by construction)* |
| **2** | **Local cause** — it was copied, or never withdrawn | withdraw it · clean its residues · verify absence |
| **3** | **Process cause** — artifacts can be introduced with no admission gate | block informal installation · require a manifest and approval |
| **4** | **Architectural cause** — no authorized composition exists for this instance | an identity manifest · a desired-state composition · the instance's overlay |
| **5** | **Institutional cause** — nothing automatically detects contamination, forbidden capability, duplication, residue or lifecycle debt | admission controller · ownership registry · drift sentinel · forbidden-mechanics registry · lifecycle gate |
| **6** | **Transversal immunity** — the same family can exist across every instance and every future template | audit the whole estate · repair the template · install gates in the shared toolchain · add tests · promote the knowledge · assess exposed projects |

Level 1 has no sufficient response and that is the point of listing it. **Deleting the artifact is
the null action** — it restores the estate to the state that produced the artifact in the first
place, which is a return to the initial conditions of the failure rather than a repair of it.

The levels are not severity. They are *locations*: each names a different place the cause could
live, and the repair at each is a different kind of object — an action at 2, a procedure at 3, a
declaration at 4, an instrument at 5, and a campaign at 6.

### 2.1 The count does not match the scope description

The ratified scope for this Part describes *"the 7-level ladder"*. The source supplies **six**,
numbered 1 through 6, with no seventh anywhere in the section.

This is the second such discrepancy in the extension — Part 28 §9 records that the same scope
document describes twenty adversarial passes where nine exist. Two independent counts in one
four-Part scope, both overstated, both in a document written outside the corpus it describes.

The pattern is now established well enough to state as a result rather than an anomaly: **a scope
description authored outside a corpus carries hypotheses about that corpus, not measurements of
it.** Three of the sealed Parts' own counts had the identical shape when the registries were built.
The correct response is the same in every case — deliver what exists, record the difference, amend
nothing that is sealed. — OBSERVED by enumeration of the source section.

## 3. The stopping rule

> **Closure is not accepted at Level 1 when the evidence shows the cause lives at Level 3, 4 or 5.**

That single sentence is what makes the ladder a control rather than a taxonomy, and it is stated as
a *gate on closure*, not as advice about thoroughness.

The rule cuts in both directions, and the second cut is the one usually missing:

**Under-elevation** treats a symptom and reports a repair. The estate is unchanged in every respect
that mattered, and the record now says the problem was handled — which is worse than no record,
because the next occurrence looks like a new problem rather than a recurrence.

**Over-elevation** answers every defect with a Level 6 campaign. This is not caution. Part XI §2's
imported-floor result applies directly: a control derived from a cause the estate does not have is
a cost with no corresponding risk, and its arrival trains everyone that controls are
disproportionate. The estate then skips the campaign when it *is* warranted.

The rule's phrasing binds elevation to **evidence** — *when the evidence shows* — which is what
prevents both failures. The level is a finding about where the cause lives, and like every other
finding in this family it is claimed with an epistemic state and can be wrong.

## 4. The Institutional Cause Test

Ten questions that locate the level. Each is answerable from the incident and the estate, and a
`yes` on any one is evidence the cause lives above Level 2.

| # | Question | Elevates toward |
|---|---|---|
| 1 | Could it reappear through the normal workflow? | **3** — process |
| 2 | Could it exist in another instance? | **6** — and triggers §5 immediately |
| 3 | Did the error come from a template? | **6** — template repair plus retroactive audit |
| 4 | Is there an ambiguous owner? | **4** — architectural |
| 5 | Did the *absence* of a rule make the failure possible? | **5** — institutional |
| 6 | Does the rule exist but lack enforcement? | **5** — but a different repair: a mechanism, not a rule |
| 7 | Would the current tests have caught it earlier? | **5** — detector gap |
| 8 | Can the same human or cognitive decision repeat? | Part 29's precursor detector |
| 9 | Can the withdrawn component be reactivated? | **2** — residue, discharged by Part 28's Pass C |
| 10 | **Does the solution depend on someone remembering to do something?** | *see below* |

Questions 5 and 6 look similar and are the most useful pair in the test, because they separate two
repairs that are constantly confused. A missing rule is repaired by writing one. A rule that exists
and is not enforced is **not** repaired by writing it more emphatically — it is repaired by a
mechanism, and Part XXIII §4 says exactly which: move it down the enforcement layers. Re-stating an
unenforced rule is the single most common non-repair in governance work.

**Question 10 is not an elevation question. It is the exit criterion.**

> A `yes` to question 10 means the work is not finished. It means the protection installed is
> doctrine — layer 5 — and depends on recall at the moment of decision.

This is Part XXIII §4's enforcement ladder arriving as a closure question, and it is the most
valuable line the source contributes to this family. It converts "did we fix it?" into a question
with a mechanical answer, and the answer is checkable by someone who was not present. — Mapping of
questions to levels INFERRED; the ten questions and question 10's force are OBSERVED in the source.

## 5. The sibling defect campaign

**Every confirmed defect generates a search for its relatives in the same session.**

The same-session constraint is the mechanism, for Part XV's reason: the context that recognises the
family is loaded now and will not be reloaded later. A sibling search deferred is a sibling search
not performed — and unlike a deferred repair, nobody notices, because the siblings were never
enumerated to begin with.

The search is keyed by **failure family**, never by the name of the instance found:

| Family | The search space |
|---|---|
| **Prohibited-mechanic family** | every naming variant of the mechanic, plus its configurations, commands, permissions, interface surfaces and persisted data |
| **Cross-context contamination** | names belonging to another context · inherited cores · copied configuration · foreign data · scripts · databases · documentation · permissions · messages |
| **Retirement debt** | disabled, superseded and backup suffixes · copies · directories with no component · configuration with no consumer · withdrawn dependencies · orphaned data |
| **Capability duplication** | second owners of a capability already owned |

Keying by family rather than by name is the same result Part 28 §6 reached for Pass F and Part XXII
§2 reached for the trap registry — three arrivals now, from three directions, at one conclusion:
**a name-keyed search finds the instance you already found.**

The campaign's output is not a list of siblings. It is a **per-family disposition**: searched and
clean · searched and found · not searched, with the reason. A campaign reporting only what it found
has reported its own diligence, which is the failure Part 28 §8 records for unrun passes.

## 6. The failure-to-immunity compiler

After the cause is fixed, the system chooses which protection to install. The mapping is
deterministic enough to be a table, and that is its value — the protection stops being a matter of
taste.

| Cause | Appropriate protection |
|---|---|
| Unexpected artifact | allowlist + scanner |
| Component from another context | context-purity gate |
| Duplicated capability | capability-ownership validation |
| Prohibited mechanic | semantic forbidden-mechanics detector |
| Residual file | lifecycle and residue scanner |
| Incorrect path | filesystem contract |
| Configuration with no consumer | wiring test |
| Manual change | desired-state reconciliation |
| Error originating in a template | template repair + retroactive audit |
| Rule ignored | enforcement hook |
| Insufficient test | a new independent test |
| Ambiguous interpretation | canonical definition + examples |
| Error of the agent's own reasoning | cognitive precursor detector |

Three rows are worth reading twice.

**Rule ignored → enforcement hook**, not a stronger rule. The table encodes question 6's answer and
refuses the restatement reflex.

**Insufficient test → a new *independent* test.** Independent of the implementation, per Part 29
§6's circular oracle: a test written by the party whose assumption failed inherits the assumption.

**Error of the agent's own reasoning → a precursor detector.** The table's last row admits a class
of cause that most incident taxonomies have no slot for, and Part 29 is the instrument it points
at. A failure caused by how the work was reasoned about cannot be immunized by a check on the
artifact.

### 6.1 The immunization artifacts

A serious incident leaves one or more of: a test · a detector · a gate · a manifest · an allowlist ·
a registry · a template correction · a migration rule · a runbook · a rollback · a candidate hard
rule · a retroactive audit · a benchmark · a mutation test.

**Not every failure needs every protection.** The source states this before the table and it is the
line that keeps the compiler affordable. Fourteen artifact kinds applied to every incident produces
the ritual accumulation Part X §6 exists to attack, and the accumulation is self-defeating: each
unnecessary artifact needs its own retirement condition, its own owner and its own maintenance, and
none of them is ever removed.

The selection is the table's left column. One cause, one protection, and a second only when the
cause genuinely has two locations.

## 7. Immunization is discharged, not promised

Part 27 §6 made `IMMUNIZATION_REQUIRED` a state that blocks `CLOSURE_CANDIDATE`. Part 29's stop
condition 6 requires the necessary immunization to be *installed*. This Part supplies what
*installed* means, because the word is where the discipline usually fails:

An immunization is installed when its artifact **exists, runs, and has been shown capable of
failing.** The third clause is Part XXIV §5 again, and it is not optional here: a detector added in
response to an incident and never shown to detect that incident is the incident's memorial, not its
immunity.

The cheapest sufficient demonstration is to run the new artifact against the **pre-repair state**.
It is available — the freeze of Part 28 §2 captured it — and it is the one moment in the lifecycle
when a known-positive case exists for free. Part XV called this the incident's short expiry; here it
has an exact deadline, because after the repair lands the known-positive case has to be
reconstructed.

> **Run the new detector against the state that caused the incident, before that state stops
> existing.** — INFERRED from Parts XV and XXIV; the freeze artifact that makes it free is Part 28's.

## 8. No orphan closure

The system does not permit isolated preventive pieces. Three laws, each requiring an artifact to
carry its links:

| Law | Must link to |
|---|---|
| **No orphan fix** | incident · cause · evidence · test · owner · context · commit or change · result |
| **No orphan rule** | failure family · prevention · detector · severity · scope · exception · escalation |
| **No orphan test** | bug family · protected behaviour · oracle · meaning of its failure · cadence · owner · baseline |

The three laws are one law applied to three artifact kinds: **a preventive artifact that cannot
name what it prevents is not a control, it is an obligation with no expiry.**

Their absence is what produces disconnected bureaucracy — a growing set of rules, tests and fixes
that nobody can retire because nobody can determine what any of them was for. Part X §6, Part XV §7,
Part XXII §8 and Part XXIII §7 each independently required retirement conditions for their own
accumulating sets; §8 is the general statement those four are instances of.

The *meaning of its failure* field in the third law is the one most often missing and the most
expensive to reconstruct. A failing test whose failure has no stated meaning generates an
investigation into what the test wanted, every time it fails, forever.

## 9. Prudent promotion of hard rules

A single session may legitimately create a local detector, create a test, correct a template,
register the archetype, draft a candidate hard rule, and audit siblings.

> **It should not automatically convert every observation into universal law.**

Two promotion paths, distinguished by where the rule's authority comes from:

**Immediate promotion** — when the rule derives directly from an already-established higher law.
Detecting and blocking a second instance of an already-prohibited mechanic does not require three
fresh incidents; it is enforcement of an existing constitution, and demanding new evidence for it
confuses *establishing* a law with *applying* one.

**Candidate promotion** — when a genuinely new mechanism appears. The proposed rule is treated as a
hypothesis and the same session must: state the hypothesis · investigate · find cases · design the
exceptions · build a provisional detector · submit the rule for review.

The source's own example of a rule that should *not* be promoted immediately is instructive: *every
directory at the root named after a component must be removed* is too broad, because some runtimes
legitimately generate such directories. The rule is not wrong; it is **unbounded**, and its
exceptions are discovered by investigation rather than by intuition.

### 9.1 This refines Part XXIII's promotion test rather than duplicating it

Part XXIII §2 promotes on **irrecoverability**, never on frequency. §9 adds a second, independent
axis — **derivation**:

| | Derives from an established law | Genuinely new mechanism |
|---|---|---|
| **Violation is unrecoverable** | promote immediately as a hard rule | candidate; investigate, then promote |
| **Violation is recoverable** | promote immediately as enforcement of the parent law | candidate process rule; provisional detector first |

The axes answer different questions. Irrecoverability decides *what kind* of rule it should be;
derivation decides *how much evidence* is required before it becomes one. Neither substitutes for
the other, and the frequency criterion both reject remains rejected. — Synthesis INFERRED; both
inputs are stated in their respective sources.

## 10. Boundary

- This Part does not define the estate-specific registries named at Level 5. Those are an estate's
  own artifacts; CLAE specifies that the level exists and what discharges it.
- It does not decide what is prohibited. Pass F and the forbidden-mechanics detector enforce a
  constitution CLAE takes as input.
- It does not set a sibling-search depth. The family key bounds the space; how exhaustively it is
  swept is a budget question and belongs to Part 29 §11.
- It does not promote any rule. §9 is the procedure; promotion remains the archive owner's act, as
  Part XXIII §2 states.

## 11. Failure modes

| Failure | Mechanism |
|---|---|
| **Closure at Level 1** | the artifact is deleted, restoring the estate to the state that produced it |
| **Level 6 for everything** | controls derived from causes the estate does not have; the campaign is skipped when it is warranted |
| **Unenforced rule restated** | question 6's answer ignored; the repair is emphasis rather than mechanism |
| **Sibling search deferred** | the context that recognises the family is gone, and the siblings were never enumerated |
| **Sibling search keyed by name** | finds the instance already found |
| **Campaign reports only findings** | diligence recorded instead of coverage; unsearched families indistinguishable from clean ones |
| **Every protection for every failure** | fourteen artifact kinds per incident, each needing its own owner and retirement |
| **Detector never shown to fire** | the incident's memorial rather than its immunity |
| **Immunization deferred past the freeze** | the known-positive case has to be reconstructed at cost, and usually is not |
| **Orphan fix, rule or test** | a preventive artifact that cannot name what it prevents and can never be retired |
| **Observation promoted to universal law** | an unbounded rule whose exceptions are discovered in production |

## 12. Detection signatures

1. **Incidents whose repair is a deletion.** Level 1 closure, visible in the change alone.
2. **A rule reissued in stronger language after being violated.** Question 6 answered `yes` and
   repaired as though it were question 5.
3. **Repairs with no sibling disposition.** No per-family record means the search was not scoped.
4. **Detectors with no recorded firing, ever.** Including the one added for the incident that
   motivated them.
5. **Tests whose failure meaning is unstated.** Each failure re-opens the question of what the test
   wanted.
6. **Rules with no exception clause added within one session of a broad-scope promotion.** The
   exceptions exist; they are being discovered by whoever trips over them.
7. **A protection table applied uniformly.** Every incident yielding the same artifact set means the
   left column is not being read.

## 13. Trap seeds — for Part XXII

- **T-CLAE-SYMPTOM-CLOSURE** — the artifact is removed and the estate returns to the state that
  produced it, with the record now saying the problem was handled.
- **T-CLAE-REFLEX-ELEVATION** — every defect answered at the transversal level, producing controls
  for causes the estate does not have and training everyone that controls are disproportionate.
- **T-CLAE-RESTATED-UNENFORCED-RULE** — an unenforced rule repaired by emphasis rather than by a
  mechanism, leaving its enforcement layer unchanged.
- **T-CLAE-DEFERRED-SIBLING-SEARCH** — the relatives search postponed past the session that
  recognised the family, so it is never performed and never missed.
- **T-CLAE-NAME-KEYED-SIBLING-SEARCH** — a campaign keyed to the instance's name, which finds the
  instance already found.
- **T-CLAE-MEMORIAL-DETECTOR** — a detector installed after an incident and never shown to detect
  it, indistinguishable from one that cannot.
- **T-CLAE-ORPHAN-PREVENTION** — a fix, rule or test that cannot name what it prevents, and can
  therefore never be retired.
- **T-CLAE-UNBOUNDED-PROMOTION** — a single observation promoted to universal law, whose exceptions
  are discovered by whoever trips over them.

## 14. Rule seeds — for Part XXIII

- **PR-CLAE-ELEVATE-ON-EVIDENCE** — the repair level is a finding about where the cause lives,
  claimed with an epistemic state; closure is refused at Level 1 when evidence places the cause
  higher.
- **PR-CLAE-RUN-THE-CAUSE-TEST** — the ten institutional-cause questions are answered before a
  repair is accepted, and their answers are recorded.
- **PR-CLAE-NO-IMMUNIZATION-THAT-DEPENDS-ON-RECALL** — a protection whose operation requires someone
  to remember is recorded as doctrine, and the work is not closed as immunized.
- **PR-CLAE-SIBLING-SEARCH-SAME-SESSION** — every confirmed defect triggers a family-keyed relatives
  search in the session that confirmed it.
- **PR-CLAE-SEARCH-THE-FAMILY-NOT-THE-NAME** — the sibling campaign is keyed by failure family;
  name-keyed searches are inadmissible as coverage.
- **PR-CLAE-PER-FAMILY-DISPOSITION** — each family is recorded searched-and-clean, searched-and-
  found, or not-searched-with-reason.
- **PR-CLAE-ONE-CAUSE-ONE-PROTECTION** — the protection is selected from the cause, and a second is
  installed only when the cause has a second location.
- **PR-CLAE-PROVE-THE-DETECTOR-ON-THE-PRE-REPAIR-STATE** — a new protection is run against the state
  that caused the incident before that state stops existing.
- **PR-CLAE-NO-ORPHAN-ARTIFACT** — every fix, rule and test carries its links; one that cannot name
  what it prevents is not admitted.
- **PR-CLAE-PROMOTE-BY-DERIVATION** — a rule deriving from an established law is promoted
  immediately; a genuinely new mechanism enters as a candidate with a provisional detector and
  designed exceptions.

## 15. Eval seeds — for Part XXIV

- **Elevation-level audit.** For closed incidents, compare the level treated against the level the
  ten questions indicate. Systematic under-elevation is the recurrence engine.
- **Recurrence probe.** Count incidents whose family matches an earlier closed incident. A non-zero
  rate measures under-elevation directly, without opinion.
- **Sibling-coverage probe.** For one confirmed defect, independently run the family search and
  compare against the campaign's disposition. The delta is the campaign's real coverage.
- **Detector-firing census.** For every installed protection, has it fired once, including on the
  incident that motivated it? Never-fired protections are the estate's decorative surface, counted.
- **Orphan census.** Sample fixes, rules and tests and check their required links. The unlinked
  fraction is the set that can never be retired.
- **Promotion-path audit.** For promoted rules, was the path immediate or candidate, and does the
  recorded derivation support it? Immediate promotions with no parent law are unbounded rules.
- **Question-10 probe.** For each closed immunization, ask whether its operation depends on recall.
  A `yes` rate above zero measures how much of the estate's protection is doctrine.

## 16. Production Reality Gate seed — for Part XXV

**Immunity Gate.** A closure may be described as *immunized* only when the ten institutional-cause
questions are answered and recorded, the treated level matches the level the evidence indicates, the
sibling campaign carries a per-family disposition, each installed protection has been run against
the pre-repair state and shown capable of failing, every fix, rule and test carries its links, and
question 10 is answered `no`. Closures failing this are recorded as **repaired** — a legitimate and
often sufficient outcome, correctly labelled — rather than as immunized.

The distinction that gate enforces is the whole Part: **repaired and immunized are different
claims**, and an estate that reports the second while achieving the first will meet the same defect
family again and record it as new.

## 17. Pseudoflow — from one defect to immunity

A finding is sustained and classified. Before repairing, answer the ten questions and record the
answers; they locate the level, and the level determines what kind of object the repair is.

Repair at the indicated level. If questions 5 and 6 disagree — the rule is absent versus present but
unenforced — repair the one the evidence supports, and never repair an enforcement gap by
re-stating the rule.

Immediately, in the same session, run the family-keyed sibling search. Record a disposition per
family, including families searched and found clean, and families not searched with the reason.

Select the protection from the cause using the compiler's left column. Install one. Run it against
the pre-repair state captured by the freeze, and record that it fired. If it does not fire, the
protection does not protect and the incident is not closed.

Link the artifact: the fix to its incident, cause, evidence, test, owner and result; a new rule to
its family, prevention, detector, severity, scope, exception and escalation; a new test to its bug
family, protected behaviour, oracle, failure meaning, cadence, owner and baseline.

If a rule is warranted, choose the promotion path by derivation. Immediate where it enforces an
established law. Candidate otherwise — hypothesis, investigation, cases, exceptions, provisional
detector, review.

Finally, answer question 10. If the protection depends on someone remembering, the state is not
immunized, and the honest record says *repaired*.

## 18. Integration

Part X supplies floor accumulation, which is why §6.1 refuses to install every artifact. Part XI
supplies the imported-floor result that §3 uses against over-elevation. Part XV supplies the
incident's short expiry, which is why the sibling search and the detector proof both happen in the
same session. Part XXI supplies the five roots, which are the elevation ladder's Level 5 in this
family's own vocabulary — a root eliminated retires every trap beneath it, which is exactly the
transversal claim of Level 6. Part XXII §2 and Part 28 §6 supply the two prior arrivals at
search-by-property. Part XXIII §2 supplies the irrecoverability axis that §9.1 crosses with
derivation. Part XXIV supplies the negative control that §7 makes mandatory for every new
protection.

Backward: this Part discharges Part 27's `IMMUNIZATION_REQUIRED` state and Part 29's stop
condition 6. Those are the two places the extension blocks on immunity, and §16's gate is what
either satisfies.

Outside the family, this stack's recurring-error log and its rule archive are the two surfaces §8's
laws would extend: the log already carries families, and the archive already carries origins. What
neither carries is the link between a rule and the detector that enforces it, which is the field
question 10 makes load-bearing.

## 19. Open questions

1. Is the six-level ladder's Level 5 distinguishable from Level 4 in practice? An absent authorized
   composition (4) and an absent detector for compositions (5) are adjacent, and the repairs differ
   — a declaration versus an instrument. Whether practitioners route consistently between them is
   untested. — UNKNOWN.
2. What is the correct recurrence window for the §15 probe? A family recurring after two years may
   indicate a retired protection rather than an unelevated cause, and the two have opposite repairs.
   Part V's horizon machinery applies but the period is unmeasured. — UNKNOWN.
3. Does running a new detector against the pre-repair state generalise beyond artifact-shaped
   defects? For a cognitive-cause row — the compiler's last — the pre-repair "state" is a session
   transcript, and whether a precursor detector can be validated against one is unresolved. —
   HYPOTHESIS, and the row most likely to be adopted without its proof.

## 20. Institutional writeback

Eight trap seeds, ten rule seeds, seven eval seeds, one production gate.

Three portable results. **Deleting the artifact is the null action** — it restores the estate to the
conditions that produced the artifact, while the record now says the matter was handled, which is
worse than no record because the recurrence will read as new. **A rule that exists but is not
enforced is not repaired by restating it** — questions 5 and 6 separate the two, and the second is
repaired only by moving it down the enforcement layers. And **repaired and immunized are different
claims**: the difference is whether the installed protection has been shown capable of firing, and
the free moment to show it is against the pre-repair state the freeze already captured.

The structural finding is question 10, and it is the sharpest thing in the source: **does the
solution depend on someone remembering to do something?** A `yes` means the protection is doctrine
and the estate's safety rests on recall at the moment of decision — which Part XXIII §5 already
measured as approximately the force of no rule at all. That question converts the vague obligation
to *fix it properly* into a check with a mechanical answer, verifiable by someone who was not
present, and it is the one line from this material that this family would have wanted most.
