---
gsd_state_version: "1.0"
milestone: v1
status: ready
stopped_at: Roadmap created by the arming pane
last_updated: "2026-11-20T23:30:00.000Z"
progress:
  total_phases: 8
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
milestone_name: resource-residency
workstream: resource-residency
created: 2026-11-20
current_phase: 1
current_phase_name: Phase 1 (see ROADMAP.md)
last_activity_desc: Owner `go residencia`; P1 + P1-NOW done inline (2ce9f811); mission armed
---

# Project State

Authority: `ROADMAP.md` + `REQUIREMENTS.md` here, and `vault/plans/resource-residency-fabric-20261120.md`.
Budget: authority 40M processed tokens + 2 top-ups of 15M; hard ceiling 70M; reserve 8M. Max 14 cycles, 30 h.
Arming pane 54c0ea73 (interactive, PP root) ran Reality Scan, P1 and P1-NOW inline.

## Baseline at arm (2026-11-20 ~23:20, laptop)
commit 64.71 GB (was 86.3/87.1 at 21:38), pagefile alloc 49.3 GB (peak 57.6), free C: 36.65 GB, claude.exe x22.

## Spend log (processed tokens, `mission_spend.py session-tree`)

| when | session | tokens | note |
|---|---|---:|---|
| 2026-11-20 23:50 | e5ca940c (Phase 1, `session-tree --transcript`) | 6,241,691 | 42 turns, avg ctx 148k: 4.2x the 1.5M line, 2.8x the 3M acceptance ceiling. Mostly re-read of the ~148k startup context per turn, not work volume |

## Phase status
- Phase 1: DONE on evidence (`vault/programs/resource-residency/P0-P1-GATE-EVIDENCE.md`): `tools/resource_census.py` +
  22 V-CENSUS gates (mutation drill red), snapshots committed, open P1 gate PASS on both halves. SPEND BREACH, see Owner notes.

- Phase 2: DONE on live evidence (worktree `rr-phase2`, branch worktree-rr-phase2, unpushed; commits 57e4a1a7 + 87a5572c).
  Lazy MCP shim (`tools/mcp_lazy_shim.py`, `mcp_scope.py lazy|unlazy`), 14/14 V-LAZY gates incl. mutation drill.
  Live on GEO-audit/google-ads (backup `~/.claude.json.mcp-scope-20261121-162646.bak` family; rollback `mcp_scope.py unlazy`).
  - Gate A PASS: `claude mcp list` Connected; events.jsonl shows only `served` (initialize, tools/list, prompts/list, resources/list).
  - Gate B PASS: read-only `claude -p` list_google_ads_accounts returned 2 accounts; `spawn` only with trigger `tools/call`.
  - Two defects found by the LIVE gate that the 14 synthetic gates missed (fixed in 87a5572c): the host probes `server/discover`
    at connect (the shim spawned on any unknown request) and enumerates `prompts/list`/`resources/list` (server advertises both,
    so the shim spawned on them). Fix: spawn allowlist (tools/call, resources/, prompts/, completion/, logging/); unknown
    methods get -32601; recorder caches prompts/resources/templates lists. No V-LAZY gate yet pins these two (debt, small).
  - Measure: idle shim private 10.5 MB. Real google-ads server private MB NOT measured (child probe hit a launcher stub);
    commit before/after first use not captured, so no "freed N MB" claim. First-call latency: not isolated (-p wall 135 s is
    dominated by SessionEnd hooks); spawn event 30 s after the list calls = model think time, not spawn cost.
  - Scope: only GEO-audit/google-ads is lazy. Other projects/servers unchanged (rea, others not converted).
- Phase 5 (shadow only): DONE to scope, dbb49a53. `tools/session_liveness.py` + 15 V-LIVE gates (mutation drill red). Live: ACTIVE 21 /
  IDLE 0 / UNKNOWN 7 of 28; threshold likely too sensitive on this host, not tuned. Nothing stopped. Canary hibernate/resume = Owner step.
- Phase 8 (close): DONE, `vault/programs/resource-residency/P8-CLOSE.md` (master gate per phase, NO APLICA for 3/4/6/7, census delta
  with its confounds, Owner steps incl. pagefile recommendation). No "freed N GB" claim: host commit rose 2.73 GB.
- MISSION SCOPE COMPLETE per D-2026-11-21. Phases 3, 4, 6, 7 remain deferred.
- Spend: supervisor-measured 12,969,713 processed at 15:22Z (before this epoch's live gate). `mission_spend session-tree` needs
  a --transcript path not available to this worker; this epoch's own spend not separately measured.

## Owner notes
- RESOLVED by OWNER DECISION D-2026-11-21 (binding): re-baseline + scope cut. Phase 1 done. Run Phase 2 (line 12M, stop 18M), then
  Phase 5 shadow only (12M / 18M), then the short Phase 8 close (3M). Phases 3, 4, 6, 7 DEFERRED: do not start. Never git push.
  The "Decision for you" in the Phase 1 spend note below is settled by this; do not wait for the Owner on it again.
- 2026-11-20 (Phase 1 spend): Phase 1 cost 6.24M processed tokens against a 1.5M line (1.5x = 2.25M) and the 3M acceptance
  ceiling, so per ROADMAP the run stops here. The overrun is per-turn context (~148k re-read x 42 turns), which a fresh
  background session per phase would not carry. Decision for you: continue with Phase 2 from a fresh session
  (`/gsd-autonomous --ws resource-residency --from 2`), or re-baseline the per-phase lines to the real turn cost.
- BLOCKED-ON-OWNER (RR-03, not automated): the remaining rea x32 (16 sessions) and google-ads x42 (14 sessions) processes sit in
  sessions born before P1 and leave when those sessions end; nothing here stops a claude.exe or a server with recorded use.
