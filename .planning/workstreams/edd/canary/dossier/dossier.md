# Dossier: edd-run
Contract: .planning/workstreams/edd/source/MISSION_PROMPT.md -> 81 concepts. Zero model calls. Raw hits: refs.jsonl (page it; never guess).

## Modules
- `modules/gsd_x/__init__.py` GSD X -- the applicability predicate gets an event. | defs: - | imported by: NONE
- `modules/gsd_x/cli.py` The seam the hook calls: a UserPromptSubmit payload in, an advisory out. | defs: inherited_block:59, family_block:99, advisory:156, main:177 | imported by: modules/sleepless_qa/__main__.py, modules/sleepless_qa/dumpers/__init__.py, tools/test_family_injection.py, tools/test_tower_inheritance.py
- `modules/gsd_x/goal/__init__.py` GSD X goal spine: a durable goal owned across sessions, worktrees and executors. | defs: - | imported by: modules/gsd_x/goal/sweep.py
- `modules/gsd_x/goal/bind_mission.py` Open one goal epoch that OBSERVES a Ralph mission already running (SPEC-GOAL-OBSERVE-RALPH). | defs: bind_running_mission:44 | imported by: tools/gsd_x_goal.py, tools/test_gsd_x_goal_bind_mission.py
- `modules/gsd_x/goal/brief.py` Compile an epoch brief from DURABLE state, and from nothing else. | defs: BriefTooLarge:40, estimate_tokens:44, compile_brief:48 | imported by: tools/gsd_x_goal.py, tools/test_gsd_x_goal_claude_providers.py, tools/test_uwcp_characterization.py, tools/test_uwcp_foundation.py
- `modules/gsd_x/goal/contract.py` Goal Contract and revision -- the Mission Contract's missing identity. | defs: GoalExists:33, GoalNotDeclared:37, normalise:45, revision_of:61, GoalState:68, project:87, declare:113, revise:124, set_budget:156, set_authority:161, last_event:166 | imported by: modules/gsd_x/goal/bind_mission.py, modules/gsd_x/goal/brief.py, modules/gsd_x/goal/convergence.py, modules/gsd_x/goal/epoch.py, modules/gsd_x/goal/evidence.py, modules/gsd_x/goal/intervention.py, modules/gsd_x/goal/judge.py, modules/gsd_x/goal/reconcile.py (+21)
- `modules/gsd_x/goal/convergence.py` Convergence planes, goal obligations, failures -- and the closure that reads them. | defs: GoalObligation:72, Convergence:96, project_convergence:106, set_plane:147, accept_obligation:160, carry_obligation:187, disposition_obligation:204, record_failure:240, disposition_failure:247, evaluate:261, satisfy:289, GoalClosure:316 | imported by: modules/gsd_x/goal/brief.py, modules/gsd_x/goal/judge.py, modules/gsd_x/goal/providers/gate.py, modules/gsd_x/goal/reconcile.py, modules/gsd_x/goal/sweep.py, tools/gsd_x_goal.py, tools/gsd_x_mission.py, tools/test_gsd_x_goal_bind_mission.py (+9)
- `modules/gsd_x/goal/engine_identity.py` The identity of the code the sweep would run: a digest of its import closure. | defs: engine_closure:120, engine_identity:139 | imported by: modules/gsd_x/goal/bind_mission.py, modules/gsd_x/goal/sweep.py, tools/test_gsd_x_goal_bind_mission.py, tools/test_gsd_x_goal_engine_identity.py, tools/test_gsd_x_goal_sweep_all.py
- `modules/gsd_x/goal/epoch.py` Bounded execution epochs, the provider contract, and receipts. | defs: RetryWithoutNewInformation:64, EpochError:68, ReceiptRefused:79, Observation:86, Receipt:93, Provider:127, echo:143, check_provider:156, scope_hash:166, info_key:202, EpochRecord:224, project_epochs:239 | imported by: modules/gsd_x/goal/bind_mission.py, modules/gsd_x/goal/brief.py, modules/gsd_x/goal/providers/claude.py, modules/gsd_x/goal/providers/codex.py, modules/gsd_x/goal/providers/gate.py, modules/gsd_x/goal/providers/long_run.py, modules/gsd_x/goal/reconcile.py, modules/gsd_x/goal/sweep.py (+20)
- `modules/gsd_x/goal/evidence.py` Negative knowledge that survives session AND model replacement (UWCP S1-5). | defs: HypothesisRefused:43, Hypothesis:52, project_hypotheses:66, record:88, rejected:137 | imported by: modules/autonomy_gate/gate.py, modules/cascade_prevention/types.py, modules/deep-research/deep_research.py, modules/gsd_x/goal/brief.py, modules/knowledge_acquisition/store.py, modules/owner_queue/stop_ledger.py, modules/sdd_os/scaffold.py, tools/gsd_mission.py (+3)
- `modules/gsd_x/goal/git_state.py` What tree is this evidence about? -- and the pin that says which gate ran. | defs: head:35, commits_between:40, blob_oid:62, file_digest:78, pin_scheme:87, digest_matches:95, file_pin:101, tree_id:124 | imported by: modules/gsd_x/goal/epoch.py, modules/gsd_x/goal/judge.py, modules/gsd_x/goal/providers/claude.py, modules/gsd_x/goal/providers/codex.py, modules/gsd_x/goal/providers/gate.py, modules/gsd_x/goal/providers/long_run.py, modules/gsd_x/goal/sweep.py, tools/gsd_x_goal.py (+10)
- `modules/gsd_x/goal/intervention.py` Operator intervention as durable goal events (UWCP S1-7). | defs: OperatorRefused:40, OperatorState:45, project_operator:54, intervene:79, blocking_reason:107 | imported by: modules/gsd_x/goal/reconcile.py, tools/test_uwcp_foundation.py
- `modules/gsd_x/goal/judge.py` The independent judge: re-run the pinned gates, or refuse to certify. | defs: JudgeReceipt:48, record:61, current:73, judge:120 | imported by: modules/gsd_x/goal/sweep.py, modules/keos_qwen/__init__.py, modules/keos_qwen/goals/__init__.py, modules/keos_qwen/goals/fire.py, modules/keos_qwen/goals/seed_goals.py, modules/keos_qwen/score/score_corpus.py, modules/sleepless_qa/healer/orchestrator.py, modules/sleepless_qa/verdict/__init__.py (+2)
- `modules/gsd_x/goal/log.py` The goal event log: the ONE durable record a goal owns. | defs: GoalLogError:46, GoalLogCorrupt:50, LostRace:54, Inconclusive:58, RepoIdUnknown:62, repo_id:84, goals_root:100, event_digest:110, Event:116, GoalLog:138 | imported by: modules/gsd_x/goal/bind_mission.py, modules/gsd_x/goal/brief.py, modules/gsd_x/goal/contract.py, modules/gsd_x/goal/convergence.py, modules/gsd_x/goal/epoch.py, modules/gsd_x/goal/evidence.py, modules/gsd_x/goal/intervention.py, modules/gsd_x/goal/sweep.py (+21)
- `modules/gsd_x/goal/providers/__init__.py` Execution providers for goal epochs. | defs: - | imported by: modules/decision_review/decision_kernel.py, modules/gsd_x/goal/bind_mission.py, modules/gsd_x/goal/sweep.py, tools/test_decision_review.py
- `modules/gsd_x/goal/providers/claude.py` Two Claude providers: one the Factory starts, one a human drives. | defs: HeadlessClaudeProvider:53, InteractiveClaudeProvider:204 | imported by: modules/cpc_os/snapshot.py, modules/universal-meta-systems/runtime/__init__.py, modules/universal-meta-systems/runtime/noun_map.py, modules/universal-meta-systems/runtime/runtime.py, modules/zero-crash/vps/crash_receiver.py, tools/fix_conhost_hook_leak.py, tools/fixtures/pp_eval_fake_claude.py, tools/settings_merger.py (+4)
- `modules/gsd_x/goal/providers/codex.py` Codex as a goal epoch: headless, bounded, and careful with a shared account. | defs: CodexProvider:92 | imported by: tools/test_gsd_x_goal_codex_provider.py
- `modules/gsd_x/goal/providers/gate.py` The deterministic provider: run a named done gate and report what it observed. | defs: GateProvider:35 | imported by: modules/autonomy_gate/__init__.py, modules/autonomy_gate/__main__.py, modules/capability_runtime/retirement.py, modules/duplicate_to_advantage/d2a_engine.py, modules/osr/__init__.py, modules/spec_gate/__init__.py, tools/test_autonomy_gate.py
- `modules/gsd_x/goal/providers/long_run.py` A /cpp-gsd-long run as one epoch of a goal: bind a v2 run, or arm a v3 mission. | defs: mission_id_for:56, LongRunProvider:71 | imported by: tools/test_uwcp_characterization.py
- `modules/gsd_x/goal/reconcile.py` The Goal Reconciler: what is justified next, decided deterministically. | defs: Decision:50, Context:62, decide:124, render:247 | imported by: modules/gsd_x/goal/sweep.py, modules/sqi/__init__.py, modules/sqi/weakening_detectors.py, tools/gsd_x_goal.py, tools/run_sqi.py, tools/test_egcc_c1.py, tools/test_gsd_x_goal_chaos.py, tools/test_gsd_x_goal_reconcile.py (+2)
- `modules/gsd_x/goal/sweep.py` The unattended driver: advance autonomous goals, under preconditions it checks. | defs: state_dir:52, record_path:58, runtime_identity:65, record_gates:86, autonomy_verdict:112, is_autonomous:150, set_autonomous:158, autonomous_goals:184, heartbeat_path:221, retry_engine_term:225, SweepReport:235, sweep_goal:278 | imported by: modules/gsd_x/goal/engine_identity.py, tools/gsd_x_goal.py, tools/test_gsd_x_goal_bind_mission.py, tools/test_gsd_x_goal_engine_identity.py, tools/test_gsd_x_goal_gate_class.py, tools/test_gsd_x_goal_sweep.py, tools/test_gsd_x_goal_sweep_all.py, tools/test_task_ledger_seam.py (+1)
- `modules/gsd_x/goal/workspace.py` Workspace Capsule: the exact relevant state of a working tree, portable (UWCP S2). | defs: CaptureRefused:98, HydrateError:102, MissingPrerequisite:110, content_hits:201, case_collisions:266, conversion_env:281, capture:309, load_manifest:519, hydrate:544, verify:645, capsule_status:721, retain:734 | imported by: tools/test_uwcp_workspace.py
- `modules/gsd_x/heartbeat.py` A record on every judgement, not only on the ones that fire. | defs: read:52, record:60, informative_rate:95 | imported by: modules/cpc_os/__init__.py, modules/cpc_os/snapshot.py, modules/gsd_x/cli.py, modules/sleepless_qa/cli.py, tools/test_gsd_x.py
- `modules/gsd_x/mission/__init__.py` GSD X Mission Intelligence -- the joins, and nothing more. | defs: - | imported by: modules/gsd_x/goal/convergence.py, modules/gsd_x/goal/sweep.py
- `modules/gsd_x/mission/closure.py` Evidence-governed transition, and a closure projection that can say no. | defs: Verdict:36, TransitionResult:58, evaluate_transition:67, satisfy:107, Blindness:134, Closure:178, project_closure:228 | imported by: modules/gsd_x/goal/convergence.py, modules/gsd_x/goal/engine_identity.py, modules/gsd_x/goal/sweep.py, tools/gsd_x_mission.py, tools/test_gsd_x_facts_v2.py, tools/test_gsd_x_goal_chaos.py, tools/test_gsd_x_goal_convergence.py, tools/test_gsd_x_goal_judge.py (+3)
- `modules/gsd_x/mission/contract.py` Mission Contract v1 -- a PROJECTION over owners that already exist. | defs: Field:47, MissionContract:115, project:141 | imported by: modules/gsd_x/goal/bind_mission.py, modules/gsd_x/goal/brief.py, modules/gsd_x/goal/convergence.py, modules/gsd_x/goal/epoch.py, modules/gsd_x/goal/evidence.py, modules/gsd_x/goal/intervention.py, modules/gsd_x/goal/judge.py, modules/gsd_x/goal/reconcile.py (+21)
- `modules/gsd_x/mission/coverage.py` Required-input closure over a structured facts document (GSDX-M06, F7). | defs: operator_gating:75, dead_operators:80, required_facts:90, unproduced:106, unproduced_for:118 | imported by: modules/session_delta/delta.py, tools/gsd_x_mission.py, tools/test_gsd_x_facts_v2.py, tools/test_uceimr_residues.py
- `modules/gsd_x/mission/obligation.py` Derived obligations: requirements the human did not state that follow from | defs: Obligation:47, Fact:135, extract_facts:232, op_irreversibility_consequence:259, op_absent_signal_consequence:286, op_failure_consequence:318, op_unfalsifiable_parity_consequence:347, derive_from_facts:454, derive:469, judge:478, invalidate_if_parent_gone:511 | imported by: modules/gsd_x/mission/closure.py, modules/gsd_x/mission/coverage.py, modules/gsd_x/mission/store.py, modules/gsd_x/mission/structured_facts.py, tools/gsd_x_mission.py, tools/test_gsd_x_facts_v2.py, tools/test_gsd_x_mission.py, tools/test_gsd_x_parity_obligation.py (+1)
- `modules/gsd_x/mission/store.py` Durable storage for derived obligations -- one mission, one file. | defs: store_path:26, load:30, GoalBound:55, binding_path:59, bound_goal:63, bind:78, refuse_if_bound:85, save:92 | imported by: modules/knowledge_acquisition/cli.py, modules/knowledge_acquisition/runner.py, modules/lease/__init__.py, tests/test_knowledge_acquisition_assessment_store.py, tests/test_knowledge_acquisition_hold_provenance.py, tests/test_knowledge_acquisition_store.py, tools/gsd_x_goal.py, tools/gsd_x_mission.py (+4)
- `modules/gsd_x/mission/structured_facts.py` Structured reality input -- the second fact source (GSDX-M04, GSDX-M05). | defs: StructuredFactsError:72, FactNote:77, FactSet:90, facts_path:107, source_of:111, load_document:166, load:258, dump:271, fingerprint:311, freshness_rows:334, freshness_verdict:369, reconcile_document:390 | imported by: tools/gsd_x_mission.py, tools/test_gsd_x_facts_v2.py, tools/test_gsd_x_structured_facts.py
- `modules/gsd_x/tier.py` The ExecutionOS Lite tier, measured instead of self-assessed. | defs: TierVerdict:66, classify:83, observable_evidence:222, classify_prompt:276 | imported by: tools/bench_gsd_x_reconstruction.py, tools/test_gsd_x_reconstruction.py, tools/test_tower_o4.py

