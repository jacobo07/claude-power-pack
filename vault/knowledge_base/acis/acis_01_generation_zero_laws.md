# ACIS-01 — Generation Zero Candidate Laws

> **Epistemic status of this entire dataset: E2.** Every law below is a *hypothesis with a
> mechanism*, not a truth. Fable authored them and Fable attempted to destroy them; that is the
> most a single model may do. None is E3 until a probe or a second substrate re-derives it; none
> is E4 until the Owner promotes it. Per `T-ACIS-MODEL-CONSENSUS-001`, the destruction attempts
> below are *not* independent validation — they are the author stress-testing its own claim, and
> a surviving law is still only a stronger hypothesis. **Provenance:** ACIS Generation Zero
> session, 2026-07-11; each law's `question_ref` is recorded in its record.
>
> **Reading protocol:** a law that formalizes already-sealed doctrine carries a `genealogy`
> pointer and is *not* claiming novelty — its contribution is the falsifiable *form*, not the
> insight. A law with no genealogy pointer is a genuinely new claim and is held to a higher bar
> of suspicion.

---

## LAW-01 — Avoidable Irrepeatability

- **id:** `ACIS-LAW-REPEAT-01` · **version:** 1 · **domain:** repeatability · **level:** E2
- **claim:** Every reasoning result a frontier model produces is either (a) reducible to a
  re-runnable artifact — a rule, an asset, a probe, a deterministic checklist — or (b) an
  irreducible act of that model's judgment. The fraction that is (a) but is *not* captured is
  **avoidable irrepeatability**, and it is pure loss: the same tokens will be spent again to
  re-derive it.
- **causal_mechanism:** a result that can be stated as a stable input→output mapping does not
  require the model that first found the mapping; leaving it uncaptured forces re-derivation,
  which is why the FD loop's open feedback edge (capture-without-close) shows up as a flat CO-12
  ratio despite a growing vault.
- **application_conditions:** the result has a statable trigger and a checkable outcome.
- **failure_conditions:** genuinely irreducible judgment (novel synthesis, aesthetic verdict,
  a first-of-its-kind architectural call) — capturing *that* as a rule produces a brittle
  overfit, not an asset.
- **predictions:** forbids a stack from having both a high deposit rate and a flat dependence
  curve *unless* the deposits are of type (b); if type-(a) results are being re-derived across
  sessions, the fingerprint stream will show repeats.
- **falsifiers:** observe a class where the same fingerprint is deposited across ≥3 sessions
  *and* a capture artifact for it already exists on disk — that refutes "uncaptured," meaning
  the loss is not avoidable-irrepeatability but something else (a navigation failure). Or:
  observe re-derivation cost *rise* after capture — that refutes "capture removes the cost."
- **counterexamples:** a rule captured too eagerly that later needed three amendments — the
  capture was real but the boundary (failure_conditions) was wrong, not the law.
- **evidence:** FD-07 no-progress-fingerprint failure mode (deposits repeat, gap flat) is the
  predicted signature. `(fingerprint-repeat-count, fd07 deposits ledger, observed)`.
- **derivations:** the FD-04 prover (captures type-(a) as re-runnable probes); the FD-05
  determinization arbitrage.
- **production_impact_chain:** law → "capture type-(a) results as probes" → FD-04 prover exists
  → a Claude Code session re-runs the probe instead of re-asking Fable → frontier call avoided
  → CO-12 Opus-avoided count rises → revision if it does not.
- **confidence:** 0.8 · **genealogy:** FD-00 root law + FD-07 flywheel closure (§stage 9).
- **retirement_conditions:** retired if a capture mechanism is shown to cost more to maintain
  than the re-derivation it prevents across a representative class (capture is net-negative).
