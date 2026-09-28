---
covers: [external-capability-assimilation, genesis-suite, context-budget, self-continuation, event-driven-loop]
tier: T3
---
# External Capability Assimilation (Genesis Suite + Context Budget + Loop + Self-Continuation) — Revised Plan

## Owner decisions (Phase 2, 2026-09-28)
1a: dedicated worktree off `feature/knowledge-acquisition@2b6f183`; Goal Spine / UCR-CIF worktrees untouched (seams recorded only).
2 hybrid: hot path native Python; cold path vendored MIT Node wrapped by one Python bridge.
3: full scope (all 25 capabilities + runner), multi-session with RESUMPTION_FILE.
4/6: experiments hybrid (dry-run grading + small real-quota runs).
5: autonomy gate goes LIVE immediately (not shadow).
Night Research: runs on the Sovereign VPS only (204.168.166.63, user kobicraft).
Push: everything.

## Reality anchors (measured)
- Package: `Downloads/for cpp-gsd-long.zip` → loop kit (4 files, NO license), self-continuation .md (NO license), context-budget 1.0.0 (MIT), genesis-suite 1.2.0 (MIT, 21 modules, Node ^24.14 — host v24.15.0 OK).
- Existing owners: `tools/gsd_mission.py` (Ralph mission; `quota_hold` @1597 already pauses on quota refusals), `tools/gsd_epoch.py` (epochs, PROVIDER_HOLD cause, certify/census/watch), `hooks/gsd_stop_continuation.js` (Ralph stop-guard, live), `modules/gsd_x` (goal/epoch/obligation/closure/evidence), UWCP (`tools/uwcp_*`, tests), graphify (knowledge graph + change impact GK-13), `_audit_cache` (hash-bound summaries), cost_collapse router, liveness gate, Knowledge Vault lessons, UKDL.
- LIVE MISSION `m-916e905e23d4` (S10 epoch-rotation proof) runs from this checkout; pane c2/e9 own `gsd_mission.py`/`gsd_epoch.py`. Do NOT perturb its behaviour mid-proof.

## Law of the plan
- Unlicensed inputs (loop kit, protocol) are NOT copied: ideas only, source SHA-256 recorded.
- Every capability gets exactly one disposition (EXTEND/MERGE/CONNECT/WRAP/SUBSUME/OPTIONAL/NEW), one CPP owner, a status LIVE/PLANNED/ABSENT, and a proof command. No IGNORED.
- Fail-open upstream semantics (context-budget probe error → 0) are inverted at the CPP boundary: UNMEASURED is a state, never 0.
- Bridge outcomes are four-valued: OK / SUBJECT_INVALID / BRIDGE_FAILED / UNREADABLE — a bridge failure never reads as a pass.

## Phase 4 audit (inline — the auditor agent was refused twice by the agent-solo guard: once by a
## foreign pane's dispatch, once because a read-only auditor cannot satisfy the durable-output clause)
G1 `modules/decision_review/decision_kernel.py` already classifies reversibility A/B/C + blast radius → item 13 EXTENDS DRK; no new classifier.
G2 `tools/gsd_mission.py:136-260` already holds an msvcrt single-flight lock → item 17 harvests only instant-failure quarantine + run receipts.
G3 UWCP = Workspace Capsule (`modules/gsd_x/goal/workspace.py`), NOT a workflow/plan DAG owner → Plan Graph CONNECTS to GSD phase-plan frontmatter (wave, depends_on, files_modified), validated by cpp-gsd-long before a relay/launch.
G4 graphify has no change-impact code (GK-13 is a KB doc only); `tools/audit_cache.py` owns sha256 + depends_on → Change Impact and Verified Reuse EXTEND audit_cache.
G5 The live Ralph hook is loaded straight from this checkout by `~/.claude/hooks/hook-dispatcher.js:172` (critical, 5 s) → "live" = merged into `feature/knowledge-acquisition`; no mirror copy; must stay fast and fail-safe; the S10 mission sees it at merge → change is additive (directive + receipts).
G6 VPS Node is v22.22.2, below Genesis `^22.23.2` → user-level Node 24 on the VPS; bridge checks the vendored engines range and returns BRIDGE_FAILED(engine) otherwise.
G7 VPS free RAM 599 MB (3.9 GB available) → night runner checks headroom before dispatch, INCONCLUSIVE if starved.
G8 T12 red team uses general-purpose agents that WRITE findings to disk as they go (read-only auditors are refused by the guard).
G9 `gsd_mission.py` / `gsd_epoch.py` belong to live pane e9/c2 → worktree branch, re-read HEAD + rebase-free merge at each tranche end.
G10 `quota_hold` has one caller (`gsd_mission.py:1272`) → keep its contract; add a separate `launch_failure_hold` consulted beside it.

