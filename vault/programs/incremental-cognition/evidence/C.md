# Pillar C -- persistent-failure retry classification: evidence

Plane: GEX44 (`kobicraft-gex44`, node v18.19.1, python3 3.12.3), run branch `mission/incremental-cognition-run`.
Written by plan 02-04 from the plan 02-01 and 02-03 summaries and a fresh regression run on 2026-10-03.

## Frozen rule (verbatim from `ledger.json`, `frozen.pillars` id C)

> correctness exception. A worker that dies on an authorization-class failure (Login expired) parks the mission in a non-relaunching state until a qualifying precondition change; red test reproduces the 137-relaunch shape

## Commands and observed outputs

Code commits: `5962571c840943ae0a3aa901efb08e69a04434da` (plan 02-01: the park) and
`60e7947dcf3cf0f9c660e412ec6276a8b2922f99` (plan 02-03: renewals inherit a quarantine, one pre-launch gate).

RED, quoted from `02-01-SUMMARY.md` (the 137-relaunch shape driven through the real `supervise` pass, before any
`gsd_mission.py` edit; the passes beside the fail are the controls proving the scenario relaunches when it should):

```
FAIL V-PFP-137-FALLBACK-PARKS: launches=3 provider_held(auth,quarantine) rows=0 (3 relay cycles, breaker unimportable)
PASS V-PFP-137-BREAKER-PARKS: launches=0 held=['provider auth QUARANTINED (streak 1): QUARANTINE (credentials) -- auth: Login expired · Please run /login']
PASS V-PFP-FALLBACK-NORMAL-REPLY-RELAYS: launches=1
PASS V-PFP-FALLBACK-QUOTED-NOT-PARKED: launches=1 (a model quoting 'Please run /login' is not a host refusal)
FAIL V-PFP-FALLBACK-HOLDS-WITHOUT-RELOGIN: launches=1 (credentials older than the refusal)
```

RED for the renewal gap, quoted from `02-03-SUMMARY.md`:

```
PASS V-LG-RENEWAL-PRECONDITION: renewed_as=m-d02e54e8cf76 predecessor=HALTED owner_kept=True launches_in_pass1=0
FAIL V-LG-RENEWAL-NO-LAUNDER: launches=1 held=[] provider_held(inherited_from=predecessor) rows=0
PASS V-LG-RENEWAL-CONTROL-HEALTHY: launches=1 held=[] (predecessor's last reply is an ordinary model reply)
```

GREEN, observed again for this evidence (2026-10-03, foreground, from the ic-run worktree):

```
python3 tools/test_persistent_failure_park.py          PFP_PASS=24/24  threshold=24/24
python3 tools/test_persistent_failure_park.py --drill  DRILL killed=5/5
python3 tools/test_mission_launch_gate.py              LG_PASS=19/19  threshold=19/19
python3 tools/test_mission_launch_gate.py --drill      DRILL killed=6/6
```

Key GREEN lines (02-01 / 02-03 summaries): `PASS V-PFP-137-FALLBACK-PARKS: launches=0 provider_held(auth,quarantine) rows=3
(3 relay cycles, breaker unimportable)`; `PASS V-LG-RENEWAL-NO-LAUNDER: launches=0 held=['provider auth QUARANTINED
inherited from m-lg-nol-r2: ...'] provider_held(inherited_from=predecessor) rows=1`.

Drills (each mutant applied in-process, unmutated control green before and after): park `M1 AUTH_FALLBACK_RE never
matches`, `M2 auth_released always releases`, `M3 auth_released never releases`, `M4 credentials_expired always
False`, `M5 fallback ignores the synthetic check` all KILLED; launch gate `M1 lineage_hold always None`, `M6
lineage_hold stops after the first hop` and four more all KILLED. Source-level drills on /tmp copies: the park call
replaced by `None` makes `V-PFP-137-FALLBACK-PARKS` and `V-PFP-FALLBACK-HOLDS-WITHOUT-RELOGIN` fail; the gate block
deleted makes `V-LG-RENEWAL-NO-LAUNDER` and `V-LG-PREFLIGHT-REFUSES` fail (`LG_PASS=8/19`); real-file sha256 before/after
identical both times.

Regression (this run; FAIL lists equal the 02-03 baselines):

