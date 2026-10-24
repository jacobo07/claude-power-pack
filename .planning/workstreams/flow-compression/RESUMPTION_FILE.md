# RESUMPTION — flow-compression

Identity: GSD X Autonomous Flow Compression. Runs on GEX44 in `~/missions/flow-compression` (branch
`mission/flow-compression`); the worker's own worktree is `.claude/worktrees/flow-compression-w`
(branch `worktree-flow-compression-w`) — keep committing there. Laptop copy m-0bd772045f65 is HELD.
Never push, never edit GEX44's live install; the laptop coordinator fetches and lands.
Thesis: missions lose time to idle control-plane states and in-worker compaction, not to relay latency.

State: Phases 1-2 SEALED (committed on worktree-flow-compression-w). P1 closed live (epoch1 wall -> epoch2 CONTEXT_ROTATION; preamble ~105k tokens/epoch).
P2: arm_preflight in tools/gsd_mission.py, tools/test_arm_preflight.py 16/16, existing suites green.

Decisions: GSD Core untouched; policy in GSD X. Rotation 0.70 x compaction line. Debt not ours: V-AMCR-ONE-RESOLVER-INVENTORY (37/38).
Test-only env: CPP_RESOURCE_ADMISSION=off when host RAM < 3000 MB. Never push. Git as plain separate commands; commit msg via -F file.

Next 3 actions:
1. Phase 3 (S3): identical launch refusal with no causal delta -> backoff hold naming unblock condition (the 53 relay_held NO_PHASES repeats are the replay case); normalised packet digest (EOL/BOM); mission_steward._r1 writes a new path; DEFER autopsy.
2. Phase 4 (S4) mission_spend.judge variance is not a stop.
3. Phases 5-8 per ROADMAP.md.

Start: read ROADMAP.md, then `/gsd-autonomous --ws flow-compression`.
