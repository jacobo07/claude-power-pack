---
covers: [resource-residency-fabric, mcp-scope, mcp-lazy, session-residency, commit-governor]
tier: T2
status: APPROVED -- P1 + P1-NOW executed inline; P0, P2-P8 pending (mission not yet armed)
owner_decision: "go residencia" (2026-11-20 ~23:00)
---

## Execution log
**2026-11-20 23:02-23:20, P1 + P1-NOW (session 54c0ea73)**
- Backup `~/.claude-json-backup-residency-20261120-230207.json` (hash-equal at copy).
- 90 d usage map: 4,929 transcripts. Zero calls: coplay-mcp, linkedin, linkedin-post, carla-meta, notion, skool,
  magic-ui, playwright. rea 3 (Capy RE 2, Credit Score Engine 1), google-ads 21 (GEO-audit), gex44 115 (7 cwds),
  vercel 46, wix 22.
- `tools/mcp_scope.py` (V-MCPSCOPE-* 15/15 PASS): user scope 13 -> 3 (gex44-browser, vercel, wix kept: 7-project
  use / http with no local process). 8 to catalog, google-ads -> GEO-audit, rea -> Capy RE + Credit Score Engine.
  `~/.claude/.mcp.json` (project scope of every session under ~/.claude): notion + @21st-dev/magic removed
  (backup `~/.claude-mcpjson-backup-residency-20261120-231951.json`); github kept (20 calls).
- Gate: `claude mcp list` from PP shows only gex44/vercel/wix (+ the .mcp.json notion, since removed);
  from GEO-audit google-ads `Connected`. A real `mcp__google-ads__*` call in a fresh GEO-audit session: NOT YET RUN.
- P1-NOW dry run caught a matcher defect: playwright's config (`mcp`, 0 args) matched 751 processes / 66.6 GB of
  unrelated MCP trees. Excluded; never killed. Applied to 5 servers: 62 roots / 267 processes / 7.14 GB private /
  0.96 GB WS, all with a live claude.exe ancestor; pid+creation time re-checked before each kill; after: 0 left,
  22 claude.exe still alive.
- Host deltas in that window (other writers active, so only the census figure is attributed): commit 81.73 -> 64.71 GB,
  pagefile alloc 57.6 -> 49.3 GB (Windows shrank it), free C: 14.74 -> 36.65 GB (8.3 GB = pagefile; rest UNATTRIBUTED).
- li-* skills: no skill references the retired MCP tools -> gate NO APLICA.
# Resource Residency Fabric -- plan (2026-11-20)

Law: availability scales with the institution; residency scales with current demand.
Mode: PLAN (no ULTRA). Repo reality makes the path decision-sufficient: MCP residency is owned by ONE file
(`~/.claude.json` user-scope `mcpServers`, 13 servers; only 4 of 111 projects carry their own scope). No PP module
owns MCP lifecycle today (grep of modules/tools/hooks/specs: no resource-residency / mcp-scope owner).

## Reality scan (sealed 2026-11-20 21:38, commands in session 54c0ea73)
| metric | value | source |
|---|---|---|
| RAM / free physical | 31.3 GB / 0.7 GB | Win32_OperatingSystem |
| commit / limit | **86.3 / 87.1 GB** | PerfOS_Memory |
| pagefile alloc / used / peak | **55.8 / 8.9 / 9.1 GB** (was 32 GB on 11-18, 51.8 at 21:15) | Win32_PageFileUsage |
| free C: | 9.57 GB | Get-PSDrive |
| processes / conhost / threads | 872 / 156 / 11,155 | Win32_Process |
| kernel pools paged / nonpaged | 3.95 / 3.95 GB | PerfOS_Memory |
| claude.exe | x22, WS 6.78 GB, private 29.92 GB | Win32_Process |
| MCP processes | **x271, WS 1.13 GB, private 12.28 GB**, +108 conhost children | Win32_Process by cmdline |

MCP private by server: rea 4.19 (x17), linkedin 2.26 (x65), coplay 2.07 (x65), linkedin-post 1.43 (x48),
google-ads 1.08 (x30), carla-meta 0.77 (x17), notion 0.24, playwright 0.18, gex44 0.05, ghost 0.01.
WS/private = 9 %: MCP rent is almost pure COMMIT rent (paged out), i.e. exactly what grows the pagefile.

Usage (14 d, 2,244 transcripts, `tool_use` names `mcp__<server>__`):
ghost 591 (TUA-X, InfinityOps-17; project-scoped already), gex44-browser 63 (Capy-RE 45, Vibe 16, Lokma 2),
wix 22 (Lokma, http), google-ads 21 (GEO-audit only), rea 2 (Capy-RE), github 16, claude.ai connectors (no local
process). **Zero calls: coplay, linkedin, linkedin-post, carla-meta, notion, skool, magic-ui, playwright, vercel.**