## Tranches (execution order; each = 1..n micro-commits, focused gate before commit)

### T1 Provenance + registry
1. `vendor/genesis-suite/**` create — verbatim upstream tree (MIT LICENSE kept per module). Verify: hash manifest matches extracted bytes.
2. `vendor/context-budget/**` create — verbatim (reference for native port). Verify: same.
3. `vendor/PROVENANCE.json` create — source zip SHA-256, inner zip SHA-256s, versions, licenses, the two unlicensed inputs with hashes and "ideas-only".
4. `vault/assimilation/genesis-2026-09/ASSIMILATION_MANIFEST.json` create — 25 capabilities + 9 runner ops + 5 handles, each {capability, owner, disposition, differential, status, proof}.
5. `tools/test_assimilation_manifest.py` create — structural discovery of vendored modules (floor 21), every discovered capability has one entry, no IGNORED, no stale entry, every LIVE entry's proof command exits 0; synthetic red drill. Verify: V-ASSIM-* all pass + red drill fails on injected gap.
6. `modules/external_assimilation/node_bridge.py` + `tools/genesis_bridge.cjs` create — one-shot JSON stdin/stdout call into a vendored module export, timeout, 4-valued outcome. Verify: `tools/test_genesis_bridge.py` incl. node missing / module throws / bad JSON / timeout.
7. `vault/liveness/reachability_registry.json` edit — declare new modules; run `python modules/liveness/reachability.py`.

### T2 Context precision layer
8. `modules/context_budget/meter.py` create (native port) — signals with MEASURED/UNMEASURED, weighted pressure, bands; OBSERVATION ONLY (no policy). Verify: unit tests + parity vs upstream `normalize` on shared cases via bridge.
9. `tools/fresh_context_tax.py` create — from transcripts: first-turn input+cache tokens, bytes of injected bootstrap, tokens before first tool call, time to first action, per epoch; unknown stays unknown. Verify: run on the S10 mission's epochs (real data).
10. `tools/gsd_epoch.py` edit (ADDITIVE, announced to c2/e9) — every rotation/continuation receipt carries a context-budget reading as evidence; policy unchanged (wall/300k stays the decider) until a paired experiment justifies a change. Verify: test_gsd_epoch 66/66 + new receipt field test.
11. Context Graph → SUBSUME into graphify: extend graphify route output with hash binding, freshness, contraindication and approval state per coordinate (differential). Verify: graphify tests + a route whose source bytes changed is marked STALE.
12. Task Context + Source Packets → WRAP via bridge: `tools/source_packet.py` CLI (paths/selectors/expected hashes → bounded packet + gaps). Consumer: successor card in `gsd_mission.py` (announced) replaces broad file dumps with a bounded packet for the current obligation's files; and `/cpp-gsd-long` + Agent prompts reference it. Verify: card bytes before/after on the same mission state (Fresh Context Tax delta measured, not claimed).

### T3 Continuation / loop / provider breaker
13. `modules/autonomy_gate/gate.py` create — Autonomy Decision Gate: 4 seed gates (irreversible, outward-facing, preference, resource-blocked) + CPP stronger controls (destructive-state authorization, HR-CASCADE deploy/rm, secrets, human-facing effects) ; semantic categories, lexical hints only as input; compact decision receipt log. Verify: table-driven tests incl. both poles per gate.
14. `hooks/gsd_stop_continuation.js` edit + live mirror to `~/.claude/hooks` — directive carries the rubric; receipts to `~/.claude/state/autonomy-decisions.jsonl`. LIVE per Owner. Verify: `node tools/test_gsd_stop_continuation.js` + real dispatcher drive + heartbeat advances.
15. `tools/gsd_mission.py` edit — generalise `quota_hold` into a provider circuit breaker: quota refusal (existing), instant-failure streak (worker died < N s with no work) → exponential cooldown, K consecutive → QUARANTINED mission state requiring operator; holds never count as progress nor pay Fresh Context Tax. Verify: test_gsd_mission + injected failure fixtures; red drills.
16. Wake-Up Continuation order in successor card: finished background children → in-flight build → todo → standing. Verify: card test with all four present.
17. Event-driven loop → SUBSUME: Ralph turn-end continuation IS completion-driven rearm; scheduled sweep stays as low-frequency watchdog. Harvest: single-flight incarnation lock check + structured run log if absent (read sweep first; add only the missing invariant). Verify: overlap drill (two concurrent sweep invocations → one acts).

