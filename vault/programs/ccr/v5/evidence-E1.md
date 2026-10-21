# E1 evidence: floor decomposition, lean profile, context admission

Full table, calibration and limits: `E1-floor-decomposition.md` (commit 1cbd1cb5). Source receipts: 41 multi-call sessions in `/home/kobii/missions/ccr-s3-data/pack/receipts` on GEX44, read with `tools/ccr_anatomy.py table` (call-1 3.01 B/token, carry 2.494 B/token, both calibrated, none assumed).

## Part 1: decomposition (call-1 context median 82,298)

| component | tokens (median) | class | source receipt |
|---|---:|---|---|
| attach:instructions | 31,103 | REDUCIBLE | GEX44 receipts, 35/41 sessions |
| tool_schemas+framing | 27,025 | REDUCIBLE | GEX44 receipts, 41/41 |
| attach:skill_listing | 9,988 | ELIMINABLE | GEX44 receipts, 33/41 |
| attach:agent_listing_delta | 9,075 | ELIMINABLE | GEX44 receipts, 28/41 |
| attach:hook_additional_context | 1,847 | REDUCIBLE | GEX44 receipts, 40/41 |
| attach:deferred_tools_delta | 1,477 | PAGEABLE | GEX44 receipts, 35/41 |
| section:heron_brook | 927 | REDUCIBLE | GEX44 receipts, 6/41 |
| attach:mcp_instructions_delta | 704 | ELIMINABLE | GEX44 receipts, 39/41 |
| section:memory | 698 | ELIMINABLE | GEX44 receipts, 33/41 |
| attach:remote_session_change + total_tokens_reminder | 197 | ELIMINABLE | GEX44 receipts |
| IRREDUCIBLE (14 rows) | 2,299 | IRREDUCIBLE | GEX44 receipts, 41/41 |

REDUCIBLE rows sum 60,902; all classified rows sum 85,340 = 103.7% of the call-1 median (row medians come from different session subsets, so they are not additive). UNKNOWN rows (22,978, sparse) are excluded and stay unclassified.

## Part 2: lean launch profile for workers

No new profile was needed: `slim-t2` already exists (`slim_argv` in `tools/gsd_mission.py`, floor 13,507 in `vault/config/route-floors.json`, `route-E1.json` already names it). Each flag it passes removes a decomposed component:

| flag | removes |
|---|---|
| `--setting-sources=local` | instructions (CLAUDE.md chain), hook prose, memory |
| `--disable-slash-commands` | skill listing |
| `--strict-mcp-config` | MCP instructions, deferred-tool names |
| `--tools=<list>` | tool schemas beyond the listed tools |
| `--system-prompt` + `--exclude-dynamic-system-prompt-sections` | default system prompt and dynamic sections |

Predicted call-1 saving against the GEX44 worker median: 82,298 - 13,507 = 68,791 tokens per worker. No `settings.json` edit was made or is needed (the budget breaker travels in `vault/config/slim-critical-settings.json`, which the profile `requires`).

## Part 3: Context Admission check at arm

`route_admission.context_check` (called from `gsd_mission.admit_route`, which `arm_chain` runs) compares the floor a route is priced at with the first-call context receipts show for that profile: OK, UNDERSTATED (measured median > 1.25 x floor), or UNMEASURED (fewer than 3 sessions or no row; absence is never OK). Default is observe: the result is recorded in `admission["context_check"]`. `CPP_CONTEXT_ADMISSION=enforce` turns UNDERSTATED into RECOMPILE. Measured medians are read from `vault/config/measured-ctx1.json` (absent file = every profile UNMEASURED).

Test output (run from the worktree root with `python -I`):
```
CTX_PASS=10/10  threshold=all          (tools/test_context_admission.py)
ADM_PASS=43/43                          (tools/test_gsd_mission_admission.py)
EST_PASS=9/9                            (tools/test_route_estimator.py)
```

## Limits
- `slim-t2` floor rests on n=2 sessions; no fresh parity run was made in this unit.
- `vault/config/measured-ctx1.json` is not created: the GEX44 receipts carry no profile label, so no per-profile sample set can be written without inventing the mapping. Until it exists the check reports UNMEASURED and refuses nothing.
- Enforce mode is opt-in and has no live arm run behind it.
- Classifications for hook prose, `heron_brook`, `remote_session_change` and `total_tokens_reminder` are candidates (see the decomposition doc).
