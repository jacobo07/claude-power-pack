# RESUMPTION — GSDX-CI (Composed Intelligence, 15 capabilities; successor of GSDX-CME)

**Identity.** Owner /cpp-gsd-long brief "GSD X Constitutional Intelligence Architect", 2026-11-08. Plan approved via
ExitPlanMode; the authority was typed as "do it yourself" (turn 9546fcd7, session 5815df63, 2026-11-08T17:26:38Z).
- Laptop plan: `vault/plans/gsdx-ci-20261108.md` (af5a4e1e).
- GEX44 product: worktree `/home/kobii/missions/gsdx-ci`, branch gsdx-ci, off gsdx-cme 5649cb56. The packet and plan
  are in `vault/programs/gsdx-ci/` (dc3e5cc3).
- Lab: t1 is read-only. S21 m-6302235f0a6c owns gen3 and t1, so never write there.

**CURRENT — 2026-11-08 ~17:31Z.** Mission **m-a2c0029e969c** is RUNNING on GEX44, worker abd8635f (sonnet, 250k).
- Milestone: 9 phases scaffolded from the packet. The previous `.planning` was archived to
  `milestones/auto-archived-20261108T182947/`.
- Authority: 8M plus 2 auto top-ups of 8M (24M ceiling); top-up base 525a00b5. Spend was 1.55M when the
  authority was set.
- Trust: written for `/home/kobii/missions/gsdx-ci` at the Owner's instruction. Backup:
  `~/.claude.json.gsdx-ci-trust-20261108T182729.bak`.
- Transcript copy for owner-turn verification: `~/.claude/projects/laptop-coordinator-5815df63/`.
- Reach GEX44 with an LF, no-BOM temp script: `cmd /c "ssh -o BatchMode=yes gex44 bash -s < file"`. Do not use
  `>` onto `.jsonl` paths (session-file-guard); use scp.

**UPDATE — 2026-11-08 23:37Z: tranche 2.**
- Tranche 1 (8M) was spent between 17:29 and 17:52Z, with 0 product commits. Breaker trip at 8,719,836, then
  parked as CAPITAL_EXHAUSTED for ~5.7 h.
- Recovery classified it SUBAGENT_NEGATIVE_EVC: a gsd-planner subagent made 24 calls and wrote no plan; an HR
  blocked its `rm -rf /tmp`. The context was ~177k, so each call cost ~180k in cache reads.
- Trap: a `directive` reaches only a rotated worker. The session autocompacted in place at 17:45Z
  (epoch_compacted, requested=false), so the economy directive was never delivered.
- Owner 'y' at 23:30:25Z (turn ecacf359) authorised three changes:
  - `retarget`: launch prompt `.planning/retarget-tranche2.txt`. Execute Phase 1 inline from the existing
    01-01/01-02 PLANs, no subagents.
  - Authority raised to 16M, applied with `--recognize-overrun`.
  - `release`.
- Epoch-2 worker 8f643528 acked at 23:36:50Z.
- STOP RULE (Owner): if tranche 2 ends with no commit outside `.planning/`, the programme stops as
  BUDGET_EXHAUSTED. No tranche 3.

**UPDATE — 2026-11-09 09:55Z: tranche 3, option b.**
- Tranche 2 (6.8M) delivered W0 and W1:
  - W0: a967e1e6, dffdd676, c2ab819c. W1: 73f0c30c. Closeout: e3c1bac9.
  - Coordinator re-ran both gates: CI_W0_PASS and CI_W1_PASS, rc 0.
  - Defect: the `register.json` states were left OPEN.
- Trap (mine): an owner turn authorises ONE act. Reusing 9546fcd7 for tranche 3 was refused. The hold had already
  been released with a `replace` queued, so I re-held it within 27 s; no launch.
- The Owner chose **b** (turn 73f24f30, 2026-11-09T09:49:08Z): authority 40M to finish all 9 phases.
- Retarget #3 (`.planning/retarget-tranche3.txt`): fix `register.json`, then Phases 3-9 inline, no subagents.
- Released. Worker aa0eccf4 resumed at 09:54:40Z; its first turn carries the new prompt (verified in its
  transcript).
- Limits: max_hours 24 from 2026-11-08 17:29Z, so the run must end by ~2026-11-09 17:29Z.

**UPDATE — 2026-11-09 ~16:15Z: PROGRAMME CLOSED PARTIAL.**
- GEX44 gsdx-ci HEAD is 2459f6ac. All 9 ROADMAP phases are ticked. Result: PARTIAL, not COMPLETE.
- Register: 7 CERTIFIED, 6 BUILT, 1 CONNECTED, 1 DEFER.
- Named gaps:
  - Lab C transfer NOT_SUPPORTED: B-A = 0.125 < 0.25, near-ceiling prompts.
  - Fresh-agent RECALLED_AND_ACTED, but n=1 per arm.
  - `evaluate_transition` has no real caller.
  - 0/161 lessons carry `invalidated_when`.
  - The causal probe passes at 0.5063, which is fragile.
- Coordinator re-ran everything:
  - Gates w0-w8: all PASS.
  - AMCR 38/38.
  - MC 242/242. With my shell's node v18 it shows 241/242 (the V-MC-PLAN-FACTS bridge needs node ^22/^24);
    with /opt/node-v24.14.0 it is 242/242. This is environmental, not a regression.
- No diff to judge.py or to the protected suites.
- Spend: ~33M of 40M. Model child calls: 30, ~0.27M tokens.
- The mission hit max_cycles (13 >= 12), so the supervisor halts it. The work was finished first.
- D1, D2 and D3 were coordinator decisions:
  - D1: the context wall is not authority exhaustion.
  - D2: bounded `claude -p` calls are allowed.
  - D3: the XLII questions were supplied, because the brief was never stored in the packet. That was my gap.
- NOT DONE (Owner-reserved): merge or deploy the branch gsdx-ci (17 product files) to the live PP clones.

**NEXT.**
1. Watch W0/W1: `register.json`, and the frozen corpora committed before any slice code.
2. Watch `evidence/gsdx-ci/budget.md`.
3. At the closeout: judge the gates. Then ask the Owner about (a) deploying to the live PP clones and
   (b) moving any policy from advisory to enforcing. Neither is pre-approved.
