# Manual Tools Audit -- 2026-06-01T13-16-21Z

**Generado:** 2026-06-01 13:16 UTC  
**Scope:** repo claude-power-pack + escaneo de proyectos/apps accesibles del Owner  
**Proposito:** identificar herramientas que hoy requieren invocacion manual y el mecanismo PP concreto que las automatizaria.  
**Metodo:** clasificador deterministico `tools/_manual_tools_audit.py` (AST/regex sobre 295 .py; cruce contra `~/.claude/settings.json` + `agents/` + `commands/` + hooks).

## RESUMEN EJECUTIVO

| Categoria | Conteo |
|-----------|--------|
| Archivos .py escaneados (tools/ + modules/) | 295 |
| Tools con entry-point CLI | 165 |
| Ya automatizados (en hooks/agents/commands) | 58 |
| Tests / dunder privados (excluidos) | 70 |
| **Manuales (no auto-disparados)** | **107** |
| -- de esos, ORPHAN (sin caller, candidatos reales) | 58 |
| -- SUB-INVOKED (ya alcanzables via parent/slash-cmd) | 18 |
| -- ONE-TIME SETUP (no deben automatizarse) | 7 |
| -- VPS-RESIDENT (corren server-side) | 4 |
| -- DEV/BENCH (ad-hoc, automatizacion bajo valor) | 20 |

**Reparto por mecanismo de automatizacion (todos los manuales):**

| Mecanismo | Conteo |
|-----------|--------|
| A - Hook automatico (settings.json event) | 35 |
| C - Agente global (~/.claude/agents) | 30 |
| B - Signal proactiva (proactive_dispatcher / SessionStart) | 19 |
| F - Task Scheduler / cron daemon | 12 |
| D - jit_skill_loader trigger (intent semantico) | 11 |

> **Lectura honesta:** de las 107 manuales, solo las **ORPHAN** son automatizables-netas. Las SUB-INVOKED ya corren al disparar su parent (`verify_spp.py`, `/osa`, modulo backup). Las ONE-TIME SETUP deben quedarse manuales por diseno (automatizarlas = re-ejecucion destructiva). Las VPS-RESIDENT viven en el VPS, no en este host.

## QUICK WINS (ORPHAN, impacto Alto, esfuerzo <= 20 LOC, ordenado por ROI)

| # | Herramienta | Que hace | Invocacion manual hoy | Mecanismo | Esfuerzo |
|---|-------------|----------|------------------------|-----------|----------|
| 1 | `cache_hint_apply` | cache_hint_apply.py - In-repo consumer for vault/cache_hints/. | `python tools/cache_hint_apply.py --quiet --as-json` | A | 20 LOC |
| 2 | `check_hook_status` | PP Hook Status -- real-time activation snapshot. | `python tools/check_hook_status.py` | A | 20 LOC |
| 3 | `compact_hang_detector` | Compact Hang Detector -- PP BL-COMPACT-001. | `python tools/compact_hang_detector.py --interactive --snooze-seconds --dry-notify` | F | 20 LOC |
| 4 | `compound_audit` | compound_audit.py - health check for the Compound Learnings stack. | `python tools/compound_audit.py` | A | 20 LOC |
| 5 | `drift_report` | drift_report.py — gap-6 fix: classify PP↔loose mirror pairs. | `python tools/drift_report.py` | A | 20 LOC |
| 6 | `jit_ref_correlate` | jit_ref_correlate.py — Stop-hook: did the agent USE what JIT injected? | `python tools/jit_ref_correlate.py` | F | 20 LOC |
| 7 | `lazarus_orphan_purge` | lazarus_orphan_purge.py - retire .jsonl.live orphans across all projec | `python tools/lazarus_orphan_purge.py --project --apply --json` | A | 20 LOC |
| 8 | `miner_v2` | miner_v2.py — Total Recall: jsonl + Cursor SQLite + clustering + visio | `python tools/miner_v2.py` | F | 20 LOC |
| 9 | `normalize_paths` | normalize_paths.py — Gap-2 (path) + Gap-10 (extended secret-scan) audi | `python tools/normalize_paths.py --check --apply --paths-only` | F | 20 LOC |
| 10 | `oracle_heartbeat` | oracle_heartbeat.py — Runtime Handshake Probe (MC-OVO-90). | `python tools/oracle_heartbeat.py --project --out --pid` | F | 20 LOC |
| 11 | `resume_reindex` | resume_reindex.py - native /resume chronology health scan + repair. | `python tools/resume_reindex.py --repair` | A | 20 LOC |
| 12 | `session-snapshot` | session-snapshot.py — Layer 3 of SESSION_SAFETY_CONTRACT.md. | `python tools/session-snapshot.py` | A | 20 LOC |
| 13 | `sovereign_miner` | sovereign_miner.py — 4-pillar repo/transcript distillation. | `python tools/sovereign_miner.py` | F | 20 LOC |
| 14 | `vault_summarize` | vault_summarize.py — Knowledge Vault Self-Optimization (MC-OVO-36) | `python tools/vault_summarize.py --project --top --check` | A | 20 LOC |

## AUTOMATIZACIONES MEDIANAS (resto de ORPHAN, 20-50 LOC)

