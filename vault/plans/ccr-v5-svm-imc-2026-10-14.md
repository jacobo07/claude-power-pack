---
covers: [ccr-v5, semantic-paging, epoch-compiler, institutional-mutation, durable-wait, continuation-sealing, ccr-residuals, lobby-canary, context-elasticity]
status: AWAITING_OWNER_APPROVAL
pane: d124ce03 (coordinator; executes nothing after approval except arming)
---
# CCR v5 — Semantic Working Set + Institutional Mutation Coordination (Master Plan)

Backup of the inline approval surface delivered 2026-10-14 in pane d124ce03. The chat copy is authoritative for approval;
this file is the durable record. Capital packet: `~/.claude/state/capital-authority/packets/ccr-v5-2026-10-14.json`.

## 1. Verified reality (2026-10-14 ~22:50)
- PP main tree `feature/knowledge-acquisition` 95e3cb5a; `ccr/v4` d77e600b NOT ancestor of HEAD (merge pending). Claude Code 2.1.300.
- CCR release 0.1.0-54f1824b ACTIVE (prev 0d60014c, feaae8b0 available for rollback). Main pane = shadow; subagents/units = enforce (policy.ts:14).
- Goal ccr: settled 113,318,278; open 1,033,575; programme 120,000,000; executable 5,648,147 (lease L12).
- ukdl-universal.md: foreign uncommitted +160 lines, last write 22:43, writer identity UNKNOWN (nothing records it). Merge still blocked.
- step2.ps1: matches report EXCEPT a failing `test_gsd_mission_ccr_a6` does NOT revert the merge (only the first two tests do). Bug.
- CCR RESUMPTION_FILE.md: still ` M` in the shared PP tree (1,172 dirty paths there).
- X2 step 5 = copy `stage3/a3/pgo-classes.json` + `stage3/a4/pgo/*.breakeven.json` into `~/.claude/ccr/state/pgo/` (WU-X2-receipt:137-139). Not done (dir empty). Turns DEFLATE on for bounded-code slim launches; rotate advice stays observe-only.
- A7 = main-session lean canary `CCR_MAIN_CANARY=1` (name-only skill/agent listings + MCP headings, page kind `mcp`), predicted ~12.7k off first call (~11% of 112,591 median). Needs an Owner-opened pane. CANARY_PENDING.
- GEX44 breaker: the v2 fail-open (A4 6.43M vs 2.25M stop) is ALREADY fixed in drive3.sh v3 (`over()` treats ERR/empty as over; fired correctly at A6 16:01). Residual: no regression test, driver unversioned (lives only in ~/missions/ccr-s3-data). Severity: pre-ratchet (runaway spend) → close with test + versioning.
- Lobby: canonical continuation `vault/kme/intake/luckyarena-lobby/RESUMPTION.md` (~140-line monolithic narrative). Phase 2.1 = re-footprint se_social from LBY-02 raw pixels, terminal decision per LBY-02 fall (+105.4, -40.2). Gate RED 43.

