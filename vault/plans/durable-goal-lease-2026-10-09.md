# Durable Goal / Disposable Lease -- Reality Delta + Master Plan (2026-10-09)

Status: PROPOSED, awaiting one Owner approval. Read-only scan; this file is the only write.
Scanning pane: 42ce1ae6 (cwd = PP repo, bound to no goal).

## 1. Reality Delta (measured)

| item | value | source |
|---|---|---|
| PP HEAD | 717f3f69 (branch feature/knowledge-acquisition, dirty from other panes) | git log -1 |
| Recon HEAD (wt_keosdtk_home, branch keosdtk-home) | 4e7d8e7, unchanged since incident | git log |
| wt_cp50_c1 (branch cp50-c1) | also at 4e7d8e7, second worktree of the same repo | git worktree list |
| rf-p3b | cap 2,400,000; used 3,318,702 = settled 3,148,832 + 1 open hold 169,870 | goal journal (16 rows) |
| rf-p3b root | `_retired_rf-p3b`; that path does not exist on disk | index.json, Test-Path |
| rf-p3b2 | ALREADY EXISTS: cap 2.4M, used 0, root wt_keosdtk_home, source "P3b-2 send+promote (Owner 2026-10-09)" | journal (1 row) |
| sessions bound to rf-p3b2 | none | state/goal-binding |
| live process on wt_keosdtk_home | none; P3b missions m-1a112049e9c8 and m-4c2ceda008e1 are HALTED | mission records, Win32_Process |
| P3b dirty assets | untracked in the PP repo (gen3/packets/P3b1.md, route-P3b1.json, recon-reforecast/build_p3b_dossier.py, P3B-DOSSIER.md); P3B-RESUMPTION.md modified | git status |
| Programme authority | NONE standing. TRANCHE-CP50.md says "CEILING EXCEEDED" (9.88M+ against 6.8M), and each lease since then was funded by a separate Owner "fund it" | TRANCHE-CP50.md:51-63 |

### The ~975K attribution: CONFIRMED by mechanism, and the figure has since grown
- The reported 2,977,891 = 215,716 (c021de1c) + 1,786,835 (4c490fa2) + 975,340 (c2ae4b5c: 810,893 settled + 164,447 open).
- c2ae4b5c is the P3B coordinator. Its transcript lives under the PP-repo project dir (role = pane). Binding record
  `{"goal":"rf-p3b","source":"cwd","since_ts":"2026-10-09T20:45:13"}`. The ledger recorded a prebind of its earlier
  life as program capex (5,805,896 at the time; the transcript has 14,152,547 before the bind).
- After the bind: 8 calls, 1,315,455 processed (transcript, deduplicated by message.id). Ledger: 1,146,281 settled
  + 169,870 open = 1,316,151. They agree within 0.05%.
- What those calls did: edited the resumption file, wrote the status report, wrote the cap-raise script, declared
  rf-p3b2, and ran one P3b-2 pre-check (the control-drift finding). Classification: CONTROL_PLANE except one PROOF
  pre-check. Productive P3b work in them: 0.
- The resumption file itself records the trigger: "Coordinator slip: one Set-Location into the goal root to re-run
  the drill, reverted at once." Prospective binding makes the first mutating call under a root write an IMMUTABLE
  record, so one reverted Set-Location charged every later call of the pane.
- A second misattribution: c021de1c (cp50 C1 worker, 215,716) was settled into rf-p3b by the steward after the
  rebind, because it lived in the same worktree. 38caeaaf later limited settles to post-`since` spend.
- rf-p3b by cause: productive P3b1 1,786,835 (under its 2.4M cap) + control-plane 1,316,151 + foreign C1 215,716.
  **Without the misattribution, P3b1 fit its lease.**
- Instrument defect: `goal-autopsy` recomputes "bound" against the CURRENT roots, so after the root moved it
  reports bound=0 for every session. Rebinding falsifies the autopsy history.

