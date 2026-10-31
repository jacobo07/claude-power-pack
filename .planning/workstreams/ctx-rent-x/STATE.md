---
gsd_state_version: "1.0"
milestone: v1
status: ready
stopped_at: Roadmap created by the arming pane
last_updated: "2026-10-31T00:00:00.000Z"
progress:
  total_phases: 8
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
milestone_name: ctx-rent-x
workstream: ctx-rent-x
created: 2026-10-31
current_phase: 1
current_phase_name: Phase 1 (see ROADMAP.md)
last_activity_desc: Owner approved `approve ctx-rent-x only`; goal declared; mission armed
---

# Project State

Authority: `ROADMAP.md` + `REQUIREMENTS.md` here, and `vault/plans/ctx-rent-x-2026-10-31.md`.
Budget: goal `ctx-rent-x`, authority 55M processed tokens + 1 top-up of 20M; hard ceiling 75M; closeout reserve 5M.
Arming pane f432029e (interactive, PP root) did the Reality Scan and arming inline; its spend is measured at arm time below.

## Spend log (processed tokens, `mission_spend.py session-tree`)

| when | session | tokens | note |
|---|---|---:|---|

## Owner notes

(none)

## Phase 1 results (worker epoch 2, 2026-10-31, plane GEX44)
- Estate 2026-10-25..10-31T15:00Z: 970 sessions, 15,773 calls, 1.563B processed; floor_rent 975M (62%). top-level 63% floor share, mean floor 59.5K; worker:background 66%, subagent 50%. All generation UNKNOWN (no CCR receipts on this host). Files: `vault/programs/ctx-rent-x/estate-gex44-w0.json`, `estate-gex44-prev.json`, `weekly-delta.txt` (diff, prior week 10-18..10-25).
- Carriage (035583c5, tb-m2): floor 88K, mean input 232K; attachment ~119K/call (dominant), tool_result ~25K, calibration est/actual 1.06 (APPROX).
- Dead rent, offline Belady, 3 transcripts (APPROX upper bound): 035583c5 470,770 of 2,849,011 result-rent (16.5%); 382f1d27 207,913/3,557,374 (5.8%); 770ad1bc 233,103/3,257,145 (7.2%). Never-referenced: 216K/82K/97K. Commands in `vault/programs/ctx-rent-x/dead-rent.json` header run: `python3 tools/ctx_rent.py dead-rent <3 files>`.
- `test_ctx_rent.py` 20/20; `ccr_release` source_commit committed in 58f310aa.
- Phase 1 acceptance reached on GEX44 data (delta by class; gen split BLOCKED-ON-LAPTOP: LAPTOP_STEPS L1/L2). Phase 1 marked COMPLETE except the laptop generation split.
- Spend: this session 67aa29b4 = 1,033,530 processed (measured, session-tree). Epoch-1 spend still unbooked (no sid in handoff).
- DECISION: ff-merge of mission/ctx-rent-x-w0 into mission/ctx-rent-x skipped; the mission is bound to w0 and the laptop coordinator fetches w0. Reversible later.
- OWNER NOTE: none needed. Next runnable: Phase 2 (floor diet) edits `~/.claude` on GEX44, which the roadmap forbids from here -> its edits go to LAPTOP_STEPS; Phase 2 BLOCKED-ON-LAPTOP.
