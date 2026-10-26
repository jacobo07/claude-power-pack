# S9 red team: the 15 Owner claims

Command: `python3 tools/redteam_s9.py run --pin .planning/workstreams/flow-compression/phases/07-s7-historical-replay-champion-challenger/07-PIN.json --claims all --json .planning/workstreams/flow-compression/phases/08-s9-knowledge-vault-ukdl-cbr-red-team-master-done-gate/08-REDTEAM.json --md .planning/workstreams/flow-compression/phases/08-s9-knowledge-vault-ukdl-cbr-red-team-master-done-gate/08-REDTEAM.md`  
Pin sha256: `b47ff018fb44766fb9e2add7b9e23276c18dc6c2ec84cb88d4709c82d95e2743` (6339 rows)  
Host write opens observed: 0

Verdicts are HELD / BREACH / UNMEASURED. HELD means the attack failed on the real subject and a guard-removed control showed it could succeed. There is no PASS.

| # | Claim | Verdict | Planes | Sub-verdicts |
|---|---|---|---|---|
| 1 | The context hypothesis was correlation, not cause. | **UNMEASURED** | repo-artefact, seeded | causal-wording=HELD; causal-effect=UNMEASURED |
| 2 | Rotation increases rehydration cost more than compaction. | **UNMEASURED** | GEX44-host-readonly | rehydration-cost=UNMEASURED |
| 3 | Preflight merely moves waits earlier without reducing span. | **UNMEASURED** | repo-artefact | span-effect=UNMEASURED |
| 4 | Auto-normalized ROADMAP changes semantics. | **HELD** | GEX44-temp-copy, repo-artefact | writer-sweep=HELD; packet-normaliser=HELD |
| 5 | Immutable packets become stale too quickly. | **UNMEASURED** | seeded | packet-staleness=UNMEASURED |
| 6 | Admission reservation causes deadlocks or resource hoarding. | **HELD** | GEX44-host-readonly, repo-artefact, seeded | primitive-sweep=HELD; hoarding=HELD; deadlock=HELD |
| 7 | Auto-renew allows runaway cost. | **HELD** | GEX44-temp-copy | renew-loop=HELD |
| 8 | The semantic progress signal can be gamed by noisy commits or tests. | **HELD** | GEX44-temp-copy | noise-cases=HELD |
| 9 | Night readiness asks too many Owner questions. | **HELD** | GEX44-host-readonly | decisions-sweep=HELD; production-frequency=UNMEASURED |
| 10 | The terminal reconciler creates false DONE. | **HELD** | GEX44-host-readonly, GEX44-temp-copy | crafted-receipts=HELD; host-evidence=UNMEASURED |
| 11 | Blocked work stealing violates dependency or workspace ownership. | **HELD** | GEX44-host-readonly, repo-artefact | no-stealing-code=HELD; predicate=HELD |
| 12 | Historical replay is biased by missing telemetry. | **HELD** | seeded | missing-telemetry=HELD |
| 13 | The efficiency compiler optimizes aggregate mission-hours rather than the actual critical path. | **HELD** | repo-artefact, seeded | subject=HELD; objective-sweep=HELD; seeded-serialization=HELD |
| 14 | GSD X policy leaked into GSD Core. | **HELD** | GEX44-host-readonly, repo-artefact | branch-diff=HELD; host-core=HELD |
| 15 | (claim text absent from the repo) | **UNMEASURED** | repo-artefact | claim-text-search=UNMEASURED |

## Claim 1: The context hypothesis was correlation, not cause.
Verdict: **UNMEASURED** (causal-effect:rotation and compaction were not randomised and no stratum is recorded, so no causal effect is estimable; S1 replay holds only UNMEASURED)

