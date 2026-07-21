# CRAIF D2A Reinforcement Packages

> Eight proposals, one per real owner CRAIF's own STOP #1 audit found already governing
> a slice of the original AISHF surface. Each package is a **proposal artifact** — it
> strengthens the named owner's own sealed corpus by reference and evidence, never by
> direct edit. Applying a package requires the owner's own Owner-approved amendment
> process (e.g. DAIF-00's evidence-and-review discipline, SQI's own extension gate);
> nothing in this file mutates any sealed dataset. Where a package's content already lives
> inside a CRAIF Part (the "dataset-internal" half), this file cites that Part rather than
> repeating it, and adds only the writeback half — the specific artifact the real owner
> would receive if the proposal were accepted.

Schema per package: **Owner** · **Mechanism Strengthened** · **Missing Adapter/Contract**
· **Integration Point** · **Test/Eval** · **No-Duplication Proof** · **Done-Gate** ·
**Target** (dataset-internal Part already satisfying this vs. proposed writeback pending
Owner approval).

---

## 1. Liveness-to-Repair Package

**Owner**: `modules/liveness/reachability.py` + `modules/liveness/liveness_ledger.py`.

**Mechanism strengthened**: reachability detection currently ends at a REACHABLE /
UNREACHABLE verdict with no standing mechanism to act on an UNREACHABLE finding beyond
surfacing it. CRAIF-01's transaction gives that verdict a closed loop: intake, evidence
freeze, authorized candidate, sandbox, verify, canary, commit-or-rollback, ledger.

**Missing adapter/contract**: liveness has no notion of a Repair Intent, no state machine
for a fix in progress, and no vocabulary for "this orphan module now has an open repair
transaction, do not re-surface it as a fresh finding on the next scan." CRAIF-00 Part IV's
Repair Intent object and CRAIF-01 Part III's Intake discipline are the missing pieces.

**Integration point**: liveness's scan output becomes a Reachability Finding (CRAIF-00
Part III) consumed at CRAIF-01 Intake; `liveness_ledger.py`'s existing file-mtime and
co-signal probe infrastructure is consumed, unchanged, as the liveness signal CRAIF-01
Part II.7 requires for transaction-hang detection — CRAIF does not build a parallel
process monitor.

**Test/eval**: replay Fixture Two (155 orphan modules) as a CRAIF-01 worked case: confirm
a template-matched candidate's Verification Contract is keyed to `reachability.py`'s own
REACHABLE verdict, per CRAIF-00 12.3, not a weaker proxy.

**No-duplication proof**: CRAIF never re-implements the reachability scan itself, the
liveness probe types, or the ledger's own signal storage — verified at content-tier this
session by reading both files in full; CRAIF only adds the transactional envelope around
an already-produced verdict.

**Done-gate**: a liveness-surfaced Finding can be traced through OPENED to a closed state
in CRAIF-01's state machine without any new field invented on the liveness side.

**Target**: dataset-internal — CRAIF-01 Part III (Intake), Part XII (Post-Repair Liveness
Observation), Part XVIII (Integration Contracts) already specify this fully. Writeback
pending: a short adapter note for `liveness_ledger.py`'s own maintainers describing the
transaction-state signal CRAIF-01 Part II.7 expects it to expose, so a future liveness
revision does not silently drop the field CRAIF-01 depends on.

---

## 2. SQI-to-Repair-Verification Package

**Owner**: `vault/knowledge_base/sqi/` (hermetic replay, executable-reality reconciliation,
evidence-admissibility ladder).

**Mechanism strengthened**: SQI already proves whether a repository's tests and claims
correspond to reality; CRAIF-01's Verification and CRAIF-02's Simulation Harness both need
that exact hermetic-replay discipline to prove a *repair* — rather than a repository state
— actually holds, without inventing a second isolation mechanism.

**Missing adapter/contract**: SQI's hermetic replay is scoped to repository-state claims
generally; it has no notion of a before-and-after pair specific to a repair transaction,
and no notion of an Activation Chain segment (CRAIF-02 Part II) as a distinct verifiable
unit.

