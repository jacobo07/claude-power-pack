# Phase 2 -- W1 audit record

## Iteration lens

- FASE 1 (premises): every engine function the amended spec names exists; see `02-premises.log` (EXIT=0). The control premise `git_state.causal_fingerprint` is absent as designed (`02-premises-control.log`, EXIT=1): that name is a NEW function the seam adds, not an existing one.
- FASE 2 (class 0-6 issues in the amended spec): none found. The one place the spec could invent an API is `causal_fingerprint`, and S4 specifies it as new code in `proof.py`, built on `git_state.blob_oid`, which exists.
- FASE 3-5: no change. Nothing in the premise run overturned an assumption of the RESEARCH recommendations the spec adopted.

## Audit Result

**Plan reviewed:** Amended GSD X proof-conserving convergence spec (S1-S16) plus plans 02-02..02-06. Together they land a zero-behaviour-change PCC seam: `proof.py`, a legacy replay golden, the semantics and replay suites, the five laws as invariants, and drills plus phase-end evidence.
**Files in scope:** 22 (read 17)
**Gaps found:** 6

### Gaps

1. **[EDGE] V-PCC-REPLAY-INTERLEAVED masks seq fields but not the seq number written into `decide().reason`**
   - Where: 02-02-PLAN.md Task 3 step 3 (the mask list from RESEARCH Pitfall 3, 02-RESEARCH.md:416). The text comes from modules/gsd_x/goal/intervention.py:111-115 (`f"cancelled by operator {op.last_actor} at seq {op.last_seq}"`), which `reconcile.decide` returns as `Decision(BLOCKED, stop)` at reconcile.py:156-158.
   - Why this matters: `syn_operator` ends with a cancel. Rebuilt with a PCC event after every writer call, the BLOCKED reason says `at seq N+k` instead of `at seq N`. The plan says "any other difference fails", so V-PCC-REPLAY-INTERLEAVED stays red after proof.py lands. 02-03 Task 1's GREEN acceptance (`PASS V-PCC-REPLAY-INTERLEAVED`) cannot be reached without improvising a wider mask mid-execution, which is a repair loop. The append-at-end gates miss it because `zz.future_event` is not an operator kind and does not move `op.last_seq`.
   - Suggested fix: Add `decide.reason` to the named mask, but only as a regex substitution of `at seq \d+` -> `at seq <seq>`, and only when OperatorState.last_seq is masked too. Name it in RESEARCH Pitfall 3 so the mask stays a closed list.

2. **[COMPLETION-GATE] A gate that raises makes the drill UNJUDGED, not KILLED, and the plan has no UNJUDGED path**
   - Where: 02-02-PLAN.md Task 3 (only projections are wrapped as `__raised__`; writer calls in the INTERLEAVED rebuild are not). 02-06-PLAN.md Task 1, drill rows `d43-ladder` (the tracer) and `d01-fingerprint-raises`. tools/mutation_drill.py:189-190.
   - Why this matters: The d43-ladder mutant sends `proof.*` events into the FAILURE_DISPOSITIONED branch, so `cv.failures[d["id"]]` raises GoalLogCorrupt (convergence.py:136-141). In the INTERLEAVED rebuild, `cv.satisfy` and `carry_obligation` call `project_convergence` after a PCC event, so the exception escapes the gate. The suite then never prints `GSDX_PCC_REPLAY_PASS=`, and mutation_drill returns UNJUDGED (exit 2) even though `FAIL V-PCC-REPLAY-IGNORE-NEW-TYPES-PCC` was already printed. The same happens when `causal_fingerprint` raises under d01-fingerprint-raises. 02-06 only says what to do on SURVIVED and on HARNESS/CONTROL_INVALID, so the very first (tracer) drill stalls.
   - Suggested fix: In both suites, wrap every gate body in a try/except that prints `FAIL <gate> raised <ExcType>: <msg>` and moves on, so the summary line always prints. Add one semantics gate that proves it (a deliberately raising gate still leaves the `_PASS=` line). In 02-06, treat UNJUDGED as a defect in the suite harness and fix it once.

