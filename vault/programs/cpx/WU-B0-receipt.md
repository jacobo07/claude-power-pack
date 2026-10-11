# B0 receipt
Status: DONE
- Settle: goal-settle cp50-c2 session 3cf66819 measured 799548 -> open 0, used 10,462,272, remaining 3,537,728 (cap 14M).
- cpx chain: B0,R1,R2,R5,R9 (R9 waits C3-receipt.md; packet says Status DONE needed). cp50-c2 chain: R3,R6,J3,C3,D21F (envelope 4.3M, max_residuals 0). Packets WU-*.md written.
- TRF W2 not armed (W4 running): amendment appended to tennis-rf/WU-W2.md (trim port + OUT_BUDGET check).
- Task PP-Cp50ChainTick: NOT registered, auto-mode classifier denied Register-ScheduledTask (Unauthorized Persistence). tick script ready at cp50-c2/chain_tick.ps1; Owner/pane must register (clone PP-CpxChain-Tick action, replace programs\cpx with programs\cp50-c2). Until then the cp50-c2 chain does not tick.
- Cap 14M->16M: capital-apply refused (packet must be a JSON capital packet; JSONDecodeError on my markdown). Skipped; R3+J3+C3 fit about 4.34M vs remaining 3.54M -> raise still needed before C3; open item.
- K7: estimate 0.4M, actual not measured (no per-call meter in this pane).
