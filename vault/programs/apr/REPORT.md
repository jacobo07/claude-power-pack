# APR REPORT -- handoff contract (WU-APR6, 2026-10-11)
Every number cites its source. Anything not measured is listed under UNPROVEN.

- Root cause: three receipt parsers disagreed on a Status-less receipt (KNOWLEDGE A1; suite V-APR-K5-UNCLOSED-RECEIPT-RENEWS red on HEAD, green after).
- Unit-state authority: `tools/receipt_judge.py` (APR-1) for receipts; `gsdx_chain.finalize`/`try_seal` + `acceptance` for done (APR-2).
- Receipt role: evidence the finalizer reads, never rewritten; verdict explicit or UNREADABLE. Canary: C1 UNREADABLE receipt -> seal.json verdict DONE.
- Residual model: classes FALSE_DONE/UNCLOSED_RECEIPT/NO_RECEIPT/WORKER_STOPPED, max_residuals per chain; canary C2 used 1 (row 927).
- Auto-recovery: halt-continue renewal (max 2) + seal-before-renew (APR-3); canary C1 not renewed.
- Event loop: terminal mission transition ticks the chain, `trigger:"event"`; test latency 7-12 ms (test_apr_event); canary arms rows 914/927/959 all event.
- Watchdog: PP-AprChain-Tick 10 min repair only; PP-AprCanary-Tick DISABLED 2026-10-11 (Get-ScheduledTask -> Disabled), not deleted.
- Bounded silence: `silence_s` 1800, one alert per (goal,action,unit), sink steward-incidents.jsonl, key `chain_goal` (APR-3 receipt).
- Fencing: per-goal tick lock `gsdx-chain-<goal>.lock`; two-process race tests 1 mission (test_apr_event). Canary: no duplicate chain arm.
- Attribution: rows carry `trigger`, `class`, `evidence`. Canary missions all `mode: ralph`.
- Route estimation: forecast = remaining route targets x overrun (APR-3). Canary XS need 406230 / S 1266053 (EXPECTED.md); actual goal `used` 6,097,042 at complete is the goal total, not canary-only (UNPROVEN canary share).
- No-user proof: canary 16:55:31 -> 17:53:28 (58 min, rows 899/961), human_gate 0 rows (`grep -c`). Pane silence not audited.
- EWC status: E1,E2 done; E3 was pause_budget (APR-4 dry-run: used 7.24M + forecast 16.9M unmeasured > envelope 22M) -- Owner decision pending: raise ewc envelope >= ~24.2M. E4-E6 not re-checked in APR-6 (UNPROVEN).
- Commits causal order (wt_apr): 6932f9b9 apr-1 judge; 830645ab apr-2 seal; 6a7c70a7 apr-3 tick lock/event/silence; 9da3e13f apr-4 fix (empty acceptance, git PATH); e0b767ae/b05c01f4/da2fd7eb canary c1/c2/c3. Live install: 741479f3, 66cb27d0, b4b91250, b2f2affb; ewc chain 9c0a195b.
- Change impact: before/after dry-runs install-before/after.json: apr, autonomy, cp50-c2 identical; ewc E3 -> pause_budget (intended); additive fields `class`,`trigger`.
- Suites at APR-4 install: receipt_judge 5/5, halt_continues 25/0, mission_steward 25/25, gsdx_chain 19/19, apr_seal 18/0, apr_event 25/0, gsd_mission 230/230, gsd_epoch 92/92, gsd_sweep_pass 11/11 (WU-APR4-receipt.md). Not re-run in APR-6.

## UNPROVEN
1. Mutation drill never run for apr-2/3 guards.
2. Coordinator pane sent nothing: inferred from triggers/modes only.
3. F1 seal.json absent for C2/C3; F2 refusal.json absent; causes unverified (PRODUCTION-REALITY).
4. F3/A8 mission layer "no receipt" vs closed C2 receipt; duplicate worker m-7a5265092233 (~77k tokens). Unfixed.
5. F4 repeated `residual_exhausted APR5` rows; alert dedupe unchecked.
6. APR-4 review not independent (no agent spawn).
7. Cross-project transfer of the UKDL candidates: not earned.
8. EWC E4-E6 behaviour under the new finalizer live.

## Next task
Fix A8 with a test (mission `no receipt` must use receipt_judge on the residual path; red then green, install like APR-4), then verify F1/F2 in code, then Owner: ewc envelope.
