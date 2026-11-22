# CPP-AIA-001 — Atomic Contracts, Durable Execution, Proof, Evaluation & Economics

**Status:** BACKLOG CONTRACT SPECIFICATIONS / UNIMPLEMENTED DELTAS UNTIL PROVEN. **Parent:** [master](2026-11-20_cpp-atomic-institutional-ascension-master.md). **Implementation:** extend existing owners rather than create a new cross-cutting source-of-truth. **Source:** Owner's 4 consolidated 2026-11-20 reports.
**Purpose:** preserve the exact technical claims (including caveats) of Atomic Engineering Ascension, Beyond the Agent Framework and Institutional Engineering At the Atomic Limit as implementable hypotheses.

## C01. The unit of change: Atomic Verified Transition (AVT)

**Definition:** smallest semantically complete transition whose cause, scope, authorization, effects and outcome can be judged independently. A physical file edit is not inherently an AVT, nor is an entire session necessarily one.

Symbolic definition: `AVT = (S_before, intent, preconditions, authority, effects, S_after, verdict)`.

Fields (logical, never a mandate to reserialize all existing GSD X records):
- `transition_id`, `goal_id`, `goal_revision`, `epoch_id`, `schema_version`.
- `subject` + `before_state_ref` + `after_state_ref`, including semantic vs observed/runtime distinctions.
- `intent` in original Owner terms, `precondition_refs` / `precondition_digest`, `postconditions`, `invariants`.
- `actor`, `authority_ref`, granted `scope`, `expiry`, `budget`, `resource_fence` when applicable.
- `effect_key` separate from `event_id`; `effect_status` (proposed/dispatched/observed/uncertain/reconciled).
- `proof_refs`, `judge_identity`, immutable verifier pins, environment/build/contract fingerprints.
- `outcome`, `residual_unknowns`, `causal_parents` and effects/knowledge produced.

**Composition rule:** T2 relying on T1 is permissible only where the proven postconditions of T1 entail the required preconditions of T2, under equal or explicitly compatible revision/scope/environment. Text similarity does NOT prove entailment. Red case: both subprocesses say PASS but consumer contract is violated.

**Proof granularity:** cheap deterministic asserter for cheap reversible transition; stronger independence and runtime/chaos test for material money/data/security/concurrency/irreversible effects. No full model council or global test sweep as the cost of every trivial edit.

## C02. Nine irreducible epistemic/operational entities

1. **Observation:** source, method, time, state, evidence and instrumentation aperture.
2. **Claim:** proposition, applicability/scope, version, confidence and dependencies.
3. **Hypothesis:** alternative explanations, differentiating predictions, invalidators and current evidence.
4. **Obligation:** goal + postcondition + expected proof/authority.
5. **Decision:** alternatives, evidence, value/risk, authority and decision rule.
6. **Transition:** before-state, causality, authorized action and after-state.
7. **Effect:** external mutation, destination, idempotency and reconcile outcome.
8. **Proof:** independent verification of a particular assertion under explicit scope/version.
9. **Capability:** implementation-independent trait contract + executable or documentary method + required evidence and limits.

Life-cycle chain: observation → claim/hypothesis → obligation → decision → transition/effect → proof → candidate capability → verified transfer → institutional baseline. **Not every observation or local change must become a universal capability.**

**Trait / Implementation / Proof separation:** a trait is a guaranteed property, implementation is a mechanism, proof is bounded evidence it holds. Distinct codebases/strategies may satisfy same trait under different assumptions.

**Proof-carrying knowledge certificate:** claim, applicability, supporting evidence, counterevidence, known failure cases, invalidators, consumers, lineage, status and supersession. An invalidated premise makes dependent proof REJUDGMENT_REQUIRED; it does NOT automatically falsify the claim.

## C03. Orthogonal epistemic and execution states

Never collapse these axes:
- Provenance: OBSERVED / REPORTED / INFERRED.
- Evidential validity: SUPPORTED / CONTRADICTED / STALE / UNJUDGED.
- Execution: NOT_RUN / RUNNING / EXECUTED / FAILED.
- Applicability: APPLICABLE / NOT_APPLICABLE / UNKNOWN.
- Authority: AUTHORIZED / DENIED / PENDING / EXPIRED.
- Proof outcome for a particular gate: PASS / FAIL / UNJUDGEABLE / REFUSED / NOT_RUN / NOT_APPLICABLE, preserving the consuming owner vocabulary.

Laws: absent data ≠ negative; not run ≠ pass; old proof ≠ new state; contradiction blocks automatic promotion; N/A needs justified trigger; external text is data not authority; unknown provider ≠ available; non-discriminating task ≠ efficacy; universal promotion requires independent applicable evidence; failure of an instrument must not become a clean result.

