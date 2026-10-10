# WU-S1 -- Autonomy Convergence unit S1

Read `vault/programs/autonomy/PROGRAMME.md` first (session loop, continuation units, constraints).
Your scope: Plan section 2 item 1 + section 3 row 'Automatic known integration'.

## Do
Build tools/land_worktree.py + test (rebase onto live HEAD, overlap check vs live dirty paths, declared test list, ff-only, JSON receipt; conflict or red test = refuse, nothing landed; mutation drill). Then land, one at a time with the tool, cherry-picked onto feat/ucda first: (a) feat/ucda itself (A4 a21ab8bf + this programme); (b) gsdx_chain.py + gsdx_chain_tick.ps1 + its tests from C:\Users\User\Apps\pp-gsdx-factory-2 (branch gsdx-factory/v2, cherry-pick only those files' commits); after it is live, repoint vault/programs/autonomy/chain_tick.ps1 to the LIVE tool; (c) cost-collapse T1 f3b503e6 + T2 2b5b0ea5 from C:\Users\User\Apps\pp-cost-collapse; (d) gsdx_reforecast.py 610808c5; (e) dgl W1b c5f22af9 + W2 31f9b5f4 from C:\Users\User\Apps\pp-dgl. Each landing: its tests green before and after; a red or conflicting landing is recorded and skipped, not forced.

Receipt: `vault/programs/autonomy/WU-S1-receipt.md`.
