# Backlog — CPP-TDD-001: Evidence-First TDD & Behavioral Verification Ratchet

**Created:** 2026-10-11 · **Status:** BACKLOG / NOT STARTED · **Priority:** P1 (candidate; reprioritize against observed work) · **Source:** https://www.skills.sh/mattpocock/skills/tdd · **Owner intent:** absorb the useful test-first discipline into Claude Power Pack (CPP) so its existing engineering verification is stronger, more economical and provably executed.

## Mission and non-goals

Convert CPP's documented **RED → GREEN → REFACTOR** rule into an **observable, falsifiable, risk-proportional construction contract** that applies automatically to suitable coding tasks without requiring the user to mention TDD.

CPP must retain its broader architecture/intent/production-reality verification. A green suite, a test file in the diff, or a report saying “TDD followed” is not evidence that a RED preceded the implementation.

**Do not:** install a second testing/agent/orchestration framework; clone the upstream skill blindly; create a new universal state store or TDD-specific daemon; turn every change into heavy mutation testing; require a new RED for purely documentary work or a behavior-preserving refactor; promote unverified claims about superiority over ordinary TDD.

## Baseline observed in CPP (2026-10-11 repository review)

| CPP owner / surface | Confirmed capability | Gap / limitation |
| --- | --- | --- |
| `rules/common/testing.md` | Says TDD is mandatory: test first, witness RED, minimum GREEN, REFACTOR, coverage and V-gates | Textual law alone does not prove ordering or behavioral relevance |
| `modules/uqf/principles/tdd_workflow.py` (P07) | Checks source/test file presence in a change set | One test file can satisfy multiple source files; does not observe failure cause, chronological RED, GREEN or REFACTOR |
| `skills/intent-driven-development/SKILL.md`, `commands/intent-verify.md` | Observable acceptance criteria and criteria-to-evidence completion check | Must join test-first evidence to the *intended behavior*, not just the presence of an intent artifact |
| `skills/verification-loop/SKILL.md`, `commands/auto-test.md` | Build/type/lint/test/diff verification and tests generated for staged diffs | Post-change testing is useful but cannot retroactively establish test-first development |
| `tools/test_gaps.py`, `commands/test-gaps.md` | Mutation-guided inspection of changed Python/pytest lines; isolates execution, names survivors/uncovered lines | Scoped to Python/pytest; does not establish a chronological TDD cycle or independent oracle |
| Existing mutation, intent, architectural-truth, production-reality and ratchet owners | Additional assurance beyond ordinary TDD | Ownership, runtime reachability and task-specific activation require Reality Scan before extension |

**Epistemic boundary:** these are inspected repo artifacts and declared capabilities, **not** a completed live end-to-end assessment of TDD adoption across every CPP entrypoint/host.

## Upstream absorption requirements

At execution time inspect the upstream skill's current content, revision, examples, license, and relevant documentation. Classify each meaningful idea as **ALREADY OWNED / EXTEND EXISTING / APPLY CONDITIONALLY / REJECT / UNVERIFIED** with evidence. The essential ideas to assess:

- RED → GREEN → REFACTOR for one observable behavior at a time.
- Vertical slices instead of test-bank-first or enormous speculative implementations.
- Behavioral tests at meaningful seams / public interfaces rather than implementation-coupled assertions.
- Independently sourced oracles: expected results come from user intent, domain specification, standards or other trusted references, **not** from copying the newly written implementation.
- Test seam selection, refactor safety, and explicit discussion of what each test can and cannot detect.

Respect copyright/licensing and preserve provenance. Absorb semantics into CPP owners, not wholesale text or an unnecessary dependency.

## Ownership and integration hypotheses — must be verified by Reality Scan

- **Canonical TDD behavioral-policy owner:** existing UQF P07 + common testing rules; evolve the weak heuristic without pretending it already observes execution.
- **Task applicability / acceptance:** SDD OS, intent-driven-development and existing spec/intent gates. Do not build another intent compiler.
- **Execution evidence / lifecycle:** existing verification-loop and execution evidence/ledger primitives, routed through normal CPP task execution (not a parallel TDD session manager).
- **Mutation and negative controls:** `mutation_probe`, `mutation_ratchet`, `test_gaps` and relevant existing adversarial infrastructure; do not duplicate the mutator.
- **Completion truth:** `intent-verify`, V-* gates, completion authority / done-gates; do not promote “tests passed” to “feature correct”.
- **Knowledge ratchet:** existing Construction Events / UCR-CIF, Knowledge Vault, UKDL and baseline promotion pathways, once real evidence warrants it.
- **Runtime hooks:** only an existing bounded, proven-reachable dispatcher if unavoidable. No unbounded stdin, orphan processes, host-coupled paths or expensive per-edit hooks; no gate introduced after the action it must prevent.

The implementation owner must be selected from actual import/call graphs, supported host adapters and available evidence, not from the similarity of filenames.

## Required contracts (minimum sufficient, reuse existing schemas first)

### C1 — TDD Applicability Contract

