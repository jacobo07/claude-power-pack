# RESUMPTION — Solver Architecture Ascension (Tennis t1 reconstruction, GEX44)

**Identity.** Owner addendum "solver architecture ascension / 10-of-10 evidence gate", approved 2026-10-31 ("APRUEBO ASCENSION"). The work runs on GEX44.
- Plan, authoritative: `/home/kobii/missions/gen3-pp/vault/programs/gsdx-factory-2/ASCENSION-PLAN.md` (branch `mission/gen3`).
- Code: `/home/kobii/missions/t1-campaign` (branch `t1/campaign`).
- Reach GEX44 with an LF, no-BOM temp script: `cmd /c "ssh -o BatchMode=yes gex44 bash -s < file"`. Export the sweep env (`CPP_CLAUDE_EXE=/home/kobii/.local/bin/claude`, `PATH=/home/kobii/.local/bin:...`) and run the PP tools from `~/.claude/skills/claude-power-pack`.

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

**Start.** Read this file, probe GEX44 for the mission and frontier state, then ask the Owner the open question.
