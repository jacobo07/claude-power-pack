# WU-S3 receipt
Status: DONE
- Fit (estimator-fit.md): 4 missions, f~18.4K first call, pooled g=1,725 (growth_n=4). Open point: 1H4 (448,589/7 calls) not reproducible by this fit; the erratum in the plan attributes it to call count (17 physical calls). Three-miss DEGRADED is the backstop.
- Code: tools/route_admission.py (growth term, estimator field, record_actual, DEGRADED pricing, `record` CLI); slim-t2 growth/growth_n/misses in route-floors.json.
- Gates: test_route_estimator.py EST_PASS=7/7; test_gsd_mission_admission.py ADM_PASS=43/43.
- Mutants (mutation_drill): drop growth term and never-clear miss list both went red (recorded at ea5cf9c8 checkpoint).
- Commit: ea5cf9c8.
- Calls: predecessor tripped the session breaker at 975K before this receipt; this epoch wrote the receipt only.
- Next unit: lc3-WU-S2 armed (goal remaining-open = 1,037,210 >= 700,000), see commit/chain output.
