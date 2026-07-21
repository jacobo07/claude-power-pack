# CRAIF Adversarial Review — Phase 3

> Scope: stress-test the CRAIF-00/01/02 specification (61,355 words, 53/53 Parts, sealed
> 2026-07-21) against named attack classes. Section A compiles every failure mode already
> named inside the three sealed datasets, cross-referenced rather than restated, confirming
> each carries a design response. Section B is the genuinely adversarial pass: attack
> vectors this review found that no CRAIF Part yet names, each resolved to either a design
> response, a proposed patch, or an explicit accepted residual risk. Section C checks the
> corpus's own constitutional invariants (CRAIF-00's Three Laws, non-duplication boundary)
> as the kill-switch set this family actually seals, rather than assuming an external list
> this document cannot independently verify. Section D is the verdict.

---

## Section A — Compiled Catalogue (24 named failure modes, cross-referenced)

Every entry below already has a full design response inside a sealed Part; this section
exists to confirm coverage and pairing discipline, not to re-derive the response.

**Verification / authority axis**
1. FALSE HEALING — CRAIF-00 14.2. Response: mandatory Activation Verification Contract for
   activation-scoped Findings (CRAIF-02 Part XII).
2. SELF-GRANTED AUTHORITY — CRAIF-00 14.3. Response: Law 3 (no self-certification) + Part V
   validation rule rejecting an Authority Decision whose evidence resolves to CRAIF's own
   prior output.
3. SCANNER-VERIFIER COLLUSION — CRAIF-00 14.5. Response: Part VI requires an independent
   check (SQI, liveness) wherever one exists, never the producer's own re-assertion.
4. LOCAL-TO-GLOBAL PROMOTION ERROR — CRAIF-00 14.6. Response: Part VII's fixed sequencing
   — local observation, local recurrence, cross-project validation, then proposal only.
5. EMERGENCY-STOP BYPASS — CRAIF-00 14.7. Response: any future L4 policy must prove
   emergency-stop coverage coextensive with its own authorization scope before taking
   effect.
6. METRIC-DRIVEN CANDIDATE AVOIDANCE — CRAIF-00 14.9. Response: standing comparison of
   attempted-Finding difficulty distribution against surfaced-Finding distribution.

**Transaction lifecycle axis**
7. RETRY exhaustion — CRAIF-01 15.x. Response: bounded retry with escalation, not infinite
   loop.
8. TIMEOUT (hung transaction) — CRAIF-01 15.x / Part II.5. Response: per-state time bounds,
   not one overall timeout.
9. PARTIAL FAILURE — CRAIF-01 Part XV. Response: any verification-state failure transitions
   directly to CLOSED-ROLLED-BACK from any point after SNAPSHOT-TAKEN.
10. FAILED ROLLBACK — CRAIF-01 Part XV. Response: escalates to Owner rather than retrying
    the same rollback mechanism blindly.
11. STALE INTENT — CRAIF-01 Part XV / CRAIF-00 Part III. Response: staleness re-validated
    at Evidence Freeze, not trusted from Intake.
12. CONCURRENT COLLISION — CRAIF-01 Part XVI / Part XVIII. Response: Concurrent Repair
    Control and Idempotency governs overlapping-target transactions explicitly.
13. REPAIR THRASHING (runtime instance) — CRAIF-01 Part XVI / CRAIF-00 14.4. Response:
    recent Incident Closure history checked before opening a fresh transaction against the
    same target.
14. DEPENDENCY-UNAVAILABLE — CRAIF-01 Part XVI. Response: named failure state, not a silent
    hang.
15. EVIDENCE CORRUPTION — CRAIF-01 Part XVI. Response: frozen evidence retained unmodified
    as part of the eventual Repair Outcome regardless of closure path.

**Corpus / metric axis**
16. FALSE HEALING (metric) — CRAIF-00 Part XIII.8. Response: near-zero revocation rate
    treated as suspicious, not celebrated.
17. OVER-REFUSAL (metric) — CRAIF-00 13.4. Response: refusal-rate countermetric attached to
    the false-positive term at definition time.

