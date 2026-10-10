# 2026-10-10 -- caa-wake chain: residual after W1R-2R (goal caa-wake-t3)

Worktree `C:\Users\User\Apps\pp-caa-wake-t3`, branch `ce/caa-wake-t3`, goal `caa-wake-t3` (cap 2,200,000, Owner
2026-10-09). Origin: `C:\Users\User\Apps\pp-caa-wake\vault\plans\caa-wake-incident-2026-10-08-t2-overcharge.md`.
Packets: `vault/programs/cognitive-economy/caa-wake/` in that worktree.

## State measured 2026-10-10
- W1R-2R m-39f175c0520c: STOPPED without `W1-receipt.md`. Steward left `W1R-2R.md.partial.json`,
  `W1R-2R.md.residual.md`, salvage `vault/specs/salvage/m-39f175c0520c`.
- Committed: `1509d8c8` V-WAIT-ZEROMODEL port; mutant lines `e0f9ecfa` `0111f6fb` `11dedec5` `db7cfec6`.
- `W1R-2-mutants.md`: 5/6 KILLED (edge-triggered, no-CAS, skipped-invalidator, UNKNOWN-as-satisfied,
  contains-ignored). `worktree-read` (gate V-WAIT-WORKTREE) has NO line.
- W2 ran and wrote `W2-receipt.md` status NOT_STARTED (gate 0: W1-receipt.md absent), commit `878cb352`.
  Nothing installed in LIVE. Which pane armed W2 is not recorded.
- Goal caa-wake-t3: used 1,543,207, open 132,635, remaining 656,793.

## Open items (in order)
1. Run the last mutant: `python tools/caa_w1r2_drill.py worktree-read`, one foreground call, append + commit its line.
2. W1R-2R step 3 (port waiting assertions from `ce/gen2-completion:tools/test_ce_t1_waiting.py`): done-ness UNVERIFIED;
   read the partial receipt before redoing it.
3. Write `W1-receipt.md` (status DONE only if WAIT 14/14, consumer 8/8, 6/6 killed) and commit.
4. Budget decision (Owner): W2 estimate is 0.9M, t3 has 0.66M left. Lower the W2 envelope or open a new goal id
   (a crossed cap is never raised). Then re-run W2 -> W4 -> W5 per `RESUMPTION.md`.
5. Ledger hygiene: caa-wake hold 324,720 and the leaked t2 holds (264,040; 161,571) still to settle at autopsy BOUND
   totals; the autopsy tool that produces BOUND was not located.
6. Docs: incident plan still says `status: OPEN`; both `RESUMPTION.md` copies still name t2 as the active goal.

## Underlying defects (PP, not caa-wake)
- Goal guard binds a coordinator pane to a goal on `Set-Location` into its root and charges the pane's whole
  pre-bind session (t2: 5,485,125 settled in one row). Same class as memory
  `feedback_coordinator_set_location_binds_goal` (ce-lifecycle-v2, 32.8M).
- `GoalLedger` has no correcting op: marks are max-monotonic (`modules/provider_routing/ledger.py:202`), so an
  over-attribution can only be escaped by abandoning the goal id. Needs an Owner-authorized `correct` op with a
  recorded reason, or bind-time `since` = the bind moment, not the session start.
- A unit that stops without its receipt still parks the chain (known gap WU-1H), and W2 was armed anyway.
