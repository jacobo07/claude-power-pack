# WU2 receipt (TOK-18 gen2, zero-model wake check)
STATUS: DONE for code + both poles (fixture); Production Reality UNVERIFIED (see below).
## What changed
- tools/wake_check.py (new): evaluator. Runs the floor gate (--check --chars-only --admit-cwd, pure Python) -> DORMANT (exit 0) / WAKE (exit 1 MATERIAL_RISE, exit 2 UNKNOWN never green). Writes vault/programs/cognitive-economy/gen2/WAKE_FLAG.json only on wake. run_gate() refuses any argv with --probe or a claude/anthropic executable and counts it; report carries model_calls.
- tools/vault_summarize.py: the --check branch now first prints one `WAKE_CHECK {json}` line (errors print WAKE_CHECK_ERROR, never silent). Exit code of --check unchanged. No new task, no re-registration: the existing PP-Vault-Summarize command (`vault_summarize.py --check`, 02:00) carries it.
- tools/test_wake_check.py (new): drives the scheduled command itself with fixture gates.
## Proof
- python tools/test_wake_check.py -> exit 0, 5/5 PASS: DORMANT (wake false, model_calls 0, no flag), FLIP (wake true, flag written), UNKNOWN-NOT-GREEN (gate exit 2 -> wake), EXIT-UNCHANGED (1,1,1), MODEL-REFUSED (--probe raises, counter 1).
- python tools/vault_summarize.py --check (real, organic gate) -> WAKE_CHECK wake=true MATERIAL_RISE gate_exit=1 model_calls=0; process exit 1 = pre-existing "INDEX.md older than errors.md" (not mine).
## Production Reality layer observed
CODE/LOCAL_RUN of the exact command line. NOT observed: Task Scheduler actually launching PP-Vault-Summarize at 02:00 under pythonw (Get-ScheduledTask / Last Run Result not read this turn). Production Reality = UNVERIFIED. Note pythonw has no console: the WAKE_CHECK stdout line is invisible there; the durable signal is WAKE_FLAG.json.
## Unknowns
- Whether the installed task still points at this tool path / cwd (installer DAEMONS says so; live registration unchecked).
- Organic gate currently exits 1 (ref 188147 vs 225830), so the real task would wake every night until the reference is re-baselined or the rise explained: Owner decision.
- Nothing consumes WAKE_FLAG.json yet (producer only; consumer is a later unit).
- test_floor_regression_gate.py 60/61 not re-run (out of scope).
## Metrics
- Page faults (files read beyond packet): vault_summarize.py (partial), install_sprint1_daemons.py (grep), floor_regression_gate.py (grep). 0 full reads of others.
- Initial context (first assistant row, agent-a9baf0fdec99741fe.jsonl): input 2 + cache_creation 95546 + cache_read 0 = 95548.
- Tool calls used: 5 (this one included).
## Bugs
- run_gate first guard was an over-complex boolean (symptom: unreadable, dead branch); simplified before first run. PowerShell Select-Object on git status gave exit 255 on a closed pipe, harmless.
## Durable state this packet lacked
- Where the real task's live registration/last result can be read; the PP_WAKE_* override env names; the flag path/consumer contract.
## Owner items
- Verify task: Get-ScheduledTask PP-Vault-Summarize | Get-ScheduledTaskInfo (LastTaskResult). Decide re-baseline of floor reference. No re-registration done.