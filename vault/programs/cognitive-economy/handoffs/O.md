# Handoff [O] -- cognitive IR / state normalization -> Goal spine owner

Pillar: [O] cognitive IR / state normalization. Terminal: MERGED_INTO_EXISTING_OWNER.

Owner (frozen): `modules/gsd_x/goal/` (the Goal spine: canonical durable-goal store).

## What was verified (2026-10-03)

- The spine is live and is the durable-goal store: `PP-GoalSweep` runs `gsd_x_goal.py sweep-all` every 5 minutes
  (`~/.claude/state/gsd-x/sweep_heartbeat.json`: `goals_seen: 1`); `python tools/test_gsd_x_goal_sweep.py` ->
  14/14; the epoch brief compiled from it (`modules/gsd_x/goal/brief.py:48`) -> 20/20 in
  `tools/test_gsd_x_goal_claude_providers.py`.
- The generated KSR view was falsified earlier (frozen rule); nothing here reopens it.

## Finding handed to the owner (audit G1-G4, `vault/audits/cognitive-economy-phase4-audit.md`)

**Whole-tree verdict pin makes Goal-spine closure unreachable in a shared checkout.**

- `modules/gsd_x/goal/git_state.py:124-133` `tree_id()`: when the declared scope is clean it returns
  `git:<HEAD^{tree}>`, the WHOLE repository's tree, whatever the scope paths are. Every SATISFIED verdict
  carries that id (`convergence.py:347-352`), and the judge refuses a verdict whose tree differs
  (`judge.py:132-136`). In a checkout shared with peer panes, any peer commit moves HEAD^{tree}, so every banked
  verdict goes stale and is re-dispatched (`reconcile.py:186-203`). Closure becomes a treadmill (G2).
- When the scope is dirty, `tree_id` falls back to an rglob content hash of the scope paths (lines 134-142);
  with the default scope `["."]` that hashes the whole repo and changes on any peer keystroke.
- A mission bound with `bind-mission` is an epoch in state `running` for its whole life; open epochs block
  `goal_closure` and the reconciler returns WAIT before gate dispatch (G1).
- `gsd_x_goal.py status --json` carries no obligation list (G3), so an external verifier cannot read SATISFIED
  ids from it.

Suggested direction for the owner (the owner decides; the campaign edits nothing under
`modules/gsd_x/goal/`): pin a clean-scope verdict to the scope's own tree entries
(`git rev-parse HEAD:<path>` per scope path) instead of `HEAD^{tree}`, and expose obligations with their
disposition in `status --json`.

## How this campaign stayed correct without it

The campaign's authority is the committed ledger `vault/programs/cognitive-economy/ledger.json`; the done-gate
`tools/test_cognitive_economy_program.py --final` re-runs every IMPLEMENTED pillar's gate in one pass, so it needs
no tree pin. The run also works in a dedicated worktree (audit G2(a)).

## What the owner keeps

The goal store, its contract, convergence, judge, sweep and all of their tests.
