---
phase: 03-counted-runs
status: passed
verified: 2026-10-05
---
# Phase 3 Verification

`python3 vault/programs/cognitive-economy/e1/e1_runner.py run` (worker epoch 3, from the e1 worktree, detached,
log `.gsd/e1-run.log`) ran 2026-10-05 10:59 -> 11:16 UTC and printed `E1-RUN ALL_DECIDED pairs=11 spent=9172196`.

| # | Success criterion | Evidence | Status |
|---|---|---|---|
| 1 | Every counted run recorded with validity, grade, first-call context, total context, output tokens | `results.jsonl`: 22 `run` records, each with `valid`, `invalid_reasons`, `grade_summary`, `metrics.first_call_context`, `metrics.total_context`, `metrics.output_tokens`; 22/22 valid, none rerun; all 22 carry `bank_access: []` (audited, no hit) | PASS |
| 2 | Ended on a contract condition named in the last record | last record `{"kind": "stop", "condition": "ALL_DECIDED", "spent": 9172196, "runs_counted": 22, "valid_pairs": 11, "over_cap_by": 0}`, committed 52f0a0dd; one commit per pair (055c44b3 ... a5b6f751) | PASS |

Positive control on pair 1: delta 21,633 >= 15,000. Harm window: 2 losses in the first 8 valid pairs (< 4).
