# Cognitive Memory Virtualization — ULTRA-PLAN (2026-09-30)

Status: APPROVED 2026-09-30 — Owner: "yes to all, as long as I don't lose output quality".
Read as: Q1 quota probes now · Q2 blanket consent per move ONLY with backup + non-inferior ablation ·
Q3 deferred list stands · Q4 (either/or, the conservative branch) V4/V5 FEED rollover/Ralph, no takeover ·
Q5 absolute before/after + non-inferiority bar · Q6 in place with pathspec commits, not a worktree
(V0c/V1 change live ~/.claude, which a worktree cannot isolate; tools/rollover.py is peer-dirty, never staged).

## Revised task list (ULTRA phase 3)
| # | file | action | purpose | verification |
|---|---|---|---|---|
| T1 | tools/session_autopsy.py | edit | growth attribution | SEALED `a270ab3`, 15/15, 4 new red on old code |
| T2 | tools/fresh_context_tax.py | edit | bootstrap per UTC day (Ralph workers only) | SEALED `61c80ae`, 5/5, 2 new red on old code |
| T3 | modules/pp_eval/runner.py `arm_args` | edit (NOT a new floor_probe.py: A1, A14) | add MCP-off (`--strict-mcp-config`) + plugins-off arms beside its existing rules/hooks/skills-off arms | fixed neutral cwd (A5); one prompt, pinned model; stream-json first call = the ONE source (A3); `<synthetic>` = UNMEASURED (A6); a positive control per arm (A4); A/A replicate spread = noise floor (A6); hook events confirm SessionStart runs under -p |
| T4 | same run | read | per-hook injected-context census from `--include-hook-events` | real numbers |
| T5 | this file | edit | V1 ranking; per move: backup -> change -> B-prime arm (rule LOADABLE via Skill, not removed: A17) -> keep/revert | per move: first-call delta beyond A/A noise + a named load-back path + measured load-back rate; quality claim = "no degradation observed" unless >= 2 tasks/rule that the removal arm FAILED (A16) |
| T6 | modules/rtk-core/rtk-rewrite.js | edit — PLAN mode (A7-A11) | PowerShell branch (today PowerShell gets a POSIX rewrite: A7); tee via `*>`/Tee-Object with `$LASTEXITCODE` preserved; NO `permissionDecision:allow` (A9); flag default OFF in the same edit (A8); size unknown pre-exec, so always-tee under flag + head/tail + locator (A10) | tests on a copy; exit-code test; both dispatchers diffed and synced (A11) |
| T7 | modules/pp_eval (peer-active: e079c57) | edit, coordinate | converter from P3 mutant/judgement tasks into the bank (A15); verdict needs >= 4 discriminating tasks (A16) | pp_eval verdict not ABSTAIN |
| T8 | vault + UKDL + tower + liveness | edit | baseline + RESUMPTION; `modules/token-optimizer` has no `__init__.py`, so liveness is vacuous there (A14): avoid new modules in it | /liveness exit 0 on a module it can see |
Debt recorded, not fixed here: p3_runner duplicates pp_eval runner helpers (A2); interactive floor is measured by
tis_observed, not T2 (A13); MCP schemas load on demand, so an MCP-off arm under-counts them (A17).
Audit evidence: session scratchpad `audit_gaps.md` (17 gaps, A1-A17).
Extends, does not replace: `vault/plans/context-rent-2026-09-27.md` and
`vault/plans/cognitive-resource-os-2026-09-27.md` (both APPROVED, both in execution by peer panes).

## Reality (measured 2026-09-30)
- HEAD `0ba8565`, branch `feature/knowledge-acquisition`, 618 dirty paths from other live writers (not ours).
- FLOOR: `tools/fresh_context_tax.py` -> bootstrap median 176,060 tok (n=111 worker sessions,
  min 122,419, max 196,381; 395 provider-refused and 61 unmeasured excluded). Historical mix: the rules
  shrank from ~260 KB to 69 KB between 09-28 and 09-30, so the current floor is not yet split by date.
- Countable file prefix: `modules/token-optimizer/prefix_inventory.py` -> ~61.5k tok ESTIMATE
  (bytes/3.8): CLAUDE.md x3 21.6k, rules 18.2k, skill listing 9.4k, agent listing 7.0k, MEMORY 4.2k,
  commands 1.1k.
- FLOOR BY DATE (same tool, grouped by transcript creation day): 09-25 median 194,800 (n=22) ->
  09-28 176,165 (n=27) -> 09-29 153,118 (n=16) -> 09-30 150,376 (n=27, min 122,419). The rule moves
  already cut ~44k. The current floor is ~150k, not 176k.
