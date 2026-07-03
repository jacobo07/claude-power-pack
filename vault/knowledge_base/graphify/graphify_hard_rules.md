# Graphify — Hard Rules & Traps (navigation doctrine)

> Durable rules born with the Knowledge Navigation Kernel. These live with the
> system they govern (the Graphify family) and are cross-referenced from the
> project UKDL. Formal sealing into the global `HARD_RULES.md` via
> `tools/bug_to_hardrule.py` is an Owner-side step (HR-001: the generator writes
> agent-owned global config). Governed by [[graphify_12_graph_first_enforcement]].

---

## HR-GRAPH-FIRST-001 — Consult the graph before expensive exploration

- **LEVEL:** 2 (detect / redirect — **advisory, NEVER a block**). Stated honestly
  per GK-12: no in-process hook can stop a model mid-turn from choosing to grep;
  this rule makes the cheaper path *visible first*, it does not forbid the other.
- **TRIGGER:** About to begin an expensive knowledge operation — a bulk read, a
  subagent research dispatch, a deep analysis, a planner run, or a filesystem
  search (Grep / Glob / a Bash grep·find·ls) — in a repo that is indexed in the
  knowledge graph, with no preceding coordinate query or route compile.
- **ACCIÓN:** Prefer a graph lookup first —
  `python modules/graphify/indexer.py --query --name <term>` (or
  `--type hard_rule|decision|contract`). The `graph_first_gate` hook surfaces
  this advisory on PreToolUse (Bash + Read/Grep chains); it enriches context,
  it does not deny. "Navega el grafo, no explora archivos."
- **RESIDUAL (named, not closed):** a raw grep issued outside the kernel, or a
  query miss that falls through to exploration. Measured, never claimed covered.
- **ORIGEN:** GK-12 Graph-First Enforcement; the flagship paradigm of GK-00.

---

## T-GRAPHIFY-STALE-NODE-001 — A stale coordinate is a hypothesis, not truth

- **TRIGGER:** Acting on a graph coordinate whose `anchor` (the sha256 of its
  source file captured at index time) no longer matches the file on disk — i.e.
  the underlying knowledge changed after the last scan.
- **LESSON:** A stale node is a *hypothesis about* the knowledge, not the
  knowledge itself — the same discipline as "plan code is a hypothesis, verify
  the source." Before navigating to a coordinate whose anchor is stale, re-index
  (`indexer --repo <path>`, or let GK-08 session-writeback refresh it at close);
  GK-07 freshness flags the drift. Never present a stale coordinate as current.
- **RESIDUAL:** a resource created or edited *between* the last scan and the
  read — the level-2 residual GK-07 registers. Freshness is scan-time, not
  real-time; the writeback loop shrinks the window, it does not eliminate it.
- **ORIGEN:** GK-07 Freshness / Integrity / Self-Evolution.

---

*Cross-ref: project UKDL `vault/knowledge_base/ukdl-universal.md` §HARD-RULES.
Sealed alongside the live build under SCS C72 ([[graphify_live_scs_c72]]).*