Liveness of MCP processes: 231/231 sampled had a live claude.exe ancestor (not orphans) -> eager per-session birth.
Secret note: `magic-ui` carries an API key in plaintext `args` in `~/.claude.json` (not echoed; HR-SECRET-003:
recommend rotation, never auto-rotate).

## Phases (each = micro-commits, Production Reality on real sessions)
- **P0 census tool** (`tools/resource_census.py`): birth identity (pid+creation time), ancestry to claude.exe/session id,
  WS vs private vs commit kept separate, MCP server attribution, conhost children, JSON snapshot + diff. Feeds every gate.
- **P1 scope elimination (first physical value)**: generate the scope map from transcript usage (90 d window, not 14),
  move servers out of user scope into the project scope of the projects that used them; zero-use servers go to a
  PP-owned registry (`vault/registry/mcp_catalog.json`) with a one-command rematerialization
  (`tools/mcp_scope.py enable <server> --project <path>`). Backup of `~/.claude.json` first; rollback = restore.
  Gate: a fresh session in PP spawns 0 of the moved servers; a fresh session in GEO-audit still gets google-ads and a
  real `mcp__google-ads__*` call succeeds; li-* skills name the enable command.
- **P1-NOW (Owner-authorised only)**: stop the MCP processes of zero-use servers inside LIVE sessions (tools vanish in
  those sessions, sessions continue). Expected: ~170 processes, ~6.8 GB private. Measured by census diff.
- **P2 lazy materialization**: Claude Code 2.1.329 has deferred tool *schemas* (ToolSearch) but spawns every stdio
  server at session start. Experiment: a stdio shim that answers `initialize`/`tools/list` from a cached schema and
  spawns the real server on the first `tools/call`; kill switch `CPP_MCP_LAZY=off`. Gate: commit before/after first
  use, first-call latency, tool correctness on google-ads + gex44. If the host rejects cached schemas -> METHOD_FAILED,
  stay on P1 scoping.
- **P3 lease + idle teardown** inside the shim (last consumer gone -> reclaim after a per-server warm window derived
  from measured cold start).
- **P4 shareability**: classify each server (stdio, auth, cwd, state). UNKNOWN never shared. Pooling only for a proven
  SHAREABLE class with positive measured ROI.
- **P5 session liveness + hibernation** (largest rent: claude.exe 29.9 GB private): classifier from CPU, child
  processes, background tasks, transcript tail, mission lease; UNKNOWN protected. Shadow first, then one canary
  hibernate -> `--resume` round trip with measured resume correctness.
- **P6 commit-pressure governor** (shadow -> advisory): thresholds derived from commit limit and pagefile growth;
  never kills ACTIVE/UNKNOWN; under pressure refuses optional MCP births and proposes hibernation.
- **P7 resource-budget CI**: a new user-scope MCP is flagged with its projected per-session rent.
- **P8 pagefile right-sizing**: LAST, only after a steady-state benchmark (commit P95 + margin).
- Cursor-proper and rea re-measure after P1/P2 (descendants removed).

## Gates
Early value: P1 must show a measured MCP-count and commit drop on a fresh real session before P2 starts, else
METHOD_PIVOT_REQUIRED. Two consecutive intervals without a physical delta -> breaker. Planning spend before the first
code/evidence commit <= 1.5M tokens (this plan included).
Master gate: the 48-item list of the Owner prompt, judged item by item at close (NO APLICA with reason allowed).

## Rollback / kill switches
`~/.claude.json` backup per change (restore = copy back); `CPP_MCP_SCOPE=off` (registry ignored), `CPP_MCP_LAZY=off`,
`CPP_MCP_IDLE_RECLAIM=off`, `CPP_SESSION_HIBERNATION=off`, `CPP_COMMIT_GOVERNOR=off`. Each tested once.

## Agent topology
Integration owner = the mission worker. At most ONE subagent at a time (adversarial safety review before P1-NOW,
P5 enforcement). Fan-out is the problem being fixed.

## Budget (tokens, bottom-up)
P0 1.5M, P1 3M, P2 6M, P3 3M, P4 2M, P5 8M, P6 4M, P7 2M, P8+benchmark 4M, docs/UKDL/close 2.5M.
Lower bound 18M; P50 36M; P80 48M; P95 62M; hard authority 70M (ceiling, not target); reserve 8M.
Max cycles 14, max hours 30. Per-wave ceiling = 1.5x its line. Arm: authority 40M + 2 top-ups of 15M.

## Order of execution (self-dogfood)
P1 runs INLINE in the arming session before `arm`, so the background worker is born without the dead MCP estate
(host is at 86.3/87.1 GB commit: one more eager session costs ~1.9 GB).

