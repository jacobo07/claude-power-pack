# Backlog — CPP-DBG-001: Evidence-Driven Bug Diagnosis & Causal Proof Ratchet

**Created:** 2026-10-11 · **Status:** BACKLOG / NOT STARTED · **Priority:** P1 (Owner requested; schedule against the observed critical path)  
**Upstream inspiration:** https://www.skills.sh/mattpocock/skills/diagnosing-bugs (Matt Pocock)  
**Related backlog:** [CPP-TDD-001 — Evidence-First TDD & Behavioral Verification Ratchet](2026-10-11_tdd-evidence-first-vertical-slice-ratchet.md)  
**Owner intent:** absorb the useful diagnostic discipline into Claude Power Pack as an automatic, observable and reusable engineering capability, not a new independent debugging OS.

## Mission

Make debugging converge on **the actual, causally supported root cause**, with a short, discriminating feedback loop, defensible reproduction, reliable correction, regression proof, and durable institutional learning.

The desired workflow is:

**Observed symptom → red-capable feedback loop → reproduce and minimise without losing prerequisites → competing causal hypotheses → discriminating experiments → minimal correction → original-path regression proof → clean-up → CEPS / Knowledge Vault / UKDL / baseline ratchet.**

Primary optimisation is **time / tokens / experiments to correct, verified causal resolution**, not number of investigations, logs, tests or theories produced.

**Constitutional constraint:** observing a symptom, reading plausible source code, seeing a green unit test, or reaching a downstream terminal state is not proof of the root cause or a correct fix. Reality, contracts and execution evidence outrank narrative.

## Starting repo evidence (inspected 2026-10-11; not a live integration audit)

| Existing CPP owner | Supported role | Boundary / unverified gap |
| --- | --- | --- |
| `skills/instrument-before-claim/SKILL.md` | Measurement integrity, negative controls, red-capable gates, detecting blind instruments | Strong measurement doctrine, but not proof of a universal bug-reproduction-first workflow |
| `skills/agent-introspection-debugging/SKILL.md` | Agent-specific failure capture, diagnosis, contained recovery and reports | Focuses on agent runtime failure; not universal product/software defect diagnosis |
| `commands/osr.md`, `modules/osr/` | External-observation model, comparison, first divergence, prerequisite ordering | Explicitly does **not** own causal investigation; hands the aligned divergence to CRAIF |
| `vault/audits/usirc/BOUNDARY_CONTRACT.md` | Ownership boundaries: CRAIF owns causal candidates, evidence and closure; crawl_os acquires evidence; OSR aligns and observes | This record contains its own historical proposal status; verify the current live ownership and wiring instead of blindly relying on doctrine |
| `commands/ceps.md` | Recurring-error evidence and appropriately reviewed correction capture | Must consume verified lessons, not speculative diagnoses as universal laws |
| `modules/done_gate/` and CPP verification surfaces | Architectural truth, completion evidence and regression checks | Needs evidence-linked “original symptom resolved” and causal sufficiency, not just passing nearby tests |
| `vault/backlog/2026-10-11_tdd-evidence-first-vertical-slice-ratchet.md` | Planned evidence-first test construction | Complementary initiative, not another causal investigation owner |

**No claim is made that these capabilities are all activated on every debugging task today.** CPP-DBG-01 must inspect actual call graphs, entrypoints, dispatchers, and installed/live parity.

## Upstream absorption: six phases to audit and adapt

Inspect the actual pinned upstream revision, licence, examples, and changelog at execution time. Classify each concept **ALREADY OWNED / EXTEND / CONDITIONAL / REJECT / UNVERIFIED**, preserving attribution and respecting intellectual property.

