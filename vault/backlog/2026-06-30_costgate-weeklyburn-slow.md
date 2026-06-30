# Finding — cost_gate.weekly_burn is 13.6s (pre-existing, not N1)

**Found:** 2026-06-30, during CO-08 (N1) runtime verification. **Priority:** P2.
**Scope owner:** CO-01/CO-02 (Operating Economics / Governor) — Sprint 4.

## What

`modules/wrapper/cost_gate.py::weekly_burn` calls `token_ground_truth.window_output(24)`
and `window_output(168)`, each of which **reads every recently-touched transcript in
full** (`fp.read_text()` over the whole file). With ~45 mtime-recent transcripts this
measured **13,656 ms** in isolation. Inside `prelaunch.run` it is capped by a 1.0s thread
timeout and the process `os._exit(0)`s past the still-running thread, so the launch is not
hung — BUT:

- the **weekly-burn advisory never actually renders** (it always exceeds its 1.0s budget
  and returns empty), so the D1 dashboard from Weekly-Burn-RCA is effectively dead;
- every kclaude launch wastes ~1.0s waiting on that timeout → prelaunch overhead ~2.1s,
  over the wrapper's stated **<2s** design budget.

## Why it is not N1

Empirically attributed (2026-06-30): `scheduler.admit` (the CO-08 gate) = 94ms; the gate
runs concurrently inside the same 1.0s window cost_gate already forces, so it adds ~0
marginal launch wall-time. The slowness is entirely pre-existing in W5.

## Fix (when CO-01/CO-02 lands)

Apply the same bounded **tail-read** optimization N1 used in
`scheduler._last_turn_within`: `window_output` only needs per-turn output within a time
window; it can stat-prefilter (already does) and then read a bounded tail / stream rather
than `read_text()` the whole file. Target: weekly_burn < 200ms, prelaunch < 1.2s.
Add a perf gate (`V-W5-WEEKLY-FAST`) to lock it.

## Interim

No action needed for correctness — fail-open already protects the launch. This is a
performance + dead-advisory defect, deferred to the economics sprint, recorded so it is
not silently normalized.