- `causal-wording` HELD [repo-artefact] control_fired=True negative_quiet=True
  - command: `paragraphs naming rotation+compaction with two medians and a causal verb; the same files with the qualifiers deleted are the control`
  - evidence: `{"comparative_effect_paragraphs": [{"causal_verbs": ["lose", "proven", "win"], "file": ".planning/workstreams/flow-compression/phases/01/01-EVIDENCE.md", "paragraph": 4, "qualified": true}], "control_qualifiers_removed_unqualified": [{"causal_verbs": ["lose", "proven", "win"], "file": ".planning/workstreams/flow-compression/phases/01/01-EVIDENCE.md", "paragraph": 4, "qualified": false}], "files_scanned": [".planning/workstreams/flow-compression/phases/01/01-01-SUMMARY.md", ".planning/workstreams/flow-compression/phases/01/01-EVIDENCE.md", ".planning/workstreams/flow-compression/phases/01/01-VERIFICATION.md", ".planning/workstreams/flow-compression/phases/07-s7-historical-replay-champion-chal`
- `causal-effect` UNMEASURED [seeded] control_fired=True negative_quiet=True reason: rotation and compaction were not randomised and no stratum is recorded, so no causal effect is estimable; S1 replay holds only UNMEASURED
  - command: `07-REPLAY.json S1 + a seeded confounded sample where the naive gap vanishes once stratified`
  - evidence: `{"phase1_comparison": "rotation n=35 median 3.2 min vs compaction n=52 median 4.8 min, stated confounded in 01-EVIDENCE.md", "s1_replay_verdicts": {"LEGITIMATE_STOP": 0, "MOVED_EARLIER": 0, "PREVENTED": 0, "UNCHANGED": 0, "UNMEASURED": 13}, "seeded_confounded_arms": {"naive_diff_min": -8.0, "strata": 2, "stratified_diff_min": 0.0}, "strata_recorded": false}`

## Claim 2: Rotation increases rehydration cost more than compaction.
Verdict: **UNMEASURED** (rehydration-cost:n too small (rotation 6, compaction 0; need 3))

- `rehydration-cost` UNMEASURED [GEX44-host-readonly] control_fired=True negative_quiet=True reason: n too small (rotation 6, compaction 0; need 3)
  - command: `first-call context of each rotation epoch vs post/pre-drop context of inferred compactions, epochs closed at the pin`
  - evidence: `{"compaction_post_ctx_lower_bound": [], "compaction_pre_ctx_ceiling": [], "instrument": "compactions are inferred from a >=30% fall in per-call context (transcripts hold no compaction marker); costs are tokens in context, not dollars", "ledger_compactions_in_closed_epochs": 5, "medians_rot_lo_hi": null, "mission": "m-3d5f0a27e41d", "per_epoch": [{"epoch": 1, "transcript": "absent"}, {"calls": 56, "cause": "CONTEXT_ROTATION", "compaction_drops": 0, "epoch": 2, "first_call_ctx": 105128, "ledger_compactions": 0}, {"calls": 63, "cause": "CONTEXT_ROTATION", "compaction_drops": 0, "epoch": 3, "first_call_ctx": 104556, "ledger_compactions": 0}, {"calls": 10, "cause": "UNKNOWN", "compaction_drops": `

## Claim 3: Preflight merely moves waits earlier without reducing span.
Verdict: **UNMEASURED** (span-effect:one S2 incident and its resolution is exogenous: the span effect of an earlier stop is not observable)

- `span-effect` UNMEASURED [repo-artefact] control_fired=True negative_quiet=True reason: one S2 incident and its resolution is exogenous: the span effect of an earlier stop is not observable
  - command: `07-REPLAY.json S2 incident + the mission's own ledger rows; seeded fixed-time vs notify-delay resolutions are the control`
  - evidence: `{"avoidable_idle_h_before_after": [1.353, 1.353], "challenger_stops_earlier_by_s": 1127.0, "incident": {"delta_s": 1127.0, "hold_window_s": 17867.0, "id": "3894f1a7a7", "kind": "relay_held", "mission_id": "m-9d00610493fc", "rows": 53, "seam": "gsd_mission.arm_preflight", "verdict": "MOVED_EARLIER"}, "mission_end": {"event": "mission_halted", "reason": "owner dead and budget: older than 5.0 h", "ts": "2026-10-07T12:26:09+00:00"}, "reading": "the earlier stop is a worker interval not spent; the mission ended by timeout, so its span is the same in both arms", "resolution_exogenous": true, "seeded_fixed_time_resolution": {"challenger_end": 5000.0, "champion_end": 5000.0, "span_delta_s": 0.0}, "s`

