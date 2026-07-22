# Liveness Ledger -- post-ship verdict (D1)

Generated 2026-07-22T15:41:31.233222+00:00 | 316 components | 136 LIVE, 180 non-LIVE (5 silent, 0 drifted, 175 orphaned, 0 unknown).

Verdict class: LIVE = recent end-to-end evidence; WIRED-BUT-SILENT = wired but no recent evidence (idle / broken producer / producer-without-consumer); DRIFTED = repo vs ~/.claude/hooks hash mismatch; ORPHANED = live artifact with no repo source.

| Component | Surface | Verdict | Evidence |
|---|---|---|---|
| `module:akos_knowledge/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:arch-decision/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:arch-decision/test_closed_loop` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:arch-decision/test_v_block` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:auto-testing/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:auto-testing/detectors` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:auto-testing/generators/_common` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:auto-testing/generators/java_gen` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:auto-testing/generators/node_gen` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:auto-testing/generators/python_gen` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:auto-testing/llm_bridge` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:backup/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:backup/retention` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:backup/runners/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:backup/runners/docker_volume_tar` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:backup/runners/pg_dump` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:backup/runners/rsync_dir` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:backup/test_v_block` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:backup/verify_restore` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:cascade_prevention/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:cascade_prevention/blocker` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:cascade_prevention/pre_mortem` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:cascade_prevention/surfaces` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:ccf/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:ccf/artifact_compiler` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:ccf/cli` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:ccf/config_schema` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:ccf/contract_engine` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:ccf/evaluation_engine` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:ccf/knowledge_feed` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:ccf/model_adapter` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:ccf/prompt_compiler` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:ccf/release_manager` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:ccf/test_ccf` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:ccf/trademark_scanner` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:code-review/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:cognitive_os/context` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:cognitive_os/economics` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:cognitive_os/gc` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:cognitive_os/governor` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:cognitive_os/guarantee_ledger` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:cognitive_os/hibernate_runner` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:cognitive_os/loop_budget` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:cognitive_os/memory` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:cognitive_os/rehydration` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:contract_fabric/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:contract_fabric/side_effect_ledger` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:cost_collapse/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:craif/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:craif/authority` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:craif/candidate` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:craif/intake` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:craif/ledger` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:craif/objects` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:craif/runtime` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:daif/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:daif/constraint_extractor` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:daif/decision_extractor` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:daif/obligation_extractor` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:daif/resume_reader` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:daif/session_continuity_compiler` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:daif/two_arm_trial` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:dataset_first/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:dataset_first/calibrator` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:dataset_first/classifier` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:dataset_first/knowledge_sufficiency` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:dataset_first/manifest` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:dataset_first/necessity_record` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:decision_review/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:decision_review/accountability` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:decision_review/decision_kernel` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:decision_review/decision_record` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:decision_review/proactive_scanner` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:decision_review/providers` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:deployment/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:deployment/detectors` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:deployment/runners/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:deployment/runners/gh_workflow` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:deployment/runners/git_push` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:deployment/runners/scp_systemd` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:deployment/test_v_block` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:done_gate/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:done_gate/artifact_done_gate` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:duplicate_to_advantage/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:error_prevention/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:fable_distillation/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:fable_distillation/fd_00_gate` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:fable_distillation/fd_04_contrast` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:fable_distillation/ukdl_queue` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:frontier_intelligence/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:frontier_intelligence/corpus_roi` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:frontier_intelligence/question_harvester` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:frontier_intelligence/session_compiler` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:frontier_intelligence/unknown_unknown_generator` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:graphify/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:hard_rules/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:hard_rules/residual` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:monitoring/alert` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:output_contracts/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:parallel_mesh/pm_01_brain` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:parallel_mesh/pm_02_intent` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:parallel_mesh/pm_04_auction` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:parallel_mesh/pm_05_prefetch` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:pp_agents/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:pp_agents/signals/backlog` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:pp_agents/signals/cost` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:pp_agents/signals/errors` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:pp_agents/signals/health` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:pp_agents/signals/lessons` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:pp_agents/signals/quality` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:pp_agents/signals/sdd_tier` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:pp_agents/signals/setup_scan` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:recall_roi/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:refcheck/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:refcheck/linter` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:rollback/runners/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:rollback/runners/restore_docker_volume` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:rollback/runners/restore_pg_dump` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:rollback/runners/restore_rsync_dir` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:rollback/source_selector` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:rule_compiler/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:rule_compiler/compiler` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:rule_compiler/digest` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:rule_compiler/parser` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:rule_compiler/schema` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sdd_os/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:session_resilience/integration` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:session_resilience/multi_window` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:session_resilience/resume_identity` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:session_resilience/snapshot_versioning` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:session_resilience/ui_state` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:setup_os/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:skill_router/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sleepless_qa/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sleepless_qa/__main__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sleepless_qa/cli` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sleepless_qa/dumpers/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sleepless_qa/dumpers/base` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sleepless_qa/dumpers/cli` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sleepless_qa/dumpers/minecraft` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sleepless_qa/dumpers/python_daemon` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sleepless_qa/dumpers/web` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sleepless_qa/healer/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sleepless_qa/healer/dispatcher_bridge` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sleepless_qa/healer/lock` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sleepless_qa/healer/orchestrator` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sleepless_qa/healer/pattern_cache` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sleepless_qa/healer/run_log` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sleepless_qa/heartbeat` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sleepless_qa/verdict/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sleepless_qa/verdict/contract` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sleepless_qa/verdict/engine` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sleepless_qa/verdict/log_pattern` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sleepless_qa/verdict/schema` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sleepless_qa/verdict/visual` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sqi/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sqi/baseline_guardian` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sqi/environment_qualifier` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sqi/reconcile` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sqi/redteam_protocol` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sqi/repo_reality_scanner` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sqi/weakening_baseline` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sqi/weakening_detectors` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sweep_enforcer/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:sweep_enforcer/rule_sweep` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:uqf/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:uqf/gates` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:wrapper/__init__` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:wrapper/auto_resumer` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:wrapper/cost_gate` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:wrapper/prelaunch` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:wrapper/repo_coordinator` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:wrapper/session_namer` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:wrapper/turn_counter` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:wrapper/verify_before_emit` | reachability | **ORPHANED** | no live surface reaches this module |
| `dfp-necessity-ledger` | decision-registry | **WIRED-BUT-SILENT** | newest necessity_ledger.jsonl 243.0h ago (> 36h -- quiet) |
| `drk-proactive` | audits | **WIRED-BUT-SILENT** | newest drk_proactive_2026-07-11.md 259.6h ago (> 36h -- quiet) |
| `kclaude-preflight` | kclaude | **WIRED-BUT-SILENT** | newest SESSION_ZERO_2026-07-11T112609Z.md 268.3h ago (> 36h -- quiet) |
| `pm-03-bus` | pm-bus | **WIRED-BUT-SILENT** | 13 producer file(s); consumer is the SessionStart hub read but emits no 'pm03_consume' signal -- consumption unmeasured |
| `sqi-runner` | audits | **WIRED-BUT-SILENT** | newest sqi_report_2026-07-12.md 238.7h ago (> 36h -- quiet) |
| `drk-kernel` | decision-registry | **LIVE** | records.jsonl 20.9h ago (<= 36h) |
| `fd-07-flywheel` | stop-chain | **LIVE** | 911 signals, freshest 0.2h ago (<= 36h) |
| `fios-token-irr` | stop-chain | **LIVE** | 864 signals, freshest 0.2h ago (<= 36h) |
| `hook-dispatcher` | hooks-dir | **LIVE** | in sync (sha256 778f8d08f08a) |
| `module:ads/__init__` | reachability | **LIVE** | reached from modules/ads/detector |
| `module:ads/detector` | reachability | **LIVE** | reached from tools/ads_backfill.py |
| `module:ads/doc_generator` | reachability | **LIVE** | reached from tools/ads_backfill.py |
| `module:ads/doc_updater` | reachability | **LIVE** | reached from tools/ads_sync.py |
| `module:akos_knowledge/akos` | reachability | **LIVE** | reached from tools/jit_skill_loader.py |
| `module:arch-decision/arch_check` | reachability | **LIVE** | reached from commands/arch-decision.md |
| `module:arch-decision/build_index` | reachability | **LIVE** | reached from commands/arch-decision.md |
| `module:auto-testing/auto_test` | reachability | **LIVE** | reached from hooks/auto-test-gate.js |
| `module:auto-testing/generators/__init__` | reachability | **LIVE** | reached from commands/auto-test.md |
| `module:auto-testing/vault_io` | reachability | **LIVE** | reached from commands/auto-test.md |
| `module:backlog_autopilot/__init__` | reachability | **LIVE** | reached from commands/what-now.md |
| `module:backlog_autopilot/engine` | reachability | **LIVE** | reached from CLAUDE.md |
| `module:backup/backup` | reachability | **LIVE** | reached from commands/backup.md |
| `module:cascade_prevention/dangerous_cmds` | reachability | **LIVE** | reached from hooks/cascade_check_bash.js |
| `module:cascade_prevention/engine` | reachability | **LIVE** | reached from hooks/cascade_check_bash.js |
| `module:cascade_prevention/types` | reachability | **LIVE** | reached from modules/cascade_prevention/engine |
| `module:cdio/__init__` | reachability | **LIVE** | reached from live:cdio-core.md |
| `module:cdio/bus_bridge` | reachability | **LIVE** | reached from live:cdio-core.md |
| `module:cdio/scorer` | reachability | **LIVE** | reached from live:cdio-reviewer.md |
| `module:cdio/telemetry` | reachability | **LIVE** | reached from modules/cognitive_os/co_12_telemetry |
| `module:code-review/code_reviewer` | reachability | **LIVE** | reached from commands/code-review.md |
| `module:code-review/test_closed_loop` | reachability | **LIVE** | reached from modules/code-review/code_reviewer |
| `module:code-review/test_combined_gate` | reachability | **LIVE** | reached from modules/code-review/code_reviewer |
| `module:code-review/test_v_block` | reachability | **LIVE** | reached from modules/code-review/code_reviewer |
| `module:code_review/__init__` | reachability | **LIVE** | reached from live:pp-code-reviewer.md |
| `module:cognitive_os/__init__` | reachability | **LIVE** | reached from modules/cdio/telemetry |
| `module:cognitive_os/co_12_telemetry` | reachability | **LIVE** | reached from tools/jit_skill_loader.py |
| `module:cognitive_os/hibernation` | reachability | **LIVE** | reached from modules/cognitive_os/process_governor |
| `module:cognitive_os/process_governor` | reachability | **LIVE** | reached from CLAUDE.md |
| `module:cognitive_os/registry` | reachability | **LIVE** | reached from modules/cognitive_os/router |
| `module:cognitive_os/router` | reachability | **LIVE** | reached from modules/cognitive_os/co_12_telemetry |
| `module:cognitive_os/scheduler` | reachability | **LIVE** | reached from modules/cognitive_os/process_governor |
| `module:cost_collapse/router` | reachability | **LIVE** | reached from CLAUDE.md |
| `module:cpc_os/__init__` | reachability | **LIVE** | reached from hooks/session_start_hub.js |
| `module:cpc_os/auto_reset_orchestrator` | reachability | **LIVE** | reached from commands/auto-reset.md |
| `module:cpc_os/backlog` | reachability | **LIVE** | reached from modules/cpc_os/__init__ |
| `module:cpc_os/beacon` | reachability | **LIVE** | reached from hooks/session_start_hub.js |
| `module:cpc_os/context_monitor` | reachability | **LIVE** | reached from commands/auto-reset.md |
| `module:cpc_os/handoff` | reachability | **LIVE** | reached from modules/cpc_os/__init__ |
| `module:cpc_os/heartbeat` | reachability | **LIVE** | reached from modules/cpc_os/__init__ |
| `module:cpc_os/recovery` | reachability | **LIVE** | reached from modules/cpc_os/__init__ |
| `module:cpc_os/registry` | reachability | **LIVE** | reached from hooks/session_start_hub.js |
| `module:cpc_os/restart` | reachability | **LIVE** | reached from modules/cpc_os/__init__ |
| `module:cpc_os/router` | reachability | **LIVE** | reached from modules/cpc_os/__init__ |
| `module:cpc_os/snapshot` | reachability | **LIVE** | reached from hooks/session_start_hub.js |
| `module:cpc_os/switch` | reachability | **LIVE** | reached from modules/cpc_os/__init__ |
| `module:cpc_os/topology_reconcile` | reachability | **LIVE** | reached from modules/cpc_os/vscode_autorun |
| `module:cpc_os/vscode_autorun` | reachability | **LIVE** | reached from commands/restore-panes.md |
| `module:cpc_os/work_state_saver` | reachability | **LIVE** | reached from commands/auto-reset.md |
| `module:deployment/deploy` | reachability | **LIVE** | reached from commands/deploy.md |
| `module:deployment/healthcheck` | reachability | **LIVE** | reached from commands/rollback.md |
| `module:duplicate_to_advantage/d2a_engine` | reachability | **LIVE** | reached from hooks/d2a_gate.js |
| `module:error_prevention/premise_verifier` | reachability | **LIVE** | reached from CLAUDE.md |
| `module:fable_distillation/epistemic_ladder` | reachability | **LIVE** | reached from modules/cognitive_os/co_12_telemetry |
| `module:fable_distillation/fd_04_prover` | reachability | **LIVE** | reached from modules/fable_distillation/epistemic_ladder |
| `module:fable_distillation/fd_07_flywheel` | reachability | **LIVE** | reached from hooks/hook-dispatcher.js |
| `module:fable_distillation/federated_ledger` | reachability | **LIVE** | reached from modules/frontier_intelligence/token_irr |
| `module:frontier_intelligence/evolution_engine` | reachability | **LIVE** | reached from modules/duplicate_to_advantage/d2a_engine |
| `module:frontier_intelligence/token_irr` | reachability | **LIVE** | reached from hooks/hook-dispatcher.js |
| `module:graphify/global_store` | reachability | **LIVE** | reached from modules/graphify/indexer |
| `module:graphify/indexer` | reachability | **LIVE** | reached from hooks/graph_first_gate.js |
| `module:graphify/session_writeback` | reachability | **LIVE** | reached from hooks/hook-dispatcher.js |
| `module:hard_rules/extractor` | reachability | **LIVE** | reached from tools/bug_to_hardrule.py |
| `module:hard_rules/writer` | reachability | **LIVE** | reached from tools/bug_to_hardrule.py |
| `module:liveness/__init__` | reachability | **LIVE** | reached from modules/liveness/liveness_ledger |
| `module:liveness/liveness_ledger` | reachability | **LIVE** | reached from commands/liveness.md |
| `module:liveness/reachability` | reachability | **LIVE** | reached from commands/liveness.md |
| `module:monitoring/__init__` | reachability | **LIVE** | reached from commands/revenue-ready.md |
| `module:monitoring/monitor` | reachability | **LIVE** | reached from modules/uqf/auditor |
| `module:monitoring/observe` | reachability | **LIVE** | reached from live:pp-monitor.md |
| `module:one_shot/__init__` | reachability | **LIVE** | reached from commands/one-shot-compile.md |
| `module:one_shot/compiler` | reachability | **LIVE** | reached from commands/one-shot-compile.md |
| `module:one_shot/escalation` | reachability | **LIVE** | reached from CLAUDE.md |
| `module:one_shot/lock` | reachability | **LIVE** | reached from CLAUDE.md |
| `module:osa/__init__` | reachability | **LIVE** | reached from modules/osa/dispatcher |
| `module:osa/dispatcher` | reachability | **LIVE** | reached from live:omni-singularity.md |
| `module:osa/gpu_eyes` | reachability | **LIVE** | reached from live:omni-singularity.md |
| `module:osa/never_again` | reachability | **LIVE** | reached from live:omni-singularity.md |
| `module:osa/osa_command` | reachability | **LIVE** | reached from modules/osa/dispatcher |
| `module:osa/throttle` | reachability | **LIVE** | reached from live:omni-singularity.md |
| `module:output_contracts/validator` | reachability | **LIVE** | reached from CLAUDE.md |
| `module:owner_queue/__init__` | reachability | **LIVE** | reached from hooks/session_start_hub.js |
| `module:owner_queue/owner_queue` | reachability | **LIVE** | reached from hooks/session_start_hub.js |
| `module:parallel_mesh/__init__` | reachability | **LIVE** | reached from modules/cdio/bus_bridge |
| `module:parallel_mesh/pm_03_bus` | reachability | **LIVE** | reached from modules/cdio/bus_bridge |
| `module:pp_agents/proactive_core` | reachability | **LIVE** | reached from hooks/bug-hunter-ceps-bridge.js |
| `module:pp_agents/proactive_dispatcher` | reachability | **LIVE** | reached from tools/jit_skill_loader.py |
| `module:pp_agents/signals/__init__` | reachability | **LIVE** | reached from modules/pp_agents/proactive_dispatcher |
| `module:pp_agents/signals/cascade` | reachability | **LIVE** | reached from live:pp-cascade-guard.md |
| `module:pp_agents/signals/code_quality` | reachability | **LIVE** | reached from hooks/uqf_pre_edit_gate.js |
| `module:pp_agents/signals/error_recurrence` | reachability | **LIVE** | reached from live:pp-error-analyst.md |
| `module:pp_agents/signals/premise_risk` | reachability | **LIVE** | reached from live:pp-premise-guardian.md |
| `module:pp_agents/signals/spec_compliance` | reachability | **LIVE** | reached from live:pp-spec-guardian.md |
| `module:recall_roi/recall_roi` | reachability | **LIVE** | reached from modules/cognitive_os/co_12_telemetry |
| `module:rollback/__init__` | reachability | **LIVE** | reached from modules/monitoring/observe |
| `module:rollback/rollback` | reachability | **LIVE** | reached from commands/rollback.md |
| `module:rollback/test_v_block` | reachability | **LIVE** | reached from modules/deployment/deploy |
| `module:sdd_os/prd_generator` | reachability | **LIVE** | reached from commands/prd-generate.md |
| `module:secret_firewall/__init__` | reachability | **LIVE** | reached from CLAUDE.md |
| `module:secret_firewall/allowlist` | reachability | **LIVE** | reached from tools/secret_scan_repo.py |
| `module:secret_firewall/detector` | reachability | **LIVE** | reached from hooks/secret_firewall_gate.js |
| `module:secret_firewall/redactor` | reachability | **LIVE** | reached from modules/session_resilience/telemetry |
| `module:secret_firewall/reporter` | reachability | **LIVE** | reached from modules/secret_firewall/__init__ |
| `module:session_resilience/__init__` | reachability | **LIVE** | reached from tools/recovery_epoch_gate.py |
| `module:session_resilience/acceptance` | reachability | **LIVE** | reached from commands/recovery-verdict.md |
| `module:session_resilience/epoch` | reachability | **LIVE** | reached from hooks/session_start_hub.js |
| `module:session_resilience/models` | reachability | **LIVE** | reached from tools/recovery_verdict.py |
| `module:session_resilience/power_beacon` | reachability | **LIVE** | reached from hooks/session_start_hub.js |
| `module:session_resilience/reentry` | reachability | **LIVE** | reached from tools/recovery_epoch_gate.py |
| `module:session_resilience/telemetry` | reachability | **LIVE** | reached from modules/session_resilience/reentry |
| `module:setup_os/backlog_generator` | reachability | **LIVE** | reached from commands/setup-backlog.md |
| `module:setup_os/drift_detector` | reachability | **LIVE** | reached from commands/setup-drift.md |
| `module:setup_os/registry` | reachability | **LIVE** | reached from modules/setup_os/scanner |
| `module:setup_os/roi_analyzer` | reachability | **LIVE** | reached from commands/analyze-roi.md |
| `module:setup_os/scanner` | reachability | **LIVE** | reached from commands/scan-repo.md |
| `module:setup_os/secure_installer` | reachability | **LIVE** | reached from commands/setup-repo.md |
| `module:skill_router/intent_classifier` | reachability | **LIVE** | reached from tools/jit_skill_loader.py |
| `module:skill_router/skill_index` | reachability | **LIVE** | reached from tools/jit_skill_loader.py |
| `module:spec_gate/__init__` | reachability | **LIVE** | reached from modules/sdd_os/prd_generator |
| `module:spec_gate/gate` | reachability | **LIVE** | reached from CLAUDE.md |
| `module:uqf/anti_patterns` | reachability | **LIVE** | reached from live:pp-uqf-auditor.md |
| `module:uqf/auditor` | reachability | **LIVE** | reached from tools/uqf_audit.py |
| `module:uqf/principles/__init__` | reachability | **LIVE** | reached from live:pp-uqf-auditor.md |
| `module:uqf/principles/aaa_test_pattern` | reachability | **LIVE** | reached from modules/uqf/principles/__init__ |
| `module:uqf/principles/error_never_silent` | reachability | **LIVE** | reached from modules/uqf/principles/__init__ |
| `module:uqf/principles/false_positives_catalog` | reachability | **LIVE** | reached from live:pp-code-reviewer.md |
| `module:uqf/principles/pre_report_gate` | reachability | **LIVE** | reached from modules/uqf/principles/__init__ |
| `module:uqf/principles/prompt_defense_baseline` | reachability | **LIVE** | reached from modules/uqf/principles/__init__ |
| `module:uqf/principles/proof_triad` | reachability | **LIVE** | reached from modules/uqf/principles/__init__ |
| `module:uqf/principles/severity_table` | reachability | **LIVE** | reached from modules/uqf/principles/__init__ |
| `module:uqf/principles/tdd_workflow` | reachability | **LIVE** | reached from modules/uqf/principles/__init__ |
| `module:uqf/principles/zero_findings_valid` | reachability | **LIVE** | reached from modules/uqf/principles/__init__ |

Non-LIVE rows are the ship->silence gap made visible. A row here is the authoritative liveness fact -- not a lesson rediscovered sessions later.
