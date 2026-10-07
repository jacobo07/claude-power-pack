# Work packet -- mission ce-a2 (Amendment A2), every worker epoch

work_tree: C:\Users\User\Apps\pp-ce-a2
done_gate: python tools/test_cognitive_economy_program.py --generation 2 --final

You are a fresh, disposable worker. Durable state is on disk; you have no transcript and need none.

1. Read `vault/programs/cognitive-economy/gen2/AMENDMENT-A2-2026-10-07.md` (laws + units) and
   `.planning/workstreams/ce-a2/STATE.md`. Then read ONLY the first unticked phase in
   `.planning/workstreams/ce-a2/ROADMAP.md` whose dependencies are ticked, plus the operating constraints at the top.
2. Run `git -C C:\Users\User\Apps\pp-ce-a2 status --short` and `log -3`. Reconcile: if a predecessor left the phase
   half-done, continue from what is committed; uncommitted changes in this tree are the predecessor's work in
   progress -- inspect, then finish or revert them deliberately.
3. Execute that phase directly (EXECUTION mode). Dossier and paged reads before archaeology. RED first.
4. Close the phase: `phases/<NN>/EVIDENCE.md`, tick its checkbox, update STATE.md (current phase, last activity,
   completed_phases, percent), micro-commit. Then continue with the next eligible phase if budget remains.
5. If a phase is blocked (needs Owner, needs another pane's tree, host limit): write it into its EVIDENCE.md, mark
   BLOCKED in STATE.md, move to the next unblocked phase. Never wait idle, never ask mid-run.
6. When every phase is ticked or BLOCKED, run the done_gate once, record its output in phase 8 EVIDENCE.md and stop.
7. At the context wall: finish and commit the current step, end with `HANDOFF NOTE:` naming the phase, the last
   commit and the next concrete action.
</content>
</invoke>
