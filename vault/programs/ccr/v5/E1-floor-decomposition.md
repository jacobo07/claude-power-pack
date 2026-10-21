# E1 floor decomposition (part 1 of 3 of WU-E1; not the done-check file)

Measured 2026-10-21 by running `tools/ccr_anatomy.py table` on the GEX44 receipts root, read-only, script sent over stdin.
Source receipts: `/home/kobii/missions/ccr-s3-data/pack/receipts` on GEX44, 41 sessions with two or more `call` rows (144 jsonl files).
Calibration printed by the tool: call-1 3.01 B/token over 33 sessions; carry 2.494 B/token over 1002 steps. Neither rate is assumed.
The 33 are the sessions in the 10 tool-configuration groups (same offered tools, traits, section bytes and deferred-tool bytes) that have at least two distinct sized-byte values; the other 8 of the 41 are in groups that cannot supply a within-group slope. A "group" is a calibration unit, not a partition of the files (`calibrate` in `tools/ccr_anatomy.py`).
The tool refuses on the laptop roots: `uz-probe-out` and `probe` use another row schema, and `.state-dev/receipts` calibrates call-1 (2.161 B/token, 7 sessions) but has no carry steps.

Each row is the median over the sessions where the component is present; medians do not sum to the call-1 context.
The ~59K invisible floor in the plan sits between the REDUCIBLE class median (55,815) and the sum of the REDUCIBLE rows below (31,103 + 27,025 + 1,847 + 927 = 60,902).

Coverage of the call-1 context median (82,298), summing the row medians in the table: REDUCIBLE 60,902 + ELIMINABLE 20,662 + PAGEABLE 1,477 + IRREDUCIBLE 2,299 = 85,340 = 103.7%. It exceeds 100% because each row is a median over a different subset of sessions, so the rows are not additive; it is a consistency check (the rows account for the whole context), not an exact partition. The UNKNOWN rows (sum of medians 22,978) are sparse (1-11 of 41 sessions each) and are left out of that sum. Class medians (55,815 / 20,373 / 1,431 / 2,389) are medians of per-session class totals and differ slightly from the row sums for the same reason.

Sessions: 41; call-1 context median 82,298, min 5,406, max 225,745.

| class | median tokens at call 1 | min | max |
|---|---:|---:|---:|
| REDUCIBLE | 55,815 | 3,232 | 193,638 |
| ELIMINABLE | 20,373 | 91 | 76,973 |
| IRREDUCIBLE | 2,389 | 2,083 | 38,686 |
| PAGEABLE | 1,431 | 0 | 8,890 |
| UNKNOWN | 153 | 0 | 37,015 |

| component | median tokens | sessions present | class | evidence |
|---|---:|---:|---|---|
| attach:instructions | 31,103 | 35/41 | REDUCIBLE | unit kernel+index replace 78,400 -> 4,817 B (V1 r2/r4), parity 5/5 |
| tool_schemas+framing | 27,025 | 41/41 | REDUCIBLE | probes P1 -> P3 remove 4,114 tokens via --tools "" --strict-mcp-config --disable-slash-commands |
| attach:skill_listing | 9,988 | 33/41 | ELIMINABLE | dropped by unit closure in V1 r2/r4, parity 5/5 |
| attach:agent_listing_delta | 9,075 | 28/41 | ELIMINABLE | dropped by unit closure in V1 r2/r4, parity 5/5 |
| attach:hook_additional_context | 1,847 | 40/41 | REDUCIBLE | hook prose; probe P4 (--setting-sources "") removes 10,569 B; candidate, no parity run |
| attach:deferred_tools_delta | 1,477 | 35/41 | PAGEABLE | names of deferred tools; ToolSearch pages them |
| section:heron_brook | 927 | 6/41 | REDUCIBLE | session-specific section, candidate |
| attach:mcp_instructions_delta | 704 | 39/41 | ELIMINABLE | dropped by unit closure in V1 r2/r4, parity 5/5 |
| section:memory | 698 | 33/41 | ELIMINABLE | dropped by unit closure in V1 r2/r4, parity 5/5 |
| attach:remote_session_change | 181 | 30/41 | ELIMINABLE | absent in probe P3; no role in a -p task; candidate, no parity run |
| attach:total_tokens_reminder | 16 | 36/41 | ELIMINABLE | 49 B per call, kept in every probe; candidate, no parity run |
| IRREDUCIBLE rows (lean_body 533, environment 331, session_context 268, session_guidance 220, env_info_simple 192, prompt 179, action_caution 173, pronouns 119, context_management 93, act_dont_rederive 92, model 43, communication 31, total_tokens 16, date 9) | 2,389 (class median) | 41/41 | IRREDUCIBLE | kept in probe P4 |

UNKNOWN rows (no measurement exists, so they stay unclassified): attach:invoked_skills 14,986 (1/41), queued_command 2,825 (2/41),
file 2,126 (3/41), hook_blocking_error 1,393 (2/41), edited_text_file 1,092 (2/41), delivering_work_max 670, bg-session 652 (8/41),
overcorrection 414, compact_file_reference 320, auto_mode 159 (11/41), hook_success 153, silent_turn_reminder 111, endconv_deferred_hint 77.

## Limits
- Four of the biggest rows (instructions, tool schemas, skill listing, agent listing) are classified from earlier parity runs (V1 r2/r4, probes P1-P4), not from a fresh parity run in this unit.
- `hook_additional_context`, `heron_brook`, `remote_session_change` and `total_tokens_reminder` are candidates with no parity run.
- The GEX44 sessions are GEX44 workers, so the laptop interactive floor can differ (hooks, skills and agents lists are laptop-specific).
- Parts 2 and 3 of WU-E1 (lean launch profile for workers, Context Admission check at arm) are not done. `evidence-E1.md` is not written.