**Integration point**: CRAIF-01 Part VIII composes SQI's hermetic-replay discipline by
reference for Sandbox Execution; CRAIF-02 Part X.2 composes it again for the Simulation
Harness. Both cite SQI's own isolation contract rather than reimplementing copy-on-read
sandboxing independently.

**Test/eval**: confirm a CRAIF-01 Sandbox Execution run and an SQI hermetic replay run,
given the identical target and identical isolation guarantees, produce consistent
verdicts on a shared synthetic case — divergence would indicate CRAIF's composition-by-
reference has silently drifted into its own competing isolation logic.

**No-duplication proof**: CRAIF-00 Part XV explicitly adopts SQI's own evidence-tier
vocabulary (VERIFIED/OBSERVED/INFERRED/etc., aligned rather than forked) and CRAIF-02 Part
XV.5 names SQI as the explicit hermetic-execution partner; no CRAIF Part defines an
independent isolation or evidence-tier scheme.

**Done-gate**: a repair's Verification Contract and an Activation Verification Contract
both resolve their admissibility tier using SQI's own vocabulary, checkable by grepping
both corpora for tier terminology and confirming identical definitions.

**Target**: dataset-internal — CRAIF-00 Part XV, CRAIF-01 Part VIII, CRAIF-02 Part X.2 and
XV.5 already specify this. Writeback pending: propose to SQI's own maintainers that a
repair-transaction replay (a before/after pair against one target, rather than a whole-
repository claim) be recognized as a valid SQI hermetic-replay invocation shape, so
CRAIF-01/02 consume SQI's existing tooling directly rather than a hand-rolled equivalent.

---

## 3. DRK-to-Repair-Authority Package

**Owner**: `vault/knowledge_base/decision_review/` (Decision Review Kernel — reversibility,
blast radius, Tipo A/B classification, evidence-burden confidence).

**Mechanism strengthened**: DRK already classifies a change's risk and reversibility;
CRAIF-00's L0-L4 Repair Authority Ladder (Part VIII) consumes exactly that classification
as one of its five conjunctive L3 eligibility conditions, rather than inventing a rival
authority scheme.

**Missing adapter/contract**: DRK's classification is general-purpose; it has no notion of
a Repair Candidate specifically, and no field distinguishing "this classification was
computed fresh against current evidence" from "this classification is being reused from a
prior, possibly stale, instance" — the exact staleness risk CRAIF-01 Part IV's Precondition
check must resolve before Authority Acquisition.

**Integration point**: CRAIF-00 Part V's Repair Authority Decision object carries DRK's
Tipo A/B classification and blast-radius estimate as required fields; CRAIF-01 Part VI
(Authority Acquisition) re-validates the classification's currency against DRK's own
evidence-burden discipline before granting a tier, never re-deriving the classification
independently.

**Test/eval**: replay Fixture Three (hook/settings divergence) through DRK's own Tipo A/B
classifier and confirm the resulting tier matches the L3 grant CRAIF-01 Part XX's worked
example assumes.

**No-duplication proof**: CRAIF-00 Part XI names DRK explicitly as owning "blast radius,
reversibility classification, or decision authority in general"; no CRAIF Part defines an
alternate reversibility taxonomy.

**Done-gate**: every Authority Decision object in a CRAIF-01 transaction trace carries a
DRK classification with a timestamp CRAIF-01 Part IV can check for staleness, never a
CRAIF-internal risk score.

**Target**: dataset-internal — CRAIF-00 Parts V, VIII; CRAIF-01 Parts IV, VI already
specify this. Writeback pending: propose DRK's own classification object gain an explicit
"computed-at" timestamp field if one does not already exist, since CRAIF's own staleness
discipline depends on it and currently infers it rather than reading it directly.

---

## 4. CPP-IAS Repair-Outcome-and-Immune-Memory Package

**Owner**: `vault/knowledge_base/cpp_ias/04_SYSTEM_ECOLOGY_IMMUNOLOGY/ias_d2_immune_system.txt`
(pathogen taxonomy, quarantine, containment, immune memory).

