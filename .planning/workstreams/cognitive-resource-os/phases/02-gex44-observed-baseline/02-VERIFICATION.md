---
phase: 02-gex44-observed-baseline
verified: 2026-09-28T13:20:00Z
status: passed
score: 7/7 must-haves verified
covered_files:
  - .planning/workstreams/cognitive-resource-os/REQUIREMENTS.md
  - .planning/workstreams/cognitive-resource-os/ROADMAP.md
  - .planning/workstreams/cognitive-resource-os/phases/02-gex44-observed-baseline/02-01-PLAN.md
  - .planning/workstreams/cognitive-resource-os/phases/02-gex44-observed-baseline/02-01-SUMMARY.md
  - .planning/workstreams/cognitive-resource-os/phases/02-gex44-observed-baseline/EVIDENCE.md
  - .planning/workstreams/cognitive-resource-os/phases/02-gex44-observed-baseline/by_entrypoint.py
covered_digest: "v1:sha256:2de029035aa980a9781fb1dadd2877c54395d8718a3ddc99c26761cd7c268492"
behavior_unverified: 0
overrides_applied: 0
---

# Phase 02: GEX44 observed baseline Verification Report

**Phase Goal:** A second, independently produced observed baseline, from a Linux host whose sessions are mostly mission workers.
**Verified:** 2026-09-28T13:20:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `tools/tis_report.py --observed --all-projects` runs on GEX44 and its state is recorded as MEASURED/MEASURED_ZERO/UNMEASURED under the stated rule (ROADMAP criterion 1) | ✓ VERIFIED | EVIDENCE.md section 1 (`tis_report_rc: 0`, `run_state: MEASURED`). Independently re-ran `python3 tools/tis_report.py --observed --all-projects`: rc=0, `calls=622` (up from the recorded 559, consistent with mission-worker corpus growth) — same MEASURED derivation |
| 2 | Per-entrypoint (cli / sdk-cli): sessions, calls, median first-call context, `startup_shared_share_median`, cache-write 1h share, API-rate-equivalent $ over 7 days, pricing file named (criterion 2) | ✓ VERIFIED | EVIDENCE.md sections 2b/2c hold all fields for both entrypoints with `pricing_file: vault/pricing/anthropic_2026-09.json`. Independently re-ran `by_entrypoint.py` (no args): structurally identical output, cli sessions 13→14 / calls 588→621, sdk-cli held flat at 3/3 — drift consistent with corpus growth, not a structural gap |
| 3 | GEX44 figures set beside the laptop's (1.9%/16.4% first-call shared prefix; 79.9% 1h cache writes; $90.06/272/62), with can/cannot-explain labelling (criterion 3) | ✓ VERIFIED | EVIDENCE.md section 3 has all 8 required (metric, entrypoint) rows plus 3 more, each with non-empty "instrument can explain" and "instrument cannot explain" cells, source id and scope named for every laptop figure. Section 3a gives 7 narrative bullets closing on the open MCP question for Phase 4 |
| 4 | Every GEX44 row carries the tag phrase; every laptop figure names its source commit and scope | ✓ VERIFIED | Untagged-row check (same regex as the plan's own verify script) re-run over the committed EVIDENCE.md: 0 untagged data rows. Laptop rows cite L1-L4 with commit shas and scope caveats |
| 5 | EVIDENCE.md holds aggregates only: no transcript text, session ids, or per-project directory names (criterion 4 privacy) | ✓ VERIFIED | Leak-pattern regex (credential shapes, UUID, `.claude/projects/-`) re-run over the committed EVIDENCE.md: 0 hits. `by_entrypoint.py` selftest S9 asserts the same for its own JSON output |
| 6 | No file under `tools/` or `modules/` changes unless a tool defect is recorded with a RED-then-GREEN gate (criterion 4) | ✓ VERIFIED | `git diff --name-only c8b73ae..HEAD -- tools modules` is empty. EVIDENCE.md section 4: `tool_defects: none`. All three instrument gates re-run independently hold their claimed pass counts: `TISOBS_PASS=25/25`, `BUDGETOBS_PASS=7/7`, `PRICESRC_PASS=5/5`, no `[FAIL]` line |
| 7 | CRO-02 phase verdict follows the stated rule and is committed | ✓ VERIFIED | `inputs: api_key=UNSET, run_state=MEASURED, reconcile=MATCH, tool_defects=none` → recomputed rule gives `phase_verdict: MEASURED` (not BLOCKED/UNMEASURED/INCONCLUSIVE), matching the recorded value; `cro02: SATISFIED` follows since all 3 conditions hold |

**Score:** 7/7 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `.planning/workstreams/cognitive-resource-os/phases/02-gex44-observed-baseline/EVIDENCE.md` | Sections 0-5: pre-checks, tis_report run, per-entrypoint baseline, laptop comparison, tool-defect record, verdict | ✓ VERIFIED | All 6 top-level sections present, each header exactly once; contains `## 3. Laptop comparison` |
| `.planning/workstreams/cognitive-resource-os/phases/02-gex44-observed-baseline/by_entrypoint.py` | Read-only reproducer with `--selftest` | ✓ VERIFIED | Contains `--selftest`; independently executed, `BYEP_SELFTEST_PASS=9/9`, exit 0 |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `tools/tis_observed.py` (scan, summarize, iter_calls, cost_usd, project_key) | `by_entrypoint.py` | `import tis_observed` | ✓ WIRED | `grep -c 'import tis_observed as T' by_entrypoint.py` = 1; functions `T.scan`, `T.summarize`, `T.iter_calls`, `T.cost_usd`, `T.project_key` all called, none re-implemented |
| `tools/budget_monitor.py` (`_load_pricing`, `_aggregate_observed`, `BURN_WINDOW_DAYS`) | `by_entrypoint.py` reconcile R5/R6 | `_aggregate_observed` | ✓ WIRED | `bm._aggregate_observed(bm.BURN_WINDOW_DAYS, pricing, project_dirs=dirs)` called in `measure()`, feeds R5/R6; independently re-run, R5=MATCH, R6=MATCH |
| `tools/pricing_source.py` `current_pricing_path()` | EVIDENCE.md `pricing_file:` line | never a typed filename | ✓ WIRED | `pricing_source.current_pricing_path()` called in `main()`, resolved to `vault/pricing/anthropic_2026-09.json`, matches the EVIDENCE.md line exactly |
| SCRATCH `byep-final.json` | EVIDENCE.md sections 2b/2c | table cells copied from JSON | ✓ VERIFIED (structurally, via reproduction) | Original scratch JSON is job-local and not persisted, but the reproducer is deterministic on live inputs and reproduces the same shape/reconcile result on independent re-run |

### Data-Flow Trace

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| EVIDENCE.md section 1 table | native summary fields (sessions, calls, startup_context_median, …) | `tools/tis_report.py --observed --all-projects` reading `/home/kobii/.claude/projects` | Yes — re-run independently returns live, non-static values that match the recorded structure with expected drift | ✓ FLOWING |
| EVIDENCE.md section 2b/2c table | per-entrypoint sessions/calls/usd_7d/etc. | `by_entrypoint.py measure()` composing `tis_observed`/`budget_monitor` over the same transcript root | Yes — re-run independently, reconcile MATCH on live data | ✓ FLOWING |
| EVIDENCE.md section 3 table | laptop reference figures (L1-L4) | commit messages `10299f8`, `ca69a04`, `9fa1017` (external, not re-verified against those commits' actual diffs in this pass) | Static quoted values, correctly labelled as such with source id | ✓ FLOWING (as a cited constant, not a live measurement — this is what the phase goal requires) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| `by_entrypoint.py --selftest` passes on synthetic fixture | `python3 by_entrypoint.py --selftest` | `BYEP_SELFTEST_PASS=9/9`, exit 0 | ✓ PASS |
| `tools/tis_report.py --observed --all-projects` runs live on GEX44 transcripts | `python3 tools/tis_report.py --observed --all-projects` | rc=0, `calls=622`, `sessions=43` | ✓ PASS |
| Three instrument gates hold their claimed pass counts | `python3 tools/test_tis_observed.py` / `test_budget_monitor_observed.py` / `test_pricing_source.py` | `TISOBS_PASS=25/25`, `BUDGETOBS_PASS=7/7`, `PRICESRC_PASS=5/5`, no `[FAIL]` | ✓ PASS |
| `by_entrypoint.py` normal-mode run reconciles against tis_observed/tis_report/budget_monitor on live data | `python3 by_entrypoint.py` | `reconcile.overall: MATCH` (R1-R6 all MATCH) | ✓ PASS |
| EVIDENCE.md is free of leak patterns and untagged rows (plan's own gate) | regex re-run over committed file | `leak patterns: []`, `untagged rows: 0` | ✓ PASS |
| No `tools/`/`modules/` diff since phase start | `git diff --name-only c8b73ae..HEAD -- tools modules` | empty | ✓ PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` probes declared or discovered for this phase; skipped (none applicable — this phase uses its own plain-python3 gates and selftest, all exercised above).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|--------------|------------|--------------|--------|----------|
| CRO-02 | 02-01-PLAN.md | GEX44's own transcripts yield an observed usage baseline split by entrypoint, compared with the laptop's | ✓ SATISFIED | REQUIREMENTS.md marks CRO-02 `[x]` / "Complete"; EVIDENCE.md section 5 `cro02: SATISFIED`; independently reproduced (see Observable Truths 1-7) |

No orphaned requirements: REQUIREMENTS.md maps only CRO-02 to Phase 2, and 02-01-PLAN.md's frontmatter declares exactly `requirements: [CRO-02]`.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | none found (`TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` grep over EVIDENCE.md and by_entrypoint.py: 0 hits) | — | — |

### Human Verification Required

None. All must-haves are grep/structural checks or independently re-run live commands; nothing in this phase's scope depends on visual, real-time, or external-service behavior.

### Gaps Summary

No gaps found. Two minor bookkeeping items observed but not treated as gaps against the phase goal (they are orchestrator/ship-workflow housekeeping, not part of CRO-02's evidence contract):

- ROADMAP.md's Phase 2 checkbox (`- [ ] **Phase 2: GEX44 observed baseline**`) and its Progress-table row (`In Progress`) have not yet been flipped to done/complete — this is normally updated by the phase-completion step after verification, not by the executor.
- `git status` shows a handful of untracked workstream-infrastructure files (`.planning/active-workstream`, `.planning/workstreams/cognitive-resource-os/{config.json,milestone.lock,state.json}`, an empty `phases/03-p3-pre-flight-p0/` directory) — none of these are declared outputs of 02-01-PLAN.md's `files_modified`, and Phase 2's own acceptance criteria only require a clean status excluding `.planning`, which holds. These belong to workstream/session scaffolding outside this phase's artifact set.

Phase 1 (CRO-01) remains BLOCKED pending an Owner decision, and Phase 2 formally depends on Phase 1 in ROADMAP.md — but 02-CONTEXT.md explicitly scoped Phase 2 to not depend on the blocked part (the pytest suite), only on the already-green plain-python3 gates, which this verification re-confirmed live. This is not a gap in CRO-02's own goal.

---

_Verified: 2026-09-28T13:20:00Z_
_Verifier: Claude (gsd-verifier)_
