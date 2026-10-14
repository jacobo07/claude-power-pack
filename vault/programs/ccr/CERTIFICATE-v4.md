# CERTIFICATE-v4 (CCR v4, Stage 3 recertification X2, 2026-10-14)

Level: EFFECTIVENESS_PARTIAL

Recertified 2026-10-14 by WU-X2 after Stage 3 units A0-A7. The level is still PARTIAL. BOUNDARY_COST: 1 of 4 ladder conditions is met (one real admission intervention, A6). LONG_HORIZON: 1 of 3 sub-conditions is met (estate elasticity, A4/A1), and the level also depends on BOUNDARY_COST. Terminal is not claimed in Stage 3 (plan).

Numbers: Linux plane GEX44, host 2.1.296, unless marked "laptop projection".

## Effectiveness ladder (plan ccr-v4-stage3-2026-10-13.md, "Effectiveness ladder")

### PARTIAL -- MET (Stage 2, unchanged)
B1+B2+B5+B6 are green on real provider usage (evidence-v4-stage1.md):
- B5: carried tool output 12,136 -> 2,733 tok (-77 %) at answer parity.
- B2: call-2 step 2.4K-3.3K across 100x estate growth.
- B6: live unit canary, costIfRides 334,773 flagged with projection off, none flagged with it on.
- B1: a5 listing of 22,506 chars, gone from a6.
- Real-boundary saving is >= 54.2 % on V1 (evidence-v4-stage2-V1.md).

### BOUNDARY_COST -- NOT MET (1 of 4)
- ABSTAIN:second_class_measured_saving:+7.95 % (A5 offline E1-D with measured capsules, 15 held-out Lobby sessions; +1.53 % once rehydration is measured, A4-D; bar 15 %). The provider canary is positive but has n = 1 of 3 per arm (below). This is not NO_WORK, because the saving is positive. A4 break-even replay: no class reaches 15 % (bounded-code +3.99 %, lobby +5.47 %, long-textual -0.64 %).
- ABSTAIN:class_forecast_heldout_p50_ape_lt_25pct:46.4 % (bounded-code, n = 24 held-out, P80 coverage 70.8 %; A3). long-textual reaches 21.7 % APE with 85.7 % coverage, but only n = 7 < 8. lookup and generic are LOW. multimodal has n = 0.
- MET: real_admission_intervention_with_correctness: DETERMINISTIC_PATH re-measured A2-A5 through `gsd_mission.launch_worker` with 0 model calls, 4/4 values exact (sha256 f6c3f228..., A6). Scope: an isolated mission store on GEX44. 0 live laptop interventions have been observed (see admission_live_on_laptop).
- ABSTAIN:ledgers_reconciled:UNKNOWN (A0 census of known rows is 21,739,876, with V1 r6-CCR UNKNOWN. The booking into lease ccr:book-s3, cap 22,826,870, is still a LAPTOP_APPLY and has not run. Sessions after the census are not booked: A0 tail, A1, A6 x3, A7, X2. The coordinator pane e10a9f08 is laptop-only).

### LONG_HORIZON -- NOT MET (1 of 3, and BOUNDARY_COST is not met)
- ABSTAIN:a5_real_canary_positive_at_parity:n=1 of 3 per arm (ROT -93.1 % weighted, 38,615.2 vs 559,925.5, parity 1/1 vs 1/1; A5). It prices one step after the capsule, not a full epoch rotation: ROT does not rebuild the epoch's ~194k floor. Rounds 2-3 are about 2.94M and did not fit the budget.
- MET: estate_elasticity_low_slope: estate gate on the real mod gives PASS, 10x estate -> 3,646 bytes (gate 8,000). Before the A4 patch it was 35,927 bytes, slope 0.0204 out-byte per estate byte (A4). A1 applied the patch, and A7's edit still passes the gate (A7: estate gate PASS).
- ABSTAIN:history_elasticity_low_slope_live:0.525 (replay only: p50 ctx at call 120 is 264,394 with capsule vs 503,776 with carry, 22 Lobby sessions, 436 vs 2,431 tok/call above the floor; A4). This is modelled from rotations at break-even. The rotate advice is observe-only, so no live session has rotated by it.

### Terminal -- not claimed (plan).

