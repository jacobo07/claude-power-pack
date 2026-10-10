---
phase: "1"
slug: usage-truth-plane
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-10-10
---

# Phase 1 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Source: `01-RESEARCH.md` section Validation Architecture.

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Plain-Python gate scripts (`check(gate, cond, ev)` prints `PASS`/`FAIL V-...`, final `*_PASS=n/m`, exit 0/1). No pytest. |
| **Config file** | none - each gate sets its own temp env (`test_mission_spend.py:22-26`) |
| **Quick run command** | `& 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe' tools\test_evc_usage_truth.py` |
| **Full suite command** | quick command + `tools\test_mission_spend.py`, `tools\test_usage_index.py`, `tools\test_pricing_source.py`, `tools\test_session_budget_guard.py`, `tools\test_gsd_mission_owner_hold.py`, `tools\test_gsd_mission_envelope.py`, `tools\test_mission_lineage.py` |
| **Estimated runtime** | hermetic part: seconds; live baselines: ~14 s cold |

## Sampling Rate

- **After every task commit:** quick command
- **After every plan wave:** quick command + `test_mission_spend.py`, `test_usage_index.py`, `test_pricing_source.py`, `test_gsd_mission_owner_hold.py`
- **Before `/gsd-verify-work`:** full suite green, then mutation drill
- **Max feedback latency:** 30 seconds

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| TBD (filled by planner) | - | - | EVC-01 | unit | `V-EVC-STREAM-LAST`, `-CONTROL`: last copy wins, first-copy rule is smaller | W0 | pending |
| TBD | - | - | EVC-01 | unit | `V-EVC-SUBAGENT-IN-TREE`: per-session vs per-tree differ by exactly the subagent tokens | W0 | pending |
| TBD | - | - | EVC-01 | unit | synthetic row excluded; cross-file duplicate merged by per-column max; identity-less call counted once | W0 | pending |
| TBD | - | - | EVC-01 | unit | `V-EVC-CATEGORIES-SUM`: four categories + call count + `last_call_ts` + `measured_at` sum to processed | W0 | pending |
| TBD | - | - | EVC-01 | unit | `V-EVC-UNKNOWN-NOT-ZERO` with paired control | W0 | pending |
| TBD | - | - | EVC-01 | integration | `V-EVC-EQ-INDEX`: reader equals `usage_index.window` on the same fixture | W0 | pending |
| TBD | - | - | EVC-01 | live | `V-EVC-BASELINE-*` within 0.05% of 371.0M / 58.4M / 245.8M; absent transcripts print `NOT_OBSERVED`, excluded from the pass count | W0 | pending |
| TBD | - | - | EVC-01 | unit | `V-EVC-STATEMENT-*`: ALIVE text `worker LIVE -> total current UNKNOWN, >= X`; UNKNOWN verdict; all DEAD; stale branch driven RED then GREEN | W0 | pending |
| TBD | - | - | EVC-01 | unit | `V-EVC-LEGACY-HOLD`: prose-only hold renders `recorded at ... not re-measured` | W0 | pending |
| TBD | - | - | EVC-01 | static + behavioural | `V-EVC-SURFACES-ONE-RENDERER`: no `owner_hold...get('reason')` interpolation outside the renderer, plus a call of each surface | W0 | pending |
| TBD | - | - | EVC-01 | integration | `V-EVC-HOLD-SNAPSHOT`: breaker trip stores `owner_hold["measured"]`, ledger text unchanged for old consumers | W0 | pending |
| TBD | - | - | EVC-02 | unit | `V-EVC-PRICE-SOURCED`: exact `claude-sonnet-5-5` row in the current file, `source_url` and `fetched_iso` present | W0 | pending |
| TBD | - | - | EVC-02 | unit | `V-EVC-PRICE-UNKNOWN`: unknown model gives None category and unpriced count, never 0; all-priced control | W0 | pending |
| TBD | - | - | EVC-03 | unit | verbatim 429 row gives event with `resets_at`, worker attribution, `http_status` 429; ordinary row yields none; auth `<synthetic>` reply is not a quota event | W0 | pending |
| TBD | - | - | EVC-03 | unit | feasibility: rejected + future reset is UNKNOWN; later success is `superseded`; reset passed is `UNKNOWN (not re-measured)` | W0 | pending |
| TBD | - | - | regression | existing | `tools\test_session_budget_guard.py` (guard parity unchanged) | yes | pending |
| TBD | - | - | regression | existing | `tools\test_pricing_source.py` on the NEW current price file | yes | pending |

*Status: pending / green / red / flaky*

## Wave 0 Requirements

- [ ] `tools/test_evc_usage_truth.py` - covers EVC-01/02/03 (hermetic temp dirs; copy `check()`/`_row()` helpers from `test_mission_spend.py:41-57`)
- [ ] `vault/pricing/anthropic_2026-10.json` - all rows of the 2026-09 file plus `claude-sonnet-5-5`; must exist before the price gate can be green

*No framework install needed.*

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Mutation drill (5 mutants) | EVC-01/02/03 | Runs mutated copies via `GSD_MISSION_DRILL_DIR`; must never touch the live-loaded file | (a) first-copy rule: `V-EVC-STREAM-LAST` and baselines red; (b) renderer prints bare figure: `V-EVC-STATEMENT-ALIVE` red; (c) unpriced model costs 0: `V-EVC-PRICE-UNKNOWN` red; (d) drop quota `on_line`: 429 gate red; (e) f-string at one echo site: `V-EVC-SURFACES-ONE-RENDERER` red |

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30 s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
