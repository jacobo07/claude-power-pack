---
covers: [bamr, account-governor, quota, mission-recovery, burn-optimization, statusline-quota-tap]
status: PARTIALLY PROVEN (P1-P2 afb43d63, P3 bf315ce6, P5 census + this spec landed; P5 hold, P4 gaps, UKDL, ratchet open)
owner_decisions: 2026-11-20 (session 05242a26)
---
# Budget-Aware Mission Recovery (BAMR)

## Problem (measured 2026-11-20, not assumed)
1. **The quota the estate judged was not the quota.** `account_governor` judged API-eq dollars over an
   ESTIMATE calibration (4570 $ = 100 %): 83.58 % weekly. The harness's own statusline `rate_limits.seven_day`
   said **18 %** at the same moment (CC 2.1.329). It was ~1.4 points from refusing every arm and top-up.
   The configured window (Sunday 00:00 UTC) is also wrong: the official reset is `1795626000` (Wed 17:00 UTC).
2. **Unknown was an allowance.** Unreadable telemetry returned ALLOW+UNKNOWN; a missing host was summed as 0.
3. **Recovery bypassed the governor.** Only `arm` asked. Relay, rotation, replacement, quota wake, top-up wake
   and the same-session `--resume` continuation launched without any quota check.
4. **Any file in account-governor-hosts/ was summed.** `measure` without `--host` wrote DESKTOP-PMT5BS8.json
   beside laptop.json -> 126 % (caused and reverted in this session).
5. **Admission scanned the whole transcript store** when config had no reset: > 180 s per launch decision.

## Owner decisions (2026-11-20, AskUserQuestion, this session)
- Plan approved; caps: session <= 40 $ API-eq (soft 25 $); autonomous model spend 0 until a real 5h/7d
  reading exists or the weekly reset. (A real reading now exists; nothing was armed regardless.)
- HR-001 granted: statusline tap in settings.json; CPP StopFailure hook beside Orca's (not yet built: no consumer).
- 5-hour reserve: 20 % (refuse at >= 80 %). Weekly reserve stays 15 % (refuse at >= 85 %).
- Unknown or stale quota blocks autonomous model spend; deterministic work continues.

## Architecture (owners unchanged; nothing parallel built)
| Concern | Owner | Change |
|---|---|---|
| Official quota | `hooks/statusline_quota_tap.js` -> `~/.claude/state/quota-reading.json` | new, zero model cost, no polling |
| Quota decision | `tools/account_governor.py` | official > estimate > UNKNOWN(refuse); `deterministic` always allowed; configured hosts only; check never scans |
| Launch admission | `gsd_mission.launch_worker` + `gsd_epoch.continue_worker` | both call `gsd_mission.account_refusal` before any claim; deterministic/done-gate closes run before it |
| Burn evidence | `tools/burn_census.py` | new, read-only census of mission records |

Kill switches: `CPP_QUOTA_TAP=off`, `CPP_GOVERNOR_UNKNOWN=allow`, `CPP_MISSION_ACCOUNT_ADMISSION=off`.
Rollback: revert the BAMR commits; restore `~/.claude/backups/settings.json.bamr-p1-20261120.bak` for the statusline.

## Gates (exact commands, from the repo root)
- `python tools/test_account_governor.py` (V-CCN-GOV-*, V-BAMR-*)
- `python tools/test_statusline_quota_tap.py` (V-QTAP-*)
- `python tools/test_mission_account_admission.py` (V-BAMR-ADMIT-*)
- `python tools/test_burn_census.py` (V-BURN-*)
- Live: `python tools/account_governor.py check --action relaunch` -> ALLOW+OFFICIAL while a session renders.

## Known limits (evidence, not opinion)
- Freshness of the official reading depends on some session rendering a statusline in the last 900 s.
  Background `claude --bg` workers are not known to render one; during a period with no interactive pane the
  reading goes STALE and launches are refused (Owner decision: unknown blocks). Mitigation candidate: an
  interactive pane, or a later decision to accept an older weekly reading.
- No `five_hour` key arrives for this account; treated as "no 5-hour window reported" (claude-swap upstream
  semantics), recorded per decision in the ledger as `no 5h window reported`.
- Burn census "no tree change" is a proxy: slim/read-only workers and worktree work can read as no change.

## Burn census (2026-11-20, `python tools/burn_census.py`)
669 missions; 9 024.7 M tokens measured (152 unmeasured = unknown); 1 406.1 M (15.6 %) in missions whose tree
never changed. Largest class: missions **superseded** after spending with no tree change (~528 M in 4).
Then `owner blocked and budget: older than N h` (186 M), `owner hold, owner dead` (81 M, 16 missions).

