# RESUMPTION_FILE: ctx-rent-a2

**Identity.** Claude Power Pack, `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`
(another writer is active: pathspec-scoped commits only). Goal `ctx-rent-a2`, cap 14,000,000 (Owner "y go p95",
2026-10-11). Plan: `vault/plans/context-rent-a2-2026-10-11.md` (read sections 1, 4, 5 only). Thesis: per-call provider
input must scale with the boundary's working set, not the session; the host re-sends the epoch, so eviction happens
only through rotation, compiled carrier subagents, or zero-model paths.

**State (coherence anchor: HEAD contains 6f5840a3 "plan(ctx-rent-a2)").**
- Measured baseline: fresh floor 122,093 (32,664 host-cached + 89,427 CPP session floor); 28a5bd61 ran 139,327 ->
  247,022 over 47 calls (9.54M). Always-loaded files 142,354 bytes (~39.5K tokens).
- Nothing implemented yet. econ-succession is paused before S1; its own file is
  `vault/programs/econ-succession/RESUMPTION_FILE.md` (do not read it until slice H).
- Held mission m-4d1b851262ff (ctx-same-pane) to be retired; its S0 commit 018230b9 (branch ctx/same-pane) to be merged in C/D.

**Active decisions.** EXECUTION mode only; no GSD plan-phase; at most 2 subagents; order A -> B -> H -> C+F -> I ->
D+E+G -> J -> K -> L. Never raise the 150K canary; budget = channel floor + packet. Rotate (/kclear) at every sealed slice.
Bind each new session: write `~/.claude/state/goal-binding/<sid>.json` with goal ctx-rent-a2 before working.

**Next 3 actions.**
1. Slice A: write `tools/context_floor_census.py` (deterministic, read-only): per-source token estimate of the call-1
   floor (instruction files, skill/agent listings, each SessionStart/UserPromptSubmit hook's injected text, measured by
   running the hook or reading its output) + per-call history charge by tool_result producer from a transcript.
   Test first in `tools/test_context_floor_census.py`. Commit.
2. Run it on 47f3da08 and 28a5bd61; write the ranked table into plan section 1; commit.
3. Slice B: pick the top hook-enforced or duplicated blocks; back up, move to skill cards, re-measure call-1 floor.

**Start.** Bind your session, then do action 1.
