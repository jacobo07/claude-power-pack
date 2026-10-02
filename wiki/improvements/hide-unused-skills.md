---
type: improvement
created: 2026-10-02
updated: 2026-10-02
sources: [2026-10-02-token-economy-external-research-2]
status: IDEA
effort: S
graduated_to:
---

# Hide the skills nobody invokes from the per-call listing

## Problem (measured, 7 d, main + subagents)

319 distinct skills were listed; 39 were invoked (336 invocations, `kclear` 113, `gsd-plan-phase`
28, `cpp-gsd-long` 27, `ultra` 25); **280 were never invoked**
(`wiki/tools/token_economy_coldstart.2026-10-02.out` [K]). The listing is part of every call's
prefix (measured 6.5k tok in a neutral cwd; ~9.4k in a session listing 276 skills), and changes to
it are re-injected mid-session as deltas (875 times, median 5.4k chars;
`token_economy_listings.2026-10-02.out`).

## Mechanism (documented)

`skillOverrides` in settings.json: `"name-only"` keeps the name in the listing and drops the
description; `"user-invocable-only"` hides it from the model; frontmatter
`disable-model-invocation: true` does the same per skill. `/skill-doctor` reports per-skill
context cost and invocation frequency ([[2026-10-02-token-economy-external-research-2]]).

## Bound

≈ -5k tokens per call ≈ 1.5-2 % of est. spend (scaled from the floor bound in
[[token-economy-levers]]), plus fewer mid-session deltas.

## Risk

Skills that should auto-trigger but rarely do would trigger even less (moved rules already
auto-invoke 0/8). Mitigation: `name-only`, not `off`, and exclude every skill named in an
activation-criteria table of a CLAUDE.md.

## Proposed steps

1. Build the keep-list: the 39 invoked + every skill an activation table names.
2. Owner applies `skillOverrides` (settings.json is Owner-side per HR-001).
3. Re-run `_coldstart` [K] and a floor probe after a week.
