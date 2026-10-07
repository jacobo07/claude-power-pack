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

## Diagnosis (2026-10-07, successor session; raw transcripts + journal, no ledger code)
Instrument: `diag.py` beside this file. The hypothesis above is **refuted** for this run. The
"first deny at 3,771,750" was the first `GOAL BUDGET` *tool_result*; the **ledger** refused much
earlier, at journal row 57 (18:46:10Z, used **3,005,579**, 5,579 over the cap). Each of the
following refusals (rows 57-66) is a settle with no reserve after it. Between a refusal and the deny,
`closeout()` (built for the session-envelope breaker) turned the goal deny into an *allow* for
Read/Grep/Glob, 4 per sid, and passed the refusal only as advisory context ("SESSION BUDGET TRIPPED
... closeout call n/4 allowed"). The canary's workload is only Reads, so all 4 were used each time.
The 5th refusal per sid was the first real deny (79f9 row 64, 9adc row 66): an exact match.

| component | tokens | source |
|---|---|---|
| used at the first ledger refusal | 3,005,579 | journal row 57 |
| 9adc crossing call (on a 364-token lease, row 48) | 174,777 | rows 55->58 |
| closeout-admitted Reads, 4 per pane (8 requests, ~98-101K each) | **793,112** | transcripts, `tools=['Read']` |
| final text reply after the real deny (1 per pane) | 200,360 | transcripts |
| **total** | **4,173,828** | = the independent total, exactly |

- **Closeout allowance in goal mode: 793,112 = 68% of the overshoot.** This is the defect.
- Subagent final answers: **0** requests after the first refusal came from a subagent file. Refuted.
- Agent hold sized from the parent's per-call: no part of the overshoot. Refuted as a cause.
- Tool-call-only observation: the residual it explains (crossing call + final reply, ~375K, about one
  per-call per pane at each end) is the declared bound working as designed, not a breach of it.
- Side finding: each advisory appears twice per call in the transcripts (two `attachment` rows), and
  a refused renew whose measured value did not move writes no journal row, so the journal
  under-counts refusals made by parallel calls.

Fix (Owner choice "handoff writes only", landed 19240f98): a goal refusal admits one write to a
handoff/plan/RESUMPTION path per pane and no Read/Grep/Glob. Expected residual per pane is one
crossing call plus the final reply. NOT yet re-measured live: the rerun canary is the done gate.

## Canary #2 after the fix (goal `canary-20261007b`, 2026-10-07 19:58Z, wall 196 s)
Same prompt, cap 3,000,000, lease_calls 2, two sonnet workers; guard at 19240f98. Driver
`canary2.py` (stderr kept separate; diag.py measurement), receipt `receipt_canary-20261007b.json`.

| worker | files | requests | tokens | ledger refusal (seq) | deny tool_result | after refusal |
|---|---|---|---|---|---|---|
| 6e022dd5 | 2 | 19 | 1,683,073 | 20:00:46.821 (51) | 20:00:46.912 | 1 request, 98,623, no tools |
| 7aa64450 | 3 | 18 | 1,524,285 | 20:01:06.625 (54) | 20:01:06.696 | 1 request, 96,461, no tools |
| **total** | 5 | 37 | **3,207,358** | | | 195,084 |

- Overshoot **207,358 (6.9%)**, was 1,173,828 (39%). Closeout advisories: **0**. Each pane's first
  refusal was its deny (one refusal per sid in the journal, versus five each in #1).
- Decomposition: 195,084 = the one final text reply per pane after the deny; the remaining 12,274
  is the spend that crossed the cap before the refusal.
- Inside the declared bound (per pane: crossing call + in-flight turn). **Not zero.** The final reply
  after a deny is a model request that no PreToolUse hook can gate. Zero needs headroom: refuse at
  cap - (live requesters x per-call). Whether this residual counts as authorized is the Owner's call.

## Relevance to A1
A1 crossed a 20M cap by 22.3M (111.5%) with no pre-call refusal at all. Here the refusal reached
every pane; the residual is a ~1.2M absolute overshoot from concurrency. That is not yet the zero
unauthorized overshoot the done-gate asks for, so goal admission is NOT declared done.
