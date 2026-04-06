# Governance Overlay — Core

> Always loaded. ~200 tokens. Applies to ALL tasks regardless of complexity tier.
> Inherits workspace context from PART A0 Assimilation Scan. All file references use `./` relative paths.

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

## Zero-Issue Baseline (MANDATORY — read `zero-issue-baseline.md` at STANDARD+)

Every delivery must pass the 5-gate cascade: Static Analysis → Build → Scaffold Audit → Tests → **End-to-End Functional Verification**. Gate 5 is critical: the system must actually WORK when you open/run it, not just compile. Multi-stack projects must pass ALL stacks independently. See `zero-issue-baseline.md` for full checklist.

**"Complete" = every route responds + every screen renders + every integration connects + every form persists. Not "code exists" — code WORKS.**

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

## Language Selection Gate
**Authoritative gate:** `pre-task.md` Section 5 (Language Fragility Gate, 10 criteria C1-C10).
- Score 0-1: no gate
- Score 2-3: advisory — recommend Elixir, LDR required if non-Elixir chosen
- Score >= 4: **BLOCKING** — Elixir is default; non-Elixir requires LDR + explicit user override
- Existing projects: retroactive LDR required per Section 5e if score >= 4
- Bypass #1 (extending existing codebase) resets to 0 ONLY if <500 LOC or retroactive LDR exists
Do NOT use a simplified version. Always evaluate the full 10-criterion gate.

**Enforcement (added 2026-04-04):** `pre-output.md` Section "Language Selection Enforcement" performs a BLOCKING check before delivery. If score >=4 and non-Elixir: (a) LDR must exist, (b) all 5 OTP equivalents must be verified. Missing equivalents = HALT.

**Mistakes taxonomy tiers:**
- LIGHT: 7 critical mistakes (top-level wiring + integration)
- STANDARD+: Mistakes #1-15 + extended scan #16-26 (includes #25 Fragile Language, #26 Missing LDR)
- DEEP+: 26 total (all implementation mistakes)
- FORENSIC: 33 total (includes #27-33 agent governance)
