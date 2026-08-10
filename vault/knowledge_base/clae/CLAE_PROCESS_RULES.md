---
title: "CLAE — Process Rules Registry"
family: clae
type: registry
kind: extract
sources: [Parts II–XXV (seeds), Part XXIII (schema, layers, promotion test)]
derivation: mechanical extraction from the sealed Parts; no entry carries information absent from its source
status: POPULATED
date: 2026-08-10
---

# CLAE — Process Rules Registry

> **What this file is.** Part XXVI §5 defines the twelve companion artifacts as *"extracts for retrieval convenience"* — the schemas, consolidations and measured counts live in the Parts. This file locates entries; it does not restate, resolve or extend them.
> **Reading rule.** Every row cites the Part that seeded it. Where a row's source is ambiguous, the ambiguity is transcribed rather than resolved.

**Schema:** Part XXIII §3 (eight fields). **Force doctrine:** Part XXIII §4 — *"A rule's actual force is determined by its enforcement layer, not by its wording."*

## 1. Census and the scope that reconciles it

| Scope | Measured |
|---|---|
| Parts I–XXI | **118** |
| Parts I–XXII | 124 |
| Parts I–XXVI (the sealed corpus) | 141 |
| Parts 27–30 (the G2 extension) | 33 |
| **Family total** | **174** |
| Distinct names | 174 |
| Duplicate names | 0 |

**Reconciliation.** Part XXIII §1 asserts *"Process rule seeds across Parts I–XXII: 118"*. The number 118 is exact — for Parts I–**XXI**. Parts I–XXII contain 124, because Part XXII §11 seeds six rules that Part XXII §15 explicitly hands forward (*"Part XXIII takes §11's six rules"*). The count's label and the count's scope differ by one Part.

Part XXIII is SEALED, so this registry records the reconciliation rather than amending the Part. Both numbers are correct about their own scope; only the label is wrong. The family total, including the G2 extension, is **174**.

## 2. Enforcement layer — how this column is filled

Part XXIII §5 states plainly that *"assigning all 118 was not performed here"*, and gives an estimate rather than an assignment. This registry does not perform the assignment either, because that would be a judgment per rule that no Part makes. It applies the Part's own stated default:

> `PR-CLAE-DECLARE-THE-LAYER` — *"A rule without one is recorded at layer 5 by default, since that is what it is until a mechanism exists."*

Every entry below is therefore **layer 5 of record**. That is a transcription of a declared default, not a measurement, and it carries the consequence Part XXIII §5 states without softening: *"A doctrine of 118 rules at layer 5 has approximately the force of a doctrine of zero rules."*

Part XXIII §5 names the subsets that are **candidates** for a lower layer. They are reproduced as candidates, not as assignments:

| Layer | Part XXIII §5's estimate | Status here |
|---|---|---|
| 1 Structural | three-valued instrument output · residual identity assigned once · the five closure verdicts as enumerated status values | candidate; not assigned per-rule |
| 2 Automated gate | *"roughly the nineteen gates"* — see `CLAE_PRODUCTION_GATES.md` | candidate; the gate census there measures 23 seeds, not 19 |
| 3–4 Advisory / checklist | *"a modest number"*, mostly Part XXIV's periodic probes | candidate; not assigned per-rule |
| 5 Doctrine | *"the majority"* | **default of record for all 174 entries** |

## 3. The entries

