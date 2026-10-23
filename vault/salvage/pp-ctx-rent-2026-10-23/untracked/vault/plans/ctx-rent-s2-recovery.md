# ctx-rent S2 recovery and replay: execution plan (PROPOSED, awaiting Owner y/n)

Written 2026-10-08 by a fresh pane. Succeeds `ctx-rent-RESUMPTION.md`; read that file first.

## Verified state (2026-10-08)
- Worktree `C:\Users\User\Apps\pp-ctx-rent`, branch `ctx/rent`, HEAD `0f8713fe` (spec).
- Dirty: `tools/rollover.py` (+2/-1), `tools/rollover_replay.py` (+42/-10), the RESUMPTION file.
- The diff matches the reported intent: `is_certify_command`, `certify_call` in the trace,
  `calls_to_certify` / `protocol_overhead` / `no_certify_call` in `fresh_cost`, and a
  `PROTOCOL_P90` rehydration basis that keeps the old figure as `upper_bound_p50`.
  `_economics` accepts the `PROTOCOL` prefix.
- Goal `ctx-rent`: used 6,033,002 of a 6,000,000 cap, bound to root `pp-ctx-rent`. Any pane
  whose cwd is in this root binds to that spent goal, and this pane now does.
  A new goal on this root is a rebind, and a rebind needs `goal-declare --owner`, which requires an
  interactive TTY (an agent shell does not have one).

## Defects to test before trusting the diff (hypotheses, not findings yet)
- H1 certify false positive: the regex matches any `rollover.py certify` command, including a
  refused certify (`certify_refused`) and `--help`. The commit detector requires a successful
  tool_result, and certify detection should require the same.
- H2 floor double count: `protocol_overhead = sum(ctx[:cc])` includes the successor's first-call
  floor. Check whether `n*` in `decide` already prices the floor ("fresh = floor + capsule/4"). If it
  does, C must exclude it.
- H3 survivorship: samples with no certify call are dropped. If those samples skew long, p90 is
  biased low. Report `no_certify_call`. The fallback to `UPPER_BOUND` below `min_samples` already
  exists, so the question is the share of samples dropped.

## Proof (deterministic, no reviewer agent)
`tools/test_rollover_replay.py`, `test_rollover.py`, `test_rollover_active_path.py`,
`test_rollover_economic.py`, plus these new red-path gates, each paired with a control:
- `V-RR-CERTIFY-DETECT`: a successful certify is counted. Controls: a refused certify, `--help`,
  and an echo of the text are not counted.
- `V-RR-PROTOCOL-NOT-WORK`: work after certify is excluded from C. Mutation: revert to the
  first-mutation sum and the gate must go red.
- `V-RR-NO-CERTIFY-NOT-ZERO`: a missing certify gives None or the UPPER_BOUND fallback, never 0.
- `V-ROLLOVER-PROTOCOL-BASIS`: `_economics` uses a PROTOCOL basis. A basis it does not recognise
  stays UNDETERMINED.

## Envelope (one Work Unit lease; the ctx-rent program cap stays separate)
The measured floor is about 124k tokens per call and this pane costs about 150k per call, so 2M buys
about 13 calls. That is too few for 4 suites, one repair cycle, a commit and the replay.
Lease: 3.0M, with stop at 3.0M and warn at 2.4M. Inside it: 0.4M proof reserve and 0.3M checkpoint
reserve. The checkpoint reserve covers the receipt, the capsule and the next-frontier note, and
funds no substantive work.

## Progress contract and trip wires
Expected durable artifacts, in order:
1. Suite results.
2. A repair commit, or none if no repair is needed.
3. The S2 commit.
4. A replay receipt at `vault/receipts/ctx-rent-s2-replay.json`.
5. The gate decision.
6. A capsule.

Trip: if spend reaches 1.0M with no suite result, or 2.0M with no commit, stop new work,
checkpoint and diagnose. A second identical failure triggers a pivot (Regla 12). A third failed fix
escalates to the Owner (HR-ONESHOT-003).

## Replay (deterministic, `rollover_replay.py`, no model)
Run the same 7-day ledger and decision corpus under two arms with the 150K gate held fixed:
- OLD: `UPPER_BOUND_P50` ≈ 1.79M.
- NEW: `PROTOCOL_P90`.
Record per arm:
- n decisions
- KEEP / ROTATE / UNDETERMINED / UNKNOWN counts
- the transition matrix between arms
- predicted rotation point (resident at the first ROBUST_ROLLOVER), p50 and p90
- C, protocol p50/p90, the floor, `no_certify_call`

The 292/666 claim is verified, corrected or rejected from these counts.
Also measure the p50 prior as a sensitivity arm, so that p90 is chosen on evidence rather than
inherited from the diff.

## 150K gate rule (decided only after the replay)
- KEEP_CURRENT_GATE: under NEW, UNDETERMINED falls to ≤ 1/3 of the OLD count and the predicted
  rotation p50 is below about 300k.
- LOWER_GATE: residual late rotation remains (p50 ≥ 400k) and the gate, not the economics, is the
  binding constraint in the remaining cases.
- REPLACE_GATE: the gate binds in cases where the economics say ROTATE at all sizes.
- UNKNOWN: anything else, recorded as UNKNOWN.
The gate is never mutated in the same commit as the prior.

## Self-hosting
- This pane works only on S2 and keeps tool output small: one command per call, results go to
  files, and summaries stay short.
- After the S2 commit and replay, it seals a `/kclear` capsule (SAFE_TO_FORGET).
- S3–S8 run as a `/cpp-gsd-long` Ralph mission, the existing owner of fresh-session continuation,
  so no new lifecycle code is written.
- Any successor gets this file, the receipt and the capsule, never the bootstrap prompt.

## S3–S8 admission
Blocked until the S2 Done-Gate passes. Each row is then recompiled from the replay with Proof of
Non-Work and ownership reconciliation (ce-lifecycle, A4, Presence, gen2). A row the corrected prior
makes moot is closed as unnecessary, not executed.

## Production Reality
A replay shows what the decider would choose. It does not show live behaviour.
- Live rotation is claimed only after a canary where a real pane rotates earlier and the successor
  starts near the floor.
- Until then the status is CODE_VERIFIED + REPLAYED.