3. **[EDGE] The synthetic-scenario recipe fails at the public writers as written**
   - Where: 02-02-PLAN.md Task 2 step 4. The repo id `pcc-synthetic-repo` and the `syn_carry` steps ("two obligations, satisfy one, carry_obligation") are refused by modules/gsd_x/goal/log.py:144 (`re.fullmatch(r"[0-9a-f]{7,64}", repo)`) and convergence.py:196 (`already belongs to revision`).
   - Why this matters: `GoalLog` raises GoalLogError on the repo id before any synthetic event is written. Even with a valid id, `carry_obligation` without an intervening `contract.revise` always refuses. V-PCC-REPLAY-SYNTHETIC and V-PCC-REPLAY-POPULATION (which needs `obligation.carried`) cannot go green until the executor redesigns the scenarios during golden capture, and the golden is the one capture that is refused once it exists.
   - Suggested fix: Use a fixed 7-64 char lower-case hex repo id (for example `0000000000000000000000000000000000pcc5e0`, all hex), and spell out `syn_carry` as: declare, accept two obligations, satisfy one, `revise` (adding an acceptance item), then carry the satisfied one.

4. **[REALITY-CONTRACT] The `proof.produced` -> FRESH path has no gate, so an `unknown:` binding can come out FRESH**
   - Where: 02-04-PLAN.md Task 2 step 4 ("FRESH if a proof.produced binding equals the candidate binding at the current revision"). Spec S2 (FRESH clause and adjacency rule) and S3 ("never from the event's stored values").
   - Why this matters: The 2916-cell truth table and V-PCC-LAW-UNKNOWN-ESCALATES only exercise `state_from_premises`. V-PCC-STATE-UNKNOWN-TREE only exercises the legacy verdict path. On the certificate path, the plan's wording is plain binding equality. A `proof.produced` with binding `{"scheme":"tree","value":"unknown:not-a-git-tree"}` and the same candidate string then yields FRESH, which is exactly the R12 class S2 says never compares equal. Separately, FRESH is derived from the event's stored binding and revision, and `append_pcc` (the only writer) checks only payload shape. So a raw or forged `proof.produced` on a never-satisfied (ACCEPTED) obligation reads FRESH, against S3. Phase 2 has no consumer, but Phase 4 would inherit this projection as proven.
   - Suggested fix: Apply the `unknown:` -> UNKNOWN rule before any FRESH decision on either path, and compare bindings through a function that is false whenever either side is `unknown:`. Add gates V-PCC-STATE-PRODUCED-UNKNOWN-BINDING (must give UNKNOWN) and V-PCC-STATE-PRODUCED-WITHOUT-SATISFIED (a raw produced event on an ACCEPTED obligation must not give FRESH in Phase 2). Add both cases to `law_unknown_escalates`.

5. **[EDGE] The synthetic budget can make the golden red days after capture**
   - Where: 02-02-PLAN.md Task 2 step 4 (`syn_contract` ... `set_budget`, payload unspecified) together with step 2 (`now` = last event ts + 60) and step 5 (volatile paths detected by two back-to-back builds). Mechanism: reconcile.py:86-87 puts `(ctx.now - started)/3600:.1f` into `Decision.reason`.
   - Why this matters: Synthetic events get wall-clock timestamps (log.py:194) at every test run. If the executor sets `max_hours` with a fixed `started_at`, the ESCALATE reason (reachable because syn_contract has unjudged planes and no blocker) grows with calendar time. The two builds at capture are seconds apart, so the field is not flagged volatile, and V-PCC-REPLAY-SYNTHETIC passes on capture day and fails later.
   - Suggested fix: Pin the `syn_contract` budget to `{"max_epochs": <n>}` only. If `max_hours` is needed, set `started_at` from the scenario's own first event ts so the elapsed time is under one second on every run.

