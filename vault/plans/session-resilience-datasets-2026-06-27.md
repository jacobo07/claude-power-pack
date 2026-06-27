# Session Resilience Dataset Family — REALITY SCAN REPORT + STOP #1

**Date:** 2026-06-27
**Mode:** ULTRA-PLAN / FASE -1 (Reality Scan, mandatory)
**Status:** STOP #1 — Owner approval required before building any dataset
**Branch:** main @ 02bf678 (clean)

---

## VERDICT (loud, up front)

The prompt's central premise — *"el PP NO tiene: detección de crash vs cierre normal,
clasificación de interrupción, rehidratación automática post-crash, verificación de
integridad, retry engine, telemetría de recuperación, OOM recovery"* — is **largely
FALSE**. The PP already ships an architecture-dataset family covering ~70–80% of the
proposed scope, at the exact depth and no-code format requested.

This is the recurring "the GAP INVENTORY is itself a hypothesis" pattern
(memory: `feedback_plan_code_is_hypothesis_verify_source`,
`feedback_audit_disproves_owner_premise`, HR-PREMISE-001, HR-CONTEXT-001).
Honoring the prompt's own hardest constraint — *"No existe ningún sistema en la familia
que duplique infraestructura ya construida en el PP"* — forbids building the full
proposed ~30-dataset family. Most of it would be a duplicate.

---

## WHAT ALREADY EXISTS (do NOT duplicate)

### Datasets — `vault/knowledge_base/pp_dataset/` (23 parts, ~672 KB)

| Part | System | Covers (proposed-area mapping) |
|---|---|---|
| **XI** (§211–231) `pp_dataset_11_crash_to_exact_terminal_topology` | Crash-to-Exact-Terminal-Topology Guarantee (CETTG) | Crash detection signals + **Crash Confidence CC0–CC4** (§221); **three-layer crash model** process/window/machine (§214); **clean-close vs crash** (§225); terminal topology manifest = pane count, cwd, conversation map, locks, task (§212); **last_known_good_topology** + promotion/validation (§213); restore-plan generator + manual plan (§216/§218); bootstrap recovery (§219); **pane restore verification** (§223); restore ordering (§224); no-pane-loss + completion report (§220); 10 chaos tests (§228) |
| **XII** (§232–259) `pp_dataset_12_ram_stewardship_os_oom_crash_survival` | RAM Stewardship OS (RS-OS) | **OOM Crash Survival Guarantee** (§233); memory levels M0–M6 (§234); RAM watchdog (§235); memory checkpointing (§236); **OOM detection + OOM Confidence OOM0–OOM4** (§239); OOM incident record (§240); **OOM autopsy** (§241); RAM-aware sequential restore (§250); `/oom-recover` (§252); RAM cascade prevention (§254) |
| **XIV** (§283–303) `pp_dataset_14_resilient_workbench_os` | Resilient Workbench OS (RW-OS) | Quiescence (§284); **safe shutdown** (§285); **dirty-shutdown detection** (§286); auto-throttle T0–T6 (§287); pane scheduler (§288); **crash replay log** (§290); **recovery loop prevention / retry degrade** (§291); **resource-safe restore queue** (§292); task draining (§293); active-work preservation (§294); **workspace stability score** (§295); **session start/end stability gates** (§297/§298) |
| X (§…) `pp_dataset_10_cpc_os_spec` (5131 lines) | CPC-OS full spec | The implemented substrate the above extend |
| XIII / XV+ | Resource Governor, Self-Safe Evolution, etc. | Adjacent (resource/deploy-safety) |

### Implemented code — `modules/cpc_os/`
snapshot.py · recovery.py · restart.py · topology_reconcile.py · vscode_autorun.py ·
work_state_saver.py · heartbeat.py · registry.py · handoff.py · switch.py ·
auto_reset_orchestrator.py · context_monitor.py · router.py · backlog.py

