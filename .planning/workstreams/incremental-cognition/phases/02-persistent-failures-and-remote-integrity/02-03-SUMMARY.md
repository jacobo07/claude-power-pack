---
phase: 02-persistent-failures-and-remote-integrity
plan: 03
subsystem: mission-supervisor
tags: [pillar-B, pillar-C, IC-B, IC-C, launch-gate, lineage-hold, renewal, mutation-drill]
requires: ["02-01", "02-02"]
provides:
  - "tools/mission_launch_gate.py: enabled, preflight_enabled, preflight, refusal -- the single pre-launch authority composing the lineage hold (C) and the env preflight (B)"
  - "provider_breaker.lineage_hold(rec, now, load=None) and MAX_LINEAGE_HOPS = 4"
  - "tools/test_mission_launch_gate.py: 19 V-LG-* gates through the real supervise pass plus --drill (6 mutants)"
  - "gsd_mission.supervise: ONE pillar-B hunk (old-start 1544); ledger launch_gate_unavailable; row field launch_gate"
  - "ledger events provider_held (+inherited_from), launch_preflight_refused, launch_preflight_unmeasurable"
affects: [02-04]
tech-stack:
  added: []
  patterns: ["one authority at the boundary every successor crosses, asked before any destructive step", "closed verdict vocabulary: only a measured NOT_READY refuses", "declared-plane activation (CPP_MISSION_PLANE) so undeclared hosts are never judged by GEX44 rules"]
key-files:
  created: [tools/mission_launch_gate.py, tools/test_mission_launch_gate.py]
  modified: [tools/gsd_mission.py, tools/provider_breaker.py]
decisions:
  - "A renewed successor inherits the hold of its NEAREST predecessor that has an owner; a healthy nearest predecessor means nothing to inherit, a missing or unreadable record means None (unmeasured is not a quarantine)"
  - "The env preflight runs only on a declared plane (CPP_ENV_PREFLIGHT=on, or CPP_MISSION_PLANE non-blank and CPP_ENV_PREFLIGHT not off); UNMEASURABLE, a raising preflight and an unknown verdict string all launch and are recorded as UNMEASURABLE, never READY"
  - "Held reason for the lineage case carries the word 'inherited' and the predecessor id; the ledger provider_held row carries inherited_from"
status: complete
commits: 1
plan_head_before: 8118412dc92dd9764f3c683db4ed40b9e8243202
actuals:
  tokens: 9700
  tasks: 3
  commits: 1
metrics:
  completed: 2026-10-03
requirements: [IC-B, IC-C]
---

# Phase 2 Plan 03: One pre-launch gate -- renewals inherit a quarantine, NOT_READY envs refuse Summary

A budget renewal no longer launches a fresh worker into a quarantined lineage (0 launches, ledger `provider_held` with `inherited_from` = the predecessor), and on a declared mission plane every successor launch is refused with the env preflight's typed reasons when it measures NOT_READY, both through one `mission_launch_gate.refusal` call in one `gsd_mission.py` hunk.

**Code commit: `60e7947dcf3cf0f9c660e412ec6276a8b2922f99`** (`git show --stat HEAD` lists exactly tools/gsd_mission.py, tools/mission_launch_gate.py, tools/provider_breaker.py, tools/test_mission_launch_gate.py; no deletions).

## What was done

- **Task 1 (tracer):** the measured a7 renewal path driven through the real `supervise` pass twice (pass 1 budget-halts a 25 h old mission with a live idle owner and renews it; pass 2 meets the PREPARED successor). RED against the laundering, GREEN after `provider_breaker.lineage_hold`, the new `tools/mission_launch_gate.py` and ONE gsd_mission.py hunk.
- **Task 2:** the env preflight branch of `refusal` (`_env`): NOT_READY refuses with a ledger row and the typed reasons; READY and UNMEASURABLE launch; a raising preflight and an unknown verdict are UNMEASURABLE. Proven with a spy on the module's own `preflight` attribute and with the REAL `gex44_env_preflight` over a scratch HOME.
- **Task 3:** `--drill` (6 mutants), source-level drill on a /tmp copy with sha256 before/after, full regression with FAIL-list diffs, liveness, pathspec commit.