Classify the work **before constructing behavior**:
- `APPLICABLE`: new or modified behavior with a testable seam and an affordable trustworthy oracle.
- `CONDITIONAL`: legacy, exploratory, UX/hardware/runtime-dependent or integration work requiring characterization, contract tests, a safe harness, or justified alternative evidence.
- `NOT_APPLICABLE`: documentation-only, nonbehavioral change, or pure refactor protected by an already observed passing baseline.
- `UNRESOLVED`: scope, testability or oracle cannot yet be established.

Do not mark `UNRESOLVED` as success. Exceptions must be reasoned and scoped, not an escape hatch for ordinary features. Handle changes to classification explicitly.

### C2 — Red Evidence Contract

For each applicable vertical slice, retain minimally sufficient evidence that:
1. the behavioral test/expected result was defined **before** the implementation satisfying it;
2. it was executed in a known environment and failed **for the intended missing behavior**;
3. red caused by syntax/import/environment/fixture failure or unrelated broken baseline was **classified**, not falsely credited;
4. provenance binds the observation to the relevant test, task/acceptance criterion, target code revision, command/runner and worktree;
5. timestamps alone do not prove causality; use revision/artifact identity and causally ordered recorded actions where feasible.

A generated “test file exists” observation is **HEURISTIC_ONLY**, never `RED_VERIFIED`. A fake or self-fulfilling RED must not pass.

### C3 — Vertical Slice & Minimal Green Contract

Complete one externally observable behavior at a time: accepted behavioral intent → RED → minimum implementation → GREEN → safe refactor → targeted regression evidence. Select public/API/integration seam where possible; avoid tests that merely restate internal helpers, mocks, or current implementation. Do not enlarge the feature merely to make the test green.

For architectural state machines, compare **valid state transitions and prerequisites**, not just whether a component was reached. A green test on an invalid setup is insufficient evidence.

### C4 — Independent Behavioral Oracle Contract

Bind test expectation to an identified acceptance criterion, public contract, specification, domain rule or independent reference. Record when an expectation is inferred/ambiguous. Reject self-consistency tests that compute expected values by invoking the same algorithm they purport to validate. If the oracle cannot be established, record `ORACLE_UNRESOLVED` and use the existing clarification/research process when material.

### C5 — Verification Integrity & Mutation Contract

For risk-appropriate slices, inject a controlled negative case/mutation to prove the test would detect relevant wrong behavior; demonstrate restoration and byte-identical or hash-verified return to the baseline. Reuse the existing mutator/test-gaps tooling when supported.

Maintain distinct outcomes **KILLED / SURVIVED / UNMEASURABLE / TIMEOUT / ERROR / NOT_RUN**. Surviving or equivalent mutants require disposition; sampling must declare coverage. Do not collapse `UNMEASURABLE` into PASS or blanket-block changes that cannot be measured.

### C6 — Completion & Institutional Ratchet Contract

Distinguish:
- `RED_VERIFIED` — observed, relevant failing test before implementation;
- `GREEN_VERIFIED` — changed behavior passes its targeted test;
- `REFACTOR_VERIFIED` — any applicable cleanup preserves verified behavior;
- `BEHAVIOR_VERIFIED` — critical acceptance and integration/production evidence satisfy the real intent;
- `EVIDENCE_INCOMPLETE` / `BLOCKED` / `EXEMPT_SCOPED` — non-success states with explicit causes.

Do not invent a competing global verdict enum: map these stage facts into existing CPP completion vocabulary and ratchet records. Only promote transferable knowledge after an observed successful construction event; record counterexamples and negative findings.

## Delivery work packages (execution order; tasks not yet implemented)

- **CPP-TDD-01 — Reality Scan and ownership map (P1).** Inspect live CPP wiring, historical tests, current UQF checks, upstream skill, auto-test and completion paths. Produce a gap/overlap ledger, reachable owner graph, duplicate-prevention decision, and explicit applicability matrix.
- **CPP-TDD-02 — Red-proof schema and negative controls (P1).** Use an existing evidence artifact/ledger. Prove the recorder rejects RED caused by the wrong failure reason, stale worktree, post-implementation tests, and unrelated suite failure. Bounded capture only.
- **CPP-TDD-03 — Vertical-slice behavioral guidance (P1).** Route to the minimum sufficient existing skill/agent guidance automatically on applicable coding tasks; behavior-first seams, independent oracle, minimal GREEN and safe REFACTOR. Preserve test-first ordering without requiring user invocation.
- **CPP-TDD-04 — Strengthen UQF P07 (P1).** Preserve the old presence heuristic as its own weaker signal. Add evidence-aware classification. A test file being present cannot satisfy `RED_VERIFIED`. Require owner/consumer reachability and precise nonblocking vs blocking authority.
- **CPP-TDD-05 — Integrate intent + done-gate (P1).** Join acceptance IDs, negative evidence, execution observations and completion authority; no false DONE for green-but-wrong behavior, tests run in invalid states, or missing critical proof. Treat historic code, pure refactors and unavailable environments proportionally.
- **CPP-TDD-06 — Risk-bounded adversarial verification (P2).** Reuse mutation/test-gaps. First support one production-realistic Python/pytest slice with controlled mutants, then evaluate TypeScript/Java/Elixir adapters from actual usage/economics; unsupported languages remain explicitly unsupported, not silently certified.
- **CPP-TDD-07 — Cost, liveness and safety engineering (P1).** Keep the RED/GREEN inner loop lightweight; reserve expensive suites, broad mutation, independent review and cross-runtime checks for suitable boundaries. Specify wall-clock, process, context and cost ceilings; timeouts/recovery; no orphan/hook stalls, no unexpected production mutations.
- **CPP-TDD-08 — Benchmark, ratchet and rollout (P2).** A/B benchmark existing CPP vs upgraded CPP on matching real tasks + deliberately seeded defects, with equal environments, model and budget; measure behavioral defect catch rate, wrong-RED acceptance, false-green completion, true/false blocking, mutation sensitivity, token consumption, latency and time-to-fix. Version proven patterns through existing knowledge owners. Promote the baseline only if useful.

