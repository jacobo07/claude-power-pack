---
program: gsdx-factory
status: PROPOSED (awaiting Owner approval in pane 530d9700, 2026-10-09)
covers: [gsdx-factory, mission-steward, stopped-worker-transition, ag1-recovery, call-unit-mismatch, floor-aware-estimate, dataset-obligation-ledger, tranche-gates, forgotten-mission]
depends-on: [gsdx-econ-recon-program-plan, cost-collapse, ctx-rent]
amends: vault/plans/gsdx-econ-recon-program-plan.md (sections 4, 6, 7, 11)
---

# gsdx-factory: steward, A-G1 recovery, recompiled program

## 1. Reality (2026-10-09 ~09:30 local, every line has a source)

| Fact | Value | Source / label |
|---|---|---|
| A-G1 core | `gsd_dossier dispose [--check]` + `tools/test_gsd_dispose.py`, commit 0573e610 | git log, MEASURED; DISPOSE_PASS=17/17 is the worker's claim, re-run at closeout |
| A-G1 residual | obligations.json (22 rows), dispositions.json, RECEIPT-AG1.json, RESUMPTION_FILE | worker RESUMPTION_FILE (uncommitted), MEASURED |
| Residual already composed | call #19 (5,155 output tokens) wrote all four artifacts in one PowerShell input; the guard refused it before it ran | transcript 6305f97c, salvage script, MEASURED |
| Physical model calls | 21 (not 27) | message.id dedup, MEASURED |
| What tripped | `session_budget_guard.js:119` compares TOOL calls (27) with an estimate expressed in MODEL calls (route envelope calls=16) | source read, DERIVED |
| Spend | 3,276,310 processed tokens; first call 121,144; mean 156K/call | transcript, MEASURED |
| Floor share | 21 x 121K = 2.54M = 78% of A-G1 spend is boot context | DERIVED |
| Estimate miss | admit used 113K x 13 x 1.2 = 1.77M, flat (no growth term); real growth 121K -> 175K over 21 calls | DERIVED |
| Goal ledger | used 3,761,830 = settled 2,922,765 + open 839,065; cap 8,000,000 | goal-status, MEASURED |
| Reservation truth | real spend 3.28M, so 0.36M of the open lease is unsettled spend and ~0.48M is unused headroom | DERIVED |
| Worker process | no claude.exe matches the session; last model call 22:58; mission record BLOCKED | MEASURED (process match is by cmdline, so "no match" is weak evidence) |
| cost-collapse | 57.1M used + 7.64M open of 69.8M; last worktree commit 42ac887c (E4a, 22:27); live tag cc-e4a-pre exists, no live E4a commit seen | MEASURED; chain liveness UNVERIFIED |
| GEX44 | load 0.58 / 20 cores, 54 GB available, 1.1 TB free, 1 claude process; clone carries ported gsd_mission fixes to 1872e9a1 | ssh probe, MEASURED |
| UWCP | no module of that name on either host | directory scan, MEASURED |
| Datasets | Optimization 1.md: 7,964 lines, 342 numbered items; Dataset 1.md: 12,832 lines, 414 numbered items; no markdown headings | ds_shape.py, MEASURED |

## 2. A-G1 call attribution (21 calls)

| Class | Calls | Which |
|---|---|---|
| Novelty | 5 | #4 dispose code, #6 test file, #17-#18 obligation probes, #19 closeout (paid, effect refused) |
| Assurance | 5 | #7-#8 test run + log, #14 test, #15 mutation drill, #16 commit |
| Repair after a real red test | 3 | #11-#13 |
| Orientation | 4 | #1 packet, #2 headings (+ a Bash call the bridge guard blocked), #3 plan + dossier, #5 drill tool |
| Tooling waste | 2 | #9 Edit refused by anti-thrash, #10 forced re-read |
| Stop-caused lifecycle | 2 | #20 RESUMPTION_FILE, #21 handoff |

