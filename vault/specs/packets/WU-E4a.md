done_gate: C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe tools/test_verdict_contract.py
work_tree: C:\Users\User\Apps\pp-cost-collapse
receipt: vault/specs/expected-completion.RECEIPT-E4a.json

# WU-E4a -- one verdict contract, live: WATCHED launches from the production sweep (convergence slice)

Plan (binding, Owner "y" 2026-10-08): `vault/plans/cost-collapse-convergence-plan.md` (read "Why E3G sat", "WATCHED
canonical contract", unit E4a). Fresh worker; no Agents, no GSD commands; never push.

## 0. Facts (verified 2026-10-08 ~20:10Z; re-check, do not trust)
- LIVE tree = `C:\Users\User\.claude\skills\claude-power-pack`, branch feature/knowledge-acquisition. The 5-min sweep runs
  THIS code. SHARED tree with other live writers (1dad0c27 landed on gsd_mission.py at 20:00Z): load the
  `concurrent-writers-shared-tree` skill first; pathspec commits only; never stage others' dirty files; never stash.
- Live tools/gsd_mission.py launches only "ADMISSIBLE": lines ~907, ~1127 (consumed_epoch), ~1559 (admission_refusal),
  ~1576 (session envelope), ~3792 (admit CLI exit). Worktree accepts ("ADMISSIBLE","WATCHED") at ~888, ~1009, ~1631,
  ~1666, ~3883. Records carry code_id (gsd_mission.py ~46/322); nothing compares it.
- Windows: PowerShell tool; git `C:\Program Files\Git\cmd\git.exe` (use -C, no cd); python = done_gate path;
  `$env:PYTHONIOENCODING='utf-8'`; test output to a log, read only `_PASS=` and FAIL lines.

## 1. Contract (worktree first, one commit)
`tools/route_admission.py`: `LAUNCHABLE_VERDICTS = ("ADMISSIBLE", "WATCHED")` and `KNOWN_VERDICTS` (every verdict
route_admission can emit). Every worktree gsd_mission site above uses the constant (import, no literal tuple left).
admission_refusal: a verdict not in KNOWN_VERDICTS -> refusal text starting `verdict_unknown:` naming the verdict, the
record's code_id and this CODE_ID. New `tools/test_verdict_contract.py` (V-VERDICT-*, both poles, hermetic temp state):
WATCHED launches (refusal None + envelope applied); ESCALATE/RECOMPILE refused; unknown verdict -> `verdict_unknown`;
static check: no literal "ADMISSIBLE" comparison left in gsd_mission launch sites. Keep green: test_gsd_mission_admission,
test_gsd_mission_envelope, test_route_admission, test_route_admission_expected, test_dependent_admission.

## 2. Live (the point of this unit)
Tag `cc-e4a-pre` on live HEAD first. Apply the SAME contract to the live tree by hand (the files differ; do not
cherry-pick wholesale): add the two constants to live route_admission.py (its champion estimator is unchanged -- it never
emits WATCHED, so no other live mission changes behaviour), switch the 5 live sites, add verdict_unknown. Copy
test_verdict_contract.py to live. Gates FROM THE LIVE TREE: test_verdict_contract, test_gsd_mission_admission,
test_gsd_mission_envelope, test_gsd_mission_owner_hold, test_gsd_mission. Mutation drill (tools/mutation_drill.py,
isolated copy, never the live file): drop "WATCHED" from LAUNCHABLE_VERDICTS -> V-VERDICT red. Pathspec commit on live.

## 3. Chain (last act) -- the WATCHED production canary
Write RECEIPT-E4a (worktree + live hashes, gate lines, drill result). Write `vault/specs/packets/WU-E3C1.md` (header
shape as this file, with `receipt:`) = WU-E3C sections 1-2 + RECEIPT-E3G open points: guard latency (state id list ->
offset/high-water; `st.offset` exists), re-run E3G drills d2-d5 and diagnose d4, run the 4 unrun suites; plus: give
slim-t2 `growth_per_call` and `calls_err` with basis `estimated:borrowed:top-level-worker` (never 0, confidence LOW) and
verify slim-t2 can run a packet (tools + guard hook) so E3C2 can run slim. Its last act arms E3C2 (= WU-E3C s3-4 +
plan unit E3C2) the same way. Write `route-E3C1.json`: envelope target 4000000, warn 5000000, stop 8000000, calls 30;
one top-level-worker, calls 25 (expected ~3.5M, safety ~5.1M -> WATCHED by design). Commit. Then from this worktree:
`tools/gsd_mission.py arm --cwd C:\Users\User\Apps\pp-cost-collapse --command "Execute the work unit in the wu_packet"
--workstream cost-collapse --no-launch --supersedes <your mission> --authority "vault/plans/cost-collapse-convergence-plan.md (Owner y 2026-10-08)"`,
`envelope --mission NEW --token-estimate 4M --model sonnet --autocompact 250k --wu-packet vault/specs/packets/WU-E3C1.md`,
`admit --mission NEW --route vault/specs/packets/route-E3C1.json --depends-on <your mission>`.
Do NOT run `supervise` and do NOT launch: the LIVE sweep launching a WATCHED unit unaided IS the canary. Record the
verdict and mission id in the receipt. If section 2 is not green: do NOT arm; receipt with the red lines; end.
Update the top ACTIVE block of RESUMPTION_FILE.md (worktree root) to: E4a done, E3C1 armed <id>, next E3C2.

## Budget
At most 15 model calls (route-E4a.json). On checkpoint: write the receipt and stop. End with `HANDOFF NOTE:` and one line.