## Adversarial acceptance fixtures (required; fixtures, not fabricated empirical results)

1. One test file + several changed source files: P07 heuristic may pass, but TDD proof **must not** automatically pass.
2. Test is added only after behavior is implemented: runner green, chronological RED proof **absent**.
3. Test fails because dependency/import/fixture is broken: **invalid RED**.
4. Test fails for a missing, independently specified behavior: **valid RED**.
5. Test copies the implementation's output as its expected result: **oracle not independent**.
6. A pure refactor with prior passing behavior tests: **scoped exemption**, not synthetic RED generation.
7. A mutation changes output but all assertions still pass: **survivor visible**, not silent success.
8. Mutation-runner times out or base suite already fails: **unmeasurable**, not pass/fail conflation.
9. The component endpoint is reached from an invalid architectural state: integration evidence **fails** the contract.
10. An inaccessible hook / lost ledger event / orphan subprocess occurs: **no success claim**; bounded recovery with existing liveness owner.
11. A test suite is entirely green but one critical user acceptance criterion is unobserved: **EVIDENCE_INCOMPLETE**.
12. Unsupported language or external runtime: **explicit support/ceiling state**, no universal-certification language.
13. Changing or dropping required acceptance IDs cannot manufacture an improved completion score (named-ratchet check).
14. Cross-worktree or parallel-agent evidence cannot be misattributed to another worktree/session.

Tests must verify both positive and negative controls, including that intentionally broken mechanisms make the appropriate gate fail and that restoration returns the repo to its original state.

## Performance and economy invariants

- Do not put full mutation testing on every edit or every micro-slice.
- Prefer the targeted failing/passing test for RED/GREEN; expand to contract/integration/E2E at boundaries.
- Cache only when provenance/freshness and scope make reuse trustworthy.
- Choose depth by risk, system criticality and expected defect cost.
- Measure **cost per correctly verified behavioral slice**, not tests-count inflation or percent-coverage alone.
- Bound loops, subprocess groups, external calls and retries; protect the host and project data.
- A weaker honest verdict is always better than an expensive false claim.

## Done-gate (all required for this backlog item)

1. Reality Scan shows the authoritative existing owner for every added contract; no duplicate TDD runtime, test generator, mutator or ledger.
2. The applicable change path automatically selects the method without an explicit “TDD” user prompt; non-applicable paths remain quiet.
3. A valid RED is observed before implementation, tied to accepted behavior and a stable evidence identity.
4. Wrong RED, post hoc tests and file-presence-only evidence demonstrably cannot certify test-first development.
5. GREEN + any refactor maintain behavior, while relevant integration, architectural prerequisites and acceptance are independently verified.
6. Every stage distinguishes observed success, failure, incomplete, unsupported and exemption.
7. At least one real representative project slice is demonstrated end to end (not exclusively mocked tests).
8. Mutation/negative-control drills prove the gates go RED when the protected invariant is broken; recovery is measured.
9. Runtime impact (wall clock, CPU/RAM, tokens, context, process liveness) is measured and bounded; no all-tests-on-every-edit regression.
10. Existing intent verification, UQF, quality/done-gates, mutation tools, Knowledge Vault and compounding owners consume the evidence they need; reachability is tested.
11. A/B benchmark compares outcome quality and engineering cost to the existing baseline; do not declare universal superiority without the data.
12. Lessons/anti-patterns are promoted at the narrowest justified scope through existing UKDL/Knowledge Vault/Construction Event ratchets; fresh agents inherit the capability.
13. Repo check and exact owner path evidence are archived; all changes land with tests, scope-aware commit, no unexplained regression or unverified DONE.

## First action when activated

Run an evidence-first Reality Scan against the **then-current** CPP HEAD and the upstream TDD skill, and produce a small reuse/extend/connect decision ledger. Start from `rules/common/testing.md`, UQF P07, intent-verify, auto-test, verification-loop and test-gaps. **Do not start by adding a new skill file, hook or TDD engine.**

## Status and provenance

This document records **approved backlog intent**, not an implemented or runtime-verified feature. Sources: user direction of 2026-10-11; existing CPP paths inspected that day; upstream URL supplied by user. Any capability claim beyond those inspected artifacts must be validated during work package CPP-TDD-01.