## Concepts (top candidate owners by keyword co-occurrence; a candidate is not an owner)

### C-01 PRIMARY SOURCE / MISSION BASIS  [kw: primary, source, mission, basis]
- `modules/knowledge_acquisition/store.py:51` (4kw, 39 hits) corpus_id      TEXT PRIMARY KEY,
- `modules/governance-overlay/mistakes-registry.md:336` (4kw, 30 hits) 1. LLM treats fallbacks as "graceful degradation" without modeling the quality delta between primary and fallback paths
- `tools/gsd_epoch.py:604` (3kw, 100 hits) def on_session_start(rec: dict, session_id: str, source: str, session_cwd: str | None,
- `tools/test_incremental_cognition_program.py:25` (3kw, 98 hits) primary file (terminal_evidence true) supports a terminal; a second_workload file supports one
- `tools/test_floor_regression_gate.py:495` (3kw, 79 hits) """The component source a hook command is filed under: the contract key, with the first script file name of the command."""
- `tools/rollover.py:44` (3kw, 67 hits) # gate, claim, refresh, exam and certify as v1 -- only the identity and the sources differ. Keyed

### C-02 EXECUTION MODE DECISION  [kw: execution, mode, decision]
- `tools/test_decision_review.py:254` (3kw, 74 hits) # V-DRK-ATTRIBUTION -- reasoning/execution/luck/context separated
- `hooks/hook-dispatcher.js:292` (3kw, 60 hits) // FD-07 Fable Learning Flywheel (SCS C82 EXECUTION-mode): at a FRONTIER
- `modules/zero-crash/hooks/context-watchdog.py:1478` (3kw, 49 hits) "-ExecutionPolicy", "Bypass", "-File", str(daemon)],
- `modules/cognitive_os/router.py:13` (3kw, 41 hits) 5. Sonnet       -- standard reasoning/execution (the MICRO/MACRO default).
- `modules/sdd_os/pre_exec_gate.py:2` (3kw, 34 hits) """SDD-OS pre-execution gate -- closes RC-3 (BL-SDD-ACT-001).
- `tools/kclaude.ps1:51` (3kw, 34 hits) # --- FD-00/FD-07 frontier-session marker (SCS C82 EXECUTION-mode) -------------

### C-03 PLAN EXPERIENCE  [kw: plan, experience]
- `modules/deep-research/test_research_engines.py:181` (2kw, 10 hits) "about pricing plans.",
- `modules/cdio/motion_patterns.py:59` (2kw, 9 hits) "pricing": {"pricing", "plans"},
- `modules/deep-research/research_engines.py:341` (2kw, 6 hits) "our agency", "our clients", "pricing plans", "talk to sales",
- `modules/governance-overlay/pre-task.md:121` (2kw, 6 hits) 3. Present plan, wait for approval
- `tools/test_hook_boundary.py:424` (2kw, 6 hits) proving anything. A planted registry keeps working after the estate is clean and
- `governance/DEPLOY_GOVERNANCE.md:12` (2kw, 3 hits) the portfolio's first commit staged a third party's phone number in a planning doc.)

### C-04 FIRST ACTION — FULL REALITY SCAN  [kw: first, action, full, reality]
- `modules/zero-crash/hooks/context-watchdog.py:48` (4kw, 54 hits) # EVERY crossing, not the first. A reading this far below the advisory
- `modules/duplicate_to_advantage/d2a_engine.py:296` (4kw, 32 hits) # The first cut of this fix skipped directories that already had a curated ID, to
- `modules/deep-research/deep_research.py:370` (4kw, 30 hits) treats NoSearchAvailable on the FIRST query as a CEILING.md write +
- `vault/specs/mission-capsule-rollover.md:28` (4kw, 27 hits) - **D3 answer leak.** `resume` prints goal, branch, HEAD and the first obligation, then asks for them.
- `tools/dataset_enricher.py:17` (4kw, 23 hits) first-paragraph synthesis plus categorization metadata. Transversal
- `modules/governance-overlay/mistakes-registry.md:66` (4kw, 21 hits) - **Detection:** Edited a file without reading it first; called a function assuming its signature

### C-05 MANDATORY ITERATION STANDARD  [kw: mandatory, iteration, standard]
- `modules/governance-overlay/mistakes-registry.md:89` (3kw, 11 hits) - **Prevention (MANDATORY for every module):**
- `modules/governance-overlay/pre-output.md:43` (3kw, 11 hits) ## DNA-400 Gate (Ley de Supremacía Empírica — MANDATORY for complex logic)
- `modules/oracle/ovo-protocol.md:98` (3kw, 3 hits) The probes are advisory at LIGHT/STANDARD/DEEP tiers and **mandatory at FORENSIC tier**. Each probe emits one of three states:
- `tools/jit_skill_loader.py:934` (3kw, 3 hits) "problem-domain; the full procedure is mandatory before solution "
- `modules/cognitive_os/loop_budget.py:45` (2kw, 27 hits) """The seven-part loop budget (CO-09 I.2). max_iterations is mandatory; a
- `modules/gsd_x/tier.py:100` (2kw, 11 hits) mandatory = [r for r in applies if r.verdict is Verdict.MANDATORY]

### C-06 DELEGATION PRINCIPLE  [kw: delegation, principle]
- NO CANDIDATE (search found nothing: NEW, DATASET ONLY, or vocabulary differs -- verify)

