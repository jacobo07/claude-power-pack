---
phase: 02-persistent-failures-and-remote-integrity
plan: 01
subsystem: mission-supervisor
tags: [pillar-C, IC-C, provider-breaker, auth-park, credentials, mutation-drill]
requires: []
provides:
  - "tools/test_persistent_failure_park.py: 24 V-PFP-* gates plus --drill (5 mutants)"
  - "gsd_mission.AUTH_FALLBACK_RE and _auth_hold_without_breaker (breaker-less auth park)"
  - "provider_breaker.credentials_state, credentials_expired, auth_released; decide(credentials=, trace=); ledger event provider_released"
affects: [02-02, 02-03, 02-04]
tech-stack:
  added: []
  patterns: ["stat-only credentials comparison in the degraded path", "shape-only secret reader (no token value leaves it)"]
key-files:
  created: [tools/test_persistent_failure_park.py]
  modified: [tools/gsd_mission.py, tools/provider_breaker.py]
decisions:
  - "Releasing an AUTH quarantine requires credentials rewritten strictly AFTER the refusal AND judged usable (unexpired, or lapsed but refreshable); unmeasurable keeps the park"
  - "The breaker-less fallback judges only host-written (model <synthetic>) replies and only stats the credentials file"
status: complete
commits: 1
plan_head_before: aa30640bd7c4240993f4c2c0678952933be0a63b
actuals:
  tokens: 8400
  tasks: 3
  commits: 1
metrics:
  completed: 2026-10-03
requirements: [IC-C]
---

# Phase 2 Plan 01: Auth refusal parks the mission until a re-login Summary

An authorization refusal (`Login expired - Please run /login`, host-written, zero usage) now parks a mission in a non-relaunching state with or without `provider_breaker.py`, and a credentials file rewritten after the refusal with a usable expiry releases it (`provider_released`), through one gsd_mission.py hunk and breaker-side release logic.

**Code commit (floor for plan 02-02, `PP_COMMIT_FLOOR`): `5962571c840943ae0a3aa901efb08e69a04434da`**
(`git show --stat HEAD` lists exactly tools/gsd_mission.py, tools/provider_breaker.py, tools/test_persistent_failure_park.py).

## What was done

- **Task 1 (tracer):** the 137-relaunch shape driven through the real `supervise` pass (fixture copies the measured transcript shape; successors advanced to owner through the real adopt path). RED against the gap, GREEN after ONE gsd_mission.py hunk (`@@ -1903,2 +1903,39 @@`, old-start > 1850, pillar A region untouched).
- **Task 2:** `credentials_state` (seven keys only), `credentials_expired`, `auth_released`, `decide(credentials=, trace=)`, `hold_for` ledgers `provider_released`. Kill switch `CPP_BREAKER_CRED_RELEASE=off`.
- **Task 3:** `--drill` (5 mutants, all killed, unmutated control green before and after), source-level drill on a /tmp copy with sha256 before/after identical, full regression against the pre-phase baseline.

## Pre-phase baseline (taken before the first edit; the .basefail lists)

All six files existed before `tools/test_persistent_failure_park.py` did (`find /tmp -newer` printed nothing).

```
test_provider_breaker                       (no FAIL lines)           tail: BREAKER_PASS=18/18  threshold=18/18
test_gsd_mission                            FAIL V-MC-PLAN-FACTS-REFUSES-OVERLAP PLAN GRAPH (checked at hand-off; the repository wins if it has changed):
                                                                      tail: MC_PASS=212/213
test_gsd_epoch                              (no FAIL lines)           tail: EPOCH_PASS=82/82
test_gsd_mission_cwd_align                  (no FAIL lines)           tail: MCA_PASS=16/16  threshold=16/16
test_gsd_mission_legacy_characterization    FAIL V-G23-LEGACY s_cards /s_cards/capped: '<CARD bf42db8a5474e71e 7828B>' != '<CARD ead7e63bb019f6ca 7912B>'
                                            FAIL V-G23-CARD-BYTES /cards/bf42db8a5474e71e: missing now; /cards/ead7e63bb019f6ca: new now
                                            FAIL V-G23-CLEAN-AFTER-MUTANTS /cards/bf42db8a5474e71e: missing now; /cards/ead7e63bb019f6ca: new now; /scenarios/s_cards/capped: '<CARD bf42db8a5474e71e 7828B>' != '<CARD ead7e63bb019f6ca 7912B>'
                                                                      tail: G23_PASS=29/32  threshold=32/32
test_handoff_packet                         FAIL V-HPKT-ATTACH: packet is UNJUDGED: bridge BRIDGE_FAILED: engine: node v18.19.1 outside ^22.23.2 || ^24.14.0
                                            FAIL V-HPKT-PARTIAL-REFUSED: packet is UNJUDGED: bridge BRIDGE_FAILED: engine: node v18.19.1 outside ^22.23.2 || ^24.14.0
                                                                      tail: TypeError: 'NoneType' object is not subscriptable   (pre-existing, node v18)
```

Regression result after the change: for all six suites `diff basefail afterfail` prints nothing and the summary lines are identical (BREAKER 18/18, MC 212/213, EPOCH 82/82, MCA 16/16, G23 29/32, handoff_packet the same TypeError). Plane: gex44, node v18.19.1.

## RED output, verbatim

Task 1, before any gsd_mission.py edit:

