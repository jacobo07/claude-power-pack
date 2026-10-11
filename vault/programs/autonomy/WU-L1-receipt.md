# L1 receipt
Status: DONE

Reconcile finished by the bootstrap pane 2026-10-11 (the L1 worker m-e85bbe12f33e stopped mid-rebase at call 27; its
handoff was this file). feat/ucda rebased onto live 696ce37a: S2 mission_spend (live capital-* + S2 programme-spend kept),
S3 gsdx_chain (live _residual + S3 is_parked/insert_continuation kept), R1 SUPERSEDED by live 696ce37a "bounded residual
re-arm" (same capability, another writer): conflicts resolved to live's side, R1 decide/tick code dropped. A stray line
left by the worker's sed accident (gsdx_chain.py:90) removed.
PROVEN after rebase: CHAIN_PASS 18/18, REG_PASS 8/8, PROGRAMME_SPEND_PASS 13/13, land_worktree 10/10 (pytest).
chain.json max_residuals=2: a breaker-halted unit now re-arms from its steward residual with zero model (live mechanism).
Landing: REFUSED REBASE_CONFLICT (landings/L1-land.json): live moved to a871ec2a and EVC U5 05340d39 conflicts in tools/gsd_mission.py. Branch intact at 1d5660b8. The released L1 worker m-e85bbe12f33e continues: rebase onto current live, resolve U5 vs live hold code (live wins when unsure), land with land_worktree, then overwrite this receipt.