## 2. Root-cause matrix
| Q | Finding | Evidence | Gap class |
|---|---|---|---|
| Q1 why ~200K/call | Lobby floor 206,186 vs PP 18K; carry p50 ctx 503,776 on >120-call sessions; thinking blocks 40.8% of coordinator carry; Ralph TURN_CONTINUATION resumes SAME session while <300k (fixed constant), wall 40%; main pane CCR = shadow only. Floor not isolated (upper bound 3,119 hard). Project-age vs epoch-age split UNKNOWN (history_elasticity ABSTAIN 0.525). | A4:39,59,107-109; CERT:28,44; B RESUMPTION:17-18 | CARRY_RENT_EXCEEDS_REHYDRATION (suspected), FLOOR_UNATTRIBUTED |
| Q2 live vs materialized | Same work: ROT ~13-14k vs CARRY ~355k ctx/call ⇒ live set ≲4% of materialized (caveat: full rotation re-pays floor) | A5:76-78 | TRANSCRIPT_USED_AS_WORKING_MEMORY |
| Q3 fragmentation | `page` MCP tool live with kinds skills/agents/mcp/file only; no typed semantic pages, ids, versions or closure | register.ts:150 | SEMANTIC_FRAGMENTATION_MISSING |
| Q4 host boundary | Launch-time filtering works (linker, attachment drop, tool deferral, system-prompt-file, pixel tombstones); in-epoch text eviction impossible | context-rent-same-pane:64 | HOST_LIMITED ⇒ rotation is the GC primitive |
| Q5 UKDL retry | No foreign-writer→durable-wait→resume path anywhere; lease store is a ledger mutex only; X2 merge is a receipt procedure run by a pane; abort = exit 1, nobody owns the dependency | modules/lease/store.py; WU-X2:4 | CONFLICT_DETECTED_BUT_NOT_RESUMED, OWNER_USED_AS_SCHEDULER |
| Q6 sealed + dirty RESUMPTION | Residual list lives only in a hand-edited file in a shared dirty tree; close report allowed STATUS COMPLETE with that DEBT | handoff 2026-10-14 | SEALED_WITH_DIRTY_CONTINUATION |

## 3. Ownership map (extend, never parallel)
| Responsibility | Canonical owner | State → action |
|---|---|---|
| Launch-time materialization (linker) | CCR mod policy.ts/register.ts | PRODUCTION units → extend |
| Page faults | CCR `page` tool | PRODUCTION (kinds limited) → add semantic kinds |
| Semantic pages / identity / closure | NONE (UCVM/UTVM/SSM are SPEC_ONLY) | build as a CCR module `ccr_pages` (no new OS); D2A family check first |
| ContextImage | gsd_mission.py rehydration card + mission_recovery.render_packet (DUPLICATED with ccr_continuation capsule) | fold capsule into the card; one compiler |
| Epoch rotation | gsd_epoch.decide_turn_end + mission_wall.js | replace 300k constant with ccr_breakeven policy; wall stays as breaker |
| PGO | ccr_pgo.py + state/pgo | install (X2 step 5) → live |
| Path/resource leases | modules/lease/store.py (mutex only) | extend to resource leases + intent |
| Durable wait | mission_recovery DURABLE_WAIT (cost holds) | add WAIT_ON_RESOURCE kind |
| Wakeup | PP-GsdLongRun-Sweep (5 min, existing scheduler) | add resource-release check; no model polling |
| Atomic validated merge | land_worktree.py + step2.ps1 logic | fold step2 into land_worktree as continuation target |
| Sealing | gsd_epoch rehydration_verified + closer | add seal gate: continuation durable (committed or ledger-owned) |
| UWCP | SPEC_ONLY, plans say NO_WORK/DEFER | not used |

