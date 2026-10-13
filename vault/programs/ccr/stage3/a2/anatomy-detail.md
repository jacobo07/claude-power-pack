calibration call-1: 2.999 B/token over 35 sessions in 11 groups; carry: 2.491 B/token over 1031 steps
### 0bdd6fe2 (calls 23, offered tools 7, unit None; ctx call 1 18,137, last call 65,566)

| bucket | tokens | class | evidence |
|---|---:|---|---|
| section:lean_body | 535 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:communication | 31 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:pronouns | 119 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:action_caution | 173 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:session_guidance | 175 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:env_info_simple | 193 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:context_management | 93 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:act_dont_rederive | 92 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:total_tokens | 16 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| attach:environment | 315 | IRREDUCIBLE | cwd/platform; kept in probe P4 (every switch off) |
| attach:model | 41 | IRREDUCIBLE | model identity; kept in probe P4 |
| attach:mcp_instructions_delta | 75 | ELIMINABLE | dropped by unit closure in V1 r2/r4, parity 5/5 |
| attach:total_tokens_reminder | 16 | ELIMINABLE | 49 B per call, kept in every probe; candidate, no parity run |
| attach:hook_additional_context | 827 | REDUCIBLE | hook prose; probe P4 (--setting-sources "") removes 10,569 B; candidate, no parity run |
| attach:session_context | 269 | IRREDUCIBLE | kept in probe P4 |
| attach:date | 9 | IRREDUCIBLE | date; kept in probe P4 |
| prompt | 42 | IRREDUCIBLE | the task itself |
| tool_schemas+framing | 15,113 | REDUCIBLE | probes P1 -> P3 remove 4,114 tokens via --tools "" --strict-mcp-config --disable-slash-commands |
| carry:tool_result | 12,786 | PAGEABLE | tool-output projection and paging exist (project events) |
| carry:response | 31,116 | HOST_LIMITED | host replays the assistant's own prior turns; no flag removes them |
| carry:attach:total_tokens_reminder | 433 | ELIMINABLE | 49 B per call, kept in every probe; candidate, no parity run |
| carry:attach:hook_additional_context | 938 | REDUCIBLE | hook prose; probe P4 (--setting-sources "") removes 10,569 B; candidate, no parity run |
| carry:attach:silent_turn_reminder | 77 | UNKNOWN | no measurement for this bucket |
| carry:attach:date | 48 | IRREDUCIBLE | date; kept in probe P4 |
| carry:attach:queued_command | 381 | UNKNOWN | no measurement for this bucket |
| carry:images | 5,328 | PAGEABLE | pixel GC tombstones images outside the window |
| carry:residual | -3,677 | UNKNOWN | carry not explained by sized buckets |

### 403d2d16 (calls 4, offered tools 86, unit None; ctx call 1 74,594, last call 80,375)

