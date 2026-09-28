# External Capability Assimilation — resumption contract

**Read this first; it is self-contained.** Spec: `vault/specs/external-capability-assimilation.md`.
Worktree `C:\Users\User\Apps\pp-assim`, branch `feat/external-assimilation`; live checkout
`C:\Users\User\.claude\skills\claude-power-pack` on `feature/knowledge-acquisition` (hooks and every
running mission load code from THERE). Coherence anchor: both branches and both remotes at the same
head (`git ls-remote origin` shows one sha for both); last go-live `398482b`.

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
- T11: `m-27f9f1ab9fb6` HALTED at epoch 1 (never rotated). Replacement `m-860e4176f1d6` armed 21:49
  Madrid in `Desktop\Cursor Projects\gsd-long-smoke` (e6275c3), 3 cycles / 1.5 h, wall 22/24/20.

## Next 3 actions
1. After 20:05Z read `~/.claude/state/night-research/reports/` on the VPS (kobicraft@204.168.166.63,
   key `~/.ssh/kobicraft_vps`). Candidate -> manifest night-research may go LIVE (caller = the
   systemd unit, tools/systemd/cpp-night-research.service); another error -> diagnose from the report.
2. When `m-860e4176f1d6` ends: `python tools/gsd_epoch.py certify --mission m-860e4176f1d6` from
   the live checkout. Rotation observed = T11 done; none = say so and why.
3. Final handoff block. Mission stays PARTIAL on items 22/32/33 (owner state: Goal Spine has no live
   invoker, UCR-CIF unmerged). Owner step still open: `python tools/install_reviewer_contract.py --install`.

## Start instruction
`git -C C:\Users\User\Apps\pp-assim log --oneline -8`, `python tools/test_assimilation_manifest.py --no-proofs`,
then action 1.
