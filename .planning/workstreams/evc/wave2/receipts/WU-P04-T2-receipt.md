Status: DONE
Unit: WU-P04-T2
HEAD: 29ce6fc8

HEAD: 29ce6fc8 (base before this commit)
RED-FIRST: test_evc_draining.py failed V-EVC-DRAIN-EXISTS (judge_predictive absent) before the code. Mutation drill on a temp copy (guard `spent is None or p95_remaining is None` removed) raised TypeError in V-EVC-DRAIN-FAILOPEN, so the fail-open gate bites.
NOTE: the plan's RED input (spent 600k + p95 500k, est 1M) is 1.1M, below authority 2.0M at the default ratio 2.0, so it cannot drain. Gate inputs scaled to spent 1.2M + p95 0.9M (2.1M > 2.0M; breaker silent since 1.2M < 2.0M). Intent unchanged.
VERIFY: python tools\test_evc_draining.py -> exit 0, ALL PASS
VERIFY: python tools\test_mission_spend.py -> exit 0, MSPEND_PASS=30/30
