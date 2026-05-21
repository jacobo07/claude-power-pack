---
name: hook-fanout-systemic-cost
description: PreToolUse hook fan-out (7-15 hooks per tool call) is the systemic cost behind transversal [Tool result missing due to internal error] hangs. Consolidating absorbable hooks into hook-dispatcher.js eliminates 5-7 spawns per tool without removing any check.
metadata:
  type: feedback
related:
  - parallel-batch-large-output-cascade.md
  - parallel-explore-cascade.md
  - feedback_parallel_write_batch_limit.md
---

## Architectural finding

`~/.claude/settings.json` (audited 2026-05-21) registers:

| Event | Hook entries | Per-tool spawns (worst case) | Max blocking budget |
|---|---|---|---|
| PreToolUse | 15 hooks across various matchers | 7-10 per Write, 3 per Read, 8+ per Bash | ~140 s per Write |
| UserPromptSubmit | 4 hooks | 4 per submit | ~40 s |
| PostToolUse | 4 hooks | 2-4 per tool | ~120 s |
| Stop | 3 hooks (one with 11-hook chain) | 13 per Stop | ~600 s |
| SessionStart | 7 hooks | 7 per session start | ~30 s |

Each per-matcher hook is a SEPARATE settings.json entry → SEPARATE Node subprocess spawn. The dispatcher pattern (`~/.claude/hooks/hook-dispatcher.js`) already exists and handles `PreToolUse-default`, `PostToolUse-default`, `Stop-chain` — but the 14 per-matcher hooks alongside it remain separate spawns.

## Why this matters

The Owner reports `[Tool result missing due to internal error]` happening transversally across every repo. Empirical RCA traces it to two compounding causes:

1. **N spawn overhead per tool**: Node startup + stdin parse + logic + exit = ~50-150 ms each. Sequential. A single Write today pays 9-10× that = up to ~1.5 s of pure hook chain overhead BEFORE the tool runs.
2. **Large hook outputs crowd the harness pipe**: `gatekeeper-semantic.js` injects ~40 KB of ExecutionOS doctrine into `additionalContext` on every Read (verified 2026-05-21: the harness wrote it to an overflow file because it exceeded the inline cap). Combined with the per-tool fan-out, parallel batches collapse — sibling tool results return `internal-error`.

Both causes have the same fix: consolidate.

## Rule

When designing or extending PP hook stack:

1. **Default to absorbing new logic into `hook-dispatcher.js`** unless the new check has a genuine isolation requirement (heavy LLM-style scan, separate stdout discipline, must survive dispatcher state corruption).
2. **Hooks that ARE absorbable** (verified case-by-case): secret-scanner, quality-gate, readonly-prompts-guard, skill-heat-map-advisor, zero-fiction-gate, gatekeeper-semantic, anti-thrash.
3. **Hooks that should stay separate**: jobs-woz-gatekeeper, process-sandbox, ovo-push-gate, quality-skill-gate, rtk-rewrite, lazarus-livesnap, scaffold-auditor.
4. **Never inject >4 KB into `additionalContext` per tool call.** If the doctrine is needed, name the file path; the agent has Read.
5. **Each hook's timeout must be justifiable individually.** A 20 s timeout on a 10 ms regex scan is wrong; tighten to 2-3 s.

## How to apply

- When proposing a new PreToolUse hook: ask "can this be a function call inside dispatcher?" first.
- When reviewing the existing stack: target the highest-fan-out paths (Write fires 9+ hooks, that's where consolidation pays most).
- Measure before/after: `vault/audits/hook-fanout-before-after-<ts>.json` is the empirical artifact. The Zero-Command plan T1.5 done-gate produces this.
- Reversibility is preserved: absorbed hooks keep their .js file on disk during a deprecation window; reverting is one `settings_merger.py register-pretool <hook>` call.

## Why fix it instead of working around it

Working around hook fanout (sequentialize tool calls, smaller batches per `parallel-batch-large-output-cascade`) is correct lesson-level mitigation but does NOT eliminate the underlying cost: every session of every repo pays the spawn overhead. Consolidation fixes it once for all sessions across all projects.

This is the architectural why behind the Zero-Command plan's Component E. The plan's other components (A/B/C/D) ADD hooks (auto-bootstrap, background verifier, etc.); stacking them on the current bloated chain without E would make hangs worse, not better. Hence the plan's "consolidate first, then layer" order.

## Reach boundary

Applies to PP-managed hooks in `~/.claude/settings.json`. Does NOT apply to plugin-provided hooks (those have their own registration paths and consolidation would break plugin contracts). The dispatcher absorbs only hooks whose source is owned by the PP repo.