- **DESTRUCTION ATTEMPT:** *"All reasoning is irreducible judgment; the (a) fraction is empty,
  so the law is vacuous."* — Refuted by existence: the fd_04 prover already captured 5 deposits
  as re-runnable probes this month; those are type-(a) by demonstration. The (a) fraction is
  non-empty, so the law has content. **Survives, weakened to:** the law does not claim the (a)
  fraction is *large* — only that it is real and that its uncaptured part is avoidable loss.

## LAW-02 — Limited Compression

- **id:** `ACIS-LAW-COMPRESS-01` · **version:** 1 · **domain:** compression · **level:** E2
- **claim:** For any captured capability there is a floor below which further compression
  destroys the capability. The floor is **strictest for a deterministic target** (any quality
  loss falsifies a zero-loss promise) and **graded looser toward the model target** (a
  "close-to-frontier, much cheaper" promise tolerates a defined margin).
- **causal_mechanism:** compression discards information; a deterministic promise is that *no*
  information relevant to the output was discarded, so a single wrong output falsifies it,
  whereas a model-target promise was probabilistic from the start and survives bounded loss.
- **application_conditions:** the capability has a measurable output quality.
- **failure_conditions:** capabilities whose output is not gradeable (pure routing decisions
  with binary correctness collapse the "graded margin" to zero — they behave like deterministic
  targets).
- **predictions:** forbids a deterministic-target capability from surviving *any* six-lens
  critical-lens loss; predicts a DEGRADED verdict the instant one appears.
- **falsifiers:** a deterministic-target capability that passes with a critical-lens loss
  present — that refutes the zero-loss floor. Or: a model-target capability that fails on the
  *first* token of margin — that refutes the graded-looser claim.
- **counterexamples:** a deterministic checklist that "lost" a step but the step was redundant —
  apparent loss, real survival; resolved by grading only critical lenses.
- **evidence:** FD-04 dataset lines 716-718 (deterministic verdict admits zero critical loss).
  `(critical-lens-loss, FD-04 six-lens grade, DEGRADED)`.
- **derivations:** the FD-04 Compression Loss Gate; the per-target threshold table.
- **production_impact_chain:** law → per-target thresholds in FD-04 → a compressed asset is
  graded against its target's floor → over-compressed assets rejected before shipping → no
  silent quality regression in production.
- **confidence:** 0.75 · **genealogy:** FD-04 §compression-loss + II.10.
- **retirement_conditions:** retired if a compression method is found that provably preserves
  all critical-lens information at the deterministic floor for a non-trivial class (the floor
  moves to zero for that class).
- **DESTRUCTION ATTEMPT:** *"The floor is just 'don't lose quality' — trivially true, no
  content."* — The content is not the floor's existence but its **inversion**: intuition says
  the model target (fuzzier) should tolerate *less* rigor, but the law asserts the opposite —
  the deterministic target is strictest because its promise is absolute. That inversion is
  non-obvious and testable. **Survives.**

## LAW-03 — Imperfect Transfer

- **id:** `ACIS-LAW-TRANSFER-01` · **version:** 1 · **domain:** transfer · **level:** E2
- **claim:** A capability distilled on the frontier model transfers to a weaker substrate with a
  loss that is *bounded and measurable*, never zero and never total. A claim of *perfect*
  transfer is a measurement failure (the test did not exercise the hard cases); a claim of
  *total* failure is usually a prompt/context artifact, not a capability limit.
- **causal_mechanism:** the weaker substrate lacks some of the frontier model's latent capacity;
  what transfers is the part the distilled artifact made explicit, what is lost is the part that
  remained implicit in the model's judgment. Since real artifacts are neither fully explicit nor
  fully implicit, transfer is partial.
- **application_conditions:** a distilled artifact and at least two substrates to compare.
- **failure_conditions:** a fully deterministic artifact (a checklist) transfers *without* loss
  because nothing was left implicit — this is the intended endpoint of determinization, and it
  is the boundary where LAW-03 stops applying and LAW-02's deterministic floor takes over.
- **predictions:** forbids a distilled-but-non-deterministic capability from scoring identically
  on frontier and mid-model in a sufficiently hard test set; predicts a gap that shrinks as the
  artifact is made more explicit.
