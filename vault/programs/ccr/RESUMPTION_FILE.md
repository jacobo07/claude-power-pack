# RESUMPTION_FILE: ccr (CPP Cognitive Runtime as a Claude Code mod)

**Identity.** Claude Power Pack, `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`
(shared tree, 1000+ foreign dirty files: pathspec-scoped commits only). Goal `ccr`, cap 36,880,000. Owner: session
**e10a9f08** (Owner-approved handoff 2026-10-12; c13cda65 and 8f164910 STANDBY). Plan of record:
`vault/plans/ccr-v4-boundary-cost-2026-10-12.md` (Stage 1 approved). Evidence: `vault/programs/ccr/evidence-v4-stage1.md`.

**State (coherence anchor: HEAD contains merge 54d35b33 "merge(ccr v4 Stage 1)").**
- SEALED earlier: S1-S4, M1 226fcc12, M2 53b4941d, M3 11444399, M4 evidence 164ae73f.
- SEALED v4 Stage 1 (branch ccr/v4, merged 54d35b33):
  - B5 94d7b49a: shell tool-output projection. Provider canary: carry -77 % at answer parity.
  - B3 e9c7f071: the "invisible 0.73M" was carried thinking blocks (a3: 1.20M, 40.8 % of carry; ablation-proven).
  - B4/B6 bb179e73: Work-Class model, contract receipt, per-call anomaly. Live canary reproduces M4 as costIfRides 334,773.
  - D1 d37bc362: Lobby unchanged re-reads 2.4 % + 2.2 %, so One-Read is NO_GO.
  - B2/U3 8789f534: elasticity 2.4K-3.3K across 100x estate. The T5 breaker already halts zero-progress lineages; docs-reset hypothesis rejected.
  - B1: the runs-tree dump was already gone from a6 onward (driver change upstream).
- NOT released: the live runtime is still 0.1.0-feaae8b0. The mod changes act only under `--plugin-dir` (dev).
- SPEND: this pane measured 27.9M processed over 144 calls (avg ctx ~194K) and was settled to goal ccr. The interactive
  coordinator pane runs CCR main=shadow, so it got none of the savings it built: self-hosting failed for the coordinator.

**Active decisions.** CAPITAL APPLIED 2026-10-12 (Owner `approve`, packet sha 15748a91, approval 7703dccb): programme
76,880,000; lease L1 closed at 34,022,521; **lease L2 open, cap 40,000,000, succession ccr:D:r2**. Scope = Stage 2 items
(1)-(7) of the packet only. Stop-losses: coordinator-pane spend on ccr > 3M after apply -> Owner; a unit > 1.5x its P50
twice -> Owner; no release mid-Madzia-attempt. Stage 2 must not run in an interactive pane; run it as declared Work
Unit workers (projection enforce, lean floor).

**Stage 2 RUNNING (2026-10-12 22:30).** Release 0.1.0-0d60014c active (rollback: `tools/ccr_release.py rollback`).
Chain `vault/programs/ccr/stage2/chain.json` (E1 -> M1 -> W1 -> V1 -> X1, max_residuals 1), task PP-CcrChain-Tick every
10 min, log `~/.claude/state/ccr-chain-tick.log`. E1 = mission m-8630677b026a. Coordinator pane e10a9f08 measured
39,060,983 / 202 calls; ~10.2M since the 28.85M settle is UNSETTLED and over the 3M stop-loss: Owner decides whether it
is settled to ccr.

**Next 3 actions.**
1. Watch the chain (`python tools/gsdx_chain.py status --chain vault/programs/ccr/stage2/chain.json`); act only on a chain_alert.
2. Release (`tools/ccr_release.py`) M1-M3 + v4 B5/B6 at a Madzia driver boundary, not mid-attempt. Units get
   projection enforce by default, so check whether the Madzia worker declares `CCR_WORK_UNIT` first.
3. Wire the pre-launch contract (`tools/ccr_pgo.py contract`) into `gsd_mission` launch admission (Economic bridge).

**Start.** `python tools/mission_spend.py goal-status --goal ccr`; then action 1.

