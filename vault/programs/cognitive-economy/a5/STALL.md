# A5 U7 -- semantic-progress stall trip (measured)

Source: A/data/calls.jsonl.gz (311 sessions, 10,985 calls, 3,106,974,814 tokens ctx+out). Progress = a MUTATION-labelled call (Edit/Write/MultiEdit/NotebookEdit or `git commit`; U1 proxy label). The guard's own progress set is the same tools plus any command containing `commit`.

## Gap between consecutive MUTATION calls (within a session)

n=2341; p50=1 p75=3 p90=9 p95=14 p99=34 max=103 (calls strictly between).

## Trip at K (fires when calls since last mutation > K)

| K | trips | TRUE (never mutated again) | FALSE (mutated later) | gaps>K | tokens cut after trip | share of corpus |
|---|---|---|---|---|---|---|
| 10 | 205 | 14 | 191 | 191/2341 = 0.082 | 75,248,468 | 2.42% |
| 15 | 120 | 13 | 107 | 107/2341 = 0.046 | 55,634,799 | 1.79% |
| 25 | 59 | 7 | 52 | 52/2341 = 0.022 | 30,567,848 | 0.98% |

Sessions with no mutation at all: 181 (58,008,491 tokens, 1.87%) -- mostly read-only subagents; a trip there cuts nothing the session was for, so the cut column counts only the tail past K.

## Rule and choice

Rule: K = the smallest K whose false-trip rate (share of mutation gaps longer than K) is <= 5%. Measured K = 14.
Existing DEFAULT_NOPROGRESS = 25; |25-14| = 11 vs 20 % of K = 2.8 -> NOT within 20 %: default changed to the measured K (env CPP_NOPROGRESS_K overrides).

## Honest bounds

- The cut is small (K=15: 1.79% of tokens; K=14 is between the K=10 and K=15 rows) because most spend sits in sessions that do mutate; the trip is a runaway bound, not a savings engine.
- Labels are a proxy. Receipt writes and matrix deltas are not separate signals here: a receipt is a Write (MUTATION); a bare matrix delta by shell is invisible to the proxy.
- FALSE trips are the price: K=14 stops about 1 in 20 gaps that would have ended in a mutation; the guard's closeout allowance then lets the worker write its receipt.