## Claim 4: Auto-normalized ROADMAP changes semantics.
Verdict: **HELD**

- `writer-sweep` HELD [repo-artefact] control_fired=True negative_quiet=True
  - command: `ast sweep of tools/*.py and modules/**/*.py for ROADMAP-naming writers + name-based call walk from arm/supervisor entry points`
  - evidence: `{"control_injected_found_and_reachable": true, "files_swept_gt_100": true, "functions_examined_gt_1000": true, "reachable_count": 0, "roadmap_write_sites": [{"file": "modules/sdd_os/scaffold.py", "function": "scaffold", "gsd_verbs": [], "opens_w": 0, "reachable_from_arm_or_supervisor": false, "writes": ["write_text"]}, {"file": "tools/setup_os_ingest.py", "function": "main", "gsd_verbs": [], "opens_w": 0, "reachable_from_arm_or_supervisor": false, "writes": ["write_text"]}]}`
- `packet-normaliser` HELD [GEX44-temp-copy] control_fired=True negative_quiet=True
  - command: `gsd_mission._normalise_packet over 312 inputs and 8 named pairs; attr_patch to a whitespace-stripping normaliser as control`
  - evidence: `{"allowed_equivalences_split": [], "control_whitespace_stripping": {"allowed_equivalences_split": ["crlf_vs_lf", "leading_bom"], "inputs": 312, "random_collision_count": 122, "random_collisions": [["", "0d0a"], ["", "0a"], ["", "20"], ["", "0d0a0d0a"], ["", "0d0a"]], "semantic_changes_merged": ["empty_vs_nl", "trailing_newline", "trailing_space"]}, "inputs": 312, "random_collision_count": 0, "random_collisions": [], "semantic_changes_merged": []}`

## Claim 5: Immutable packets become stale too quickly.
Verdict: **UNMEASURED** (packet-staleness:supersession share 0.125 is under 0.25 but closed-phase re-targeting (Owner live evidence) is not observable in the pin)

- `packet-staleness` UNMEASURED [seeded] control_fired=True negative_quiet=True reason: supersession share 0.125 is under 0.25 but closed-phase re-targeting (Owner live evidence) is not observable in the pin
  - command: `share of admitted wu_packets superseded within 24 h; seeded fast/slow/untimed sets are the controls`
  - evidence: `{"live_evidence_not_used": "Owner: AMR packets r2/r4 re-targeted closed phases 03 and 07 (host recovery dirs mutate; not reproducible, so not a verdict input)", "packet_refusal_rows": 0, "real": {"admitted": 17, "share": 0.125, "superseded_fast": 2, "timed": 16, "untimed": 1}, "rule": "stale-fast = superseded within 24.0 h of packet admission; claim proven at a share >= 0.25", "seeded_fast": {"admitted": 12, "share": 1.0, "superseded_fast": 12, "timed": 12, "untimed": 0}, "seeded_slow": {"admitted": 12, "share": 0.0, "superseded_fast": 0, "timed": 12, "untimed": 0}, "seeded_untimed": {"admitted": 3, "share": null, "superseded_fast": 0, "timed": 0, "untimed": 3}, "share_by_window_h": {"1.0": `

## Claim 6: Admission reservation causes deadlocks or resource hoarding.
Verdict: **HELD**

- `primitive-sweep` HELD [repo-artefact] control_fired=True negative_quiet=True
  - command: `ast sweep of wake predicates, lock primitives and the claim order in launch_worker`
  - evidence: `{"admission_runs_before_the_claim": true, "claim_at": 7508, "claim_deadline_s": 300, "control_injected_wait_and_lock_found": true, "launching_branch_reads_deadline": true, "lock_like_primitives_in_admission_modules": [], "resource_admission_reads_other_missions": [], "resource_refusal_at": 2678, "route_admission_at": 2346, "stray_wakes": [], "wake_kinds_on_the_path": ["env_ready"], "wake_sites": 1}`
- `hoarding` HELD [GEX44-host-readonly] control_fired=True negative_quiet=True
  - command: `pair launch_claimed with the next row of the same mission over the pinned prefix; read the refusal code for any other-mission input`
  - evidence: `{"claims": 160, "claims_followed_up_late": 0, "claims_never_followed_up": 0, "deadline_plus_ten_min_s": 900, "pin_rows": 6339, "refusal_code_reads_other_missions": [], "refusal_rows": 2266, "refusal_rows_inside_another_missions_open_claim": 1, "seeded_open_claim_blocks_other_under_mutant": 1}`
