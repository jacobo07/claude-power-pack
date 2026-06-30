# SCS C59 — Weekly-Burn-Awareness-by-default

**Sealed:** 2026-06-30
**Mode:** EXECUTION MODE — extends the W4/W5 wrapper, no new OS
**Verifier:** `tools/test_weekly_burn_tracking.py` → 10/10 ×3 hermetic, exit 0
**No regression:** `test_wrapper.py` 15/15; `test_tco_tracking.py` 6/6; `test_tco.py` 10/10
(its own `V-BASELINE-INTACT` = pytest 43 passed).

## Origin

Weekly-Burn-RCA (`vault/plans/weekly-limit-burn-rca-2026-06-30.md`). Per-turn
forensic over the last 48h: **49.2M output tokens, 1.81× the June daily average
(13.5M/day)**. 74% of the burn = TUA-X (48%) + InfinityOps (26%). Mechanism:
large structured prompts (EXECUTION/ULTRA-PLAN, ~80k–230k output each) fired in
consecutive tandas ~40 min apart, **amplified by parallel panes of the same
repo** (06-28 15:00–21:00, hourly output 2.5–2.9M/h). NOT a cache break (48h
cache ratio 95.8% ≈ lifetime 96.4%). NOT this PP session (~1% of burn).

## Capability

The cost_gate (W5) trackea **burn semanal**, no solo diario. The repo_coordinator
(W4) detecta **paneles paralelos del mismo repo** lanzando prompts grandes.
PR-MODE-SELECTION-001 gobierna la elección de modo: **EXECUTION por defecto,
ULTRA-PLAN solo para decisiones arquitecturales genuinas**. Never blocks — solo
informa para que el Owner decida.

## What built

- `tools/token_ground_truth.py::window_output(hours)` — per-turn-timestamp output
  sum, mtime-prefiltered (lossless: a turn at T implies file mtime ≥ T). The
  precision the weekly projection needs (vs the whole-session bucket of analyze).
- `modules/wrapper/cost_gate.py::weekly_burn()` — fires when the last-24h output
  rate ≥ 1.5× the June daily average. Projection = `weekly_limit / burn_24h` =
  days a weekly allowance lasts at the current rate (<7 → unsustainable).
  Reset-anchor-free (a trailing-7d sum spans weekly resets and would falsely read
  "exhausted"). Wired as block 3b of `cost_gate()`. Fail-open.
- `modules/wrapper/repo_coordinator.py::parallel_burn()` — 2+ same-repo panes
  each firing a large prompt (>8k chars) within 60 min → fail-open advisory. The
  pattern `coordinate()` never caught (it only offered RESUME). Wired into
  `prelaunch._w4`; W4/W5 timeouts 0.5→1.0s (concurrent, no wall-time regression).

## Honest scope

`WEEKLY_OUTPUT_LIMIT_EST = 66M` is an **Owner-derived estimate** (49.2M = "74% of
weekly" → ~66M), configurable. Anthropic's exact weekly weighting is not exposed
in transcripts, so the projection is advisory, never a hard gate. Trailing-7d
output (~145M) confirms the limit window resets within 7 days — hence the
projection is rate-based (`limit / burn_24h`), not balance-based.

## Lessons sealed (UKDL)

- **PR-MODE-SELECTION-001** — EXECUTION by default, ULTRA-PLAN only for genuine
  architecture (~3–5× output cost). Cross-project Process Rule.
- **T-PARALLEL-PANES-BURN-001** — same-repo parallel panes multiply burn without
  multiplying progress; one pane per feature, `/kclear` between large features.
