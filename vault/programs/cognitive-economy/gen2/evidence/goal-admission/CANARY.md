# Goal budget admission -- live canary, 2026-10-07

**Verdict: FAIL on the overshoot bound; PASS on refusal reach and post-deny containment.**

Setup: goal `canary-20261007`, cap 3,000,000 processed tokens, lease_calls 2, roots = the canary work
dir; two headless `claude -p --model sonnet` workers bound by cwd AND `CPP_GOAL`, told to loop Reads
and spawn one Agent. Live code: guard sha256 `2FE660A8...` (main checkout == ce/goal-admission b79f4737,
merged as c12138da); live dispatcher `6C8BF09F...`; settings `Task|Agent -> PreToolUse-Agent-default`.
Wall 251 s.

## Measured (independent: raw transcripts, ledger code not used -- scratchpad canary/measure.py)

| worker | files | requests | processed tokens | first deny (ledger used) | after first deny |
|---|---|---|---|---|---|
| 79f9c88f | 2 | 22 | 1,963,307 | 18:46:38Z (3,771,750) | 1 request, 98,836 |
| 9adc4255 | 3 | 25 | 2,210,521 | 18:46:47Z (3,973,468) | 1 request, 101,524 |
| **total** | 5 | 47 | **4,173,828** | | 200,360 |

Overshoot vs cap: **1,173,828 (39%)**. Ledger final settled 3,973,468 + post-deny 200,360 = the
independent total exactly, so the ledger's accounting is faithful up to its last settle.

## What held
- Every worker reached a GOAL BUDGET deny and stopped within ONE further request (~100K each): a
  plain permissionDecision deny contains the pane; `{continue:false}` was not needed.
- The Agent lane fired live: three subagents admitted, each with an agent hold in the journal.
- No call ran ungated after the deny; no UNKNOWN was admitted.

## What failed
~970K was spent BEFORE the first deny: the first refusal already saw used 3,771,750. The declared
bound (per pane: one lease + the crossing call + the in-flight turn) is wrong.

Hypothesis (UNVERIFIED -- next session's first task): the gate measures only at tool calls and only
what is already written, while five concurrent requesters (2 workers + 3 subagents under the same
sids) spend ~100K per request; leases of ~180K are smaller than the spend between two observations,
and requests that end in text (a subagent's final answer) pass no gate at all. Candidate fixes to
evaluate, not yet chosen: count each live subagent as its own requester in the bound and the lease;
size the Agent hold from measured subagent cost instead of the parent's per-call; refuse new Agents
once remaining < (requesters x per-call).

## Also found
- Renewal churn: parallel calls in one pane renew repeatedly at the same measured value (journal
  rows 39-46, four settles at 1,358,752). Not over-counting (each settle closes the prior lease) but
  one extra python spawn per parallel call.
- Instrument defect (fixed by hand here): canary.py merged stderr into stdout, a `SessionEnd hook
  ... failed` line broke the JSON parse, and the driver reported independent_total 0 and 0 denies --
  a zero from an instrument that never looked.

## Relevance to A1
A1 crossed a 20M cap by 22.3M (111.5%) with no pre-call refusal at all. Here the refusal reached
every pane; the residual is a ~1.2M absolute overshoot from concurrency. That is not yet the zero
unauthorized overshoot the done-gate asks for, so goal admission is NOT declared done.
