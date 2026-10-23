# gsdx-fabric RESUMPTION (coordinator pane, updated 2026-10-15) -- PROGRAMME CLOSED

**UPDATE 2026-10-22 (night) -- ALL-MATCH plan approved by the Owner; READ THIS FIRST.** Plan = 4 lanes + closing planner (truth/certification,
admissibility 1,070, exact search 276, generative cascade), commits in order: (1) canonical projection, (2) certification of the 439, (3) v4
challenger + global type/prototype solver, (4) objdiff fingerprints + persistent search, (5) donor cascade, (6) repair-rule miner, (7) full
regression on GEX44. Steps 1 and 2 are DONE (fabric HEAD 2f4e8147 = bare `mission/gsdx-fabric`; clone at b7d6cf4d, pull ff before the next job):
- `modules/recon_fabric/projection.py` (NOT frontier.py, which is D4's dominator frontier): one row per fn from `evidence/pc1/ledger.jsonl` + the
  four FM sweeps (champion v3 = `evidence/fm1-repair3`), counters derived, every inconsistency a FrontierError. `python -m modules.recon_fabric.projection build|check`.
- `modules/recon_fabric/certify.py run` (GEX44 only): CERT1 batch 76f2c342 certified 439/439, 0 tokens, 121 s. Now CERTIFIED 451, COMPILES_NO_MATCH 276,
  NO_COMPILE 1,070, UNKNOWN 0. Gates (local, any plane): FR1 15/15, CERT1 15/15, FM2 22/22.
- How a deterministic job runs: push the sha to `ssh://kobii@gex44/home/kobii/repos/claude-power-pack.git` refs/heads/mission/gsdx-fabric (NEVER origin = GitHub),
  then `cmd /c "ssh -i ~/.ssh/kobicraft_gex44 kobii@gex44 bash -s < script.sh"` (LF, no BOM, `</dev/null` on every inner command) in `/home/kobii/missions/gsdx-fabric`:
  refuse if a tennis claude worker or `gsdx-fabric-stage/driver.py` runs, pull ff, check HEAD, run, commit evidence on the clone, then `git fetch <clone> HEAD` + `merge --ff-only` here.
- Digests are over LF bytes and paths are POSIX (KN-FR1-01): never hash raw bytes of a checkout file that crosses planes.
- Goal gsdx-factory-2 now on lease L18 (Owner raised twice: programme 267,817,916, cap 140,047,764). Work from the PP pane with `git -C`; never Set-Location into the worktree.
- Step 3 (first round) DONE: repair v4 is the CHAMPION (sweep b7d8e028: compile 934, MATCH 485, 0 regressed vs v3); re-certified on v4 (687046fa:
  473/473). Fabric HEAD 54ca4a8e = bare. Now CERTIFIED 485, COMPILES_NO_MATCH 449, NO_COMPILE 863. Gates FR1 15, CERT1 15, FM2 38, FM1 10.
  A new champion lane = add it to projection.LANES, set CHAMPION, sweep `fastmatch sweep repairN`, require 0 regressions, then `certify run` again.
  Read the compiler messages first: `diag_v4*.sh` pattern (read-only python heredoc on the clone printing first errors per family).
- v5 challenger COMMITTED, NOT SWEPT: fabric HEAD 33ad265f = bare (FM2 49/49). v4 core refactored to `_core4(src, v5)`; the 92 "no-code" NO_COMPILE
  are m2c jump-table lift failures (no C emitted; needs a lift-side fix, not a repair rule).
- 2026-10-23 v5 is the CHAMPION. v4 identity re-sweep: 1797/1797 cache hits, sweep.jsonl sha 0eafbefb unchanged. v5 sweep c7d2ddda: compile 1059, MATCH 502,
  0 match / 0 compile regressed vs v4 (+17 / +125). LANES+CHAMPION=v5 (44f4e735), CERT1 on v5 3d2a1fd3: 490/490 certified, 128 s, 0 tokens. Projection 1cbb2bbd
  = bare = clone: CERTIFIED 502, COMPILES_NO_MATCH 557, NO_COMPILE 738, UNKNOWN 0. Gates on both planes: FR1 15, CERT1 15, FM2 49, FM1 10.
  v5 NO_COMPILE first errors: 10149 x265, 10209 x109, no-code x92 (jump-table lift), 10377 x70, 10140 x57, 10499 x52.
NEXT: step 4 = search lane on COMPILES_NO_MATCH (557 under v5); step 5 = lift-side fix for the 92 no-code NO_COMPILE.

**UPDATE 2026-10-23 -- TENNIS ALL-MATCH T1 MISSION RUNNING (supersedes the step-4/5 NEXT above).** Owner "y" on the inline T1 master plan
(brief: Tennis ALL-MATCH + Wii/MWCC reconstruction compiler + universal method mechanisms; dormant pieces get activation predicates, not code).
- Ralph mission `m-260aa89142c8` on GEX44, clone `/home/kobii/missions/tennis-all-match` (branch `mission/tennis-all-match`, armed at d5a86458),
  `/gsd-autonomous --workstream tennis-all-match`, capsule-v2, permission auto, **authority 56,000,000**, max 60 cycles / 120 h. Supervised by
  `agora-mission-sweep.timer`. Worker 1 sid b541504e (launched ~2026-10-23 07:20 CEST), planning Phase 1.
- Plan of record = `.planning/workstreams/tennis-all-match/ROADMAP.md` (10 phases: registry, fingerprints, search engine, near-match, NO_COMPILE families,
  jump-table lift, inversion corpus, families, telemetry/CBR/red team, fixed-point + T2 sizing). Budget central 44M (25-73M) + 12M contingency.
- COORDINATOR DUTIES (this pane, lean): (1) per epoch: settle each worker session into gsdx-factory-2 (`mission_spend.py goal-settle --goal gsdx-factory-2
  --session <sid> --measured <processed>`); (2) fetch the worker's branch (it may run in `.claude/worktrees/<x>` on `mission/tennis-all-match-run`; check
  `git -C <clone> branch -a`) and ff the Fabric worktree, push to bare `mission/gsdx-fabric`; (3) merge `tennis-all-match/knowledge` + `ukdl-candidates.md`
  into the KV/UKDL; (4) carry `tennis-all-match/owner-bundle.md` lines to the Owner. Status: `CPP_CLAUDE_EXE=/home/kobii/.local/bin/claude python3
  ~/.claude/skills/claude-power-pack/tools/gsd_mission.py status` on GEX44.
