# Governance Overlay — Pre-Output Gate

> Loaded for STANDARD, DEEP, and FORENSIC tiers. ~150 tokens. Final gate before returning code.

## Full 15-Mistake Scan

Before claiming ANY work is complete, verify each item:

| # | Mistake | Check |
|---|---------|-------|
| 1 | Building Without Wiring | Every new file has ≥1 import somewhere |
| 2 | Detail Without Integration | New utilities are called in the same session |
| 3 | Data Without Save Triggers | Save() exists in every completion path |
| 4 | Events Without Sources | Every listener has a corresponding emitter |
| 5 | Config Without Consumers | Every config getter has a reader |
| 6 | File Exists ≠ Works | Consumer + observable output verified |
| 7 | Upgrade Without Replacement | Wired into existing call chain, old refs updated |
| 8 | Constants Drift | Ratios verified after geometry/layout changes |
| 9 | Deprecated Patterns | Used existing utilities, didn't rebuild |
| 10 | Report Gaps Instead of Fixing | Fixed issues in the same pass, didn't just note them |
| 11 | Remote != Localhost | No hardcoded localhost for remote targets |
| 12 | Approximating Instead of Implementing | Solved the actual hard problem |
| 13 | Assumptions Without Verification | Read files before editing, verified existence |
| 14 | Analyzing Callee Without Caller | Traced full call chain upward |
| 15 | Static Display of Dynamic Data | Counters track real state, not initial totals |
| 27 | Agent Without Kill Switch | Every agent loop has max_iterations + breaker + cost_limit |
| 28 | Unbounded Tool Access | allowed_tools explicitly defined, no open shell access |
| 29 | Trust Without Verification | Agent-to-agent calls authenticated |
| 30 | Privilege Escalation via Tool Chain | No transitive escalation paths |
| 31 | SLO-Blind Deployment | SLOs defined before agent deployment |
| 32 | Unsigned Plugin | Agent plugin signatures verified |
| 33 | Stateful Without Saga | Multi-step workflows have rollback |

## Quality Gates (Run ALL That Apply)

Execute the applicable commands and verify output:

```
TypeScript:  npx tsc --noEmit          → 0 errors
Python:      mypy --strict / ruff check → 0 errors
Lint:        project linter             → 0 errors
Tests:       npm test / pytest          → all pass
Build:       project build command      → passes
Schema:      prisma validate / etc      → valid
Agent:       agt audit owasp-asi <dir>  → 0 CRITICAL (if agent system)
Agent Policy: agt policy validate <file> → valid (if agent system)
```

**Evidence required.** Run the command. Read the output. THEN claim the result. "Should pass" is not evidence.

## End-to-End Functional Verification (Gate 5 — MANDATORY)

After compile/build/test gates pass, verify the system WORKS:

| Project Type | Verification |
|-------------|-------------|
| Web app | Start dev server → hit main route → HTTP 200 → hit API endpoints → DB data returns |
| Multi-stack | EACH stack passes Gates 1-4 independently → integrated system verified end-to-end |
| Library | Import → call primary function → confirm expected output |
| CLI | Run `--help` → run primary command → confirm behavior |
| Backend | Boot → health endpoint 200 → primary endpoint returns data |

**Cannot verify end-to-end?** Document what was verified and what wasn't. Never use kill-switch words for unverified functionality.

### Completeness Checklist (ALL must be true before claiming "done")
- [ ] Every route/endpoint responds (not 404/500)
- [ ] Every UI screen renders without console errors
- [ ] Every form submits and result persists
- [ ] Every integration connects and returns data
- [ ] No TODO/placeholder in user-visible UI
- [ ] Mobile responsive at 375px (if web)

## Language Decision Verification

If this task involved writing new backend/infrastructure code:

| Check | Verify |
|-------|--------|
| Fragility score computed? | Score was calculated in pre-task gate |
| If score >= 2, LDR exists? | Language Decision Record was created or Elixir was chosen |
| If non-Elixir chosen, OTP equivalents listed? | Checklist of manually-needed patterns exists |
| If non-Elixir chosen, equivalents implemented? | Supervision, circuit breakers, shutdown handlers present in code |

If OTP equivalents were listed but NOT implemented, flag as incomplete.
