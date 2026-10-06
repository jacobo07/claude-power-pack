---
phase: 01
plane: gex44
head: f28235584ce0e346f6c5347452a11cb7ccd3f007
measured_at: 2026-10-06T20:22:06Z
---

# Phase 1 baseline (untouched tree, GEX44)

Every command was run in a fresh foreground process from the worktree root, `timeout 300`, before any source edit.
Exit code and the last non-empty output line are verbatim. A crash records the exception class and message.

## Consumer regression set (untouched tree)

| command | exit | last line |
|---|---|---|
| `python3 tools/test_usage_index.py` | 0 | `USAGE_INDEX_PASS=22/22  threshold=22/22` |
| `python3 tools/test_usage_index_identity.py` | 1 | `FileNotFoundError: [Errno 2] No such file or directory: 'cmd'` (crash: `junction()` shells out to `cmd /c mklink /J`, absent on Linux) |
| `python3 tools/test_estate_shadow.py` | 1 | `ESTATE_SHADOW_PASS=10/11  threshold=11/11` (red gate: `V-SHADOW-NESTED-PROJECT: {'tuA': ('', False), 'tuB': ('', False)}`) |
| `python3 tools/test_fanout_ledger.py` | 0 | `FANOUT_LEDGER_PASS=17/17  threshold=17/17` |
| `python3 tools/test_root_progress.py` | 0 | `ROOT_PROGRESS_PASS=11/11  threshold=11/11` |
| `python3 tools/test_spawn_outcomes.py` | 0 | `SPAWN_OUTCOMES_PASS=24/24  threshold=24/24` |
| `python3 tools/test_spawn_policy_v2.py` | 0 | `SPAWN_POLICY_V2_PASS=26/26  threshold=26/26` |
| `python3 tools/test_async_spawns.py` | 0 | `ASYNC_SPAWNS_PASS=12/12  threshold=12/12` |
| `python3 tools/test_goal_journey.py` | 0 | `GOAL_JOURNEY_PASS=7/7  threshold=7/7` |
| `python3 tools/test_execution_shape.py` | 0 | `EXECUTION_SHAPE_PASS=14/14  threshold=14/14` |
| `python3 tools/test_displacement.py` | 0 | `DISPLACEMENT_PASS=16/16  threshold=16/16` |
| `python3 tools/test_store_identity_consumers.py` | 1 | `FileNotFoundError: [Errno 2] No such file or directory: 'cmd'` (crash: same `junction()` helper) |
| `python3 tools/test_frontier_intelligence_os.py` | 1 | `DATASET_FAMILY_VERDICT=FAIL` (preceded by `FIOS_ACTIVATION_PASS=48/49  threshold=49/49`; red gate: `V-FIOS-LIVE-PATH-WIRED: missing: ['kclaude -> compiler --preflight']`) |
| `python3 tools/test_token_ground_truth_junction.py` | 1 | `FileNotFoundError: [Errno 2] No such file or directory: 'cmd'` (crash: same `mklink /J` shell-out) |
| `python3 tools/test_kme_pillars.py` | 0 | `KMEP_PASS=89/89  threshold=89/89  skipped=0  inconclusive=0` |
| `python3 tools/test_gsd_x_goal_engine_identity.py` | 0 | `GSDX_ENGINE_ID_PASS=14/14  threshold=14/14` |

Reading of the table: four suites are red or crashed on the untouched tree for reasons that predate this phase and are
not caused by usage_index (identity, store-identity-consumers and token-ground-truth-junction cannot create a junction on
Linux; estate_shadow and frontier_intelligence_os each carry one red gate). Their exit codes here are the baseline;
a later plan must show them unchanged or better, never "green" by omission.

## Not runnable on this plane

`vault/programs/cognitive-economy/gates/gate_baseline.py` reads the default index
`~/.claude/state/usage_index/index.sqlite`, which does not exist on GEX44. Its regression status is UNMEASURED here and
becomes a laptop owner-bundle line in plan 06.

## Identity suite after the Linux fallback

`junction()` in `tools/test_usage_index_identity.py` keeps `cmd /c mklink /J` under `os.name == "nt"` and creates a
directory symlink with `os.symlink(..., target_is_directory=True)` elsewhere (INCONCLUSIVE exit 2 if that fails); the
two seeded-alias separators use `os.sep`.

`python3 tools/test_usage_index_identity.py` -> exit 0, last line `USAGE_INDEX_IDENTITY_PASS=11/11  threshold=11/11`.
No V-UXID gate is red.

## Store-identity consumers suite after the Linux fallback (Rule 3 deviation)

`tools/test_store_identity_consumers.py` carried the identical `mklink /J` shell-out and crashed on Linux, which would
have made the plan's own Task 2 gate (`PASS V-SIC-UX-ONE-PRODUCER`) unrunnable. The same `junction()` fallback was
applied (committed separately from the two-file Task 1 commit). Post-fix: exit 0, last line
`STORE_IDENTITY_CONSUMERS_PASS=12/12  threshold=12/12`, `PASS V-SIC-UX-ONE-PRODUCER` present. This is the comparison
line for plan 01 Task 2. `tools/test_token_ground_truth_junction.py` keeps its crash (no gate of this phase needs it).

