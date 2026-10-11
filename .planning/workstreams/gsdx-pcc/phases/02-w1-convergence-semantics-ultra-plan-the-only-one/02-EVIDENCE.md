# Phase 2 evidence -- W1 convergence semantics

- Branch `gsdx/pcc` (worktree `C:\Users\User\Apps\pp-gsdx-pcc`), PLAN_BASE `854dee0d`, HEAD at the phase-end gates `425db6d3`, date 2026-10-11. Nothing pushed.
- Phase commits (`02-phase-end-git.log`, section c, `git log --oneline 854dee0d..HEAD` at the time of the run):

```
c8c58d91 test(gsdx-pcc-02): mutation drills of the PCC seam -- every mutant class with a control
a051673e test(gsdx-pcc-02): close drill blind spot d01-disposition-write, d01-fingerprint-dotdot
f234ad16 docs(gsdx-pcc-02): 02-05 summary; DENOMINATOR D44 done
a353fb7b test(gsdx-pcc-02): D44 invariants -- no second store, pure projections, declared additive vocabulary, spec resolved
66f71a1d feat(gsdx-pcc-02): Proof Conservation ledger, Concurrency-by-Proof definition, Unknown Escalates (D03)
dfc87abc feat(gsdx-pcc-02): Work and Semantic Conservation laws measured on the recorded corpus (D03)
340c792d docs(gsdx-pcc-02): 02-04 summary
e85345a0 feat(gsdx-pcc-02): typed proof contract and freshness classes as a second axis (D10)
ecdc8d1b feat(gsdx-pcc-02): certificate validity, causal fingerprint and the exhaustive proof-state table (D01)
ec1c1b82 feat(gsdx-pcc-02): proof states -- legacy mapping equals _needs_a_gate_here on the recorded corpus (D01, D10)
63db7439 docs(gsdx-pcc-02): 02-03 summary
56e3f3f8 feat(gsdx-pcc-02): kill switches GSDX_FRONTIER / GSDX_PROOF_INHERITANCE -- call-time parser, typo means OFF
62bdec3c test(gsdx-pcc-02): PCC payloads -- malformed raises only in proof.py, newer v UNKNOWN, CAS, export/restore
735170c0 feat(gsdx-pcc-02): PCC event seam -- proof.py ledger projection and CAS writer (D44, liveness declared)
bafb0fad docs(gsdx-pcc-02): 02-02 summary
15e8e2f1 test(gsdx-pcc-02): RED -- replay suite gates for the PCC seam (proof module absent)
98609c4f test(gsdx-pcc-02): legacy replay golden captured from the unmodified engine (D43)
13a0ee2c test(gsdx-pcc-02): legacy goal fixture -- byte copy of g-002/g-001 with manifests (verified, scanned)
142eafea docs(gsdx-pcc-02): 02-01 summary
f14420a0 docs(gsdx-pcc-02): W1 audit persisted; every gap injected or dispositioned
86c3e628 docs(gsdx-pcc-02): spec Semantics S1-S16 resolved, ULTRA Q&A recorded, premises verified
a223b337 docs(gsdx-pcc-02): spec Semantics S1-S8 resolved (checkpoint)
fabe7c88 docs(gsdx-pcc-02): spec S2 proof states resolved (W1 tracer)
7a3223a1 docs(gsdx-pcc-02): plan check iteration 1 persisted; 2 warnings + 3 info fixed
```

## Results

| success criterion | verdict | evidence file | command | exit |
|---|---|---|---|---|
| SC1 amended spec audited, every gap dispositioned | PROVEN | 02-AUDIT.md, `## Audit dispositions` below; V-PCC-SPEC-RESOLVED (S1..S16 each resolved once) | `python tools/test_gsd_x_goal_pcc_semantics.py` | 0 |
| SC2 seam lands with zero behaviour change; every goal suite at its Phase 1 count | PROVEN on this host | 02-phase-end-suites-table.md (19 suites, 0 DIFFERS), 02-phase-end-git.log (a) | `tools/gsdx_reality_baseline.py suites` / `table` | 0 / 0 |
| SC3 legacy replay over recorded logs | PROVEN on the hermetic committed copy | tools/fixtures golden, `GSDX_PCC_REPLAY_PASS=28/28` | `python tools/test_gsd_x_goal_pcc_replay.py` | 0 |

## Audit dispositions

