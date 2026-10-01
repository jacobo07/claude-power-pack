---
type: concept
created: 2026-09-30
updated: 2026-09-30
sources: [2026-09-30-karpathy-llm-wiki]
---

# Compounding vs re-derived knowledge

- **Re-derived**: each question rebuilds the answer from raw material (typical RAG, file upload).
  Nothing accumulates; a subtle cross-document question costs the full search every time
  ([[2026-09-30-karpathy-llm-wiki]]).
- **Compounding**: synthesis is compiled once and kept current; cross-references and flagged
  contradictions already exist when the next question arrives ([[2026-09-30-karpathy-llm-wiki]]).

## Test for any knowledge store

Interpretation: a store compounds only if all three hold —
1. it is **written** when knowledge is produced,
2. it is **read** when the knowledge is needed,
3. it is **kept current** when newer evidence arrives.

A store that is written but never read is an archive, not compounding knowledge.

## Relevance to PP

Open question tracked in [[measure-knowledge-store-consultation]]. See also [[llm-wiki-pattern]].
