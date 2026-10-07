# RESUMPTION -- goal budget admission (A1 incident)

(Root RESUMPTION_FILE.md belongs to the gsd-x programme; do not overwrite it.)

**Identity.** Worktree `C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\goal-admission`,
branch `ce/goal-admission` (off feature/knowledge-acquisition 5da49554; `main` is 960 commits behind and
lacks every file). Thesis: A1's cap was read after spend; reserve from the goal's ledger BEFORE each
call. Spec `vault/specs/goal-budget-admission.md`. /ultra phases 1-5 done; phase 6 implemented.

**Sealed.** 31f1e714: GoalLedger (ledger.py), goal-* CLI (mission_spend.py), guard goal mode
(session_budget_guard.js), Agent lane (hook-dispatcher.js), V-GOAL suite, spec, OWNER_QUEUE entry.
Review (pp-code-reviewer) WARNING 2H/1M/1L, all fixed in the follow-up commit: H1 authority (lease
checked against the journal, guard state protected, --owner TTY confirmation), H2 anchored status
exemption, M1 agent hold survives renew, L1 dots-only ids. Now GOAL_PASS=45/45; mutation_drill
10/10 KILLED (scratchpad goal_drills.py). Regression SBG 16/16, ADMIT 12/12, ROUTE 33/33.
Coherence anchor: live ~/.claude/hooks/hook-dispatcher.js == PP mirror at HEAD (89AC7744) pre-change.

**Pending.**
- pp-code-reviewer verdict on 31f1e714 (fix findings as a follow-up commit).
- The live hook loads the guard from the MAIN checkout, not this worktree: fast-forward
  feature/knowledge-acquisition to ce/goal-admission there (Owner go), then the Owner does the two
  HR-001 steps in vault/OWNER_QUEUE.md (Copy-Item dispatcher; settings Task|Agent registration).
- Live canary: session scratchpad `canary/canary.py <pp> <canary_dir> canary-20261007 3000000 2 30`.
  Liveness probe first: sha256 of main-checkout hooks/session_budget_guard.js == this branch's.

**Decisions.** Binding CPP_GOAL > cwd roots > budget file. Lease = lease_calls x measured per-call,
exhausted by measured token delta. Deny only, never {continue:false} (dispatcher:423-433). No
override phrase; a crossed cap is never raised. GEX44 = UNKNOWN unless listed in hosts.
Debt (not this change): test_hook_registration_integrity.py StopIteration on the unmodified
checkout; V-SBG-LATENCY flaky under load.

**Next 3.** (1) fold review findings; (2) on Owner go: ff main checkout + verify guard hash;
(3) after Owner registration: run canary, write gen2/evidence/goal-admission/CANARY.md with hashes
and receipt.
