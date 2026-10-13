# ce-a5 HANDOFF

- Program: CE gen2 A5. Machine: GEX44 (kobicraft-gex44). Pane/process: fault-capsule successor of m-ff4fd18d5e41 (epoch 1), unit U10c. Work tree /home/kobii/missions/ce-a5, branch ce/a5.
- Heads: W at 6010c808 before U10c commits (final head in A/U10-receipt.md); DWS HEAD 466b62d82 (read-only, data/orca-dws).
- Goal ledger (goal-status --goal ce-a5, GSD_LONG_RUN_STATE_DIR=/home/kobii/ce5-env/state): cap 20,000,000; used 6,373,529; settled 5,623,529; open 750,000; remaining 13,626,471; ok=true.
- Spend per unit: per-unit token spend is not stated in the receipts U1-U4, U8, U9 (UNKNOWN, not 0); see U0/U5/U6/U7 receipts for the units that report it. Units and commits: U0 9f42e216, U1 579db9aa, U2 4fd5444a, U3 be7c3c69, U4 09c31f84, U5 7537be39, U6 7c2b6225, U7 b9185c63, U8 a6db93d1, U9 700b5c21. U10 stopped at the call breaker; closed by U10c.
- Capital created: tools (a5_stall, a5_holdout, a5_u10_budget, tests test_a5_u*), slim floor/rotation promotable policies, STALL K=14 guard, STATE projection card, reality plan, DWS-BUDGET-FINAL.md, dws-claims-semantic.json [src: unit receipts].
- Rejections: 36 ledger rows NEGATIVE_ROI (A/LEDGER.json); read-once, STATE projection, poll->event kept DWS-local, not promoted (A/HOLDOUT.md).
- Remaining debt: unmeasured calls per obligation (expected vs P90 20.9x), rotation capsule fidelity, 46 unpriced sleeping claims, Owner reality session (55 min) [src: DWS-BUDGET-FINAL.md Meta-analysis].
- Blockers: Owner decision (APPROVE DWS EXECUTION or OPTIMIZE FURTHER); two live-dispatcher guard tests fail outside scope (V-SBG-WIRED, V-SBG-E2E) [src: A/U7-receipt.md].
