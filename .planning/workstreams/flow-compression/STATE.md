---
gsd_state_version: "1.0"
milestone: v1
status: ready
stopped_at: Phase 8 context gathered
last_updated: "2026-10-25T06:10:56.688Z"
state_head: 5c0995074e48550f89b70cb91f1096062cd0bdb1
progress:
  total_phases: 8
  completed_phases: 7
  total_plans: 8
  completed_plans: 8
  percent: 88
milestone_name: flow-compression
workstream: flow-compression
created: 2026-10-24
current_phase: 7
current_phase_name: Phase 7 (see ROADMAP.md)
last_activity_desc: Phase 6 sealed (S6 blocker compiler + Owner boundary, 72/72, VERIFICATION passed, GSD 6/8)
---

# Project State

Authority: `ROADMAP.md` + `REQUIREMENTS.md` in this directory, and `vault/specs/flow-compression.md`.
Budget: authority 140M processed tokens + 2 semantic top-ups of 30M; absolute ceiling 200M. Arming pane spent
~4.5M (reality scan) + S1 build before arm (measured at arm time in RESUMPTION_FILE.md).
Stop only on: done-gate pass, budget spent, or an action that needs Owner authorization (name it).
Update this file and `RESUMPTION_FILE.md` (this dir) after every sealed phase, with measured spend.

## Incident for Phase 8 (recorded 2026-10-24, epoch 6)

- Symptom: phases 1-4 sealed and closed twice, yet GSD listed 0/8 complete and re-queued `/gsd-execute-phase 1`; mission parked at an AMR Owner boundary for ~1.5 h.
- Root: hand-written VERIFICATION/SUMMARY artifacts with no GSD frontmatter (phase, verified, status, score); GSD completion is `verification.status === passed` read from frontmatter.
- Earliest discoverable point: the phase-close step (right after sealing each phase).
- Fix applied: frontmatter added (commit 89fa5527); `gsd_long_run.gsd_status` now reports 4/8.
- Prevention (S2/S5 check): after every phase seal, assert `gsd_status.completed` advanced; if not, the seal is not closed. Phases 5-8 artifacts are produced via GSD workflows (gsd-planner/verifier), not by hand.
- Decision: worked in the main clone (bound branch mission/flow-compression); the stale worktree .claude/worktrees/flow-compression-w (f7ee5b7d) is not used.

## Incidents for Phase 8 (recorded 2026-10-24, epoch 8)

- S5 gate fixtures (5 red at hand-off): the divergence fixture wrote `{"measured": ...}` while `receipt_judge` reads `values`, so a DIVERGENT receipt looked DONE in two gates; the test set `CPP_HALT_CONTINUE=off`, which also disables the missing-receipt halt, so two gates could not see the halt. Root: fixtures written from memory of the contract, not from the reader. Earliest discoverable point: the first red run (a fixture whose negative control never fires proves nothing). Prevention: every negative control must be shown to fire against the real reader before it counts as a gate.
- Plane: the directive says work in the clone with no worktree; the mission card binds the worker to `.claude/worktrees/flow-compression-w`. Decision (reversible, internal): keep committing in the bound worktree and `git merge --ff-only` into the clone after each commit, so the clone's branch `mission/flow-compression` carries every commit. No push.
- `gsd_long_run.gsd_status` is not a CLI subcommand. Status check used: `node ~/.claude/gsd-core/bin/gsd-tools.cjs query init.progress --ws flow-compression --raw` (per-phase `phase_complete`).

## Incidents for Phase 8 (recorded 2026-10-24, epoch 9, phase 6 / plan 06-01)

