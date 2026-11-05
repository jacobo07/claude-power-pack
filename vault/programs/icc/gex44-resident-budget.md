# GEX44 resident budget (ICC Phase 1, ICC-11)

Measured 2026-11-05, read-only on GEX44 (host kobii@5.9.23.174), newest `-home-kobii` transcript
`f775dbf4`, `floor_regression_gate.py --write-reference` to `/tmp` (no write under GEX44 `~/.claude`).
PLANE: **recorded plane** (transcript chars), except the one `first_call_total` which is the transcript's call-1 usage
(request plane, one session, n=1). Recorded chars are NOT request tokens.

call-1 total (request plane, n=1): **54,407 tokens**; recorded floor 109,544 chars.
The laptop figure (71,883, 78,179 in -p) is another plane and another install: the gate itself refuses to compare them
("fields differ: plane, platform, install_home, cwd" -> UNMEASURABLE). Do not subtract one from the other.

| Layer (recorded chars) | GEX44 | Note |
|---|---:|---|
| skill_listing (unattributed + universal) | 30,000 | at the harness listing budget; 194 skill dirs, a new skill displaces descriptions |
| agent_listing_delta | 27,971 | 95 agent files |
| rules | 17,308 | 23 rule files in `~/.claude/rules` (16,941 B on disk) |
| system_prompt | 7,410 | harness |
| memory_global (`~/.claude/CLAUDE.md`) | 6,892 | file is 6,938 B |
| deferred_tools_delta | 6,722 | far below laptop 45,603 (fewer MCP servers) |
| SessionStart hook context | 7,434 | 4,029 + 3,405 |
| UserPromptSubmit hook context | 2,460 | |
| mcp_instructions_delta | 2,033 | |
| harness misc | ~1,300 | |

Resident budget (proposal, GEX44 recorded plane): total <= 115,000 chars; skill_listing <= 30,000 (cap, already binding);
agent_listing <= 28,000; rules <= 17,500; memory_global <= 7,000. A layer over budget = review, not auto-fail, until a
floor-CI reference exists on GEX44 (Phase 6).

## Dangling doctrine pointers in GEX44 `~/.claude/CLAUDE.md`
Of the `~/.claude/...` paths it names, exactly two do not exist on GEX44:
- `~/.claude/knowledge_vault/core/HARD-RULES-DIGEST.md`
- `~/.claude/SESSION_SAFETY_CONTRACT.md`

Effect: the HARD RULES router tells a GEX44 session to read a digest that is not there. Fixing it is a write under GEX44
`~/.claude` (HR-001) -> see `OWNER_STEPS.md`. Not done by this mission.

## The -13,786 attribution
The original delta compared a laptop reference with a GEX44 session; the gate classes that as `not_comparable`, so a
per-layer attribution of that figure is **UNMEASURABLE** by construction. What is measured instead is the table above
(GEX44 against itself). Remaining gap: no GEX44 reference file is committed, so GEX44 has no regression gate yet (Phase 6).