1. **Build a tight feedback loop.** Prefer the smallest agent-runnable test, HTTP/CLI probe, real-browser assertion, trace replay, isolated harness, property/fuzz test, bisection, differential comparison, or structured human-in-loop instrument that can observe the *reported symptom* and reach the relevant path.
2. **Reproduce and minimise.** Run it and observe the correct red; remove irrelevant inputs/dependencies/steps one by one while preserving the causal preconditions.
3. **Generate competing, falsifiable hypotheses.** Usually 3–5 ranked hypotheses for hard bugs, each with a predicted observation that distinguishes it from alternatives. Do not require artificial enumeration for an obvious typo with direct evidence.
4. **Instrument to discriminate.** Select a debugger/REPL or targeted boundaries; change one independent factor where possible; use uniquely tagged temporary logs; profile or bisect performance regressions against sound baselines.
5. **Fix and regress.** Convert a valid reproducer into a regression test at a seam that represents the *actual* triggering conditions; prove red before fix and green after; re-run the **original, unminimised** reproduction.
6. **Clean up and retain the cause.** Remove debug-only assets or explicitly classify them as retained regression instruments, record causality and limitations, and promote portable learnings only through existing owners.

Upstream's strong “no hypothesis without a loop” principle is a **default discipline, not an absolute bar on investigating intermittent or inaccessible production faults**. When a safe deterministic loop cannot be constructed, remain epistemically honest and use bounded evidence-gathering rather than guess or silently claim closure.

## Ownership map and anti-duplication rules

**Provisional causal authority: CRAIF** (current executable owner/reachability must be reconstructed in CPP-DBG-01).
- **CRAIF:** causal candidate graph, hypotheses, interventions, proof sufficiency and closure. No duplicate “bug engine” or investigation ledger.
- **OSR:** observed-state/differential timeline and first divergence. Never claim causal attribution merely because it found a divergence.
- **crawl_os / acquisition owner:** collection, integrity, authorization and provenance of external/run-time evidence. Do not reproduce capture in CRAIF.
- **Instrument Before Claim / test-oracle owner:** validate measurement's ability to distinguish healthy vs faulty states, relevance to real entrypoint, and independence from tested implementation.
- **TDD / test-gaps / mutation / existing tests:** regression-test construction and sensitivity verification; distinguish feature-test-first from incident diagnostic red.
- **Architectural Truth / completion authority:** prevent success claims resting on invalid start states, wrong execution paths, green-but-unobserved critical behaviors, or missing durable side-effects.
- **CEPS / Knowledge Vault / FD / rule_compiler / UKDL / UCR-CIF:** record incident and promote patterns through existing review, scope and versioning paths. Preserve distinct read/write/placement ownership.
- **Agent introspection debugging and liveness guardian:** narrower owners for agent self-retry loops, orphan processes, context exhaustion and hook/tool runtime failures.
- **Existing task routing / JIT activation:** automatic minimum-sufficient activation on actual bug/failure/slow-regression intent; no requirement to name the skill.

Perform a **REUSE → EXTEND → MERGE → CONNECT → GENERALIZE → CREATE** review before introducing any file, hook, tool, persistent state or runtime service. Unreachable code and passive documentation are not delivered capabilities.

## Required contracts (extend the current owner schemas / verdicts rather than creating competing global enums)

### DBG-C01 — Symptom & Reality Snapshot

An incident binds: reported symptom (verbatim where possible), expected vs observed behavior, scope, runtime/host, version/commit/worktree, environment, time window, invocation, affected operation, last-known-good where available, and safety/data sensitivity. Separate facts, assumptions and unknowns.

Never infer business acceptance rules merely from existing code. Preserve private data confidentiality and redact logs, HARs, traces, tokens, cookies, credentials and customer payloads before surfacing or storing sharable evidence. Never copy production secrets to a test fixture.

### DBG-C02 — Discriminating Feedback Loop

Construct the smallest **red-capable, causally relevant** test/probe. A valid loop must:
- reach the *actual class of failure* through the real entrypoint or a demonstrably equivalent seam;
- assert the exact outcome distinguishing faulty and correct behavior, not merely “did not crash”;
- have a reproducible or quantified-probabilistic trigger;
- be executable within explicit time, memory, process, external-call and token budgets;
- record expected source, invocation, code/environment identity, negative control and observed output;
- demonstrate it can answer both RED and GREEN under safe counterexamples, not be a one-answer instrument.

A convenient but more permissive mock/emulator is not a valid substitute unless equivalence of the relevant contract is demonstrated.

