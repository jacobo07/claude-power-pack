---
id: PLAN-CE-A3B-RECOVERY
covers: [ce-a3b-recovery, a3b-salvage, goal-reconcile, canonical-goal-grants, runtime-pin, goal-progress-tripwire, goal-autopsy, fault-capsule-bound-session]
status: APPROVED (Owner "y" 2026-10-08, pane 88df3ab3) -- executing; reforecast in section 10
extends: gen2 Amendment A3b (b2754615); depends on ce-lifecycle L1/L2/L3 (1386ec34, APPROVED) and ctx-rent (0f8713fe); A4 W1b delegates here
source: forensic pane 88df3ab3 (cwd main checkout, UNBOUND -- never entered pp-ce-a3b; every read by absolute path, git -C)
---

# A3b recovery + the immunity gaps nobody owns

## 1. Forensics (raw transcripts + journal, deterministic; scratchpad autopsy.py)

Premise correction (MEASURED): no worker burned 6.2M. "6.2M" was the growth of the goal's `used`, which
includes 1,422,621 of phantom reservations. Raw processed across the four sessions bound to ce-a3b = 6,666,082.

| sid | role | model | calls | processed | of which charged retroactively (before cwd entered root) | stop cause |
|---|---|---|---|---|---|---|
| 9437261e | worker 1 | sonnet | 4 | 435,148 | 0 | GOAL_STATE lexical FP: Read of `vault/specs/goal-budget-admission.md` denied (session_budget_guard.js:221) |
| 116de5ca | worker 2 | sonnet | 10 | 1,160,335 | 0 | live guard threw `MAX_TOOL_IDS is not defined` at 23:54; ffd8f9e9 defined it at 23:56. A half-edited guard in the SHARED checkout is the live guard (hook-dispatcher.js:113-120 load it from the working tree) |
| 2494f14c | coordinator pane | opus | 29 | 3,993,419 | 629,367 | `Set-Location` into pp-ce-a3b bound it (guard binds by event.cwd, :198-201); at the end 2 refused calls 5 s apart (second attempt after a terminal refusal) |
| f538b230 | observer pane | opus | 8 | 1,077,180 | 797,740 | `Set-Location` into the root to inspect, bound, refused, one closing reply |