- GROWTH ATTRIBUTION (scratch probe `growth_probe.py`, 60 transcripts >200 KB from the last 5 days, chars as a
  token proxy): tool_result 78.4 %, user text incl. injected reminders 12.1 %, assistant text 6.4 %,
  thinking 3.2 %. By tool: Read 56.5 %, PowerShell 26.0 %, Grep 9.3 %, Agent 0.9 %. Read calls 1,550,
  of which 506 re-read an already-read path (32.6 %; 10.7 % of tool_result chars; includes legitimate
  re-reads after edits). Excluding re-reads that follow an Edit/Write of the same path: 208/1,495 = 13.9 %,
  6.5 % of tool_result chars (upper bound: paged reads of one file also count).
- UNATTRIBUTED FLOOR today ~88k (150k - 61.5k); historically ~110k: harness system prompt, tool schemas (5 MCP servers, 8 plugins),
  plugin skills and agents, and context injected by the 13 SessionStart hooks. No instrument has measured it
  (context-rent P1b deferred it because of quota).
- GROWTH: `tools/token_ground_truth.py` (dedup since 8c39c27), 2026-09: cache read 43.9 B,
  cache create 670 M, output 121 M, hit rate 98.5 %. Incident 04b41ed7: rent = 47 % floor + 53 % growth.
- Already live: rollover.py (/kclear -> gate -> /clear -> /kresume, ACTIVE by default, kill switch
  CPP_ROLLOVER_ACTIVE=0); gsd_epoch/gsd_mission (Ralph, owned by a peer); tis_observed; session_autopsy;
  pricing source; the P3 ablation that moved 9 rules into skills (09-29/30); rules-evidence split.

## Governing decision (HR-NOVELTY-001)
This is the third architectural pass on this area in four days. 0 new systems. The prompt's concepts map to
existing owners. NEW is limited to instruments that have no owner.

## Harness constraint that shapes everything
Claude Code cannot remove content from a live context. The only primitives are: not loading content,
loading it on demand (skills, Read, graph query), a separate context (subagent), and the epoch boundary
(/clear + rehydrate, /compact). So "eviction" = what the next epoch's capsule leaves out, "paging in" =
on-demand load, and the "working-set manager" = the capsule compiler plus a break-even controller.

## Quality evidence already on record
P3 ablation (`.planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/REPORT.md`, `bec5fa0`):
32/32 + 24/24 judgement runs, non-inferior; moves 1-3 cut first-call context by ~27k. Moved-rule skills
auto-activated 0/4. Only a PreToolUse card (`destructive_doctrine_card.js`) reliably pages a moved rule
back in. The 6 moves of 09-30 have NO ablation (their pointer files say so): quality debt.

## Phases (dependency order; EXECUTION mode unless marked)
- V0 Metrology completion: session_autopsy growth attribution (from the scratch probe, with tests);
  fresh_context_tax date split; harness-floor attribution by controlled headless arms (quota, Q1);
  census of context injected per hook.
- V1 Floor levers ranked by V0 size, each = backup + p3_runner ablation arm + Owner yes (Q2). Page faults
  for lazy doctrine = deterministic hook card, never skill auto-activation (0/4). Backfill ablation for
  the 6 unablated moves of 09-30.
- V2 Always-on context tax budget: claude_md_firewall.js aperture over rules/, listings, hook injections.
- V3 Growth: Read discipline advisory (unchanged path / large full read -> offset or LSP symbol),
  PowerShell large-output tee + locator. Shadow first, measured on the V0 probe.
- V4 Break-even controller (PLAN mode): rollover trigger from a fixed % to a cost model, shadow-logged.
- V5 Capsule = context image: settled decisions + negative cache with freshness; resume exam recall items.
- V6 Baseline: UKDL 3 levels, tower/CBR, liveness, KNOWN_FALSE_POSITIVES, RESUMPTION.

## Ownership audit amendments (subagent, ~38 files, file:line cited in session)
- V3 output tee: MISSING, no owner diverts output to a file; build it inside rtk-rewrite.js (EXTEND), not as a new hook.
- V4: rollover.py:485-510 `decide()` already computes break-even N*, runs SHADOW only
  (context-watchdog.py:1034-1068); live trigger is the fixed wall (watchdog :45, rollover_wall.js).
  V4 = judge the shadow log, then promote decide(); no new controller.
- V1/V5 ablation: p3_runner is a one-off under .planning; pp_eval (SCHEDULED nightly) has a task bank of 0.
  Move P3 tasks into pp_eval so non-inferiority becomes a standing gate. Skill auto-activation 1/12 overall.
- V5 negative cache: only gsd_x/goal/epoch.py:275 (orphan engine). EXTEND session_delta instead.
- Retire candidates: tools/memory_manager.py (stale kobig path, 0 callers), memory-engine/append_memory.py.
- Symbol-first: audit_cache has no symbols; decision stands = harness LSP, no new index.

## Rejected / deferred
MVCC, copy-on-write, fork/join (agent results 0.9 % of growth). Learned policies and budget market (no
trustworthy telemetry yet). Physical KV (not controllable). New MMU store (graphify IDs exist). Belady
oracle = offline metric only. Mid-session eviction (not a harness primitive).
