# W5 receipt
Status: PARTIAL -- merge DONE (bd5af362), 11/11 gates green in the merged tree, NOT deployed (no Owner OK).
COMMITS: dgl/durable-goal-lease ef6bd810 (source, all 11 gates green there); merge bd5af362 on dgl/live-merge (parents 829b8ac5 + ef6bd810, scratch worktree C:\Users\User\.claude\jobs\20af2491\tmp\mwt).
Live checkout = C:\Users\User\.claude\skills\claude-power-pack on feature/knowledge-acquisition 829b8ac5 (no worktree holds main; main=908b543 is an ancestor). Untouched: no copy, no schtasks change, no hook copy.
Premise broken: the packet assumed W1-W4 files can be checked out over live. Live already holds W1b/W2 ported under other hashes (d55f33c9, 95030b22, 3dd05871) plus OCA/econ-contain (a30db705, 9c88ebad, 999984d1) in the same files. Fork base d0c2077b, live is 192 commits ahead, 36 dgl commits.
Merge: 4 conflicted files (hooks/lib/goal_binding.js, modules/provider_routing/ledger.py, tools/mission_spend.py, tools/test_goal_lease.py); in every hunk live was a strict superset (quarantine, recovery/role accounting, OCA first-programme check) so resolved with --ours. No dirty live path overlaps the dgl file list.
Gates in merged tree: goal_lease 10/10, workspace_lease 10/10, succession 9/9, GOALCRASH 11/11, GOALDRAIN 6/6, GOALAUTOPSY 5/5, AUTOPSY 10/10, session_budget_admission 12/12, tranche_driver 27/27, hook_boundary 7/7; test_goal_budget_admission 58/59 (FAIL V-GOAL-AGENT-LANE: dispatcher carries the Agent lane and its no-event route). Not diagnosed: live's gate has 59 checks vs 54 on the branch.

## W5-r3 (2026-10-12, sessions 3ae2a3cb then c2be1789, lease L11 dgl:W5:r4)
- Gate fix: V-GOAL-AGENT-LANE now checks lane MEMBERSHIP (live's lane also carries cognitive_admission.js). Committed in bd5af362.
- test_goal_budget_admission 59/59 on 4 of 5 runs; one run 58/59 with the failing check unnamed (output truncated). Intermittent, open.
- test_tranche_driver: 26/27 with cwd=mwt, 27/27 with cwd=pp-dgl. V-DRIVER-REAL-GUARD-ADMITS-N-REFUSES-N+1 prices calls from the
  live session-floor of the CWD's project folder, empty for mwt (per_call=None). Environment-dependent, not a merge defect.
- Overlap (scratchpad overlap.py): live now feature/knowledge-acquisition e36b7506, 22 commits past 829b8ac5, 1188 dirty entries.
  dgl's 39 files intersect neither the dirty set nor the 40 files those 22 commits touch: 0 and 0.
- Side effect: settling 20af2491 / 4b246bb6 / 20f0feeb booked 4.5M into L10 and overdrew the 37M programme. Owner raised it to
  42,948,823 (capital packet 380bbee5, 'approve dgl only' 2026-10-12T13:59:31Z); L11 = 3,000,000.
- m-afd50917585a HALTED (hold_settled seq 17), owner_hold kept.

Remaining (needs Owner OK to deploy): live is no longer at 829b8ac5, so it cannot fast-forward to bd5af362; merge bd5af362 into
live e36b7506 (zero file overlap, expected clean), copy session_budget_guard.js to ~/.claude/hooks, re-point PP-DglChain-Tick,
run the step 5 smoke, then schtasks /run.
Calls: about 18 (W5-r2) + W5-r3.