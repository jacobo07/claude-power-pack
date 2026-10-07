# E5 receipt -- live savings probe for R2

VERDICT: UNDECIDED

## What happened
- The probe did not run. The session cap was 500,000 processed tokens, which is 1 call at this repo's measured per-call floor. The probe needs at least 6 calls: read the CLI, create two worktrees, run two ON probes, meter both with spend(sid), remove the worktrees.
- Wrote vault/programs/cognitive-economy/gen2/evidence/tranche/E5-probe.json, labelled ESTIMATED. Expected delta = 605 tokens (chars/4). Measured delta = null.
- No code changed. No worktrees were created, so none were left behind.

## Commands and exit codes
- One PowerShell call: wrote E5-probe.json and this receipt, then ran git add and git commit with a pathspec. The commit hash is in the git log, not here, because the receipt cannot contain its own hash.
- tools/test_listing_floor_probe.py: NOT RUN (no budget left).

## Mutation
- None. No gate was added or changed, so there was nothing to mutate.

## Physical tool calls
- 1

## Semantic boundaries (named decisions)
- D1: Stay inside the cap and write an honest ESTIMATED result. Not chosen: running the probe and overrunning the cap.
- D2: Name the unverified premises (the probe CLI, the spend() signature, the test file) instead of asserting they exist.
- D3: Record the confounders (cache state, global CLAUDE.md size at run time, per-session hook injection, chars/4 heuristic) so a later MEASURED run can control for them.
- Next: re-dispatch E5 with a cap of at least 6 calls.

COMMITS: none