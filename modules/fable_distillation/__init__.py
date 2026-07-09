"""modules.fable_distillation -- EXECUTION-mode activation of the Fable Advantage
Distillation Suite (FD-00..FD-07, datasets sealed under SCS C82).

This package turns the sealed architecture datasets into live code on the real
session path:

  fd_00_gate     -- FD-00 admission gate: the Delta-Only law's admission clause as
                    a four-valued verdict (ADMIT / DECLINE / ROUTE_CHEAPER /
                    ANSWER_FROM_ASSET). Advisory, fail-open -> ADMIT. Never blocks.
  fd_07_flywheel -- FD-07 close-boundary loop: at a frontier session's Stop it
                    extracts+classifies this session's deltas, triages each to a
                    destination, writes it back idempotently, and reports loop
                    health THROUGH CO-12 (never a parallel metric).

Both are honest to the datasets' anti-duplication boundaries: the gate CONSULTS
CO-03/CO-05 (never re-implements routing), the flywheel REPORTS through CO-12
(never forks the metric) and RIDES the GK-08 Stop hook (never new plumbing).
Guarantee level (CO-10): advisory today; the dispatcher + kclaude wiring makes the
close-boundary the one rung-3 enforcement point.
"""
