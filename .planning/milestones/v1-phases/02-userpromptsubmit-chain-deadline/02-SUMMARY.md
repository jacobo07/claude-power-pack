# Phase 2: UserPromptSubmit chain deadline — Summary

**Measured:** 2026-09-19 · session `37cfb187` · host 32,061 MB total

## The question

The phase was written from two readings — 19.4 s and 17.1 s against a 15 s cap,
with an 11.5 s internal deadline — and asked one thing: measure the gap between
the chain starting and its deadline clock starting, then say whether **the cap**
or **the clock** is the defect.

## The instrument

The harness's 15 s cap starts at **process spawn**. The chain's deadline clock
starts at `runChain()`, `hook-dispatcher.js:751`. Everything in between — node
startup, module load, reading stdin — is spent against the cap and is invisible
to the deadline. So the real budget is `cap − startup − flush`, never `cap`, and
that startup term had never been measured.

Rather than guess it, the measurement went on the dispatcher's **existing**
`CLAUDE_DISPATCH_DEBUG` stderr line (added for the scratchpad fast path, same
file, same reason): `startup=<ms>` and `deadline=<ms>`, computed as
`process.uptime()` at the instant the deadline clock is taken. Env-gated, so it
costs nothing when nobody is asking, and it keeps answering for every future
change to this chain.

## The numbers

Real dispatcher, real chain, real payload, `--event=UserPromptSubmit-chain`,
`config_invalid=0` and `runnable=6/6` on every run, n=5, medians:

| | value |
|---|---|
| free RAM (before → after) | **4,965 → 4,984 MB of 32,061 (15.5 % free)** |
| **startup: spawn → deadline clock** | **42 ms** (38, 42, 42, 52, 65) |
| total chain wall time | 3,589 ms (2,513 · 3,158 · 3,589 · 3,869 · 5,516) |
| chain deadline | 11,500 ms |
| harness cap | 15,000 ms |

## The cause, named

**Neither the cap nor the clock.** The gap the phase asked about is **42 ms** —
0.28 % of the 15 s cap and 0.37 % of the 11.5 s deadline. The clock does not
start meaningfully late, so the 3,500 ms of headroom between the deadline and
the cap is real and is not being consumed by unaccounted startup.

The 19.4 s and 17.1 s readings **predate the deadline mechanism**. The
`CHAIN_DEADLINE_MS` entry carries its own measurement — `15,173 → 6,595` — so
those overruns are what the deadline was introduced to fix. This phase's premise
was stale, and the honest finding is that the fix holds: on a host at 15.5 %
free memory the chain's worst of five runs was 5,516 ms, well inside both
bounds.

## What this does NOT establish

The **total** is a lower bound, not a worst case. The probe used a synthetic
session id and an empty `transcript_path`, so hooks whose cost is proportional
to the transcript did less work than in a real turn — and that includes
`jit_skill_loader`, historically the 11.4 s straggler that forced the deadline
in the first place. A payload that cannot reach the expensive path measures
startup, not the chain.

The **startup figure is unaffected** by that: it is taken before any chain work,
so the phase's actual question is answered on solid ground while the total is
indicative only. Measuring the straggler under a real transcript is the natural
follow-up and is not claimed here.

One reading was discarded rather than reported: an earlier batch invoked the
dispatcher as `--event UserPromptSubmit` (space form). The dispatcher requires
`--event=<chain>`, printed `CONFIG INVALID`, and recovered the chain from the
payload — its fail-safe working, not a defect. Those numbers came from a
recovery path and were re-taken rather than used.
