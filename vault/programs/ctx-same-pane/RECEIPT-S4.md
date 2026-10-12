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