6. **[EDGE] For a raw log where `o.revision` differs, the plan says STALE and the spec says UNKNOWN**
   - Where: 02-04-PLAN.md Task 1 step 2 ("SATISFIED otherwise -> STALE") against spec S2 legacy-mapping bullet ("a raw log where `o.revision` differs maps to UNKNOWN, never FRESH").
   - Why this matters: Both states force a FULL re-run, but the recorded reason differs, and no gate pins the case (V-PCC-STATE-LEGACY-MAP only checks FRESH <=> legacy). An executor following the plan contradicts the audited spec without any test going red. goal_closure blocks this case on its own clause (convergence.py:359-361), not on the tree/revision clauses.
   - Suggested fix: Make step 2 map SATISFIED + verdict tree/revision equal + `o.revision != state.revision` to UNKNOWN, and add a semantics case with a raw `obligation.accepted` under an older revision.

### Audit clean items (informational, not blocking)
- The legacy readers skip unknown event types: contract.project:93-109, project_convergence:110-141, project_epochs:241-259, project_operator:56-57, project_hypotheses:68-70 and judge.current:88-90. `contract.last_event` (contract.py:166) has no caller. `sweep.is_autonomous` reads only events, so the new engine digest from proof.py does not reach the golden. No legacy goal file contains a `proof.`/`obligation.contract` string, so the capture marker is valid.
- AST discovery finds exactly 22 module-level dotted event constants under modules/gsd_x/goal (contract 4, epoch 4, convergence 7, intervention 4, evidence 1, judge 1, sweep 1). The file-name constants are excluded by FILE_SUFFIXES or contain a hyphen.
- tools/mutation_drill.py:134-139 copies all of `tools/` (fixtures and golden included) plus `modules/` and `copy_dirs` for a test outside the subject's dir, so the drill layout and the live-sha check support the 02-06 drills (apart from gap 2). The export/restore round trip through cmd_export/cmd_restore (tools/gsd_x_goal.py:333-365) and the CAS/LostRace path (log.py:180-241) work as the plans assume.

## Dispositions

Every fix below is a plan defect, applied in place by the executing plan and recorded as a deviation in that plan's SUMMARY. None changes a Decision in STATE.md. A target of `CODE:02-0N` means plan 02-0N reads the row before its first edit.

| gap | category | disposition | target | change |
|---|---|---|---|---|
| 1 | EDGE | INJECTED | CODE:02-02 | INTERLEAVED mask gains `decide.reason` as a regex substitution `at seq \d+` -> `at seq <seq>`, only when `OperatorState.last_seq` is masked; named in the closed mask list |
| 2 | COMPLETION-GATE | INJECTED | CODE:02-02, CODE:02-06 | every gate body in both suites is wrapped so a raise prints `FAIL <gate> raised <ExcType>: <msg>` and the `_PASS=` line always prints; one semantics gate proves it; 02-06 treats UNJUDGED as a suite-harness defect fixed once |
| 3 | EDGE | INJECTED | CODE:02-02 | synthetic repo id is fixed 7-64 char lower-case hex; `syn_carry` = declare, accept two, satisfy one, revise (add acceptance item), carry the satisfied one |
| 4 | REALITY-CONTRACT | INJECTED | SPEC:S2, CODE:02-04 | `unknown:` -> UNKNOWN before any FRESH decision on both paths; binding compare false when either side is `unknown:`; new gates V-PCC-STATE-PRODUCED-UNKNOWN-BINDING and V-PCC-STATE-PRODUCED-WITHOUT-SATISFIED; both cases added to `law_unknown_escalates` |
| 5 | EDGE | INJECTED | CODE:02-02 | `syn_contract` budget is `{"max_epochs": n}` only; no wall-clock `max_hours` |
| 6 | EDGE | INJECTED | SPEC:S2, CODE:02-04 | SATISFIED + verdict tree/revision equal + `o.revision != state.revision` maps to UNKNOWN; new semantics case with a raw `obligation.accepted` under an older revision |

Audit G4: the spec S2 FRESH clause is held to the rule above (stated in the Dispositions row; S2 already says an `unknown:` binding never compares equal).
Audit G6: the spec S2 legacy-mapping bullet already says UNKNOWN; plan 02-04 is brought into line with it, not the reverse.

Gaps found: 6 -- 6 injected, 0 deferred, 0 rejected.
