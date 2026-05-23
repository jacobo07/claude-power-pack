---
description: Instant FTS5-ranked UI design-pattern lookup across 10 real design systems. Usage: /cpp-design <query>
---

# /cpp-design — Design Pattern Retrieval

Arguments: $ARGUMENTS

## Behavior

1. If `$ARGUMENTS` is empty, ask the Owner what UI pattern / problem they
   need (e.g. `modal`, `empty state`, `command palette`) and STOP.
2. Run the FTS5 index:
   `python ~/.claude/skills/claude-power-pack/tools/design_index.py --search "$ARGUMENTS" --limit 8`
3. If the table is empty on first use, `design_index.py` self-builds the
   baked dataset, then searches — no manual `--build` needed.
4. Present the ranked hits verbatim: each shows pattern, use-case, the
   established implementation technique, and the system's canonical docs
   URL. Use these to ground any UI you then generate.

## Contract

- BM25-ranked over an ISOLATED `design_tools_fts` table — it never reads
  or mutates the conversation `turns_fts` index.
- DONE gate (Q6 #2): a real query returns **≥3 ranked results in
  <250 ms**; `design_index.py` exits non-zero if either bound is missed.
- Dataset = 10 real design systems × 15 real UI patterns (150 rows).
  `source_url` is each system's real canonical docs root; snippets are
  established, system-agnostic techniques — no fabricated entries.
- Updates are opt-in: `design_index.py --refresh` applies
  `modules/karimo-harness/refresh_sources.json` `manual_entries`. The
  baked dataset stays canonical and network-immune (Q1: hybrid).

## Examples

- `/cpp-design modal` → Dialog/Modal patterns across shadcn, Radix, ARIA…
- `/cpp-design keyboard navigation` → Command Palette, Tabs, Data Table…
- `/cpp-design perceived performance` → Skeleton Loader, Infinite Scroll…
