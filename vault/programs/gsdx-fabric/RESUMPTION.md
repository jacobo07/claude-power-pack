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

**Everything left is in the PP backlog as D29** (`vault/plans/deferred-backlog.md`). Summary, Owner's choice (no work scheduled):
1. F3c (REA canary): needs Ghidra function boundaries >= 90 % vs DTK; F3b measured 79.52 %. A boundary-adjudication pass comes first.
2. The three D12 compiler replays (commands in WU-F5-receipt.md) need GEX44 compute jobs, excluded from this programme.
3. Promotion of any Tennis-derived item needs a held-out replay on a second corpus and an outside consumer (CBR: nothing PROMOTED).

**Start.** Nothing to resume. A new request about these units starts from this file and the receipts.
