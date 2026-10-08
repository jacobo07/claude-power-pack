# WU-ADV -- the sweep advances approved work: plan-unit consumer + consume-once approval + goal-aware admission

Plan: ce-a3 Amendment D L2 (Owner "y" ~18:05, pp-ce-a3 3aa002af, section 3 L2 + section 3b) and the lifecycle-v2
bootstrap master plan (79350a8e, APPROVED). Goal ce-lifecycle-v2. Worktree = your cwd (branch ce/lifecycle-v2).
Precondition: WU-1H-receipt.md says WU-1H done. If BLOCKED, stop and repeat its blocker.

Why: every transition so far depended on a worker's last step or a pane. WU-1B deferred its arm to "a fresh pane";
the Owner's y lived only in a transcript. This unit makes the sweep itself advance approved work.

Budget: 20 model calls per epoch, max 2 epochs (0.7M). CHECKPOINT FIRST: commit a stub WU-ADV-receipt.md. Large batched
PowerShell calls, logs under _logs/wuadv/. Read only supervise's dispatch loop, route_admission's goal hook, and
modules/provider_routing/ledger.py declare_cap (~233). Past ~50K context: commit green, append receipt, HANDOFF NOTE.

Steps:
1. Approval record (no new journal op; EXTEND ledger.declare_cap):
   `<state>/approvals/<approval_id>.json` = {approval_id, goal, plan_path, plan_commit, plan_sha256, scope: [unit ids],
   cap_delta, source_quote}. A consumer applies cap_delta through declare_cap with source naming approval_id, only if the
   journal holds no `cap` op whose source names that approval_id (consume-once). Extension #1 (Amendment D, seq 26)
   is already applied: write its record marked consumed, citing seq 26, and prove the consumer refuses to re-apply it.
2. Plan-unit consumer = an `advance` stage in `supervise` (tools/gsd_mission.py), kill switch CPP_SWEEP_ADVANCE=off.
   For each goal, read the plan named by the approval record. Frontmatter status must be APPROVED, and the units list
   must appear in plan order. Find the first unit whose receipt (`<unit>-receipt.md`, a gate/PASS line, not a partial
   receipt) is absent and that has no live or PREPARED mission. If its predecessor's receipt exists, and its packet sha
   matches the plan's listed sha when one is listed, and goal remaining - open >= its estimate + 300,000, arm it through
   the atomic arm (WU-1H addendum C). Otherwise record WAITING_FOR_AUTHORITY or WAITING_FOR_RECEIPT in the advance log.
   Never arm a packet absent from the plan's list. Never edit code. Never raise a cap except through step 1.
   Singleflight: key (goal, unit, packet sha), persisted before the arm. A second pass with the key present is a no-op.
3. Route admission reads goal remaining: tools/route_admission.py (or the admit path in gsd_mission.py) takes the
   mission's goal and refuses when need > remaining - open. Today it prints remaining=None. A goal-less mission keeps
   today's behaviour.
4. Tests (red first), hermetic state dir + temp git repo + temp plan:
   V-LIFE-ADV-ARMS-NEXT (receipt of unit N present -> unit N+1 armed once), V-LIFE-ADV-ONCE (two passes -> one arm),
   V-LIFE-ADV-NOT-LISTED (packet absent from the plan list -> no arm), V-LIFE-ADV-NO-AUTHORITY (-> WAITING, no arm),
   V-LIFE-APPROVAL-ONCE (same approval_id twice -> one cap op), V-LIFE-ADMIT-GOAL (need > remaining -> refused) +
   an admitted control for each refusal. Mutants via tools/mutation_drill.py: drop the singleflight key -> ADV-ONCE
   red; drop the list check -> NOT-LISTED red; drop the source check -> APPROVAL-ONCE red.
5. Run test_gsd_mission.py, test_process_lifecycle.py, test_goal_budget_admission.py, test_hook_boundary.py.
6. Commit by pathspec with -F msgfile; verify `git log -1 --format=%s`. Never push, reset, stash or check out.
7. WU-ADV-receipt.md (<= 50 lines): gates, mutants, commits, calls, file hashes for the L5 installer. Do NOT deploy.
8. Arm WU-1C (roots, Amendment D L3) if WU-1C.md and route-WU-1C.json exist AND remaining - open >= 800,000. Use
   the atomic arm with --parallel-unit lc-WU-1C and --token-estimate 500000. Otherwise WAITING_FOR_AUTHORITY.
   Never hand the arm to a pane.

Do not touch: the live checkout under ~/.claude, ctx-rent, ce-lifecycle-v, ce-a3b-r (m-d84de9dd1edb is the Owner's).

End your final message with: HANDOFF NOTE: WU-ADV done