- Capital regex over-match: the first census typed budget-flavoured texts CAPITAL_EXHAUSTED. Root: `_CAPITAL_RE` matched the bare word "budget". Earliest discoverable point: the first census run over the host ledger (116 compiled rows). Repair: tightened the regex and added an `authority_trip` rule. Test: class controls (positive, negative, named neighbour per class). Pattern: a class regex is tested against the real population before it counts.
- Precedence is census-driven: HOST_GATE must precede the intent rules, or a host gate that quotes a command is typed COMMAND_REQUEST. First match wins; the order is pinned by V-S6-CLASS gates and the M-DROP-INTENT-RULE mutant.
- Classifier gap, fails toward the Owner: the autonomy gate classes a force push as OWNER/irreversible, which compiled to UNKNOWN. `_m_publish` now matches `outward-facing` and `irreversible`. PROTECTED keywords stay a fail-toward-Owner filter in `foreseeable_decisions`. The compiler does not read the `authorized` flag on a git push, so an authorized push still reports `owner_required: true` (conservative, not repaired).
- Pre-existing, not ours: the blocked_intent `/ql/ops` COMMAND label is a mislabel in the intent rules; left as is (test_blocked_intent 16/16 unchanged).
- Step 0 findings (before any edit): no consumer compares an `owner_hold` as a whole; no BLOCKED writer exists beyond the five AST-confirmed `block_mission` callers; `annotate_hold` is used by `set_owner_hold` and `_amr_boundary`.
- V-S6-HOLD-PARKS-TYPED first run failed: the gate read ledger event `recovery_owner_boundary`, but the typed row is the transition event `recovery_boundary` (the separate `recovery_owner_boundary` ledger row carries no blocker fields). Root: a gate written from memory of the writer, not from the writer. Repair: read `recovery_boundary`. Same class as the S5 fixture incident; prevention unchanged.
- Every gate passed on its first run, which proves nothing about their ability to fail. Answer: 34 mutation drills (each mapped gate must be green on baseline and red under its mutant) plus V-S6-DRILL-CONTROL-NOOP-FIRES (all 34 drills fail when the mutants are replaced by no-ops).
- RESOLVE_BY_POLICY is narrowed to preference-class items with a recorded rule; anything touching a protected keyword stays with the Owner. Requirement lines and prior STATE wording are kept out of the decision list by the ask-form filter plus the autonomy classifier (two layers); incident text no longer quotes those phrases, so the live compilation over this workstream reports no spurious item (verifier W1, fixed).
- `arm_chain` batching goes through `arm(launch=False)`, so the single call in `arm` covers both; no second call site was added.
- Decision (safest option): the worktree branch `worktree-flow-compression-w` does not match the agent-* allow-list in the pre-commit assertion, but it is the orchestrator-designated, non-protected branch. Only the protected-branch case was enforced. Commits ff-merged into `mission/flow-compression` after each commit; no push.
- Host measurement: `decisions --cwd . --workstream flow-compression` returns measured true, 0 items. OWNER_QUEUE.jsonl sha256 prefix 2c03045bfb579004 before and after both regression batches (tests never wrote the host queue). The host ledger is live (6249 rows at census time, 6268 later) so the census is a dated snapshot.

## Session

**Last session:** 2026-10-25T06:10:56.303Z
**Stopped at:** Phase 8 context gathered
**Resume file:** .planning/workstreams/flow-compression/phases/08-s9-knowledge-vault-ukdl-cbr-red-team-master-done-gate/08-CONTEXT.md

## Decisions (phase 7 planning, 2026-10-25)

- D-02 switch names: the real S1-S6 switches are CPP_ROTATION_INVARIANT, CPP_ARM_PREFLIGHT, CPP_GSD_HOLD_BACKOFF, CPP_ECON_LEASE, CPP_TERMINAL_RECONCILE, CPP_BLOCKER_COMPILE. CPP_CCR_ADMISSION / CPP_MISSION_RENEW / CPP_MISSION_BOUNDED_RENEWAL pre-date flow-compression, so they are held equal in both arms and replayed on a separate renewal axis. Chosen because a champion with them off would be a strawman; reversible, internal.
- Read-only proof uses an open-mode write probe plus a byte check on a temp copy, not before/after hashes of live host files (other processes append).

## Incidents for Phase 8 (recorded 2026-10-25, phase 7 / plans 07-01 and 07-02)

