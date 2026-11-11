# Ascension autopilot reorientation: structural-blocker discovery -- PLAN (2026-11-11, pane fa41bae9)

Status: PROPOSED, not armed. Backup of the inline plan given to the Owner. Supersedes RESEARCH-100-PLAN.md (4046acfc).
Owner brief (2026-11-11, typed): reorient the autopilot to discovering and removing shared structural blockers inside
the existing runtime and authority. 60M processed ceiling for diagnosis + pilots + integration, the rest frozen behind
value gates. No new Mission Runtime, scheduler or evaluation system. Before any new generation: the comparison of the
three best structural opportunities, their discriminating experiments and the first unblock to demonstrate.
Mode: EXECUTION (extends autopilot.py, planner brief, existing tools); not ULTRA (no new system).
Family-baseline note: the kobiicraft_mode baseline was matched on the word "modalidad"; NO APLICA (no Minecraft mode).

## 0. Safety action already taken
2026-11-11T20:26:24Z: kill switch `~/agora/ascension-autopilot/OFF` written (documented rollback, reversible with `rm`).
The running S28K worker (m-979b562fbce7, 20.5M authority) is NOT touched; it runs to its own checkpoint. OFF only stops
the autopilot from judging/planning/arming the next generation, so S28K's checkpoint is the transition point.

## 1. Reconciliation (M = measured, with source; P = prediction; A = assumption)
| Item | Value | Kind | Source (GEX44 t1-campaign unless noted) |
|---|---|---|---|
| KSR main frontier | 8,687 / 30,388 CERTIFIED; CNM 9,941; NO_COMPILE 5,453; FLAGS_SPLIT 3,447; NO_TARGET 2,858 | M | evidence/ksr-frontier/counters.json (252a2652, unchanged since 2026-10-29) |
| ksr-v5r-s25stage receipts (S26C) | 582 | M | s26c receipts; not in any headline (Owner: "une los 582" pending) |
| ksr-v5r-s25stage receipts (S26D) | 24 (23 nocompile + 1 cnm), judge AGREE | M | s26d/checkpoint_s26d.md; certify TRANSFORMED sources: lane frontier does not recognise them (Owner decision (a)) |
| S28K fwidth, running | dev 8 exact (4 canonical-arm); held-out 22 exact / 319 (11 canonical-arm); 0 certified yet | M (exact) / P (certs) | s28k/fwidth/summary_*.json; P4 certify.decide pending |
| Tennis frontier | 1,198 / 1,797 (1,139 C + 58 CXX, overlap removed) | M | evidence/frontier/counters.json (369509ac) |
| S27 Tennis | 0 new; T2 transfer 22 compile / 0 exact; T3 0/28; T4 38 compile / 0 exact; KSR held-out UNMEASURED | M | s27/checkpoint_s27.md |
| "117" | G-NT1 any-arm exact 699 - canonical 582, stage ksrmb-s25; diagnostic only | M | s25/checkpoint_s25.md |
| "87" | `?` repair, isolated variant, 336 KSR fns; global rewrite changes 178 certified fns -> fallback-only | M (diagnostic) | s25/checkpoint_s25.md |
| "141" | no source found this turn in s26/s26c/s26e | UNVERIFIED -- dropped | grep |
| 117 vs D3 37 vs fwidth 15 disjoint | different input pools (raw-compiles / NO_COMPILE / CNE); not checked by id | A | -- |
| 87 vs D3 45 `?`->char | overlap not measured | A | -- |
| Autopilot ledger | judge 1.72M + planner 3.04M measured; S28K 20.5M granted; PRIOR S27 200M | M | ledger.jsonl |
| Booked against 400M | 225.26M -> 174.74M left (not ~200M) | M | ledger + PRIOR_AUTHORITY |
| S27/S26D mission spend | 32.94M of its 200M authority (rest unused but booked, Owner decision) | M | ledger generation_closed |
| Tennis lane | PARKED: planner's S28T named a new profile without S26C conditions; policy refused | M | owner_queue.md |
| Known red, pre-existing | test_ksr_override rc=1 (S23 pin vs cmd_certify changed by S26C work) | M | s28k/ksr_override_diag.md |
No S26C rate is extrapolated anywhere below; candidate counts are BINARY_EXACT, never certificates.

