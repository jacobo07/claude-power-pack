# Stage 0 evidence -- InfinityOps odr-device-trust (TOK-18 gen2 first live canary workload)

Measured 2026-10-05 by pane tua-x-96 (session 242ae047), read-only, zero-model scripts over transcripts.
Workload: InfinityOps worktree `C:\Users\User\Apps\io-device-trust` (branch feat/odr-device-trust, HEAD b01fb3ac),
missions m-4df3ebcb89ff -> m-608c8d8d761f (renewal 1), workers be2a71eb 50d3a9f0 affe87e4 63bc3ed8 dc79aa64 5f5bc46f
4f1b398d dfc0acda; transcripts in `~/.claude/projects/C--Users-User-Apps-io-device-trust/`.
Unit: processed = input + cache_write + cache_read + output, deduplicated by message id (same as ../README.md).

This closes the "UNVERIFIED" floor/role split in ../README.md "External baseline" -- re-run the scripts instead of re-deriving.

## Totals (`io_phase_tokens.py`; attribution = phase of the next commit, 55/55 commits carry a phase id)
| phase | msgs | cache_read | cache_write | output | processed |
|---|---|---|---|---|---|
| 1 (7 req, 5 plans) | 457 | 113,887,832 | 2,373,519 | 268,379 | 116,530,644 |
| 2 (5 req, 5 plans) | 530 | 124,212,928 | 2,868,898 | 268,954 | 127,351,840 |
| 3 (4 req, 5 plans) | 342 | 86,989,345 | 1,889,121 | 214,542 | 89,093,692 |
| 4 so far (context, research, UI spec) | 202 | 40,532,544 | 982,848 | 57,222 | 41,573,018 |
| total | 1,531 | 365,622,649 | 8,114,386 | 809,097 | 374,549,194 |
Fresh input 3,062 tokens in total.

## Main workers vs subagents
- Main (`io_context_rent.py`): 903 calls; first-call floor mean 129,030 (min 125,997, max 132,504); context per call
  mean 275,249, median 273,524, p90 380,540, peak 419,509 (rotation wall ~400k).
- Subagents (`io_subagents.py`): 23 transcripts, 628 calls, 125,189,983 context (33%); floor mean 84,637; per run:
  gsd-planner 3 runs 43.9M (14.6M/run), gsd-phase-researcher 4 runs 35.8M (8.9M), gsd-verifier 3 runs 22.1M (7.4M),
  gsd-code-reviewer 3 runs 8.4M (2.8M), plan-checker 4.9M, ui-researcher 4.8M, executor 2 runs 1.6M total.
  Execution ran INLINE in main workers; per-plan cost is planning/research/verification amplification.

## Main-worker context rent by class (`io_context_rent.py`, normalized; +-10% relative)
floor 44% (rent = floor x calls) / injected attachments 27% / tool_result 21% / tool_call_input 7% / model text +
thinking < 1%. "Workers rereading their own narrative" is false here.

Two instrument corrections, both found by the scripts' own controls:
1. `prompt_snapshot` attachments are the host's RECORD of system prompt + tool schemas (18,155 + 137,431 chars), not
   extra context. Counting them as history double-counted 44.4M (attribution read 108% of measured). Excluded: 90%.
2. Hook success text IS in context: regressing per-call context growth on appended chars (`io_hook_regression.py`,
   895 calls) gives 0.594 tok/char for `hook_success` records vs 0.411 conversation, 0.319 other attachments -- a
   coefficient that could have been ~0 and is not. Collinear with tool calls: magnitude approximate, direction
   solid. PreToolUse/PostToolUse success text ~7-13% of main-worker context (~20M on this workload).

## Floor composition per main worker (~129k; `io_attachments.py`, chars x 0.32)
host system prompt ~5k + tool schemas ~35-44k (hard; part may be account connectors -- split UNKNOWN) /
instructions (CLAUDE.md + rules) ~45k / agent listing ~13k / skill listing ~12k / SessionStart + UserPromptSubmit
hook output ~6.6k + ~2k / deferred tools + MCP instructions + files ~4k. CPP-controllable soft floor ~80k.

## Not measured
Dead share of tool_result rent; subagent history composition; Phase 4 remaining plan count; floor savings achievable
under Claude Code's actual listing/skill controls.
