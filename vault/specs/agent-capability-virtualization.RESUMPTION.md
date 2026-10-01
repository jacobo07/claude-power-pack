# Agent Capability Virtualization -- resumption (after S2)

Repo `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`,
worktree = repo root. Plan + Owner decisions: `vault/specs/agent-capability-virtualization.md`
(approved 2026-09-30: full scope, commits pushed, benchmark on subscription quota, cheapest design).

## Sealed (pushed)
- aa1b8e9 agent-solo-guard deadlock fix (18/18). c75abd4 estate audit + real discovery curve
  (N=0/100/400/1000 -> 68,288/77,082/97,195/135,563 parent tokens; 64-88 per listed agent).
- 5f44ac3 benchmark fixtures frozen (vault/benchmarks/agent_virtualization, MANIFEST sha256).
- a5e2e33 S1: AgentSpec (modules/capability_runtime/agent_spec.py), 3 carriers (agents/carriers,
  installed in ~/.claude/agents), carrier_bash_guard.js wired in PreToolUse-Bash-chain.
- S2 commit (this one): resolver, proof bundle, pointer delivery, silent-failure-hunter spec,
  prompt-defense-baseline primitive, tools/agent_carrier_run.py. Real boundary: VALID bundle
  through cpp-carrier-investigator (vault/audits/agent_estate/real_boundary/).

## Do not re-litigate
- Agent tool is ASYNC in Claude Code 2.1.286: carrier reply = last sidechain text.
- `git` is not on subprocess PATH here: current_state_version falls back to absolute path.
- hooks/hook-dispatcher.js carries ANOTHER pane's uncommitted hunk (names in the
  CHAIN-DEADLINE log). Never commit or deploy it; stage only your own hunks.

## Next 3 actions
1. S3 DONE -> VERDICT VOID (2026-10-01, runs/s3/score.json). Hits/8 mono|virtual|crippled:
   F1 8|7|8, F2 8|8|7, F3 8|8|8; FP F1 0|2|1, F2 0|0|1, F3 1|1|1. The crippled control
   (inline pages only) never regressed, so these fixtures cannot see a capability loss. The
   inline core alone reaches ceiling on them. Also: virtual carriers read their image but
   opened 0 deep pages in 3/3 runs -- virtual behaved as crippled + a path list, so even a
   valid NON_INFERIOR would not have tested paging. F1 virtual's miss+FP is one block that
   raised a different real ReconcileService flaw (frozen key: miss + FP). S4 BLOCKED.
   One F3-crippled run was UNMEASURED (Haiku parent made no Agent call) and re-run once.
   OWNER CHOSE (a), 2026-10-01. Done so far: paging fixed (af6b287: probe refuted "the
   no-explore sentence blocks paging", a stated read-step made the carrier read 05/06/10 on
   frozen F1; cost 354 s vs ~140 s, n=1) + harness no longer loses a run to temp-dir cleanup.
   Benchmark v2 (S3b) authored + FROZEN: vault/benchmarks/agent_virtualization_v2 (F4-F6,
   6 defects each, every one deep-page-only doctrine; key gates in test_agent_bench.py 16/16:
   correct finding hits own defect, restating a step scores nothing, page is on_demand).
   v2 RUNS ON GEX44 (laptop run was reaped at 0.8 GB free, 0/9 done): clone
   /home/kobii/missions/agent-bench-s3b @ bench/s3b = 8a7cfaa (manifest now hashes LF-normalized
   content; same frozen content), carriers installed in kobii's ~/.claude/agents, runner pid
   2188580 detached, log s3b_run.log, records in that clone's runs/s3b/. Resumable: re-run
   `python3 tools/agent_bench.py run --set v2` there. Then score there (or fetch runs/s3b back)
   with `score --set v2`. Only NON_INFERIOR unblocks S4. GEX44 has no agent-solo-guard and no
   carrier_bash_guard hook (test_agent_spec 24/26 there for that reason only).
2. S4: migrate the other 9 dormant agents (agent_split_markers/*.json), gated on S3 NON_INFERIOR.
3. S5 telemetry, S6 foundry, S7 closure (UKDL, liveness, agent-creation gate).

Start: read the spec, run `python tools/test_agent_spec.py`, `test_agent_resolver.py`,
`test_agent_bundle.py` (all green at this commit), then action 1.