**Counterexample:** successful process exit is an observation, not proof an externally requested database write committed or that the specified feature behaves.

## C04. Identity, determinism and provenance

Required separately scoped identities:
- Repository independent from path (verify portability, root identity, multi-root behavior).
- Goal vs goal semantic revision vs execution epoch vs worktree/head/index/untracked capsule.
- Toolchain/version/flags/environment; schema version and projector version.
- Artifact digest vs observation/event ID vs effect key vs authority/fence.
- Proof pin (verifier version, artifacts, environment, time, test subject).
- Capability identity and generation of baseline.

Hash gives byte/version integrity, NOT statement truth, signer identity or immutable storage against a complete chain rewrite. Detect missing/moved/corrupt evidence. Protected histories may require independently held anchors/signatures based on actual threat model.

**Canonicalization warning:** deterministic serialization, ordering, text encoding and source-version pin must be specified; apparently equal records may be different under another runtime/locale/toolchain. Never assume one host's time decides causal order across machines.

## C05. Lifecycle of a protected effect

Logical states: PROPOSED → VALIDATED → AUTHORIZED → INTENT_RECORDED → DISPATCHING → OBSERVED → RECONCILING → VERIFIED → COMMITTED → CLOSED, with failure/REFUSED/UNKNOWN branches. Treat as design vocabulary mapped to existing `gsd_x/goal/epoch.py`, not a new competing enum.

**Crash window law:** record intent and pre-mint effect identity BEFORE dispatch; on restart PROBE/ADOPT/RECONCILE rather than blind resend. A queued/sent acknowledgement ≠ postcondition met. If remote effect occurs but response vanishes, set UNKNOWN_EFFECT and reconcile using provider identity, idempotency, read-after-write or Owner adjudication.

**Exactly-once realism:** receiver-enforced dedup is needed for a strict externally visible exactly-once effect; local attempt counters cannot guarantee it. Retry only with new information or provable idempotence. Separate event dedup from effect dedup, because distinct events can request same logical effect and duplicate event notifications can arrive after state changes.

**Authority:** principal/action/resource/scope/context/expiry/budget/fence; enforce at resource boundary, not only planner. Pause/cancel stop new effects; in-flight effects still require reconciliation. Revocation before effect must deny. In-flight revocation needs declared semantics.

**Temporal invariants (desired, not formally proved):**
- Always: committed protected effect implies valid authority, subject to chosen revocation linearization.
- Always: accepted receipt matches current goal revision, epoch identity and resource fence.
- Always: stale fence cannot write a protected resource.
- Always: closure implies all applicable proof obligations have acceptable receipts.
- Conditional liveness: if resources, permissions and fair scheduling remain available, eligible obligations eventually advance; no promises during indefinitely unavailable resources/Owner approval.
- Dormant goals with no unresolved cognitive step use zero resident model calls.

**Linearizability:** for shared state, construct concurrent histories and a sequential reference model; test stale holder, split-brain, duplicate events and crash/restart. Evaluate Porcupine/Jepsen only for test lab when current tools demonstrably cannot inspect history.

## C06. Event envelope and projection contracts

For inter-owner events, expose an adapter compatible where helpful with CloudEvents: event id, source, event type, schema, subject, goal/revision/epoch, per-authority sequence, causal parents, actor, authority/fence, artifact/payload digest, evidence, observed/recorded time, sensitivity and retention. Not all fields are universal; make per-event schema required set explicit.

**Event time is not causal authority.** Use ledger/CAS/sequence/fencing or properly modeled causal relation; do not infer total causal order from clocks across hosts.

Projections/snapshots require: source log, last included seq, projection code/version, state digest, materialization runtime, rebuild rule, health proof. Source event log remains authoritatively reconstructable; avoid second mutable truth. Snapshot must not erase audit/recovery data or hide diverged writers.

Journal hash chains detect inconsistent local history but cannot authenticate external actor or prevent full rewrite by a storage owner without an independent root of trust. Document threat model before adding crypto/attestation.

## C07. Proof ladder and independent judgment

Evidence/verification levels (higher levels do not universally substitute for lower):
- V0 structural: schema/typing/references.
- V1 behavioral: assertions against real function/contract.
- V2 adversarial: deliberately failing inputs/mutation/fault conditions.
- V3 integration: contract composition, backward compatibility, nonlocal impact.
- V4 runtime: actual browser, deployed service, device/hardware, process/remote environment.
- V5 transfer: later comparable task in another project or environment benefits causally.

