# CPP-AIA-001 — The 48 Atomic Engineering Obligations (R/E/V/K/C/I)

**Source:** Owner's four consolidated 2026-11-20 research reports. **Status:** 48/48 explicitly registered as OPEN / NOT IMPLEMENTED UNDER THIS EPIC. **Accounting:** six families × eight atomic items = 48. This document is a requirement census, NOT a schedule to create 48 new modules. Prior work already shipped can satisfy an item only after *fresh evidence*.
**Parent:** [CPP-AIA-001](2026-11-20_cpp-atomic-institutional-ascension-master.md). **Phase dependencies:** R+V foundations → E/K/C pilots → I valuation and institutional transfer.
**Disposition per item:** NEW_GAP / ALREADY_OWNED_PROVEN / EXTEND / CONNECT / MERGE / NO_OP / REJECT / UNVERIFIED. Owner + current host + evidence must resolve the disposition. **Never change a carried baseline to make a red test green.**

## R — Reality & Liveness Integrity [P0]

Candidate owners: `modules/liveness`, `modules/capability_runtime`, mirror discovery, installation verification, live hook dispatcher.

| ID | Exact required increment | Red-capable proof / negative control |
| --- | --- | --- |
| **R01** | Discover for EVERY capability repository commit, installed bytes, selected runtime and actually invoked implementation. | Drift only the installed file: discrepancy recognized, not false LIVE or matched. |
| **R02** | Reconstruct hook/dispatcher/consumer registration and liveness, including first/second-order cross-language calls; registry entries must not supply their own proof. | Unregistered hook lying in hooks/ must NOT read as LIVE; production dispatcher callback still recognized. |
| **R03** | Reconcile the 73 PLANNED registry entries as of snapshot individually: expected owner, planned consumer, prerequisites, evidence, legitimate deferral vs dead. Re-discover denominator. | Built module without a consumer/authorization cannot be reported shipped; legit PLANNED can remain deliberately dormant. |
| **R04** | Find every runtime-critical unversioned host setting/path and distinguish repo export from actual live config. | Clean installation lacks a host-specific prerequisite: exact missing dependency reported. |
| **R05** | Verify real reachability for advertised CLIs/skills/hooks, not filenames or docs alone. | Missing entrypoint, absent command, dead import or return-success-without-execution yields UNKNOWN/FAIL. |
| **R06** | Reconcile README, SKILLBANK, architecture, manifests and installed catalog with discovered reality. | Old "13 modules" cannot appear as a fresh inventory without source/date. |
| **R07** | Trace each durable receipt/knowledge record into the actual consumer that reads it; identify produced-but-never-consumed evidence. | Inject an orphan receipt and verify it is discoverable as UNCONSUMED, not proof of completion. |
| **R08** | Expose one per-capability queryable view: owner, applicability, repo/live version, wiring, evidence, tests, last activation and limits. | Disable its only real entrypoint: view must demote LIVE without changing capability source. |

**Acceptance:** every discovered applicable capability is dispositioned; unknown host conditions remain unknown; completeness denominator discovered from source and live registration, not hand-picked. Include no false orphans due to dispatcher and no false LIVE from directory presence.

## E — Execution, Effects & Recovery [P0/P1]

Candidate owners: `modules/gsd_x/goal`, `modules/gsd_x/mission`, UWCP, `modules/lease`, `modules/provider_routing`, `modules/contract_fabric`.

| ID | Exact required increment | Red-capable proof / negative control |
| --- | --- | --- |
| **E01** | Preserve dispatch identity before effect and differentiate intent persisted, effect unknown, effect not started and effect completed. | Kill process between intent and dispatch, then immediately after dispatch: no unsafe duplicate re-dispatch. |
| **E02** | Verify active fence at the real protected resource boundary, not merely at scheduler or lease allocator. | Frozen holder A wakes after B obtains successor fence; stale write must fail. |
| **E03** | Ensure remote ambiguity is represented as UNKNOWN_EFFECT and reconciled using provider-supported identity/idempotency or Owner intervention. | Remote effect commits but response is lost: no invented PASS or blind second mutation. |
| **E04** | Replay goal state from durable log including corruption/truncation/race handling, with distinct no-events vs unreadable. | Alter/remove middle event, truncate event or inject sharing violation; no false empty/healthy state. |
| **E05** | Bind event data and projectors to version-compatible schemas; preserve safe replay across code upgrades. | New reader replays old history equivalently or explicitly refuses unsupported version. |
| **E06** | Prove writer authority across laptop/GEX44/VPS and ownership home, including network partitions and stale nodes. | Two nodes attempt incompatible ownership during partition: no double-authorized effects. |
| **E07** | Deduplicate notifications, wakeups, receipts and idempotent effects on correct distinct identities. | Duplicate/out-of-order event causes one logical transition, never false effect dedup based solely on event ID. |
| **E08** | Establish actorless/zero-resident waiting where task needs only external event or time. | Waiting/paused mission uses zero model calls and safely resumes on correct trigger. |