**Mechanism strengthened**: IAS-D2 classifies and contains a threat; it has no standing
mechanism to receive a *confirmed-repaired* outcome and fold it into immune memory as a
pattern the system should recognize faster next time — a gap CRAIF's own Guardian
Promotion Candidate pipeline (CRAIF-00 Part VII) closes.

**Missing adapter/contract**: IAS-D2's immune memory has no object shaped like a Repair
Certificate; it needs a consumer-side contract describing what a "verified-and-held"
repair outcome looks like before it can be promoted into standing immune memory rather
than treated as a one-off resolution.

**Integration point**: CRAIF-00 Part VII's Guardian Promotion Candidate, produced only
after CRAIF-01's local-recurrence-then-cross-project-validation pipeline (Part XIV.6),
becomes an immune-memory candidate IAS-D2 evaluates under its own promotion criteria —
CRAIF proposes, IAS-D2 (or whichever authority owns immune memory promotion) decides.

**Test/eval**: a Repair Certificate for a recurring Failure Pattern, held across two
independent confirmations, produces a Guardian Promotion Candidate; confirm IAS-D2's own
promotion gate, not a CRAIF-internal one, makes the final promotion decision.

**No-duplication proof**: CRAIF-00 Part XI explicitly excludes "the immune/pathogen
taxonomy, quarantine, or containment"; IAS-D2 Part XIV's own false-healing structure is
the direct model CRAIF-00 Part XIV mirrors rather than replaces, cited by name.

**Done-gate**: a promoted guardian's origin is traceable to a specific CRAIF Repair
Certificate, and IAS-D2's own promotion log — not a CRAIF ledger — is the system of record
for the promotion decision itself.

**Target**: dataset-internal — CRAIF-00 Part VII, Part XIV.6, CRAIF-01 Part XIV. Writeback
pending: a formal proposal to CPP-IAS's own maintainers specifying the Guardian Promotion
Candidate's field shape as an input their existing promotion pipeline could accept.

---

## 5. DAIF Repair-to-Advantage Package

**Owner**: `vault/knowledge_base/d2a_fabric/` (DAIF-00 D2A constitution, DAIF-21 semantic
drift/reality-sync).

**Mechanism strengthened**: DAIF-00 defines the Duplicate-to-Advantage doctrine CRAIF's
entire founding decision applied; this package closes the loop by feeding CRAIF's own STOP
#1 audit — the ownership matrix, the residue register, this very package set — back to
DAIF-00 as a second, independently-produced worked instance of D2A doctrine in practice,
distinct from DAIF's own founding cases.

**Missing adapter/contract**: DAIF-21's semantic-drift detection has no standing consumer
for "a Trigger or Loader reference has gone stale because a relocated artifact broke it" —
exactly CRAIF-02 Part IV.5's Stale Bootstrap Reference taxonomy member, which CRAIF
correctly routes to DAIF-21 rather than owning itself.

**Integration point**: CRAIF-02 Part XV.8 names this routing explicitly: a Stale Bootstrap
Reference finding is submitted to DAIF-21 as a semantic-drift finding, with CRAIF
contributing only the activation-chain symptom, never the drift-detection logic.

**Test/eval**: construct a synthetic Stale Bootstrap Reference case (Part V.3's synthetic-
source discipline) and confirm it produces a DAIF-21-shaped finding rather than a CRAIF-
internal one when routed.

**No-duplication proof**: CRAIF-00 Part XI names DAIF-00 and DAIF-21 explicitly as excluded
domains; CRAIF-02 Part IV.6 explicitly distinguishes a CRAIF activation finding from a
DAIF-21 drift finding by root cause, not merely by symptom.

**Done-gate**: DAIF-00's own D2A doctrine gains CRAIF as a second full worked application,
independently produced without DAIF-00's own authors having directed CRAIF's construction
— evidence the doctrine generalizes rather than being self-referentially confirmed.

**Target**: writeback proposed — this package itself, submitted to DAIF-00's maintainers
as a second case study of the doctrine, is the artifact; CRAIF-02 Part IV.6/XV.8 already
specify the operational routing rule this package documents at the family level.

