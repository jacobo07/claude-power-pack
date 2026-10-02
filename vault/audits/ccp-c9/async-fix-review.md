# Pre-commit review — async launch-ack fix (2026-10-03)

Reviewer: pp-code-reviewer (read-only; report persisted by the parent session).
Scope: `tools/fanout_ledger.py` (is_launch_ack, LAUNCHED/ASYNC_RAN, child_last_call),
`tools/estate_shadow.py` class Equivalents only, `tools/test_async_spawns.py`.

**Verdict: APPROVE** — CRITICAL 0 / HIGH 0 / MEDIUM 0 / LOW 1.

Checks passed: ack detection only on non-error results (is_error is always 0/1 when
result_ts is set, `usage_index.py:194`); list bodies joined before truncation; JOIN
`subagents.file = calls.file` consistent under junction canonicalization (both in
`_PATH_COLUMNS`); nested spawns map to their direct child (correct for "still running");
GROUP BY linear in calls, same shape as `spawns_in`; only SELECTs added (no write SQL);
tests drive both poles and would have caught the original bug.

LOW (fixed in the same commit): no gate pinned the NO_RESULT bound's expiry for a
LAUNCHED spawn without a subagent — a "no end = running forever" mutant stayed green.
Added V-ASYNC-EQ-NO-CHILD-BOUND; replica drill A4 (`last.get(tuid, inf)`) KILLED by it.

Replica drill (tools + modules + vault/pricing + vault/config, clean control 12/12):
A1 ack read as RETURNED -> V-ASYNC-OUTCOMES; A2 Equivalents ends at the ack ->
V-ASYNC-EQ-RUNNING; A3 error read as ack -> V-ASYNC-ERROR-NOT-ACK; A4 endless ack ->
V-ASYNC-EQ-NO-CHILD-BOUND. 4/4 KILLED.
