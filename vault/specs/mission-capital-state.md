---
covers: [mission-capital-state, mission-topup-policy-epoch]
tier: T2
status: approved by Owner 2026-11-23 ("APRUEBO CAPITAL"); W0 committed 8c452fac; W1 committed on gsd/mission-capital; W2+ pending
date: 2026-11-23
plan: vault/plans/mission-capital-continuity-20261123.md
extends: vault/specs/mission-auto-topup.md
---

# Mission capital state: one economic state, not several labels

## Canonical model (plan §3, target)
- `capital_state(rec, pol, spent, forecast)` -> HEALTHY | PRESSURE | RENEW_ELIGIBLE | EXHAUSTED_OWNER |
  WAITING_PROVIDER | TERMINAL | UNKNOWN. A pure function in `tools/mission_topup.py`; `judge()` consumes only it.
- Every label maps into it: the authority-trip hold, BLOCKED + blocker CAPITAL_EXHAUSTED, HALTED by the dead-worker
  guard, and a stale cost hold whose authority was raised later (headroom exists).
- Envelope = Owner ceiling + step (+ emergency reserve). Grants are counted per policy epoch; the cap is the CEILING.
  Spent comes from `mission_spend` (monotonic).
- All three budget dimensions (authority tokens, max_hours, max_cycles) are checked together before a release/grant.
- Progress = mission-keyed ledger receipts + commit delta over every lineage root (binding generations, worker and
  subagent worktrees), excluding unrelated branches and `.planning/`-only commits.
- Exactly-once: a grant is keyed (mission, policy_epoch, n), written before its effect, completed by resume.
- Authority is a portable HMAC-signed `authority_receipt` (mission_id, goal_sha, ceiling, step, source), verified by
  the consuming host instead of a host-local transcript lookup.
- Provider quota (account_governor) is WAITING_PROVIDER: grants nothing, wakes on the reset time.

## Hypotheses and live evidence (2026-11-22/23, GEX44 ledger)
| H | finding | evidence |
|---|---|---|
| H1 | one economic state, several labels; judge sees only the authority trip | m-76e04d86896d BLOCKED/CAPITAL_EXHAUSTED 00:37Z, no owner_hold; stall 8h13m until a hand raise 08:50Z |
| H2 | progress read from one checkout | bound root p4-handoff-note: 1 `.planning` commit since 08:50Z; mission branch: 14 commits / 3 code paths; agent worktrees 4-16 commits each |
| H3 | authority is host-local | laptop approval unverifiable on GEX44; raises 175M->215M written with owner_turn=null |
| H4 | renewal is reactive | forecast saw 3.06M headroom 6 min before BLOCK (00:31Z), nothing acted |
| H5 | polling first | the 5-min sweep is the only caller of `mission_topup.sweep` |
| H6 | policy-epoch bug | 09:40:40Z "top-ups exhausted (1/1)" at 214.06M/215M with ceiling 255M: the old grant (70M->85M) counted against the re-set policy; 1h06m of the 2h29m stall |
| H7 | silent boundary | GEX44 notify = "no channel configured" (00:37Z, again on the W0 refusal) |
| H8 | budget dimensions not checked together | m-396659f48a16 released on authority+hours, HALTED on cycles 9/9 at 12:09Z (runtime renewed it 12:14Z: a precheck gap, not a stall cause) |

Also measured: W0 live sweep refused on the account governor (weekly 86.1% >= 85%), the first live
WAITING_PROVIDER sample; unstuck under Owner override 12:09Z (grant n=2, 215M->255M, TOPUP2, worker acked).

## W0 fix (code, `tools/mission_topup.py`)
- `budget()` on an existing policy opens a new epoch: current `grants` are appended to `prior_grants`, `grants=[]`,
  `policy_epoch += 1` (missing = 0). New policies start at epoch 0 with empty `prior_grants`.
- `judge()` counts only the current epoch. With a ceiling, it refuses only when authority >= ceiling; without one,
  `max_topups` is honoured as before.
- Grant `n = len(prior_grants) + len(grants) + 1` (and the grant records its `epoch`), so `TOPUP<n>` decision ids
  never repeat across epochs (a reused id is a replay no-op that never wakes the worker).
