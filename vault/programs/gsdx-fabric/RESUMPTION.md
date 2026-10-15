# gsdx-fabric RESUMPTION (coordinator pane, updated 2026-10-15)

**Identity.** GSD X Reconstruction Fabric = gsdx-factory Part C, goal `gsdx-factory-2`. Plan:
`vault/plans/gsdx-fabric-master-plan-2026-10-14.md` (in the fabric worktree). Live chain: `vault/programs/gsdx-fabric/chain.json`
(this repo). Fabric worktree: `C:\Users\User\Apps\pp-gsdx-factory-2\.claude\worktrees\fabric` (branch gsdx-factory/fabric,
NEVER pushed anywhere but the GEX44 bare repo via the launcher; fixtures hold disc-derived data). Workers run on GEX44 clone
`/home/kobii/missions/gsdx-fabric` only through the Owner-run launcher `C:/Users/User/fabric-unit-gex44.ps1 -Unit <U>`.
Kit: `C:/Users/User/fabric-kit/` (driver.py, run-unit.sh, prompt-<U>.txt, watch-unit.ps1).

**State.** Sealed (receipt + coordinator re-run of every gate + mutants red): F1 34/34, F2 33/33, F4 41/41, F3b 36/36
(c888ecd0; functions/xrefs PARTIAL, so F3c NOT compiled), F6 28/28 (7508e8f3), F7 43/43 (5b9c7612). F5 breaker-stopped with
no commit (salvage: GEX44 `gsdx-fabric-stage/f5-untracked/`); residual **F5r running** on lease L12 (cap 4,725,000).
Programme 57,817,916 (capital 63c090d4, Owner +6M 2026-10-15), settled 43,000,624. Packets committed, not yet in chain: WU-F8.md.

**Coherence anchor.** `mission_spend.py programme-status --goal gsdx-factory-2` shows lease L12 open and settled 43,000,624
until F5r settles; fabric worktree HEAD 505e644e = GEX44 clone HEAD before F5r commits.

**Decisions.** Units route M unless the packet says S (F3b on S needed two residuals; ~70k tokens/message). Never edit an armed
packet: residuals get a new prompt-<U>r.txt. F7 Birth lists every module: a unit adding a module re-pins F7 in its own commit.
Stop-loss in capital 63c090d4: F5r without a committed receipt returns to the Owner before F8.

**Next 3 actions.**
1. On F5r's watcher result: verify on GEX44 (git log, asm grep, gates f5/f1/f2/f4/f3b/f6/f7 + mutants, F7 re-pin), fetch and
   ff the worktree, settle L12 with `goal-settle --measured <processed>`.
2. Append F8 to chain (route S, lease cap 2,160,000, prompt-F8.txt ready), Owner runs `-Unit F8 -Stop 2000000 -Turns 30`.
3. After F8: commit its WU-F9.md, append F9, then KV/UKDL closeout and the programme close.

**Start.** Read this file, run programme-status, read the newest `run-<U>/result.json` on GEX44, continue at the first action.
