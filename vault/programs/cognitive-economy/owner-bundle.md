# Cognitive Economy Program -- Owner bundle

One line per Owner decision, tagged with its pillar. Nothing here was asked mid-run; each item is what the
campaign could not do itself under its envelope.

- [RUN] Merge branch `cognitive-economy/autonomous-run` (worktree `.claude/worktrees/cognitive-economy`, created
  from 8b62b6ce) into `feature/knowledge-acquisition`. The harness refuses background edits in the shared
  checkout, so every campaign commit lives on that branch; the done-gate passes there, and passes on
  `feature/knowledge-acquisition` only after the merge. Command:
  `git -C <repo> merge --no-ff cognitive-economy/autonomous-run`.
- [L] Apply compound steps 7+8 to the live state and switch the call site: make `/cpp-compound` step 7 and `tools/compound_unattended.py` call `python vault/programs/cognitive-economy/compound/steps78.py --state ~/.claude/state/compound-learnings.json --project <pid> --marker <cwd>/LEARNINGS_PENDING.md` instead of doing the mutex/merge/rename/unlink by hand. Proven on temp copies by `gates/gate_compound78.py` (green, and red under `--break-rollback`); the live file was never written.
- [B] Decide the remaining rules->skills moves, one yes per move. 13 global rules are still resident in full
  (56,861 B, listed in `evidence/B-T-floor-and-gc.md`). The bytes are a ceiling, not a saving. Moves 1-3 carried an
  ablation; the 2026-09-30 moves carry none. The campaign executed no move.
- [T] Declare or wire the 14 DORMANT_TESTED orphan modules (each has a test, but no live surface reaches it), via
  `vault/liveness/reachability_registry.json` (LIBRARY / PLANNED) or a caller. 8 of them, plus the 3
  PACKAGE_INTERNAL units, are `modules/knowledge_acquisition`, which is the current branch's subject. No module is
  proposed for deletion (RETIRE_CANDIDATE = 0). The 142 skills not invoked in D-W7 are handed to the C owners and
  are not a removal request.
- [R] UC-04 -- promote into `vault/knowledge_base/ukdl-universal.md` the trap "a shared-checkout progress fingerprint
  makes a no-progress halt unreachable" (`tools/gsd_mission.py` progress_fingerprint; handoff J). The text is in
  `ukdl-candidates.md`. The campaign did not write to the peer-hot file (audit G10).

## Disposition of each item (2026-10-05, W7)

Owner decisions 1-7 were given on 2026-10-04 (verbatim in session 0f1368ee); ledger `state.<P>.owner_decision`
quotes the ones that bind a pillar. A closed item says how the obligation closed, not that a capability is active.

- [RUN] DONE: merged as `11470e92` (24 mission commits, campaign paths only).
- [L] WIRED, not ACTIVE: decision 2; `/cpp-compound` step 7 calls steps78.py since `f207585b`. ACTIVE needs the
  first real run's receipt (ADVANCED, with `compound-learnings.json.bak` written inside that run's window).
- [B] DEFERRED_BY_OWNER_QUOTA (decision 3), still open as an effectiveness obligation. E1 approved on 2026-10-05
  as a grouped set first (Owner answer: "Approve, E1 after reset"), then moved forward the same day: "do the
  17M tokens thing now by the way, but on GEX44".
  The terminal moves only on E1's result, never on this line.
- [T] DONE as decided: decision 4. Five modules declared DORMANT in `0ea53eef` (craif/oier,
  dataset_first/transduction, done_gate/architectural_truth, fable_distillation/fd_04_acceleration, sqi/ratchet),
  each note naming its test. The 8 modules/knowledge_acquisition modules stay with their owner. Gate offenders
  66 -> 61.
- [R] UC-04 DONE: decision 6; promoted in `ecb5977a`. CBR half handed to modules/tower (`handoffs/R-cbr.md`).
