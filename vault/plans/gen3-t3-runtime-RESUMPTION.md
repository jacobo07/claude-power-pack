# RESUMPTION -- Gen3 T3 bounded execution runtime (Owner-approved 2026-10-05, "Approve all, gate lifted")

Worktree `C:\Users\User\Apps\pp-gen3-t3`, branch `ce/gen3-t3-runtime` (from 646c6c86). Programme cap 50M processed,
checkpoint at 20M before S7. Supersedes the "Owner decision (a)/(b)/(c)" obligation of tok18-pre-rearm-optimization-RESUMPTION.md.

## Reality Delta (measured 2026-10-05, zero-model; scripts in session 2cc507fd scratchpad acct.py / win.py)
- Subagents 34.93M exact (= README). Parent orchestration 17:35-19:37Z = 8.20M / 20 calls (README ~9.33M estimate).
  T2 in README scope = 43.13M; + parent readout/seal 5.79M (13 calls, 445k/call) + pre-T2 1.87M -> full pane 48.9-50.8M (cap 42M).
- Executors: every worker started at ~104k (host floor); 158 calls x 104k = 16.4M of 26.38M (62%). Reviewer started 72.5k.
- Causes CONFIRMED in source: session_budget_guard read only the parent transcript (children unmetered; Agent has no
  dispatcher lane); agent-solo tracker had no session id; rollover_wall.js has no sealed/clear-pending state;
  session_checkpoint.py roots at Path.cwd() (canary tracks memory/project_session_handoff.md).
- Rollover 87601e81: decision ROBUST_ROLLOVER at 43% (breakeven 17.4 calls) then 13 more calls ran (~2.3M avoidable).

## Sealed in this branch
- S1 80c356fb agent-solo session scope (21/21, mutant red).
- S2 (next commit) tree meter + running-child reserve + per_child_stop + dispatch reserve (V-SBT 6/6, mutant red);
  mission_spend.declare/CLI --per-child-stop --child-reserve, unit field. OPEN: V-SBG-LATENCY 103 ms > 50 ms (flake or
  readdir/stat cost: measure 5 runs at HEAD~1 vs HEAD before landing).
- NOT YET: agent-solo-guard calling decide(payload, {dispatch:true}) (parent kill switch on Agent dispatch).

## Landing rule (live = main checkout working copy, loaded by ~/.claude/hooks/hook-dispatcher.js)
Main checkout holds ANOTHER pane's uncommitted hunk in hooks/session_budget_guard.js (lines ~169-180, per-pid tmp) and
tools/test_session_budget_guard.py. Never commit/overwrite it: apply only this branch's hunks (git diff 646c6c86..HEAD |
git apply --3way in the main checkout, then commit with git apply --cached of the same patch). agent-solo-guard: canonical
copy + Copy-Item to ~/.claude/hooks, hash-verify.

## Next 3 actions
1. Resolve V-SBG-LATENCY; wire dispatch gate into agent-solo-guard (+ red/green case); land S1+S2 live; live probe: one
   tiny subagent Read -> state file shows caller (= is transcript_path the child file?) and files{}.
2. S3: rollover state machine (sealed -> clear_pending -> cleared; wall + Stop no-op while unchanged) and checkpoint root
   from the session's launch project, not Path.cwd(); red/green each.
3. S4 ContextImage on tools/source_packet.py + lean worker profile (measure floor); then S5 LOW micro-canary
   (holdings-client.server.ts:343, envelope stop 1.0M, headless worker), S6 local reality, 20M checkpoint report, S7.

Start: read this file, `git -C C:\Users\User\Apps\pp-gen3-t3 log --oneline -4`, declare the session envelope
(mission_spend.py session-declare, stop <= remaining programme cap), then action 1. Rotate by the economic rule, not 45%.
