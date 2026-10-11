# APR2 receipt
Status: DONE

Commit: apr/self-closing in wt_apr (see git log): `tools/gsdx_chain.py` (finalizer, seal/refusal, classes, human_gate, try_seal), `tools/test_apr_seal.py`.

- PROVEN 17/17 `tools/test_apr_seal.py`: E2-shape (no Status, commit, gate rc0) -> seal + arm B; receipt bytes untouched; false-DONE (gate rc1) -> refusal, no arm; FALSE_DONE no-steward deadlock -> residual packet written by finalizer, arms; DONE+pass arms; no-acceptance unchanged (0 gate calls); cache (1 run over 3 ticks, rerun on new HEAD, refusal cached); timeout -> refusal; require_commit; same fingerprint on top rung -> human_gate, different fp -> not; classes UNCLOSED_RECEIPT/NO_RECEIPT/WORKER_STOPPED; try_seal ok + fail-closed; real runner timeout awaited.
- PROVEN no regression: test_gsdx_chain 19/19, test_receipt_judge 5/5, test_halt_continues 25/0, test_mission_steward 25/25.
- RED (old code, tick kwargs shimmed): E2 -> stopped_without_done; false-DONE -> arm B (the bug); deadlock fixture -> arm B; cache/timeout fixtures fail.
- Schema: `<receipt>.seal.json` {unit, verdict DONE, sealed_by, receipt_status, receipt_sha256, gates[{argv,rc,tail}], commits, head, at}; `.refusal.json` same + verdict FALSE_DONE, reason, fingerprint, fingerprints[]; `.gate.json` cache {sha, head, passed,...}. Acceptance: {gates, cwd, require_commit (default false), files, timeout_s (default 600)}.
- NOT_PROVEN: mutation drill (tools/mutation_drill.py) not run; live tick not exercised (inert until APR-4).
- Next unit: `try_seal(packet, missions=None)` returns {"sealed": bool, seal, result}; tick(...) takes gate_runner/git injection; residual rows carry `class` and `evidence`; actions new: human_gate, wait_finalizer. Calls used: ~14.
