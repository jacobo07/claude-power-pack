# External Capability Assimilation — resumption contract

**Read this first; it is self-contained.** Spec: `vault/specs/external-capability-assimilation.md`.
Worktree `C:\Users\User\Apps\pp-assim`, branch `feat/external-assimilation`; live checkout
`C:\Users\User\.claude\skills\claude-power-pack` on `feature/knowledge-acquisition` (the hook
dispatcher and every running mission load code from THERE). Both pushed at `8ee41c6`.

## Thesis
Every capability (Genesis 21 modules + runner, Context Budget, loop kit, self-continuation) gets ONE
CPP owner/disposition in `vault/assimilation/genesis-2026-09/ASSIMILATION_MANIFEST.json`.

## Go-live pattern
Commit in pp-assim; re-read main HEAD; check branch files vs main's dirty set (another writer keeps
~590 hook/doc paths dirty there -- never commit in main); `merge --ff-only` in main; rerun the live
gates there (test_gsd_mission, test_handoff_packet, test_mission_watchdog, test_gsd_long_run,
test_gsd_epoch, test_rollover_active_path, `node tools/test_gsd_stop_continuation.js`).

## Sealed (T1-T7 at 6fdd61a; this session)
`4f27cff` test isolation: runtime audit hook (tools/state_write_audit) proved d10bd31 left 46 marker
writes + live watchdog log/snapshot writes; fixed; ratchet `tools/test_state_isolation.py` (28 suites).
`46675ff` item 29 routing metrics · `96f753c` item 30 verified reuse (batch_drafts consumer; cannot
approve) · `7e12fcb` exp-successor-packet-002 registered BEFORE runs (001 withdrawn) · `c9f750d` T8
closed: packets by reference on `handoff --packet`, routes in `gsd_epoch certify` · `fe2be9c` item 22
task ledger MERGED into gsd_x/goal (attribution + AST ratchet), PLANNED · `8ee41c6` item 32 task
adaptation in contract.revise, PLANNED. Decision record: `vault/experiments/exp-successor-packet-002/REPORT.md`.

## Blockers / truths a successor must not re-derive
- Goal Spine engine (gsd_x/goal) has NO live invoker (no command/hook/task reaches
  tools/gsd_x_goal.py; registry says UWCP S6). Items 22, 32 are merged there and stay PLANNED.
- Vendor credential-line filter blocks 441/1,091 Python files whole (322 only for "pass" + ":"/"=").
- ~/.claude/agents/pp-code-reviewer.md: HR-001, not written by the agent.

## Next 3 actions
1. T9 item 33 Charter Lab (UCR-CIF seam; construction worktree untouched), reviewer-contract
   installer (Owner runs it), rollover RESUMPTION reconcile (its owner's file: facts only).
2. T10 night research on the VPS (user Node 24 first; check VPS cron for gsd_x_goal).
3. T11 smoke mission + `gsd_epoch certify`; T12 red team, Knowledge Vault, UKDL, UCR-CIF, baseline.

## Start instruction
`git -C C:\Users\User\Apps\pp-assim log --oneline -8`, run `python tools/test_assimilation_manifest.py`
(re-runs every LIVE proof), then action 1.