- Workers: 1,595,483 (24%). Panes: 5,070,599 (76%), of which 1,427,107 was charged for work done before binding.
- Ledger: used 6,863,796 = settled 5,441,175 + open 1,422,621. The open part is lease 9437261e:1 511,680 (the "~511K
  dead worker"), leaked lease 116de5ca:3 611,060, and finals 146,534 + 153,347. `leak` rows keep counting forever
  (modules/provider_routing/ledger.py:221); there is no reconcile. Settled under-measures the workers (102k vs 435k,
  553k vs 1.16M) because measuring stops when the guard denies or crashes.
- Context: per-call context 102k-153k, growth inside a session <= 30k. Dead-history rent was NOT material; the
  fresh floor (~100k sonnet, ~123k opus) times 51 calls was. Archaeology, call explosion and packet breadth were not
  material (worker 2: 5 Read, 2 Grep, 1 Glob, 1 Write, 2 Edit). Work-Unit size is UNKNOWN: no unit ran long enough.
- Why no commit: worker 2 finished B0 output, then every Edit, including the RECEIPT checkpoint write, was denied by
  the UNKNOWN fail-closed path. The guard refused the checkpoint itself.
- Product of the whole spend: `tools/entry_matrix.py` + `gen2/evidence/a3b/ENTRY_MATRIX.md` (uncommitted, valid,
  3 known flaws: self-match, "unbounded" overstated, docstring/test hits) + receipt commit a0c92f1b. Finding inside
  it: 28 of 35 headless launch-site files carry no binding and no ceiling. The A3b workers were themselves
  hand-launched `claude -p`, not `gsd_mission arm`, so no envelope, breaker or capsule applied.
- The one-file exception: the spec was byte-copied to `Apps/ce-a3b-admission-spec.md` with the name assembled from
  parts so the regex missed it (RECEIPT.md:21-29). This is authorization by string accident. The only alternative,
  `CPP_SESSION_BUDGET=off`, drops all accounting.
- FIOS zero portable assets: reported, UNVERIFIED (R6 measures it).

Salvage verdict: **RECOMPILE_AND_CONTINUE**. B0 is salvaged (R0). B1-B3 are rescoped against live owners below.

## 2. Root-cause graph
1. cwd = economic identity. A mid-session `cd` binds, and binding charges the transcript since goal.since -> panes
   were charged for 76%, 1.43M of it retroactive. (Recurrence: memory feedback_coordinator_pane_is_the_overrun.)
2. The live guard = an editable shared working tree. One unsaved edit killed worker 2; a branch checkout changes
   enforcement for every pane.
3. Lexical resource policy: GOAL_STATE matches substrings of any path -> worker 1 dead; the only "exception" was path
   obfuscation.
4. No reconcile: dead sessions' leases and finals count forever -> 1.42M phantom, and the goal reads exhausted.
5. Goal mode has no progress notion: a lease renews while authority remains; the session-envelope no-progress
   breaker (session_budget_guard.js:126) never applies to bound sessions; nothing caps one session's share of a goal.
6. No pre-model admission: refusals are bought as full model turns (ce-lifecycle L1 owns it).
7. Ad-hoc headless launches bypass the mission substrate, so no capsule, envelope or breaker applies.

## 3. Ownership
| Obligation | Class | Owner |
|---|---|---|
| Binding immutable at SessionStart, precedence, no mid-session cwd bind (observer isolation) | DEPENDENCY | ce-lifecycle L2 |
| Pre-model admission, terminal refusal | DEPENDENCY | ce-lifecycle L1 |
| Checkpoint reserve, CHECKPOINT state | DEPENDENCY | ce-lifecycle L3 |
| Lifecycle decide / successor / zero-Owner handoff | REUSE | ce-lifecycle L4 + gsd_mission arm + sweep |
| Context Rent meter, floor | DEPENDENCY | ctx-rent (its goal died of root cause 1 too) |
| Null-config resolution (A3b B2 core) | SUPERSEDED | Presence U6a (7e201298); the enforce flip is A4 W1c |
| Forecast / envelope admission | DEPENDENCY | A4 W1a (cost-collapse T2 autopsy+forecast) |
| GOAL_STATE narrowing + scoped grants (A3b B1 deliverable 1; A4 W1b delegates it) | OWN | R1 |
| Goal reconcile of dead-session reservations | OWN (gap) | R2 |
| Runtime pin / installer for guards | OWN (gap) | R3 |
| Goal-mode progress tripwire + per-session share of a goal | OWN (trigger); L3 owns the state it enters | R4 |
| Control-plane autopsy + Fault Capsule for bound sessions | OWN (extends mission_capsule.py, turns attribute) | R5 |
| Default envelope for unbound sessions, UNKNOWN fails closed at admit_route / loop_budget (C21) | OWN, after L2 | R6 |
| Relay re-admission (C25), canaries (C22-C24) | OWN | R7 |
| Goal refusal admits no closeout Read | CLOSE_NO_WORK (19240f98); R1 pins it with a test | -- |

No new system. Every unit extends session_budget_guard.js, mission_spend.py, ledger.py, mission_capsule.py or
gsd_mission.py.

## 4. Units (goal `ce-a3b-r`, root `C:\Users\User\Apps\pp-ce-a3b-r`, branch ce/a3b-r off a0c92f1b)
Each unit runs as a `gsd_mission arm` slim sonnet worker (capsule + envelope + breaker apply) with a packet <= 3K.
Progress contract per unit: the first durable progress is a commit or receipt row on ce/a3b-r. If none appears by 40%
of the unit cap, the unit stops, writes a capsule and goes to recompile. Receipts chain units; there is no
coordinator.

| Unit | Work | Durable progress / proof | Cap |
|---|---|---|---|
| R0 | Copy the 2 salvage files (sha256-checked), fix the 3 flaws, rerun, commit B0 | ENTRY_MATRIX regenerates byte-identical; a planted unbound site shows | 0.3M |
| R1 | Replace GOAL_STATE regex with a canonical resource set (realpath, case, separators, junctions of the goal-budget dir, index, `session-budget-*` files). Add Owner grants `goal-grant --owner` (TTY): subject sid, op, canonical resource + sha256, count, expiry, journal receipt, revocation. Retire the copy-by-name exception | V-GOAL-GRANT-*: exact grant passes; alias/relative/case/`..`/concat/junction/expired/reused/widened all deny; a spec whose name contains "goal-budget" is readable; control: real ledger write denied | 0.9M |
| R2 | `goal-reconcile`: a session with no live process (beacon) and an idle transcript settles at its transcript-measured actual and releases open leases/finals. Unreadable transcript = UNKNOWN, stays counted. A live session is never released. Run once on ce-a3b | V-GOAL-RECONCILE-*: dead -> SPENT+RELEASED; live -> untouched; unreadable -> UNKNOWN; ce-a3b used becomes 6.67M MEASURED | 0.6M |
| R3 | Runtime pin: `tools/runtime_install.py` stages the guard set, runs its suites, copies to `~/.claude/runtime/pp/<sha>/`, verifies hashes, swaps a pointer atomically and keeps the previous pointer for rollback. Dispatcher loads from the pointer; `/liveness` flags drift | V-RUNTIME-*: a syntax-broken working-tree guard does not change live behaviour; rollback restores; drift detected. ONE Owner command installs (HR-001) | 0.7M |
| R4 | Goal-mode progress tripwire: per-session spend since last progress (commit in root or receipt-path write declared in the packet) > first-progress envelope -> CHECKPOINT (L3 state; if L3 has not landed, the existing closeout path). Per-session ceiling = unit cap, so one session never inherits the goal. Context-growth-with-flat-progress halves the envelope | V-GOAL-PROGRESS-*: canary 1 (zero progress trips before 40%); canary 2 (receipt-only research unit does not trip); canary 3 (goal intact after a session hits its ceiling); canary 13 | 0.9M |
| R5 | `mission_spend.py goal-autopsy --goal X` (deterministic, exempt like goal-status): per-session calls, processed, pre-bind vs bound, refusals, phantom opens, git dirty. A bound session's terminal refusal / SessionEnd writes a Fault Capsule through mission_capsule.py | Canary 6 (exhausted goal inspectable from an unbound pane at zero goal spend); canary 7 (killed worker leaves a capsule); this incident's table reproduces byte-identical | 0.6M |
| R6 | After L2 lands: default envelope for unbound sessions from the measured floor; UNKNOWN fails closed at admit_route (processed None) and loop_budget (est 0) -- A3b B1 rest, C21 | V-GOAL extensions, RED first, admitted control per refusal | 1.2M |
| R7 | C25 relay re-admission; canaries C22-C24 (zero-activation in a separate project), 5 (observer, via L2), 8 (terminal refusal, via L1), 14-17; Cognitive CI clauses for the failure family; KV + UKDL (dedupe first) + CBR gates; retire RECEIPT exception prose, manual forensic steps and packet "commit after every unit" prose | `test_cognitive_economy_program.py --generation 2 --final` C21-C25 green; `/liveness` + router freshness gate | 1.0M + 0.6M |
| -- | reserve 0.8M; coordinator (this pane, after approval) 0.4M | | |

**Cap 8.6M**, goal `ce-a3b-r`. Order: R0 -> R1 -> R2 -> R5 -> R4 -> R3 -> (L2 landed) R6 -> R7. Two strikes per
unit, then stop and write state. A cap is never raised.

Dependency rule (deterministic): R6 and the L-dependent canaries start only when ce/lifecycle carries the V-LIFE-BIND /
V-LIFE-PREMODEL commits. Until then the mission is WAIT (zero hot, sweep wakes it). If L2 never lands, those rows end
DEFERRED, never PASS. R4 touches decideGoal like L3: whichever lands second rebases; L3 owns the state, R4 the trigger.

## 5. Self-hosting
This pane stays unbound in the main checkout. It never enters the new root, because that would charge its whole
transcript retroactively (root cause 1). After approval it does four things: declare `ce-a3b-r` (source = this file),
create the worktree, write the R0 packet, `gsd_mission arm` R0, then exit. Its own spend is measured by the
autopsy script against 0.4M; that limit is self-enforced, not guard-enforced (stated honestly). Every worker is a
mission, never a hand `claude -p`.

## 6. Security / rollback
Grants are Owner-TTY only, single-use by default, and journaled. Workers never write `~/.claude`. Kill switches:
`CPP_GOAL_GRANTS=0` (canonical deny, no grants), `CPP_GOAL_PROGRESS=0`, runtime pointer revert, every unit a
revertible micro-commit on ce/a3b-r, no push. pp-ce-a3b is kept read-only as forensic evidence.

## 7. Done-Gate
Every row of the prompt's gate maps to an R-unit proof, an L/ctx-rent dependency, or DEFERRED. PASS means MEASURED
from suites, journals or raw transcripts. A3b is done when C21-C25 are green on ce/a3b-r; rows blocked on L1/L2 are
reported DEFERRED with the dependency named. Economics table at close: processed, calls, pane vs worker share,
retroactive charge, phantom reservation, first-progress cost, Owner operations, before vs after.

## 8. Owner operations that remain
This approval. One `runtime_install.py` command at R3 (HR-001; it includes the dispatcher pointer and the SessionEnd
capsule entry). Nothing else.

## 9. Approval
Phrase: **"go a3b-r: 8.6M"** -- declares goal ce-a3b-r (8.6M, root pp-ce-a3b-r), accepts the ownership table
(B2 superseded by U6a; binding/premodel/reserve stay with ce-lifecycle; A4 W1b delegated here), and authorizes R0-R7.

## 10. Reforecast at approval (forecast drift changes execution; the cap is not raised)
The section-4 unit caps ignored the measured floor. Floor-derived cost = calls x ~115k (MEASURED: worker 2,
10 calls = 1,160,335). Re-costed: R0 1.0M, R1 2.0M, R2 1.2M, R5 1.2M, R4 1.5M, R3 1.2M, R6 1.8M, R7 2.0M = 11.9M
against the 8.6M cap. Decision: same order, envelopes take the floor-derived numbers, and the cap stays the firewall.
Expected reach inside 8.6M: R0, R1, R2, R5, R4 (about 7.1M) plus reserve. R3, R6 and R7 are DEFERRED unless earlier
units come in under forecast. Each receipt records actual vs forecast, and the next packet re-costs from the measured
unit. Already done below the model boundary by the coordinator: worktree, salvage copy (sha256 417432259B4EE2E0 /
2DF3C3DFB2F3FCDC, identical to pp-ce-a3b).
