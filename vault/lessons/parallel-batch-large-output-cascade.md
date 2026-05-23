---
name: parallel-batch-large-output-cascade
description: When batching tool calls in one response, if any tool returns >5 KB (Bash with hook decorations, or Read intercepted by gatekeeper-semantic's 40 KB blob), lightweight sibling tool results may return [Tool result missing due to internal error]. Third sister of the parallel-IO cascade family.
metadata:
  type: feedback
related:
  - parallel-explore-cascade.md
  - feedback_parallel_write_batch_limit.md
  - feedback_internal_error_verify_before_retry.md
  - hook-fanout-systemic-cost.md
---

## Rule

When dispatching multiple tools in a single response:

- **Never batch Bash with Read/Glob/Grep whose results you need to proceed.** Bash output is hook-decorated (rtk warning prefix, dispatcher reminders, additionalContext blobs); under load the harness pipe can drop the lightweight neighbors.
- **Never batch a Read against a known doctrine-heavy path with other Reads.** If gatekeeper-semantic's blob fires inline (≤ inline cap, on small files), the same crowding-out happens.
- If you must run a Bash + 1 Read in parallel, batch size 2 max and pick the Bash that returns small output (e.g. `git status --short` not `git log -20`).
- For >2 tool calls per response when output volume is unpredictable: sequentialize across responses.

## Why

2026-05-21 Zero-Command plan PASO 0: batched `Glob + Read(offset=60, limit=25) + Bash(git log)` in one response. The Bash returned ~30 lines that the dispatcher prefixed with the Power Pack reminder (~2 KB), making total Bash output ~3 KB. The Read on a 78-line markdown file returned `[Tool result missing due to internal error]` despite the file being trivially small. Pure root cause: harness pipe budget crowded out the small Read result; the Bash result returned in full.

This is the third instance in the same lineage:

| Surface | Existing memory | Failure trigger |
|---|---|---|
| Parallel Explore agents | `parallel-explore-cascade.md` | ≥2 file-read-heavy Explore agents on same repo |
| Parallel Writes | `feedback_parallel_write_batch_limit.md` | 3+ parallel Writes in one message |
| Parallel mixed tools | **this lesson** | Bash + Read|Glob|Grep in one batch where Bash output is large |

All three are facets of the same underlying constraint: the Claude Code harness pipe has finite capacity per response turn; large-output tools crowd out lightweight neighbors. The official Anthropic SDK has timeout/buffer limits that under load drop the smaller results rather than block the whole batch.

## How to apply

1. Before composing a parallel tool-call batch, classify each call by expected output size: tiny (<1 KB), medium (1-5 KB), large (>5 KB).
2. If any call is large or unpredictable AND a sibling call's result is on the critical path for your next reasoning step → sequentialize. Run the large one alone or with one tiny sibling at most.
3. Hook-decorated outputs always run larger than the raw command suggests. A `git log -3` may emit 200 bytes of git output + 2 KB of hook-injected boilerplate. Budget for the decoration.
4. When a parallel batch returns one or more `[Tool result missing due to internal error]`, the lesson `feedback_internal_error_verify_before_retry.md` (BL-0012) applies: verify state before retry. Plus: re-dispatch the missed tools sequentially in the next response.

## Reach boundary

Applies to in-session tool-call batching. Does not apply to subagent dispatch (covered by `parallel-explore-cascade.md`) or to settings-level hook stack overhead (covered by `hook-fanout-systemic-cost.md`).

Until the hook stack is consolidated (see `[[hook-fanout-systemic-cost]]` for the underlying architectural cause and the Zero-Command plan's Component E for the fix), this rule is load-bearing.