## 4. Workstreams (mode, P50 processed tokens)
- W1 EXECUTION — Context-rent attribution: decompose lobby first-call 206K (constitution/memory/hooks/tools/history) on one fresh Core Files session; fixed vs project-age vs epoch-age; Context Rent Ledger rows. 3.0M. **Gate G1:** if >70% of lobby floor is host-fixed and unmovable, W3 shrinks to receipts only and the saving goes to W5.
- W2 ULTRA-PLAN (narrow) — page identity + page store location + invalidation; run /d2a-family on {page compiler, page graph, closure, GC, epoch compiler, mutation coordinator}. 2.5M.
- W3 EXECUTION — `ccr_pages`: typed pages (Goal, WU, decision, proof, failure, file-contract, economic, continuation) compiled from RESUMPTION/receipts/vault; id = type:stable-key, version = sha256 of source span + authority; invalidators = source revision change; L0 handle / L1 certified summary / L2 evidence / L3 raw pointer; closure from WU dependency edges; served by `page` tool. 10.0M.
- W4 EXECUTION — Fault receipts (fact, page, reason, size, decision-changed), fault-storm → PGO prefetch, Semantic GC = demote at rotation, raw recall test. 4.0M.
- W5 PLAN→EXECUTION — Epoch compiler: gsd_epoch uses carry-rent vs rehydration+locality (ccr_breakeven, per Work Class PGO) instead of 300k; hard ceiling kept; successor ContextImage = closure pages only (folds ccr_continuation capsule). 5.0M.
- W6 EXECUTION — Institutional Mutation Coordination: resource leases + intent + base revision in modules/lease; writer identity via dirty-path owner probe; conflict ⇒ WAIT_ON_RESOURCE durable row; sweep wakes on commit/release/writer death; land_worktree runs validate+rollback (step2 folded, a6-revert bug fixed); abandoned writer ⇒ never touch its bytes, bounded merge WU. 8.0M.
- W7 EXECUTION — Seal gate: WU cannot reach SEALED while successor-critical continuation is dirty unless a certified store owns it; CCR RESUMPTION becomes a projection of ledger/pages. 3.0M.
- W8 EXECUTION — Residuals: main-tree merge via W6 path (auto when ukdl clears); commit RESUMPTION (pathspec); X2 step 5; breaker regression test + version drive3.sh in repo; A7 read-out after Owner opens canary pane. 4.0M.
- W9 EXECUTION — Lobby Phase 2.1 canary: compile minimum ContextImage for Phase 2.1 (se_social + LBY-02 only), run in fresh epoch under CCR_WORK_UNIT, measure first-call/avg ctx vs old pane and fresh-session baseline, record page faults. CCR-side 4.0M; the Phase 2.1 work itself bills goal luckyarena-lobby (authority checked at W9; if none → returns to Owner).
- W10 EXECUTION — CI: elasticity, overmaterialization, page-fault, stale page, raw recall, epoch economics, conflict, abandoned writer, sealing. 5.0M.
- W11 EXECUTION — Knowledge Vault/FIOS/UKDL (HR/PR/Trap, deduped)/CBR ratchet + retirements; iteration prompt applied at each listed checkpoint. 3.0M.

## 5. Token budget (processed tokens, goal ccr)
| Bound | Tokens | Basis |
|---|---|---|
| Semantic lower bound | 14M | code+tests only at 18K floor, no rework |
| LOWER | 32M | |
| P50 | 48M | sum W1-W11 51.5M less shared reuse, + meta tax 3M |
| P80 | 62M | +30% (Stage 3 overran its packet ~40%) |
| P95 | 80M | |
| HARD AUTHORITY | P80 tier ceiling | breaker per WU 1.5x route |
Confidence: medium-low. Already spent this pane on the Reality Delta ≈1.5M (booked under L12). Existing executable 5.65M does NOT cover P80 ⇒ capital packet.
Ceilings (programme goal ccr, settled+open 114.35M at packet): P50 163M · P80 177M · P95 195M.

## 6. Execution vehicle (self-hosting)
Ralph mission (`gsd_mission.py arm`) in a fresh PP worktree `ccr-v5` (branch ccr/v5 from d77e600b), GSD workstream `ccr-v5`, each epoch a declared Work Unit (CCR_WORK_UNIT) so CCR v5 develops under its own policy. Coordinator pane d124ce03 only arms and does not coordinate (memory: coordinator pane is the overrun). Micro-commits per primitive; releases via ccr_release.py at driver boundaries with rollback.

## 7. Approval envelope
Authorized on approval: PP worktree commits; CCR releases (ccr_release.py, rollback kept); hook logic inside already-registered hook-dispatcher chain; main-tree merge of ccr/v4 and ccr/v5 ONLY via the W6 guarded path when foreign writers clear; X2 step 5; drive3.sh versioning; UKDL/CBR promotions after proof.
Excluded: settings.json edits (HR-001); push; touching any foreign writer's bytes; production game servers; Stage 4; GEX44 runs beyond W8 breaker test.
Stop-loss: a WU settles >1.5x route twice; coordinator pane spend >2M after apply; G1 says dominant rent is host-fixed; any release mid-Madzia attempt.
Returns to Owner: A7 canary pane (`$env:CCR_MAIN_CANARY='1'; claude`); lobby goal authority if absent; any settings.json need; capital beyond tier.
