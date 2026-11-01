# ce-a3b-r: v2 milestone blocked on goal budget, plus what the stall exposed (2026-10-31)

Source: Owner-pasted transcript of the `pp-ce-a3b-r` pane (2026-10-08, ~17:30-18:03). Worktree
`C:\Users\User\Apps\pp-ce-a3b-r`. Nothing below has been started.

## State at write time
- Goal `ce-a3b-r` is spent and the session is TOMBSTONED: used 9,533,534 of a cap of 8,600,000 (settled 9,383,534, reserved
  150,000, lease L1). Source: the UserPromptSubmit `ECONOMIC STATUS` block. Re-check with
  `python tools/mission_spend.py goal-status --goal ce-a3b-r`.
- v1 (continuation-proven-live, phases 1-5) is archived under `.planning/milestones/`. `.planning/ROADMAP.md` has no active
  milestone. `/gsd-new-milestone` never ran, so `.planning/` is unchanged.
- `RESUMPTION_FILE.md` in that worktree was **overwritten**: uncommitted, +20 / -356 lines against HEAD. The previous content
  is intact in git at `8fb014fe` (verified 2026-10-31 with `git diff --stat`).

## Items, in rough order of leverage

1. **Repair the clobbered RESUMPTION_FILE before anything commits it** (S, Owner-safe). The new 20-line v2 block was written
   into the middle of the old file, and that file still carried live sections: the 2026-09-20 and 09-18 post-incident state,
   the F5 blocker, the GSD X router, and the SQI/USEA/DAIF/Crawl OS pointers. Fix: `git show 8fb014fe:RESUMPTION_FILE.md`,
   then put the v2 block on top as a new section and keep the old body under it. Do not `git checkout` the file, because
   that discards the v2 block.
2. **Owner: declare a successor goal id (or close ce-a3b-r)** (Owner decision). Options from the hook: `subelo 70M <goal>`
   from any pane, or close the goal. Until then nothing runs in that pane. `econ detach` frees the pane.
3. **Run milestone v2 under the new goal**: `/gsd-new-milestone`, then `/gsd-autonomous`. Scope is Owner-approved and comes
   from "Carried into the next milestone" in `.planning/ROADMAP.md`:
   - a re-derivable instrument for the UserPromptSubmit chain-deadline measurement (v1 phase 2);
   - prove the reap path by deleting a real stale entry;
   - exercise `continuation_transport` delivery and confirmation, as a second producer of `resume_confirmed`
     (overlaps C3 in `2026-09-23_torre-universal-out-of-scope.md`);
   - one cleanup phase for the five pre-existing mirror DRIFT pairs (overlaps C2, same file).
   Excluded: the `/cpp-compound` steps 7+8 fix (item 4).
4. **Unblock the `/cpp-compound` steps 7+8 fix.** Another writer's abandoned change in `tools/compound_unattended.py` blocks
   it. That file is also ` M` in the PP main tree (`feature/knowledge-acquisition`, git status 2026-10-31). Find out whose it
   is and whether it is the same change before touching it (`concurrent-writers-shared-tree`, `destructive-state-authorization`).
   The stuck loop itself is already tracked (C1, and `2026-10-27_ccr-a2-landing-remaining.md`).
5. **Goal cap is not a cap: spend overshot by ~933k (10.8 %).** 8,707,222 was already over the cap when the first refusal
   fired, and spend kept rising to 9,533,534. Measure where the overshoot comes from. Candidates: settle lag (spend is
   settled from the transcript after the fact), the 150k reservation, and the allowed closeout writes still costing a full
   turn of context each. Decide whether the gate should refuse at `cap - reservation`. Do not raise the cap to explain the
   overshoot.
6. **Budget hook fails with ETIMEDOUT on PowerShell**: `PreToolUse:PowerShell hook error: GOAL BUDGET ... did not answer
   (ETIMEDOUT)`. It failed closed, which was the right outcome on a spent goal. But a timeout is not a verdict. Check that
   the refusal message names the timeout as a timeout, and that on a live (unspent) goal it does not block a call it would
   have allowed (`guard-event-reachability`, `technical-failure-to-product-state`).
7. **The agent could not tell whether its overwrite destroyed a file.** The read-before-write check was refused by the same
   hook that allowed the write. So the hook's allow-list lets a blind overwrite of `RESUMPTION_FILE.md` through. Either the
   closeout write must be append/create-only, or the allow-list must also permit a read of the target. Item 1 is the
   incident this caused.

Already tracked elsewhere, not duplicated here: the `claude_md_linter` 39,812-char WARN and FIOS IRR "tokens unmeasured"
(`2026-10-03_token-economy-wave2.md`, rows 15 and context); B64 (native wall, `CHAIN_DEADLINE_MS` for Stop-chain) in
`2026-10-03_handoff-harvest.md`.
