# F6 — content check of vault/plans/

Date: 2026-08-09. Instrument: sealed-rule ids per plan, differenced against
the two canonical corpora (`ukdl-universal.md`, `knowledge_vault/core/HARD-RULES.md`).

The earlier count of 119 unreferenced plans matched filenames, so a plan whose
content was promoted under a different name scored as stranded. It bounded the
reachable set; it never measured loss. This differences content instead.

Nothing is moved by this pass. Classification only.

## Totals

| class | plans | meaning |
|---|---|---|
| PROMOTION_CANDIDATE | 23 | carries sealed ids absent from both corpora |
| REVIEW_DECISIONS_ONLY | 37 | no sealed ids, but records Owner decisions or verdicts |
| ALREADY_PROMOTED | 52 | every id it names is already in a corpus |
| NOT_INDEXABLE | 14 | operational or temporal, no structural knowledge |
| total | 126 | |

## Promotion candidates, by count of absent ids

| plan | absent ids | the ids |
|---|---|---|
| `ksf-compendium-2026-07-26.md` | 6 | HR-BACKLOG-001, HR-CG-13, HR-CONTEXT-001, HR-COST-001, HR-ONESHOT-001, HR-SPEC-001 |
| `egcc-corpus-2026-08-06.md` | 4 | HR-APA-016, HR-COST-001, HR-GOV-001, HR-GOV-003 |
| `memory-audit-2026-08-09.md` | 4 | HR-MEMORY-IS-ROUTER-001, PR-SESSION-WRITEBACK-001, T-KNOWLEDGE-STRANDED-IN-PLANS-001, T-ROUTER-BRIDGE-UNRESOLVED-001 |
| `uceimr-corpus-2026-08-04.md` | 3 | HR-APA-006, HR-APA-016, HR-UCEIMR-02 |
| `apir-corpus-2026-08-03.md` | 2 | HR-APA-016, HR-APA-017 |
| `dataset-first-protocol-2026-07-12.md` | 2 | HR-SPEC-001, T-DATASET-FIRST-DOGMA-001 |
| `efaif-expansion-2026-08-06.md` | 2 | PR-AUDIT-RESIDUE-FIRST-001, T-STOP1-BACKLOG-AS-GOVERNANCE-DEFECT-001 |
| `iig-compendium-2026-07-30.md` | 2 | HR-COST-001, PR-NOVELTY-PROOF-REQUIRED-001 |
| `spec-driven-auto-2026-06-03.md` | 2 | HR-CONTEXT-001, HR-SPEC-001 |
| `wrapper-w1-w5-2026-06-23.md` | 2 | T-SPAWN-WINDOW-001, T-WRAPPER-TRANSCRIPT-ANCHOR-001 |
| `aishf-corpus-2026-07-21.md` | 1 | HR-SPEC-001 |
| `crawlos-corpus-2026-07-19.md` | 1 | T-CRAWLOS-TOKEN-IN-ARTIFACTS-001 |
| `d2a-replacement-2026-07-17.md` | 1 | T-SYMMETRY-PARTS |
| `decision-intelligence-2026-07-11.md` | 1 | HR-ONESHOT-003 |
| `efaif-corpus-2026-08-04.md` | 1 | HR-COST-001 |
| `egcc-expansion-2026-08-07.md` | 1 | HR-COST-001 |
| `faitp-debts-2026-07-14.md` | 1 | HR-DOES-NOT-EXIST-999 |
| `gap-discovery-2026-07-30.md` | 1 | HR-COST-002 |
| `re-baseline-compendium-2026-07-26.md` | 1 | HR-SECRET-002 |
| `seip-sprint2-2026-08-06.md` | 1 | T-FICTIONAL-OWNER-001 |
| `session-resilience-datasets-2026-06-27.md` | 1 | HR-CONTEXT-001 |
| `tab-order-capture-2026-07-06.md` | 1 | T-TAB-ORDER-EXTENSION-ONLY-001 |
| `ukr-runtime-2026-07-30.md` | 1 | HR-UKR-01 |

## Decisions-only, needing a human read

