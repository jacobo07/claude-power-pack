# WU-C4 -- Semantic breaker + token incident + stop-the-line

Common brief: `vault/programs/cdc/PROGRAMME.md`. Plan section: 3 (C4).

Goal: waste is stopped before the raw token ceiling.
1. `hooks/semantic_breaker.js` on PostToolUse `*` for BOUND sessions only (mission/goal bound; kill
   `CPP_SEM_BREAKER=off`). Progress = commit (HEAD moved), work-tree change, new file, receipt write, test red->green.
   Counters per sid in `~/.claude/state/semantic-breaker/<sid>.json`: calls since progress, rereads (same path,
   unchanged), context growth since progress (from transcript usage if cheap; else skip, never guess).
2. Thresholds come from data: compute calls-between-progress distribution over the existing ledgers (C1 tool) on
   >= 5 historical worker transcripts; trip at p95 (write the numbers into the receipt). Default if data absent: 25.
3. On trip: write `~/.claude/state/token-incidents/<ts>-<sid>.json` (reason, counters, last N tool names) + run the
   C1 role autopsy for that sid into the incident + write the session deny budget through the existing
   session_budget_guard state (EVC U5 spend capability if landed; check `.claude/worktrees/evc` receipts first).
   The worker's next tool call is refused with a recompile message. FIOS class TOKEN_INCIDENT.
4. Tests: synthetic loop of 30 no-progress calls trips; a loop with commits does not; kill switch off = no trip.
5. Live canary: a bounded throwaway mission that loops trips the breaker; record incident file.
Land via land_worktree.
