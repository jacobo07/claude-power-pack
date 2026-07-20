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
| IV | Capability Genesis | ABSORB → REFERENCE | *pending wave 2* | | |
| VIII | Learning Dynamics | ABSORB → REFERENCE | *pending wave 2* | | |
| VI | Execution Reality | ABSORB → REFERENCE | *pending wave 2* | | |
| VII | Evidence Physics | ABSORB → REFERENCE | *pending wave 2* | | |
| V | Mission Computation | EXTEND | *pending wave 3 (spot-check)* | | |
| X | Governance Yield | EXTEND | *pending wave 3 (spot-check)* | | |
| XI | Evolutionary Ecology | EXTEND-thin | *pending wave 3 (spot-check)* | | |

**Running tally: 5 verified — 4 overturned to EXTEND, 1 survived as ABSORB.**

That one survivor is load-bearing. A re-audit in which every verdict flips is measuring
its own method, not its subject. Science IX surviving at ~90%, with the verifier reporting
zero findings and explicitly declining to manufacture one, is what makes the other four
credible.

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
