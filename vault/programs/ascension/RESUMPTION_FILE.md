# RESUMPTION — Solver Architecture Ascension (Tennis t1 reconstruction, GEX44)

**Identity.** Owner addendum "solver architecture ascension / 10-of-10 evidence gate", approved 2026-10-31 ("APRUEBO ASCENSION"). The work runs on GEX44.
- Plan, authoritative: `/home/kobii/missions/gen3-pp/vault/programs/gsdx-factory-2/ASCENSION-PLAN.md` (branch `mission/gen3`).
- Code: `/home/kobii/missions/t1-campaign` (branch `t1/campaign`).
- Reach GEX44 with an LF, no-BOM temp script: `cmd /c "ssh -o BatchMode=yes gex44 bash -s < file"`. Export the sweep env (`CPP_CLAUDE_EXE=/home/kobii/.local/bin/claude`, `PATH=/home/kobii/.local/bin:...`) and run the PP tools from `~/.claude/skills/claude-power-pack`.

**CURRENT (2026-11-05 ~14:35 UTC, session 95e69b3d) — read this first.**
- Owner /cpp-gsd-long brief "Global Constraint Closure, Exact Tail Compression, Generative Population Collapse" = **Generation S13**.
  - Brief stored VERBATIM (no condensation; S12C lost §XXIX that way) in gen3 `vault/programs/gsdx-factory-2/S13-BRIEF-VERBATIM.md` (40 sections, body sha256 321961cda6f6e669), plus `S13-COORDINATOR-NOTES.md` (scan, cohort correction, paths, budget) and the iteration methodology copy. gen3 commit `7a5e1468`.
  - S12C milestone archived under `.planning/milestones/s12c-closed-partial-*` with CLOSE-NOTE (phase 8 unmet: gates 11, 14); new 8-phase milestone W0..W7, GSD 0/8.
- **Mission m-84f2641865dd**: 30M processed, 0 top-ups, 12 cycles / 24 h, USD 0, workset t1. Launched 14:33:51Z (INITIAL), worker ca4ef299 working W0.
- **S12C m-9dc71428699e closed PARTIALLY PROVEN**: frontier 1121/1797, compiler pin cc38fa03, 15 pre-S12C reds classified; 46.4M/60M; envelope ended 13:54Z; owner hold "never launch".
- Coordinator duties: watch `topology --mission m-84f2641865dd`; at the S13 closeout land S12C + S13 `promotions.json` together (PP UKDL has a dirty concurrent hunk on the laptop: land via private index) and run the fresh-inheritance check; judge the 25 gates.
- Trap: `claude ps` on GEX44 is not a listing; it ran a model turn.

**Earlier (2026-11-04 ~14:00 UTC, session 95e69b3d).**
- The Owner's /cpp-gsd-long brief "GSD X Reconstruction Factory: Convergence and First Population Collapse" = **Generation S12C**. It supersedes the unlaunched S12.
  - Brief condensed faithfully into gen3 `vault/programs/gsdx-factory-2/S12C-CONVERGENCE-BRIEF.md`: 18-item done-gate, 6 mission terms.
  - gen3 commit `86da3c29` = brief + `S12C-PHASES.md` + ASCENSION-PLAN section + GSD milestone (8 phases W0..W5; GSD was NO_PHASES, scaffold → OK 0/8; old v1 files archived under `.planning/milestones/auto-archived-20261104T145409`).