## Consumer regression set (after the change)

Run at HEAD 77e911796da94d2c90a6469a6df3acb8be196082 (plan 01-05, after plans 01-01..01-04 and the two evidence commits),
plane gex44, 2026-10-06, each command a fresh foreground process from the worktree root with `timeout 300`
(`/home/kobii/ao-scratch/p1/regress.py`; exit code and last non-empty stdout line verbatim). `vs baseline` compares with the
untouched-tree table above and the "after the Linux fallback" sections: `better` = the exit code improved (identity and
store-identity-consumers were crashes on the untouched tree and are green after the Linux `junction()` fallback of plan 01-01),
`same` = same exit code and same last line, the red gates identical (re-checked by name: `V-SHADOW-NESTED-PROJECT`,
`V-FIOS-LIVE-PATH-WIRED`). The last four rows have no untouched-tree counterpart (a gate or command that did not exist, or was
not run, before this phase): a green exit is judged `better` than a missing baseline; the reachability row exits 1 for modules
unrelated to this phase and is judged `same` only in that sense (see the note under the table).

| command | exit | last line | vs baseline |
|---|---|---|---|
| `python3 tools/test_usage_index.py` | 0 | `USAGE_INDEX_PASS=22/22  threshold=22/22` | same |
| `python3 tools/test_usage_index_identity.py` | 0 | `USAGE_INDEX_IDENTITY_PASS=11/11  threshold=11/11` | better |
| `python3 tools/test_estate_shadow.py` | 1 | `ESTATE_SHADOW_PASS=10/11  threshold=11/11` | same |
| `python3 tools/test_fanout_ledger.py` | 0 | `FANOUT_LEDGER_PASS=17/17  threshold=17/17` | same |
| `python3 tools/test_root_progress.py` | 0 | `ROOT_PROGRESS_PASS=11/11  threshold=11/11` | same |
| `python3 tools/test_spawn_outcomes.py` | 0 | `SPAWN_OUTCOMES_PASS=24/24  threshold=24/24` | same |
| `python3 tools/test_spawn_policy_v2.py` | 0 | `SPAWN_POLICY_V2_PASS=26/26  threshold=26/26` | same |
| `python3 tools/test_async_spawns.py` | 0 | `ASYNC_SPAWNS_PASS=12/12  threshold=12/12` | same |
| `python3 tools/test_goal_journey.py` | 0 | `GOAL_JOURNEY_PASS=7/7  threshold=7/7` | same |
| `python3 tools/test_execution_shape.py` | 0 | `EXECUTION_SHAPE_PASS=14/14  threshold=14/14` | same |
| `python3 tools/test_displacement.py` | 0 | `DISPLACEMENT_PASS=16/16  threshold=16/16` | same |
| `python3 tools/test_store_identity_consumers.py` | 0 | `STORE_IDENTITY_CONSUMERS_PASS=12/12  threshold=12/12` | better |
| `python3 tools/test_frontier_intelligence_os.py` | 1 | `DATASET_FAMILY_VERDICT=FAIL` | same |
| `python3 tools/test_token_ground_truth_junction.py` | 1 | `FileNotFoundError: [Errno 2] No such file or directory: 'cmd'` | same |
| `python3 tools/test_kme_pillars.py` | 0 | `KMEP_PASS=89/89  threshold=89/89  skipped=0  inconclusive=0` | same |
| `python3 tools/test_gsd_x_goal_engine_identity.py` | 0 | `GSDX_ENGINE_ID_PASS=14/14  threshold=14/14` | same |
| `python3 tools/test_usage_index_v5.py` | 0 | `USAGE_INDEX_V5_PASS=71/71  threshold=71/71` | better |
| `python3 tools/test_usage_index_v5.py --drill` | 0 | `DRILL killed=18/18` | better |
| `python3 tools/test_incremental_cognition_program.py --generation 2 --selftest` | 0 | `ICP_GEN2_SELFTEST=PASS` | better |
| `python3 modules/liveness/reachability.py` | 1 | `\| tower/ratchet \| ORPHAN \| - \|` | same |

Note on the reachability row: `modules: 490 | REACHABLE: 310 | ORPHAN: 180 | UNKNOWN: 0 | gate offenders: 59` (header line verbatim,
`python3 modules/liveness/reachability.py` saved to `/home/kobii/ao-scratch/p1/reach.txt`). Neither `usage_index` nor `tis_observed`
appears in its output, so the exit 1 is **inherited** from unrelated modules (`gsd_x/goal/*`, `arch-decision/test_*`,
`cognitive_os/hibernate_runner`, `tower/ratchet`, ...). Its stated aperture is `modules/` only: `tools/` is not scanned, so the
absence of `tools/usage_index.py` from that list is absence from the denominator, not evidence of reachability. No baseline
line exists for it (not in the 16-command set), so `same` means "not attributable to this phase", not "unchanged from a measurement".
`gate_baseline.py` stays UNMEASURED on this plane (no default index), as recorded above.
