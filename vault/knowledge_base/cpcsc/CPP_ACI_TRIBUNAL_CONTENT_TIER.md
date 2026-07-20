# CPP-ACI Tribunal — Content-Tier Re-run

> **Status: IN PROGRESS — 3 of 12 Sciences verified.** Wave 1A complete.
> Supersedes the title-tier verdicts in `../cpp_aci/MASTER_BUILD_PLAN.md` §2.2 per
> `PR-CORPUS-AUDIT-CONTENT-TIER-001`: a content-tier verdict takes absolute precedence.

## Why this re-run exists

The 2026-07-12 Tribunal classified 12 proposed Sciences against existing owners by
comparing names. `T-OWNERSHIP-AUDIT-ABSORPTION-BIAS-001` established that method is
biased in one direction: 6 of 6 verdicts re-checked at content level moved toward
less-owned, none the other way.

**Recorded defect in the source artifact.** The Tribunal's §2.2 table lists **9**
ABSORB rows (I, II, III, IV, VI, VII, VIII, IX, XII) while its own tally line reads
"8 of 12 ABSORB, 3 EXTEND, 0 NEW" — summing to 11, not 12. Internally inconsistent by
one row before any verdict is tested. This re-run uses the table.

## Verdicts

| # | Science | Tribunal (title tier) | Content tier | Cov. (claimed owners) | Cov. (corrected owner-set) |
|---|---|---|---|---|---|
| I | Cognitive Reality | ABSORB → REFERENCE | **EXTEND** | ~45% | **85%** |
| II | Institutional Epistemology | ABSORB → REFERENCE | **EXTEND — owner misattributed** | ~30% (ACIS) | **75%** |
| XII | Autopoietic / Meta-Science | ABSORB → REFERENCE | **EXTEND** | ~55% | ~55% |
| III | Reasoning Compilation | ABSORB → REFERENCE | **EXTEND** | ~0% (owner does not exist) | **60%** |
| IX | Cognitive Capital | ABSORB → REFERENCE | **ABSORB — survives** | partial | **~90%** |
| IV | Capability Genesis | ABSORB → REFERENCE | **EXTEND** | owner mis-set both ways | **80%** |
| VIII | Learning Dynamics | ABSORB → REFERENCE | **ABSORB — survives** | partial | **~95%** |
| VI | Execution Reality | ABSORB → REFERENCE | **EXTEND** | thin (schema only) | **85%** |
| VII | Evidence Physics | ABSORB → REFERENCE | **ABSORB — survives** | partial | **~90%** |
| V | Mission Computation | EXTEND (white-space) | **EXTEND — shrinks hard** | — | **80% owned** |
| X | Governance Yield | EXTEND | **ABSORB — moves the other way** | — | owned by name |
| XI | Evolutionary Ecology | EXTEND-thin | **ABSORB — moves the other way** | — | owned outright |

## FINAL: 12 of 12 verified

| | Tribunal (title tier) | Content tier |
|---|---|---|
| ABSORB | 9 (I II III IV VI VII VIII IX XII) | **5** (VII VIII IX X XI) |
| EXTEND | 3 (V X XI) | **7** (I II III IV V VI XII) |
| KEEP-AS-NEW | 0 | **0** |

**The correction runs in BOTH directions.** Six ABSORB verdicts fell to EXTEND — and
three moved the opposite way: X and XI became ABSORB, and V collapsed from "genuine
white-space" to 80%-owned with a one-Part remainder. Nine of twelve verdicts changed, in
opposing directions.

This is the strongest available evidence that the content-tier method measures its subject
rather than its own bias. A correction that only ever produced "more new" would be
indistinguishable from a method that rewards finding gaps.

**The owner column is wrong far more often than the verdict column.** The verdict changed
in 9 of 12 cases; the owner-set was wrong or incomplete in **12 of 12**. Science IV is the
sharpest: the Tribunal's ABSORB was **right for the wrong reason** — it credited DFP, which
does not own the subject, while the real owner went unscored. A correct-verdict/wrong-owner
outcome survives any audit that re-checks only conclusions.

### Root cause — and why this re-run was only possible after Task 1

