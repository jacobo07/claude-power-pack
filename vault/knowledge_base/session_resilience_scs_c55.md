# SCS C55 — Session-Resilience-OS-by-default

Sealed 2026-06-27. Companion: `vault/knowledge_base/session_resilience/`
(family index + 5 datasets), `vault/plans/session-resilience-datasets-2026-06-27.md`
(reality-scan report), `tools/test_session_resilience.py` (V-gate suite, 8/8).
Builds on: `pp_dataset_11` (CETTG), `pp_dataset_12` (RS-OS), `pp_dataset_14` (RW-OS),
`modules/cpc_os/*`, `extension/` (PP Sessions), SCS C50 (no-duplicate-panes).

## Standard

All session-recovery architecture is designed under the **Crash Recovery Contract**:
after any crash — OOM, power loss, machine reboot, forced kill — the restored session
must be **indistinguishable from a Reload Window**, with no Owner intervention.
"Indistinguishable" spans the whole window, not just terminals: same windows, same
terminal panes, same editor surfaces (tabs, order, focus, scroll, panels, splits),
same foreground. A recovery is "complete" only when the Recovery Acceptance Framework
scores it accepted; "all panes green" is not session acceptance.

The Session Resilience OS family is the **completeness standard** for any recovery
system: a new recovery feature is incomplete unless it (1) declares the fundamental
property it guarantees, (2) names its contracts, responsibilities, relationships and
anti-patterns, (3) references — never reimplements — the existing CETTG/RS-OS/RW-OS
substrate, and (4) ships an end-to-end acceptance gate, not a writer-only path.

## Reality-scan precedent (why the family is 5, not ~30)

The prompt's premise ("the PP has no crash/OOM detection, classification, rehydration,
verification, retry, telemetry") was **disproved** by FASE -1: CETTG (XI), RS-OS (XII)
and RW-OS (XIV) already cover ~70–80% at the requested depth, plus implemented
`modules/cpc_os/*`. Building the full proposed family would have duplicated them,
violating the prompt's own non-duplication constraint. Path A (Owner-approved at STOP #1)
built **only the 5 genuine residual gaps**. This is the recurring "gap inventory is a
hypothesis" discipline (`feedback_audit_disproves_owner_premise`, HR-PREMISE-001):
verify the premise against source, honor intent, correct the literal, report loudly.

## The family (38 entities, no code)

- **01 UI/Editor State Persistence Layer (G1)** — editor surface, today terminal-only.
- **02 Multi-Window Coordinator (G2)** — set-of-windows recovery; was absent.
- **03 Incremental Snapshot & Session Versioning Engine (G3)** — delta capture + versions.
- **04 Recovery Acceptance Framework (G4)** — session-level acceptance verdict + gate.
- **05 Recovery Telemetry & Diagnostics Layer (G5)** — unified recovery observability.

## Verification

`python tools/test_session_resilience.py` → SESSION_RESILIENCE_PASS=8/8 (V-SR-FILES,
V-REALITY-SCAN, V-COVERAGE, V-DEPTH ≥2000 words/dataset, V-NO-CODE, V-RELATIONSHIPS,
V-ANTI-PATTERNS, V-BASELINE-INTACT). The datasets are architecture specs (no code,
pseudocode, JSON or APIs); the family is markdown-only and touches zero production code.
Implementation of any G1–G5 system is a separate, future build governed by this standard.