- Resume (a grant already written for this hold) is unchanged. Pre-W0 policy files load and behave as before.
- Gates (`tools/test_mission_topup.py`): V-TOPUP-EPOCH-BUDGET, -EPOCH-CONTROL-PRE-W0 (the verbatim pre-W0 judge
  refuses the live shape "exhausted (1/1)"), -EPOCH-CEILING-BOUND, -EPOCH-GRANT (n=2, TOPUP2, 255M),
  -EPOCH-CEILING-REACHED, V-TOPUP-OLD-SCHEMA-EXHAUSTED/-GRANT/-REBUDGET.
- Behaviour change to note: a policy WITH a ceiling no longer refuses on the grant count before the ceiling.

## Kill switches
- `CPP_MISSION_AUTO_TOPUP=off` (existing: sweep does nothing)
- `CPP_CAPITAL_STATE=off` (W1: judge reverts to `is_authority_trip`)
- `CPP_TOPUP_PREDICTIVE=off` (W3), `CPP_TOPUP_EVENT=off` (W3), `CPP_AUTHORITY_RECEIPT=off` (W4)
- Rollback: one commit per W; GEX44 deploys by CAS with `*.bak-mcc-<W>-<ts>` backups under cron.lock.

## W1 (code, `tools/mission_topup.py`, `tools/gsd_mission.py`)
- `capital_state(rec, pol, spent, now)` -> {state, label, why, dims}; states HEALTHY | PRESSURE | RENEW_ELIGIBLE |
  RESUME_ONLY | EXHAUSTED_OWNER | TERMINAL | UNKNOWN (WAITING_PROVIDER is W5). dims: authority, spent, closeout
  reserve, headroom = authority - reserve - spent, min_lease (as `_dead_worker_authority_guard`), hours deadline
  (created_at + waited_s + 3600*max_hours), cycles used/max (`iterations`/`max_cycles`), occurrence key.
- Labels: `authority_hold` (owner_hold kind cost, reason "cost breaker (mission authority)", guard park included);
  `blocked_capital` (H1: state BLOCKED, no hold, `rec.blocker.class == CAPITAL_EXHAUSTED` -- the record field
  `block_mission` writes, never ledger text). HALTED (guard) -> TERMINAL.
- Order: terminal; hours deadline passed -> EXHAUSTED_OWNER "hours exhausted" (notice names `--extend-hours`);
  spent None -> UNKNOWN (never grants, never zero); headroom > min lease -> RESUME_ONLY (H4 stale hold); ceiling /
  top-ups -> EXHAUSTED_OWNER; else RENEW_ELIGIBLE. Cycles exhausted is recorded only (the runtime renews it).
- `judge()` consumes it: grant | resume (grant already written for this key) | release (RESUME_ONLY: release + a
  `RESUME<k>` decision, no grant, no capital; entry written to `pol.resumes` before the effect) | refuse | none.
- Occurrence key: a hold's `set_at`; a BLOCKED park's `blocker.at` (block_mission stamps the transition time), else
  the deterministic `blocked-e<epoch>` (one block lives in one epoch; a relaunch bumps it). `_complete` already
  skips the release when there is no hold and still delivers `TOPUP<n>`.
- Half-applied grant on re-budget: VOIDED, not completed -- `grant.voided` + ledger `authority_topup_voided` before
  the new epoch opens. The Owner's re-budget is the newer authority statement; completing would apply and wake under
  a raise `set_authority` overwrites in the same call.
- `adopt_defaults` also adopts a BLOCKED/CAPITAL_EXHAUSTED mission (both labels).
- Dup-arm guard: `arm()` refuses when a non-terminal, unheld record has the same resolved cwd or git common dir,
  unless `--parallel-unit`; when both name a workstream the goal guard owns the case. Message names the mission id.
- Gates: `tools/test_mission_topup.py` 53/53 (37 W0 + V-CAP-BLOCKED-RENEWS(+CONTROL, +FAILS-AT-8c452fac),
  -BLOCKED-EXACTLY-ONCE, -STALE-HOLD-RESUME(+CONTROL), -HOURS-EXHAUSTED(+CONTROL), -CYCLES-NOT-REFUSED,
  -UNKNOWN-SPENT(+CONTROL), -TERMINAL(+CONTROL), -KILL-SWITCH (25 shapes equal to the 8c452fac judge loaded from git),
  -REBUDGET-HALF-GRANT(+CONTROL)); spend injected hermetically (SPEND dict, like GOV).
  `tools/test_mission_dup_arm.py` 7/7 (V-DUPARM-REFUSE, -REFUSE-WORKTREE, -REFUSE-FAILS-AT-8c452fac,
  -PARALLEL-UNIT-ALLOWS, -HELD-ALLOWS, -TERMINAL-ALLOWS, -KILL-SWITCH).
