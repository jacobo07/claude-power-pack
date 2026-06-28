# SCS C57 — Workspace-Continuity G6 (Power Transition & Wake Recovery) sealed

**Sealed:** 2026-06-28
**Mode:** ULTRA-PLAN Path A — approved at STOP #1 (EXTEND_EXISTING_PARENT, no new parent systems)
**Verifier:** `tools/test_session_resilience.py` → 10/10 × 3 hermetic, exit 0
**Baseline:** `tools/test_session_resilience_build.py` → 40/40 (G1–G5 modules untouched)

## What sealed

After any power transition — sleep, wake, hibernate, battery↔AC, reboot, host/extension update, or
an **ungraceful power loss following a failed lid-close sleep** — the workbench returns to its last
stable state with no Owner intervention, or the divergence is detected, reported and reduced to the
closest achievable approximation. Power events are first-class recovery scenarios, each with its own
Recovery Contract (normal / degraded / never-guarantee), owned by the Power Transition & Wake Recovery
Engine (Dataset 06 / PTWRE), which orchestrates the existing capture (CETTG/G1/G2), storage (G3),
acceptance (G4) and telemetry (G5) systems across power boundaries without re-implementing any of them.

## Reality-scan honesty (premise corrected)

The proposed "Workspace Continuity OS" (Power Transitions + 9-engine Resume Identity + 3-engine
Startup Router + 5-engine Determinism + 4-engine Session Continuity) collapsed under the FASE -1 scan
to **one genuine gap**:

- **Power transitions** — 0 references in `modules/` or the family → **NEW** → Dataset 06 (G6, 9 entities).
- **Resume identity** — already owned by `RESUME_V3_FEATURE_SPEC.md` (C1–C5) + `NAMED_RECOVERY_INDEX.md`
  + `resume_reindex.py` → **EXTENDED in place** (RESUME_V3 §8: stable names, metadata, work-type
  classification, index-scoped semantic search, scalable navigation; host limit documented).
- **Startup routing (Home/Agents)** — **config-complete** (live settings already carry
  `workbench.startupEditor:"none"`, `window.restoreWindows:"all"`, persistent sessions on, automatic
  tasks off, hot-exit on). Not a config gap; residual = ungraceful-loss unflushed state → folded into
  PTWRE §6.6 (Ungraceful-Shutdown Detector) + §6.7 (Cold-Start Workspace Reentry). No standalone dataset.
- **Workspace determinism** — already owned by G4 `acceptance.py` + `models.py` (canonical/state_hash) → no dataset.
- **Session continuity** — already owned by G1 + `--resume`; xterm scrollback / composer draft are
  host-owned out-of-scope → no dataset.

## Artifacts

- `vault/knowledge_base/session_resilience/session_resilience_06_power_transition_and_wake_recovery_engine.md` (new, ≥2500 words)
- `vault/knowledge_base/RESUME_V3_FEATURE_SPEC.md` §8 (extended)
- `vault/knowledge_base/session_resilience/SESSION_RESILIENCE_OS_INDEX.md` (G6 + extensions registered; family now 6 datasets / 47 entities)
- `tools/test_session_resilience.py` (V-G6-DEPTH + V-RESUME-IDENTITY gates added)
