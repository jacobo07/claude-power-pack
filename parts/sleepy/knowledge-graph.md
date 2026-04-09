# Knowledge Graph Navigation (Part KG)

When `_knowledge_graph/INDEX.md` exists in the project root, use the Knowledge Graph for architecture discovery instead of raw grep/glob scanning.

## Navigation Protocol

1. **Read INDEX.md first** — it contains the full module/class/function map with wikilinks (~400-500 tokens).
2. **Follow [[wikilinks]]** to drill into specific nodes. Each node is ~150-300 tokens.
3. **Max 10 nodes per task** — read only what is relevant. Never load the entire vault.
4. **Hot Spots section** in INDEX.md lists the most-connected nodes — start there for architecture questions.
5. **Architecture views** in `_knowledge_graph/architecture/`:
   - `DEPENDENCY_GRAPH.md` — who imports whom
   - `CLASS_HIERARCHY.md` — inheritance trees
   - `ENTRY_POINTS.md` — main() and CLI handlers
   - `BUSINESS_RULES.md` — extracted constraints and invariants

## When to Fall Back to Raw Code

- The graph is stale (check `_knowledge_graph/_meta/graph_meta.json` → `generated_at`)
- You need to read actual implementation logic (the graph has signatures and summaries, not full code)
- The file you need was created after the last graph generation

## Sync Command

Run `/cpp-obsidian-setup` to regenerate or sync the vault. Sync mode only re-parses changed files.
