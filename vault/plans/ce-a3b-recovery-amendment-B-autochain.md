---
id: PLAN-CE-A3B-RECOVERY-AMENDMENT-B
covers: [a3b-autochain, unit-succession-without-owner, goal-reconcile-run, runtime-install-guard-r1, a3b-r-authority-request]
status: APPROVED (Owner "y" 2026-10-08 ~14:30, unbound pane a9461604)
extends: vault/plans/ce-a3b-recovery-2026-10-08.md (APPROVED, Owner "y" 2026-10-08)
source: unbound pane in the main checkout, 2026-10-08 ~14:20; every read by absolute path or git -C, no cd into any goal root
---

# Amendment B: the a3b-r chain stopped at R2 waiting for a person. Remove that wait, then finish A3b.

## 1. Reality delta (measured 2026-10-08 14:21)
The 2026-10-08 bootstrap prompt describes A3b as it stood about 5 hours earlier. Since then:
- B0 is SALVAGED. R0 copied the two salvage files (sha256-identical) into ce/a3b-r, fixed the 3 flaws, EMX 9/9.
  The 6 untracked files in pp-ce-a3b are forensic duplicates -> SUPERSEDED. They stay untouched and read-only.
- Canonical resource policy + scoped Owner grants: R1/R1b d0d0eb2b, GOAL_PASS 67/67, mutation KILLED.
  NOT LIVE: the main checkout still has the substring regex (hooks/session_budget_guard.js:221).
- goal-reconcile: R2 10bf871b, GOAL_PASS 72/72, mutation KILLED. NEVER RUN on a real goal. ce-a3b still reads
  used 6,863,796 / open 1,422,621. ce-a3b-r reads used 4,314,243 = settled 3,291,863 + open 1,022,380, while all
  three of its workers (m-f81fab63562c, m-800c72bfe406, m-3f5eb97ba3d0) are COMPLETED. The open amount is likely
  phantom (UNVERIFIED until the run).
- The chain is parked. R2.md ends "Do not arm R5", so after 13:32 nothing is armed and the next step is a person.
  This is the failure class the prompt names, live inside the recovery program itself.
- ce-lifecycle-v: WU-1 (prospective binding) has a live writer (dirty goal_binding.js, session_budget_guard.js).
  WU-4 (A1) owns executable-authority admission, WU-5 owns sweep succession, WU-7 owns installer recipes.
- a1/u1 and a1/a1-2 are about 950 commits ahead of main and belong to the Cognitive Economy A1 programme, not A3b.

## 2. Changes to the approved card
B1. Autochain (Outcome A, interim until lifecycle WU-5). Each a3b-r packet ends by arming the next unit with the
    lifecycle-v interim recipe (arm --no-launch, envelope, admit --route). The admit step gates on executable
    authority: remaining minus open minus 0.8M reserve must cover the unit envelope.
    If it fits: the unit launches. Owner operations: zero.
    If it does not fit: the worker writes ONE authority-request row to vault/OWNER_QUEUE.md (amount, scope,
    excludes), the mission ends HALTED, and nothing waits hot.
    The packets stop saying "do not arm". When WU-5 lands, its sweep takes over and B1 retires.
B2. Coordinator control-plane step, run once by this unbound pane: `goal-reconcile` on ce-a3b and on ce-a3b-r.
    Before and after are recorded. Expected: ce-a3b used becomes about 6.67M MEASURED, and ce-a3b-r gets back
    most of the 1.02M. Any UNKNOWN row stays counted.
B3. R3 (runtime pin) builds the single installer, and lifecycle WU-7 reuses it (DO_NOT_DUPLICATE; a note goes
    into WU-7's packet via the lifecycle receipt chain, never an edit under its live writer). First install =
    the R1 guard. Activation needs ONE Owner command, once, ever (HR-001: settings/hooks under ~/.claude are
    classifier-blocked in auto mode). After that pointer exists, guard updates need zero Owner operations.
B4. Order after reconcile: R5 (autopsy + capsule) -> R4 (progress tripwire) -> R3 (installer). Forecast 3.9M plus a
    0.8M reserve, re-costed from each receipt. R6 waits for lifecycle L2/WU-1 (WAIT, zero hot). R6 and R7
    (~3.8M forecast) are not funded here. When R3 closes, the chain raises one semantic request
    ("A3b needs up to X to finish R6+R7, excludes nothing else"). YES = it continues automatically. NO = DEFERRED.
B5. a1 branches: DEFER to their owner. No merge from A3b.

## 3. Done-gate additions
V-A3B-AUTOCHAIN: a unit completes and the next is armed with no pane involved (proved on R5 -> R4).
Reconcile before/after recorded. R1 guard live by hash after R3. The authority request is raised exactly once
and its YES path continues on its own. Every other row is unchanged from the card's section 7.
