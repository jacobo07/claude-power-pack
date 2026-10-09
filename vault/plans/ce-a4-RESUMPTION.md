# RESUMPTION -- CE Amendment A4 estate rearm (goal ce-a4)

**Identity.** Worktree `C:\Users\User\Apps\pp-ce-a4`, branch `ce/a4` off 86ad6f16. Card
`vault/plans/ce-a4-estate-rearm-2026-10-08.md` (APPROVED 2026-10-08, Owner "go a4: 21.7M, gsdx migrate, deferrals
accepted", pane f883c056). Thesis: make the CE capabilities that already exist reachable, enforce the presence
baseline, migrate the estate by economics, chain units without a parent model.

**State (sealed).**
- Goal `ce-a4` declared: cap 21,700,000, root `c:\users\user\apps\pp-ce-a4`, host DESKTOP-PMT5BS8, since 2026-10-08T08:14:31.
- Mission m-b76843b319af (cost-collapse) put on OWNER HOLD; release only by W1a.
- Pane f883c056 stopped by its own session breaker at 651,154 > 0.6M (post-approval spend; the pre-approval scan
  is outside the goal). Overrun ~51k on the issuing call.

**State (pending, UNCOMMITTED in this worktree).** `vault/programs/cognitive-economy/a4/W0.md` (packet) and this file.
`route-W0.json` NOT written yet. W0 NOT armed.

**Decisions.** Units are compiled packets on slim workers; arm them WITHOUT --model/--autocompact (the U6a resolver
picks; shadow applies Sonnet + policy ceilings) and confirm from the ledger row `baseline_resolved` + the worker's
raw transcript model id. A coordinator pane does at most: read this file, arm one unit, update this file, exit. A
crossed cap stops; it is never raised.

**Next 3 actions (fresh pane, cwd = this worktree, so the pane binds to ce-a4 by root).**
1. Write `vault/programs/cognitive-economy/a4/route-W0.json` =
   `{"envelope":{"target":1000000,"warn":1100000,"stop":1200000,"calls":30},"workers":[{"name":"ce-a4-W0","profile":"slim-t2","calls":28,"packet":6000}]}`.
   Commit W0.md + route-W0.json + this file (`git commit -F <msgfile> -- <paths>`).
2. Arm: `gsd_mission.py arm --cwd C:\Users\User\Apps\pp-ce-a4 --command "/gsd-autonomous" --no-launch --parallel-unit a4-W0 --rollover-protocol capsule-v2`;
   `envelope --mission <id> --wu-packet <abs path W0.md> --token-estimate 1.2M`; `admit --mission <id> --route <abs route-W0.json>`.
   Only ADMISSIBLE launches (the sweep launches PREPARED within 5 min). Check `status` + ledger for `baseline_resolved`.
3. When `W0-receipt.md` lands: verify its tests exit 0 yourself, then arm W1a the same way from the worker-written
   W1a.md/route-W1a.json. W1b runs in goal ce-a3b and is blocked until the Owner copies the narrowed GOAL_STATE
   regex into `~/.claude/hooks/session_budget_guard.js` (HR-001; the fix itself is a W1b deliverable).

**Start.** Open a fresh pane with cwd C:\Users\User\Apps\pp-ce-a4, read only this file, run step 1.

**2026-10-09 consolidation (Owner y, pane 0f9b771b).** Goal ce-a4 cap lowered to 16.6M (F0 reforecast, main repo A4 section 6c, commits c8fc9f8a/58d2977b). W0.md extended with the F0 slim-floor check (> 60k -> stop for re-approval) and the P0 proof. Duplicate W0 m-4bf75e9e8ecc is held + superseded: ignore it. The steps above are unchanged otherwise.