**Activation axis (CRAIF-02)**
18. FALSE POSITIVE ACTIVATION FINDING — Part 14.2. Response: Simulated Session fidelity
    review; harness self-validation cadence (Part 10.7).
19. FALSE NEGATIVE ACTIVATION FINDING — Part 14.3. Response: corpus case authored against
    the capability's actual Trigger logic, not an assumed simplification.
20. SESSION-RESTART DRIFT — Part 14.4. Response: named explicitly as an unlicensed
    continuity assumption; no segment may rely on it.
21. WORKTREE DRIFT — Part 14.5. Response: named as the shared-repository twin of 14.4;
    Repo Profile comparison is structural, not moment-of-use.
22. SILENT MUTUAL SUPPRESSION — Part 7.8. Response: harness corpus required to include a
    joint-replay case for every known overlapping-Trigger pair.
23. PROFILE OVERFITTING — Part 8.9 / 8.11. Response: a verified-profile entry must name the
    characteristic tested, not merely the repository.
24. BUDGET STARVATION BY VOLUME — Part 9.6. Response: Context Cost metric surfaces the
    aggregate the per-capability audit cannot see.

**Pairing-discipline check**: CRAIF-00 14.8 and CRAIF-02 14.8 both state the same rule —
no mechanism's threshold may be tightened against one pole of a failure without measuring
the effect on its paired pole. Spot-check: item 18 (false positive) and item 19 (false
negative) are explicitly paired inside CRAIF-02 14.8 itself; item 16 and 17 are explicitly
paired inside CRAIF-00 13.4. No item above is addressed by a design response that ignores
its paired opposite — verified by re-reading each cited subsection's own text rather than
by name-matching alone.

---

## Section B — Newly-Surfaced Attack Vectors

These were not named in any CRAIF-00/01/02 Part before this review. Each is resolved below;
none are left as a bare open question.

### B1. Authority-ladder gaming by sequential splitting

**Attack**: an actor who wants to make a change too large or ambiguous to qualify for L3
under CRAIF-00 Part VIII's conjunctive test splits it into many small sub-changes, each
individually satisfying all five L3 conditions (unambiguous ownership, proven rollback,
Tipo A, deterministic verification, active observability) in isolation, cumulatively
achieving an outcome the whole change, submitted at once, would never have cleared.

**Assessment**: CRAIF-00 Part VIII scopes eligibility per Repair Candidate, not per
cumulative session or per Finding lineage, and no CRAIF-01 Part currently checks whether a
sequence of small, individually-eligible transactions targets the same underlying object
or Failure Pattern in aggregate. This is a genuine gap, structurally distinct from Part
7.8's Silent Mutual Suppression (which concerns Trigger interaction, not authority
splitting) and distinct from CRAIF-01 Part XVI's Repair Thrashing (which concerns
recurrence after a closed transaction, not concurrent decomposition before any transaction
opens).

**Response — proposed, not yet dataset-internal**: CRAIF-01's Intake (Part III) should
check a new Repair Intent's target against any other Intent opened within a bounded recent
window whose target overlaps at the level of a shared parent object (a directory, a
capability family, a shared configuration file), and require the aggregate blast radius of
overlapping-window Intents — not any single Intent's own radius — be re-evaluated against
DRK's classification before a second or later Intent in the window may proceed at L3. This
patch is named here as PROPOSED per this corpus's own evidence discipline; it is not yet
written into CRAIF-01 and requires a future revision cycle, per CRAIF-00 16.8's amendment
discipline, before it binds.

### B2. Metric-gaming the anti-Goodhart countermetric itself

**Attack**: CRAIF-00 13.8 states a near-zero Certification Revocation rate is itself
suspicious, treated as evidence the False Healing countermetric may be too lax rather than
as good news. An actor aware of this rule could game the meta-level instead of the object
level: deliberately allow a small, harmless trickle of low-stakes revocations specifically
to keep the revocation rate in the "looks healthy" range, while the actual false-healing
rate on higher-stakes repairs remains suppressed through some other means the revocation
mechanism does not catch.

