# RESUMPTION -- ce-lifecycle (process lifecycle + context rent)

Identity: worktree C:\Users\User\Apps\pp-ce-lifecycle, branch ce/lifecycle off 86ad6f16. Card
vault/plans/ce-lifecycle-master-plan-2026-10-08.md (APPROVED, Owner "y" 2026-10-08). Goal ce-lifecycle, cap 8M.
Thesis: one lifecycle decision for context edge and lease edge; refuse before the model; successor by arm, never by Owner.

Sealed: card + L1 packet + route-L1.json committed; L1 armed via gsd_mission (mission id in the commit after arm).
Pending: Owner TTY rebind of ce-lifecycle to this root (card section 10 item 4) -- until then the worker is bounded by
its mission envelope only. ctx-rent S1 is owned by goal ctx-rent / pp-ctx-rent (its own RESUMPTION_FILE.md, next = S1);
not armed from here because that worktree holds another pane's uncommitted spec.

Decisions: units are slim-worker missions armed without --model/--autocompact; each unit writes the next packet; a
coordinator pane only reads this file, arms the next unarmed packet whose predecessor receipt exists, updates this
file, exits. A crossed cap stops; it is never raised.

Next 3 actions:
1. When L1-receipt.md lands: re-run `python tools/test_process_lifecycle.py` yourself; exit 0 required.
2. Arm L2 the same way (arm --no-launch --rollover-protocol capsule-v2 --parallel-unit lc-L2; envelope --wu-packet
   <abs L2.md> --token-estimate 0.8M; admit --route <abs route-L2.json>).
3. Hand the L1 deploy recipe from the receipt to the Owner as one copy step (HR-001).

Start: read only this file, then action 1.
