# Phase 1 EVIDENCE: Hard enforcement

Date 2026-10-15. Worktree `ccr-v5`, branch `ccr/v5`. Python 3.12 with `-I`, Node on PATH.

## Reality check (iteracion-avanzada, phase 1)
- Source read: `hooks/mission_wall.js` (PostToolUse only, feedback via `decision:'block'`, cannot deny),
  `hooks/session_budget_guard.js` (registered PreToolUse: dispatcher `EVENT_MAP` lines 124-126, 133; settings
  matchers Bash|PowerShell, Write|Edit|MultiEdit|NotebookEdit, Read|Grep, Agent|Task), `hooks/amr_fence.js`,
  `tools/gsd_mission.py` (`set_envelope`, `_cost_breaker`, supervise cost-hold branch), `tools/mission_spend.py`.
- False premise found: the ROADMAP said `mission_wall.js` is on the registered PreToolUse path. It is not.
  Class 1 (plan assumed a capability the code does not have). Fix: the deny sits in `session_budget_guard.js`.
- Class of the incident defect: PHASE_STOP_LOSS_MODEL_OVERRIDABLE (0 hits for any phase breaker in gsd_mission /
  mission_spend / mission_recovery / gsd_epoch before this phase). UKDL entries are written in Phase 5.

## Commands and observed output
| Gate | Command | Exit | Observed |
|---|---|---|---|
| Lease judge | `python -I tools/test_phase_lease.py` | 0 | `PHASE_LEASE_PASS=23/23` |
| Mission lease + breaker | `python -I tools/test_gsd_mission_phase_lease.py` | 0 | `PHASE_LEASE_MISSION_PASS=15/15` |
| In-turn gate | `python -I tools/test_mission_gate.py` | 0 | `MISSION_GATE_PASS=31/31` |
| Regression cost hold | `python -I tools/test_gsd_mission_cost_hold.py` | 0 | `COST_HOLD_PASS=23/23` |
| Regression owner hold | `python -I tools/test_gsd_mission_owner_hold.py` | 0 | `OWNER_HOLD_PASS=37/37` |
| Regression guard | `python -I tools/test_session_budget_guard.py` | 0 on rerun | `SBG_PASS=22/22`; first run 21/22 |

`V-SBG-LATENCY` (< 50 ms) is a host-load flake: it failed twice on the UNCHANGED main tree (127.47 ms, 138.79 ms)
and failed once and passed once (26.07 ms) in the worktree. Not caused by this phase; the gate adds one missed
`readFileSync` (the worker marker) per call for a non-worker session.

## Fault injection requested by the roadmap
| Case | Test | Result |
|---|---|---|
| Phase at hard while the model "wants to continue" -> stopped | V-PL-HARD-HOLDS-AND-STOPS | held + stopped in the same sweep, no grace flag on disk, `stops=[['claude','stop',...]]` |
| Ambiguous prior-phase accounting -> BLOCKED | V-PL-PHASE-MOVED-BLOCKS, V-PL-UNMEASURED-BLOCKS, V-PL-STATE-UNREADABLE-BLOCKS, V-LEASE-BASE-ABOVE-SPENT | all BLOCKED, held and stopped |
| Subagent past cap -> denied | V-MG-SUBAGENT-CAP-DENIES-PAST, V-MG-SUBAGENT-TOKENS-DENIES (msg id counted once: 1,200 not 1,800) | denied |
| Hold flag -> denied (worker + subagents) | V-MG-COST-HOLD-DENIES-{Bash,Read,Edit,Grep}, V-MG-GUARD-DELEGATES-COST-HOLD | denied |
| Control: under cap -> allowed | V-PL-CONTROL-UNDER-LEFT-RUNNING, V-MG-CONTROL-* (11 controls) | allowed |
| Model cannot write its own lease | V-PL-CALLER-BASE-IGNORED, V-MG-AUTHORITY-DENIES-* (6), V-MG-CONTROL-ALLOWS-* (4) | base is measured, never supplied; record/verb writes denied; `status`, Read and ordinary edits pass |

## Verdict
- Lease judge, supervise breaker, in-turn cost-hold deny, authority deny, subagent call/token caps: **PROVEN**
  against the real `set_envelope` / `supervise` / `set_owner_hold` / hook code with temp state (V-gates above).
- Successor "reforecast-only packet": **OBSERVED, partial**. The hold carries `resume_with: "reforecast-only: ..."`
  and the reason names the reforecast, but no separate compiled packet file is generated. Recovery's packet compiler
  is Stage B work; the hold keeps the mission parked until the Owner acts, so no spend continues.
- `agent_id` in the real PreToolUse payload: **UNJUDGED**. The gate keys a subagent by `agent_id`, falling back to
  `agent_type` (documented in `carrier_bash_guard.js`). The fallback caps per type per session, not per agent.
  Phase 4's canary measures the real payload.

## Residuals and Owner steps
- OWNER STEP (not done, outside the allowed edits): tool lanes with no registered guard are not denied by a cost
  hold: Glob, WebFetch/WebSearch, MCP tools, Skill, Task* tools. A `settings.json` matcher plus a dispatcher lane
  would close them. A held worker is also stopped by the sweep within one pass and by Agent/Bash/Edit/Read denials.
- Landing is Stage B: the live copy of `session_budget_guard.js` in the main tree is unchanged, so none of this
  protects a running mission until the branch is merged. `lib/mission_gate.js` must land with it.
- Per-agent-type caps in the record (`subagent_caps`) have no writer yet beyond a transition; PGO overrides are a
  later wiring. Defaults: 30 calls / 3,000,000 processed tokens; env `CPP_SUBAGENT_CAP_CALLS/TOKENS`.
- Kill switches: `CPP_MISSION_GATE=off` (in-turn gate), `CPP_COST_HOLD_STOP=off` (sweep stop).

## Learning seed (written in Phase 5)
Class: PHASE_STOP_LOSS_MODEL_OVERRIDABLE / SUBAGENT_SPEND_UNGOVERNED. Rule shape: an authority a worker can
read past is guidance; the check must run at the effect boundary the worker cannot skip, from a record the worker
cannot write.
