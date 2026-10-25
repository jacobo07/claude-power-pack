---
phase: 06-s6-blocker-compiler-owner-boundary
verified: 2026-10-24T21:30:00Z
status: passed
score: "72/72 gates; 8/8 plan truths; 3/3 roadmap criteria"
---

# Phase 6 verification - PASSED (3 warnings recorded, none blocks the goal)

Verifier re-ran the gates itself (CPP_RESOURCE_ADMISSION=off) at HEAD 98fddd3b and read tools/blocker_compiler.py and tools/gsd_mission.py directly. SUMMARY claims were not used as evidence. Two SUMMARY statements did not survive (see W1, W2).

## Gates re-run
- `python3 tools/test_s6_blockers.py` S6_PASS=72/72 (exit 0, 10 s). 36 base gates, 34 mutant drills, V-S6-DRILL-CONTROL-NOOP-FIRES.
- Regression vs the plan baseline, all foreground: test_blocked_intent BI 16/16; test_owner_boundary_delivery OBD 14/14; test_s5_reconcile S5 44/44; test_gsd_epoch EPOCH 111/111; test_arm_preflight PRE 16/16; test_mission_recovery AMR 69/69; test_gsd_mission MC 234/234; test_mission_spend 44/45 (V-MSPEND-HOLD-PLAN-NONE, pre-existing); test_mission_continuity 37/38 (V-AMCR-ONE-RESOLVER-INVENTORY, pre-existing). Counts equal the SUMMARY table.
- Host isolation: `~/.claude/state/OWNER_QUEUE.jsonl` sha256 prefix 2c03045bfb579004 before and after the whole regression batch.
- `python3 tools/blocker_compiler.py census --json`: exit 0, 6278 rows now (6249 at the committed census; the ledger is live), non-empty populations. 06-CENSUS.md lists the ledger path, per-event populations, class-to-evidence table for all 15 classes, and the 5-row UNKNOWN residual.
- Independent mutation spot-checks (verifier edited the real source, ran the suite, restored by `git checkout`; tree clean afterwards):

| Mutation applied to real source | Result |
|---|---|
| `_independent` returns True first | 54/72, 18 FAIL (TRACER-UNKNOWN-REACHABLE, INDEPENDENT-*, UNKNOWN-NEVER-INDEPENDENT, ...) |
| `_compile_blocker` except narrowed to KeyboardInterrupt (fail-closed) | 70/72: V-S6-TRACER-FAIL-OPEN + drill M-FAIL-CLOSED |
| batch delta ignores prior owner_decisions_batched rows | 69/72: V-S6-BATCH-IDEMPOTENT + two drills |
| `_autonomy` returns None (autonomy gate ignored) | 66/72: CLASS-POSITIVE, AUTONOMY-AGREEMENT, NOOP-FIRES + drills |
| planted direct `mission_blocked` writer in gsd_mission | 69/72: V-S6-WRITER-DISCOVERY names `_sneaky` + two drills |
| `_gate_question` always RESOLVE_BY_POLICY | 70/72: BATCH-POLICY-RULE-RECORDED red; outward items still held back by the category check (defence in depth) |

An earlier first attempt at two mutants was syntactically broken or too weak to matter; they were redone and are the rows above. Every mutation that reached the code went red.

