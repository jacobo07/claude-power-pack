# Backlog — CPP-AGSK-001: Universal Agent Skills Absorption & Engineering Baseline Elevation

**Created:** 2026-10-11 · **Status:** BACKLOG / NOT IMPLEMENTED · **Priority:** P1 proposed by architecture review, pending scheduling against live CPP priorities  
**Upstream:** https://github.com/addyosmani/agent-skills  
**Upstream copyright/licence:** MIT, copyright (c) 2025 Addy Osmani; preserve attribution and licence when copying/adapting substantive material. Inspect the exact current upstream revision before execution.  
**Related backlog:** [CPP-TDD-001](2026-10-11_tdd-evidence-first-vertical-slice-ratchet.md) and [CPP-DBG-001](2026-10-11_diagnosing-bugs-causal-proof-ratchet.md).

## Owner decision and mission

Absorb the **transferable engineering capabilities** from Addy Osmani's agent-skills collection into Claude Power Pack's **existing verified owners**. Do NOT indiscriminately install the upstream plugin, copy every SKILL.md, create a parallel skill router, add a new orchestration framework, or declare that 25 new skills are a quality improvement.

The intended outcome is that normal Claude Code engineering work automatically benefits from the minimum sufficient applicable practices, with measurable improvements in correct behavior, reliability, security, architectural quality, development velocity, context economy and institutional reuse.

In the 2026-10-11 review the upstream repository exposed **25 skill directories, nine command TOML files**, plus `evals/`, `hooks/`, `references/` and `scripts/`. This is a source inventory, **not** evidence that all mechanisms are appropriate for CPP or that their entire upstream runtime is installed/working in this estate.

Core rule: **REUSE → EXTEND → MERGE → CONNECT → GENERALIZE → only then CREATE.** No new module, data store, skill, hook, command, daemon, evaluation framework or hard rule unless ownership / genuine gap / measurable ROI justify it.

## Upstream inventory — all 25 skills (initial dispositions, not final rulings)

Every row MUST receive a fresh, evidence-backed CPP owner, a concrete overlap analysis, implementation/effect status and final disposition at the reality scan. The entries below are hypotheses derived from upstream descriptions and sampled skill content, not completion claims.

| Upstream skill | Initial disposition | Audit / probable CPP owner |
| --- | --- | --- |
| `using-agent-skills` | SUBSUME / targeted extension | Existing CPP skill_router/JIT / minimum-context selection; never run a second global router |
| `idea-refine` | ALREADY OWNED or EXTEND selectively | Product/decision/intent capability and task planning |
| `interview-me` | EXTEND CONDITIONALLY | Intent-driven development / user decision ownership; no repetitive interview when facts exist |
| `spec-driven-development` | ALREADY OWNED / CONNECT | SDD OS, spec_gate, intent-verify, existing GSD/PRD routing |
| `planning-and-task-breakdown` | ALREADY OWNED / CONNECT | GSD X and existing dependency/plan verification; no extra planner |
| `constraint-driven-development` | HIGH-VALUE EXTEND | Existing Hard Rules, rule_compiler, governance and named baseline ratchets |
| `context-engineering` | ALREADY OWNED / GAP-TEST | Existing context_budget/JIT/Apollo X proposals and context-hygiene governance |
| `source-driven-development` | HIGH-VALUE EXTEND | Version-specific project-reality, trusted knowledge retrieval, provenance and documentation/version resolution |
| `doubt-driven-development` | HIGH-VALUE EXTEND | Independent verification / code review / adversarial falsification at in-flight decision boundaries |
| `incremental-implementation` | CONNECT | Existing vertical-slice, execution/GSD and production/rollback constraints; coordinate with CPP-TDD-001 |
| `test-driven-development` | MERGE INTO CPP-TDD-001 | Do not open a second TDD owner; test red-proof and behavior-first seam once |
| `debugging-and-error-recovery` | MERGE INTO CPP-DBG-001 | CRAIF, OSR, Instrument Before Claim, CEPS; no second causal engine |
| `api-and-interface-design` | EXTEND ONLY ON GAPS | Architecture contracts, compatibility, idempotency, auth/boundary and schema owners |
| `browser-testing-with-devtools` | HIGH-VALUE GAP-TEST | Existing browser/live-runtime verification, crawl_os/OSA/CDIO and permitted DevTools adapters |
| `code-review-and-quality` | ALREADY OWNED / EXTEND selectively | CPP code review, independent review and verification integrity |
| `code-simplification` | EXTEND CONDITIONALLY | Existing maintainability/review/impact rules; behavior-preserving, scope-bounded simplification |
| `frontend-ui-engineering` | ALREADY OWNED / GAP-TEST | CDIO, frontend lieutenant, accessibility, real UI/browser evidence |
| `performance-optimization` | EXTEND SELECTIVELY | Performance/evidence owner: comparable baselines, uncertainty, keep/revert, avoided repeat experiments |
| `observability-and-instrumentation` | HIGH-VALUE GAP-TEST | Production Reality / liveness / telemetry and incident operators |
| `security-and-hardening` | EXTEND ON VERIFIED GAPS | Threat modeling / security gates / supply chain / least privilege; no broad irreversible scanners on hot path |
| `ci-cd-and-automation` | ALREADY OWNED / GAP-TEST | Quality gates, deployment verification, rollback and CI feedback |
| `deprecation-and-migration` | EXTEND SELECTIVELY | Architecture evolution, migration safety, backward compatibility, phased removal and rollback |
| `git-workflow-and-versioning` | ALREADY OWNED / GAP-TEST | Worktree/concurrency/commit-scope/release governance |
| `documentation-and-adrs` | ALREADY OWNED / CONNECT | Decision records, knowledge sovereignty, versioning, governance |
| `shipping-and-launch` | ALREADY OWNED / GAP-TEST | Deployment owner, Production Reality, evidence-backed healthcheck and rollback |