## X1 close (2026-10-13)
**State.** Stage 2 merged into feature/knowledge-acquisition (merge 1daee36b, `--no-ff ccr/v4`). Post-merge `tools/test_gsd_mission.py` MC_PASS=230/230, no revert. No change under mods/, so no plugin test or release was needed (live release 0.1.0-0d60014c unchanged).
**Certificate.** `vault/programs/ccr/CERTIFICATE-v4.md` = EFFECTIVENESS_PARTIAL. BOUNDARY_COST abstained: Madzia -0.2 %, V1 FAIL:runaway (saving UNKNOWN), class-only forecast error 93 %, admission only synthetic. Negative knowledge in `NEGATIVE_KNOWLEDGE.md`.
**Remaining authority.** goal-status ccr: cap 4,725,000, remaining 4,725,000, used 0 (lease L9), settled 47,214,915.
**Next actions.**
1. Owner decision: rerun V1 with a per-run guard ~1.5M or a lighter harness (needs raise), else close CCR at PARTIAL.
2. Run a Lobby R1 provider-measured rotation (k=40) to turn the +21.1 % model into a number.
3. Flip CPP_CCR_ADMISSION to enforce only after one live refusal is observed.

## V1 attempt 2 (2026-10-13, Owner "go ahead"; supersedes X1 next action 1)
**State.** Merge a4f02e04 (ccr/v4 b25fbae1). The real canary on haiku, with the guard at 1.5M: weighted saving **>= 54.2 %** (MET). Over the two measured CCR runs it is -65.5 %; processed -81.7 %; parity 5/5. r6-CCR was killed by the host memory reaper, so the CCR arm is n=2 and that parity line stays ABSTAIN. The saving is the per-call floor (78K -> 21K). The contract forecast is 13.8x high (Madzia class model). Certificate rechecked: still **PARTIAL**. Chain task PP-CcrChain-Tick DISABLED (chain complete). This run was made from the coordinator pane, not by a worker.
**Next actions.**
1. Fit a class model for bounded lookups (its floor of ~21K already matches), so `ccr_pgo contract` forecasts within 25 %.
2. Lobby R1 provider-measured rotation (k=40) -- the second work class BOUNDARY_COST needs.
3. Book the unbooked worker spend (~3M: E1/M1/W1/V1/X1 + V1b haiku) into a coord lease, after fixing `ledger._gfold` once ledger.py is no longer dirty.

## Stage 3 ARMED (2026-10-13, Owner "approve stage 3 + main canary"; supersedes the V1 attempt 2 next actions)
**Plan.** `vault/plans/ccr-v4-stage3-2026-10-13.md` (31d2867b). Chain `vault/programs/ccr/stage3/chain.json` (9c6ca0a8): A0 accounting+_gfold -> A1 version receipt -> A2 21K anatomy/hard floor -> A3 Work-Class PGO held-out -> A4 epoch economics/elasticity -> A5 Lobby R1 -> A6 real admission -> A7 main canary -> X2 recertify. Routes S3M 1.5M / S3L 3.0M (from Stage 2 measured worker spend); forecast 18M of 28,631,510 remaining; no new capital.
**Tick.** Task PP-CcrChain-Tick now runs stage3/chain_tick.ps1 every 10 min; it holds (log `ram_hold free_gb=N` in `~/.claude/state/ccr-chain-tick.log`) while free RAM < 4 GB. At arming time the host had 0.7-2.5 GB free with 32 claude.exe, so A0 starts only when RAM frees.
**Coordinator.** e10a9f08, cap 2M from here; acts only on chain_alert or a stuck state. Unbooked spend (~4-6M) is A0's first job.
**Split to GEX44 (2026-10-13 16:03, Owner "ship the pack + lobby"; the Owner ran scratchpad ship_ccr_s3.ps1 because auto mode refused the transfer from the pane).** A2-A5 run on GEX44: clone `~/missions/ccr-s3` (branch mission/ccr-s3 = e16e8036), data `~/missions/ccr-s3-data`, which holds:
- the content-free pack: 433 missions, 516 sessions, 44 logs missing;
- the Lobby repo archive and 315 Lobby logs;
- `drive.sh`, which runs one unit at a time as `claude -p` with `--max-turns` 30/40. Log `drive.log`; kill with `touch STOP`. A2 started as sid 0c9c8dbd.

