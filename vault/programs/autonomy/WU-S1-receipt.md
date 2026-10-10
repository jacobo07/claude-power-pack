# WU-S1 receipt
Status: DONE

Tool: tools/land_worktree.py + tests/test_land_worktree.py (10 tests incl. conflict, overlap, red test, live-moved, post-red, no-tests, mutation drill). Per-landing JSON receipts in vault/programs/autonomy/landings/.
Commits landed in live (ff-only, tests green before AND after, each via the tool):
- (a) feat/ucda: A4 a21ab8bf + programme + tool -> live b97ced4a  PROVEN (test_tier_routing, test_land_worktree)
- (b) gsdx_chain.py + tick + test (final content of gsdx-factory/v2 5e835a8a; 5 commits' worth, these 3 files only) -> 173a25dfd  PROVEN (test_gsdx_chain rc 0); chain_tick.ps1 now points at the LIVE tool (commit 8f5090f9)
- (d) gsdx_reforecast 610808c5 -> b50e58be  PROVEN
- (e) dgl: c5f22af9 + 1bfb30cf + d3f397ff + test part of b2dc5812 + db9c2153 + 47aa4d77 + 31f9b5f4 + fixtures of 58b83582 -> 046df5d4  PROVEN (goal_lease 10/10, workspace_lease 10/10). W1b/W2 alone were red (RED-first test, missing impl and fixtures), so the dependency commits were included.
- (c) cost-collapse T1 f3b503e6 and T2 2b5b0ea5: SKIPPED, BLOCKED_CONFLICT. T1: content conflict in tools/gsd_mission.py and tools/test_grammar_default.py (deleted on feat/ucda base). T2: content conflict in tools/mission_spend.py (overlaps dgl d3f397ff/47aa4d77 edits and live). Cherry-pick aborted, nothing forced. Needs a human/worker re-port against live HEAD.
NOT_PROVEN: post-landing tests ran in dirty live only for the declared lists; no full-suite run.
Next unit: land with `python tools/land_worktree.py --worktree <wt> --live <live> --test "<cmd>"`; script-style tests (sys.exit at import) must be declared as `python tools/x.py`, not pytest. Do not land commits that are RED-first alone. Calls used: ~30.
