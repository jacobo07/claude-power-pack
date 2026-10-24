# Ownership map — /cpp-gsd-long mission control plane (2026-10-24, HEAD d5b2590e)

Reality scan of the arming pane. Line numbers drift; grep the function names.

- Ledger: `gsd_long_run.ledger_append` -> `~/.claude/state/gsd-autorun-ledger.jsonl`; every `gsd_mission.transition` writes a row.
- Sweep: `tools/gsd_long_run_sweep.ps1` -> `gsd_mission supervise --actions-only` -> `mission_topup sweep` -> retired v2 sweep.
- GSD Core: `~/.claude/gsd-core` v1.14.0 (not vendored); reached ONLY via `gsd-tools.cjs query init.manager`
  (`gsd_long_run.gsd_manager`). ROADMAP parsing = Core. GSD X = `modules/gsd_x/` + `tools/gsd_mission.py` and satellites.
- State machine: `gsd_mission.transition` (single CAS writer), `plan_next` (pure decider), `_supervise_core` (effects).
  Other transition callers: gsd_epoch.continue_worker, mission_supersede, mission_steward._step, decision_plane, dgl unit_done,
  gsd_x/goal/providers/long_run.cancel (second HALTED writer).
- Admission: `admit_route` -> `route_admission.admit`; refusal `admission_refusal` compares `admission.packet_sha256` with
  raw-bytes sha of the packet (EOL/encoding changes count). `readmit_for_relay` re-admits only consumed_epoch.
  Packet mutators: `mission_steward._r1` rewrites `<base>.residual.md` in place (can be the admitted packet);
  worker/git edits of in-tree packets. Events `route_admission`, `launch_refused_admission`.
- Launch: `launch_worker` (packet -> admission -> resource_admission -> deterministic -> baseline -> CAS claim -> spawn);
  same-session continue = `gsd_epoch.continue_worker` (COPY detection `_COPY_RE`). `arm` is NOT gated by
  `mission_launch_gate.refusal` (debt at mission_launch_gate.py:30) and never calls gsd_status.
- Resources: `tools/resource_admission.py` (floors: top-level-worker 3000 MB); second authority `mission_resources.py`.
- Capsule/custody: `_capsule_rotate` / `_capsule_seal`; custody reasons from `rollover.completeness`.
- Cost: pure `mission_spend.judge` (trip ratio 2.0, stall 0.5); drivers `_cost_breaker` vs `_reconciled_breaker`
  (flag-switched), plus `_phase_breaker`, authority guards, `session_budget_guard.js`, `mission_gate.js`;
  `econ_incident.classify` re-derives level by regex. Estimate `_auto_budget`; top-up `tools/mission_topup.py`.
- Terminal: `slim_result` + `_supervise_core` "slim worker finished ... no receipt" -> HALTED; receipt resolvers:
  `_receipt_path`, `packet_receipt_path`, AMR successor receipt (three). Reconcilers: gsdx_chain.try_seal,
  mission_steward R1/R3, settle_stopped_worker, renew_mission. `gsd_epoch.epochs` closes only on halted/completed.
- Owner boundary: `blocked_recovery` -> `mission_policy.classify_blocked` (RESOLVE_BY_DEFAULT/POLICY/OWNER);
  `MAX_DECISION_RECOVERIES`; AMR `_amr_boundary`; two `goal_liveness` (mission_policy, mission_recovery).
- NO_PHASES: `gsd_long_run.gsd_status`; `GSD_HOLD_BLOCK_AFTER NO_PHASES=2`.
- Replay seams: `plan_next`/`supervise` injectables (now, sessions, gsd_status, runner, measure, fingerprint, dry_run);
  golden fixture `tools/fixtures/gsd_mission_legacy_golden.json`; `tools/a5_counterfactual.py`; `gsd_epoch.census/epochs`.
- Context (S1): `gsd_epoch.decide_turn_end` (ceiling), `hooks/mission_wall.js` (mid-turn wall, now pct OR tokens),
  `gsd_mission.apply_rotation_invariant` (single owner of the rotation-before-compaction ordering).
