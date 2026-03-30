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

## Quality Gates (Run ALL That Apply)

Execute the applicable commands and verify output:

```
TypeScript:  npx tsc --noEmit          → 0 errors
Python:      mypy --strict / ruff check → 0 errors
Lint:        project linter             → 0 errors
Tests:       npm test / pytest          → all pass
Build:       project build command      → passes
Schema:      prisma validate / etc      → valid
```

**Evidence required.** Run the command. Read the output. THEN claim the result. "Should pass" is not evidence.
