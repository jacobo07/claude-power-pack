# RESUMPTION — flow-compression

Identity: GSD X Autonomous Flow Compression. Runs on GEX44 in `~/missions/flow-compression` (branch
`mission/flow-compression`); the worker's own worktree is `.claude/worktrees/flow-compression-w`
(branch `worktree-flow-compression-w`) — keep committing there. Laptop copy m-0bd772045f65 is HELD.
Never push, never edit GEX44's live install; the laptop coordinator fetches and lands.
Thesis: missions lose time to idle control-plane states and in-worker compaction, not to relay latency.

State: S1 code + tests landed by the arming pane (`tools/test_rotation_invariant.py` ROT_PASS=16/16).
Phase 1 evidence written: `.planning/workstreams/flow-compression/phases/01/01-EVIDENCE.md` (36 historical
rotations, rotation first-commit median 3.2 min vs compaction 4.8, confounded). Epoch 1 of m-3d5f0a27e41d was
ended by the live context wall at 17% — that IS the live S1 firing; Phase 1 is not ticked until epoch 2 is seen.

Decisions: GSD Core untouched; all policy in GSD X. Rotation at 0.70 x compaction line. Pre-existing debt, not
ours: V-AMCR-ONE-RESOLVER-INVENTORY (37/38). Test-only env: `CPP_RESOURCE_ADMISSION=off` when host RAM < 3000 MB.
Shell hygiene: the worktree guard refuses commands that mention git inside heredoc/python text; keep git calls
as plain separate commands, and write helper scripts with the Write tool into `$CLAUDE_JOB_DIR/tmp`.

Next 3 actions:
1. Close Phase 1: `python3 tools/gsd_epoch.py epochs --mission m-3d5f0a27e41d` shows epoch 2 CONTEXT_ROTATION
   (trigger wall)? Record epoch-2 preamble tokens and minutes to first commit in 01-EVIDENCE.md; tick ROADMAP.
2. Phase 2 (design done, nothing coded): `arm_preflight(cwd, resume_command, ...)` in `tools/gsd_mission.py`
   next to `arm()` (~L5795). Checks: `lr.gsd_status` (NO_PHASES/ALL_COMPLETE refuse, UNAVAILABLE = unmeasured),
   `mission_launch_gate.refusal(rec,'arm',now)` (lineage), `resource_admission.refusal(slim_profile(rec) or
   'top-level-worker')`, `apply_rotation_invariant` diff (REPAIRED), authority presence (`authority_tokens` or
   `ledger_goal`). Injectable readers; returns {ok, checks[], refusal}; call in `arm()` before `create()` when
   launch=True and through `arm_chain`; kill switch `CPP_ARM_PREFLIGHT=off`; ledger row `arm_preflight`.
   Tests `tools/test_arm_preflight.py` V-PRE-*, including a mutant (always-pass) that must go red. Replay the
   NO_PHASES/low-memory cases from the ledger (prevented / moved earlier / legitimate).
3. Phase 3 per ROADMAP.md.

Start: read ROADMAP.md, then `/gsd-autonomous --ws flow-compression`.
