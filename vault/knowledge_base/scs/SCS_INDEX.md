# SCS Index — Sealed Cognitive Systems ledger

The authoritative list of sealed SCS entries. Each row: ID, name, the modules/tools
that carry it, the UKDL hard-rules/traps it sealed, seal date, state. New seals append
here (the next free slot is **C80** — C71/C72 are Graphify, C73..C79 below).

Note: SCS files live in two places — `vault/knowledge_base/scs/` (C68+) and
`vault/knowledge_base/` root / `graphify/` / `cognitive_os/` (older + domain-grouped).
This index is the single ledger across both.

| ID | Name | Modules / tools | UKDL sealed | Date | State |
|----|------|-----------------|-------------|------|-------|
| C68 | Token-Corpus-Doctrine | `tools/token_corpus_audit.py` | volume-audit axis | 2026-07-03 | Sealed |
| C69 | Conversation-Quality | `tools/conversation_quality_audit.py` | behavior-audit axis | 2026-07-03 | Sealed |
| C70 | Cognitive-Leak-Taxonomy | `tools/scheduled_task_health.py` | non-token leak axis (5 scheduled-task leaks) | 2026-07-03 | Sealed |
| C71 | Graphify — Knowledge-Navigation-Kernel (arch) | `modules/graphify/` (GK-00..GK-12) | GK-12 graph-first advisory | 2026-07-03 | Sealed |
| C72 | Graphify — Live activation | `modules/graphify/` + `hooks/hook-dispatcher.js` | `T-HOOK-DISPATCHER-DRIFT-001` | 2026-07-03 | Sealed |
| C73 | Activate-Before-Build (Scope A) | `hooks/session_start_hub.js` (Hook 13), `modules/parallel_mesh/pm_03_bus.py`, `modules/cognitive_os/scheduler.py` | PM-03/GK-12/CO-08 activation | 2026-07-03 | Sealed |
| C74 | CO-NextGen — CO-12 Cognitive-Readiness-Telemetry | `modules/cognitive_os/co_12_telemetry.py` | `T-CLAUDE-MD-SIZE-001` | 2026-07-04 | Sealed |
| C75 | Process-Hibernation (FASE A + loop-boundedness advisory) | `modules/cognitive_os/process_governor.py`, `hibernate_runner.py`, `rehydration.py`; `tools/run_hibernation.py`, `test_hibernation.py` | `HR-STALLED-SESSION-ADVISORY-001`, `T-UNBOUNDED-SESSION-001` | 2026-07-04 | Sealed |
| C76 | CO-08 Intent-Gate live-path wiring | `modules/wrapper/prelaunch.py` (`_gate`), `modules/cognitive_os/scheduler.py` (`decide`), `modules/parallel_mesh/pm_02_intent.py` (`scope_gated_admit`) | `T-INERT-ARCHITECTURE-TAX-002` | 2026-07-04 | Sealed |
| C77 | CO-08 Scope-Gate auto-activation (kclaude exports PP_PANE_SCOPE) | `modules/parallel_mesh/pm_02_intent.py` (`resolve_launch_scope`), `modules/wrapper/prelaunch.py` (`_apply_launch_scope`, `--sid`), `tools/kclaude.ps1` (`--scope`, sid recall) | `T-SCOPE-GATE-OPT-IN-ANTIPATTERN-001` | 2026-07-05 | Sealed |
| C78 | CDIO — Chief Design Intelligence Officer (design-intelligence layer) | `agents/cdio-*.md`, `vault/knowledge_base/cdio/`, `modules/cdio/` | design-opinion-vs-criteria + review gate | 2026-07-05 | Sealed |
| C79 | pane_map + PP Sessions resume uses kclaude (wrapper active on every resume) | `tools/build_pane_map.ps1`, `extension/src/restore_guard.js`, `extension/src/extension.js`; tests `test_pane_map.py`, `verify_session_ext.py`, `test_restore_guard.js` | `HR-RESTART-VIA-KCLAUDE-001` (C79 addendum) | 2026-07-06 | Sealed (Tier-1; cpc_os/lazarus Tier-2 pending) |

## Notes

- **C75 correct module path** is `modules/cognitive_os/` — NOT `modules/session_resilience/hibernation/` (a recurring handoff mislabel; the governor + runner + rehydration all live under `cognitive_os/`). See `[[scs_c75_process_hibernation]]`.
- **Owner-side pending** (documented, not auto-executable per HR-001): C75 Scheduled-Task LIVE activation (`vault/patches/hibernation/INSTALL.md`); C73 PM-03 Stop-publish wiring (`modules/parallel_mesh/hub_wiring_instructions.md`).
- Older SCS (C44..C67) are catalogued in their domain files under `vault/knowledge_base/` (e.g. `cognitive_os_scs_c61.md`, `graphify/graphify_scs_c71.md`); this ledger indexes C68+ where the flat `scs/` layout began, plus the two Graphify seals for slot continuity.
