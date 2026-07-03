"""Graphify live runtime (GK-10 global store + indexer).

The architecture datasets live in vault/knowledge_base/graphify/ (SCS C69).
This package is the live implementation: a central, cross-repo knowledge
store under ~/.claude/state/graphify/ that every repo and session can query
without a restart. Node/edge extraction is delegated to tools/graphify_knowledge.py
(GK-03/04); this package adds the global layer (GK-10) and the indexer.
"""

__all__ = ["global_store", "indexer"]
