# RESUMPTION -- A3b recovery (goal ce-a3b-r)

Identity: worktree C:\Users\User\Apps\pp-ce-a3b-r, branch ce/a3b-r off a0c92f1b. Card
vault/plans/ce-a3b-recovery-2026-10-08.md (APPROVED, Owner "y" 2026-10-08). Goal ce-a3b-r, cap 8.6M, root = this
worktree. Thesis: the A3b "6.2M worker burn" was 76% coordinator/observer panes bound by cwd, 1.42M phantom
reservations, and two guard defects. Fix the unowned gaps, finish A3b C21-C25.

Sealed: R0 (B0 salvaged; EMX 9/9; R0-receipt.md). R1 packet + route written and armed (see mission id in R1-receipt.md
or `gsd_mission.py status`).
AMENDMENT B (APPROVED 2026-10-08 ~14:30, vault/plans/ce-a3b-recovery-amendment-B-autochain.md): R1, R1b, R2 sealed.
goal-reconcile run by the unbound coordinator: ce-a3b used 6,863,796 -> 6,829,856 (open 1,422,621 -> 0);
ce-a3b-r used 4,314,243 -> 3,907,484 (open 1,022,380 -> 0, remaining 4,692,516). Order now R5 -> R4 -> R3, then ONE
authority request for R6+R7. Every packet's Close arms the next unit (autochain) or writes one AUTHORITY_REQUEST line.
Old goal ce-a3b and worktree pp-ce-a3b: forensic evidence, read-only. Never cd into either root from a pane.

Decisions: units are slim-worker missions; each unit writes and arms the next packet; no coordinator pane. Order
R1 -> R2 -> R5 -> R4 -> R3 -> R6 -> R7. Expected reach in 8.6M: through R4 (section 10). ce-lifecycle's goal is
over its cap (L1 stopped after step 1, commit c21200e0), so the R6 / L-dependent canaries are DEFERRED until a
ce-lifecycle successor goal lands L2.

Next 3 actions (for a fresh pane, only if the chain broke):
1. `python tools/gsd_mission.py status` -> find the a3b-r unit; read its out.json, never its transcript.
2. If a receipt exists and the next unit is not armed: arm it exactly as R1.md "Close" says.
3. If a unit stopped on a guard refusal: read the receipt; R1 is the fix for path-pattern refusals.

Start: read only this file.