| # | Rule | Part | Layer | Statement |
|---|---|---|---|---|
| 1 | `PR-CLAE-ABSENCE-REQUIRES-ROUTES` | 28 | 5 | an unreachability claim carries its route enumeration: routes considered, checked, and not checked. Without it the claim is recorded as an unknown. |
| 2 | `PR-CLAE-ACQUIRE-WITH-RECORD` | V | 5 | a reference is usable only from the moment its acquisition record exists, complete with standing argument, rejected candidates and horizon. Records written later are labelled reconstructed and the dependent claims re-read. |
| 3 | `PR-CLAE-ADMIT-ON-OBSERVATION` | XXII | 5 | entries are admitted when a trap has been observed, not when one is imagined. |
| 4 | `PR-CLAE-ADVERSARIAL-VARIANT` | XXIV | 5 | every eval records how it could be satisfied without compliance. Where that path is cheaper than compliance, the eval is redesigned. |
| 5 | `PR-CLAE-ALWAYS-PINNED` | V | 5 | residuals cite a pin generation, never a moving object. Pin updates are events with records. |
| 6 | `PR-CLAE-ANCHOR-EVERY-OBJECTION` | 27 | 5 | an admissible objection cites a declared intent, a reference delta, or a registered trap or rule. |
| 7 | `PR-CLAE-ARGUE-THE-PROJECTION` | VI | 5 | a projection-based extraction records an argument that the projection preserves the dimension. Absent it, the extraction is L0. |
| 8 | `PR-CLAE-ASK-FOR-THE-CRITERION` | XVII | 5 | where a verdict would serve, ask for the criterion behind it. A criterion resolves the class; a verdict resolves the instance. |
| 9 | `PR-CLAE-ASK-IN-THE-WINDOW` | XVII | 5 | questions are routed once a concrete instance exists and while the cost of acting on an unfavourable answer is still bounded. A question routed after that point is recorded as a ratification, not as a judgment. |
| 10 | `PR-CLAE-ATTRIBUTION-BEFORE-REFERENCE` | XXI | 5 | pin generations and work-versus-bar decomposition are established before a reference discipline is adopted, since L2 makes unattributed adoption worse than none. |
| 11 | `PR-CLAE-BENCHMARK-THE-FAMILY` | XXIV | 5 | CLAE's self-assessment reports levels, not compliance. A pass/fail self-report is the family's own founding critique, self-inflicted. |
| 12 | `PR-CLAE-BOOK-TO-INSTRUMENT-DEBT` | XIV | 5 | a cycle spent building an instrument reports instrument debt repaid, never zero quality debt closed alone. |
| 13 | `PR-CLAE-BORROW-AS-HYPOTHESIS` | XI | 5 | an externally sourced minimum is adopted as a hypothesis and derived locally. Where time does not permit, it is labelled provisional with the derivation recorded as owed. |
| 14 | `PR-CLAE-BOUNDARY-NOT-TUNED-BY-COMPLAINT` | XVI | 5 | boundary placement is reviewed deliberately. Movement inward requires the same justification as movement outward, since only one direction generates feedback. |
| 15 | `PR-CLAE-BUDGET-BY-RISK` | 29 | 5 | review scope is set by what the change touches, and a simple change does not receive a full-estate scan. |
| 16 | `PR-CLAE-CAPTURE-THE-OBJECT` | V | 5 | where both are affordable, hold the artifact rather than the derived measurements, so unforeseen dimensions remain available. |
| 17 | `PR-CLAE-CERTIFICATE-CARRIES-NOT-EVALUATED` | 27 | 5 | drift coverage records what was not assessed and why, alongside what was. |
| 18 | `PR-CLAE-CHAIN-COVERAGE-INTERSECTED` | XIII | 5 | a chain declares its end-to-end coverage as the intersection of its members', and its envelope as compounded. |
| 19 | `PR-CLAE-CLASS-BECOMES-FLOOR` | XV | 5 | a recurring incident class across many artifacts is promoted to a floor rather than converted into a probe per occurrence. |
| 20 | `PR-CLAE-CLASSIFY-BEFORE-DISPOSING` | 29 | 5 | every sustained finding is classified self-repairable, owner-required or governance-violation before any action is taken on it. |
| 21 | `PR-CLAE-CLOSURE-HAS-A-HORIZON` | XX | 5 | every closure records a validity horizon. Past it, the unit is unverified rather than closed. |
| 22 | `PR-CLAE-CLOSURE-PACK-LISTS-REMOVALS` | 28 | 5 | withdrawn, quarantined and migrated items are enumerated, because they are the input to the negative pass. |
| 23 | `PR-CLAE-CLOSURE-PUBLISHES-STATE` | XX | 5 | closure publishes all six items of §4, including the undefined dimensions. A closure omitting them is a completeness claim and is labelled as one. |
| 24 | `PR-CLAE-COMPUTE-AT-EACH-SCALE` | XX | 5 | phase closure re-runs the closure obligation over aggregate residuals against phase-scale floors. Closure is never inherited from constituent units. |
| 25 | `PR-CLAE-CONTRACT-BEFORE-AUTONOMY` | XIX | 5 | autonomous work begins from a single written evidence contract carrying scope, dimensions, references, floors, instruments, oracle boundary, publication obligation and halt conditions. A distributed or implicit standard is recorded as absent. |
| 26 | `PR-CLAE-CONVERT-INSIDE-THE-INCIDENT` | XV | 5 | the probe is written during the diagnosis, not after the fix. Conversion deferred past the incident is recorded as an unconverted incident, not as pending work. |
| 27 | `PR-CLAE-DECLARE-EXTRACTION-LEVEL` | VI | 5 | every residual records its extraction level from §3. Ranking consumes only L3 or above. |
| 28 | `PR-CLAE-DECLARE-INSTRUMENT-PROPERTIES` | XIII | 5 | coverage, envelope, perturbation, extraction level, cost per observation and failure behaviour are declared before an instrument is used in accounting. |
| 29 | `PR-CLAE-DECLARE-THE-BOUNDARY` | XVI | 5 | the set of properties the system cannot verify about itself is written, versioned and consulted at routing time. An undeclared boundary is indistinguishable from coverage. |
| 30 | `PR-CLAE-DECLARE-THE-CLASS` | IX | 5 | an aggregate states its equivalence class. Aggregates across modes, pins, fidelities, dimensions or reference directions are not published. |
| 31 | `PR-CLAE-DECLARE-THE-LAYER` | XXIII | 5 | every rule records its enforcement layer. A rule without one is recorded at layer 5 by default, since that is what it is until a mechanism exists. |
| 32 | `PR-CLAE-DECLARE-THE-SAMPLE` | VI | 5 | sampled extraction declares its rule, records the unsampled region as undefined, and records who chose the sample and why. |
| 33 | `PR-CLAE-DECLARE-THE-UNCOVERED` | XII | 5 | dimensions without a complete Phase Zero chain are registered as measurement debt at the outset, not discovered later as an absence. |
| 34 | `PR-CLAE-DECLARED-ESCAPE` | X | 5 | every floor has a recorded route to ship below it via a deviation with a proven constraint and measured loss. Floors without one produce silent violations. |
| 35 | `PR-CLAE-DECLARED-HALTS` | XIX | 5 | every contract states conditions under which work stops, recognizable without judgment. |
| 36 | `PR-CLAE-DENSITY-EXAMINES-THE-PLAN` | XVIII | 5 | clustered deviations trigger review of the plan for that area, not of the people working in it. |
| 37 | `PR-CLAE-DERIVE-FROM-CONSEQUENCE` | XI | 5 | a floor records the concrete failure event, who bears the consequence, and the reasoning from that consequence to the minimum. A value without this chain is labelled imposed or provisional. |
| 38 | `PR-CLAE-DIRECTION-ON-REFERENCE` | IV | 5 | a historical-self reference is labelled regression-only at acquisition, and no surface may cite it for a ceiling claim. |
| 39 | `PR-CLAE-DISCOVER-DONT-DECLARE` | IV | 5 | where a reference set is required and no external instance exists, the set is discovered from what exists rather than enrolled by hand. |
| 40 | `PR-CLAE-DISPROVE-BEFORE-ADAPTING-A-TEST` | 29 | 5 | a test may be changed only after what was wrong with it is demonstrated and recorded. |
| 41 | `PR-CLAE-DISTANCE-NOT-COUNT` | VII | 5 | ranking effectiveness is reported as distance closed. Where only counts exist, the limitation is stated alongside them. |
| 42 | `PR-CLAE-DOMINANCE-FIRST` | VII | 5 | the ordering is derived mechanically by dominance over the declared factors. Preference is expressed only on the incomparable frontier. |
| 43 | `PR-CLAE-EFFECT-NOT-STRUCTURE` | VI | 5 | deltas are extracted at the level of effect. Structural comparison is admissible only where structure is itself the dimension. |
| 44 | `PR-CLAE-ELEVATE-ON-EVIDENCE` | 30 | 5 | the repair level is a finding about where the cause lives, claimed with an epistemic state; closure is refused at Level 1 when evidence places the cause higher. |
| 45 | `PR-CLAE-ENTRY-CONDITIONS` | XIX | 5 | Phase Zero demonstrated, loop validated, oracle boundary declared, instruments three-valued. Below any of these, autonomy is unbounded by construction and is recorded as such. |
| 46 | `PR-CLAE-ENVELOPE-NOT-DETERMINISM` | XII | 5 | capability four is satisfied by a characterized variation envelope. Phase Zero produces the noise floor as a recorded artifact. |
| 47 | `PR-CLAE-ESCAPE-FROM-INSIDE` | XXII | 5 | every escape is executable with what remains available inside the trap. Escapes requiring what the trap removed are recorded as prevention-only. |
| 48 | `PR-CLAE-EVALS-ARE-INSTRUMENTS` | XXIV | 5 | evals declare coverage, envelope and three-valued output, and are subject to every instrument rule. |
| 49 | `PR-CLAE-EVERY-RULE-HAS-AN-EVAL` | XXIII | 5 | a rule with no corresponding check in the eval set is advisory, and is recorded as advisory rather than as required. |
| 50 | `PR-CLAE-EVIDENCE-HAS-A-CONSUMER` | XIX | 5 | each piece of required evidence names what evaluates it. Unconsumed evidence is not part of the gate. |
| 51 | `PR-CLAE-EXECUTOR-REQUESTS-NEVER-GRANTS` | 27 | 5 | the executing party's output vocabulary does not contain a terminal verdict; it may submit a closure request only. |
| 52 | `PR-CLAE-FIVE-CONDITIONS` | IV | 5 | an object is cited as a reference only when externality, instantiation, observability, provenance and standing are all recorded. Any missing, it is a criterion and is named as one. |
| 53 | `PR-CLAE-FIVE-VERDICTS` | XX | 5 | closure is recorded as complete, complete with residual, complete with deviation, reduced, or halted. A binary status field is recorded as insufficient. |
| 54 | `PR-CLAE-FIX-OR-DELETE-NEVER-MUTE` | XV | 5 | an intermittent probe is either measuring an uncharacterized envelope, in which case characterize it, or is not a probe, in which case delete it. Muting is not available. |
| 55 | `PR-CLAE-FLOORS-ARE-DERIVED` | X | 5 | a floor states the domain reasoning that produced its minimum. An imported figure is a preference and is labelled as one. |
| 56 | `PR-CLAE-FOUR-CONDITIONS` | XIV | 5 | required dimension, no existing instrument found by actual search, cost below the unfalsifiable work prevented, and more than one use. All four before building. |
| 57 | `PR-CLAE-FOUR-MARKS` | XVI | 5 | a question is routed outward when it is value-laden, constituency-dependent, reference-absent by nature, or self-referential. Absent all four it is an instrument question and is answered by a procedure. |
| 58 | `PR-CLAE-FOUR-OUTCOMES` | VIII | 5 | every correction records closed, partial, null or adverse, with the expected magnitude alongside the observed one. |
| 59 | `PR-CLAE-FOUR-PART-DEVIATION` | XVIII | 5 | a deviation records the proven constraint, the original intent, the substitution and the measured loss. Missing any part, it is recorded as a compromise, shortcut or deferral by its correct name. |
| 60 | `PR-CLAE-FREEZE-BEFORE-EVIDENCE` | 28 | 5 | the artifact is frozen before the closure pack is assembled, and modification is prohibited until the first review completes. |
| 61 | `PR-CLAE-GATE-POINTS-NOT-GATES` | XXV | 5 | checks are consolidated into a small number of lifecycle gate points. A gate per rule is recorded as unimplemented doctrine. |
| 62 | `PR-CLAE-GATES-ARE-INSTRUMENTS` | XXV | 5 | every gate declares coverage, emits could-not-run, and carries a negative control demonstrated within its re-validation interval. |
| 63 | `PR-CLAE-HALT-IS-SUCCESS` | XIX | 5 | a halt on a declared condition is recorded as a contract outcome. Halt counts are read as evidence the conditions are live, never as a defect rate. |
| 64 | `PR-CLAE-IDENTITY-TRIPLE` | IX | 5 | residual identity is dimension, reference lineage and effect-level location, assigned at first observation and carried forward, never re-derived. |
| 65 | `PR-CLAE-INTENT-AT-ORIGIN` | XVIII | 5 | intent is recorded when the approach is chosen. Deviations are checked against the original intent, never against the immediately preceding plan. |
| 66 | `PR-CLAE-JOINT-PUBLICATION` | IX | 5 | a verdict is published together with the residual summary for the same artifact version, in the same emission. |
| 67 | `PR-CLAE-K-FROM-ATTRIBUTION` | VIII | 5 | k is set by the attribution the cycle requires; capacity is a ceiling on k, never its source. |
| 68 | `PR-CLAE-KNOWN-ANSWER-CASE` | XIII | 5 | every instrument has a case whose true value is established independently, run at construction and repeated when the instrument changes. Instruments without one have undetectable drift by construction. |
| 69 | `PR-CLAE-LABEL-EVIDENCE-BLOCK-FLOORS` | XXV | 5 | gates reading distance-derived evidence label; gates reading floors block. Blocking on evidence quality creates pressure that resolves against the gate. |
| 70 | `PR-CLAE-LABEL-THE-DERIVATION` | XXIII | 5 | each rule records whether it derives from an observed failure or from inference. The registry reports the ratio. |
| 71 | `PR-CLAE-LABELS-PROPAGATE` | XXV | 5 | a claim built on a labelled input inherits the label. A label that does not propagate is a note. |
| 72 | `PR-CLAE-LEDGER-EVERY-MATERIAL-CLAIM` | 29 | 5 | each material claim is registered with its epistemic state, evidence, provenance, the files not consulted, its consumer and its risk if false. |
| 73 | `PR-CLAE-LINEAGES-RETIRE` | XXI | 5 | each lineage carries a retirement condition naming the structural elimination of its root. Lineages are not checked in perpetuity. |
| 74 | `PR-CLAE-MARK-DONT-DELETE` | V | 5 | residuals against a retired reference are marked with the retirement, never removed. |
| 75 | `PR-CLAE-MEASURE-THE-NOISE-FLOOR` | VI | 5 | every instrument records its variance under repeated observation of one object. Residuals below it are recorded as indistinguishable, never as small. |
| 76 | `PR-CLAE-MODE-DECLARED` | II | 5 | every residual record states its measurement mode; *undefined* and *unmeasured by choice* are distinct dispositions and never substituted for each other. |
| 77 | `PR-CLAE-NAME-THE-CONSEQUENCE` | X | 5 | every floor names the failure class it prevents. A floor without one is not admitted to the set. |
| 78 | `PR-CLAE-NAME-THE-OPERATING-SUBSET` | XXIII | 5 | the registry states which rules actually operate. A doctrine that declares all of itself mandatory has declared none of itself enforceable. |
| 79 | `PR-CLAE-NARROWEST-FIRST` | XIV | 5 | build the narrowest instrument answering the blocking question. Generalize on the second use, never in anticipation. |
| 80 | `PR-CLAE-NEGATIVE-CONTROL` | XXIV | 5 | every eval carries a known-noncompliant case it is shown to flag, re-run when the eval or its environment changes. An eval without one is recorded as unverified. |
| 81 | `PR-CLAE-NEVER-SYNTHESIZE` | IV | 5 | a reference is never generated by the assessing system. Where no reference qualifies, the residual is undefined; §9 lists the legitimate alternatives. |
| 82 | `PR-CLAE-NO-ABDICATION` | XVI | 5 | a question the system has the standing, evidence and criterion to answer is answered, and the answer is recorded. Routing it outward is a cost, not a courtesy. |
| 83 | `PR-CLAE-NO-BLOCK-ON-DISTANCE` | II | 5 | residual magnitude informs prioritization and never gates admission. Enforcement belongs to floors and prohibitions. |
| 84 | `PR-CLAE-NO-CRITICAL-CLAIM-LEFT-INFERRED` | 29 | 5 | at closure a critical claim is verified, rejected, or carried explicitly as unknown with risk, containment and owner. |
| 85 | `PR-CLAE-NO-DEVIATION-AROUND-JUDGMENT` | XVIII | 5 | where the blocker is an unavailable oracle, the responses are block, reduce scope, or route properly. Substituting a self-made determination is self-certification. |
| 86 | `PR-CLAE-NO-FABRICATED-ESCAPE` | XXII | 5 | a trap with no valid escape is recorded as prevention-only, and its preventive rule is promoted in priority accordingly. |
| 87 | `PR-CLAE-NO-IMMUNIZATION-THAT-DEPENDS-ON-RECALL` | 30 | 5 | a protection whose operation requires someone to remember is recorded as doctrine, and the work is not closed as immunized. |
| 88 | `PR-CLAE-NO-ORPHAN-ARTIFACT` | 30 | 5 | every fix, rule and test carries its links; one that cannot name what it prevents is not admitted. |
| 89 | `PR-CLAE-NO-RANK-BELOW-L3` | VII | 5 | residuals below extraction level L3 are not ranked. They are recorded and their extraction improved first. |
| 90 | `PR-CLAE-NULL-PIVOT` | VIII | 5 | after a declared number of consecutive nulls on a dimension, correction stops and instrument investigation begins. |
| 91 | `PR-CLAE-OBJECTION-CARRIES-ITS-DISCHARGE` | 27 | 5 | every objection states what evidence would settle it; one that cannot is not recorded as an objection. |
| 92 | `PR-CLAE-OBSERVE-EXPOSURE` | VII | 5 | exposure is observed from actual use. An assumed exposure is labelled as such and the ranking beneath it inherits that status. |
| 93 | `PR-CLAE-ONE-CAUSE-ONE-PROTECTION` | 30 | 5 | the protection is selected from the cause, and a second is installed only when the cause has a second location. |
| 94 | `PR-CLAE-ONE-MEANING` | III | 5 | a term defined in this Part carries that meaning throughout the family. A Part needing a different concept names a new term and adds it here rather than narrowing an existing one locally. |
| 95 | `PR-CLAE-ONLY-THE-ARBITER-CLOSES-AN-OBJECTION` | 27 | 5 | the party objected to may repair or contest, never resolve. |
| 96 | `PR-CLAE-ORACLE-TRIAGE` | III | 5 | before routing a question to an oracle, establish that no procedure could answer it in principle. Mechanical questions are answered by instruments. |
| 97 | `PR-CLAE-PAIRED-OBSERVATION` | VI | 5 | artifact and reference are observed in the same act, with the same instrument, under the same conditions. A fresh-versus-stored comparison is labelled as such and its residuals carry that fidelity. |
| 98 | `PR-CLAE-PER-FAMILY-DISPOSITION` | 30 | 5 | each family is recorded searched-and-clean, searched-and- found, or not-searched-with-reason. |
| 99 | `PR-CLAE-PER-PASS-DISPOSITION` | 28 | 5 | every pass records ran-and-found, ran-and-clean, not- applicable, or not-run-with-reason. A single aggregate verdict is inadmissible. |
| 100 | `PR-CLAE-PERTURBATION-UNDER-ENVELOPE` | XIII | 5 | an instrument whose perturbation exceeds its envelope is recorded as measuring itself, and residuals from it are withdrawn. |
| 101 | `PR-CLAE-PHASE-ZERO-FIRST` | XII | 5 | the six capabilities are demonstrated on at least one dimension before the first feature. Work begun without it records the omission as declared measurement debt. |
| 102 | `PR-CLAE-PREFER-THE-LOWEST-LAYER` | XXIII | 5 | where a violation can be made unrepresentable, do that instead of forbidding it. Structural enforcement retires the rule rather than enforcing it. |
| 103 | `PR-CLAE-PREFLIGHT-SEVEN-SURFACES` | 29 | 5 | before modifying a capability, read owner, consumers, configuration, tests, manifest, historical decision and equivalent implementation. |
| 104 | `PR-CLAE-PREPARE-THE-DECISION-NOT-THE-PROBLEM` | 29 | 5 | an owner gate carries options, evidence and a recommendation; a gate presenting a problem has moved the work rather than the choice. |
| 105 | `PR-CLAE-PRESENT-ALTERNATIVES-EVENLY` | XVII | 5 | options are presented with comparable preparation, each with its consequence and its cost to reverse. |
| 106 | `PR-CLAE-PROBE-THREE-VALUED` | XV | 5 | a probe with absent preconditions reports could-not-run, never passed. |
| 107 | `PR-CLAE-PROBES-SURVIVE-REDESIGN` | XV | 5 | probes are not rewritten when intent changes and are not removed with the tests of a redesigned feature. They are historical records. |
| 108 | `PR-CLAE-PROMOTE-BY-DERIVATION` | 30 | 5 | a rule deriving from an established law is promoted immediately; a genuinely new mechanism enters as a candidate with a provisional detector and designed exceptions. |
| 109 | `PR-CLAE-PROMOTE-ON-IRRECOVERABILITY` | XXIII | 5 | a process rule becomes a hard rule when violation forecloses recovery, never because violation is frequent. |
| 110 | `PR-CLAE-PROMOTE-RECURRING-RESIDUALS` | X | 5 | a residual recurring on one dimension across many artifacts is reviewed as a floor candidate; per-domain minima are cheaper than per-artifact measurement. |
| 111 | `PR-CLAE-PROSECUTOR-IS-THREE-VALUED` | 27 | 5 | the role reports could-not-assess as a distinct outcome from no-objections. |
| 112 | `PR-CLAE-PROSECUTOR-READS-PRIMARY-EVIDENCE` | 27 | 5 | the challenge is run against artifacts, filesystem and runtime, never against the closure summary. |
| 113 | `PR-CLAE-PROVE-BEFORE-DEVIATING` | XVIII | 5 | a constraint proof states what was attempted, what was observed, and why the observation implies a property of the situation. A single failure is a defect, not a constraint. |
| 114 | `PR-CLAE-PROVE-THE-DETECTOR-ON-THE-PRE-REPAIR-STATE` | 30 | 5 | a new protection is run against the state that caused the incident before that state stops existing. |
| 115 | `PR-CLAE-PROVENANCE-BEFORE-REFERENCE` | III | 5 | the word *reference* may be used only where provenance and version are recorded. Absent either, the object is a criterion and is named as one. |
| 116 | `PR-CLAE-PUBLISH-THE-REBASELINE` | V | 5 | a pin update publishes the unchanged artifact's residual against both old and new pins, so subsequent changes decompose into work and bar. |
| 117 | `PR-CLAE-PUBLISH-THE-UNDEFINED` | IX | 5 | every summary states the dimensions it could not measure. A summary listing only measured dimensions is incomplete by construction. |
| 118 | `PR-CLAE-QUALITATIVE-FIRST` | XI | 5 | a floor is stated qualitatively wherever the intent permits. Numbers are used only for genuinely continuous properties where a line must be drawn. |
| 119 | `PR-CLAE-RATCHET-TURNS-BOTH-WAYS` | XIX | 5 | scope widening is an oracle decision; narrowing is triggered by impossible halts, out-of-scope residuals, or instruments found two-valued. |
| 120 | `PR-CLAE-REASK-ON-GROUNDS-ONLY` | XVII | 5 | re-asking requires material change, lapsed scope or changed constituency. Inconvenience is not a ground, and the re-ask rate per question class is tracked. |
| 121 | `PR-CLAE-RECORD-DISTANCE-OPENED` | VIII | 5 | every cycle records distance opened alongside distance closed, and reports the net. |
| 122 | `PR-CLAE-RECORD-INTENT-AT-ORIGIN` | XXI | 5 | original intent is recorded when an approach is chosen. L5 is the only lineage with an unrecoverable terminal, and this is its sole preventive. |
| 123 | `PR-CLAE-RECORD-SENSITIVITY` | XI | 5 | a numeric floor records what changes at plus or minus a fifth of its value. Where nothing does, the floor is stated as a range with a chosen operating point. |
| 124 | `PR-CLAE-RECORD-THE-CHOICE` | IV | 5 | provenance records which candidates were considered and why one was selected, not only the origin of the winner. |
| 125 | `PR-CLAE-RECORD-THE-FRONTIER` | VII | 5 | every frontier ordering records the incomparable set, the chosen order, the grounds, and whether each decision was observed or judged. |
| 126 | `PR-CLAE-RECORD-WHAT-WAS-SHOWN` | XVII | 5 | every oracle record carries the presentation alongside the answer. An answer without it has unbounded scope in practice. |
| 127 | `PR-CLAE-REDERIVE-ON-CONSEQUENCE-CHANGE` | XI | 5 | floors are re-derived when their consequence changes, not on a calendar. Periodic review catches accumulation; only the recorded consequence catches drift. |
| 128 | `PR-CLAE-REFREEZE-AFTER-REPAIR` | 29 | 5 | a repair returns the artifact to the frozen state and restarts the affected passes, not all passes. |
| 129 | `PR-CLAE-REGISTER-OR-DELETE` | XIV | 5 | at cycle end a built instrument is registered with its Part XIII declarations and known-answer case, or deleted. Leaving it unregistered is not an outcome. |
| 130 | `PR-CLAE-REMEASURE-IN-CYCLE` | VIII | 5 | re-measurement occurs inside the cycle. A correction not re-measured before the next is admitted is recorded as a hypothesis, not a closure. |
| 131 | `PR-CLAE-REOPEN-THE-MODEL-BEFORE-THE-SECOND-PATCH` | 29 | 5 | a second correction to the same region requires the causal model to be restated, not extended. |
| 132 | `PR-CLAE-REOPENING-IS-NOT-FAILURE` | XX | 5 | reopening on declared grounds is recorded as a closure outcome. A unit with no reopening path is recorded as abandoned. |
| 133 | `PR-CLAE-REPRODUCTION-HANDLE` | XII | 5 | every failure record carries what failed, where, with what input, and enough to re-run it. Records lacking the handle are notifications, not diagnoses. |
| 134 | `PR-CLAE-RETAIN-BEFORE-THRESHOLD` | II | 5 | where a gate computes a graded quantity before applying a threshold, that quantity is recorded. The threshold decides admissibility; it does not license discarding the measurement. |
| 135 | `PR-CLAE-RETIREMENT-AT-CREATION` | X | 5 | every floor states, when created, what would make it unnecessary. A floor whose retirement condition cannot be stated indicates an unidentified consequence. |
| 136 | `PR-CLAE-REVIEW-ROOTS-NOT-ENTRIES` | XXII | 5 | periodic review covers the five roots. The entry set is consulted on symptom and never enumerated. |
| 137 | `PR-CLAE-RUN-THE-CAUSE-TEST` | 30 | 5 | the ten institutional-cause questions are answered before a repair is accepted, and their answers are recorded. |
| 138 | `PR-CLAE-SCOPE-EVERY-ANSWER` | XVI | 5 | an oracle answer records its scope of validity. Scopeless answers are either re-purchased indefinitely or obeyed after their context has gone. |
| 139 | `PR-CLAE-SCOPE-IS-A-BOUNDARY` | XIX | 5 | work outside the contract's stated scope is not covered by it. Extension requires a contract revision, not a judgment that the work is related. |
| 140 | `PR-CLAE-SCOPE-THE-CONSTRAINT` | XVIII | 5 | every constraint records the environment, version and configuration it was proven under, and is re-examined when that scope lapses. |
| 141 | `PR-CLAE-SEARCH-BY-PROPERTY-NOT-NAME` | 28 | 5 | constitutional review searches for the governed properties, never for the governed names. |
| 142 | `PR-CLAE-SEARCH-THE-FAMILY-NOT-THE-NAME` | 30 | 5 | the sibling campaign is keyed by failure family; name-keyed searches are inadmissible as coverage. |
| 143 | `PR-CLAE-SEEING-BLOCKER-STOPS-WORK` | XIV | 5 | where the blocker is the ability to observe rather than the work itself, building the instrument is the work. Production past a seeing-blocker is recorded as unfalsifiable output. |
| 144 | `PR-CLAE-SELECT-BY-LEVEL` | XIII | 5 | instrument selection begins from the extraction level the downstream operation requires, not from what is available. |
| 145 | `PR-CLAE-SEPARATE-THE-OPERATIONAL-REGISTER` | XXII | 5 | the small, symptom-keyed, cost-bounded register of locally-recurring traps is maintained separately from the reference registry. |
| 146 | `PR-CLAE-SEPARATE-THE-THREE` | XXV | 5 | floor, gate and eval are distinguished in the record even when one mechanism performs all three. |
| 147 | `PR-CLAE-SHOW-THE-ARTIFACT` | XVII | 5 | the artifact is presented, not a description. Where only a summary can be shown, the answer's scope is bounded to the summary in the record. |
| 148 | `PR-CLAE-SHRINK-DONT-STACK` | XIV | 5 | an instrument needing its own instrument to validate is over-scoped and is narrowed until direct inspection of a known-answer case suffices. |
| 149 | `PR-CLAE-SIBLING-SEARCH-SAME-SESSION` | 30 | 5 | every confirmed defect triggers a family-keyed relatives search in the session that confirmed it. |
| 150 | `PR-CLAE-SPLIT-ACCOUNTING-FROM-ACCEPTANCE` | XX | 5 | the producer closes the accounting; acceptance is recorded separately by the constituency. The acceptance line stays empty until filled by someone with standing. |
| 151 | `PR-CLAE-STANDING-RECORDED` | XVI | 5 | every oracle answer records the answerer and the standing they held. Answers from outside the constituency are labelled proxy, not judgment. |
| 152 | `PR-CLAE-STARVATION-ESCAPE` | VII | 5 | a residual ranked without action for a declared number of cycles is promoted for one cycle or explicitly accepted with an owner. Indefinite ranking without action is not a disposition. |
| 153 | `PR-CLAE-STATE-THE-THRESHOLD-CHOICE` | XI | 5 | a floor records whether it sits at possibility, likelihood or irreversibility, and why. The placement is a risk posture and is stated as one. |
| 154 | `PR-CLAE-STOP-ON-CONDITION-NOT-FATIGUE` | 29 | 5 | the review ends on the seven stated conditions, including a further pass producing no material findings. |
| 155 | `PR-CLAE-SYMPTOM-KEYED-REGISTRY` | XXII | 5 | the registry's primary index is by observable symptom. Name and root listings are secondary. |
| 156 | `PR-CLAE-THIN-VERTICAL` | XII | 5 | Phase Zero proves all six capabilities end to end on one dimension rather than provisioning many dimensions partially. |
| 157 | `PR-CLAE-THREE-ARTIFACTS` | XV | 5 | a significant incident yields a fix, a test where intent needs asserting, and a probe. The probe is not satisfied by either of the others. |
| 158 | `PR-CLAE-THREE-DEBTS-SEPARATE` | IX | 5 | quality, measurement and instrument debt are reported separately and never summed. |
| 159 | `PR-CLAE-THREE-OBJECTS` | II | 5 | a report may use the word *distance* only when it names an artifact, a versioned external reference, and an observed difference. Two objects is a compliance report and is labelled as one. |
| 160 | `PR-CLAE-THREE-VALUED-OUTPUT` | XIII | 5 | every instrument returns a value, observed-nothing, or could-not-observe. Two-valued instruments are not admitted, and existing ones are widened at their boundary rather than governed by rules on their consumers. |
| 161 | `PR-CLAE-TIER-THE-SUITE` | XXIV | 5 | evals are assigned continuous, periodic or audit tiers. An untiered suite of this size does not run. |
| 162 | `PR-CLAE-TREAT-THE-EARLIEST-LINK` | XXI | 5 | on a recurring failure, identify its lineage and intervene at the earliest reachable link. Recurrence after a fix is evidence that a downstream link was treated. |
| 163 | `PR-CLAE-TREND-WITHIN-GENERATION` | V | 5 | a residual trend crossing a pin boundary is published only alongside the re-baseline delta. |
| 164 | `PR-CLAE-UNVERIFIED-DISPOSITION` | IX | 5 | a residual not re-measured within the declared interval is marked unverified. It is not reported as open at its last value. |
| 165 | `PR-CLAE-VALIDATE-THE-LOOP` | VIII | 5 | the first cycle against a new reference runs at k = 1 and issues a loop-validation verdict. A negative verdict halts correction and returns to extraction. |
| 166 | `PR-CLAE-VERIFY-BEFORE-RETIRING-A-FLOOR` | XXI | 5 | a floor's zero-violation record justifies retirement only alongside evidence its check executed. This breaks L6 at its fifth link. |
| 167 | `PR-CLAE-VERIFY-THE-CHECK` | X | 5 | a floor's zero-violation record is evidence only alongside proof its check executed. |
| 168 | `PR-CLAE-VERIFY-THE-CLAIM-NOT-THE-FIELD` | XXIV | 5 | an eval checks that a declaration corresponds to observed behaviour, not that a field is populated. |
| 169 | `PR-CLAE-WHOLE-DIMENSION` | VIII | 5 | re-measurement covers the whole dimension, not the corrected delta. Where sampled, the sampling rule is declared and the corrected delta is not the sample. |
| 170 | `PR-CLAE-WITHHOLD-THE-SUMMARY` | 28 | 5 | the challenge receives primary materials first; the executor's summary is read afterwards as one more claim to check. |
| 171 | `PR-CLAE-WRITE-THE-BLOCKER-FIRST` | XIV | 5 | the blocking question is recorded before construction begins, and the instrument's first use is answering it. |
| 172 | `PR-CLAE-ZERO-CARRIES-COVERAGE` | II | 5 | a reported residual of zero is accompanied by the observing instrument's declared detection scope, or it is recorded as undefined. |
| 173 | `PR-CLAE-ZERO-GATES-AUTONOMY` | XII | 5 | autonomous work requires a demonstrated Phase Zero on the dimensions it will affect. Below it, autonomy is unbounded by construction. |
| 174 | `PR-CLAE-ZERO-LOSS-REVISES-THE-PLAN` | XVIII | 5 | a substitution with no loss is adopted as an improvement and the plan updated, or its loss is measured. It is not recorded as a costless deviation. |

## 4. Completeness and measurement debt

| Field (Part XXIII §3) | Derivable | Note |
|---|---|---|
| Name · Statement | ✅ all 174 | the seed |
| Origin (Part) | ✅ all 174 | the seeding Part; the *observed failure* half is not carried by the seed |
| Enforcement layer | ◐ by default | layer 5 per the Part's declared default, not per-rule measurement |
| Root | ❌ none | no seed carries a root assignment |
| Eval · Retirement condition · Escape route | ❌ none | no seed carries them |

> **Measurement debt.** Three of Part XXIII's own six rules for this registry are unsatisfied by it: `PR-CLAE-LABEL-THE-DERIVATION` (per-entry derivation kind is not in any seed — §6 of that Part states only the aggregate, *"largely deductive"*), `PR-CLAE-EVERY-RULE-HAS-AN-EVAL` (no seed names its eval), and `PR-CLAE-NAME-THE-OPERATING-SUBSET` (the operating subset is estimated in §5, never enumerated). Recorded, not filled.

Part XXIII §16 adds the one this registry can neither settle nor conceal: semantic overlap among the entries is **unmeasured**, and the Part's own honest expectation is that *"the effective rule count is materially lower"*. Name-distinctness is 174 of 141; behavioural distinctness is unknown.