When the environment cannot be reproduced safely, register which evidence acquisition was attempted and which contract remains unmeasured. Do not mark a mere test stub as a witnessed bug.

### DBG-C03 — Causal Precondition Preservation

Before calling a minimised reproduction faithful, compare its necessary state transitions, concurrency topology, ordering, persistent records, permissions, identities, retry behavior and external dependencies against the original incident.

Perform **one-variable-at-a-time reduction** where feasible. If removing a prerequisite eliminates the bug, retain it as load-bearing rather than “simplifying away” the cause.

Use OSR first-divergence observations as *candidate evidence*, not automatic root cause. “Terminal component reached” is not equivalent to “architecturally prepared and reached.”

### DBG-C04 — Falsifiable Hypothesis & Experiment Contract

For materially ambiguous incidents, generate a bounded, ranked set of competing candidate causes; each must include a prediction and a discriminating experiment:
- causal mechanism and impacted contract;
- predictions if true and if false;
- independently observable measurement and control;
- expected information gain, experiment cost, risk and reversibility;
- current evidence for and against, including contradictions;
- disposition after execution: supported, falsified or unresolved, without inventing certainty.

Prefer tests that sharply separate alternatives. Pivot after repeated non-informative probes rather than consuming tokens repeating the same guess. Do not alter live production configuration or data for a probe without authorization and rollback.

### DBG-C05 — Instrumentation Integrity & Provenance

Prefer debugger/profiler/REPL when suitable, then tagged, targeted logs at causal boundaries. Record unique debug marker, insertion site, bounded lifetime, cleanup owner, safe redaction and proof of removal. Never create unbounded “log everything and grep” behavior.

For performance: pin baselines, warm-up, sample sizes, host contention, system clocks, caches, distributions and variance; avoid treating a drifting host or unrelated initialization as causal. Compare against the same workload and observable contract.

For intermittent bugs, record reproduction probability/confidence, attempt count, trigger rate and uncertainty; reproduce under bounded stress only in safe environments. Parallel stress and sleeps can change the system's behavior, so they are experiments requiring interpretation, not automatic ground truth.

### DBG-C06 — Fix, Regression & Original-Path Closure

Before fixing, retain the failing reproducer when a correct seam exists. The regression test must preserve the original failure preconditions and user-visible effect. If the current architecture prevents a faithful test seam, report a named testing/architecture gap; **do not manufacture a shallow false-green test**.

After the minimal safe fix:
1. witness the targeted regression GREEN;
2. re-run the **original, unminimised** symptom loop;
3. verify relevant architectural prerequisites, integrations and durable external behavior;
4. run risk-appropriate negative-control/mutation tests to show the regression assertion can detect the old bug;
5. ensure no related tests/security contracts regress;
6. report what was observed vs still inaccessible.

Root-cause confirmation requires evidence that discriminates the proposed cause from competing explanations. A symptom disappearing temporarily is not proof of cause.

### DBG-C07 — Bounded Investigation & Non-Reproduction

No blind infinite loop. Define graduated operation tiers:
- **LIGHT:** directly observed and localised defect — smallest relevant probe and fix; no ritual 5 hypotheses.
- **STANDARD:** uncertain bug spanning components — reproduction, multiple causal candidates, targeted instruments and regression.
- **FORENSIC:** concurrency, intermittent, external/production, state-ordering, security, data or performance issue — timeline, reproduction-rate measurement, contract reconstruction, instrumentation integrity, independent verifier when ROI-positive.

When no loop can be built safely: disclose **NOT_REPRODUCED / UNMEASURED** using the existing CPP epistemic vocabulary; document safe attempts, captured artifacts and explicit access/evidence request. Limited observations and competing hypotheses may proceed as hypotheses, but not as an invented verified RCA or “DONE”.

Enforce wall-clock, token, subprocess-tree, retry and memory budgets; use CPP's existing liveness, process termination and recovery controls. A debug harness may not outlive its owner unless deliberately supervised and bounded.

### DBG-C08 — Cleanup & Institutional Knowledge Ratchet

Remove temporary logs/probes and private traces unless deliberately retained in approved, access-controlled, versioned incident artifacts; ensure artifacts are scrubbed and cleanup is testable.