- Kill switches added: `CPP_CAPITAL_STATE=off` (judge = 8c452fac verbatim), `CPP_MISSION_DUP_ARM_GUARD=off`.
- Not yet: other `gsd_mission` arm suites not re-run (RAM); no live GEX44 replay; W0 notify channel (H7) still open.

### W1 review correction (parent, 2026-11-23)
The duplicate-arm guard ships in SHADOW by default: a duplicate is recorded as a `duplicate_arm_shadow` ledger row,
not refused. Enforced, it broke arm flows that other suites drive on one repo (test_arm_worker_guard 2/6,
test_mission_pivot, test_programme_spend and test_gsd_mission_capsule_v2 crashed; all green with the guard off). Switch:
`CPP_MISSION_DUP_ARM_GUARD=on` enforces, `=off` skips. Promote to enforce only after the pivot / programme / capsule
arm flows are classified and the shadow rows show no legitimate duplicates.
The test_gsd_mission V-MC-CLI-PERMISSION fixture now arms in its own directory per iteration (248/248).
Pre-existing, not W1: test_gsd_mission_capsule_v2 V-MV2-L1-WITHIN-BACKOFF-HELD-SILENT (78/79 with the guard off too:
it reads live background-task state), test_two_pane_exactness harness (no drill data).

## W2 progress receipts (code, `tools/mission_topup.py`, 2026-11-24)
Replaces the provisional any-branch reading (8c059095 `branch_tips`, live on GEX44 as 90c6f26f), in which a NEW
unrelated branch anywhere in the clone bought a grant.
- `progress_receipts(rec, pol)` = union since the last grant (`pol.last_at`, else `set_at`):
  - (a) `ledger_receipts`: this mission's `breaker_receipt` rows with classification `GOOD_PROGRESS` (mark or lease).
    That receipt is a MEASUREMENT: the breaker's allow-listed content fingerprint of the bound tree moved, and
    bookkeeping (STATE.md, RESUMPTION.md) never moves it. `cost_mark` always follows one, so it adds nothing.
  - (b) the non-bookkeeping commit delta over the HEADs of the LINEAGE roots, excluding `last_head` and the
    `last_tips` recorded at the last grant. Lineage roots = the execution root, the binding's `previous`, every root
    a `workspace_rebound` row or rebind receipt of this mission names, plus each worktree of the repository where one
    of the mission's own sessions (every `worker_acked` worker + the owner) wrote a file or ran a subagent after the
    last grant. Ids only, never a branch name or the cwd.
  - (c) excluded: branches outside the lineage, commits touching only `.planning/`.
- Departures from plan §3, decided here: a checkpoint and an obligation closed by hand (`obligation_set`) are the
  worker's own statements, not measurements, so they never buy capital. A settled obligation (artifact found) rides
  on a `cost_mark`, which a GOOD receipt already counts. The arm checkout (`cwd`) is a root only while it is the
  execution root or a session wrote there: a background worker's main-thread cwd is that checkout, which other panes
  share. Remaining risk: another pane committing on the SAME branch in a lineage root still counts (no per-commit
  attribution), as it did before W2.
- Measured = either source answered. Neither = unmeasured (refuse "progress unmeasured"), never "no progress".
  A grant bought by receipts on an unreadable root keeps the previous `last_head`.
- Cost: read only at a capital boundary (the sweep visits ~69 policies); the ledger is parsed once per ledger
  version and grouped by mission; at most 64 transcripts per judgement, skipped when untouched since the last grant.
- Kill switch `CPP_PROGRESS_RECEIPTS=off` -> `progress_since` (any-branch, 8c059095).
- Gates (`tools/test_mission_topup.py` 75/75): V-W2-UNRELATED-BRANCH-NOT-PROGRESS (was V-TOPUP-WORKTREE-PROGRESS,
  whose fixture is a plain branch no session named), -KILL-SWITCH-ANY-BRANCH, -REVERT-CONTROL (the 2483d9e6 module
  grants on the same fixture), -CHILD-WORKTREE(-UNNAMED pole, -NO-RECOUNT), -FOREIGN-WORKTREE-NOT-PROGRESS
  (pole -OWN-WRITE-WORKTREE), -RECEIPT (poles -STALE-OR-SELF-REPORT, -NO-RECOUNT), -PLANNING-ONLY-NOT-PROGRESS
  (pole -PLANNING-CONTROL), -NOT-READ-OFF-BOUNDARY. Neighbours: s6_blockers 72/72, gsd_sweep_pass_py 18/18,
  gsd_sweep_pass 11/11, mission_dup_arm 8/8.
