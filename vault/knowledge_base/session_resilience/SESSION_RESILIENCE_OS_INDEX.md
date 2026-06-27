# Session Resilience OS — Family Index

**Created:** 2026-06-27
**Mode:** ULTRA-PLAN Path A (residual-gap family) — approved at STOP #1
**Headline property:** After any crash (OOM, power loss, machine reboot, forced kill), the
restored session is **indistinguishable from a Reload Window** — same windows, same terminals,
same editor surfaces, same focus — with no Owner intervention.

---

## Why this family is small (Reality Scan verdict)

The FASE -1 Reality Scan (see `vault/plans/session-resilience-datasets-2026-06-27.md`)
disproved the prompt's premise that crash/OOM recovery does not exist in the PP. It already
exists, as datasets, at the requested depth:

- **Crash detection, classification, three-layer crash model, terminal topology restore,
  per-pane verification, no-pane-loss** → `pp_dataset_11` (CETTG, §211–231)
- **OOM detection/confidence, memory levels, checkpointing, OOM survival, RAM-aware restore,
  OOM autopsy** → `pp_dataset_12` (RS-OS, §232–259)
- **Quiescence, safe/dirty shutdown, auto-throttle, pane scheduler, crash-replay,
  recovery-loop prevention, restore queue, stability score, session gates** → `pp_dataset_14`
  (RW-OS, §283–303)
- Implemented substrate → `modules/cpc_os/*`, `modules/wrapper/*`, `extension/*`

Building the full proposed ~30-dataset family would have duplicated all of the above,
violating the prompt's own non-duplication constraint. This family therefore contains **only
the 5 genuine residual gaps**, each referencing the existing systems as dependencies.

---

## The family (5 datasets, 38 entities)

| # | Dataset | Gap | Entities | Headline contribution |
|---|---|---|---|---|
| 01 | [UI / Editor State Persistence Layer](session_resilience_01_ui_editor_state_persistence_layer.md) | G1 | 8 | Restores the *editor* surface (tabs, order, focus, scroll, panels, splits) — today only *terminals* are restored |
| 02 | [Multi-Window Coordinator](session_resilience_02_multi_window_coordinator.md) | G2 | 8 | Restores the *set of windows* as a coordinated whole — confirmed absent |
| 03 | [Incremental Snapshot & Session Versioning Engine](session_resilience_03_incremental_snapshot_and_session_versioning_engine.md) | G3 | 8 | Cheap delta capture + restore-to-a-prior-version |
| 04 | [Recovery Acceptance Framework](session_resilience_04_recovery_acceptance_framework.md) | G4 | 7 | Session-level "was recovery successful?" verdict + completion gate |
| 05 | [Recovery Telemetry & Diagnostics Layer](session_resilience_05_recovery_telemetry_and_diagnostics_layer.md) | G5 | 7 | Unified recovery observability + root-cause diagnosis |

---

## How the family composes (dependency graph)

```
CETTG (XI) ── terminals ─┐
                         ├─► Multi-Window Coordinator (02) ─► whole-session board
Dataset 01 ── editor ────┘
                         │
Dataset 01/02/CETTG ──► Incremental Snapshot & Versioning (03) ──► restorable versions
                                                                         │
                  reconstructed reference version ──► Recovery Acceptance Framework (04)
                  CETTG §223 verify + RW-OS stability ──┘   │  verdict gates "complete"
                                                            ▼
RS-OS (XII) + RW-OS (XIV) + 02 + 04 events ──► Recovery Telemetry & Diagnostics (05)
```

(The diagram above is an architecture relationship sketch in prose-art, not source code.)

---

## Dependency summary (no system reimplements another)

- **01 UESPL** depends on: CETTG (sibling, terminal half), CPC-OS (cadence), ISVE (history),
  RAF (audit). Owns: editor surface only.
- **02 MWC** depends on: CETTG + 01 (window interiors), RW-OS (resource-safe sequencing),
  CPC-OS (identity). Owns: cross-window census + coordination only.
- **03 ISVE** depends on: capture systems (CETTG/01/02) for input, CPC-OS snapshot entry point.
  Owns: history/versioning only — distinct from setup_os transaction rollback.
- **04 RAF** depends on: CETTG §223, RW-OS stability, 01/02 descriptions, ISVE reference version.
  Owns: session-level acceptance verdict + gate only.
- **05 RTDL** depends on: RS-OS incidents, RW-OS replay, RAF scorecards, MWC/CETTG/01/ISVE
  events, URB (redaction). Owns: aggregation/diagnosis/presentation only — never acts.

---

## Done-gate

- V-REALITY-SCAN — no dataset duplicates an existing PP system (each declares "Does NOT duplicate")
- V-COVERAGE — the headline property is decomposed across the family; all 5 gaps present
- V-DEPTH — each dataset ≥ 2000 words
- V-NO-CODE — no source code fences in any dataset
- V-RELATIONSHIPS — each dataset declares dependencies + a relationships section
- V-ANTI-PATTERNS — each dataset declares explicit anti-patterns
- V-BASELINE-INTACT — additions are isolated; core modules still import

Verifier: `tools/test_session_resilience.py` (V-gate convention).
