STATUS: DONE
COMMITS: a6db93d1
GATE: python3 -I tools/test_a5_u8.py -> A5_U8_PASS=17/17 (round trip, 1,100-line synthetic card <= 8 KB, unknown section kept as pointer, mutant drop-blockers red, with admitting controls)
NUMBERS: DWS STATE.md 119,359 B / 1,101 lines (~53K tokens, plan calibration) vs card 6,993 B (~3.1K tokens, same ratio = ESTIMATE); source A/PROJECTION.md
NUMBERS: STATE.md Read calls 119 in 47 sessions (corpus A/data/calls.jsonl.gz); card replaces 119 upper bound, 47 conservative (72 are followed by a STATE.md Edit)
FAULT CHECK: 3 sampled sessions 24 reads, 0 FAULT; all 119 reads 0 FAULT (COVERED 218, TASK 382). Iteration 1 had faults (phase dir/ROADMAP/matrix pointers missing); schema fixed.
FILES: tools/gsd_state_projection.py, tools/a5_u8_fault_check.py, tools/test_a5_u8.py, A/PROJECTION.md, A/data/dws-worker-card.md, A/data/dws-state-projection.json
DEVIATIONS: no worker replay (no model calls allowed) -> "replayed worker no fault" is a static next-5-targets check; TASK targets (source files, shell, Grep) are not state-derivable and excluded from FAULT.
LIMIT: "changed since rev" cannot diff decisions for DWS (STATE.md git-excluded); gives changed-file list + note. Decision-blocker/unknown extraction is keyword-heuristic (some noise in decision ids).
LIMIT: token figures are bytes/2.25 estimates, not tokenizer counts.
HANDOFF NOTE: U9 can use A/PROJECTION.md numbers; a real worker replay on the card is still unrun.
