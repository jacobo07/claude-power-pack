# Phase 1 evidence -- W0 reality, baseline and incumbent measurement

- Branch `gsdx/pcc`, base `fbca24fc`.
- HEAD at writing: `29c7ed70`. Date: 2026-10-07.
- Worktree `C:\Users\User\Apps\pp-gsdx-pcc`. Nothing pushed.
- PHASE_DIR = `.planning/workstreams/gsdx-pcc/phases/01-w0-reality-baseline-and-incumbent-measurement`.

Phase commits (`git log --oneline fbca24fc..HEAD`, before this file's own commit):

```
29c7ed70 chore(gsdx-pcc): vault/progress.md entry for worker session 83e8b14f
f0406128 docs(01-05): complete incumbent measurement plan; record worker decisions
46af64c6 docs(gsdx-pcc-01): incumbent sweep->judge timelines and judge replay
8b83216c docs(gsdx-pcc-01): incumbent measurement -- all goal suites (mutation suite in a copy)
c75dc3cc fix(gsdx-pcc-01): reality-baseline in-copy runs get a clean one-commit git checkout
02032644 docs(gsdx-pcc-01): incumbent measurement -- gate_provider timed through the instrument
3fc8aebf docs(01-04): complete premises, liveness freeze and R10 plan
f83c2a61 docs(gsdx-pcc-01): DENOMINATOR R10 -- gsd_x/goal liveness debt tracked to Phase 10
96bdb8b1 chore(gsdx-pcc-01): freeze inherited liveness debt by name (65 standing, 57 new at fbca24fc)
ed0d833d docs(gsdx-pcc-01): HR-PREMISE-001 premise record for the spec's APIs (control included)
f42928f6 docs(01-03): complete goal timeline instrument plan
e9a61556 feat(gsdx-pcc-01): goal timeline instrument -- hermetic fixture goal through the real CLI
8aedb547 feat(gsdx-pcc-01): goal timeline instrument -- recorded goal over a verified copy
a9ae1e7d docs(01-02): complete reality-baseline instrument plan
77fcf1e8 feat(gsdx-pcc-01): reality-baseline instrument -- in-copy runs, UNKNOWN rows, table
a2bec412 feat(gsdx-pcc-01): reality-baseline instrument -- guarded hermetic suite timing
44708ffd docs(phase-1): record phase start (wave 1 in progress)
903005c2 test(gsdx-pcc-01): RED -- V-RB gates for the reality-baseline instrument (tool absent)
09386658 docs(01-01): complete R01 gate supervisor fix plan
0c93c0e9 docs(gsdx-pcc-01): UKDL trap -- handle-less supervisor loses gate output on Windows (R01)
6216a3c9 test(gsdx-pcc-01): mutation drill of the R01 fix -- revert KILLED, stderr-only recorded
58934936 fix(gsdx-pcc-01): gate supervisor hands its std handles to the gate (R01)
dc2ab789 chore(gsdx-pcc): track GSD state.json; ignore the hook-generated .pp-capabilities marker
5e43ddc3 docs(01): create phase plan
31f84167 docs(phase-1): add research and validation strategy
7852456d docs(01): auto-generated context (discuss skipped)
bce48c4f docs(gsdx-pcc): add Phase Details so the GSD roadmap parser sees the 10 phases
d07e266c plan(gsdx-pcc): spec, roadmap and denominator for proof-conserving convergence
```

## Results

| success criterion | verdict | evidence file | command | exit |
|---|---|---|---|---|
| SC1 every API the spec names exists with its real signature (HR-PREMISE-001) | PROVEN | 01-PREMISES.md, 01-premises.log, 01-premises-control.log | `python modules/error_prevention/premise_verifier.py --premises PHASE_DIR/01-premises.json` (control: `01-premises-control.json`) | 0 (control 1) |
| SC2 R01 fixed red-first: gate_provider 18/18, drill KILLED, UKDL written | PROVEN on this Windows host | 01-r01-red.log, 01-r01-green.log, 01-r01-drill.log, 01-phase-end-gate-provider.log | `python tools/test_gsd_x_goal_gate_provider.py`; `python tools/mutation_drill.py --spec PHASE_DIR/r01-drill.json` | RED 1 -> GREEN 0; drill 0; phase end 0 |
| SC3 incumbent measured: per-suite wall, judge replay, a real goal's sweep->judge timeline, UNKNOWN where unmeasurable | OBSERVED (1 suite UNKNOWN) | 01-INCUMBENT.md, 01-incumbent-suites-table.md, 01-incumbent-suites.jsonl, 01-timeline-*.json | `python tools/gsdx_reality_baseline.py suites/table`; `python tools/gsdx_goal_timeline.py recorded/fixture` | 0 per suite call; mutation suite UNKNOWN |
| Phase-end liveness gate | OBSERVED (debt frozen, not cleared) | 01-phase-end-liveness.md | `python modules/liveness/reachability.py` | 0 |

## R01

- **Incident:** on Windows every gate verdict's `observed` field was `''`, and the gate run logs were 0 B.
  - Pre-fix run logs (`%TEMP%\gsdx_gate_runs_7qvrkn49`): `gate-tok-ok.log`, `gate-tok-bad.log` and `gate-tok-slow.log`, all 0 B (01-01-SUMMARY).
- **Root cause:** the handle-less `subprocess.run(cmd)` at `modules/gsd_x/goal/providers/gate.py:72`, called under a supervisor whose stdout is the log file. The grandchild never received the supervisor's std handles, so its output never reached the log.
- **Class:** lens CLASE 4, a tool call that failed silently. The gate exited 0 and its evidence was empty.
- **Fix:** `58934936` runs the gate with `stdout=sys.stdout, stderr=sys.stderr`.
- **Regression:** the `V-GATE-VERDICT-FIELDS` gate, plus the committed drill spec `r01-drill.json` (revert mutant) and `r01-drill-stderr.json`.
- **Guard:** the gate_provider suite is in the final done-gate (ROADMAP item 1) and was re-run at phase end.
- **UKDL:** `T-SUBPROCESS-WITHOUT-INHERITED-STD-HANDLES-LOSES-GRANDCHILD-OUTPUT-ON-WINDOWS-001` (commit `0c93c0e9`, `vault/knowledge_base/ukdl-universal.md:15295`).

Verbatim:

- RED (`01-r01-red.log`):
  - `  FAIL V-GATE-VERDICT-FIELDS: verdict={'gate': 'gate_ok.py', 'exit_status': 0, 'observed': '', 'tree_hash': 'git:3a75e645697930094bbfbb95860f4ff53efa6c2c', 'revision': 'rev1', 'gate_class': 'unit', 'gate_pin': [['gate_ok.py', 'aa56ee99025e4171912fcd6b0bdb0a44fc494274e8cc561df48310738b4df244']]}`
  - `GSDX_GATE_PROVIDER_PASS=17/18  threshold=18/18`
  - `EXIT=1`
- GREEN (`01-r01-green.log`): `GSDX_GATE_PROVIDER_PASS=18/18  threshold=18/18`, `EXIT=0`.
- Phase end, fresh (`01-phase-end-gate-provider.log`): `GSDX_GATE_PROVIDER_PASS=18/18  threshold=18/18`, `EXIT=0`.
- Collateral, pre -> post (`01-r01-collateral-pre.log` / `-post.log`), all `EXIT=0`:

  | suite | pre | post |
  |---|---|---|
  | sweep | `GSDX_GOAL_SWEEP_PASS=14/14` | `GSDX_GOAL_SWEEP_PASS=14/14` |
  | gate_class | `GSDX_GATE_CLASS_PASS=11/11` | `GSDX_GATE_CLASS_PASS=11/11` |
  | cli | `GSDX_GOAL_CLI_PASS=25/25` | `GSDX_GOAL_CLI_PASS=25/25` |
  | chaos | `GSDX_GOAL_CHAOS_PASS=15/15` | `GSDX_GOAL_CHAOS_PASS=15/15` |

- Drill (`01-r01-drill.log`), revert mutant: `GSDX_GATE_PROVIDER_PASS=17/18  threshold=18/18`, `MUTANT KILLED gate=V-GATE-VERDICT-FIELDS`, `EXIT=0`. The clean control had passed first.
- Drill (`01-r01-drill-stderr.log`), stderr-only mutant: `GSDX_GATE_PROVIDER_PASS=18/18  threshold=18/18`, `MUTANT SURVIVED gate=V-GATE-VERDICT-FIELDS`, `EXIT=1`.
- Through the real CLI at the current engine (`01-timeline-fixture.json`): every one of the 4 gate receipts has `observed` = `['2 passed']`.

### Known limits

- **The stderr-only mutant SURVIVED** (verbatim above). The suite's gates print only to stdout, so losing stderr alone is invisible to `V-GATE-VERDICT-FIELDS`. This is recorded as a blind spot, not hidden.
- **`observed` keeps only the last log line, 200 characters** (`gate.py:179-181`). Carried to Phase 4 (D13 certificates).
- **POSIX / GEX44 was not re-run:** UNJUDGED.

## Premises (HR-PREMISE-001)

- **Real set:** `python modules/error_prevention/premise_verifier.py --premises PHASE_DIR/01-premises.json` -> `EXIT=0`. It covers 62 premises: 8 files and 54 attrs.
- **Control:** `python modules/error_prevention/premise_verifier.py --premises PHASE_DIR/01-premises-control.json` -> `[FAIL] decide in modules.parallel_mesh.pm_02_intent`, `EXIT=1`.
- **Corrections:** none needed.
- **Findings** (from [01-PREMISES.md](01-PREMISES.md), with file:line there):
  - `decide` lives at `modules/cognitive_os/scheduler.py:94`; `pm_02_intent` only wraps it (:220-233).
  - `CollisionDetector.overlap` is exact-token intersection, so `tools` and `tools/x.py` do not collide. Phase 3 needs its own prefix rule.
  - `tools/family_baseline.py` has build-b0/show/review/verify/revert and no promote; promotion is `modules.tower.ratchet.promote`.
  - `modules/tower/donegate.py` is REPORT-ONLY.
  - `tools/evidence_bundle.py`: the A->B->A limit is at :140-141 (R05), and `run_check` captures its output explicitly (:68), so R01 does not affect it.
  - `tools/change_impact.py` scans only `*.py` (:47; D21/R06).
  - `tools/mutation_drill.py` takes `--spec` only, with the exit map at :205.

## Incumbent

Copied verbatim from `01-incumbent-suites-table.md` and from the sections of `01-INCUMBENT.md`. The raw rows are in `01-incumbent-suites.jsonl` (written by `python tools/gsdx_reality_baseline.py suites ...`, every `suites` call exit 0 except the mutation-suite attempt) and the per-run output is in `incumbent-logs/`.

| suite | runs | cold s | min s | max s | exit codes | summary | baseline | command |
|---|---|---|---|---|---|---|---|---|
| test_gsd_x_goal_gate_provider.py | 3 | 5.092 | 5.092 | 5.841 | 0 | GSDX_GATE_PROVIDER_PASS=18/18 | = 18/18 | python tools/test_gsd_x_goal_gate_provider.py |
| test_gsd_x_goal.py | 3 | 4.095 | 3.951 | 4.095 | 0 | GSDX_GOAL_PASS=26/26 | - | python tools/test_gsd_x_goal.py |
| test_gsd_x_goal_bind_mission.py | 3 | 12.797 | 9.551 | 12.797 | 0 | GSDX_BIND_MISSION_PASS=10/10 | - | python tools/test_gsd_x_goal_bind_mission.py |
| test_gsd_x_goal_chaos.py | 3 | 13.845 | 13.845 | 14.699 | 0 | GSDX_GOAL_CHAOS_PASS=15/15 | = 15/15 | python tools/test_gsd_x_goal_chaos.py |
| test_gsd_x_goal_claude_providers.py | 3 | 9.221 | 9.053 | 9.221 | 0 | GSDX_CLAUDE_PROVIDERS_PASS=20/20 | - | python tools/test_gsd_x_goal_claude_providers.py |
| test_gsd_x_goal_cli.py | 3 | 53.433 | 53.433 | 55.929 | 0 | GSDX_GOAL_CLI_PASS=25/25 | - | python tools/test_gsd_x_goal_cli.py |
| test_gsd_x_goal_codex_provider.py | 3 | 4.201 | 3.929 | 4.221 | 0 | GSDX_CODEX_PROVIDER_PASS=18/18 | - | python tools/test_gsd_x_goal_codex_provider.py |
| test_gsd_x_goal_convergence.py | 3 | 2.984 | 2.901 | 2.984 | 0 | GSDX_GOAL_CONV_PASS=29/29 | = 29/29 | python tools/test_gsd_x_goal_convergence.py |
| test_gsd_x_goal_engine_identity.py | 3 | 5.722 | 5.715 | 6.476 | 0 | GSDX_ENGINE_ID_PASS=14/14 | - | python tools/test_gsd_x_goal_engine_identity.py |
| test_gsd_x_goal_epoch.py | 3 | 0.397 | 0.397 | 0.426 | 0 | GSDX_GOAL_EPOCH_PASS=19/19 | = 19/19 | python tools/test_gsd_x_goal_epoch.py |
| test_gsd_x_goal_gate_class.py | 3 | 6.408 | 4.212 | 6.408 | 0 | GSDX_GATE_CLASS_PASS=11/11 | - | python tools/test_gsd_x_goal_gate_class.py |
| test_gsd_x_goal_judge.py | 3 | 8.961 | 8.346 | 8.961 | 0 | GSDX_JUDGE_PASS=11/11 | = 11/11 | python tools/test_gsd_x_goal_judge.py |
| test_gsd_x_goal_long_run_provider.py | 3 | 0.289 | 0.214 | 0.289 | 0 | GSDX_LONGRUN_PROVIDER_PASS=16/16 | - | python tools/test_gsd_x_goal_long_run_provider.py |
| test_gsd_x_goal_mutation_safety.py | 3 | 1.454 | 1.348 | 1.454 | 0 | GSDX_GOAL_MUTATION_SAFETY_PASS=8/8 | = 8/8 | python tools/test_gsd_x_goal_mutation_safety.py |
| test_gsd_x_goal_reconcile.py | 3 | 1.301 | 1.289 | 1.347 | 0 | GSDX_RECONCILE_PASS=22/22 | = 22/22 | python tools/test_gsd_x_goal_reconcile.py |
| test_gsd_x_goal_sweep.py | 3 | 14.569 | 14.077 | 14.569 | 0 | GSDX_GOAL_SWEEP_PASS=14/14 | = 14/14 | python tools/test_gsd_x_goal_sweep.py |
| test_gsd_x_goal_sweep_all.py | 3 | 9.327 | 9.327 | 10.567 | 0 | GSDX_SWEEP_ALL_PASS=11/11 | - | python tools/test_gsd_x_goal_sweep_all.py |
| test_gsd_x_goal_mutation.py | UNKNOWN (in-copy run 2 (git-clean copy, c75dc3cc) was stopped by the Claude Code background memory-pressure reaper while the host was low on RAM; no row, empty log incumbent-logs/test_gsd_x_goal_mutation-2.log; not restarted by policy (needs CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP=1 at launch or free RAM); run 1 measured only the instrument refusal rc=2) | - | - | - | - | - | - | - |
| test_gsd_x_goal_mutation.py | 1 | 0.282 | 0.282 | 0.282 | 2 | none | - | python tools/test_gsd_x_goal_mutation.py [in copy] |

### Incumbent full goal-suite wall

Over the 17 measured suites, excluding the mutation suite. The numbers come from the rows (`free_ram_mb` per row ranged 3430-3771 MB).

- sum cold = 4.095 + 12.797 + 13.845 + 9.221 + 53.433 + 4.201 + 2.984 + 5.722 + 0.397 + 6.408 + 5.092 + 8.961 + 0.289 + 1.454 + 1.301 + 14.569 + 9.327 = **154.096 s**
- sum min  = 3.951 + 9.551 + 13.845 + 9.053 + 53.433 + 3.929 + 2.901 + 5.715 + 0.397 + 4.212 + 5.092 + 8.346 + 0.214 + 1.348 + 1.289 + 14.077 + 9.327 = **146.680 s**

Both are a **lower bound -- 1 suite(s) UNKNOWN** (`test_gsd_x_goal_mutation.py`) for the whole goal-suite family. `test_gsd_x_goal_cli.py` alone is 53.4 s, about 36 % of the min sum.

### Timelines

- **Guard:** the live store was fingerprinted before and after all three runs (`01-guard-timeline.json` / `.log`): `SAME: files 253 -> 253`, `EXIT=0`. The only change was `sweep_heartbeat.json`, which is excluded by name.
- **How the tables were made:** they were rendered from the committed JSONs (`01-timeline-{g002,g001,fixture}.json`, with stdout and `EXIT=` in the matching `.log`). Times are seconds relative to `goal.declared`.
- **What the recorded goals include:** g-002 and g-001 are real goals recorded on this host by an older engine. Their declare-to-judged spans include operator and scheduler idle time, so they are timelines, not compute. g-001's 871323.695 s (about 10 days) is mostly idle time between epochs.
- **g-001 receipts:** three of its gate epochs carry no `cost.seconds` (a receipt shape that predates the field), so they read UNKNOWN.
- **The fixture:** a fresh goal driven through the real CLI by the current engine, hermetic, with a 0.2 s pass interval set by the instrument.
#### g-002-router-surface -- recorded 2026-09-22, older engine

| metric | value | command | exit code |
|---|---|---|---|
| declare -> first dispatch (s) | 60.592 | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 4a226561... --goal g-002-router-surface` | 0 |
| epoch ep-e141e8dbd990 (gate) dispatch -> ended (s) / receipt cost.seconds | 4.84 / 4.7 | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 4a226561... --goal g-002-router-surface` | 0 |
| epoch ep-8b07e4810c67 (gate) dispatch -> ended (s) / receipt cost.seconds | 4.683 / 4.6 | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 4a226561... --goal g-002-router-surface` | 0 |
| epoch ep-cc6d54668881 (gate) dispatch -> ended (s) / receipt cost.seconds | 5.881 / 5.8 | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 4a226561... --goal g-002-router-surface` | 0 |
| epoch ep-68a14c7b78b3 (gate) dispatch -> ended (s) / receipt cost.seconds | 4.821 / 4.7 | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 4a226561... --goal g-002-router-surface` | 0 |
| epoch ep-bc5b4eef1a63 (gate) dispatch -> ended (s) / receipt cost.seconds | 4.944 / 4.8 | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 4a226561... --goal g-002-router-surface` | 0 |
| epoch ep-9abb04b6c1a5 (gate) dispatch -> ended (s) / receipt cost.seconds | 4.934 / 4.8 | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 4a226561... --goal g-002-router-surface` | 0 |
| declare -> last judged (s) | 155.755 | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 4a226561... --goal g-002-router-surface` | 0 |
| judged gates / verdict | 6 / PASS | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 4a226561... --goal g-002-router-surface` | 0 |
| judge replay (s, sum of per-gate seconds, 0.1 s source precision) | 2.9 | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 4a226561... --goal g-002-router-surface` | 0 |

#### g-001-smoke-runner -- recorded, older engine

| metric | value | command | exit code |
|---|---|---|---|
| declare -> first dispatch (s) | 106.42 | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 1f924bca... --goal g-001-smoke-runner` | 0 |
| epoch ep-9e40a91d49dc (codex) dispatch -> ended (s) / receipt cost.seconds | 21.167 / 20.7 | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 1f924bca... --goal g-001-smoke-runner` | 0 |
| epoch ep-a72779d9d196 (claude-interactive) dispatch -> ended (s) / receipt cost.seconds | 130.238 / 130.1 | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 1f924bca... --goal g-001-smoke-runner` | 0 |
| epoch ep-fa58f6044552 (gate) dispatch -> ended (s) / receipt cost.seconds | 6.964 / UNKNOWN | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 1f924bca... --goal g-001-smoke-runner` | 0 |
| epoch ep-0a6d8cd273a0 (gate) dispatch -> ended (s) / receipt cost.seconds | 7.061 / UNKNOWN | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 1f924bca... --goal g-001-smoke-runner` | 0 |
| epoch ep-5ad65671a665 (gate) dispatch -> ended (s) / receipt cost.seconds | 7.096 / UNKNOWN | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 1f924bca... --goal g-001-smoke-runner` | 0 |
| epoch ep-9e778f3ad9aa (gate) dispatch -> ended (s) / receipt cost.seconds | 7.163 / 7.1 | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 1f924bca... --goal g-001-smoke-runner` | 0 |
| epoch ep-8411c78ee50d (gate) dispatch -> ended (s) / receipt cost.seconds | 7.083 / 7.0 | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 1f924bca... --goal g-001-smoke-runner` | 0 |
| epoch ep-3cad47f4d4e7 (gate) dispatch -> ended (s) / receipt cost.seconds | 7.662 / 7.5 | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 1f924bca... --goal g-001-smoke-runner` | 0 |
| epoch ep-ff1f9b5fff47 (gate) dispatch -> ended (s) / receipt cost.seconds | 1.999 / 1.8 | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 1f924bca... --goal g-001-smoke-runner` | 0 |
| epoch ep-d6eb00480dc1 (gate) dispatch -> ended (s) / receipt cost.seconds | 2.181 / 2.0 | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 1f924bca... --goal g-001-smoke-runner` | 0 |
| epoch ep-002809fe2a28 (gate) dispatch -> ended (s) / receipt cost.seconds | 1.742 / 1.6 | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 1f924bca... --goal g-001-smoke-runner` | 0 |
| epoch ep-0365595b5480 (gate) dispatch -> ended (s) / receipt cost.seconds | 41.331 / 41.1 | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 1f924bca... --goal g-001-smoke-runner` | 0 |
| epoch ep-1bd4e103cecc (gate) dispatch -> ended (s) / receipt cost.seconds | 14.546 / 14.3 | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 1f924bca... --goal g-001-smoke-runner` | 0 |
| epoch ep-e68c00f7fa53 (gate) dispatch -> ended (s) / receipt cost.seconds | 16.291 / 16.1 | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 1f924bca... --goal g-001-smoke-runner` | 0 |
| epoch ep-0954eedea9fe (gate) dispatch -> ended (s) / receipt cost.seconds | 73.986 / 73.8 | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 1f924bca... --goal g-001-smoke-runner` | 0 |
| epoch ep-37d87d5a72cf (gate) dispatch -> ended (s) / receipt cost.seconds | 300.205 / 300.0 | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 1f924bca... --goal g-001-smoke-runner` | 0 |
| epoch ep-ae4d94763a40 (gate) dispatch -> ended (s) / receipt cost.seconds | 300.47 / 300.3 | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 1f924bca... --goal g-001-smoke-runner` | 0 |
| epoch ep-9284ed933f2d (gate) dispatch -> ended (s) / receipt cost.seconds | 1203.929 / 1203.7 | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 1f924bca... --goal g-001-smoke-runner` | 0 |
| epoch ep-f89214c2f7e0 (gate) dispatch -> ended (s) / receipt cost.seconds | 300.466 / 300.3 | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 1f924bca... --goal g-001-smoke-runner` | 0 |
| epoch ep-07456db4e2e3 (gate) dispatch -> ended (s) / receipt cost.seconds | 298.223 / 298.0 | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 1f924bca... --goal g-001-smoke-runner` | 0 |
| declare -> last judged (s) | 871323.695 | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 1f924bca... --goal g-001-smoke-runner` | 0 |
| judged gates / verdict | 6 / PASS | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 1f924bca... --goal g-001-smoke-runner` | 0 |
| judge replay (s, sum of per-gate seconds, 0.1 s source precision) | 32.3 | `python tools/gsdx_goal_timeline.py recorded --store ~/.claude/state/gsd-x/goals --repo 1f924bca... --goal g-001-smoke-runner` | 0 |

#### fixture g-w0-fixture -- current engine 8b83216c, hermetic, this host

| metric | value | command | exit code |
|---|---|---|---|
| declare -> first dispatch (s) | 9.244 | `python tools/gsdx_goal_timeline.py fixture` | 0 |
| epoch ep-b55b7c8f6a50 (gate) dispatch -> ended (s) / receipt cost.seconds | 4.379 / 4.3 | `python tools/gsdx_goal_timeline.py fixture` | 0 |
| epoch ep-ed943394cdf9 (gate) dispatch -> ended (s) / receipt cost.seconds | 4.168 / 4.1 | `python tools/gsdx_goal_timeline.py fixture` | 0 |
| epoch ep-dedbd99f4400 (gate) dispatch -> ended (s) / receipt cost.seconds | 4.116 / 4.0 | `python tools/gsdx_goal_timeline.py fixture` | 0 |
| epoch ep-51106e7cea28 (gate) dispatch -> ended (s) / receipt cost.seconds | 4.996 / 4.9 | `python tools/gsdx_goal_timeline.py fixture` | 0 |
| declare -> last judged (s) | 39.676 | `python tools/gsdx_goal_timeline.py fixture` | 0 |
| judged gates / verdict | 4 / PASS | `python tools/gsdx_goal_timeline.py fixture` | 0 |
| judge replay (s, sum of per-gate seconds, 0.1 s source precision) | 0.4 | `python tools/gsdx_goal_timeline.py fixture` | 0 |
| reconcile/status passes to CLOSURE CLEAR | 8 | `python tools/gsdx_goal_timeline.py fixture` | 0 |
| pass interval (s; instrument parameter, not an incumbent property) | 0.2 | `python tools/gsdx_goal_timeline.py fixture` | 0 |
| judge CLI wall (s) | 1.558 | `python tools/gsdx_goal_timeline.py fixture` | 0 |
| receipt `observed` (all epochs; R01 at the CLI plane) | ['2 passed'] | `python tools/gsdx_goal_timeline.py fixture` | 0 |
| converged | True | `python tools/gsdx_goal_timeline.py fixture` | 0 |

### UNKNOWN

- **The scheduler's real cadence between sweep passes on this host.** The fixture drives passes back to back at an instrument-chosen 0.2 s interval. The recorded goals' gaps mix scheduler cadence with operator idle time and cannot separate the two.
- **Judge replay of g-002 / g-001 at the current engine.** Their repositories' trees are not available in this worktree. The 2.9 s and 32.3 s are the older engine's recorded per-gate seconds.
- **POSIX / GEX44 timings.** They were not run in this phase. Every number here is Windows, this laptop, with 3.4-3.8 GB of RAM free.
- **`test_gsd_x_goal_mutation.py` wall time and CAUGHT count.** See Suite findings: the instrument gap was fixed, then the run was stopped by the memory-pressure reaper and not restarted unattended.
- **`cost.seconds` for three g-001 gate epochs.** Their receipts predate the field.

## Liveness

- **This worktree at the start of the phase:** 57 gate offenders (`01-liveness-before.md`, `python modules/liveness/reachability.py`, `EXIT=1`).
- **The main checkout:** 61, orchestrator-observed on 2026-10-07 during plan-phase, read-only. The 57 are a strict subset of the 61. This phase did not probe the main checkout.
- **Freeze:** `96bdb8b1` (`reachability.py --baseline`, 65 modules of standing debt). It was re-applied as an order-preserving rewrite of `known_orphans` only; see 01-04-SUMMARY.
- **After the freeze:** `gate offenders: 0`, `EXIT=0` (`01-liveness-after.md`).
- **Phase end, fresh:** `gate offenders: 0`, `EXIT=0` (`01-phase-end-liveness.md`).
- **Incident class:** lens CLASE 2. The roadmap constraint assumed a green gate at the base, and it was red. The guard is the named-set ratchet, so new orphans now fail the gate. Tracked as DENOMINATOR R10 (Phase 10).

The frozen offenders (verbatim from `01-liveness-before.md`; the 8 rows also present in the old `known_orphans` are included, since that file lists all unreachable-and-undeclared modules):

| module | status | via |
|---|---|---|
| arch-decision/test_closed_loop | ORPHAN | - |
| arch-decision/test_v_block | ORPHAN | - |
| capability_runtime/agent_bundle | ORPHAN | - |
| ccf/test_ccf | ORPHAN | - |
| deployment/test_v_block | ORPHAN | - |
| gsd_x/goal/__init__ | ORPHAN | - |
| gsd_x/goal/bind_mission | ORPHAN | - |
| gsd_x/goal/brief | ORPHAN | - |
| gsd_x/goal/contract | ORPHAN | - |
| gsd_x/goal/convergence | ORPHAN | - |
| gsd_x/goal/engine_identity | ORPHAN | - |
| gsd_x/goal/epoch | ORPHAN | - |
| gsd_x/goal/git_state | ORPHAN | - |
| gsd_x/goal/judge | ORPHAN | - |
| gsd_x/goal/log | ORPHAN | - |
| gsd_x/goal/providers/__init__ | ORPHAN | - |
| gsd_x/goal/providers/claude | ORPHAN | - |
| gsd_x/goal/providers/codex | ORPHAN | - |
| gsd_x/goal/providers/gate | ORPHAN | - |
| gsd_x/goal/providers/long_run | ORPHAN | - |
| gsd_x/goal/reconcile | ORPHAN | - |
| gsd_x/goal/sweep | ORPHAN | - |
| gsd_x/mission/__init__ | ORPHAN | - |
| gsd_x/mission/closure | ORPHAN | - |
| gsd_x/mission/contract | ORPHAN | - |
| gsd_x/mission/coverage | ORPHAN | - |
| gsd_x/mission/obligation | ORPHAN | - |
| gsd_x/mission/store | ORPHAN | - |
| gsd_x/mission/structured_facts | ORPHAN | - |
| keos_qwen/__init__ | ORPHAN | - |
| keos_qwen/goals/__init__ | ORPHAN | - |
| keos_qwen/goals/fire | ORPHAN | - |
| keos_qwen/goals/seed_goals | ORPHAN | - |
| keos_qwen/ledger/__init__ | ORPHAN | - |
| keos_qwen/ledger/ledger | ORPHAN | - |
| keos_qwen/outcome | ORPHAN | - |
| keos_qwen/probe/__init__ | ORPHAN | - |
| keos_qwen/probe/agentic_loop | ORPHAN | - |
| keos_qwen/score/score_corpus | ORPHAN | - |
| knowledge_acquisition/__init__ | ORPHAN | - |
| knowledge_acquisition/boundary | ORPHAN | - |
| knowledge_acquisition/classifier | ORPHAN | - |
| knowledge_acquisition/cli | ORPHAN | - |
| knowledge_acquisition/corpus_parser | ORPHAN | - |
| knowledge_acquisition/engine3 | ORPHAN | - |
| knowledge_acquisition/eva_adapter | ORPHAN | - |
| knowledge_acquisition/expectation | ORPHAN | - |
| knowledge_acquisition/models | ORPHAN | - |
| knowledge_acquisition/provenance | ORPHAN | - |
| knowledge_acquisition/queues | ORPHAN | - |
| knowledge_acquisition/raw_vault | ORPHAN | - |
| knowledge_acquisition/routing | ORPHAN | - |
| knowledge_acquisition/runlock | ORPHAN | - |
| knowledge_acquisition/runner | ORPHAN | - |
| knowledge_acquisition/session | ORPHAN | - |
| knowledge_acquisition/store | ORPHAN | - |
| session_resilience/integration | ORPHAN | - |
| session_resilience/multi_window | ORPHAN | - |
| session_resilience/resume_identity | ORPHAN | - |
| session_resilience/ui_state | ORPHAN | - |
| surface_architecture/verticals/design_md_adapter | ORPHAN | - |
| surface_architecture/verticals/prd_adapter | ORPHAN | - |
| surface_architecture/verticals/surface_phrases | ORPHAN | - |
| tower/donegate | ORPHAN | - |
| tower/ratchet | ORPHAN | - |

## Hermeticity

| when | instrument | result |
|---|---|---|
| 01-01 Task 1 (R01 suites) | PowerShell count + max LastWriteTimeUtc of `~/.claude/state/gsd-x` | 254 -> 254 files. Max ticks moved 639269757593441469 -> 639269760517912049, and only `sweep_heartbeat.json` was newer, written by scheduled task PP-GoalSweep (13:20:48Z). Attributed to the scheduler, not the suites. This led to the named heartbeat exclusion in 01-02. |
| 01-02 smoke runs (convergence suite) | `gsdx_reality_baseline.py suites` guard | SAME (two runs) |
| 01-03 g-002 cross-check | `fingerprint --out / --against` | SAME 253 -> 253 |
| 01-05 `suites` calls that completed (17 suites + mutation attempt 1) | guard rows in `01-incumbent-suites.jsonl` | 18 guard rows, all SAME, 0 `"verdict": "CHANGED"` (`Select-String` count). `sweep_heartbeat.json` was excluded-changed during the cli call. Mutation attempt 2 was killed by the memory-pressure reaper before it reached its guard step, so it wrote **no guard row** (corrected 2026-10-07 after the verifier flagged the earlier "every call" wording as an overclaim). It is covered only by the later timeline fingerprint and the empty `git status` below. |
| 01-05 timelines | `fingerprint --out 01-guard-timeline.json` / `--against` | `SAME: files 253 -> 253`, `EXIT=0` (`01-guard-timeline.log`), with the heartbeat excluded-changed |
| 01-05 mutation attempts | `git status --porcelain -- modules tools` | empty. No orphan process was left after the reaper stopped run 2. |

No hermeticity incident was attributable to a measured suite. The file count differs between 01-01 (254) and later (253) because the later instrument excludes `sweep_heartbeat.json` by name.

## Production Reality verdicts

| claim | plane | verdict | evidence |
|---|---|---|---|
| R01 fixed: gate output reaches the log and `observed` | Windows, this host | PROVEN | RED 17/18 -> GREEN 18/18; revert drill KILLED after a passing control; phase-end 18/18 EXIT=0; fixture receipts `observed` = `2 passed` through the real CLI |
| R01 fixed on POSIX / GEX44 | POSIX | UNJUDGED | not run this phase |
| Premise record | repo | PROVEN | real set EXIT=0, with a control that failed (EXIT=1) |
| Liveness gate green | repo | OBSERVED | EXIT=0 after freezing the inherited debt by name. The debt is frozen, not cleared (R10) |
| Incumbent suite wall times (17 suites) | Windows, shared noisy host | OBSERVED | 51 runs, rc 0, guard SAME, free RAM recorded per row |
| Incumbent mutation-suite timing | Windows | UNJUDGED | run 1 hit the instrument's missing-git gap (rc=2, fixed in c75dc3cc); run 2 was stopped by the memory-pressure reaper and not restarted unattended |
| g-002 / g-001 timelines and judge replay (2.9 s / 32.3 s) | recorded on this host, older engine | OBSERVED | read through a hash-verified copy; guard SAME |
| Fixture timeline at the current engine (CONVERGED, 8 passes, replay 0.4 s) | Windows, hermetic | OBSERVED | `01-timeline-fixture.json`, EXIT=0 |

## Denominator rows moved

- **R01:** set by Task 2 of 01-06 (see DENOMINATOR.md), with this file as its evidence.
- **R10:** appended OPEN by `f83c2a61` (gsd_x/goal liveness debt, to Phase 10).

## UKDL entries written

- `T-SUBPROCESS-WITHOUT-INHERITED-STD-HANDLES-LOSES-GRANDCHILD-OUTPUT-ON-WINDOWS-001`: commit `0c93c0e9`.

## Owner steps

None -- no live hook, settings or global file was changed.

Optional, to close the one UNJUDGED incumbent row: relaunch Claude Code with `CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP=1`, or free RAM. Then run the mutation-suite command recorded in 01-05-SUMMARY.md.

Added 2026-10-07 (worker epoch 3):

- **Owner decision, 20:05:** the mutation-suite timing stays UNKNOWN in Phase 1. It is carried as DENOMINATOR R11, an ENTRY OBLIGATION of Phase 6: measure the incumbent in an isolated copy before any speedup claim.
- **OWNER STEP:** change the `human_needed` routing of the global `gsd-autonomous` skill (`~/.claude/gsd-core/workflows/autonomous.md`), so an UNATTENDED run executes the human_verification commands itself or records OWNER DECISION NEEDED and continues. The mission must not edit `~/.claude`, so it is not done here. Source: the incident below.

## Incident: unattended worker ended its turn on a human_needed question

| field | value |
|---|---|
| what | Phase 1 verification returned `status: human_needed` (commit 7efe5322, 2026-10-07 16:24 +0200). Worker epoch 2 ended its turn on a question to the Owner, although the mission card says UNATTENDED, never ask. |
| cost | The mission parked BLOCKED until the Owner answered at 20:05, about 3h41m. The next commit is baf27b86 (20:12). |
| root cause | The `gsd-autonomous` workflow routes `human_needed` to a stop and ask. The worker followed the workflow over the mission card's DECISION GATE. Four of the five items were commands the worker could run (the re-runs at baf27b86 are `01-verify-vrb.log` 17/17, `01-verify-vtl.log` 8/8, `01-verify-gate-provider.log` 18/18 and `01-verify-git.log`, all EXIT=0). The fifth item was a decision, not a resource block, so the gate already had the answer: record it and continue. |
| class | CLASE 5 (process/orchestration): a workflow default overrode a stronger mission constraint. |
| rule | When verification returns human_needed in an unattended run, run the checks yourself or record the decision per the DECISION GATE, then continue. Never end a turn on a question. |
| guard | Mission STATE.md Decisions (this workstream); UKDL candidate T-UNATTENDED-HUMAN-NEEDED-ENDS-TURN-ON-QUESTION-PARKS-MISSION-001. The mechanical fix is the OWNER STEP above. |
| verdict | OBSERVED (git timestamps; the Owner's own report of the BLOCKED park). |

