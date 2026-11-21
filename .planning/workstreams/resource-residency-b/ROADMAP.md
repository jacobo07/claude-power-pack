# Roadmap — resource-residency-b (Tranche B, control plane)

Authority: Owner "Solo tramo B" (2026-11-21, session 54c0ea73) on `vault/plans/resource-residency-fabric-20261120.md`
Addendum B. Tranche A is CLOSED (mission m-e78bdb938339 COMPLETED, integrated ba190506): read
`vault/programs/resource-residency/P8-CLOSE.md` and the Tranche A STATE (`.planning/workstreams/resource-residency/STATE.md`)
first and do NOT re-measure what they state. Owners to EXTEND (never a parallel system): `tools/resource_census.py`,
`tools/mcp_lazy_shim.py` + `tools/mcp_scope.py`, `tools/session_liveness.py`, `tools/gsd_mission.py`,
`modules/cognitive_os/process_governor.py`.

Rent ranking that orders this tranche (measured 2026-11-21 ~19:00, `resource_census.py snapshot` + psutil private bytes):
claude.exe x23 = 30.5 GB private (11.5 GB WS) >> rea MCP 22 procs / 11 sessions = 2.73 GB >> powershell.exe x40 =
2.76 GB (owner unknown) >> every other MCP < 0.2 GB. Host commit 71.3 / 76.9 GB, free RAM 1.7 GB.

PLANE: laptop, PP root, shared tree (other writers' dirty files: never stage them; `vault/plans/deferred-backlog.md`,
`.planning/STATE.md` root, `vault/knowledge_base/ukdl-universal.md` carry foreign hunks -- append to UKDL only through a
private-index blob, as ba190506 did). Commit only your hunks with exact pathspec; verify `git log -1` after each commit.
**Commit only; no push authority** (machinery since 699ddb9a: a refusal is expected, do not retry or work around it).
EXECUTION mode. At most ONE subagent at a time. Few large turns; no re-reads of what STATE.md summarises.
Memory: working set, private and commit are three numbers, never one "RAM" number; every freed figure is a measured
before/after with its command; unattributable deltas are UNATTRIBUTED. **UNKNOWN is never reclaimable.**
Never stop an interactive claude.exe session, never stop an MCP process of a server with recorded use, never touch the
pagefile: those are Owner steps (BLOCKED-ON-OWNER, numbered, in STATE.md) while you continue elsewhere.
Measure your spend per phase and record it; a phase over 1.5x its line -> stop with a one-line Owner note.
Two consecutive phases without a measured physical delta or a decision-grade measurement -> BREAKER in STATE.md, stop.
Each phase: kill switch, both-pole gates on real byte shapes, a mutation drill that goes red, then a LIVE gate on the
real host (Tranche A lesson T-LAZY-SHIM-SYNTHETIC-GREEN-001: synthetic green missed two live defects).
Per epoch record in STATE.md: first-call context, mean context, calls to first Edit.
Close status "TRANCHE B COMPLETE" -- never "RESOURCE RESIDENCY COMPLETE".

## Phases

- [ ] **Phase 1: resource explain + Tranche A debt** -- line 3M, stop 4.5M
- [ ] **Phase 2: liveness v2 (IDLE candidates with evidence, shadow)** -- line 6M, stop 9M
- [ ] **Phase 3: rea lazy + idle reclaim in the shim** -- line 7M, stop 10.5M
- [ ] **Phase 4: zero-process wait for parked missions** -- line 7M, stop 10.5M
- [ ] **Phase 5: admission under commit pressure (shadow)** -- line 4M, stop 6M
- [ ] **Phase 6: close** -- line 3M

## Phase Details

### Phase 1: resource explain + Tranche A debt
**Depends on**: nothing. Line 3M.
- `resource_census.py explain <pid>`: ancestry to its claude.exe / session id / mission / scheduled task, MCP server,
  age, private/WS/commit, and a verdict OWNED(<owner>) / ORPHAN(evidence) / UNKNOWN. Run it over the powershell.exe x40
  and node.exe population and commit the table (who owns 2.76 GB of shells). Explain only: nothing is stopped.
- V-LAZY gates pinning the two live-only paths of 87a5572c: `server/discover` -> -32601 without spawn; prompts/list and
  resources/list served from cache without spawn. Each must go red on the pre-87a5572c behaviour.

### Phase 2: liveness v2
**Depends on**: Phase 1. Line 6M. Extend `tools/session_liveness.py` (Tranche A: ACTIVE 21 / IDLE 0 / UNKNOWN 7 of 28,
threshold too sensitive, interactive pid -> session unmapped).
- Map an interactive claude.exe pid to its session id (transcript handle, cwd + create time, or the hub's beacon);
  unmapped stays UNKNOWN.
- Calibrate from a multi-sample window (>= 10 samples over >= 10 min), never one CPU sample, never transcript age alone.
- Output: IDLE candidates, each with its evidence, its private bytes and the exact Owner command for a hibernate ->
  `claude --resume <sid>` canary (BLOCKED-ON-OWNER). Kill switch `CPP_SESSION_HIBERNATION=off`. Nothing is stopped.
- Gate: on the live host the report names >= 1 IDLE with evidence OR records why none qualifies (decision-grade).

### Phase 3: rea lazy + idle reclaim
**Depends on**: Phase 1. Line 7M. Second-largest rent (2.73 GB).
- `mcp_scope.py lazy rea` in ONE project where rea has recorded use (backup per change; rollback `unlazy`).
- Inside the shim: after the last tools/call, reclaim the real server after a warm window derived from its MEASURED cold
  start (kill switch `CPP_MCP_IDLE_RECLAIM=off`); next tools/call respawns transparently.
- Live gate: fresh session in that project -> 0 real rea processes until first call; a real read-only call succeeds;
  after the window the child is gone and a second call respawns and succeeds. Census before/after with the three numbers.
  If the host rejects the shim for rea: METHOD_FAILED recorded, unlazy, continue.

### Phase 4: zero-process wait
**Depends on**: Phase 1. Line 7M. Extend `tools/gsd_mission.py`.
- First MEASURE: how many live claude.exe belong to missions parked BLOCKED / owner_hold / authority hold, and their
  private bytes. Zero or negligible -> NO APLICA with the number, skip to Phase 5.
- Otherwise: a mission parked longer than a threshold, with no pending background child, has its worker stopped through
  the host (the existing relay stop path, exact `--session-id` match only) and is resumed with `claude --bg --resume
  <sid>` on release. Only mission workers; never an interactive session. Kill switch `CPP_MISSION_ZERO_PROCESS_WAIT=off`.
- Gate: both poles in V-MC style + one live canary on a throwaway mission; the existing mission suites stay green.

### Phase 5: admission under commit pressure
**Depends on**: Phase 3. Line 4M. In the shim: when host commit > threshold (derived from commit limit and the measured
pagefile growth), an OPTIONAL server's first spawn is refused with a clear MCP error and logged; shadow (log only) by
default. Kill switch `CPP_MCP_ADMISSION=off`. Gate: both poles with an injected commit reading; live shadow log on host.

### Phase 6: close
**Depends on**: Phases 1-5. Line 3M. Two-snapshot census delta with confounds named; master gate item by item (NO APLICA
allowed with reason); Owner steps; UKDL entries via private-index append; next frontier ranked by measured rent.
