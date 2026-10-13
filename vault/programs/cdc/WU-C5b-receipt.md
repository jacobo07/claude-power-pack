# C5b receipt
Status: DONE

## Baseline B (step 1)
Serial, cap 300 s, base 7aaff610 (worktree, 462 suites, sum 7252 s, 6451 checks). red=66, timeout=4 (timeouts are NOT red):
test_assimilation_manifest, test_cdio, test_gsd_x_goal_mutation, test_state_isolation. Raw: evidence/C5b-baseline.json (+.log). Runner: tools/c5b_baseline.py (every subprocess awaited).

## Closure vs full on 3 leaf landings (step 2)
Full suite run at each landing commit (3 in parallel, cap 300 s), verdict = reds minus B. Raw: evidence/C5b-full-<sha>.json, C5b-step2.json.
| landing | files | closure suites / secs / checks | closure verdict (red - B) | full suites / secs | full reds - B (raw) | after serial rerun + parent control |
|---|---|---|---|---|---|---|
| d37bc362 | ccr_reread_audit + test | 1 / 0.2 / 4 | EMPTY | 459 / 6861 | 3 (proactive_agents, session_start_cost, terminal_registry) | only test_proactive_agents, red at parent too -> not caused |
| 107a6971 | cep_gen2 + test | 8 / 13.3 / 130 | EMPTY | 433 / 6565 | 7 | 4 (gsd_mission*, hook_registration_integrity), all red at parent -> not caused |
| f35feba1 | tranche_driver + test | 9 / 16.8 / 134 | EMPTY | 419 / 6545 | 5 | 4 serial; 3 red at parent; test_motion_grammar is FLAKY (parent red, green, red; outside closure) -> not caused |
Verdict: AGREE on all 3 (neither side attributes a new red to the change). Caveat, recorded not hidden: raw "full minus B" is NOT empty (3/7/5) because the baseline is itself non-deterministic (contention timeouts, flaky suites, and landing states that differ from 7aaff610); agreement needed the serial rerun + parent control. No case where the full suite caught something the closure missed. Full suite cost ~6500 s CPU per landing vs 0.2-17 s for the closure (~400-30000x).
Note: 459/433/419 suites at the older commits (suite count grows with history); picks: mission_spend, gsdx_chain, gsd_mission (hubs, 272 suites) excluded by design.

## Code (steps 3-5), tools/test_land_worktree.py 24/24
- `land_worktree --baseline-red FILE` (JSON {"red":[..]} or one path per line; timeout key ignored). Red suites in the baseline are listed as baseline_red_before/after and do not block; any other red still blocks (V-LAND-12..15).
- Hub: change_impact.hub_report; a path whose closure > 25 % of tools/test_*.py is HUB, flagged in receipt (`hub`); without explicit --test -> REFUSED AFFECTED_HUB_NEEDS_EXPLICIT_TEST; with explicit --test only those run (V-LAND-16..19).
- hooks/<name>.js -> tools/test_<name>.py by name when it exists (V-LAND-20/21); other js/vault stay unmapped and need explicit --exempt.
Open: a baseline-red suite hides a genuine regression in that same suite (accepted, listed in receipt for the reviewer). Baseline file for the live estate: vault/programs/cdc/evidence/C5b-baseline.json (stale as commits move; regenerate with tools/c5b_baseline.py).
LANDING: live be27af74 (land_worktree --affected, explicit --test of the 2 hub suites, --exempt c5b_baseline.py + vault/*, --baseline-red C5b-baseline.json). Calls used: ~45.
