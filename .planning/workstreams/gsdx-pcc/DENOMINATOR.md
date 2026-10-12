# Completion denominator -- gsdx-pcc

Discovered from: the dataset (46 sections), the Reality Scan (spec §Reality Scan), historical incidents, and
gaps found during execution (append rows; never delete one). Status: OPEN | DONE | BLOCKED | REJECTED | UNNECESSARY
| DEFERRED_EXTERNAL. Every non-OPEN row cites evidence (commit, test gate, EVIDENCE.md line). UNKNOWN is never a
disposition. Phase = the roadmap phase expected to close it.

| id | concept (dataset §) | owner found (Reality) | disposition | phase | status | evidence |
|---|---|---|---|---|---|---|
| D01 | FRESH/INHERITED/SUPERSEDED/UNKNOWN->full (intro) | none | EXTEND convergence projection | 2,4 | OPEN | Phase 2 part landed (V-PCC-STATE-TRUTH-TABLE 2916 cells, V-PCC-FINGERPRINT-*, drills d01-*; 02-EVIDENCE.md); closed by Phase 4 |
| D02 | TTPD first-class (§1) | none | BUILD projection over GoalLog | 9 | OPEN | |
| D03 | Five laws executable (§2) | UCR-CIF doc only | CONNECT as invariants + V-gates + baseline entries | 2,10 | OPEN | Phase 2 part landed (V-PCC-LAW-*, drill d03-ledger-blind; 02-EVIDENCE.md); closed by Phase 10, R09 |
| D04 | Four frontiers (§3) | reconcile scalar | EXTEND compile_frontier | 3 | DONE | 03-VERIFICATION.md (Linux plane GSDX_FRONTIER_PASS=40/40 x9 at 298ba2c6; drills m1-m8 KILLED); V-FRONTIER-FRONTIERS, -GLOBAL-WAIT, -WAIT-ONLY-EMPTY; m1 |
| D05 | Convergence graph (§4) | none | BUILD minimal edges in frontier | 3 | DONE | 03-VERIFICATION.md (Linux plane GSDX_FRONTIER_PASS=40/40 x9 at 298ba2c6; drills m1-m8 KILLED); V-FRONTIER-GRAPH |
| D06 | No global WAIT (§5) | reconcile.py:148 | EXTEND | 3 | DONE | 03-VERIFICATION.md (Linux plane GSDX_FRONTIER_PASS=40/40 x9 at 298ba2c6; drills m1-m8 KILLED); V-FRONTIER-LEGACY-EQUAL, -SWEEP-N, -BEGIN-REFUSES |
| D07 | Execution unit properties (§6) | epoch spec | EXTEND (derived, not model-filled) | 3 | DONE | 03-VERIFICATION.md (Linux plane GSDX_FRONTIER_PASS=40/40 x9 at 298ba2c6; drills m1-m8 KILLED); V-FRONTIER-UNIT-DERIVE, -UNDECLARED, -INDEP, -RESOURCE, -UNSAFE-WRITES; m2 m3 m4 |
| D08 | Critical-path scheduler (§7) | none | BUILD, measured priors, UNKNOWN allowed | 3 | DONE | 03-VERIFICATION.md (Linux plane GSDX_FRONTIER_PASS=40/40 x9 at 298ba2c6; drills m1-m8 KILLED); V-FRONTIER-PRIOR, -CRITICAL-PATH |
| D09 | Wall-clock vs compute postures (§8) | goal budget | EXTEND budget owner | 3 | DONE | 03-VERIFICATION.md (Linux plane GSDX_FRONTIER_PASS=40/40 x9 at 298ba2c6; drills m1-m8 KILLED); V-FRONTIER-POSTURE, -SWEEP-BOUND; m5 |
| D10 | Typed proof contract (§9) | done_gate + gate_class | EXTEND, legacy = 1-element contract | 2,4 | OPEN | Phase 2 part landed (V-PCC-GATE-CLASSES-PINNED, V-PCC-CONTRACT-WEAKENING-IGNORED, V-PCC-FRESHNESS-SCAN-ESCALATES-ONLY, drills d10-*; 02-EVIDENCE.md); closed by Phase 4 |
| D11 | Proof algebra AND/OR/SEQ/QUORUM (§10) | none | BUILD minimal | 4 | OPEN | |
| D12 | Causal proof binding (§11) | tree_id whole-repo (Reality 4) | EXTEND, unknown -> legacy binding | 4 | OPEN | |
| D13 | Proof certificate (§12) | evidence_bundle (no certificate) | EXTEND producer | 4 | OPEN | |
| D14 | Freshness classes (§13) | gate_class | EXTEND | 4 | OPEN | |
| D15 | Judge VALIDATE vs REPLAY (§14) | judge.py | EXTEND | 5 | OPEN | |
| D16 | Parallel judge replay (§14) | judge.py serial | EXTEND bounded | 5 | OPEN | |
| D17 | Reviewer concurrency (§15) | evidence_bundle ticket/nonce | CONNECT + close A->B->A hole | 5 | OPEN | |
| D18 | Isolated parallel mutant farm (§16) | mutation_drill isolated; probe live | EXTEND drill discipline | 6 | OPEN | |
| D19 | Mutation contract by failure class (§17) | ratchet tiers | EXTEND | 6 | OPEN | |
| D20 | Minimal sufficient verification set (§18) | none | BUILD solver, UNKNOWN -> FULL | 4 | OPEN | |
| D21 | Universal impact adapter contract (§19) | change_impact Python-only | EXTEND owner | 7 | OPEN | |
| D22 | Semantic (non-import) impact edges (§20) | GK-13 doc only, no code | BUILD in adapter contract (GK-13 vocabulary) | 7 | OPEN | |
| D23 | Candidate snapshots (§21) | tree_id only | BUILD on git objects | 4 | OPEN | |
| D24 | Continuous verification (§22-23) | none | follows D12+D23, measured in 9 | 4,9 | OPEN | |
| D25 | Speculative execution (§24) | none | BUILD bounded/isolated/cancellable, yield tracked | 3 | OPEN | Phase 3 part landed: admit_speculative policy + report (V-FRONTIER-SPEC-ADMIT, -SPEC-REFUSE, -REPORTED-NOT-EXECUTED); nothing speculative executes; executed speculation closed by Phase 4; 03-VERIFICATION.md |
| D26 | Racing candidates (§25) | none | BUILD on worktrees, same proof contract | 3 | OPEN | Phase 3 part landed: admit_race policy + yield ledger (V-FRONTIER-RACE-ADMIT, -YIELD); nothing races; executed racing closed by Phase 4; 03-VERIFICATION.md |
| D27 | Resource-aware scheduling (§26) | parallel_mesh advisory | EXTEND (pure fns, synthetic ids) | 3 | DONE | 03-VERIFICATION.md (Linux plane GSDX_FRONTIER_PASS=40/40 x9 at 298ba2c6; drills m1-m8 KILLED); V-FRONTIER-CLASSES |
| D28 | Worker classes (§27) | cognitive scheduler (panes only) | EXTEND | 3 | DONE | 03-VERIFICATION.md (Linux plane GSDX_FRONTIER_PASS=40/40 x9 at 298ba2c6; drills m1-m8 KILLED); V-FRONTIER-ORDER, -CRITICAL-PATH; m6 |
| D29 | Boundary ContextImages (§28) | brief.py | EXTEND per-job briefs | 8 | OPEN | |
| D30 | Continuation object (§29) | mission card + brief | EXTEND | 8 | OPEN | |
| D31 | Semantic epoch rotation alignment (§30) | gsd_mission rotation | CONNECT | 8 | OPEN | |
| D32 | Convergence monotonicity / no-progress (§31) | mission no_progress (commits only) | EXTEND to frontier delta | 8 | OPEN | |
| D33 | Information-gain scheduling (§32) | none | BUILD separate signal | 3 | DONE | 03-VERIFICATION.md (Linux plane GSDX_FRONTIER_PASS=40/40 x9 at 298ba2c6; drills m1-m8 KILLED); V-FRONTIER-INFOGAIN |
| D34 | Failure-first scheduling (§33) | none | BUILD, measured priors only | 3 | DONE | 03-VERIFICATION.md (Linux plane GSDX_FRONTIER_PASS=40/40 x9 at 298ba2c6; drills m1-m8 KILLED); V-FRONTIER-FAILURE-FIRST |
| D35 | Latency observatory (§34) | none | BUILD projection | 9 | OPEN | |
| D36 | Metric set, not collapsed (§35) | none | BUILD | 9 | OPEN | |
| D37 | Shadow mode + escape law (§36) | none | BUILD | 7,9 | OPEN | |
| D38 | Adapter maturity states (§37) | none | BUILD append-only events, ceiling PROBATION | 7 | OPEN | |
| D39 | Fresh proof islands (§38) | REALITY plane + gate_class | EXTEND policy | 4 | OPEN | |
| D40 | Phase-6 recompilation replay (§39) | io-ucg history (Reality 15) | REPLAY | 9 | OPEN | |
| D41 | Elixir pilot (§40) | none | BUILD adapter in SHADOW on io-chatgpt-plugin copy | 7 | OPEN | |
| D42 | Owner map (§41) | spec | per rows | -- | OPEN | |
| D43 | Backward compat decide()/done_gate (§42) | reconcile/convergence | EXTEND + legacy replay test | 2 | DONE | 02-EVIDENCE.md; replay suite GSDX_PCC_REPLAY_PASS=28/28; golden 98609c4f before proof.py 735170c0; V-PCC-NO-LEGACY-EDIT |
| D44 | Event log, not second DB (§43) | GoalLog | invariant test | 2 | DONE | a353fb7b; 02-EVIDENCE.md; V-PCC-NO-SECOND-STORE, V-PCC-PROJECTION-PURE, V-PCC-WRITER-CAS, drill d44-cache-write |
| D45 | Explicit INHERITED events (§44) | none | BUILD event | 4 | OPEN | |
| D46 | Work classes (§45) | none | BUILD ledger + evidence-gated promotion | 9 | OPEN | |
| D47 | GSD X root function wording (§46) | spec | EXTEND module docs + baseline | 10 | OPEN | |
| R01 | Gate output lost on Windows (gate.py:72) | gate provider | FIX red-first + drill + UKDL | 1 | DONE | 58934936; GSDX_GATE_PROVIDER_PASS=18/18 (01-phase-end-gate-provider.log); drill MUTANT KILLED gate=V-GATE-VERDICT-FIELDS exit 0 (01-r01-drill.log); UKDL T-SUBPROCESS-WITHOUT-INHERITED-STD-HANDLES-LOSES-GRANDCHILD-OUTPUT-ON-WINDOWS-001; .planning/workstreams/gsdx-pcc/phases/01-w0-reality-baseline-and-incumbent-measurement/01-EVIDENCE.md |
| R02 | Whole-repo tree binding | git_state.py:129 | covered by D12 | 4 | OPEN | |
| R03 | Goal workers get no family baseline (`claude -p`) | providers/claude.py | FIX via brief injection | 10 | OPEN | |
| R04 | mutation_probe live-tree mutation (8/10 pairs) | mutation_probe | farm never uses live mode; record as debt | 6 | OPEN | |
| R05 | evidence_bundle A->B->A hole | evidence_bundle.py:140 | close in D17 | 5 | OPEN | |
| R06 | auto-testing detectors lack mix.exs | auto-testing/detectors.py | EXTEND or prove FULL fallback | 7 | OPEN | |
| R07 | Ecosystems: Python, Elixir, Rust, Go, Java, Kotlin, Node, PHP, Ruby | sdd_os/scaffold + hook-runtime | each: trusted adapter OR proven FULL fallback | 7 | OPEN | |
| R08 | Pilot identity: Owner chose io-chatgpt-plugin; scout found Phase 6 in io-ucg | Reality 15 | pilot io-chatgpt-plugin, replay io-ucg; record discrepancy | 7,9 | OPEN | |
| R09 | software_construction tower family (Owner D-O2) | modules/tower | BUILD B0 + inheritance proof | 10 | OPEN | |
| R10 | gsd_x/goal/* unreachable per liveness gate (frozen as inherited debt in Phase 1) | modules/liveness/reachability.py; 17 gsd_x/goal units among 57 offenders at fbca24fc in this worktree (61 in the main checkout), frozen in vault/liveness/reachability_registry.json known_orphans | wire or DECLARE in reachability_registry by Phase 10 | 10 | OPEN | frozen at 96bdb8b1; .planning/workstreams/gsdx-pcc/phases/01-w0-reality-baseline-and-incumbent-measurement/01-liveness-before.md |
| R11 | Incumbent test_gsd_x_goal_mutation.py timing UNKNOWN in Phase 1 | tools/gsdx_reality_baseline.py (01-INCUMBENT.md:71; Owner decision 2026-10-07 20:05: keep UNKNOWN in Phase 1) | ENTRY OBLIGATION of Phase 6: measure the incumbent mutation suite itself in an isolated copy (`tools/gsdx_reality_baseline.py suites --suite tools/test_gsd_x_goal_mutation.py --in-copy`, plus the required `--out`/`--log-dir`; full form in 01-05-SUMMARY.md:47) before any speedup claim | 6 | OPEN | |
| R12 | `unknown:` tree ids compare equal (git_state.tree_id returns the constant `unknown:not-a-git-tree`), so two unknown trees match in closure/reconcile | modules/gsd_x/goal/git_state.py (02-RESEARCH.md G2) | FIX red-first in Phase 4 (UNKNOWN never equals UNKNOWN); not in the Phase 2 zero-behaviour seam | 4 | OPEN | |

## Mutation corpus (each a faithful mutant killed for the right reason)
false reuse after relevant change · failure to invalidate a causal dependency · UNKNOWN treated as clean ·
unsupported adapter authorising selective execution · stale review surviving mutation · gate weakening accepted ·
builder self-certification · fresh-required proof inherited · resource collision admitted as independent · global
WAIT despite independent work · unsafe parallel writes · proof omitted without INHERITED event · full path finds
failure optimized path called covered · adapter authority kept after discrepancy · candidate changes under
verification · handoff loses a blocking frontier.
</content>
</invoke>