**Acceptance:** survive process death, duplicate/lost events, missed acknowledgements and host transitions without inventing exactly-once for uncooperative external APIs. Recoverable state must outlive transcript, context, worker, worktree and device.

## V — Verification & Proof Integrity [P0]

Candidate owners: `modules/pp_eval`, `modules/gsd_x/goal/judge.py`, Tower/done gate, mutation ratchet, `tools/verify_spp.py` and CI.

| ID | Exact required increment | Red-capable proof / negative control |
| --- | --- | --- |
| **V01** | Inspect live pp_eval task bank, last nightly, usage/budget, discriminating task coverage, current layer fingerprints and A/B oracle. | Empty/ceiling-only bank returns INSUFFICIENT, not NO_LOSS or EFFECTIVE. |
| **V02** | Re-run suites-at-risk inventory (historical 58/126, later carried 14 G1 / 9 G3), prioritize genuinely non-falsifiable protection. | Gate with no failing outcome is surfaced and must detect a seeded failure; legitimate tests not penalized solely by AST heuristics. |
| **V03** | Separate new regressions from named carried debts without deleting criteria, suppressing tests or lowering coverage denominators. | A malicious threshold/population edit masquerading as green triggers authorized exception or red. |
| **V04** | Pin independent judge's verifier version, tree, origin and revision before builder modifies them. | Builder weakens test and reruns it green; judge refuses due to pin drift. |
| **V05** | Assert tested worktree/build artifact is exactly the one being certified; capture environment where relevant. | Execute tests on tree B, try to certify tree A: rejected. |
| **V06** | Pilot property/stateful testing on one critical transition system using the existing test owner. | Generate invalid transition sequence, shrink to minimal counterexample, keep stable proof. |
| **V07** | Run existing Semgrep/OSV wrappers on consented REAL projects; report CLEAN, FINDINGS and UNCHECKED separately; coverage/security gap analysis. | Missing binary/network/lockfile reports UNCHECKED, never CLEAN; changed-line false negative caught. |
| **V08** | Add repo-versioned CI with changed-file proof scope, host-specific allowances, permission hardening and verifiable local parity. | Intentional bad change causes pipeline red, clean baseline does not silently skip entire suite. |

**Acceptance:** every gate that materially protects software has a real invocation path, positive and red-capable negative control and protected oracle; do not force whole-estate 100% execution on every one-line change when affected-proof closure is enough.

## K — Knowledge, Context & Institutional Transfer [P1]

Candidate owners: Knowledge Vault, UKDL, UCR-CIF, `modules/graphify`, `modules/decision_review`, `modules/knowledge_acquisition`, `modules/capability_runtime` and Context First.

| ID | Exact required increment | Red-capable proof / negative control |
| --- | --- | --- |
| **K01** | Bind reusable claims to actual observations, sources, environments, methods and scope. | Unsupported invented rule cannot move from HYPOTHESIS to INSTITUTIONALIZED. |
| **K02** | Detect invalidators (dependency, version, topology, environment, changed requirements), propagate STALE to affected proof/knowledge consumers. | Supersede source/version: applicability or proof rejudged before future use. |
| **K03** | Dedup semantic equivalents while keeping contradictions, caveats, timestamps, provenance and supersession. | Conflicting two-writer and one-writer results not flattened into a false universal. |
| **K04** | Evaluate bilingual positive/negative skill and family routing; distinguish work requests from status/metadiscussion. | "¿queda mucho de arena 5?" cannot awaken KobiiCraft mode *construction*; relevant construction requests do. |
| **K05** | Create minimal, sufficient cognitive interrupt/resumption packet from live obligations rather than entire chat history. | Fresh session continues correctly and preserves a rejected hypothesis without transcript archaeology. |
| **K06** | Record retrieval/consumption and measure whether it actually altered outcome versus control; separate read, cited, applied, beneficial. | Useless injected knowledge cannot be counted as positive influence or institutional lift. |
| **K07** | Classify local/tenant-private knowledge, domain patterns and cross-domain transferrable rules with privacy/applicability guardrails. | A Wii-only compiler tactic is not blindly loaded as a universal app rule; private client raw evidence does not transfer. |
| **K08** | Test one Work Class with and without certified reusable pattern in independent project tasks. | If no improvement, improper routing or regression, do not claim compounding; admit null result. |

**Acceptance:** no new memory SSOT, no growth in unconditional prompt prefix for unrelated jobs, and positive *and* negative transfer tests for globally promoted patterns.

## C — Code & Production Intelligence [P1]

Candidate owners: `tools/change_impact.py`, `modules/graphify`, SDD OS, `modules/osa`, `modules/cdio`, `modules/product_demo`, `modules/auto-testing` and `tools/security_scan.py`.