- Deployed to GEX44 2026-11-24 (port 7724e2c1, live md5 889659a4), after the stage suite (75/75) and a read-only
  replay over all 69 live policy records (0 errors; 1 intended DIFF: a .planning-only lineage, m-c63c3d9338f7).
  Rollback `~/rollback-mcc-w2-20261124T110333Z.sh`. The W1 dup-arm guard (shadow) shipped in the same
  window by anchor port (gsd_mission 0f011e30 -> 2387bc7c).

## W3 predictive renewal, in-process events, exactly-once (code, 2026-11-24)
- **One lock per mission.** `sweep_one` runs under `mission-topup-<mid>.lock` (gsd_mission `_Lock`: a kernel
  byte-range lock the OS drops when the holder dies, never reclaimed by age), reached through one seam
  `_topup_lock`. The poller, an event, a manual CLI pass and recovery all pass through it. A pass that cannot take
  it acts on nothing: the poller waits up to 30 s, an event 15 s, then the event is ledgered `capital_event_deferred`
  and the holder (or the next poll) judges. `budget()` holds it too, so no pass judges a half-written re-budget.
- **Seq CAS.** A NEW grant or resume entry is written only if the record's `seq` still equals the one judged
  (progress reading takes seconds). Moved -> `authority_topup_cas_moved`, action none, the next pass re-judges.
  Completing an entry already written (resume) needs no CAS: `_complete` is idempotent.
- **Predictive renewal (H4).** At no boundary, `capital_state` is PRESSURE when headroom < max(min lease, next
  lease). Next lease = `work_class_profile.lease_forecast(work class)` (p80, else the largest settled sample), else
  the policy step, named in `lease_basis`. Under PRESSURE, `judge(predictive=True)` grants on the same envelope and
  progress gates as a boundary grant, keyed `pressure:e<epoch>:a<authority>` (a completed raise moves the key, so the
  next one needs new progress). Short of a grant it answers `none`, never a refusal: a running mission is not
  parked and nobody is told it is. The governor's refusal is `none` too. A predictive grant only raises authority:
  no hold to release, no decision, no wake. The poller judges PRESSURE as well (reconciler).
- **Event path (H5).** `gsd_mission._capital_event` -> `mission_topup.on_capital_event(mid, cause)` after the write
  commits, at: `set_owner_hold(kind=cost)` (`cost_hold`), `block_mission` (`blocked`), `set_authority`
  (`authority_set`), both `cost_mark` writes, `_recompile_forecast` (`forecast_invalidated`), and `launch_worker`
  before a relaunch's claim (`pre_launch`); `budget()` dispatches `budget` once its policy is whole. Predictive only
  for cost_mark / forecast_invalidated / pre_launch. No policy = one stat. An event never fails the write it follows
  (`capital_event_error`), and returns the fresh record only when the top-up acted.
- **No host call in-process.** The event's decide records the decision (`wake=False`) and stamps the existing
  `pending_wake`, which `retry_pending_wake` delivers to an idle owner next pass or clears for a dead one (the card
  carries it). An event fires inside the supervisor's breaker thread, where `claude stop` + continue measured > 60 s.
- **Reentrancy.** A thread-local depth (`_Quiet`) marks a top-up pass and `budget()`; their own set_authority /
  release / decide are not re-dispatched.
- Kill switches: `CPP_TOPUP_EVENT=off` (no dispatch, the poller alone), `CPP_TOPUP_PREDICTIVE=off` (boundary
  grants only). `tools/test_mission_topup.py` pins the poller and runs with both off.
- Gates `tools/test_mission_topup_w3.py` 29/29 (3 consecutive runs): PREDICTIVE-GRANT, -EXACTLY-ONCE, -HEALTHY-NONE,
  -NO-PROGRESS-NONE, -KILL-SWITCH, -CEILING-NONE, -LEASE-FORECAST (+ -LEASE-STEP-CONTROL), FORECAST-EVENT
  (+ -KILL-SWITCH), PRE-LAUNCH-EVENT, EVENT-COST-HOLD, -NO-REENTRY, -KILL-SWITCH, -NO-POLICY-NOOP, -FAULT-ISOLATED,
  -BLOCKED (+ -CONTROL), -AUTHORITY-SET, BUDGET-EVENT; races: CONCURRENT-EXACTLY-ONCE (4 threads),
  REVERT-CONTROL-2455e994 (pre-W3 on the same race: two grant rows, or a pass crashing on the policy file,
  `WinError 32`; both measured), LOCK-MUTANT-SEQ-HOLDS (lock removed: the CAS alone refuses the stale pass),
  CAS-MOVED (+ -CONTROL), EVENT-BUSY, WORKER-BLOCK-VS-POLLER, MANUAL-VS-AUTO (half-written grant + an Owner raise
  above it: the Owner's figure stands, TOPUP1 once), CRASH-KILLED-MID-GRANT (a real process `os._exit` after the
  grant write: lock free, poller resumes once).