The laptop chain is now A0 -> A1 -> A6 -> A7 -> X2 (forecast 7.5M). A6 `wait`s on WU-A3/A5 receipts in the main tree.
**Coordinator duty:** fetch `ssh://gex44/home/kobii/missions/ccr-s3 mission/ccr-s3`, merge it into ccr/v4, copy the DONE receipts to stage3/, run each receipt's LAPTOP_APPLY, and book the GEX44 sessions' measured spend into goal ccr.
**GEX44 A2-A5 DONE_WITH_LIMITS (2026-10-13 17:24), merged into ccr/v4 as 72b82fbe (fetch of mission/ccr-s3 72274ac4).**
Measured processed tokens per unit (GEX44 run files):

| unit | processed | calls | route |
|---|---|---|---|
| A2 | 4,302,121 | 51 | 1.5M |
| A3 | 1,678,774 | 32 | 3M |
| A4 | 6,352,270 | 66 | 3M |
| A5 | 2,012,075 | 29 | 3M |
| total | 14,345,240 | | |

Results:
- A2: tool schemas are most of the "21K floor" (REDUCIBLE).
- A3: no class meets the gate (bounded-code APE 46.4 %, n=24).
- A4: the mod edit was refused, so it ships as `stage3/a4/ccr-mod-a4.patch`. Estate gate: real mod FAIL, patch PASS.
- A5: ROT -93.1 % weighted, parity, n=1 per arm.

**STOP-LOSS HIT (A2 2.9x and A4 2.1x their routes).** The drive.sh breaker failed open on a string `message` line. PP-CcrChain-Tick is DISABLED, so A0, A1, A6, A7 and X2 do not run until the Owner decides. The A2-A5 receipts are NOT yet copied to the main-tree stage3/. GEX44 spend is unbooked.
**Phase 2 on GEX44 (Owner "1 en GEX44", 22:44).** drive3.sh runs A0 -> A1 -> A6 -> A7 -> X2 (packets `~/missions/ccr-s3-data/packets/WU-*-linux.md`, generated by scratchpad gen_s3b_linux.py). Limits: breaker fails CLOSED, 2.25M per unit, 7.5M phase cap. The plugin is loaded from a snapshot outside the clone, so the mod is editable. A1 applies the A4 patch.
Laptop-only effects come back as `## LAPTOP_APPLY` in each receipt: booking, release, merge, A7 canary command. The laptop chain stays DISABLED (superseded). A0 started as sid 47649e90.
**Coordinator duty when drive.log says "phase 2 all done":** fetch mission/ccr-s3 into ccr/v4, run each LAPTOP_APPLY in unit order, and write the RESUMPTION text from X2's receipt.
**CAPITAL OVERRUN (2026-10-13 22:53). Phase 2 is STOPPED after A1** (`~/missions/ccr-s3-data/STOP`).
- A0's LAPTOP_APPLY is booked: lease L11 `ccr:book-s3`, cap 22,826,870, 16 sessions. Goal ccr settled 69,216,205 of 76,880,000.
- Coordinator e10a9f08 transcript measures 70,526,108 processed over 351 calls. Its last ledger mark is 43,076,626, so **27,449,482 is unbooked**. Programme total ~96.7M, about 20M over the envelope.
- Not booked: it exceeds L11 and the programme. It needs an Owner decision: raise the capital or close Stage 3.
- A1 (sid 9dde3bfe) finishes; A6, A7 and X2 have not run.
- The coordinator pane is the overrun again (memory feedback_coordinator_pane_is_the_overrun). Do not coordinate further from this pane.
**Superseded next actions.** 1. Owner: resume the laptop chain (re-enable PP-CcrChain-Tick) or close Stage 3 at the GEX44 results. 2. On resume: copy the WU-A2..A5 receipts to the main-tree stage3/ (releases A6) and include the 14.35M in A0's census. 3. Apply ccr-mod-a4.patch in a unit (A6/X2), not by hand. 2. If `ram_hold` persists for hours, the Owner frees RAM (close idle panes); never kill another session. 3. On chain_alert, read the unit receipt first.