# SCS C72 — Graphify Knowledge Navigation Kernel — LIVE BUILD — SEALED

> The **architecture** of the Graphify Intelligence Kernel was sealed under
> **SCS C71** (13 datasets, GK-00..GK-12). **This** seal, **SCS C72**, covers the
> **live implementation** — the running code that makes the kernel navigate, not
> just describe. C71 is the map; C72 is the territory.

---

## What is sealed (the live surface)

| Sprint | Artifact | Role |
|---|---|---|
| 1 | `tools/graphify_knowledge.py` + `kobi_graphify.py --knowledge` | GK-03/04 knowledge-node + typed-edge grapher; extends the existing code grapher, does not reimplement it |
| 2 | `modules/graphify/global_store.py` | GK-10 central cross-repo store (`~/.claude/state/graphify/`); signal-gated promotion, union-with-provenance merge (HR-006) |
| 2 | `modules/graphify/indexer.py` | active-repo discovery from `terminal_slots.json` + standalone runner |
| 3 | `hooks/graph_first_gate.js` | GK-12 Graph-First advisory (level-2, never blocks), wired into the Bash + Read/Grep PreToolUse chains |
| 5 | `modules/graphify/session_writeback.py` | GK-08 writeback Stop hook — re-indexes the repo at session close, bounded + fail-open |
| 5 | `tests/test_graphify_live.py` | 3 hermetic V-gates (classify / promotion / writeback-loop) |
| 5 | `graphify_hard_rules.md` | HR-GRAPH-FIRST-001 + T-GRAPHIFY-STALE-NODE-001 |

Commits: `2d80b27` (Sprint 1), `7ef61ab` (Sprint 2), `0b2a837` (Sprint 3),
this commit (Sprint 5). SCS C69→C71 collision fix: `4d7f727` (concurrent pane).

## Done-gate (observed evidence)

- **Cross-repo query** spans **6 repos**; `ukdl-universal` merged from 3 origins,
  `HR-001..006` from 2 — union-with-provenance proven, no directional overwrite.
- **Promotion discipline**: global_nodes **8069 → 232** after the signal gate;
  GEO-audit promotion **7516 → 76** of 8312 nodes (selective, not a flood).
- **`test_graphify_live.py`**: `GRAPHIFY_LIVE_PASS=3/3`, exit 0, on two
  consecutive hermetic runs (re-run-safe, no global writes).
- **`graph_first_gate`**: runtime-verified — advisory fires for Grep / Bash-search
  citing real counts (688 repo + 232 cross-repo), silent for git/Edit/Read,
  throttle + fail-open confirmed; `node --check` clean.

## Activation — CONFIRMED 2026-07-03

The Owner synced `~/.claude/hooks/hook-dispatcher.js` from canonical. Verified
live, observed evidence (not assumption):
- **graph_first_gate fires and REACHES THE MODEL** — a Grep PreToolUse through the
  live Read-chain returns the advisory in `hookSpecificOutput.additionalContext`.
- **session_writeback advances the store** — a Stop event re-indexed PP (695
  nodes), `graphify_global.json` `updated_at` advanced, `writeback.log` receipt written.
- **test_graphify_live** 3/3, dispatcher `node --check` clean, canonical↔live IN SYNC.

**Bug fixed en route (`026573e`):** the dispatcher's `sanitizeForSchema` dropped
`additionalContext` for the PreToolUse family while `mergeOutputs` added it — an
internal contradiction that had silently muted EVERY PreToolUse context-injector
(not just GK-12). PreToolUse `additionalContext` is a first-class field (official
hooks docs, verified). Kept in the PreToolUse branch. Re-sync was required after
the fix — the drift recurs on any canonical dispatcher change (T-HOOK-DISPATCHER-DRIFT-001).

## Honest residuals (level-2, per GK-12 — named, not closed)

- **Re-sync on every canonical dispatcher change (HR-001).** The agent cannot
  write `~/.claude/hooks/`; each new hook wired into canonical stays inert until
  an Owner `Copy-Item` canonical→live. Runbook + drift trap capture the ritual.
- **Librarian swarm (GK-11 / Sprint 4) deferred** — Owner-side `~/.claude/agents/`
  registration; datasets designed, live agents not yet dispatched.
- **Big-repo writeback defers** (> 4000 md files) to the scheduled `indexer --all`
  — a bounded, logged residual, not a silent skip.
- **Glob + Task matchers** are an optional future `settings.json` extension; today
  the gate covers Grep (Read chain) + Bash-search.

*Live build sealed under **SCS C72**. Architecture: [[graphify_live_scs_c72|C71]].
Parent conscience: [[graphify_12_graph_first_enforcement]] (CO-10 ladder).*

---

## Addendum — GK-11 Librarian agents shipped (2026-07-05)

The GK-11 residual above ("Librarian swarm deferred — Owner-side `~/.claude/agents/`
registration") is now closed on the PP-internal side. Three librarian agent files were
created — canonical source under `vault/agents/` (version-controlled), copied to the live
`~/.claude/agents/`:

- **`graphify-librarian.md`** — GK-11 locate-not-reason finder; navigates the coordinate graph
  (`indexer --query`) and returns a compressed route with an explicit confidence label; also runs
  the freshness/integrity pass. Cheap model (sonnet, HR-COST-001).
- **`graphify-route-governor.md`** — GK-11 Route Governor; arbitrates competing librarian
  proposals into one minimal route and audits GK-06 route quality; proposes optimizations, never
  auto-applies.
- **`graphify-writeback.md`** — GK-08 deep writeback; complements the automatic
  `session_writeback.py` Stop hook with on-demand extraction of edges / decisions /
  negative-knowledge, verified before promotion.

All three ground on real invocations (`python -m modules.graphify.indexer`, `session_writeback`,
`tools/kobi_graphify.py` / `graphify_knowledge.py`), carry valid frontmatter (name / description /
tools / model / color), and contain zero placeholders (slop-scanned clean).

**Honest residual (cold-load, `[[PR-AGENT-FILES-IN-REPO-001]]`):** agent files cold-load like
hooks — the three are on disk in `~/.claude/agents/` but become dispatchable only after a
`/restart`. The canonical copy is `vault/agents/`; the live copy is what Claude dispatches — keep
both in sync (Copy-Item on any change; same drift discipline as the dispatcher,
`[[T-HOOK-DISPATCHER-DRIFT-001]]`).

With GK-11 agents shipped, the **Graphify Knowledge Navigation Kernel (GK-00..GK-12) is completely
built** — architecture (C71) + live code (C72) + the librarian agent family.