## Addendum 2026-11-21 -- control plane (Owner mid-flight prompt; PROPOSED, awaiting "go tranche")
Reality scan 14:33-14:50 (session 54c0ea73), the addendum's premises checked against evidence:
- Mission m-e78bdb938339: state LAUNCHING, worker null since the wall at 14:06 (last write of transcript e5ca940c
  14:06:46); no sweep action logged for it after 12:02Z. P2 NOT started (worker's last turn: "I did no Phase 2 work:
  the context wall was hit"). P5 not started. Worktree HEAD 3728e9c06, 9 untracked doc stubs. Mission meter 7.89M / 40M.
- Startup context: first call of the P0 worker = 97,128 tokens (all cache creation), NOT 148K. 148-151K is the MEAN per
  call of a 95-call session growing to the 175K advisory wall (max 196,953). Sum of per-call context over the session
  14.41M; the mission meter counts 7.89M (two instruments, both labelled). First Edit at call 27.
- Unauthorized push, root cause: the worker called git through a variable from the PowerShell tool at 23:53:24 (reflog
  "update by push"; transcript e5ca940c line 697). ovo-push-gate.js IS registered in the dispatcher's Bash|PowerShell
  chain and `.powerpack` exists, but BLOCK_REGEX requires the literal word pair at a command boundary: the real command
  (git via `$g`) does not match. Inverse defect observed the same day: the gate blocked a PowerShell call of this
  session whose here-string only QUOTED the word pair after a backtick (no push ran). The host's own Woz advisory tells
  agents to call git by full path or variable, i.e. the shape that evades the gate. The gate is a quality-verdict gate,
  not an authority gate; laptop missions carry no push-authority field (only CPP_MISSION_PUSH for policy phrasing).
- Exposure: origin is PUBLIC (github.com/jacobo07/claude-power-pack). Only b74fe8d74 is not on another remote branch;
  no secret values in its files; mcp_catalog.json names 3 project folders (Capy RE, Credit Score Engine, GEO-audit).
- Host 14:33: commit 69.6/80.5 GB, pagefile 49.2 GB, free RAM 1.8/31.3 GB, free C: 24.4 GB, 627 processes, 25 claude.exe.

### A. Current tranche completion (inside the approved 40M; no new authority)
- W0 push immunity, BEFORE any worker relaunch: (a) the repo's pre-push git hook (the strongest controllable layer:
  every shell and invocation shape reaches it) refuses when the pushing process descends from a mission worker whose
  record has no push authority; (b) ovo-push-gate matches git by path / variable / `-C`, and stops matching quoted text;
  (c) historical regression = the exact 23:53 command shape, both poles, plus the false-positive shape of 2026-11-21;
  (d) mission record field `push_authority`, default none. Line 1.5M.
- Diagnose and fix the stuck relay (LAUNCHING, worker null) once W0 is live; relaunch once.
- P2 lazy MCP (line 12M, stop 18M); P5 liveness shadow (line 8M, stop 12M; extends
  modules/cognitive_os/process_governor.py); close 3M. Close status "TRANCHE COMPLETE", never "RESOURCE RESIDENCY
  COMPLETE"; next frontier ranked by measured rent.
- Dogfood: per epoch record first-call context, mean context, calls to first edit (scratch instrument promoted to a tool).
Budget remaining: lower 12M, P50 22M, P80 30M, P95 38M; authority 40M (7.89M spent) + 2 x 15M top-ups already granted;
reserve 5M; cycles <= 10; hours <= 24; per-wave ceiling 1.5x its line.

### B. Next control-plane tranche (ESTIMATE ONLY; separate approval after A closes)
Order derived at close from measured rent. Default candidates: lease + idle reclaim inside the P2 shim; session
hibernation canary (Owner-run) + zero-process wait for missions parked BLOCKED; admission (refuse optional MCP birth
under pressure); resource explain (why is pid X alive / who owns it). Lower 18M, P50 30M, P80 42M, P95 55M. Rotation
wall 175K -> ~120K (card-carried) only if tranche A's epoch data shows mean-context savings exceed the extra 97K starts.
Deferred items (P3 lease/idle, P4 shareability, P6 governor, P7 resource CI, cross-node, pools) carry owner / trigger /
reopen condition here, not in deferred-backlog.md (foreign dirty state there).

**APPROVED 2026-11-21 (Owner "Solo tramo B", after A closed: m-e78bdb938339 COMPLETED, integrated ba190506; no push).**
Order from measured rent at ~19:00 (claude.exe x23 30.5 GB private >> rea 2.73 GB >> powershell x40 2.76 GB owner
unknown >> other MCP < 0.2 GB): workstream `.planning/workstreams/resource-residency-b/` -- P1 explain + A debt 3M,
P2 liveness v2 6M, P3 rea lazy + idle reclaim 7M, P4 zero-process wait 7M (measure first, NO APLICA if negligible),
P5 admission shadow 4M, P6 close 3M = 30M (P50). Authority 40M + 1 x 15M top-up (P95 55M). Rotation wall unchanged
(tranche A recorded no per-epoch mean-context data to justify 120K).