- Do NOT run sweeps/certify in `/home/kobii/missions/gsdx-fabric` while the mission runs (same toolchain/CPU; the worker owns deterministic jobs now).
Pitfall seen: never pipe ssh through Select-Object -First (cuts the pipe; the remote commit survived only by luck).

**Identity.** GSD X Reconstruction Fabric = gsdx-factory Part C, goal `gsdx-factory-2`. Plan:
`vault/plans/gsdx-fabric-master-plan-2026-10-14.md` (in the fabric worktree). Live chain: `vault/programs/gsdx-fabric/chain.json`
(this repo). Fabric worktree: `C:\Users\User\Apps\pp-gsdx-factory-2\.claude\worktrees\fabric` (branch gsdx-factory/fabric at
039af4a6, NEVER pushed anywhere but the GEX44 bare repo via the launcher; fixtures hold disc-derived data).

**State: every chain unit has a receipt; nothing is running.** F1 34/34, F2 33/33, F4 41/41, F3b 36/36 (c888ecd0; functions and
xrefs PARTIAL, F3c not compiled), F6 28/28 (7508e8f3), F7 43/43 (5b9c7612; re-pinned 49b9ea22, b4a212e9), F5 slice 20/20
(6d07f05d; 3 compiler replays NOT_LIFTED), F8 slice 20/20 (68d0c3bf; routing not better than chance, MATCH-rate and tokens
NOT_PROVEN), F9 15/15 (039af4a6). Coordinator re-ran all nine gates and every mutant set at the close.
Programme 57,817,916, settled 53,278,196, unspent 4,539,720. KV `~/.claude/knowledge_vault/domain/binary-reconstruction-fabric.md`
(indexed), UKDL 86658b3f.

**Coherence anchor.** `programme-status --goal gsdx-factory-2` settled 53,278,196, open 0; fabric worktree HEAD = GEX44 clone HEAD 039af4a6.

