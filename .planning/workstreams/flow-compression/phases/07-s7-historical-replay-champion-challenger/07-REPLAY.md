# S7 replay report

Command: `python3 tools/flow_replay.py report --pin .planning/workstreams/flow-compression/phases/07-s7-historical-replay-champion-challenger/07-PIN.json --json .planning/workstreams/flow-compression/phases/07-s7-historical-replay-champion-challenger/07-REPLAY.json --md .planning/workstreams/flow-compression/phases/07-s7-historical-replay-champion-challenger/07-REPLAY.md --mutants`
Pin sha256: `b47ff018fb44766fb9e2add7b9e23276c18dc6c2ec84cb88d4709c82d95e2743`

## Verdicts (UNMEASURED shown beside, never inside)

- PREVENTED: 2
- MOVED_EARLIER: 1
- LEGITIMATE_STOP: 125
- UNCHANGED: 121
- UNMEASURED (apart): 17

## Coverage

failure-class rows 3400; mapped to S1-S6 588; unmapped 2812; unmapped loops 41 (carried to Phase 8)

## Time (three separate numbers)

- summed_mission_hours: {'basis': 'open missions end at their last row; the unobserved tail is not part of hours', 'hours': 1651.959, 'left_out': [], 'missions': 148, 'open_at_pin': 92, 'open_hours_bounded_at_last_row': 874.328, 'unobserved_tail_hours': 25831.952}
- wall_clock_hours: {'hours': 715.125, 'from': '2026-09-25T09:52:05+00:00', 'to': '2026-10-25T04:59:35+00:00'}
- critical_path_wall_clock_hours: {'hours': 323.921, 'chain': ['m-f011d7fdebc9'], 'unmeasured': [], 'basis': 'ledger_lineage', 'chain_len': 1}
- phase 9 note (claim 12): this Time section was regenerated; open missions end at their last row and the unobserved tail is reported beside hours (see summed_mission_hours). Other sections are the phase-7 output as committed.
- definitions: {'summed_mission_hours': 'sum over missions of (end - start); concurrent missions add', 'wall_clock_hours': 'first launch to last row of the window as one interval', 'critical_path_wall_clock_hours': 'longest successor chain, head start to tail end, gaps included'}

## Avoidable idle

{'gaps': 66, 'by_class': {'avoidable': 22, 'legitimate': 36, 'inputs_incomplete': 8}, 'avoidable_h_before': 1.353, 'avoidable_h_after': 1.353, 'legitimate_h': 12.759, 'unmeasured_h': 0.651, 'moved': [], 'carried_unchanged': 66, 'basis': "inferred: gap start is the mission's last row before the next launch (no worker-end row exists); the owner is rebuilt as a host-backgrounded worker, which plan_next leaves to the host (UNKNOWN -> none)", 'note': 'a challenger figure for a gap no seam recomputed is the champion figure, not a measured gain'}

## S8

S8 unmeasured: no recorded independent_work values exist yet; S8 stays dormant for lack of evidence. 55 pre-S6 mission_blocked rows are unmeasured. W3: the recorded mission_blocked row carries no unblock_condition/independent_reason, so why a value is false is not recoverable; the replay does not need it. The replay does not depend on W2 (compile_blocker is called with cwd=None).

## Held group

{'CPP_CCR_ADMISSION': 'observe', 'CPP_MISSION_RENEW': 'on', 'CPP_MISSION_BOUNDED_RENEWAL': 'shadow'}

## Incidents