## ABSTAIN list carried from Stage 2, re-read against Stage 3
- ABSTAIN:madzia_real_driver_saving:-0.2 % (E1 measured, held-out). A6 DEFLATE on 9cdf4fbb gives -60.5 % processed / -49.6 % weighted (laptop projection), but it is a counterfactual, not a re-run, and 9cdf4fbb is not in the A3 corpus. A counterfactual does not replace the measurement.
- ABSTAIN:reviewer_parity_on_real_boundary:5/5 measured, CCR arm n = 2 (unchanged; the protocol requires 3/3 per arm).
- ABSTAIN:lobby_real_provider_measurement:n=1 (A5 canary, one bounded continuation, haiku). The old +21.1 % stays a model. The offline result with measured capsules is +7.95 % / +1.53 %.
- ABSTAIN:forecast_error_class_only_worker:46.4 % (A3 bounded-code held-out P50 APE, superseding Stage 1's 93 %; gate < 25 %).
- MET (A3, n = 2, LOW confidence): forecast_vs_actual_on_ccr_run: a lookup model fit only on pre-V1 data forecasts P50 93,545, which is +4.5 % on r2-CCR (89,475) and +14.5 % on r4-CCR (81,674). The old value was +1,278 %. The OFF arm of the same task (312-471k) falls outside that model's P80. The arm drives the cost, and the class does not encode it. The held-out gate above still fails.
- ABSTAIN:admission_live_on_laptop:0 observed (the W1 contract enforce is still opt-in, `CPP_CCR_ADMISSION=enforce`. DEFLATE is default-on only for MEDIUM bounded-code slim launches, after the merge and once pgo-classes.json is in the laptop PGO dir. Neither has run on the laptop.)
- ABSTAIN:successor_from_capsule_works:n=1 (A5 ROT 2d004877 continued from a measured capsule and passed the answer check, 1/1, one step. Under the A5 protocol of 3 per arm it is unproven.)
- ABSTAIN:reasoning_rent_novelty_vs_reconstruction:UNKNOWN (B3; content not stored).
- ABSTAIN:one_read:2.40 % same-session / 2.21 % later (D1 NO_GO, bar 3 %). A4 added fingerprint invalidation (V_CCRCONT_07 passes), which is correctness, not frequency.

## New in Stage 3
- ABSTAIN:hard_floor_isolated:UNKNOWN (A2: P4 3,119 tok at call 1 is an upper bound, every token in it is controllable; P3 residual 1,354 UNKNOWN; laptop registry rows UNKNOWN).
- ABSTAIN:cws_tool_schema_saving:UNKNOWN (A2: 0 probes with `--tools Read,Grep,Glob` left. The attachments-only projection is -2,034 tok at call 1, -11 %; the CWS patch is not applied).
- ABSTAIN:main_lean_canary:UNKNOWN (A7 CANARY_PENDING; predicted ~12.7k tok off the first call, ~11 % of the laptop median 112,591; the shadow estimate is 3.8 % of main-loop processed, chars/4 assumption).

## Negative knowledge from Stage 3 execution
- Budget overruns (census-measured, `ccr_spend_census.py measure`):
  - A2: 4,359,814, against a 1,500,000 budget and a 2,250,000 unit stop; drive.log said 4,302,121. Cause: a continuation after the turn cap reread ~150K context per call.
  - A4: 6,431,753 over 66 calls, against a 3,000,000 packet budget and a 2,250,000 unit stop then in force; drive.log said 6,352,270.
  - A6: 6,070,930 over 3 attempts, against 3,000,000.
  - A7: 3,613,494, against 3,000,000.
  - A0: 1,781,551, against 1,500,000.
  - Only A1 (1,470,725), A3 (1,711,442) and the A5 worker (2,043,483) stayed under their budgets.
- GEX44 breaker failure: the driver's unit measurement failed open. Per the coordinator's diagnosis, a string `message` line in the stream made the measurement return nothing; the evidence is that drive.log A4 `processed=` is empty. With no number, the breaker never compared and never fired, and A4 ran to 6.43M. A2 also passed the 2.25M stop with no kill line: its r1 run alone is 2,588,333, and drive.log did record A2's number, so the A2 cause is UNKNOWN. The one breaker kill in Stage 3 is A6 attempt 1 at 2,367,697. A breaker whose measurement can be empty must treat empty as over the limit.
- drive.log `processed=` undercounts output by ~1.3-1.9 %: on stream-json assistant lines, `output_tokens` is the pre-stream count, and the `result` line holds the truth (A0).

Never rounded up: a missing number is UNKNOWN, not a pass.