```
FAIL V-PFP-137-FALLBACK-PARKS: launches=3 provider_held(auth,quarantine) rows=0 (3 relay cycles, breaker unimportable)
PASS V-PFP-137-FALLBACK-VISIBLE: provider_breaker_unavailable rows=3
PASS V-PFP-137-BREAKER-PARKS: launches=0 held=['provider auth QUARANTINED (streak 1): QUARANTINE (credentials) -- auth: Login expired · Please run /login']
PASS V-PFP-FALLBACK-NORMAL-REPLY-RELAYS: launches=1
PASS V-PFP-FALLBACK-QUOTED-NOT-PARKED: launches=1 (a model quoting 'Please run /login' is not a host refusal)
FAIL V-PFP-FALLBACK-HOLDS-WITHOUT-RELOGIN: launches=1 (credentials older than the refusal)
PASS V-PFP-FALLBACK-RELEASES-ON-RELOGIN: launches=1
FAIL V-PFP-AUTH-PARITY: AttributeError: module 'gsd_mission' has no attribute 'AUTH_FALLBACK_RE'
PFP_PASS=5/8  threshold=8/8
```

Task 2, before any provider_breaker.py edit (the 8 Task-1 gates were green by then):

```
FAIL V-PFP-CRED-SHAPE-ONLY ... V-PFP-CRED-MISSING (8 gates): AttributeError: module 'provider_breaker' has no attribute 'credentials_state'
FAIL V-PFP-RELEASE-ON-RELOGIN, V-PFP-HOLD-UNCHANGED, V-PFP-HOLD-RELOGIN-STILL-EXPIRED, V-PFP-HOLD-CRED-UNREADABLE, V-PFP-RELEASE-KILL-SWITCH, V-PFP-RELEASE-ONLY-AUTH: TypeError: decide() got an unexpected keyword argument 'credentials'
FAIL V-PFP-SUP-RELOGIN-RELAYS: launches=0 provider_released rows=0
PASS V-PFP-SUP-NO-RELOGIN-PARKS: launches=0 provider_released=0 provider_held(auth)=3
PFP_PASS=9/24  threshold=24/24
```

## GREEN and drills

- `python3 tools/test_persistent_failure_park.py` -> `PFP_PASS=24/24`; `PASS V-PFP-137-FALLBACK-PARKS: launches=0 provider_held(auth,quarantine) rows=3 (3 relay cycles, breaker unimportable)`.
- `--drill`:
  ```
  PASS DRILL-CONTROL unmutated run: 24/24 gates green
  KILLED M1 AUTH_FALLBACK_RE never matches by V-PFP-137-FALLBACK-PARKS
  KILLED M2 auth_released always releases by V-PFP-HOLD-UNCHANGED
  KILLED M3 auth_released never releases by V-PFP-RELEASE-ON-RELOGIN, V-PFP-SUP-RELOGIN-RELAYS
  KILLED M4 credentials_expired always False by V-PFP-HOLD-RELOGIN-STILL-EXPIRED
  KILLED M5 fallback ignores the synthetic check by V-PFP-FALLBACK-QUOTED-NOT-PARKED
  PASS DRILL-CLEAN-AFTER-MUTANTS unmutated rerun: 24/24 gates green
  DRILL killed=5/5
  ```
- Source-level drill (/tmp copy, `_auth_hold_without_breaker(sid, now)` call replaced by `None`): `FAIL V-PFP-137-FALLBACK-PARKS: launches=3 ...` and `FAIL V-PFP-FALLBACK-HOLDS-WITHOUT-RELOGIN`. Real files: `sha256sum` before/after identical (gsd_mission.py `29bdac5a...a0ca`, provider_breaker.py `3d82505d...0744`), `diff` printed nothing.
- `grep -c` of token-value indexing in provider_breaker.py -> `0`; `python3 tools/provider_breaker.py status --mission m-none` -> exit 3, "mission record not found".

## Deviations from Plan

**1. [Plan-driven commit granularity] One commit for all three tasks.** The plan's Task 3 specifies a single pathspec commit of the three files and requires `git show --stat HEAD` to list exactly them (it is the PP_COMMIT_FLOOR for 02-02); Tasks 1 and 2 carry no commit step. Followed the plan rather than the generic per-task-commit convention.

**2. [Rule 1 - Bug, in my own test harness] Drill re-runs counted each other's ledger rows.** The first `--drill` run showed `DRILL-CLEAN-AFTER-MUTANTS 20/24` because the ledger is keyed by mission id and the gates reused ids across runs (a mutant could also have been "killed" by stale row counts). Fixed in `drive()` with a unique mission id per run; control 24/24, five mutants killed, rerun 24/24. No production code involved.

Otherwise the plan executed as written. No auth gates. No architectural changes.

## Known Stubs

None.

## Threat Flags

None. The credentials reader surface was in the plan's threat model (T-02-01-01/02); V-PFP-CRED-SHAPE-ONLY pins that no canary token value appears in the returned dict or in the `why` of an unreadable file.

## Open items (not this plan)

- Gap 3 (a budget renewal launching a fresh successor of a quarantined mission) is closed in 02-03 via `provider_breaker.lineage_hold`, not here.
- Ledger `state.C` NOT written: the PRG (a real parked mission in a live sweep) is Owner-run; plan 02-04 records the `[C]` owner-bundle line. `python3 tools/test_incremental_cognition_program.py --pillar C` is expected to stay `CEP_PILLAR_C=FAIL` (no terminal disposition).
- Deploying this to the a7 install (which predates provider_breaker.py) is an Owner action (owner bundle), never done from this phase.
- Pre-existing GEX44 reds (node v18 plan-graph facts, G23 card bytes) are unchanged and out of scope.

## Self-Check: PASSED

- `tools/test_persistent_failure_park.py`, `tools/gsd_mission.py`, `tools/provider_breaker.py` exist and are in commit `5962571c840943ae0a3aa901efb08e69a04434da` (verified with `git show --stat HEAD`; no deletions).
- `PFP_PASS=24/24`, `DRILL killed=5/5`, six-suite diff against the pre-phase baseline empty, one gsd_mission.py hunk (old-start 1903).
