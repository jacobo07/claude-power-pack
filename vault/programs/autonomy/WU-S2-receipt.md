# S2 receipt
Status: DONE

Commit: see `git log -1 --format=%h -- tools/test_programme_spend.py` on feat/ucda.

- PROVEN (13/13 tools/test_programme_spend.py): (1) plain `arm` under a declared goal root records `ledger_goal` (new mission id binds the same goal; cwd outside roots stays unbound); (2) `mission_spend programme-spend --goal G`: settled / reserved / unknown / available (+ available_certain), from ledger journal + transcripts; (3) roles worker (mission-owner sid) / control (ledger sid, no mission) / interactive (Owner prompts, reported as interactive_processed, excluded from productive); (4) unattributed or unledgered-worker spend >= 100k tokens -> telemetry_failures, exit 3, counted in unknown. Ledger charge with no transcript = UNKNOWN.
- Mutation drill: goal_for_cwd unbound -> binding gate red; new mission id leaves the view unchanged.
- Regression: test_goal_lease 10/10, test_goal_budget_admission 58/58, test_arm_worker_guard 6/6, test_gsd_mission_goal_control 27/27.
- NOT_PROVEN: live run against the real goal autonomy-convergence (live state not read; the goal was not touched). `ledger_goal` is recorded at arm but the mission envelope/judge does not yet read it.
- Next unit: run `python tools/mission_spend.py programme-spend --goal autonomy-convergence` once live; threshold env-free (MATERIAL_TOKENS=100000).