### Implemented code — `modules/wrapper/` (W-series)
prelaunch.py · auto_resumer.py · session_namer.py · repo_coordinator.py ·
turn_counter.py · cost_gate.py

### Extension — `extension/` (PP Sessions, kobii.pp-sessions)
extension.js · restore_guard.js (cold-start restorer, SCS C50 Option C)

### Other datasets already present
`sdd_os/` (5), `setup_os/` (4), `RESUME_V3_FEATURE_SPEC.md`, `dataset-driven-build.md`

---

## PROPOSED-AREA → EXISTING-COVERAGE MAP

- **ÁREA 1 Crash Recovery OS** → Part XI + XII. *Crash Recovery Contract, OOM Recovery
  Contract = BUILT.* Recovery Acceptance Framework / Recovery Benchmark = **partial/gap.**
- **ÁREA 2 Snapshot Engine** → Part XI §212/§213 (manifest, LKG, atomic, validation,
  integrity) = BUILT. **Incremental Snapshot + Session Versioning = GAP.**
- **ÁREA 3 UI State Persistence** → Part XI captures **terminal topology only**.
  Editor tabs, tab order, active focus, scroll position, panel layout/dimensions,
  splits = **GAP** (the literal "Reload Window" editor surface is NOT snapshotted).
- **ÁREA 4 Multi-Window Coordinator** → grep found **zero** coverage = **GAP.**
- **ÁREA 5 Conversation Restoration** → `--resume` + Part XI conversation→pane routing =
  BUILT. Agent Context Restoration (beyond transcript) = partial (handoff).
- **ÁREA 6 Recovery Engine Family** → Reconstruction (XI + recovery.py), Verification
  (§223), Retry (XIV §291/§292), Crash Classification (XI CC + XII OOM) = BUILT.
  State Diff Engine = partial (topology_hash compare).
- **ÁREA 7 Observability** → OOM incident/autopsy (XII), crash replay (XIV), stability
  score / `/workbench-status` (XIV) = partial. Unified Recovery Telemetry/Diagnostics
  layer = **gap-ish.**

---

## GENUINE RESIDUAL GAPS (the only non-duplicative datasets worth building)

- **G1 — UI / Editor State Persistence Layer.** Today only *terminal* topology is
  captured. A true "OOM = Reload Window" guarantee for the editor needs: open editor
  tabs + their order, active focus (which tab/group/window), scroll/cursor position per
  document, panel layout (sidebar/panel open-state + dimensions), and editor splits.
  **This is the real heart of the Owner's acceptance criterion** and it is missing.
- **G2 — Multi-Window Coordinator.** Cross-window topology + coordination. Confirmed absent.
- **G3 — Incremental Snapshot + Session Versioning.** Delta snapshots and restore-to-a-
  prior-version. Absent.
- **G4 — Recovery Acceptance Framework + Recovery Benchmark.** A formal, system-level
  "was this recovery successful?" contract + quality baseline, above per-pane verify.
  Mostly absent as a named system.
- **G5 — Unified Recovery Telemetry / Diagnostics Layer.** Consolidates the partial
  signals (OOM incident, crash replay, stability score) into one observability surface.

---

## PATHS FOR THE OWNER (STOP #1)

- **Path A (recommended) — Build only G1–G5** as standalone datasets in
  `vault/knowledge_base/session_resilience/`, each explicitly referencing XI/XII/XIV as
  dependencies. Smallest real gap; zero duplication. ~5 datasets.
- **Path B — Consolidate + extend.** Re-home XI/XII/XIV crash content into a properly
  structured standalone `session_resilience/` System→Layer→Engine family AND add G1–G5.
  Larger; produces the "complete family" aesthetic but partially re-expresses existing
  content (mitigated by referencing, not copying).
- **Path C — Build the full ~30-dataset family as written.** **NOT recommended** —
  directly violates the prompt's own non-duplication constraint against XI/XII/XIV.
- **Path D — Owner disputes the audit** / wants a different scope.

Awaiting Owner decision before any dataset is written.