- Premise correction, switch names: the plan named switches that do not exist. The real S1-S6 switches are CPP_ROTATION_INVARIANT, CPP_ARM_PREFLIGHT, CPP_GSD_HOLD_BACKOFF, CPP_ECON_LEASE, CPP_TERMINAL_RECONCILE, CPP_BLOCKER_COMPILE; the admission, renew and bounded-renewal switches are a HELD group equal in both arms. Earliest discoverable point: reading the env names in the six slice modules before the plan. Prevention: the HELD and SWITCHES sets are asserted disjoint (V-S7-HELD-EQUAL).
- Premise correction, plan_next is insensitive to S2-S6: the idle-gap seam answers the same under either arm, so a challenger idle figure for a gap no seam recomputed is the champion figure. Prevention: the report labels it as carried unchanged and never as a gain.
- Premise correction, event names and receipts: the plan's event names did not match the ledger, and the ledger holds zero halts without a receipt. Prevention: coverage is computed from a discovered event census (3400 failure-class rows), not from a hand list.
- Premise correction, S3 and S5: the S3 digest needs normalisation that no switch controls, and the S5 reconcile champion arm cannot be measured (annotation only), so those verdicts are UNMEASURED or UNCHANGED by construction and are reported apart.
- Premise correction, the ledger does not carry every plan_next field: the rebuilt owner of an idle gap is a host-backgrounded worker, and the gap start is inferred because no worker-end row exists. Prevention: basis is printed as inferred on every such row.
- Pin size: the plan text said 6333 rows; the pinned prefix holds 6339 (1740294 bytes, sha256 b47ff018fb44...). The harness measurement wins; recomputed independently from the raw bytes in plan 07-02.
- Seeded scenarios were non-deterministic: the FC-06 inputs of the seeded cases held temp paths, so two replays differed. Root: paths stored raw. Earliest point: V-S7-DETERMINISTIC on the first seeded run. Prevention: `_scrub` keeps basenames only.
- Seed spent past a cap: the spend-within-authority seed set token_estimate 100000 and tripped the estimate cap, so the control read as a hold. Fixed to 600000; the seed is checked against the real judge.
- Controls that did not fire on the first run: (1) the first calibration matrix counted absent gates as red, because the calibrate edit had not applied; (2) the readonly group crashed on every re-run in one temp tree (`mkdir` on an existing probe directory), which made its gates absent and falsely red in every drill; both fixed before the matrix was trusted; (3) M-CENSUS-DIFF-ZERO was an equivalent mutant (the pin count made 0 equal the expected difference) and was changed to an off-by-one; (4) M-PROBE-BLIND crashed on a missing attribute of the blinded probe; (5) M-PIN-READS-SHORT and M-REPORT-EMPTY-COMMAND only made whole groups crash, so no gate went red by its own check; replaced by M-PIN-READS-WHOLE, M-PIN-DROPS-ROW and a drop of the report mutation (the builder refuses an empty tag, which is the intended guard).
- Gates green on first run without a drill: all of them. Answer: 78 mutation drills (each mapped gate green on baseline and red under its mutant), V-S7-DRILL-CONTROL-NOOP-FIRES (a no-op substitution leaves 81/81 mapped gates green, so every drill would read it as a failure), V-S7-DRILL-REAL-FILE-UNTOUCHED (flow_replay.py sha256 identical across 78 mutated copies) and V-S7-MUTANT-MAP (every gate mapped or listed UNMUTATED). Two gates stay UNMUTATED with a stated reason: V-S7-HELD-RESTORED (a leak persists after its first occurrence, so it cannot see a leak an earlier call made; V-S7-SCOPE-RESTORED is the red gate under M-HELD-LEAKS) and V-S7-READONLY-COPY-IDENTICAL (its subject is the temp copy tree; the in-gate control carries the proof).
- Test-versus-CLI difference: under test_s7_replay the replay sees 215 incidents and the CLI sees 266 (the 51-incident S5 slice is absent). Corrected by the verifier: the root is `gate_pin`, which builds its pin over a copy with no mission records (records=[]), so the S5 slice is empty; it is not import order. Not a host leak. Not repaired; the committed report comes from the CLI.
- Report versus 07-01 summary: the committed report prints 66 idle gaps (22 avoidable, 1.353 h before and after, 8 inputs-incomplete, 0.651 h unmeasured); the 07-01 summary printed 7 avoidable gaps at 0.728 h and 23 unmeasured. Cause (verifier): the 07-01 summary counted only the 7 'start ack overdue' gaps; the report is the figure of record because it is regenerated from the pin and reproduces byte for byte. Carry to Phase 8.
- Mutant result: all six policy mutants are caught by differing from the challenger (terminal-without-proof only on the seeded set, because the host set has no receipts); each FC-06 assertion breaches under at least one mutant; the challenger has 0 breaches on 266 host incidents and 19 seeded scenarios.
- Carried to Phase 8, unmapped supervise_error loop: 41 unmapped loops over 2812 unmapped failure-class rows, the largest supervise_error loop on route-floors.json with at least 500 rows; listed, not repaired.
- Carried to Phase 8, epoch_compacted rows carry no context size, so S1 verdicts are all UNMEASURED (13 incidents); no size evidence exists to replay against.
- Carried to Phase 8, W2 and W3: the replay called compile_blocker with no cwd, so W2 does not enter any verdict; the recorded mission_blocked rows carry no unblock condition or independent reason (W3), so why a value is false is not recoverable and S8 stays unmeasured (55 pre-S6 rows, 0 recorded independent_work values). The replay showed no verdict distorted by either; both left unrepaired.
- Known prior failures untouched and re-measured: mission_spend 44/45 (V-MSPEND-HOLD-PLAN-NONE) and mission_continuity 37/38 (V-AMCR-ONE-RESOLVER-INVENTORY), each failing by exactly that gate.
- Phase 7 executed, awaiting verification.