**UPDATE 2026-10-20 -- F3adj DONE and R1 applied.** Packet a3631cbd, receipt 9d66f035 (worker sid 9d28ea23, 2,770,772 of 3,500,000
tokens, settled on gsdx-factory-2). `functions` 79.52 % -> 92.93 % (1670/1797) via the R1 return-split post-pass, NOT held-out (R1 was
chosen after reading the DTK mismatches). Applied as a separate provider record `ghidra_r1` (`provider-caps/ghidra-r1.json`, built by
`ghidra_f3adj caps` from `ghidra-tennis-adj/runs.json` only); the raw `ghidra` record keeps `functions` PARTIAL. Fabric branch HEAD
9c20b159 (dbcf74ca apply, then the F7 re-pin 68 -> 72 inputs, all four new ones UNKNOWN). All ten gates green on the GEX44 clone.
Goal gsdx-factory-2: programme 127,817,916 (Owner "subelo 70M", lease L16 cap 72,160,000), settled 56,048,968. F3c is NOT compiled and
needs an Owner word (it spends compute on GEX44). Anchor: `programme-status --goal gsdx-factory-2` settled 56,048,968; fabric HEAD = GEX44 clone HEAD 9c20b159.

**UPDATE 2026-10-20 (later) -- F3c-1 DONE by the coordinator, zero worker tokens.** The unit was only downloads and hashes, so no worker
was armed (the F3adj packet forbids network to workers). Fabric HEAD 2718a453, ten gates green on GEX44 (F7 re-pinned again, 72 -> 74
inputs: `pin:node`, `pin:rea-agents`, both INHERITED). `supply-chain.json` now pins node v22.23.3 linux-x64 (sha256 df450af8...2de) and
rea-agents 6.5.0 (sha256 531717a0...699; sha1 + sha512 SRI match the registry). Both tarballs sit in `~/fabric-tools/dl/` on GEX44,
NOTHING installed. Finding: the PPC lane IS in the 6.5.0 tarball (`dist/ghidra/GhidraPowerPcProfile.js`: ELF32 EM_PPC big-endian
ET_EXEC, `PowerPC:BE:32:default`, honours `REA_GHIDRA_LANGUAGE_ID`, refuses EF_PPC_EMB, no DOL), so F3c does not stop at TARGET_UNAVAILABLE.
**F3c-2 (next, needs the Owner word and a stop of ~4M):** extract node to `~/fabric-tools/node-22/` (never on PATH), `npm install
--ignore-scripts` rea-agents into `~/fabric-tools/rea-agents/` (39 deps incl. native node-pty: judge what its absence disables), write
the DOL -> ELF32 ET_EXEC bridge, one receipt per capability, then the economic gate. Compare REA against ghidra_r1, not raw ghidra.
Node's checksum list is same-origin, GPG unverified (recorded in supply-chain.json).

**UPDATE 2026-10-20 (evening) -- F3c ran PARTIAL; residual F3cr RUNNING.** Node 22 and rea-agents are now INSTALLED offline by the coordinator
(173 pkgs, lock sha256 18e1a5ce..., only frida has an install script, skipped). F3c worker (sid fe056ef8, packet 3f8366f0) hit its 4M breaker at 4,021,175
tokens (72 msgs): SETTLED on gsdx-factory-2 (settled 56,048,968 -> 60,070,143; remaining 65,368,053 of cap 72,160,000). It committed the bridge
(`modules/recon_fabric/dol_elf_bridge.py`), the gate `tools/test_recon_fabric_f3c.py` 27/27 and a partial receipt (842bc8a6, fast-forwarded into the
fabric worktree). Measured: REA ADMITS the bridge ELF, procedure_count 12,061 = the raw Ghidra export of F3b; 237.7 s and 2.0 GB per call, and every REA call
re-runs the analysis (the `function` call took 3:54 again, even with --snapshot). Half the budget went on 3 environment attempts (wrong GHIDRA_INSTALL_DIR;
REA needs a full JDK, solved with `~/fabric-tools/jdk21-shim-rea`; recipe in `~/fabric-tools/out/f3c/rea_env.sh`). Likely disposition ECONOMICALLY_INFERIOR, NOT yet
demonstrated per function. F3cr (packet fa3cfe68, Owner "1", stop 2,000,000, 40 turns, pid 3092045, log gex44 `~/missions/gsdx-fabric-stage/run-F3cr.log`) compares
`runs/search.json` with the F3b export / DTK / ghidra_r1, writes `provider-caps/rea-tennis/*` receipts and `evidence/f3c/economics.json`. WHEN IT ENDS (coordinator):
read `result.json` for sid + processed, `goal-settle --goal gsdx-factory-2 --session <sid> --measured <processed>`, pull the clone commits (`git fetch` from the clone, ff-only),
re-run all ten gates on the clone, re-pin F7 (`--write-pin` on GEX44, scp the 3 files back), then apply the verdict as a separate provider record (like ghidra_r1), never over rea.json.