| ID | Exact required increment | Red-capable proof / negative control |
| --- | --- | --- |
| **C01** | Pilot precise symbol/definition/reference and contract-level change impact using ast-grep/SCIP/Tree-sitter only when it beats current graph. | Public API rename must identify true consumers and not mark unrelated code impacted. |
| **C02** | Extend live post-edit syntax diagnostics to project-aware TypeScript and suitable type checks; keep bounded, targeted costs. | Introduce TS type error: visible same-turn or bounded follow-up without running misconfigured one-file tsc. |
| **C03** | Include dynamic imports, subprocess, cross-language bridges and unknown edges in conservative affected closure. | Unresolvable dynamic dependency raises explicit gap, never false "no tests required." |
| **C04** | Pilot generative property/API testing on a consented real application with actual oracle. | Hidden regression or seed fault caught; false positives reconciled against true contract. |
| **C05** | Add contract/migration checks for schema/API versions, locking, backward/forward compatibility and reversible cutover. | API/schema breaking change cannot clear only-unit-test gate; migration data loss caught. |
| **C06** | Audit supply chain SBOM, SCA, licenses, provenance, dependency drift and source trust with existing security owner. | New vulnerable/unlicensed dependency is identified and status of unavailable scanner remains UNCHECKED. |
| **C07** | Verify built and running product's real user paths (browser/mobile/hardware as applicable), not screenshots or static tests alone. | Broken CTA, disabled form, absent analytics/success state rejected despite green unit tests. |
| **C08** | Account for production config, services, network, remote artifacts and real deployment fingerprint as mutable evidence. | Changing production flag/remote image invalidates previous proof dependent on it. |

**Acceptance:** target software quality, not only CPP gate quality; tests on a different artifact/deployment never certify the real one; specific stack and rights handled explicitly.

## I — Intelligence Economics & Autonomous Capitalization [P1/P2]

Candidate owners: Cognitive OS, `modules/pp_eval`, UCR-CIF, cost_collapse, `modules/decision_review`, Tower.

| ID | Exact required increment | Red-capable proof / negative control |
| --- | --- | --- |
| **I01** | Attribute complete verified-outcome cost: model, context, tools, CPU/RAM, verification, waiting, recovery, infrastructure, humans, maintenance. | A retry-heavy or always-idle workflow must not appear free or cheaper solely on tokens. |
| **I02** | Detect and compile eligible known decisions/operations to deterministic software under original proof/authority guarantees. | Known valid task needs zero model calls; novel or invalid assumptions force safe deoptimization. |
| **I03** | Run risk-gated single-agent vs Hyperplan/adversarial review comparative study. | Tiny typo never launches five-model meeting; serious planted fault is detected at justified cost. |
| **I04** | Use pp_eval ablations on context/rules/hooks/skills with actual positive controls and version matches. | Removing beneficial layer yields reproducible red; removing inert text does not invent uplift. |
| **I05** | Track marginal total cost/novelty across repeated comparable Work Class executions. | Detect plateau: 5th equivalent job repeats costly discovery; record failed capitalization. |
| **I06** | Attribute avoidable Owner interventions by type, authority necessity and recurrence. | Mechanical manual approval cannot be labeled inherently necessary; true irreversible authorization remains Owner. |
| **I07** | Propose retirement/deoptimization for redundant, obsolete, negative-ROI or unused capability without deleting history. | Unused tool with valid required safety role not auto-retired; bogus low usage insufficient. |
| **I08** | Evaluate meta-improvement policy itself: proposal quality, false wins, repeated research, maintenance and total verified value. | Self-improvement proposals proliferate without real consumer/value: institution fails progress test. |

**Acceptance:** profitability is not an excuse to violate safety/proof; institutional gains measured as Product/Reliability/Intelligence/Economic/Developmental Deltas with sensible uncertainty and comparative evidence.

## Universal gate matrix for all 48

Every work item must record: **current HEAD; owner and consumers; before-state with measured denominator; applicability and exceptions; proposed delta; real effect authority; action trace; positive control; negative control; mutation/fault injection where justified; live/system proof; after-state; regression scope; raw receipt and content identity; independent reviewer when high risk; rollback; residual uncertainty; knowledge/UKDL disposition; cost.**

An item may conclude ALREADY_OWNED_PROVEN / NO_OP / REJECT / BLOCKED without creating code. Such a conclusion is a valid closed *assessment* only if its evidence and required effect/no-op checks are valid. Do not mark its hypothesized production capability SHIPPED merely because its paperwork is complete.

## Critical dependencies

R01/R02/R04/R08 unlock truthful execution topology; V01/V02/V04/V05/V08 establish valid judges; E01/E02/E03 and T2 hot-path security precede unattended high-effect autonomy; K01–K04 precede global promotion or trait inheritance; K08/I01/I04/I05/I08 precede claims of measured institutional improvement; C01–C08 are pilots on **real projects**, not speculative frameworks. Follow [release plan](2026-11-20_cpp-atomic-tranches-proof-gates.md) for T0–T5 / A0–A9 order and Owner permissions.
