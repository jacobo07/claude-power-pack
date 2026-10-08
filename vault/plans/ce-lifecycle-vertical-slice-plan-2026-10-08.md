---
id: PLAN-CE-LIFECYCLE-VS
title: ce-lifecycle vertical slice -- L1->L4 closed loop, prospective binding, one-yes authority
status: APPROVED (Owner "y A" 2026-10-08 -- option A, 8M program envelope, lineage goal cap 5,126,080)
date: 2026-10-08
extends: vault/plans/ce-lifecycle-master-plan-2026-10-08.md (APPROVED; sections 3-4 and 6-7 stay valid)
preserves: vault/plans/ce-lifecycle-L2-addendum-2026-10-08.md, vault/plans/ce-lifecycle-L1-blocker.md (untracked; committed in WU-0)
covers: [ce-lifecycle, prospective-binding, authority-broker, process-lease, checkpoint-reserve, successor-supervisor, premodel-admission, observer-isolation, runtime-installer]
bootstrap: the Owner's 2026-10-08 /cpp-gsd-long prompt is retired by this file. Successors read section 7 (packet) only.
---

# 1. Reality delta (labels MEASURED / INFERRED / UNKNOWN)

| # | Fact | Label | Source |
|---|---|---|---|
| R1 | Branch ce/lifecycle HEAD c21200e0. L1 step 1 landed (V-LIFE-PREMODEL-TRANSPORT: dispatcher passes UserPromptSubmit blocks). Steps 2-8 not done | MEASURED | git log; L1-blocker.md |
| R2 | L1 mission m-0e11396839b5 is COMPLETED (the worker stopped at the guard, not because the work was done) | MEASURED | state/gsd-mission-m-0e11396839b5.json |
| R3 | ce-lifecycle: cap 8,000,000; settled 8,714,992; open 976,203; used 9,691,195. ce-lifecycle-2 was never declared, so the addendum's manual recovery never ran | MEASURED | goal-status |
| R4 | **Retroactive attribution confirmed.** The guard counts every transcript record at or after the GOAL-wide `entry.since`, not the session's own binding moment. At its first charge, pane bf948408 settled 5,920,094 with no prior lease, and L1 worker 6e96dc51 settled 897,181 the same way. That is 6,817,275 of pre-binding history (09:09 -> root-add ~09:41) | MEASURED | session_budget_guard.js:342-344; journal seq 6, 10 |
| R5 | Spend the goal actually caused after binding: f5f5a496 670,543 + bf948408 1,100,868 + 6e96dc51 126,306 = **1,897,717 settled**. Open 976,203 = 684,435 phantom lease of dead pane f5f5a496 (never settled) + 2 unsettled finals | MEASURED | journal arithmetic |
| R6 | Avoidable overshoot: after crossing the cap, bf948408 burned 884,804 under "final" allowances (~4 calls at ~220K), and the worker took 3 finals. The one-final rule is per reservation, not per terminal process | MEASURED | journal seq 8-17 |
| R7 | `gsd_mission arm` carries no budget goal. Worker binding falls to the cwd root, so a worker in pp-ce-lifecycle binds the exhausted ce-lifecycle. A NEW goal needs no Owner proof (F5); rebinding or removing a root needs `--owner` on a TTY | MEASURED | gsd_mission.py (no goal arg); master plan F1/F5 |
| R8 | Successor substrate is live: sweep heartbeat 09:51Z rc 0; Ralph relay + card exists | MEASURED | gsd-sweep-heartbeat.json |
| R9 | ctx-rent: only S0 (spec) landed. A4: L0 packet uncommitted (superseded by D1) | MEASURED | git logs |
| R10 | Installer pieces exist (install_global_core.py, verify_global_mirrors.py, test_hook_mirror_identity.py) but hook deployment is still Copy-Item by hand | MEASURED / INFERRED | tools/ |
| R11 | Concurrent writers: mission m-9bee7894f20f RUNNING in the main checkout. No live mission in pp-ce-lifecycle | MEASURED | mission records |

