# Cognitive Control Plane — RESUMPTION

Read this and continue with zero prior context. Update after every sealed unit.

## 1. Identity
Repo `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`,
shared tree (690+ dirty paths from other panes: commit by explicit pathspec only).
Plan of record: `vault/plans/cognitive-control-plane-2026-10-02.md` (Owner APPROVED 2026-10-02,
six defaults; section 10 = audit fixes, overrides sections 4-6). Incident: `weekly-limit-burn-rca-2026-10-02.md`.
Thesis: close the burn control loop inside EXISTING owners; no new mega-system.

## 2. Sealed
- `19a7bc5` plan + C0: CO-08 scheduler docstrings now say verdict LIVE / enforcement ABSENT.
- `286ccbe` C1: `tools/usage_index.py` (incremental SQLite index at
  `~/.claude/state/usage_index/index.sqlite`, typed burn states, MONITOR_FAILURE) wired into
  `cost_gate`; `weekly_burn` unwired. RCA §13 (P0: subagents do not inherit the parent; the floor
  is set by agent type) and §14 (meter reconciliation FAILS: no weighting of transcript usage
  explains 75 % -> 90 %; GEX44 not the cause; anomaly replay NORMAL throughout).
Coherence anchor: `python tools/test_usage_index.py` 22/22; `python tools/usage_index.py window
2026-09-30T17:00:00Z 2026-10-02T09:40:00Z` = 23,925 calls / 6,230,548,450 cache read.

## 3. Active decisions
- The 75 % reading is `suspended` in `vault/config/weekly_meter_readings.json`; the alarm shows
  NO percentage until the Owner answers the meter question (RCA §14 hypotheses 1-3).
- Do not edit `tools/rollover.py`, `context-watchdog.py` (SPEC-ECON-ROLLOVER peer-owned and
  implemented), `tools/gsd_mission.py` (Ralph, peer), `hooks/agent-solo-guard.js` (audit G4).
- Model-calling runs wait for the weekly reset (2026-10-07 17:00Z) unless the Owner says "spend now".
- `modules/cognitive_os/loop_budget.py` (CO-09, "subagent admission budget") has only one
  non-test caller: inspect it before building any C3 budget.

## 4. Next three actions
1. C2 fan-out ledger: extend the index with subagent meta (`agentType`, `toolUseId`,
   `spawnDepth`, model inherit-vs-explicit) and a "why did this prompt cost N calls" report.
   0 model calls.
2. C3 shadow: first MEASURE which spawn classes traverse PreToolUse-Agent (positive control: a
   mission worker's subagent), then a NEW sibling non-blocking hook that logs shadow verdicts
   from the cached estate view.
3. C4.0 zero-quota probe of `updatedInput.model` on the Agent tool.

## 5. Start instruction
`git log --oneline -5 -- tools/usage_index.py`, run the coherence anchor, read plan section 10,
then action 1.