| slice | kind | mission | champion | challenger | verdict | basis | delta_s |
|---|---|---|---|---|---|---|---|
| S5 | terminal_reconcile | m-032c87418a2e | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-0729ac737bec | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-084b5ee34a78 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-0b72311a0676 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-0e839e9d581a | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-16bde3ea1101 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-1c22d15ee4ff | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-1fb7263df86b | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-23ae5b4a7113 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-260aa89142c8 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-2a029bc2117d | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-32b2dd69eae1 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-33ad663fd7dc | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-3964901ac30d | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-3d5f0a27e41d | None | None | UNMEASURED | unmeasured | None |
| S5 | terminal_reconcile | m-3d8e5c151705 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-3fa466eb6cc8 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-51b4175db047 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-5ddc61864481 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-5f627f3869ac | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-604666a514a3 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-75d9c9944f13 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-7a8e9ac0b451 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-7e268fc1a6d9 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-7fb90e8735d4 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-80fd126a23cc | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-84da090be030 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-897b0922ee87 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-8ed9da30553c | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-99b4cc7104f9 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-9d00610493fc | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-a6fedd2e311d | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-a828e0f4feb9 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-aa3ed32c1e70 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-b63653ec5676 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-c0ef23d24fd7 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-c474d0bfc3e6 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-c597a68e7077 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-c63384bde9d0 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-ccb533cfc2ad | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-ce29fdac4224 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-d2bdfa31de21 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-d93f9dbc5c9a | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-da6e925b5092 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-e06956b05759 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-e3ed7e14a5e2 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-e6f3dd0fb70e | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-ee81e1595007 | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-f05c5248176d | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-f9290d78278f | None | None | UNCHANGED | inferred | None |
| S5 | terminal_reconcile | m-f9764584738e | None | None | UNCHANGED | inferred | None |
| none | launch_failed | m-897b0922ee87 | 1 | 1 | UNCHANGED | measured | None |
| S6 | mission_blocked | m-897b0922ee87 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-897b0922ee87 | None | None | LEGITIMATE_STOP | measured | None |
| none | armed | m-a6fedd2e311d | 12 | 12 | UNCHANGED | measured | None |
| none | launched | m-a6fedd2e311d | 12 | 12 | UNCHANGED | measured | None |
| none | launch_cause | m-a6fedd2e311d | 11 | 11 | UNCHANGED | measured | None |
| none | launch_claimed | m-a6fedd2e311d | 11 | 11 | UNCHANGED | measured | None |
| provider | quota_held | m-a6fedd2e311d | 95 | 95 | LEGITIMATE_STOP | measured | None |
| provider | quota_held | m-3964901ac30d | 1056 | 1056 | LEGITIMATE_STOP | measured | None |
| none | relay_held | m-5f627f3869ac | 5 | 5 | UNCHANGED | measured | None |
| none | continuation_failed | m-5f627f3869ac | 10 | 10 | UNCHANGED | measured | None |
| provider | quota_held | m-33ad663fd7dc | 264 | 264 | LEGITIMATE_STOP | measured | None |
| none | orphan_stopped | m-3964901ac30d | 73 | 73 | UNCHANGED | measured | None |
| none | orphan_stopped | m-33ad663fd7dc | 51 | 51 | UNCHANGED | measured | None |
| none | launch_failed | m-1fb7263df86b | 1 | 1 | UNCHANGED | measured | None |
| S6 | mission_blocked | m-1fb7263df86b | None | None | LEGITIMATE_STOP | measured | None |
| none | relay_held | m-e06956b05759 | 1 | 1 | UNCHANGED | measured | None |
| S6 | mission_blocked | m-d2bdfa31de21 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-e06956b05759 | None | None | LEGITIMATE_STOP | measured | None |
| S1 | epoch_compacted | m-1fb7263df86b | None | None | UNMEASURED | unmeasured | None |
| provider | quota_held | m-1fb7263df86b | 286 | 286 | LEGITIMATE_STOP | measured | None |
| provider | quota_held | m-3d8e5c151705 | 185 | 185 | LEGITIMATE_STOP | measured | None |
| provider | quota_held | m-a828e0f4feb9 | 16 | 16 | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-1fb7263df86b | None | None | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-f011d7fdebc9 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-f011d7fdebc9 | None | None | LEGITIMATE_STOP | measured | None |
| provider | provider_held | m-eaf2843afb16 | 284 | 284 | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-75d9c9944f13 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-75d9c9944f13 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-75d9c9944f13 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-eaf2843afb16 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-ee81e1595007 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-99b4cc7104f9 | None | None | LEGITIMATE_STOP | measured | None |
| S1 | epoch_compacted | m-99b4cc7104f9 | None | None | UNMEASURED | unmeasured | None |
| S6 | mission_blocked | m-99b4cc7104f9 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-99b4cc7104f9 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-51b4175db047 | None | None | LEGITIMATE_STOP | measured | None |
| none | continuation_failed | m-51b4175db047 | 4 | 4 | UNCHANGED | measured | None |
| none | continuation_failed | m-b63653ec5676 | 4 | 4 | UNCHANGED | measured | None |
| S6 | owner_hold_set | m-b63653ec5676 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-84da090be030 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-604666a514a3 | None | None | LEGITIMATE_STOP | measured | None |
| S4 | cost_breaker_tripped | m-84da090be030 | 1 | 1 | LEGITIMATE_STOP | inferred | None |
| S6 | owner_hold_set | m-84da090be030 | None | None | LEGITIMATE_STOP | measured | None |
| S1 | epoch_compacted | m-604666a514a3 | None | None | UNMEASURED | unmeasured | None |
| S4 | cost_breaker_tripped | m-604666a514a3 | 1 | 1 | LEGITIMATE_STOP | inferred | None |
| S6 | owner_hold_set | m-604666a514a3 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-da6e925b5092 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-23ae5b4a7113 | None | None | UNCHANGED | measured | None |
| S6 | owner_hold_set | m-9d00610493fc | None | None | LEGITIMATE_STOP | measured | None |
| S2 | relay_held | m-9d00610493fc | None | None | MOVED_EARLIER | inferred | 1127.0 |
| S3 | relay_held | m-9d00610493fc | 54 | 12 | PREVENTED | measured | None |
| S4 | cost_breaker_tripped | m-da6e925b5092 | 264 | 264 | LEGITIMATE_STOP | inferred | None |
| S6 | mission_blocked | m-9d00610493fc | None | None | LEGITIMATE_STOP | measured | None |
| none | launch_held_cwd | m-e3ed7e14a5e2 | 2 | 2 | UNCHANGED | measured | None |
| S6 | owner_hold_set | m-5373d6f4cda7 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-4bb8952b2903 | None | None | LEGITIMATE_STOP | measured | None |
| S4 | cost_breaker_tripped | m-5373d6f4cda7 | None | None | UNMEASURED | unmeasured | None |
| S6 | owner_hold_set | m-5373d6f4cda7 | None | None | LEGITIMATE_STOP | measured | None |
| S4 | cost_breaker_tripped | m-4bb8952b2903 | 1 | 1 | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-4bb8952b2903 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-79f84cdd34dc | None | None | LEGITIMATE_STOP | measured | None |
| S4 | cost_breaker_tripped | m-79f84cdd34dc | None | None | UNMEASURED | unmeasured | None |
| S6 | owner_hold_set | m-79f84cdd34dc | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-c597a68e7077 | None | None | LEGITIMATE_STOP | measured | None |
| S4 | cost_breaker_tripped | m-c597a68e7077 | None | None | UNMEASURED | unmeasured | None |
| S6 | owner_hold_set | m-c597a68e7077 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-0729ac737bec | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-5ddc61864481 | None | None | LEGITIMATE_STOP | measured | None |
| none | launch_failed | m-c474d0bfc3e6 | 1 | 1 | UNCHANGED | measured | None |
| none | continuation_failed | m-0729ac737bec | 2 | 2 | UNCHANGED | measured | None |
| S6 | owner_hold_set | m-c474d0bfc3e6 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-0729ac737bec | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-5ddc61864481 | None | None | LEGITIMATE_STOP | measured | None |
| none | supervise_error | m-c474d0bfc3e6 | 1 | 1 | UNCHANGED | measured | None |
| S6 | mission_blocked | m-c474d0bfc3e6 | None | None | LEGITIMATE_STOP | measured | None |
| none | continuation_failed | m-c474d0bfc3e6 | 2 | 2 | UNCHANGED | measured | None |
| S6 | mission_blocked | m-c474d0bfc3e6 | None | None | LEGITIMATE_STOP | measured | None |
| none | launch_failed | m-ce29fdac4224 | 1 | 1 | UNCHANGED | measured | None |
| none | continuation_failed | m-ce29fdac4224 | 2 | 2 | UNCHANGED | measured | None |
| S6 | mission_blocked | m-ce29fdac4224 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-16bde3ea1101 | None | None | LEGITIMATE_STOP | measured | None |
| none | continuation_failed | m-032c87418a2e | 2 | 2 | UNCHANGED | measured | None |
| S6 | owner_hold_set | m-032c87418a2e | None | None | LEGITIMATE_STOP | measured | None |
| none | continuation_failed | m-2a029bc2117d | 2 | 2 | UNCHANGED | measured | None |
| none | launch_held_cwd | m-2a029bc2117d | 2 | 2 | UNCHANGED | measured | None |
| none | launch_failed | m-1c22d15ee4ff | 3 | 3 | UNCHANGED | measured | None |
| none | supervise_error | m-ccb533cfc2ad | 1 | 1 | UNCHANGED | measured | None |
| S6 | mission_blocked | m-ccb533cfc2ad | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-2a029bc2117d | None | None | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-ccb533cfc2ad | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-0216790ee987 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-e4e3ccc6ac95 | None | None | LEGITIMATE_STOP | measured | None |
| none | continuation_failed | m-2bd5ec56c69a | 2 | 2 | UNCHANGED | measured | None |
| S6 | mission_blocked | m-2bd5ec56c69a | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-2bd5ec56c69a | None | None | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-0b72311a0676 | None | None | LEGITIMATE_STOP | measured | None |
| none | supervise_error | m-32b2dd69eae1 | 1 | 1 | UNCHANGED | measured | None |
| S6 | mission_blocked | m-32b2dd69eae1 | None | None | UNCHANGED | measured | None |
| S6 | mission_blocked | m-084b5ee34a78 | None | None | LEGITIMATE_STOP | measured | None |
| S1 | epoch_compacted | m-084b5ee34a78 | None | None | UNMEASURED | unmeasured | None |
| S6 | mission_blocked | m-084b5ee34a78 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-0e839e9d581a | None | None | LEGITIMATE_STOP | measured | None |
| S1 | epoch_compacted | m-f9290d78278f | None | None | UNMEASURED | unmeasured | None |
| S4 | cost_breaker_tripped | m-f9290d78278f | 1 | 1 | LEGITIMATE_STOP | inferred | None |
| S6 | owner_hold_set | m-f9290d78278f | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-f9290d78278f | None | None | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-aa3ed32c1e70 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-f9764584738e | None | None | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-f9764584738e | None | None | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-f9764584738e | None | None | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-f9764584738e | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-f9764584738e | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-f9764584738e | None | None | LEGITIMATE_STOP | measured | None |
| none | continuation_failed | m-44475d6f0fe3 | 2 | 2 | UNCHANGED | measured | None |
| S6 | mission_blocked | m-44475d6f0fe3 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-44475d6f0fe3 | None | None | LEGITIMATE_STOP | measured | None |
| none | launch_failed | m-80fd126a23cc | 1 | 1 | UNCHANGED | measured | None |
| none | armed | m-80fd126a23cc | 13 | 13 | UNCHANGED | measured | None |
| none | rehydration_verified | m-80fd126a23cc | 13 | 13 | UNCHANGED | measured | None |
| none | worker_acked | m-80fd126a23cc | 13 | 13 | UNCHANGED | measured | None |
| S6 | owner_hold_set | m-44475d6f0fe3 | None | None | LEGITIMATE_STOP | measured | None |
| none | cost_mark | m-80fd126a23cc | 21 | 21 | UNCHANGED | measured | None |
| none | turn_continued | m-80fd126a23cc | 10 | 10 | UNCHANGED | measured | None |
| S6 | mission_blocked | m-80fd126a23cc | None | None | LEGITIMATE_STOP | measured | None |
| none | launch_held_cwd | m-80fd126a23cc | 2 | 2 | UNCHANGED | measured | None |
| none | continuation_failed | m-80fd126a23cc | 8 | 8 | UNCHANGED | measured | None |
| S6 | owner_hold_set | m-80fd126a23cc | None | None | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-7e268fc1a6d9 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-7e268fc1a6d9 | None | None | UNCHANGED | measured | None |
| S6 | mission_blocked | m-c0ef23d24fd7 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-7e268fc1a6d9 | None | None | LEGITIMATE_STOP | measured | None |
| none | continuation_failed | m-7e268fc1a6d9 | 2 | 2 | UNCHANGED | measured | None |
| S6 | mission_blocked | m-7e268fc1a6d9 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-7e268fc1a6d9 | None | None | LEGITIMATE_STOP | measured | None |
| none | armed | m-e6f3dd0fb70e | 16 | 16 | UNCHANGED | measured | None |
| none | rehydration_verified | m-e6f3dd0fb70e | 11 | 11 | UNCHANGED | measured | None |
| none | worker_acked | m-e6f3dd0fb70e | 15 | 15 | UNCHANGED | measured | None |
| S6 | mission_blocked | m-e6f3dd0fb70e | None | None | LEGITIMATE_STOP | measured | None |
| none | continuation_failed | m-e6f3dd0fb70e | 2 | 2 | UNCHANGED | measured | None |
| S6 | mission_blocked | m-e6f3dd0fb70e | None | None | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-e6f3dd0fb70e | None | None | UNCHANGED | measured | None |
| S6 | mission_blocked | m-e6f3dd0fb70e | None | None | LEGITIMATE_STOP | measured | None |
| none | cost_mark | m-e6f3dd0fb70e | 58 | 58 | UNCHANGED | measured | None |
| none | launch_held_cwd | m-e6f3dd0fb70e | 4 | 4 | UNCHANGED | measured | None |
| S6 | mission_blocked | m-e6f3dd0fb70e | None | None | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-e6f3dd0fb70e | None | None | UNCHANGED | measured | None |
| none | armed | m-7fb90e8735d4 | 16 | 16 | UNCHANGED | measured | None |
| none | rehydration_verified | m-7fb90e8735d4 | 16 | 16 | UNCHANGED | measured | None |
| none | worker_acked | m-7fb90e8735d4 | 16 | 16 | UNCHANGED | measured | None |
| none | cost_mark | m-7fb90e8735d4 | 22 | 22 | UNCHANGED | measured | None |
| S6 | mission_blocked | m-7fb90e8735d4 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-7fb90e8735d4 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-c63384bde9d0 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-c63384bde9d0 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-c63384bde9d0 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-c0ef23d24fd7 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-c0ef23d24fd7 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-c0ef23d24fd7 | None | None | LEGITIMATE_STOP | measured | None |
| none | breaker_receipt | m-8987e45f7f26 | 37 | 37 | UNCHANGED | measured | None |
| S1 | epoch_compacted | m-8987e45f7f26 | None | None | UNMEASURED | unmeasured | None |
| none | cost_mark | m-8987e45f7f26 | 27 | 27 | UNCHANGED | measured | None |
| S6 | mission_blocked | m-8987e45f7f26 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-8987e45f7f26 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-8987e45f7f26 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | mission_blocked | m-8987e45f7f26 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-34bc2fe24e53 | None | None | LEGITIMATE_STOP | measured | None |
| S1 | epoch_compacted | m-34bc2fe24e53 | None | None | UNMEASURED | unmeasured | None |
| S4 | cost_breaker_tripped | m-34bc2fe24e53 | 1 | 1 | LEGITIMATE_STOP | inferred | None |
| S6 | owner_hold_set | m-34bc2fe24e53 | None | None | LEGITIMATE_STOP | measured | None |
| none | supervise_error | m-34bc2fe24e53 | 521 | 521 | UNCHANGED | measured | None |
| none | obligations_saved | m-34bc2fe24e53 | 520 | 520 | UNCHANGED | measured | None |
| none | launch_held_cwd | m-d93f9dbc5c9a | 2 | 2 | UNCHANGED | measured | None |
| S6 | owner_hold_set | m-d93f9dbc5c9a | None | None | LEGITIMATE_STOP | measured | None |
| none | launch_failed | m-5797d3d34285 | 1 | 1 | UNCHANGED | measured | None |
| S6 | owner_hold_set | m-5797d3d34285 | None | None | LEGITIMATE_STOP | measured | None |
| S1 | epoch_compacted | m-260aa89142c8 | None | None | UNMEASURED | unmeasured | None |
| none | heartbeat | m-260aa89142c8 | 25 | 25 | UNCHANGED | measured | None |
| S4 | cost_breaker_tripped | m-260aa89142c8 | 1 | 1 | LEGITIMATE_STOP | inferred | None |
| S6 | owner_hold_set | m-260aa89142c8 | None | None | LEGITIMATE_STOP | measured | None |
| S4 | cost_breaker_tripped | m-260aa89142c8 | 1 | 1 | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-260aa89142c8 | None | None | LEGITIMATE_STOP | measured | None |
| S1 | epoch_compacted | m-8ed9da30553c | None | None | UNMEASURED | unmeasured | None |
| S4 | cost_breaker_tripped | m-8ed9da30553c | 1 | 1 | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-8ed9da30553c | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-8ed9da30553c | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-f05c5248176d | None | None | LEGITIMATE_STOP | measured | None |
| none | launch_held_cwd | m-f05c5248176d | 2 | 2 | UNCHANGED | measured | None |
| none | armed | m-f05c5248176d | 12 | 12 | UNCHANGED | measured | None |
| none | rehydration_verified | m-f05c5248176d | 12 | 12 | UNCHANGED | measured | None |
| none | worker_acked | m-f05c5248176d | 12 | 12 | UNCHANGED | measured | None |
| S1 | epoch_compacted | m-f05c5248176d | None | None | UNMEASURED | unmeasured | None |
| S4 | cost_breaker_tripped | m-f05c5248176d | 1 | 1 | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-f05c5248176d | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-8e496d13dff1 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-34e3f2d4b556 | None | None | LEGITIMATE_STOP | measured | None |
| S1 | epoch_compacted | m-8e496d13dff1 | None | None | UNMEASURED | unmeasured | None |
| S1 | epoch_compacted | m-34e3f2d4b556 | None | None | UNMEASURED | unmeasured | None |
| none | launch_held_cwd | m-8e496d13dff1 | 2 | 2 | UNCHANGED | measured | None |
| S6 | mission_blocked | m-34e3f2d4b556 | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-f05c5248176d | None | None | LEGITIMATE_STOP | measured | None |
| S6 | owner_hold_set | m-f05c5248176d | None | None | LEGITIMATE_STOP | measured | None |
| S4 | cost_breaker_tripped | m-f05c5248176d | 1 | 0 | PREVENTED | inferred | None |
| S6 | owner_hold_set | m-f05c5248176d | None | None | LEGITIMATE_STOP | measured | None |
| none | baseline_resolved | m-3d5f0a27e41d | 12 | 12 | UNCHANGED | measured | None |
| none | armed | m-3d5f0a27e41d | 13 | 13 | UNCHANGED | measured | None |
| none | launched | m-3d5f0a27e41d | 12 | 12 | UNCHANGED | measured | None |
| none | rehydration_verified | m-3d5f0a27e41d | 13 | 13 | UNCHANGED | measured | None |
| none | worker_acked | m-3d5f0a27e41d | 13 | 13 | UNCHANGED | measured | None |
| none | cost_mark | m-3d5f0a27e41d | 19 | 19 | UNCHANGED | measured | None |
| S4 | cost_breaker_tripped | m-3d5f0a27e41d | 1 | 1 | LEGITIMATE_STOP | inferred | None |
| S6 | owner_hold_set | m-3d5f0a27e41d | None | None | LEGITIMATE_STOP | measured | None |
| S1 | epoch_compacted | m-3d5f0a27e41d | None | None | UNMEASURED | unmeasured | None |
| none | breaker_receipt | m-3d5f0a27e41d | 18 | 18 | UNCHANGED | measured | None |
| provider | quota_held | m-3d5f0a27e41d | 1 | 1 | LEGITIMATE_STOP | measured | None |