| Herramienta | Que hace | Invocacion manual hoy | Mecanismo | Esfuerzo | Impacto |
|-------------|----------|------------------------|-----------|----------|---------|
| `build_index` | build_index.py -- Architecture Decision Skill index builder. | `python modules/arch-decision/build_index.py` | A | 20 LOC | Medio |
| `llm_bridge` | LLM bridge for the Auto-Testing Skill — claude.exe -p via STDIN. | `python modules/auto-testing/llm_bridge.py` | A | 20 LOC | Medio |
| `research_discovery` | research_discovery.py — SessionStart auto-discovery for deep-research. | `python modules/deep-research/research_discovery.py` | A | 20 LOC | Medio |
| `query_telemetry` | OmniCapture — Query Telemetry CLI. | `python modules/omnicapture/query_telemetry.py --project --since --severity` | B | 30 LOC | Alto |
| `chatgpt_distiller` | chatgpt-distiller — Extract vision, decisions, and preferences from Ch | `python tools/chatgpt_distiller.py <distill\|rebuild\|scan\|update> --top --verbose --dry-run` | A | 20 LOC | Medio |
| `e2e_clean_install` | e2e_clean_install.py — E1 clean-machine verification. | `python tools/e2e_clean_install.py --keep-sandbox` | A | 20 LOC | Medio |
| `memory_manager` | Memory Manager — Hot/Cold context splitter for session handoff files. | `python tools/memory_manager.py --file --dry-run` | B | 30 LOC | Alto |
| `rtk_savings_export` | rtk_savings_export.py — thin, decoupled JSON exporter of RTK savings. | `python tools/rtk_savings_export.py` | A | 20 LOC | Medio |
| `skill_heat_map_indexer` | Skill semantic heat-map indexer (BL-0016 / MC-SYS-27). | `python tools/skill_heat_map_indexer.py --dry-run --query --out` | A | 20 LOC | Medio |
| `arch_check` | arch_check.py -- Architecture Decision Skill verdict engine. | `python modules/arch-decision/arch_check.py --fast --deep --budget` | B | 30 LOC | Medio |
| `cross_signal_bus` | Cross-signal bus for autoresearch. | `python modules/autoresearch/cross_signal_bus.py` | B | 30 LOC | Medio |
| `nightcrawler` | Nightcrawler v2 -- Autoresearch orchestrator. | `python modules/autoresearch/nightcrawler.py` | B | 30 LOC | Medio |
| `rss_sniffer` | RSS feed poller for autoresearch. | `python modules/autoresearch/rss_sniffer.py` | B | 30 LOC | Medio |
| `youtube_firehose` | YouTube channel poller for autoresearch. | `python modules/autoresearch/youtube_firehose.py` | B | 30 LOC | Medio |
| `append_memory` | Claude Power Pack — Memory Engine | `python modules/memory-engine/append_memory.py` | B | 30 LOC | Medio |
| `session_cost_estimator` | Session Cost Estimator - Estimate token overhead per session based on  | `python modules/token-optimizer/session_cost_estimator.py --tier --project-dir` | B | 30 LOC | Medio |
| `atomic_branding` | atomic_branding.py - brand prompt -> Tailwind + Framer-Motion tokens. | `python tools/atomic_branding.py --brand --out --report` | B | 30 LOC | Medio |
| `bulk_vault_extract` | BL-0052 — Bulk vault extraction for projects under a root path. | `python tools/bulk_vault_extract.py` | B | 30 LOC | Medio |
| `claudemd_linter` | CLAUDE.md Linter - Find, measure, and optionally compress CLAUDE.md fi | `python modules/token-optimizer/claudemd_linter.py --scan-dir --global-file --max-words` | C | 50 LOC | Alto |
| `token_autopsy` | Claude Power Pack — Token Forensics: Burn Report (Part R) | `python modules/token-optimizer/token_autopsy.py --session --output --top` | C | 50 LOC | Alto |
| `lazarus_post_reboot_arm` | lazarus_post_reboot_arm.py - sanitize Lazarus state once per logon (BL | `python tools/lazarus_post_reboot_arm.py --dry-run --force --strict` | C | 50 LOC | Alto |
| `lost_chat_recovery` | lost_chat_recovery.py — safe probe for "lost" Claude session jsonls (B | `python tools/lost_chat_recovery.py --cwd --force-after-merge --json` | C | 50 LOC | Alto |
| `setup_schedule` | Cross-platform scheduler for autoresearch nightcrawler. | `python modules/autoresearch/setup_schedule.py --uninstall --status` | D | 40 LOC | Medio |
| `absorb_apollo_skills` | absorb_apollo_skills.py — vendor apollographql/skills into the Power P | `python tools/absorb_apollo_skills.py --refresh` | D | 40 LOC | Medio |
| `bulk_kg_deploy` | BL-0054 — Bulk KG deploy via kobi_graphify.py. | `python tools/bulk_kg_deploy.py` | D | 40 LOC | Medio |
| `cascade_populate_js` | cascade_populate_js.py — JavaScript cascade populator (MC-OVO-107). | `python tools/cascade_populate_js.py --project --write --json` | D | 40 LOC | Medio |
| `gh_skill_scanner` | gh skill scanner (sin docstring; ver fuente) | `python tools/gh_skill_scanner.py --limit --filenames --out-raw` | D | 40 LOC | Medio |
| `obsidian_enrich` | Obsidian Enrich — Add inline [[wikilinks]] to knowledge vault body tex | `python tools/obsidian_enrich.py --vault --apply` | D | 40 LOC | Medio |
| `plugin_skill_scanner` | plugin skill scanner (sin docstring; ver fuente) | `python tools/plugin_skill_scanner.py --out --summary` | D | 40 LOC | Medio |
| `skills_index_merge` | skills index merge (sin docstring; ver fuente) | `python tools/skills_index_merge.py --out` | D | 40 LOC | Medio |
| `vault_indexer` | Knowledge Vault Indexer (MC-KNB-01) | `python tools/vault_indexer.py` | D | 40 LOC | Medio |
| `query_lightning` | Agent Lightning — Query Client for Claude Code. | `python modules/agent-lightning/query_lightning.py --suggestions --patterns --model-stats` | C | 50 LOC | Medio |
| `vision_scorer` | Vision Scorer — Score video frames for architectural/RE value. | `python modules/autoresearch/vision_scorer.py --frames-dir --max-frames --output` | C | 50 LOC | Medio |
| `whisper_bridge` | Whisper Bridge — Audio transcription with graceful degradation. | `python modules/autoresearch/whisper_bridge.py --audio --output` | C | 50 LOC | Medio |
| `query_infra` | Kobii Infrastructure — Unified VPS System Query. | `python modules/infrastructure/query_infra.py --status --aadef --resilience` | C | 50 LOC | Medio |
| `cross_project_dedup` | Cross-Project Dedup - Find duplicate rules across CLAUDE.md files in m | `python modules/token-optimizer/cross_project_dedup.py --scan-dir --threshold` | C | 50 LOC | Medio |
| `executionos_compressor` | ExecutionOS Compressor - Parses markdown prompts, scores sections by u | `python modules/token-optimizer/executionos_compressor.py --compress` | C | 50 LOC | Medio |
| `prompt_pattern_optimizer` | Prompt Pattern Optimizer - Find repeated 4-grams across CLAUDE.md file | `python modules/token-optimizer/prompt_pattern_optimizer.py --scan-dir --min-projects --ngram-size` | C | 50 LOC | Medio |
| `baseline_ledger_append` | baseline ledger append (sin docstring; ver fuente) | `python tools/baseline_ledger_append.py --law --evidence --trigger` | C | 50 LOC | Medio |
| `check_playwright_mcp` | Playwright MCP Plugin Health Check -- PP BL-PLAYWRIGHT-001 (Option A). | `python tools/check_playwright_mcp.py` | C | 50 LOC | Medio |
| `mistake_frequency` | Mistake Frequency Counter — closes the Mistakes→Curriculum loop. | `python tools/mistake_frequency.py --show --top --increment` | C | 50 LOC | Medio |
| `mydeepchat_skill_scanner` | mydeepchat skill scanner (sin docstring; ver fuente) | `python tools/mydeepchat_skill_scanner.py --page-size --no-prompt --out-raw` | C | 50 LOC | Medio |
| `rtk_corpus` | rtk_corpus.py — build a deterministic, frequency-weighted RTK benchmar | `python tools/rtk_corpus.py --limit --out` | C | 50 LOC | Medio |
| `topology_apply` | topology apply (sin docstring; ver fuente) | `python tools/topology_apply.py --dry-run --i-have-no-open-windows --search-roots` | C | 50 LOC | Medio |

## REQUIEREN DECISION OWNER (no automatizar sin tradeoff explicito)

| Herramienta | Status | Por que NO auto-disparar | Invocacion manual |
|-------------|--------|--------------------------|-------------------|
| `migrate` | ONE-TIME SETUP | Setup unico; re-ejecucion = mutacion no deseada | `python modules/executionos-lite/migrate.py --verify` |
| `install_adapter` | ONE-TIME SETUP | Setup unico; re-ejecucion = mutacion no deseada | `python modules/omnicapture/install_adapter.py --dolphin-log --follow --type` |
| `init_engine` | VPS-RESIDENT | Corre en el VPS (204.168.166.63), no en este host Windows | `python modules/omnicapture/vps/init_engine.py --deep --force --json` |
| `crash_receiver` | VPS-RESIDENT | Corre en el VPS (204.168.166.63), no en este host Windows | `python modules/zero-crash/vps/crash_receiver.py --config --port` |
| `fork_storm_migration_2026-05-21` | ONE-TIME SETUP | Setup unico; re-ejecucion = mutacion no deseada | `python tools/fork_storm_migration_2026-05-21.py` |
| `lazarus_topology_daemon` | VPS-RESIDENT | Corre en el VPS (204.168.166.63), no en este host Windows | `python tools/lazarus_topology_daemon.py <loop\|start\|status\|stop> --interval` |
| `lazarus_topology_push_vps` | VPS-RESIDENT | Corre en el VPS (204.168.166.63), no en este host Windows | `python tools/lazarus_topology_push_vps.py --host --key --remote-dir` |
| `migrate_to_hub` | ONE-TIME SETUP | Setup unico; re-ejecucion = mutacion no deseada | `python tools/migrate_to_hub.py --dry-run` |
| `optimize_session_start` | ONE-TIME SETUP | Setup unico; re-ejecucion = mutacion no deseada | `python tools/optimize_session_start.py --dry-run` |
| `register_global_hooks` | ONE-TIME SETUP | Setup unico; re-ejecucion = mutacion no deseada | `python tools/register_global_hooks.py --dry-run` |
| `rtk_install` | ONE-TIME SETUP | Setup unico; re-ejecucion = mutacion no deseada | `python tools/rtk_install.py` |

> Las **DEV/BENCH** (20) tampoco se recomiendan para auto-disparo: son harnesses ad-hoc (probes, benchmarks, scaffolders, e2e) que se corren en un gate o una sola vez. Forzar un trigger anadiria ruido sin valor operativo.

## MATRIZ COMPLETA (107 herramientas manuales)

| Herramienta | Repo | Que hace | Invocacion manual exacta | Mec | Esfuerzo | Impacto | Status |
|-------------|------|----------|--------------------------|-----|----------|---------|--------|
| `modules/agent-lightning/query_lightning.py` | PP | Agent Lightning — Query Client for Claude Code. | `python modules/agent-lightning/query_lightning.py --suggestions --patterns --model-stats` | C | 50 LOC | Medio | ORPHAN |
| `modules/arch-decision/arch_check.py` | PP | arch_check.py -- Architecture Decision Skill verdict engine. | `python modules/arch-decision/arch_check.py --fast --deep --budget` | B | 30 LOC | Medio | ORPHAN |
| `modules/arch-decision/build_index.py` | PP | build_index.py -- Architecture Decision Skill index builder. | `python modules/arch-decision/build_index.py` | A | 20 LOC | Medio | ORPHAN |
| `modules/auto-testing/llm_bridge.py` | PP | LLM bridge for the Auto-Testing Skill — claude.exe -p via STDIN. | `python modules/auto-testing/llm_bridge.py` | A | 20 LOC | Medio | ORPHAN |
| `modules/autoresearch/cross_signal_bus.py` | PP | Cross-signal bus for autoresearch. | `python modules/autoresearch/cross_signal_bus.py` | B | 30 LOC | Medio | ORPHAN |
| `modules/autoresearch/nightcrawler.py` | PP | Nightcrawler v2 -- Autoresearch orchestrator. | `python modules/autoresearch/nightcrawler.py` | B | 30 LOC | Medio | ORPHAN |
| `modules/autoresearch/rss_sniffer.py` | PP | RSS feed poller for autoresearch. | `python modules/autoresearch/rss_sniffer.py` | B | 30 LOC | Medio | ORPHAN |
| `modules/autoresearch/setup_schedule.py` | PP | Cross-platform scheduler for autoresearch nightcrawler. | `python modules/autoresearch/setup_schedule.py --uninstall --status` | D | 40 LOC | Medio | ORPHAN |
| `modules/autoresearch/vision_scorer.py` | PP | Vision Scorer — Score video frames for architectural/RE value. | `python modules/autoresearch/vision_scorer.py --frames-dir --max-frames --output` | C | 50 LOC | Medio | ORPHAN |
| `modules/autoresearch/whisper_bridge.py` | PP | Whisper Bridge — Audio transcription with graceful degradation. | `python modules/autoresearch/whisper_bridge.py --audio --output` | C | 50 LOC | Medio | ORPHAN |
| `modules/autoresearch/youtube_firehose.py` | PP | YouTube channel poller for autoresearch. | `python modules/autoresearch/youtube_firehose.py` | B | 30 LOC | Medio | ORPHAN |
| `modules/deep-research/research_discovery.py` | PP | research_discovery.py — SessionStart auto-discovery for deep-research. | `python modules/deep-research/research_discovery.py` | A | 20 LOC | Medio | ORPHAN |
| `modules/infrastructure/query_infra.py` | PP | Kobii Infrastructure — Unified VPS System Query. | `python modules/infrastructure/query_infra.py --status --aadef --resilience` | C | 50 LOC | Medio | ORPHAN |
| `modules/memory-engine/append_memory.py` | PP | Claude Power Pack — Memory Engine | `python modules/memory-engine/append_memory.py` | B | 30 LOC | Medio | ORPHAN |
| `modules/omnicapture/query_telemetry.py` | PP | OmniCapture — Query Telemetry CLI. | `python modules/omnicapture/query_telemetry.py --project --since --severity` | B | 30 LOC | Alto | ORPHAN |
| `modules/token-optimizer/claudemd_linter.py` | PP | CLAUDE.md Linter - Find, measure, and optionally compress CLAUDE.md files across projects. | `python modules/token-optimizer/claudemd_linter.py --scan-dir --global-file --max-words` | C | 50 LOC | Alto | ORPHAN |
| `modules/token-optimizer/cross_project_dedup.py` | PP | Cross-Project Dedup - Find duplicate rules across CLAUDE.md files in multiple projects. | `python modules/token-optimizer/cross_project_dedup.py --scan-dir --threshold` | C | 50 LOC | Medio | ORPHAN |
| `modules/token-optimizer/executionos_compressor.py` | PP | ExecutionOS Compressor - Parses markdown prompts, scores sections by universality tier, co | `python modules/token-optimizer/executionos_compressor.py --compress` | C | 50 LOC | Medio | ORPHAN |
| `modules/token-optimizer/prompt_pattern_optimizer.py` | PP | Prompt Pattern Optimizer - Find repeated 4-grams across CLAUDE.md files to identify token  | `python modules/token-optimizer/prompt_pattern_optimizer.py --scan-dir --min-projects --ngram-size` | C | 50 LOC | Medio | ORPHAN |
| `modules/token-optimizer/session_cost_estimator.py` | PP | Session Cost Estimator - Estimate token overhead per session based on tier and project con | `python modules/token-optimizer/session_cost_estimator.py --tier --project-dir` | B | 30 LOC | Medio | ORPHAN |
| `modules/token-optimizer/token_autopsy.py` | PP | Claude Power Pack — Token Forensics: Burn Report (Part R) | `python modules/token-optimizer/token_autopsy.py --session --output --top` | C | 50 LOC | Alto | ORPHAN |
| `tools/absorb_apollo_skills.py` | PP | absorb_apollo_skills.py — vendor apollographql/skills into the Power Pack. | `python tools/absorb_apollo_skills.py --refresh` | D | 40 LOC | Medio | ORPHAN |
| `tools/atomic_branding.py` | PP | atomic_branding.py - brand prompt -> Tailwind + Framer-Motion tokens. | `python tools/atomic_branding.py --brand --out --report` | B | 30 LOC | Medio | ORPHAN |
| `tools/baseline_ledger_append.py` | PP | baseline ledger append (sin docstring; ver fuente) | `python tools/baseline_ledger_append.py --law --evidence --trigger` | C | 50 LOC | Medio | ORPHAN |
| `tools/bulk_kg_deploy.py` | PP | BL-0054 — Bulk KG deploy via kobi_graphify.py. | `python tools/bulk_kg_deploy.py` | D | 40 LOC | Medio | ORPHAN |
| `tools/bulk_vault_extract.py` | PP | BL-0052 — Bulk vault extraction for projects under a root path. | `python tools/bulk_vault_extract.py` | B | 30 LOC | Medio | ORPHAN |
| `tools/cache_hint_apply.py` | PP | cache_hint_apply.py - In-repo consumer for vault/cache_hints/. | `python tools/cache_hint_apply.py --quiet --as-json` | A | 20 LOC | Alto | ORPHAN |
| `tools/cascade_populate_js.py` | PP | cascade_populate_js.py — JavaScript cascade populator (MC-OVO-107). | `python tools/cascade_populate_js.py --project --write --json` | D | 40 LOC | Medio | ORPHAN |
| `tools/chatgpt_distiller.py` | PP | chatgpt-distiller — Extract vision, decisions, and preferences from ChatGPT exports. | `python tools/chatgpt_distiller.py <distill\|rebuild\|scan\|update> --top --verbose --dry-run` | A | 20 LOC | Medio | ORPHAN |
| `tools/check_hook_status.py` | PP | PP Hook Status -- real-time activation snapshot. | `python tools/check_hook_status.py` | A | 20 LOC | Alto | ORPHAN |
| `tools/check_playwright_mcp.py` | PP | Playwright MCP Plugin Health Check -- PP BL-PLAYWRIGHT-001 (Option A). | `python tools/check_playwright_mcp.py` | C | 50 LOC | Medio | ORPHAN |
| `tools/compact_hang_detector.py` | PP | Compact Hang Detector -- PP BL-COMPACT-001. | `python tools/compact_hang_detector.py --interactive --snooze-seconds --dry-notify` | F | 20 LOC | Alto | ORPHAN |
| `tools/compound_audit.py` | PP | compound_audit.py - health check for the Compound Learnings stack. | `python tools/compound_audit.py` | A | 20 LOC | Alto | ORPHAN |
| `tools/drift_report.py` | PP | drift_report.py — gap-6 fix: classify PP↔loose mirror pairs. | `python tools/drift_report.py` | A | 20 LOC | Alto | ORPHAN |
| `tools/e2e_clean_install.py` | PP | e2e_clean_install.py — E1 clean-machine verification. | `python tools/e2e_clean_install.py --keep-sandbox` | A | 20 LOC | Medio | ORPHAN |
| `tools/gh_skill_scanner.py` | PP | gh skill scanner (sin docstring; ver fuente) | `python tools/gh_skill_scanner.py --limit --filenames --out-raw` | D | 40 LOC | Medio | ORPHAN |
| `tools/jit_ref_correlate.py` | PP | jit_ref_correlate.py — Stop-hook: did the agent USE what JIT injected? | `python tools/jit_ref_correlate.py` | F | 20 LOC | Alto | ORPHAN |
| `tools/lazarus_orphan_purge.py` | PP | lazarus_orphan_purge.py - retire .jsonl.live orphans across all projects (BL-0073). | `python tools/lazarus_orphan_purge.py --project --apply --json` | A | 20 LOC | Alto | ORPHAN |
| `tools/lazarus_post_reboot_arm.py` | PP | lazarus_post_reboot_arm.py - sanitize Lazarus state once per logon (BL-0073). | `python tools/lazarus_post_reboot_arm.py --dry-run --force --strict` | C | 50 LOC | Alto | ORPHAN |
| `tools/lost_chat_recovery.py` | PP | lost_chat_recovery.py — safe probe for "lost" Claude session jsonls (BL-0073). | `python tools/lost_chat_recovery.py --cwd --force-after-merge --json` | C | 50 LOC | Alto | ORPHAN |
| `tools/memory_manager.py` | PP | Memory Manager — Hot/Cold context splitter for session handoff files. | `python tools/memory_manager.py --file --dry-run` | B | 30 LOC | Alto | ORPHAN |
| `tools/miner_v2.py` | PP | miner_v2.py — Total Recall: jsonl + Cursor SQLite + clustering + vision. | `python tools/miner_v2.py` | F | 20 LOC | Alto | ORPHAN |
| `tools/mistake_frequency.py` | PP | Mistake Frequency Counter — closes the Mistakes→Curriculum loop. | `python tools/mistake_frequency.py --show --top --increment` | C | 50 LOC | Medio | ORPHAN |
| `tools/mydeepchat_skill_scanner.py` | PP | mydeepchat skill scanner (sin docstring; ver fuente) | `python tools/mydeepchat_skill_scanner.py --page-size --no-prompt --out-raw` | C | 50 LOC | Medio | ORPHAN |
| `tools/normalize_paths.py` | PP | normalize_paths.py — Gap-2 (path) + Gap-10 (extended secret-scan) auditor. | `python tools/normalize_paths.py --check --apply --paths-only` | F | 20 LOC | Alto | ORPHAN |
| `tools/obsidian_enrich.py` | PP | Obsidian Enrich — Add inline [[wikilinks]] to knowledge vault body text. | `python tools/obsidian_enrich.py --vault --apply` | D | 40 LOC | Medio | ORPHAN |
| `tools/oracle_heartbeat.py` | PP | oracle_heartbeat.py — Runtime Handshake Probe (MC-OVO-90). | `python tools/oracle_heartbeat.py --project --out --pid` | F | 20 LOC | Alto | ORPHAN |
| `tools/plugin_skill_scanner.py` | PP | plugin skill scanner (sin docstring; ver fuente) | `python tools/plugin_skill_scanner.py --out --summary` | D | 40 LOC | Medio | ORPHAN |
| `tools/resume_reindex.py` | PP | resume_reindex.py - native /resume chronology health scan + repair. | `python tools/resume_reindex.py --repair` | A | 20 LOC | Alto | ORPHAN |
| `tools/rtk_corpus.py` | PP | rtk_corpus.py — build a deterministic, frequency-weighted RTK benchmark | `python tools/rtk_corpus.py --limit --out` | C | 50 LOC | Medio | ORPHAN |
| `tools/rtk_savings_export.py` | PP | rtk_savings_export.py — thin, decoupled JSON exporter of RTK savings. | `python tools/rtk_savings_export.py` | A | 20 LOC | Medio | ORPHAN |
| `tools/session-snapshot.py` | PP | session-snapshot.py — Layer 3 of SESSION_SAFETY_CONTRACT.md. | `python tools/session-snapshot.py` | A | 20 LOC | Alto | ORPHAN |
| `tools/skill_heat_map_indexer.py` | PP | Skill semantic heat-map indexer (BL-0016 / MC-SYS-27). | `python tools/skill_heat_map_indexer.py --dry-run --query --out` | A | 20 LOC | Medio | ORPHAN |
| `tools/skills_index_merge.py` | PP | skills index merge (sin docstring; ver fuente) | `python tools/skills_index_merge.py --out` | D | 40 LOC | Medio | ORPHAN |
| `tools/sovereign_miner.py` | PP | sovereign_miner.py — 4-pillar repo/transcript distillation. | `python tools/sovereign_miner.py` | F | 20 LOC | Alto | ORPHAN |
| `tools/topology_apply.py` | PP | topology apply (sin docstring; ver fuente) | `python tools/topology_apply.py --dry-run --i-have-no-open-windows --search-roots` | C | 50 LOC | Medio | ORPHAN |
| `tools/vault_indexer.py` | PP | Knowledge Vault Indexer (MC-KNB-01) | `python tools/vault_indexer.py` | D | 40 LOC | Medio | ORPHAN |
| `tools/vault_summarize.py` | PP | vault_summarize.py — Knowledge Vault Self-Optimization (MC-OVO-36) | `python tools/vault_summarize.py --project --top --check` | A | 20 LOC | Alto | ORPHAN |
| `modules/backup/verify_restore.py` | PP | Restore-test verifier. | `python modules/backup/verify_restore.py` | C | 50 LOC | Bajo | SUB-INVOKED |
| `modules/deployment/healthcheck.py` | PP | Healthcheck helpers -- tcp / http / curl-grep. | `python modules/deployment/healthcheck.py` | D | 40 LOC | Bajo | SUB-INVOKED |
| `modules/executionos-lite/migrate.py` | PP | ExecutionOS Migration Tool | `python modules/executionos-lite/migrate.py --verify` | B | 30 LOC | Bajo | ONE-TIME SETUP |
| `modules/omnicapture/install_adapter.py` | PP | OmniCapture — Adapter Installer. | `python modules/omnicapture/install_adapter.py --dolphin-log --follow --type` | F | 20 LOC | Bajo | ONE-TIME SETUP |
| `modules/omnicapture/vps/init_engine.py` | PP | KobiiClaw Initialization Engine — Zero-Shot Repository Discovery. | `python modules/omnicapture/vps/init_engine.py --deep --force --json` | C | 50 LOC | Medio | VPS-RESIDENT |
| `modules/osa/osa_command.py` | PP | OSA CLI entry point: /osa --audit / --status / --budget / --force. | `python modules/osa/osa_command.py --audit --status --budget` | B | 30 LOC | Bajo | SUB-INVOKED |
| `modules/session-continuity/tests/e2e_continuity.py` | PP | <module>/tests/e2e_continuity.py - simulates 3 slots, crash, restore; asserts invariants. | `python modules/session-continuity/tests/e2e_continuity.py` | C | 50 LOC | Bajo | DEV/BENCH |
| `modules/session-continuity/tests/e2e_reboot_cycle.py` | PP | <module>/tests/e2e_reboot_cycle.py | `python modules/session-continuity/tests/e2e_reboot_cycle.py` | A | 20 LOC | Bajo | DEV/BENCH |
| `modules/sleepless_qa/healer/dispatcher_bridge.py` | PP | Dispatcher bridge — wraps modules/dispatcher/dispatch.py to fire a healing | `python modules/sleepless_qa/healer/dispatcher_bridge.py` | C | 50 LOC | Bajo | SUB-INVOKED |
| `modules/zero-crash/vps/crash_receiver.py` | PP | Zero-Crash Telemetry Receiver — VPS-resident anonymous crash data collector. | `python modules/zero-crash/vps/crash_receiver.py --config --port` | B | 30 LOC | Medio | VPS-RESIDENT |
| `tools/bench_jit_loader.py` | PP | bench_jit_loader.py -- cold-start microbench for jit_skill_loader. | `python tools/bench_jit_loader.py` | A | 20 LOC | Bajo | DEV/BENCH |
| `tools/cache_e2e_probe.py` | PP | cache_e2e_probe.py - End-to-end empirical proof of the cache_hints chain. | `python tools/cache_e2e_probe.py --model --dry-run` | B | 30 LOC | Bajo | DEV/BENCH |
| `tools/ceps_seed_categories.py` | PP | M5 -- Seed the 9 CEPS categories with real historical patterns. | `python tools/ceps_seed_categories.py` | A | 20 LOC | Bajo | DEV/BENCH |
| `tools/ceps_test_gen.py` | PP | M15 -- CEPS auto-test stub generator + stale-stub audit. | `python tools/ceps_test_gen.py <audit\|generate> --events --force --stale-days` | C | 50 LOC | Bajo | DEV/BENCH |
| `tools/fork_storm_migration_2026-05-21.py` | PP | fork_storm_migration_2026-05-21.py | `python tools/fork_storm_migration_2026-05-21.py` | A | 20 LOC | Bajo | ONE-TIME SETUP |
| `tools/ghost_driver_test.py` | PP | BL-0057 — Synthetic tier-2 advisory injector for ghost_input_driver.ps1. | `python tools/ghost_driver_test.py --cwd --used-pct --session-id` | B | 30 LOC | Bajo | DEV/BENCH |
| `tools/lazarus_topology_daemon.py` | PP | lazarus topology daemon (sin docstring; ver fuente) | `python tools/lazarus_topology_daemon.py <loop\|start\|status\|stop> --interval` | F | 20 LOC | Medio | VPS-RESIDENT |
| `tools/lazarus_topology_push_vps.py` | PP | lazarus topology push vps (sin docstring; ver fuente) | `python tools/lazarus_topology_push_vps.py --host --key --remote-dir` | F | 20 LOC | Medio | VPS-RESIDENT |
| `tools/lazarus_topology_verify.py` | PP | lazarus topology verify (sin docstring; ver fuente) | `python tools/lazarus_topology_verify.py` | C | 50 LOC | Bajo | DEV/BENCH |
| `tools/lt_empirical_regen.py` | PP | M6 -- Regenerate the LT empirical fixture with BOTH arms populated. | `python tools/lt_empirical_regen.py` | B | 30 LOC | Bajo | DEV/BENCH |
| `tools/measure_compression.py` | PP | measure_compression.py — Apollo-retrofit compression gate. | `python tools/measure_compression.py --min --coordinated --programmatic` | A | 20 LOC | Bajo | DEV/BENCH |
| `tools/measure_session_start.py` | PP | measure_session_start.py -- empirical timing of ~/.claude/settings.json | `python tools/measure_session_start.py --json` | A | 20 LOC | Bajo | DEV/BENCH |
| `tools/migrate_to_hub.py` | PP | migrate_to_hub.py -- ONE-TIME OWNER SETUP for SCS C23. | `python tools/migrate_to_hub.py --dry-run` | A | 20 LOC | Bajo | ONE-TIME SETUP |
| `tools/optimize_session_start.py` | PP | optimize_session_start.py -- ONE-TIME OWNER SETUP. | `python tools/optimize_session_start.py --dry-run` | A | 20 LOC | Bajo | ONE-TIME SETUP |
| `tools/oracle_chaos.py` | PP | oracle_chaos.py — Fault-Injection Validation harness (MC-OVO-92). | `python tools/oracle_chaos.py --project --out --cmd` | F | 20 LOC | Bajo | DEV/BENCH |
| `tools/probe_global_watchdog.py` | PP | BL-0046 — Empirical probe: confirm context-watchdog.py snapshots | `python tools/probe_global_watchdog.py` | A | 20 LOC | Bajo | DEV/BENCH |
| `tools/probe_vault_load.py` | PP | BL-0047 — Empirical probe: measure 'primary cerebrum' coverage. | `python tools/probe_vault_load.py` | D | 40 LOC | Bajo | DEV/BENCH |
| `tools/probe_zero_fiction.py` | PP | BL-0048 — Empirical probe: zero-fiction-gate.js actually blocks | `python tools/probe_zero_fiction.py` | A | 20 LOC | Bajo | DEV/BENCH |
| `tools/register_global_hooks.py` | PP | PP Global Hooks Registration -- ONE-TIME OWNER SETUP. | `python tools/register_global_hooks.py --dry-run` | A | 20 LOC | Bajo | ONE-TIME SETUP |
| `tools/replay_harness.py` | PP | replay_harness.py — Adversarial Replay Harness (MC-OVO-106). | `python tools/replay_harness.py --project --json --self-test` | C | 50 LOC | Bajo | DEV/BENCH |
| `tools/rtk_install.py` | PP | rtk_install.py — zero-argument RTK PreToolUse activation. | `python tools/rtk_install.py` | A | 20 LOC | Bajo | ONE-TIME SETUP |
| `tools/run_all_benchmarks.py` | PP | run_all_benchmarks.py -- one-shot orchestrator for the PP Benchmark Audit. | `python tools/run_all_benchmarks.py` | A | 20 LOC | Bajo | DEV/BENCH |
| `tools/run_bench_passes.py` | PP | run_bench_passes.py -- second-pass corrections + re-measurements. | `python tools/run_bench_passes.py` | A | 20 LOC | Bajo | DEV/BENCH |
| `tools/scaffold_fastapi.py` | PP | scaffold_fastapi.py — FastAPI Sovereign Scaffolder (MC-OVO-32-F) | `python tools/scaffold_fastapi.py --out --name --no-boot-test` | C | 50 LOC | Bajo | DEV/BENCH |
| `tools/scaffold_qemu_dumper.py` | PP | scaffold_qemu_dumper.py -- QEMU RAM Dumper Sovereign Scaffolder (MC-OVO-31-Q) | `python tools/scaffold_qemu_dumper.py --out --name --no-boot-test` | F | 20 LOC | Bajo | DEV/BENCH |
| `tools/verify_apollo_integration.py` | PP | verify_apollo_integration.py — empirical DONE gate for Apollo Skills fusion. | `python tools/verify_apollo_integration.py` | A | 20 LOC | Bajo | SUB-INVOKED |
| `tools/verify_full_install.py` | PP | verify_full_install.py - Host audit for the Programmatic Budget Layer. | `python tools/verify_full_install.py --quiet` | A | 20 LOC | Bajo | SUB-INVOKED |
| `tools/verify_global_mirrors.py` | PP | verify_global_mirrors.py - BL-0064 enforcement (dynamic, branch-flip-immune). | `python tools/verify_global_mirrors.py --repo-path --ref --self-test` | A | 20 LOC | Bajo | SUB-INVOKED |
| `tools/verify_globalization.py` | PP | verify_globalization.py — sub-verifier for BL-GLOB-001. | `python tools/verify_globalization.py` | C | 50 LOC | Bajo | SUB-INVOKED |
| `tools/verify_hard_rules.py` | PP | verify_hard_rules.py -- sub-verifier for BL-HARDRULE-001. | `python tools/verify_hard_rules.py` | B | 30 LOC | Bajo | SUB-INVOKED |
| `tools/verify_hooks_registration.py` | PP | verify_hooks_registration.py -- sub-verifier for BL-HOOKS-REG-001. | `python tools/verify_hooks_registration.py` | A | 20 LOC | Bajo | SUB-INVOKED |
| `tools/verify_monitoring.py` | PP | verify_monitoring.py -- MONITORING_AXIS probe for verify_spp. | `python tools/verify_monitoring.py` | F | 20 LOC | Bajo | SUB-INVOKED |
| `tools/verify_osa.py` | PP | verify_osa.py — sub-verifier for the OSA axis (sealed 2026-05-28). | `python tools/verify_osa.py` | B | 30 LOC | Bajo | SUB-INVOKED |
| `tools/verify_proactive_agents.py` | PP | verify_proactive_agents.py -- sub-verifier for BL-PROACTIVE-001. | `python tools/verify_proactive_agents.py` | A | 20 LOC | Bajo | SUB-INVOKED |
| `tools/verify_rtk_fusion.py` | PP | verify_rtk_fusion.py — empirical DONE gate for the RTK proxy fusion. | `python tools/verify_rtk_fusion.py --corpus` | A | 20 LOC | Bajo | SUB-INVOKED |
| `tools/verify_rules.py` | PP | verify_rules.py -- RULES_TAXONOMY probe (verify_spp row). | `python tools/verify_rules.py` | C | 50 LOC | Bajo | SUB-INVOKED |
| `tools/verify_tco.py` | PP | verify_tco.py -- TCO_GATE probe (verify_spp row). | `python tools/verify_tco.py` | C | 50 LOC | Bajo | SUB-INVOKED |
| `tools/verify_tis.py` | PP | M7 -- Token Intelligence System (TIS) probe for verify_spp. | `python tools/verify_tis.py` | C | 50 LOC | Bajo | SUB-INVOKED |
| `tools/verify_uqf.py` | PP | verify_uqf.py -- UQF_ACTIVE probe (verify_spp row). | `python tools/verify_uqf.py` | C | 50 LOC | Bajo | SUB-INVOKED |

## SUB-INVOKED -- ya alcanzables (no requieren nueva automatizacion)

| Herramienta | Parent automatizado que ya la invoca |
|-------------|---------------------------------------|
| `verify_restore` | modules/backup (automatizado) post-backup |
| `healthcheck` | modules/monitoring (observe) + deployment runners |
| `osa_command` | /osa slash-command (commands/osa.md) + omni-singularity agent |
| `dispatcher_bridge` | modules/dispatcher/dispatch.py (proactive_dispatcher) |
| `verify_apollo_integration` | verify_spp.py / done-gate orchestrator |
| `verify_full_install` | verify_spp.py / done-gate orchestrator |
| `verify_global_mirrors` | verify_spp.py / done-gate orchestrator |
| `verify_globalization` | verify_spp.py / done-gate orchestrator |
| `verify_hard_rules` | verify_spp.py / done-gate orchestrator |
| `verify_hooks_registration` | verify_spp.py / done-gate orchestrator |
| `verify_monitoring` | verify_spp.py / done-gate orchestrator |
| `verify_osa` | verify_spp.py / done-gate orchestrator |
| `verify_proactive_agents` | verify_spp.py / done-gate orchestrator |
| `verify_rtk_fusion` | verify_spp.py / done-gate orchestrator |
| `verify_rules` | verify_spp.py / done-gate orchestrator |
| `verify_tco` | verify_spp.py / done-gate orchestrator |
| `verify_tis` | verify_spp.py / done-gate orchestrator |
| `verify_uqf` | verify_spp.py / done-gate orchestrator |

## HERRAMIENTAS EN REPOS EXTERNOS (escaneo de hosts accesibles)

Los repos de codigo vivos del Owner (KobiiCraft / InfinityOps / TUA-X) **no estan clonados** en los working-dirs accesibles de este host. Lo que SI existe como codigo conectable:

| Repo / App | Script manual | Que hace | Mecanismo PP de conexion |
|------------|---------------|----------|--------------------------|
| `Apps/whisprflow-apk` | `scripts/ci-local.ps1` | Build/CI local del APK | E - post-deploy callback via `modules/deployment/detectors.py` (android) |
| `Apps/whisprflow-apk` | `scripts/device-verify.ps1` | Verificacion ADB on-device | A - PostToolUse tras build, o `osa_deploy_detector` |
| `Apps/mcp-video-analyzer` | `boot_server.ps1` / `boot_tunnel.ps1` | Levanta MCP server + tunnel | F - Task Scheduler (arranque) o signal SessionStart si el proyecto activo lo requiere |
| `Apps/mcp-video-analyzer` | `run_remote.ps1` | Ejecucion remota del analyzer | C - agente `video-analyzer` (ya existe skill) que invoque el script |
| `Desktop/Repos-GitHub/n8n-skills-main` | (n/a) | -- | **EXCLUIDO**: n8n prohibido como runtime (memoria `feedback_no_n8n_ever`) |

> Datasets/prompts en `Downloads/Promptsss` (KobiiCraft, InfinityOps, TUAX, NexumOps, SalesTrainer) son material de referencia, no codigo ejecutable -- fuera de scope de este audit.

## PLAN DE IMPLEMENTACION SUGERIDO (priorizado por ROI)

| # | Herramienta | Mecanismo | Esfuerzo | Sprint |
|---|-------------|-----------|----------|--------|
| 1 | `cache_hint_apply` | A | 20 LOC | 1 |
| 2 | `check_hook_status` | A | 20 LOC | 1 |
| 3 | `compact_hang_detector` | F | 20 LOC | 1 |
| 4 | `compound_audit` | A | 20 LOC | 1 |
| 5 | `drift_report` | A | 20 LOC | 1 |
| 6 | `jit_ref_correlate` | F | 20 LOC | 1 |
| 7 | `lazarus_orphan_purge` | A | 20 LOC | 1 |
| 8 | `miner_v2` | F | 20 LOC | 1 |
| 9 | `normalize_paths` | F | 20 LOC | 1 |
| 10 | `oracle_heartbeat` | F | 20 LOC | 1 |
| 11 | `resume_reindex` | A | 20 LOC | 1 |
| 12 | `session-snapshot` | A | 20 LOC | 1 |
| 13 | `sovereign_miner` | F | 20 LOC | 1 |
| 14 | `vault_summarize` | A | 20 LOC | 1 |
| 15 | `build_index` | A | 20 LOC | 2 |
| 16 | `llm_bridge` | A | 20 LOC | 2 |
| 17 | `research_discovery` | A | 20 LOC | 2 |
| 18 | `query_telemetry` | B | 30 LOC | 2 |
| 19 | `chatgpt_distiller` | A | 20 LOC | 3 |
| 20 | `e2e_clean_install` | A | 20 LOC | 3 |
| 21 | `memory_manager` | B | 30 LOC | 3 |
| 22 | `rtk_savings_export` | A | 20 LOC | 3 |

**Sprint 1 (quick wins):** wire los ORPHAN de impacto Alto via hook/signal -- maximo ROI, minimo LOC.  
**Sprint 2-3:** scanners/indexers/distillers (mecanismo C/D) que aportan valor recurrente.  
**No-go:** ONE-TIME SETUP, VPS-RESIDENT y DEV/BENCH se quedan manuales por diseno.

---
*Fuentes de datos: `tools/_manual_tools_audit.py` -> `_manual_audit_clean.json` (sha verificable). Total filas con datos reales: 107 / 107. Cero TBD.*
