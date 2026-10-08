# WU-CLOSE -- closeout: UNKNOWN fails closed, canaries, knowledge, ctx-rent handoff (Amendment D L9, ex U5 + R6/R7)

Plan: ce-a3 Amendment D (pp-ce-a3 3aa002af, Owner "y") L9 + section 6 done-gate; lifecycle-v2 bootstrap master plan.
Goal ce-lifecycle-v2. cwd = this worktree. Bound: 0.8M. Precondition: WU-GEX-receipt.md says done.

Budget: 20 calls per epoch, max 2 epochs. CHECKPOINT FIRST: commit a stub receipt. Logs under _logs/wuclose/.

Steps:
1. UNKNOWN fails closed: in route admission (admit_route) and the loop budget, an unreadable or missing goal
   remaining / spend / transcript is a refusal, never an admit. Gates V-LIFE-UNKNOWN-REFUSES + an admitted control +
   a mutant treating UNKNOWN as 0 (must go red).
2. Canaries on real edges (Amendment D section 6), each recorded with the mission id / log line that proves it:
   packetless arm -> no process; success without receipt -> RECOVERY_PENDING + record; held DEAD worker settles;
   held LIVE worker stops after checkpoint; the cap extension kept cumulative spend and no new goal id (journal seq 26);
   live guard hash = approved hash (WU-INST receipt) and a spec read passes while a protected write is denied;
   one sweep-armed successor with no pane (cite the advance log). A canary that cannot run is UNKNOWN, not PASS.
3. Knowledge: one entry each in vault/knowledge_base (dedupe against ukdl-universal.md first): CONTROL_PLANE_INSIDE_
   EXECUTION_FAILURE_DOMAIN, APPROVAL_WITHOUT_CONSUMER, RETROACTIVE_ATTRIBUTION_ON_BIND (incl. settle-into-ledger),
   HALTED/DEAD_WITHOUT_RECEIPT, WORKER_DEFERS_ARM_TO_PANE, COPY_INSTALL_REVERTS_LIVE_COMMITS. UKDL: promote a Hard Rule
   only where its gate is green; traps for the rest. CBR: list each guarantee whose canary passed.
4. CI: add the new V-LIFE-* suites to whatever suite runner the repo's CI or pre-commit already calls (find it; do not
   invent a new runner).
5. ctx-rent canary handoff: write vault/programs/cognitive-economy/lifecycle/ctx-rent-S2-approval.json in WU-ADV's
   approval-record format, scope [ctx-rent-S2], plan = Apps\pp-ctx-rent vault/plans/ctx-rent-s2-recovery.md (its cap
   3,000,000 is already on goal ctx-rent-s2; cap_delta 0). Do NOT edit the ctx-rent worktree (its dirty S2 state is
   the canary's input). Record in the receipt what the advance consumer still needs from ctx-rent (an APPROVED units
   list + S2 packet) as ONE Owner-visible line if it is missing.
6. WU-CLOSE-receipt.md: gates, canary table (PASS/FAIL/UNKNOWN with evidence), KV/UKDL/CBR entries, residual debt.
   Commit by pathspec. No further arm: this is the last unit of the lineage.

End your final message with: HANDOFF NOTE: WU-CLOSE done (ce-lifecycle-v2 lineage closed)
