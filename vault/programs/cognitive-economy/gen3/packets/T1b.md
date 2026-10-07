# cep-gen3 T1b -- autonomous token budget assignment (EXECUTION)

Supersedes T1 (m-67e0ddbedffa, held at 4,559,225 processed, no product). Owner 2026-10-07: "token budget should be
autonomously assigned" + "y". Do not read transcripts. Envelope: estimate 4.6M (breaker trips at 9.2M); plan <= 30 tool
calls; batch reads into one call where safe. At ~25 calls write a partial receipt and commit.

Repo C:\Users\User\.claude\skills\claude-power-pack, shared with live panes. Commit only your paths (`git add` new
files; `git commit -F <msg> -- <paths>`), verify `git log -1 --format=%s`, never push/reset/stash/checkout.
git = & 'C:\Program Files\Git\cmd\git.exe'; python = & 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'.

0. Overlap check first (<= 2 calls): another pane runs a "CE-T1" cognitive-economy tranche (commits 7c706eec,
   dcca2027). `git show --stat` both; if either already assigns or requires mission budgets, EXTEND it, do not
   duplicate. Record the decision in the receipt.
1. Auto-assignment (deterministic, zero model) in tools/gsd_mission.py, applied at `arm` and on the first sweep pass
   of any non-terminal mission whose token_estimate is None:
   a. packet + admitted route: estimate = route need_with_margin x calibration factor;
   b. no packet: workstream p75 processed per epoch (from the mission ledger / mission_spend) x remaining cycles;
   c. no history: estate default from a new config key (vault/config/, e.g. mission-budget-defaults.json);
   d. already RUNNING with spend: estimate = ceil((spent + default_headroom 15M) / trip_ratio).
   Record token_estimate_src="auto" + basis on the record, one ledger row `envelope_auto_assigned`. An operator value is
   never overwritten. Unmeasurable spend is never zero: case d with spend None -> use case b/c and say so in basis.
   A missing budget no longer refuses a launch (replaces T1's refuse-unless-waiver).
2. Calibration: factor = median(actual / route-predicted) over closed missions that have both; seed rows from
   measured gen3 T1 (4,559,225 / 2,009,574) and T2 (3,015,851 / 1,603,656). Floor 1.0; default 2.0 when n < 2.
3. Uncurable refusals: a launch refused for a reason no sweep can cure (e.g. missing admission) moves the mission to
   BLOCKED once with the reason surfaced; it must not retry every pass until max-hours (the first gen3 arming was
   refused 86 times over 8 h).
4. Tests in the existing gsd_mission suites: one per case a-d, operator value preserved, unmeasurable-spend path,
   calibration (n<2 default, n>=2 median), uncurable refusal -> BLOCKED once. Run the touched suites; record exit codes.
5. Receipt vault/programs/cognitive-economy/gen3/T1b-receipt.md (<=30 lines): overlap decision, commits, tests,
   calibration value, measured spend of this mission, bugs. Spend row in vault/plans/cep-gen3-universal-economy-2026-10-07.md.
6. If green: release T2 (m-9bee7894f20f) is the OWNER's call -- write the exact command into the receipt, do not run it.
   Do NOT arm T3 in this unit.
End the turn with `HANDOFF NOTE: T1b done` (or the blocker).