**UPDATE 2026-10-21 -- F3c DONE: ECONOMICALLY_INFERIOR. Nothing is running.** F3cr (sid ad431c7f) stopped at its 2.0M breaker (2,038,163) and is SETTLED
(settled 62,108,306 of programme 127,817,916; lease L16 remaining 63,329,890). REA's procedure start set is IDENTICAL to the F3b export (12,061), starts only, no sizes; 231-238 s and ~2 GB
per operation vs Ghidra-direct 88.9 s for everything (2.6x wall). Eight receipts in `provider-caps/rea-tennis/`, `evidence/f3c/economics.json`; no provider record added, `rea.json` untouched.
Fabric HEAD 29300bd1 = GEX44 clone HEAD (pushed to the bare repo only). Gates on the clone: F1 34, F2 35, F3adj 31, F3b 36, F3c 37, F4 41, F5 20, F6 28, F7 43 (re-pinned 74 -> 75 inputs, 1195da33), F8 20, F9 15.
Anchor: `programme-status --goal gsdx-factory-2` settled 62,108,306, open 150,000 (f381f018 tombstoned, settles on detach).

**UPDATE 2026-10-21 (night) -- CURRENT STATE, read this first. Nothing is running on GEX44.**
Fabric HEAD b11aca5b = clone HEAD; pushed to the bare repo only; F7 re-pinned 77 inputs; gates green (F1 34, F2 35, F3adj 31, F3b 36, F3c 37, F4 41, F5 20, F6 28, F7 43, F8 20, F9 15, PC1 43; D12d 20/22 with 2 intended scientific reds).
Ledger gsdx-factory-2: settled 68,651,091 of programme 127,817,916, remaining 56,787,105 of cap 72,160,000 (lease L16), open 150,000 (f381f018 tombstone).
- D12d FINAL: held-out 12 = shuffled 12 -> transfer NOT established; lint-clean is routing evidence only (KN-D12D-01..04 in the KV). Receipt 08d04105.
- PC1 DONE (sid 46e776dd, 3,041,131 settled, receipt febfd213): ledger MATCH 12 / cross-title EXACT donor 129 (SHADOW) / family 0 / parameterized 0 / residual 1,656; stage 2 CLOSED (discounted compiler-admissible 284 < 300; no mechanism >= 150 held-out-backed);
  residual bounds LOWER 0 / UPPER 1,473 (wide because library identity and behavioural sufficiency are UNMEASURED); graph: 625 shared roots, top-10 roots close 103 fns, top-50 150, all 625 only 227 (structure, correctness unproven).
  Owner note in the receipt: 284 is 16 below the bar and rests on the unknown identity of the 169 D12d fns (only counts were persisted).
- LEARNING LOOP tranche A (Owner approved 'Tramo A ahora; B y C automaticos solo si A paga') is in the PP worktree `C:\Users\User\Apps\pp-learning-loop` branch `gsdx-learning/loop`, commits 99f82883..1c300267, NOT merged, NOT pushed:
  `modules/learning_loop/{surprise,proxy_authority,blast,outcome}.py`, `tools/learning_gate.py`, `tools/test_learning_loop.py` (44 V-LL gates, 11 mutants killed), `vault/learning_loop/` (bank D4/F8/D12c/D12d, authority registry with lint_clean semantic_correctness derived to NO from the raw run, gate kinds, 2 rescue events),
  spec `vault/specs/learning-loop-tranche-a.md`, UKDL candidates `vault/knowledge_base/learning_loop/UKDL_CANDIDATES_PROXY_AUTHORITY.md`. The fabric launcher `C:/Users/User/fabric-unit-gex44.ps1` now runs `learning_gate check-packet` before arming (refused PC1 re-launch: no ack marker).