- Residual risks: `adopt_defaults` still writes a new policy unlocked (a policy only appears there, and an event
  needs one to exist). A crash between the deferred decision and its `pending_wake` stamp leaves the decision on the
  card with no in-place wake (the next launch carries it). Not deployed.

### W3 review (vault/audits/mission-capital-W3-review.md: APPROVE, 2 MEDIUM + 3 LOW, all acted on)
- **Run as a script.** `mission_topup.py` registers itself as `mission_topup` when it runs as `__main__`. Without
  this, the poller's own grant re-entered through a second module copy. Measured before the fix: 21.4 s and a false
  `capital_event_deferred` row; after: 2.4 s, no row. Gate V-W3-MAIN-NO-SELF-DEFER runs the file in a child
  process via runpy.
- **One unspent predictive step.** A further predictive grant waits until the last predictive grant's step has
  been spent. Without this, a next lease larger than headroom + step let every commit buy another step and drain
  the top-ups early. This was a judgement call; the Owner may loosen it. Gates V-W3-PREDICTIVE-ONE-AHEAD and
  -SPENT-CONTROL.
- **Unapplied predictive grant.** An unapplied predictive grant (authority still equal to its `from`) is completed
  first, by the boundary or the predictive judge, so a crash followed by a park spends no extra slot. Gate
  V-W3-PREDICTIVE-CRASH-THEN-PARK.
- **Owner raise mid-grant.** `_complete` raises with `expected_seq`. If the authority is neither the grant's `from`
  nor >= its `to`, someone set it after the grant was written: the grant is VOIDED
  (`authority_topup_voided`, the W1 re-budget rule) and the next pass judges at that figure. Voided grants are
  never resumed. Gate V-W3-OWNER-RAISE-MID-GRANT: an Owner raise to 150M lands mid-grant; 150M stands, no TOPUP is
  sent, and the stale park is released by RESUME1.
- **pre_launch is predictive-only.** It never acts at a boundary on the record being launched. Gate
  V-W3-PRE-LAUNCH-PREDICTIVE-ONLY.
- **Kill switches (LOW-1).** With both switches off, behaviour is the poller's, except that the lock and the seq
  CAS still apply. A pass can be deferred one poll by a moved record, or report busy against a concurrent
  `budget()`. Kept on purpose: these are safety properties, not features of the event path.
- Gates: test_mission_topup_w3 35/35.
- **Ask after a predictive grant.** Found by the GEX44 stage smoke, fix e75d64ca. A worker's BLOCKED ask is
  RESUME_ONLY when an unvoided predictive grant was made in the record's current epoch: a predictive raise tells the
  worker nothing, so its ask is stale. With no such raise, an ask with room left stays the Owner's (W1).
  Gate V-W3-PREDICTIVE-THEN-ASK (+CONTROL); W3 37/37.
- Deployed to GEX44 2026-11-24 17:57:53Z: mission_topup 8130b8c3, gsd_mission 8a39b79f (anchor port of 7 hunks,
  foreign hunks byte-identical), GEX44 port commit 2cd830a5. Rollback `~/rollback-mcc-w3-20261124T175753Z.sh`.
## W4: portable authority receipt (H3)

The issuing host verifies the Owner turn in its own transcript (verify_owner_turn, unchanged). It then signs one act
for one mission with HMAC-SHA256 under an estate key. The consuming host checks the signature, the key id, the
mission id, the goal fingerprint and the expiry. It never reads a transcript. Module `tools/authority_receipt.py`.

- **Key.** `~/.claude/secrets/estate-authority.key` (or `CPP_ESTATE_KEY_FILE`): 32 random bytes as hex, created with
  mode 600 and never overwritten. On POSIX a key readable by group or other is refused. Receipts name the key only by
  `key_id` (a hash). Gate V-W4-NO-KEY-LEAK scans every state file, the token and the CLI output for the key.
