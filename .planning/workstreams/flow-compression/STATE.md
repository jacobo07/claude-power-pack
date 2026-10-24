---
gsd_state_version: "1.0"
milestone: v1
milestone_name: flow-compression
current_phase: 3
current_phase_name: S3 Admission refusal loop + packet identity
status: ready
workstream: flow-compression
created: 2026-10-24
last_updated: "2026-10-24T00:00:00.000Z"
last_activity_desc: Phases 1-2 sealed (arm_preflight landed, PRE 16/16)
progress:
  total_phases: 8
  completed_phases: 2
---

# Project State

Authority: `ROADMAP.md` + `REQUIREMENTS.md` in this directory, and `vault/specs/flow-compression.md`.
Budget: authority 140M processed tokens + 2 semantic top-ups of 30M; absolute ceiling 200M. Arming pane spent
~4.5M (reality scan) + S1 build before arm (measured at arm time in RESUMPTION_FILE.md).
Stop only on: done-gate pass, budget spent, or an action that needs Owner authorization (name it).
Update this file and `RESUMPTION_FILE.md` (this dir) after every sealed phase, with measured spend.
