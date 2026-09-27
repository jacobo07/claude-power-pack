# 2026-09-27 -- mission supervisor: 48 workers, zero work (m-66ebaaa0324e lineage)

Worktree `C:\Users\User\Apps\pp-mission-fix`, branch `fix/mission-supervisor-blocked` (from 9f750fa).
Progress log, appended as each fact is confirmed.

## Findings

- F0 `tools/gsd_mission.py:372-374` liveness(): a host row with `state:"blocked"`, no `status`,
  no `waitingFor` reads LIVE "host lists session blocked"; `owner_idle()` (:909) treats exactly
  that shape as "turn ended" (W0 measurement), so plan_next (:478) plans `relay`.
- F1 (hypothesis "untrusted cwd" REFUTED, 2026-09-28): `~/.claude.json` has 68 project keys, forward
  slashes, and ZERO under `C:/Users/User/Apps/*`, yet `Apps\orca-dws-wt` (worktree of trusted Orca X)
  has 38 worker transcripts. Worktree config resolves to the main repo entry (InfinityOps: trusted,
  `enabledMcpjsonServers: []`). io-ql-complete's `.mcp.json` is byte-identical (sha256 46683C06...) to
  the working `InfinityOps\.claude\worktrees\ql-kernel` one, so project MCP approval is not the
  discriminator either. A trust check keyed on `.claude.json` paths would refuse legitimate
  worktrees -> NOT implemented.
- F2 where the host keeps the block reason: `~/.claude/jobs/<bg_id>/state.json` field `needs`
  (e.g. "login required -- run /login · Login expired", "approve Entering worktree", a question).
  `claude agents --json --all` (read 2026-09-28, 569 rows) shows such a job as
  `{"state":"blocked"}` with NO `status`, NO `waitingFor`, NO `pid` -- exactly the shape
  `owner_idle()` (gsd_mission.py:909) calls "turn ended". Live examples: 1ba72a2c (needs: login
  required) and f8ae9144 (needs: a question to the Owner). A genuinely finished turn reads
  `state:"done"` (13 rows) or `status:"idle"` (38 rows).
- F3 the 48 io-ql workers' job files were all overwritten to `state:"stopped"` when the supervisor
  stopped them (no `needs`, no `cliVersion`, no `linkScanPath`, no `tokens`, no session-env, no
  debug log, no transcript). The actual pre-conversation block reason is UNRECOVERABLE from
  records. Same pattern (adopted-without-ack then "blocked" relay x12) hit m-bba77d357eb4
  (`Apps\kme-wt-arena3`) on 2026-09-24.
- F4 `last_progress_at` is written ONLY at create (gsd_mission.py:213) and is null on all 44
  mission records, including KobiiCraft lineages that did 48 iterations of real work. A predicate
  on it would refuse every renewal -> progress evidence must come from elsewhere.
- F5 renewal: `renewal_refusal` (:1045) only checks halt-was-budget + GSD OK + cap; the halt
  reason "turn ended and budget: iterations 12 >= max 12" contains "budget:", GSD said OK (work
  remains -- nothing was done), so each lineage renewed 3 times.

RE-ARM ANSWER: NOT safe to re-arm m-66ebaaa0324e's cwd on the pre-fix supervisor (it would relay
blocked workers again). What blocks the next worker is UNKNOWN (evidence overwritten); after the
fix the first blocked worker parks the mission BLOCKED and the reason is read from
`~/.claude/jobs/<bg_id>/state.json` `needs` -- read that before stopping anything.
## Fixes

- BASELINE (pre-change, 9f750fa): test_gsd_mission MC_PASS=163/163; test_cpp_gsd_long_routing
  ROUTE_PASS=8/9 -- the 1 FAIL is pre-existing and environmental: V-ROUTE-LIVE-COMMAND-IS-REPO-COMMAND
  compares the LIVE ~/.claude/commands/cpp-gsd-long.md with this worktree's copy (live install drift).
- DEFECT 2 fix: liveness() returns BLOCKED (WAITING_HUMAN) for a bare host `state:"blocked"`;
  owner_idle() no longer calls it idle; supervise records the host's own `needs` (new
  host_job_needs(), read before any stop) in the mission_blocked reason. Characterization
  V-MC-BG-BLOCKED-NO-WAITING-RELAY inverted in place -> V-MC-BG-BLOCKED-NO-WAITING-IS-BLOCKED.
  RED pre-fix: 6 FAIL / MC_PASS=162/168 (5 new cases + control coupled to the red count, decoupled).
  GREEN post-fix: MC_PASS=168/168. Control V-MC-SUP-CONTROL-STOPPED-STILL-REPLACED green;
  V-MC-BG-TURN-ENDED-RELAY (status idle) still relays.