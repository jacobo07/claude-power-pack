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
- `30bdaaa` C1b+C2: index schema v2 (prompts, spawns, subagents, quota tables; one-pass
  ancestry via `tis_observed.calls_from(on_line=)`), `tools/fanout_ledger.py` (quota / summary /
  top / prompt), RCA §15 (>= 2 accounts share the transcript store: H4).
- `9a9ea1f` C3: `scheduler.decide_spawn` (SHADOW ONLY) + `tools/estate_shadow.py replay`.
- `4cb3606` C4.0: `tools/floor_probe.py probe` (attachment-text fit, provider remainder explicit).
- Plan §11 = the approved reconciliation (Owner "y" 2026-10-02). Peer state-centric mission owns
  Goal state / packet / delta (`modules/gsd_x/goal`); CCP feeds it metrology only.
Coherence anchor: `test_usage_index` 22/22, `test_fanout_ledger` 15/15, `test_estate_shadow` 9/9,
`test_floor_probe` 4/4; `python tools/usage_index.py window 2026-09-30T17:00:00Z
2026-10-02T09:40:00Z` = 23,925 calls / 6,230,548,450 cache read (must survive the v2 backfill).

## 3. Active decisions
- The 75 % reading is `suspended` in `vault/config/weekly_meter_readings.json`; the alarm shows
  NO percentage until the Owner answers the meter question (RCA §14 hypotheses 1-3).
- Do not edit `tools/rollover.py`, `context-watchdog.py` (SPEC-ECON-ROLLOVER peer-owned and
  implemented), `tools/gsd_mission.py` (Ralph, peer), `hooks/agent-solo-guard.js` (audit G4).
- Model-calling runs wait for the weekly reset (2026-10-07 17:00Z) unless the Owner says "spend now".
- `loop_budget.py` (CO-09) is a declared-budget library with no spawn-path caller; C3 did not
  build on it (spawns declare nothing). A live C3 hook needs Owner OK (shared dispatcher).
- Provider quota: the Wed-17Z seven-day window is REJECTED 2026-10-02T11:54Z -> 2026-10-07T17:00Z.

## 4. Next three actions
1. PRG on the real index once the v2 backfill is done: anchor totals unchanged; one real HUMAN
   prompt tree and one CONTINUATION/MISSION root (`fanout_ledger.py prompt/top/summary`);
   `estate_shadow.py replay` (protected_deferred must be 0, review top 15); `floor_probe.py
   probe` (rent ranking). Record results in RCA §16 + plan §12.
2. C4.1: pick the largest CPP-controllable lifetime-rent component with an enforcement-preserving
   path; quality A/B waits for the reset.
3. C4.0b zero-quota probe of `updatedInput.model` on the Agent tool (audit G5).

## 5. Start instruction
`git log --oneline -5 -- tools/usage_index.py`, run the coherence anchor, read plan section 10,
then action 1.