- `deadlock` HELD [seeded] control_fired=True negative_quiet=True
  - command: `3 seeded missions refused by mission_launch_gate, released by flipping the preflight verdict; wait-for graph from the real wake predicates`
  - evidence: `{"held_after_ready_in_reverse_order": 0, "held_under_preflight_not_ready": 3, "mutant_wait_for_cycle_found": true, "renewed_from_loop_ends_without_hold": true, "resource_refusal_after_delta": null, "resource_refusal_low_memory": "REFUSE_LOW_MEMORY", "wait_for_cycle": null, "wait_for_edges": 0, "wake_kinds_seen": ["env_ready"]}`

## Claim 7: Auto-renew allows runaway cost.
Verdict: **HELD**

- `renew-loop` HELD [GEX44-temp-copy] control_fired=True negative_quiet=True
  - command: `mission_spend.judge in a 100-call pure loop (fingerprint moves every call); mission_topup.judge x30; mutant expand-authority; LEASE_MAX_RENEWALS patched`
  - evidence: `{"authority_lapsed_at_call_10": {"cap": 9999000000, "final_spent": 17964, "over_cap_no_trip": 0, "renew_after_lapse": 0, "renewals": 4, "tripped_at": 11, "trips": 1}, "base": {"cap": 9999000000, "final_spent": 79550930, "over_cap_no_trip": 0, "renew_after_lapse": 0, "renewals": 20, "tripped_at": 43, "trips": 1}, "control_expand_authority_over_cap_calls": 39, "control_lease_cap_removed_renewals": 30, "control_seq_ignored_grants": 30, "lease_max_renewals": 20, "topup": {"grants_for_one_hold": 1, "second_hold_at_max_refused": true, "terminal_is_none": true}}`

## Claim 8: The semantic progress signal can be gamed by noisy commits or tests.
Verdict: **HELD**

- `noise-cases` HELD [GEX44-temp-copy] control_fired=True negative_quiet=True
  - command: `gsd_mission.progress_fingerprint before/after 9 noise cases and 6 real-work cases in temp git repos + mission_spend.judge; CPP_PROGRESS_BOOKKEEPING=count control`
  - evidence: `{"blind_cases": [], "bound_on_damage": {"ceiling": "authority less closeout reserve (claim 7)", "lease_max_renewals": 20}, "cases": {"amend_identical_tree": {"measured": true, "moved": false, "renewal_granted": false}, "empty_commit": {"measured": true, "moved": false, "renewal_granted": false}, "gitignored_dir_file": {"measured": true, "moved": false, "renewal_granted": false}, "mtime_only": {"measured": true, "moved": false, "renewal_granted": false}, "resumption_file_md_only": {"measured": true, "moved": false, "renewal_granted": false}, "resumption_md_only": {"measured": true, "moved": false, "renewal_granted": false}, "state_md_only": {"measured": true, "moved": false, "renewal_granted"`

## Claim 9: Night readiness asks too many Owner questions.
Verdict: **HELD**

- `decisions-sweep` HELD [GEX44-host-readonly] control_fired=True negative_quiet=True
  - command: `blocker_compiler.foreseeable_decisions over every .planning/workstreams entry of this clone; each item re-classified by modules.autonomy_gate.gate.classify(authorized=()); control: use_filters=False`
  - evidence: `{"control_filters_off": {"items_positive": true, "spurious_positive": true, "workstreams": 12}, "definition": "too many = at least one emitted item that is not Owner-class, or that duplicates another item", "real": {"duplicate_workstreams": [], "duplicates": 0, "sources_read_ge_5": true, "spurious": 0, "spurious_examples": [], "workstreams": 12}, "seeded_ask": {"duplicate_workstreams": [], "duplicates": 0, "items": 1, "owner_class": 1, "sources_read": 1, "spurious": 0, "workstreams": 1}}`
