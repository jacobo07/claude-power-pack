# Liveness Ledger -- post-ship verdict (D1)

Generated 2026-07-22T16:53:01.292437+00:00 | 316 components | 165 LIVE, 151 non-LIVE (130 silent, 0 drifted, 21 orphaned, 0 unknown).

Verdict class: LIVE = recent end-to-end evidence; WIRED-BUT-SILENT = wired but no recent evidence (idle / broken producer / producer-without-consumer); DRIFTED = repo vs ~/.claude/hooks hash mismatch; ORPHANED = live artifact with no repo source.

| Component | Surface | Verdict | Evidence |
|---|---|---|---|
| `module:arch-decision/test_closed_loop` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:arch-decision/test_v_block` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:backup/test_v_block` | reachability | **ORPHANED** | no live surface reaches this module |
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
| `module:deployment/test_v_block` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:session_resilience/integration` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:session_resilience/multi_window` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:session_resilience/resume_identity` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:session_resilience/snapshot_versioning` | reachability | **ORPHANED** | no live surface reaches this module |
| `module:session_resilience/ui_state` | reachability | **ORPHANED** | no live surface reaches this module |
| `dfp-necessity-ledger` | decision-registry | **WIRED-BUT-SILENT** | newest necessity_ledger.jsonl 244.2h ago (> 36h -- quiet) |
| `drk-proactive` | audits | **WIRED-BUT-SILENT** | newest drk_proactive_2026-07-11.md 260.8h ago (> 36h -- quiet) |
| `kclaude-preflight` | kclaude | **WIRED-BUT-SILENT** | newest SESSION_ZERO_2026-07-11T112609Z.md 269.4h ago (> 36h -- quiet) |
| `module:auto-testing/detectors` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:auto-testing/generators/_common` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:auto-testing/generators/java_gen` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:auto-testing/generators/node_gen` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:auto-testing/generators/python_gen` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:auto-testing/llm_bridge` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:backup/retention` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:backup/runners/__init__` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:backup/runners/docker_volume_tar` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:backup/runners/pg_dump` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:backup/runners/rsync_dir` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:backup/verify_restore` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:cascade_prevention/pre_mortem` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:cognitive_os/context` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:cognitive_os/economics` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:cognitive_os/gc` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:cognitive_os/governor` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:cognitive_os/guarantee_ledger` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:cognitive_os/hibernate_runner` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:cognitive_os/loop_budget` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:cognitive_os/memory` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:cognitive_os/rehydration` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:contract_fabric/__init__` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:contract_fabric/side_effect_ledger` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:craif/__init__` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:craif/authority` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:craif/candidate` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:craif/intake` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:craif/ledger` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:craif/objects` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:craif/runtime` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:daif/__init__` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:daif/constraint_extractor` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:daif/decision_extractor` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:daif/obligation_extractor` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:daif/resume_reader` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:daif/session_continuity_compiler` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:daif/two_arm_trial` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:dataset_first/__init__` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:dataset_first/calibrator` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:dataset_first/classifier` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:dataset_first/knowledge_sufficiency` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:dataset_first/manifest` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:dataset_first/necessity_record` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:decision_review/__init__` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:decision_review/accountability` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:decision_review/decision_kernel` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:decision_review/decision_record` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:decision_review/proactive_scanner` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:decision_review/providers` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:deployment/detectors` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:deployment/runners/__init__` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:deployment/runners/gh_workflow` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:deployment/runners/git_push` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:deployment/runners/scp_systemd` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:done_gate/__init__` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:done_gate/artifact_done_gate` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:fable_distillation/fd_00_gate` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:fable_distillation/fd_04_contrast` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:fable_distillation/ukdl_queue` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:frontier_intelligence/corpus_roi` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:frontier_intelligence/session_compiler` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:frontier_intelligence/unknown_unknown_generator` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:hard_rules/residual` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:monitoring/alert` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:parallel_mesh/pm_01_brain` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:parallel_mesh/pm_02_intent` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:parallel_mesh/pm_04_auction` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:parallel_mesh/pm_05_prefetch` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:pp_agents/signals/backlog` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:pp_agents/signals/cost` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:pp_agents/signals/errors` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:pp_agents/signals/health` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:pp_agents/signals/lessons` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:pp_agents/signals/quality` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:pp_agents/signals/sdd_tier` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:pp_agents/signals/setup_scan` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:refcheck/__init__` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:refcheck/linter` | reachability | **WIRED-BUT-SILENT** | unreachable; declared PLANNED |
| `module:rollback/runners/__init__` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:rollback/runners/restore_docker_volume` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:rollback/runners/restore_pg_dump` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:rollback/runners/restore_rsync_dir` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:rollback/source_selector` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:sleepless_qa/__init__` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:sleepless_qa/__main__` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:sleepless_qa/cli` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:sleepless_qa/dumpers/__init__` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:sleepless_qa/dumpers/base` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:sleepless_qa/dumpers/cli` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:sleepless_qa/dumpers/minecraft` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:sleepless_qa/dumpers/python_daemon` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:sleepless_qa/dumpers/web` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:sleepless_qa/healer/__init__` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:sleepless_qa/healer/dispatcher_bridge` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:sleepless_qa/healer/lock` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:sleepless_qa/healer/orchestrator` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:sleepless_qa/healer/pattern_cache` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:sleepless_qa/healer/run_log` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:sleepless_qa/heartbeat` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:sleepless_qa/verdict/__init__` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:sleepless_qa/verdict/contract` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:sleepless_qa/verdict/engine` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:sleepless_qa/verdict/log_pattern` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:sleepless_qa/verdict/schema` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:sleepless_qa/verdict/visual` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:sqi/__init__` | reachability | **WIRED-BUT-SILENT** | unreachable; declared SCHEDULED |
| `module:sqi/baseline_guardian` | reachability | **WIRED-BUT-SILENT** | unreachable; declared SCHEDULED |
| `module:sqi/environment_qualifier` | reachability | **WIRED-BUT-SILENT** | unreachable; declared SCHEDULED |
| `module:sqi/reconcile` | reachability | **WIRED-BUT-SILENT** | unreachable; declared SCHEDULED |
| `module:sqi/redteam_protocol` | reachability | **WIRED-BUT-SILENT** | unreachable; declared SCHEDULED |
| `module:sqi/repo_reality_scanner` | reachability | **WIRED-BUT-SILENT** | unreachable; declared SCHEDULED |
| `module:sqi/weakening_baseline` | reachability | **WIRED-BUT-SILENT** | unreachable; declared SCHEDULED |
| `module:sqi/weakening_detectors` | reachability | **WIRED-BUT-SILENT** | unreachable; declared SCHEDULED |
| `module:sweep_enforcer/__init__` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:sweep_enforcer/rule_sweep` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:uqf/gates` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:wrapper/__init__` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:wrapper/auto_resumer` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:wrapper/cost_gate` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:wrapper/prelaunch` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:wrapper/repo_coordinator` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:wrapper/session_namer` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:wrapper/turn_counter` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `module:wrapper/verify_before_emit` | reachability | **WIRED-BUT-SILENT** | unreachable; declared LIBRARY |
| `pm-03-bus` | pm-bus | **WIRED-BUT-SILENT** | 13 producer file(s); consumer is the SessionStart hub read but emits no 'pm03_consume' signal -- consumption unmeasured |
| `sqi-runner` | audits | **WIRED-BUT-SILENT** | newest sqi_report_2026-07-12.md 239.9h ago (> 36h -- quiet) |
| `drk-kernel` | decision-registry | **LIVE** | records.jsonl 22.1h ago (<= 36h) |
| `fd-07-flywheel` | stop-chain | **LIVE** | 918 signals, freshest 0.2h ago (<= 36h) |
| `fios-token-irr` | stop-chain | **LIVE** | 871 signals, freshest 0.2h ago (<= 36h) |
| `hook-dispatcher` | hooks-dir | **LIVE** | in sync (sha256 778f8d08f08a) |
| `module:ads/__init__` | reachability | **LIVE** | reached from package-init of ads/doc_updater |
| `module:ads/detector` | reachability | **LIVE** | reached from tools/ads_backfill.py |
| `module:ads/doc_generator` | reachability | **LIVE** | reached from tools/ads_backfill.py |
| `module:ads/doc_updater` | reachability | **LIVE** | reached from tools/ads_sync.py |
| `module:akos_knowledge/__init__` | reachability | **LIVE** | reached from package-init of akos_knowledge/akos |
| `module:akos_knowledge/akos` | reachability | **LIVE** | reached from tools/jit_skill_loader.py |
| `module:arch-decision/__init__` | reachability | **LIVE** | reached from package-init of arch-decision/build_index |
| `module:arch-decision/arch_check` | reachability | **LIVE** | reached from commands/arch-decision.md |
| `module:arch-decision/build_index` | reachability | **LIVE** | reached from commands/arch-decision.md |
| `module:auto-testing/__init__` | reachability | **LIVE** | reached from package-init of auto-testing/generators/__init__ |
| `module:auto-testing/auto_test` | reachability | **LIVE** | reached from hooks/auto-test-gate.js |
| `module:auto-testing/generators/__init__` | reachability | **LIVE** | reached from commands/auto-test.md |
| `module:auto-testing/vault_io` | reachability | **LIVE** | reached from commands/auto-test.md |
| `module:backlog_autopilot/__init__` | reachability | **LIVE** | reached from commands/what-now.md |
| `module:backlog_autopilot/engine` | reachability | **LIVE** | reached from CLAUDE.md |
| `module:backup/__init__` | reachability | **LIVE** | reached from package-init of backup/backup |
| `module:backup/backup` | reachability | **LIVE** | reached from commands/backup.md |
| `module:cascade_prevention/__init__` | reachability | **LIVE** | reached from package-init of cascade_prevention/dangerous_cmds |
| `module:cascade_prevention/blocker` | reachability | **LIVE** | reached from modules/cascade_prevention/__init__ |
| `module:cascade_prevention/dangerous_cmds` | reachability | **LIVE** | reached from hooks/cascade_check_bash.js |
| `module:cascade_prevention/engine` | reachability | **LIVE** | reached from hooks/cascade_check_bash.js |
| `module:cascade_prevention/surfaces` | reachability | **LIVE** | reached from modules/cascade_prevention/__init__ |
| `module:cascade_prevention/types` | reachability | **LIVE** | reached from modules/cascade_prevention/__init__ |
| `module:cdio/__init__` | reachability | **LIVE** | reached from live:cdio-core.md |
| `module:cdio/bus_bridge` | reachability | **LIVE** | reached from live:cdio-core.md |
| `module:cdio/scorer` | reachability | **LIVE** | reached from live:cdio-reviewer.md |
| `module:cdio/telemetry` | reachability | **LIVE** | reached from modules/cognitive_os/co_12_telemetry |
| `module:code-review/__init__` | reachability | **LIVE** | reached from package-init of code-review/code_reviewer |
| `module:code-review/code_reviewer` | reachability | **LIVE** | reached from commands/code-review.md |
| `module:code-review/test_closed_loop` | reachability | **LIVE** | reached from modules/code-review/code_reviewer |
| `module:code-review/test_combined_gate` | reachability | **LIVE** | reached from modules/code-review/code_reviewer |
| `module:code-review/test_v_block` | reachability | **LIVE** | reached from modules/code-review/code_reviewer |
| `module:code_review/__init__` | reachability | **LIVE** | reached from live:pp-code-reviewer.md |
| `module:cognitive_os/__init__` | reachability | **LIVE** | reached from package-init of cognitive_os/co_12_telemetry |
| `module:cognitive_os/co_12_telemetry` | reachability | **LIVE** | reached from tools/jit_skill_loader.py |
| `module:cognitive_os/hibernation` | reachability | **LIVE** | reached from modules/cognitive_os/process_governor |
| `module:cognitive_os/process_governor` | reachability | **LIVE** | reached from CLAUDE.md |
| `module:cognitive_os/registry` | reachability | **LIVE** | reached from modules/cognitive_os/router |
| `module:cognitive_os/router` | reachability | **LIVE** | reached from modules/cognitive_os/co_12_telemetry |
| `module:cognitive_os/scheduler` | reachability | **LIVE** | reached from modules/cognitive_os/process_governor |
| `module:cost_collapse/__init__` | reachability | **LIVE** | reached from package-init of cost_collapse/router |
| `module:cost_collapse/router` | reachability | **LIVE** | reached from CLAUDE.md |
| `module:cpc_os/__init__` | reachability | **LIVE** | reached from hooks/session_start_hub.js |
| `module:cpc_os/auto_reset_orchestrator` | reachability | **LIVE** | reached from commands/auto-reset.md |
| `module:cpc_os/backlog` | reachability | **LIVE** | reached from modules/cpc_os/__init__ |
| `module:cpc_os/beacon` | reachability | **LIVE** | reached from hooks/session_start_hub.js |
| `module:cpc_os/context_monitor` | reachability | **LIVE** | reached from commands/auto-reset.md |
| `module:cpc_os/handoff` | reachability | **LIVE** | reached from modules/cpc_os/__init__ |
| `module:cpc_os/heartbeat` | reachability | **LIVE** | reached from modules/cpc_os/snapshot |
| `module:cpc_os/recovery` | reachability | **LIVE** | reached from modules/cpc_os/__init__ |
| `module:cpc_os/registry` | reachability | **LIVE** | reached from hooks/session_start_hub.js |
| `module:cpc_os/restart` | reachability | **LIVE** | reached from modules/cpc_os/__init__ |
| `module:cpc_os/router` | reachability | **LIVE** | reached from modules/cpc_os/__init__ |
| `module:cpc_os/snapshot` | reachability | **LIVE** | reached from hooks/session_start_hub.js |
| `module:cpc_os/switch` | reachability | **LIVE** | reached from modules/cpc_os/__init__ |
| `module:cpc_os/topology_reconcile` | reachability | **LIVE** | reached from modules/cpc_os/vscode_autorun |
| `module:cpc_os/vscode_autorun` | reachability | **LIVE** | reached from commands/restore-panes.md |
| `module:cpc_os/work_state_saver` | reachability | **LIVE** | reached from commands/auto-reset.md |
| `module:deployment/__init__` | reachability | **LIVE** | reached from package-init of deployment/healthcheck |
| `module:deployment/deploy` | reachability | **LIVE** | reached from commands/deploy.md |
| `module:deployment/healthcheck` | reachability | **LIVE** | reached from commands/rollback.md |
| `module:duplicate_to_advantage/__init__` | reachability | **LIVE** | reached from package-init of duplicate_to_advantage/d2a_engine |
| `module:duplicate_to_advantage/d2a_engine` | reachability | **LIVE** | reached from hooks/d2a_gate.js |
| `module:error_prevention/__init__` | reachability | **LIVE** | reached from package-init of error_prevention/premise_verifier |
| `module:error_prevention/premise_verifier` | reachability | **LIVE** | reached from CLAUDE.md |
| `module:fable_distillation/__init__` | reachability | **LIVE** | reached from package-init of fable_distillation/epistemic_ladder |
| `module:fable_distillation/epistemic_ladder` | reachability | **LIVE** | reached from modules/cognitive_os/co_12_telemetry |
| `module:fable_distillation/fd_04_prover` | reachability | **LIVE** | reached from modules/fable_distillation/epistemic_ladder |
| `module:fable_distillation/fd_07_flywheel` | reachability | **LIVE** | reached from hooks/hook-dispatcher.js |
| `module:fable_distillation/federated_ledger` | reachability | **LIVE** | reached from modules/frontier_intelligence/token_irr |
| `module:frontier_intelligence/__init__` | reachability | **LIVE** | reached from package-init of frontier_intelligence/question_harvester |
| `module:frontier_intelligence/evolution_engine` | reachability | **LIVE** | reached from modules/duplicate_to_advantage/d2a_engine |
| `module:frontier_intelligence/question_harvester` | reachability | **LIVE** | reached from modules/akos_knowledge/__init__ |
| `module:frontier_intelligence/token_irr` | reachability | **LIVE** | reached from hooks/hook-dispatcher.js |
| `module:graphify/__init__` | reachability | **LIVE** | reached from package-init of graphify/session_writeback |
| `module:graphify/global_store` | reachability | **LIVE** | reached from modules/graphify/indexer |
| `module:graphify/indexer` | reachability | **LIVE** | reached from hooks/graph_first_gate.js |
| `module:graphify/session_writeback` | reachability | **LIVE** | reached from hooks/hook-dispatcher.js |
| `module:hard_rules/__init__` | reachability | **LIVE** | reached from package-init of hard_rules/writer |
| `module:hard_rules/extractor` | reachability | **LIVE** | reached from tools/bug_to_hardrule.py |
| `module:hard_rules/writer` | reachability | **LIVE** | reached from tools/bug_to_hardrule.py |
| `module:liveness/__init__` | reachability | **LIVE** | reached from package-init of liveness/reachability |
| `module:liveness/liveness_ledger` | reachability | **LIVE** | reached from commands/liveness.md |
| `module:liveness/reachability` | reachability | **LIVE** | reached from commands/liveness.md |
| `module:monitoring/__init__` | reachability | **LIVE** | reached from commands/revenue-ready.md |
| `module:monitoring/monitor` | reachability | **LIVE** | reached from modules/uqf/auditor |
| `module:monitoring/observe` | reachability | **LIVE** | reached from live:pp-monitor.md |
| `module:one_shot/__init__` | reachability | **LIVE** | reached from commands/one-shot-compile.md |
| `module:one_shot/compiler` | reachability | **LIVE** | reached from commands/one-shot-compile.md |
| `module:one_shot/escalation` | reachability | **LIVE** | reached from CLAUDE.md |
| `module:one_shot/lock` | reachability | **LIVE** | reached from CLAUDE.md |
| `module:osa/__init__` | reachability | **LIVE** | reached from package-init of osa/dispatcher |
| `module:osa/dispatcher` | reachability | **LIVE** | reached from live:omni-singularity.md |
| `module:osa/gpu_eyes` | reachability | **LIVE** | reached from live:omni-singularity.md |
| `module:osa/never_again` | reachability | **LIVE** | reached from live:omni-singularity.md |
| `module:osa/osa_command` | reachability | **LIVE** | reached from modules/osa/dispatcher |
| `module:osa/throttle` | reachability | **LIVE** | reached from live:omni-singularity.md |
| `module:output_contracts/__init__` | reachability | **LIVE** | reached from package-init of output_contracts/validator |
| `module:output_contracts/validator` | reachability | **LIVE** | reached from CLAUDE.md |
| `module:owner_queue/__init__` | reachability | **LIVE** | reached from hooks/session_start_hub.js |
| `module:owner_queue/owner_queue` | reachability | **LIVE** | reached from hooks/session_start_hub.js |
| `module:parallel_mesh/__init__` | reachability | **LIVE** | reached from modules/cdio/bus_bridge |
| `module:parallel_mesh/pm_03_bus` | reachability | **LIVE** | reached from modules/cdio/bus_bridge |
| `module:pp_agents/__init__` | reachability | **LIVE** | reached from package-init of pp_agents/proactive_dispatcher |
| `module:pp_agents/proactive_core` | reachability | **LIVE** | reached from hooks/bug-hunter-ceps-bridge.js |
| `module:pp_agents/proactive_dispatcher` | reachability | **LIVE** | reached from tools/jit_skill_loader.py |
| `module:pp_agents/signals/__init__` | reachability | **LIVE** | reached from modules/pp_agents/proactive_dispatcher |
| `module:pp_agents/signals/cascade` | reachability | **LIVE** | reached from live:pp-cascade-guard.md |
| `module:pp_agents/signals/code_quality` | reachability | **LIVE** | reached from hooks/uqf_pre_edit_gate.js |
| `module:pp_agents/signals/error_recurrence` | reachability | **LIVE** | reached from live:pp-error-analyst.md |
| `module:pp_agents/signals/premise_risk` | reachability | **LIVE** | reached from live:pp-premise-guardian.md |
| `module:pp_agents/signals/spec_compliance` | reachability | **LIVE** | reached from live:pp-spec-guardian.md |
| `module:recall_roi/__init__` | reachability | **LIVE** | reached from package-init of recall_roi/recall_roi |
| `module:recall_roi/recall_roi` | reachability | **LIVE** | reached from modules/cognitive_os/co_12_telemetry |
| `module:rollback/__init__` | reachability | **LIVE** | reached from modules/monitoring/observe |
| `module:rollback/rollback` | reachability | **LIVE** | reached from commands/rollback.md |
| `module:rollback/test_v_block` | reachability | **LIVE** | reached from modules/deployment/deploy |
| `module:rule_compiler/__init__` | reachability | **LIVE** | reached from tools/hardrule_compile.py |
| `module:rule_compiler/compiler` | reachability | **LIVE** | reached from tools/hardrule_compile.py |
| `module:rule_compiler/digest` | reachability | **LIVE** | reached from tools/hardrule_compile.py |
| `module:rule_compiler/parser` | reachability | **LIVE** | reached from modules/rule_compiler/compiler |
| `module:rule_compiler/schema` | reachability | **LIVE** | reached from modules/rule_compiler/digest |
| `module:sdd_os/__init__` | reachability | **LIVE** | reached from package-init of sdd_os/prd_generator |
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
| `module:setup_os/__init__` | reachability | **LIVE** | reached from package-init of setup_os/secure_installer |
| `module:setup_os/backlog_generator` | reachability | **LIVE** | reached from commands/setup-backlog.md |
| `module:setup_os/drift_detector` | reachability | **LIVE** | reached from commands/setup-drift.md |
| `module:setup_os/registry` | reachability | **LIVE** | reached from modules/setup_os/scanner |
| `module:setup_os/roi_analyzer` | reachability | **LIVE** | reached from commands/analyze-roi.md |
| `module:setup_os/scanner` | reachability | **LIVE** | reached from commands/scan-repo.md |
| `module:setup_os/secure_installer` | reachability | **LIVE** | reached from commands/setup-repo.md |
| `module:skill_router/__init__` | reachability | **LIVE** | reached from package-init of skill_router/skill_index |
| `module:skill_router/intent_classifier` | reachability | **LIVE** | reached from tools/jit_skill_loader.py |
| `module:skill_router/skill_index` | reachability | **LIVE** | reached from tools/jit_skill_loader.py |
| `module:spec_gate/__init__` | reachability | **LIVE** | reached from package-init of spec_gate/gate |
| `module:spec_gate/gate` | reachability | **LIVE** | reached from CLAUDE.md |
| `module:uqf/__init__` | reachability | **LIVE** | reached from package-init of uqf/auditor |
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
