# Resource Residency P0 + open P1 gate -- evidence (2026-11-20)

Tool: `tools/resource_census.py` (gate `python tools/test_resource_census.py`, 22 V-CENSUS-*, ALL PASS incl. a mutation drill
that removes the bare-command refusal and goes red). Counters: WS = psutil rss, private = PrivateUsage, commit = pagefile-charged;
host commit = GetPerformanceInfo. Snapshots in this directory carry counts and server names only (no args, env, signatures).

## MCP load, before P1 vs now (live sessions)
| | before P1 (plan reality scan, 21:38, Win32_Process) | now (`census-baseline-20261120.json`, 23:40) |
|---|---|---|
| claude.exe sessions | 22 | 25 |
| MCP processes | 271 (+108 conhost) | 114 attributed (conhost children included in their root) |
| MCP private | 12.28 GB | 5.18 GB (rea 3.97, google-ads 1.03, github 0.09, gex44-browser 0.05, mcp-search 0.03, ghost 0.02) |
| host commit / limit | 86.3 / 87.1 GB | 69.06 / 80.60 GB |

The remaining rea (x32, 16 sessions) and google-ads (x42, 14 sessions) belong to sessions born before P1 and to servers with
recorded use: RR-03 forbids stopping them, they leave when those sessions end (Owner step, not automated).
Two different methods produced the two columns (Win32_Process by cmdline vs this census); the delta is indicative, not a
like-for-like figure. UNATTRIBUTED: commit/limit movement (other writers active).

Refused as UNKNOWN by the signature rule (never attributed, never stopped): discord, fakechat, imessage, telegram (bun + flags only).

## Open P1 gate
1. Fresh PP session (`claude -p`, haiku, cwd = PP worktree, census at +20 s, `census-fresh-pp-session.json`): it spawned
   `gex44-browser` + `github` only (both deliberately kept in P1); 0 catalogued servers (rea, google-ads, coplay, linkedin,
   linkedin-post, carla-meta, notion, skool, magic-ui, playwright). PASS.
2. Fresh GEO-audit session (`claude -p`, haiku, cwd GEO-audit, `--allowedTools mcp__google-ads`, read-only prompt): replied
   `mcp__google-ads__list_google_ads_accounts returned 2 accounts.` (a real tool name from the server; account ids not shown). PASS.

## Matcher defects found and fixed while building the census
- `npx -y <pkg>`: `-y` consumed the package as a flag value, so google-ads was unattributable (gate V-CENSUS-NPX-Y-PACKAGE-IS-SIGNATURE).
- Servers launched by a binary path with 0 args (ghost) were refused; a path to a non-launcher binary is now a signature.
- A plugin config wrapper key (`mcpServers`) was read as a server name.
