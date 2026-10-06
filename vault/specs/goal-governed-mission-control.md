---
covers: [goal-governed-mission-control, mission-control-tax, renewal-carries-route, unbounded-renewal, never-launched-renewal, goal-policy, mission-singleflight, mission-sleep-wake, mission-surface]
status: C1-C3 LIVE (924bdad6); C4 LIVE (f71fbdd1); C5 LIVE (063ff456; GEX44 4db97ab0); C6 LIVE with the commit that lands test_gsd_mission_surface
production: 2026-10-06T12:37:10Z laptop sweep halted m-8c64d4f52fc9 and logged "not renewed: never launched" (C3)
parent: vault/specs/mission-owner-hold.md; vault/specs/mission-envelope-and-compiled-wu.md; Owner ULTRA-PLAN approval "y" 2026-10-06
---

# Goal-governed mission control

## Why (measured 2026-10-06, read-only scan, estate of 121 records on laptop + GEX44)
The sweep is already zero-model (`plan_next` under the laptop task and the GEX44 agora/b001 timers). The
cost of mission control sits in four seams of `tools/gsd_mission.py`:

* **G2 renewal sheds the route.** `renew_mission` carries directives only. KME `m-1d0e4d0681ac` (no
  token_estimate) was budget-renewed at 2026-10-05T05:51Z as `m-98719dd9d1b1`; its worker `ec95adbc` ran 99
  calls / 27,715,869 processed in 27 min (transcript-measured) before parking on a question. The successor
  `m-e935055d072d` carries an Owner-approved bounded route (CLOSEOUT_PLAN_v3: 3.5M/5.5M/8M) only as prose in
  `note`; its renewal would have dropped it.
* **G3 a never-launched attempt renews.** product-surface `m-8c64d4f52fc9` sat PREPARED behind a cwd/work_dir
  divergence for 23 h (470 ledger rows, 0 launches) and is renewed at its budget like a mission that worked.
* **G1 a mission id is its own authority.** `create()` refuses only a live record with the same id: a fresh
  `arm` on a workstream whose attempt is under Owner hold (KSR recon-factory, InfinityOps odr-device-trust)
  starts a new attempt beside the hold.