| bucket | tokens | class | evidence |
|---|---:|---|---|
| section:lean_body | 535 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:communication | 31 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:pronouns | 119 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:action_caution | 173 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:session_guidance | 221 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:memory | 714 | ELIMINABLE | dropped by unit closure in V1 r2/r4, parity 5/5 |
| section:env_info_simple | 193 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:context_management | 93 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:act_dont_rederive | 92 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:heron_brook | 930 | REDUCIBLE | session-specific section, kept in probes P1-P4 and V1 (absent in Madzia lean+print); candidate |
| section:total_tokens | 16 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| attach:hook_additional_context | 1,853 | REDUCIBLE | hook prose; probe P4 (--setting-sources "") removes 10,569 B; candidate, no parity run |
| attach:environment | 315 | IRREDUCIBLE | cwd/platform; kept in probe P4 (every switch off) |
| attach:model | 42 | IRREDUCIBLE | model identity; kept in probe P4 |
| attach:deferred_tools_delta | 1,436 | PAGEABLE | names of deferred tools; ToolSearch pages them; absent in probe P3 (--tools "" --strict-mcp-config) |
| attach:agent_listing_delta | 8,750 | ELIMINABLE | dropped by unit closure in V1 r2/r4, parity 5/5 |
| attach:mcp_instructions_delta | 707 | ELIMINABLE | dropped by unit closure in V1 r2/r4, parity 5/5 |
| attach:skill_listing | 5,022 | ELIMINABLE | dropped by unit closure in V1 r2/r4, parity 5/5 |
| attach:total_tokens_reminder | 16 | ELIMINABLE | 49 B per call, kept in every probe; candidate, no parity run |
| attach:instructions | 26,142 | REDUCIBLE | unit kernel+index replace 78,400 -> 4,817 B (V1 r2/r4), parity 5/5 |
| attach:session_context | 269 | IRREDUCIBLE | kept in probe P4 |
| attach:date | 9 | IRREDUCIBLE | date; kept in probe P4 |
| attach:remote_session_change | 181 | ELIMINABLE | absent in probe P3; no role in a -p task; candidate, no parity run |
| prompt | 156 | IRREDUCIBLE | the task itself |
| tool_schemas+framing | 26,576 | REDUCIBLE | probes P1 -> P3 remove 4,114 tokens via --tools "" --strict-mcp-config --disable-slash-commands |
| carry:tool_result | 3,409 | EMBODIABLE | answer is script-computable (V1 truth.py): DETERMINISTIC_PATH embodies the reads |
| carry:response | 1,376 | HOST_LIMITED | host replays the assistant's own prior turns; no flag removes them |
| carry:attach:total_tokens_reminder | 59 | ELIMINABLE | 49 B per call, kept in every probe; candidate, no parity run |
| carry:attach:hook_additional_context | 316 | REDUCIBLE | hook prose; probe P4 (--setting-sources "") removes 10,569 B; candidate, no parity run |
| carry:residual | 621 | UNKNOWN | carry not explained by sized buckets |

### 4f0ecc00 (calls 6, offered tools 86, unit None; ctx call 1 74,594, last call 82,456)

| bucket | tokens | class | evidence |
|---|---:|---|---|
| section:lean_body | 535 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:communication | 31 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:pronouns | 119 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:action_caution | 173 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:session_guidance | 221 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:memory | 714 | ELIMINABLE | dropped by unit closure in V1 r2/r4, parity 5/5 |
| section:env_info_simple | 193 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:context_management | 93 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:act_dont_rederive | 92 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:heron_brook | 930 | REDUCIBLE | session-specific section, kept in probes P1-P4 and V1 (absent in Madzia lean+print); candidate |
| section:total_tokens | 16 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| attach:hook_additional_context | 1,853 | REDUCIBLE | hook prose; probe P4 (--setting-sources "") removes 10,569 B; candidate, no parity run |
| attach:environment | 315 | IRREDUCIBLE | cwd/platform; kept in probe P4 (every switch off) |
| attach:model | 42 | IRREDUCIBLE | model identity; kept in probe P4 |
| attach:deferred_tools_delta | 1,436 | PAGEABLE | names of deferred tools; ToolSearch pages them; absent in probe P3 (--tools "" --strict-mcp-config) |
| attach:agent_listing_delta | 8,750 | ELIMINABLE | dropped by unit closure in V1 r2/r4, parity 5/5 |
| attach:mcp_instructions_delta | 707 | ELIMINABLE | dropped by unit closure in V1 r2/r4, parity 5/5 |
| attach:skill_listing | 5,022 | ELIMINABLE | dropped by unit closure in V1 r2/r4, parity 5/5 |
| attach:total_tokens_reminder | 16 | ELIMINABLE | 49 B per call, kept in every probe; candidate, no parity run |
| attach:instructions | 26,142 | REDUCIBLE | unit kernel+index replace 78,400 -> 4,817 B (V1 r2/r4), parity 5/5 |
| attach:session_context | 269 | IRREDUCIBLE | kept in probe P4 |
| attach:date | 9 | IRREDUCIBLE | date; kept in probe P4 |
| attach:remote_session_change | 181 | ELIMINABLE | absent in probe P3; no role in a -p task; candidate, no parity run |
| prompt | 156 | IRREDUCIBLE | the task itself |
| tool_schemas+framing | 26,576 | REDUCIBLE | probes P1 -> P3 remove 4,114 tokens via --tools "" --strict-mcp-config --disable-slash-commands |
| carry:tool_result | 4,500 | EMBODIABLE | answer is script-computable (V1 truth.py): DETERMINISTIC_PATH embodies the reads |
| carry:response | 1,918 | HOST_LIMITED | host replays the assistant's own prior turns; no flag removes them |
| carry:attach:hook_additional_context | 292 | REDUCIBLE | hook prose; probe P4 (--setting-sources "") removes 10,569 B; candidate, no parity run |
| carry:attach:total_tokens_reminder | 98 | ELIMINABLE | 49 B per call, kept in every probe; candidate, no parity run |
| carry:residual | 1,054 | UNKNOWN | carry not explained by sized buckets |

