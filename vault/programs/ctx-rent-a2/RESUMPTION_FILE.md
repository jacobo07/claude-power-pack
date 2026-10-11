# RESUMPTION_FILE: ctx-rent-a2

**Identity.** Claude Power Pack, `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`
(another writer is active: pathspec-scoped commits only). Goal `ctx-rent-a2`, cap 14,000,000 (Owner "y go p95",
2026-10-11). Plan: `vault/plans/context-rent-a2-2026-10-11.md` (read sections 1, 4, 5 only). Thesis: per-call provider
input must scale with the boundary's working set, not the session; the host re-sends the epoch, so eviction happens
only through rotation, compiled carrier subagents, or zero-model paths.

**State (coherence anchor: HEAD contains 6f5840a3 "plan(ctx-rent-a2)").**
- Measured baseline: fresh floor 122,093 (32,664 host-cached + 89,427 CPP session floor); 28a5bd61 ran 139,327 ->
  247,022 over 47 calls (9.54M). Always-loaded files 142,354 bytes (~39.5K tokens).
- Slice A SEALED 4de21ba8: `tools/context_floor_census.py <sid...>` (gate `tools/test_context_floor_census.py` 23/23);
  ranked table in plan section 1.1. CPP files = 139.8K chars (61 % of attributed floor): global CLAUDE.md 39.8K,
  PP CLAUDE.md 39.0K, rules 38.0K (18 moved-to-skill stubs = 16.2K), MEMORY.md 17.1K, ~/CLAUDE.md 6.0K. Host
  listings 57.5K (25 %). Session-specific unattributed bracket +28K / -3K. Hooks timed out before call 1.
- econ-succession is paused before S1; its own file is
  `vault/programs/econ-succession/RESUMPTION_FILE.md` (do not read it until slice H).
- Held mission m-4d1b851262ff (ctx-same-pane) to be retired; its S0 commit 018230b9 (branch ctx/same-pane) to be merged in C/D.

**Active decisions.** EXECUTION mode only; no GSD plan-phase; at most 2 subagents; order A -> B -> H -> C+F -> I ->
D+E+G -> J -> K -> L. Never raise the 150K canary; budget = channel floor + packet. Rotate (/kclear) at every sealed slice.
Bind each new session: write `~/.claude/state/goal-binding/<sid>.json` with goal ctx-rent-a2 before working.

**Next 3 actions.**
1. Slice B, CPP files only (listings need settings = Owner): back up each file to `~/.claude/backups/rules-<ts>/`,
   then (a) collapse the 18 moved-to-skill rule stubs into ONE index file (one line each: name + load-when), (b) move
   hook-enforced prose out of ~/.claude/CLAUDE.md (Windows bridge, closer-guard amendments) and the PP CLAUDE.md
   inline HARD RULES mirror to linked files, keeping each rule's one-line trigger, (c) compact MEMORY.md. Revert line per move.
2. Re-measure: new session call-1 floor via `tools/context_floor_census.py <new sid>`; record the delta in plan 1.1.
3. Slice H (econ-succession S1 canary) on the reduced floor.

**Start.** Bind your session, then do action 1.
