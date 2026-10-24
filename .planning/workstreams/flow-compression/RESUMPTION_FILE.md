# RESUMPTION — flow-compression

Identity: GSD X Autonomous Flow Compression. Runs on GEX44 in `~/missions/flow-compression` (branch
`mission/flow-compression`; the worker may enter its own worktree branch). Laptop copy m-0bd772045f65 is HELD.
Never push, never edit GEX44's live install; the laptop coordinator fetches and lands.
Thesis: missions lose time to idle control-plane states and in-worker compaction, not to relay latency.

State: S1 (rotation invariant) code + tests landed by the arming pane; its Production Reality is Phase 1.
Coherence anchor: `tools/test_rotation_invariant.py` ROT_PASS=16/16 and its no-op mutant goes red.

Decisions: GSD Core untouched; all policy in GSD X. Rotation at 0.70 x compaction line (measured: host compacts
at ~87 % of `--autocompact`). Pre-existing debt, not ours: V-AMCR-ONE-RESOLVER-INVENTORY (37/38).
Test-only env: `CPP_RESOURCE_ADMISSION=off` when host RAM < 3000 MB (launch tests are otherwise refused).

Next 3 actions:
1. Phase 1: read this mission's epochs/ledger; record rotation evidence and rehydration cost.
2. Phase 2: arm_preflight() reusing existing checks; replay historical structural escapes.
3. Phase 3: admission refusal-loop backoff + packet identity.

Start: read ROADMAP.md, then `/gsd-autonomous --ws flow-compression`.