The Tribunal's error was structural, not incidental: **it scored the code surface
(`modules/`, `commands/`) while the mechanisms live in the dataset surface
(`vault/knowledge_base/cpp_ias/`)** — a 14-file, ~34k-word-per-file family it appears
never to have opened.

It could not have opened it. On 2026-07-12 CPP-IAS sat unversioned in `Downloads`, outside
the repository entirely. The denominator defect was not carelessness; it was a corpus that
was **physically outside the audit's reach**. Repatriating it (`6b83358`) is what made this
re-run possible, and `ias_c1_capability_portfolio.txt` alone turns out to be the true or
co-true owner of Sciences IX, IV, V, X and XI — named in none of them.

That is the enrollment defect at its most consequential: not a registry row someone forgot,
but half a million words of owner-evidence sitting one directory outside the boundary,
silently converting "we already own this" and "this is white-space" into coin flips.

---

## III — Reasoning Compilation → EXTEND (60%)

**The Tribunal cited a proposal as its own owner.** `MASTER_BUILD_PLAN.md:74` names the
owner as "**Reasoning Compiler** (exists)". A repo-wide grep for
`Reasoning Compiler|reasoning_compiler|ReasoningCompiler` returns 7 hits, **zero of which
are an implementation** — three are later audit reports, one is that line itself, and one
is `D2A_REINFORCEMENT_FINDINGS.md:45`, which lists "Reasoning Compiler" as a *proposal*
that falsely FOLDed to SQI-02. There is no `modules/reasoning_compiler`. An owner column
populated by name-lookup can close a loop on itself and read as ABSORB.

**Mechanism present — and the prior verifier missed it.** DAIF-02 has a real compiler
middle end at `PART XV — THE OPTIMIZER PIPELINE` (:257): "a pipeline of named passes, each
taking a declared input class of units and edges, performing one declared transformation,
emitting a declared output class, and each gated… A pass with no fidelity check is not an
optimization but a deletion with a good story." The register includes constant folding,
decision folding, dead-knowledge exclusion and duplicate elimination under reference
conservation — literal compiler passes. Plus a back end at `PART XVI — ADAPTIVE LOWERING`
(:277): "a compiler that emits one fixed artifact regardless of who will execute it is a
compiler with a broken back end."

The objective functions are also not opposite, which the verifier tried to falsify and
failed: `PART XVIII — COMPILATION ECONOMICS` (:329) meters "tokens avoided, reasoning
reused, errors prevented, missions accelerated." This is why coverage is 60%, not 10%.

The owner set is larger than the Tribunal's two: `vault/plans/cognitive-kernel-datasets-2026-07-03.md:40-47`
had already adjudicated this exact question, naming `one_shot/compiler.py`, CO-03, 
`spec_gate.classify_tier`, GK-06 and GK-05, and ruling it `DEFERRED (EXTEND CO-03 + one_shot)`.

**Mechanism absent — the post-hoc execution axis.** DAIF-02's input is CIR-0 artifacts:
"conversations, datasets, PRDs, decisions, commits, logs, audits, results" (:29) — things
already produced. Nothing ingests a *live* trace. The estate names the gap itself (:48):
"no single unified pre-execution compile pass ties intention → deps → existing-assets →
routes → model → budget → plan into one entry gate."

**Unique remainder:** live-trace ingestion; the decompiler; a cognitive VM; execution-step
passes; and the unified pre-execution entry gate — which the estate has already classified
as EXTEND (wiring), not a new dataset.

---

## IX — Cognitive Capital → ABSORB SURVIVES (~90%)

The Tribunal's verdict is correct. Its denominator was not.

**Mechanism present, and one owner is running code rather than doctrine.**
`cognitive_os_01_operating_economics.md` is literally titled "Operating Economics &
Cognitive Capital", with a Work-Unit metric gated against vanity (:82): "a Work Unit only
counts when the Production Reality Gate confirms it." `modules/frontier_intelligence/token_irr.py:4-16`
is executable and treats "the frontier token as R&D CAPITAL, not operational cost", with
`frontier_dependence_index` — "fraction of deposits still frontier-only (0 = fully
distilled, 1 = wholly model-bound). **THE central metric.**"