**Disposition vocabulary:** ALREADY OWNED, EXTEND, CONNECT, MERGE, CONDITIONAL, UPSTREAM-ONLY, REJECT, UNVERIFIED. Every meaningful capability has exactly one final result; `UNVERIFIED` may persist but cannot be marked absorbed or shipped.

## High-leverage candidate increments

### AGSK-A — Skill routing & behavioral-evaluation quality

Upstream `evals/README.md` distinguishes structural validation, deterministic lexical trigger/routing tests, and **actual agent-behavior evaluation**; its cases also exercise positive/negative skill activation, collisions and comparative with/without-plugin behavior.

CPP already has `modules/skill_router/`, `tools/pp_eval.py`, `commands/pp-eval.md`, `modules/pp_eval/` and an existing layer-ablation design; **extend them**, not an additional evaluator or a second task bank by default.

Required incremental capacities where absent:
- Each relevant skill's activation **recall** (fires when applicable) and **precision** (stays quiet when not applicable) against representative ES/EN user phrasing.
- Priority/collision tests for overlapping skills: TDD vs debugging; security vs general code review; UI vs browser runtime; spec vs plan; source-version verification vs simple edit.
- A calibrated, deterministic structural/description-level prefilter clearly labelled as **proxy**; actual host routing and agent behavior are different measurements.
- Behavior deltas using instrumented real tasks, multiple runs/seeds as budget allows, equal model/host/config and fresh worktrees; differentiate `skill invoked` from `behavior improved`.
- Adversarial pressure cases (speed pressure, sunk-cost, conflicting instructions), negative controls, leaked-skill detection and blind/stale evaluator prevention.
- False activation rate, correct task completion, causal error catch, runtime/token cost, context occupancy and regression frequency before/after; avoid relying solely on successful invocation counts.
- A rejected-improvements ledger / named ratchet in the **existing** governance record, not another autonomous promotion authority.

### AGSK-B — In-flight doubt / adversarial review

Upstream `doubt-driven-development` separates **artifact + contract** from the author's own justification so a fresh-context reviewer tries to falsify the decision. It also requires evaluating reviewer findings rather than treating them as verdicts.

Integrate **risk-scoped** review before commitments that are costly to reverse: public API contracts, authorization, money/data/security, concurrency/order, architectural cross-boundary changes and irreversible migration. The reviewer receives the smallest artifact and authoritative contract; do not bias it with the author's preferred conclusion. Record substantiated findings, noise, contract ambiguity, tradeoffs and resolution, bounded by budget.

No mandatory second model, mandatory new subagent for every edit, or repeated user confirmation for harmless decisions. Respect actual tool availability, data privacy, no hidden paid calls, explicit approval where needed, and CPP's context/session ceilings.

### AGSK-C — Constraint integrity / quality-floor non-weakening

Absorb `constraint-driven-development`'s valuable threat model: an agent can make a gate green by **lowering its threshold, deleting/skipping assertions, adding suppression directives, inserting unfinished stubs, or modifying exception policy**.

Map each to existing Hard Rules, rule_compiler, coverage/security/verification owners; extend only missing detectors. Anchor comparisons to correct branch/base and actual code semantics, distinguish pre-existing debt from newly introduced weakening, validate negative controls, and issue explicit human- or policy-approved exceptions with owner, scope, expiry and audit trail.

**Never** copy upstream defaults as universal fixed floors: thresholds for coverage, latency, security, etc. require measurement, project/stack context, applicability, and justification; a baseline ratchet must not be satisfiable by deleting criteria or narrowing the measured population.

