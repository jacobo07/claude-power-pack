# CERTIFICATE-v4 (CCR v4, Stage 2 close, 2026-10-13)

Level: EFFECTIVENESS_PARTIAL

Basis (contract: plan ccr-v4-boundary-cost-2026-10-12.md, "Effectiveness contract"):
- PARTIAL requires B1+B2+B5+B6 gates green on real provider usage. Evidence: evidence-v4-stage1.md
  - B5: carried tool output 12,136 -> 2,733 tok (-77 %) at answer parity (haiku provider canary).
  - B2: call-2 step 2.4K-3.3K across 100x estate growth (provider-measured).
  - B6: live unit canary, costIfRides 334,773 flagged with projection off, none with it on.
  - B1: measured from streams (a5 22,506-char listing, gone from a6).
- BOUNDARY_COST needs two work classes (Madzia driver real + Lobby offline/R1) with forecast error and admission proven. Not met; see ABSTAIN list.
- LONG_HORIZON not attempted (depends on BOUNDARY_COST).

## ABSTAIN list
- ABSTAIN:madzia_real_driver_saving:-0.2 % (evidence-v4-stage2-E1.md; best train arm F, held-out, no arm positive; bar >= 15 %)
- ABSTAIN:real_boundary_weighted_saving_ge_15pct:UNKNOWN (evidence-v4-stage2-V1.md; FAIL:runaway, OFF run 457,404 > 400,000 guard, 1 of 6 runs, no CCR run)
- ABSTAIN:reviewer_parity_on_real_boundary:UNKNOWN (V1 parity 1/1 OFF only; no CCR arm)
- ABSTAIN:lobby_real_provider_measurement:UNKNOWN (Lobby +21.1 % held-out, D k=40, is a model: capsule 8k assumed, post-rotation work assumed unchanged; not provider-measured)
- ABSTAIN:forecast_error_class_only_worker:93 % (Stage 1 B4/B6; with floor and length known 15 %, reviewer 6.6 %; gate < 25 %)
- ABSTAIN:forecast_vs_actual_on_ccr_run:UNKNOWN (V1 recorded no CCR contract)
- ABSTAIN:admission_proven_live:UNKNOWN (W1 enforce proven only by 5 synthetic tests; no live refusal observed, default is observe)
- ABSTAIN:successor_from_capsule_works:UNKNOWN (M1 capsule 1,430 tok vs 58,770 ctx; no model call tested the successor)
- ABSTAIN:reasoning_rent_novelty_vs_reconstruction:UNKNOWN (B3; content not stored)
- ABSTAIN:one_read:2.40 % same-session / 2.21 % later (D1 NO_GO, bar 3 %)

Never rounded up: a missing number is UNKNOWN, not a pass.
