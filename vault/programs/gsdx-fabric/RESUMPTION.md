# gsdx-fabric RESUMPTION (coordinator pane, updated 2026-10-15)

**Identity.** GSD X Reconstruction Fabric = gsdx-factory Part C, goal `gsdx-factory-2`. Plan:
`vault/plans/gsdx-fabric-master-plan-2026-10-14.md` (in the fabric worktree). Live chain: `vault/programs/gsdx-fabric/chain.json`
(this repo). Fabric worktree: `C:\Users\User\Apps\pp-gsdx-factory-2\.claude\worktrees\fabric` (branch gsdx-factory/fabric,
NEVER pushed anywhere but the GEX44 bare repo via the launcher; fixtures hold disc-derived data). Workers run on GEX44 clone
`/home/kobii/missions/gsdx-fabric` only through the Owner-run launcher `C:/Users/User/fabric-unit-gex44.ps1 -Unit <U>`.
Kit: `C:/Users/User/fabric-kit/` (driver.py, run-unit.sh, prompt-<U>.txt, watch-unit.ps1).

**State.** Sealed (receipt + coordinator re-run of every gate + mutants red): F1 34/34, F2 33/33, F4 41/41, F3b 36/36
(c888ecd0; functions/xrefs PARTIAL, so F3c NOT compiled), F6 28/28 (7508e8f3), F7 43/43 (5b9c7612, re-pinned 49b9ea22 for d12 modules), F5 DONE slice 20/20 (6d07f05d,
after F5 + residual F5r; 3 compiler replays NOT_LIFTED). F8 in chain (route S), lease L13 open (cap 2,160,000), not launched.
Programme 57,817,916 (capital 63c090d4, Owner +6M 2026-10-15), settled 47,620,631.

**Coherence anchor.** `mission_spend.py programme-status --goal gsdx-factory-2` shows lease L13 and settled 47,620,631 until
F8 settles; fabric worktree HEAD 6d07f05d = GEX44 clone HEAD before F8 commits.

**Decisions.** Units route M unless the packet says S (F3b on S needed two residuals; ~70k tokens/message). Never edit an armed
packet: residuals get a new prompt-<U>r.txt. F7 Birth lists every module: a unit adding a module re-pins F7 in its own commit.
Stop-loss in capital 63c090d4: F5r without a committed receipt returns to the Owner before F8.

**Next 3 actions.**
1. Owner runs `-Unit F8 -Stop 2000000 -Turns 30` (prompt-F8.txt ready; capital stop-loss tripped literally on F5r's
   uncommitted receipt, so F8 needs the Owner's go).
2. On F8's watcher result: verify on GEX44 (git log, asm grep, all gates + mutants), ff the worktree, settle L13 --measured.
3. Commit F8's WU-F9.md, append F9, then KV/UKDL closeout and the programme close.

**Start.** Read this file, run programme-status, read the newest `run-<U>/result.json` on GEX44, continue at the first action.
