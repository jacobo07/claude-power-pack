# Phase 4 Research -- premise verification (HR-PREMISE-001)

Method: every function, field and line the Phase 4 plans touch was read in source this session at HEAD fb3a0651.
`P` = read in source. Nothing here is from memory of an earlier phase. Open items are marked `UNVERIFIED` and have a
plan task that verifies them before code depends on them.

## 1. Seams Phase 4 reuses (no new store; GoalLog is the only store, spec S13)

| Premise | Evidence | Status |
|---|---|---|
| `append_pcc(log, state, type_, data, actor)` writes one PCC event through the CAS `GoalLog.append`, refuses unknown type / bad payload / newer `v` | proof.py:129-141; log.py:180 | P |
| Four PCC types exist as code: `obligation.contract`, `proof.produced`, `proof.inherited`, `proof.invalidated`; required fields per type | proof.py:41-45, 67-72 | P |
| `check_payload` checks required keys only; extra keys are allowed (so additive payload fields need no schema change) | proof.py:79-97 | P |
| `project_proofs(state)` -> `ProofLedger{contracts,produced,inherited,invalidated,unsupported}`; entries are `{seq, actor, ts, data}` | proof.py:100-126 | P |
| `proof_states(state, candidate, observed, now)` is pure, per obligation, consumes `observed[claim_id] = {"cert","current"}`; today nothing supplies `observed` | proof.py:425-464; no caller outside tests (grep of `modules/gsd_x`: only definitions) | P |
| `observe_premises(cert, current, now)` flattens a certificate dict with keys `claim, revision, gate_pin, fingerprint, environment, policy, freshness_class, env_deps, ts` | proof.py:214-227 | P |
| `state_from_premises`: changed > unknown > all-equal-with-event; switch off -> UNKNOWN | proof.py:230-244 | P |
| `claim_id(obligation)`; `legacy_contract` is one element with `inheritability: "never"` | proof.py:155-171 | P |
| `binding(tree, fingerprint)` returns `causal` only for a non-`unknown:` fingerprint | proof.py:174-178 | P |
| `causal_fingerprint(root, paths)` -> `cf1:` + sha256, `unknown:` on empty/absolute/`..`/escape/unreadable; ABSENT is a value | proof.py:273-301 | P |
| `environment_fingerprint(env_deps)`; `POLICY_VERSION = 1`; `FUTURE_SKEW_S = 300` | proof.py:189-190, 304-307 | P |
| `freshness_class(obligation, verdict, contract)`: unit->DETERMINISTIC, integration->ENVIRONMENT_SENSITIVE, in_game/live/REALITY->FRESH_REQUIRED, non-AND combine->UNKNOWN, keyword scan only escalates | proof.py:338-389 | P |
| `effective_contract(ledger, obligation)` -> (contract, refused seqs); weaker contracts ignored | proof.py:407-422 | P |
| `law_proof_conservation(ledger)` detects a second `proof.produced` for one (claim, binding) with no `proof.invalidated` between | proof.py:509-525 | P |
| `independent(a, b)` is the one independence definition | proof.py:528-541 | P |
| `switch_on(name)`, `inheritance_enabled()` read env at call time | proof.py:57-65 | P |

## 2. Producer path (where `proof.produced` is written)

| Premise | Evidence | Status |
|---|---|---|
| The only production caller of `cv.satisfy` is `sweep._apply_verdicts`; it builds `mcl.Verdict` from `receipt.verdicts` and passes `source={epoch, provider, handle}` | sweep.py:248-275; convergence.py:289-310 (docstring names it) | P |
| `satisfy` appends `obligation.satisfied` only when `evaluate` allows; returns `TransitionResult(allowed, outcome, reason)` | convergence.py:261-310 | P |
| `evaluate` refuses a stale revision, a pin that differs from the accepted pin, a non-runtime gate on a REALITY obligation, an empty tree | convergence.py:261-286 | P |
| `Receipt` carries `tree_before` and `tree_after`; the gate provider fills `tree_before` at start and `tree_after` at harvest from `tree_id(root, scope_paths)` | epoch.py:93-102; providers/gate.py:143, 187, 212 | P |
| The gate verdict's `tree_hash` is the tree AFTER the run (`tree = tree_id(...)` at harvest), so a gate that dirties its own scope binds its verdict to a tree it did not start on | gate.py:187, 202-204 | P |
| `GateProvider.harvest` is reached from `sweep_goal` HARVEST branch with `spec` carrying `root`, `scope_paths`, `identity`; receipt then `ep.ingest_receipt`, then `_apply_verdicts` | sweep.py:330-351 | P |
| `ingest_receipt` compares the receipt with its own epoch's identity and fence | epoch.py:355 (body not needed beyond this) | P |

Consequence (decision in CONTEXT): the dispatch-time candidate must be remembered to compare at harvest. The
`epoch.dispatching`/`running` spec already stores `tree_hash` (reconcile.py:221-222 `spec["tree_hash"]`) -- verified
P. The causal fingerprint at dispatch is added to the stored spec as a new additive key `causal` (UNVERIFIED how
`_start_gate` composes the spec at sweep.py:429+; plan 04-03 task 1 reads it before editing).

