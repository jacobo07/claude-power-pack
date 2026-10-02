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

~~≈ -5k tokens per call ≈ 1.5-2 %~~ **Corrected 2026-10-03: ≈ -1.2k tokens per call (~0.4 %).**
The live listing is already capped at its budget (30,000 chars, 269 entries in this repo) and the
harness already drops the least-used descriptions; the proposal removes 4,541 chars
(`wiki/tools/skill_listing_savings.2026-10-03.out`). The main gain is quality: the skills actually
used keep full descriptions inside the budget. Plus fewer mid-session listing deltas.

## Keep-list built (2026-10-03, Owner "yes")

`wiki/tools/skill_keep_list.py` over 30 d (2,689 transcripts; `skill_keep_list.2026-10-03.out`):
352 skills listed, 50 invoked (572 invocations). **KEEP 210, propose `name-only` for 142.**
- KEEP if invoked in 30 d, OR named in an always-loaded CLAUDE.md or `~/.claude/rules/**`
  (covers the moved-rule skills), OR a plugin skill, OR not under `~/.claude` (bundled harness
  skills such as `artifact-design`, and other repos' project skills, are left alone).
- Plugin skills cannot be overridden: claude.exe 2.1.288 returns "on" when `source==="plugin"`.
- Accepted values confirmed in the binary: "Per-skill listing overrides keyed by skill name.
  "name-only" lists the skill without its description; "user-invocable-only" hides it from the
  model but keeps /name; "off" hides it from both. Absent = on."
- Proposed settings fragment: `wiki/tools/skill_overrides.proposed.json` (142 entries, all
  `name-only`; every `/name` keeps working).
- Owner review points: the `kobiicraft-*` pack (domain skills that might auto-trigger in the
  KobiiCraft repo, zero invocations in 30 d) and the `gsd-*` commands typed by hand.

## Risk

Skills that should auto-trigger but rarely do would trigger even less (moved rules already
auto-invoke 0/8). Mitigation: `name-only`, not `off`, and exclude every skill named in an
activation-criteria table of a CLAUDE.md.

## Proposed steps

1. Build the keep-list: the 39 invoked + every skill an activation table names.
2. Owner applies `skillOverrides` (settings.json is Owner-side per HR-001).
3. Re-run `_coldstart` [K] and a floor probe after a week.