- **Mission m-9dc71428699e**: cwd gen3-pp, workset t1 product, 12 cycles / 24 h, authority 60M processed tokens, 0 top-ups, model USD $0, no push, worker never edits the PP.
  - Launched by the sweep 13:59:09Z; worker d8280bc4 acked and rehydrated.
  - The brief's "300k model tokens" is not the breaker's unit (processed = input + cache + output; S11H's 2 epochs = 11.6M), so cycles and hours are the binding budget. Recorded in the brief.
  - `worker_marker_refused` (the retired v2 marker requires a leading '/') is benign for Ralph missions.
- m-fc7047a29f01 (S12, never launched) and m-a9d8915ae366 (recon general, done) are under owner hold "never launch".
- Coordinator duties:
  - watch the epochs (`gsd_mission.py topology --mission m-9dc71428699e`);
  - land KV/UKDL/baseline candidates from t1 `evidence/ascension/s12c/promotions.json` into the PP;
  - judge the closeout's 18-item done-gate.

**Earlier (2026-11-04 ~10:00 UTC).**
- Owner "hazlo tú y prepara la siguiente generación". Public PRs: #11 squash-merged (`36e83ca8`). #12 had a private host path in its spec (`/home/kobii/missions/t1-campaign`, found by a pattern scan with a 1/1 control; recon_public_gate does not check paths). Scrubbed and squashed to 1 commit `58c3ebe6` (force-push with lease). GitHub never synced #12's head and reopen failed, so #12 was closed and **#13** was merged (`abc63bb9`). Public main = 70c2fde4 + 2 commits, 201 files, 0 hits. Residue: closed #12 still serves old commit 429b0126 (path visible) via refs/pull/12; only GitHub support can purge it. /tmp/pp-kunit removed from GEX44.
- S11H final: t1 `2091cdad` R4 certified 5 more; **frontier 1100** = C 1086 + CXX 14.
- **S12 PREPARED, not launched:** proposal `S12-PLAN-PROPOSAL.md` (this dir). Prompt `/tmp/s12_command.txt` on GEX44 (sha 3055fd6d...). `retarget` applied live to m-fc7047a29f01 (first production use; seq 19; still held at checkpoint, worker stopped). On Owner "y": write the S12 section into gen3 ASCENSION-PLAN.md, run mission_topup budget to 50M, then `checkpoint --clear`.

**Earlier CURRENT (2026-11-03 ~15:45 UTC).**
- Owner (publish): "1 + 2" = full lineage stays PRIVATE; curated public export only. Done: PR jacobo07/claude-power-pack#11, branch `export/s11-mission-policy` @ `2ef46df6` off public main 70c2fde4 (mission_policy + heldout_release + 2 tests + owner-gate fixture; fn_80222480/80222ED8 -> fn_00000A01/B02, "Tennis" + local paths scrubbed; MPOL 52/52, HOLDOUT 10/10 in the export worktree; secret scan 0 hits / control 1/1). Pivot autonomy (gsd_mission.py, ~35 deps absent on public main) NOT exportable without the lineage. Export worktree: scratchpad `pp-public-export`; older clean worktree `C:/Users/User/Apps/pp-public-s11` (gsdx/s11-mission-autonomy @ 70c2fde4) is superseded, not deleted.
- Owner (H2): KEEP 20. Record the static-scan exposure (H2x vptr/this-call scan touched 2 members, raw feature only) as an incident; debt = corpus scans exclude H2 by structure.
- recon-general m-a9d8915ae366: CHECKPOINT_COMPLETE "ready for public gate", but `--range 70c2fde4..HEAD` (16 commits) was VIOLATIONS {TITLE: 1}: private-target module names in tools/rf_parity.py. Coordinator replaced them with `TARGET_COUNT = 21` and amended the unpushed PARITY commit 6e723398 -> **429b0126** (factory 33/33; range CLEAN; per-commit CLEAN 16/16). Pushed `recon-factory/general` to GitHub, **PR #12**. Mission left parked at its checkpoint (no worker, no spend).
- m-fc7047a29f01: CHECKPOINT_COMPLETE "S11H harvest done"; parked.
- K unit: (a)(b)(c) committed `d2c61492` (S11-INCIDENTS.md, UKDL S10-S11H block, prompt-debt registry). NOT pushed: origin is the PUBLIC repo and the lineage stays private (Owner 2026-11-03). (d) halted-on-cycles = sweep refused renewal on NO_PHASES (log 11:48:40Z), owned by gsd-x-universal (other pane 37b2abaf/0f80c09a). `retarget` verb `7c1fecfc` (review WARNING, 4 findings fixed; V-RETARGET 14/14, drills 6/6).
- **GEX44 DEPLOYED 2026-11-03 19:55:08Z (Owner "y")**: live PP clone ce2414c1 -> **bc815b36** = canary/k-unit in the bare repo (ce2414c1 + e0252b2f [37b2abaf] + 73b3027b [0f80c09a] + bc815b36 [7c1fecfc minus the ascension docs]). Canary worktree /tmp/pp-kunit, sweep env: RETARGET 14/14 + drills 6/6, PRE 23/23, SCAFFOLD 14/14, MPOL 52/52, PIVOT 29/29 + drills, HOLDOUT 10/10, S9_WAIT 31/31, S6 72/72, EPOCH 111/111, MC 242/242. HR-2 real-host smoke /tmp/smoke_kunit.py 5/5 (real GSD NO_PHASES refuse -> scaffold -> ok; CLI retarget; real host 307 rows, unproven owner refused; hash-only ledger). ff done only when no python3 ran live-clone gsd_* code (predicate proven by a sweep-shaped control; ce5 cron runs its own copy). First post-deploy agora pass 19:59:51-52Z: exit 0, outcome ran, fail_streak 0, 0 errors. Rollback: `git -C ~/.claude/skills/claude-power-pack reset --keep ce2414c1`. Live dirty files quality_audit.py + terminal_slots.json untouched.
- Pre-existing on public main: vault/evidence/two-pane-exactness/*.json carry C:\Users\User paths, .planning/* carry /home/kobii paths (low risk, not touched).

**Earlier CURRENT (2026-11-03 14:15 UTC).**
- S11 CLOSED without H2 (Owner D1: no waiver, no control swap; t1 `58082c73`). H2 sealed, unread, unspent (manifest sha `922f214e`).
- Frontier unique 1095/1797 = C 1086 + CXX 9, overlap 0 (H0, t1 `c3dc137f`). fn_80222480 is already CERTIFIED_CXX (S10b fixture); its 98.9 is only the raw-m2c control.
- S11H (Owner "y", gen3 `3955257f`, plan backup `S11H-PLAN-PROPOSAL.md`): H0/H1/H2x done (t1 `c3dc137f`, `bba49802`, `6fbf44f7`, handoff `474670d1`). Mission m-f0b595fd509f HALTED on max-cycles 24; successor **m-fc7047a29f01** launched 14:10:39Z (authority 19.8M = remainder of the 80M, max-cycles 16, pivot Gen2 on), continuing at H3.
- PP live on GEX44 `ce2414c1` (Gen2: typed receipts, authority objects, evidence-weighted pivots; D1-D3 + P5). Laptop `23691d01`. Rollback `git reset --keep db6bc9c6`.
- Next: watch m-fc7047a29f01 H3->S; at its CHECKPOINT_COMPLETE review s11h/closeout.md. Coordinator debt: K unit (KV incidents, UKDL, CBR, Prompt Debt registry), U (upstream desk audit), `retarget` CLI for a generation's launch prompt (gap found today).

**State (sealed 2026-11-01 ~15:10 UTC).**
- Waves R0, M0 and S1-S8 are CLOSED. No mission is active in gen3-pp. The last one, m-f9560b5e8f1f, is HALTED with no_progress after S8 closed.
- Frontier **1086/1797** (`FRONTIER_CHECK OK`).
- Maturity **2/10**:
  - D01, D02 and D09 are at 2;
  - D04, D05, D07 and D11 are at 10, but D11 rests on S6's weak 21-vs-20 result.
- Master gate `tools/test_recon_fabric_ascension.py`: 5/6, red only on maturity.
- Model spend since Gen4: ~$331 of the $471.10 authority.
- Coherence anchor: t1 `62e108c6`, gen3 `ddd4d95a`, PP clone on GEX44 `ac18e7a9`. Nothing pushed.

**Active decisions.**
- The current method is exhausted: the solver compiles but does not reach exact. S8 made 73 functions compile, and both deterministic search and the model failed to close any of them (0/27).
- The Owner was asked: plan a new method (compiler-causality operators for near-exact residuals), or close the programme? **Unanswered.**

**Next 3 actions.**
1. Get the Owner's answer to that question.
2. If the answer is plan: write a wave S9 plan in ASCENSION-PLAN.md that targets the residuals S8 left (the 26 IMPROVED, the 73 new compiles) with D04 relations turned into operators. Arm a mission with `--no-launch`, set its budget with `mission_topup.py budget`, then let the sweep launch it. Never hold a mission whose worker could die.
3. Machinery debt:
   - the cost breaker watches only the bound repo;
   - there is no clock-wait primitive for a live worker;
   - F6: a run overshoots `--budget-usd` while in flight;
   - sync `ac18e7a9` to the laptop.

**Update 2026-11-01 ~16:00 UTC.**
- The Owner first chose a "bounded S9 pilot", then sent the Exactness Bridge + Mission Control addendum, which supersedes it.
- The S9 plan was proposed inline. Backup: `S9-PLAN-PROPOSAL.md` (this directory). It is awaiting one-click approval.
- Nothing is armed and nothing is edited on GEX44.
- Next action on approval: A0, reconcile the diverged PP copies (`ac18e7a9` on GEX44 vs laptop `05407d94`).

**Update 2026-11-01 ~19:30 UTC (S9 approved "y"; Phase 1 units sealed).**
- A0: the PP copies were reconciled at `fa32ba2f` (laptop and GEX44).
- gen3 `591176e2` records the approved S9 section.
- Lane A is laptop PP `98504a8d`, shipping to GEX44 with ff-only:
  - wait parks and stops an idle live owner; waited time is excluded from max_hours;
  - an Owner hold outlives its worker;
  - checkpoint states plus the CHECKPOINT blocker;
  - `workset --add`;
  - `--expect-cwd`;
  - pending_wake;
  - local gates are green (S9_WAIT 31/31).
- A4 spend lease is t1 `b567bc8a` (V-LEASE 11/11).
- Lane B B0-B2 is t1 `8adf4843`; see `S9-laneB-census.md`.
  - Spend is $331.03 of $471.10.
  - The Build Twin shows no shared cause.
  - The 73 collapse to 10 classes. The top fan-out class is FAR:STRUCTURAL_CFG (28, 3 held-out).
  - Closest to exact are NEAR:SDA_RELOCATION (4 at ~99.9 %, one RELOC_FORM each) and NEAR:REGISTER_ALLOCATION (14, 11 within 1 %).
- Next:
  1. A6 canaries MC-PR1..7 on GEX44 with throwaway missions;
  2. arm the gen3 mission (Workset gen3 + t1 + PP) for B3-B6, canary on NEAR:SDA_RELOCATION first;
  3. write the KV incidents and UKDL entries.

**Update 2026-11-02 ~09:35 UTC (Phase 1 SEALED, Phase 2 RUNNING).**
- HR-2 incident: the GEX44 PP clone was ff'd before smoke, rolled back, then real-host canaries ran. All MC-PR gates are green on `98504a8d` (run 3 plus a targeted PR6). The live-idle branch was never observed on host 2.1.302; it is unit-gated only.
- The live GEX44 clone was redeployed to `98504a8d` at 09:21:18Z: 0 supervise_error on the first pass, S9_WAIT 31/31.
- gen3 `e7b6c63a` records the Phase 1 seal.
- Phase 2 mission **m-9f94bef51619**:
  - cwd gen3-pp, Workset + t1-campaign;
  - 120M authority, 2x20M top-ups, 14 cycles, 36 h;
  - runs B3-B6 from the brief: SDA_RELOCATION canary first, model cap 25 USD through the lease, checkpoint verbs at wave end;
  - RUNNING, worker 25a88074.
- Next:
  1. monitor m-9f94bef51619 (gen3 status lines, t1 commits, `lease.json` from the first llm_fix run = MC-PR3 production evidence);
  2. on a CHECKPOINT verdict, judge the stop rule;
  3. open debt: S9-8 fast-finisher adoption, EPOCH 108/111, node v18 gate, UKDL entries from S9-INCIDENTS.md.

**Update 2026-11-02 ~11:40 UTC (S9 Phase 2 at CHECKPOINT METHOD_PIVOT_REQUIRED).**
- m-9f94bef51619 is parked on a checkpoint hold (epoch 3, iter 3). gen3 `142de164`, t1 `d5338029`. Model spend $0, so no llm_fix ran and MC-PR3 still has no production `lease.json`.
- B3 SDA_RELOCATION 0/4 (judge-bound: pooled literal vs split SDA label). B3 REGISTER_ALLOCATION 0/14 under `-lang c`. The mechanism is C++ virtual-call lowering (r12 vptr reuse, in 139 uncertified targets and 0 of the 1086 certified). 3 functions are LANE_EXACT under `-lang c++`, uncertified. B4 held-out 0/14 applicable.
- Stop rule (§Stop rule): certified exact 0 <= 1. The only remaining delta is behind 2 Owner policy questions: (1) SDA literal-pool equivalence, (2) admit a pinned `-lang c++` certifying lane. Both no = close the programme. (2) yes = narrow S10 (lane flags pinned plus controls, certify 3, run the 139 class).
- S9-8 fix is laptop PP `9915d59c`. It is not on GEX44 (needs a canary plus the Owner's go).

**Update 2026-11-02 ~13:20 UTC (Owner decisions; S9-8 canary green; S10 plan proposed).**
- Owner: (1) YES to a separate `-lang c++` certification lane plus a bounded S10, with no relaxing of exact. (2) NO to SDA literal-pool equivalence: SDA_RELOCATION stays 0/4. (3) YES only to the isolated S9-8 canary; a live deploy needs a separate go.
- S9-8 PP `9915d59c` + S9-10 marker guard `24d117e2`, on branch `canary/s9-8` in the GEX44 bare repo. Canary 2 at `24d117e2` (worktree /tmp/pp-s98, state /tmp/s98-canary2): 16/16. On GEX44 at 52 GB free: MC 242/242, S9_WAIT 31/31, EPOCH 111/111 x3 (and with the fix off), S6 72/72. Live clone still `98504a8d`.
- S10 plan: `S10-PLAN-PROPOSAL.md` (cert-cxx@1 contract, kill gates K1-K6, 40M+15M tokens, 20 USD model cap). Awaiting approval. Nothing armed, nothing written to gen3.
- UKDL promotions block "Solver Ascension S9" added. S9-6 and S9-7 closed (memory variance / environment).
- Function status unchanged by today's work: CERTIFIED_C 1086 (frontier 1086/1797), CERTIFIED_CXX 0, LANE_CANDIDATE 3 (+2 near misses), r12 class 139 (14 in H) uncertified.
- Next: (a) Owner go on the S10 plan, then write the S10 section into ASCENSION-PLAN.md and arm with `--no-launch` + topup; (b) Owner go to ff the live GEX44 clone `98504a8d` -> `24d117e2` (HR-LIVE-CLONE-IS-DEPLOY-001); (c) close m-9f94bef51619's checkpoint into S10.

**Update 2026-11-02 ~13:30 UTC (Owner "apruebo y autorizo": S9-8 deployed, S10 RUNNING).**
- Deploy: live GEX44 PP clone ff `98504a8d` -> `24d117e2` at 13:15:30Z, between passes (HR-2: same-commit smoke 16/16). First real pass at 13:19:40Z; 0 `supervise_error` since the deploy (re-checked at 13:25). Rollback: `git reset --keep 98504a8d` in `~/.claude/skills/claude-power-pack` on GEX44.
- gen3 `e6fe9ac3` holds the approved "Wave S10" section.
- S10 mission **m-e6e0340e743d**: cwd gen3-pp, Workset + t1-campaign, 40M authority + 1x15M, 12 cycles, 36 h. Launched by the sweep at 13:25:10Z, RUNNING, worker 3fbc7b02 (own ack).
- m-9f94bef51619 (S9) is left parked at checkpoint METHOD_PIVOT_REQUIRED: nonterminal, no worker, no spend. `--supersedes` refuses without a workstream goal key, and `checkpoint --clear` would relaunch S9 (S9-12).
- Next: (1) monitor m-e6e0340e743d: gen3 status lines, t1 commits; the S10-1/S10-2 V-CXX controls and mutation drill are the first gate (K1); (2) on S10-3, check the independent revalidation of the 3 LANE_EXACT; (3) on its checkpoint verb, judge the S10 stop rule.

**Update 2026-11-02 ~15:45 UTC (S10 closed on K5; S10b proposed).**
- S10 m-e6e0340e743d: K5 tripped (count of `s8/sweep-h.json` read before S10-6), 0 certificates, `cert_cxx.py` draft UNVALIDATED. t1 `35a1e465`, gen3 `d8c4e40c`. The epoch-2 worker only declared checkpoint NEXT_PLAN_REQUIRED (13:36Z). The sweep has not acted on it since, so it is parked. The sweep's RESOLVE_BY_DEFAULT on the sd8 question was NOT acted on.
- Owner decisions: (1) old H is cohort-exposed: development/replay only; a new unseen H2 with a frozen manifest, sealed run, no partial reads. (2) `cert-cxx@2` admits sd8 with the same gates; count once; corroborating ≠ independent; both-exact → UNDERDETERMINED_TOOLCHAIN.
- Plan: `S10B-PLAN-PROPOSAL.md` (this dir). Awaiting Owner approval. Nothing armed, nothing written to GEX44.
- Next on approval: S10b section + H2 manifest into gen3, measure S10's token use, arm with `--no-launch` inside the remaining S10 envelope.

**Update 2026-11-02 ~17:49 UTC (S10b approved "y"; S10b-0 sealed; mission armed).**
- gen3 `475a5559` S10b section (= H2 seed), `fe8ad47d` H2 manifest `S10B-H2-MANIFEST.json` (file sha256 922f214e..., h2_sha256 0a706af9...). Universe 122 = 139 r12 − 12 in `H.json` − 5 with S9/S10 C++-lane names; H2 = 20, disjoint from old H in every name form (verified). B4's "14 H" list was 15 r12 names, 3 outside `H.json`; all excluded.
- Isolation is structural: the worker runs S10b-1..5 only, freezes the method, checkpoints "ready for sealed H2". THE COORDINATOR runs S10b-6 (sealed) and, before it, audits the worker transcripts for any H2 name (K5'). There is no per-mission read-deny knob, and a settings deny would not stop Bash `cat` (P1b).
- S10 consumed 8.44M (transcript usage sum; cost_mark said 3.6M). Mission **m-f41146776f2b** PREPARED, cwd gen3 + t1 product, 12 cycles / 36 h, authority 31.5M + 1x15M. Command text `/tmp/s10b_command.txt` on GEX44. The sweep launches it.
- Debt: the sweep's decision recovery answered an Owner-class question (sd8 admission) as RESOLVE_BY_DEFAULT on S10; it was not acted on, but the classifier is wrong for contract questions.
- Next: watch m-f41146776f2b to CHECKPOINT_COMPLETE; then K5' audit, run S10b-6 sealed, open after SEAL, S10b-7.

**Update 2026-11-02 ~19:15 UTC (S10b CLOSED, METHOD_PIVOT_REQUIRED, H2 UNSPENT).**
- Worker S10b-1..5 (t1 6816d2a4..5bb40081): cert-cxx@2 gates 27/27, controls 28/28, mutants 16/16; **3 CERTIFIED_CXX** (80222ED8 UNDERDETERMINED_TOOLCHAIN; 80222480 and 80256314 IDENTIFIED:cxx/sd8); census 940 of 1086: 752 UNDERDETERMINED, 188 c/sd8, 146 not reconstructed; batches 0/262, K3; model $0.
- The frozen method c631de1e FAILS its positive control (OFF_SHAPE on the 3 known CXX). Owner "a": S10b-6 not run, H2 stays sealed and unspent (manifest fe8ad47d unchanged).
- K5' audit clean. K6 3/3 (identical unit/object sha). My first K6 attempt fed the raw fixture without `make_unit` and refused 3/3: an instrument error, not a lane failure.
- Closeout t1 `6515f6b0`, gen3 `80c0703c`, mission checkpoint METHOD_PIVOT_REQUIRED. Frontier: 1089/1797 functions certified once (C 1086 + CXX 3). Master gate 5/6 (maturity 2).
- Open Owner question: plan a layout-recovery method (vtable/class structs before the operator) that H2 can test, or close the programme.

**Update 2026-11-02 ~20:15 UTC (Generation S11 APPROVED "y"; Lane B RUNNING; A1 sealed).**
- Owner addendum (C++ Object Model Recovery + Method-Pivot autonomy) → inline plan approved. gen3 `7f27924f` = S11 section; backup `S11-PLAN-PROPOSAL.md` (this dir).
- Reality: official frontier is 1086 (CXX 3 outside the projection; S11 adds the column). Model $140.07 left; S11 cap $40. `.data` readable via `dol_elf_bridge` → vtables measurable.
- Lane B mission **m-f0b595fd509f**: gen3 + t1, 24 cycles / 72 h, 60M + 2×15M, RUNNING (worker b633a8c7, epoch 1 at 20:12Z). Command `/tmp/s11_command.txt` on GEX44. Ends at CHECKPOINT_COMPLETE "ready for H2 preflight".
- Lane A (coordinator, laptop PP): **A1 DONE** `c138604e` (TRUTH_CONTRACT owner class; red 47/49 → green 49/49, drills 4/4, S6 72/72, S9_WAIT 31/31). NOT yet on GEX44.
- **Update ~20:30 UTC — Lane A DONE and LIVE.** Laptop: A1 `c138604e`, A2 `0206a1e8` (opt-in `pivot-autonomy --on`, `checkpoint --residual/--gain`, streak cap 3, kill switch CPP_PIVOT_AUTONOMY=off; PIVOT 12/12, drills 3/3, MC 242/242), A3 `a6a0a032` (`tools/heldout_release.py`, HOLDOUT 10/10, drills 3/3). GEX44: `canary/s11` = 24d117e2 + cherry-picks (bccb45ad, 98bc6224, 41773cc3) — the laptop line also carries 14 foreign GPF/CCR commits, NOT deployed. Canary on host: MPOL 49/49, PIVOT 12/12, HOLDOUT 10/10, S9_WAIT 31/31, EPOCH 111/111, MC 241/242 == base 24d117e2 (pre-existing node v18 bridge gate). Live clone ff 24d117e2 → **41773cc3** at 20:24:32Z; first pass 0 supervise_error. Rollback: `git reset --keep 24d117e2`. Pivot autonomy ON for m-f0b595fd509f. Future sync: the laptop line holds the originals; the cherry-picks are patch-identical (a rebase drops them).
- Lane B progress: t1 `f798a6a3` S11-0 census + B1 registry (upstream live read incomplete), `cc0afa79` B1 controls 15/15, mutants 4/4.
- Next: watch Lane B to OM-PR1 (positive control from raw m2c); at CHECKPOINT_COMPLETE run `heldout_release.py` preflight, then the sealed H2 run. K unit pending: KV incidents (RESOLVE_BY_DEFAULT, make_unit false refusal, stale RUNNING after closeout, positive-control blindness), UKDL (Held-out Consumption Law, TRUTH_CONTRACT), prompt-debt record.
- (superseded) Next: A2 opt-in pivot routing (`arm --pivot-autonomy`, `checkpoint --residual`, method graph, ≤3 pivots, gate_question on every proposal) + MA-PR1..5 replays; A3 H2 consumption law; then canary on a throwaway mission and ff the live GEX44 clone (covered by the Owner's "y", only if the canary is green). Then H2 preflight + sealed run when Lane B checkpoints.

**Start.** Read this file, probe GEX44 for the mission and frontier state, then ask the Owner the open question.
