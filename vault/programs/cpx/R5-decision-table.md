# R5 decision table (cpx, 2026-10-11)
Source: plan cpx-control-plane-extinction sections 6, 7c, 9; deferred-backlog D14/D20/D26/D27.
Admission rule (A1): a row gets ONE slice only when C3 + TRF W6/W7 show falling marginal verified cost. No row runs wholesale. C3/W6/W7 not yet reported, so every evidence gate below is currently CLOSED.

| Row | Verdict | Evidence line |
|---|---|---|
| D24 dgl W3-W8 | KEEP_PARKED | Plan s6: CAPEX ~4-5M; tax removed is one 750K lease. Known UNKNOWN holds: 2 (530d9700 232,321; cp50-c1 150,000), both pre-chain; 0 new this week in cpx receipts. Reprice trigger (>=2 UNKNOWN holds/week across chain programmes) NOT met. |
| D26 gsdx-factory-2 | PARKED_AWAIT_OWNER | Calibration rows: spent 8,817,916 measured, open 0; forecast remaining 12.7M expected (5.1M lower / 22.1M safety), total 21.4M inside 40M; K7 over-prices ~2.8x (R2 actual 0.1M vs 1.9M est, ~19x). Resumes only on Owner activation after C3. |
| D11 REA evidence fabric | SUPERSEDED_BY_D27 | REA canary REJECT for PPC (REA-DISPOSITION). Deep fabric work frozen until D27 P7. |
| D12 ADCR procedure compiler | GATED_SLICE_LATER | D14 step 4: smallest canary on one repeated Work Class, only after trace telemetry (C3). Slice not admitted. |
| D13 Modder X intervention | GATED_SLICE_LATER | D14 step 5: one real KSR/WSR uncertainty only. Not admitted. |
| D14 sequencing guard | BINDING | Not a build row. Steps 1-7 order; freeze any layer whose meta-cost exceeds lifetime saving. |
| D15 KME Recon | GATED_SLICE_LATER | D20 step 2 canary only after repeated Work Class evidence. |
| D16 Visual Reconstruction | GATED_SLICE_LATER | D20 step 3: only where visual constraints cut iteration; needs C3. |
| D17 Time-to-Ready | GATED_SLICE_LATER | D20 step 4: instrument TTR and find the real blocker first. |
| D18 Derived Development Fabric | GATED_SLICE_LATER | D20 step 5: needs a mixed-source Feature IR (>=2 source types). |
| D19 Feature Evolution Kernel | DEFERRED | D20 step 7: only after repeated feature-family evidence. |
| D20 sequencing guard | BINDING | D15-D19 order 1-10 and the lifetime-avoided-cost gate apply to every slice. |
| D27 REA Wii/PPC Enablement | KEEP_CPP + EXTEND_UPSTREAM; P0 not armed | Activation = cpx R6 receipt DONE + C3 two-arm result. Gate: USE_REA only if P7 EVC < R6 dossier, else KEEP_CPP. D21 never waits on it. |

## FIOS duplicate-cost measurement
UNMEASURABLE here: no tools/*fios* telemetry source and no duplicate-cost field in R1/R2/B0 receipts (only B0 note: V-FIOS-LIVE-PATH-WIRED red, kclaude.ps1 lacks session_compiler --preflight). Materiality threshold: optimize only if duplicate processed tokens exceed 500K per week or 2% of weekly processed tokens. Verdict: NO_OPTIMIZATION; measurement belongs with the wiring follow-up.

## D27 P0 not armed
Reason: P0 needs a network install of the current rea-agents release (read server.json + release tag, claimed 6.4.0 unverified) and a Node 24 hang probe. Arming means editing chain.json, which this unit must not do by hand, and no live ticking chain exists to host it from this worktree. Packet to arm: zero-model, install into a fresh dir under Apps, run `rea --help` with a 45 s timeout, record version/tag/hang yes-no. Owner or R-next may arm it.
