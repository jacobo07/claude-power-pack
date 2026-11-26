---
covers: [held_launch, held_age, held_align, held_final_checkpoint, ascension_autopilot]
tier: T2
owner_turn: "2026-11-26 pane 31498a3e, Owner: \"go ahead y aumenta autonomia para que esto se hubiera solucionado solo\""
---
# Ascension autopilot: held launches repair themselves (round 8)

## PRD
At 21:51Z on 2026-11-26 all 8 lanes read RUNNING. No mission had a live worker. Three of them were stuck on
something no day-cap rollover fixes:
- **FIFA S392F.** It wrote `CHECKPOINT_FINAL: true` both on main (432c76d5) and on its work-tree branch (b0a65817),
  so the two diverged on that checkpoint. gsd_mission held every relaunch ("cwd diverged") from 14:57Z. The autopilot
  never judged it, because the mission was not terminal.
- **FIFATC S383C.** Its work tree was 2 commits ahead of main. The product's only uncommitted file,
  `evidence/f36/mutant_rc.json`, is not touched by the branch. It was held "behind_dirty" from 12:20Z (9.5 h).
- **WIIPARTY S400W.** BLOCKED on a host permission prompt. This one did reach alerts.json as a question.

Why nothing ended the first two:
1. `held_too_long` measured from the mission's `updated_at`. gsd_mission rewrites that on every touch, so the
   2-hour re-plan never fired. FIFA read "30 min" at 20:40Z after being held for 6 h.
2. The held notice reached only `owner_queue.md` on GEX44. alerts.json, which the laptop mails, had no held level.
3. Had the re-plan fired, it would have thrown the generations' finished work away.

## Behaviour
- **`held_age`**: the autopilot keeps its own first sighting per mission and hold cause in `ls.held_seen`, and drops
  it when the hold ends. `held_too_long` and the running_watch notice take the larger of that age and the
  `updated_at` age.
- **`held_align`**: runs from `HELD_REPAIR_S` (600 s) on, on every tick while the launch is held.
  - It applies only to a "launch held: cwd" reason whose work tree is a different tree of the same repository.
  - **Product behind the work tree:** if no uncommitted product change touches a path the branch changes, it runs
    `merge --ff-only`. Git keeps the uncommitted file.
  - **The two diverged:** if no path changed on both sides and neither tree has tracked changes, it runs
    `merge --no-ff` of the work-tree head into the product, then fast-forwards the work tree to the merge.
  - Each alignment writes a ledger row (`held_align`), a log line and a digest line.
  - Each refusal is told once per key and reason. A later tick still aligns once the obstacle is gone.
- **`held_final_checkpoint`**: looks for a checkpoint committed on the product since the base that is named after
  the generation (`checkpoint_s392f.md`) and whose last `CHECKPOINT_FINAL` declaration says true. If found, the held
  mission is judged through the normal checkpoint path, with `set_at` "held-final:<path>" (one judgment).
- **Order:** align, then FINAL checkpoint, then the old path (the re-plan at HELD_REPLAN_S, the running_watch notice).
- **`build_alerts`**: gains level `held` once a RUNNING lane's launch has been held for HELD_NOTICE_S by the
  autopilot's own clock. The alert reaches the mailed alerts.json.

## Never
- No reset, rebase, checkout, stash or force. Nothing uncommitted is discarded.
- No merge across shared paths. No acting on a work tree from another repository.
- No change to gsd_mission, the budget, the breaker, the certifier or the held-out.
- A host permission prompt (WIIPARTY) is not auto-approved. It stays an Owner question.

## Acceptance (V-AP-HELD-*, real git)
- AGE-OWN-CLOCK, AGE-CLEARS
- ALIGN-FF-KEEPS-DIRTY
- ALIGN-FF-REFUSES-OVERLAP (told once; aligns once the obstacle is gone)
- ALIGN-MERGE-NO-SHARED (3-parent check, work tree == product)
- ALIGN-MERGE-REFUSES-SHARED, ALIGN-FOREIGN-TREE
- FINAL-CHECKPOINT (the last declaration wins; another generation's file is never taken)
- ALERTS
- REPAIR-WIRED (lane_tick calls align, then FINAL, before the re-plan)

Mutants: held_age_trusts_updated_at, held_align_never, held_align_ignores_dirty, held_final_ignores_decl,
held_repair_never, held_alert_off. The running_watch_off and running_watch_repeats mutants now accept the `age`
keyword, so they die on their own tests instead of by crash.

## Rollback
Restore `autopilot.py.bak-3149-heldrepair-<ts>` and `test_autopilot.py.bak-3149-heldrepair-<ts>` in
`~/agora/ascension-autopilot` on GEX44. That directory is not a git repo. A `state.json` backup is taken with the
same timestamp. The new lane keys (`held_seen`, `held_align_told`, `held_final_for`) are ignored by the old code.

## Gate
Staging `/tmp/ap-r8-stage-3149`. The deployer (`deploy_on_green.sh`) deploys only on AUTOPILOT_GATE_PASS with
"MUTANTS SURVIVED: none", under cron.lock and autopilot.lock, and only if the live files still match
329a12ea / 3860d148 / 7e89fa2f.
