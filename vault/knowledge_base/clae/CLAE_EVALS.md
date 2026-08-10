---
title: "CLAE — Evals Registry"
family: clae
type: registry
kind: extract
sources: [Parts I–XXV (seeds), Part XXIV (schema, tiering, controls)]
derivation: mechanical extraction from the sealed Parts; no entry carries information absent from its source
status: POPULATED
date: 2026-08-10
---

# CLAE — Evals Registry

> **What this file is.** Part XXVI §5 defines the twelve companion artifacts as *"extracts for retrieval convenience"* — the schemas, consolidations and measured counts live in the Parts. This file locates entries; it does not restate, resolve or extend them.
> **Reading rule.** Every row cites the Part that seeded it. Where a row's source is ambiguous, the ambiguity is transcribed rather than resolved.

**Schema:** Part XXIV §3 (eight fields). **Central requirement:** Part XXIV §5 — *"an eval that has never failed is indistinguishable from an eval that cannot fail"*, so every eval needs a negative control.

## 1. Census

| Scope | Measured | Part XXIV asserts |
|---|---|---|
| Parts I–XXIII | **119** | *"roughly one hundred and ten"* (§1) |
| Parts I–XXV (family total) | **155** | — |

Part XXIV hedges its number (*roughly*), and the measured figure sits above the hedge. §8 then reasons from a firm *"One hundred and ten evals is a programme, not a check"*. The argument is unaffected by the correction — 119 is more of a programme than 110 — but the operative count is 119.

## 2. The set worth running first

Part XXIV §8 selects five by cost against what they reveal. This is the operating subset; the remaining 150 are the programme.

1. **Arity probe** — can each instrument report could-not-observe? Expected to fail nearly everywhere and it invalidates every clean result beneath it.
2. **Count-versus-distance plot** — the fingerprint of fixability bias, two lines and no machinery.
3. **Negative-control census** — which evals have ever been shown to fail? Cheapest way to find out which checks are decorative.
4. **Undefined-publication probe** — do quality summaries state what they could not measure?
5. **Layer census** — what fraction of the rule set has any mechanism at all?

### Tiers

Part XXIV §8: **Continuous** (cheap, per-cycle, automatable) · **Periodic** (moderate, scheduled) · **Audit** (expensive, rare, deliberate). Tier is assigned per eval in the Part's prose for a named handful only; it is not carried by the seeds and is therefore absent from §3 below.

## 3. The entries

