---
name: generate-docs
description: Retroactively generate the four ADS docs (PRD, Architecture Spec, Constitution, Changelog) for every module in the active repo that does not yet have them. Manual counterpart to the automatic Stop-hook ADS sync — use it to seed docs for an existing codebase. Read-only walk; NEVER stages or commits; writes only to docs/{prd,arch,constitution,changelog}/<slug>.md in the current repo. A docs/.ads-disabled file turns ADS off for the repo.
---

# /generate-docs — ADS retroactive backfill

Walks the active repo, finds modules (package dirs with an `__init__.py` /
`index.{js,ts}` / `mod.rs`, plus standalone source files over 80 LOC that
expose a public symbol), and generates the four ADS documents for any that
lack them. Modules already documented are skipped.

The Stop-hook runner (`tools/ads_sync.py`) keeps docs current as you change
code; `/generate-docs` is the one-time seed for code that predates ADS.

## Preview (no writes)

```
python tools/ads_backfill.py --repo . --dry-run
```

Lists the modules that WOULD get docs. Review this first.

## Generate

```
python tools/ads_backfill.py --repo .
```

## Output

For each module: `docs/prd/<slug>.md`, `docs/arch/<slug>.md`,
`docs/constitution/<slug>.md`, `docs/changelog/<slug>.md`. Each file has an
`<!-- ADS:AUTO -->` block (code-derived, refreshed automatically on change)
and an `<!-- ADS:OWNER -->` block (yours to fill — ADS never touches it).

Notes:
- Never commits. Inspect with `git status` and stage what you want.
- Slug = the module's repo-relative path with `/` → `__` (collision-free).
- To opt a repo out entirely: `touch docs/.ads-disabled`.
