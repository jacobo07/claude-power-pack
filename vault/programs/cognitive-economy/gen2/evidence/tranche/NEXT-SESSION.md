# Next session: close tranche context-runtime-3

Repo: C:\Users\User\.claude\skills\claude-power-pack, branch feature/knowledge-acquisition, at 2ea65ca2 or later.
Nothing has been pushed. Commit by pathspec only; other sessions write in this tree.

## Where it stands (sealed)
- S6 driver `tools/tranche_driver.py` (V-DRIVER 21/21). Workers run in a git worktree outside ~/.claude (`--root`),
  because headless sessions cannot Write under ~/.claude, and explicit Edit allow rules do not lift that.
- S1 PASS (8cb4de07..59db2f35): CPP hooks add 3,051 first-call tokens (ON 105,454 vs OFF 102,403). Host-forced share
  UNDECIDED. Biggest controllable item ~/.claude/CLAUDE.md (39,809 chars) REJECTED, pending an Owner decision.
- S3 PASS (e5a88eb3, 711a2be5): `tools/wake_check.py --consume <repo> <goal>` moves the Goal through GoalLog.
  Unit scope only: no real goal is bound and nothing schedules it.
- S4 `cep_gen2 --tranche` merges re-run results and meters the coordinator from `<name>-tranche.json` (14/14).
- S5 PASS (599bd751, c7ca71d8), verdict UNDECIDED. Its files were written through PowerShell after Write refusals,
  so review them before relying on them. The live mutant was not run.
- S7 BLOCKED_BY_OWNERSHIP: ukdl-universal.md carries another writer's uncommitted hunks.
- Nightly 02:00 ran 2026-10-07 02:00:01 with result 1 (floor gate red), so that clause is no longer WAITING.
- Gate: `python tools/cep_gen2.py --tranche context-runtime-3` -> FAIL on spend 24,521,947 > 7,200,000 (workers
  ~6.08M; coordinator e6e0eca7 ~18.4M). This is the true result. Do not re-baseline the manifest to make it green.

## Owner decisions (answered 2026-10-07: "all rec")
1. S5: ACCEPT 599bd751/c7ca71d8 after a diff review (read-only, no re-run). If the review finds a defect, re-run
   S5 through the worktree driver instead.
2. Floor: FIX THE HARD RULES COMPILER SOURCE (vault/hard_rules/HARD_RULES.md and its compiler; drop the stub entries
   HR-001..007 incl. the test entry HR-002 from the ~21k-char mirror in the project CLAUDE.md). Do NOT edit
   ~/.claude/CLAUDE.md. Prove it with the S1 probe pair (same class, before/after first-call tokens).
3. Wake: DEFER. Bind no goal and do not schedule `--consume` until the floor gate is green; otherwise the
   nightly job fires a wake every night. Ask the Owner for the goal id at that point.
4. UKDL: WAIT for the other writer's hunks to land; do not fork into a new file.

## Rules for the next session
- New tranche name with its own manifest (cap + coordinator sid + baseline from self_spend at start).
- Coordinator under 6 calls. Every fix-and-relaunch loop goes to a worker packet, never to the coordinator pane.
- Meter the coordinator before every relaunch.

Start: read this file; the decisions above are answered. Build worker packets for items 1 and 2 only.