---

## 6. Assurance-and-Claim-Language Package

**Owner**: `vault/knowledge_base/acis/` (ACIS epistemic ladder, Generation Zero laws,
E0-E7 evidence tiers).

**Mechanism strengthened**: ACIS owns the general epistemic ladder and the falsifiability
discipline (a derived level caps at E3, no self-certification, per project memory
`project_acis_generation_zero_scs_c88.md`); CRAIF-00 Part XV explicitly reuses ACIS "by
reference" rather than defining a rival ladder, adding only the repair-specific refinement
that presence evidence for an activation claim is never strong, only medium at best.

**Missing adapter/contract**: ACIS's general ladder has no repair-specific tier
distinction between presence-only and before-and-after evidence; CRAIF-00 Part XV.2-XV.3
is exactly that missing refinement, currently living only inside CRAIF-00 rather than
folded back into ACIS's own general ladder where any future repair-adjacent system could
reuse it without re-deriving it.

**Integration point**: every VERIFIED/OBSERVED/INFERRED/HYPOTHESIS/PROPOSED/REJECTED
marking across all three CRAIF datasets uses ACIS's own vocabulary unmodified; CRAIF adds
zero new evidence-tier terms, only a domain-specific admissibility rule for when a term
applies.

**Test/eval**: audit every evidence-status marking in CRAIF-00/01/02 (there are dozens)
and confirm each resolves to one of ACIS's own defined tiers with no undefined term
introduced — a mechanical grep-based check, not a judgment call.

**No-duplication proof**: CRAIF-00 15.1 states this explicitly: "CRAIF does not define a
new evidence-tier taxonomy; it composes the estate's existing epistemic ladder... and adds
exactly one refinement."

**Done-gate**: ACIS's own maintainers confirm the presence-vs-before-and-after refinement
is either (a) already implied by an existing ACIS tier and CRAIF's restatement is
redundant, requiring CRAIF-00 XV to cite the existing ACIS tier directly instead of
restating it, or (b) a genuine gap ACIS did not yet cover, in which case this package's
writeback is the candidate amendment.

**Target**: writeback proposed — submit CRAIF-00 Part XV.2-XV.4 to ACIS's maintainers as a
candidate refinement to the general ladder (a repair-claim-specific before-and-after
admissibility rule), pending Owner review of whether it belongs in ACIS itself or remains
a CRAIF-local specialization cited by reference.

---

## 7. UKDL-and-Knowledge-Vault Learning-Closure Package

**Owner**: `vault/knowledge_base/ukdl-universal.md` and the broader knowledge-vault
learning-closure infrastructure (Hard Rules / Process Rules / Traps extraction).

**Mechanism strengthened**: UKDL is the estate's existing mechanism for turning a session's
discoveries into durable, checkable rules; CRAIF-01's Learning Candidate and Guardian
Promotion Candidate objects (CRAIF-00 Part VII) are exactly the shape of input UKDL's own
extraction process consumes, but CRAIF currently has no explicit handoff contract
specifying which of a repair's outcomes become a UKDL entry versus an IAS-D2 guardian
versus both.

**Missing adapter/contract**: a Learning Candidate needs an explicit routing rule — a
repair pattern that recurred across projects (Part XIV.6's cross-project validation)
routes to IAS-D2 for immune-memory promotion per Package 4 above; a repair pattern that
reveals a new Hard Rule-shaped constraint (a class of mistake CRAIF itself should never
repeat, distinct from a pattern the immune system should recognize) routes to UKDL instead.
The two routes are not mutually exclusive, but CRAIF-01 Part XIV names only the first
explicitly.

**Integration point**: CRAIF-01's Learning Handoff (Part XIV) is proposed to gain an
explicit UKDL-routing branch alongside its existing Guardian-Promotion branch, consuming
UKDL's own existing Hard Rule / Process Rule / Trap categories rather than inventing a
fourth CRAIF-specific category.

**Test/eval**: replay Fixture Five (Owner Intervention Escape) as a Learning Candidate and
confirm it routes to UKDL as a Hard-Rule-shaped finding — "root-cause analysis stopping at
the component" is a process defect, not an immune-memory pattern, and should never be
routed to Package 4's channel instead.

**No-duplication proof**: CRAIF defines no rule-storage format of its own anywhere in its
three datasets; every Hard Rule this corpus itself cites (HR-SECRET-*, HR-CASCADE-*, etc.
in the surrounding project CLAUDE.md) is read from the existing vault, never restated as a
CRAIF-owned rule.

**Done-gate**: this corpus's own required UKDL writeback (per the family's build order) —
a Hard Rules / Process Rules / Traps extraction from CRAIF's own founding session —
demonstrates the routing branch this package proposes, using CRAIF's own construction as
the first worked instance.

