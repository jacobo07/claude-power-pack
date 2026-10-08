# WU-GEX -- GEX44 goal binding: Proof of Need first (Amendment D L8, ex ce-a3 U4)

Plan: ce-a3 Amendment D (pp-ce-a3 3aa002af, Owner "y") L8. Goal ce-lifecycle-v2. cwd = this worktree. Bound: <= 0.8M.
Precondition: WU-FLOOR-receipt.md says done.

Budget: 12 calls for the proof, 20 total. CHECKPOINT FIRST: commit a stub receipt. Logs under _logs/wugex/.

Steps:
1. Proof of Need, read-only: does any goal in ~/.claude/state/goal-budget/index.json list a non-empty `hosts` that is not
   this laptop, OR does any mission record in ~/.claude/state with a live/PREPARED state point at a GEX44 cwd/host?
   Also read the ce-a3 U4 row (pp-ce-a3 gen2/AMENDMENT-A3-2026-10-07.md) for the case it was written for.
2. No such goal or worker -> verdict NO_WORK with the evidence (the index rows and mission ids inspected). Skip to 4.
3. Need proven -> implement only the binding the U4 row names (a worker on GEX44 is charged to its goal through the
   same binding record / prebind semantics as the laptop, never by cwd), with a hermetic gate + mutant, four suites,
   pathspec commit. No ssh mutation of the GEX44 host in this unit; a remote deploy is an installer step.
4. WU-GEX-receipt.md: verdict, evidence, commits, calls.
5. Arm WU-CLOSE unless held by a mission, if remaining - open >= 1,100,000 (atomic arm, lc-WU-CLOSE, --token-estimate
   800000). Never hand the arm to a pane.

End your final message with: HANDOFF NOTE: WU-GEX done
