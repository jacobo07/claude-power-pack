---
phase: 06-s6-blocker-compiler-owner-boundary
plan: 01
subsystem: mission-supervisor
tags: [blocker-compiler, owner-boundary, batching, mutation-drills, S6]
requires: [05-01]
provides:
  - tools/blocker_compiler.py (compile_blocker, plan_evidence, census, foreseeable_decisions, CLI)
  - gsd_mission.block_mission (single mission_blocked writer), annotate_hold, batch_foreseeable_decisions
  - tools/test_s6_blockers.py (72 gates, 34 mutant drills)
  - 06-CENSUS.md (class-to-evidence table from the host ledger)
key-files:
  created:
    - tools/blocker_compiler.py
    - tools/test_s6_blockers.py
    - .planning/workstreams/flow-compression/phases/06-s6-blocker-compiler-owner-boundary/06-CENSUS.md
  modified:
    - tools/gsd_mission.py
    - .planning/workstreams/flow-compression/STATE.md
decisions:
  - independent_work is information-only (D-05 narrowing): no consumer acts on it, no new launch path
  - Unclassifiable blockers are UNKNOWN with owner_required true and independent_work false
  - RESOLVE_BY_POLICY applies only to preference-class items with a recorded rule; PROTECTED keywords fail toward the Owner
  - Kill switch CPP_BLOCKER_COMPILE=off restores the exact old record and ledger shape; compiler faults fail open to UNKNOWN
requirements: [FC-06, FC-08, FC-10, FC-12]
completed: 2026-10-24
status: complete
commits: 5
plan_head_before: cea6b85b0e9f6cfb3289524ccb11e394ecd459a5
actuals:
  tokens: 120000
  tasks: 3
  commits: 5
---

# Summary 06-01

Landed S6. Every BLOCKED transition, Owner hold and AMR OWNER_BOUNDARY park now carries a typed blocker `{class, unblock_condition{kind,...}, unblock_text, independent_work, independent_reason, owner_required, rule}`. `gsd_mission.block_mission` is the only writer of `mission_blocked` (an AST search over `tools/` confirms five callers and no other writer); `annotate_hold` types `set_owner_hold` and `_amr_boundary`. Foreseeable Owner decisions are batched once at arm (`owner_decisions_batched` ledger row under session `arm-preflight`, queue row `q-decisions-<key>`), idempotent, with no authority expansion and no new state machine.

## D-05 narrowing

`independent_work` is information-only. It is true only on positive plan evidence (ROADMAP checkboxes, "Depends on", STATE current_phase) for unit-scoped classes. It is false with a reason for mission-wide classes (`mission_wide`), UNKNOWN (`unclassified`), unreadable evidence (`unmeasured`), an empty measured set (`no_other_unit`) and exhausted authority (`authority_exhausted`). Nothing reads the flag to launch work.

## Taxonomy and census

15 classes: HOST_GATE, COMMAND_REQUEST, DECISION_REQUEST, RESOURCE_REQUEST, PUBLISH_BOUNDARY, CAPITAL_EXHAUSTED, COST_HOLD_RECOVERING, PROVIDER_LIMIT, WAIT_RESOURCE, GSD_HOLD, CAPSULE_NOT_CERTIFIED, CAPSULE_SEAL_REFUSED, SETUP_HOLD, OWNER_PARK, UNKNOWN. First match wins.

Census (host ledger, 6249 rows at generation; live, so a dated snapshot): mission_blocked 55, blocked_intent 8, owner_hold_set 56, recovery_owner_boundary 5, 116 compiled rows. Per class: HOST_GATE 9, COMMAND_REQUEST 9, DECISION_REQUEST 12, RESOURCE_REQUEST 1, PUBLISH_BOUNDARY 5, CAPITAL_EXHAUSTED 16, COST_HOLD_RECOVERING 13, PROVIDER_LIMIT 3, WAIT_RESOURCE 0, GSD_HOLD 1, CAPSULE_NOT_CERTIFIED 0, CAPSULE_SEAL_REFUSED 2, SETUP_HOLD 16, OWNER_PARK 24, UNKNOWN 5. The zero-row classes exist only as named hold kinds in code.

UNKNOWN residual (5 rows, five distinct reasons, each seen once): a "dispatch gsd-executor to run ..." instruction, "open this session to continue setup", "arm a new TB-FULL mission epoch under the R-REFC packet ...", "say so if you want the in-play probe launched", and "run `/gsd-autonomous --from 20` from the p17-growth worktree". All are owner_required true and independent_work false; none is counted as a pass.

## Gates and mutants

