# UCEP live observations (session 300ac3a1, 2026-10-03) — feed for Phase 9 incidents/metrics

## D7 false activation (vocabulary-only family injection), observed on the real prompt path
- When: orchestrator turn receiving the Phase 2 researcher hand-back (subagent report, builds nothing).
- Injected: `wii_homebrew/B0` (sha256 2603cf39889c), 8 rules shown + 7 "judged anyway".
- Trigger: matched word "wii" — the report mentioned the repo name "ABSW2-Wii" as a zero-manifest example.
- Disposition given: NO APLICA (orchestration turn, no Wii build).
- Same class as the plan-of-record line 6 incident (hand-back containing "schema" -> persistent_state/B0).
- Denominator note: count every orchestrator turn that received a family block vs turns that actually built that family.

## SDD-OS ambiguous binding refusal on an orchestration turn
- Hook refused Tier-2 binding: 6 specs matched equally (cdio-enforcement..., claude-md-compaction..., intent-verified-done..., d2a-family-wiring, parent-context-epoch-rotation, uwcp). None governs UCEP.
- Mitigation used: governing spec named explicitly in every executor/planner prompt (vault/plans/ucep-naked-verb-2026-10-02.md).

## Tooling friction (not UCEP scope, record only)
- EnterWorktree failed: "git not found" (git absent from the harness PATH). Worked in place via absolute paths.
- gsd-tools `worktree.base-check` returned head-unresolvable for the same reason (node has no git on PATH); degrade verdict correct by coincidence.
- Agent isolation guard required an explicit `dispatch-isolation --force-isolation none` sentinel per plan.
- Executor subagents had no PowerShell tool; ran via Bash with absolute exe paths.
- concurrent-writers hook blocked a tracking commit of gsd-tools-written hunks (tool writes invisible to it); re-issue passed.

## Second D7 false activation (epoch-1 worker, reported in the epoch-2 hand-off card)
- The mission card said: "Add this session's second false activation: `wii_homebrew/B0` was injec..." and the card was TRUNCATED there.
- Recorded by epoch 2 (session 911e5177) as: count = 1 additional `wii_homebrew/B0` false activation in the epoch-1 worker; trigger and turn type UNKNOWN (lost to card truncation).
- Phase 9 note: the hand-off card itself drops tail facts. A fact that only lives in the card's last line is lost; durable facts belong in this file or STATE.md, not the card.

## Epoch 2 (session 911e5177, 2026-10-03)
- Prompt path on wake: Tower baseline block injected (inherited lessons), NO family block -> no D7 activation this turn.
- concurrent-writers hook again blocked the phase.complete tracking commit (cb47c973); identical re-issue passed. Second occurrence of the same class.
- AGENT-SOLO contract guard blocked a gsd-plan-checker dispatch TWICE: first prompt carried a write-as-you-go clause (correct block, checker has no Write); second prompt used the guard's own fix (2) wording ("the parent session persists your returned report to disk") and was blocked identically. Root cause (read agent-solo-guard.js:287): DURABLE_OUTPUT regex 1 matched the NOUN "plan of record; audit gaps in `vault/plans/...audit.md`" (`record` + path ending .md) -- the mandated governing-spec line triggers it in every read-only dispatch. Pivoted to fix (1): general-purpose agent reading gsd-plan-checker.md.
- Hand-back turns (executor reports 02-01..02-03): no family block injected on any of them (0 D7 activations in 3 hand-back turns this epoch; denominator for the D7 rate).
- SDD-OS ambiguous-binding refusal recurred on the 02-03 hand-back turn (orchestration only, builds nothing): 4 specs matched equally (claude-md-compaction-2026-07-26, d2a-family-wiring, parent-context-epoch-rotation, uwcp-assimilation); none governs UCEP. Same class as the epoch-1 entry above.
- Measured by the 02-03 executor (RESEARCH A10 settled): on this host `os.walk(followlinks=False)` DOES descend a directory junction (128 files with the link vs 2 without). trait_scan now prunes islink/isjunction itself, and its gate disables the prune to prove it can fail.
- D7 FALSE ACTIVATION #3 (mission total; #1 epoch 1 on "wii", #2 epoch 1 truncated): the 02-04 executor hand-back turn was injected `persistent_state/B0` (sha256 bcb20d37f568), 7 rules shown + 8 "judged anyway". Trigger words "database, sqlite" -- they occur only inside the subagent's REPORT ("re-stat'ing a live database would pin the cache STALE", "sqlite, level.dat"). Disposition: NO APLICA x15 (orchestration turn; writes were a log line and a tracking commit; nothing persisted, nothing destroyed). Running rate this epoch: 1 family block in 4 hand-back turns, 0 of which built that family.
- D7 FALSE ACTIVATION #4: the 02-05 executor hand-back turn was injected `wii_homebrew/B0` (sha256 2603cf39889c), 8 shown + 7 "judged anyway". Trigger "wii" from the repo name "ABSW2-Wii" inside the subagent's real-pole report line -- identical trigger to #1. Disposition: NO APLICA x15 (no Wii build; Python capability module; orchestration turn). Running rate this epoch: 2 family blocks in 5 hand-back turns, 0 built the family. A repo NAME in evidence text is enough; any later real-pole report citing ABSW2-Wii will re-trigger it.
- Host timing fact for any budget gate: `time.monotonic()` is GetTickCount64 (15.6 ms); `time.perf_counter()` is QPC (0.1 us). A `budget_s=0` cut written against monotonic can read elapsed 0 and never fire.