### Recurrence (this is a class, not a one-off)
Lineages fragmented by rotation: ce-lifecycle -> -v -> -v2 -> -v3; caa-wake -> -t2 -> -t3; cp50-c1 -> -c1b;
rf-p3b -> rf-p3b2; ce-presence -> -2..-4. Coordinator cwd-binding incidents: caa-wake t2 ("control-pane
over-attribution"), ce-lifecycle-v2 (32.8M, memory), ce-unify scan (bound to ce-a3b-r), rf-p3b (1.32M).

### Root-cause answers
- Root exclusivity lives at goal level: `goal_declare` rejects overlapping roots, and the roots key the cwd binding
  (mission_spend.py:510-512, 663-672). There is no workspace object, only goal.roots.
- A successor is Owner-gated because the ledger has no lease concept. A goal is one immutable cap, so
  continuation = a new goal, and a new goal needs the root, which needs `--owner` on a TTY (review H1, :501-509).
- A lease cannot rotate automatically because no Programme envelope exists for it to draw from.
- Mission-level lineage already exists: renew_mission (gsd_mission.py:2192) has lineage_id/renewal/capsule-v2, and
  mission_steward settles stopped workers (R1) and proposes residuals (R3). The gap is only in the economic and
  workspace layers.
- Reconciliation looks manual for interactive panes: the steward settles mission workers only. A pane's open hold
  (c2ae4b5c 169,870) has no owner, because a pane's sid is not on its process command line.

### P3b-2 frontier: BLOCKED on an Owner semantic decision (genuine)
SB.impact on the real store: control_proven=5, but each of the 5 has drift=["match_py"] and
bundle_verifies=false. match.py changed in recon ac1f1ae (2026-10-04), after the 5 were sealed. The drill's IMPACT
gate did not catch it. The choice is (a) accept and re-judge the 5 through the bundle path (294 = 5 + 289), or
(b) revalidate the 5 against the current match.py first.

### Ownership / HR-NOVELTY-001
No new programme. Existing owners: mission_spend + provider_routing.GoalLedger = the single writer of economic
truth; gsd_mission (renewal, lineage, capsule-v2) + mission_steward = lifecycle; goal_binding.js +
session_budget_guard.js = binding and guard; ce-lifecycle-v3 (L3 econ installed, 37a5f3c0) and ce-a4 (16.6M, owns
compiler/lifecycle) = programme owners. Whether this lands as an amendment of ce-lifecycle-v3 or ce-a4 is decided
in E0, the same way as precedents A1-A3.

## 2. Architecture (minimum, additive)
1. Lease epochs in GoalLedger: ops `lease_open{lease, cap, forecast, programme}` / `lease_close{receipt}`. A legacy
   goal = one implicit lease. The cap of a closed lease is immutable. rf-p3b and rf-p3b2 become leases 1 and 2 of
   durable goal P3b through an additive `lineage` record; no row is rewritten.
2. Programme envelope: `goal-budget/programmes/<id>` journal, Owner-confirmed ONCE on a TTY. Executable authority =
   envelope - settled - open - UNKNOWN - protected reserves (proof, closeout, recovery). A successor lease inside
   the envelope needs no Owner. When the envelope is exhausted: checkpoint, AUTHORITY_REQUIRED, one notification.
3. Workspace lease: `goal-budget/workspaces/<ref>.json {path, holder:{goal,lease}, generation}`, changed only by
   compare-and-swap on generation. The guard rejects a mutating call whose bound generation is stale (zombie
   fencing). Roots stop being a goal property. index.json keeps a derived roots view for compatibility.
4. Binding precedence: explicit launch binding (mission env CPP_GOAL+lease) > mission record > workspace holder for
   sessions LAUNCHED inside the workspace > nothing. A pane that changes directory into a workspace is OBSERVE: reads
   are free, and a mutation is refused with the reason. It never writes a binding record. Kill switch kept.
5. Terminal reconciliation in the steward: settle measured spend and close holds of sessions proven terminal (pid
   whose cmdline carries the sid, or the host listing). Anything unproven -> UNKNOWN_RESERVED with a bounded TTL,
   then settle at the measured transcript total. Never released as free.
6. Atomic succession as an idempotent steward step journaled under a succession id: freeze, receipt, settle,
   release, residual (existing `.residual.md` / capsule-v2), lease_open, workspace CAS, renew_mission (PREPARED),
   launch by the sweep. Replay skips completed steps; a double race loses on CAS.
7. Predictive edge: the guard's warn becomes DRAIN when spent + forecast remaining + tail reserve > lease remainder
   (the route estimator already exists). DRAIN = checkpoint commit + receipt, then succession.
8. Event wake: worker SessionEnd/Stop calls the steward for its own mission. The 5-min sweep stays as recovery.
9. goal-autopsy: classify against the binding record and the workspace history, not current roots.

## 3. Execution order (after approval; EXECUTION mode, one worktree, never Set-Location into a goal root)
E0 ownership reconciliation (ce-lifecycle-v3 / ce-a4 plans) + preserve P3b dirty assets (commit to PP by pathspec).
E1 tests first (red paths): crossed-cap mutation, cwd rebinding, double successor, stale writer, reservation leak,
   unknown spend, crash at each of 7 succession points, lost event, context loss, authority exhaustion.
E2 1+2 (ledger leases, programme). E3 3+4 (workspace, binding, fencing). E4 5 (reconcile). E5 6+7+8 (succession,
   edge, wake). E6 9 + migration canary (P3b lineage + one cheap fixture goal; no spend disappears).
E7 P3b self-host: lineage P3b{L1=rf-p3b crossed, L2=rf-p3b2}, workspace holder = L2 gen 1, c2ae4b5c hold reconciled.
E8 P3b-2 under L2 (after the drift decision): preflight, RF_CURRENT_PHASE 3, send job 1/2, zero-hot wait,
   repatriate, judge, assemble, promote, verify PROVEN delta = accepted count with refused rows named.
E9 fresh-project canary (inherits without prompt mention), UKDL (HR/PR/TRAPS), CBR, retire the manual
   root-retirement / successor-declaration instructions (kept cold).
Live succession proof: the first real lease exhaustion after E7, or a staged 2-lease canary on a fixture goal.

## 4. Token budget (processed tokens; measured floors: worker call ~125-160k, main-pane call ~160-250k)
| line | lower | expected | safety | hard stop |
|---|---|---|---|---|
| incident already spent (rf-p3b) | 3,318,702 measured incl. 169,870 open (UNKNOWN until reconciled) | | | |
| this scan (pane 42ce1ae6) | ~1.0M, unmeasured | | | |
| architecture E0-E6 (6 leases) | 6.0M | 9.0M | 12.0M | 14.0M |
|   of which failure-injection / crash matrix | 1.2M | 2.0M | 2.8M | |
|   migration + canaries (E6, E9) | 0.8M | 1.3M | 2.0M | |
| P3b self-host E7 | 0.3M | 0.6M | 1.0M | |
| P3b-2 E8 (worker, zero-hot wait) | 1.2M | 1.8M | 2.4M | 2.4M = rf-p3b2 cap, already authorized |
| UKDL/CBR/retirement E9 | 0.5M | 0.9M | 1.3M | |
| proof reserve (protected) | | 1.0M | | |
| TOTAL new authority requested (excl. P3b-2) | 7.6M | 11.8M | 16.1M | 17.0M |
Model-call budget ~70-90 worker calls; semantic boundaries 6 leases + 1 P3b-2 lease.
Expected savings: 4 recorded cwd misattributions = 1.3M + 1.3M (rf-p3b, caa-wake t2 scale) + 32.8M (v2); 5
fragmented lineages each needed ~2-4 Owner commands and a main-pane relay at ~0.5-1.5M. Conservative avoidance
~1-2M per rotation event at the current rate of several per day. Confidence: LOW-MEDIUM. Two of four
previous leases ran past their stop (TRANCHE-CP50.md:71-76).

## 5. Owner decisions (genuine boundaries only)
D1 Capital: fund 17.0M hard stop for E0-E7+E9 as a Programme envelope (one TTY confirmation creates it; after that
   no further Owner mechanics), OR fund it inside ce-a4's remaining authority if E0 shows ce-a4 owns this.
D2 P3b-2 drift: (a) accept + re-judge the 5 through bundles, or (b) revalidate the 5 first.