Store confirmed cause, ruled-out hypotheses, failing and passing discriminants, fix provenance, reproduction/rollback procedures and regression identifier in the existing incident/CEPS knowledge records. Separate evidence-backed transferable failure classes from repository-specific accidents.

Only approved promotable patterns reach UKDL/hard rules via the existing knowledge owner; avoid auto-generalisation from one anecdote. The next agent should retrieve a relevant prior incident without reading the whole corpus.

## Delivery work packages

- **CPP-DBG-01 — Reality Scan, upstream revision and ownership [P1].** Verify latest CPP HEAD and upstream source, licence and exact content. Inventory active CRAIF entrypoints, OSR, crawlers, forensic replay, incident learning, TDD and done-gates. Trace producer→consumer paths and actual dispatch; produce overlap/reuse ledger.
- **CPP-DBG-02 — Symptom fidelity + bounded feedback-loop contract [P1].** Build on existing test/evidence mechanisms. Establish real-path red-capable observations, negative controls, timestamps *plus* artifact identities, oracle independence and explicit non-reproduction states. Avoid a new test framework.
- **CPP-DBG-03 — Causal-precondition-preserving minimisation [P1].** Preserve ordering, concurrency, state, initialization and external prerequisites while shrinking reproduction; integrate OSR-first-divergence only when relevant; use original-case replay for close.
- **CPP-DBG-04 — Hypotheses, predictions and experiment selection [P1].** Extend CRAIF owner, not OSR. Add bounded candidate competition, informative experiments, falsification/contradiction and “inconclusive” recognition; classify straightforward bugs out of heavyweight ceremony.
- **CPP-DBG-05 — Instrumentation, redaction and runtime safety [P1].** Tagged temporary probes, cleanup proof, profiler/performance branch, redacted custody, production-risk authorization, hook liveness and bounded subprocesses.
- **CPP-DBG-06 — Root-cause and regression verification [P1].** Link relevant original symptom, faithful seam, test-first regression, minimal fix, original-path retest and architectural-state/intent confirmation; wire to existing done-gate and CPP-TDD-001 without conflating owners.
- **CPP-DBG-07 — Automatic routing and compounding [P2].** Ensure ordinary “broken”, “fails”, “slow”, “regression” and equivalent requests select sufficient guidance automatically, without full corpus loading; CEPS/UKDL/Knowledge Vault receive verified and correctly scoped learning, not uncertain candidate diagnoses.
- **CPP-DBG-08 — Real incidents, adversarial benchmark and rollout [P2].** Test against representative historical bugs and matched seeded incidents, measuring correct RCA, wrong fixes, time-to-repro, hypothesis churn, cost, retries, regressions, agent autonomy, and reoccurrence. Compare against current CPP and upstream-style discipline at comparable model/budget/host.

## Required adversarial fixtures (not claims of passed tests)

1. Syntax/import failure is mistaken for the actual reported bug — **reject false RED**.
2. Repro only tests “no crash” while output remains wrong — **reject weak oracle**.
3. Mock reproduces error but real runtime does not / vice versa — **surface contract mismatch**.
4. Minimisation removes a real prerequisite (race, initialization sequence, persisted identity) — **reject as unfaithful**.
5. Visible divergence appears after the causal divergence — **do not equate first visible symptom to first cause**.
6. One plausible hypothesis fails its own discriminating probe while another survives — **promote the latter only with sufficient corroboration**.
7. Several hypotheses produce identical predictions — **experiment is non-discriminating**.
8. 1%-flake gets one green run after patch — **do not mark fixed without statistical evidence/uncertainty**.
9. Performance numbers taken under changing host load or mismatched test inputs — **mark measurement confounded**.
10. Regression test passes at a shallow unit seam while the multi-caller system still fails — **do not claim closure**.
11. Mutation/negative control disables the proposed fix but existing suite remains green — **expose blind regression gate**.
12. Real bug never reproduced despite bounded instrumentation — **explicit unresolved state**, not invented RCA.
13. Hook/child hangs and holds stdout open — **bounded termination with truthful evidence and no orphan**.
14. Logged HAR includes authentication material — **redact/prevent leakage before output or promotion**.
15. Debug instrumentation survives final cleanup — **not completion eligible** unless explicitly retained/owned.
16. Two concurrent worktrees produce mixed timestamps/output — **reject unbound provenance**.
17. Original real workflow remains broken while minimised test passes — **block success claim**.
18. A transient workaround masks a root cause — **separate mitigation from proven resolution**.
19. Incident record becomes a hard rule despite unresolved/contradictory evidence — **governance refuses promotion**.
20. A trivial one-line bug triggers an expensive multi-agent forensic ceremony — **performance/routing regression**.