- NEXT (autonomous, in order): (1) add the line `Proxy-authority-ack: lint_clean 2026-10-21` to `WU-PC1.md` in the fabric worktree (deliberately not done while PC1 ran), commit pathspec, push; (2) tranche A closing: run `python -I tools/test_learning_loop.py`, red-team the detector (false positives on D12c-like nulls, over-staling in `consumers`), write the tranche A receipt + KV/UKDL dispositions, measure actual spend of the learning layer;
  (3) decide tranche B/C ONLY on evidence: B opens if tranche A caught a real failure the old prose rule did not (it did derive the D12d downgrade and refused the PC1 relaunch) AND a second incident family reproduces; otherwise FREEZE (meta-optimization moratorium);
  (4) the Owner question that remains open and is NOT mine to answer: whether to fund a compile-verification pilot on a seeded sample of the lint-clean candidates (needs a GEX44 compile job, a new Owner ask) or to price the 625 shared roots first.
  Open Owner correction to honour: a CLOSED verdict never means 'the rest needs a model per function'.

**UPDATE 2026-10-21 (later) -- D12d RUNNING.** Owner "go ahead" on the large-population joint-fact test (D12c had only 91 fns and was already negative: held-out 0/46, complementarity 0, stop-loss at step 3).
Packet 6cfb60f8 (`WU-D12d.md`), stop 3,500,000, 50 turns, pid 1895686, log gex44 `~/missions/gsdx-fabric-stage/run-D12d.log`. Coordinator ceiling (from `residuals_v1.jsonl`): helper-only 133 fns, helper+fields 890 of 1,521.
Pre-registered bar on held-out: >=100 newly lint-clean SUPPORTED, 1..99 PARTIAL, 0 CLOSED. WHEN IT ENDS: `result.json` -> `goal-settle --goal gsdx-factory-2 --session <sid> --measured <processed>`; `git fetch` from the clone and ff;
rescue any uncommitted clone files; ten+ gates on the clone; F7 will be red (re-pin via `--write-pin`, scp 3 files, restore clone); add D12d to chain.json; commit with pathspec.