## 3. Consumption path (where inheritance changes a decision)

| Premise | Evidence | Status |
|---|---|---|
| `goal_closure(state, tree_hash, open_epochs=None)` blocks a SATISFIED obligation whose `verdict.tree_hash != tree_hash` or whose revision differs | convergence.py:347-355 | P |
| `_needs_a_gate_here(o, ctx)` returns '' for retired, a reason for ACCEPTED, and a reason when the verdict tree/revision differs | reconcile.py:101-121 | P |
| `decide`/`_decide_legacy`/`frontier.decide_frontier` all call `goal_closure` and `_needs_a_gate_here` | reconcile.py:170, 203, 213-222; frontier.py:260-282 (`_runnable_gate_obligations`) | P (frontier body line-checked in plan 04-04 task 1) |
| `Context` fields are pinned by V-PCC-DECIDE-SIG | tools/test_gsd_x_goal_pcc_replay.py:878-879, 986 | P -> no new Context field |
| `judge()` re-runs every SATISFIED obligation's pinned gate and requires `tree_id(worktree) == tree_hash` | judge.py:120-147 | P -> judge untouched, so inheritance cannot close a goal alone |
| `goal_closure` is documented "necessary for CONVERGED, never sufficient" | convergence.py:326-327 | P |

## 4. R12 / unknown trees

`git_state.tree_id` returns the constant `unknown:not-a-git-tree` when `git rev-parse HEAD^{tree}` fails
(git_state.py:129-131). Two such strings compare equal in `goal_closure` (convergence.py:350) and in
`_needs_a_gate_here` (reconcile.py:115). `proof_states` already treats any `unknown:` candidate as UNKNOWN
(proof.py:446, 453). P.

## 5. Candidate snapshot on git objects

| Premise | Evidence | Status |
|---|---|---|
| `git_state._git(root, *args)` is the only git runner (tries the Windows path then `git`), 60 s timeout, returns `(rc, stdout)`, no env parameter | git_state.py:21-32 | P |
| `_git` does not pass `env`, so a temporary index needs either a new `env` parameter (additive, default None) or a candidate-local runner | git_state.py:24-32 | P -> candidate.py carries its own `_run` with `GIT_INDEX_FILE`; `git_state.py` untouched |
| `blob_oid` normalises CRLF and equals `git hash-object` of the normalised bytes | git_state.py:62-75 | P |
| git: `git add -A -- <paths>` into a `GIT_INDEX_FILE` temp path then `git write-tree` yields a tree oid without touching refs or the real index | git plumbing contract; behaviour verified by gate V-CAND-SNAPSHOT-NO-SIDE-EFFECT (real repo in tmp) | UNVERIFIED until 04-01 task 2 runs it; fallback if `write-tree` fails -> `unknown:` |
| `core.autocrlf=true` on this clone (S11 note) means `git add` may re-normalise; the snapshot tree oid may differ from a Linux checkout of the same content | spec S11 | P -> the candidate oid is host-local; the CAUSAL fingerprint (blob_oid based) is the portable identity |

## 6. Test and drill harness

| Premise | Evidence | Status |
|---|---|---|
| Suite pattern: `check(gate, cond, ev)`, `run_gate`, hermetic HOME/USERPROFILE/GSDX_GOALS_ROOT before any engine import, summary `GSDX_..._PASS=n/m  threshold=m/m` | tools/test_gsd_x_goal_pcc_semantics.py:1-60 | P |
| Drill spec JSON: `{file, test, gate, old, new, copy_dirs}` (exact-substring replacement; one gate named) | Phase 2 `drills/d01-unknown-as-equal-drill.json` | P |
| `tools/mutation_drill.py` runs the mutated test with no `cwd=` (housekeeping from Phase 3) | 03-CONTEXT.md Housekeeping | P |
| New `.py` under `goal/` changes `engine_identity` (S14 G17) | spec S14; engine_identity.py:34-39 (per spec) | P (spec-cited) |

## 7. Premises that FAILED or narrowed

- The packet text says `modules/gsd_x/goal/frontier.py` exists as a "Phase 2/3 seam": confirmed (377 lines), but
  `proof_states` has no caller in it. `grep proof_states` found only the definition. So Phase 3's frontier does not
  yet read proof states: plan 04-04 wires that consumption instead of assuming it.
- `Context` cannot gain a field (pinned). The inheritance observation therefore travels in the log as a
  `proof.inherited` event written by the sweep, not through `decide`.
- D25/D26 are assigned to Phase 3 by DENOMINATOR; not built here (CONTEXT).

## 8. Reuse map (what is NOT built)

No new event store, cache, sqlite or copy tree. New modules: `candidate.py` (snapshot + drift), `inherit.py`
(observe/plan/apply/verification_set/fresh_islands). Everything else is an edit in `proof.py` (algebra,
`candidate.promoted`), `convergence.py` (R12 + `inherited` arg), `reconcile.py` (R12 + `inherited` arg), `sweep.py`
(produce + reconcile step) and two new suites.