Conclusion: ~17 calls were legitimate for this unit. The 13-call forecast left out the repair loop and the commit/closeout calls.
Avoidable calls: ~4 (#9, #10, #20, #21) plus the lost effect of #19.
The dominant cost is not the call count. It is the 121K boot floor x every call.
"Double the call estimate" would have budgeted the floor twice. The fix is to remove the floor (slim tiers) and the unit mismatch.

## 3. Ownership (extend, do not build beside)

| Need | Owner today | Gap -> unit |
|---|---|---|
| Durable mission with no model | live 5-min sweep in `tools/gsd_mission.py` over mission records + goal ledger (laptop task, GEX44 own clone) | has no transition for a worker STOPPED with an incomplete receipt -> S1 |
| Receipt -> successor | worker's last act arms its successor (chain); dependent admission 3f2ff5c4 on cost-collapse branch | a dead worker never performs its last act -> S1 arms from the packet's declared successor |
| Singleflight / no duplicate worker | `arm --supersedes` + `transition(expect_epoch, expect_state)` CAS + `--parallel-unit` conflict check | none; reused |
| Lease reconciliation | GoalLedger `renew` settles a sid at its cumulative measured spend | nothing settles a stopped sid -> S1 settles at transcript-measured spend |
| Call accounting | session_budget_guard.js (tool calls) vs route envelope (model calls) | unit mismatch -> S2 |
| Forecast | route_admission estimator, flat per-call | no growth term, no floor by profile -> S3 (worktree, rides cost-collapse E4b convergence) |
| Paid cognition lost on refusal | E3G "packet-declared receipt survives the stop" (cost-collapse branch) | refused tool inputs are not kept -> S1 salvage artifact |
| Forgotten mission | nothing | ACTIVE goal, no RUNNING/ADMISSIBLE/WAITING record for 30 min -> S1 incident |
| Proof reuse, ContextImage, CBR, KME-L lab | verified_reuse.py, gsd_dossier, tower_capsule.py, wiki/tools/kme_replay.py | unchanged from the parent plan, section 4 |
| Dataset disposition gate | A-G1's own `dispose --check` | dogfood: the ledger is gated by it -> L1 |

## 4. Units (EXECUTION mode; ULTRA only on a new architectural fork)

- R0 A-G1 close, ZERO_MODEL: replay the salvaged #19 command (reviewed in this pane: worktree-only writes, pathspec commits, no push) under a script that pins its sha256. Re-run the dispose gate and the V-DISPOSE suite; the receipt records the real counts, including an honest FAIL if the canary fails. Settle the stopped sid at 3,276,310 and close its lease. Mark m-fa18e2b8b44d terminal with the receipt. Cost: 1-2 calls of this pane.
- S1 stopped-worker transition in the live sweep (deterministic, no model). Order: STOPPED/BLOCKED + no canonical receipt -> settle lease at measured -> fallback partial receipt (git log, transcript call/token counts, refused inputs saved to `salvage/`) -> residual packet (original packet + RESUMPTION_FILE + salvage) -> arm/envelope/admit at the cheapest profile the packet allows -> launch by the normal sweep. Also covers the forgotten-mission incident and arming a packet's declared successor from its receipt. Gate V-STEWARD-* covers both poles. Drills: duplicate receipt gives one launch; sweep restart mid-transition is idempotent; a missing transcript leaves the residual UNKNOWN and nothing is settled. Est. 2.0M, top-level, once.
- S2 call-unit fix: the guard counts model calls (message.id) for the divergence breaker, and tool calls become a separate, wider breaker. The mutation drill runs on an isolated copy (the hook is live-loaded). Est. 0.8M, slim-t2 if S4 passes.
- S3 floor-aware forecast: per-profile floor + measured growth (calls_err), which is what E3C1 was asked to add. If E4b has not converged when S3 is ready, S3 joins that chain instead of duplicating it. Est. 0.6M.
- S4 slim-tier dominator probe: can slim-t2 / slim-t1 run a packet with tools + guard (8.8K-13.5K floor vs 121K)? Every later unit's price depends on this one answer. Est. 0.3M.
- L1 Dataset Obligation Ledger: deterministic extraction of the 756 numbered lines -> stable ids -> clustering against owners (D2A family engine `--family-file --repo-evidence`) -> batched slim disposition into the closed vocabulary -> `dispose --check` must exit 0 (OMITTED is unrepresentable: undisposed fails). A speculative row gets IMPLEMENT_EXPERIMENT with its falsifier written in the row. Est. 3-5M.
- A-G2..A-G5 + Part B recompiled from L1 and S4: never re-armed from stale packets. Each unit carries a semantic-boundary count; its forecast comes from S3. GEX44 is the primary plane for Part B (KSR / reconstruction live there and run on the second account's quota); the laptop keeps Part A (it edits the live control plane). Code moves between hosts as git bundles over ssh to our own clone, never pushed to a remote.
- Economics: each unit's receipt carries calls, boundaries, floor, tier, attribution (section 2 vocabulary) and avoidable calls. Learning-curve gate: A-G2 (same class as A-G1: one tool + V-gate + real input) must cost less per verified gate than A-G1's 3.28M / 17 gates, or the receipt states why the two are not comparable.
- Optimizer moratorium: self-optimization spend is capped at 15% of program spend. A candidate needs CAPEX < 1/3 of its credible saving, and a replayed or production before/after, to be promoted.

## 5. Forecast and authority

- Remaining program, expected 55-70M (parent plan ~60-65M; plus ~6M of steward/ledger work; minus slim-tier savings if S4 passes). Lower bound ~40M. Safety 100M. Hard stop (airbag) 140M.
- One Owner action, ever, for this program: `python tools/mission_spend.py goal-declare --goal gsdx-factory --cap 100000000 --source vault/plans/gsdx-steward-recovery-plan.md --owner`. A cap can only be raised from an interactive Owner terminal; that is a deliberate security boundary, and an agent signing its own spending authority is exactly what it prevents. Tranches T1..T4 become steward-side admission gates: the next tranche opens only on receipt-verified progress and a fresh forecast. The ledger cap stays the airbag.
- Wake the Owner only for: total authority beyond 100M, scope change (full WSR stays out of scope), or a physical-reality dependency.