### 8c3d8a8e (calls 4, offered tools 86, unit bounded-code-worker; ctx call 1 18,308, last call 24,573)

| bucket | tokens | class | evidence |
|---|---:|---|---|
| section:lean_body | 535 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:communication | 31 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:pronouns | 119 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:action_caution | 173 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:session_guidance | 221 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:env_info_simple | 193 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:context_management | 93 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:act_dont_rederive | 92 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:heron_brook | 930 | REDUCIBLE | session-specific section, kept in probes P1-P4 and V1 (absent in Madzia lean+print); candidate |
| section:total_tokens | 16 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| attach:hook_success | 154 | UNKNOWN | no measurement for this bucket |
| attach:hook_additional_context | 1,853 | REDUCIBLE | hook prose; probe P4 (--setting-sources "") removes 10,569 B; candidate, no parity run |
| attach:environment | 315 | IRREDUCIBLE | cwd/platform; kept in probe P4 (every switch off) |
| attach:model | 42 | IRREDUCIBLE | model identity; kept in probe P4 |
| attach:deferred_tools_delta | 1,436 | PAGEABLE | names of deferred tools; ToolSearch pages them; absent in probe P3 (--tools "" --strict-mcp-config) |
| attach:total_tokens_reminder | 16 | ELIMINABLE | 49 B per call, kept in every probe; candidate, no parity run |
| attach:instructions | 1,606 | REDUCIBLE | unit kernel+index replace 78,400 -> 4,817 B (V1 r2/r4), parity 5/5 |
| attach:session_context | 269 | IRREDUCIBLE | kept in probe P4 |
| attach:date | 9 | IRREDUCIBLE | date; kept in probe P4 |
| attach:remote_session_change | 181 | ELIMINABLE | absent in probe P3; no role in a -p task; candidate, no parity run |
| prompt | 156 | IRREDUCIBLE | the task itself |
| tool_schemas+framing | 9,865 | REDUCIBLE | probes P1 -> P3 remove 4,114 tokens via --tools "" --strict-mcp-config --disable-slash-commands |
| carry:tool_result | 3,148 | EMBODIABLE | answer is script-computable (V1 truth.py): DETERMINISTIC_PATH embodies the reads |
| carry:response | 1,694 | HOST_LIMITED | host replays the assistant's own prior turns; no flag removes them |
| carry:attach:deferred_tools_delta | 884 | PAGEABLE | names of deferred tools; ToolSearch pages them; absent in probe P3 (--tools "" --strict-mcp-config) |
| carry:attach:total_tokens_reminder | 59 | ELIMINABLE | 49 B per call, kept in every probe; candidate, no parity run |
| carry:residual | 481 | UNKNOWN | carry not explained by sized buckets |