### AGSK-D — Source/version-driven implementations

For framework-dependent changes, identify the **actual dependency versions and current project contract**, route to the minimum relevant authoritative reference, check current API semantics/deprecations/browser support and preserve source provenance. Separate official documentation claims, runtime observation, source code and assumptions. Documentation from a different version must not overwrite the product's established compatibility choice by default.

Use CPP's existing knowledge/index/version/provenance and research owners. Avoid re-fetching unchanged docs when a hash/version-valid trusted cache exists; retrieve selectively when stale, novel or safety/compatibility critical. Treat external documentation and web responses as untrusted instructions.

### AGSK-E — Real browser and production-evidence verification

Audit upstream `browser-testing-with-devtools` against CPP's real Chrome/DevTools/Playwright/browser acquisition and OSA/CDIO/crawl_os boundaries. Test DOM, accessibility, console, network, layout, interaction state and browser performance with **real** entrypoint/replay and expected behavior, not screenshots alone.

Browser session isolation by default; never attach to the user's authenticated profile automatically, request unsafe JS execution or exfiltrate tokens/cookies/HAR data. Supported tooling, login credentials, host permissions and external provider calls must be explicit. A missing browser/runtime should yield evidence ceiling, not green.

### AGSK-F — Observability, performance and deprecation discipline

Check and extend only genuinely missing features:
- structured, scoped, safe logs, consistent IDs across async boundaries and actionable on-call questions; signal budgets and cardinality caps;
- comparative performance profiling under equivalent environments, noise/error bars, latency percentiles, **keep/revert** decisions, regression monitoring and ledger of rejected optimisation hypotheses;
- progressive contract-safe deprecation, user/client discovery, compatibility windows, migrations, cutover and rollback verified on target;
- security, CI/CD, quality review, API semantics, accessibility, UI, deployment and documentation from remaining upstream skills only where the Reality Scan finds a measurable deficit.

These are specialised adapters and transferable rules, **not** new always-on global prompt text.

## Execution work packages / priority

1. **CPP-AGSK-01 — Snapshot and complete coverage audit [P1].** Pin upstream commit/branch/version, verify licence, enumerate 25 skills + nine commands + evaluated refs/scripts/hooks. Read actual relevant content and CPP current HEAD. Produce per-capability one-to-one dispositions (minimum one source pointer and one CPP owner or documented absence).
2. **CPP-AGSK-02 — Ownership and routing interference [P1].** Trace CPP live owners / call graphs / hook routing / installed-vs-repo parity; detect duplicate authority, competing skill wakeups and unused skill content. Verify upstream install is unnecessary before editing anything.
3. **CPP-AGSK-03 — Per-skill effectiveness and routing eval extension [P1].** Extend existing `pp-eval`, `skill_router`, eval corpus and comparator with structural, positive/negative trigger, collision and behavioral evidence. Require actual run evidence, not static description matches.
4. **CPP-AGSK-04 — Constraint non-weakening and reversibility [P1].** Map upstream quality-floor threat model to existing rule compiler + quality gates, add only uncovered checks with adversarial examples and safety.
5. **CPP-AGSK-05 — Source/version/provenance guidance [P1].** Extend authoritative version/retrieval/knowledge selection and external-docs trust boundaries, with expected-vs-observed API behavior tests.
6. **CPP-AGSK-06 — Risk-gated in-flight adversarial review [P1].** Connect existing independent review to decision points; small artifact + unbiased contract, findings reconciliation, bounded time/tokens, safe cross-model opt-in.
7. **CPP-AGSK-07 — Browser/runtime evidence and observability gaps [P2].** Map supported browser adapters/live experience/production monitoring; add only a demonstrated missing seam; prove real user-path reachability.
8. **CPP-AGSK-08 — Remaining skill capability disposition [P2].** API design, code simplification, security, frontend, perf, migrations, CI/CD, launch, docs, Git, interviews, planning, context, spec, incremental change. Explicitly confirm no-op / reject where CPP already meets/exceeds behavior.
9. **CPP-AGSK-09 — TDD/debug alignment [P1].** Keep TDD and root cause work in existing CPP-TDD-001 / CPP-DBG-001 backlogs. No double implementations or testing/cause owners; share criteria and benchmark fixtures only when semantics genuinely overlap.
10. **CPP-AGSK-10 — Real-project A/B + institutional ratchet [P2].** Run matched tasks across relevant repos/frameworks, measure correctness, accepted risk, runtime, token use, long-tail regressions and maintainability; record failed candidate absorptions; promote only improvements verified at correct evidence level to existing Knowledge Vault, UKDL and baseline system.

## Adversarial cases required