Positive controls must show valid investigations succeeding; negative controls must prove actual gates can go red; faulty artifacts must be restored and original source integrity checked after mutation/drills.

## Performance, privacy and reliability constraints

- Default to a small, high-signal probe; escalate based on defect criticality and discriminating value.
- Expensive full-suite runs, fuzz/stress, differential deploys, external observations and independent reviews belong at justified checkpoints, not on each edit.
- Keep capture within authorization and privacy constraints. Synthetic fixtures where necessary, but never claim synthetic equivalence to production by default.
- Never build an observer inside the same failure domain when its liveness must survive the target's crash.
- Avoid unbounded output/log growth and reruns; context-sensitive checkpoints must preserve evidence without repeating investigation.
- Use existing CPP process/timeout guards. Termination must cover full process trees and inherited streams, not only wrappers.
- An unmeasured or inaccessible system is *unknown*, not healthy.

## Measurable completion criteria

1. No duplicate causal owner, incident ledger, runner, evidence-capture system, tool router or rule-placement authority.
2. A normal debugging request selects the correct level automatically without naming Matt Pocock's skill.
3. At least one real representative bug is reproduced by a red-capable, symptom-faithful loop with observable positive and negative controls.
4. Minimised and original reproductions preserve identified causal prerequisites; checks reject convenient-but-unfaithful harnesses.
5. Materially ambiguous cases have falsifiable alternatives, discriminating experiments and a recorded causal verdict; unsupported claims remain unresolved.
6. Intermittent and production-only incidents have bounded safe investigation modes; no fictitious guarantees of 100% reproducibility.
7. Fix verification proves the correct targeted regression and the **original full-path scenario**; a nearby green test cannot close the issue.
8. Instruments are safe, redacted, reversible and disposed of, and their provenance ties to the actual code/environment identity.
9. Adversarial drills break the intended assertion or causal invariant and produce the expected red without contaminating source.
10. CRAIF causal owner, OSR, acquisition, test-gaps/TDD, completion authority and CEPS knowledge owners can consume the minimal evidence each needs, with reachability verified from a **real** user entrypoint.
11. Runtime/time/tokens/CPU/RAM/process bounds are measured; no regression from mandatory expensive debug instrumentation for simple bugs.
12. At least one matched benchmark demonstrates improved correct-diagnosis outcomes or reduced total cost without loss of quality; reject “superior” claims without evidence.
13. Failure knowledge is attached to source evidence, correctly scoped, versioned and discoverable by the next agent; rule promotion is evidence-gated.
14. A fresh CPP session can diagnose a comparable failure without this conversation or an explicit skill name.

## First action upon execution

**Reality Scan first.** Read then-current CPP HEAD and upstream pinned skill; independently inspect `skills/instrument-before-claim/SKILL.md`, `skills/agent-introspection-debugging/SKILL.md`, CRAIF callers, `commands/osr.md`, the evidence-acquisition boundary, `commands/ceps.md`, CPP-TDD-001 and existing completion authority.

Produce an owner/consumer/reachability diagram and **REUSE / EXTEND / CONNECT / DECLINE** ledger. Only then pick the minimum sufficient implementation surface. Do not begin by installing a separate `diagnosing-bugs` skill or adding a new “Debugging OS.”

## Status/provenance

**Backlog only, no runtime implementation claimed.** Derived from Owner's explicit instruction of 2026-10-11, original skill URL and the observed CPP repository paths listed above. The proposed capabilities, performance gains and owner integrations remain hypotheses pending CPP-DBG-01 and actual end-to-end tests.