| suite | observed | FAIL lines |
|-------|----------|-----------|
| test_provider_breaker | BREAKER_PASS=18/18 | none |
| test_gsd_mission | MC_PASS=212/213 | `V-MC-PLAN-FACTS-REFUSES-OVERLAP` (pre-existing: node v18.19.1 is outside `^22.23.2 \|\| ^24.14.0`) |
| test_gsd_epoch | EPOCH_PASS=82/82 | none |
| test_gsd_mission_cwd_align | MCA_PASS=16/16 | none |
| test_gex44_env_preflight | ENVPF_PASS=55/55, `--drill` 6/6 | none |
| test_gex44_env_deploy | DEPLOY_PASS=16/16, `--drill` 6/6 | none |

Pre-existing GEX44 reds, not re-run here and quoted from 02-03: `test_gsd_mission_legacy_characterization` G23_PASS=29/32
(card bytes), `test_handoff_packet` TypeError with `V-HPKT-ATTACH` / `V-HPKT-PARTIAL-REFUSED` (node v18),
`node tools/test_gsd_x_runtime_preflight.js` GSDXPF_PASS=3/7 (laptop-plane).

Ledger check: `git diff --stat 34d08aa9 -- vault/programs/incremental-cognition/ledger.json` prints nothing. Pillar
status command, quoted:

```
$ python3 tools/test_incremental_cognition_program.py --pillar C
  FAIL L3 C: no terminal disposition
CEP_PILLAR_C=FAIL
```

## Artifacts (LF sha256 of each committed file the evidence relies on)

```
504e2f4b7035f31f831c48015eda896769d33b5e5be1fb3befbe0f5cb7508d86  tools/gsd_mission.py
098a61ebfd60133b69825233f652a73ea3a14f5c5876d0802dd91e5b3bcd6ece  tools/provider_breaker.py
95e538e52af2e218724d33ae95c62b3e45e823be83ceea6ad775b29579d6198f  tools/mission_launch_gate.py
1677cbfa1d81619a5a2c6fa84896592ac31475514b494314ba07f675047ad5c0  tools/test_persistent_failure_park.py
85167c30ace95071f658b75f36da735a7971348b12e5573a664629b383f7b48f  tools/test_mission_launch_gate.py
```

## Product Delta

What changes for the Owner:

- A worker that meets an expired login (`Login expired - Please run /login`, host-written, zero usage) is no longer
  relaunched, with or without `provider_breaker.py` present. The a7 loop (96+ dead relaunches, 137 in the replayed
  transcript shape) stops at the first refusal and the mission shows `provider_held` (class auth, quarantine true).
- After a re-login (credentials rewritten after the refusal and judged usable) the mission resumes by itself:
  ledger `provider_released`, one relay. Nobody has to un-stick it by hand.
- A budget renewal can no longer launch a fresh successor into a quarantined lineage: the successor inherits the hold
  of its nearest predecessor that has an owner (`provider_held` carries `inherited_from`).

## Intelligence Delta

What the system knows now that it did not:

- An auth-class host reply is classified even when the breaker module is missing: the breaker-less fallback judges
  only host-written (`<synthetic>`) replies, so a model that merely quotes "Please run /login" is not parked.
- A credentials rewrite AFTER the refusal is a qualifying precondition change; a rewrite that is still expired, or
  unreadable, is not (unmeasurable keeps the park).
- A lineage inherits its predecessor's hold; a missing or unreadable predecessor record means "nothing to inherit",
  never a quarantine, and the walk is bounded (`MAX_LINEAGE_HOPS = 4`, cycles terminate).

## Named debts

- `gsd_mission.py arm` launches its first worker through `launch_worker` without the pre-launch gate (attended action;
  gating it needs a second `gsd_mission.py` hunk). Shrink-only; recorded in `owner-bundle.md` and in `B.md`. Closing
  condition: `mission_launch_gate.refusal` called on the arm path, proven by a red-first test.
- `tools/test_gsd_x_runtime_preflight.js` is laptop-plane: 3/7 on GEX44.
- `modules/liveness/reachability.py` does not enumerate `tools/` (its banner says `modules/` only); the reachability
  proof for the new tools is the import edge from `gsd_mission.supervise`, driven by `V-LG-REAL-PREFLIGHT-E2E`.
- The Windows-only "bare git is not on PowerShell PATH" trap in `modules/cascade_prevention/dangerous_cmds.py` fires on
  Linux for plain `git` commands: a rule defect for its owner, not staleness.

## Status: OPEN

Ledger `state.C` is NOT written and IC-C is not ticked. The terminal is the Owner-run PRG (a real parked mission in a
live sweep, `[C]` line in `owner-bundle.md`, saved as `evidence/C-prg.md`). `--pillar C` prints `CEP_PILLAR_C=FAIL`
"no terminal disposition", as expected.