- `production-frequency` UNMEASURED [GEX44-host-readonly] control_fired=None negative_quiet=None reason: no owner_decisions_batch row in the pinned prefix: live frequency unmeasured
  - command: `count of owner_decisions_batch rows in the pinned ledger prefix`
  - evidence: `{"owner_decisions_batch_rows_in_pin": 0}`

## Claim 10: The terminal reconciler creates false DONE.
Verdict: **HELD**

- `crafted-receipts` HELD [GEX44-temp-copy] control_fired=True negative_quiet=True
  - command: `mission_reconcile.reconcile over 6 crafted cases + forced-status guard control; flow_replay.mutant_scope('terminal-without-proof')`
  - evidence: `{"cases": {"divergent_values": "AMBIGUOUS", "epoch_mismatch": "AMBIGUOUS", "measured_key": "RECOVERED_DONE", "missing": "AMBIGUOUS", "not_done": "AMBIGUOUS", "other_mission_receipt": "AMBIGUOUS"}, "false_done_cases": [], "forced_status_guard_alone": {"is_done": false, "mutant": "RECOVERED_DONE", "unmutated": "AMBIGUOUS"}, "mutant_recovered_done_cases": ["forced_status_not_done"], "negative_control_real_values": "RECOVERED_DONE", "noted_not_breach": {"measured_key": "certificate under key 'measured' (not 'values') is ignored by receipt_judge"}, "reconcile_calls": 15}`
- `host-evidence` UNMEASURED [GEX44-host-readonly] control_fired=None negative_quiet=None reason: no host receipts (done_proof not_applicable)
  - command: `07-REPLAY.json (sha256 checked against the committed blob)`
  - evidence: `{"done_proof": null, "s5_slice": {"keys": ["buckets_h", "missions", "now", "quoted_not_measured", "unmeasured"]}}`

## Claim 11: Blocked work stealing violates dependency or workspace ownership.
Verdict: **HELD**

- `no-stealing-code` HELD [repo-artefact] control_fired=True negative_quiet=True
  - command: `ast sweep: functions reading independent_work that also call launch/claim/assign/dispatch (S8 is dormant by decision D-09)`
  - evidence: `{"consumers": [], "control_injected_consumer_found": true, "files_swept": 894, "readers_of_independent_work": [{"file": "tools/blocker_compiler.py", "function": "_independent"}, {"file": "tools/blocker_compiler.py", "function": "compile_blocker"}, {"file": "tools/flow_replay.py", "function": "s6_incidents"}, {"file": "tools/flow_replay.py", "function": "s8_sentence"}, {"file": "tools/gsd_mission.py", "function": "_compile_blocker"}, {"file": "tools/gsd_mission.py", "function": "_blocker_ledger"}, {"file": "tools/gsd_mission.py", "function": "_cli"}, {"file": "tools/s9_kv_check.py", "function": "recount_s8"}, {"file": "tools/s9_kv_check.py", "function": "check_spec_predicate"}, {"file": "tool`
- `predicate` HELD [GEX44-host-readonly] control_fired=True negative_quiet=True
  - command: `s8_predicate(rows) from D-09 over the pinned prefix, a seeded qualifying ledger and two negative seeds`
  - evidence: `{"action_without_independent_work_true": false, "independent_work_true_without_action": false, "pin_rows": 6339, "pinned_prefix": {"blocked_rows": 55, "blocked_with_independent_work_true": 0, "incidents": 0, "value": false}, "seeded_qualifying": true}`

## Claim 12: Historical replay is biased by missing telemetry.
Verdict: **HELD**

- `missing-telemetry` HELD [seeded] control_fired=True negative_quiet=True
  - command: `recompute mission spans with my own terminal predicate; flow_replay's figure must be bounded with the open count and tail beside it; pin-ended windows are the control`
  - evidence: `{"bias_exceeds_tolerance": false, "flow_replay_beside": {"open_at_pin": 92, "open_hours_bounded_at_last_row": 874.328, "unobserved_tail_hours": 25831.952}, "flow_replay_summed_h": 1651.959, "guard_removed_pin_ended": {"bounded_ok": false, "breach": true, "open_count_ok": true, "summed_h": 27483.911, "tail_beside_ok": false}, "independent": {"bias_h": 25831.952, "bias_ratio": 15.232, "bounded_h": 1695.94, "headline_h": 27527.892, "missions": 148, "open": 92}, "independent_matches_flow_replay": true, "judged": {"bounded_ok": true, "breach": false, "open_count_ok": true, "tail_beside_ok": true}, "seeded_complete": {"bias_h": 0.0, "bias_ratio": 0.0, "bounded_h": 12.0, "headline_h": 12.0, "missio`

