# Build Session Resilience OS (G1–G5) — IMPLEMENTATION READINESS REPORT + STOP #1

**Date:** 2026-06-27
**Mode:** ULTRA-PLAN / FASE -1 (read datasets + real source before any code)
**Status:** STOP #1 — Owner approval required before writing any module
**Branch:** main @ 5ab5a1e (datasets sealed, V-gates 8/8)

---

## A. Two premises in the prompt that source contradicts (must resolve at STOP #1)

### A1. The dependency graph is inverted at 3 edges

The prompt states: *G4 independent · G5→G4 · G3→G4 · G2→G3 · G1→G2&G3.*
The datasets (which I authored and the Owner approved) say the **data flows the other way**:

- Dataset 01 (UESPL/G1) is a **producer**; Dataset 02 (MWC/G2) "aggregates per-window UESPL
  descriptions" → **G2 consumes G1**, not G1→G2.
- Dataset 04 (RAF/G4) "uses the exact version reconstructed by ISVE (Dataset 03) as its
  reference" and scores 01/02/03 descriptions → **G4 consumes G3 (and G1/G2)**, not G3→G4.
- Dataset 05 (RTDL/G5) ingests RAF scorecards → **G5 consumes G4**. ✓ (the one correct edge)

**Corrected data-flow graph:** `G1 → {G2, G3} → G4 → G5` (arrows = "feeds").

**Build order is still G4 → G5 → G3 → G2 → G1**, but justified by *build-test independence*
(each is testable on synthetic fixtures), **not** by the prompt's dependency claims. G4 and G3
are independently testable; G5 needs G4's verdict shape; G2's census logic is independent
(consumes G1 *data*, testable with fixtures); G1's UI capture is the host-side producer.

### A2. The literal reality contract is not achievable as written

The prompt requires: *implement as **Python modules** · agent **simulates crash (kill)** ·
Cursor reopens · **scroll/focus/tab-order restored** · **no Owner intervention** · agent
confirms **visually indistinguishable**.* Source proves this cannot be delivered that way:

- **Python cannot manipulate Cursor's UI.** Tab/scroll/focus capture+restore is only possible
  from the **extension (JS)** via `vscode.window.tabGroups` / `TextEditor.visibleRanges`
  (read) and `showTextDocument` / `revealRange` (apply). Scroll restore is **approximate**
  (`revealRange`), not pixel-exact — Dataset 01 itself documents this as the
  "known-but-unrestorable" contract.