- **falsifiers:** a non-deterministic distilled capability scoring *identically* across
  substrates on a test set that includes its known-hard cases — refutes "never zero loss." Or: a
  capability where making the artifact more explicit does *not* shrink the transfer gap —
  refutes the mechanism.
- **counterexamples:** an artifact that transferred perfectly — on inspection it had been fully
  determinized, so LAW-03 never applied (boundary, not counterexample).
- **evidence:** FD-04 is named "Intelligence Decay & Transfer-Proof Detector"; the six-lens
  transfer test measures exactly this gap. `(cross-substrate-score-gap, FD-04, >0)`.
- **derivations:** fd_04_prover's `attest(substrate=...)` records which substrate re-derived a
  capability and with what evidence — the transfer measurement made concrete.
- **production_impact_chain:** law → measure transfer gap per capability → route the capability
  to the cheapest substrate whose gap is acceptable → CO-03 routing rule → frontier calls fall
  for that class.
- **confidence:** 0.7 · **genealogy:** FD-04 doctrine; CO-03 routing.
- **retirement_conditions:** retired if a non-deterministic capability is shown to transfer
  losslessly, collapsing LAW-03 into LAW-02.
- **DESTRUCTION ATTEMPT:** *"'Bounded and measurable but never zero' is unfalsifiable hedging —
  any result fits."* — Not so: it makes two sharp forbidden predictions (no perfect transfer for
  non-deterministic artifacts; no total failure that survives a prompt/context fix). Either can
  be observed and would refute the law. **Survives, but flagged:** the "never total" half is
  weaker than the "never zero" half and should be split into its own law if a total-failure case
  ever resists a prompt fix.

## LAW-04 — Cognitive Debt

- **id:** `ACIS-LAW-DEBT-01` · **version:** 1 · **domain:** debt · **level:** E2
- **claim:** A capability that is *used* but not *captured* accrues cognitive debt — the ongoing
  frontier-token cost of re-deriving it — and the debt compounds because each re-derivation also
  fails to capture. A stack's total cognitive debt is a leading indicator of dependence, visible
  *before* the cost shows in the budget.
- **causal_mechanism:** re-derivation without capture is the degenerate-feedback loop (CWOPS
  §4.6): the stack pays for the same reasoning repeatedly and the payment itself produces no
  asset, so the cost recurs with interest (the interest = the compounding sessions that could
  have started from a higher floor but did not).
- **application_conditions:** a capability invoked across ≥2 sessions.
- **failure_conditions:** a capability invoked exactly once ever — no recurrence, no debt (it
  was a one-time judgment, correctly not captured).
- **predictions:** forbids the dependence metric from being flat while re-derivation is
  occurring; predicts that classes with high frontier-call-admitted counts and no deposits are
  the debt hot-spots.
- **falsifiers:** a class re-derived every session whose frontier cost does *not* rise and whose
  dependence contribution is flat — refutes "debt compounds." Or: capturing a high-debt class
  and observing *no* fall in its frontier calls — refutes the mechanism.
- **counterexamples:** a class that looked like debt but was genuinely novel each time (a
  changing external API) — recurrence without repeatability; the debt was illusory.
