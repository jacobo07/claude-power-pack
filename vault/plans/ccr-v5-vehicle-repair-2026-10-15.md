---
covers: [ccr-v5-vehicle-repair, phase-breaker, subagent-governance, unit-done-typing, usage-attribution, worktree-mcp-receipt, ccr-v5-resume]
status: AWAITING_OWNER_APPROVAL
pane: d124ce03 (coordinator; hands off after approval, executes nothing productive)
packet: ~/.claude/state/capital-authority/packets/ccr-v5-stageA-2026-10-15.json
---
# CCR v5 — Stage A: repair the execution vehicle (Master Plan, backup of the chat approval surface)

## 1. Measured reality (2026-10-15 ~12:20, read-only scan)
- ccr/v5 HEAD bf7f2613, tree clean. Mission m-a43d0aa7ce28 RUNNING-on-hold (cost breaker 68,107,834 > 2 x 33M).
- Goal ledger `ccr`: settled 138,414,270; open 1,033,575; L13 cap 79,000,000, used 25,095,992, "remaining" 53,904,008.
  The ledger is WRONG low: it holds only one booked worker session.
- Measured processed, transcript-deduped by message id (script `v5usage.py`, main + subagents):
  | Mission | session | main | subagents | total | booked |
  |---|---|---|---|---|---|
  | M1 | 24dd7650 | 1.91M (13 calls) | 5.48M (gsd-planner, 36 calls) | 7.39M | no |
  | M1 | 3f676ac2 | 4.87M (30 calls) | 0 | 4.87M | no |
  | M2 | af436132 | 8.20M (51 calls, 1 compact) | 21.29M (6 agents, 157 calls) | 29.49M | 25.10M |
  | M2 | f06addea | 5.83M (37 calls) | 33.02M (4 agents, 221 calls) | 38.85M | no |
  | coord | d124ce03 | 31.82M (160 calls since 10-12, multi-task) | 1.92M | 33.74M | partial (L12), v5 share UNKNOWN |
- v5 workers total 80.60M. True goal use ~ 139.45M + 55.5M unbooked = ~195.0M (+ coordinator v5 share).
- Main-thread context: first call 114-118K, max 216K, 1 compaction in total. NO same-session runaway.
- Subagents: first call 84-89K, mean 97-152K, up to 217K. One gsd-planner (f06addea) = 157 calls, 24.04M
  (Phase 3 planning). The three planners together = 32.2M = 40% of v5.

## 2. Root-cause matrix (claims tested)
| Claim (incident report) | Verdict | Evidence |
|---|---|---|
| one long session compacted instead of rotating | FALSE | main 37-51 calls, max 216K, 1 compaction |
| context carry drove the 68M | PARTIAL | the carry was inside SUBAGENTS: 54.3M/68.3M (79%) |
| stop-loss bypassed by the model | TRUE | no phase breaker in code (0 hits in gsd_mission/mission_spend/mission_recovery/gsd_epoch); it was ROADMAP prose |
| mission breaker absent | FALSE | it fired deterministically at 2 x estimate; the coordinator set estimate 33M = breaker at 66M = the whole lease |
| 25.1M = coordinator transcript overcharge | FALSE | af436132 is the epoch-1 WORKER; measured 29.49M; UNDER-booked ~4.4M |
| DEFLATE globally disabled | FALSE | pgo-classes.json installed 09:27; CPP_CCR_DEFLATE unset (User/Machine/process); acts only on slim `claude -p` bounded-code units, never on `claude --bg` GSD workers |
| unit DONE closes mission | TRUE | gsd_mission.py:4274-4290: a recovery-injected packet's receipt DONE -> state COMPLETED on a roadmap mission |
| worktree MCP approval | TRUE | the worktree walks up to ~/.claude/.mcp.json; the approval lives in the main tree's gitignored settings.local.json |

Dominant defects: (D1) ungoverned subagents (no per-agent call/token cap, planners re-reading);
(D2) no phase-level breaker; (D3) breaker threshold chosen by a person/model, not derived; (D4) settlement only by worker
self-booking, so a breaker-stopped session is never booked; (D5) unit receipt closes a mission; (D6) per-call floor ~86-118K.

## 3. Stage A workstreams (EXECUTION unless marked)
- A0 Accounting truth (deterministic): book M1 (12.26M), f06addea (38.85M), the af436132 residual (4.39M) with
  `goal-settle --measured`, each row naming its mission/epoch. Measure the coordinator's v5 share by timestamp
  window and book it to ccr. The 25.1M stays: real, correctly attributed. The worker's goal-correct proposal is REJECTED with
  evidence. No row is rewritten; append-only.
- A1 Supervisor settles every stopped worker (gsd_mission reap path -> goal_settle with mission/epoch tags) so D4
  cannot recur.