Instrument validity factors: aperture, sensitivity, specificity, environment fidelity, independence of verifier, freshness, relevant population, reproducibility. Positive + negative + mutation control mandatory for critical gates. A test that reads wrong stdin or catches nothing is vacuous even with 0 exit.

Independent judge must pin accepted gate/source/commit/tree and NOT run as the builder's own untrusted epoch. Detect gate edits, wrong-tree testing, stale revision, mutated thresholds, skipped assertions, fake exceptions, forged PASS, expired proof and changed production configuration. Never let a pass from static source claim real UI/runtime correctness.

**Affected-proof closure:** `tools/change_impact.py` plus Graphify/scanner must select affected proofs. Dynamic/unknown edges broaden scope or mark UNJUDGED, never "no tests needed."

## C08. 24 adversarial incident families — complete owner-supplied corpus

Each item must include real producer path, predeclared expected result, a positive counterpart, exact state/receipt evidence and recovery semantics:

| Incident | Perturbation | Invariant / expected behavior |
| --- | --- | --- |
| F01 Filesystem crash | Kill between data write and publication | Valid complete record or detectable no-record, not partial accepted |
| F02 Filesystem corruption | Truncate or alter a historic event | Never parse unreadable as empty/healthy |
| F03 Concurrent writers | Race two appends/CAS | Linearizable winner and loser re-read |
| F04 Frozen stale worker | Resume after lease TTL/fence turnover | Old fence cannot commit |
| F05 Lost external ACK | Remote effect happened, reply lost | UNKNOWN and reconcile; no blind repeat |
| F06 Reordered messages | Stale result arrives after new epoch | Rejected or causally reconciled |
| F07 Duplicate messages | Same notification delivered twice | One logical transition, not double effect |
| F08 Worker death | Kill process mid-mission | Durable obligations survive |
| F09 Version change | Upgrade runtime mid-goal | Compatible replay or explicit refusal |
| F10 Quota exhausted | Provider returns limit | No retry loop or quota-burning probe |
| F11 Semantic failure disguised as success | HTTP 200/exit 0 carries provider refusal | Outcome classified as failure |
| F12 Compaction mid-work | Context wall crossed | Correct session/goal identity and continuation |
| F13 Incomplete handoff | Cold agent missing critical constraint | Evidence gap identified, no confident fabrication |
| F14 Prompt injection | External docs demand privileged mutation | Treated as data, no authority gained |
| F15 Permission revoked | Revoke capability before protected mutation | New effect refused |
| F16 Oracle weakening | Builder edits test/policy to green | Independent gate pin/refusal |
| F17 Always-green test | Remove real error condition | Non-discriminating instrument detected |
| F18 Missing tool | SAST/browser/compiler unavailable | UNCHECKED / UNJUDGEABLE, not PASS |
| F19 Misapplied knowledge | Wii-only tactic suggested for unrelated app | Applicability rejects transfer |
| F20 Stale evidence | Dependency/source version changes | Proof invalidated/refreshed |
| F21 Recurrent known bug | Equivalent counterexample reappears in new project | Detect unlearned class, measure prevention |
| F22 False token optimization | Tokens fall but repair/failures rise | No economic winner |
| F23 Green static UI, broken real journey | Broken booking/form/CTA in browser | Runtime check fails |
| F24 Remote unavailable | VPS disconnected mid-mission | Durable state, bounded overhead and appropriate retry/wake |

Additional host-specific probes explicitly from source: 394,476-trace backlog and single >8MiB file; trace transport HTTP/Bearer; two exporters; missing auth; malformed JSONL; path containing spaces; conflicting Windows/POSIX newline/permissions; no CI config; clean-install dependency; files beyond classifier scan cutoff; false-positive task family wake.

## C09. Causal evaluation / pp_eval: the eight experiments

All trials have frozen source/target/expected outcomes, independent grader, predeclared comparison and controls; equal host/model/permissions when possible, A/A variability, task holdouts, repeated runs, true total cost, version fingerprints and uncertainty.

| Experiment | Question | Minimum result |
| --- | --- | --- |
| A CPP vs minimal | Does pack improve correctness or just cost? | More verified outcomes or lower cost at equal quality |
| B Always-on vs JIT | Which text/hook/skill actually helps? | Context reduction without new regressions, positive controls |
| C Single vs Hyperplan | Where adversarial review has ROI? | More meaningful defects caught per total cost, no false wakes |
| D Institutional knowledge vs cold | Does knowledge avoid rediscovery? | Lower archaeology/research cost without incorrect transfer |
| E Conventional vs property-based | Are new valid defects found? | Stable additional counterexample, low noise |
| F GSD X vs durable engine pattern | Survive killed worker? | No lost goal/effect duplication, cost comparison |
| G Symbol-aware vs static graph | Does impact analysis prevent regression? | True consumers found, unknown edges acknowledged |
| H New Work Class same pattern | Does knowledge transfer across projects? | Better first-pass holdout result while preserving applicability |