| gap | category | disposition | target | change |
|---|---|---|---|---|
| G1 | EDGE | INJECTED | CODE:02-02 | INTERLEAVED mask gains `decide.reason` as a regex substitution `at seq \d+` -> `at seq <seq>` |
| G2 | COMPLETION-GATE | INJECTED | CODE:02-02, CODE:02-06 | every gate body wrapped so a raise prints `FAIL <gate> raised <ExcType>: <msg>` and the `_PASS=` line always prints; UNJUDGED treated as a harness defect fixed once |
| G3 | EDGE | INJECTED | CODE:02-02 | synthetic repo id fixed 7-64 char lower-case hex; `syn_carry` recipe pinned |
| G4 | REALITY-CONTRACT | INJECTED | SPEC:S2, CODE:02-04 | `unknown:` -> UNKNOWN before any FRESH decision on both paths; V-PCC-STATE-PRODUCED-UNKNOWN-BINDING and V-PCC-STATE-PRODUCED-WITHOUT-SATISFIED |
| G5 | EDGE | INJECTED | CODE:02-02 | `syn_contract` budget is `{"max_epochs": n}` only |
| G6 | EDGE | INJECTED | SPEC:S2, CODE:02-04 | SATISFIED with `o.revision != state.revision` maps to UNKNOWN |

Gaps found: 6; rows: 6

## Requirements

| id | what landed | gates | stays for |
|---|---|---|---|
| D01 | proof states FRESH/INHERITED/SUPERSEDED/STALE/UNKNOWN + NOT_APPLICABLE, six-premise observation, causal fingerprint | V-PCC-STATE-TRUTH-TABLE (2916 cells), V-PCC-STATE-NO-EVENT-NOT-INHERITED, V-PCC-FINGERPRINT-* | OPEN; Phase 4 closes |
| D03 | five laws as pure checkers (semantic, proof, work, concurrency definition, unknown-escalates) | V-PCC-LAW-* | OPEN; baseline entries Phase 10 (R09) |
| D10 | typed contract + freshness classes as a second axis, legacy = 1-element contract | V-PCC-GATE-CLASSES-PINNED, V-PCC-CONTRACT-WEAKENING-IGNORED, V-PCC-FRESHNESS-SCAN-ESCALATES-ONLY | OPEN; Phase 4 closes |
| D43 | legacy replay golden captured pre-seam, replay suite | V-PCC-REPLAY-*, V-PCC-NO-LEGACY-EDIT | DONE |
| D44 | event log not a second store | V-PCC-NO-SECOND-STORE, V-PCC-PROJECTION-PURE, V-PCC-ADDITIVE-ONLY | DONE |

## Edge-probe rows

| row | probe | resolution | gate |
|---|---|---|---|
| E1 | D01 adjacency (neighbouring obligations, superseding strength) | a stronger later claim supersedes only an identical binding | V-PCC-STATE-SUPERSEDED-STRENGTH |
| E2 | D01 empty (no obligations / no premises) | empty projection, no premise means UNKNOWN | V-PCC-STATE-EMPTY |
| E3 | D01 ordering | projection order stable | V-PCC-STATE-ORDER-STABLE |
| E4 | D03 unknown | unknown never skips a gate, 2916 cells 0 violations, mutant 63 | V-PCC-LAW-UNKNOWN-ESCALATES |
| E5 | D10 weaker contract | ignored, seq reported | V-PCC-CONTRACT-WEAKENING-IGNORED |
| E6 | D43 interleaved new event types | legacy readers ignore proof.* types | V-PCC-REPLAY-INTERLEAVED |
| E7 | D44 idempotency | export/restore round trip | V-PCC-EXPORT-RESTORE-ROUNDTRIP |
| E8 | D44 concurrency | CAS append, loser refused | V-PCC-WRITER-CAS |

## Drills

Tool `tools/mutation_drill.py` (isolated copy, passing control, `copy_dirs` = `vault/specs` and the phase dir). Logs `drills/<id>-drill.log`.

| drill | gate | verdict |
|---|---|---|
| d43-ladder | V-PCC-REPLAY-IGNORE-NEW-TYPES-PCC | MUTANT KILLED |
| d10-gate-classes | V-PCC-GATE-CLASSES-PINNED | MUTANT KILLED |
| d01-unknown-as-equal | V-PCC-STATE-TRUTH-TABLE | MUTANT KILLED |
| d01-inherited-without-event | V-PCC-STATE-NO-EVENT-NOT-INHERITED | MUTANT KILLED |
| d01-disposition-write | V-PCC-STATE-NOT-IN-DISPOSITION | MUTANT KILLED (first run MUTANT SURVIVED) |
| d01-fingerprint-dotdot | V-PCC-FINGERPRINT-OUTSIDE-ROOT | MUTANT KILLED (first run MUTANT SURVIVED) |
| d01-fingerprint-raises | V-PCC-FINGERPRINT-ABSENT | MUTANT KILLED |
| d01-switch-ignored | V-PCC-SWITCH-PARSE | MUTANT KILLED |
| d10-weakening-adopted | V-PCC-CONTRACT-WEAKENING-IGNORED | MUTANT KILLED |
| d10-scan-lowers | V-PCC-FRESHNESS-SCAN-ESCALATES-ONLY | MUTANT KILLED |
| d44-cache-write | V-PCC-NO-SECOND-STORE | MUTANT KILLED |
| d03-ledger-blind | V-PCC-LAW-PROOF-CONSERVATION-LEDGER | MUTANT KILLED |

