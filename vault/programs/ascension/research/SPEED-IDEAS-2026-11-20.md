# Ascension: ways to certify faster (Owner 2026-11-20 "also it should brainstorm ways to make things faster")

Standing duty of the loop: every idea names its measured basis and the instrument that will keep or drop it.
Instrument: `factory/ledger/progress.jsonl` (hourly: certified fns/bytes per lane, permuter counters, rate since the
previous sample), `factory/lane.log`, `factory/perm_stage.log`, `factory/stages/perm_tried.jsonl`.

| # | idea | measured basis | expected effect | status |
|---|---|---|---|---|
| S1 | every compile in its own empty cwd | wibo cost scales with cwd entries: 25 s (cwd /tmp, 737k) vs 0.013-0.023 s | permuter 23-62 -> 8.9k-16.7k iterations / 300 s | DONE (perm_stage, pilot) |
| S2 | twin transfer before any compile: unmatched body == a matched body (masked) -> copy its source | 3,541 transfer-ready fns; MP6 tool 762 in 12 min | thousands of certs at ~0 CPU | NEXT (D43 ladder step 2) |
| S3 | apply windows: lanes RUNNING block applies for hours (WIIPARTY eb9e76f waited all day) | lane.log "waits for a window" every 10 min since 11:15Z | apply at the autopilot's own arm boundary (it already holds cron.lock and knows the next base) | proposal: autopilot change = Owner "y" |
| S4 | compounding permuter: an IMPROVED output becomes the next round's base | pilot: 19/50 improved, several at score 5-10 (one register swap) | second rounds on the improved set | NEXT (perm_sources kept) |
| S5 | adaptive permuter budget and parallelism | host 28-39% CPU idle; time-to-zero varies (e.g. 3,954 iterations) | jobs = f(idle CPU); wall from the measured time-to-match distribution | after 24 h of perm_tried data |
| S6 | compile-result cache keyed by (source sha256, flags, compiler sha) | 4,785 identical bodies in >=3 games, 1,599 in all 5 | each shared body compiled once for every game | proposal |
| S7 | re-sweep against pinned targets, vs2 producer | 15,457 MKW / 14,787 WSR fns with target drift; vs2 cut WIIPARTY NO_COMPILE -58% | valid near-miss pool for the permuter on the two biggest lanes | NEXT |
| S8 | ledger-routed scheduling: each function gets the cheapest untried method for its failure class | atlas: >=99% = 74% register-only (permuter), 90-95% = structural (rewrites) | no CPU on methods that cannot fix the class | after S2/S7 |
| S9 | incremental lane gates: reuse the scratch build for the lane build (same tree after ff) | each apply = scratch base + full + lane build | ~1/3 of gate wall time | proposal |
| S10 | night sweeps at higher thread counts when the autopilot is idle | day cap parks lanes ~81 h/week (worker CPU free then) | sweeps where the CPU is idle anyway | proposal |
