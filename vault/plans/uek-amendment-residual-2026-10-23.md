---
covers: [uek, uek-amendment-residual, cpp-fsck, aser-disposition, ctx-rent-a2-reconcile, slice-b-receipt, zombie-worktree]
status: WITHDRAWN 2026-10-23 ~15:45 (Owner chose option 1 after raising ctx-rent-a2 to 60M): R1-R6 run in pane 36d35fab on goal ctx-rent-a2, hard 5.0M. UEK owns nothing from this card. Was: OWNER-DIRECTED FOLD (785a9c6b).
priority: AFTER every UEK phase; only inside remaining goal-uek authority. If uek authority cannot cover it, return to the Owner; never raise 38M silently.
---

# UEK amendment: residual stages R1-R6

Source plan: `vault/plans/incremental-kernel-residual-2026-10-23.md` (commit aa97ebf8, sha256 1ee344b3...8bfb).
Read its sections 1-4 for the measured reality; not repeated here.

## Split by where the work can run
GEX44 worker (code only, fixtures copied in):
- R4 `rollover.py dispositions` read-only view (capsule -> claim -> verdict -> failure class).
- R5 `tools/cpp_fsck.py`, zero model, read-only, 6 checks with production fixtures + paired controls + mutation drill on a copy.
- R6 KV/FIOS/UKDL pattern after a dedupe check.

UEK coordinator on the laptop (subjects are laptop-local):
- R1 ctx-rent-a2 economics. **State changed this session, read first:**
  - 15:20-15:22 pane 36d35fab settled the three LEAKED leases with `goal-settle` (no --measured, transcript-derived):
    47f3da08 (hold 952,270), 262be369 (hold 1,060,540), b8ff709c (hold 750,000).
  - The b8ff709c settle charged about 6.87M (settled 12,076,304 -> 18,943,657), far above its 750,000 hold. That session had
    a `prebind` row measured 1,021,626 and no settle mark, so the mark-capped path in `goal_settle` (mission_spend.py:650-656)
    did not apply. Suspected pre-binding attribution, the class of [[project-ce-lifecycle-v]]. UNVERIFIED: the check was
    refused by the goal-budget guard.
  - Result: lease L1 remaining -5,360,817; programme 30M, settled 18,943,657, executable 10,639,183. Pane 36d35fab
    is fenced (bound, lease crossed) and holds a 417,160 open hold of its own; settle it after `econ detach`.
  - Next: decide from the transcript whether 6.87M is real spend or pre-binding history; if history, `goal-correct`
    (note: goal-correct does not unbook a lease). Then label `lease_remaining` vs `programme_executable` in goal-status.
- R1b regenerate ctx-rent-a2 RESUMPTION_FILE (stale: still says "do Slice B").
- R2 Slice B receipt: file component already measured (139.8K -> 96.0K chars, -31%; MEMORY.md +4.2K regrowth) +
  one fresh headless session through `tools/context_floor_census.py` vs the 122,093 floor.
- R3 worktrees `Apps\pp-ctx-rent` (SUPERSEDED) and `Apps\pp-ce-lifecycle-v3` (DURABLE_WAIT): save patches to
  `vault/salvage/`, record lifecycle rows. No deletion.
- Hand-off already in the source plan: `chain_tick.ps1` should read `parked` before the RAM pre-check.

## Budget
Source plan P80 3.75M, hard 5.0M, charged to goal `uek` per the Owner's fold. Lowest priority in the mission.
