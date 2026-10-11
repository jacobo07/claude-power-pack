# S7b receipt
Status: DONE

Session breaker tripped at call 46 (limit 45); closed out with the slice below. Residual in the last section.

## Claims
1. `--live` CLI: `python tools/autonomy_gates.py --live [chain.json]` builds state from programme_status.project + ledger goal view (`live_state`, `_ledger_spend`). Code written; NOT_PROVEN: not run, and no test of the live spend_agreement comparison was added (breaker).
2. Release re-admit: `release_owner_hold` calls `readmit_for_relay` (packet + route sha intact -> re-admitted). PROVEN: test_gsd_mission_chain.py 13/13 incl. V-S7B-RELEASE-READMITS and red V-S7B-RELEASE-SHA-CHANGED-NO-READMIT.
   Limit: only covers a CONSUMED ADMISSIBLE admission; a mission never admitted (verdict none) has no recorded route and stays refused.
3. Breaker-halted unit with residual: R1 covers it. Added V-S7B-HALTED-WITH-RESIDUAL-NOT-STOPPED to test_gsdx_chain.py. NOT_PROVEN: edit made after the last run of that suite (previous run 19/19).
4. Attribution: ledger ROLES gains `interactive`; `goal_renew` charges it when the pane's binding record carries role=interactive (`write_binding(..., role=)`); `programme_spend` shows role interactive + `interactive_settled`; cap still counts it. PROVEN: test_programme_spend.py 17/17 (4 new checks incl. red unmarked pane stays productive).
   NOT_PROVEN: nothing yet WRITES role=interactive for a pane entering a goal root (the JS goal_binding hook twin is untouched).
5. Compiled patterns: manual re-arm -> chain (gsdx_chain), manual landing -> land_worktree; both already in REFLEXES (coverage 8/8). Nothing further recorded.

## Next unit must know
- Run test_autonomy_gates.py, test_gsdx_chain.py, then add the live spend_agreement test (inject status+ledger into `live_state`, differing settled -> FAIL).
- Wire the interactive role writer (hooks goal_binding.js + write_binding role) for panes whose cwd is in a goal root.
- Changes are uncommitted until the commit that carries this receipt.
