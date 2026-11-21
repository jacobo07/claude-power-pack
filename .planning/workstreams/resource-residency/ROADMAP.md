# Roadmap — resource-residency (v1)

Authority: `vault/plans/resource-residency-fabric-20261120.md` (Owner `go residencia`, 2026-11-20). Read its Reality
scan and Execution log first and do NOT re-scan what they state. P1 + P1-NOW are DONE (commit 2ce9f811): user-scope MCP
13 -> 3, `tools/mcp_scope.py` owns scope, `vault/registry/mcp_catalog.json` + private store
`~/.claude/state/mcp_catalog_private.json` (secrets: never print, never commit, never copy into the repo).
Law: availability scales with the institution; residency scales with current demand.
PLANE: laptop, PP root, shared tree. Commit only your hunks with exact pathspec; verify `git log -1` after each commit.
`vault/plans/deferred-backlog.md` and `.planning/STATE.md` (root) carry other writers' changes: never stage them.
EXECUTION mode, small scopes, plan each phase inline. **At most ONE subagent at a time** (fan-out is the problem being
fixed). Measure your own spend per phase (`python tools/mission_spend.py session-tree --session <sid>`), record it in
STATE.md; a phase over 1.5x its line -> stop and write the one-line Owner note.
Memory figures: working set, private bytes and commit are three numbers, never one "RAM" number. Every freed figure is a
measured before/after with its command; deltas you cannot attribute are UNATTRIBUTED. UNKNOWN is never reclaimable.
Never stop a claude.exe session, never stop an MCP process of a server with recorded use, never touch the pagefile
setting: those are Owner actions, written as numbered steps in STATE.md (BLOCKED-ON-OWNER) while you continue elsewhere.
Two consecutive phases without a measured physical delta -> write BREAKER in STATE.md and stop.
**Commit only; no push authority.** Since 699ddb9a this is machinery, not prose: the pre-push hook and ovo-push-gate
refuse any push from a session listed in a mission record without a grant (`tools/push_authority.py`). A refusal is
expected behaviour, not a blocker: do not retry, work around or ask; record nothing about it.

**Owner "go tranche" (2026-11-21, plan `vault/plans/resource-residency-fabric-20261120.md` Addendum A).** Corrected
measurement: a fresh worker's FIRST call is ~97K (not 148K); ~150K is the MEAN per call of a session that grows to the
175K wall. Per-turn rent is what to cut: few large turns, no re-reads of what STATE.md already summarises.
Close status is "TRANCHE COMPLETE" -- never "RESOURCE RESIDENCY COMPLETE" -- with the next frontier ranked by measured
rent. Record per epoch in STATE.md: first-call context, mean context, calls to first Edit (dogfood).

**Owner decision D-2026-11-21 (re-baseline + scope cut).** Phase 1 measured the real turn cost: ~148k startup context
re-read per turn, 6.24M for a 1.5M line. Lines below are re-baselined to that rate; the per-phase stop is now 1.5x the NEW
line. Scope cut to the two largest remaining rents: Phase 2 (lazy MCP) and Phase 5 (session liveness, shadow only), then a
short close. Phases 3, 4, 6, 7 are DEFERRED (not done): do not start them; Phase 8 shrinks to the close below.
Keep turns few and large: plan a phase in one turn, batch edits, avoid re-reading files already summarised in STATE.md.

## Phases

- [x] **Phase 1: P0 resource census + the open P1 gate** (b74fe8d74, evidence `vault/programs/resource-residency/P0-P1-GATE-EVIDENCE.md`)
- [ ] **Phase 2: P2 lazy materialization shim (experiment)** -- line 12M, stop at 18M
- [ ] **Phase 5: P5 session liveness classifier (shadow report only)** -- line 8M, stop at 12M. States derived from
  multi-signal evidence (never transcript age alone, never one CPU sample); UNKNOWN protected; nothing is stopped
- [ ] **Phase 8: close** -- line 3M: 2-snapshot census delta (not the 24 h benchmark), pagefile recommendation as an
  Owner step, UKDL entry, plan status, master gate judged item by item with NO APLICA for the deferred phases

Deferred (Owner D-2026-11-21, kept for a later mission): Phase 3 P3 lease + idle teardown; Phase 4 P4 shareability;
Phase 6 P6 commit governor; Phase 7 P7 resource-budget CI. Their details below stay as the design record.

