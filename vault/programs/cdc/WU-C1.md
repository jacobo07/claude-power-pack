# WU-C1 -- Cognitive ledger: economic role per call + receipts

Common brief: `vault/programs/cdc/PROGRAMME.md`. Plan section: 3 (C1), 4.

Goal: every model call in a transcript gets an economic role, deterministically, so waste is diagnosable.
1. Extend `tools/session_autopsy.py` (keep its CLI) with `--roles`: per call classify from the assistant turn's tool
   uses and their inputs: READ, REREAD (same path already read in this epoch and unchanged sha/mtime), RESEARCH
   (WebSearch/WebFetch), PLAN (Write/Edit under .planning/ or vault/plans, or no tool + long text before any edit),
   IMPLEMENT (Edit/Write elsewhere), PROOF (test/gate commands), CONTROL (git status/log, mission/chain/status tools),
   STATUS (status/handoff rendering), RECOVERY (retry of a failed identical command), REPAIR (edit after a red test),
   CONTEXT_FAULT (Read of a file named in the capsule/card), NOVELTY (rest with an edit producing new code). Subagent
   transcripts (`<sid>/subagents/*.jsonl`) included and tagged.
2. Output per role: calls, processed tokens, share; `unattributed` share must be reported, never hidden.
3. Semantic transitions: count commits, new files, receipt claims, test red->green; print tokens/transition.
4. Tests: `tools/test_session_autopsy_roles.py` with 3 golden mini-transcripts + a mutant per role (role flips RED).
5. Run on the QuickLease Phase-1 worker `6ddc58ea` (+7 subagents) and store `vault/programs/cdc/evidence/ql-phase1-roles.json`
   (input for C12; do NOT interpret QL beyond the table). Land via land_worktree.
Receipt: the role table for QL Phase 1 + unattributed share.
