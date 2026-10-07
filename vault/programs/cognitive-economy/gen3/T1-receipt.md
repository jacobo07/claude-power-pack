# cep-gen3 T1 receipt -- mandatory envelope at launch

Branch `ce/gen3-t1-envelope` (worktree C:\Users\User\Apps\pp-gen3-t1), code commit 44cbe15d. NOT merged or pushed:
the shared checkout rejects edits from a background job, so the work landed on this branch; merge is the Owner's call.

## Change (tools/gsd_mission.py)
- `envelope_missing(rec)`: no token_estimate AND no wu_packet AND no waiver. `CPP_MISSION_ENVELOPE_REQUIRED` =
  shadow (default, ledgers `would_refuse_no_envelope`, launches) | enforce (refuses before the claim, ledgers
  `launch_refused_no_envelope`) | off. Waiver: `envelope --waiver-reason "<text>"` (blank refused).
- Uncurable refusal (unadmitted packet, or missing envelope under enforce) parks a PREPARED mission BLOCKED once
  (`launch_parked`, field `launch_hold`); `plan_next` returns none for it; supervise un-parks it (`launch_unparked`)
  when cured. Never touches a mission with an owner or an Owner hold.

## Tests (exit codes)
- test_gsd_mission_envelope_required.py (new): ENVREQ_PASS 15/15, exit 0 -- refuse pole, admit poles (estimate,
  packet, waiver), shadow pole, off, parked-once, not-retried, un-parked-when-cured, CLI.
- test_gsd_mission*.py: mission 225/225, admission, cwd_align 16/16, envelope 39/39, freshness 18/18, goal_control
  27/27, owner_hold 12/12, protocol 11/11, quota_relogin 7/7, sleep 6/6, surface 6/6: all exit 0.
- legacy_characterization: 23/32 before, 32/32 after `--amend` of 8 scenarios (+1 shadow row each, recorded in
  golden meta.amendments).
- capsule_v2: 71/72, exit 1 -- the SAME single failure (V-MV2-HALT-NONE-FIRST-WORKER) on the unchanged main
  checkout; pre-existing, not caused by T1, not fixed here.

## Evidence
- Real refused launch row: mission m-gen3t1-probe (never launched, closed HALTED), ledger event
  `launch_refused_no_envelope` at 2026-10-07T11:05:04Z, epoch stayed 0.
- Real ledger before T1: `launch_refused_admission` 351 rows (one per pass); `would_refuse_no_envelope` 0.
- CPP_MISSION_BOUNDED_RENEWAL shadow rows (`renewal_unbounded_shadow`): 2 of 100 renewals, on m-42c68efbb4b4
  (RUNNING) and m-b65977d380b3 (BLOCKED), both Owner-undecided and untouchable. NOT flipped to enforce: two rows
  on two protected missions is not a base rate, and flipping changes their next renewal. Re-evaluate after ~1 week.
- T3 armed: m-595b674b8e41 (supersedes m-a128e03c7419), estimate 12.5M, sonnet, autocompact 250k, packet T3.md,
  route-T3.json -> admission verdict ADMISSIBLE (recorded). Not launched here (--no-launch); supervisor starts it.

## Spend / bugs
- Spend: not measured (no transcript query run). Roughly 35 tool calls, within the 3M cap by construction.
- Gap: CPP_MISSION_ENVELOPE_REQUIRED default stays shadow; enforce flip needs the Owner after shadow rows accrue.
- EnterWorktree failed ("could not read the repository git config"); used `git worktree add` instead.