## FC-06 invariants (challenger, host + seeded)

Challenger breaches: 0

| assertion | host clear/breach/n.a. | seeded clear/breach/n.a. |
|---|---|---|
| capital_ceiling | 7/0/259 | 7/0/12 |
| packet_digest | 0/0/266 | 2/0/17 |
| done_proof | 0/0/266 | 2/0/17 |
| protections | 111/0/155 | 4/0/15 |

Self-test (breach fires, clean control quiet): {"capital_ceiling": {"breach_fires": true, "clean_quiet": true}, "done_proof": {"breach_fires": true, "clean_quiet": true}, "packet_digest": {"breach_fires": true, "clean_quiet": true}, "protections": {"breach_fires": true, "clean_quiet": true}}

## Seeded scenarios (CONSTRUCTED; not host evidence; never counted in verdict totals)

| scenario | seam | champion | challenger | FC-06 breaches |
|---|---|---|---|---|
| seed:arm_no_phases | gsd_mission.arm_preflight | {"ok": true, "refusal": null} | {"ok": false, "refusal": "gsd_status: NO_PHASES: GSD parses 0 phases from ROADMAP.md -- arming would launch a worker with no work"} | 0 |
| seed:arm_phases_remain | gsd_mission.arm_preflight | {"ok": true, "refusal": null} | {"ok": true, "refusal": null} | 0 |
| seed:blocker_branch_protection | blocker_compiler.compile_blocker | {"class": "UNKNOWN", "owner_required": true, "rule": "no_rule_matched"} | {"class": "UNKNOWN", "owner_required": true, "rule": "no_rule_matched"} | 0 |
| seed:blocker_capital | blocker_compiler.compile_blocker | {"class": "CAPITAL_EXHAUSTED", "owner_required": true, "rule": "capital_text"} | {"class": "CAPITAL_EXHAUSTED", "owner_required": true, "rule": "capital_text"} | 0 |
| seed:blocker_force_push | blocker_compiler.compile_blocker | {"class": "PUBLISH_BOUNDARY", "owner_required": true, "rule": "autonomy_outward"} | {"class": "PUBLISH_BOUNDARY", "owner_required": true, "rule": "autonomy_outward"} | 0 |
| seed:blocker_ordinary | blocker_compiler.compile_blocker | {"class": "UNKNOWN", "owner_required": true, "rule": "no_rule_matched"} | {"class": "UNKNOWN", "owner_required": true, "rule": "no_rule_matched"} | 0 |
| seed:packet_digest_match | gsd_mission._packet_digest_matches | {"admitted": true} | {"admitted": true} | 0 |
| seed:packet_digest_mismatch | gsd_mission._packet_digest_matches | {"admitted": false} | {"admitted": false} | 0 |
| seed:receipt_done | gsd_mission.receipt_complete -> receipt_judge.is_done | {"done_claimed": true} | {"done_claimed": true} | 0 |
| seed:receipt_not_done | gsd_mission.receipt_complete -> receipt_judge.is_done | {"done_claimed": false} | {"done_claimed": false} | 0 |
| seed:renewal_authority_exhausted | gsd_mission.renewal_refusal | {"refusal": "owner hold: cost breaker (mission authority): processed 9,100,000 >= authority 9,000,000"} | {"refusal": "owner hold: cost breaker (mission authority): processed 9,100,000 >= authority 9,000,000"} | 0 |
| seed:renewal_cap_reached | gsd_mission.renewal_refusal | {"refusal": "renewal cap 3 reached for lineage m-seed"} | {"refusal": "renewal cap 3 reached for lineage m-seed"} | 0 |
| seed:renewal_clean | gsd_mission.renewal_refusal | {"refusal": null} | {"refusal": null} | 0 |
| seed:renewal_never_launched | gsd_mission.renewal_refusal | {"refusal": "never launched: every launch of this attempt was held, a fresh budget changes nothing"} | {"refusal": "never launched: every launch of this attempt was held, a fresh budget changes nothing"} | 0 |
| seed:renewal_owner_hold | gsd_mission.renewal_refusal | {"refusal": "owner hold: owner park"} | {"refusal": "owner hold: owner park"} | 0 |
| seed:rotation_over_line | gsd_mission.apply_rotation_invariant | {"continue_max_tokens": 590000, "has_marker": false, "repaired": {}} | {"continue_max_tokens": 420000, "has_marker": true, "repaired": {"continue_max_tokens": [590000, 420000]}} | 0 |
| seed:spend_no_authority | mission_spend.judge | {"level": "DEFAULT_CEILING", "trip": true} | {"level": "DEFAULT_CEILING", "trip": true} | 0 |
| seed:spend_over_authority | mission_spend.judge | {"level": "MISSION_AUTHORITY", "trip": true} | {"level": "MISSION_AUTHORITY", "trip": true} | 0 |
| seed:spend_within_authority | mission_spend.judge | {"level": null, "trip": false} | {"level": null, "trip": false} | 0 |

## Policy mutants (each must differ from the challenger)

| mutant | caught | by | differing host | differing seeded | FC-06 breaches | stub calls |
|---|---|---|---|---|---|---|
| always-admit | True | both | 1 | 2 | 1 | 10 |
| never-rotate | True | both | 11 | 1 | 0 | 24 |
| always-renew | True | both | 13 | 4 | 1 | 36 |
| terminal-without-proof | True | seeded | 0 | 1 | 1 | 4 |
| drop-blocker-class | True | both | 111 | 4 | 16 | 120 |
| expand-authority | True | both | 17 | 3 | 2 | 741 |

Every number above carries command `python3 tools/flow_replay.py report --pin .planning/workstreams/flow-compression/phases/07-s7-historical-replay-champion-challenger/07-PIN.json --json .planning/workstreams/flow-compression/phases/07-s7-historical-replay-champion-challenger/07-REPLAY.json --md .planning/workstreams/flow-compression/phases/07-s7-historical-replay-champion-challenger/07-REPLAY.md --mutants` and pin `b47ff018fb44`.
