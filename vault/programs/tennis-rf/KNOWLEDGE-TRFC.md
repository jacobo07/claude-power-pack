# TRF-C knowledge (coordinator-side; KNOWLEDGE.md stays the workers' file)

K-TRFC-01 A pid captured from `nohup ... &` inside `ssh bash -s` is the wrapper subshell, not `claude`. Liveness of a
headless worker = `pgrep -af 'claude -p'` plus a growing worker.jsonl, never the captured pid. (P1P2, 2026-10-12.)

K-TRFC-02 Owner capital approval (packet 9ff2a9f9, programme 90M) did not raise the live goal cap (55M); the goal
breaker fenced the W12 worker after judging and before records, and fenced the coordinator mid-write. A fresh session
binds the successor lease. Before arming a worker, read the goal's cap, not the programme total.

K-TRFC-03 A worker's closing summary is a claim: W12's said 14 MATCH, the ledger says 12. Close a unit from the
ledger with a script (`evidence/w12/records.py`), never from the worker's prose.

K-TRFC-04 A headless packet with a turn limit must put the run of the analysis code BEFORE its last-turn writes. P1P2
spent turn 37 writing factor.py and never ran it; the coordinator ran it (zero model) and found a KeyError the worker
would have hit: `gid()` labels only partition members, so below-DATA_MIN / zero-idiom fns had no key. Fix = default
no-group plus a per-fn basis field, so below-minimum is never read as singleton (A1).

K-TRFC-05 My own gate first checked `m2c_with_ctx.status == "CLEAN"`; status holds the m2c status (L1/...), cleanliness
is the `clean` boolean, so the gate reported 22/22 regressions. Every gate now carries a liveness twin
(V-P1P2-CLEAN-FIELD-LIVE: count of clean=True must equal knowledge_shock clean_after, 276).

K-TRFC-06 The custody guard refuses any unit source containing the word "asm"; header COMMENTS count. Keep that word
out of tennis_context.h entirely.

K-TRFC-07 Knowledge shock is the measured lever: one context header took lint-clean 175 -> 276 over all 1,797 Tennis fns
(80 newly clean outside the draws), and W12 compile-verified 12/22 vs W10c's 0/12 without it.