- **evidence:** the FD-00 admission log read as a worklist (III §"a class that repeatedly returns
  ADMIT for the same reason is the prime candidate for a distilled replacement").
  `(admit-count-per-class, frontier_call_admitted signals, observed)`.
- **derivations:** the Cognitive Leak Taxonomy (C70) is the debt detector for the non-token axis;
  FD-05 arbitrage is the debt-repayment mechanism.
- **production_impact_chain:** law → read the admission log as a debt ledger → highest-debt class
  is next to determinize → FD-05 converts it → debt repaid, dependence falls.
- **confidence:** 0.75 · **genealogy:** CWOPS §4.6; Cognitive Leak Taxonomy C70; FD-05.
- **retirement_conditions:** retired if a high-recurrence, high-cost, uncaptured class is shown
  to have *falling* cost over time without capture (the debt self-amortizes).
- **DESTRUCTION ATTEMPT:** *"Debt is just LAW-01 (avoidable irrepeatability) restated."* — Real
  overlap, but LAW-04 adds the **compounding** claim (debt grows, not just persists) and the
  **leading-indicator** claim (visible before the budget). Those are separable and separately
  falsifiable. **Survives, but MERGE-flagged:** if the compounding claim fails its falsifier,
  LAW-04 collapses into LAW-01 and should be retired via D2A `MERGE`.

## LAW-05 — Marginal Saturation

- **id:** `ACIS-LAW-SATURATE-01` · **version:** 1 · **domain:** saturation · **level:** E2
- **claim:** Within a bounded domain, the marginal delta a frontier session extracts falls
  monotonically toward zero; past the saturation point every additional frontier token buys
  a result the stack could already produce. The saturation point is *detectable in-session*
  before the budget is spent.
- **causal_mechanism:** a session extracts the highest-leverage deltas first (FD-02 ranks them);
  as the admitted questions are answered, the remaining ones route ROUTE_CHEAPER/DECLINE because
  the floor now covers them — the gate verdict *is* the saturation signal.
- **application_conditions:** a session with a ranked question portfolio and a floor.
- **failure_conditions:** an unbounded or shifting domain (external reality changed) — the delta
  can re-open, so saturation is not monotonic there.
- **predictions:** forbids a saturated session (all-remaining ROUTE_CHEAPER/DECLINE) from
  producing a NEW above-floor delta; predicts that pushing past saturation yields DUP deposits.
- **falsifiers:** a session where, after all questions route cheaper, a further frontier push
  *does* yield a NEW above-floor delta on the *same* bounded domain — refutes monotonicity.
- **counterexamples:** a "saturated" session that later yielded a delta — inspection showed the
  domain had shifted (new external constraint); boundary, not counterexample.
- **evidence:** Session #2 (2026-07-11) stopped correctly at saturation — 1 ADMIT answered, all
  others ROUTE_CHEAPER/DECLINE. `(remaining-verdicts, SESSION_ZERO gate, all-cheaper-at-stop)`.
- **derivations:** the FD-00 stopping criteria; the FD-07 no-progress-fingerprint stop.
- **production_impact_chain:** law → stop the session at saturation → tokens not spent on DUP
  deposits → the emergency budget category is preserved for genuinely open domains.
- **confidence:** 0.8 · **genealogy:** FD-00 §stopping criteria; FD-07 II.2.
- **retirement_conditions:** retired if the gate verdict is shown to be a poor saturation proxy
  (frequent NEW deltas after an all-cheaper verdict on a stable domain).
- **DESTRUCTION ATTEMPT:** *"Monotonic decline is false — creative leaps come late."* — The law's
  escape hatch is `failure_conditions`: a late leap almost always rides a *shifted* domain (new
  information entered), which the law explicitly excludes. The hard test is a leap on a provably
  *unchanged* bounded domain. That is the falsifier, and it has not been observed. **Survives,
  sharpened:** the burden is on any late delta to prove the domain did not shift.

## LAW-06 — Mandatory Writeback

- **id:** `ACIS-LAW-WRITEBACK-01` · **version:** 1 · **domain:** writeback · **level:** E2
- **claim:** A delta not written back to a location a *future session will navigate to* has zero
  compounding value regardless of its quality — an unwritten insight and a wrong insight are
  economically identical (both leave the next session's floor unchanged).
- **causal_mechanism:** compounding requires the next session to start from a higher floor;
  the floor rises only if FD-01 subtracts against a baseline that *includes* the delta; that
  inclusion happens only if the delta was written to a navigated location — otherwise stage 9 of
  the flywheel stays open and the loop "stalls into a log file."
- **application_conditions:** any extracted delta intended to compound.
- **failure_conditions:** a delta deliberately kept ephemeral (a one-session scratch result) —
  it was never intended to compound, so the law does not judge it.
- **predictions:** forbids the floor from rising after a session that wrote nothing to a
  navigated store; predicts that deltas written only to un-navigated locations (a stray note, an
  un-indexed file) fail to raise any future floor.
- **falsifiers:** a delta written *only* to an un-navigated location that nonetheless raises a
  future session's floor — refutes "must be navigated." Or: a high-quality delta written
  nowhere that still reduces future frontier calls — refutes the economic-equivalence claim.
- **counterexamples:** a delta written to a navigated store that *still* did not compound —
  inspection showed the store was navigated but the FD-01 baseline was stale (didn't reload it);
  a time-effect, not a writeback failure.
- **evidence:** FD-07 canonical failure "stalls into a log file" (deposits accrue, gap flat, no
  session navigates to them). `(floor-delta-after-unwritten-session, FD-01 baseline, ~0)`.
- **derivations:** FD-06 writeback execution; GK-08 session-writeback Stop hook; the UKDL
  candidate ledger (a navigated store).
- **production_impact_chain:** law → every session's Stop hook writes deltas to a navigated store
  → next session's FD-01 subtracts against the raised floor → the same delta is not re-extracted
  → dependence falls.
- **confidence:** 0.85 · **genealogy:** FD-06/FD-07; GK-08; SCS C41.
- **retirement_conditions:** retired if compounding is shown to occur *without* writeback (e.g.
  the model's own weights improve on the domain), which would move the moat off the loop.
- **DESTRUCTION ATTEMPT:** *"An unwritten insight the human remembers still compounds."* — In a
  human-carried process, yes; but ACIS's unit of compounding is the *stack's* floor, not the
  human's memory, and the stack's floor is provably unchanged by an unwritten delta. The law is
  scoped to the stack, and within that scope it holds. **Survives, scoped explicitly:** "zero
  compounding value" means *to the stack*, and the stack is the moat, not the operator.

## LAW-07 — Operational Evidence

- **id:** `ACIS-LAW-EVIDENCE-01` · **version:** 1 · **domain:** evidence · **level:** E2
- **claim:** No capability claim is stronger than the evidence its pipeline position licenses; a
  claim asserted above its evidenced level is not optimistic — it is *false*, because the gap
  between asserted and evidenced level is exactly a lie about what was verified.
- **causal_mechanism:** the epistemic ladder derives level from disk artifacts (deposits, proofs,
  rules); a claim that asserts E4 while only an E2 deposit exists is contradicted by the disk,
  and a claim contradicted by its own substrate is false by inspection, not merely unproven.
- **application_conditions:** any claim about a capability's status.
- **failure_conditions:** none within scope — this is the law that has no failure condition
  *by design*, which is itself suspicious and flagged below.
- **predictions:** forbids a "done/proven/shipped" claim whose evidenced level (per the derived
  function) is below the asserted one; predicts that every such claim, on audit, resolves to a
  missing artifact.
- **falsifiers:** a claim correctly asserted at E4+ for which *no* Owner-authored rule and *no*
  Hard Rule exists on disk — that would refute "level is derivable from artifacts," meaning
  level can be legitimately asserted without a referent. This is the sharpest self-test.
- **counterexamples:** a claim that felt E4 but was E3 — the ladder correctly capped it; the
  feeling was the error, not the law.
- **evidence:** CO-12 Telemetry-Before-Claims contract; every FD guarantee carries a
  `(metric, source, value)` triple or is a hypothesis. `(asserted-vs-derived-level-gap, ladder,
  0-required)`.
- **derivations:** the No-Autopromotion Invariant (ACIS-00 I.2); `V-NO-AUTOPROMOTION`.
- **production_impact_chain:** law → the derived function computes evidenced level → a done-claim
  is gated against it → over-asserted claims are blocked before shipping → the Reality Contract
  holds at every done-gate.
- **confidence:** 0.9 · **genealogy:** CO-12; CO-10 honest guarantee levels; the Reality Contract.
- **retirement_conditions:** retired if level is shown to be *not* reliably derivable from disk
  artifacts (the function has irreducible false positives/negatives), which would move evidence
  back to human judgment.
- **DESTRUCTION ATTEMPT:** *"A law with no failure condition is dogma — you said so yourself in
  ACIS-00."* — **This is the strongest attack and it lands.** LAW-07 as stated has `none` for
  failure_conditions, which by ACIS's own retirement doctrine makes it a candidate dogma. The
  resolution: the *falsifier* is real and sharp (an E4 claim with no on-disk referent), so the
  law is falsifiable even though it claims no application boundary. But the absence of a failure
  condition means it claims universality, and LAW-03's mechanism warns that universal claims are
  usually false. **Survives at reduced confidence, explicitly flagged:** LAW-07 must be the
  *first* law Generation One tries to break, precisely because it is the one the author could not
  find a boundary for — and an unbroken boundary is more often unfound than absent.

## LAW-08 — Selective Determinization

- **id:** `ACIS-LAW-DETERM-01` · **version:** 1 · **domain:** determinization · **level:** E2
- **claim:** Not every capability should be determinized; the ones that should are exactly those
  whose input→output mapping is *stable* and whose recurrence is *high*. Determinizing an
  unstable mapping produces a brittle asset that costs more in maintenance than it saves;
  refusing to determinize a stable, high-recurrence mapping is the LAW-04 debt.
- **causal_mechanism:** a deterministic asset encodes a fixed mapping; if the true mapping drifts,
  the asset is wrong and must be maintained, so the asset's value = (recurrence × per-call
  saving) − (drift-rate × maintenance cost). The sign of that expression is what "should" tracks.
- **application_conditions:** a capability with an estimable recurrence and mapping-stability.
- **failure_conditions:** capabilities where stability cannot be estimated ex ante (novel
  domains) — the decision must wait for recurrence data.
- **predictions:** forbids a determinized unstable-mapping asset from having positive net value;
  predicts that such assets show up as high-amendment-rate rules.
- **falsifiers:** a determinized unstable mapping with *positive* net value over a representative
  window — refutes the value expression. Or: a stable high-recurrence mapping left un-determinized
  whose debt does *not* accrue — refutes the "refusing is debt" half.
- **counterexamples:** a rule amended often that was still net-positive — high recurrence
  outweighed the maintenance; the law's expression accommodates this (it is a sign test, not an
  amendment-count test).
- **evidence:** FD-05 arbitrage converts frontier-required parts to deterministic *only* when the
  mapping is stable; the D2A `DETERMINIZE` operation carries a regression-risk score.
  `(net-value-sign, FD-05 conversion outcomes, positive-when-stable)`.
- **derivations:** FD-05 anti-dependence arbitrage; CO-05 asset registry; D2A `DETERMINIZE`.
- **production_impact_chain:** law → estimate recurrence × stability per candidate → determinize
  only positive-net ones → CO-05 gains durable assets, avoids brittle ones → dependence falls
  without a maintenance-debt swap.
- **confidence:** 0.75 · **genealogy:** FD-05; CO-05; D2A operation set.
- **retirement_conditions:** retired if a maintenance-free method to determinize unstable
  mappings is found (the drift-cost term goes to zero), collapsing "selective" into "always."
- **DESTRUCTION ATTEMPT:** *"'Determinize the stable, high-recurrence ones' is obvious; no
  frontier session was needed."* — The obvious part is the direction; the content is the **value
  expression with the drift-rate term**, which predicts that some high-recurrence capabilities
  should *not* be determinized (when drift is high) — the non-obvious half. A stack that
  determinizes purely on recurrence will over-build brittle assets, which the law forbids.
  **Survives:** the counter-intuitive prediction (high recurrence can still be a "do not
  determinize") is the testable content.

---

## Part II — Contradiction Scan Across the Sealed Families

The Reality-Scan mandate to *detect contradictions in the existing architecture* — one thing
only a synthesis pass can do. Findings, each E1 (observation) pending confirmation:

1. **No hard contradiction found between FD, FIOS, CO, D2A, UKDL** on the axes scanned. The
   families are consistent because they were built on the shared "one system, no parallels"
   invariant (GK-00) and the shared CO-12 accountant.
2. **A latent tension, not a contradiction:** FD-00's no-bloat rule ("not every answer deserves
   a deposit") and LAW-06's mandatory-writeback pull in opposite directions at the margin — the
   first says write less, the second says write or lose. **Resolution (not a conflict):** they
   are the same rule at different levels — write back every delta *that clears the floor*, and
   nothing that does not. The no-bloat gate selects *what* is a delta; LAW-06 governs what
   happens to it *once selected*. Recorded as a genealogy note, not a defect.
3. **A verified redundancy the D2A engine would flag `MERGE`:** LAW-01 (avoidable
   irrepeatability) and LAW-04 (cognitive debt) share a core; LAW-04's independent content is the
   *compounding* + *leading-indicator* claims. If those fail their falsifiers, `MERGE → LAW-01`.
   Left separate at Generation Zero because the compounding claim is independently testable.

---

## Part III — Generation One Research Agenda (the open questions that threaten ACIS)

The unknown-unknown generator's output: questions whose answers could *invalidate* the theory,
ranked by how much of ACIS they would take down. These are E0 prompts for a future session —
**explicitly not resolved here**, because a model resolving its own invalidators is not
independent evidence (`T-ACIS-MODEL-CONSENSUS-001`).

1. **[threatens LAW-07, highest]** Is epistemic level *actually* reliably derivable from disk
   artifacts, or are there capabilities whose real status no on-disk artifact captures? If yes,
   the ladder has irreducible blind spots and the No-Autopromotion Invariant leaks. *Test: audit
   a sample of deposits for cases where the human-judged level and the derived level disagree.*
2. **[threatens the whole PLAN verdict]** Does making level explicit *change behavior*, or is it
   inert documentation? If sessions do not route differently once level is visible, ACIS-00 is a
   naming with no production impact and should be retired to REFERENCE. *Test: measure whether
   the derived level ever gates a done-claim in a real session.*
3. **[threatens LAW-05]** Can saturation be gamed — a session that declares saturation to stop
   early and bank budget, when a real delta remained? *Test: re-open a "saturated" bounded domain
   with a fresh model and check for above-floor deltas.*
4. **[threatens LAW-03/LAW-08]** Is the frontier/deterministic boundary *stable*, or does model
   improvement continuously move capabilities from "needs frontier" to "determinizable," making
   every determinization decision temporary? If the boundary drifts fast, selective
   determinization is a moving target and LAW-08's value expression needs a time-decay term.
5. **[threatens the model-consensus rule itself]** Is a *different model* genuinely independent
   evidence, or do frontier models share enough training that Opus re-deriving a Fable claim is
   weak validation? If model diversity is illusory, E5 needs a stronger independence criterion
   (production evidence, not a second model). *This question threatens `T-ACIS-MODEL-CONSENSUS-001`
   — the rule ACIS proposes — which is exactly why it must be asked.*
6. **[meta, threatens ACIS's own existence]** Is a self-evolving law system net-positive, or does
   the overhead of maintaining laws, levels, and falsifiers exceed the compounding they produce?
   The Safety Constitution's reversibility requirement means this must be answerable — and if the
   answer is negative, ACIS retires itself with genealogy, which is the system working as designed.

**Generation One escalation criterion:** open a multi-session ACIS campaign only if ≥3 of these
questions return ADMIT after a preflight (i.e. the floor does not already answer them). Today
that is untested — the agenda is the deliverable, not its resolution.
