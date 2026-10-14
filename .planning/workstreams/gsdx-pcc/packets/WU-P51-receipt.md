# WU-P51 receipt -- wave 5.1 residual (GEX44 Linux driver)
Status: DONE
Missions: predecessor m-9eb6bbaadb29 (laptop, stopped PARTIAL at budget) + GEX44 residual driver (this clone, branch mission/pcc-p51r).
Commits: predecessor 5d8e967f (RED hermetic gate), fdc0c18b (hermetic mutation suite); this run b30b3f88 (semantics test: usable git), be0b5482 (Part B: 05-CROSS-PLATFORM.md, logs, D15, STATE), plus the WU-P52 commit and this receipt (see git log).
Gates, Linux plane (GEX44, Linux 6.8, py3.12.3), logs `phases/05-*/logs/05-51-linux-*.log`:
- GSDX_PCC_SEMANTICS_PASS=48/48 (first run 46/48: test-side Windows git path, fixed b30b3f88, product code unchanged)
- GSDX_PCC_REPLAY_PASS=28/28 ; GSDX_FRONTIER_PASS=40/40 ; GSDX_INVALIDATION_PASS=26/26 ; GSDX_JUDGE_VALIDATE_PASS=11/11
- GSDX_MUTATION_HERMETIC_PASS=5/5 (first POSIX run: hard kill via os.killpg at 21.1 s, entry tree byte-identical, 58/58 CAUGHT in the copy)
- liveness `python3 modules/liveness/reachability.py`: **exit 1, 2 offenders** (cognitive_os/hibernate_runner, session_resilience/snapshot_versioning). RED, not papered over. Same at HEAD without my edits; laptop log 05-05-liveness-green.log was exit 0 (312 reachable vs 310 here). Cause: scan seeds from the live ~/.claude install, which on GEX44 never references those two. Inferred from seed logic + empty grep, not from the laptop's hook files. Not declared in the registry.
Windows-plane evidence from the predecessor (not re-run here): hermetic 5/5 (RED was 3/5), d3 KILLED, 58/58 in a copy; logs 05-51-hermetic-*.log, 05-51-d3-windows.log.
Proof kinds (05-CROSS-PLATFORM.md): PORTABILITY = d3, 58-mutant verdicts, semantics/replay/frontier/invalidation/judge_validate, hermetic outcome. Everything else PLATFORM (Windows). Liveness = NOT portable.
DENOMINATOR rows moved: D15 evidence (d3 KILLED on both planes, tree dd6c4ba3). STATE.md: Phase 5 CLOSED, planes named; does not claim more than WU-P52 compiled in this run.
Predecessor patch did not apply (section-sign encoding in context lines); same edits made by hand.
Burn: predecessor 7.30M + this run: see drive.log (the driver measures it).
WU-P52 route: 127 calls x 118K x 1.2 = 17.98M <= target 18M <= cutoff 24M; warn 21M, stop 24M. Plan s6 says 150 calls: 23-call gap (150 would need 21.2M). Receipt at ~80% of need (14.4M).
Open: (1) liveness host-dependence -> N19 / done-gate registry (in WU-P52 inputs). (2) The residual note contained no concurrent-writers text; WU-P52 uses the concurrent-writers-shared-tree rule instead. (3) Windows semantics 48/48 predates the _usable_git edit (same executable chosen there). (4) Linux leg of N17 is the coordinator's.
HANDOFF NOTE: WU-P51 done -- WU-P52 (trust core) compiled