## 2. Causal portfolio (shared causes, from existing rows; no new tokens spent on it)
| Blocker | Shared cause found | Population | Evidence |
|---|---|---|---|
| FLAGS_SPLIT | 6 objects only; both -sdata arms hold exclusive matches, so ksr_lane admits no arm for the whole object | 3,447 | s25/flags/census.json: 673 exact under some arm, 652 under the best single arm, excl sd0 21 / sd8 181, 16 arm switches in address order |
| No admissible arm (any state) | exact bytes produced by a mechanism land in an object with no admissible arm (FLAGS_SPLIT or NO_MATCH) | D3 37 of 60 exact; fwidth 15 of 30 exact | s26d/nocompile/findings.md; s28k/fwidth summaries (52 of 90 = 58% of the newest exacts stranded) |
| COMPILES_NO_MATCH | float width (target stfs/lfs/psq vs ours stfd/fctiwz) dominates INLINING_OR_CALLSHAPE 66/200 | 9,941 (applicability unmeasured) | s26d/cnm/gaps.md; S28K cohort A 382/639 with float evidence |
| COMPILES_NO_MATCH | grammar gaps with no operator: OTHER_CODEGEN 24, SAVEAREA 11 (35/200) | sample only | s26d/cnm/gaps.md |
| NO_COMPILE | missing types / prototypes / struct layout; compile movement rarely becomes bytes | 5,453 KSR; 494 Tennis | D3 60/1,147 exact (tiny fns via `?`->char); S27 T2/T4 0 exact |
| NO_TARGET | 2,837 of 2,858 recovered by S24X/S25 stage; residue moves into the classes above | 21 left without target | s25 G-NT1 |
| Certificate identity | certificates over transformed sources are outside the lane frontier | every source-transform lever | S26D decision (a) -- OWNER, not an opportunity I can act on |

## 3. The three opportunities compared
| | A. Object arm admissibility (TU ownership) | B. Float-width typing (fwidth) | C. Type recovery for NO_COMPILE |
|---|---|---|---|
| Hypothesis | FLAGS_SPLIT objects are concatenations of contiguous TUs, each with one -sdata recipe | a large share of CNM differs from target only by float/double/int width | missing type/prototype info is the first error of a large shared class |
| Demonstrated (M) | 673 BINARY_EXACT any arm (raw m2c source, existing recipes), 0 certified | held-out 22/319 exact (6.9%), 11 canonical-arm; certification pending S28K P4 | 60/1,147 exact (5.2%), 23 certified, mostly tiny fns; Tennis 0 exact |
| Reach | 3,447 + lifts stranded exacts of every other lever (58% of newest) | 9,941 KSR CNM + Tennis 164, applicability unmeasured | 5,453 + 494 |
| Source identity | raw source: no transformed-source question | transformed source: Owner decision (a) | transformed source: Owner decision (a) |
| Independent verifier | target-side relocation labels (SDA21 vs HALO_small; S26D D2 instrument with V0 validity) + certify.decide | unchanged certify.decide, pre/post controls, A2 negatives | same as B |
| Main risk | D2 was UNDETERMINED on stage object 801639EC (163 SD8 labels, 0 SD0); 80007EE0 shows 9 switches | half its exacts are stranded by A | compile movement without bytes (S27 T2/T4) |
| Discriminating cost | deterministic (relocs + existing sweep rows), est. 3-6M orchestration, 0 fresh | scan 0 LLM; pilot est. 8M | est. 6M |
| Certification path | new additive re-split stage: S26C conditions + Owner act | existing profile ksr-v5r-s25stage | existing profile |
Ranking: A first (largest measured stranded byte-exact set, raw source, multiplies B and C), B second (live in S28K;
its conversion depends on A), C third (lowest demonstrated byte yield; mainly feeds CNM).

## 4. Discriminating experiments (each frozen in a commit before the judged run)
A1 (first unblock to demonstrate): the 6 main-frontier FLAGS_SPLIT objects.
- Fit: the minimal contiguous segmentation consistent with the 202 exclusive matches (fit set).
- Held-out oracle: relocation-labelled fns NOT in the fit set; D2's frozen label rule and V0 check reused unchanged.
- Rivals: R1 per-fn interleaved recipes (labels alternate inside a segment); R2 the arm difference is another flag
  (labels disagree with exclusive matches -> V0 fails).
- Rule per object: H_SUPPORTED = V0 valid, >= 3 labelled held-out fns per side, 0 contradictions; REFUTED = V0 valid and
  >= 1 contradiction; else UNDETERMINED (counts as no progress).
- Measure (diagnostic only): BINARY_EXACT under per-segment arms; prediction <= 673, never a certificate.
- Expand: H_SUPPORTED on objects covering >= 50% of the 3,447 -> request (Owner) a re-split additive stage under all six
  S26C conditions. Stop: REFUTED on 80007EE0 and 800C4EE4 -> retire with reopen condition "a second independent TU-boundary
  signal". Cap 6M.
A2 (cheap join, same generation): of the 52 stranded exacts (D3 37, fwidth 15), how many sit in FLAGS_SPLIT vs NO_MATCH
  objects. Decides whether A's scope must include NO_MATCH objects. ~0.5M.
