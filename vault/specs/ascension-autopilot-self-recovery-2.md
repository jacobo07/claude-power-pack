---
covers: [ascension-autopilot, self-recovery, watchdog, disk-floor, owner-alerts, sha-hold, held-replan, planner-template]
tier: T2
owner_go: "go ahead, hazlas todas" (laptop pane 5f1414ed, 2026-11-25)
---
# Ascension autopilot: self-recovery, round 2

Round 1 (same day, deployed 20:30Z) re-plans a lane when a refused cost top-up leaves it RUNNING-idle, and recovers
a lane whose tick died after the judgment was taken. This round covers the other ways lanes stopped on 2026-11-25.

## Measured causes (GEX44, 2026-11-25)
- KSR 00:50Z, MKW 06:00Z: parked with "checkpoint hold names no evidence or residual path". The holds did name
  something: a product commit sha (`5cb05abd` in t1-campaign, `289143e1` in mkw-decomp). Each commit adds exactly the
  checkpoint file (`checkpoint_s329k.md`, `checkpoint_s338m.md`). Four minutes later `gsd_mission` auto-pivoted and
  cleared the hold, so the mission went on while its lane stayed PARKED and unwatched:
  - KSR went BLOCKED on an Owner decision and HALTED on age 16 h later;
  - MKW has been "launch held: cwd diverged" for 15 h.
  Every mission notice went to `incident_notify_failed`, because GEX44 has no channel (no Telegram, toast is Windows-only).
- FIFATC 11:58Z, MKWLIB 01:53Z: ENOSPC crashes. The disk was 100% full from about 06:16Z (the leaking TENNIS
  exemplar, fixed in c011b2fc). MKW's S338M checkpoint is itself an INSTRUMENT_FAIL "disk 4G<10G".
- `/tmp/ap-dry-*`: 12,382 dirs (~250 MB) since 11-11. test_autopilot's dry-tick check calls main(dry-tick) once per
  run_all, which is about 167 times per gate run, and never removes the scratch dir.
- Policy refusals since 11-19: 52 on plan 1 and 20 on plan 2, with 0 parks. Re-planning already absorbs them, so this
  round only saves tokens there: most are S26C conditions missing from the profile line, then forbidden-act wording.

## Changes (autopilot.py, test_autopilot.py, planner_prompt.md on GEX44; one laptop script + task)
1. **Commit-sha holds.** `checkpoint_from_sha`: an evidence/residual sha that is a product commit after the generation
   base resolves to the checkpoint*/residual*.md that commit adds. The commit need not be reachable from HEAD: a
   worktree branch is fine, because discover_checkpoint fast-forwards. The branch fallback uses the product HEAD when
   the mission head is a control-repo commit (as terminal_checkpoint already does).
   A hold that still names nothing waits `NOPATH_WAIT_S` (30 min), since gsd_mission may pivot or name it, then parks.
2. **Launch held too long.** A RUNNING mission whose launch has been held for at least `HELD_REPLAN_S` (2 h) is
   re-planned from the kept judgment through `breaker_replan(cause="held")`. It shares the BREAKER_REPLAN_MAX streak.
   With no kept judgment it parks visibly.
   Fix to round 1: a breaker re-plan that drew a policy refusal resumes from its kept plan at the next tick, instead
   of returning on breaker_replan_for forever.
3. **Idle watchdog.** Each tick fingerprints a RUNNING/WAITING lane: lane status, gen, judged_for, pending gen,
   mission state, updated_at, hold set_at and cost tokens. An unchanged fingerprint for `WATCHDOG_S` (3 h) gives one
   WATCHDOG notice per fingerprint, plus a ledger row. It never parks: waits (day cap, weekly guard) are legitimate
   and still get reported.
4. **Disk floor and own tmp sweep.** Every tick, real ticks only, removes `/tmp/ap-(dry|test)-*` dirs older than
   24 h that the autopilot user owns, at most 2000 per tick. Below `AP_DISK_FLOOR_GB` (20 G free), no lane is ticked:
   nothing is judged, planned or armed, the state is kept, and one notice goes out per episode. The test now removes
   its dry scratch and its tmp dir.
5. **Owner alerts.** Each tick writes `alerts.json`: parked/stopped lanes with their last queue line and whether
   their mission is still live, idle watchdog hits, and the disk floor. Laptop task `PP-Ascension-Alerts`
   (`~/.claude/scripts/ascension_alerts_notify.py`, every 15 min) emails the Owner on new alert keys, plus a reminder
   at most every 24 h while any stay open, and also when alerts.json is older than 30 min (autopilot not ticking).
   The Gmail token stays on the laptop.
6. **Planner template.** planner_prompt.md carries a fill-in line for a new-profile phase, which the gate proves
   passes policy_check, plus the forbidden-wording rule.

