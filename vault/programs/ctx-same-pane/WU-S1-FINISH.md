# WU-S1-FINISH -- ctx-same-pane S1 items 4-6. Owner-approved; no Owner questions.
Repo C:\Users\User\Apps\pp-ctx-same-pane, branch ctx/same-pane. Goal ctx-same-pane, lease L5 (1.0M). Owner chose
option 1 on 2026-10-11 (S1 finish 1.0M, then S4 1.3M, inside the P80 ceiling 26,572,474). This WU is S1 only.
Admitted route: AT MOST 5 calls (790K free after another session's 209K reservation). A fresh session costs about
119K per call: 1 boot call, then ONE call per item (each call writes, runs and commits), and the receipt goes in the
same call as the item-6 commit.
Items 1-3 are DONE (aa82d3ac, 68b26a9d; suites 11/11, 17/17, 30/30). Do not re-validate them; do not re-read the code
beyond what a step needs.
0. Boot in ONE call, no exploration. Run both in one PowerShell command:
   mission_capsule.py resume --mission m-4d1b851262ff ; mission_capsule.py certify --mission m-4d1b851262ff --goal STATE.md --branch ctx/same-pane --head <git rev-parse --short=7 HEAD> --next "S1 items 4-6" --dirty 0
   (tools under C:/Users/User/.claude/skills/claude-power-pack/tools/; --goal is the bare name STATE.md, other forms fail).
   Ignore .planning GSD phase state.
1. Item 4: tools/floor_census.py, deterministic, no model calls: chars/4 estimate of what loads at session start
   (CLAUDE.md chain, rules/, MEMORY.md, SessionStart hook output if logged, tool/agent listings if measurable).
   Reconcile against call-1 context (input + cache_read + cache_creation of the first assistant entry) of 5 real
   transcripts under ~/.claude/projects/ (6d8f3412 and 98bcc118 included). Report the gap as host floor.
2. Item 5: vault/programs/ctx-same-pane/s1/attribution.json from the same 5 transcripts via tools/session_autopsy.py
   (floor vs growth split, subagents per type). Add V-gates to the existing test file and kill one mutation drill
   with tools/mutation_drill.py on an isolated copy.
3. Item 6: the controllable-floor figure (the part of the census the repo controls: CLAUDE.md, rules, memory, hooks),
   written in attribution.json and the receipt. Under 25K controllable means A1 is not worth it: say so plainly.
A commit after each item, pathspec only.
Stop-loss: halt with the receipt when L5 has under 150K left, or a step fails twice after a local fix. Whatever does
not fit goes to the receipt as remaining.
Common: no Monitor, no waiting call, no GSD commands, no planner or plan checker, no subagents. Never edit
tools/gsd_mission.py or settings.json. Never call capital-apply, goal-declare or goal-lease-open.
Done-check: S1 done-gate of REARM-S1-S4.md met; commits listed.
Receipt: append to vault/programs/ctx-same-pane/RECEIPT-S1-STOPLOSS.md a section '## WU-S1-FINISH' with Status DONE
or BLOCKED, commits, measured calls and processed tokens (from your own transcript usage), the controllable-floor
figure, and what remains. Write the receipt BEFORE the last item if budget is short.
