# WU-S3 -- context-growth estimator + three-miss DEGRADED mode (plan v3 S3, Owner "A" 2026-10-09)

Goal ce-lifecycle-v3. cwd = this worktree. Work class: IMPLEMENTATION (small, one module + one config + one test).

Defect (verified by the coordinator, do not re-derive): tools/route_admission.py:98-99 prices a worker as
`calls * (floor + packet)`, i.e. every call as call 1. Real cost per call = resident context, which grows each call.
Measured: WU-1H4 forecast 139K (need 138,659), actual 448,589 over 7 calls; WU-1H3 645K/10; WU-1H2 755K/18.

Read ONLY: tools/route_admission.py (129 lines, already the whole module), vault/config/route-floors.json.
Do not read gsd_mission.py.

Budget: hard cap 10 model calls. Checkpoint-commit as soon as step 3 is green (verified milestone), before the receipt.

Steps:
1. Fit data, one PowerShell call running a scratch script (in _logs/wus3/, not committed): for the worker transcripts of
   missions m-93c9624fb4cc, m-6ffa7ac2513b, m-1cb7a01e969b, m-c60ceb4c354c (owner sid in
   ~/.claude/state/gsd-mission-<id>.json "owner"; transcript under ~/.claude/projects/*/<sid>.jsonl), sum per assistant
   message input + cache_read + cache_creation tokens; print calls, total, first-call cost, and least-squares
   growth g in cost_i = f + g*i. Write the table to vault/programs/cognitive-economy/lifecycle/estimator-fit.md.
2. route-floors.json: add to slim-t2 `"growth": <fitted g>, "growth_n": <epochs used>` and a `"misses": []` list.
   route_admission.admit: cost = calls*(floor+packet) + growth*calls*(calls-1)//2 when growth is present (absent = old
   formula, so other profiles are unchanged). Add `estimator: "growth"|"floor"` to the output.
   Three-miss rule: a new function record_actual(profile, need, actual) appends {need, actual} to `misses` when
   actual > 1.25*need, clears the list on a hit; when the last three are misses the profile is DEGRADED and admit()
   prices it at the largest observed actual/need ratio x need and adds reason "estimator DEGRADED for <profile>".
   CLI: `route_admission.py record --profile P --need N --actual A` (no wiring into gsd_mission here; S5 calls it).
3. tools/test_route_estimator.py (new, hermetic, temp floors file): V-EST-GROWTH-QUADRATIC (7 calls with the fitted g
   predicts within 25% of 448,589), V-EST-NO-GROWTH-UNCHANGED (control: profile without growth = old number),
   V-EST-THREE-MISS-DEGRADED, V-EST-HIT-CLEARS, V-EST-DEGRADED-PRICES-UP. Mutants via tools/mutation_drill.py: drop the
   growth term; make the miss list never clear. Each must go red. Run test_gsd_mission_admission.py (baseline 43/43).
4. Commit by pathspec with -F msgfile (route_admission.py, route-floors.json, the test, estimator-fit.md, this packet).
5. WU-S3-receipt.md (<= 30 lines): fit table summary, gates, mutants, calls used, Status: DONE. Commit.
6. Arm the next unit (no pane, no Owner): if `mission_spend.py goal-status --goal ce-lifecycle-v3` shows
   remaining - open >= 700,000, run the LIVE `python C:\Users\User\.claude\skills\claude-power-pack\tools\gsd_mission.py
   arm-chain` with --cwd <this worktree> --parallel-unit lc3-WU-S2 --wu-packet <abs WU-S2.md> --token-estimate 680000
   --route <abs route-WU-S2.json>. Else write WAITING_FOR_AUTHORITY in the receipt.

NEVER write "needs a fresh pane" or "/kclear". End your final message with: HANDOFF NOTE: WU-S3 done


## Residual
Proposed by the steward for stopped mission m-a1a658f26a16 (PROPOSAL ONLY: arming it needs the Owner/coordinator).
- Partial receipt: C:\Users\User\Apps\pp-ce-lifecycle-v3\vault\programs\cognitive-economy\lifecycle\WU-S3.md.partial.json
- RESUMPTION_FILE: C:\Users\User\Apps\pp-ce-lifecycle-v3\RESUMPTION_FILE.md
- Salvage: C:\Users\User\Apps\pp-ce-lifecycle-v3\vault\specs\salvage\m-a1a658f26a16