## Interruption taxonomy (P4): each class -> its existing owner and action
No second classifier was built: every class below already has an owner. Read 2026-11-20 from the code named.
| Class (Invariant 6) | Owner / signal | Action | Gap? |
|---|---|---|---|
| 5-hour limit | `quota_hold` (host reply, QUOTA_RE) + governor `five_hour` | hold until stated reset; relaunch only via governor (5h reserve 20 %) | none (same action as weekly) |
| weekly limit | same + governor `seven_day` | hold until reset; relaunch via governor (reserve 15 %) | none |
| quota/authorisation unknown | governor `REFUSE+UNKNOWN` | no model launch; deterministic work continues | NEW this spec |
| auth / permission revoked | `provider_breaker` AUTH | QUARANTINE until re-login or `clear` | none |
| context exhausted | `hooks/mission_wall.js` + rotation | fresh session with card (no compaction on this path) | none |
| compaction not confirmed | n/a: Ralph rotates instead of compacting; native autocompact is a safety net only | -- | not applicable |
| worker died | host listing + pid (`liveness`) | host restarts a busy crash; mission replaces a stopped one (CAS) | none |
| transient provider failure | `provider_breaker` TRANSIENT | backoff 300 s x 2^n, cap 1 h; quarantine at 4 | unknown host text is read as TRANSIENT (bounded, not blind) |
| permanent error / repeated equivalent failure | breaker streak (QUARANTINE_AFTER=4); `loop_budget` CONSECUTIVE_FAIL_LIMIT=2 | quarantine / kill | breaker allows 4, Regla 12 says 2: unreconciled |
| tool failure | worker-level; no mission class | -- | GAP (no mission-level signal) |
| stall / no verifiable progress | `no_progress` (3 epochs, no tree change) | HALTED, never renewed | none |
| Owner cancel / pause | mission state + `owner_hold` | terminal / parked | none |
| permission prompt | BLOCKED | surfaced, never replaced | none |
| ambiguous remote effect | none generic | -- | GAP (no reconciliation owner for external effects) |
| corrupt state | `load` + `history.missing` in status | record judged with seq gaps | partial |
| host memory | `resource_admission` (RAM floor) | refuse launch | none |
| unknown cause | breaker -> TRANSIENT; governor -> UNKNOWN | bounded backoff / refuse | none |

## Single authority (P6, read-only audit 2026-11-20)
- Launch authority is the mission supervisor's CAS claim (`launch_worker`, `continue_worker`); a duplicate supervisor
  loses the CAS and launches nothing (`tools/test_gsd_mission.py:518`, the `reason="dup"` launch, observed green 248/248
  this session; `tools/test_a5_u7.py:152` covers it too but that suite fails before it, pre-existing). The host only
  restarts a busy crashed worker.
- Lazarus (`modules/session_resilience/epoch.py`) only detects/records; revival writes `tasks.json` resumes. Measured:
  0 of 750 known mission worker sids appear in `pane_map.json` (101 panes) or the 83 mission-repo `tasks.json` files;
  positive control (this interactive session is found). Safe by observation, NOT by construction:
  `cpc_os/vscode_autorun.generate_from_snapshot` has no mission-worker exclusion. Candidate guard, other owner.
- Orca's StopFailure hook is a notifier; it launches nothing.

## Pre-existing failures seen (not BAMR; identical at baseline 5dccbb62 in a detached worktree)
- `tools/test_a5_u7.py`: JSONDecodeError in `guard_denies` (empty stdout).
- `tools/test_gsd_mission_capsule_v2.py`: `V-MV2-L1-WITHIN-BACKOFF-HELD-SILENT` 78/79.

## Open obligations (next executable first)
1. P4 gaps above: reconcile breaker QUARANTINE_AFTER=4 with Regla 12 (2); a mission-level tool-failure signal; an
   external-effect reconciliation owner. The StopFailure recorder lands only with a consumer (Liveness Standard).
2. P5 BURN_OPTIMIZATION_REQUIRED hold in gsd_mission fed by burn_census signals (supersede-after-spend first).
3. P6 single-authority audit: Lazarus (`session_resilience/epoch.py`) vs mission supervisor vs host restart.
4. Owner: correct `account-governor.json` reset_at / calibration (implied calibration is reported by `status`).

## Review of P3 (pp-code-reviewer, sonnet, 2026-11-20): APPROVE, 0 critical/high
- No launch path bypasses the gate: `worker_argv` only via `launch_worker`/`_launch_slim`; `resume_argv` only in
  `continue_worker`; callers read `.get("ok")`/`.get("why")` only (no crash on the refusal dicts).
- LOW-1 arm-guard fail-open + DEFAULT_STATE: fixed in `bf315ce6` (same `account_refusal` policy).
- LOW-2 a refused mission adds one governor ledger row per sweep tick (bounded by missions x ticks; accepted).
- INFO-1 the closeout reserve launch is gated too: Owner decision needed if a closeout must run on the last quota.
- Out of scope, named gap: `claude -p` spend outside the mission machinery is ungated --
  asc_design_gate_run.py:108, asc_inherit_run.py:68, agent_carrier_run.py:128, compound_unattended.py:216,
  ccn_bench.py:87, exp_successor_packet.py:165, agent_discovery_curve.py:64.

## UKDL entries (LANDED 17c6717a)
T-QUOTA-ESTIMATE-IS-NOT-QUOTA-001, PR-ADMISSION-AT-EVERY-LAUNCH-PATH-001, T-HOST-NAME-DEFAULT-DOUBLE-COUNT-001,
T-ADMISSION-CHECK-THAT-SCANS-001, T-SUPERSEDE-AFTER-SPEND-IS-THE-LARGEST-BURN-001 -- in `vault/knowledge_base/ukdl-universal.md`.

## P5 design question (open, Owner)
The hold is named but undefined. It would be a new `set_owner_hold` kind (`tools/gsd_mission.py:1952`), not a new
mechanism. Undecided: (a) trigger -- per mission at supersede/replace time when it spent >= N tokens with no tree
change, vs at `arm` when the census class of the same repo already burned without change; (b) threshold N;
(c) release -- Owner `release_owner_hold` only, or automatic once an optimisation record cites the census class.