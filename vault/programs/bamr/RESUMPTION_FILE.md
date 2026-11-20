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
3. NEXT: P4 gaps (breaker 4 vs Regla 12 = 2; tool-failure signal; external-effect reconciliation).
4. Owner: correct `~/.claude/state/account-governor.json` reset_at (official reset Wed 17:00 UTC) and calibration
   (`python tools/account_governor.py status --json` -> `implied_calibration_api_eq_per_100pct`).
5. Debt named by the review: 7 `claude -p` tools spend ungated (list in the spec); closeout-on-quota decision.

## 5. Rejected / do-not-redo
- Do not run `account_governor.py measure` without `--host laptop` (it now refuses; it once made 126 %).
- Do not glob `Desktop/Cursor Projects/**` for tasks.json (minutes); use mission cwds.
- Do not regex-insert a line into CRLF files with `.*$` (it keeps the `\r` -> whole-file diff); rebuild from HEAD.
- Mission suites need >= 3000 MB free RAM or CPP_RESOURCE_ADMISSION=off to be meaningful.
- Pre-existing at baseline 5dccbb62 (not BAMR): test_a5_u7, capsule_v2 V-MV2-L1, legacy_characterization 8/33,
  cwd_align 20/22; s5/s6 exceed 600 s; s7/s9_redteam need the GEX44 ledger; verdict_contract lacks envelope_fixture.
- Resume check: `python tools/account_governor.py check --action relaunch` (ALLOW+OFFICIAL while a pane renders).
