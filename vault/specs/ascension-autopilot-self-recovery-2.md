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
