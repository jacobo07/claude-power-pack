---
covers: [economic-kernel-bootstrap, floor-autopsy, boundary-autopsy, physical-forecast-gate, context-admission, boundary-authority, coordinator-rent]
status: AWAITING_OWNER_APPROVAL
pane: d124ce03 (coordinator; retires after approval)
packet: ~/.claude/state/capital-authority/packets/ccr-v5-kernel-2026-10-15.json
---
# CCR v5 — Economic kernel bootstrap + floor/boundary autopsy (Master Plan backup; chat is the approval surface)

## 1. Measured reality (2026-10-15 ~14:50 local; deterministic scripts, no model replay)
- ccr/v5 HEAD 9288c829 (clean). PP main 5faab075. Mission m-44dde27a3f1c held (authority -5,019,507).
- Goal ccr: settled 210,941,819 + open 1,033,575 = 211.98M of 213M. Coordinator d124ce03 v5 share since
  2026-10-14T20:00Z = 21,975,866 (102 calls, ~197K/call), mostly UNBOOKED. True programme ~232.5M.
- Safety commits 5bfce1df..9288c829 = 9 files (phase_lease.py, hooks/lib/mission_gate.js, session_budget_guard.js +5,
  gsd_mission.py +103, mission_spend.py +35, 4 test files). The main tree has 0 commits on those paths since
  merge-base 77e1cbf0 and 0 dirty bytes there, so a path-scoped landing is clean. Nothing is live today.
- Overshoot cause: the sweep's mission stage hit its 600 s timeout at 11:31, 11:47 and 12:01 UTC (process tree
  killed). Effective cadence was 14+ min, so the asynchronous breaker was the only breaker.
- Worker 49c0ae70 first call 116,502 (cache_create 86,147 + read 30,353). Transcript-visible pre-call surfaces
  ~57K tokens: `instructions` (CLAUDE.md chain + rules) 28.2K; skill_listing 9.2K; agent_listing 7.3K;
  prompt_snapshot 3.8K; deferred tools 2.5K; SessionStart hooks 3.8K; file 1.5K; MCP 0.8K; UserPromptSubmit 0.6K.
  Invisible remainder ~59K = system prompt + tool schemas (to decompose from CCR api-request receipts).
  The worktree lives under C:\Users\User, so the host walks up to ~/CLAUDE.md AND ~/.claude/CLAUDE.md + rules.
  Lean slim workers (10-16K) launched with system-prompt-file / no listings; GSD bg workers get everything.
- 103 calls: ~55 read/search (Read 12 + multi-Read 12 + Grep 13 + multi-Grep 7 + Grep+Read 5 + Glob 6), 17 test runs,
  ~28 edit/write, 3 other. 50 Read calls on 16 files; gsd_mission.py (5.6k lines) read 24x in chunks. 37/103
  calls were already parallel.
- Falsified (negative knowledge): subagents (0); runaway transcript (peak 218K); compaction as cause (2, harmless).

## 2. Root causes of 17M
R1 per-call floor 116K, ~50% controllable (instructions chain, listings, hooks). R2 boundary amplification
~2.3-3x: about half the calls rediscover code (gsd_mission.py paged 24x). R3 hard limit enforced only by an
asynchronous sweep whose pass times out. R4 forecasts not checked against floor x calls. R5 coordinator rent unmeasured
and unbooked (22M).

## 3. Envelopes (processed tokens; calibrated: bg worker ~150-165K/call, slim worker target 25-40K/call)
| Env | Scope | LB | Low | P50 | P80 | P95 | Hard |
|---|---|---|---|---|---|---|---|
| 0 | land 9 files live, live tests, gate next-call exposure, sweep: mission breaker first + per-mission budget | 0.8 | 1.5 | 2.5 | 3.5 | 4.5 | 4.0 |
| 1 | floor: decompose invisible ~59K from receipts; lean launch profile for workers; Context Admission check at arm | 0.5 | 1.0 | 1.5 | 2.2 | 3.0 | 2.5 |
| 2 | boundary ledger tool + call profile PGO + boundary authority (max_calls) in phase lease + gate | 0.4 | 0.8 | 1.2 | 1.8 | 2.5 | 2.0 |
| 3 slice | physical forecast gate (calls x floor) + code-map page for large files (UCRE projection) + fresh epoch per plan + canary | 1.0 | 1.8 | 2.8 | 3.8 | 5.0 | 3.5 |
| reserve | recovery + settlement | | | | | | 1.0 |
| **0-3** | **requested now** | 2.7 | 5.1 | 8.0 | 11.3 | 15.0 | **13.0** |
| 4 | rest of Stage A (indicative, after reforecast) | | | 6 | 9 | 13 | not requested |
| 5 | CCR v5 residual Ph3-Ph11 + A7 (indicative) | | | 25 | 38 | 55 | not requested |
| 6 | original Cognitive Economics (indicative) | | | 30 | 45 | 70 | not requested |

## 4. Vehicle
Executor: a packet-bound SLIM unit (`arm-chain`, `claude -p`, lean launch, main thread, no Agent) per envelope, not a
bg GSD worker and not this pane. Env 0 lands first; every later unit runs under the live gate (self-hosting).
The coordinator pane books its own v5 share (21.98M measured) and retires.

## 5. Authority
Authorized: path-scoped landing of exactly the 9 files into the PP main tree after a re-check that they are still
untouched by others (per-file 3-way apply, tests, revert on any failure). Edits to gsd_mission.py, mission_spend.py,
phase_lease.py, mission_gate.js / session_budget_guard.js (already registered), gsd_long_run_sweep.ps1 logic,
ccr_rent_ledger/ccr_anatomy, tests. Append-only ledger settlements. Slim canaries with caps.
Excluded: settings.json / CLAUDE.md / rules; push; broad merge; goal-correct; DEFLATE flags; Env 4-6 work;
foreign bytes; releasing m-a43d0aa7ce28 / m-44dde27a3f1c.
Returns to Owner: >13M; a new hook registration; a lean-launch change that needs settings.json; capital for Env 4+.