## RED output, verbatim

Task 1, before `lineage_hold`, the gate module or the hunk existed (preconditions and controls PASS, so the scenario really renews and really launches when healthy):

```
PASS V-LG-RENEWAL-PRECONDITION: renewed_as=m-d02e54e8cf76 predecessor=HALTED owner_kept=True launches_in_pass1=0
FAIL V-LG-RENEWAL-NO-LAUNDER: launches=1 held=[] provider_held(inherited_from=predecessor) rows=0
PASS V-LG-RENEWAL-CONTROL-HEALTHY: launches=1 held=[] (predecessor's last reply is an ordinary model reply)
PASS V-LG-RENEWAL-RELOGIN-LAUNCHES: launches=1 (credentials rewritten after the refusal, access token usable)
FAIL V-LG-LINEAGE-MULTIHOP: AttributeError: module 'provider_breaker' has no attribute 'lineage_hold'
FAIL V-LG-LINEAGE-CYCLE-BOUNDED: AttributeError: module 'provider_breaker' has no attribute 'lineage_hold'
LG_PASS=3/6  threshold=6/6
```

Task 2, with Task 1 green and the preflight branch still `return None`:

```
FAIL V-LG-PREFLIGHT-REFUSES: launches=1 refused_rows=0 held=None
FAIL V-LG-GATE-BEFORE-STOP: refused: stops=1 epoch=1 state=LAUNCHING; control(READY): stops=1 launches=1
FAIL V-LG-PREFLIGHT-UNMEASURABLE-LAUNCHES: launches=1 unmeasurable_rows=0 launch_gate=None
FAIL V-LG-PREFLIGHT-READY-LAUNCHES: launches=1 launch_gate=None
FAIL V-LG-PREFLIGHT-RAISES: launches=1 unmeasurable_rows=0 names_class=False launch_gate=None
FAIL V-LG-PREFLIGHT-UNKNOWN-IS-UNMEASURABLE: launches=1 launch_gate=None (an unknown answer is not READY)
FAIL V-LG-PLANE-DEFAULT-ON: preflight calls=0 launches=1 (CPP_MISSION_PLANE=gex44 alone)
FAIL V-LG-REAL-PREFLIGHT-E2E: launches=1 refused_rows=0 reasons=[] held=None
FAIL V-LG-REAL-PREFLIGHT-CONTROL: preflight ran=False launch_gate=None launches=1 auth_expired in reasons=False (other reasons on this host: [])
LG_PASS=10/19  threshold=19/19
```

(The 10 passes include the gates that must hold before the branch exists: PREFLIGHT-OFF, UNMARKED-NOT-CALLED, GATE-OFF, GATE-UNAVAILABLE.)

## GREEN and drills

- `python3 tools/test_mission_launch_gate.py` -> `LG_PASS=19/19  threshold=19/19`. Key lines:
  - `PASS V-LG-RENEWAL-NO-LAUNDER: launches=0 held=['provider auth QUARANTINED inherited from m-lg-nol-r2: QUARANTINE (credentials) -- auth: Login expired · Please run /login'] provider_held(inherited_from=predecessor) rows=1`
  - `PASS V-LG-GATE-BEFORE-STOP: refused: stops=0 epoch=1 state=RUNNING; control(READY): stops=1 launches=1` (the control proves a launch does stop the owner, so "0 stops" on a refusal is not vacuous)
  - `PASS V-LG-PREFLIGHT-RAISES: launches=1 unmeasurable_rows=1 names_class=True launch_gate='UNMEASURABLE'`
  - `PASS V-LG-REAL-PREFLIGHT-E2E: launches=0 refused_rows=1 reasons=['auth_expired', 'hooks_broken', 'interpreter_unsupported'] ...`
  - `PASS V-LG-REAL-PREFLIGHT-CONTROL: preflight ran=True launch_gate='NOT_READY' launches=0 auth_expired in reasons=False (other reasons on this host: ['hooks_broken', 'interpreter_unsupported'])`