## Phase Details

### Phase 1: P0 census + open P1 gate
**Depends on**: nothing. Line 1.5M.
- `tools/resource_census.py`: per process pid + creation time, ancestry to claude.exe and its session id, WS / private /
  commit kept separate, MCP server attribution from `~/.claude.json` + `.mcp.json` + plugin configs, conhost children,
  JSON snapshot + `diff A B`. Matcher must refuse a signature that is a bare command with 0 args (the playwright defect:
  `mcp` + 0 args matched 751 unrelated processes) -> UNKNOWN, never attributed.
- `tools/test_resource_census.py` (V-CENSUS-*) on real byte shapes; a mutation drill that must go red.
- Open P1 gate: a fresh `claude -p` session in GEO-audit makes one READ-ONLY `mcp__google-ads__*` call (account list)
  and succeeds; a fresh PP session spawns 0 catalogued servers (census diff). Record both.
- **Acceptance (early value):** census snapshot committed under `vault/programs/resource-residency/`, MCP count per
  session before/after P1 from real data. Not reached within 3M -> `METHOD_PIVOT_REQUIRED` in STATE.md, stop.

### Phase 2: P2 lazy materialization
**Depends on**: Phase 1. Line 6M.
- stdio shim answering `initialize` / `tools/list` from a cached schema, spawning the real server on first `tools/call`.
  Kill switch `CPP_MCP_LAZY=off` (shim execs the real server immediately). Apply first to ONE server in ONE project
  (google-ads in GEO-audit) via `tools/mcp_scope.py`, backup per change.
- Gate: commit before/after first use, first-call latency, tool correctness. If Claude Code rejects cached schemas:
  `METHOD_FAILED` recorded, stay on P1 scoping, go to Phase 3 only for what still applies.

### Phase 3: P3 lease + idle teardown
**Depends on**: Phase 2 (skip with reason if P2 failed). Line 3M. Inside the shim: last consumer gone -> reclaim after a
per-server warm window derived from the measured cold start. Kill switch `CPP_MCP_IDLE_RECLAIM=off`.

### Phase 4: P4 shareability
**Depends on**: Phase 1. Line 2M. Classify each server (stdio/http, auth, cwd, state) SHAREABLE / PER_SESSION / UNKNOWN.
UNKNOWN never shared. Pooling only for a proven SHAREABLE class with positive measured ROI; otherwise document and stop.

### Phase 5: P5 session liveness + hibernation
**Depends on**: Phase 1. Line 8M. Largest rent (claude.exe ~29.9 GB private, 22 sessions at 21:38). Classifier from CPU,
children, background tasks, transcript tail, mission lease; ACTIVE / IDLE / UNKNOWN, UNKNOWN protected. Extend
`modules/cognitive_os/process_governor.py` (HR-STALLED-SESSION-ADVISORY-001: advisory only, never auto-kill). Shadow
report only. The one canary hibernate -> `--resume` round trip is an Owner step (BLOCKED-ON-OWNER with the exact
command). Kill switch `CPP_SESSION_HIBERNATION=off`.

### Phase 6: P6 commit-pressure governor
**Depends on**: Phase 5. Line 4M. Thresholds from commit limit and pagefile growth rate; shadow, then advisory (toast /
SessionStart line). Never kills ACTIVE/UNKNOWN. Under pressure: refuses optional MCP births (via the shim) and proposes
hibernation. Kill switch `CPP_COMMIT_GOVERNOR=off`.

### Phase 7: P7 resource-budget CI
**Depends on**: Phase 1. Line 2M. A check (hook or test) that flags a new user-scope MCP with its projected per-session
rent (measured per-process private x live sessions). Proven to fire on a real `~/.claude.json` shape and to stay silent
on a project-scope add.

### Phase 8: P8 benchmark + close
**Depends on**: Phases 1-7. Line 4M + close 2.5M. Steady-state benchmark over >= 24 h of census snapshots: commit P50/P95,
pagefile alloc, MCP count. Pagefile size recommendation (P95 + margin) written as an Owner step, never applied. UKDL entry,
plan status CLOSED, master gate judged item by item (NO APLICA with reason allowed).
