# Phase 7: X -> X-prime replay (GEX44, window 2026-10-25..11-01) -- ESTIMATE

Tool `tools/ctx_replay.py` (test `tools/test_ctx_replay.py` 7/7), data `replay-gex44-a7.json`.
Lever priced: A7 main-lean floor only. delta = 20,795 tokens/call (MEASURED on the laptop, L5 call-1), applied here as an ASSUMPTION
to interactive top-level calls, clamped to each call's own input. Workers and subagents untouched (canary is interactive-only).

| class (heuristic, APPROX) | sessions | calls | X processed | X-prime | saving |
|---|---:|---:|---:|---:|---:|
| mission_worker | 13 | 703 | 111.5M | 111.5M | 0% (not interactive) |
| kresume_successor | 24 | 135 | 11.9M | 9.1M | 23.6% |
| debugging | 101 | 1,110 | 104.3M | 81.4M | 22.0% |
| sparse | 416 | 1,666 | 121.6M | 90.3M | 25.8% |
| other | 487 | 12,949 | 1,256.4M | 989.9M | 21.2% |
| subagent | 37 | 1,120 | 161.6M | 161.6M | 0% |
| **total** | 1,078 | 17,683 | 1,767.4M | 1,443.8M | **18.3%** |

Not covered, stated plainly: (1) no `ksr_style`, `long_repo` or `coherent_large_context` session exists on this host in the window, so
CR-22 stays UNKNOWN; (2) quality of a counterfactual is UNKNOWN, the only quality evidence is the live L6 arm (n=3 pairs, one unit
class, 6/6 correct, 0 page faults, processed -27.8%); (3) these "top-level" sessions include non-interactive background jobs that this
host cannot tell apart from panes, so 18.3% is an upper bound on what interactive panes alone would save; (4) Safe-to-Forget (Phase 5)
is not built, so no content-removal saving is included. Do not add this figure to the MEASURED L5/L6 figures.