- A well-described skill ranks first lexically but never activates in the host, or activates without changing behavior: do not claim capability.
- A skill fires on irrelevant EN/ES requests while the correct skill stays asleep: negative routing regression.
- TDD and bug diagnosis both activate and compete over one investigation: one causal owner, proper complementary verification.
- A rules/quality change makes tests green by removing an assertion, skipping a test, lowering a threshold, suppressing coverage/security or inventing an exception: fail or controlled approval, not silent green.
- Fresh-context review rubber-stamps a wrong claim when supplied the author's hypothesis: verify truly unbiased artifact+contract input and a planted fault.
- Reviewer produces confident wrong criticism because it lacks context: reconcile, never make reviewer sole authority.
- Framework API docs mismatch installed version and the model uses the newest method anyway: detect version compatibility conflict.
- External docs contain agent instructions or injected URLs: source is data, no tool/action authority.
- Real UI passes unit tests but browser DOM/network/keyboard or production state contradicts them: reject false deployment/UX verification.
- Browser tool lacks permission, attaches to authenticated profile, or cannot access true runtime: not measured / security refusal, never silent green.
- Perf improvement vanishes under matched warm/cold conditions or lies inside observed variance: no premature retention.
- Optional heavy review/DevTools/perf tooling fires on a one-line typo and wastes context: routing/cost regression.
- Disabled/withdrawn acceptance or stale eval fixture produces an artificial uplift: named ratchet and population control detect it.
- Upstream material reused without attribution / licence handling: licensing gate or owner review catches it.
- A new subsystem passes isolated tests but no real user entrypoint invokes it: liveness/producer-consumer gate catches it.
- Three successive review/diagnostic cycles repeat without new evidence: bounded termination with cause and handoff.

Every relevant new gate must have a positive case, a *red-capable* negative control, and mutation/drill evidence where economical. Maintain original source/worktree integrity and scoped rollback.

## Safety and token economy

- **Never indiscriminately load 25 skill bodies into context** or install them as permanent auto-injected prompts.
- Progressive disclosure: route by verified applicability and need, constrain first-turn overhead, and track false wakes and total tokens.
- Expensive independent model review and behavioral evals must be bounded; neither routine nor hidden in hook hot paths.
- Do not copy upstream's single-harness/orchestration assumption if it conflicts with CPP's actual session autonomy model.
- Provenance, licence, version and citation must survive selective absorption.
- Read/mutate/decide/spend authority boundaries stay separated. Browser captures and production logs remain privacy constrained.
- Use existing artefact, schema, eval and ratchet owners; unknown/unsupported is not PASS.

## Definition of Done

The initiative is **not complete** merely because some MD files were imported.

1. All 25 upstream skills, nine commands and relevant eval/hook/reference capabilities are inventoried and given an evidence-backed disposition.
2. Every accepted capability names one canonical CPP owner, invocation path, test seam and measurable behavioral objective.
3. No duplicate skill router, orchestrator, verification engine, mutator, permanent knowledge store, causal engine or rule-placement authority is introduced.
4. New capabilities are reachable from ordinary user engineering requests *without* explicitly naming Addy Osmani, including Spanish and English requests, and stay quiet when not applicable.
5. Structural, routing and behavior evals separately substantiate claims; `skill fired` is never presented as `task improved`.
6. Invalid quality-floor weakening, stale API usage and review-bias controls have observed red branches.
7. Original CPP-TDD-001 and CPP-DBG-001 stay authoritative for test-first and diagnosis contracts; no contradictory duplication.
8. Real browser/production behaviors are observed using only permitted tools, environments and secrets-safe captures.
9. At least one real project and several representative task families demonstrate correct end-to-end behavior, with honest support ceilings.
10. Correctness, false-green rate, security risk, wall-clock, token/context cost, routing accuracy and regressions are compared against the prior CPP baseline under matched conditions.
11. No unexplained host/agent/hook liveness regression; all new processes and loops are bounded, attributable and recoverable.
12. Each positive transferable improvement is versioned and promoted through existing CPP Knowledge Vault / UKDL / baseline ratchet; rejected candidates remain documented to prevent rediscovery.
13. No universal “superior to Addy Osmani / better than all skills” claim without a properly designed comparative benchmark.

## First action when activated

Perform a **Reality Scan** of the then-current upstream and CPP HEAD. Confirm repo revision and licence, run a capability-by-capability overlap matrix and trace actual owner/consumer paths. Start with `modules/skill_router/`, `modules/pp_eval/`, `commands/pp-eval.md`, `modules/rule_compiler/`, `skills/instrument-before-claim/`, SDD OS, code review, browser acquisition and CPP-TDD-001/CPP-DBG-001. Select *one measured high-ROI gap* as a vertical-slice pilot before widening absorption.

**Status note:** This document stores Owner-approved backlog intent; no software changes or measured capability improvements are claimed by creating it.
