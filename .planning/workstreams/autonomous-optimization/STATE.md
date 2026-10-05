---
gsd_state_version: "1.0"
milestone: v1
milestone_name: autonomous-optimization
current_phase: 0 — Spec, gen2 freeze, novelty gate
current_plan: Not started
status: planning
stopped_at: Workstream created from the approved plan; armed on GEX44
last_updated: "2026-10-05T00:00:00.000Z"
last_activity: 2026-10-05
last_activity_desc: Workstream created from the approved autonomous-optimization plan
progress:
  total_phases: 8
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
workstream: autonomous-optimization
created: 2026-10-05
current_phase_name: Spec, gen2 freeze, novelty gate
---

# Project State

## Mission

Autonomous Optimization (IC gen2): observe execution, detect recurring avoidable cost, price it, build the smallest
challenger, prove it, promote through `modules/tower/ratchet`, make future work inherit it. KME-L zero-rescan is the
first proving incident; a second workload must be taken by the loop itself.

## Current Position

**Status:** Ready to plan
**Current Phase:** 0 — Spec, gen2 freeze, novelty gate

## Decisions

- [Owner 2026-10-05]: inline plan APPROVED; run plane GEX44 (laptop 1.84 GB free < 4 GB gate).
- [Plan]: new pillars live in an IC gen2 ledger because the gen1 `frozen` object is immutable.
- [Plan]: champion/challenger is offline replay on the corpus copy; no extra model sessions (IC rows 11/12).
- [Plan]: TOK-18 Gen3 (T2-1 canary from 2026-10-11) is not touched by this programme.
- [Owner 2026-10-05, ONE-ARM WAIVER of IC row 19]: "Arm now, default env". Preflights at arm time: a7 NOT_READY
  (auth_expired, pp_install_stale), a5 NOT_READY (pp_install_stale), default env with
  CPP_NODE_EXE=/opt/node-v24.14.0/bin/node NOT_READY on pp_install_stale only = hash-floor false positive (picks
  25a10ce5/308da56b in live 4856b50d; PFP 28/28, LG 20/20 on GEX44). The default env is undeclared, so the relay
  launch gate does not run the preflight. The waiver covers this arm only; a re-arm needs exit 0 or a new waiver.
  Relays launched by agora-mission-sweep run with system node v18 (row 16 wiring still pending): only
  node_bridge consumers are affected; do not judge MC/HPKT gates on this plane without CPP_NODE_EXE.

## Session Continuity

**Stopped At:** Phase 0 not started.
**Next exact action:** write `vault/specs/autonomous-optimization.md`, then the gen2 ledger + FROZEN_AT.
**Resume File:** this STATE.md + vault/plans/autonomous-optimization-2026-10-05.md
