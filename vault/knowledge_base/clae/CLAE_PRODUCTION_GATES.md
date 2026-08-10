---
title: "CLAE — Production Gates Registry"
family: clae
type: registry
kind: extract
sources: [Parts I–XXIV (seeds), Part XXV (contract, consolidation, block-or-label)]
derivation: mechanical extraction from the sealed Parts; no entry carries information absent from its source
status: POPULATED
date: 2026-08-10
---

# CLAE — Production Gates Registry

> **What this file is.** Part XXVI §5 defines the twelve companion artifacts as *"extracts for retrieval convenience"* — the schemas, consolidations and measured counts live in the Parts. This file locates entries; it does not restate, resolve or extend them.
> **Reading rule.** Every row cites the Part that seeded it. Where a row's source is ambiguous, the ambiguity is transcribed rather than resolved.

**Contract:** Part XXV §3 (six fields). **Failure action doctrine:** Part XXV §5 — *"Distance informs. Floors enforce."*

## 1. Census, and three numbers that disagree

| Quantity | Measured |
|---|---|
| Gate seeds in the corpus | **23** (22 named + 1 stated as prose, Part I §13) |
| Checks enumerated by Part XXV §4's four gate points | **20** |
| Part XXV §1 and §4 assert | **nineteen** |

Nineteen is exact for one scope: the gates seeded by Parts **II–XXI**. Part XXV §1 labels the count *"seeded across Parts I through XXIV"*, which contains 23 — the three registry gates of Parts XXII, XXIII and XXIV, plus Part I's prose gate, sit outside the nineteen while inside the stated range. This is the same label-versus-scope gap that `CLAE_PROCESS_RULES.md` §1 records for Part XXIII, arrived at independently.

## 2. The four gate points

Part XXV §4 groups the seeded gates by *when they fire*. Transcribed:

**G1 — Measurement Admission** — Fires before a residual enters the ledger. Consumes the reference integrity, provenance integrity, extraction integrity and instrument integrity checks. Answers: *is this number interpretable?*

**G2 — Artifact Admission** — Fires before an artifact ships. Consumes the underbuild floor check, the floor derivation check and the deviation integrity check. Answers: *is this a real implementation, and is what it lacks recorded?*

**G3 — Closure** — Fires before a unit is declared closed. Consumes residual visibility, phase closure, oracle boundary, ranking integrity and correction cycle. Answers: *does the closing statement say what remains?*

**G4 — Autonomy Entry** — Fires before autonomous work begins. Consumes Phase Zero, autonomy entry, toolsmith, incident conversion, eval integrity, trap registry, rule registry and lineage position. Answers: *can this system's output be checked at all?*

Part XXV §5 assigns the failure action: **G2 blocks** (its subject is admissibility, and floors enforce); **G1, G3 and G4 label** (their subject is the interpretability of evidence, and *"blocking on incomplete evidence stops work that may be entirely sound"*).

## 3. Seeded gates, mapped to their point

