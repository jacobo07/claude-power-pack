# APR5 receipt
Status: BLOCKED_HUMAN

- FILES (committed, live checkout): vault/programs/apr-canary/{chain.json, WU-C1/C2/C3.md, route-XS.json, route-S.json, chain_tick.ps1, EXPECTED.md}. Dry-run tick: wait_writer C1 (held by my mission; expected).
- PRICES: XS calls 6 need 406230 / margin 487476 -> envelope 500000/575000/675000 ADMISSIBLE. S calls 12 need 1266053 / margin 1519264 -> envelope 1.6M/1.84M/2.16M ADMISSIBLE.
- NOT DONE: scheduled task PP-AprCanary-Tick was NOT registered. The auto-mode classifier denied Register-ScheduledTask (Unauthorized Persistence). I did not work around it.
- Needed from the Owner: run Register-ScheduledTask PP-AprCanary-Tick, cloned from PP-AprChain-Tick: wscript //B //Nologo hidden_launch.vbs <apr-canary>\chain_tick.ps1, 10 min, IgnoreNew, 9 min limit. Or approve a PowerShell permission rule.
- The canary was not ticked. Event-driven progression does not need the task; it only repairs.
