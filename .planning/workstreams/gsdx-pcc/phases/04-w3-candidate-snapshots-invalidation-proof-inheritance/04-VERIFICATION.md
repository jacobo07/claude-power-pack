---
phase: 4
workstream: gsdx-pcc
status: passed
verified: 2026-10-13
head_at_verification: b65b533e
---

# Phase 4 Verification -- W3 Candidate snapshots, invalidation, proof inheritance

Every check below was run by the worker. Plane is stated per line. **Windows plane** = the laptop (hermetic temp roots). **Linux plane** = GEX44: nothing in Phase 4 ran there.

## Gates

| Gate | Result | Plane | Source |
|---|---|---|---|
| `GSDX_INVALIDATION_PASS=26/26  threshold=26/26` | PASS | Windows | logs/04-verify-invalidation.log |
| `GSDX_PCC_REPLAY_PASS=28/28  threshold=28/28` | PASS | Windows | logs/04-verify-pcc_replay.log |
| `GSDX_PCC_SEMANTICS_PASS=48/48  threshold=48/48` | PASS | Windows | logs/04-verify-pcc_semantics.log |
| `GSDX_FRONTIER_PASS=40/40  threshold=40/40` (full suite, one run) | PASS | Windows | logs/04-verify-frontier.log |
| `python modules/liveness/reachability.py` | exit 0 | Windows | logs/04-verify-liveness.log |
| 18 other goal suites (convergence 29, reconcile 22, certificate 7, mutation_safety 8, cli 25, sweep 14, sweep_all 11, chaos 15, engine_identity 14, epoch 19, gate_class 11, gate_provider 18, judge 11, long_run_provider 16, claude_providers 20, codex_provider 18, bind_mission 10, test_gsd_x_goal 26) | PASS | Windows | logs/04-05-suite-*.log |
| `test_gsd_x_goal_mutation.py` | **UNRUN** (270 s timeout; kill left `judge.py` mutated, restored by `git checkout`, diff empty) | -- | 04-05-SUMMARY.md |

## Mutation drills (`tools/mutation_drill.py`; KILLED only after a valid clean-copy control)

| Drill | Mutant | Gate | Verdict | Plane |
|---|---|---|---|---|
| d1 | unknown premise no longer unknown | V-INV-UNKNOWN-NOT-CLEAN | KILLED | Windows |
| d2 | FRESH_REQUIRED made eligible | V-INV-FRESH-REQUIRED-NEVER | KILLED | Windows |
| d3 | inherited_ids synthesises an event | V-INV-OMITTED-WITHOUT-EVENT | KILLED | Windows |
| d4 | moved-under-verification always False | V-CERT-MOVED-UNDER-VERIFICATION | KILLED | Windows |
| d5 | tree_equal stops refusing `unknown:` | V-INV-R12-CLOSURE | KILLED | Windows |
| d6 | fingerprint premise always EQUAL | V-INV-FALSE-REUSE | KILLED | Windows |
| d7 | unknown premise no longer forces `full` | V-INV-VSET-UNKNOWN-FULL | KILLED | Windows |
| d8 | event premises not compared with certificate | V-INV-EVENT-DISAGREES | KILLED | Windows |

Logs: `logs/04-05-drill-d1..d8.log`. All eight are the ROADMAP RED cases (false reuse, UNKNOWN as clean, fresh-required inherited, omitted proof without event, candidate moved under verification).

## Requirements

| Req | Evidence (gate, plane) | Verdict |
|---|---|---|
| D01 | V-INV-INHERIT-OK, -UNKNOWN-NOT-CLEAN, -ALGEBRA-TRUTH (Windows; d1 d6) | met |
| D10 | V-INV-FRESH-REQUIRED-NEVER, V-CERT-PRODUCED-ON-SATISFY (Windows; d2) | met |
| D11 | pure algebra `proof.combine_states` only (V-INV-ALGEBRA-TRUTH, -NONAND-RUNS-FULL); no engine path evaluates a non-AND claim through it | PARTIAL, row stays OPEN |
| D12 | V-CERT-BINDING-SCHEME, V-INV-FALSE-REUSE (Windows; d6) | met |
| D13 | V-CERT-PRODUCED-ON-SATISFY, -ONLY-AFTER-SATISFY, -LAW-CONSERVATION (Windows) | met |
| D14 | V-INV-FRESH-REQUIRED-NEVER, -FRESH-ISLANDS (Windows) | met |
| D20 | V-INV-VSET-* gates (Windows; d7) | met |
| D23 | V-CAND-* gates, V-INV-PROMOTED-PROJECTION (Windows) | met as substrate: no sweep path records `candidate.promoted` yet |
| D24 | substrate only (V-INV-DRIFT-SUBSTRATE, V-CAND-DRIFT; d4); watcher is Phase 9 | OPEN |
| D39 | V-INV-FRESH-ISLANDS (Windows) | met |
| D45 | V-INV-OMITTED-WITHOUT-EVENT, -EVENT-DISAGREES (Windows; d3 d8) | met |
| R02 | V-CERT-BINDING-SCHEME, V-INV-FALSE-REUSE (Windows) | met |
| R12 | V-INV-R12-CLOSURE, -NEEDS-GATE, -CONTROL (Windows; d5) | met |

## Human-verification checks, run myself

1. Phase 2 suites green: replay 28/28, semantics 48/48 (rows above). Done.
2. Phase 3 frontier suite 40/40 (rows above). Done.
3. Every `04-0N-SUMMARY.md` present (01..05). Done.
4. Liveness exit 0 with `candidate` and `inherit` declared PLANNED. Done.
5. Kill switches: V-INV gates cover `GSDX_PROOF_INHERITANCE` off => full run, no inheritance. Done (Windows).
6. Nothing pushed; `git status --short` is clean except `vault/progress.md` and `LEARNINGS_PENDING.md`. Done.

## Honest limits

- `test_gsd_x_goal_mutation.py` is UNRUN and belongs to the Linux plane (coordinator item; see STATE.md OWNER DECISION NEEDED).
- Nothing in Phase 4 ran on the Linux plane.
- D11 is pure algebra; D23 and D24 are substrate. Do not report them as executed capabilities.
- `judge.py` is untouched, so closure is necessary-not-sufficient; Phase 5 owns the judge.