Incidents, each fixed once (Regla 12):
- Three first drills printed `MUTANT CONTROL_INVALID`: the isolated copy lacked the phase dir that V-PCC-SPEC-RESOLVED reads (`02-06-PLAN.md`). Fixed by adding the phase dir to `copy_dirs` in every spec.
- `MUTANT SURVIVED gate=V-PCC-STATE-NOT-IN-DISPOSITION`: the AST scanner missed a `setattr(o, "disposition", ...)` write. `scan_disposition` now flags it (control flags 3); commit `a051673e`.
- `MUTANT SURVIVED gate=V-PCC-FINGERPRINT-OUTSIDE-ROOT`: the resolve-based check also refuses escaping paths, so removing the `..` clause was invisible; the gate now pins `sub/../a.txt` (inside the root) as unknown; commit `a051673e`.
- The `EXIT=` line of the first d43-ladder log came from `%ERRORLEVEL%` expanded at parse time; every log was re-run with `$LASTEXITCODE` appended.
- Live tree: `git status --porcelain -- modules tools` empty after the drills (except the intended suite fix, later committed); proof.py `86EF3E9F...F7D2` and convergence.py `D6CF29D6...23FC` hashes equal before and after. No known limit remains.

## Incumbent suites

| suite | runs | cold s | min s | max s | exit codes | summary | baseline | command |
|---|---|---|---|---|---|---|---|---|
| test_gsd_x_goal.py | 1 | 17.985 | 17.985 | 17.985 | 0 | GSDX_GOAL_PASS=26/26 | = 26/26 | python tools/test_gsd_x_goal.py |
| test_gsd_x_goal_bind_mission.py | 1 | 28.159 | 28.159 | 28.159 | 0 | GSDX_BIND_MISSION_PASS=10/10 | = 10/10 | python tools/test_gsd_x_goal_bind_mission.py |
| test_gsd_x_goal_chaos.py | 1 | 45.585 | 45.585 | 45.585 | 0 | GSDX_GOAL_CHAOS_PASS=15/15 | = 15/15 | python tools/test_gsd_x_goal_chaos.py |
| test_gsd_x_goal_claude_providers.py | 1 | 15.721 | 15.721 | 15.721 | 0 | GSDX_CLAUDE_PROVIDERS_PASS=20/20 | = 20/20 | python tools/test_gsd_x_goal_claude_providers.py |
| test_gsd_x_goal_cli.py | 1 | 239.276 | 239.276 | 239.276 | 0 | GSDX_GOAL_CLI_PASS=25/25 | = 25/25 | python tools/test_gsd_x_goal_cli.py |
| test_gsd_x_goal_codex_provider.py | 1 | 19.692 | 19.692 | 19.692 | 0 | GSDX_CODEX_PROVIDER_PASS=18/18 | = 18/18 | python tools/test_gsd_x_goal_codex_provider.py |
| test_gsd_x_goal_convergence.py | 1 | 3.982 | 3.982 | 3.982 | 0 | GSDX_GOAL_CONV_PASS=29/29 | = 29/29 | python tools/test_gsd_x_goal_convergence.py |
| test_gsd_x_goal_engine_identity.py | 1 | 9.239 | 9.239 | 9.239 | 0 | GSDX_ENGINE_ID_PASS=14/14 | = 14/14 | python tools/test_gsd_x_goal_engine_identity.py |
| test_gsd_x_goal_epoch.py | 1 | 0.810 | 0.810 | 0.810 | 0 | GSDX_GOAL_EPOCH_PASS=19/19 | = 19/19 | python tools/test_gsd_x_goal_epoch.py |
| test_gsd_x_goal_gate_class.py | 1 | 8.823 | 8.823 | 8.823 | 0 | GSDX_GATE_CLASS_PASS=11/11 | = 11/11 | python tools/test_gsd_x_goal_gate_class.py |
| test_gsd_x_goal_gate_provider.py | 1 | 14.080 | 14.080 | 14.080 | 0 | GSDX_GATE_PROVIDER_PASS=18/18 | = 18/18 | python tools/test_gsd_x_goal_gate_provider.py |
| test_gsd_x_goal_judge.py | 1 | 20.827 | 20.827 | 20.827 | 0 | GSDX_JUDGE_PASS=11/11 | = 11/11 | python tools/test_gsd_x_goal_judge.py |
| test_gsd_x_goal_long_run_provider.py | 1 | 0.378 | 0.378 | 0.378 | 0 | GSDX_LONGRUN_PROVIDER_PASS=16/16 | = 16/16 | python tools/test_gsd_x_goal_long_run_provider.py |
| test_gsd_x_goal_mutation_safety.py | 1 | 3.424 | 3.424 | 3.424 | 0 | GSDX_GOAL_MUTATION_SAFETY_PASS=8/8 | = 8/8 | python tools/test_gsd_x_goal_mutation_safety.py |
| test_gsd_x_goal_reconcile.py | 1 | 2.265 | 2.265 | 2.265 | 0 | GSDX_RECONCILE_PASS=22/22 | = 22/22 | python tools/test_gsd_x_goal_reconcile.py |
| test_gsd_x_goal_sweep.py | 1 | 35.375 | 35.375 | 35.375 | 0 | GSDX_GOAL_SWEEP_PASS=14/14 | = 14/14 | python tools/test_gsd_x_goal_sweep.py |
| test_gsd_x_goal_sweep_all.py | 1 | 17.976 | 17.976 | 17.976 | 0 | GSDX_SWEEP_ALL_PASS=11/11 | = 11/11 | python tools/test_gsd_x_goal_sweep_all.py |
| test_gsd_x_goal_pcc_semantics.py | 1 | 8.001 | 8.001 | 8.001 | 0 | GSDX_PCC_SEMANTICS_PASS=48/48 | - | python tools/test_gsd_x_goal_pcc_semantics.py |
| test_gsd_x_goal_pcc_replay.py | 1 | 142.055 | 142.055 | 142.055 | 0 | GSDX_PCC_REPLAY_PASS=28/28 | - | python tools/test_gsd_x_goal_pcc_replay.py |