### b0de7339 (calls 3, offered tools 2, unit None; ctx call 1 6,458, last call 18,709)

| bucket | tokens | class | evidence |
|---|---:|---|---|
| section:lean_body | 535 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:communication | 31 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:pronouns | 119 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:action_caution | 173 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:session_guidance | 175 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:env_info_simple | 193 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:context_management | 93 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:act_dont_rederive | 92 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:total_tokens | 16 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| attach:hook_success | 154 | UNKNOWN | no measurement for this bucket |
| attach:environment | 315 | IRREDUCIBLE | cwd/platform; kept in probe P4 (every switch off) |
| attach:model | 41 | IRREDUCIBLE | model identity; kept in probe P4 |
| attach:mcp_instructions_delta | 75 | ELIMINABLE | dropped by unit closure in V1 r2/r4, parity 5/5 |
| attach:total_tokens_reminder | 16 | ELIMINABLE | 49 B per call, kept in every probe; candidate, no parity run |
| attach:hook_additional_context | 705 | REDUCIBLE | hook prose; probe P4 (--setting-sources "") removes 10,569 B; candidate, no parity run |
| attach:session_context | 269 | IRREDUCIBLE | kept in probe P4 |
| attach:date | 9 | IRREDUCIBLE | date; kept in probe P4 |
| prompt | 27 | IRREDUCIBLE | the task itself |
| tool_schemas+framing | 3,417 | REDUCIBLE | probes P1 -> P3 remove 4,114 tokens via --tools "" --strict-mcp-config --disable-slash-commands |
| carry:response | 1,595 | HOST_LIMITED | host replays the assistant's own prior turns; no flag removes them |
| carry:attach:total_tokens_reminder | 39 | ELIMINABLE | 49 B per call, kept in every probe; candidate, no parity run |
| carry:images | 10,483 | PAGEABLE | pixel GC tombstones images outside the window |
| carry:residual | 133 | UNKNOWN | carry not explained by sized buckets |

### bf6d4b07 (calls 26, offered tools 7, unit None; ctx call 1 17,235, last call 99,443)

| bucket | tokens | class | evidence |
|---|---:|---|---|
| section:lean_body | 535 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:communication | 31 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:pronouns | 119 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:action_caution | 173 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:session_guidance | 175 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:env_info_simple | 193 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:context_management | 93 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:act_dont_rederive | 92 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:total_tokens | 16 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| attach:environment | 315 | IRREDUCIBLE | cwd/platform; kept in probe P4 (every switch off) |
| attach:model | 41 | IRREDUCIBLE | model identity; kept in probe P4 |
| attach:mcp_instructions_delta | 75 | ELIMINABLE | dropped by unit closure in V1 r2/r4, parity 5/5 |
| attach:total_tokens_reminder | 16 | ELIMINABLE | 49 B per call, kept in every probe; candidate, no parity run |
| attach:hook_additional_context | 705 | REDUCIBLE | hook prose; probe P4 (--setting-sources "") removes 10,569 B; candidate, no parity run |
| attach:session_context | 269 | IRREDUCIBLE | kept in probe P4 |
| attach:date | 9 | IRREDUCIBLE | date; kept in probe P4 |
| prompt | 42 | IRREDUCIBLE | the task itself |
| tool_schemas+framing | 14,333 | REDUCIBLE | probes P1 -> P3 remove 4,114 tokens via --tools "" --strict-mcp-config --disable-slash-commands |
| carry:tool_result | 18,631 | PAGEABLE | tool-output projection and paging exist (project events) |
| carry:response | 61,784 | HOST_LIMITED | host replays the assistant's own prior turns; no flag removes them |
| carry:attach:total_tokens_reminder | 492 | ELIMINABLE | 49 B per call, kept in every probe; candidate, no parity run |
| carry:attach:hook_additional_context | 1,263 | REDUCIBLE | hook prose; probe P4 (--setting-sources "") removes 10,569 B; candidate, no parity run |
| carry:attach:silent_turn_reminder | 39 | UNKNOWN | no measurement for this bucket |
| carry:attach:queued_command | 385 | UNKNOWN | no measurement for this bucket |
| carry:images | 7,869 | PAGEABLE | pixel GC tombstones images outside the window |
| carry:residual | -8,254 | UNKNOWN | carry not explained by sized buckets |

