# ce-lifecycle L2 addendum (Owner "y" 2026-10-08) -- read BEFORE writing L2.md

Written with the single closeout allowance of pane bf948408 after goal ce-lifecycle was exhausted.

## Incident (MEASURED unless marked)
- Owner rebound ce-lifecycle to root C:\Users\User\Apps\pp-ce-lifecycle (--owner). Before: used 1,354,978.
- Next call from pane bf948408 (whose cwd had become that worktree): refused, used 7,709,534 of 8,000,000.
- Cause (INFERRED): cwd-root binding charged the pane's ENTIRE pre-binding transcript to the goal, plus L1
  worker m-0e11396839b5 (716,643 at last read). Failure class: RETROACTIVE_ATTRIBUTION_ON_BIND.
- Contributing (MEASURED): the coordinator pane stayed in the root it was about to bind (my error).
- L1 worker likely refused from that point; its commits (if any) are on ce/lifecycle after 5f06225e. UNVERIFIED.

## Recovery (Owner, by hand this once)
Retire ce-lifecycle onto an unused root, declare ce-lifecycle-2 (5M, root pp-ce-lifecycle, --owner), verify
goal-status of both. If ce-lifecycle still lists pp-ce-lifecycle, --root appends: STOP, L2 must add root removal.

## L2 scope additions (first task, ahead of section 5 L2 of the master plan)
1. `mission_spend.py goal-approve` (one-word Owner flow): given an exhausted goal whose approved plan still has
   unarmed units, print ONE question ("Approve <N> for <goal>-<k>? type the id"), then mechanically: retire the old
   goal's roots, declare the successor with --source = plan path, verify both statuses, mark the old goal
   `superseded_by`, mark bound panes QUIESCENT, release/re-arm the mission. TTY confirmation stays (anti-laundering).
2. Bind is prospective only: a session binds from its first call AFTER the binding record; tokens before it are
   never charged (`since` = binding time per session, not goal since). Test: replay this incident -> no jump.
3. Two live goals may not share a root (declare refuses); rebind must be able to REMOVE a root.
4. NEW goal caps require the same Owner proof as raises (F5).
5. Coordinator panes never cd into a root they are about to bind (packet rule + guard warning).
Tests: V-LIFE-BIND-RETRO-*, V-LIFE-APPROVE-* with positive controls and mutants.
