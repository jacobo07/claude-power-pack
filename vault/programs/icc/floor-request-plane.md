# ICC W0 A1 -- request-plane floor probes (2026-11-05)
Plane: REQUEST (API usage of call 1 = input + cache_creation + cache_read), `claude -p --model haiku`, n=3/arm, pinned session ids,
cwd = ICC worktree. Driver: `floor_probe.py`; raw: `floor-request-plane.json`. Not transcript chars.

| Arm | median call-1 tokens | delta vs control |
|---|---|---|
| control | 78,179 | -- |
| CCR_MAIN_CANARY=0 | 78,220 | +41 (noise) |
| --strict-mcp-config, empty MCP | 74,619 | -3,560 |

Reading:
- MCP server names + instructions marginal cost in `-p` = ~3.56k request tokens. Residual hard floor (system prompt + built-in tool
  schemas + CLAUDE.md/memory chain + hooks) = ~74.6k in this cwd.
- CCR main canary has NO measurable effect in `-p` (+41 = noise, spread within arm ~1.2k on control). Either the canary does not
  engage in headless `-p`, or its savings are not on the call-1 request. So "CCR strips listings" is UNMEASURED on this path;
  the interactive-pane figure (71,883 at arm) must come from a pane probe, not `-p`. Do not claim canary savings from this table.
- Interactive ~71.9k vs `-p` ~78.2k: planes differ; never compare across them.