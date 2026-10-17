# Requirements — experiment-admission (v1)

Authority: `vault/specs/experiment-admission.md` (APPROVED 2026-10-17, Owner "y"). Read it first; it lists the
existing owners to extend, the contracts, the acceptance gate and the budget. This file holds the facts the
arming pane established, so no worker re-derives them.

## Facts (reality scan 2026-10-17, pane 88ca6ab1)
- Code work happens in the git worktree `.claude/worktrees/experiment-admission` (branch `feature/experiment-admission`).
  The main checkout is shared by other panes (67 dirty files at seal); never commit there except these workstream files.
- Two Builders (TB) repo: laptop `C:\Users\User\Desktop\Cursor Projects\Wii Projects\LEGO-SW-Two-Builders` (read + fetch),
  writer clone on GEX44 `~/missions/tb-m2` (`ssh gex44`, BatchMode). TB HEAD a636220. TB mission m-f9290d78278f stays HELD.
  Coordinator run scripts: GEX44 `~/missions/p3N_run.sh` (p38 newest). Pattern: build -> wit-extract disc gate -> commit prereg
  -> ledger AUTHORIZED -> `TB_DOLPHIN_LOG=1 tb_local.py run` -> ledger CONSUMED. Laptop: `git fetch ssh://gex44/home/kobii/missions/tb-m2 HEAD`
  + ff-merge, then `python tools/gex44/ledger_reconcile.py --apply` (from the TB root; ledger at 149 events, 0 violations).
- Run scripts p32-p38 never called `tools/prereg_lint.py` (a ROUTING fault: the lint existed and was bypassed).
  `prereg_lint.probe_keys` reads only the PROBES dict literal; P38's probe is a post-dict assignment, so the lint would reject it.
- Measured incident costs (processed tokens): P25 3.65M, P26 5.54M, P27 ~4.15M, P28 2.40M, P29 4.58M, P30 1.50M,
  P31 3.54M, P31b 1.58M (workers; sources: goal file lines 21-111). P31c-P38 are coordinator-pane runs, not yet measured.
- WompRat state after P38: the hub door line (`Spawn_MainRoom`, MainRoomDoor) made every visible patron (P37). With
  type=WompRat it made nothing (P37). `character "womprat" resident` in Levels/Map/map.txt did not help (P38).
  Confound: every stock womprat spawn uses a womprat script (MosEisley_B AI/level3.scp `script=AlleyWompRat`,
  MosEisley_D AI/level2.scp `script=CoinRat`, EndorBattle_C `script=trailertrash`); the hub lines all used `script=party`.
  The MainRoomIdle locators have never been on camera (P36). The hub reads every level's .txt in one sweep (FileMon).

## Owner answers (2026-10-17)
- Tranche 30M HARD, re-forecast at 20M.
- Canary scope: one gate-admitted P39 and its verdict. Finishing TB phase 5 is out of scope.
- Commit locally; push `feature/experiment-admission` only at the done-gate.
- GEX44 slots for TB `tb-disc-boot` runs are under grant OG-TB-2026-10-14-UNTIL-FINISHED (each AUTHORIZED+CONSUMED).

## Never
- No parallel GSD, mission runtime, experiment OS, ratchet or prereg format. Extend the owners named in the spec.
- No WompRat-specific code in PP modules: TB specifics stay in the TB repo and the corpus.
- No PASS from UNKNOWN, INCONCLUSIVE, an unqualified instrument or a candidate visual verdict.
- No reset, stash, clean or force-push; pathspec-scoped commits; verify `git log -1` after each.
