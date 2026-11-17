---
spec: ascension-autopilot-self-unpark
status: IMPLEMENTED (pending deploy)
tier: T2 (autopilot behaviour change: three park causes stop waiting on the Owner)
covers: [ascension-autopilot, evolve, checkpoint discovery, running_watch]
owner_decision: "Owner 2026-11-17 pane 08cba76c: 'b' (root fix, not the per-lane un-park)"
---
# Ascension: the autopilot stops parking on its own mechanical faults

## Problem (observed 2026-11-17 12:08Z)
7 of 8 lanes parked between 00:07Z and 01:34Z and sat ~10.5 h; 83M of the 500M day spent. Three of the causes were the
autopilot's, not the work's:
1. EVO packet refusals (S112T "no 'rival' in the phases", S114M "caps 10.5M > 10M") parked on the FIRST plan; the
   bounded re-plan (POLICY_REPLANS) only covered the base policy.
2. Checkpoint holds the autopilot could not read: S111C (FIFATC, F17 SUPPORTED, held-out 11/40) held CHECKPOINT_COMPLETE
   with evidence null; S113R (WSR) wrote "branch worktree-s113r commit ac2201a: evidence/.../checkpoint.md", taken whole
   as a path -> CHECKPOINT_ON_BRANCH with 0 holders.
3. S108W (WIIPARTY) went BLOCKED on a host permission prompt with no hold; the lane read RUNNING and nothing said so.

## Design
- `plan_and_arm.checked(p)`: base policy, then (policy-clean plans only) `evolve.packet_problems`; the re-plan loop runs
  on either refusal, told the reasons; the last refusal parks as before (`_refused`, kind evo for EVO). The policy itself
  is unchanged. `replan_feedback` adds one sentence on EVO packets.
- `hold_checkpoint`: evidence containing whitespace is prose; the last `*.md|*.json` path named in it is the checkpoint,
  none -> the residual.
- `checkpoint_from_branch(product, base, head)`: for a hold naming no path, the most recently committed
  `*checkpoint*|*residual*.md` in `base..head` that exists at head. No base, or base == head -> '' (an older generation's
  checkpoint is never judged as this hold's). Then the normal discovery/judge path.
- `evolve.discover_checkpoint`: local branch tips count as holders besides worktree HEADs (a removed --worktree keeps
  its branch); one commit counts once; a tip that is an ancestor of another holder is the same line. Still exactly one
  holder, fast-forward only, clean product.
- `running_watch`: a BLOCKED mission (blocker.at older than HELD_NOTICE_S) is told once per mission and blocker, with
  what it needs. Not parked: an answered prompt resumes the mission and the lane must still see its checkpoint.

## Not changed
Day cap, envelopes, top-up terms, the policy checks, the judge, certify.decide. Lanes already parked stay parked until
un-parked (per-lane option (a), not chosen).

## Acceptance
`test_autopilot.py`: V-EVO-REFUSAL-REPLANNED, V-AP-HOLD-FREEFORM, V-AP-EMPTY-HOLD-FINDS-BRANCH-CHECKPOINT,
V-AP-NOPATH-{FOUND-ON-BRANCH, WINDOW-ONLY, NONE-NAMED}, V-EVO-CHECKPOINT-{VANISHED-WORKTREE, TWO-TIPS-PARKS},
V-AP-BLOCKED-NOTICE{,-ONCE,-WAITS}; mutants hold_freeform_ignored, nopath_never_found, nopath_any_window,
evo_branches_ignored killed (with replan_off, held_notice_*); whole gate AUTOPILOT_GATE_PASS.

## Rollback
Restore autopilot.py / evolve.py from the `*.bak-08cb-unpark-*` copies on GEX44 (or the previous mirror commit).
