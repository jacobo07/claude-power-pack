# Plan — Wire FD-00 Admission Gate + FD-07 Close-Boundary Flywheel (EXECUTION MODE)

**Date:** 2026-07-09 · **Family:** Fable Advantage Distillation (SCS C82, sealed `f51faa1`)
**Goal:** activate the two hooks the FD datasets document as their EXECUTION-mode next build —
turn the architecture (FD-00, FD-07) into live code in the real session flow.

## Reality Contract (not done until)
1. FD-00 admission gate REJECTS a task the PP can already produce without a frontier model.
2. FD-07 close-boundary hook fires at a real session Stop and produces >= 1 classified asset
   written to the correct stack location.

## PASO -1 (done) — premises verified against real source
- `modules/parallel_mesh/pm_03_bus.py`: `FindingsBus.load(repo)`, `drain_staging_findings(repo, sid)`,
  `stage_finding`, `publish_session_findings`. Finding = `{repo,topic,claim,evidence,sid,anchor,ts}`.
- `modules/cognitive_os/co_12_telemetry.py`: `record_signal(kind, payload)` producer sink,
  `load_signals()`, `readiness_report()` — EXTEND (add `fd_metrics()`, fold into report). Never fork.
- `modules/cognitive_os/router.py`: `route(task) -> RouteDecision.rung` in
  {vault,asset,deterministic,haiku,sonnet,opus} — the cheaper-rung detector.
- `modules/cognitive_os/registry.py`: `vault_resolver/asset_resolver/lookup/store_asset` — CO-05 floor.
- `modules/graphify/session_writeback.py`: the exact Stop-hook shape to mirror (reads `{cwd,session_id}`
  from stdin, `main()` ALWAYS exit 0, fail-open absolute).
- `hooks/hook-dispatcher.js` `CHAIN_MAP['Stop-chain']`: child entries `{exe,script,timeoutMs}`;
  `session_writeback.py` already wired at line 140 — FD-07 registers identically.
- `PP_FRONTIER_SESSION`: exists NOWHERE. `tools/kclaude.ps1` exports env to launched claude (see
  `PP_PANE_SCOPE` line 163) — the honest export point (kclaude = Opus/frontier launcher on this host).

## Honest refinements vs the inline plan
- Writeback target = append-only SHA-256-idempotent `deposits.jsonl` (+ UKDL append for rule/trap class,
  + real CO-05 `store_asset` for asset class) — NOT auto-writing prose into sealed datasets (slop-gate +
  Reality Contract). Faithful to FD-06 (permanent, idempotent, append-with-supersede).
- Live activation of the dispatcher + kclaude requires an Owner-side `Copy-Item` canonical->live
  (T-HOOK-DISPATCHER-DRIFT-001); PP-internal half ships this turn, mirror step documented (HR-001).

## Hunks
- **H1** `modules/fable_distillation/fd_00_gate.py` — `check_admission(task) -> AdmissionDecision`
  (ADMIT / DECLINE / ROUTE_CHEAPER / ANSWER_FROM_ASSET, mapped to admit|reject|defer). Criteria from
  FD-00: dataset covers topic -> reject; CO-03 resolves sub-frontier -> reject/route_cheaper; format/
  expand/boilerplate -> reject; discovery/architecture/critique -> admit. Fail-open -> ADMIT. Advisory.
- **H2** `modules/fable_distillation/fd_07_flywheel.py` — the nine-stage loop, deterministic real
  executors (extract/classify, triage/destination, writeback+idempotency, CO-12 signals), `main()` Stop
  entry gated on `PP_FRONTIER_SESSION`. Wire into dispatcher Stop-chain + kclaude export.
- **H3** `co_12_telemetry.py` — add `fd_metrics()` (5 fd_* signals) + fold into `readiness_report()`,
  instrument-pending until live.
- **H4** `tools/test_fable_distillation.py` — V-FD00-*, V-FD07-*, V-CO12-* gates ×3 hermetic; UKDL
  `T-FRONTIER-SESSION-DETECTION-001`; SCS C82 addendum; git micro-commits + push (REMOTE_DELTA 0 0).

## Constraints honored
Fail-open everywhere (advisory, never blocks the Owner). Read fd_00/fd_07 first (done). No `git add -A`
(pathspec-scoped). Windows: PowerShell for git/python, parallel-write cap 2, Read-reset before repeated
same-file edits. Zero placeholders (Reality Contract).