## Claim 13: The efficiency compiler optimizes aggregate mission-hours rather than the actual critical path.
Verdict: **HELD**

- `subject` HELD [repo-artefact] control_fired=True negative_quiet=True
  - command: `grep every tools/*.py path and body for an efficiency compiler`
  - evidence: `{"files_naming_an_efficiency_compiler": [], "files_swept": 894, "subject_used": "flow_replay.time_accounting + verdict + render_md (the only code that reads summed hours)"}`
- `objective-sweep` HELD [repo-artefact] control_fired=True negative_quiet=True
  - command: `ast sweep: functions reading summed_mission_hours that branch on it or are named choose/select/optimise/decide/rank`
  - evidence: `{"control_injected_decider_found": true, "deciders": [], "readers": [{"file": "tools/flow_replay.py", "function": "time_accounting"}, {"file": "tools/flow_replay.py", "function": "render_md"}]}`
- `seeded-serialization` HELD [seeded] control_fired=True negative_quiet=True
  - command: `time_accounting over 2 parallel vs 2 serialized seeded missions; a summed-hours labeller is the control`
  - evidence: `{"critical_path_keyed_label_calls_it_a_gain": false, "critical_path_rises": true, "parallel": {"critical_path_wall_clock_hours": 3.0, "summed_mission_hours": 6.0, "wall_clock_hours": 3.0}, "serialized": {"critical_path_wall_clock_hours": 4.0, "summed_mission_hours": 4.0, "wall_clock_hours": 4.0}, "summed_drops_when_serialized": true, "summed_keyed_label_calls_serialized_a_gain": true, "wall_rises": true}`

## Claim 14: GSD X policy leaked into GSD Core.
Verdict: **HELD**

- `branch-diff` HELD [repo-artefact] control_fired=True negative_quiet=True
  - command: `git diff --name-only 7edba723..043bb2b4 ; git diff --name-only 043bb2b4..HEAD`
  - evidence: `{"changed_files_in_range": 205, "control_diff_flagged": ["gsd-core/bin/x.cjs"], "control_mutate_classified": 1, "gsd_core_paths_changed": [], "gsd_tools_call_functions": 2, "mutating_call_functions": []}`
- `host-core` HELD [GEX44-host-readonly] control_fired=True negative_quiet=True
  - command: `grep -rlE <switch names> ~/.claude/gsd-core (text files)`
  - evidence: `{"control_injected_found": true, "core_files_read": 743, "files_naming_a_switch": [], "files_newer_than_base_supplementary": 0, "laptop_core": "LAPTOP-ONLY-not-observed", "needles": 14}`

## Claim 15: (claim text absent from the repo)
Verdict: **UNMEASURED** (claim-text-search:claim text absent; OWNER DECISION NEEDED)

- `claim-text-search` UNMEASURED [repo-artefact] control_fired=True negative_quiet=True reason: claim text absent; OWNER DECISION NEEDED
  - command: `regex a numbered list of 15+ consecutive items in STATE, RESUMPTION (workstream+root), 08-CONTEXT, the spec; a planted 15-item list is the control`
  - evidence: `{"claim_text_found": false, "files_missing": [], "files_searched": [".planning/workstreams/flow-compression/RESUMPTION_FILE.md", ".planning/workstreams/flow-compression/STATE.md", ".planning/workstreams/flow-compression/phases/08-s9-knowledge-vault-ukdl-cbr-red-team-master-done-gate/08-CONTEXT.md", "RESUMPTION_FILE.md", "vault/specs/flow-compression.md"], "lists_of_15_or_more": []}`

## Claim 15
UNMEASURED: claim text absent; OWNER DECISION NEEDED. No text is invented for it.

## LAPTOP-ONLY (not observed on this plane)
- the laptop gsd-core install
- live hooks and laptop ledger facts
