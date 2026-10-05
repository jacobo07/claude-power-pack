# Pillar K -- deferred-tools rise: attribution, host lever, budget

Session c59ad762, 2026-10-05, laptop, Claude Code 2.1.290, HEAD b7170420.

## Attribution (fa7e93cb vs reference 8f983bc6, `deferred_tools_delta` attachment)

| | reference | now |
|---|---|---|
| names | 72 | 113 |
| attachment chars (gate unit, `other:deferred_tools_delta`) | 5,116 | 8,494 |
| removed names | 0 | 0 |

All 41 added names are claude.ai connectors: `mcp__claude_ai_Gmail__*` 30, `mcp__claude_ai_Google_Drive__*` 11. The
announcement carries **names only** (~37 chars each); descriptions and schemas are NOT resident, they load on demand
through ToolSearch -- the deferral of descriptions works. The names themselves scale linearly with connected tools
(113 names: Gmail 30, gex44-browser 25, notion 24, built-in 15, Google Drive 11, Claude Docs 8). Producer: the host,
from MCP servers configured for the account (claude.ai connectors) and settings; no CPP code emits them.

## Host lever (measured, one headless session, $0.48)

    cd C:\Users\User\Apps\listing-probe\champion
    claude -p "Reply with the single word OK." --strict-mcp-config --max-turns 1 --output-format json
    session 38e32976-6a74-468b-9305-747bd71918df

| | default launch (6eba7a1f) | `--strict-mcp-config` (38e32976) |
|---|---|---|
| deferred names | 113 | 15 (built-in only) |
| deferred attachment chars | 8,494 | 591 |
| mcp_instructions_delta | present (2,038) | absent |
| first-call tokens | 80,241 | 76,517 |

So the host DOES permit tool-surface specialization for a headless launch: `--strict-mcp-config` drops every MCP
server not passed by `--mcp-config`, claude.ai connectors included. `--tools` and `--bare` are further levers
(`claude --help`). An interactive session has no such launch flag: there the connector names are account floor.

## Decision (Owner 2026-10-05: "Budget as account floor")

- K probe launch stays the reference's kind (no flag), so the comparison stays valid; the +3,378 is carried as an
  accepted, evidenced budget on `other:deferred_tools_delta` (explanation in `floor/reference.json`, commit 9),
  bound 3,400 chars, review when the connector set changes. The reference's components are not touched.
- Worker launches (gsd_mission / Ralph, probes that are not K checks) passing `--strict-mcp-config` with a Work-Unit
  `--mcp-config` would remove ~7.9 k chars of names and ~2 k of MCP instructions per headless worker. That is a
  launcher change (gsd_mission.py, deploy gated at >= 4 GB free RAM by audit G6) and belongs to the deferred
  tool-surface specialization phase (cognitive-microkernel brief), with discoverability measured before it ships.
