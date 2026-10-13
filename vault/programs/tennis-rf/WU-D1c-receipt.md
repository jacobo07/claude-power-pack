# WU-D1c receipt
Status: DONE_WITH_LIMITS
gate_rc: 0
limits:
- DETERMINISTIC_USED_MODEL is a pure function (chain_pre.used_model) with tests; it is NOT yet fed the ledger's model-call count by receipt_judge/chain (no cheap per-unit count source was read). Wiring is a follow-up.
- A MODEL/SEARCH worker finds results at the deterministic path `<packet>.pre.json` and the arm row carries `pre_json`; the arm-chain command line was not changed (no card argument exists), so the worker is not told the path automatically.
- pre never runs in --dry-run (it has side effects); residual re-arms skip pre (it ran for the original packet sha).
- On a pre_failed unit the .pre.json persists; the Owner edits the packet (new sha) to rerun.

Evidence (code in claude-power-pack: tools/chain_pre.py new, one hunk in tools/gsdx_chain.py `_tick_locked`, 11 new gates in tools/test_gsdx_chain.py):
- test_gsdx_chain 30/30 (was 19; RED 3 FAIL before the hunk), test_receipt_judge 5/5, test_claim_evidence 9/9, test_apr_seal 21/0, test_apr_event 26/0, test_gsdx_reforecast ALL PASS.
- Mutation drills (isolated copies): `if rec.get("rc") != 0` -> disabled = KILLED by V-PRE-FAIL-NO-ARM; deterministic close disabled = KILLED by V-PRE-DETERMINISTIC-CLOSES.
- Kill switch CPP_CHAIN_PRE=off: V-PRE-KILL-SWITCH. Timeout (rc 124, process tree killed, cap 900): V-PRE-TIMEOUT, -CAPPED. Once per sha: V-PRE-ONCE-PER-SHA. P1P2-shaped replay (DETERMINISTIC, pre writes DONE receipt, no worker, successor then arms): V-PRE-P1P2-NO-WORKER.
- Bugs found by the tests: quote-strip of a command that itself starts/ends with a quote; Windows shell timeout left the pipe held for the full sleep (fixed with taskkill /T).
- gsdx_chain.py working copy was CRLF vs LF in the index (whole-tree noise); it is now LF and the commit diff is the hunk only.
