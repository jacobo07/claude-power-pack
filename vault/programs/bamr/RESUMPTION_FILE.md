# BAMR — Budget-Aware Mission Recovery — RESUMPTION

## 1. Goal
Every model-spending mission launch is admitted by the REAL account quota (harness `rate_limits`), unknown quota
refuses model spend (never deterministic work), and burn without progress becomes evidence an optimisation must cite.
Spec + all measured facts + Owner decisions: `vault/specs/budget-aware-mission-recovery.md` (read it first).

## 2. State (2026-11-20, session 05242a26, branch feature/knowledge-acquisition)
- LANDED `afb43d63`: statusline quota tap + fail-closed governor (official > estimate > UNKNOWN refuse).
- LANDED `bf315ce6`: account admission at both launch paths (launch_worker, continue_worker) + arm-guard on the
  same policy; admission never scans transcripts.
- LANDED with this file: `tools/burn_census.py` (+ `tools/test_burn_census.py`), the spec, this RESUMPTION.
- LIVE: `~/.claude/settings.json` statusLine -> `hooks/statusline_quota_tap.js` (backup
  `~/.claude/backups/settings.json.bamr-p1-20261120.bak`). Official weekly read 18-19 %; no 5h window reported.
- The governor's API-eq estimate read 86.7 % at the same time: the pre-BAMR governor would refuse every arm now.

## 3. Budget
Owner caps: session <= 40 $ API-eq (soft 25 $). Autonomous model spend 0 — nothing armed. This session measured
8.45 $ at the census point (`ccn_bench.transcript_cost` on its own transcript) plus one Sonnet review (~72 k tokens).

## 4. Next executable obligation
1. DONE `17c6717a`: the 5 UKDL entries (verified 2026-11-20 by session 3da1f022: all 5 ids in the commit).
2. DONE (session 3da1f022): P5 burn-optimisation hold at supersede, N=50M, released by `burn-cite`
   (spec "P5 burn-optimisation hold"; gate `tools/test_mission_burn_hold.py` 27/27; review's 4 findings fixed).
3. P4 DONE (2026-11-21, `provider_breaker.py`): Regla 12 (2 identical non-transient -> quarantine; known
   transient keeps 4), `tool_failure` class (2 workers stuck on one tool error), `effect_unconfirmed` park (last
   effect call with no result; `clear` reconciles). Gate `tools/test_provider_breaker.py` 64/64; review's
   6 findings fixed (tool text redacted to a digest, transient regex widened, tool failures out of the streak).
   P6 guard belongs to another owner.
4. DONE: `~/.claude/state/account-governor.json` reset_at = Wed 17:00 UTC (pane aa9f2e25, 2026-11-20); calibration
   4570 -> 5956 (Owner "si, cambialo" 2026-11-21; implied by official weekly 36.0 %; estimate now reads 36.0 % =
   official; backup `~/.claude/backups/account-governor.json.calib-20261121.bak`). Re-derive with
   `python tools/account_governor.py status --json` -> `implied_calibration_api_eq_per_100pct` if they drift apart.
5. DONE (2026-11-21): the 7 `claude -p` tools ask the governor before spawning (`tools/model_spend_gate.py`,
   gate `tools/test_model_spend_gate.py` 27/27, commit c5334896).
6. DONE (2026-11-21, Owner: "autonomia responsable, que no queden paradas las misiones"): a closeout spends the
   reserve band up to 97 % (unknown still refuses), and a closeout refused before its claim (quota / RAM) is
   CLOSEOUT_DEFERRED and retried every pass instead of FAILED forever. Spec INFO-1 "DECIDED 2026-11-21".

## 5. Rejected / do-not-redo
- Do not run `account_governor.py measure` without `--host laptop` (it now refuses; it once made 126 %).
- Do not glob `Desktop/Cursor Projects/**` for tasks.json (minutes); use mission cwds.
- Do not regex-insert a line into CRLF files with `.*$` (it keeps the `\r` -> whole-file diff); rebuild from HEAD.
- Mission suites need >= 3000 MB free RAM or CPP_RESOURCE_ADMISSION=off to be meaningful.
- Pre-existing at baseline 5dccbb62 (not BAMR): test_a5_u7, capsule_v2 V-MV2-L1, legacy_characterization 8/33,
  cwd_align 20/22; s5/s6 exceed 600 s; s7/s9_redteam need the GEX44 ledger; verdict_contract lacks envelope_fixture.
- Resume check: `python tools/account_governor.py check --action relaunch` (ALLOW+OFFICIAL while a pane renders).