S6_PASS=72/72: 36 base gates (including the declared-unmutated V-S6-MUTANT-MAP), 34 drill gates, V-S6-DRILL-CONTROL-NOOP-FIRES. 34 distinct mutants, each mapped (in `MUTANT_FOR`, exact gate names) to the gates that must go red under it; a drill also requires its mapped gate green on the baseline, and an absent or crashing gate counts as red. V-S6-DRILL-CONTROL-NOOP-FIRES replaces every mutant with a no-op and requires all 34 drills to fail.

Unmutated gates: V-S6-MUTANT-MAP (it is the map's own integrity check, declared in `UNMUTATED`). The drill gates and the no-op control are excluded by definition (they are the mutation harness, not subjects of it).

## Regression vs baseline (foreground, CPP_RESOURCE_ADMISSION=off)

| Suite | Result | Baseline |
|---|---|---|
| test_blocked_intent | 16/16 | 16/16 |
| test_owner_boundary_delivery | 14/14 | 14/14 |
| test_s5_reconcile | 44/44 | 44/44 |
| test_gsd_epoch | 111/111 | 111/111 |
| test_arm_preflight | 16/16 | 16/16 |
| test_mission_recovery | 69/69 | 69/69 |
| test_mission_spend | 44/45 | 44/45 (V-MSPEND-HOLD-PLAN-NONE, pre-existing) |
| test_mission_continuity | 37/38 | 37/38 (V-AMCR-ONE-RESOLVER-INVENTORY, pre-existing) |
| test_gsd_mission | 234/234 | 234/234 |
| test_s6_blockers | 72/72 | new |

Host isolation: OWNER_QUEUE.jsonl sha256 prefix 2c03045bfb579004 before and after both regression batches. `decisions --cwd . --workstream flow-compression` returns measured true, 0 items.

## Deviations from Plan

**1. [Rule 1 - Bug] `_m_publish` broadened to `irreversible`.** The real autonomy gate classes a force push as OWNER/irreversible, which compiled to UNKNOWN. Both outward-facing and irreversible now type as PUBLISH_BOUNDARY. Commit b6a30be4.

**2. [Rule 1 - Bug] Capital regex over-match.** The bare word "budget" typed unrelated rows as CAPITAL_EXHAUSTED; tightened, plus an `authority_trip` rule. Found by the first census.

**3. [Rule 1 - Bug] V-S6-HOLD-PARKS-TYPED read the wrong event.** Typed row is the transition event `recovery_boundary`, not the ledger row `recovery_owner_boundary`. Gate fixed.

**4. Extra mutants beyond the plan table.** Added M-NEVER-INDEPENDENT, M-DROP-INTENT-RULE, M-UNTYPED-BLOCK, M-CENSUS-DROPS-EVENT, M-ITEM-ID-UNSTABLE, M-POLICY-RULE-DROPPED, M-NEW-STATE-LIVE. M-ALWAYS-INDEPENDENT is not mapped to INDEPENDENT-POSITIVE (always-true leaves that gate green); M-ONE-QUEUE-PER-ITEM also kills BATCH-ONE-RECORD-ONE-QUEUE.

**5. Batching reaches arm_chain through `arm(launch=False)`.** No second call site was added.

**6. Branch allow-list.** `worktree-flow-compression-w` does not match the agent-* pre-commit pattern; it is the orchestrator-designated, non-protected branch. Only the protected-branch assertion was enforced. Recorded in STATE.md.

**7. Known conservative gap (not repaired).** The compiler ignores the `authorized` flag on a git push, so an authorized push still reports owner_required true.

Pre-existing debt not repaired: V-AMCR-ONE-RESOLVER-INVENTORY, V-MSPEND-HOLD-PLAN-NONE.

## Commits

37a34d35 (tracer), 66fe63ea (batching), b6a30be4 (gate set, publish broadening, census), f1ef65fb (mutation drills, MUTANT_FOR, no-op control), eaa3f426 (STATE incidents). The commit that adds this SUMMARY follows and is not counted in `commits:`.

## Known Stubs

None.

## Not done here (orchestrator-owned)

Phase close: `completed_phases` / `current_phase` edit, RESUMPTION_FILE.md, and 06-VERIFICATION.md (GSD verifier). No GSD Core change (FC-10); no push; live Power Pack install untouched.

## Self-Check: PASSED

Files present: tools/blocker_compiler.py, tools/test_s6_blockers.py, 06-CENSUS.md, STATE.md edits. Commits present in `git log`: 37a34d35, 66fe63ea, b6a30be4, f1ef65fb, eaa3f426. S6_PASS=72/72 observed in the foreground run after the last code commit.
