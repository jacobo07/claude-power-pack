---
phase: 01-usage-index-v5-substrate
verified: 2026-10-07
verdict: GAPS
plane: gex44
---

# Phase 1 Verification (goal-backward)

Goal: execution history is ingested once per content identity into queryable structured state.
Every row below is `plane: gex44`. Commands run from the repo root on `kobii@kobicraft-gex44`, tree at the
`ao-p1fix:` WR-02 commit.

| # | Success criterion | Command | Output tail | plane | Result |
|---|---|---|---|---|---|
| 1 | Schema v5 (tool events, cwd, attribution, realpath + content id); incremental migration, no re-read | `python3 tools/test_usage_index_v5.py` | `USAGE_INDEX_V5_PASS=76/76  threshold=76/76` (V-UX5-SCHEMA, -TOOL-EVENT, -CWD, -MIGRATE-ZERO-REREAD) | gex44 | PASS |
| 2 | Negative controls go red when they should (mixed, distinct histories, alias once, `_archived`, parser failure, empty refuses) | `python3 tools/test_usage_index_v5.py --drill` | `DRILL killed=18/18`, `DRILL-CLEAN-AFTER-MUTANTS ... 76/76 gates green`; identity: `USAGE_INDEX_IDENTITY_PASS=11/11` | gex44 | PASS |
| 3 | KME-L parity 102 / 34,871 / 11,549,646,300 on the GEX44 copy | `python3 tools/usage_index.py population --db /home/kobii/ao-scratch/p1/cold.sqlite --project-filter 'KobiiCraft-Core-Files\|kme-wt-arena2' --until 2026-10-03T16:13:37Z --select kme --host gex44 --expect KME-L --plane gex44` (re-run after the fixes) | exit 0, `EXACT`, `{'sessions_active': 102, 'sessions_dead': 0, 'calls': 34871, 'cache_read': 11549646300}` | gex44 | PASS |
| 4 | Refresh cost (wall, bytes) cold and delta | measured earlier, not re-run here: `01-EVIDENCE.md` § Cost (cold 128.069 s / 9,932,073,959 B; delta 0.07 s / 709,630 B); `V-UX5-CLI-COST-KEYS` green in the 76/76 run | | gex44 | PASS (evidence carried by reference, not re-measured; the fixes do not touch the ingest hot path beyond the per-file `except`) |
| ledger | pillar O closed in gen2 state | `python3 tools/test_incremental_cognition_program.py --generation 2 --status` | `{"open": ["M", "P", "Q", "R"], "closed": ["O"], "violations": []}` | gex44 | PASS |

## Review findings

| ID | Status | Gate |
|---|---|---|
| CR-01 | FIXED | V-UX5-UNTIL-DATE-ONLY-REFUSED, V-UX5-UNTIL-GARBAGE-REFUSED, V-UX5-UNTIL-VALID-CONTROL |
| WR-01 | FIXED | V-UX5-POISON-FILE-CONTINUES (V-UX5-CRASH-RESUME re-stated: a mid-file crash is now one file's typed error, status OK, rows rolled back, next refresh converges) |
| WR-02 | FIXED | V-UX5-LEGACY-GROWN-NO-LAUNCH-ROOT |
| IN-01 .. IN-05 | OPEN (not fixed here) | `expected_final_failures` falsy-terminal; `--perturb` ignored without `--expect`; bool accepted in `expected`; sessions with no `first_ts` vanish under `until`; `_census_skipped` archived shapes |

## Verdict: GAPS

Criteria 1-4 have evidence. The packet's done_gate ("full suite command ... every command exit 0") is NOT met,
because three consumer-set commands exit 1 and did so identically in `01-BASELINE.md` before Phase 1 (not
caused by these fixes, not fixed here):

- `tools/test_estate_shadow.py` exit 1, `ESTATE_SHADOW_PASS=10/11` (V-SHADOW-NESTED-PROJECT)
- `tools/test_frontier_intelligence_os.py` exit 1, `FIOS_ACTIVATION_PASS=48/49` (V-FIOS-LIVE-PATH-WIRED)
- `tools/test_token_ground_truth_junction.py` exit 1, `FileNotFoundError: 'cmd'` (Windows `mklink` shell-out)

Also open: criterion 4 was not re-measured in this unit.