- **The visual "indistinguishable" gate is inherently Owner-run.** Killing a live Cursor GUI
  and confirming scroll-at-60% is a UI-only check with no CLI — exactly the precedent SCS C50
  sealed ("Reload Window is a UI-only action… inherently Owner-driven"). A headless agent
  cannot self-certify it. Claiming otherwise = Scaffold Illusion (Mistake #16) + false DONE
  (HR-OUTPUT-002, Reality Contract).
- **The host already does much of it.** Cursor/VS Code restores editor layout + scroll on
  reload AND on crash via built-in hot-exit/backup. Our genuine gap is the **cold-start /
  post-OOM-reboot** case where host state is gone, plus the structured acceptance/telemetry/
  versioning around it.

This is not a refusal — it is scoping the contract to what is real, per the Reality Contract's
"if it can't be wired end-to-end this turn, state the gap and stop."

---

## B. Real source confirmed (extend, don't duplicate)

- `modules/cpc_os/snapshot.py` — **full** pane-snapshot renderer (md + json sidecar); terminal
  state only; **no deltas, no versioning, no UI**. → G3 extension point.
- `modules/cpc_os/work_state_saver.py` — structured WIP (branch/task/changed-files) keyed by
  session_id|cwd. → G3 input source.
- `modules/cpc_os/registry.py` (`PaneRegistry`, `_atomic_write`) — source of truth + atomic IO.
- `extension/src/extension.js` + `restore_guard.js` — host access; **terminal-only** restore
  today; pure-decision-logic-with-edge-effects pattern. → G1/G2 apply point (JS).
- `tools/build_pane_map.ps1`, `tools/restore_panes.ps1` (`cursor <path>` per repo) → G2 window-open.
- Secret Firewall / URB (`modules/secret_firewall`) → G5 redaction.

---

## C. Per-entity feasibility map (38 entities)

Tiers: **[H]** headless Python, real hermetic test, self-verifiable ·
**[J]** extension JS (host access) · **[L]** host-API-limited (approximate) ·
**[O]** Owner-GUI-verified only.

### G4 Recovery Acceptance Framework (7) — extends nothing; new `modules/session_resilience/acceptance/`
Acceptance Criteria Registry [H] · Recovery Scorecard Engine [H] · Equivalence Oracle [H] ·
Partial-Recovery Classifier [H] · Acceptance Gate [H] · Recovery Benchmark Engine [H] ·
Regression Sentinel [H]. **All 7 fully buildable + self-verifiable on fixtures.**

### G5 Recovery Telemetry & Diagnostics (7) — new `modules/session_resilience/telemetry/`
Recovery Event Collector [H] · Metrics Aggregator [H] · Root-Cause Diagnostics Engine [H] ·
Recovery Health Observatory [H] · Telemetry Redaction Bus [H, reuses URB] · Anomaly & Trend
Detector [H] · Diagnostics Correlation Engine [H]. **All 7 fully buildable + self-verifiable.**

### G3 Incremental Snapshot & Versioning (8) — extends `snapshot.py`; new `…/snapshot/`
Delta Capture Engine [H] · Baseline Anchor Registry [H] · Snapshot Chain Manager [H] · Version
Catalog [H] · Version Restore Selector [H] · Compaction & Retention Engine [H] · Integrity
Chain Validator [H] · Version Diff Presenter [H]. **All 8 buildable + testable on synthetic
state descriptions** (real-world value bounded by capture fidelity from G1/G2).

### G2 Multi-Window Coordinator (8) — extends `build_pane_map.ps1`/`restore_panes.ps1`; new `…/multi_window/`
Window Registry [H] · Cross-Window Topology Engine [H] · Window Identity Resolver [H] ·
Window-to-Workspace Binding Engine [H] · Window Restoration Orchestrator [H logic / O action] ·
Focus Arbitration Engine [H logic / O action] · Cross-Window Lock Coordinator [H] · Window
Lifecycle Event Channel [H]. **Logic fully testable headless; the window-open ACTION
(`cursor <path>`) works but its visual verification is Owner-run.**

### G1 UI / Editor State Persistence (8) — Python model + **extension JS** capture/apply
Editor Tab Inventory Engine [J] · Tab Ordering Registry [J] · Active Focus Engine [J] · Scroll
& Cursor Position Layer [J,L] · Panel Layout Engine [J,L] · Editor Split Topology Engine [J,L] ·
Pinned & Preview Tab Classifier [J] · UI State Diff Adapter [H]. **Only the Diff Adapter +
manifest model are Python; the 7 capture/apply entities are extension-JS, host-API-limited,
and the headline done-gate is Owner-GUI-only.**

**Summary:** ~30 entities (G4+G5+G3 + G2 logic + G1 diff/model) are **headless-real and
self-verifiable this turn**. ~7–8 (G1 capture/apply + the multi-window/visual actions) are
**extension-JS / Owner-GUI-verified** and cannot be self-certified by a headless agent.

---

## D. Paths for the Owner (STOP #1)

- **Path A (recommended) — Build the real headless backbone now.** Implement G4, G5, G3-core,
  G2-core, and G1's Python-feasible pieces (diff adapter + manifest model) as real modules under
  `modules/session_resilience/` with hermetic V-gate tests that pass for real (no mocks, no
  GUI). Ship the G1 capture/apply as a written extension-JS spec + the feasible Python half,
  with the visual contract explicitly marked **Owner-run** (SCS C50 precedent). Honest, large,
  fully verifiable scope. The empirical "OOM = Reload Window" visual gate is handed to the Owner.
- **Path B — A + actually write the G1 extension JS** (tabGroups/visibleRanges/showTextDocument/
  revealRange in the PP Sessions extension), accepting scroll is approximate and the done-gate
  stays Owner-run GUI. More work; headline test still ends Owner-run.
- **Path C — Reframe the contract first, then build A.** Agree explicitly that "OOM = Reload
  Window" is delivered partly by the host (hot-exit) and partly by our cold-start layer, the
  agent-run gate is the hermetic logic suite, the visual gate is Owner-run — then proceed with A.
- **Path D — Owner disputes the feasibility read** / wants a different scope.

I will not write code, declare DONE on the visual contract, or mock a verdict before this choice.
