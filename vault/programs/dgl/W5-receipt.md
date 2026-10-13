# W5 receipt
Status: DONE
Steps 1-7 DONE (W6.md + route-W6.json at 4651a6ab). Flipped from PARTIAL after W6 capital packet bc01a911 APPLIED (Owner 'approve dgl only' 2026-10-13; programme 47.5M -> 48.5M, executable 3,686,595 >= route-W6 stop 3,400,000).
COMMITS: source dgl/durable-goal-lease ef6bd810; merge bd5af362 on dgl/live-merge (W5-r1/r2, 4 conflicts resolved --ours, live a strict superset);
live merge 187629ad = d05a39f6 + bd5af362 on feature/knowledge-acquisition (session 159949c6, lease L13 dgl:W5:r6, packet b9b456dd).
Live HEAD at deploy: 187629ad. Pre-merge: 0 staged, no MERGE_HEAD, overlap of the 39 dgl files with 401 committed + 1133 dirty live paths: 0/0.
Gates at bd5af362 (mwt, this session): 11/11 rc=0 (GOAL_PASS 59/59, HOOK_PASS 7/7, DRIVER 27/27 from pp-dgl cwd).
Gates in live 187629ad: 9/11 in one batch run concurrently with the e2e smoke; workspace_lease 9/10 (V-WS-HOOK-CLOSED-LEASE-FENCED got
  UNKNOWN deny) and goal_budget_admission TIMEOUT at 300 s. Each re-run alone: WS_LEASE 10/10, GOAL_PASS 59/59 (170 s). Both read as
  load-dependent (guard's python call slow -> fail-closed UNKNOWN), cause NOT proven. goal_lease is 20/20 in live (d28 3c98097b added 10).
Smoke e2e (scratchpad dgl_smoke.py, mkdtemp state, live code): SMOKE_PASS=4/4 -- goal_succession succeed CLI (L1 closed, L2 open,
  workspace gen 2, total_used 700,000); goal_autopsy CLI state OK; node session_budget_guard.js DRAIN deny on Agent; closeout Write allowed.
Hook: NOT copied. hook-dispatcher.js loads ../skills/claude-power-pack/hooks/session_budget_guard.js from the live checkout (Bash/Edit/Read/
  Agent lanes), so the merge itself deployed it; a copy in ~/.claude/hooks would be a dead twin. goal_session_end.js unregistered (Owner-side).
Task PP-DglChain-Tick: before wscript hidden_launch.vbs "C:\Users\User\Apps\pp-dgl\vault\programs\dgl\dgl_chain_tick.ps1";
  after same wrapper, "C:\Users\User\.claude\skills\claude-power-pack\vault\programs\dgl\dgl_chain_tick.ps1"; trigger PT15M unchanged.
schtasks /run 15:19:43 -> LastTaskResult 0, log 15:22:40 rc=0 stopped_without_done W5 (acted on nothing). chain.json units still point
  receipts/packets at Apps\pp-dgl (live copy is content-identical; paths unchanged on purpose).
Decisions that differ: no hook copy (above); receipt PARTIAL not DONE (step 7 excluded); the two live-batch reds accepted on solo re-runs.
Calls: W5-r1..r3 ~40; this session (159949c6) ~35.
