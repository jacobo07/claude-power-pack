# Ascension Cognitive Throughput -- Tranche 1 work packet (Owner "y", 2026-11-22, pane 37612bb0)

Authority: 15M processed tokens (W1 8M, W2 5M, closeout 2M), 0 top-ups. Owner approved Q1 (the day cap counts measured
spend + open reservations, not booked authority) and Q2 (this mission, in worktree C:\Users\User\Apps\pp-ascension-throughput,
branch gsd/ascension-throughput). Full plan with the measured Reality Scan: vault/plans/ascension-cognitive-throughput-20261122.md
(copy it into this worktree from the main tree if absent; the inline chat copy was authoritative).

Code owners: vault/programs/ascension/autopilot/autopilot.py (+ test_autopilot.py), tools/mission_policy.py (+ its suite),
tools/account_governor.py (read-only consumer). Live copy on GEX44: /home/kobii/agora/ascension-autopilot/autopilot.py
(reach GEX44 with an LF no-BOM temp script: cmd /c "ssh -o BatchMode=yes gex44 bash -s < file"; give </dev/null to any
stdin-reading command inside it).

NOT authorised: changing DAY_CAP / TOTAL_CAP / GEN_CAP values; relaxing any certification or judge verdict contract; any push;
deploying to GEX44 without the suite green in this session; touching lane product repos; editing the main PP tree.
Deploy rule: take /home/kobii/agora/ascension-autopilot/cron.lock (flock) while replacing autopilot.py; back up the live file
first (autopilot.py.bak-<UTC stamp>); verify md5 equals the committed file after the copy.

## Phases

Phase 1: O1 reservation release -- at generation close, the day booking of that generation becomes its measured spend (the open reservation stays booked while the generation is open; attribution stays on the arm day). Add a reservation_overhead figure to the digest. Tests from both poles (closed gen frees capital; open gen still reserved; unmeasured spend keeps the full reservation, never 0).
Phase 2: O2 judge admission split -- judging asks a JUDGE_ASK (judge p99 1.15M + planner p99 2.2M, rounded to 4M, constant with its measured provenance) instead of GEN_CAP + 2*CALL_RESERVE; arming keeps its GEN_CAP ask and its kept-judgment wait. Tests both poles.
Phase 3: O3 judgment executability -- a checkpoint marked not final yields a deterministic JUDGMENT_NOT_EXECUTABLE ledger row with zero model call (locate how the autopilot detects "marked not final" today and whether the judge is still called; the FIFATC S261C row cost 183,084 tokens). Regression test.
Phase 4: Deploy W1 to GEX44 under the deploy rule, then Production Reality: observe at least one real judgment admitted under the day cap (TENNIS S297T / WIIPARTY / FIFATC were waiting) and record the ledger rows.
Phase 5: O4 joint daily+weekly eligibility -- before arming, the autopilot runs account_governor check --action arm; a refusal is one weekly_wait log/ledger row naming the next weekly reset and a forecast of the guard trip, with no gsd_mission arm attempt and no traceback. Tests both poles.
Phase 6: O5 EnterWorktree immunity -- in mission_policy.probe_capabilities/topology_for, EnterWorktree is UNHEALTHY for a repo with no `origin` remote or whose origin lacks the current branch (it bases on fetched origin/<branch>; MKWLIB S247L/S296L incidents), so the worker gets the main-tree/disallowed topology instead of a permission prompt. Tests both poles; run the mission_policy and gsd_mission suites.
Phase 7: O6 INSTRUMENT_FAIL census -- classify the 38 evo_decision INSTRUMENT_FAIL generations from the GEX44 ledger + checkpoints into causes; write the dataset and a ranked recommendation (no gate code in this tranche).
Phase 8: Deploy W2, closeout -- UKDL entries (traps: "29M reservation is judge cost", "5-min budget wait burns model tokens", "daily reset implies runnable"), update vault/programs/ascension/RESUMPTION_FILE.md, reconcile spend against the 15M authority, final checkpoint with the measured before/after.