# 2. Ownership (extend, never duplicate)

Every Owner is the one named in master plan section 2. Additions:
- **Authority plane** = `tools/mission_spend.py` GoalLedger, extended with `program` (cumulative envelope plus lineage) and `authority_request` / `authority_event` journal ops. There is no new store.
- **Binding record** = `state/goal-binding/<sid>.json`, written by the launcher (arm / kclaude / SessionStart) and read by one shared resolver, `hooks/lib/goal_binding.js` (Python twin in mission_spend).
- **Control plane** = the existing PP-GsdLongRun-Sweep plus `gsd_mission.py`. It gains a `lifecycle` stage (decide -> settle -> successor). No new daemon.
- **Approval surface** = the Owner's own prompt in any interactive pane (UserPromptSubmit), plus a Windows toast / PushNotification. See section 4.

# 3. Work Units (lease = work + checkpoint reserve; reserve = max(2 x p90 per call, measured kclear))

| WU | Deliverable | Progress contract | Lease (work + reserve) | Proof | Trip |
|---|---|---|---|---|---|
| WU-0 bootstrap (deterministic, no model) | commit the preserved files + this plan; one honest ledger correction (section 4.4); declare the lineage goal; new worktree; arm WU-1 | 1 commit + journal rows | 0 model | goal-status shows the lineage and its remaining authority; mission LAUNCHING | any step error -> stop and report |
| WU-1 Prospective binding + observer isolation (L2 core) | `goal_binding.js`/py resolver; per-session `since` = binding event; precedence: launcher record > explicit event > cwd hint (cwd never binds a session already running, never binds a read-only observer); `arm --goal`; overlapping live roots refused; root removal | commit + V-LIFE-BIND-RETRO / OBSERVER / ROOT red-green, with mutants | 0.9M + 0.25M | replay of the R4 journal -> no jump; observer canary | 0.4M with no commit |
| WU-2 Authority broker + program envelope (L2) | `program` envelope (cumulative, lineage-summed, so a new goal/session/process adds no money); `authority_request` written by the control plane; `premodel_gate` resolves an Owner prompt `approve <REQ-id>` / `deny <REQ-id>` into an authority event; NEW caps need an APPROVED plan or an Owner event (closes F5) | V-LIFE-APPROVE-* + forge mutants (a worker writes the event / the autotype types "approve" -> refused) | 1.0M + 0.25M | case B/C dry run on a test goal | 0.4M flat |
| WU-3 L1 finish: pre-model admission | `premodel_gate.js` (<= 2 s) blocks the prompt when the session is terminal / superseded / quiescent / exhausted; one-final-per-PROCESS (fixes R6); surface classification table (PRE_MODEL / LAUNCH / TOOL_ONLY / HOST_LIMITED) | V-LIFE-PREMODEL-* incl. the dispatcher-drop mutant still owed | 0.7M + 0.2M | canary 10: a dead pane's prompt costs 0 model tokens | 0.3M flat |
| WU-4 Lease / checkpoint / settlement (L3) | CHECKPOINT state; the reserve funds only kclear/receipt/arm; settle-on-exit releases unused reservations; an unsettled lease of a dead process is reconciled by the sweep (fixes the 684K phantom); feasibility floor (lease >= 3 x p90) | V-LIFE-RESERVE-* (mutant "reserve funds work" goes red); SAFE_TO_FORGET = card re-read + hash | 0.8M + 0.2M | canary CAP: small test goal, overshoot <= measured in-flight envelope (1 call) | 0.3M flat |
| WU-5 Successor supervisor (L4) | `lifecycle.decide` (master plan section 4) + sweep `lifecycle` stage: settle -> resolve authority -> singleflight + stale-wake check -> resolve worktree + baseline (U6a resolver) -> card -> arm, or run a deterministic step, or WAIT, or APPROVAL; closer-guard and Stop recognize terminal state | V-LIFE-DECIDE / SUCCESSOR / SINGLEFLIGHT / STALE / ORPHAN | 1.3M + 0.3M | canaries 7, 8, 9, 12: zero-terminal case A | 0.5M flat |
| WU-6 Context Rent hook-in | ctx-rent S1 meter + decide's ROTATE inequality on the same executor (no second lifecycle); provider compact counted as `compact_fallback` | V-CTX-* + V-LIFE-ROTATE | 0.6M + 0.15M (shared with the ctx-rent goal per D2) | canary CONTEXT RENT | 0.3M flat |
| WU-7 Runtime installer | `install_global_core.py --certified`: stage -> test -> mutation -> atomic swap -> sha/version -> drift check in the sweep -> rollback; the arm path refuses on drift | V-INSTALL-* | 0.5M + 0.15M | a hook change lands live with zero Owner Copy-Item | 0.25M flat |
| WU-8 Self-host + CI + KV/UKDL/CBR + retirement | ce-lifecycle crosses its own WU boundaries via WU-5; `test_process_lifecycle.py` registered in /liveness; <= 4 HR + 1 PR + traps after dedupe; retire the manual instructions (goal-declare --owner recovery, "open a fresh pane", L2-addendum recovery section) | Master Done-Gate (master plan section 8 + this section 5) | 0.7M + 0.2M | canary SELF-HOST: WU-5 -> WU-6 -> WU-7 -> WU-8 handoffs with no Owner action | 0.3M flat |

