# Governance Overlay — Core

> Always loaded. ~200 tokens. Applies to ALL tasks regardless of complexity tier.

## Pre-Output Checklist (7 Critical Mistakes)

Before returning ANY code output, verify:

1. **Every new file has a consumer** — grep for at least one import/require. No orphan files.
2. **Every new function is called somewhere** — exported functions must have a call site in the same session.
3. **Save/persist calls exist in completion paths** — if data is created or modified, Save() must be in the completion path.
4. **No hardcoded localhost for remote targets** — if code will run remotely, connection strings must use env vars or config.
5. **No assumptions — verify before patching** — read the file before editing. Check the function exists before calling it.
6. **No scaffold illusions** — every module is WIRED (active in startup/supervision, not commented out), has DEFENSIVE DEFAULTS (timeouts, retries, error handlers), and is tested for FAILURE cases (not just happy path). Compiles != works.
7. **Integration before unit** — at least 1 test exercises the full path (input → process → output) before claiming completion. A system of passing units with no integration test is not verified.
8. **Return type contracts verified** — for every `case Module.func() do` pattern, the matched atoms/tuples must exist in the callee's actual return values. Read the callee's source, don't assume.
9. **Remote deploy integrity** — after SCP/heredoc deploy, read back the file and verify no shell escaping corruption (especially `\`, `$`, quotes in regex patterns).
10. **Zero-issue gate passed** — compile (0 errors, 0 warnings), tests (all pass), scaffold audit (0 CRITICAL). The `zero-issue-gate.js` hook enforces this automatically on every session end. If it blocked you, fix the issue before responding.

## Quality Gate (run if project has the tool)

| Stack | Command | Pass Criteria |
|-------|---------|---------------|
| TypeScript | `npx tsc --noEmit` | 0 errors |
| Python | `python -m py_compile <file>` or `mypy --strict` | 0 errors |
| Lint | Project-specific linter | 0 errors |
| Tests | `npm test` / `pytest` | All pass |
| Runtime (DEEP+) | `python modules/omnicapture/query_telemetry.py --project <X> --summary` | 0 CRITICAL/FATAL |

**If ANY gate fails → fix before claiming completion. No exceptions.**

## Completion Claim Rule

The words "done", "complete", "ready", "fixed", "passing" require evidence from running the verification commands above. "Should work" or "looks correct" are not evidence.

## Tier Upgrade Signal

If during a LIGHT task you discover:
- 3+ files need modification → upgrade to STANDARD
- Cross-module dependencies → upgrade to DEEP
- Production risk or prior failures → upgrade to FORENSIC

On upgrade, load the additional governance modules for that tier.

## Language Selection Gate (added 2026-03-30)
When starting a NEW backend project (not extending existing), evaluate:
- If requires: 5+ workers + real-time WebSocket + fault tolerance + no ML -> RECOMMEND Elixir
- If requires: ML/data science + rapid prototyping + existing Python -> RECOMMEND Python
- Document decision in governance/ARCHITECTURE_DECISIONS.md
- Does NOT apply when extending existing projects
