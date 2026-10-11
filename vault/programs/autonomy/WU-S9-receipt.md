# S9 receipt
Status: DONE

Commit: see git log "S9:" (pathspec micro-commit).

## Claims
1. PROVEN UKDL: 6 entries appended to vault/knowledge_base/ukdl-universal.md (plumbing-not-intelligence, status cost O(1), programme authority survives rotation, unattributed spend = telemetry failure, experiment needs positive VOI, chain default-on). Dedup: grep of the six id/keyword families found no existing entry first.
2. PROVEN default-on: tools/chain_registry.py `discover()` ticks any vault/programs/<x>/chain.json the registry does not list; off only via registry enabled=false or "enabled":false/"parked":true in the chain file. test_chain_registry.py 10/10; mutant REG_MUTANT=no-default-on -> V-REG-DEFAULT-ON FAIL (9/10). Dry-run on the real tree: discovered apr, apr-canary, cp50-c2, cpx, ewc, tennis-rf; none would arm (running/complete/wait_event/pause_budget/residual_exhausted).
3. PROVEN retired: cpp-gsd-long "arm it again" text; steward residual text "otherwise the Owner/coordinator does" (test_mission_steward 25/25); tools/gsdx_chain_tick.ps1 (superseded by chain_registry_tick.ps1, no references); 160M prose in economic-engine-repair plan (marked superseded, enforced 65M).
4. Fixed stale V-REG-SHIPPED-REGISTRY (expected only autonomy; S8 added xdomain-canary).
5. NOT_PROVEN: fresh-project inheritance beyond S8's canary; existing generated *.residual.md files still carry the old wording (history, untouched).

## Next unit must know
- Discovery is live only after landing to the live PP and when the tick task runs that tree; the tick task still points at pp-ucda-wt.
- apr is residual_exhausted (APR5 BLOCKED_HUMAN) and ewc is pause_budget: discovery will now report them each tick; neither arms.
- Calls used: ~22.
