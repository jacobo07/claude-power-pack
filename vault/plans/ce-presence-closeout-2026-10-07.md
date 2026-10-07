# ce-presence -- closeout at goal cap (2026-10-07)

Goal `ce-presence` CONTAINED: used 6,080,514 of cap 6,000,000 (guard refusal, pane 77cfae43). Cap is not raisable;
continuing needs a NEW goal id from the Owner (e.g. `ce-presence-2`, root C:\Users\User\Apps\pp-ce-presence).
Where it went: planner pane 77cfae43 ~4.5M before U6a + ~1M after (Opus 1M, ~215-260k per call, MEASURED by guard);
U6a worker 6929ab8d 1,042,266 processed (968,006 cache read + 68,218 create + 42 in + 18,327 out), Sonnet, $0.65.
Lesson (confirmed again): continuing in the long planner pane ("do it here") costs ~250k per call; a fresh pane does
the same step for ~15-100k.

State:
- SEALED, committed on ce/presence: fb9f10fd (plan, packet, route), b4314931 (U6a resolver: resolve_baseline,
  work_class, CPP_CE_BASELINE shadow|enforce|off, legacy_reason enum, policy in mission-budget-defaults.json).
  Re-verified in this pane: baseline 19/19, envelope 55/55, admission 43/43, epoch 92/92 (all exit 0).
  Code review: worker_argv reads the transitioned record (gsd_mission.py:1054) -> resolution really reaches argv.
- UNCOMMITTED in the worktree, NOT yet run: provenance fix in resolve_baseline (records `values`; a field still
  equal to what the last resolution wrote is re-resolved, an operator change stays explicit) + 2 gates
  V-BASE-RERESOLVE-STAYS-POLICY / -OPERATOR-EXPLICIT in tools/test_gsd_mission_baseline.py. Bug it fixes: after the
  first launch every policy value read back as `explicit`, so a policy change never reached a live mission.
- NOT MERGED into the live checkout. No mission launches with the resolver yet.

Next exact actions (fresh pane, cwd this worktree, under the new goal id):
1. `python tools/test_gsd_mission_baseline.py` -> expect 21 passed; red-before: run it against
   `git show b4314931:tools/gsd_mission.py` -> the 2 RERESOLVE gates must FAIL; restore by hash. Commit both files.
2. Merge ce/presence into the live branch at C:\Users\User\.claude\skills\claude-power-pack (no dirty overlap in
   gsd_mission.py / mission-budget-defaults.json at 02a20a93); re-run the 4 suites there.
3. Arm U6b with NO --model/--autocompact/route (self-hosting negative canary); confirm sonnet + 250k from the worker's
   raw transcript and a `baseline_resolved` ledger row.