- A2 Phase breaker (deterministic, in the sweep): the mission record carries per-phase leases {forecast, warn 1.2x,
  hard 1.5x, reserve}. Phase spend = processed since the phase's first commit (read from ROADMAP/STATE). On hard: owner
  hold + stop the worker. Successor gets a reforecast-only packet. The model cannot write the lease (CAS on the record;
  envelope refuses raise without an Owner packet).
- A3 In-turn enforcement: the existing PostToolUse mission_wall.js reads the hold flag. On hold it denies further tool
  calls for the worker AND its subagents (subagent calls carry the parent session). This closes the 5-minute sweep gap
  (~2.1M/sweep at the measured 0.42M/min).
- A4 Subagent governance (D1): per-subagent cap (calls and processed, by agent type, from PGO, default 30 calls / 3M).
  Enforced in the same hook by denying the subagent's tool calls. Mission default topology for GSD workers: planning in
  the main thread, `gsd-planner`/`general-purpose` research agents denied, executors allowed with cap.
- A5 Derived estimate (D3): arm/envelope compute the estimate from the roadmap routes still open, with a 1.5x hard
  cap. Authority above the lease remainder minus reserve is refused.
- A6 Type-safe completion (D5): a packet injected by recovery onto a workstream mission is typed `unit`. Its receipt
  DONE relays to the roadmap and never sets COMPLETED. Completion receipts carry {type, id, parent, residual}.
- A7 Worktree MCP receipt: arm detects inherited .mcp.json servers without an approval for the cwd. If git-common-dir
  equals the main tree's, it copies that repo's own decision into the worktree's settings.local.json (same
  repository identity). Otherwise it refuses arm with the exact remedy.
- A8 Compaction accounting: test only (transcripts keep pre-compaction usage rows, so breakers see them). The full
  Lifetime Governor stays in the v5 roadmap Phase 8 (Stage C). Containment: continue_max_tokens 250K is kept.
- A9 DEFLATE: no ablation in Stage A, because DEFLATE does not touch the failed vehicle. Policy recorded: keep
  as-is (on for slim bounded-code, hold documented). Ablation is moved to Stage C with real slim-unit data.
- A10 Fault-injection CI: phase cap vs model prose; ambiguous prior-phase accounting -> BLOCKED; unit DONE with
  residual phases -> mission open; subagent past cap -> denied; compaction keeps spend; coordinator+worker -> no
  double charge; MCP worktree arm.
- A11 Canary: a real `claude --bg` mission on a toy unit in a scratch worktree, phase cap 400K. It must be stopped by
  A2/A3 within cap + one sweep, and a subagent stopped by A4. Then Stage B reforecast from measured per-call cost.
- A12 Knowledge: UKDL HR/PR/Traps (deduped), KV, FIOS; CBR only after the canary.

## 4. Vehicle for Stage A
Fresh Ralph mission in worktree ccr-v5 (branch ccr/v5; new work under `vault/plans` + tools in this branch). Main thread
only, Agent tool denied, estimate 6M (breaker 12M = authority). This coordinator pane hands off after approval:
it is itself a 228K-per-call transcript.

## 5. Budget (processed tokens; per-call cost measured ~150K main thread)
Envelope A: semantic lower bound 3M · LOWER 5M · P50 8M · P80 11M · P95 14M · HARD 12M (incl. 1M recovery reserve).
Confidence: medium (the floor is measured; the call counts are estimated).
Envelope B (indicative, NOT requested): Phase 3 residual 03-02..03-06 + A7 read-out + main merge: P50 9M · P80 13M.
Envelope C (indicative, NOT requested): v5 Phases 4-11 under the repaired vehicle: P50 35M · P80 48M.

## 6. Capital request
Programme ceiling for goal ccr to 210,000,000 (P80) = measured truth ~195.0M + Envelope A 12M + 3M coordinator
attribution reserve. Tiers: P50 205M · P80 210M · P95 213M. Expires 2026-10-18.

## 7. Approval envelope
Authorized: edits to tools/gsd_mission.py, tools/mission_spend.py, tools/mission_recovery.py, hooks reached by the
registered dispatcher chain (mission_wall.js), tests, and the ccr/v5 branch. Append-only goal-ledger settlements (A0/A1).
The toy canary mission. Pathspec commits in the worktree.
Excluded: ~/.claude/settings.json and CLAUDE.md/rules; push; main-tree merge (Stage B); goal-correct of any row;
DEFLATE global flags; Stage B/C productive work; foreign writer bytes.
Stop: Envelope A breaker 12M; a canary that exceeds its cap by more than one sweep; any need for new hook
registration -> OWNER STEP.
