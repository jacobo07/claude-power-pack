# UWCP Assimilation -- resumption contract

**Read first; self-contained.** Plan: `vault/specs/uwcp-assimilation.md` (APPROVED 2026-09-25, Q1-Q6
as recommended + Owner addition "reconstruct everything we can't include"). Amendments for the UWCP
pane: `vault/specs/uwcp.AMENDMENTS.md`. Knowledge: `vault/knowledge_base/uwcp_assimilation/`.

## Identity
Repo `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`. Lane R
(this program) writes only NEW files outside `modules/gsd_x/goal`; Lane L (the UWCP pane) owns
`modules/gsd_x/goal` and executes A1-A8, X0, X3, X4 from AMENDMENTS.md. Live panes and ~490 foreign
dirty paths: pathspec commits, re-read HEAD, check hunk headers. `ukdl-universal.md` carries another
writer's hunks -- do not commit it by pathspec.

## Sealed (Lane R, all pathspec commits)
c639661 plan+amendments · b8cf2ae R1 withdrawn (workspace.py owns capsules) · 0a90bf4 X1 research
record · acea1f6 R2 lease (21/21, 14 mutants) · 141df71 R3 history_check (16/16, 13) · 7f8412a R5
trace_context (11/11, 9) · a486bf8 X2 TLA+ model (15/15; jar dev-only, sha256-pinned) · 3be5780 A2f ·
13c66b0 R4 provider_routing (33/33, 17) · 7b25803 R6 inference_bench (13/13, 9) · cf34451 X6
evidence class (9/9, 4) · a8b61c6 X5 corpus (7/7, 28 entries) · ca60f38 liveness PLANNED ·
f451a64 UKDL. Coherence anchor: `python tools/test_uwcp_tla.py` -> TLA_PASS=15/15.

## Open (owed, with owner)
- Lane L: every OWED row in the corpus; replay the TLC counterexamples as failing Python tests
  first (S1-8c FalseLost, A2f Expire).
- REMOTE_REALITY: GEX44 pause drill via a dispatcher signal verb (A3, PLAN checkpoint); R6 run
  against llama-server on GEX44 via the dispatcher (S6a); real claude/codex exit codes on quota text.
- Owner: X8 ratchet promotion after UWCP Golden 01.

## Next 3 actions
1. Owner points the UWCP pane at `vault/specs/uwcp.AMENDMENTS.md` (Q1).
2. On each Lane L commit that touches a corpus row: flip it OWED -> REGRESSION (the corpus gate
   refuses a regression naming a gate that does not exist).
3. Re-run all Lane R gates after any Lane L change to `modules/keos_qwen/outcome.py` or the lease API.

## Start instruction
Run the eight Lane R gates listed in the handoff; if green, continue from "Open".