**Assessment**: this is a second-order attack on 13.4's own anti-Goodhart design — gaming
the metric that exists to catch gaming. CRAIF-00 Part XIII.5 already names an analogous
concern (a runtime with authority over its own measurement cadence widening its window) and
resolves it structurally by placing the measurement window outside the runtime's own
control, via CO-12. The same structural principle resolves B2: since the revocation count
itself is computed from Repair Certificates whose issuance and revocation both live in
CRAIF-01's ledger (Part XIII), and that ledger's own append-only, externally-observable
design (per CRAIF-00 12.4's Fixture Three lesson — self-report is not evidence) means a
"deliberately manufactured trickle" would itself require the runtime to selectively
under-verify a specific class of higher-stakes repair, which is precisely what CRAIF-00
Part VI's independent-check requirement (echoing item 3 above) already forecloses.

**Response**: no new mechanism required; item 2 (scanner-verifier collusion's response) and
item 16 already jointly close this vector, because gaming the revocation rate at the meta
level requires the identical object-level failure — an unverified self-report accepted as
verification — that Part VI already refuses to permit. Recorded here as a confirmed-closed
finding, not a residual risk, and cross-referenced from CRAIF-00 13.8 for future readers.

### B3. Corpus poisoning via open authorship

**Attack**: the D2A Package 5.11 note (`CRAIF_D2A_REINFORCEMENT_PACKAGES.md` §5, and
CRAIF-02 Part V.11 itself) opens corpus-case authorship to any capability author, not only
CRAIF-02's own maintainers. A careless or adversarial proposer could submit a corpus case
whose "expected trace" field is subtly wrong — claiming a defective capability's expected
trace shows correct completion — such that the harness, replaying that case, certifies a
still-broken capability as DEFECT-RESOLVED.

**Assessment**: CRAIF-02 Part V.11 already requires a proposed case's taxonomy tag be
"confirmed against Part IV rather than self-assigned by the proposing author," but this
confirms the tag, not the expected-trace field's own correctness — a real gap distinct from
anything Part V or Part X currently names.

**Response — proposed, not yet dataset-internal**: a corpus case's expected-trace field
should require independent construction or confirmation by a party other than the case's
own proposer before the case enters the standing corpus — the identical separation-of-
powers principle CRAIF-00 Part IX applies to a repair transaction, applied here to corpus
authorship itself, since an unverified expected-trace field is functionally equivalent to
letting a producer certify its own repair. This is named PROPOSED and requires a future
amendment to CRAIF-02 Part V before it binds.

### B4. Concurrent authority acquisition across worktree panes

**Attack**: the estate's own documented multi-pane, shared-worktree operating pattern
(`feedback_check_sibling_commits_before_refactor.md`, `feedback_g2_reviewer_rebase_race`
in this project's own governance) means two panes could each independently open a Repair
Intent against the identical target, each pass Intake and Precondition Checking against a
state neither has seen the other mutate, and each acquire authority concurrently — a
double-repair race CRAIF-01 Part XVIII (Concurrent Repair Control and Idempotency) is
titled to address but which this review must confirm actually covers the specific
cross-pane case rather than only a single-process concurrency case.

**Assessment**: this is not a new failure mode in the sense of B1-B3 — CRAIF-01 Part XVIII
exists specifically for this — but this review flags a scoping question worth stating
explicitly for a future reader: whether Part XVIII's idempotency mechanism is verified
against the shared-`.git/index` race pattern this very project's own governance already
documents as real and recurring (pathspec-scoped commits exist because of it), or only
against a more generic, single-host concurrency model. This review did not re-read Part
XVIII's full text against that specific pattern during this pass.

**Response**: recorded as an open verification item, not a design gap — CRAIF-01 Part
XVIII's mechanism is PROPOSED per this corpus's own evidence discipline, and a future
audit pass should specifically replay the shared-`.git/index` scenario as a CRAIF-01
corpus case before this item is closed.

### B5. Harness-reality divergence ("teaching to the test")

**Attack**: a capability author aware of CRAIF-02's Simulation Harness could, deliberately
or through convenient coincidence, tune a capability's Trigger to pass exactly the specific
Simulated Session conditions the standing corpus exercises (per Part V) while behaving
differently under a real Intent phrased even slightly outside the corpus's own coverage —
optimizing for the test rather than for genuine activation correctness.

**Assessment**: this is distinct from False Positive/Negative Activation Finding (Part
14.2-14.3), which concern the harness's own diagnostic accuracy; B5 concerns a capability's
own design being shaped around the harness's known coverage rather than around genuine
correctness. CRAIF-02 Part VI.10 already names a related concern — Ambiguous-case
proportion as a systemic underspecification signal — but does not name this specific
gaming vector.

**Response — proposed, not yet dataset-internal**: CRAIF-02's harness should reserve a
held-out subset of synthetic cases, generated per Part V.3's discipline but never disclosed
to capability authors before a capability's own submission, specifically to catch Trigger
designs over-fit to the disclosed corpus — the identical held-out-test-set principle used
against overfitting generally, applied here to activation-chain testing. Named PROPOSED,
requiring a future amendment to CRAIF-02 Part V and Part X before it binds.

---

## Section C — Constitutional Invariant Cross-Check

This corpus's own binding invariants, verified against the sealed text rather than assumed
from memory of the original founding directive (whose full 16-item kill-switch list is not
independently re-verifiable in this review's own context):

- **Law 1 (Institutional Existence)** — CRAIF-00 Part X. Confirmed present, unmodified,
  cited by CRAIF-01 Part I.2 and CRAIF-02 Part I.1 by cross-reference rather than restated.
- **Law 2 (Escape Attribution)** — CRAIF-00 Part X, Part XIII.7's worked OIER example.
  Confirmed present; Fixture Five (Part XII) is its founding evidence.
- **Law 3 (No Self-Granted Authority)** — CRAIF-00 Part X, Part V's validation rule, Part
  XIV.3's failure-mode entry. Confirmed present and enforced at the object level (a
  rejected field state), not merely stated as prose.
- **Non-duplication boundary (Part XI)** — checked against all three datasets' own Part XI/
  XV Integration Contracts sections; no CRAIF Part was found, on this pass, defining a
  shadow object, a forked mechanism, or an independent ontology for any of the nine
  explicitly excluded domains (reachability, drift, test-reach, blast radius/reversibility,
  immune taxonomy, D2A doctrine itself, rollback mechanics, escalation queueing, epistemic
  ladder).
- **Evidence discipline (Part XV)** — spot-checked across roughly a dozen VERIFIED/
  OBSERVED/PROPOSED markings across all three datasets; none asserts VERIFIED without
  naming a specific reproduction, consistent with Part XV.6's own requirement.

**Explicit limitation of this section**: the founding directive that chartered CRAIF named
16 specific kill-switches; this review's own context does not carry a verified verbatim
copy of all 16 to check against individually, and fabricating a 16-item list to appear
complete would itself violate this corpus's own Reality Contract. The five invariants above
are the ones independently re-derivable from the sealed corpus text itself, and this
section's honest scope is limited to them. A future session with access to the original
founding directive's full text should re-run this cross-check against the literal 16-item
list and record any gap found.

---

## Section D — Verdict

Twenty-four previously-named failure modes checked: all carry a design response, and the
family's own pairing discipline (no mechanism tightened against one failure pole without
checking its paired pole) holds on spot-check. Five new attack vectors surfaced: two
(B2, B4) resolve to an existing mechanism already closing them or an open verification item
rather than a gap; three (B1, B3, B5) are genuine gaps, each given a named, scoped, PROPOSED
patch rather than left as a bare finding — none of the three requires a new dataset or a new
object family, each is a bounded amendment to an existing Part (CRAIF-01 Part III for B1,
CRAIF-02 Part V for B3, CRAIF-02 Part V and Part X for B5). No CRITICAL finding — nothing
here indicates the corpus's own constitutional invariants (Section C) are violated by any
of the five new vectors, since B1, B3, and B5 are all gaps in a not-yet-built runtime and
harness's operational discipline, not gaps in the constitution governing them. Recommended
disposition: defer B1/B3/B5 patches to the runtime's and harness's own future implementation
phase (both explicitly out of scope for this dataset-authoring session), record them here
as binding requirements on that future phase rather than optional suggestions, and proceed
to the family's Production Reality Gate report with this review as satisfied for the
dataset-authoring phase's own scope.
