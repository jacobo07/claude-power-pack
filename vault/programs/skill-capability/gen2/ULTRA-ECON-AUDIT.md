# /ultra Phase 4 audit -- oneshot-architect-auditor on ULTRA-ECON-PLAN.md (2026-10-05)

Persisted by the parent (pane e1cb7fc6); the auditor is read-only. Auditor spend: 110,272 subagent tokens, 16 tool uses.
Premises: all 6 named owner paths exist. Gaps: 12.

1. [INTEGRATION] 4.3: hooks/agent-solo-guard.js:177-180 exits 0 on non-win32 before reading stdin; Gen 2 spawns run on
   GEX44 (Linux) -> a SHADOW spawn gate there records zero decisions; D4's 100-decision exit unreachable (silent dead gate).
   Fix: host spawn/model-call admission in tools/gsd_mission.py (J.md:5 owner) or a hook proven registered and
   platform-unconditional on GEX44; liveness check counting real GEX44 decisions.
2. [INTEGRATION] 4.3 "J detector" does not exist (J.md:3,16,31-32: DEFERRED, proposal only, owner gsd_mission.py);
   J.md:18-21 shared-checkout fingerprint defect not carried. Fix: owner = gsd_mission.py progress_fingerprint/no_progress,
   scoped to the mission's own branch/worktree.
3. [COMPLETION-GATE] W7: gsd_mission.py:486-493 budget_exhausted stops only on max_cycles/max_hours; no token ceiling ->
   D5 100/150 M not enforced at runtime. Fix: processed-token halt from usage_index over the mission's own transcripts,
   set at the admitted upper interval, never > 150 M, with a known-red drill.
4. [EDGE] 0.1: usage_index.window() is estate-wide by time and has no processed field. Fix: processed = in+cw+cr+out,
   filtered by program session ids (laptop) and mission clone project dirs (GEX44); commands in SPEND.md.
5. [COMPLETION-GATE] 0.1 baseline omits spend already incurred (D1: "todo lo previo a la decision"). Fix: anchor at the
   brief (2026-10-05), include panes c85f3eb9 and e1cb7fc6.
6. [COMPLETION-GATE] No per-wave allocation; no mechanical rule for what continues past 24 M. Fix: per-wave budgets in
   SPEND.md + pre-declared continue list (W3 replay, W6 compile) and stop list (W5 canary, E, 2.2 LLM classification).
7. [INTEGRATION] 4.1 routing premise unverified on GEX44 (clone .planning/config.json and gsd-core resolver not read).
   Fix: read both; single-spawn probe confirming the model id in the transcript before W5.
8. [COMPLETION-GATE] W5 canary has no paired control (replay averages on different tasks) -> reads "equivalent" whatever
   happens. Fix: freeze WU selection, proof contract, pass/fail metric, sequential-stop rule before W5; matched task
   families with a stated quality oracle.
9. [EDGE] W5 GEX44 model calls not ordered after E1. Fix: gate W5 and all GEX44 model work on an E1 terminal read.
10. [COMPLETION-GATE] W6 omits brief :2089-2097 / :2105-2121 predicates (proof has obligation, derivation reuse decision,
    external owner connected, det vs model share, Agent count, Opus calls, per-WU context, proof reuse, quality envelope).
    Fix: all 8 + 9 predicates as checked fields; D5 verdict mechanically requires them.
11. [INTEGRATION] Known-red phase-average test has no owning component/file; prose could satisfy it. Fix: name the
    budget-compile owner (one_shot / cost_collapse or a W6 tool) + test file, red fixture + green control.
12. [AUTH] 0.3 names a key but no user@host (PHASE1-NOTES:10 -> user likely kobii); no step deploys/pins the reader on
    GEX44. Fix: explicit user@host; copy reader at a pinned commit, verify remote sha256 before 0.1 and 3.3.

Audit-clean: 3.3 replay can return the other answer (exact reconciliation, seeded fixture + control, frozen 3.1);
D3, D6 for E, D5 thresholds carried faithfully; no parallel OS; 4.5 3 % materiality consistent with CE precedent.
