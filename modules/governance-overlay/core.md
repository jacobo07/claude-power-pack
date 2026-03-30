# Governance Overlay — Core

> Always loaded. ~200 tokens. Applies to ALL tasks regardless of complexity tier.

## Pre-Output Checklist (5 Critical Mistakes)

Before returning ANY code output, verify:

1. **Every new file has a consumer** — grep for at least one import/require. No orphan files.
2. **Every new function is called somewhere** — exported functions must have a call site in the same session.
3. **Save/persist calls exist in completion paths** — if data is created or modified, Save() must be in the completion path.
4. **No hardcoded localhost for remote targets** — if code will run remotely, connection strings must use env vars or config.
5. **No assumptions — verify before patching** — read the file before editing. Check the function exists before calling it.

## Quality Gate (run if project has the tool)

| Stack | Command | Pass Criteria |
|-------|---------|---------------|
| TypeScript | `npx tsc --noEmit` | 0 errors |
| Python | `python -m py_compile <file>` or `mypy --strict` | 0 errors |
| Lint | Project-specific linter | 0 errors |
| Tests | `npm test` / `pytest` | All pass |

**If ANY gate fails → fix before claiming completion. No exceptions.**

## Completion Claim Rule

The words "done", "complete", "ready", "fixed", "passing" require evidence from running the verification commands above. "Should work" or "looks correct" are not evidence.

## Tier Upgrade Signal

If during a LIGHT task you discover:
- 3+ files need modification → upgrade to STANDARD
- Cross-module dependencies → upgrade to DEEP
- Production risk or prior failures → upgrade to FORENSIC

On upgrade, load the additional governance modules for that tier.
