# Phase 8 master gate report (flow-compression S9)

Verdict: **NOT_DONE**

Rendered from 08-DONE-GATE.json by `python3 tools/s9_done_gate.py report`; never edited by hand.

## Causes

- suite test_cpp_gsd_long_routing red: ["red outside the known set: ['V-ROUTE-LIVE-COMMAND-IS-REPO-COMMAND']"]

## Statement on the one red suite

test_cpp_gsd_long_routing is red outside the known set on this host: V-ROUTE-LIVE-COMMAND-IS-REPO-COMMAND finds no cpp-gsd-long.md under the HOME the test builds (its own message: 'sync with Copy-Item if red'). The other 8 gates of that suite pass. This is a host-installation check, not a repo defect; it is recorded as a cause because the known-red set is closed.

## Gates

- FAIL V-S9-ACCEPTANCE: ['test_cpp_gsd_long_routing'] not PASS
- PASS V-S9-BREACH-INCIDENT-IFF: breaches [8, 12] file True sections [8, 12]
- PASS V-S9-CORE-UNCHANGED: gsd-core paths changed since 7edba723: []
- PASS V-S9-FC-TABLE: FC-01=MET FC-02=MET_WITH_UNMEASURED FC-03=MET_WITH_UNMEASURED FC-04=MET_WITH_UNMEASURED FC-05=MET_WITH_UNMEASURED FC-06=MET FC-07=MET FC-08=MET FC-09=MET_WITH_UNMEASURED FC-10=MET FC-11=MET FC-12=MET
- PASS V-S9-FRONTMATTER: 28 files, bad [], pending ['08-VERIFICATION.md']
- PASS V-S9-INCIDENTS: 9 files, findings []
- PASS V-S9-MILESTONES: S1=MET_WITH_UNMEASURED S2=MET_WITH_UNMEASURED S3=MET_WITH_UNMEASURED S4=MET_WITH_UNMEASURED S5=MET_WITH_UNMEASURED S6=MET S7=MET_WITH_UNMEASURED
- PASS V-S9-PREDICATE-AGREE: spec False red team False
- PASS V-S9-REDTEAM: blob_equals_file=True claims=15 claim15=UNMEASURED
- PASS V-S9-SPEC-PREDICATE: findings []
- FAIL V-S9-SUITES: 17/18 suites PASS, red ['test_cpp_gsd_long_routing'], inconclusive []
- PASS V-S9-UKDL: findings []
- PASS V-S9-VERDICT: NOT_DONE

## Suites

- PASS test_arm_preflight total=18
- PASS test_blocked_intent total=16
- FAIL test_cpp_gsd_long_routing total=9
- PASS test_gsd_epoch total=111
- PASS test_gsd_mission total=234
- PASS test_gsd_mission_baseline total=21
- PASS test_mission_continuity total=38
- PASS test_mission_recovery total=69
- PASS test_mission_spend total=46
- PASS test_mission_steward total=27
- PASS test_owner_boundary_delivery total=14
- PASS test_rotation_invariant total=17
- PASS test_s3_admission total=11
- PASS test_s4_lease total=14
- PASS test_s5_reconcile total=44
- PASS test_s6_blockers total=72
- PASS test_s7_replay total=164
- PASS test_s9_redteam total=112

## Milestones S1-S7

- S1: MET_WITH_UNMEASURED
- S2: MET_WITH_UNMEASURED
- S3: MET_WITH_UNMEASURED
- S4: MET_WITH_UNMEASURED
- S5: MET_WITH_UNMEASURED
- S6: MET
- S7: MET_WITH_UNMEASURED

## FC-01..FC-12

- FC-01: MET
- FC-02: MET_WITH_UNMEASURED
- FC-03: MET_WITH_UNMEASURED
- FC-04: MET_WITH_UNMEASURED
- FC-05: MET_WITH_UNMEASURED
- FC-06: MET
- FC-07: MET
- FC-08: MET
- FC-09: MET_WITH_UNMEASURED
- FC-10: MET
- FC-11: MET
- FC-12: MET

## Residuals