**Depreciation — the near-miss that produced the counter-bias finding.** A
`depreciat|amortiz|impairment` grep returns nothing across FD, CO-01 and token_irr. The
verifier nearly declared it absent, then applied the Science III lesson and checked the
section index: the mechanism exists as a `DECLINING → RETIRED` lifecycle with evidence
gates in `ias_c1_capability_portfolio.txt:1604-1648`, including an anti-drift rule against
"quietly aging positions toward retirement without fresh evidence", and ":1632 — RETIRED is
not deletion." FD-04 is literally titled *Intelligence Decay*.

**Denominator correction.** `ias_c1_capability_portfolio.txt` (34,895 w) was never scored
and is the truest owner — 648 hits for `portfolio|capital|depreciat|ROI|valuation|asset`
against a handful in every file the Tribunal cited. It already absorbed four prior
candidates, and phrases the object its named owners cannot (:33): "given everything the
estate already has, where should its next unit of scarce cognitive capital go, and which
of its existing holdings **have stopped earning their keep**."

**Mechanism absent: zero findings.** The verifier declined to manufacture one.

**Unique remainder: none material.** The honest caveat is substrate, not coverage —
IAS-C1 and the DAIF/CO datasets are *specifications*, while only `token_irr.py` and
`token_ground_truth.py` run. If Science IX were re-proposed, its sole defensible delta is
wiring IAS-C1's portfolio lifecycle into an executable, not new doctrine.

---

## IV — Capability Genesis → EXTEND (80%)

**The Tribunal's owner-set was wrong in both directions.** DFP should be *struck*: it
governs whether the governing corpus exists before a build, and its DFP-02 lifecycle is
the lifecycle of **a corpus**, not of a capability — 8 stages ending at CERTIFICATION and
FREEZE. That is the reverse vector from a dataset→system foundry. Citing it is
"lifecycle" as shared metaphor.

The true owners were never scored: `ias_d1_system_ecology.txt` carries
`PART XX — THE DATASET GENOME AND LINEAGE` with a formal definition (§20.2) — "A system's
GENOME, DEFINED, is the heritable subset of its property record… that transfers, with
evidenced completeness, to whatever successor system a speciation, merger, or
succession-resolution event produces" — at 69 hits on the genome vocabulary, an order of
magnitude above anything the Tribunal scored, plus `PART IX — NICHE DISCOVERY`. And
`ias_c1` §15.2 owns the capability lifecycle outright: PROPOSED → FUNDED → TESTING →
SETTLED → MATURE → DECLINING → RETIRED, "gated by evidence, never by elapsed time alone."
D2A was correctly credited and already hands its birth score to IAS-C1 §15.2 — the two
families are wired.

**Mechanism absent — the foundry step itself.** Nothing downstream of DFP's FREEZE emits
an executable artifact. `ias_a1` §10.6 explicitly disclaims construction: closing a
decomposition gap by BUILDING a capability is "outside this dataset's own authority," and
IAS-C2 forecasts demand without fabricating. The estate can detect a vacancy, price it,
score a candidate, write a build contract, ratify capital, and govern the position's whole
life — but **the arrow from certified corpus to running capability is drawn by a human
session every time.**

**Unique remainder:** corpus→executable transduction — the seam between DFP's FREEZE gate
and IAS-C1's FUNDED state.

---

## VIII — Learning Dynamics → ABSORB SURVIVES (~95%)

The verifier states it looked hard for a gap and did not find one worth naming.