**UPDATE 2026-10-21 (evening) -- D12d ENDED at its breaker; verdict PENDING its controls.** Worker sid 3c8c5c23, 3,501,654 tokens, SETTLED (settled 65,609,960; remaining 59,828,236 of cap 72,160,000). Fabric HEAD a93d7803 (D12d commits ff'd, PC1 packet committed, pushed to the bare repo only).
First full apply (partial receipt 5385f882): 1,292 facts (707 helper + 585 struct) from the pack half; newly lint-clean PACK 157 / HELD-OUT 12 of 767 (rule verbatim => PARTIAL), 0 regressions, 19 hidden FIELD_UNTYPED blockers. DEFECT, reported not fixed: held-out 12 > the pre-defined ceiling 9
(`V-RF-D12D-HELD-LE-CEILING` red; the ceiling counts direct coverage only, 5 of the 12 cleared through another written prototype). By construction struct facts cannot reach the held-out half (ARG-rooted clusters are accessed almost only by their root fn; 3,721 non-ARG-root clusters were NOT tested).
Reading: the tested envelope = helper prototypes + ARG-rooted widths; transfer pack 157/754 (20.8 %) vs held-out 12/767 (1.6 %). It does NOT say anything about global layouts or the other mechanisms.
The worker never ran per-kind runs, controls or summary. The COORDINATOR started them on GEX44 with zero model tokens: `tools/d12d_run.py kinds|controls|summary`, nohup, log `~/d12d-resid.log` (started 2026-10-21 evening, ~2-3 h CPU: 3 per-kind + shuffled + inflated applies of ~30 min each). Do NOT launch PC1 until `== done` is in that log (same clone tree).
WHEN IT ENDS: read `evidence/d12d/summary.json` + controls; the verdict is VALID only if no-op is byte-identical, shuffled held-out ~0 and inflated does not raise; a red ceiling is recorded as a gate-definition defect, not hidden. Commit the evidence from the clone (it writes under evidence/d12d/), then run the gates, re-pin F7, then launch PC1.
Immediate yield if valid: the 169 newly lint-clean fns (276 -> 445) are compiler-admissible m2c candidates; that alone exceeds the stage-2 gate's second leg (>= 300), so PC1 must evaluate it honestly (lint-clean is not MATCH; verification rate 0.347-0.731 is tag D).

**AFTER D12d -- decision tree for a fresh session (2026-10-21).** D12d only measures lint-clean (m2c output without unresolved types); it reconstructs NOTHING. MATCH needs a compile
and a byte compare, and the verification rate is 12/22 = 0.545 (Wilson95 0.347-0.731, n=22).
A. AUTONOMOUS (no Owner word needed): close the unit with the "WHEN IT ENDS" list above, then read `evidence/d12d/summary.json` and apply the pre-registered bar VERBATIM (never re-cut it):
   - held-out newly lint-clean >= 100 -> SUPPORTED; 1..99 -> PARTIAL; 0 -> CLOSED. Check the three control rows and the ceiling assertion first; a failed control makes the result INVALID, not a pass.
   - Record the verdict in `vault/knowledge_base`/KV `binary-reconstruction-fabric.md` as SHADOW (never PROVEN), and add negative knowledge KN-D12D-* if CLOSED. Update chain.json (D12d entry, DONE) and this file.
B. SUPPORTED or PARTIAL -> next unit is D12e = VERIFY a sample by compile. Compile is a GEX44 compute job: the Fabric plan s4 says "0 jobs; any later compile need = new Owner ask", and D28 job slots
   are 7 approved / 3 used / 4 reserved (D6, D8, D9). So the session may COMPILE THE PACKET (WU-D12e: random sample of <= 30 held-out newly-lint-clean fns, seed pinned, mwcc replay, MATCH count with Wilson interval,
   header applied exactly as D12d wrote it) and stage the launcher command, but must STOP with one concrete question to the Owner: "approve D12e (1 compile job, stop ~3M)". Do not arm it unasked.
C. CLOSED -> do NOT start compile work, and do NOT conclude the 1,521 need a model each. CLOSED retires ONLY the tested mechanism (scripted helper+field header facts) inside its tested envelope
   (Owner correction 2026-10-21: "a failed collapse hypothesis does not prove the residual requires function-by-function reasoning"). Next = the population-collapse addendum: re-rank the OTHER collapse mechanisms
   (families, libraries, cross-title donors, compiler rules, batch candidate search) by expected verified collapse per cost; the individually-reasoned residual is MEASURED after subtraction, never assumed.
   Early datum (worker commit 4dfe172b, not yet gate-verified): 707 helper + 585 struct facts from the pack half, 5 conflicts, HELD-OUT CEILING 9, so the >=100 bar is unreachable and CLOSED/low PARTIAL is expected.
D. In every branch the claim "Tennis reconstructed to X %" is made ONLY from MATCH counts (byte-equal compile), never from lint-clean, never from the 0.347-0.731 estimate (that stays tagged D).
F. POPULATION-COLLAPSE ADDENDUM (Owner 2026-10-21 approved STAGE 1 only; stage 2 = candidate search + compile jobs needs a separate Owner word AND the pre-registered gate). Central stage-1 budget ~12M (8-19M) of the 63.3M left in L16.
   First unit PC1: packet `WU-PC1.md` is WRITTEN BUT UNCOMMITTED in the fabric worktree (deliberately: the clone branch moved ahead with D12d commits, so commit it after the ff from the clone) and the kit prompt is `C:\Users\User\fabric-kit\prompt-PC1.txt`.
   Launch AFTER D12d is closed: `fabric-unit-gex44.ps1 -Unit PC1 -Stop 4000000 -Turns 50`. Gate for stage 2 (pinned in the packet): >= 150 fns of EXCLUSIVE new coverage with held-out evidence, or >= 300 mechanically skeletonable compiler-admissible fns; else the deliverable is the residual report.
   Coordinator baseline: 14,329 of 14,963 distinct vars are singletons (some derived), so the fan-out thesis is untested, not assumed. Later units (decide from PC1's result, one worker at a time): PC2 = type/layout propagation + families on thunks/accessors/<=20-insn fns; PC3 = homology/delta + gate report.
E. Housekeeping the session does without asking: settle every worker (`--measured <processed>`), pull the clone commits, rerun the gates (F4 needs ~550 s), re-pin F7 if red, pathspec commits, keep `programme-status` anchor in this file.

**Everything left is in the PP backlog as D29** (`vault/plans/deferred-backlog.md`). Summary, Owner's choice (no work scheduled):
1. F3c (REA canary): needs Ghidra function boundaries >= 90 % vs DTK; F3b measured 79.52 %. A boundary-adjudication pass comes first.
2. The three D12 compiler replays (commands in WU-F5-receipt.md) need GEX44 compute jobs, excluded from this programme.
3. Promotion of any Tennis-derived item needs a held-out replay on a second corpus and an outside consumer (CBR: nothing PROMOTED).

**Start.** Nothing to resume. A new request about these units starts from this file and the receipts.