Order: WU-0 -> 1 -> 2 -> 3 -> 4 -> 5 (vertical slice closes here; the first zero-terminal canary runs) -> 6 / 7 -> 8. One live writer mission at a time on this branch. Micro-commits, no push. Kill switches: `CPP_PREMODEL_GATE=0`, `CPP_LIFECYCLE_DECIDE=0`, `CPP_CHECKPOINT_RESERVE=0`, `CPP_PROSPECTIVE_BIND=0`. Forecast: 7.95M work+reserve (MEASURED basis: L1 worker 1.02M for ~1 step at 63K/call, so these leases carry +30 % over the master plan's caps). Each WU's receipt reforecasts.

# 4. Answers the prompt requires

1. **Authorization without PowerShell.** A worker that hits exhaustion writes nothing itself. The sweep (deterministic) appends `authority_request REQ-xxxx {goal, amount, why, plan}` and raises a toast. The Owner types `approve REQ-xxxx` (or `deny ...`) in ANY Claude pane. `premodel_gate` sees the human prompt at UserPromptSubmit, records `authority_event` and blocks that turn (0 model tokens). The sweep then arms. This is forge-safe because the model never produces UserPromptSubmit text. The autotype allow-list (only /clear, /kclear, /kresume) and bg-resume prompts are tested NOT to match `approve`. Host limit, stated plainly: there is no native approve button, so the "surface" is the Owner's own prompt. The terminal is not part of the contract.
2. **Existing authority -> automatic successor.** The lease edge leads to CHECKPOINT (reserve), then SAFE_TO_FORGET, then QUIESCENT. The sweep's lifecycle stage sees that program remaining > next lease, takes a successor lease under the SAME goal, and runs `arm --goal` with the card. Zero Owner operations.
3. **New authority -> one yes.** See 1. After YES the sweep arms. After NO the goal goes to `quiescent`, with no retries.
4. **Pre-binding history stops being charged.** Per-session `since` equals the binding event. The R4 history is moved by one journaled `reattribute` op into `PRE_BINDING_PROGRAM_CAPEX` (6,817,275, kept and reported, never deleted, never Goal spend).
5. **Folder stops being economic identity.** cwd is a hint that only applies to a session's FIRST binding, and only when no launcher record exists. Observers (status/read-only or a different binding) never bind. Two live goals cannot share a root.
6. **Overshoot bounded.** One final reply per process (R6). Phantom leases are reconciled. The pre-model block stops dead-pane turns. The residual is 1 in-flight call (autonomous turns after a tool result never pass UserPromptSubmit), measured in canary CAP.
7. **Dead panes stop consuming turns.** Terminal/QUIESCENT state lets the pre-model block refuse the prompt, and closer-guard permits a silent close.
8. **Context Rent -> fresh successor.** decide's ROTATE uses the same executor as the lease edge (WU-6).
9. **ce-lifecycle crosses its own boundary.** From WU-1 on, every WU ends with a receipt and the sweep arms the next. This planning pane ends after WU-0 and does not wait.
10. **Manual commands become obsolete.** `goal-declare --owner` recovery, CPP_GOAL, "open a pane and say continue" and hook Copy-Item are removed from the docs in WU-8. `goal-declare` for a NEW goal without an APPROVED plan or Owner event becomes impossible (WU-2).

## 4.4 What the one approval authorizes (the bootstrap, WU-0)

The ledger cannot yet express a program envelope or a reattribution, and a worker in pp-ce-lifecycle binds the exhausted goal by cwd (R7). So WU-0, run deterministically by this pane right after YES, does three things:
- commits the plan and preserved files on ce/lifecycle;
- creates worktree `C:\Users\User\Apps\pp-ce-lifecycle-v` on new branch `ce/lifecycle-v` from that commit (the last time a folder is used to separate authority; WU-1 removes the need);
- declares goal `ce-lifecycle-v` with `--source` = this plan, `continues: ce-lifecycle`, cap = the Owner-approved amount below, root = the new worktree; then arms WU-1 there.

The old worktree goes quiescent (its goal is exhausted, so nothing runs there).

**Authority options:**
- (A, recommended) Keep the 8M program envelope. Spend genuinely caused after binding is 1,897,717 + 976,203 open (worst case) = 2,873,920, so the new cap is **5,126,080**. That covers WU-0..WU-4 plus part of WU-5. When it runs out, the broker built in WU-2 asks you ONE semantic question. That moment is the live Case-B canary.
- (B) A 12M program envelope (cap 9,126,080) covers the full forecast without a mid-run question.

# 5. Done-gate additions (on top of master plan section 8)

The Master Done-Gate also needs these real canaries, each with ledger evidence:
- NO-TERMINAL (case A with no Owner command);
- PROSPECTIVE-BINDING (a pane with known history binds, and the cap moves only by post-bind spend);
- OBSERVER (a status read does not bind);
- CAP (overshoot <= 1 measured in-flight call);
- CONTEXT RENT (ROTATE before the provider wall);
- WAITING (an authority request leaves 0 hot calls until the event);
- SELF-HOST (>= 3 WU handoffs with no Owner action).

UNKNOWN stays UNKNOWN. A canary that cannot run because of quota is DEFERRED, never PASS.

# 6. CBR

Each verified guarantee becomes a gate in `test_process_lifecycle.py`, registered in /liveness and the completion baseline. The text it replaces (manual recovery, CPP_GOAL, Context Pressure /compact line) is retired in the same commit.

# 7. Successor packet (the ONLY input of each WU worker)

Goal ce-lifecycle-v, worktree pp-ce-lifecycle-v. Read this file's sections 3 and 4 plus your WU row, and master plan sections 4-5 if your WU is 3, 4 or 5. Do not read the bootstrap prompt. On finish: write `vault/programs/cognitive-economy/lifecycle/<WU>-receipt.md` (decision / effect / proof / unknowns / refs / spend / reforecast) and commit it. Until WU-5 lands, arm the next row yourself (`gsd_mission.py arm --goal ce-lifecycle-v` once WU-1 adds the flag); after WU-5, the sweep arms it. Do not wait on workers.
