# UZ evidence
Status: DONE_WITH_LIMITS (RAM_HOLD)
- Source check: ccr-v5 mods/cpp-cognitive-runtime/hooks policy.ts 531 / register.ts 410 lines; line-by-line identical to active 0.1.0-54f1824b (zero differing lines, COMPAT still 2.1.296). PASS.
- Host: claude 2.1.302.
- RAM gate: free physical RAM 3.51 GB then 3.46 GB, below the 4 GB requirement -> RAM_HOLD. Probe, gates, COMPAT widening and release NOT run.
- Probe table: not testable (held). Gate counts: not run. Released id: none. Post-release diff: n/a.
- Next: rerun WU-UZ when >= 4 GB free; source check already clean.