### T4 Workflow / agents
18. Plan Graph → CONNECT to UWCP: write-ownership overlap + cycle/depth validation via bridge in UWCP plan intake. Verify: UWCP tests + overlapping-write plan refused.
19. Worker Router → MERGE properties into T3 breaker + cost_collapse routing (attempt budget, deadline, concurrency cap); vendored router OPTIONAL provider. Verify: routing tests.
20. Batch Drafts → WRAP: `tools/batch_drafts.py` for 2–4 independent static reviews; validation refuses unbound evidence. Verify: real batch over 2 CPP files.
21. Prompt Kit → EXTEND existing Agent prompt contract (objective/owner/criteria/stop/output/deadline/write ownership) — `tools/task_contract.py` renderer used by source_packet and batch. Verify: renderer tests.

### T5 Evidence / review
22. Task Ledger → MERGE into gsd_x mission closure evidence: artifact hash binding + reviewer ≠ worker. Verify: closure tests + reviewer==worker refused.
23. Evidence Collector → WRAP in `gsd_epoch certify`/closure: normalised receipts, missing stays MISSING. Verify: certify on S10.
24. Review Gate → CONNECT: reviewer outputs (pp-code-reviewer, oneshot auditor) parsed strict; malformed/failed = INCOMPLETE never APPROVE. Verify: malformed fixture → INCOMPLETE.

### T6 Knowledge
25. Regression Memory → EXTEND Knowledge Vault lessons with a `regression:` block (failing output, reproducer, source sha256, passing receipt, staleness) + `tools/regression_staleness.py` reopening entries whose bytes moved. Verify: synthetic lesson reopens on byte change.
26. Constraint Compiler → CONNECT UKDL → candidate checks via bridge; output labelled candidate, checksRun=0. Verify: one real UKDL rule compiles; nothing promoted.

### T7 Integrity
27. Change Impact → SUBSUME into graphify change impact (GK-13) — harvest "unmapped impact stays explicit". Verify: test.
28. Release Integrity → `tools/verify_vendor_integrity.py` (vendor bytes vs PROVENANCE, fresh-checkout mode) wired into assimilation gate. Verify: tamper drill.

### T8 Measurement
29. Routing Metrics → WRAP fed by epoch/worker receipts; unknown usage stays unknown. Verify: report on S10.
30. Verified Reuse → EXTEND `_audit_cache` reuse with objective/contract/role binding, no approval inheritance. Verify: stale source → reuse refused.
31. Paired Experiments → WRAP + one preregistered experiment: current successor card vs bounded-packet card (hybrid: dry-run grading + ≤ small real-quota runs). Verify: registration hash frozen before runs; analysis report committed.

### T9 Institutional
32. Task Adaptation → CONNECT to gsd_x obligation revisions: revisions cannot weaken original criteria; accept/reject with actor+reason. Verify: weakening revision refused.
33. Charter Lab → WRAP with CPP state; promotion requires frozen gates + holdout; seam note to UCR-CIF worktree (no write there). Verify: unsupported promotion refused.

### T10 Night Research (VPS only)
34. `tools/night_research_runner.py` — refuses unless host is Linux+kobicraft; window, pause file, single worker, bounded report, findings UNPROMOTED; deploy via git pull on VPS + systemd user timer. Verify: local refusal proof + VPS dry pass + one real pass (quota-bounded).

### T11 cpp-gsd-long integration + Production Reality
35. After S10 completes (or never perturbing it): arm a fresh smoke mission exercising breaker, gate, packet card, pressure receipts; certify ≥1 real rotation with receipts. Verify: `gsd_epoch.py certify`.

### T12 Closure
36. Red team (2 independent reviewers, sequential), Knowledge Vault lessons for every failure met, UKDL candidates (not promoted), UCR-CIF stage per capability, Constitutive Baseline status table, docs, RESUMPTION_FILE, merge into `feature/knowledge-acquisition`, push.

## Multi-pane safety
All edits to `gsd_mission.py`, `gsd_epoch.py`, `gsd_stop_continuation.js` are additive, tested against their full suites, and merged only after re-reading HEAD; bracket wide oracles by dirty-path set.

## Rollback
Each tranche is independent commits; kill switches: `CPP_AUTONOMY_GATE=off`, `CPP_PROVIDER_BREAKER=off`, `CPP_SOURCE_PACKET_CARD=off`; vendor tree removable without runtime effect (bridge returns BRIDGE_FAILED → callers fall back to prior behaviour with a logged reason).
