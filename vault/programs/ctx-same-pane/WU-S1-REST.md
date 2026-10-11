# WU-S1-REST -- ctx-same-pane S1 (validate a65b5c5e, then S1 steps 3-6). Owner-approved; no Owner questions.
Repo C:\Users\User\Apps\pp-ctx-same-pane, branch ctx/same-pane. Goal ctx-same-pane, lease L4 (2.7M). Owner typed
`approve p80` 2026-10-11T13:50:10Z on packet 125f0003 (programme 26,572,474): this WU is S1 only. S4 is a later WU.
Admitted route: AT MOST 15 calls (about 2.1M). Budget them: 2 boot, about 5 for step 2, the rest for step 3 in order;
whatever does not fit goes to the receipt as remaining, for the next WU. Measured: a fresh session costs about 119K
per call, so every call counts. The last worker burned 11 of 14 calls on
boot; do not repeat it.
0. Boot in 2 calls, no exploration. Run exactly:
   mission_capsule.py resume --mission m-4d1b851262ff
   then mission_capsule.py certify --mission m-4d1b851262ff --goal STATE.md --branch ctx/same-pane --head <git rev-parse --short=7 HEAD> --next "S1 validate a65b5c5e" --dirty 0
   (tools under C:/Users/User/.claude/skills/claude-power-pack/tools/; --goal is the bare name STATE.md, other forms fail).
   Ignore .planning GSD phase state; it is non-authoritative for this WU.
1. Read vault/programs/ctx-same-pane/RECEIPT-S1-STOPLOSS.md (in the repo) and `git show a65b5c5e -- tools/mission_spend.py`.
2. Validate: run tools/test_goal_autopsy.py and tools/test_mission_spend.py. Add a fixture session with one subagent
   (agent-x.jsonl + agent-x.meta.json, check the real naming against one real <sid>/subagents/ dir first) that must
   report main + subagent; prove with tools/mutation_drill.py on an isolated copy that removing the subagent walk goes
   red. Fix only real defects. Pathspec commit.
3. S1 steps 3-6 of the receipt, in order, a commit after each: session_autopsy per-call floor vs growth split
   (tool_result / assistant / user / injected), dedupe by message.id; static floor census (deterministic, no model
   calls) reconciled against call-1 context of 5 real transcripts (6d8f3412 and 98bcc118 included);
   vault/programs/ctx-same-pane/s1/attribution.json with V-gates and one killed drill; the controllable-floor figure.
Stop-loss: halt with the receipt when L4 has under 300K left, or a step fails twice after a local fix.
Common: no Monitor, no waiting call, no GSD commands, no planner or plan checker, at most 1 subagent. Never edit
tools/gsd_mission.py or settings.json. Never call capital-apply, goal-declare or goal-lease-open.
Done-check: both test files exit 0; S1 done-gate of REARM-S1-S4.md met; commits listed.
Receipt: append to vault/programs/ctx-same-pane/RECEIPT-S1-STOPLOSS.md a section '## WU-S1-REST' with Status DONE or
BLOCKED, commits, measured calls and processed tokens (from your own transcript usage), and what remains.