B1: deterministic float-evidence scan over the 9,941 main CNM and Tennis 164 (applicability count, 0 LLM), then a frozen
  200-fn held-out under the unchanged certifier only if applicability >= 10%. Cap 8M. Expansion: held-out certified >= 3%
  at <= 300K tokens/cert. Stop: < 1% held-out or certifier rejects claimed exacts.
C1: pair the S27/D3 NO_COMPILE->COMPILES fns with fwidth; tests whether compile movement converts to bytes. Cap 6M, after B1.
Tennis: no demonstrated byte mechanism; only B1's Tennis scan (information). Lane stays PARKED otherwise.

## 5. Autopilot changes (integration, in this pane, est. 4M; nothing goes live without the Owner)
1. Progress taxonomy replaces the boolean blank test. Per generation, exactly one of:
   CERT = new receipt rows, ids absent from all earlier receipts, re-derived by the judge via certify.decide;
   CAPABILITY = a new gate whose planted mutant is red AND a measured state change on a frozen held-out cohort,
     re-run by the judge;
   INFORMATION = a pre-registered hypothesis resolved SUPPORTED or REFUTED with its positive control seen, whose freeze
     commit is a git ancestor of the result commit (checked by autopilot.py with `git merge-base --is-ancestor`, not by
     the judge's text) and recorded in negative.jsonl or the portfolio;
   NONE = anything else (UNDETERMINED, INSTRUMENT_FAIL, docs-only or commit-only work).
   Stops: 3 consecutive NONE stops the lane (rule kept); 2 consecutive INFORMATION without CERT/CAPABILITY parks the lane
   for an Owner look ("research without conversion"); the judge's verdict must cite file shas; autopilot re-checks them.
2. Budget: UNLOCKED_CAP = booked at approval (225.26M) + 60M = 285.26M; the 114.74M above it is FROZEN. A frozen tranche
   is only ever requested (owner_queue) when a lever meets its expansion condition; never released by the autopilot.
   Same 25M per-generation and 80M/day caps.
3. Planner brief: the portfolio (section 2) + section 3/4 + mode rule: EXPLOIT a mechanism with a certified held-out
   result; EXPLORE (discriminating pilot) when no exploit lever meets its expansion condition. MethodGraph / Strategy Genome
   (recon-general modules/reconstruction_factory, 429b0126): REUSE as the search prior for B/C operators (graph learned
   from solved paths incl. S28K fwidth exacts; genome evolves operator orderings); not applicable to A (not a search).
   No parallel component. The portfolio is a file under evidence/ascension/, produced by the existing s26 portfolio tool
   (extend, not new).
4. Tests: test_autopilot.py gains checks for each taxonomy class (incl. a docs-only commit classified NONE, a result
   committed before its freeze classified NONE) and the frozen cap; mutants for each; gate must stay all-green.

## 6. Budget (processed tokens; fresh 0; USD 0)
| Item | Cap |
|---|---|
| This pane: reconciliation + comparison (done) + integration | 6M |
| A1 + A2 (next KSR generation after S28K checkpoint) | 6.5M |
| B1 (KSR + Tennis scan, pilot if gated) | 8M |
| C1 | 6M |
| Judge + planner calls (~6 x 1.5M) | 9M |
| Contingency / closeouts | 24.5M |
| Total | 60M |
S28K's 20.5M was granted before this plan and is outside the 60M.

## 7. Gates and governance
Production Reality Gate: the live system is the GEX44 cron autopilot; DONE for integration = gate green on GEX44 against
the real PP clone + a dry-tick on the S28K checkpoint showing the new classification; OFF stays until the Owner says
re-enable. Independent validators: the existing judge (fresh claude -p) per generation + one blind woz review of the
autopilot diff. Agent Teams: not used (no independent parallel work worth the overhead); one reviewer subagent only.
Micro-commits: one per change (taxonomy, cap, brief, tests). Knowledge Vault / UKDL: the stranded-exact pattern
("a lever's exacts can be invisible because object admissibility is per object") and the progress taxonomy enter UKDL
after A1 resolves, not before. Constitutive Baseline Ratchet: receipts sha 02c80ae3/8687 and every historical receipts
file re-proved byte-identical at each checkpoint; certifier, canonical ctx, headers untouched.
Not authorised by this plan: certification authority changes, re-split stage certification, budget beyond 60M,
canonical context, deploy, push, headline merges.

## 8. Owner decisions
1. Approve this plan (integration + the 60M ceiling as written)?
2. A1 as the first generation after S28K's checkpoint?
3. Pending, unchanged: transformed-source certificates (S26D a); "une los 582"; test_ksr_override re-pin vs revert.