### f03c1c84 (calls 31, offered tools 7, unit None; ctx call 1 19,100, last call 83,561)

| bucket | tokens | class | evidence |
|---|---:|---|---|
| section:lean_body | 535 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:communication | 31 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:pronouns | 119 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:action_caution | 173 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:session_guidance | 175 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:env_info_simple | 193 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:context_management | 93 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:act_dont_rederive | 92 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:total_tokens | 16 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| attach:hook_additional_context | 1,091 | REDUCIBLE | hook prose; probe P4 (--setting-sources "") removes 10,569 B; candidate, no parity run |
| attach:environment | 315 | IRREDUCIBLE | cwd/platform; kept in probe P4 (every switch off) |
| attach:model | 41 | IRREDUCIBLE | model identity; kept in probe P4 |
| attach:mcp_instructions_delta | 75 | ELIMINABLE | dropped by unit closure in V1 r2/r4, parity 5/5 |
| attach:total_tokens_reminder | 16 | ELIMINABLE | 49 B per call, kept in every probe; candidate, no parity run |
| attach:session_context | 269 | IRREDUCIBLE | kept in probe P4 |
| attach:date | 9 | IRREDUCIBLE | date; kept in probe P4 |
| prompt | 42 | IRREDUCIBLE | the task itself |
| tool_schemas+framing | 15,812 | REDUCIBLE | probes P1 -> P3 remove 4,114 tokens via --tools "" --strict-mcp-config --disable-slash-commands |
| carry:tool_result | 15,635 | PAGEABLE | tool-output projection and paging exist (project events) |
| carry:response | 48,057 | HOST_LIMITED | host replays the assistant's own prior turns; no flag removes them |
| carry:attach:total_tokens_reminder | 570 | ELIMINABLE | 49 B per call, kept in every probe; candidate, no parity run |
| carry:attach:hook_additional_context | 314 | REDUCIBLE | hook prose; probe P4 (--setting-sources "") removes 10,569 B; candidate, no parity run |
| carry:attach:silent_turn_reminder | 116 | UNKNOWN | no measurement for this bucket |
| carry:attach:queued_command | 759 | UNKNOWN | no measurement for this bucket |
| carry:attach:edited_text_file | 170 | UNKNOWN | no measurement for this bucket |
| carry:attach:hook_blocking_error | 354 | UNKNOWN | no measurement for this bucket |
| carry:images | 7,292 | PAGEABLE | pixel GC tombstones images outside the window |
| carry:residual | -8,807 | UNKNOWN | carry not explained by sized buckets |

### f898280c (calls 6, offered tools 86, unit None; ctx call 1 74,809, last call 81,672)