* **G4 no exception surface.** `status` lists every record; panes and workers turn derivable state into
  Owner questions (this programme's own trigger: "Ask Owner: hold KME?", 36 calls / 6.37M to answer from records).

## Contract
### C1 Renewal carries the route (G2)
`renew_mission` carries the launch envelope: `token_estimate`, `token_trip_ratio`, `model`, `autocompact`,
`continue_max_tokens`, `wu_packet` (re-based to the successor's epoch 0), `mission_terms`, and the arm brief
`note` labelled as the predecessor's. It never carries `admission`: a renewed unit is re-admitted, because
the remaining budget is re-measured.

### C2 No unaffordable birth by renewal (G2)
A budget halt of a mission with NO `token_estimate` renews only an unbounded attempt. Mode
`CPP_MISSION_BOUNDED_RENEWAL`: `shadow` (default until the S6 shadow readout) records
`renewal_unbounded_shadow` and renews as before; `enforce` refuses with the reason. `off` disables both.

### C3 A never-launched attempt does not renew (G3)
A halt of a record whose epoch is 0 (no worker ever launched) is refused renewal: a precondition that held
every launch for a whole budget is not cured by a fresh budget. Always on; it can only refuse.

### C4 Goal policy and singleflight (G1) -- lands in S2
Goal key = workstream within the repo identity of `cwd` (git common dir). An Owner hold on any live attempt
of a Goal is a Goal hold: `create`/`arm` refuse a new attempt for that Goal while it stands; a second live
attempt of the same Goal is refused unless it names a distinct work unit. Supersession is explicit, with
the Owner's provenance recorded on the new attempt.

### C5 Sleep and wake (G3) -- lands in S4
Precondition failure and provider holds carry a typed wake predicate and write the ledger only on change.

Measured 2026-10-06 on the laptop ledger (15,955 rows, 2026-09-18..10-06): `quota_held` 3,011 of 3,029 rows
repeat the previous row of the same mission unchanged; `launch_held_cwd` and the `launch_held` transition
1,530 of 1,661 each. About 40% of the ledger restates a hold nothing changed, and every `launch_held` repeat
also rewrites the record and spends a `seq`.

- A hold is a `sleep` entry on the record: `{cause, wake, epoch, reason, since}` (`tools/mission_sleep.py`).
  `wake` is typed: `time` (`at`), `owner` (quarantine: an Owner release is the only waker), `env_ready`
  (preflight reasons), `cwd_aligned` (cwd, work_dir, status).
- Sites: quota and provider hold on relay/replace, the launch gate's lineage hold and preflight NOT_READY,
  and the cwd-alignment launch hold. Each writes its typed row and persists `sleep` through ONE `transition`
  only when the entry differs from the record's (`since` ignored). An unchanged pass writes nothing; the
  pass still holds (the sweep row says `held`, no launch).
- Any transition that does not set `sleep` drops it: after real movement the next hold is news again.
- Out of scope: `relay_held` (its gsd counter `n` is load-bearing for `GSD_HOLD_BLOCK_AFTER`) and the
  turn-end HOLD row; they keep writing per pass and are named debt.
- Readers: `gsd_epoch` `provider_holds` now counts hold episodes, not passes; `routing_metrics` still sees
  the first `quota_held` of each epoch.
- Acceptance 5: two identical held passes write one hold row and one record write; a changed reason or a new
  epoch writes again; a hold after a non-sleep transition writes again (control); the pass that writes
  nothing still launches nothing.

### C6 Surface (G4) -- lands in S5
`status --surface`: each non-terminal attempt classed HOT / WARM / COLD / TERMINAL with its wake predicate
and an Owner-only flag; KPIs (hot ratio, owner-only count, rejects by kind).

Pure and zero-model (`tools/mission_surface.py`), from the record, `plan_next` and the clock. `plan_next`
does not read `sleep`, so a sleeping attempt still plans relay/launch and supervise holds it: the sleep is
judged BEFORE the plan. Closed rules, first match wins:
1. TERMINAL -- state terminal.
2. COLD (owner_only) -- unreadable record; `owner_hold`; `sleep.wake.kind == owner` (quarantine);
   plan `surface_blocked` (a human is asked). Nothing in the machine moves it.
3. WARM -- asleep on a machine waker (`time` with `at` in the future or unknown, `env_ready`,
   `cwd_aligned`); `gsd_hold`; `capsule_hold`; plan `await` or `surface_unknown`. It wakes by itself or
   is waiting for an answer already asked.
4. HOT -- everything else: a `time` wake already due, a live owner at work, or a pass that will act
   (launch / relay / replace / adopt / unblock / halt).
KPIs over non-terminal attempts: `hot_ratio` = HOT / non-terminal (None when there are none: absent is not
zero), `owner_only` count, `holds_by_cause` = count of `sleep.cause`. `status` without `--surface` keeps
its exact output.
Acceptance 6: one fixture per rule, the sleeping-relay case classed WARM not HOT (control: the same record
without `sleep` is HOT), a due `time` wake HOT, and `hot_ratio` None on an empty estate.

## Acceptance (each gate driven red by a mutation drill on a copy, never on the live file)
1. A renewal keeps token_estimate, wu_packet, note; never admission (control: fields present on the halted rec).
2. Unbounded budget renewal: shadow renews and ledgers; enforce refuses; bounded control renews in both.
3. Epoch-0 halt refuses renewal; epoch-1 control renews.
4. Held Goal + fresh arm on the same workstream refused; other workstream allowed; released Goal allowed.

## Rollback
Each contract lands in its own commit. C2: `CPP_MISSION_BOUNDED_RENEWAL=off`. Revert the commit otherwise;
records written under it stay readable by the old code (all fields optional).
