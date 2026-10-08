# R0 receipt -- A3b B0 salvaged (goal ce-a3b-r)

decision: salvage, not rebuild. The two B0 files from pp-ce-a3b (sha256 417432259B4EE2E0 / 2DF3C3DFB2F3FCDC, identical
copies) were valid with three known flaws. Done in the coordinator pane below the worker boundary (about 6 calls vs a
forecast of 8+ worker calls at the ~115k floor).

effect:
- tools/entry_matrix.py: skips its own source (flaw 1); the label says `no binding/ceiling ref found`, never
  "unbounded" (flaw 2); `sites` counts code lines only, and a launch named only in comments/docstrings stays listed
  as `mention only` (flaw 3).
- Finding corrected (MEASURED): the regex never matched argv-list launches (`[exe, "-p", ...]`). The old "28 of 35
  unbound" counted files that DESCRIBE a launch. Now: headless 34 files = 7 matched in code + 27 mention only; 28
  without any binding or ceiling ref. The headline survives, but 27 of the rows are UNJUDGED, not proven unbounded.
  A4 section 4 item 4 cites "28 unbound" -- read it as "28 with no ref, 7 code-matched".
- First fix attempt dropped the comment-only files entirely. It was caught by listing what the fix removed:
  tools/gsd_mission.py, llm_bridge.py, deep_research.py and agent_carrier_run.py are real launchers that would
  have read as absent.

proof: `python tools/test_entry_matrix.py` EMX_PASS=9/9. Mutant drills (isolated copies): comment filter + self-skip
removed -> 4/7 (3 red); mention-only rows dropped -> 6/9 (3 red). ENTRY_MATRIX.md regenerates byte-identical.

unknowns: which of the 27 mention-only files bind at runtime (B3/R7 canaries judge enforcement, not text).

refs: vault/plans/ce-a3b-recovery-2026-10-08.md sections 1, 4, 10; forensics/autopsy.py (raw-transcript autopsy
behind section 1, promoted by R5).

actual vs forecast: coordinator pane, not separately metered (UNKNOWN, est. 6 calls x ~130k). Forecast was 1.0M.
