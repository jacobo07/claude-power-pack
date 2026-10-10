# WU-C10 -- Holdouts + cross-domain canary

Common brief: `vault/programs/cdc/PROGRAMME.md`. Plan section: 3 (C10).

Goal: universality, not QuickLease overfit.
1. Holdout traces NOT used in C1-C8 design: Live QA packet workers, Clock A (e0cd1dbb, be97307b), intent/order
   (ec66dcff), DWS. Use EVC U8 replay harness if landed, else rollover_replay / C1 roles. For each: roles, avoidable
   share under CDC rules (breaker trip point, admission denials, reread, proof closure), scope-normalized table.
2. Live cross-domain canary: one bounded non-PP task (pick a small open item in TUA-X or KobiiCraft backlog that is
   safe and read-mostly, or a docs-only change) run as a slim mission with CDC guards on; record calls, tokens,
   denials, incidents. No deploy, no push.
3. Report `vault/programs/cdc/evidence/holdouts.md`. Land via land_worktree.