### C-07 OPPORTUNITY DELEGATION PRINCIPLE  [kw: opportunity, delegation, principle]
- NO CANDIDATE (search found nothing: NEW, DATASET ONLY, or vocabulary differs -- verify)

### C-08 MISSION NORTH STAR  [kw: mission, north, star]
- `tools/gsd_mission.py:2` (2kw, 530 hits) """gsd_mission -- the mission outlives the session (spec vault/specs/mission-continuity.md).
- `tools/fixtures/gsd_mission_legacy_golden.json:4` (2kw, 160 hits) "gsd_mission_sha256": "d53245689ce9a87ae05039c9b22d79ce6765446f0f7a2fa3e7671344fc9531e8",
- `tools/test_gsd_mission.py:2` (2kw, 149 hits) """V-MC-* gates for tools/gsd_mission.py (spec vault/specs/mission-continuity.md).
- `tools/test_floor_regression_gate.py:911` (2kw, 129 hits) "command_permissions": {"allowedTools": ["Bash"]},
- `tools/gsd_epoch.py:4` (2kw, 121 hits) A mission (tools/gsd_mission.py) is carried by `claude --bg` workers. Until 2026-09-28 every turn a
- `hooks/hook-dispatcher.js:62` (2kw, 103 hits) // Mission hand-off wall, judged MID-TURN (spec vault/specs/mission-continuity.md).

### C-09 ARCHITECTURAL TARGET — SEMANTIC REALITY COMPILATION  [kw: architectural, target, semantic, reality]
- `tools/verify_spp.py:804` (4kw, 6 hits) [PY, str(PP / "tools" / "test_architectural_truth.py")],
- `vault/specs/arch-decision-skill.md:9` (4kw, 5 hits) Before the agent (or the Owner) commits to an architectural decision,
- `modules/cdio/scorer.py:6` (3kw, 21 hits) conformance, type-level count, tap-target size, line measure). The score is a
- `tools/_osa_standards_append.py:214` (3kw, 17 hits) def cherry_pick_copy(source: Path, target: Path) -> bool:
- `modules/duplicate_to_advantage/d2a_engine.py:10` (3kw, 14 hits) D2A-1 Duplicate Detection Core   -- 3-axis (semantic/functional/architectural) overlap of
- `hooks/session_start_hub.js:6` (3kw, 13 hits) * Architectural rationale (T-NODE-COLD-001):

### C-10 SEMANTIC CONSERVATION LAW  [kw: semantic, conservation]
- NO CANDIDATE (search found nothing: NEW, DATASET ONLY, or vocabulary differs -- verify)

### C-11 UNIVERSAL SEMANTIC CONSERVATION FAMILIES  [kw: universal, semantic, conservation, families]
- `modules/duplicate_to_advantage/d2a_engine.py:404` (3kw, 30 hits) #   SRIF -> sleepless_qa (Universal Empirical Verification Pipeline)
- `tools/test_dataset_first_protocol.py:169` (3kw, 5 hits) "sealed universal standard that will outlive every contributor, is irreversible "
- `modules/deep-research/research_engines.py:299` (2kw, 12 hits) "biorxiv.org", "semanticscholar.org", "researchgate.net",
- `tools/test_duplicate_to_advantage.py:139` (2kw, 10 hits) # V-D2A-DETECTION-SEMANTIC -- duplicate detected > 80%.
- `modules/cdio/scorer.py:297` (2kw, 9 hits) The VQ-4 semantic-colour exemption is for a *hue* being reused as a state signal
- `modules/universal-meta-systems/runtime/corpus_parser.py:67` (2kw, 7 hits) _DEFAULT_CORPUS = Path(r"C:\Users\User\Apps\universal-meta-systems-corpus")

### C-12 PURPOSE-FIRST REASONING  [kw: purpose-first, reasoning]
- NO CANDIDATE (search found nothing: NEW, DATASET ONLY, or vocabulary differs -- verify)

### C-13 RELATIONSHIP COMPLETENESS  [kw: relationship, completeness]
- NO CANDIDATE (search found nothing: NEW, DATASET ONLY, or vocabulary differs -- verify)

### C-14 TEMPORARY STATE LAW  [kw: temporary, state]
- `tools/test_parallel_mesh.py:66` (2kw, 56 hits) with tempfile.TemporaryDirectory() as td:
- `tools/test_session_resilience_build.py:5` (2kw, 56 hits) Hermetic by construction: every persistence path is a fresh TemporaryDirectory,
- `tools/test_monitoring.py:5` (2kw, 47 hits) self-contained in a tempfile.TemporaryDirectory(); none of them hit
- `tools/test_decision_review.py:574` (2kw, 42 hits) with tempfile.TemporaryDirectory() as td:
- `tools/test_auto_reset.py:76` (2kw, 34 hits) with tempfile.TemporaryDirectory() as td:
- `tools/test_strategic_gaps.py:49` (2kw, 33 hits) with tempfile.TemporaryDirectory() as td:

### C-15 OWNERSHIP CLOSURE  [kw: ownership, closure]
- `modules/architecture_horizon/horizon.py:57` (2kw, 14 hits) """Ownership granularity is the package directory: that is what a person owns,
- `vault/specs/external-capability-assimilation.md:66` (2kw, 6 hits) 18. Plan Graph → CONNECT to UWCP: write-ownership overlap + cycle/depth validation via bridge in UWCP plan intake. Verify: UWCP tests + overlapping-write plan r
- `vault/specs/gsd-x-n4.RESUMPTION.md:34` (2kw, 6 hits) names were reused; the ownership was not.
- `tools/verify_spp.py:818` (2kw, 4 hits) # The ownership audit was itself unwired -- an audit of who owns what,
- `vault/specs/gsd-x-n5.RESUMPTION.md:46` (2kw, 4 hits) population. Field names were reused; ownership was not.
- `commands/architecture-horizon.md:7` (2kw, 3 hits) UPAC residue R2 (`vault/audits/upac/SYSTEM_OWNERSHIP_OVERLAP_MAP.md`). A sweep of all

### C-16 PROJECTION CLOSURE  [kw: projection, closure]
- `modules/gsd_x/mission/closure.py:2` (2kw, 17 hits) """Evidence-governed transition, and a closure projection that can say no.
- `modules/gsd_x/goal/reconcile.py:5` (2kw, 15 hits) FUNCTION of durable state -- events, projections, observations, the clock -- and
- `modules/gsd_x/goal/convergence.py:208` (2kw, 11 hits) `obligation.dispositioned` has been read by the projection since C2 and
- `tools/test_gsd_x_facts_v2_mutation.py:44` (2kw, 7 hits) # The closure is never told: the projection falls back to UNMEASURED.
- `vault/specs/gsd-x-n8.RESUMPTION.md:46` (2kw, 7 hits) `error`, which `shell-command-projection.cjs:588-593` deliberately preserves.
- `vault/specs/agent-capability-virtualization.md:92` (2kw, 4 hits) | 2 | HIGH | agent_pack_sync is a copier, not a generator | New projection writer; pack_sync untouched, only distributes generated packs. |

### C-17 EDD CANONICAL RESPONSIBILITY  [kw: canonical, responsibility]
- `tools/usea_ownership_audit.py:144` (2kw, 4 hits) "One canonical architectural authority already exists and it is the "
- `modules/deep-research/deep_research.py:126` (2kw, 3 hits) # decomposer returned an axis outside the canonical set — an unrecognised
- `modules/duplicate_to_advantage/d2a_engine.py:1589` (2kw, 3 hits) desc = "Token Budget Planner"      # the canonical worked example
- `vault/specs/mission-capsule-rollover.md:120` (2kw, 3 hits) | T4 | mutation guard + dispatcher wiring (canonical + live, 2 lines each) | hooks/capsule_mutation_guard.js, hooks/tests/test-capsule-mutation-guard.js, hooks/
- `commands/usea.md:22` (2kw, 2 hits) Check the canonical corpus against its seal.

### C-18 COMPLETION LENSES  [kw: completion, lenses]
- NO CANDIDATE (search found nothing: NEW, DATASET ONLY, or vocabulary differs -- verify)

### C-19 ACTIVE EPISTEMIC CONTROL  [kw: active, epistemic, control]
- `modules/deep-research/research_engines.py:777` (3kw, 31 hits) REJECTED   — the contents actively refute this. Return it anyway when it \
- `tools/test_decision_review.py:469` (3kw, 15 hits) from modules.decision_review.proactive_scanner import scan_repo
- `tools/verify_spp.py:441` (3kw, 9 hits) ("uqf-active",
- `vault/specs/agent-capability-virtualization.md:152` (3kw, 7 hits) | S6 foundry (recorder -> challenger -> active), S7 closure | PLANNED, entry gates below |
- `commands/cpp-deep-research.md:127` (3kw, 6 hits) - **IDLE_PRIORITY_CLASS** on Windows so the agent yields to interactive
- `tools/test_floor_regression_gate.py:1994` (2kw, 41 hits) "607795c4-aa30-4fb8-886c-5b1e24a7a991.jsonl")      # interactive session, finished

### C-20 FOUNDER DECISION QUESTIONS  [kw: founder, decision, questions]
- `modules/deep-research/deep_research.py:1121` (3kw, 28 hits) reader is a founder/operator; a learning carrying a CLI invocation is a
- `modules/deep-research/research_engines.py:679` (3kw, 27 hits) # The old prompt asked for "what a founder should LEARN" and returned prose with
- `modules/deep-research/research_quality.py:23` (3kw, 18 hits) these learnings is a founder/operator, not a data engineer.
- `tools/rollover.py:1175` (3kw, 8 hits) except FileNotFoundError:
- `modules/deep-research/test_research_quality.py:237` (3kw, 6 hits) reader_ok = "founder or operator" in prompt or "founder/operator" in prompt
- `tools/verify_spp.py:285` (3kw, 5 hits) except FileNotFoundError as e:

