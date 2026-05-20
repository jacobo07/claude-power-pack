---
name: parallel-explore-cascade
description: Dispatching >=2 file-read-heavy Explore subagents in parallel against the same repo returns [Tool result missing due to internal error] on the 2nd+ agent. Sister rule to the parallel-Write batch cap.
metadata:
  type: feedback
related:
  - feedback_parallel_write_batch_limit.md
  - feedback_internal_error_verify_before_retry.md
---

## Rule

When dispatching Explore subagents in parallel:

- **Maximum 2 agents in parallel.**
- **At most 1 of those 2 may be file-read-heavy** (>3 Globs or >5 Reads expected).
- The rest go sequential — one Agent call per response, wait for return, then the next.
- A WebFetch-only agent is light and may always pair with one file-read-heavy agent.

## Why

On 2026-05-20 during Spec Kit integration PASO 0 audit, three Explore agents were dispatched in a single message:

| Agent | Scope | Outcome |
|---|---|---|
| #1 | WebFetch on 5 spec-kit URLs | OK |
| #2 | Broad file-read on PP repo (Glob+Read 12+ files) | `[Tool result missing due to internal error]` |
| #3 | Broad file-read on PP repo (Glob+Read 8+ files) | `[Tool result missing due to internal error]` |

The harness collapses concurrent heavy file I/O against the same repo. The retry succeeded immediately when agents #2 and #3 were re-dispatched **sequentially** (one at a time across two response turns).

This is the same root failure mode as `feedback_parallel_write_batch_limit.md` (3+ parallel Writes return atomic-batch internal-error) but on a different tool surface. The general principle: concurrent heavy I/O against shared state collapses.

## How to apply

1. Before dispatching N>1 Explore agents in one message, classify each: WebFetch-only, narrow-file, broad-file-IO.
2. If 2+ are broad-file-IO on the same repo: dispatch them in separate turns (sequentially).
3. If unsure, default to sequential.
4. If you have inherited an apparently-stalled Explore agent that returned internal-error, do NOT retry the same parallel layout. Verify state of any partial outputs first (per [[feedback_internal_error_verify_before_retry]] BL-0012), then re-dispatch sequentially.

## Reach boundary

Applies to Explore subagent dispatch. The Write/Edit equivalent is `feedback_parallel_write_batch_limit.md` (max 2 parallel Writes/Edits per message). A Read tool call is independent and is not subject to this cap.
