# WU-1H -- HALTED without a receipt continues: fault capsule + bounded renewal (V-LIFE-HALT-CONTINUES)

Plan: vault/plans/ce-lifecycle-WU-1R-recovery-plan-2026-10-08.md (APPROVED, Owner A), row WU-1H; this is unit L1 of
ce-a3 Amendment D (Owner "y" ~18:05, pp-ce-a3 3aa002af), which runs it FIRST. Cites amendment A1.
Goal ce-lifecycle-v2. Worktree = your cwd (branch ce/lifecycle-v2).
Precondition: WU-1B-receipt.md exists and says WU-1B done. If it says BLOCKED, stop and repeat its blocker.

Third measured case (2026-10-08 16:06 UTC): WU-1C's worker (m-1783bda2a44b) died mid-run. Its out.json was empty and
supervise took the "slim worker failed: pid exited and ... holds no result JSON" branch -> HALTED, nothing renewed.
Steps 1-3 apply to that branch too: capsule (DONE/SALVAGE may both be empty), one renewal of the same packet.
Add V-LIFE-DEAD-NO-RESULT (empty out.json + dead pid -> capsule + one successor).

Measured gap (read in the live checkout 2026-10-08): in `supervise`, the `slim_finished` branch
(tools/gsd_mission.py ~2790) moves a worker that tripped its envelope straight to HALTED. It writes no capsule and
renews nothing. That is how WU-1 (m-3403c155ecb8, 1,198,372 > 1,150,000) stranded its uncommitted steps 2-4 until a
pane intervened. `renew_mission` (~2161) already makes a PREPARED same-work successor that the normal launch path starts.
EXTEND these two; do not add a new supervisor.

Budget discipline: hard cap 16 model calls (Amendment D L1 = 0.6M) per epoch, max 2 epochs; CHECKPOINT FIRST: commit a
stub WU-1H-receipt.md before step 1, so a dead worker leaves a trace; batch into large PowerShell calls, logs under _logs/wu1h/; read only the
slim_finished branch, renew_mission, _renewal_why_not and the capsule-v2 helpers they call. Past ~50K context: commit
what is green, append to the receipt, end with HANDOFF NOTE.

Steps:
1. In the slim_finished HALTED branch, before or with the HALTED transition, write
   `<state>/fault-capsules/<mission_id>-e<epoch>.json` with `wx` (exists = already written, never rewrite):
   HEAD, commits since the mission's origin fingerprint (`git -C <cwd> log --oneline <origin>..HEAD`), dirty paths +
   `git diff --stat`, the last `^(PASS|FAIL|[A-Z_]+_PASS=)` lines in the worker's result text, spend (slim tokens,
   envelope stop), the final result text truncated to 2,000 chars, and a partial-receipt split DONE (committed) vs
   SALVAGE (dirty). Read-only git only; never stash, reset or check out.
2. Renew once: if the HALTED mission has a wu_packet AND the receipt for that packet is absent AND the goal's remaining
   executable authority (goal-status remaining minus open reservations) covers the packet's token_estimate, call
   renew_mission with the capsule path carried (continuity_from). Singleflight: skip if the ledger already holds
   `mission_renewed` for this mission_id; the transition's expect_epoch CAS covers concurrent passes. Otherwise record
   `renewal: not renewed: <reason>` and stop at WAITING_FOR_AUTHORITY.
   Never renew past max renewal 2 per lineage; the third halt surfaces to the Owner.
3. The successor's packet prefix must name the capsule path, so the fresh worker starts from it and not from a transcript.
4. Kill switch: CPP_HALT_CONTINUE=off restores the old behaviour (HALTED, no capsule, no renewal).
5. Tests in tools/test_gsd_mission.py (or test_process_lifecycle.py, wherever supervise fixtures already live),
   hermetic state dir, fake slim result with tripped=true and a temp git repo with one commit + one dirty file:
   - V-LIFE-HALT-CONTINUES: one capsule, DONE/SALVAGE correct, exactly one PREPARED successor carrying the capsule.
   - V-LIFE-HALT-ONCE: two supervise passes over the same halt -> one capsule, one successor.
   - V-LIFE-HALT-NO-AUTHORITY: remaining below the estimate -> capsule written, no successor, reason recorded.
   - V-LIFE-HALT-KILL: kill switch -> old behaviour.
   - Mutants on an isolated copy (tools/mutation_drill.py): require a normal receipt before renewing -> HALT-CONTINUES
     red; drop the ledger singleflight check -> HALT-ONCE red.
6. Run the four suites (process_lifecycle, goal_budget_admission, hook_boundary, gsd_mission). Record PASS lines.
7. Commit by pathspec with -F msgfile and verify `git log -1 --format=%s`. Never push, reset, stash or check out.
8. Write WU-1H-receipt.md (<= 40 lines) with a deploy recipe for tools/gsd_mission.py (files + sha256 + base sha in the
   live checkout + rollback). Do NOT deploy (HR-001). Commit it.
9. Arm WU-ADV (Amendment D L2) only if WU-ADV.md and route-WU-ADV.json exist AND goal-status for ce-lifecycle-v2
   shows remaining minus open >= 1,100,000 (0.8M + 300K checkpoint reserve). Use the atomic arm from addendum C if it
   is green, else: arm --cwd <this worktree> --command /gsd-autonomous --no-launch --rollover-protocol capsule-v2
   --max-cycles 3 --parallel-unit lc-WU-ADV; envelope --mission <id> --wu-packet <abs WU-ADV.md> --token-estimate
   800000; admit --mission <id> --route <abs route-WU-ADV.json>. Otherwise write
   WAITING_FOR_AUTHORITY with the numbers into the receipt. Never hand the arm to "a fresh pane": arm it yourself or
   record ARM_FAILED + the error (WU-1B's worker deferred its arm to a pane; that is the trap this unit closes).

Scope addendum (ce-a3 Amendment C, Owner "y" 2026-10-08, pp-ce-a3 4f1fe9ae; measured cases, not hypotheses):
A. COMPLETED counts too. ce-a3 U2's worker ended `subtype: success` after a cap refusal with no receipt. Apply steps
   1-3 to a COMPLETED mission whose wu_packet receipt is absent: work-unit status RECOVERY_PENDING, no dependent arm.
   Add V-LIFE-SUCCESS-NO-RECEIPT + a mutant that treats provider success as the receipt (must go red).
B. One capsule format. ce/a3b-r 6902264d already has `mission_capsule.fault_capsule` (R5, AUTOPSY 10/10). Reuse it via
   `git cherry-pick -x 88d37fe9 6902264d` if it applies cleanly; otherwise record in the receipt why a second format exists.
C. Atomic arm. R5c's Close ran `arm` without --no-launch twice: two packet-less /gsd-autonomous launches with the auto
   7.5M envelope (m-413f1e324aa5, m-d84de9dd1edb, now on owner hold); ce-a3b-r used 5.87M -> 8.23M over R5c plus those two, 1.44M held open by them. Step 9 and every Close:
   arm --no-launch, then envelope, then admit; if envelope or admit fails, `hold` the armed mission with the error.
If 13 calls cannot cover A-C, finish steps 1-9 first and list A-C as residual in the receipt.

Do not touch: the live checkout under ~/.claude, ctx-rent, the ce-lifecycle-v worktree.

End your final message with: HANDOFF NOTE: WU-1H done
