---
covers: [flow-compression, rotation-invariant, mission-preflight, admission-loop, economic-lease, terminal-reconciler, blocker-compiler, mission-replay]
tier: T2
owner_approved: 2026-10-24 (Owner reply "y" to the inline master plan)
---

# Spec — GSD X Autonomous Flow Compression

## Objective
Raise critical-path productive duty cycle of `/cpp-gsd-long` missions: remove avoidable idle and
in-worker waste without weakening Owner authority, capital ceilings, proof gates or workspace isolation.
All policy lives in GSD X (`tools/gsd_mission.py` + satellites, `modules/gsd_x/`). GSD Core
(`~/.claude/gsd-core`, CLI only) is not modified; any Core need goes through the special gate in the plan.

## Measured baseline (ledger `~/.claude/state/gsd-autorun-ledger.jsonl`, since 2026-10-10, 378 missions)
Mission-hours (summed, NOT wall-clock): RUNNING 1254 · BLOCKED 523 · PREPARED 398 · HALTED 382.
Relay median 3.4 min (healthy, out of scope). Context: 0 rotations / 382 compactions since 10-08.
Admission rejects 544, concentrated: 313 "packet changed" in 2 missions (10-11..10-12), 231 DEFER/none in 8.
HALTED "no receipt": 86 missions, followed by steward_settled (45) / mission_renewed (34): likely accounting.

## Slices (each: kill switch, tests, Production Reality evidence, micro-commit)
- S1 rotation invariant — DONE in arming pane: `apply_rotation_invariant` (0.70 x compaction line) bounds
  `continue_max_tokens` and derives `wall.advisory_tokens`; `mission_wall.js` token wall; policy v2;
  `epoch_compacted` evidence (`rotation_verdict`). Kill: `CPP_ROTATION_INVARIANT=off`. Gate: `tools/test_rotation_invariant.py`.
  Remaining: live proof (a mission rotates instead of compacting, state intact) + rehydration cost
  (fresh launch -> first verified semantic delta) + champion/challenger vs compaction cycles.
- S2 arm preflight — one `arm_preflight()` reusing existing checks: gsd_status NO_PHASES, mission_launch_gate
  (closes `mission_launch_gate.py:30` debt), custody/dirty, resource_admission, rotation invariant, authority.
  Deterministic repair only when unambiguous. Idempotent. Historical replay: prevented / moved-earlier / legitimate.
- S3 admission — identical refusal without causal delta -> hold with unblock condition (no 5-min retry loop);
  packet digest normalised (EOL/BOM); `mission_steward._r1` writes a new versioned path, never the admitted file;
  DEFER autopsy (false-defer rate). No admit/reserve/launch transaction unless a real race is proven.
- S4 economics — estimate-variance with verified semantic delta (HEAD-tree / .planning fingerprint) and remaining
  authority -> recompile + reforecast, not a trip. Stall and authority ceiling unchanged. Semantic top-up
  renewal, idempotent by seq. Class calibration from unit_settlement. Controls: productive crosses, runaway stops.
- S5 terminal — dispose the 149 h; close epochs on slim/supersede terminals; one receipt resolver;
  reconciler RECOVERED_DONE/CONTINUATION/FAILED/AMBIGUOUS, never DONE without receipt_judge closure.
- S6 blockers/Owner — taxonomy from the ledger; every mission_blocked carries class, unblock condition,
  independent-work flag; foreseeable decisions batched at arm; RESOLVE_BY_POLICY only for explicit policy.
- S7 replay — harness over the ledger through plan_next() seams; champion vs challenger S2-S6; mutants
  (always-admit, never-rotate, always-renew, terminal-without-proof) must fail; mission-hours vs wall vs critical path.
- S8 work stealing — DORMANT: activation predicate recorded; build only if S7 shows a consumer. Activation predicate: at least one incident where an independent safe action existed while the critical path was blocked AND the blocker row recorded independent_work=true. Measured value at the 07 pin (ledger prefix 1740294 bytes, 6339 rows, sha256 b47ff018fb44766fb9e2add7b9e23276c18dc6c2ec84cb88d4709c82d95e2743): FALSE. The pinned prefix holds 55 mission_blocked rows and 0 of them carry independent_work=true (the key is absent from all 55, so this is not-recorded, not measured-false-per-row); recounted in phase 8 by tools/s9_kv_check.py from flow_replay.read_prefix and agreeing with 07-VERIFICATION. S8 stays DORMANT, and no work-stealing code is written, until the S6 independent_work field accumulates real rows that make the predicate true.
- S9 Knowledge Vault + UKDL + CBR + red team.

## Acceptance (master done-gate)
The seven mandatory milestones of the Owner prompt, each with real/replayed evidence; existing suites green
(`test_gsd_mission`, `test_mission_continuity` [37/38 pre-existing V-AMCR-ONE-RESOLVER-INVENTORY debt],
`test_mission_recovery`, `test_gsd_epoch`, `test_cpp_gsd_long_routing`, `test_rotation_invariant`); no GSD Core change.

## Rollback
Per-slice env kill switch; land via pathspec commit on the live branch with a backup copy of each live file first.

## Budget
Central 112M (low 70M, high 170M); authority 140M + 2 semantic top-ups of 30M; absolute ceiling 200M.
