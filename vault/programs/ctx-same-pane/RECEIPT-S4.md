# ctx-same-pane S4 receipt (zero-model status)
Status: BUILT, NOT ACTIVATED. HALTED on stop-loss (calls). Capital packet bfccd115 (Owner approve 2026-10-12T22:21Z),
lease L7 cap 2,500,000. Executed inline by coordinator pane 5847a1a4.

## Probe (step 1): HOLDS
`claude -p estado --settings <temp settings with a UserPromptSubmit hook returning decision=block>` in a scratch dir:
result JSON `num_turns 0`, `total_cost_usd 0`, all usage 0, `result` = "UserPromptSubmit operation blocked by hook:
<reason> ... Original prompt: estado". No settings.json edit. The reason reaches the user with no model turn.

## Built (step 2)
- `tools/status_fastpath.py`: exact allow-list after accent/punctuation normalisation (estado, como va, status,
  how is it going, ...); projection = missions whose cwd is this cwd (state files, ~0.1 s), the session's bound goal
  via the LIVE PP mission_spend ledger, branch @ sha read from .git files, dirty tracked count via git with the
  remaining deadline (else "unknown"). Deadline 3 s, fail-open, kill switch CPP_STATUS_FASTPATH=off.
- `hooks/status-fastpath.js`: node shim; outer kill 6 s (interpreter start-up on a loaded host); any failure = pass.
- `tools/test_status_fastpath.py`: V-SFP 10/10 (matcher both poles, projection, kill switch, deadline, fail-open,
  node->python->JSON boundary: block, pass, garbage).
- Mutation drill (tools/mutation_drill.py, isolated copy): substring matcher -> MUTANT KILLED by
  V-SFP-MATCH-MIXED-REFUSED.

## Measured on this host (2026-10-13)
Host heavily loaded (40+ claude sessions): node start 9.5 s, git log 1.95 s, python start 0.3 s, goal ledger
import 0.83 s. Python path on the real worktree: 2.46 s (no goal) / 4.08 s (bound goal). Through the node shim with
a bound goal: 9.74 s -> pass-through. So under this load the fast path mostly falls back to the model; it is safe,
not yet fast. Faster on a quiet host is NOT measured.

## Not done
- Activation: registering hooks/status-fastpath.js on UserPromptSubmit in the live dispatcher is an Owner action
  (live hooks dir); the exact registration entry was not prepared in this slice.
- S1 close (items 4-5 not done, controllable floor ~25-30K provisional) is recorded in PP
  vault/programs/ctx-same-pane/RECEIPT-S1-CLOSE.md (c99dbf68): the goal fence refused the worktree while L6 was spent.

## Cost
Coordinator pane after the approval: 37 calls, 6,607,222 processed (context+output summed per call) against a
packet sizing of 16 calls / 2.2M. Stop-loss breached on calls; nothing was booked to L7 because the coordinator
pane is not goal-bound. Booking is an Owner decision.

## Booking (2026-10-13, Owner option 1)
Correction packet 12e74c71 (approve 2026-10-13T10:19:24Z) APPLIED: programme 28,889,796 -> 33,597,018.
goal-settle --measured 7,902,658 = S4 span 6,607,222 + correction step 1,295,436 (12 calls since
2026-10-13T08:21:55Z, scratchpad since_ts.py). Ledger after: settled 34,292,454, L7 used 7,902,658 of 2,500,000.
The correction step breached its own stop-loss (6 calls / 0.6M), so the goal is now ~0.7M over the approved
programme. Halted: L7 was not closed and nothing was raised. The calls for this receipt and its commit are not booked.

## GEX44: measured and ACTIVATED (2026-10-13, packet 4735ec4f, Owner approve 12:35:50Z)
Packet c695efbc was INVALIDATED (the 9,251,821 settle landed before it applied); 4735ec4f APPLIED, programme ->
37,641,617. Branch pushed as mission/ctx-same-pane-s4 (827711e5), cloned to GEX44 ~/missions/ctx-same-pane-s4.
Linux plane (load 1.1, 55 GB available): V-SFP 10/10 (CPP_NODE=/opt/node-v24.14.0/bin/node, CPP_PYTHON=python3,
CPP_STATUS_GIT=git). Shim end to end on 'estado': 296/205/51/55/47 ms, 5/5 block; mixed prompt passes (0 bytes).
Activation gate met: GEX44 ~/.claude/settings.json backed up (settings.json.bak-status-fastpath-20261013144607),
one UserPromptSubmit command hook added (node shim at the clone path, timeout 8 s). Live drive `claude -p estado`
from /tmp/sfp-live: num_turns 0, cost 0, the projection shown. ACTIVE on GEX44 only; the laptop stays unregistered.
Rollback: copy the backup over GEX44 ~/.claude/settings.json, or CPP_STATUS_FASTPATH=off.
