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

**NEXT.**
1. Watch W0/W1: `register.json`, and the frozen corpora committed before any slice code.
2. Watch `evidence/gsdx-ci/budget.md`.
3. At the closeout: judge the gates. Then ask the Owner about (a) deploying to the live PP clones and
   (b) moving any policy from advisory to enforcing. Neither is pre-approved.
