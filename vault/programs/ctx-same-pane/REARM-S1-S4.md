# ctx-same-pane re-arm packet: S1 + S4 only (Owner option 1, 2026-10-10)

S0 is closed: commits 018230b9 (code) and 71b66b0b (evidence). The goal hit its 16M hard stop during S0. That spend
was real: worker 5.6M, plus 11.7M in subagents (gsd-executor 7.2M, gsd-planner 4.3M).
The Owner raised the cap by 4M for this packet ONLY. S2, S3, S5-S7 and Amendment A1
(`claude-power-pack/vault/plans/context-rent-same-pane-2026-10-10-A1.md`) are NOT authorised by it.

## Execution rules (these are the fix for the S0 overrun)

- **No GSD plan-phase.** Do not dispatch gsd-planner, gsd-plan-checker or gsd-executor, and do not run
  /gsd-plan-phase or /gsd-execute-phase. This file is the plan.
- Work inline in the worker session. At most ONE subagent per slice, and only for a read-only sweep; its prompt
  must carry a write-as-you-go clause and a bound.
- Commit per slice by pathspec, and verify with `git log -1 --format=%s`.
- Budget: S1 1.5M, S4 1.5M, reserve 1.0M. If a slice reaches its budget, stop it, write a receipt in
  `vault/plans/`, and move on or halt. Never borrow from the other slice.
- Ignore `.planning/workstreams/ctx-same-pane/phases/02-s1-rent-attribution/`. It is GSD plan-phase output from
  before the stop, and it is not authoritative.

## S1: rent attribution, including subagents (budget 1.5M)

1. `tools/session_autopsy.py` gains a per-call breakdown:
   - floor (call #1 context) versus growth;
   - growth split into tool_result, assistant, user and injected (hook additionalContext);
   - subagent transcripts (`<sid>/subagents/agent-*.jsonl`, typed via `.meta.json` agentType) counted per type.
   Deduplicate by message.id. Read with FileShare.ReadWrite semantics; never lock a live transcript.
2. `tools/mission_spend.py goal-autopsy` includes subagent spend.
   - Today it reports 5.6M for a goal whose ledger says 16.6M.
   - Red-path gate: a fixture session with one subagent must report main + subagent, and must fail when the
     subagent walk is removed (mutation drill).
3. Static floor census, a deterministic script with no model calls. It sizes in tokens (chars/4 stated as the
   estimate method) everything injected at session start:
   - global and project CLAUDE.md, `~/.claude/rules/*`, MEMORY.md;
   - the skill and agent listings;
   - each SessionStart and UserPromptSubmit hook's additionalContext, measured by running the hook with a
     canned input.
   Reconcile the census total against the measured call-#1 context of 5 real transcripts. The gap is reported
   as host floor, not hidden.
4. Done-gate: the breakdown run on 5 real transcripts (this worker's, 6d8f3412, included), output
   `vault/programs/ctx-same-pane/s1/attribution.json`, V-gates green, plus one mutation drill killed.

## S4: zero-model status (budget 1.5M)

1. Probe, one call: does a UserPromptSubmit hook returning `decision: "block"` with a `reason` show that reason to
   the Owner, with no model turn on this host build? Record the evidence (transcript shows no assistant usage
   row for that prompt).
2. If it holds, build a thin hook registered through the dispatcher:
   - It answers pure status prompts only. The matcher is a deterministic allow-list such as "status",
     "estado", "how is it going", "como va". Anything with a question beyond status passes through.
   - It renders a projection from existing owners: `gsd_mission.py status --surface` summary, `mission_spend.py
     goal-status` for bound goals, rollover state, HEAD and dirty count.
   - Fail-open, kill switch `CPP_STATUS_FASTPATH=off`, bounded runtime (under 3 s, else pass through).
3. If the probe fails, record EXTERNAL_LIMITATION with the evidence. The fallback is a documented shell command;
   make no claim of zero-model status.
4. Done-gate: a test of the matcher (status prompts admitted, mixed prompts refused), a hook-boundary test
   (node -> python -> JSON), and a live probe receipt.

## Close

Append facts to `LOG.md`. Write `vault/plans/ctx-same-pane-s1-s4-receipt.md` with:
- the measured numbers;
- the controllable-floor figure (this feeds A1's stop-loss: less than 25K controllable means A1 is not worth it);
- spend per slice.

Then halt. The Owner decides on S2 and A1 from these numbers.