| # | Eval | Part | Seed statement |
|---|---|---|---|
| 1 | Internal-Bar Detection Eval | I | Present an artifact that passes every existing gate and is demonstrably inferior to an available external instance. The stack currently reports success; a CLAE-equipped stack must report the residual. Failure to distinguish these two cases is the defect, measured directly. |
| 2 | Threshold Staleness Eval | I | For each quality threshold, measure elapsed time since last revision against domain movement in the same period. Surfaces Signature 1. |
| 3 | Pass-Rate Information Eval | I | For each gate, measure pass rate. A rate approaching unity is flagged for resolution review. Surfaces Signature 2. |
| 4 | Category Assignment Eval | I | For a mixed set of criteria, verify correct classification into prohibition, safety floor, invariant or aspiration. Guards against the §6 error in both directions. |
| 5 | Saturation probe | II | Present a surface with an artifact already at its maximum reported value, then supply a demonstrably superior external instance. The value must move. If it does not, the surface is stage two and its reports are relabelled. |
| 6 | Retention probe | II | For each gate in the stack, compare the quantity present in the run output against the quantity present in the durable record. Any gate whose magnitude vanishes at the threshold is a retention candidate. |
| 7 | Zero-coverage probe | II | For every reported residual of zero, verify a coverage declaration accompanies it. Zeros without coverage are reclassified as undefined. |
| 8 | Mode-integrity probe | II | Sample residual records and verify that each *undefined* entry genuinely lacks a reference, rather than reflecting a skipped measurement. |
| 9 | Collapse probe | II | Where a single quality figure is published, verify that either it is genuinely one-dimensional or the weighting is declared and auditable. |
| 10 | Drift probe | III | Sample the family's own artifacts for each banned usage in §9. The family violating its own ontology is the earliest available signal of vocabulary drift. |
| 11 | Provenance probe | III | For every use of *reference*, verify a recorded provenance and version. Uses without either are reclassified as criteria and the surrounding claims re-read. |
| 12 | Boundary probe | III | For each pair in §8, construct one case sitting on the boundary and confirm the stated test resolves it. A test that cannot resolve its own boundary case is not a usable test. |
| 13 | Write-access probe | IV | For every cited reference, determine who can modify it. Any writable by the assessing party is reclassified as a criterion and dependent claims re-read. |
| 14 | Direction probe | IV | For every historical-self reference, verify no consuming surface makes a ceiling claim from it. |
| 15 | Acquisition-trail probe | IV | For every reference, require an acquisition record with a date and method. References without one are candidate synthesized ideals. |
| 16 | Dimension-coverage probe | IV | Count distinct references against distinct measured dimensions. A ratio far below one indicates the single-reference stretch. |
| 17 | Bound-availability probe | IV | For each dimension currently reported as undefined, ask whether a formal bound or a discoverable set exists. This probe converts undefined residuals into measurable ones and is the cheapest expansion available to the family. |
| 18 | Record-completeness probe | V | For each reference in use, verify all ten acquisition fields. Missing standing arguments and missing horizons are the two that predict later failure. |
| 19 | Pin-citation probe | V | Sample residuals and verify each cites a pin generation. Uncited residuals are uninterpretable and are relabelled as such. |
| 20 | Decomposition probe | V | For each pin update, verify a re-baseline delta was published. Its absence means every subsequent trend conflates work with bar movement. |
| 21 | Horizon-expiry probe | V | List references past their declared horizon with no re-examination event. This probe is cheap, runs unattended, and catches the §7 staleness failure before it flatters a report. |
| 22 | Fidelity-propagation probe | V | Verify residuals inherit the fidelity of the reference beneath them, and that no residual is reported at higher fidelity than its acquisition supports. |
| 23 | Commensurability probe | VI | For each extraction in use, verify artifact and reference are observed by one instrument under one set of conditions. Any fresh-versus-stored pair is relabelled. |
| 24 | Noise-floor probe | VI | For each instrument, observe one unchanged object repeatedly and record the spread. Any residual currently reported below that spread is reclassified as indistinguishable. This probe is cheap and is expected to invalidate a meaningful share of existing residuals, which is the point. |
| 25 | Level-declaration probe | VI | Verify every residual carries an extraction level, and that no ranking consumes residuals below L3. |
| 26 | Projection-argument probe | VI | For each projection-based extraction, require the preservation argument. Those without one are reclassified L0 and their residuals withdrawn. |
| 27 | Structure-versus-effect probe | VI | Sample delta lists and classify each entry as structural or effect-level. A list dominated by structural entries indicates the §6 trap. |
| 28 | Count-versus-distance probe | VII | Over several cycles, plot open residual count against total distance. Falling count with flat distance is fixability bias, and this probe is the cheapest high-value check in the family. |
| 29 | Traversal-correlation probe | VII | Compare work order against the extraction instrument's traversal order. Strong correlation indicates discovery-order ranking. |
| 30 | Frontier-completeness probe | VII | Verify every frontier decision carries grounds and an observed-or-judged label. Frontiers that are entirely judged with no grounds are preference lists. |
| 31 | Starvation probe | VII | List residuals present in the top-k for many cycles and never in the worked set. Their existence is expected; their invisibility is the failure. |
| 32 | Exposure-provenance probe | VII | For each exposure value, determine whether it was observed or assumed. Assumed exposure reproduces the author's model of usage inside the loop. |
| 33 | Outcome-distribution probe | VIII | Over a programme's history, count closed, partial, null and adverse. A distribution of nearly all closed indicates targeted re-measurement rather than an excellent model. |
| 34 | Net-versus-gross probe | VIII | Compare summed distance closed against the change in total distance. A large divergence is unrecorded distance opened. |
| 35 | Recurrence probe | VIII | Identify residual identifiers appearing in multiple cycles. Their presence with adverse outcomes between is oscillation and indicates coupling. |
| 36 | First-cycle probe | VIII | For each reference in use, verify a loop-validation verdict exists. Absent one, the loop beneath it was never tested and its outputs are unwarranted. |
| 37 | Null-response probe | VIII | For each null outcome, verify whether the next action was instrument investigation or more correction. The latter is the §7 failure and is cheap to detect. |
| 38 | Identity-persistence probe | IX | Rename, relocate or restructure a region containing a known residual and re-run. The identity must survive. If it does not, every trend in the ledger is unreliable and this is the cheapest way to find out. |
| 39 | Undefined-publication probe | IX | Sample published summaries and verify each names its unmeasured dimensions. Absence is the §5 failure in its published form. |
| 40 | Debt-separation probe | IX | Verify the three debts are reported as three numbers. |
| 41 | Staleness probe | IX | List entries older than the re-measurement interval and verify each is marked unverified rather than reported as open. |
| 42 | Aggregate-legitimacy probe | IX | For each published aggregate, verify a declared equivalence class and confirm no regression-reference residual is summed with a ceiling-reference one. |
| 43 | Reader probe | IX | For each ledger field, name the consumer that reads it. Fields with no reader are storage, and fields consumers need that do not exist are the actual gap. |
| 44 | Six-shape probe | X | For a sample of shipped artifacts, check each of §4's shapes directly. This is the family's most direct test of the gap in §9 and needs no reference at all. |
| 45 | Test-mirror probe | X | Compare each artifact's test cases against its implemented branches. Near- exact correspondence indicates tests that inherited the author's conception rather than the domain's requirements. |
| 46 | Check-execution probe | X | For every floor, confirm its check actually ran on the last several artifacts. Zero violations without execution evidence is a decorative floor. |
| 47 | Escape-usage probe | X | Count deviations recorded against each floor. A floor with many violations and no deviations has an unusable escape route and is being bypassed silently. |
| 48 | Retirement-condition probe | X | Verify every floor states one. Those without are the seeds of the ritual accumulation in §6. |
| 49 | Floor economics probe | X | For each floor, compare satisfaction cost against the expected cost of the failure it prevents. Net-negative floors are candidates for retirement independent of their soundness. |
| 50 | Derivation-presence probe | XI | For every floor in force, require the recorded consequence chain. Floors without one are relabelled imposed or provisional, which is a labelling change rather than a removal, and is cheap. |
| 51 | Sensitivity probe | XI | For every numeric floor, ask what changes at plus or minus a fifth. Silence identifies decoration and is the fastest discriminator in this Part. |
| 52 | Threshold-placement probe | XI | For every floor, determine which of the three thresholds it sits at. Floors whose authors cannot say have a risk posture nobody chose. |
| 53 | Qualitative-restatement probe | XI | For each numeric floor, attempt a qualitative restatement of the same intent. Success indicates the number was a numeric reflex and the restatement is strictly more portable. |
| 54 | Travelling-threshold probe | XI | Search for identical values across unrelated domains in the same organization. Repetition of a specific figure indicates propagation rather than derivation. |
| 55 | Chain-completeness probe | XII | For each dimension claimed measurable, walk all six capabilities and identify the first that breaks. Dimensions breaking before capability five produce no comparable measurements regardless of their instrumentation. |
| 56 | Envelope-existence probe | XII | For each instrument, look for a recorded variation envelope. Absence means every residual from it is uninterpretable at small magnitudes. |
| 57 | Reproduction-handle probe | XII | Sample failure records and attempt to re-run each from the record alone. The success rate is the real value of capability six. |
| 58 | Retrofit-history probe | XII | Examine when each observable was added relative to the incident that needed it. A consistent after-the-incident pattern quantifies §2's cost in undiagnosable events. |
| 59 | Debt-register probe | XII | Compare the dimensions a project makes quality claims about against the dimensions with a Phase Zero chain. The difference is measurement debt, and whether it was declared or discovered is the finding. |
| 60 | Arity probe | XIII | For every instrument, determine whether it can express could-not-observe. This is the cheapest high-value check in the family and is expected to fail nearly everywhere. |
| 61 | Silent-green probe | XIII | Disable an instrument's preconditions deliberately and observe its output. If it reports clean, it is two-valued and its entire history of clean results is uninterpretable. |
| 62 | Chain-coverage probe | XIII | For each instrument chain, compute the intersected coverage and compare it against what consumers believe the chain detects. |
| 63 | Perturbation probe | XIII | For each perturbing instrument, compare its measured perturbation against its envelope. |
| 64 | Calibration probe | XIII | For each instrument, look for a known-answer case and the date it last ran. Instruments without one, or with a stale one, have unbounded drift. |
| 65 | Blocker-provenance probe | XIV | For each instrument built in the last period, look for the blocking question recorded before construction. Absence indicates substitution or yak-shave. |
| 66 | Search-first probe | XIV | For each new instrument, determine whether an existing capture already held the observation. This probe is cheap and is expected to find several. |
| 67 | Second-use probe | XIV | Count instruments used exactly once. Each was a manual observation that became an artifact, and each is a register-or-delete decision that was never made. |
| 68 | Register-completeness probe | XIV | Compare instruments in active use against the instrument register. Unregistered veterans have no coverage declaration, so every zero they have ever reported is uninterpretable. |
| 69 | Accounting probe | XIV | Examine cycles reporting zero distance closed and determine how many repaid instrument debt. A high proportion means the accounting is teaching the wrong lesson. |
| 70 | Conversion-latency probe | XV | For each significant incident, measure the interval between the incident and its probe. Intervals beyond the incident's own working session indicate reconstruction from memory. |
| 71 | Rule-without-check probe | XV | For each recorded rule with an origin incident, determine whether an executable check exists. The ratio quantifies §11's finding and is directly actionable. |
| 72 | Precondition-drift probe | XV | Run the probe suite under deliberately absent preconditions. Any probe reporting pass is two-valued and its green history is uninterpretable. |
| 73 | Mute-census probe | XV | Count disabled probes. Any non-zero count is a standing erosion of the suite's authority and each is a fix-or-delete decision that was never made. |
| 74 | Survival probe | XV | For features rewritten in the last period, check whether their probes survived the rewrite. |
| 75 | Boundary-existence probe | XVI | Look for the declared set. Its absence is the finding, and it is the most common state. |
| 76 | Judgment-provenance probe | XVI | For a sample of quality claims, identify who answered each judgment in the chain. Claims with no oracle anywhere in their history are self-certified. |
| 77 | Mark-classification probe | XVI | Take the questions currently routed outward and classify each against the four marks. Those matching none are exhausting the channel and should be instrumented. |
| 78 | Constituency probe | XVI | For each oracle answer, compare the answerer against the constituency the question concerned. Mismatches without a proxy label are fabricated standing. |
| 79 | Boundary-movement probe | XVI | Examine the declared set's history. Movement only inward, following objections, is §5's drift. |
| 80 | Answer-age probe | XVI | List oracle answers whose scope of validity has lapsed and which still govern. |
| 81 | Window probe | XVII | For each routed question, compare its date against the point the decision became expensive to reverse. Questions routed after it were ratifications. |
| 82 | Answer-type census | XVII | Classify recorded answers by type. An all-verdict distribution means the channel's load can only grow. |
| 83 | Presentation-completeness probe | XVII | Check each record for §3's six items, especially the cost to change later. Its absence is the most consequential omission. |
| 84 | Re-ask-rate probe | XVII | Count returns per question class and diagnose each against §7's three causes. |
| 85 | Scope-stretch probe | XVII | For each answer in current use, compare what it is being applied to against what was shown when it was given. |
| 86 | Unfavourable-rate probe | XVII | Compute the proportion of unfavourable answers. A rate near zero indicates ratification or leading framing rather than good work. |
| 87 | Ledger-population probe | XVIII | Count deviations over a period of substantive work. Zero or near-zero warrants investigation of the recording, not congratulation. |
| 88 | Constraint-evidence probe | XVIII | For each recorded constraint, count the attempts cited. Single- attempt constraints are below the bar and their deviations are deferrals. |
| 89 | Zero-loss census | XVIII | Count deviations recording no loss. Each is a plan-revision candidate or an unmeasured cost, and both are actionable. |
| 90 | Chain-integrity probe | XVIII | For a sample of areas, read the full deviation chain and ask whether the current behaviour is derivable from the original intent. Composition drift is invisible in any single record and obvious across the chain. |
| 91 | Scope-lapse probe | XVIII | List deviations whose constraint scope names an environment or version no longer in use. Each is a standing deviation still charging its loss. |
| 92 | Density probe | XVIII | Plot deviations by area. Clusters locate wrong plans. |
| 93 | Contract-locatability probe | XIX | Ask for the accepted standard as a single artifact. Failure to produce one is the most common finding and the most consequential. |
| 94 | Entry-condition probe | XIX | For each autonomous run, verify all four of §5. The instrument arity check is expected to fail nearly everywhere, per Part XIII §11. |
| 95 | Halt-census probe | XIX | Count halts and their triggering conditions over a run. Zero halts over substantial work warrants examining whether the conditions can fire at all. |
| 96 | Scope-conformance probe | XIX | Compare work products against the contract's stated scope. Products outside it were produced under no gate. |
| 97 | Evidence-consumer probe | XIX | For each evidence artifact, name its consumer. Unnamed artifacts are volume. |
| 98 | Ratchet-direction probe | XIX | Examine the scope history for narrowing events. A monotone history means invalidated evidence has never been acted on. |
| 99 | Verdict-vocabulary probe | XX | Inspect closure surfaces for available states. Binary fields guarantee the common case is misreported, and this is the cheapest finding in the Part. |
| 100 | Residual-in-closure probe | XX | For each closure statement, check for remaining-gap and undefined-dimension sections. |
| 101 | Signature probe | XX | Compare the accounting signatory against the acceptance signatory. Identity indicates self-acceptance. |
| 102 | Horizon probe | XX | List closures past their validity horizon with no re-examination. Each should read as unverified and probably reads as closed. |
| 103 | Aggregate probe | XX | For each closed phase, verify an aggregate measurement exists at phase scale rather than a roll-up of unit closures. |
| 104 | Reopening probe | XX | Count reopenings and their grounds. Zero over a long period indicates reopening is read as failure. |
| 105 | Lineage-position probe | XXI | For each of the six, determine which links are currently in place. The output is a position, not a pass or fail, and it is the only form in which this Part is actionable. |
| 106 | Recurrence-lineage probe | XXI | For each failure that has recurred after a fix, identify which link the fix addressed. Downstream fixes predict recurrence and this makes the prediction checkable. |
| 107 | Compound probe | XXI | Test specifically for L1 with L6 — internal criteria plus two-valued verification. This compound is invisible to any single-dimension check. |
| 108 | Point-of-no-return probe | XXI | For lineages with links in place, determine the distance to the point of no return. L5's proximity is the highest-urgency measurement in the family. |
| 109 | Root-census probe | XXI | For each of the five roots, count the surfaces exhibiting it. Roots are where interventions have the widest effect. |
| 110 | Symptom-entry probe | XXII | Give a reader one of §7's observations and no trap names, and measure whether they reach the relevant entry. This is the registry's actual usability test. |
| 111 | Escape-validity probe | XXII | For each escape, verify it is executable given the trap's own conditions. Escapes assuming the healthy state are the most common defect in trap registries. |
| 112 | Prevention-only census | XXII | Confirm the four §5 entries are marked, and check for others whose escape silently assumes destroyed evidence. |
| 113 | Provenance probe | XXII | For each entry, identify the observed failure that produced it. Hypothetical entries are dilution. |
| 114 | Consultation probe | XXII | Count registry consultations and their outcomes over a period. A registry never consulted mid-incident is a reference work and should be labelled one rather than expected to operate. |
| 115 | Layer-census probe | XXIII | Assign every rule a layer and report the distribution. The layer-5 proportion is the fraction of the doctrine that depends on recall. |
| 116 | Citation probe | XXIII | Over a period, count which rules were actually invoked in decisions. The cited set is the operating doctrine; the gap between it and the archive is the reference work. |
| 117 | Derivation-ratio probe | XXIII | Count observed versus inferred origins. A high inferred ratio means the archive is largely hypothesis and should say so. |
| 118 | Layer-1 opportunity probe | XXIII | For each rule, ask whether its violation could be made unrepresentable. Positives are the cheapest permanent improvements available. |
| 119 | Overlap probe | XXIII | Cluster rules by the behaviour they require rather than by name, and count clusters. This is the check that §1's distinct-name count could not perform. |
| 120 | Negative-control census | XXIV | For every eval, look for a known-noncompliant case and the date it last flagged. This is the cheapest way to find decorative checks and is expected to find many. |
| 121 | Adversarial-path probe | XXIV | For each eval, attempt the cheapest satisfaction that does not comply. Success identifies an eval certifying the wrong thing. |
| 122 | Eval-arity probe | XXIV | Verify each eval can report could-not-run. An eval suite is the last place a two-valued instrument should be, and is a common place to find one. |
| 123 | Red-response probe | XXIV | For evals that have fired, check whether anything changed. Firing without response is muting without the record. |
| 124 | Level-versus-verdict probe | XXIV | Examine the family's self-reports for levels. Compliance-only self-assessment is the failure this Part exists to prevent. |
| 125 | Trigger-wiring probe | XXV | For each specified gate point, verify something fires there. Doctrine-only gates are the most common finding in any consolidated set. |
| 126 | Propagation probe | XXV | Label an input deliberately and trace whether downstream claims inherit it. Non-propagating labels are notes with no force. |
| 127 | Gate-arity probe | XXV | Confirm each gate point emits could-not-run. |
| 128 | Gate negative control | XXV | Present each gate point with a deliberately failing artifact and confirm it fires — the same discipline Part XXIV §9 applied to this build's own gate. |
| 129 | Threshold-drift probe | XXV | For blocking gates, examine whether their thresholds have moved downward. Downward drift is the negotiated-block signature. |
| 130 | Negative-control acquittal probe | 27 | Submit a known-defective closure pack. A prosecutor that approves it has been shown to be decorative, and every prior approval is void. |
| 131 | Anchor-citation census | 27 | Over a period, what fraction of objections cite one of the three anchors? The uncited fraction predicts the role's disablement. |
| 132 | Summary-dependence probe | 27 | Withhold the executor's summary and re-run the challenge. A materially different objection set means the prosecutor was auditing the narrative. |
| 133 | Arity probe | 27 | Deny the prosecutor runtime access and observe the output. If it reports no-objections rather than could-not-assess, it is two-valued. |
| 134 | State-skip probe | 27 | Walk closure traces and count transitions into `DONE_VERIFIED` whose predecessor was not `CLOSURE_CANDIDATE`. |
| 135 | Alias-collision probe | 27 | Read certificates and check that each verdict maps to exactly one Part XX verdict, and that `Reduced` closures are not being recorded as `PARTIAL_VERIFIED`. |
| 136 | Freeze-integrity probe | 28 | Hash the artifact at `CHANGE_FROZEN` and again at verdict. Any difference means the review's subject changed underneath it. |
| 137 | Anchoring probe | 28 | Run the challenge twice, once with the summary and once without, and compare the finding sets. A large difference measures the anchoring the source asserts without measuring. |
| 138 | Vacuous-negative census | 28 | Classify every negative test as route-enumerated or non-observation. The second class is the estate's false confidence, counted. |
| 139 | Route-space probe | 28 | For one withdrawal, independently enumerate the routes and compare against the closure's list. The delta is the negative pass's real coverage. |
| 140 | Rename probe | 28 | Rename a governed mechanism and re-run Pass F. If it is no longer found, the review is name-keyed. |
| 141 | Selection-audit probe | 28 | Over a period, count closures where an unconditional pass was recorded not-run. Each is a gate that did not fire. |
| 142 | Hedge-to-assertion probe | 29 | Grep session records for hedged verbs and check whether the corresponding claim carries a non-`VERIFIED` state in the ledger. Mismatches are precursor 1. |
| 143 | Ledger-completeness probe | 29 | Sample material claims from a closure and check how many appear in the ledger. The unlisted fraction is the ledger's real coverage. |
| 144 | Circular-oracle probe | 29 | For each test, ask what it would take for it to fail. Tests with no answer share the implementation's assumption. |
| 145 | Re-freeze probe | 29 | For each in-session repair, compare the artifact hash at repair time and at the restarted review. A difference means the review ran against a moving artifact. |
| 146 | Exhaustion-profile probe | 29 | Split each session into quarters and count negative tests, log reads and sibling searches per quarter. A monotone decline is precursor 9, measured. |
| 147 | Owner-gate necessity probe | 29 | Classify past owner gates as agent-decidable or not. The agent-decidable fraction is the oracle dilution rate. |
| 148 | Stop-condition audit | 29 | For closed reviews, check that condition 7 was evaluated rather than assumed. |
| 149 | Elevation-level audit | 30 | For closed incidents, compare the level treated against the level the ten questions indicate. Systematic under-elevation is the recurrence engine. |
| 150 | Recurrence probe | 30 | Count incidents whose family matches an earlier closed incident. A non-zero rate measures under-elevation directly, without opinion. |
| 151 | Sibling-coverage probe | 30 | For one confirmed defect, independently run the family search and compare against the campaign's disposition. The delta is the campaign's real coverage. |
| 152 | Detector-firing census | 30 | For every installed protection, has it fired once, including on the incident that motivated it? Never-fired protections are the estate's decorative surface, counted. |
| 153 | Orphan census | 30 | Sample fixes, rules and tests and check their required links. The unlinked fraction is the set that can never be retired. |
| 154 | Promotion-path audit | 30 | For promoted rules, was the path immediate or candidate, and does the recorded derivation support it? Immediate promotions with no parent law are unbounded rules. |
| 155 | Question-10 probe | 30 | For each closed immunization, ask whether its operation depends on recall. A `yes` rate above zero measures how much of the estate's protection is doctrine. |

## 4. Completeness and measurement debt

| Field (Part XXIV §3) | Derivable | Note |
|---|---|---|
| Objective | ◐ partial | the seed states what it probes, not always which rule it verifies |
| Setup · Pass/fail criteria | ❌ none | no seed states them separately, which is the specific requirement of §3.3 |
| Adversarial variant · False-positive risk · Cost and tier · Negative control · Output arity | ❌ none | no seed carries them |

> **Measurement debt: 0 of 155 eval seeds satisfy the eight-field record schema.** The gap that matters most is the negative control, because Part XXIV §5 makes it the difference between an eval and a decoration. Part XXIV §9 ran exactly one negative control — against this build's own gate — and that remains the only eval in the family with a demonstrated ability to fail.
