# C23b progress — a new work-unit packet starts a fresh worker

Facts appended as found (2026-10-05). Work done in worktree `.claude/worktrees/cwops-c23b` (branch `cwops-c23b`
from 75691a64): the background-session guard refuses edits in the shared checkout.

1. Owner epoch: `owner.epoch = rec["epoch"]` at adoption (tools/gsd_mission.py:852, :1409), so a worker
   launched after `envelope --wu-packet` has owner epoch > the epoch at which the packet was set
   (launch transitions bump epoch). A worker that predates the packet has owner epoch == packet epoch.
2. `decide_turn_end` already reads `rec["continue_max_tokens"]` (tools/gsd_epoch.py); the CLI had no setter.
3. Plan: `set_envelope` records `wu_packet_epoch = rec["epoch"]` only when (path, sha256) changes; new rule in
   `decide_turn_end` after children-HOLD and in-flight-continuation, before the token ceiling.
4. Red first: `test_gsd_epoch.py` EPOCH_PASS=86/87 (V-EPOCH-NEW-PACKET-ROTATES-FRESH: "context 180002 < 300000
   tokens: same session continues"); `test_gsd_mission_envelope.py` failed on the 5 `wu_packet_epoch` checks
   (None) and then TypeError on `continue_max_tokens=`.
5. Green: EPOCH_PASS=87/87, ENVELOPE_PASS=39/39.
6. Mutant drill (rule block removed, mutated `gsd_epoch.py` preloaded into `sys.modules`, the real
   `test_gsd_epoch.py` run against it): EPOCH_PASS=86/87, exit 1, the failure is
   V-EPOCH-NEW-PACKET-ROTATES-FRESH. The rule is the only thing that turns that case.
7. Regression, all exit 0: MC_PASS=225/225, MV2_PASS=72/72, G23_PASS=32/32, OWNER_HOLD_PASS=12/12,
   MSPEND_PASS=20/20.
8. No live mission record was touched by this work unit: no CLI was run against a real mission; the new
   tests build their records in `tempfile` dirs.
