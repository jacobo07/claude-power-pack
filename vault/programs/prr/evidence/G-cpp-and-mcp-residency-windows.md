# G. CPP-owned and MCP process residency, windows-laptop (2026-10-13)

Instrument: one read-only Win32_Process pass over node/python/bun/uv, grouped by command identity (working set =
resident; PrivatePageCount = commit). 149 processes, 1,947 MB resident in total. Plane: windows-laptop, live panes.

| Group | n | resident MB | commit MB | Owner / class |
|---|---|---|---|---|
| Next.js dev server + workers (`Apps/io-ql-dock/.../infinity_ui`) | 4 | ~1,385 | ~1,389 | another project's pane; NOT CPP. Largest single resident process on the host (990 MB) |
| hook-dispatcher.js | 3 | 115.5 | 30.6 | CPP_CONTROLLED (long-lived dispatcher) |
| gsdx_chain.py / gsd_mission.py / gsd_x_goal.py / a5_mission_notify.py | 6 | 152.4 | 106.1 | CPP_CONTROLLED (mission control plane) |
| kobi_graphify.py | 1 | 55.5 | 47.2 | CPP_CONTROLLED, **parent dead** (orphan) |
| lazarus-index-aggregator.js / context-watchdog.py | 2 | 68.7 | 59.9 | CPP_CONTROLLED |
| gsd-statusline.js | 11 | 47.3 | 38.7 | all 11 parent-dead (statusline children of closed panes) |
| notion MCP (bun x + node) | 18 | 30.2 | **668.7** | AVOIDABLE_BY_CONSTRUCTION: one copy per session, and notion fails to connect on this host (CONNECT_TIMEOUT) |
| playwright MCP | 1 | 11.3 | 97.8 | MCP, per session |
| background_verifier_run.py / delta.py / jit_ref_correlate.py | 15 | 13.9 | 5.4 | parent-dead, tiny |

## Reading
- CPP-owned long-lived residency on this plane is ~0.45 GB resident: real, but an order of magnitude below
  claude.exe (9.6 GB private resident over 39 processes, evidence F).
- MCP cost is per-session duplication (N sessions x 1 server each), visible mostly as commit, not resident. A
  server that cannot connect still costs ~37 MB commit per session.
- Orphans with dead parents are tiny in bytes. Their governance belongs to the reaper (c1513b35 for the
  suspended-probe class). The graphify orphan and the statusline children are not yet classified by the reaper rules.

## Next
- Same-PID drift of hook-dispatcher / gsdx_chain over hours (handles, timers, RSS slope): priority 6/11.
- Decide per-session vs shared MCP only with this duplication measured per server (priority 8 decision gate).
