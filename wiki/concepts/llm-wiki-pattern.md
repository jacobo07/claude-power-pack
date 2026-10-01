---
type: concept
created: 2026-09-30
updated: 2026-09-30
sources: [2026-09-30-karpathy-llm-wiki]
---

# LLM Wiki pattern

A persistent, interlinked markdown wiki that an agent writes and maintains, sitting between raw
sources and the user's questions ([[2026-09-30-karpathy-llm-wiki]]).

## Structure

- **Raw sources** — immutable evidence.
- **Wiki** — agent-owned pages: summaries, entities, concepts, comparisons, synthesis.
- **Schema** — the operating guide the agent follows; co-evolved with the user.

## Operations

- **Ingest** — read a source, integrate it across existing pages, flag contradictions, update index + log.
- **Query** — answer from the index and pages with citations; file reusable answers back.
- **Lint** — find stale claims, contradictions, orphans, missing pages and cross-links.

## Why it works

Maintenance, not reading or thinking, is what kills human wikis; an agent does it at near-zero cost
([[2026-09-30-karpathy-llm-wiki]]). Core payoff: [[compounding-vs-rederived-knowledge]].

## In this repo

This wiki is an instance; its schema is [[CLAUDE]]. Status: LIVE as of 2026-09-30 (created, one
source ingested).