**A/A calibration first**, and negative controls that must fail. A/B win is not proved by one favorable model run, longer prose, or invalid sample. Two variants that always pass give ceiling/INSUFFICIENT, not no-loss proof.

**Trajectory quality:** measure tool selection, information value, redundant reads/retries, privacy/policy, sequence of decisions and final proof. Use Inspect AI/Harbor/SWE-smith/Pydantic Evals for optional isolated comparison, not parallel persistent evaluator.

## C10. Developmental Replay and real causal inheritance

D0 historical real code state; D1 freeze then-known environment; D2 define subsequent traits/guarantees; D3 freeze *permitted* institutional context for trial; D4 rerun; D5 record total cost/failures/interruptions/proofs; D6 compare valid comparable historical path; D7 classify avoidable vs genuinely novel vs unobservable-at-the-time work; D8 record retained, rejected or unproven knowledge.

Tests: first exposure original, second new project equivalent and improvement, third negative case violating preconditions and correct refusal, fourth known defect avoided or caught early. Guard hindsight leakage: later facts unavailable at initial time must not be mis-scored as avoidable historical mistakes. Holdout task cannot carry training answer; historic denominator frozen.

## C11. Economic model and performance roofline

Total verified cost = cognition + context + known execution + verification + recovery + infrastructure + coordination + waiting + transport + human attention + maintenance + safety consequence where estimable. No fictitious numeric probabilities or false dollar precision.

Reusable capability expected value (symbolic) = sum over eligible future cases of P(case) × avoided total verified cost minus build + maintenance + risk/proof costs. Safety/authority/correctness are constraints not just inexpensive factors in one weighted score.

Measurement set:
- Effective Capability Coverage (denominator is actually applicable capabilities, not all modules).
- Verified First-Pass Success and Regression Escape Rate.
- Cognitive Cost per Verified Outcome, Goal-hours per model token, useful vs wasted wake rate.
- Institutional Reuse Rate and Knowledge-to-Behavior Conversion.
- Autonomous Recovery Success and effect reconciliation rate.
- Cost by novelty, known work, proof, coordination, waiting, retries and Owner mechanics.
- Institutional Capitalization Efficiency = *verified future value of actually reused capabilities* / *total create + maintain cost* (UNKNOWN without impact data).
- Work-Class Learning Plateau and cost per repetition at equal quality (do not invent compounding curve).
- Developmental Compression = valid comparable historical trajectory cost / new cost; not meaningful if goals or era differ.
- Embodied Knowledge = applied justified work done below model, not number of scripts.
- Evolutionary Change Confidence = transformations retaining declared traits.
- False Activation, Knowledge Miss, Stale Proof, Unowned Effect, Duplicate Mechanism, Resume Archaeology, Capability Maintenance Rent.

**Roofline:** classify actual bottleneck as cognition, context, proof, runtime, coordination, memory, authority, external reality or knowledge. Optimize real limiter; no token tricks when the mission is blocked on authorization or CI.

## C12. Security / telemetry / supply-chain and trust

Separate constructor / independent verifier / promotion authority. No modifying judge, threshold, scope or heldout to pass. Gate actual action boundary, not just prompts. External source repositories, SKILL.md and docs are untrusted instructions. Source/license/third-party assets and SBOM provenance must be checked.

Existing trace flusher risk research obligations: test transport protection (plain HTTP default with Bearer unless secured network; do not assume a tunnel), redact sensitive prompts/logs before export, hard cap synchronous read including first file, move network/queue drain off interactive Stop boundary if cost measurement supports it, ack/timeout/idempotency, crash during delete/flush, two concurrent exporters, malformed JSONL, secret absence, durable retention and health probes.

For high-value build/provenance: SLSA-like source/toolchain/artifact/runner identity and evidence refs; include dirty index/untracked files and installed/deployed artifact fingerprints, not just HEAD. Hash chains authenticate integrity relative to an anchor, not full actor provenance.

## C13. Deliverable / stop rule

Deliver only the minimum new contracts/adapters required to bridge **proven** producer→consumer gaps. Do not implement all C01–C12 as parallel modules. Every row's next actual step is a read-only existing owner + test route investigation, then a bounded pilot if material. Enforced no-op is a possible positive outcome. Use [48 items](2026-11-20_cpp-atomic-48-obligations.md) and [tranche plan](2026-11-20_cpp-atomic-tranches-proof-gates.md) for admission.