- claim 8 BREACH
- claim 12 BREACH
- claim 1 UNMEASURED
- claim 2 UNMEASURED
- claim 3 UNMEASURED
- claim 5 UNMEASURED
- claim 15 UNMEASURED
- milestone S1 MET_WITH_UNMEASURED
- milestone S2 MET_WITH_UNMEASURED
- milestone S3 MET_WITH_UNMEASURED
- milestone S4 MET_WITH_UNMEASURED
- milestone S5 MET_WITH_UNMEASURED
- milestone S7 MET_WITH_UNMEASURED
- 4 legacy PLAN files carry no frontmatter: ['01-01-PLAN.md', '02-01-PLAN.md', '03-01-PLAN.md', '04-01-PLAN.md']
- LAPTOP-ONLY: S3 DEFER autopsy
- LAPTOP-ONLY: S5 149 h disposal on the laptop ledger
- LAPTOP-ONLY: live laptop hooks and settings
- LAPTOP-ONLY: the laptop gsd-core
- known red V-AMCR-ONE-RESOLVER-INVENTORY

## Residuals cited verbatim

> [07-VERIFICATION.md] - W1: **The summed mission-hours headline is about 94 percent unobserved time.** 27483.911 h counts every mission with no terminal row as running until the end of the pin. 92 of 148 missions are "open at pin"; they contribute 26706 h, 86 of them have no ledger row for more than 24 h, and 25832 h of the total lies after each open mission's last row. Closed missions contribute 777.6 h; open missions bounded at their last row would add about 874 h (about 1650 h total). 27484 h against 715 h of wall-clock implies 38x concurrency, which is not what happened. The open count is disclosed in the report, so FC-11's separation holds, but the figure should be shown as an upper bound or split (closed / open-to-last-row / open-assumed-running) before it is quoted. D-07 says missing interval evidence is unmeasured, never an assumed value; here it is assumed running.
> [07-VERIFICATION.md] - W2: **Avoidable idle is generous and inferred.** Gap start is the mission's last row; no worker-end row exists. 15 of the 22 avoidable gaps are arm-to-first-launch latency (plan_next "prepared, nothing launched") and 7 are "start ack overdue" timers (about 4 min each; four of them belong to m-5f627f3869ac) that fire immediately because the rebuilt record carries no start evidence. 34 of 36 legitimate gaps are legitimate only because plan_next answers none for a host-backgrounded owner. The report states basis "inferred" and that after = before; the S2-removal path never fired (moved = []). FC-01 is therefore reported, not shown improved.
> [07-VERIFICATION.md] - W3: **Two summary/STATE claims are false.** (i) 07-01-SUMMARY avoidable idle 7 / 0.728 h; (ii) STATE.md line 82 root cause for 215 versus 266 (see above). 07-02-SUMMARY says "cause not isolated" for (b) and "import-order cause" for (a); both are now isolated. STATE.md should be corrected before it is quoted to Phase 8.
> [07-VERIFICATION.md] - W4: **FC-06 zero is partly vacuous on host data.** On the 266 host incidents done_proof and packet_digest are not_applicable for all 266 (0 clear); only capital_ceiling (7 clear) and protections (111 clear) have host evidence. The remaining coverage is the 19 seeded scenarios (2 clear each). The zero is honest and the assertions fire in self-tests and under mutants, but "0 breaches on 266 host incidents" does not mean done-proof and digest were exercised by real history.
> [07-VERIFICATION.md] - W5: **Coverage is narrow.** 588 of 3400 failure-class rows map to S1-S6; 2812 are unmapped (provider waits, supervise_error), 41 unmapped loops carried to Phase 8. All 13 S1 verdicts are UNMEASURED (no size evidence), S5 is UNCHANGED by construction (annotation only), and all renewal-axis halts are UNMEASURED. Only 3 incidents of 266 show a measured change (2 PREVENTED, 1 MOVED_EARLIER).
> [STATE.md] - Carried to Phase 8, epoch_compacted rows carry no context size, so S1 verdicts are all UNMEASURED (13 incidents); no size evidence exists to replay against.
> [STATE.md] - Carried to Phase 8, W2 and W3: the replay called compile_blocker with no cwd, so W2 does not enter any verdict; the recorded mission_blocked rows carry no unblock condition or independent reason (W3), so why a value is false is not recoverable and S8 stays unmeasured (55 pre-S6 rows, 0 recorded independent_work values). The replay showed no verdict distorted by either; both left unrepaired.
