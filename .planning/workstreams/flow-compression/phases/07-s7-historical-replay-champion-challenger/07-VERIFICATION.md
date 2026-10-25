---
phase: 07-s7-historical-replay-champion-challenger
verified: 2026-10-25T06:20:00Z
status: passed
score: "164/164 gates; 8/8 plan truths; 2/2 roadmap criteria"
---

# Phase 7 verification - PASSED (5 warnings recorded, none blocks the goal)

Verifier re-ran everything itself (CPP_RESOURCE_ADMISSION=off) at HEAD 25dca5f5 and read tools/flow_replay.py directly. SUMMARY and STATE.md statements were not used as evidence. Three of them did not survive (W1, W2, W3).

## Gates re-run
- `python3 tools/test_s7_replay.py`: S7_PASS=164/164 (exit 0, about 170 s). 83 behaviour/control gates, 78 mutation drills, V-S7-DRILL-CONTROL-NOOP-FIRES, V-S7-DRILL-REAL-FILE-UNTOUCHED, V-S7-MUTANT-MAP (unmutated: V-S7-HELD-RESTORED, V-S7-READONLY-COPY-IDENTICAL, both declared).
- Regression, all foreground: test_s6_blockers 72/72; test_s5_reconcile 44/44 (needs more than 100 s); test_gsd_epoch 111/111; test_rotation_invariant 17/17; test_arm_preflight 16/16; test_s3_admission 11/11; test_s4_lease 14/14; test_gsd_mission 234/234; test_mission_spend 44/45 (V-MSPEND-HOLD-PLAN-NONE) and test_mission_continuity 37/38 (V-AMCR-ONE-RESOLVER-INVENTORY), both pre-existing and unchanged.
- Report reproduced: `flow_replay.py report --mutants` to a temp path exits 0, 266 incidents, and every report section's `data` is byte-equal to the committed 07-REPLAY.json (only the command tag differs).
- Independent mutations on the real source (edit, run full suite, `git checkout --`; tree clean afterwards):

| Mutation | Result |
|---|---|
| `verdict()` returns PREVENTED where it returns UNMEASURED | 142/164, 22 red: V-S7-UNMEASURED-NOT-PREVENTED, UNMEASURED-REACHABLE-REAL, REPORT-UNMEASURED-APART, ALL-FIVE-REAL, S1-EFFECT-UNMEASURED, RECORD-DRIFT-UNMEASURED, ... |
| `run_status` ignores `challenger_breaches` (FC-06 soft) | 160/164: V-S7-FC06-HARD-FAIL, two FC06 drills, NOOP-FIRES |

## Isolation and scope
- Host: OWNER_QUEUE.jsonl sha256 prefix 2c03045bfb579004 before and after every run. The ledger grows (live) but the pinned prefix still hashes to the pin (b47ff018..., 6339 rows, 1740294 bytes); the harness reads exactly the pinned byte count. The only host mission record that differs from the pin, gsd-mission-m-3d5f0a27e41d.json, is the RUNNING record of this very mission, rewritten by its supervisor (ledger row at 05:53:38Z), not by the harness; the replay marks it UNMEASURED record_changed_since_pin.
- Harness write sites: the pin file, the --json/--md report paths, and seeded-scenario files inside the harness sandbox. No ledger, queue or record writer.
- `git diff 98fddd3b..HEAD` outside `.planning` is exactly two new files, tools/flow_replay.py and tools/test_s7_replay.py. No GSD Core file, no gsd_mission.py edit (FC-10).
- Every CPP_ token in flow_replay.py already existed in tools/ at phase 6; no new switch (D-02). Champion = six S1-S6 switches off, challenger = on, HELD group (CCR admission observe, renew on, bounded renewal shadow) equal in both arms.

## Roadmap criteria and plan truths
1. VERIFIED (criterion 1): replay over the ledger goes through real seams: gsd_mission.plan_next (classify_gap), the S2/S3 hold backoff, mission_reconcile.dispose, mission_spend judge, blocker_compiler, apply_rotation_invariant, renewal_refusal. Mutant stubs record call counts (stub_calls non-zero for all six), so the seams are exercised. Champion differs from challenger on real incidents: PREVENTED 2 (S3 relay_held 54 -> 12, one S4), MOVED_EARLIER 1 (S2, 1127 s).
2. VERIFIED (criterion 2): time and idle are reported (see W1, W4 for caveats). Three numbers are separate and defined in the report: summed 27483.911 h, wall-clock 715.125 h, critical path 516.808 h. Avoidable idle before and after both 1.353 h, no gap moved, labelled "a challenger figure for a gap no seam recomputed is the champion figure, not a measured gain".
3. VERIFIED: mutants fail. Six mutants (always-admit, never-rotate, always-renew, terminal-without-proof, drop-blocker-class, expand-authority) are all `caught`, none `harness_defect`; terminal-without-proof is caught on the seeded set only (host differing 0), as the summary says and the report records. My two source mutations above went red.
4. VERIFIED: UNMEASURED is a closed-set verdict kept apart: 125+121+2+1 measured, 17 apart, sum 266. Arithmetic recomputed from the JSON; the first mutation shows the gates catch UNMEASURED leaking into PREVENTED.
5. VERIFIED: FC-06 challenger breaches = 0 on 266 host incidents and 19 seeded scenarios; each assertion has a self-test where the breach fires and the clean case stays quiet (all four true); each assertion breaches under at least one mutant (16 for drop-blocker-class). See W4 for what the zero covers.
6. VERIFIED: S8 sentence present in 07-REPLAY.md: "S8 unmeasured: no recorded independent_work values exist yet; S8 stays dormant for lack of evidence. 55 pre-S6 mission_blocked rows are unmeasured." plus W2/W3 independence statement. Recomputed from the pin: 55 mission_blocked rows, none carrying independent_work.
7. VERIFIED: pin and report arithmetic: coverage 588 mapped + 2812 unmapped = 3400; idle gaps 22+36+8 = 66; census cross-check 55 = 55.
8. VERIFIED: every gate has a MUTANT_FOR entry or a stated exemption; NOOP control fires.

