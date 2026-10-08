# WU-FLOOR -- Fresh Focus Floor: measure first, cut only the proven residual (Amendment D L7, ex ce-a3 U3)

Plan: ce-a3 Amendment D (pp-ce-a3 3aa002af, Owner "y") L7. Goal ce-lifecycle-v2. cwd = this worktree. Bound: <= 1.0M.
Precondition: WU-TRIP-receipt.md says done.

Context: the measured cost driver is context rent (WU-1: floor ~18K, +2.4K per call). A fresh worker's floor is what
every unit pays per call. TOK-18 / cognitive-economy E1 may already have cut it; prove before building.

Budget: 16 calls per epoch, max 2 epochs. CHECKPOINT FIRST: commit a stub receipt. Logs under _logs/wufloor/.

Steps:
1. Proof of Non-Work: locate tools/floor_regression_gate.py (Glob from this worktree). If absent, say so and measure
   directly: the first-call input tokens (input + cache read + cache creation) of the last 5 slim workers' out.json
   files under ~/.claude/state/slim-jobs/ for this goal. Record per-worker floor and its sources (CLAUDE.md chain,
   rules, hook additionalContext, skill list) as measured, never estimated.
2. Compare against the target in ce-a3 U3 (gen2/AMENDMENT-A3-2026-10-07.md in pp-ce-a3, read only the U3 row). If the
   measured floor is within target, write NO_WORK with the numbers and skip to step 5.
3. Otherwise cut only the largest proven contributor that lives in THIS repo (hook additionalContext emitted to slim
   workers, packet prefix size). Do not edit ~/.claude/CLAUDE.md or ~/.claude/rules (Owner files, HR-001); if the
   residual lives there, write one OWNER_QUEUE line with the measured bytes and the proposed cut.
4. Prove the cut: a hermetic gate that measures the emitted context for a slim profile before/after, with a mutant
   that restores the old emission and must go red. Run the four suites. Commit by pathspec.
5. WU-FLOOR-receipt.md: floor before/after with sources, verdict (NO_WORK / CUT / OWNER_QUEUE), calls used.
6. Arm WU-GEX unless held by a mission, if remaining - open >= 1,100,000 (atomic arm, lc-WU-GEX, --token-estimate
   800000). Never hand the arm to a pane.

End your final message with: HANDOFF NOTE: WU-FLOOR done