| bucket | tokens | class | evidence |
|---|---:|---|---|
| section:lean_body | 535 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:communication | 31 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:pronouns | 119 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:action_caution | 173 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:session_guidance | 221 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:memory | 714 | ELIMINABLE | dropped by unit closure in V1 r2/r4, parity 5/5 |
| section:env_info_simple | 193 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:context_management | 93 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:act_dont_rederive | 92 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:heron_brook | 930 | REDUCIBLE | session-specific section, kept in probes P1-P4 and V1 (absent in Madzia lean+print); candidate |
| section:total_tokens | 16 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| attach:hook_success | 154 | UNKNOWN | no measurement for this bucket |
| attach:hook_additional_context | 1,853 | REDUCIBLE | hook prose; probe P4 (--setting-sources "") removes 10,569 B; candidate, no parity run |
| attach:environment | 315 | IRREDUCIBLE | cwd/platform; kept in probe P4 (every switch off) |
| attach:model | 42 | IRREDUCIBLE | model identity; kept in probe P4 |
| attach:deferred_tools_delta | 1,436 | PAGEABLE | names of deferred tools; ToolSearch pages them; absent in probe P3 (--tools "" --strict-mcp-config) |
| attach:agent_listing_delta | 8,750 | ELIMINABLE | dropped by unit closure in V1 r2/r4, parity 5/5 |
| attach:mcp_instructions_delta | 707 | ELIMINABLE | dropped by unit closure in V1 r2/r4, parity 5/5 |
| attach:skill_listing | 5,022 | ELIMINABLE | dropped by unit closure in V1 r2/r4, parity 5/5 |
| attach:total_tokens_reminder | 16 | ELIMINABLE | 49 B per call, kept in every probe; candidate, no parity run |
| attach:instructions | 26,142 | REDUCIBLE | unit kernel+index replace 78,400 -> 4,817 B (V1 r2/r4), parity 5/5 |
| attach:session_context | 269 | IRREDUCIBLE | kept in probe P4 |
| attach:date | 9 | IRREDUCIBLE | date; kept in probe P4 |
| attach:remote_session_change | 181 | ELIMINABLE | absent in probe P3; no role in a -p task; candidate, no parity run |
| prompt | 156 | IRREDUCIBLE | the task itself |
| tool_schemas+framing | 26,637 | REDUCIBLE | probes P1 -> P3 remove 4,114 tokens via --tools "" --strict-mcp-config --disable-slash-commands |
| carry:tool_result | 4,027 | EMBODIABLE | answer is script-computable (V1 truth.py): DETERMINISTIC_PATH embodies the reads |
| carry:response | 1,986 | HOST_LIMITED | host replays the assistant's own prior turns; no flag removes them |
| carry:attach:total_tokens_reminder | 98 | ELIMINABLE | 49 B per call, kept in every probe; candidate, no parity run |
| carry:attach:hook_additional_context | 155 | REDUCIBLE | hook prose; probe P4 (--setting-sources "") removes 10,569 B; candidate, no parity run |
| carry:residual | 597 | UNKNOWN | carry not explained by sized buckets |

### fa1e65cd (calls 4, offered tools 86, unit bounded-code-worker; ctx call 1 18,077, last call 22,049)

| bucket | tokens | class | evidence |
|---|---:|---|---|
| section:lean_body | 535 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:communication | 31 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:pronouns | 119 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:action_caution | 173 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:session_guidance | 221 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:env_info_simple | 193 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:context_management | 93 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:act_dont_rederive | 92 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:heron_brook | 930 | REDUCIBLE | session-specific section, kept in probes P1-P4 and V1 (absent in Madzia lean+print); candidate |
| section:total_tokens | 16 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| attach:hook_additional_context | 1,853 | REDUCIBLE | hook prose; probe P4 (--setting-sources "") removes 10,569 B; candidate, no parity run |
| attach:environment | 315 | IRREDUCIBLE | cwd/platform; kept in probe P4 (every switch off) |
| attach:model | 42 | IRREDUCIBLE | model identity; kept in probe P4 |
| attach:deferred_tools_delta | 1,424 | PAGEABLE | names of deferred tools; ToolSearch pages them; absent in probe P3 (--tools "" --strict-mcp-config) |
| attach:total_tokens_reminder | 16 | ELIMINABLE | 49 B per call, kept in every probe; candidate, no parity run |
| attach:instructions | 1,606 | REDUCIBLE | unit kernel+index replace 78,400 -> 4,817 B (V1 r2/r4), parity 5/5 |
| attach:session_context | 269 | IRREDUCIBLE | kept in probe P4 |
| attach:date | 9 | IRREDUCIBLE | date; kept in probe P4 |
| attach:remote_session_change | 181 | ELIMINABLE | absent in probe P3; no role in a -p task; candidate, no parity run |
| prompt | 156 | IRREDUCIBLE | the task itself |
| tool_schemas+framing | 9,799 | REDUCIBLE | probes P1 -> P3 remove 4,114 tokens via --tools "" --strict-mcp-config --disable-slash-commands |
| carry:tool_result | 1,801 | EMBODIABLE | answer is script-computable (V1 truth.py): DETERMINISTIC_PATH embodies the reads |
| carry:response | 1,585 | HOST_LIMITED | host replays the assistant's own prior turns; no flag removes them |
| carry:attach:deferred_tools_delta | 870 | PAGEABLE | names of deferred tools; ToolSearch pages them; absent in probe P3 (--tools "" --strict-mcp-config) |
| carry:attach:total_tokens_reminder | 59 | ELIMINABLE | 49 B per call, kept in every probe; candidate, no parity run |
| carry:residual | -343 | UNKNOWN | carry not explained by sized buckets |