| plan | decision markers |
|---|---|
| `CCF_ARCHITECTURE.md` | 13 |
| `CCF_CLI_SPEC.md` | 7 |
| `CCF_KNOWLEDGE_SYSTEMS.md` | 4 |
| `CCF_QUALITY_GATES.md` | 4 |
| `INSTITUTIONAL_EXTRACTION.md` | 1 |
| `OVO_FORENSIC_UPGRADE.md` | 6 |
| `OVO_VPS_CONTINUATION.md` | 3 |
| `PP_CAPABILITY_INVENTORY.md` | 4 |
| `SOVEREIGN_ADAPTER_PLAN.md` | 2 |
| `STOP_LEDGER.md` | 69 |
| `activate-inert-2026-07-03.md` | 1 |
| `arch-decision-skill-2026-05-23.md` | 6 |
| `auto-testing-skill-2026-05-23.md` | 7 |
| `autoresearch-vps-migration-2026-06-30.md` | 2 |
| `backup-skill-2026-05-24.md` | 2 |
| `ccfl-pdpf-corpus-2026-07-31.md` | 6 |
| `cgf-phase2-2026-07-22.md` | 5 |
| `code-review-skill-2026-05-23.md` | 18 |
| `cognitive-os-build-readiness-2026-06-30.md` | 4 |
| `cognitive-os-datasets-2026-06-30T145754Z.md` | 4 |
| `context-watchdog-tier2-2026-05-20.md` | 1 |
| `cross-repo-reports-2026-08-03.md` | 2 |
| `daif-two-arm-trial-2026-07-13.md` | 2 |
| `dataset-owner-side-2026-06-02.md` | 1 |
| `deep-research-agent-2026-05-23.md` | 1 |
| `deferred-backlog.md` | 1 |
| `deployment-skill-2026-05-24.md` | 2 |
| `emergence-audit-2026-07-31.md` | 2 |
| `graphify-kernel-datasets-2026-07-03.md` | 2 |
| `process-hibernation-fase-a.md` | 2 |
| `ram-optimization-2026-06-04.md` | 3 |
| `recovery-epoch-pinned-reference-2026-07-14.md` | 2 |
| `rollback-skill-2026-05-25.md` | 10 |
| `rtk-next-level-2026-05-19.md` | 2 |
| `sqi-baseline-guardian-2026-07-12.md` | 2 |
| `token-optimization-audit-2026-07-03.md` | 1 |
| `weekly-limit-burn-rca-2026-06-30.md` | 1 |

## Already promoted

`DRK_RESUMPTION.md`, `acis-generation-zero-2026-07-11.md`, `build-session-resilience-2026-06-27.md`, `cdicf-corpus-2026-08-06.md`, `cdio-build-2026-07-05.md`, `claude-md-compaction-2026-07-26.md`, `co-nextgen-datasets-2026-07-04.md`, `cognitive-kernel-datasets-2026-07-03.md`, `cognitive-leak-taxonomy-2026-07-03.md`, `conversation-quality-report-2026-07-03.md`, `crpf-2026-07-27.md`, `crpf-option-a-wiring-2026-07-27.md`, `crpf-overlap-audit-2026-07-27.md`, `d2a-expansion-2026-08-03.md`, `d2a-wiring-2026-07-10.md`, `design-baseline-2026-07-12.md`, `drk-wiring-proactive-2026-07-11.md`, `duplicate-to-advantage-2026-07-10.md`, `e-passes-audit-2026-07-29.md`, `faitp-round-2026-07-14.md`, `fd-hooks-activation-2026-07-09.md`, `fios-dispatcher-resync-2026-07-10.md`, `fios-wiring-2026-07-10T124341Z.md`, `gap-reverification-2026-08-03.md`, `graphify-activation-2026-07-03.md`, `housekeeping-pm03-wire-2026-07-04.md`, `igef-2026-07-29.md`, `iic-corpus-architecture-2026-07-12.md`, `imf-corpus-2026-07-17.md`, `kclaude-cursor-profile-2026-07-01.md`, `kclaude-new-session-speed-2026-07-01.md`, `kclaude-scope-export-2026-07-05.md`, `kclaude-startup-restart-fix-2026-07-01.md`, `kickbacks-dual-bug-2026-06-30.md`, `kickbacks-global-context-compat-2026-06-30T125531Z.md`, `liveness-reachability-2026-07-13.md`, `meta-systems-runtime-2026-07-10.md`, `pane-map-versioning-2026-07-06.md`, `parallel-mesh-datasets-2026-07-01.md`, `pm06-co08-wire-2026-07-04.md`, `pp-activation-2026-07-20.md`, `recovery-beacon-activation-2026-07-10.md`, `sdd-os-activation-2026-07-26.md`, `seip-corpus-2026-08-04.md`, `sleepy-skills-2026-06-02.md`, `sovereign-roadmap.md`, `sqi-reconciliation-engine-2026-07-12.md`, `sqi-uqios-architecture-2026-07-12.md`, `sqi-weakening-detectors-2026-07-12.md`, `strategic-gap-audit-2026-07-10.md`, `uceimr-expansion-2026-08-04.md`, `usirc-corpus-2026-07-31.md`

## Not indexable

`2026-05-18_lazarus-resume-hardening.md`, `REVERSE_ENGINEERING_REPORT.md`, `apollo-retrofit-2026-05-18.md`, `blocked-delivery-fix-2026-05-20.md`, `conversation-quality-audit-2026-07-03.md`, `daif-session-compiler-2026-07-13.md`, `governance-propagation-2026-06-08.md`, `kclaude-terminal-profile-2026-07-01.md`, `lateral-thinking-skill-plan.md`, `mcp-vid-analyzer-e2e-verification-2026-05-24T18-12-07Z.md`, `pm03-wire-sched-repair-2026-07-03.md`, `programmatic-budget-layer-2026-05-19.md`, `session-safety-global-2026-05-22.md`, `spec-department-2026-06-03.md`
