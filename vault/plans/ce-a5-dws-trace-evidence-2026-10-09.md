# DWS trace evidence (read-only, 2026-10-09, deterministic scripts dws_trace_mine.py / dws_session_shape.py)

- 312 transcript files, 10,985 deduplicated calls, 3.10 B context tokens (input + cache read + cache write; includes the 09-28 anomaly).
- Context per call: p50 265,345 · p90 429,546.
- Subagents: 9,455 calls (86 %) and 2.70 B tokens (87 %). Main sessions: 1,530 calls, 0.40 B.
- Agent dispatches: 132 (94 general-purpose, 11 gsd-executor, 7 plan-checker, 6 planner, 4 code-fixer, 3 verifier, 3 reviewer, 3 researcher).
- Session length: 64 of 311 sessions ran > 60 calls and carry 84.4 % of tokens; 14 ran > 150 calls and carry 45.6 %.
- First-call context (fixed floor before any work): p50 102,225; executor subagents start at ~150 K.
  Floor alone ~ 102 K x 10,985 ~ 1.1 B of 3.1 B (~36 %) — baseline rent, not semantics.
- Largest single sessions: Sonnet subagents of 609 / 472 / 400 / 406 calls, context climbing 150 K -> 490-510 K; top 10 ~ 1.3 B (~42 %).
- Tool steps ~ 1 per call (12.9 K tool_use for 11 K calls): calls are serial single-tool steps.
- Reads: 3,946 over 1,060 paths (3.7 per path). STATE.md 123, completion matrix 85, ROADMAP 35, orca-runtime.ts 99.
- Shell: `Set-Location` prefix 1,576; `sleep 1` 157; `until` poll loops 37 -> polling control loops.
- Measurement caveat: "calls without tool_use" from the first script is invalid (streamed blocks share a message id); not used.
