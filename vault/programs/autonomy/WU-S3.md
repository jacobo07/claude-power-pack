# WU-S3 -- Autonomy Convergence unit S3

Read `vault/programs/autonomy/PROGRAMME.md` first (session loop, continuation units, constraints).
Your scope: Plan section 2 item 3 + section 3 row 'Zero-model chaining'.

## Do
Generalize the live gsdx_chain into ONE chain tick for N programmes: a registry of chain.json files (this programme first), continuation-unit insertion supported, held/parked missions never read as running (dgl gap), one scheduled task instead of PP-GsdxChain-Tick + PP-DglChain-Tick + this programme's tick. Convert the Sidecar Live QA programme queue into a chain.json (units B-P3..A-experiments) but leave it DISABLED (parked: Stage B decides). Tests: two-unit chain relays with zero model; parked chain arms nothing; mutation drill.

Receipt: `vault/programs/autonomy/WU-S3-receipt.md`.
