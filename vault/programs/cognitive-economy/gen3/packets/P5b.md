# P5b -- recon-factory Phase 5 re-lease: closure census + population matrix

Mission: m-bc6473bfe5bd (supersedes m-6d6bb4cef637; write this id in the receipt, mandatory).
Authority: Owner "y" 2026-10-08 on gen3/P5-receipt.md (c9d30769). Funds Phase 5 ONLY. Never arm a mission, never start
another phase, never push. P5 burned 1.41M searching for premises; every premise is now in the dossier.
Envelope (route-P5b.json, floor 110,835/call): expected 8 x (110,835 + 14k) x 1.2 = 1.2M (route target) | warn 1.3M |
HARD STOP 1.4M. Hard limit 8 tool calls. 0 subagents. NO search tools (Glob/Grep) at all.

## Corpus = ONE file
Read `C:\Users\User\.claude\skills\claude-power-pack\vault\programs\cognitive-economy\gen3\recon-reforecast\P5-DOSSIER.md`
once. It pins the input paths + sha256, every row schema, the M0 method and the M0 recipe already verified to reproduce
1,131 / 541 / 302 / 148 / 115 / 25. Read no other file. Anything not in the dossier is UNKNOWN: write it down, never look it up.

## Deliverables (recon work tree C:\Users\User\Apps\recon_work\wt_keosdtk_home)
1. `tools/wros/full/closure_census.py` (stdlib only; may import from tools/wros/binary/decomp only, never wt_match_accel).
   - `census`: the dossier's M0 recipe as a function of (census path, region LO/HI, shared set); input sha256 recorded.
   - `matrix`: one row per census id (34,159), joined on `id` with main_L0. Fields: class; shape family (shape_id,
     shape_family_size); blockers; library anchor (from census bucket/primary/families when they name a library
     family -- LIBRARY_SIGNATURE, SDK, SDK_RUNTIME_SIGNATURE, NW4R, RFL, COMPILER_SUPPORT -- otherwise ABSENT); closure
     membership (pln_region / pln_shared_helper for the M0 region, M0 closure-list membership from M0_closure.json read
     via `git show aa1d82c:<path>` as the dossier says; otherwise ABSENT); required depth (M0_closure.json `depth`,
     otherwise ABSENT). ABSENT is a missing key, never 0, never "".
   - `collapse`: for SDA (FLAGS_BLOCKED_SDA), LIB (TOOLCHAIN_UNPROBED_LIBRARY), CXX (FLAGS_BLOCKED_CXX), PS (class PS):
     rows carrying it, and rows where it is the ONLY blocker besides CLASS_UNPROBED; ranked by the second number.
   - CLI: `python -m tools.wros.full.closure_census run --out-jsonl P --summary P` (outputs outside git, e.g. %TEMP%).
2. `tools/wros/full/test_closure_census.py` (NOT test_phase5.py: that name belongs to another programme). Gates print
   `PASS/FAIL V-CENSUS-*` and a final `CENSUS_DRILL=n/m`:
   - V-CENSUS-M0: the six numbers + blockers 588/330/94/2 exactly.
   - V-CENSUS-RED: region HI moved down by one function -> the M0 gate must FAIL (red control proves it can fail).
   - V-CENSUS-ABSENT: a row outside the M0 region has no closure/depth keys; a row inside has them.
   - V-CENSUS-ROWS: matrix rows == 34,159 and the id join has 0 census-only ids.
   - Jsk/Png positive controls: their region bounds are NOT in the dossier. Print `NOT-RUN V-CENSUS-JSK-PNG: region
     bounds unknown (M0 controls were scene-registry lookups)`. Do not search for them.
3. `.planning/workstreams/recon-factory/phases/05-closure-census-population-matrix/05-01-PLAN.md` (<= 30 lines) and
   `05-01-SUMMARY.md` with the drill output lines verbatim and the collapse ranking.

## Call plan (8)
1 Read dossier. 2 Write closure_census.py. 3 Write test_closure_census.py. 4 Run the drill (PowerShell, absolute python
`C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`, cwd = work tree, PYTHONIOENCODING=utf-8). 5 Write PLAN.
6 Write SUMMARY. 7 Write receipt `C:\Users\User\.claude\skills\claude-power-pack\vault\programs\cognitive-economy\gen3\P5b-receipt.md`.
8 One PowerShell call: commit the 4 recon paths in the work tree, then the receipt in the PP repo, each by pathspec
(`git add -- <paths>; git commit -F <msgfile> -- <paths>`; git = `C:\Program Files\Git\cmd\git.exe`), then print both
`git log -1 --format=%h %s`. If the drill fails at call 4, fix once inside call 5's budget and skip nothing else: write
the failure into SUMMARY and receipt as PARTIAL.

The recon work tree has ~568 dirty `.ksr_vault` paths owned by other sessions: never stage, restore or clean them.
Do not edit ROADMAP.md or STATE.md.

## Receipt (<= 20 lines)
Mission id, calls used, files + commit hashes, drill lines verbatim, collapse ranking, open points. Spend is metered by
the control plane. Ending on a question counts as a failure. End with `HANDOFF NOTE: P5b done` or the blocker.