- `--drill`:
  ```
  PASS DRILL-CONTROL unmutated run: 19/19 gates green
  KILLED M1 lineage_hold always None by V-LG-RENEWAL-NO-LAUNDER
  KILLED M2 refusal ignores NOT_READY by V-LG-PREFLIGHT-REFUSES
  KILLED M3 UNMEASURABLE refuses by V-LG-PREFLIGHT-UNMEASURABLE-LAUNCHES
  KILLED M4 preflight_enabled ignores CPP_MISSION_PLANE by V-LG-PLANE-DEFAULT-ON
  KILLED M5 preflight_enabled always True by V-LG-UNMARKED-NOT-CALLED
  KILLED M6 lineage_hold stops after the first hop by V-LG-LINEAGE-MULTIHOP
  PASS DRILL-CLEAN-AFTER-MUTANTS unmutated rerun: 19/19 gates green
  DRILL killed=6/6
  ```
- Source-level drill (/tmp copy of `tools` and `modules`, the 1042-character inserted gate block deleted from the COPY, asserted to match once): `FAIL V-LG-RENEWAL-NO-LAUNDER: launches=1 ...`, `FAIL V-LG-PREFLIGHT-REFUSES: launches=1 ...`, `LG_PASS=8/19`. Real files, `sha256sum` before/after identical (`diff` printed nothing): gsd_mission.py `504e2f4b...`, provider_breaker.py `098a61eb...`, mission_launch_gate.py `95e538e5...`.
- Hunk proof: `git diff -U0 -- tools/gsd_mission.py` -> `@@ -1544,0 +1545,17 @@`, `grep -c '^@@'` = `1`, old-start 1544 (inside 1540-1550), directly above `turn_end = None`.

## Regression (baseline taken before the first edit, `/tmp/ic-p2-03-<suite>.base`)

| suite | before | after | FAIL-list diff |
|-------|--------|-------|----------------|
| test_gsd_mission | MC_PASS=212/213 | MC_PASS=212/213 | empty (V-MC-PLAN-FACTS-REFUSES-OVERLAP) |
| test_gsd_epoch | EPOCH_PASS=82/82 | EPOCH_PASS=82/82 | empty |
| test_gsd_mission_cwd_align | MCA_PASS=16/16 | MCA_PASS=16/16 | empty |
| test_gsd_mission_legacy_characterization | G23_PASS=29/32 | G23_PASS=29/32 | empty (3 FAIL lines) |
| test_handoff_packet | TypeError (node v18) | TypeError (node v18) | empty (2 FAIL lines) |
| test_provider_breaker | BREAKER_PASS=18/18 | BREAKER_PASS=18/18 | empty |

Also run after the change: `test_persistent_failure_park` PFP_PASS=24/24 and `--drill` killed=5/5; `test_gex44_env_preflight` ENVPF_PASS=55/55 and `--drill` killed=6/6; `test_mission_launch_gate` LG_PASS=19/19 and `--drill` killed=6/6. Plane: gex44, node v18.19.1, python3 3.12.3. The pre-existing reds are the node v18 / card-byte ones named in the plan.

## Liveness

`timeout 300 python3 modules/liveness/reachability.py` -> **exit 1**: `modules: 490 | REACHABLE: 310 | ORPHAN: 180 | UNKNOWN: 0 | gate offenders: 64`, last rows `tower/donegate | ORPHAN`, `tower/ratchet | ORPHAN`. That is standing debt in `modules/`; this plan touched nothing under `modules/`. Its own banner: "packages under `modules/` only. `tools/` is NOT scanned", so the new tools files are outside its denominator and the run is no evidence about them. The reachability proof that does exist is the import edge: `gsd_mission.supervise` imports `mission_launch_gate` (gsd_mission.py line 1551), which imports `gex44_env_preflight` inside `preflight()`, driven end to end with no spy by `V-LG-REAL-PREFLIGHT-E2E`.