| Gate | Part | Point | Seed statement |
|---|---|---|---|
| Residual Visibility Gate | II | G3 | A phase, a build or an autonomous mission may not be reported as closed while any gate on its path discarded a graded quantity it had already computed. Closure requires that every such quantity is present in the durable record with its measurement mode and, where zero, its coverage declaration. Passing gates do not satisfy this; the presence of the residuals does. |
| Reference Integrity Gate | IV | G1 | No surface may publish a distance claim unless the cited reference carries a recorded class, an acquisition record with date and method, a standing argument, and a direction label. A historical-self reference without a regression-only label, or any reference writable by the publishing party, fails the gate — and failing it downgrades the claim to a criterion report rather than blocking the work. |
| Provenance Integrity Gate | V | G1 | A distance claim may be published only when its reference cites a pin generation, an acquisition record with date, method and fidelity, and a horizon that has not expired without re-examination. A pin updated since the last published claim additionally requires the re-baseline delta. Failure downgrades the claim to an uninterpretable measurement rather than blocking the work, consistent with Part |
| Extraction Integrity Gate | VI | G1 | A residual may enter the ledger only when it records its extraction level, its instrument, that instrument's noise floor, whether the observation was paired, and — if sampled — its sampling rule and unsampled region. A residual below the recorded noise floor enters as indistinguishable. A residual from an unargued projection does not enter at all, since its level is L0 and L0 supports no claim. |
| Ranking Integrity Gate | VII | G3 | A correction cycle may consume a ranking only when every ranked residual carries extraction level L3 or above, the dominance order was computed before any preference was applied, the frontier record exists with grounds and observed-or-judged labels, and the previous cycle published distance closed rather than count closed. A ranking failing any of these is consumed as an unordered set, which is ho |
| Correction Cycle Gate | VIII | G3 | A cycle may be recorded as complete only when re-measurement covered the whole dimension under paired observation against the same pin generation, every admitted residual carries one of the four outcomes with expected and observed magnitudes, distance opened is recorded alongside distance closed, and the net is published. A programme's first cycle against any reference additionally requires a loop |
| Underbuild Floor Gate | X | G2 | An artifact may be admitted only when each of the six shapes has been checked and either cleared or covered by a recorded deviation. The gate additionally requires that every floor applied names its consequence, carries a retirement condition, and has execution evidence for its check on this artifact. A floor without execution evidence does not count toward admission, since an unexecuted check and |
| Floor Derivation Gate | XI | G2 | A floor may be enforced at full authority only when it records the concrete failure event, the consequence and its bearer, the threshold placement with its reasoning, and — if numeric — its sensitivity. Floors lacking these are enforced as provisional and are reported as such wherever floor compliance is published, so that a passing floor set states how much of its own authority is derived. Impose |
| Phase Zero Gate | XII | G4 | A project may begin feature work, and an agent may begin autonomous work, only when at least one dimension has demonstrated all six capabilities end to end, the variation envelope is recorded for each instrument in use, failure records carry reproduction handles, and every dimension the project intends to make quality claims about either has a chain or is registered as measurement debt. A partial |
| Instrument Integrity Gate | XIII | G1 | A residual may be admitted to the ledger only from an instrument that declares coverage, envelope, perturbation, extraction level and failure behaviour, that returns three-valued output, whose perturbation is below its envelope, and that has passed its known-answer case within the declared re-validation interval. Instruments failing any of these produce observations recorded as unverified rather t |
| Toolsmith Gate | XIV | G4 | An instrument built during work may be used in accounting only when its blocking question was recorded before construction, all four conditions of §4 were established, its known-answer case is verifiable by direct inspection, and it is registered with its Part XIII declarations at cycle end. A cycle containing instrument construction publishes instrument debt repaid alongside its distance figures. |
| Incident Conversion Gate | XV | G4 | A significant incident may be recorded as closed only when its diagnosis produced a fix and either a probe or an explicit recorded decision not to convert, with the reason drawn from §4 or §10. The probe must carry its incident lineage, reproduction, distinguishing observable, three-valued output and retirement condition. An incident closed with neither a probe nor a recorded decision is registere |
| Oracle Boundary Gate | XVI | G3 | A quality claim about an artifact may be published only when the declared boundary exists and has been consulted, every judgment in the claim's chain that matches one of the four marks carries an oracle answer with a recorded answerer, standing and scope, and no answer in that chain is past its validity scope. Claims whose chains are entirely self-answered are published as self-certified — a label |
| Deviation Integrity Gate | XVIII | G2 | Work performed below a floor, or diverging from a recorded plan, may be admitted only when a deviation record exists carrying a constraint proof citing at least two attempts of the same shape, the intent as stated at the original decision, the substitution, the measured loss entered as a ledger residual, and the constraint's scope. Deviations recording zero loss are returned as plan-revision candi |
| Autonomy Entry Gate | XIX | G4 | Autonomous work may be recorded as evidence-gated only when a single written contract exists carrying all §4 components, all four §5 entry conditions are demonstrated for the in-scope dimensions, halt conditions are stated and recognizable without judgment, and every required evidence artifact names its consumer. Runs failing any condition are recorded as unsupervised work — a label applied to the |
| Phase Closure Gate | XX | G3 | A unit may be recorded as closed only when its verdict is one of the five, its statement publishes all six obligation items including the undefined dimensions, its accounting and acceptance are separately attributed, it carries a validity horizon, and — for a composite — its residuals were aggregated and checked against composite-scale floors rather than inherited from its parts. Closures failing |
| Lineage Position Gate | XXI | G4 | A system may claim measured quality only when its lineage position is published alongside the claim: which links of which lineages are currently in place. A claim from a system with L1 and L6 links present is labelled structurally unfalsifiable, since no internal observation could contradict it. This is a label carried with the claim, not a block — the claim may still be correct, and the reader is |
| Trap Registry Gate | XXII | G4 | The registry is usable as a control only when every entry carries all seven fields, every escape is executable from inside its trap or the entry is marked prevention-only, the symptom index resolves each of §7's observations, and the operational register is maintained separately from the reference set. A registry failing these is recorded as documentation — which is a legitimate artifact, correctl |
| Rule Registry Gate | XXIII | G4 | A rule set may be described as governance only when every entry carries its enforcement layer, derivation kind, retirement condition and eval reference, and the operating subset is named separately from the reference set. Sets failing this are described as doctrine — a legitimate artifact, correctly labelled — so that a reader knows whether a given entry will stop them or merely inform them. |
| Eval Integrity Gate | XXIV | G4 | An eval result may be cited as evidence only when the eval carries a negative control demonstrated within the re-validation interval, an adversarial variant that is not cheaper than compliance, a declared false-positive risk below the muting threshold, and three-valued output. Results from evals lacking a negative control are recorded as unverified — they may be correct, and nothing has shown they |

## 4. Seeded gates absent from the consolidation

Part XXV §4 states: *"The consolidation loses nothing — every seeded gate survives as a check within a point."* Checked against the seeds, **3 do not appear by name** in any of the four points:

| Gate | Part | Nearest named check in §4 | Status |
|---|---|---|---|
| Residual Ledger Gate | IX | *residual visibility* (G3), seeded by Part II | absent by name; a merge is plausible and unstated |
| Oracle Routing Gate | XVII | *oracle boundary* (G3), seeded by Part XVI | absent by name; a merge is plausible and unstated |
| (unnamed prose gate) | I | — | stated as prose without a gate name; outside the named set |

Each orphan has an adjacent-Part neighbour covering a similar subject, so silent consolidation is the likely explanation rather than omission. **The text does not say so**, and this registry does not decide it: the rows are recorded unresolved. What is certain is that §4's *"loses nothing"* is not verifiable as written, and the reader of a four-point implementation would not know two seeded gates had no home.

## 5. Completeness and measurement debt

| Field (Part XXV §3) | Derivable | Note |
|---|---|---|
| Trigger point | ✅ for the 20 consolidated | via the gate point; the orphans have none |
| Failure action | ✅ by point | G2 blocks; G1/G3/G4 label (§5) |
| Inputs consumed | ◐ partial | named at point granularity, not per gate |
| Verdict values · Bypass route · Owner | ❌ none | no seed carries them; **Owner is unassigned for all 23** |

> Part XXV §3 field 3 requires verdict values *"including could-not-run"*. Part XXVI §5 records that this build's own gate cannot report could-not-observe — so the one gate the family actually ran fails the arity requirement the family wrote. That is stated in three Parts and is not resolved here.