Requirements: FC-01 (idle measured, with limits W2), FC-06 (assertions, zero breaches, hard-fail exit 3), FC-09 (champion/challenger with mutants that go red), FC-10 (no Core change, no new state or switch), FC-11 (three numbers separated; see W1), FC-12 (incident entries in STATE.md lines 70-89) are satisfied.

## Executor-flagged discrepancies, resolved
- (a) 215 versus 266: STATE.md's stated root cause (module-level gsd_mission import binding the empty temp tree) is wrong. The 215 comes from `gate_pin` in the test: it builds its own pin over `copy_host(base, records=[], queue=False)`, a copy with no mission records, then calls `fr.main(["replay","--pin",...])`, which prints incidents=215 (test output line 2). With no records the S5 slice (51 incidents) is empty; 266 - 51 = 215. The full replay used by the other gates and by the CLI is 266: reproduced in-process with the test's environment variables and a prior `import gsd_mission` (266, S5 51). Benign test scaffolding, no host leak.
- (b) idle figures: the committed report (66 gaps, 22 avoidable, 1.353 h) is the reproducible one. It reproduces from the pin with the code at 9bf8cd9a (the 07-01 commit) and at HEAD. The 07-01-SUMMARY figures (7 avoidable, 0.728 h, 23 unmeasured 1.276 h) are what you get by counting only the 7 `replace` (start ack overdue) gaps (0.727 h) as avoidable and leaving the 15 `launch` (prepared, nothing launched; 0.625 h) plus 8 incomplete (0.651 h) as unmeasured: 0.625 + 0.651 = 1.276. The summary was written from an earlier classifier state; no code history explains it. The report's headline claims are mutually consistent (66 = 22+36+8; before = after = 1.353; moved = []).

## Warnings (do not block; fix or accept before Phase 8 relies on them)
- W1: **The summed mission-hours headline is about 94 percent unobserved time.** 27483.911 h counts every mission with no terminal row as running until the end of the pin. 92 of 148 missions are "open at pin"; they contribute 26706 h, 86 of them have no ledger row for more than 24 h, and 25832 h of the total lies after each open mission's last row. Closed missions contribute 777.6 h; open missions bounded at their last row would add about 874 h (about 1650 h total). 27484 h against 715 h of wall-clock implies 38x concurrency, which is not what happened. The open count is disclosed in the report, so FC-11's separation holds, but the figure should be shown as an upper bound or split (closed / open-to-last-row / open-assumed-running) before it is quoted. D-07 says missing interval evidence is unmeasured, never an assumed value; here it is assumed running.
- W2: **Avoidable idle is generous and inferred.** Gap start is the mission's last row; no worker-end row exists. 15 of the 22 avoidable gaps are arm-to-first-launch latency (plan_next "prepared, nothing launched") and 7 are "start ack overdue" timers (about 4 min each; four of them belong to m-5f627f3869ac) that fire immediately because the rebuilt record carries no start evidence. 34 of 36 legitimate gaps are legitimate only because plan_next answers none for a host-backgrounded owner. The report states basis "inferred" and that after = before; the S2-removal path never fired (moved = []). FC-01 is therefore reported, not shown improved.
- W3: **Two summary/STATE claims are false.** (i) 07-01-SUMMARY avoidable idle 7 / 0.728 h; (ii) STATE.md line 82 root cause for 215 versus 266 (see above). 07-02-SUMMARY says "cause not isolated" for (b) and "import-order cause" for (a); both are now isolated. STATE.md should be corrected before it is quoted to Phase 8.
- W4: **FC-06 zero is partly vacuous on host data.** On the 266 host incidents done_proof and packet_digest are not_applicable for all 266 (0 clear); only capital_ceiling (7 clear) and protections (111 clear) have host evidence. The remaining coverage is the 19 seeded scenarios (2 clear each). The zero is honest and the assertions fire in self-tests and under mutants, but "0 breaches on 266 host incidents" does not mean done-proof and digest were exercised by real history.
- W5: **Coverage is narrow.** 588 of 3400 failure-class rows map to S1-S6; 2812 are unmapped (provider waits, supervise_error), 41 unmapped loops carried to Phase 8. All 13 S1 verdicts are UNMEASURED (no size evidence), S5 is UNCHANGED by construction (annotation only), and all renewal-axis halts are UNMEASURED. Only 3 incidents of 266 show a measured change (2 PREVENTED, 1 MOVED_EARLIER).

## Pre-existing debt not ours, not repaired
V-AMCR-ONE-RESOLVER-INVENTORY (37/38), V-MSPEND-HOLD-PLAN-NONE (44/45), Phase 6 W2 (compile_blocker not strictly pure) and W3 (ledger row lacks unblock_condition). The replay calls compile_blocker with cwd=None and does not depend on W2 or W3.

## Not verified here
Phase close (`completed_phases`, `current_phase`, ROADMAP checkbox, RESUMPTION_FILE.md) is orchestrator-owned and untouched. No push was made. Real-hardware or live-host behaviour of the challenger policy is out of scope: this is a replay of recorded history.
