# PCC continuation plan, 2026-10-14 (awaiting Owner approval)

Approval surface: the copy of this plan shown inline in chat. This file exists so a fresh session can pick it up.
Source prompt: Owner /cpp-gsd-long PCC continuation, 2026-10-14 (26 second-order requirements N01-N26).

## 1. Verified reality (read-only scan, 2026-10-14)

- Worktree `C:\Users\User\Apps\pp-gsdx-pcc`, branch `gsdx/pcc`, HEAD `46d470e1` (WU-P5 receipt). The branch has 115
  commits that feature/knowledge-acquisition lacks, and is 503 commits behind it.
- Dirty: `M vault/progress.md`, `?? LEARNINGS_PENDING.md`. Both are hook artefacts and are not PCC work; they stay
  untouched.
- Workers: none for PCC. Phase 5 mission m-ee676522b2fd is HALTED, "host lists session done". 12 claude.exe running,
  7.2 GB RAM free. 14 other non-terminal missions belong to other programmes; none writes this worktree.
- The Owner's report holds: Phase 5 suites 11/11, 14/14, 10/10, 12/12; regression 48/48, 28/28, 40/40, 26/26;
  drills 9 of 10 KILLED on Windows; d3 UNRUN; `test_gsd_x_goal_mutation.py` UNRUN for Phase 5. Source:
  `packets/WU-P5-receipt.md`.
- **Phase 5 epistemic status: CLOSED-WINDOWS / CROSS-PLATFORM-PENDING.**

## 2. Audit of W0-W4 (what was found)

| # | Finding | Evidence | Verdict |
|---|---|---|---|
| A1 | D25 (speculation) and D26 (racing): Phase 3 says "executed ... closed by Phase 4", but both rows are still OPEN. Nothing speculative or racing ever executes. | DENOMINATOR D25/D26 | Phase 3/4 closure overstated. Reopened, assigned to W7 |
| A2 | D11 proof algebra is pure functions only. No engine path evaluates a non-AND claim; non-AND always re-runs. | DENOMINATOR D11 | Correct but unwired. EXTEND in 5.2 |
| A3 | D23: no sweep path records `candidate.promoted` | DENOMINATOR D23 | Substrate only. Production path is W7 |
| A4 | `proof.environment_fingerprint` hashes python version, OS, machine and tool NAMES only. No tool versions, lock state or runtime. | `modules/gsd_x/goal/proof.py:347-349` | Weaker than N17. REPAIR in 5.2 |
| A5 | The certificate's six premises do not bind gate implementation, adapter, policy or validator VERSION. A defective authority cannot revoke anything. | `proof.py:195` | N01/N02/N05 missing. BUILD in 5.2 |
| A6 | Phase 4 invalidation evidence comes from the Windows plane only; frontier has Linux x9 | 04-VERIFICATION.md | Platform proof, not portability proof. Recorded in 5.1 |
| A7 | `test_gsd_x_goal_mutation.py` mutates LIVE modules (journal + sha256 restore). Phase 4 left `judge.py` mutated after a kill. `tools/mutation_drill.py` already provides isolated copy + control. | `tools/test_gsd_x_goal_mutation.py:370-528` | Avoidable live dependency. PORT to the drill substrate in 5.1 |
| A8 | R10: 17 gsd_x/goal units frozen as liveness debt | DENOMINATOR R10 | Still open. Wire as each wave touches them; closes in the final wave |
| A9 | Judge VALIDATE re-derives through `inherit.plan` | D15, 970ea212 | Strong base for N16. Forgery attacks still need to be driven |
| A10 | `tools/gsdx_pcc_done.py` does not exist | file probe | BUILD as a question-registry gate (section 7) |

Strong enough to keep: GoalLog-as-only-store (D44), frontier/scheduler core (D04-D09, D27, D28, D33, D34, Linux
x9), certificate production (D13), fresh islands (D39), review A->B->A (R05), gate provider R01.

## 3. Mode verdict (ROI)

- Campaign: /cpp-gsd-long as a **chain of compiled Work-Unit packets**, one per wave, on Sonnet workers. Plain
  `/gsd-autonomous` relaunches spent 11 of 14 calls on boot (memory feedback_relaunch_worker_compiled_unit_not_gsd).
- Chain: `tools/gsdx_chain.py` + tick task, as CCR Stage 2 used it. Each packet is compiled when its predecessor's
  receipt lands, and sized from that predecessor's measured burn.
