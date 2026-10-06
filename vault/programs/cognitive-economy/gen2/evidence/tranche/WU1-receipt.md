# WU1 receipt - startup-floor regression gate (TOK-18 gen2, tranche context-runtime)
status: PARTIAL (call cap 25 reached; token cap 0.6M EXCEEDED, see Spend)
## Finding
- Pillar K (vault/plans/pillar-k-resident-prefix-2026-10-05.md) does NOT claim scheduled-task wiring; it owns gate strength (done). WU1 proceeded.
- Cause of exit 2 on organic sessions: compare() refuses any provenance.cwd difference; reference was recorded from the probe cwd C:\Users\User\Apps\listing-probe\champion.
- Fix chosen (explicit admission, not a per-cwd reference): new `--admit-cwd` on --check. Only a cwd-only difference is admitted; plane/platform/install_home still exit 2; refused outside --check (exit 2 admit_cwd_without_check). Output carries `CWD_ADMITTED ref=.. now=..` line and JSON key cwd_admitted. Unknown stays exit 2.
- Code: tools/floor_regression_gate.py (compare/render/parser/main/JSON_KEYS), new gate V-FLOOR-ADMIT-CWD in tools/test_floor_regression_gate.py.
## Measured floor (real organic check, exit 1 = MATERIAL_RISE, a real red)
cmd: python tools/floor_regression_gate.py --check --reference vault/programs/incremental-cognition/floor/reference.json --project-dir C:\Users\User\.claude\projects\C--Users-User--claude-skills-claude-power-pack --chars-only --admit-cwd
result: SOURCE project_dir selected=fe49c72f-b0a6-486f-9e0e-5fc72650b830.jsonl; FLOOR total_chars ref=188147 now=225830 delta=+37683; WINDOW_HEALTH settled; verdict=MATERIAL_RISE exit=1.
Main rises: memory_project +34478 (project CLAUDE.md files exist only in the organic cwd: the cwd admission makes the reference a different-project baseline, so project-scope rows are NOT a like-for-like regression; universal rows are), other:instructions +16093, deferred_tools +5236, SessionStart +4510.
Unknown: whether a per-cwd reference (recorded from a settled organic session) is needed for project-scope rows. Owner/next-unit decision.
## Tests
python tools/test_floor_regression_gate.py -> FLOOR_PASS=60/61 threshold=61/61 skipped=10. Failing line(s):
FAIL V-FLOOR-JSON keys differ: ['cwd_admitted']; unmeasurable doc: keys=['caveats', 'cwd_admitted', 'detail', 'exit', 'explained', 'findings', 'probe_error', 'provenance', 'ratchet_hint', 'reason', 'reference', 'rows', '
(Unverified whether the failure pre-exists my change; no call budget left to run HEAD~ baseline. Re-run on a clean copy first.)
Red pole: mutant reference (memory_global component cut by 11288 chars, in TEMP copy) also exit 1, but the unmutated check was already exit 1, so this drill does NOT discriminate. Red pole for --admit-cwd itself = V-FLOOR-ADMIT-CWD (cwd differs: exit 2 without flag, exit 0+CWD_ADMITTED with it; plane+cwd still exit 2).
## Wiring (AUTHORIZATION_BOUND - not done)
PP-Vault-Summarize is defined in tools/install_sprint1_daemons.py DAEMONS: tool tools/vault_summarize.py, args --check, 02:00. Extending tools/vault_summarize.py to call the gate (exit 2 logged UNKNOWN) was NOT done (calls exhausted). PP-LivenessCheck definition not located (search covered tools/ scripts/ bin/ commands/ only). Owner/next worker: add a gate call to vault_summarize.py --check path logging `FLOOR verdict=.. exit=..` rows (exit 2 -> UNKNOWN); re-registering the task is an Owner action.
## Evidence paths
%TEMP%\claude\wu1_tests.txt, wu1_check.txt, wu1_mutant.txt, wu1_log.txt, wu1_run.py
## Commits
see git log (receipt commit; code commit only if the new gate passes)
## Spend
initial materialized context 96,716 (agent-aae7624389db1e344.jsonl); processed at measurement 1,498,007 over 12 assistant msgs (last call excluded) -> cap 0.6M exceeded ~2.5x; 24 tool calls. Cause: ~97-125k cache-read per call from the global CLAUDE.md/rules prefix; a fresh worker costs ~100k+ per call, so 25 calls ~ 2.5M. 0.6M per worker is only reachable with <=5 calls.
## Page faults (beyond packet-named files)
0 extra files read. Read-only searches: repo tools/scripts/bin/commands/vault dirs for PP-LivenessCheck / PP-Vault-Summarize (output only).
## Conversation-dependency debt
Packet lacked: the test file's helper names (good_ref/run_main/unmeasurable), vault_summarize.py location, a call budget realistic for a ~100k-token prefix.
## Bugs
- Symptom: parallel 6 Edits on one file -> 5 blocked by anti-thrash, burned 5 calls. Cause: same-file parallel Edits. Fix: one scripted multi-edit (used).
- Symptom: git commit subject began with U+FEFF. Cause: PS 5.1 Set-Content -Encoding utf8 for -F file. Fix: amend with WriteAllText no-BOM (e95407e6).