### C-21 FOUNDER QUESTION COMPRESSION  [kw: founder, question, compression]
- `tools/jit_skill_loader.py:53` (3kw, 3 hits) # ModuleNotFoundError, was swallowed by its fail-open handler, and went
- `tools/test_git_invocation.py:6` (3kw, 3 hits) raises FileNotFoundError -- and in each place it was found, the exception was
- `modules/frontier_intelligence/session_compiler.py:6` (2kw, 79 hits) constraints + unknowns + candidate questions -- and compiles a concrete, ordered,
- `modules/deep-research/deep_research.py:1121` (2kw, 40 hits) reader is a founder/operator; a learning carrying a CLI invocation is a
- `modules/deep-research/research_engines.py:679` (2kw, 31 hits) # The old prompt asked for "what a founder should LEARN" and returned prose with
- `modules/deep-research/research_quality.py:23` (2kw, 30 hits) these learnings is a founder/operator, not a data engineer.

### C-22 INTENT CLOSURE CHECKPOINTS  [kw: intent, closure, checkpoints]
- `modules/gsd_x/mission/obligation.py:3` (2kw, 39 hits) the intent plus the project's own reality.
- `tools/test_gsd_x_mission.py:36` (2kw, 29 hits) "INTENT.txt": "65b00c071929566fc8d00a7b4739b9a4d97403c7",
- `tools/gsd_x_mission.py:27` (2kw, 26 hits) prose adapter over INTENT.txt + README.md otherwise. `derive` reports which.
- `tools/gsd_x_goal.py:4` (2kw, 23 hits) python tools/gsd_x_goal.py declare  --goal <id> --root <repo> --intent "..." \
- `tools/test_gsd_x_facts_v2.py:156` (2kw, 21 hits) def _mission(tmp: Path, doc=None, intent="", reality="") -> Path:
- `tools/test_gsd_x_goal_convergence.py:221` (2kw, 19 hits) s7 = gc.revise(lg7, s7.last_seq + 1, s7.intent, s7.acceptance + ["and it is fast"],

### C-23 ASSUMPTION LIABILITY  [kw: assumption, liability]
- `hooks/windows-bash-bridge-guard.js:69` (2kw, 2 hits) *     answerable with an instrument rather than an assumption.

### C-24 MULTI-REFERENCE INTELLIGENCE  [kw: multi-reference, intelligence]
- NO CANDIDATE (search found nothing: NEW, DATASET ONLY, or vocabulary differs -- verify)

### C-25 REFERENCE MECHANISM EXTRACTION  [kw: reference, mechanism, extraction]
- `modules/gsd_x/mission/obligation.py:221` (3kw, 21 hits) # Enrichment only. A reference that RUNS can be interrogated on inputs
- `modules/deep-research/research_engines.py:381` (3kw, 15 hits) "rfc ", "specification", "reference implementation",
- `commands/cpp-deep-research.md:11` (3kw, 8 hits) algorithm (n8n source workflow is reference material only — see
- `modules/zero-crash/hooks/context-watchdog.py:694` (3kw, 6 hits) non-observation is ledgered once per cycle reference, so a run that never
- `tools/chatgpt_distiller.py:3` (2kw, 28 hits) chatgpt-distiller — Extract vision, decisions, and preferences from ChatGPT exports.
- `modules/deep-research/deep_research.py:5` (2kw, 12 hits) Algorithm reverse-engineered from a community n8n workflow (reference only;

### C-26 REFERENCE FRONTIER  [kw: reference, frontier]
- `tools/test_frontier_intelligence_os.py:373` (2kw, 46 hits) _ok("V-FIOS-LIVE-PATH-WIRED", "dispatcher + kclaude reference the engines")
- `modules/frontier_intelligence/session_compiler.py:16` (2kw, 40 hits) dependence-reducing) is REFERENCED as the ORDER heuristic among admitted
- `tools/jit_skill_loader.py:137` (2kw, 26 hits) # reference pointers). Everything else is explicit negative space
- `modules/liveness/reachability.py:24` (2kw, 14 hits) would call the genuinely-live `power_beacon` an orphan. References are matched as
- `tools/usea_outcome_contrast.py:39` (2kw, 12 hits) are reachable: a known-good reference implementation must PASS and the naive
- `tools/test_duplicate_to_advantage.py:203` (2kw, 9 hits) # V-D2A-NO-DUPLICATE -- registry references real sealed families; doctrine declares

### C-27 EXCELLENCE FRONTIER  [kw: excellence, frontier]
- NO CANDIDATE (search found nothing: NEW, DATASET ONLY, or vocabulary differs -- verify)

### C-28 FOUNDER OPPORTUNITY REVIEW  [kw: founder, opportunity, review]
- `tools/test_decision_review.py:529` (2kw, 43 hits) type="opportunity", description="a dataset is never recalled", repo="pp",
- `tools/normalize_paths.py:401` (2kw, 15 hits) `subprocess.check_output(['git', ...])` with FileNotFoundError
- `tools/_s_plus_plus_plus_lessons_seed.py:28` (2kw, 9 hits) `FileNotFoundError: [WinError 2]` under PowerShell -NonInteractive
- `tools/test_floor_regression_gate.py:1842` (2kw, 9 hits) raise FileNotFoundError(2, "gone")
- `tools/jit_skill_loader.py:53` (2kw, 7 hits) # ModuleNotFoundError, was swallowed by its fail-open handler, and went
- `modules/decision_review/proactive_scanner.py:70` (2kw, 6 hits) type: str          # decision_needed | debt | orphan | opportunity

### C-29 SUPERIORITY CLAIMS REQUIRE PROOF  [kw: superiority, claims, require, proof]
- `modules/fable_distillation/fd_04_acceleration.py:105` (3kw, 32 hits) return {"verdict": UNMEASURABLE, "repeated_claims": 0,
- `modules/fable_distillation/fd_04_prover.py:175` (3kw, 24 hits) "deposited claims"}
- `tools/test_assimilation_manifest.py:71` (3kw, 22 hits) # A proof that exits 0 says the code works WHEN INVOKED; LIVE also claims something
- `modules/deep-research/research_engines.py:38` (3kw, 20 hits) for internally-deposited claims. That ladder measures a DIFFERENT axis (does
- `modules/gsd_x/mission/closure.py:126` (3kw, 19 hits) # nothing unknown are different claims about the world, and collapsing them
- `modules/capability_runtime/agent_bundle.py:14` (3kw, 16 hits) INVALID    malformed, or claims evidence it does not cite, or from another spec

### C-30 EXPECTED REALITY VERSUS OBSERVED REALITY  [kw: expected, reality, observed, reality]
- `modules/gsd_x/mission/obligation.py:247` (3kw, 56 hits) # the text of the obligation it is expected to produce, because an operator that
- `tools/rollover.py:992` (3kw, 48 hits) wrong.append({"key": item["key"], "expected": item["a"] or "UNREADABLE NOW", "given": answers.get(item["key"])})
- `tools/test_gsd_x_mission.py:41` (3kw, 48 hits) # The holdout's expected material obligations, by the operator that should find
- `tools/test_gsd_x_facts_v2.py:221` (3kw, 40 hits) f"expected {{{ORPHAN!r}}}, got {sorted(ob.ORPHAN_FACT_NAMES)}")
- `tools/test_daif_session_compiler.py:125` (3kw, 31 hits) f"expected [] on all three, got empty={len(a)} corrupt={len(b)} missing={len(c)}")
- `tools/test_osr.py:135` (3kw, 26 hits) expected = {"state_with_entry_and_no_exit", "failure_mode_with_no_recovery_path"}

### C-31 SEMANTIC RESIDUALS  [kw: semantic, residuals]
- `hooks/session_start_hub.js:25` (2kw, 5 hits) *      semantics to the standalone hooks/jit_warm.js.

### C-32 CONTINUOUS BUG → CAPABILITY ASCENSION  [kw: continuous, capability, ascension]
- `modules/setup_os/graph.py:326` (2kw, 14 hits) ("continuous_integration", "ci_cd"),
- `modules/governance-overlay/mistakes-registry.md:361` (2kw, 4 hits) - **Example (Java/Minecraft):** `block.setType()` called 200x per server tick on the main thread — each call triggers lighting update + chunk dirty flag. 384k b
- `vault/specs/gsd-x-n8.RESUMPTION.md:307` (2kw, 4 hits) changed name: the UKDL's continuous writer is the CEPS auto-appender (GSDX-M09), so
- `tools/design_index.py:177` (2kw, 2 hits) ("Infinite Scroll", "continuous feed",
- `vault/specs/unhealed-knowledge-paths.md:30` (2kw, 2 hits) The estate's real constraint is not capability. `vault/plans/STOP_LEDGER.md`

### C-33 SEMANTIC INVALIDATION EVENT  [kw: semantic, invalidation, event]
- `tools/jit_skill_loader.py:958` (3kw, 13 hits) # genuine semantic overlap, mutex stays.
- `hooks/hook-dispatcher.js:519` (2kw, 128 hits) { exe: NODE_EXE, script: './gatekeeper-semantic.js', timeoutMs: 3000 },
- `tools/ceps.py:18` (2kw, 79 hits) Fail-open semantics (Ley 24): any internal error is logged to
- `modules/governance-overlay/mistakes-registry.md:320` (2kw, 70 hits) 2. File-based databases (DuckDB, SQLite) have single-writer semantics but this isn't enforced at connection time by default
- `tools/gsd_epoch.py:17` (2kw, 36 hits) * continue_worker -- the same-session continuation effect. Host semantics verified 2026-09-28
- `tools/ceps_backfill_audit.py:2` (2kw, 25 hits) """Classify historical CEPS events against the semantic admission rules.

### C-34 DUAL REPAIR OBLIGATION  [kw: dual, repair, obligation]
- `tools/usea_ownership_audit.py:82` (3kw, 3 hits) ["modules/duplicate_to_advantage", "modules/hard_rules/residual.py"]),
- `modules/gsd_x/goal/convergence.py:320` (2kw, 59 hits) residual_risk: list = field(default_factory=list)
- `modules/gsd_x/mission/closure.py:184` (2kw, 32 hits) residual_risk: list[str] = field(default_factory=list)
- `tools/gsd_x_mission.py:347` (2kw, 27 hits) # measurement that failed and a question nobody asked are repaired by
- `modules/hard_rules/residual.py:2` (2kw, 26 hits) """residual.py -- the residual-move compiler (PR-PROHIBITIONS-DO-NOT-CONFLICT-001).
- `tools/test_gsd_x_facts_v2.py:574` (2kw, 21 hits) # different repairs. The scope is the gating set and nothing wider: the

### C-35 EARLIEST PREVENTABLE POINT  [kw: earliest, preventable, point]
- `modules/surface_architecture/boundaries.py:10` (2kw, 14 hits) product whose earliest justified position is LATER than its latest safe one has a
- `modules/cdicf/installer.js:377` (2kw, 11 hits) * rename is an install that needs recovery for a preventable reason.
- `tools/test_ceps_admission.py:17` (2kw, 7 hits) Two layers are asserted because the defect has two earliest-prevention
- `modules/agent-lightning/query_lightning.py:89` (2kw, 6 hits) print(f"Date range:    {data.get('earliest', '?')} → {data.get('latest', '?')}")
- `tools/test_osr.py:273` (2kw, 3 hits) _ok("V-OSR-ALIGN-T1", "earliest INTERNAL divergence located at index 1")
- `tools/test_surface_architecture.py:157` (2kw, 3 hits) """Earliest-justified after latest-safe has no valid position. Say so."""

### C-36 CAPABILITY LEARNING OVER BUG MEMORIZATION  [kw: capability, learning, over, memorization]
- `modules/deep-research/deep_research.py:136` (3kw, 172 hits) # capability, evidence, claimed vs final epistemic level, source quality.
- `modules/duplicate_to_advantage/d2a_engine.py:6` (3kw, 137 hits) structured search for the best adjacent capability that does NOT yet exist.
- `modules/deep-research/research_engines.py:25` (3kw, 123 hits) E3 REALITY        — every learning carries the CAPABILITY it confers plus an
- `modules/deep-research/test_research_engines.py:46` (3kw, 69 hits) build_capability_learnings_prompt,
- `hooks/hook-dispatcher.js:403` (3kw, 55 hits) // Carrier least privilege (agent-capability-virtualization S1, 2026-09-30). A carrier's
- `modules/deep-research/research_quality.py:222` (3kw, 49 hits) # SUPERSEDED by research_engines.CAPABILITY_LEARNINGS_PROMPT (v0.3.0).

### C-37 SIBLING EXPLOSION SEARCH  [kw: sibling, explosion, search]
- `modules/deep-research/deep_research.py:691` (2kw, 127 hits) #      subprocess to avoid recursion-explosions.
- `modules/deep-research/research_engines.py:40` (2kw, 25 hits) are siblings, not duplicates. This one measures: what kind of evidence, from
- `hooks/session_start_hub.js:48` (2kw, 22 hits) * ASCII-only constraint inherited from the .ps1 sibling (Owner-side
- `modules/duplicate_to_advantage/d2a_engine.py:164` (2kw, 22 hits) # family. "Compound effect between sibling datasets" is its own subject matter; the
- `tools/jit_skill_loader.py:94` (2kw, 16 hits) # Sibling of the 2026-06-08 RAM regression above: that fix closed the
- `tools/design_index.py:398` (2kw, 13 hits) """Own file, never the vault DB. --db > env > sibling of the vault DB."""

### C-38 FORWARD IMMUNITY PROPAGATION  [kw: forward, immunity, propagation]
- `tools/ceps.py:5` (2kw, 4 hits) M10 (forward propagation), and M11 (distributor). Deviation from the
- `tools/test_trace_context.py:57` (2kw, 3 hits) check("V-TRACE-FORWARD-COMPAT", future is not None,
- `modules/bug-hunter/agent.json:56` (2kw, 2 hits) "primary_check_pattern": "grep delta for (write|dump|encode|serialize|insert|persist) calls; for each, walk forward 5 lines for (fsync|flush|sync|force|commit|r

### C-39 SELF-EVOLUTION DEBT  [kw: self-evolution, debt]
- NO CANDIDATE (search found nothing: NEW, DATASET ONLY, or vocabulary differs -- verify)

### C-40 CAPABILITY REVISIONING / NO SELF-CORRUPTION  [kw: capability, revisioning, self-corruption]
- NO CANDIDATE (search found nothing: NEW, DATASET ONLY, or vocabulary differs -- verify)

### C-41 FACTORY REGRESSION  [kw: factory, regression]
- `modules/sqi/baseline_guardian.py:84` (2kw, 25 hits) lost_identities: list[str] = field(default_factory=list)
- `modules/duplicate_to_advantage/d2a_engine.py:616` (2kw, 17 hits) secondary_parents: list = field(default_factory=list)
- `modules/gsd_x/goal/convergence.py:97` (2kw, 12 hits) planes: dict = field(default_factory=dict)          # plane -> (state, reason)
- `modules/tower/ratchet.py:105` (2kw, 10 hits) generations: list = field(default_factory=list)
- `modules/cdio/scorer.py:89` (2kw, 8 hits) critical: list = field(default_factory=list)
- `modules/sqi/ratchet.py:111` (2kw, 7 hits) reasons: list[str] = field(default_factory=list)

### C-42 NOVEL HOLDOUTS  [kw: novel, holdouts]
- NO CANDIDATE (search found nothing: NEW, DATASET ONLY, or vocabulary differs -- verify)

### C-43 PREVENTION DEPTH RATCHET  [kw: prevention, depth, ratchet]
- `tools/verify_spp.py:324` (3kw, 9 hits) from modules.cascade_prevention.verification_state import (
- `modules/liveness/reachability.py:208` (2kw, 8 hits) # `modules.pkg.mod`, `modules/pkg/mod`, `modules\pkg\mod` -- at ARBITRARY depth. An
- `tools/jit_skill_loader.py:871` (2kw, 6 hits) "prevention, governance overlay and the /cpp-* command set. Full "
- `tools/seed_capability_contracts.py:41` (2kw, 6 hits) owner="modules/error_prevention/premise_verifier.py",
- `tools/usea_ownership_audit.py:54` (2kw, 6 hits) ["modules/sdd_os", "modules/error_prevention/premise_verifier.py",
- `hooks/scaffold-auditor.js:15` (2kw, 5 hits) * vault/standards/blocked-delivery-prevention.md.

### C-44 EXPECTATION ESCAPE INCIDENTS  [kw: expectation, escape, incidents]
- `modules/hard_rules/residual.py:318` (2kw, 4 hits) "matches_expectation": (exp is None or out["verdict"] == exp)}
- `hooks/agent-solo-guard.js:436` (2kw, 2 hits) // old form would have let an error escape as an unhandled rejection -- and a
- `modules/spec_gate/gate.py:216` (2kw, 2 hits) if re.search(r"\b" + re.escape(t) + r"(?:s|es)?\b", text):
- `tools/family_scan.py:280` (2kw, 2 hits) print("  PREDECLARED EXPECTATION NOT MET.")

### C-45 BLIND COUNTERFACTUAL REPLAY  [kw: blind, counterfactual, replay]
- `vault/specs/agent-capability-virtualization.md:204` (3kw, 4 hits) STREAM_BLIND / BLOCKED (settings, guard file or node missing). Runner pins and records the CLI
- `tools/test_kme_replay.py:311` (2kw, 32 hits) # = 2,010, wholly cache-read (cache_read 53,010) -> 201.0. A floor-blind model avoids the whole cut (52,020) on calls
- `modules/rule_compiler/counterfactual.py:10` (2kw, 23 hits) one it kept was effect measurement -- the counterfactual half was never built, so
- `tools/test_spawn_policy_v2.py:153` (2kw, 14 hits) ok("V-SPV2-EQ-FUTURE-BLIND", eq.active(h, T0 + 11.0 * 3600, "tuJ1") == 0,
- `modules/rule_compiler/effect_harness.py:151` (2kw, 13 hits) def _counterfactual_ids() -> set:
- `modules/duplicate_to_advantage/d2a_engine.py:152` (2kw, 12 hits) "kw": ("observatory", "coverage", "blind", "spot", "hotspot", "benchmark",

### C-46 SKYPARTY FORENSIC GOLD SET  [kw: skyparty, forensic, gold]
- NO CANDIDATE (search found nothing: NEW, DATASET ONLY, or vocabulary differs -- verify)

### C-47 FOUNDER-FIRST SURPRISE  [kw: founder-first, surprise]
- NO CANDIDATE (search found nothing: NEW, DATASET ONLY, or vocabulary differs -- verify)

### C-48 DECISION FRONTIER  [kw: decision, frontier]
- `tools/test_decision_review.py:1` (2kw, 69 hits) """test_decision_review.py -- DRK done-gate (V-DRK-* gates + FASE-5 scenarios).
- `hooks/hook-dispatcher.js:27` (2kw, 50 hits) *   - decision: "deny" wins over "allow" (most restrictive).
- `tools/test_frontier_intelligence_os.py:57` (2kw, 45 hits) class _FakeDecision:
- `modules/fable_distillation/fd_00_gate.py:23` (2kw, 27 hits) needs the coarse decision (the prompt's H1 contract).
- `modules/decision_review/proactive_scanner.py:3` (2kw, 25 hits) The reactive kernel answers when a decision is brought to it. Most of a stack's
- `tools/kclaude.ps1:86` (2kw, 24 hits) # --- helper: fast (launch-critical) prelaunch decision, or $null -------------

### C-49 REFERENCE CHALLENGE CONTRACT  [kw: reference, challenge, contract]
- `vault/specs/agent-capability-virtualization.md:234` (3kw, 15 hits) UBC = no module found, CBR family injection is the canonical equivalent. FIOS: reference only.
- `tools/test_floor_regression_gate.py:332` (2kw, 183 hits) # (a) write the reference
- `tools/test_experience_contract.py:5` (2kw, 48 hits) only ever been seen asking for MORE feedback is a preference with a schema, so this
- `tools/jit_skill_loader.py:137` (2kw, 39 hits) # reference pointers). Everything else is explicit negative space
- `modules/cdio/scorer.py:326` (2kw, 31 hits) # preference, not a gate. These four checks make it refusable.
- `tools/test_gsd_x_reconstruction.py:12` (2kw, 23 hits) working reference, a candidate, and a fidelity requirement should raise its own

### C-50 EXCELLENCE / FRONTIER ADVANCEMENT  [kw: excellence, frontier, advancement]
- NO CANDIDATE (search found nothing: NEW, DATASET ONLY, or vocabulary differs -- verify)

### C-51 EXPECTATION CLOSURE  [kw: expectation, closure]
- `modules/osr/align.py:5` (2kw, 2 hits) one run against recorded expectations and emits MATCH / DIFF / SHIM_ERROR /

### C-52 PROOF COMPILATION  [kw: proof, compilation]
- `modules/capability_runtime/agent_bundle.py:2` (2kw, 5 hits) """agent_bundle.py -- validate and persist a specialist's proof bundle.
- `commands/prd-tier2.md:55` (2kw, 2 hits) - Proof of real behavior (not just "compiles"): <...>
- `modules/governance-overlay/mistakes-registry.md:495` (2kw, 2 hits) 1. Ley DNA-400 (Supremacía Empírica): complex logic must be validated by sandbox execution or synthetic test before delivery. Model reasoning is a vector of err
- `modules/universal-meta-systems/SKILL.md:41` (2kw, 2 hits) | FORENSIC | integrity / universality audit | + `UNIVERSALITY_PROOF.md` + `DONE_GATE.md` + `META_SYSTEM_REGISTRY.md` |
- `tools/test_agent_bundle.py:31` (2kw, 2 hits) b = {"bundle": "proof-bundle/v1", "spec": f"{spec.id}@{spec.contract.version}",

### C-53 EVIDENCE AUTHORITY  [kw: evidence, authority]
- `tools/test_decision_review.py:20` (2kw, 61 hits) DecisionObject, DecisionRecord, Evidence, EvidenceType, Reversibility,
- `tools/gsd_mission.py:20` (2kw, 41 hits) * liveness is three-valued plus BLOCKED. ``DEAD`` needs positive evidence
- `modules/decision_review/decision_kernel.py:4` (2kw, 38 hits) verdict: scope-test -> instantiate -> classify -> route -> evidence/burden ->
- `modules/gsd_x/mission/obligation.py:12` (2kw, 33 hits) `authority` and `evidence` are DAIF's field names with DAIF's meanings
- `tools/test_cognitive_economy_program.py:9` (2kw, 32 hits) A-T must be in a terminal state, each terminal backed by the evidence ITS KIND needs,
- `modules/duplicate_to_advantage/d2a_engine.py:195` (2kw, 27 hits) "DRK-03": {"name": "Evidence Burden & Confidence",

### C-54 PRODUCTION REALITY GATE  [kw: production, reality, gate]
- `tools/test_duplicate_to_advantage.py:533` (3kw, 84 hits) "production reality. Design the intent compiler, the architecture synthesis "
- `tools/test_gsd_x_goal_gate_class.py:10` (3kw, 78 hits) have satisfied a production-reality claim with a green that meant nothing.
- `tools/test_gsd_x_goal_mutation.py:223` (3kw, 59 hits) BRIEF, '    a("- You may NOT write to any production system, deploy, '
- `tools/verify_spp.py:690` (3kw, 59 hits) # was wired canonically and did not run in production. A test that
- `modules/gsd_x/goal/convergence.py:87` (3kw, 55 hits) # unreachable and a unit test could prove a production claim. Measured
- `tools/test_gsd_x_facts_v2.py:441` (3kw, 44 hits) #     demanding its remaining gating facts would be production nobody

### C-55 REALITY CONTRACT  [kw: reality, contract]
- `modules/cdio/scorer.py:16` (2kw, 30 hits) dropped (CDIO-00 reality contract).
- `tools/seed_capability_contracts.py:202` (2kw, 29 hits) retirement_condition="never -- the Reality Contract depends on it",
- `modules/gsd_x/mission/obligation.py:3` (2kw, 27 hits) the intent plus the project's own reality.
- `tools/test_gsd_x_goal_gate_class.py:5` (2kw, 27 hits) `{"class": "in_game" if o.plane == cv.REALITY else "unit"}`, deriving the class
- `tools/test_gsd_x_mission.py:7` (2kw, 24 hits) on a reality that supports nothing, is the evidence that these are rules rather
- `tools/test_capability_runtime.py:99` (2kw, 23 hits) ARCH = _c(id="arch_truth", name="Architectural Reality", owner="setup_os",

### C-56 CROSS-DOMAIN TRANSFER  [kw: cross-domain, transfer]
- `modules/deep-research/test_research_quality.py:131` (2kw, 5 hits) "Cross-domain metrics need identity mapping (customer_id↔user_id) "

### C-57 EDD BENCHMARK  [kw: benchmark]
- `modules/session_resilience/acceptance.py:15` (1kw, 15 hits) 6. Benchmark                 -- baseline expectations (time, fidelity)
- `tools/bench_all.py:1` (1kw, 15 hits) """PP Benchmark Suite -- tools/bench_all.py
- `tools/rtk_corpus.py:2` (1kw, 11 hits) """rtk_corpus.py — build a deterministic, frequency-weighted RTK benchmark
- `tools/verify_bench_all.py:1` (1kw, 10 hits) """verify_bench_all.py -- verify_spp BENCHMARKS_OK probe.
- `modules/sqi/ratchet.py:22` (1kw, 9 hits) saturation there and proposes a harder bar for a benchmark whose current bar is met by
- `tools/run_all_benchmarks.py:1` (1kw, 9 hits) """run_all_benchmarks.py -- one-shot orchestrator for the PP Benchmark Audit.

### C-58 NEGATIVE CONTROLS  [kw: negative, controls]
- `tools/usea_outcome_contrast.py:100` (2kw, 14 hits) # gives -signal; Windows delivers a teardown as a negative int or a 0xCxxxxxxx
- `modules/fable_distillation/fd_04_contrast.py:23` (2kw, 13 hits) an empty answer MUST score FAILED (negative -- else the rubric is vacuous). A run
- `tools/test_kme_replay.py:430` (2kw, 11 hits) def g_rereads_negative():
- `tools/test_conhost_hook_leak.py:64` (2kw, 7 hits) def test_negative_controls() -> None:
- `vault/specs/agent-capability-virtualization.md:2` (2kw, 6 hits) covers: [agent-virtualization, agent-spec, agent-estate-audit, carrier-agents, agent-resolver, proof-bundle, role-paging, agent-foundry, agent-discovery-cost, a
- `hooks/closer-guard.js:92` (2kw, 5 hits) // class's own negative control, which is the argument for shipping one.

### C-59 MUTATE EDD ITSELF  [kw: mutate, itself]
- `tools/test_hook_registration_integrity.py:152` (2kw, 9 hits) def mutate(d: dict, fn) -> dict:
- `hooks/closer-guard.js:244` (2kw, 8 hits) // it in one run ("could not find the D6c structural pattern to mutate"), which
- `tools/rollover.py:873` (2kw, 7 hits) and the guard (which reads any certified_at as certified) let the new worker mutate (I1).
- `modules/governance-overlay/mistakes-registry.md:16` (2kw, 6 hits) - **Detection:** State is mutated but no `.save()`, `.update()`, or `.insert()` in the path
- `tools/test_gsd_x_manifest_reachability_mutation.py:12` (2kw, 5 hits) A green control (the unmutated manifest, through the same override path) runs
- `tools/test_kme_pillars.py:2721` (2kw, 5 hits) """Control first (all in-process gates green), each mutant applied and restored, then an unmutated rerun."""

### C-60 CONSTITUTIVE BASELINE RATCHET  [kw: constitutive, baseline, ratchet]
- `modules/tower/ratchet.py:1` (3kw, 12 hits) """Anti-downgrade for constitutive baselines: changing a rule is allowed only on the record.
- `tools/test_tower_ratchet.py:1` (3kw, 11 hits) """V-TRAT-* -- a constitutive rule can be weakened only on the record.
- `modules/tower/baselines.py:1` (3kw, 8 hits) """Constitutive baseline generations per system family.
- `modules/tower/donegate.py:20` (3kw, 6 hits) constitutive (select.py). Each report and each finding is stamped with
- `tools/test_sqi_ratchet.py:2` (2kw, 71 hits) """V-gate for the SQI Baseline Ratchet (Ley XV) and the rule counterfactual probe.
- `modules/sqi/baseline_guardian.py:1` (2kw, 58 hits) """SQI-02 Part XII — the Baseline Guardian. Protection may not be withdrawn in silence.

### C-61 BASELINE OF COMPLETENESS FOR FUTURE SOFTWARE  [kw: baseline, completeness, future, software]
- `tools/test_usea_cross_domain_benchmark.py:2` (4kw, 5 hits) """Cross-domain benchmark for the USEA completeness baseline (Phase III, section 18-23).
- `tools/verify_spp.py:519` (3kw, 11 hits) ("cross-project-baseline",
- `modules/daif/two_arm_trial.py:11` (3kw, 8 hits) re-reading path and isolating it would test a baseline nobody actually has.
- `tools/test_predictive_governance_gate.py:266` (3kw, 8 hits) # ---------------------------------------------------------- baseline logic
- `tools/test_completion_authority.py:73` (3kw, 7 hits) # tools/test_baseline_inheritance.py; this is only a liveness check that
- `tools/test_gsd_x_facts_v2.py:112` (3kw, 6 hits) variable, so the baseline is full gating coverage and each case moves only

### C-62 UKDL — THREE LEVELS  [kw: ukdl, three, levels]
- `modules/decision_review/epistemic_algebra.py:60` (3kw, 17 hits) # gate"; "verified" requires the strictly higher UKDL rungs (8.3), so E3 is
- `hooks/hook-dispatcher.js:295` (3kw, 15 hits) // idempotently to the deposits ledger (+ UKDL candidate / CO-05 asset side-
- `vault/specs/gsd-x-n3.RESUMPTION.md:56` (3kw, 6 hits) | UKDL promotion of 5 rule candidates | `PROMOTION_PENDING_CONCURRENT_WRITER` | `vault/knowledge_base/ukdl-universal.md` held **1,061** uncommitted foreign rows
- `modules/rule_compiler/schema.py:37` (3kw, 4 hits) "ukdl", "never_again", "session_lessons", "osa absorption",
- `tools/design_gate.py:490` (3kw, 4 hits) looked" -- which is the sealed rule at ukdl-universal.md:7035, recurring here.
- `tools/test_sdd_os_activation.py:65` (3kw, 4 hits) # (the doc's own UKDL entry quotes the phrase it forbids).

### C-63 KNOWLEDGE VAULT  [kw: knowledge, vault]
- `tools/vault_extractor.py:38` (2kw, 67 hits) (r"AKOS Knowledge|ChatGPT Vision|DNA Flywheel", "stacks", "knowledge-tools.md"),
- `tools/normalize_paths.py:77` (2kw, 62 hits) "vault/knowledge_base/session_lessons.md",
- `tools/vault_sync.py:5` (2kw, 56 hits) Scans ~/.claude/knowledge_vault/ for all .md files, rebuilds INDEX.md with
- `tools/kobi_graphify.py:3` (2kw, 49 hits) kobi-graphify — Knowledge Graph Generator for Claude Power Pack.
- `tools/dataset_enricher.py:4` (2kw, 46 hits) Walks every knowledge_base / mistakes / lessons file across the canonical
- `tools/graphify_knowledge.py:3` (2kw, 40 hits) graphify_knowledge — GK-03/GK-04 knowledge-node + typed-edge extension for kobi_graphify.

### C-64 ERROR → IMMUNITY  [kw: error, immunity]
- NO CANDIDATE (search found nothing: NEW, DATASET ONLY, or vocabulary differs -- verify)

### C-65 SUCCESS → INSTINCT  [kw: success, instinct]
- `tools/ceps.py:277` (2kw, 7 hits) resolution_success: bool = False,
- `modules/done_gate/architectural_truth.py:11` (2kw, 3 hits) function returned success   is not   side effect committed correctly

### C-66 AGENT TEAMS MODE  [kw: agent, teams, mode]
- `vault/specs/agent-capability-virtualization.md:2` (3kw, 72 hits) covers: [agent-virtualization, agent-spec, agent-estate-audit, carrier-agents, agent-resolver, proof-bundle, role-paging, agent-foundry, agent-discovery-cost, a
- `vault/specs/cursor-window-session-restoration.md:6` (3kw, 5 hits) originating_prompt: /ultra-plan, AGENT TEAMS MODE autónomo
- `modules/capability_runtime/agent_spec.py:2` (2kw, 82 hits) """agent_spec.py -- AgentSpec: a capability contract that a carrier agent can run.
- `modules/governance-overlay/mistakes-registry.md:82` (2kw, 80 hits) - **Example:** KairosDreamer module file didn't exist, its startup was commented out in application.ex, yet the commit message claimed "persistent memory via Ec
- `tools/agent_carrier_run.py:2` (2kw, 79 hits) """agent_carrier_run -- dispatch one compiled AgentSpec through a REAL carrier.
- `tools/gsd_mission.py:406` (2kw, 65 hits) """``claude agents --json``: every active session, interactive and background.

### C-67 UWCP  [kw: uwcp]
- `vault/specs/tla/counterexamples/UWCP_current.txt:1` (1kw, 198 hits) # TLC counterexample for UWCP_current.cfg (predicted: AtMostOneLiveExecutor)
- `vault/specs/tla/counterexamples/UWCP_nostopevidence.txt:1` (1kw, 184 hits) # TLC counterexample for UWCP_nostopevidence.cfg (predicted: AtMostOneLiveExecutor)
- `vault/specs/tla/counterexamples/UWCP_mutant_nofence.txt:1` (1kw, 183 hits) # TLC counterexample for UWCP_mutant_nofence.cfg (predicted: StaleFenceCannotAdvance)
- `vault/specs/tla/counterexamples/UWCP_nobound.txt:1` (1kw, 182 hits) # TLC counterexample for UWCP_nobound.cfg (predicted: EveryRunningEpochEndsOrBlocks)
- `vault/specs/tla/counterexamples/UWCP_pre_cf4d71b.txt:1` (1kw, 169 hits) # TLC counterexample for UWCP_pre_cf4d71b.cfg (predicted: ReceiptOnlyForOpenEpoch)
- `vault/specs/tla/counterexamples/UWCP_mutant_resumeaftercancel.txt:1` (1kw, 167 hits) # TLC counterexample for UWCP_mutant_resumeaftercancel.cfg (predicted: CancelledNeverResumes)

### C-68 LOOPS / AUTONOMOUS ONE-SHOT CONVERGENCE  [kw: loops, autonomous, one-shot, convergence]
- `tools/test_convergence_bounds.py:8` (3kw, 10 hits) diminishing-return detection. Nothing new was built. `/loops` was not created.
- `tools/test_gsd_mission.py:59` (2kw, 35 hits) rec = gm.create(TMP, "/gsd-autonomous", mission_id="m-a", now=NOW)
- `modules/gsd_x/goal/sweep.py:2` (2kw, 20 hits) """The unattended driver: advance autonomous goals, under preconditions it checks.
- `tools/test_gsd_x_goal_sweep_all.py:4` (2kw, 12 hits) The scheduler calls `sweep-all`, which must DISCOVER autonomous goals from the
- `tools/test_gsd_x_goal_sweep.py:46` (2kw, 11 hits) def make_goal(base: Path, gid: str, repo: Path, autonomous: bool):
- `tools/gsd_x_goal.py:211` (2kw, 9 hits) def cmd_autonomous(args) -> int:

### C-69 CONTEXT HYGIENE  [kw: context, hygiene]
- `tools/tco_compact_gate.py:10` (2kw, 46 hits) -> current session context-pct estimate + recommendation
- `hooks/session_start_hub.js:18` (2kw, 22 hits) *   1. hookRestartResume (INLINE, may emit additionalContext)
- `vault/specs/cpp-gsd-long.CERTIFICATION.md:72` (2kw, 10 hits) row newer than the cycle reference. A low context reading is not one: on
- `tools/gsd_x_recon_streams.py:22` (2kw, 9 hits) "S02": ("UWCP continuity plane and its assimilated primitives (lease, trace context, provider routing, history check, inference bench, done-gate evidence class)
- `modules/cognitive_os/gc.py:6` (2kw, 4 hits) so context stays minimal and the asset store stays clean. It is the proactive,
- `modules/code-review/code_reviewer.py:185` (2kw, 3 hits) "Bare 'git' in PowerShell context -- git is NOT on PowerShell -NonInteractive PATH on this host.",

### C-70 MICRO-COMMITS  [kw: micro-commits]
- `commands/speckit-tasks.md:24` (1kw, 1 hits) 7. **Commit.** `git commit -m "feat(tasks): <feature-id> N tasks across M micro-commits"`.
- `tools/ceps.py:4` (1kw, 1 hits) Covers FASE 2 micro-commits M8 (3 triggers), M9 (root-cause extractor),
- `vault/specs/agent-capability-virtualization.md:115` (1kw, 1 hits) ## Slices (micro-commits, V-gates, pushed)
- `vault/specs/external-capability-assimilation.md:40` (1kw, 1 hits) ## Tranches (execution order; each = 1..n micro-commits, focused gate before commit)
- `vault/specs/uwcp.md:211` (1kw, 1 hits) ## 17-18. Slices and micro-commits (~46, three repos; HEAD re-read + pathspec + staged-diff check before each)

### C-71 CONCURRENT WRITER SAFETY  [kw: concurrent, writer, safety]
- `tools/foreign_hunk_guard.py:5` (3kw, 21 hits) against concurrent writers, and they work -- until two writers are inside the
- `hooks/hook-dispatcher.js:125` (3kw, 12 hits) // On Windows the shell is Git Bash; ≳3 concurrent msys2 forks collapse the
- `modules/cpc_os/vscode_autorun.py:64` (3kw, 10 hits) # so a 30-pane repo spawns 30 concurrent `claude --resume` handshakes on window
- `vault/specs/parent-context-epoch-rotation.md:82` (3kw, 8 hits) limit ends wscript, not the python grandchild, so `IgnoreNew` does not stop overlap: concurrent
- `vault/specs/mission-continuity.RESUMPTION.md:9` (3kw, 7 hits) commit by pathspec, check diff hunk headers (UKDL is edited by others concurrently).
- `vault/specs/mission-continuity.md:167` (3kw, 7 hits) - **Concurrent panes** in this repo (hundreds of dirty foreign paths) → new files preferred, pathspec commits, HEAD re-read before each commit.

### C-72 NO CODE IN THIS MISSION PROMPT  [kw: code, mission, prompt]
- `tools/gsd_mission.py:45` (3kw, 503 hits) def _code_id() -> str:
- `tools/fixtures/gsd_mission_legacy_golden.json:102` (3kw, 192 hits) "code_id",
- `tools/test_gsd_mission.py:148` (3kw, 146 hits) check(gate, r.returncode == 9 and got["note"] == want_note and got["epoch"] == before["epoch"],
- `modules/knowledge_acquisition/store.py:116` (3kw, 120 hits) USING fts5(prompt_id UNINDEXED, question, family, tokenize='unicode61');
- `vault/specs/mission-capsule-rollover.md:3` (3kw, 103 hits) status: SPEC (T0). T1-T6 built; section 11 (M2/L1/L2/no-note/guard/T7) LIVE in code S1-S7 (T7 partial, see 11.6); T8 Production Reality HELD by Owner (2026-10-0
- `tools/test_gsd_mission_capsule_v2.py:90` (3kw, 101 hits) self.stdout, self.stderr, self.returncode = out, "", 0

### C-73 FIRST VERTICAL SLICE  [kw: first, vertical, slice]
- `vault/specs/gsd-x-n5.RESUMPTION.md:65` (3kw, 9 hits) this denial first-hand on its first attempt to write this very file.
- `tools/test_gsd_x_mission.py:31` (3kw, 7 hits) GIT = shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"   # PATH first: GEX44 (Linux) runs these
- `vault/specs/gsd-x-n4.RESUMPTION.md:53` (3kw, 6 hits) Production Reality: **FIRST_VERTICAL_SLICE**, `UNIVERSAL_CAPABILITY_UNPROVEN`.
- `modules/knowledge_acquisition/SPEC.md:46` (3kw, 4 hits) | Promotion gates | `dataset_first/manifest.py:75-113`, `hard_rules/writer.py:186-235` | REUSE |
- `vault/specs/gsd-x-n3.RESUMPTION.md:63` (3kw, 3 hits) The Mission Intelligence Spine's first vertical slice — sparse intent → Mission Contract
- `hooks/closer-guard.js:128` (2kw, 33 hits) // Spanish-coverage gap it first looked like, and patching only the Spanish

### C-74 PRODUCER → CONSUMER → COMPLETION EFFECT  [kw: producer, consumer, completion, effect]
- `modules/governance-overlay/mistakes-registry.md:346` (4kw, 21 hits) ## Mistake #38: Producer-Consumer Gap (Deferred Wiring That Never Completes)
- `tools/verify_spp.py:752` (4kw, 12 hits) # from outcomes; the Constitution improves) had no producer because of it.
- `tools/test_dataset_first_protocol.py:120` (4kw, 8 hits) # --- V-DFP-ONTOLOGY-COMPLETE -- every canonical object has a producer AND consumer
- `modules/oracle/ovo-protocol.md:32` (4kw, 6 hits) 3. For each entry in `new[]`, identify the **consumer**: grep for imports or references. If no consumer exists in the same session's proposed output, flag **Mis
- `vault/specs/external-capability-assimilation.md:77` (4kw, 5 hits) 25. Regression Memory → EXTEND Knowledge Vault lessons with a `regression:` block (failing output, reproducer, source sha256, passing receipt, staleness) + `too
- `tools/test_gsd_x_facts_v2.py:27` (3kw, 26 hits) This paragraph used to record a limitation: no fact the producer could emit was

### C-75 DONE GATE — REQUIRED CLOSURES  [kw: gate, required, closures]
- `tools/gsd_x_mission.py:2` (3kw, 38 hits) """Mission Intelligence CLI -- derive, inspect, gate, close.
- `tools/test_gsd_x_facts_v2.py:1` (3kw, 36 hits) """V-FACTSV2-* -- GSDX-M05: what the fact source could NOT say reaches the gate.
- `modules/gsd_x/mission/closure.py:11` (3kw, 26 hits) a verdict produced by a gate that ran -- carrying the gate's identity, its exit
- `modules/governance-overlay/mistakes-registry.md:82` (3kw, 17 hits) - **Example:** KairosDreamer module file didn't exist, its startup was commented out in application.ex, yet the commit message claimed "persistent memory via Ec
- `tools/test_floor_regression_gate.py:2` (2kw, 161 hits) """V-FLOOR-* gates: the floor regression gate (incremental-cognition phase 4, pillar K).
- `tools/test_uceimr_residues.py:2` (2kw, 157 hits) """test_uceimr_residues.py -- V-gates for UCEIMR residues R1 and R2.

### C-76 FOUNDER INTERACTION DURING THE MISSION  [kw: founder, interaction, during, mission]
- `tools/rollover.py:1175` (3kw, 48 hits) except FileNotFoundError:
- `modules/zero-crash/hooks/context-watchdog.py:301` (3kw, 29 hits) except FileNotFoundError:
- `tools/verify_spp.py:285` (3kw, 8 hits) except FileNotFoundError as e:
- `vault/specs/cross-project-baseline.md:194` (3kw, 8 hits) `ModuleNotFoundError` (2).
- `tools/test_capture_liveness.py:170` (3kw, 4 hits) ("FileNotFoundError: cannot open C:\\Users\\User\\repo\\alpha.py line 42",
- `tools/gsd_mission.py:2203` (2kw, 438 hits) # certified (a budget halt during a same-session continuation, review 2026-10-05).

### C-77 REFERENCE FRONTIER AMBITION  [kw: reference, frontier, ambition]
- `tools/test_frontier_intelligence_os.py:373` (2kw, 46 hits) _ok("V-FIOS-LIVE-PATH-WIRED", "dispatcher + kclaude reference the engines")
- `modules/frontier_intelligence/session_compiler.py:16` (2kw, 40 hits) dependence-reducing) is REFERENCED as the ORDER heuristic among admitted
- `tools/jit_skill_loader.py:137` (2kw, 26 hits) # reference pointers). Everything else is explicit negative space
- `modules/liveness/reachability.py:24` (2kw, 14 hits) would call the genuinely-live `power_beacon` an orphan. References are matched as
- `tools/usea_outcome_contrast.py:39` (2kw, 12 hits) are reachable: a known-good reference implementation must PASS and the naive
- `tools/test_duplicate_to_advantage.py:203` (2kw, 9 hits) # V-D2A-NO-DUPLICATE -- registry references real sealed families; doctrine declares

### C-78 META-ANALYSIS AT SESSION / EPOCH CLOSURE  [kw: meta-analysis, session, epoch, closure]
- `modules/gsd_x/goal/epoch.py:5` (3kw, 86 hits) a worktree, a headless Claude session, a deterministic gate, a /cpp-gsd-long
- `modules/gsd_x/goal/providers/claude.py:4` (3kw, 40 hits) HEADLESS (`claude -p`) is a NEW session in an isolated worktree, authorised by
- `vault/specs/uwcp.md:237` (3kw, 34 hits) 46 certification record, UKDL (HR/PR/T), vault lessons, ratchet candidate, meta-analysis, RESUMPTION, handoff.
- `tools/test_gsd_x_goal_mutation.py:177` (3kw, 33 hits) LRP, 'return Observation(OBS_UNKNOWN, "", "no ledger rows for this session")',
- `modules/gsd_x/goal/sweep.py:17` (3kw, 32 hits) exits; a work epoch spends the Owner's Codex account or starts a session. The
- `tools/gsd_x_goal.py:299` (3kw, 32 hits) # providers spend an account or a session and are dispatched

### C-79 FINAL HANDOFF  [kw: final, handoff]
- `tools/test_cognitive_economy_program.py:6` (2kw, 43 hits) python tools/test_cognitive_economy_program.py --final
- `tools/test_gsd_mission.py:128` (2kw, 41 hits) # Hard kill at the rename boundary, in a real separate process (no finally/cleanup runs).
- `tools/test_alert_escalation.py:76` (2kw, 39 hits) finally:
- `tools/test_incremental_cognition_program.py:4` (2kw, 38 hits) python tools/test_incremental_cognition_program.py --final
- `tools/gsd_mission.py:205` (2kw, 34 hits) finally:
- `tools/rollover.py:1056` (2kw, 31 hits) finally:

### C-80 FINAL KILL-SWITCHES  [kw: final, kill-switches]
- NO CANDIDATE (search found nothing: NEW, DATASET ONLY, or vocabulary differs -- verify)

### C-81 ULTIMATE CONSTITUTIONAL OUTCOME  [kw: ultimate, constitutional, outcome]
- `tools/usea_corpus_gate.py:12` (2kw, 20 hits) * its opening and closing anchors still match the constitutional contract,
- `tools/verify_spp.py:796` (2kw, 20 hits) # registered none of them, so the constitutional floor was enforced by
- `modules/zero-crash/hooks/context-watchdog.py:82` (2kw, 19 hits) the next source and ultimately to the constants.
- `tools/test_baseline_inheritance.py:2` (2kw, 10 hits) """V-gates for constitutional baseline inheritance.
- `tools/test_dataset_first_protocol.py:165` (2kw, 8 hits) "design the permanent constitutional governance authority and ontology for a "
- `commands/usea.md:43` (2kw, 5 hits) Audit which Power Pack owner discharges each constitutional law.

## Salvaged prior work: `.planning/workstreams/edd/phases/01-reality-scan-ownership-matrix-spec/01-RESEARCH.md` (54293 B; headings only, page for body)
# Phase 1: Reality scan + ownership matrix + spec - Research
## User Constraints (from CONTEXT.md)
### Locked Decisions
### Claude's Discretion
### Deferred Ideas (OUT OF SCOPE)
## Phase Requirements
## Summary
## Architectural Responsibility Map
## Project Constraints (from CLAUDE.md)
## Package Legitimacy Audit
## A. gsd_x mission pipeline: traced facts (read this session)
### A1. `modules/gsd_x/mission/obligation.py` (534 lines)
### A2. `modules/gsd_x/mission/closure.py` (316 lines)
### A3. `modules/gsd_x/mission/coverage.py` (124 lines)
### A4. Mission-path consumers (who calls what) [VERIFIED by grep + read this session]
### A5. LATENT DEFECT FOUND (dogfood item for Phase 4 + Knowledge Vault): `contract.project` references `o.id`
### A6. Goal spine (`modules/gsd_x/goal/*`) - traced
### A7. Bridge gap, stated precisely (mission `Obligation` vs goal `GoalObligation`) [VERIFIED: tools/gsd_x_goal.py:86-97, tools/gsd_x_mission.py:71-126, mission/store.py:85-95]
## B. Decision provenance owner (D-01/D-02 target) - what the scan found
## C. Test locations and the measured BASELINE on GEX44 (run this session, foreground, isolated HOME)
## D. Spec format and the SDD gate that reads `covers:` [VERIFIED by reading this session]
### A8. Caller table (public functions of the probable owners; grep over modules/, tools/, hooks/, commands/, capabilities/; tests listed separately) [VERIFIED by grep + reads this session]
### A9. Test directories and where each owner's tests live
## E. Where the other named systems live in THIS repo (searched, not assumed)
### E1. Liveness baseline addendum (ran `python3 modules/liveness/reachability.py` at HEAD 0372b5f5, host GEX44)