## Deviations from Plan

**1. [Plan-driven commit granularity] One commit for all three tasks.** Tasks 1 and 2 carry no commit step; Task 3 specifies a single pathspec commit of the four files and `git show --stat HEAD` listing exactly them (same as 02-01 and 02-02).

**2. [Attribution] Commit trailer is `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`,** the line the session's attribution instruction gives, not the plan's literal `Claude Opus 5.5 (1M context)` text.

**3. [Rule 3 - harness] The first source-level-drill command began with `rm -rf /tmp/ic-p2-03-drill`;** a destructive-state hook asked for the five questions first. The directory did not exist (checked with `ls`), so nothing was lost; I dropped the `rm` and ran `mkdir -p` as the plan also says.

**4. [Test shape, host-dependent] V-LG-REAL-PREFLIGHT-E2E/-CONTROL assert on `auth_expired` only,** not on the overall verdict: on this host the real preflight over a scratch HOME also reports `hooks_broken` (no settings.json in the scratch HOME) and `interpreter_unsupported` (node v18.19.1), so the control is refused for other reasons. The control still proves the preflight ran (`launch_gate` set) and that `auth_expired` is absent with a future expiry. On a host with a supported node the control would launch.

**5. [Branch namespace] The commit is on `mission/incremental-cognition-run`,** the run branch the orchestrator set up, not an `agent-*` branch; the protected-branch check passed (not main/master/develop/trunk/release).

Otherwise the plan executed as written. No auth gates. No architectural changes.

## Named debt (shrink-only)

- `gsd_mission.py arm` launches its first worker through `launch_worker` directly and is NOT gated (attended action; gating it needs a second hunk). Plan 02-04 records it in B.md and as a `[B]` owner-bundle DEBT line.
- Deploying this to the a5/a7 installs (which predate `provider_breaker.py`) is an Owner/02-04 action, never done from this plan. Every currently deployed a5/a7 install reports `interpreters` UNMEASURABLE; per the gate's fail directions that is recorded as `launch_preflight_unmeasurable` and the launch proceeds (it refuses only on a measured NOT_READY, e.g. a7's `auth_expired`).

## Known Stubs

None.

## Threat Flags

None. New surface is ledger rows carrying reason codes and instants from the preflight (which never holds token values, 02-02 canary) and one import inside a try; T-02-03-01..07 are pinned by V-LG-RENEWAL-NO-LAUNDER/drill M1, V-LG-UNMARKED-NOT-CALLED/GATE-OFF, V-LG-PREFLIGHT-UNMEASURABLE-LAUNCHES/drill M3, V-LG-LINEAGE-CYCLE-BOUNDED, V-LG-GATE-BEFORE-STOP, V-LG-GATE-UNAVAILABLE.

## State bookkeeping

Ledger `state.B` / `state.C` NOT written: the PRGs are Owner-run (plan 02-04 adds the `[B]`/`[C]` owner-bundle lines). IC-B / IC-C stay unticked in REQUIREMENTS.md (requirement = ledger terminal).

## Self-Check: PASSED

- `tools/mission_launch_gate.py`, `tools/test_mission_launch_gate.py`, `tools/provider_breaker.py`, `tools/gsd_mission.py` exist and are in commit `60e7947dcf3cf0f9c660e412ec6276a8b2922f99` (`git show --stat HEAD`, no deletions).
- `LG_PASS=19/19`, `DRILL killed=6/6`, source-level drill FAIL lines present with sha256 identical, six-suite FAIL-list diffs empty, one gsd_mission.py hunk (old-start 1544).