`test_gsd_x_goal_mutation.py` is not run (R11, Phase 6 entry obligation).

## Liveness

`02-phase-end-liveness.log`: `modules: 491  |  REACHABLE: 312  |  ORPHAN: 179  |  UNKNOWN: 0  |  gate offenders: 0`, `EXIT=0`.

## Hermeticity

Live-store guard `C:\Users\User\.claude\state\gsd-x`: `SAME: files 253 -> 253 (delta +0)`, only `sweep_heartbeat.json` (excluded by default) changed; the suites' own guard rows also printed SAME. No `record-gates` or other live-store write was run.

## Production Reality verdicts

| claim | plane | verdict | evidence |
|---|---|---|---|
| seam zero behaviour change on this Windows host | Windows, hermetic suites | PROVEN | 0 DIFFERS over 17 incumbent suites; replay mutants and 12 drills KILLED; git diff shows only `A proof.py` |
| legacy replay over the recorded logs | hermetic committed copy | PROVEN | GSDX_PCC_REPLAY_PASS=28/28 |
| GSDX_FRONTIER inert | local | PROVEN | V-PCC-SWITCH-* gates, no reader of the switch outside proof.py |
| fixture judge replay vs Phase 1's 0.4 s | Windows, saturated host | OBSERVED | 4.8 s and 12.3 s on two runs (judge CLI wall 14.591 s and 37.826 s vs 1.558 s); over 2x at host CPU 100% and 1.1-3.4 GB free RAM; judge.py unchanged, so host noise, not a regression claim |
| g-002 / g-001 judge replay at the current engine | needs their trees | UNJUDGED | trees absent from this worktree (01-EVIDENCE.md:209) |
| POSIX / GEX44 | not run | UNJUDGED | not run |
| live sweep autonomy record under the new engine digest | live store | UNJUDGED | never run against the live store, by design |
| incumbent mutation suite | R11 | UNJUDGED | Phase 6 entry obligation |

## Owner-visible notes

- `proof.py` changes `engine_identity`: `record-gates` must be re-run after merge and never from this worktree.
- Verify `PP-GoalSweep` runs the main checkout before merge (A7).
- Spec S12 names `duplicate_payment`/729; the implemented names are `law_proof_conservation`/2916 (see 02-05-SUMMARY).

## Denominator rows moved

D43 -> DONE; D44 -> DONE (evidence text refreshed). D01, D03, D10 stay OPEN with their Phase 2 part cited. No row deleted.

## UKDL entries written

`vault/knowledge_base/ukdl-universal.md`, `## GSD X proof-conserving convergence, W1 (2026-10-07)` / `T-FAILURE-SENTINEL-COMPARES-EQUAL-TO-ITSELF-001`.

## Owner steps

None.
