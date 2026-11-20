# Requirements — resource-residency (v1)

- **RR-01** Every memory figure names its counter (WS, private, commit, pool) and the command that produced it.
- **RR-02** A process is attributed to an MCP server only by a signature that cannot match unrelated processes;
  otherwise UNKNOWN. UNKNOWN is never stopped, shared or reclaimed.
- **RR-03** No automation stops a claude.exe session or an MCP of a server with recorded use; those are Owner steps.
- **RR-04** Every change to `~/.claude.json` or a `.mcp.json` goes through `tools/mcp_scope.py` (or an equivalent with a
  backup and compare-and-swap); full server configs never enter the repo or any log.
- **RR-05** Each mechanism has a kill switch (`CPP_MCP_SCOPE`, `CPP_MCP_LAZY`, `CPP_MCP_IDLE_RECLAIM`,
  `CPP_SESSION_HIBERNATION`, `CPP_COMMIT_GOVERNOR`), each exercised once by a test.
- **RR-06** Every new gate has a mutation drill that goes red.
- **RR-07** The pagefile setting is changed only by the Owner, after the Phase 8 benchmark.
- **RR-08** Availability is preserved: a catalogued server comes back with one command and is proven to work after it.
