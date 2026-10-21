# gsdx-fabric RESUMPTION (coordinator pane, updated 2026-10-15) -- PROGRAMME CLOSED

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

**UPDATE 2026-10-21 (later) -- D12d RUNNING.** Owner "go ahead" on the large-population joint-fact test (D12c had only 91 fns and was already negative: held-out 0/46, complementarity 0, stop-loss at step 3).
Packet 6cfb60f8 (`WU-D12d.md`), stop 3,500,000, 50 turns, pid 1895686, log gex44 `~/missions/gsdx-fabric-stage/run-D12d.log`. Coordinator ceiling (from `residuals_v1.jsonl`): helper-only 133 fns, helper+fields 890 of 1,521.
Pre-registered bar on held-out: >=100 newly lint-clean SUPPORTED, 1..99 PARTIAL, 0 CLOSED. WHEN IT ENDS: `result.json` -> `goal-settle --goal gsdx-factory-2 --session <sid> --measured <processed>`; `git fetch` from the clone and ff;
rescue any uncommitted clone files; ten+ gates on the clone; F7 will be red (re-pin via `--write-pin`, scp 3 files, restore clone); add D12d to chain.json; commit with pathspec.

**AFTER D12d -- decision tree for a fresh session (2026-10-21).** D12d only measures lint-clean (m2c output without unresolved types); it reconstructs NOTHING. MATCH needs a compile
and a byte compare, and the verification rate is 12/22 = 0.545 (Wilson95 0.347-0.731, n=22).
A. AUTONOMOUS (no Owner word needed): close the unit with the "WHEN IT ENDS" list above, then read `evidence/d12d/summary.json` and apply the pre-registered bar VERBATIM (never re-cut it):
   - held-out newly lint-clean >= 100 -> SUPPORTED; 1..99 -> PARTIAL; 0 -> CLOSED. Check the three control rows and the ceiling assertion first; a failed control makes the result INVALID, not a pass.
   - Record the verdict in `vault/knowledge_base`/KV `binary-reconstruction-fabric.md` as SHADOW (never PROVEN), and add negative knowledge KN-D12D-* if CLOSED. Update chain.json (D12d entry, DONE) and this file.
B. SUPPORTED or PARTIAL -> next unit is D12e = VERIFY a sample by compile. Compile is a GEX44 compute job: the Fabric plan s4 says "0 jobs; any later compile need = new Owner ask", and D28 job slots
   are 7 approved / 3 used / 4 reserved (D6, D8, D9). So the session may COMPILE THE PACKET (WU-D12e: random sample of <= 30 held-out newly-lint-clean fns, seed pinned, mwcc replay, MATCH count with Wilson interval,
   header applied exactly as D12d wrote it) and stage the launcher command, but must STOP with one concrete question to the Owner: "approve D12e (1 compile job, stop ~3M)". Do not arm it unasked.
C. CLOSED -> do NOT start compile work. The remaining 1,521 fns are model-per-function work with no measured price above class 1 (D3). Autonomous output: a one-page cost frame (class 0-1 = 275 fns scriptable; class 2-5 = 1,522 unpriced; naive bound 1,522 x 50-200K = 76-304M, H) and ONE question to the Owner:
   whether to price class 2 with a small model-per-function pilot (N=20, stop ~2M), or park Tennis at the class 0-1 slice. Nothing else is scheduled.
D. In every branch the claim "Tennis reconstructed to X %" is made ONLY from MATCH counts (byte-equal compile), never from lint-clean, never from the 0.347-0.731 estimate (that stays tagged D).
E. Housekeeping the session does without asking: settle every worker (`--measured <processed>`), pull the clone commits, rerun the gates (F4 needs ~550 s), re-pin F7 if red, pathspec commits, keep `programme-status` anchor in this file.

**Everything left is in the PP backlog as D29** (`vault/plans/deferred-backlog.md`). Summary, Owner's choice (no work scheduled):
1. F3c (REA canary): needs Ghidra function boundaries >= 90 % vs DTK; F3b measured 79.52 %. A boundary-adjudication pass comes first.
2. The three D12 compiler replays (commands in WU-F5-receipt.md) need GEX44 compute jobs, excluded from this programme.
3. Promotion of any Tennis-derived item needs a held-out replay on a second corpus and an outside consumer (CBR: nothing PROMOTED).

**Start.** Nothing to resume. A new request about these units starts from this file and the receipts.