## Roadmap criteria and plan truths
1. VERIFIED: every BLOCKED transition is typed through one writer. My own AST scan of non-test tools/*.py (transition/ledger_append with event `mission_blocked` or `state=BLOCKED`) finds exactly one site, `block_mission` (gsd_mission.py:402). Five callers of `block_mission` (lines 4772, 5075, 5481, 5513, 5664). Other `expect_state=BLOCKED` transitions (mission_unblocked, capsule_seal_refused, line 5519) set no BLOCKED state. Record carries `blocker` with epoch and at; ledger row carries blocker_class, independent_work, owner_required, unblock_kind. See W3 for the narrower ledger shape.
2. VERIFIED: taxonomy is census-derived and committed (06-CENSUS.md, 15 classes; WAIT_RESOURCE and CAPSULE_NOT_CERTIFIED have zero rows and are named in-code hold kinds, as the plan allows). UNKNOWN is a fall-through with owner_required true, independent_work false, reason `unclassified`. Mutant M-UNKNOWN-INDEPENDENT-style edit went red.
3. VERIFIED: `independent_work` is evidence-only. `plan_evidence` returns measured false for missing/unparseable ROADMAP/STATE or no current_phase; `_independent` returns False with unmeasured / no_other_unit / mission_wide / authority_exhausted. A candidate must lie after the blocked unit, be unchecked, with all dependencies checked off and none the blocked unit. grep shows no consumer reads the flag (only the writer, the status render at gsd_mission.py:7249 and the compiler), and the compiler has no launch call (V-S6-NO-NEW-LAUNCH-PATH green).
4. VERIFIED: set_owner_hold (line 1728) and _amr_boundary (line 2950) both build their hold through `annotate_hold`; V-S6-HOLD-PARKS-TYPED and the writer-discovery guard (planted-bypass control fired in my mutation run) cover it.
5. VERIFIED: `batch_foreseeable_decisions` is called from `arm` after `create` (arm_chain reaches it via `arm(launch=False)`); delta-only, one `owner_decisions_batched` row under session `arm-preflight`, one queue row `q-decisions-<key>`, fail-open with `owner_decisions_batch_failed`; answered items omitted with reasons. Idempotency gate and its mutants verified red.
6. VERIFIED: RESOLVE_BY_POLICY requires `category == "preference"`, not PROTECTED, a policy key and a policy source; the rule {key, source, fingerprint} is recorded. Outward categories (outward-facing, irreversible, resource-blocked) and PROTECTED keywords stay Owner. No capital/push/deploy/protection is ever resolved (FC-06). Autonomy gate is the classifier (no second one); AUTONOMY-AGREEMENT gate green.
7. VERIFIED: `CPP_BLOCKER_COMPILE=off` returns None from `_compile_blocker` (old call and row shape), skips batching and the preflight check; compiler faults fall back to UNKNOWN with compile_error and the BLOCKED write stands (fail-open mutant red). Consumer-tolerance gate green; all pre-plan suite counts held.
8. VERIFIED: every V-S6 gate has an entry in MUTANT_FOR checked by V-S6-MUTANT-MAP; drills require the mapped gate green on baseline, treat absent/crashing gates as red, and a no-op control requires all 34 drills to fail.

Requirements: FC-06 (no authority expansion), FC-08 (typed blocker on every BLOCKED, hold and AMR park), FC-10 (no new state, event dispatch or launch path; V-S6-FC10-NO-NEW-STATE green), FC-12 (incident entries in STATE.md, commit eaa3f426) are satisfied. D-05 narrowing (independent_work is information only) is a documented, accepted narrowing.

## Warnings (do not block; fix or accept before Phase 8)
- W1: **SUMMARY claim "decisions ... returns measured true, 0 items" is false at HEAD.** `python3 tools/blocker_compiler.py decisions --cwd . --workstream flow-compression` returns measured true with 1 item, OD-c8614770, from `STATE.md:46`. Commit eaa3f426 (the S6 incident entry) quotes the phrase `needs Owner authorization (name it)` and the words money/publish/credentials, so the ask-form marker and the autonomy classifier (resource-blocked) both match. The compiler therefore treats the documentation of its own filter as a foreseeable Owner decision; the next `arm` on this workstream would write one spurious Owner-queue row. No authority is widened (it fails toward the Owner), and no gate fails, because the negative-control gates read the old STATE line, not this paraphrase. Fix: reword STATE.md:46 to avoid the ask-form phrase, or exclude quoted/backticked/incident text in `foreseeable_decisions`; add a gate that runs the live compilation over this repository's own files.
- W2: **The compiler is not strictly pure as the plan specified.** `compile_blocker` accepts `cwd` and lazily calls `plan_evidence` (file reads) and `_autonomy` (module import), whereas the plan put the evidence read in the helper only. Output is deterministic for fixed files (V-S6-DETERMINISTIC green) and the tracer path is fail-open, so this is a spec deviation, not a defect.
- W3: **Ledger flat fields are narrower than the plan's Task 1 text.** The `mission_blocked` row carries blocker_class, independent_work, owner_required and `unblock_kind`; the full `unblock_condition` and `independent_reason` live only on the mission record (`blocker`). Phase 7 replay over the ledger alone cannot see why independent_work was false. Known conservative gap noted in the SUMMARY (the compiler ignores the `authorized` flag on a push) is real and fails toward the Owner.

## Pre-existing debt not ours, not repaired
V-AMCR-ONE-RESOLVER-INVENTORY (37/38) and V-MSPEND-HOLD-PLAN-NONE (44/45), unchanged from baseline.

## Not verified here
Phase close (`completed_phases`, `current_phase`, RESUMPTION_FILE.md) is orchestrator-owned and untouched. No push was made; GSD Core and the live install were not touched.
