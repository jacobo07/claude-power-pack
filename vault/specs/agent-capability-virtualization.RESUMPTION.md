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
1. S3 benchmark: for F1..F3 x modes monolithic/virtual/crippled, run
   `python tools/agent_carrier_run.py oneshot-architect-auditor --mission-file <fixture> --mode <m> --model sonnet`
   (mission = "Audit this plan. Output the ULTRA gap list." + fixture text); write a scorer
   against answer_key.json (verify MANIFEST hashes first). Verdict rule is in the spec.
2. S4: migrate the other 9 dormant agents (agent_split_markers/*.json), gated on S3 NON_INFERIOR.
3. S5 telemetry, S6 foundry, S7 closure (UKDL, liveness, agent-creation gate).

Start: read the spec, run `python tools/test_agent_spec.py`, `test_agent_resolver.py`,
`test_agent_bundle.py` (all green at this commit), then action 1.