- This pane does not coordinate. Coordinator spend cap is 3M for the whole campaign: act on chain_alert only
  (memory feedback_coordinator_pane_is_the_overrun).
- EXECUTION by default. PLAN MODE inside 5.2 (authority-bound certificate schema + revocation projection) and W6
  (scoped adapter authority model).
- **ULTRA-PLAN: none at plan time.** Revocation and lineage fit the existing append-only GoalLog (D44) as events +
  projection. That is a bounded design, not an open foundation. Re-open only if 5.2 finds authority versions cannot
  enter certificate identity without breaking D43 legacy replay.

## 4. Ownership map (REUSE / EXTEND / CONNECT / BUILD / RETIRE)

| Capability | Decision | Owner |
|---|---|---|
| Revocation, lineage, authority monotonicity | EXTEND | `proof.py` premises (add authority versions) + GoalLog events + projection. No second store. Graphify only as a read index, never the store |
| Forgery resistance | EXTEND | `judge.py` derives security-critical fields itself; builder fields are claims |
| Environment equivalence | EXTEND | First search tower/applicability/capability_runtime for an existing owner; otherwise `proof.environment_fingerprint` becomes the canonical module |
| Platform proof vs portability, Linux routing | EXTEND | frontier resource classes (D27) + receipt fields; executor GEX44 |
| Mutant farm + dispositions | EXTEND | `tools/mutation_drill.py` + `vault/governance/mutation_ratchet.json`. RETIRE live mode from all PCC paths (R04) |
| Adapters, scoped authority, dynamic frontier | EXTEND | change_impact owner (D21) |
| Cancellation, fairness, prediction error | EXTEND | `frontier.py` / `epoch.py` |
| Continuation validity | EXTEND/CONNECT | `brief.py` + mission card; SSM connected if the scan finds a live owner |
| Observatory, economics, rent | BUILD | projection over GoalLog (D02/D35/D36) |
| Sentinels, trust descent/recovery | BUILD | policy inside inherit/judge; maturity as append-only events (D38) |
| Baseline ratchet | EXTEND | `tools/family_baseline.py` family `software_construction` (R09) |
| Final gate | BUILD | `tools/gsdx_pcc_done.py`, question registry |

## 5. Denominator: old OPEN rows + N01-N26 mapped to waves

| Wave (GSD phase) | Old rows | New requirements |
|---|---|---|
| 5.1 W4 closure | D15 d3, R11 (prep) | N18 (route), N19 (record), mutation suite hermetic (A7) |
| 5.2 Trust core | D11 (wire) | N01, N02, N05, N16, N17, N19 (semantics), N23 (ledger seed) |
| 6 W5 Mutant farm | D18, D19, R04, R11 | N09 (farm-level), N13 OBSERVE start, N14, N15, N18 (exec) |
| 7 W6 Adapters + Elixir | D21, D22, D37 (adapter), D38, D41, R06, R07, R08 | N03, N04, N20, N21 |
| 8 W7 Continuation + scheduling | D23 (prod), D25, D26, D29-D32 | N09, N10, N24 |
| 9 W8 Observatory | D02, D24, D35, D36, D37, D40, D46 | N07, N11, N12, N25, N13 SHADOW compare |
| 10 W9 Trust control | (historical incident replay) | N06, N22, N23 (complete), revocation cascade live, trust recovery |
| 11 W10 Reality + ratchet | D03, D42, D47, R03, R09, R10 | N08 (scoped), N13 self-close, N26, fresh agent, done-gate, meta-analysis |

Order rationale: the trust core (5.2) changes the certificate schema that every later wave emits. Doing it before
W5 means one migration instead of five.

## 6. Waves: done-gates, Production Reality boundary, budget

Per-call floor measured at P5: 29.4M / 243 calls = 121K/call on Sonnet. Admission floor 118K. Calls below are
counted from denominator items x (RED + fix + verify + commit), not copied from earlier phases.