**All three legs owned.** Learning closure is FD-07's organizing thesis, not an incidental
feature: "question → delta → novelty → triage → transmute → writeback → eval → benchmark →
transfer-test → registry → prompt-improvement." Promotion economy is FD-03's 8-home
taxonomy composed over compound-learnings' signal thresholds, and is an economy in the
strict sense — contention and waste over promotion effort (`fd_03:610`: "two panes each
independently deciding that a capability warrants promotion… and both spending the
transmutation effort").

**Non-recurrence proof is owned by an unscored file — and this is where failure mode B
would have bitten.** Grepping `non.?recurrence|cannot recur` returns essentially nothing in
`ias_d2_immune_system.txt`. **The term is absent; the mechanism is the file's entire
subject.** Its Part index names `PART VIII — IMMUNIZATION: FROM INCIDENT TO PREVENTIVE
PROTECTION`, `PART IX — THE ANTIBODY RECORD`, `PART XIII — IMMUNITY DECAY MONITORING`.

**The owner is ahead of the proposal, not behind it.** IAS-D2 does not merely provide
non-recurrence proof — it refutes the proposal's framing as unsound. §13.1: "three
independent processes erode a confirmed antibody's validity over time without any single
one of them announcing itself as a regression." §13.2: "a test that already passed once
will continue to report CLEAR indefinitely unless something makes the underlying artifact
re-readable and re-evaluated." **A static non-recurrence proof is precisely the artifact
PART XIII exists to catch.** Building it as specified would install the failure mode the
owner was written to prevent.

**Unique remainder:** the 5% is a rename, not a mechanism — no artifact carries "learning
dynamics" as an index entry, so the material is reachable only through four families'
separate vocabularies. A navigation cost (a GK-06 route), not a build.

---

## VI — Execution Reality → EXTEND (85%)

**`pp_dataset_22` assessed on the ACIS standard: a schema skeleton, not a mechanism.**
Seventeen field-lists (`EXECUTION_LEASE`, `EXECUTION_CAPSULE`, `EXECUTION_SAGA`,
`ROLLBACK_DECISION`) where every entry is a bare field name with no semantics —
`rollback_available:`, `state_before:`, `state_after:`. It names the parts of a sovereign
runtime; it does not specify how any of them decides anything.

**Mechanism present, in files never scored.** `daif_04` PART IV defines an action contract
as a triple — subject, predicate, evaluator — and rules that "an assertion with no named
evaluator is undecidable in practice regardless of how decidable it looks on paper," with
UNVERIFIED as a distinct terminal state. §7.7 carries reversibility: "a contract with
irreversible effects MUST declare a compensation path before it may be executed at all.
Not before it fails — before it runs." §7.8 forbids "the undeclared partial, which is a
promise that produces an unknowable world." `daif_07` §6.5 supplies proof-of-reality-change
via a ranked closure hierarchy topped by an observed reality probe. `ias_f3` §2.3 owns the
intended-vs-observed delta object outright via its DIVERGENCE RECORD. `drk_02` carries
decision-layer reversibility at the highest hit density in the estate.

**A candidate correctly rejected.** DAIF-21 is a title match, not a subject match: its
PART I is "every compiled artifact is a photograph of a world that has since moved on" —
subject is staleness of derived representations, not side effects of executed actions.
Adjacent, not owner.

**Mechanism absent — the undeclared side effect.** 731 hits across 111 files for the
side-effect vocabulary, and every one governs *declared* effects: postconditions promised,
halting states enumerated, irreversible effects registered, forecasts predicted. Nothing
discovers effects **nobody declared** — a world-diff observed before and after an action,
reconciled against its effect manifest, surfacing an unenumerated mutation as unauthorized.

**Unique remainder (~15%):** the per-action side-effect ledger over undeclared mutations.

---

## VII — Evidence Physics → ABSORB SURVIVES (~90%)

Held on its own merits; the verifier was explicitly warned not to flip it for consistency
with SQI's reputation, and states it did not.

**Mechanism present.** SQI-00 §10.2 is a literal court with rules of standing — Builder,
Prosecutor, Defender, Court, Auditor, Guardian — and §10.7 carries the load: "a reviewer
reads what was produced and asks whether it is coherent, and a coherent fabrication passes
review effortlessly. An Auditor asks whether the same reality produces the same artifact,
and a fabrication does not survive that question."

Proxy extermination is owned by an unscored file, and better than the proposal states it:
`daif_03` PART VII — "But the screens are proxies and this is the criterion. A compilation
that passes all nine proxies and fails behaviorally has failed, and the nine proxies were
wrong about it" — then §7.6 names *why* proxies pass while reality fails, and keeps them
anyway on an explicit economic argument. `ias_e1` PART VIII adds per-hop evidence drift
classified `STABLE | DECAYED | INFLATED`, where "INFLATION is more dangerous than decay
because decay merely loses information, while inflation actively manufactures false
confidence."

SQI's root law is backed by an executed instrument rather than prose alone:
`baseline_guardian.py` gates three absolutes, refuses ratios, and was *observed refusing* —
two real failures on first execution, repaired and re-verified.

**Mechanism absent — the artifact reality graph as a single queryable object.** The
capability exists but is distributed and un-unified: E1 graphs claims across hops, DAIF-02
holds provenance, GK-04 holds typed derivation edges, ACIS holds the ladder. Nothing binds
a *shipped artifact* to the evidence licensing belief in it. The nearest declared owner,
**SQI-09 Evidence Admissibility & Chain of Custody, is DEFERRED — not built.** The court
exists and sits; its rules of evidence are backlog.

**Unique remainder (~10%):** the unified artifact→evidence graph, and its join to E1's
drift records so an inflation event can be traced to the artifact it contaminated.

---

## V — Mission Computation → EXTEND, but shrinks from "white-space" to ~20% remainder

Three of four pillars are already built. **Dynamic org assembly** is `ias_a1` PART VII
verbatim: the runtime structure that "DISSOLVES once the mission completes, leaving no
standing artifact in the ensemble beyond the route trace… builds and discards by design."
It even bounds a failure mode the Science would have had to rediscover.

**Mission market** is owned by `ias_c1` PARTS VI and IX — a clearing mechanism for missions
competing over a finite capability pool, expressed in portfolio vocabulary rather than
market vocabulary. Textbook failure mode B: grepping "mission market" returns 0 in c1 while
the mechanism is a named Part. **Mission hypervisor** splits across `ias_a2` PARTS XII–XIII
and `ias_a1` PART XI.

**Absent:** mission constitution as a per-mission normative object. The 82 constitution hits
resolve to the estate-level `CONSTITUTION.md` and F1/F2 federation law — a *standing*
constitution, not one compiled per mission and retired with it. Subject genuinely differs.

**Unique remainder:** a per-mission normative envelope (which rules bind, which are waived,
who may amend, expiry at dissolution) attaching to a1's PART VII workflow instance.
**Roughly one Part, not a Science.**

---

## X — Governance Yield → ABSORB (moves the opposite way)

The Tribunal's stated delta was "*measured* yield (value ÷ cost)". That exists **by name**:
`ias_c1` **PART XIV — MEASURED GOVERNANCE YIELD: THE COST OF GOVERNING, PRICED HONESTLY**
(:1461), defining it as "the value-to-cost ratio of the estate's governance mechanisms
specifically, computed by the SAME valuation discipline (Part IV)". At :1483 it states it is
answering this very proposal: "this is precisely the honest discipline 'measured governance
yield' was reaching for."

It also carries the two hard parts the proposal never named: a **prevented-harm** advantage
term (§14.3 — governance value is what does *not* happen, invisible to consumer-count), and
an **anti-gaming countermetric** (§14.5 — "a governance position's yield may never be
computed from its OWN self-reported activity log alone"). **The Science as proposed would
have shipped the naive ratio and hit exactly that trap.**

Honest caveat recorded by the verifier: `ias_e1` PART XIX's theater-detection signature is
about *observability* theater, not governance theater — close but not identical. c1
§14.4–14.5 covers the governance-specific case, so the pair closes it.

**Unique remainder: near-nil.** At most, wiring c1's formula to real audit-log block counts
so the yield is computed rather than defined — an implementation ticket, not a Science.

---

## XI — Evolutionary Ecology → ABSORB (moves the opposite way)

`ias_d1_system_ecology.txt` (42,779 w, 26 Parts) owns all four primitives outright.
**Fitness** → PARTS II–IV, and PART III's title alone encodes a constraint the proposal
lacks: *fitness per environment, never one global number*. **Extinction** → PART XV
(retiring a system while preserving its useful law). **Speciation** → PARTS XI–XII.

**Mutation** is the one term genuinely thin in d1 — one hit. And it is the textbook failure
mode B trap: the mechanism is not absent, it is in a sibling's named Part —
`ias_g1` **PART X — THE MUTATION SANDBOX** plus PART XI *The Evolution Planner*, with d1
PART XXII supplying governed-change discipline.

d1 also owns material the Science never proposed: niche discovery and breadth/overlap, a
Biodiversity Governor with anti-monoculture *and* anti-proliferation poles, dataset genome
and lineage, and adversarial cases against gaming the ecology's own mechanisms. Its PART I
is literally titled *"Why Neither D2A Nor EVOLUTION_ENGINE Already Owns It"* — d1
pre-adjudicated its boundary against two of the Tribunal's three claimed owners.

**Unique remainder: none worth a Science.** At most a bridge from g1's mutation sandbox to
d1's fitness landscape — and d1 PART XXVI already names that integration.

---

## The genuine delta after 12 content-tier verdicts

Seven EXTENDs, each with a named remainder. Ordered by how much is actually missing:

| Science | remainder | size |
|---|---|---|
| XII | the theory generator / law extraction from evidence — "a tribunal without a legislature" | large |
| I | unknown-unknown generation (every owner detects divergence in what is already represented) | large |
| II | claim-level confidence calibration · epistemic debt as a standing balance · **unification** of five owners' overlapping algebras | medium |
| III | live-trace ingestion · decompiler · cognitive VM · unified pre-execution entry gate | medium |
| IV | corpus→executable transduction — the seam between DFP's FREEZE and IAS-C1's FUNDED | medium |
| VI | the undeclared side-effect ledger | small |
| V | mission constitution — one Part | one Part |

Five ABSORBs with no material remainder: VII, VIII, IX, X, XI.

---

## I — Cognitive Reality → EXTEND (85% under the corrected owner-set)

**Mechanism present.** SQI-01 Part II is a genuine premise-disproof engine, and enforces
symmetry — it disproves assertions of *presence* and of *absence* alike. SQI-01 Part III
specifies the Reality Scanner as read-only and manifest-first: "every field is either an
observation with its basis attached or an explicit unknown, and there is no third kind of
field" (¶3.10).

**Owner correction.** The truer owner is `daif_21_reality_sync_v1.txt` (36,331 w), which
the Tribunal never scored, and it is stronger than both named owners on four of six
sub-claims — believed-vs-observed state, a 12-class drift taxonomy with four currency
verdicts, external-state reconciliation via pull probes, and the epistemic core: "the
absence of a change signal is not evidence of stability… an artifact which has never been
re-checked is not fresh. It is unexamined" (:47).

**Mechanism absent — unknown-unknowns.** Grep `unknown[- ]unknown` returns **zero** in
`sqi/`, zero in `d2a_fabric/`, zero in `modules/error_prevention/` — every file the
Tribunal named plus the one it missed. This is not inference from silence: DAIF-21
concedes it in its own voice (¶4.4) — "the assumption everyone shared, which stopped being
true, and which no artifact ever wrote down because it was too obvious to state. Against
this class, structural comparison is silent and will remain silent." FIOS carries it as
🟡 EXTEND — not built.

Also confirmed thin: `premise_verifier.py` exposes three checks (file/attr/function
exists) — a symbol-existence probe, which SQI-01 itself distinguishes at ¶1.9: "That layer
operates at the granularity of a symbol… This dataset operates at the granularity of a
repository."

**Unique remainder:** unknown-unknown generation (every owner detects divergence in things
already represented; nothing enumerates the unrepresented), and reality binding for a live
external system never compiled into a unit.

---

## II — Institutional Epistemology → EXTEND (75%), and the Tribunal's attribution is wrong

**ACIS alone covers ~30%,** owning two of five sub-claims: the E0–E7 ladder, and the
falsifier gate — "A theorem without a concrete, observable refutation condition is not a
weak theorem — it is *not a theorem at all*" (`acis_00:124`).

**The other three sub-claims are owned by files outside the denominator:** DRK-00 defines a
ten-member typed Evidence record (fact / observed_evidence / inference / hypothesis /
prediction / assumption / preference / constraint / uncertainty / unknown), deliberately
not collapsed to a confidence scalar; `daif_01:133` carries a ten-status epistemic lattice
with an enforcement rule that "an inference may never be typed as a fact"; `daif_21:31`
supplies truth maintenance in substance — "a claim whose only support has collapsed does
not merely weaken, it falls to the weakest link that remains."

**Mechanism absent — confidence calibration, and ACIS rules it out by doctrine.** This is
the same subject-opposite pattern that collapsed two verdicts in the prior audit:
`acis_00:119` defines confidence as "subjective, and *decoupled from level*… confidence is
not evidence; the ladder ignores it for promotion." A system whose central rule is *ignore
confidence* cannot own confidence calibration. Calibration-against-outcome exists in DRK-07
but its subject is **decisions, not claims**, and DRK-03 draws the line itself: "Level is
an ACIS concept; burden is a DRK concept."

`epistemic debt|truth maintenance|belief revision` returns **zero hits** outside the
proposal's own build plan.

**Scale check on the Tribunal's premise:** ACIS is 8,169 words across four files, one a
558-word session record and one an 836-word index, and states its own footprint verbatim —
"The only new code in the entire ACIS family is one derived function that reads four
ledgers and returns a level" (:213). That cannot own evidence objects, claim-proof algebra,
epistemic debt, truth maintenance *and* calibration. The scope is largely covered; the
Tribunal credited it to a family that disclaims four-fifths of it.

**Unique remainder:** claim-level confidence calibration; epistemic debt as a standing,
aging, owner-assigned balance (DAIF-07 ages obligations, not beliefs); and **unification** —
five owners across three families hold slices of one algebra with no join, and DRK-00's
evidence types and DAIF-01's statuses overlap without a mapping.

---

## XII — Autopoietic / Meta-Science → EXTEND (55%)

**Mechanism present.** Falsification is genuinely owned, with an operational standard that
distinguishes a real falsifier from a slogan: "'The law is false if reasoning doesn't
compress' is not a falsifier… a falsifier names a measurement, a signal, and a window"
(`acis_00:132`). Paradigm replacement is owned in mechanism — retirement is "a designed
operation rather than an embarrassment to be avoided," preserving genealogy (:139).
Self-modifying doctrine is owned by a third file the Tribunal did not name, `dfp_05`:
"A protocol that can change anything about itself is a capture risk, because the first
thing a self-modifying governance system learns to modify is the mechanism by which it
could be found wrong" (:404).

**Mechanism absent — the theory generator and law extraction from evidence.** Grep
`theory generat|law extract|hypothesis generat` returns **one hit corpus-wide: the
proposal describing itself.** The claimed owner rules it out explicitly —
`ACIS_INDEX.md:51` lists "unknown-unknown infra" under **DO_NOT_BUILD**, and `acis_00:35`
states the ladder "is therefore a read-only projection… it writes nothing, stores nothing,
and signals nothing new."

The one artifact that *looks* like a generator is not one: ACIS-01's "unknown-unknown
generator's output" sits above a hand-written list of five open questions from a single
session, flagged as "E0 prompts for a future session." The output exists; the generator
does not.

**FD-03 fails the subject check.** Its own opening defines it as a destination-and-form
router for an insight someone already had. Placement compiler, not discovery engine —
"transmutation" is a shared metaphor whose subject differs: FD-03's input is a finished
insight; a law-extractor's input is raw evidence.

**Unique remainder:** the generative half. Every owner *judges* a law that a human or a
frontier session already wrote. Nothing *proposes* one. **ACIS is a tribunal without a
legislature.** Four ledgers (FD-07 deposits, fd_04 proofs, UKDL rules, CEPS events) are
read only to compute a level; nothing mines them for a candidate law.

*Scoping question for the Owner, not a defect:* autonomous paradigm replacement is blocked
by the No-Autopromotion Invariant and DFP-05's propose-never-apply. Under the proposal's
framing that may be a feature.

---

## Process findings for the denominator (independent of any verdict)

1. **The Tribunal's owner column reads like an index lookup** — family name matched to
   Science name. In two of three cases the true owner was a file it never scored:
   `daif_21` for Science I, and the whole `decision_review/` family plus `daif_01` Part
   VIII for Science II. A denominator assembled by title matching missed the biggest owner
   both times — `PR-COVERAGE-BY-CONSTRUCTION-001` again, now at the audit layer.

2. **Method upgrade adopted for waves 2 and 3.** Remaining verdicts are verified against a
   **discovered** denominator: grep the proposal's mechanism vocabulary across all of
   `vault/knowledge_base/`, rank candidate owners by hit density, and only then read. The
   Tribunal's named owner becomes a hypothesis to test, not the search scope. This is the
   same correction applied to the D2A registry in `314ad9a`, now applied to the human
   audit method.