## Not granted
No budget, research-cap or weekly-guard change. No certifier or policy change. No deletion outside the two own tmp
prefixes. Lanes parked on an honest stall (JUDGMENT_NOT_EXECUTABLE plus no new lever) stay parked.

## Acceptance
`AP_PP=... python3 test_autopilot.py` prints AUTOPILOT_GATE_PASS with every new V-AP-* gate, and each new mutant is
killed by an assertion. Deploy runs under cron.lock with `.bak-5f14-sr2-*` backups. The first live tick writes
alerts.json. The laptop task's first run sends one email.

## Rollback
Copy the `.bak-5f14-sr2-*` files back (autopilot.py, test_autopilot.py, planner_prompt.md, state.json), then run
`Unregister-ScheduledTask PP-Ascension-Alerts`. Kill switches: `AP_DISK_FLOOR_GB=0` disables the floor.

## Round 3: Owner answers (Owner 2026-11-26 "autorizo y deberia tener la capacidad", KSR cohort-exclusion clause)
Cause: KSR's mission asked an Owner decision (DECISION_REQUEST), blocked, and died on age 16 h later. The only way in
was a hand-run `gsd_mission.py decide`, which a terminal mission refuses. Nothing showed the question to the Owner.
- `autopilot.py answer <LANE> <text | ->` appends one line to `answers.jsonl` (no lock needed). Laptop:
  `ascension_alerts_notify.py answer <LANE> "<ruling>"` does the same over ssh, with the text on stdin.
- Each tick takes new complete lines (`answers_seen` offset): the ruling is kept on the lane (newest 5), and a
  PARKED/STOPPED lane goes WAITING with its judgment cleared. The Owner answering is the only thing that unparks it.
- `planner_prompt()` appends "OWNER RULINGS (binding)" for the lane. `deliver_rulings` sends each ruling once to the
  lane's live mission as gsd_mission decision `AP-<id>`. It skips terminal missions and stops after 3 refusals per
  mission, with one notice.
- alerts.json has a `question` entry for a mission whose DECISION_REQUEST no ruling has answered since it was asked,
  with the answer command. The email lists that command.
- Not granted: the autopilot never answers a question itself. Truth-contract, held-out, capital and scope rulings stay
  the Owner's.
- Gate: 425/425 and 190/190 mutants killed. 8 new mutants: answer_ignored/retaken/keeps_park,
  ruling_not_in_prompt/redelivered/delivered_dry, question_alert_off/never_quiet.
- Deployed 2026-11-26T09:30:32Z (backups `*.bak-5f14-sr3-20261126T093032Z`).
- First use: KSR ruling 087b57b8. Tick 09:35Z: unparked and S329K judged. 09:37Z: S374K armed as m-7b0319e33ed3,
  with Phase 1 citing the ruling. 09:40Z: the decision was delivered to the mission.

## Round 4: stranded generation work (Owner 2026-11-26 "go ahead y subele la autonomia")
Cause: a generation's worker did its work in the PREVIOUS generation's worktree, and the product kept only its
scaffold.
- FIFATC S364C, in worktree-s359c: phases 1-3, held-out 55/60 SUPPORTED, provisional checkpoint. `gsd_mission`
  measured the product, saw "3.9M processed since the work tree last changed", cut it on cost and settled it HALTED.
  The lane parked.
- MKW S369M, in worktree-s362m: its relaunch was held "cwd diverged", and the round-2 held re-plans re-created the
  divergence.

What `reconcile_stranded` merges, and when:
- It acts only on commits whose subject starts with the lane's current generation, on a worktree branch the product
  lacks, in a worktree that is not the generation's own.
- It merges them `--no-ff` into the product only when all of these hold: the product side since the merge base is
  scaffold alone (`.planning/` plus the packet dir), the two sides share no path, and no uncommitted product change
  touches the merged paths. The worktree is then fast-forwarded to the merge.
- Anything else is a `skip:` notice, and nothing moves.
- It runs from tick_lane, before lane_tick, when the mission is terminal or held on cwd alignment. CLI:
  `autopilot.py reconcile <LANE> [--apply]`.

Round 4b: a merge home sets `held_grace_until = now + HELD_REPLAN_S`. Reason: MKW was re-planned at 12:15Z, one tick
after its merge, from the old kept judgment, so S382M was armed instead of S369M being relaunched.

Gate: 433/433, 197/197 mutants killed. Deployed 12:14:28Z (backups `*.bak-5f14-sr4-*`), then 4b at 12:30:00Z
(`*.bak-5f14-sr4b-*`).

Live, 12:14Z:
- MKW: merged as edfc5588 (41 paths).
- FIFATC: merged as d8dbbd8 (76 paths). S364C was then judged; its checkpoint is not final, so it is continued once,
  and S383C was armed as m-afb62e6a2d35.

Not granted, unchanged: no budget, cap, certifier or policy change, no history rewrite, and Owner questions stay the
Owner's.
