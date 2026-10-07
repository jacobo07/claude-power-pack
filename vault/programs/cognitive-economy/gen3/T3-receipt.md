# T3 receipt -- recon-factory plan 04-03 under compiled grammar (DONE)

## Commits (worktree wt_keosdtk_home, branch keosdtk-home; each code commit = workunit.py + test_workunit.py only)
- 6cc1bba Task 1: nine WU event kinds, stored-total refusal, cost derivation with absent kept absent
- dba5fc4 Task 2: per-unit leases, injected clock, kept STALE record, locked append
- a06d4e9 Task 3: verify-links, CLI, phase-closing drill
- 1c8bf78 docs(recon-factory-04): 04-03 SUMMARY (index check: no entry for decomp/workunit.py, so no --touch)

## Gate (re-run by me after the worker, foreground, all exit 0)
- test_workunit.py: WORKUNIT_DRILL=37/37, 0 FAIL lines (V-WU-BROKEN-CHAIN, -COST-ABSENT-NOT-ZERO, -LEASE-EXPIRY, -REQUIRED-GATES-RAN pass per worker)
- test_transaction_v2.py: TX2_DRILL=18/18 (incl. V-TX2-READS-REAL-V1); test_admission_scope.py: ADMISSION_SCOPE_DRILL=13/13
- `decomp_factory\workunits` not created. test_transaction.py NOT-RUN (compiles; zero local compiles).
- Worker also ran each task's own verify: T1 22/22, T2 28/28, T3 37/37 + PHASE-4 DRILLS GREEN.

## Measured spend (transcripts, deduped by message id; processed = input + cache create + cache read + output)
- Worker subagent: 42 calls, 7,256,620. Main pane: 22 calls, 3,174,989. Combined (global dedupe): 63 calls, 10,269,382.
- Envelope: <=60 calls, 12.5M. Calls 63 (worker 42 of its 55 cap) is 3 over the 60 pane+worker line; processed is inside it.

| arm | processed | calls | gate | quality |
|---|---|---|---|---|
| champion (04-01+04-02, per plan) | 16.6M | n/a | green | accepted |
| T3 compiled grammar (04-03) | 10.27M | 63 | 37/37, 18/18, 13/13 | 3 tasks, 3 commits + SUMMARY |

Ratio 0.62 of champion per plan. Caveat: 04-03 is a different plan (larger spec, 85k est), so one sample, not a rate.

## Deviations / open points
- gsd_dossier.py does not exist (plan file used as dossier). source_packet.py gave PARTIAL (truncated, redacted) = DEOPT; worker read source directly.
- Worker wrote implementation with its gates in one step (no separate RED run); gates carry red controls. 04-02 SUMMARY still absent.
- 63 calls exceeds the packet's 60-call bound by 3 (main pane overhead: dossier/packet probing).

HANDOFF NOTE: T3 done