- **Receipt.** `{v, kind, act (authority|close), mission_id, goal_sha, terms{tokens, extend_hours, ceiling, step,
  stage}, close{outcome, reason}, source{host, session, timestamp, uuid, text_sha256, text_head}, issued_at,
  expires_at (default 72h), nonce, key_id, sig}`. It travels as `ar1.<base64url>`.
- **goal_sha** = sha256 of [mission_id, created_at, workstream, mission_terms]. The resume command is left out
  because a pivot can rewrite it.
- **Consume.**
  - `set_authority(receipt=)` / `gsd_mission.py authority --receipt`: a figure the caller gives must equal the
    signed one, and a figure the receipt does not sign cannot be added.
  - `mission_topup.budget(receipt=)` / `budget --receipt`: the receipt must sign tokens, ceiling and step. A
    receipt (or a local owner turn) applied again is a no-op, because a replay would open a new policy epoch and
    restore top-ups already granted.
  - `close_mission(receipt=)` / `close --receipt`: the signed outcome and reason are the close's own.
- **Provenance.**
  - Every authority receipt entry carries `provenance`: owner_turn, portable_receipt, topup_policy or none.
  - Without one, the raise is still applied, a `authority_receipt_missing` ledger row is written, and
    `authority_lineage().receipt_less_raises` counts it.
  - Rows from before W4 carry no provenance and are not counted: their provenance is unknown, which is not the
    same as none.
- **Kill switch** `CPP_AUTHORITY_RECEIPT=off`: every receipt is refused and receipt-less raises are no longer
  flagged. The local `--owner-turn` path does not depend on the switch.
- **Gates:**
  - test_authority_receipt 26/26: tamper, wrong key, wrong mission, goal mismatch, expiry, no key, both sources,
    bounded figures, replay, kill switch, budget, close and CLI round trip. Each has its control, and the
    no-transcript control is the H3 shape.
  - V-W4-KEY-PERMS runs on POSIX only.
## W5: WAITING_PROVIDER, deterministic wake, metrics, census

- **WAITING_PROVIDER.** `provider_of(rec, now)` reads the gsd_mission.provider_hold seam: the provider breaker's
  quota, auth and transient classes, plus its own degraded fallback. It is read only at a capital boundary or under
  predictive PRESSURE.
  - A live hold there means WAITING_PROVIDER: the judge returns `none` with `wake_at`. Nothing is granted, resumed
    or released, and the Owner is not pinged.
  - A grant already written waits too. Its key does not change, so it is resumed exactly once after the reset.
  - Hours exhausted still wins (EXHAUSTED_OWNER), because that boundary is the Owner's either way.
  - A provider hold on a HEALTHY mission is not a capital state.
  - The weekly account ceiling (account_governor, Owner Q2 85%) stays an Owner-policy refusal: it is the Owner's rule,
    not the provider's.
- **Deterministic wake.** The wake is the provider's own reset, taken at the first top-up pass at or after
  `wake_at`, so it lands within one poll of the reset.
  - `capital_waiting_provider` is written when a wait starts or its reset moves, never on every pass.
  - `capital_provider_cleared` is written when the wait ends, with `waited_s` and `late_s`.
  - A quarantine (until None) needs a re-login, which is not a capital act.
- **Metrics.** `capital_metrics(mid)` is computed from the ledger only:
  - `authorized_capital_stall_s`: the time spent in parks that ended without a new Owner act (an auto grant or a
    resume over authority that already existed).
  - `owner_boundary_s`: the time spent in parks that ended on an Owner raise. `open_s` covers parks still open.
  - `renewal_latency_s` (p50 and max).
  - `owner_interrupts`: "legitimate" when the why names an Owner rule (ceiling, hours, top-ups exhausted, no progress,
    weekly). Anything else is listed under `review`, not counted as avoidable, because the ledger cannot prove that.
  - `predictive_rate`, `provider_waits`, `receipt_less_raises`.
  - Consumer: `mission_topup.py status --mission <id>` returns {policy, capital, metrics} for the Owner packet.
- **Census.** `mission_topup.py census [--days N]` reads the ledger once and gives the per-mission metrics, totals and
  the top 10 stalls.
- **Kill switch** `CPP_TOPUP_PROVIDER=off`: a provider hold no longer separates from capital (the pre-W5 behaviour).
- **Gates:** test_mission_topup_w5 15/15. Each pole has its control: no provider means a grant, the switch off means
  a grant, a park ended by a top-up's own set is auto, HEALTHY is left untouched.