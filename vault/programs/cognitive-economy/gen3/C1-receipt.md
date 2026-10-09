# C1 receipt -- bench.py + drill (build only)

Mission id: UNKNOWN to this session (no rehydration card was visible; packet names restart of m-4c2ceda008e1, goal cp50-c1b).
Calls used: 6 of 6 (packet, dossier, bench.py, test_bench.py, run, receipt+commit; the dossier's second page was not read, bench.py needs none of it).
Status: COMPLETE. No subagent, no search tool, nothing sent to VPS/GEX44, no compile, no model call, G0_HOLDOUT.json never opened.

Files (recon work tree C:\Users\User\Apps\recon_work\wt_cp50_c1, branch cp50-c1, commit hash: `git -C <tree> log -1 -- tools/wros/binary/decomp/bench.py`):
- tools/wros/binary/decomp/bench.py (policy v1: load_draw, cohorts, validate_record, run_cohort, freeze_threshold, read_b, criterion, CLI plan|freeze|criterion)
- tools/wros/binary/decomp/test_bench.py
PP repo: this receipt only. Merge of cp50-c1 into keosdtk-home is the coordinator's step.

Drill (verbatim):
PASS V-BENCH-DRAW n=300 loads; one swapped id -> DRAW_ANCHOR
PASS V-BENCH-HOLDOUT basename and sha-prefix refused; control loads
PASS V-BENCH-COHORT 1-50 -> 5 contiguous cohorts; 1-5 -> 1; range 0 refused
PASS V-BENCH-RECORD valid passes; missing key, reasonless absent, string cost refused; reasoned absent accepted
PASS V-BENCH-LOCK B_LOCKED before; reads after; second freeze THRESHOLD_FROZEN; edited A -> A_DRIFT
PASS V-BENCH-CRITERION B far below A -> MET (4 cells); B equal -> NOT_MET
PASS V-BENCH-PLANE B on another plane -> NO_SAME_PLANE; same plane compared
PASS V-BENCH-EXECUTOR no executor -> ARM_EXECUTOR_ABSENT, nothing written; injected -> 3 valid records; rerun refused
BENCH_DRILL=8/8
PLAN cohorts=1 functions=5   (plan --arm A --first 1 --last 5: ids main:80426354,main:8044D4A8,main:804263A4,main:8044064C,main:8042A4D0)

C2 executor debt: the arm-A executor (candidates -> cohort capsule -> GEX44 -> repatriate -> records) is absent and is C2's first deliverable; capsule_build selects from the factory ledger, not a cohort. Real arms refuse ARM_EXECUTOR_ABSENT until it is injected.
Open points (decided, not asked): (1) learning-curve window needs >=10 numeric new_cognition values (LC_MIN) else INSUFFICIENT; (2) a B cell with no matching A (stratum, plane, component) is NO_SAME_PLANE; (3) rows with absent host_plane or absent cost value are excluded from medians, never counted as 0; (4) freeze CLI takes the seed from draw.seeds.seed of the loaded freeze; (5) amendment (d) values are free-form measurements or {"absent": reason}, only presence/reason is validated.

HANDOFF NOTE: C1 done