### 228f7133 (calls 1, offered tools 0, unit bounded-code-worker; ctx call 1 10,155, last call 10,155)

| bucket | tokens | class | evidence |
|---|---:|---|---|
| section:lean_body | 535 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:communication | 31 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:pronouns | 119 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:action_caution | 173 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:session_guidance | 175 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:env_info_simple | 193 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:context_management | 93 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:act_dont_rederive | 92 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:heron_brook | 930 | REDUCIBLE | session-specific section, kept in probes P1-P4 and V1 (absent in Madzia lean+print); candidate |
| section:total_tokens | 16 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| attach:hook_additional_context | 3,524 | REDUCIBLE | hook prose; probe P4 (--setting-sources "") removes 10,569 B; candidate, no parity run |
| attach:environment | 234 | IRREDUCIBLE | cwd/platform; kept in probe P4 (every switch off) |
| attach:model | 42 | IRREDUCIBLE | model identity; kept in probe P4 |
| attach:total_tokens_reminder | 16 | ELIMINABLE | 49 B per call, kept in every probe; candidate, no parity run |
| attach:instructions | 2,151 | REDUCIBLE | unit kernel+index replace 78,400 -> 4,817 B (V1 r2/r4), parity 5/5 |
| attach:session_context | 441 | IRREDUCIBLE | kept in probe P4 |
| attach:date | 9 | IRREDUCIBLE | date; kept in probe P4 |
| prompt | 23 | IRREDUCIBLE | the task itself |
| tool_schemas+framing | 1,354 | UNKNOWN | no tools offered: residual is host framing plus calibration error, unsplit |

### 2ee1f371 (calls 1, offered tools 0, unit bounded-code-worker; ctx call 1 3,119, last call 3,119)

| bucket | tokens | class | evidence |
|---|---:|---|---|
| section:lean_body | 535 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:communication | 31 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:pronouns | 119 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:action_caution | 173 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:session_guidance | 175 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:env_info_simple | 193 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:context_management | 93 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:act_dont_rederive | 92 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:heron_brook | 930 | REDUCIBLE | session-specific section, kept in probes P1-P4 and V1 (absent in Madzia lean+print); candidate |
| section:total_tokens | 16 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| attach:environment | 234 | IRREDUCIBLE | cwd/platform; kept in probe P4 (every switch off) |
| attach:model | 42 | IRREDUCIBLE | model identity; kept in probe P4 |
| attach:total_tokens_reminder | 16 | ELIMINABLE | 49 B per call, kept in every probe; candidate, no parity run |
| attach:session_context | 441 | IRREDUCIBLE | kept in probe P4 |
| attach:date | 9 | IRREDUCIBLE | date; kept in probe P4 |
| prompt | 23 | IRREDUCIBLE | the task itself |
| tool_schemas+framing | -6 | UNKNOWN | no tools offered: residual is host framing plus calibration error, unsplit |

