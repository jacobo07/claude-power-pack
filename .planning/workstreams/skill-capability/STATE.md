---
gsd_state_version: "1.0"
milestone: v1
milestone_name: skill-capability
current_phase: 1 — Card precision
current_plan: Not started
status: planning
stopped_at: Workstream created; P0 ledger + done-gate wrapper sealed interactively
last_updated: "2026-10-03T00:00:00.000Z"
last_activity: 2026-10-03
last_activity_desc: Workstream created from the approved skill-capability program
progress:
  total_phases: 9
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
workstream: skill-capability
created: 2026-10-03
current_phase_name: Card precision
---

# Project State

## Mission

Skill / Capability Program: drive every pillar A-N of the approved master program to an evidence-backed
terminal disposition. Mission terms: skill-capability, card-precision, skill-delivery, skill-listing,
compile-out, capability-lifecycle. Availability without residency, proven by need-time delivery.

## Current Position

**Status:** Ready to plan
**Current Phase:** 1 — Card precision
**Last Activity:** 2026-10-03

## Sealed before the run (interactive pane, session c85f3eb9)

- Plan `bd5a5a5c`. P0: ledger pre-registration (A-N, denominators D-LISTING / D-CARD / D-SESSIONS / D-W7,
  retained settings: `/skillOverrides` sha256 + `/env/CLAUDE_DOCTRINE_CARDS=deny`) and the wrapper verifier.
- `--selftest` PASS: 10 wrapper checks (rebind control, R1 clean + 8 mutants) + every inherited CE check.
- Done-gate: `python tools/test_skill_capability_program.py --final` (FAIL by design: 14 pillars open).

## Decisions

- [P0]: CE's `V-CEP-REAL-HANDOFF` pins "frozen at 1cabd117 -> not landed", false since fa9ae2ed / 8b62b6ce touched
  its probe file again, so CE's own `--selftest` / `--final` currently FAIL (S0). The CE file is not edited here (live
  mission). The wrapper substitutes exactly that line with `V-SCP-REAL-HANDOFF`, pinned to the probe file's history
  as read at run time; every other CE line must pass, and both red poles of the substitution were driven.
- [Plan]: the committed ledger is the authority; the verifier re-runs each IMPLEMENTED pillar's gate.
- [Plan]: Owner items are batched into `vault/programs/skill-capability/owner-bundle.md`; never asked mid-run.

## Session Continuity

**Stopped At:** Workstream created, ready to plan Phase 1
**Resume File:** None