**Target**: writeback proposed — the routing branch itself is a candidate amendment to
CRAIF-01 Part XIV (dataset-internal, pending a future revision cycle) and, separately, the
actual UKDL writeback this corpus owes per the family manifest, produced at Phase 3 sealing.

---

## 8. JIT-and-Activation-Simulation Package

**Owner**: the JIT skill loader (latent-card + full-body mechanism) and the SKILL.md
capability-manifest surface.

**Mechanism strengthened**: the JIT loader already implements a partial answer to
CRAIF-02's own Trigger-visibility science — a compact, always-loaded card with the full
body loaded only on a matching trigger — but has no standing mechanism to be tested
hermetically against the taxonomy of bootstrap defects CRAIF-02 Part IV catalogues, and no
Capability Pointer (CRAIF-02 Part VIII) tracking which repository profiles a given skill's
activation has actually been verified against.

**Missing adapter/contract**: the loader has no visibility-audit hook — no standing check
that a new skill's card actually satisfies CRAIF-02 Part III's externality-and-
evaluability test before the skill is registered, meaning a future Fixture-One-shaped
defect could re-enter the estate exactly the way the original did.

**Integration point**: CRAIF-02 Part III.5 and Part XV.2 name this integration explicitly:
CRAIF-02 supplies the visibility-audit procedure and the Part IV taxonomy as a diagnostic
the loader's own maintainers may apply to any new skill before registration; the loader
itself is never forked or reimplemented.

**Test/eval**: run CRAIF-02's own Simulation Harness (Part X), once built, against every
skill currently registered in the estate's SKILL.md catalogue as a live visibility-and-
evaluability audit, and report any skill whose Trigger fails either test — this is the
concrete, checkable version of the manual thirty-project audit Fixture Four's own
discovery required.

**No-duplication proof**: CRAIF-02 Part I.9 states this explicitly: "CRAIF-02 does not
rebuild, replace, or fork any part of that existing loading infrastructure... the loader
itself... belongs to whichever module or skill currently owns that code."

**Done-gate**: every skill in the estate's own catalogue has a Capability Pointer entry
(CRAIF-02 Part VIII.2) recording at least the home-repository profile as directly
verified, closing Fixture Four's own gap without requiring another manual audit.

**Target**: dataset-internal — CRAIF-02 Parts III, VIII, XV already specify the full
mechanism. Writeback pending: the Simulation Harness's actual construction (explicitly
out of scope for this dataset-authoring phase per the family's executable-runtime
deferral) and its first real run against the live SKILL.md catalogue, gated on a future,
separately Owner-approved implementation phase.

---

## Cross-Package Discipline

No package above proposes a direct edit to any sealed corpus. Each is a candidate
amendment or a candidate first-application, requiring the named owner's own review and
acceptance before any sealed dataset changes. Three packages (4, 6, 7) are pure writeback
proposals with no CRAIF-internal Part yet satisfying them; five packages (1, 2, 3, 5, 8)
already have their mechanism fully specified inside a CRAIF Part, with only the writeback
artifact — the note the real owner would actually receive — still pending. This asymmetry
is expected and not a gap: CRAIF-00/01/02 were authored to be self-sufficient as a
specification first, per the family's dataset-first convention; the writeback half is
Phase 3-and-beyond work, tracked in `CRAIF_INDEX.md`'s governance artifacts table.
