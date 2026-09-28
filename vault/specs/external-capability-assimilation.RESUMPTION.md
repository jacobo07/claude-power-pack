# External Capability Assimilation — resumption contract

**Read this first; it is self-contained.** Spec: `vault/specs/external-capability-assimilation.md`.
Worktree `C:\Users\User\Apps\pp-assim`, branch `feat/external-assimilation`; live checkout
`C:\Users\User\.claude\skills\claude-power-pack` on `feature/knowledge-acquisition` (hooks and every
running mission load code from THERE). Coherence anchor: both branches and both remotes at the same
head (`git ls-remote origin` shows one sha for both); last go-live `c842f23`.
**Go-live hazard (2026-09-28):** `merge --ff-only` in main failed half-way with "unable to unlink
tools/gsd_mission.py" -- a sweep pass was importing it. 4 of 5 files were written, HEAD did not move.
Check `gsd-sweep-heartbeat.json` for `"outcome":"running"` before the ff; if it half-applies, verify
the written files equal the branch (`git diff --name-only <branch> -- <files>` empty), restore them
to HEAD, and ff again.

## Go-live pattern
Commit in pp-assim; re-read main HEAD; if main moved, merge it into the branch first (docs from other
panes land there); branch files vs main's dirty set must not overlap (~600 paths dirty there from
another writer -- never commit in main); `merge --ff-only` in main; rerun there
`tools/test_state_isolation.py` (runs all 38 long-run/rollover/assimilation suites under the write
audit) + `node tools/test_gsd_stop_continuation.js`; push both.

## State (2026-09-28 ~21:55 Madrid)
- Red team R1 (0 crit/0 high, fixed 58629ff) and R2 (claims vs code) DONE. R2 fixes `1b5247c`:
  manifest status IMPLEMENTED (built, proof exits 0, no production caller); LIVE now needs a
  gate-checked `caller`. 14 LIVE / 16 IMPLEMENTED / 5 PLANNED; ASSIM 15/15. The Ralph Stop hook is
  opt-in (`continuation: stop-block`, on 0 of 12 markers) -- stop-directive + decision-log are
  IMPLEMENTED, not LIVE.
- Night research: first REAL pass (19:01Z) died rc=143 in 1.46 s -- the worker read the vendor's
  `deadlineMs` duration as an epoch time. Fixed `cb47e78`, pinned by V-NIGHT-REAL-WORKER-DEADLINE-IS-DURATION
  (mutant reproduces the VPS signature). VPS `~/pp-night` at 398482b, smoke 12/12 there. Second and
  last pass of the night fires 20:04Z.
- Isolation ratchet now also watches `<checkout>/vault` (`cfa1e22`): test_mission_watchdog was writing
  the live progress.md. 43/43 from both checkouts.
- T11 (updated ~21:13Z): both earlier smokes stalled on the SAME cause -- the worktree's STATE named
  the shipped v1 milestone, so GSD saw 0 phases and the sweep (the real continuation owner) held the
  relay silently. Not Ralph, not host re-invoke. Lesson T-FIX-IN-THE-TREE-THE-JUDGE-DOES-NOT-READ-001
  in `vault/lessons/external-assimilation-t8-t12-2026-09-28.md`. Fixes live at c842f23: `551bdee`
  bounded GSD hold -> BLOCKED, `ad8f398` `<synthetic>` row is not context 0, `430b5de` drill copy_dirs.
  Fixture repaired in the smoke worktree (`66c490b`, milestone v2.0, phases 9-12, GSD says OK 0/4).
  `m-860e4176f1d6` HALTED by operator at epoch 2 after 1 rotation (both epochs hit the 22 % wall on
  their first turn; epoch 2 made no commit). NEW smoke `m-3e72c75c4a06` armed 21:11Z, production
  wall 35/40/30, 300k continuation ceiling, 6 cycles / 2 h, worker 1 `e050802d`.

## Next 3 actions
1. Watch `m-3e72c75c4a06` with one-shot reads of `~/.claude/state/gsd-autorun-ledger.jsonl` (no
   watcher; host at ~4 GB free). Wanted: >=2 `turn_continued` with a progress fp change, >=1
   `launch_cause` CONTEXT_ROTATION, commits in the worktree after it. Then
   `python tools/gsd_epoch.py certify --mission m-3e72c75c4a06` from the live checkout.
2. Night research: read `~/.claude/state/night-research/reports/` on the VPS (kobicraft@204.168.166.63,
   key `~/.ssh/kobicraft_vps`); LIVE only on a produced candidate, never on runtime alone.
3. Final handoff block. Mission stays PARTIAL on items 22/32/33 (owner state: Goal Spine has no live
   invoker, UCR-CIF unmerged). Owner step still open: `python tools/install_reviewer_contract.py --install`.

## Start instruction
`git -C C:\Users\User\Apps\pp-assim log --oneline -8`, `python tools/test_assimilation_manifest.py --no-proofs`,
then action 1.