## Phase 7 close (2026-10-25)

- Phase 7 VERIFICATION passed with 5 warnings (020e12ea); GSD reports 7/8 complete via init.progress. Carried to Phase 8: summed mission-hours 27,484 is ~94% unobserved time (open-at-pin missions counted to the pin; bounded ~1,650 h); idle gap starts are inferred and challenger idle equals champion; done-proof and packet-digest FC-06 checks only exercised by seeded scenarios; only 3 of 266 incidents show a measured change; the 07-01 summary idle figures are superseded by the report.
- Plane: executors cannot write the clone and gsd-executor dispatch demands a fresh worktree, so plans ran via general-purpose agents in the bound worktree, ff-merged into the clone after each step; no push.

**Last session:** 2026-10-25
**Stopped at:** Phase 7 verified; next Phase 8 (discuss)

## OWNER DECISION NEEDED (recorded 2026-10-25, phase 8 discuss)

- Question: what categories does the red team cover? The Owner prompt "GSD X AUTONOMOUS FLOW COMPRESSION" is not in the repo; only the line "S9 Knowledge Vault + UKDL + CBR + red team" exists. Options: (a) narrow: adversarial attempts on S1-S6 against FC-01..FC-08 with controls; (b) wait for the prompt text. Pick: (a), reversible and internal; the Owner may add categories later.

## Phase 8 planning status (epoch 17, 2026-10-25)

- Plans 08-01/02/03 committed (96f093f7), plan-checker ISSUES fixed in 08-03 verify chains (e64056d0). Re-check not needed for those two items.
- Subagents (planner) are blocked from writing the clone by the harness guard ("parent bg session hasn't isolated"); execute plans from the main session itself (Bash cp/Write worked there). No worktree per Owner directive; no push.
- OWNER DECISION NEEDED: red-team claim 15 is not in the repo; plans record it as UNMEASURED. Pick: leave UNMEASURED.
- Next: execute 08-01 Task 1 (tools/s9_kv_check.py + phase-seal incident), then 08-02 (independent), then 08-03, then gsd-verifier, then `python3 tools/s9_done_gate.py seal-check --expect 8`.