### 95ab3d08 (calls 1, offered tools 8, unit bounded-code-worker; ctx call 1 13,361, last call 13,361)

| bucket | tokens | class | evidence |
|---|---:|---|---|
| section:lean_body | 535 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:communication | 31 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:pronouns | 119 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:action_caution | 173 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:session_guidance | 175 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:env_info_simple | 193 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:context_management | 93 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:act_dont_rederive | 92 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:heron_brook | 930 | REDUCIBLE | session-specific section, kept in probes P1-P4 and V1 (absent in Madzia lean+print); candidate |
| section:total_tokens | 16 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| attach:hook_additional_context | 3,526 | REDUCIBLE | hook prose; probe P4 (--setting-sources "") removes 10,569 B; candidate, no parity run |
| attach:environment | 234 | IRREDUCIBLE | cwd/platform; kept in probe P4 (every switch off) |
| attach:model | 42 | IRREDUCIBLE | model identity; kept in probe P4 |
| attach:deferred_tools_delta | 492 | PAGEABLE | names of deferred tools; ToolSearch pages them; absent in probe P3 (--tools "" --strict-mcp-config) |
| attach:total_tokens_reminder | 16 | ELIMINABLE | 49 B per call, kept in every probe; candidate, no parity run |
| attach:instructions | 2,151 | REDUCIBLE | unit kernel+index replace 78,400 -> 4,817 B (V1 r2/r4), parity 5/5 |
| attach:session_context | 441 | IRREDUCIBLE | kept in probe P4 |
| attach:date | 9 | IRREDUCIBLE | date; kept in probe P4 |
| prompt | 23 | IRREDUCIBLE | the task itself |
| tool_schemas+framing | 4,067 | REDUCIBLE | probes P1 -> P3 remove 4,114 tokens via --tools "" --strict-mcp-config --disable-slash-commands |

### 99d97182 (calls 1, offered tools 35, unit bounded-code-worker; ctx call 1 14,269, last call 14,269)

| bucket | tokens | class | evidence |
|---|---:|---|---|
| section:lean_body | 535 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:communication | 31 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:pronouns | 119 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:action_caution | 173 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:session_guidance | 221 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:env_info_simple | 193 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:context_management | 93 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:act_dont_rederive | 92 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| section:heron_brook | 930 | REDUCIBLE | session-specific section, kept in probes P1-P4 and V1 (absent in Madzia lean+print); candidate |
| section:total_tokens | 16 | IRREDUCIBLE | CCR lean core, kept in probe P4; controllable by --system-prompt, so not a floor |
| attach:hook_additional_context | 3,524 | REDUCIBLE | hook prose; probe P4 (--setting-sources "") removes 10,569 B; candidate, no parity run |
| attach:environment | 234 | IRREDUCIBLE | cwd/platform; kept in probe P4 (every switch off) |
| attach:model | 42 | IRREDUCIBLE | model identity; kept in probe P4 |
| attach:deferred_tools_delta | 650 | PAGEABLE | names of deferred tools; ToolSearch pages them; absent in probe P3 (--tools "" --strict-mcp-config) |
| attach:total_tokens_reminder | 16 | ELIMINABLE | 49 B per call, kept in every probe; candidate, no parity run |
| attach:instructions | 2,151 | REDUCIBLE | unit kernel+index replace 78,400 -> 4,817 B (V1 r2/r4), parity 5/5 |
| attach:session_context | 441 | IRREDUCIBLE | kept in probe P4 |
| attach:date | 9 | IRREDUCIBLE | date; kept in probe P4 |
| attach:remote_session_change | 181 | ELIMINABLE | absent in probe P3; no role in a -p task; candidate, no parity run |
| prompt | 23 | IRREDUCIBLE | the task itself |
| tool_schemas+framing | 4,591 | REDUCIBLE | probes P1 -> P3 remove 4,114 tokens via --tools "" --strict-mcp-config --disable-slash-commands |

