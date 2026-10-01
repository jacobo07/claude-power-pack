---
type: source
created: 2026-09-30
updated: 2026-09-30
sources: [2026-09-30-karpathy-llm-wiki]
raw: raw/2026-09-30-karpathy-llm-wiki.md
kind: gist
origin: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
---

# Karpathy — LLM Wiki (gist)

Idea file describing a pattern: an agent builds and maintains a persistent markdown wiki between raw
sources and the user's questions. Deliberately abstract; the specifics are left to user + agent.
This wiki is an instance of it — see [[llm-wiki-pattern]].

## Key points

- RAG-style use re-derives knowledge on every question; "There's no accumulation." → [[compounding-vs-rederived-knowledge]]
- Three layers: immutable raw sources, agent-owned wiki, schema file (e.g. CLAUDE.md) co-evolved with the user.
- Three operations: ingest (one source may touch 10-15 pages), query (good answers filed back as pages), lint.
- `index.md` (content catalog, read first on queries) + `log.md` (append-only, greppable `## [date] op | title`).
- Index alone works to ~100 sources / hundreds of pages; beyond that, local search (e.g. qmd).
- Humans abandon wikis because upkeep grows faster than value; an agent makes upkeep near-free.
- Tips: Obsidian as the reader ("Obsidian is the IDE; the LLM is the programmer"), images downloaded
  locally, YAML frontmatter + Dataview, git for history.

## What it implies for PP

Interpretation: PP already has many knowledge stores; the pattern's question for PP is not "do we
store knowledge" but "does it compound — is it read back and kept current". Tracked as
[[measure-knowledge-store-consultation]].

## Disagreements

None yet (first source).
