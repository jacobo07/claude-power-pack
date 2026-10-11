# ctx-same-pane S1 stop-loss receipt

Date: 2026-10-11. Halted at the request of the coordinator pane (claude-power-pack-3e): lease L2 had used
2,266,165 of 3,000,000 while the S1 budget was 1.5M. S4 was NOT started. Status: S1 INCOMPLETE (WIP commit).

## Finished (code written, NOT yet run or tested)
- `tools/mission_spend.py`: new `_subagent_autopsy(tx, roots)` walks `<sid>/subagents/agent-*.jsonl`, typed by the
  sibling `.meta.json` agentType (UNTYPED when absent). `goal_autopsy` rows now INCLUDE subagent calls / processed /
  bound, and expose `main_processed`, `main_calls`, `subagent_processed`, `subagents` (by type).
- Existing incident table is unchanged by construction (its fixtures have no subagents); this was NOT re-run.
- Not verified: the `.meta.json` naming (`agent-x.meta.json` via `with_suffix`) against a real transcript directory.

## Remaining for S1 (REARM-S1-S4.md)
1. Run `tools/test_goal_autopsy.py` and `tools/test_mission_spend.py` (regression).
2. Red-path gate: fixture session with one subagent reports main + subagent; mutation drill removing the subagent walk
   must go red (`tools/mutation_drill.py`, isolated copy).
3. `tools/session_autopsy.py`: per-call floor vs growth; growth split tool_result / assistant / user / injected
   (hook additionalContext, a bucket that does not exist yet); subagent transcripts counted per type; dedupe by message.id.
4. Static floor census (deterministic script, no model calls; chars/4 estimate) reconciled against call-#1 context of
   5 real transcripts (6d8f3412 included); gap reported as host floor.
5. `vault/programs/ctx-same-pane/s1/attribution.json` from 5 real transcripts, V-gates green, one drill killed.
6. Controllable-floor figure for A1's stop-loss (less than 25K controllable means A1 is not worth it): UNMEASURED.

## Measured cost
- Lease L2: 2,266,165 used of 3,000,000 (coordinator figure). Per call about 225K (coordinator figure; each call
  re-reads the resident context, which is the very rent this programme measures).
- S1 budget 1.5M exceeded before the done-gate. Nothing in S1's done-gate is satisfied yet.

## Not done / not claimed
- S4 (zero-model status probe): not started. No claim of zero-model status.
- Phase 2 GSD artifacts under `.planning/.../02-s1-rent-attribution/` are non-authoritative (packet says ignore);
  committed only because the coordinator asked for the path to be included.
