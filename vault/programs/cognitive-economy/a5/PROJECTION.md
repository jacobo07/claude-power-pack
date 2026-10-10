# A5-U8 GSD STATE projection (DWS measurement)
Tool: tools/gsd_state_projection.py (STATE.md + ROADMAP.md + matrix -> JSON -> card). Card: A/data/dws-worker-card.md; JSON: A/data/dws-state-projection.json.

## Size (DWS STATE.md at repo HEAD 466b62d82)
- STATE.md 119,359 B / 1,101 lines (plan §1: ~53K tokens => ~2.25 B/token, calibration from the plan, not re-measured).
- Card 6,993 B (limit 8,192 B; without a changed-since list) = 5.9% of STATE.md bytes; ~3.1K tokens by the same ratio (ESTIMATE).
- Per-read saving ~49.9K tokens (estimate). Synthetic 1,100-line STATE also renders <= 8 KB (test).
- Card holds: frontier, changed since rev, blockers, open unknowns, proof state (matrix 76 rows: ABSENT 31, PARTIAL 33, PASS 11, UNKNOWN 1), pointers path#Lnn for the 134 decisions and every section.
- "Changed since rev" needs STATE.md at the rev; DWS STATE.md is git-excluded (.planning/), so there it degrades to a changed-files list plus a note. Not a fault, a limit.

## Trace corpus (A/data/calls.jsonl.gz, 10,985 calls)
- STATE.md Read calls: 119 in 47 sessions (65 main, 54 subagent). Label STATE_READ in TRACE-REPORT is wider (684: any .planning/ ROADMAP/matrix read) and is not the count here.
- Upper bound replaced by card: 119 reads (all 119 have 0 faults in the next 5 calls).
- Conservative: 47 reads. The other 72 are followed within 5 calls by an Edit of STATE.md (orchestrator state writes); these need the file for writing, the card does not replace them.
- Tokens: 119 x ~49.9K = ~5.94M processed-token-equivalents at read-result size (upper); 47 x ~49.9K = ~2.35M (conservative). Estimates; does not include the re-reads of that content carried in context after the read.

## Fault check (tools/a5_u8_fault_check.py)
Target kinds: planning/matrix/spec paths (state-derived) -> must be named or pointed to; shell/Grep/Glob/Agent/source files -> TASK (from the task prompt, not STATE; cannot be on a state card, not counted as fault).
- 3 sampled sessions (agent-a27c33b2c0f55b7a9 subagent 09-28; 0ad7757a main 09-30; d059600e main 09-30): 24 STATE reads, targets COVERED 50, TASK 55, FAULT 0.
- All 119: COVERED 218, TASK 382, FAULT 0.
- Iteration 1 of the card had no phase-dir/ROADMAP/matrix pointers: those targets would have been FAULTs (0ad7757a read 07-01-PLAN.md under phases/07-...). Schema fixed: sibling files, matrix path, phase-dir names added. Final: 0 FAULT.
- Weakness: COVERED accepts a basename or phase-dir match, so a pointer is not proof the worker finds the right plan file. Replay of a worker on the card was not run (no model calls allowed): the packet gate "replayed worker has no fault" is a static check only.
