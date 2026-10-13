# 04-05 SUMMARY -- drills, liveness, regression, evidence

Plane for everything below: **Windows laptop** (local, hermetic temp roots). Nothing ran on the Linux plane.

## Drills (`tools/mutation_drill.py`, spec JSON under `drills/`, one per call, logs `logs/04-05-drill-dN.log`)
| drill | mutant | gate | verdict |
|---|---|---|---|
| d1 | `state_from_premises` stops treating an unknown premise as unknown | V-INV-UNKNOWN-NOT-CLEAN | KILLED |
| d2 | FRESH_REQUIRED added to `inherit.ELIGIBLE` | V-INV-FRESH-REQUIRED-NEVER | KILLED |
| d3 | `inherited_ids` synthesises an event when none exists | V-INV-OMITTED-WITHOUT-EVENT | KILLED |
| d4 | `_moved_under_verification` always False | V-CERT-MOVED-UNDER-VERIFICATION | KILLED |
| d5 | `tree_equal` stops refusing `unknown:` ids | V-INV-R12-CLOSURE | KILLED |
| d6 | fingerprint premise always EQUAL | V-INV-FALSE-REUSE | KILLED |
| d7 | `verification_set` stops flagging unknown premises as `full` | V-INV-VSET-UNKNOWN-FULL | KILLED |
| d8 | `_agrees` stops comparing event premises with the certificate | V-INV-EVENT-DISAGREES | KILLED |
A KILLED verdict is only returned after the harness's clean-copy control shows the named gate passing (CONTROL_INVALID otherwise).
Anchors are single-line (d5 mutates the `unknown:` clause of `tree_equal` rather than rewriting its body to `==`; both remove the same protection).

## Liveness
`python modules/liveness/reachability.py` exit 0, gate offenders 0 (`logs/04-05-liveness.log`). First run: 2 offenders, `gsd_x/goal/candidate` and
`gsd_x/goal/inherit`; both declared PLANNED in `vault/liveness/reachability_registry.json` with the same note as `frontier` / `proof` (the goal
engine's only entrance is `tools/gsd_x_goal.py`, outside the scanner's aperture). `inherit` is imported by `sweep.py`/`reconcile.py`, `candidate` by `inherit`.

## Regression (one suite per call; logs `logs/04-05-suite-*.log`)
semantics 48/48; replay 28/28 and frontier 40/40 (04-04 logs, sweep code unchanged since); convergence 29/29, reconcile 22/22, certificate 7/7,
mutation_safety 8/8, cli 25/25, sweep 14/14, sweep_all 11/11, chaos 15/15, engine_identity 14/14, epoch 19/19, gate_class 11/11, gate_provider 18/18,
judge 11/11, long_run_provider 16/16, claude_providers 20/20, codex_provider 18/18, bind_mission 10/10, test_gsd_x_goal 26/26.

## UNRUN
`tools/test_gsd_x_goal_mutation.py` hit my 270 s per-suite timeout and was killed. It mutates LIVE files and restores them by SHA-256, so the kill
left `modules/gsd_x/goal/judge.py` mutated (`if moved:` -> `if False:`). I found it in `git status`, restored it with `git checkout -- modules/gsd_x/goal/judge.py`,
and confirmed an empty diff. Not retried. **Coordinator: run it on the Linux plane (GEX44) and label the result "Linux plane".**

## DENOMINATOR
D01 D10 D12 D13 D14 D20 D23 D39 D45 R02 R12 -> DONE, each row cites the passing gates. D11 stays OPEN (PARTIAL: pure algebra only). D24 OPEN (substrate
noted). D25/D26 untouched.
