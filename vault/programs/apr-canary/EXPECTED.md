# apr-canary EXPECTED
Rows (gsdx_chain tick/event), in order:
1. C1 armed. Worker commits canary/c1.txt, writes receipt without a Status line.
2. C1 finalized: sealed (try_seal, acceptance passes), NO renewal. C2 armed (trigger: event).
3. C2 attempt 1 writes Status: DONE and nothing else -> finalizer refusal (FALSE_DONE), residual written.
4. ONE residual arm of C2 (max_residuals 1; packet has "## Residual"); creates canary/c2.txt, commit, DONE -> sealed DONE.
5. C3 armed with row trigger: event; DONE; chain `complete`.

Max wall time: bounded-silence window per unit (APR-3) x 3 units + one residual; target < 90 min, hard bound 3 h.
Forbidden: any coordinator/human message to a pane; duplicate arm of the same unit+attempt; any human_gate; a C1 renewal; a 2nd residual.
Watchdog PP-AprCanary-Tick (10 min) only repairs; progression must not depend on it.

Prices (route_admission admit): XS calls 6 need 406230, with margin 487476, envelope target 500000/warn 575000/stop 675000 (ADMISSIBLE).
S calls 12 need 1266053, with margin 1519264, envelope 1.6M/1.84M/2.16M (ADMISSIBLE).
