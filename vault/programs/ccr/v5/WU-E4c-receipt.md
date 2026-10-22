# E4c receipt
Status: DONE_WITH_LIMITS
Limit L1 (route call cap): the route allows 8 calls. Two sessions have now run: the first tripped the hook at 13 calls with the canary not started, and this residual session found the same state with about 5 calls spent on re-deriving it. The canary needs at least 12 calls: arm --no-launch, envelope with the phase lease, admit, launch, observation, evidence, receipt, and cleanup. No A11 check was observed. evidence-E4c.md is not written, so the done-check is not met.
Mission m-f55d74d74795 stopped with 13 model calls and 363,524 tokens. Its only salvage was a refused cleanup command, not canary work. The partial receipt names no commits, and I did not verify its ledger rows.
Reforecast: the E4b actual was about 50k tokens against a 1,600,000 target, so the 1.3x gate did not fire. Free RAM was 6.0 GB, above the floor.
Open point (HUMAN GATE candidate): who sweeps the phase breaker is undecided. A manual supervise cycle would work. The PP-CcrChain-Tick task is a human gate and I did not enable it.
Next step: rerun E4c with a 25-call route and the same 1,400,000 target.
K7 row: this residual session ~7 calls, ~40k tokens, no canary spend. The earlier session spent ~90k.
