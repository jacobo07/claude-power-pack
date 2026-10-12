# WU-S1-FINISH (v2) -- ctx-same-pane S1 items 4-6. Owner-approved; no Owner questions.
Repo C:\Users\User\Apps\pp-ctx-same-pane, branch ctx/same-pane, HEAD 4dff1b8. Goal ctx-same-pane, lease L6 (1.27M).
Owner option 1 (2026-10-12): finish S1 inside the P80 ceiling. S4 is NOT in this WU.
Admitted route: AT MOST 9 calls at about 115K each. Plan: call 1 boot, calls 2-3 item 4, calls 4-6 item 5,
call 7 item 6, call 8 receipt + final commit, call 9 spare. Items 1-3 are DONE (aa82d3ac, 68b26a9d); do not
re-validate them. The previous worker spent 7 of 9 calls on boot and reading: do not read code to orient.

Call 1 -- boot. Paste EXACTLY this one command (no `cd`, no `$var=` assignments: the pre-certification hook
refuses any command that assigns a variable or does more than observe):
  $env:PYTHONIOENCODING='utf-8'; & 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe' C:/Users/User/.claude/skills/claude-power-pack/tools/mission_capsule.py resume --mission m-4d1b851262ff; & 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe' C:/Users/User/.claude/skills/claude-power-pack/tools/mission_capsule.py certify --mission m-4d1b851262ff --goal STATE.md --branch ctx/same-pane --head 4dff1b8 --next "execute phase 1: S0 ctx-rent S2 repair" --dirty 0
If certify says Wrong: next, re-run ONLY the certify part with --next copied verbatim from the resume output.

The 5 real transcripts (do not search for them):
  C:\Users\User\.claude\projects\C--Users-User-Apps-pp-ctx-same-pane\6d8f3412-4bcf-4ed2-be85-9c6bf2f323f5.jsonl
  C:\Users\User\.claude\projects\C--Users-User-Apps-pp-ctx-same-pane\98bcc118-c66b-4b20-b741-bf20a247a9c6.jsonl
  C:\Users\User\.claude\projects\C--Users-User-Apps-pp-ctx-same-pane\f6a396a1-a307-4f9a-920b-1f28ae898b6e.jsonl
  C:\Users\User\.claude\projects\C--Users-User-Apps-pp-ctx-same-pane\e4347e5e-b685-4afc-ae40-86be3e005d64.jsonl
  C:\Users\User\.claude\projects\C--Users-User--claude-skills-claude-power-pack\d5063bac-b344-446e-9dfb-9ac2234ce8bf.jsonl
Known: e4347e5e's first call carried 108,499 context tokens (input + cache read + cache creation).

Item 4 -- tools/floor_census.py (repo-relative, run from the worktree), deterministic, no model calls: chars/4
  estimate of what loads at session start: ~/.claude/CLAUDE.md, ~/.claude/rules/*.md, the repo CLAUDE.md files
  on the cwd chain, the project MEMORY.md, and the SessionStart hook additionalContext found in each transcript's
  first entries. Reconcile against call-1 context of the 5 transcripts; report the unexplained gap as host floor
  (system prompt + tool schemas). Test file tools/test_floor_census.py with V-FLOOR-CENSUS-* gates. Commit.
Item 5 -- vault/programs/ctx-same-pane/s1/attribution.json from the same 5 transcripts via tools/session_autopsy.py
  (floor vs growth split, subagents per type). Add V-gates for it to tools/test_floor_census.py and kill one
  mutation drill with tools/mutation_drill.py on an isolated copy. Commit.
Item 6 -- the controllable-floor figure: the census part the Owner's files control (CLAUDE.md chain, rules,
  memory, hook context), in attribution.json and the receipt. Under 25K controllable means A1 is not worth it:
  say so plainly. Commit.
Every commit: pathspec only. Stop-loss: halt with the receipt when L6 has under 150K left, or a step fails
twice after a local fix; whatever does not fit goes to the receipt as remaining.
Common: no Monitor, no waiting call, no GSD commands, no planner or plan checker, no subagents. Never edit
tools/gsd_mission.py or settings.json. Never call capital-apply, goal-declare, goal-lease-open or goal-settle.
Receipt: append to vault/programs/ctx-same-pane/RECEIPT-S1-STOPLOSS.md a section '## WU-S1-FINISH' with Status
DONE or BLOCKED, commits, measured calls and processed tokens from your own transcript, the controllable-floor
figure, and what remains. If budget is short, write the receipt BEFORE item 6.