| Wave | Key done-gate (machine) | Reality boundary | Calls | Target | Cutoff | Linux |
|---|---|---|---|---|---|---|
| 5.1 | d3 + goal-mutation 58/58 on GEX44, bound to 46d470e1 + toolchain; ported suite passes in isolated copy with live tree sha-unchanged | real GEX44 run | 55 | 6.5M | 9M | d3, suite (~10 min) |
| 5.2 | RED: revoked authority keeps cert invalid with unchanged bytes; inherited authority > original refused; 8 forgery attacks refused; env drift invalidates | real certificate + real judge VALIDATE/REPLAY | 150 | 18M | 24M | env-equivalence pair |
| 6 | effective kills / faithful mutants; timeout/crash/setup != KILLED; canonical sha intact; R11 incumbent measured | real parallel farm on real candidate | 175 | 21M | 29M | R11 incumbent + farm leg |
| 7 | Elixir SHADOW vs full `mix test`; 12 fault injections each execute the fallback; partial fallback proven | real pilot worktree + real mix | 240 | 29M | 40M | optional |
| 8 | stale completion cannot satisfy N+1; starvation detector red; continuation staleness classified | real multi-job dispatch + real resume | 165 | 20M | 27M | - |
| 9 | metric projections over real GoalLog; time-saved vs time-shifted split; rent + Net TTPD | PCC's own construction log | 145 | 17.5M | 24M | - |
| 10 | sentinel catches a seeded escape -> downgrade + revocation cascade; trust re-earned | real sentinel full run | 165 | 20M | 27M | sentinel leg |
| 11 | `gsdx_pcc_done.py` exit 0; fresh-agent PASS; fresh Goal inherits laws unprompted | real future Goal | 165 | 20M | 27M | portability pair |
| **Total** | | | **1,260** | **152M** | **programme cap 175M** | |

- Per-wave cutoffs are stop-losses; the programme cap (175M) is lower than their sum (207M).
- Contingency: 23M (15 %), released only by recompiling the remaining frontier, never by default.
- UNKNOWN, bounded: the Elixir semantic surface (W7) is bounded by its 40M cutoff. If exceeded, the unsupported
  classes fall back to FULL and are recorded as Proof Optimization Debt, not built.
- Reviewer cost: one independent adversarial review per wave (~1.5-2.5M, Opus), included above.
- Coordinator: 3M cap across the campaign.

## 7. Done-gate design

`tools/gsdx_pcc_done.py` lands in 5.2 as a working gate over a question registry. It holds the prompt's ~40
questions, each mapped to a V-gate id + evidence file + plane. It exits 1 while any question is OPEN, UNKNOWN or
single-plane where portability is claimed. That makes it the honest progress meter from day one, and it is
strengthened each wave. Final PASS also requires: liveness exit 0, DENOMINATOR fully dispositioned, `family_baseline
verify software_construction` exit 0, fresh-agent report, clean worktree.

## 8. Self-host, shadow, ratchet

- From W5: each wave's work units are emitted as a real Goal in a dedicated goals root
  (`.planning/workstreams/gsdx-pcc/selfhost`). OBSERVE in W5, SHADOW-plan compare in W8-W9, trusted subsets only
  where earned. Never self-certifying: the judge stays independent.
- Ratchet: universal laws (UNKNOWN escalates, explicit inheritance, monotonic authority, revocation, lineage,
  sentinels, conservative fallback, candidate binding, independent judge, Production Reality) go into
  `software_construction` B0. Scoped accelerators carry applicability (e.g. "Elixir static module reachability,
  PROBATION"). Promotion wider than the family stops at PENDING_OWNER (D-O2).

## 9. Micro-commits and continuation

- One verified semantic delta per commit, RED first, `git commit -F`, verify the subject after each commit, never
  push.
- Each wave ends with EVIDENCE.md + receipt + DENOMINATOR rows moved + UKDL HR/PR/T evaluation.
- Continuation: the chain launches the next packet when the receipt lands. Context walls rotate to a fresh session
  with the mission card. Stop only on: final gate PASS, programme cap, or a genuine Owner decision. Any blocker is
  written into the row and the chain continues with unblocked work.
- Two identical failures -> pivot (Regla 12). A unit at >1.5x its target twice -> chain_alert to Owner.

## 10. Risks

- Laptop RAM (7.2 GB free now): d3 and the mutation suite already died to the reaper. Linux legs go to GEX44 by
  design.
- Auto mode may refuse an ssh transfer from a worker (seen in CCR Stage 3). 5.1 probes that first. If refused, the
  coordinator runs the Linux leg (bounded, inside the 3M cap) and records it.
- The worktree is 503 commits behind the main branch, so the final merge may conflict in `modules/gsd_x`.
  Rebase/merge is planned in W10 with full regression, not mid-campaign.
</content>
</invoke>
