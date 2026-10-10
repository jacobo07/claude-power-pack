# S3 receipt
Status: DONE
Commits: see `git log -1` on feat/ucda (tools/gsdx_chain.py, chain_registry.py, chain_registry_tick.ps1, test_chain_registry.py, vault/programs/chains.json, vault/programs/sidecar-liveqa/chain.json).
PROVEN: test_chain_registry 8/8 (two-unit relay zero model; N chains isolated; parked chain/entry arms nothing; held/PARKED mission -> action `held`, not `running`; continuation insert re-points successor and relays A->Ab->B; kill switch; shipped registry). test_gsdx_chain 13/13 unchanged.
PROVEN (mutation drill): REG_MUTANT=no-parked (is_parked disabled) -> V-REG-HELD-NOT-RUNNING RED, 7/8.
NOT_PROVEN: parked-chain guard has no own mutant drill (covered by 3 gates, not mutated); live scheduled task not registered; tool not landed to live PP.
BLOCKED_HUMAN-ish (no stop): replacing PP-GsdxChain-Tick/PP-DglChain-Tick/PP-AutonomyChain-Tick with PP-ChainRegistry-Tick (tools/chain_registry_tick.ps1) needs landing via the S1 tool, then Task Scheduler change; gsdx/dgl registry entries are enabled=false until that cutover so no double-arming.
Sidecar chain: 4 units B-P3..A-experiments, enabled=false/parked; packets for B-P4/B-park/A-experiments and the route do not exist (Stage B compiles them). io-liveqa untouched.
Next unit must know: autonomy chain tick still runs via chain_tick.ps1 until cutover; landing S3 = ff of feat/ucda via land_worktree.
