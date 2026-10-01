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
   S3b DONE -> VERDICT NON_INFERIOR (run on GEX44 @ cdae503, records copied to
   vault/benchmarks/agent_virtualization_v2/runs/s3b/, laptop re-score identical). Hits/6
   mono|virtual|crippled: F4 6|6|5, F5 6|5|4, F6 6|6|5 (totals 18|17|14); FP F4 1|2|2,
   F5 0|1|1, F6 0|1|1. Crippled regressed on F5 only (the control can now see a loss; thinly).
   Virtual paged 5-6 deep pages in 3/3. Mean seconds 64.1|76.9|59.1 (virtual +20 %). n=1 per
   arm. Fixed on the way: manifest hashed host line endings (8a7cfaa); parser lost the reply in
   claude 2.1.285's sync Agent shape and recorded reply=0 as MEASURED (cdae503; 3 bad records
   kept in runs/s3b/invalid/). GEX44 lacks agent-solo-guard + carrier_bash_guard hooks.
2. S4 IN PROGRESS -- plan APPROVED by Owner 2026-10-01, harness-optimizer = WRITER class (option a).
   Correction: only 2 markers existed (both done). The 9 come from
   vault/audits/agent_estate/INDEX.generated.md: comment-analyzer, type-design-analyzer
   (investigator); cpp/go/java/python/rust/typescript-reviewer (verifier: they run diagnostic
   commands); harness-optimizer (writer). Nothing written yet. Verified facts for the markers:
   - Each body = provenance comment, `## Prompt Defense Baseline` (byte-identical to
     agent_primitives/prompt-defense-baseline.md in all 9 -> use the primitive), then the role.
     Role-start prefixes (unique): `# Comment Analyzer Agent`, `# Type Design Analyzer Agent`,
     `You are the harness optimizer.`, `You are a senior {C++|Go|Python|Rust} code reviewer`,
     `You are a senior {Java|TypeScript} engineer`. Copy silent-failure-hunter.json's shape.
   - Deep (on_demand) pages ONLY: java `### HIGH -- JPA / Relational Database` (data layer,
     incl. Panache/NoSQL) up to `### MEDIUM -- Concurrency and State` (inline again);
     java `### MEDIUM -- Workflow and State Machine` up to `## Diagnostic Commands` (inline);
     typescript `### MEDIUM -- React / Next.js` up to `### MEDIUM -- Performance` (inline).
     Everything else inline (paging cost +20 % in S3b). output_contract native for all 9.
   - Contracts: CapabilityContract needs owner, triggers, consumers. Writer harness-optimizer
     with write_surfaces REQUIRES rollback + kill_switch (HR-APA-009). Resolver default grant
     is verifier, so writer is only resolvable with an explicit writer grant (intended).
   - Triggers are phrase + order-free word-set matched: use multi-word language triggers
     (`go code`, `go handler`, `golang`), never bare `go`.
   DONE 2026-10-01: 9 markers written + split, all 9 round-trip byte for byte (java 7 pages,
   ts 5, rest 3). tools/test_agent_s4.py 43/43 (load+round-trip, class keeps every source
   tool, carriers grant exactly their class, primitive in 9/9, deep set exact, 9 positive
   routes, 3 negatives, writer excluded without grant / top with --max-class writer,
   HR-APA-009 refusal, bare-"go" mutant turns a negative red). spec 26/26, resolver 14/14,
   bundle 14/14, bench 16/16. Known limit: "C++" tokenizes to nothing, so cpp-reviewer is
   reached via cpp / cmake / raii / smart pointer vocabulary, never by "C++" alone.
   harness-optimizer gains Write via the writer class (source had Edit only).
   NEXT: one real GEX44 dispatch per carrier class (investigator: comment-analyzer; verifier:
   go-reviewer; writer: harness-optimizer on a throwaway repo -- first writer-class run).
3. S5 telemetry, S6 foundry, S7 closure (UKDL, liveness, agent-creation gate).

Start: read the spec, run `python tools/test_agent_spec.py`, `test_agent_resolver.py`,
`test_agent_bundle.py` (all green at this commit), then action 1.
