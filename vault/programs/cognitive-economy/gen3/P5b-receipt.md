# P5b receipt -- recon-factory Phase 5 re-lease

Mission: m-bc6473bfe5bd (supersedes m-6d6bb4cef637). Calls used: 6 tool calls before the commit call (2 reads, 1 write batch, 1 drill, 1 doc batch) + 1 commit call = 7 of 8. 0 subagents, 0 searches. Spend metered by the control plane.

Files (recon work tree, branch keosdtk-home): tools/wros/full/closure_census.py, tools/wros/full/test_closure_census.py, .planning/workstreams/recon-factory/phases/05-closure-census-population-matrix/05-01-PLAN.md and 05-01-SUMMARY.md. Commit hashes: see the final `git log -1` lines printed by the commit call (recorded in the job report). Receipt itself committed in the PP repo.

Drill (verbatim):
PASS V-CENSUS-M0 (region 1133, pln 1131, 541/302/148/115/25, blockers 588/330/94/2)
PASS V-CENSUS-RED hi-1fn -> region=1132 pln=1130 (gate must fail)
PASS V-CENSUS-ABSENT inside=main:80425378 outside=main:80007E70
PASS V-CENSUS-ROWS rows=34159 census_only=0 corpus_only=28
NOT-RUN V-CENSUS-JSK-PNG: region bounds unknown (M0 controls were scene-registry lookups)
CENSUS_DRILL=4/4

Collapse ranking (sole besides CLASS_UNPROBED / carrying): SDA 8,362 / 11,079 > LIB 3,120 / 5,193 > CXX 1,507 / 3,336 > PS 248 / 3,057.

Open points: Jsk/Png controls unrun (bounds not in dossier); matrix/summary outputs live in %TEMP% (p5b_matrix.jsonl, p5b_summary.json), not in git; 400/400 M0 closure addrs matched the census.

HANDOFF NOTE: P5b done
