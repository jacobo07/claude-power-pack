# ctx-same-pane: budget HARD STOP during Phase 1 / Plan 01-01 (receipt)

The ROADMAP asks for `vault/programs/ctx-same-pane/RECEIPT.md`; the goal-budget guard refused that path (only vault/plans/*.md,
memory/handoffs/*.md and RESUMPTION_FILE.md qualify for closeout), so the receipt lives here.

Goal `ctx-same-pane`: used 16,044,483 of cap 16,000,000 at the first refusal (16,237,134 at the second). Cap not raised, goal not rebound.

## State at stop: code and evidence DONE, NOTHING COMMITTED
Worktree `C:\Users\User\Apps\pp-ctx-same-pane`, branch ctx/same-pane, HEAD 9123a103. Plan 01-01 Tasks 1 and 2 are complete; Task 3
step 1 (six suites) is complete. Not done: commit A, LOG.md sha/suite/drill lines, commit B, 01-01-SUMMARY.md (the guard refused every Bash call
before `git status`).

Modified, for commit A pathspec: tools/rollover.py, tools/rollover_replay.py, tools/test_rollover_replay.py, tools/test_rollover_decide_evidence.py.
New, for commit B pathspec: vault/programs/ctx-same-pane/s0 (apply-check.txt, fresh-cost-real.json, drills/*.json x4, drill-*.txt x4, suite-*.txt)
and vault/programs/ctx-same-pane/LOG.md (has the patch/H1/real-ledger facts; lacks commit sha, suite counts and drill outcomes).
Not mine, leave untracked: .planning/workstreams/ctx-same-pane/phases/01-s0-ctx-rent-s2-repair/_apply_check.txt,
.planning/workstreams/ctx-same-pane/phases/02-s1-rent-attribution/, .pp-capabilities.
This file is also new (vault/plans) and untracked.

## Measured (source: files under vault/programs/ctx-same-pane/s0)
- git apply --check rc=0 and git apply rc=0: applied, not hand-ported.
- H1 finished with `_is_certified_result`: counted only for a non-error result containing `RESUME_CERTIFIED -- ` or
  `RESUME_CERTIFIED (already) -- authority restored` and not `NOT restored`.
- Final suites: test_rollover_replay 41/41, test_rollover 57/57, test_rollover_active_path 46/46, test_rollover_economic 19/19,
  test_rollover_decide_evidence 13/13, test_rollover_horizon_wiring 11/11.
- Drills, all `MUTANT KILLED` (exit 0), the failing line being the named gate: V-RR-CERTIFY-DETECT[refused] (suite 37/41),
  V-RR-PROTOCOL-NOT-WORK (39/41), V-RR-NO-CERTIFY-NOT-ZERO (40/41), V-ROLLOVER-PROTOCOL-BASIS (12/13).
- Real ledger, read only (`prior --write` not run): certified 301, samples 300, protocol_overhead n=298 p10 353,401 p50 387,598 p90 593,098;
  calls_to_certify p50 3 p90 5; old carried_before_first_mutation n=294 p50 1,801,735 p90 4,172,439; no_certify_call 2; secret grep 0 hits.

## Next exact action (needs a new goal id from the Owner)
1. `git status --short` must show only the files above plus the three not-mine entries.
2. Commit A by pathspec (4 tools files), subject `fix(rollover): ctx-rent S2 PROTOCOL rehydration basis + certified-result H1 (S0)`; verify `git log -1 --format=%s`.
3. Add sha + suite + drill lines to LOG.md; `git add --` then commit B (s0 + LOG.md), subject `docs(ctx-same-pane): S0 suite + drill evidence`.
4. Write and commit 01-01-SUMMARY.md; then plans 01-02 and 01-03.
