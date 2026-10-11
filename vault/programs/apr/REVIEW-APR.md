# REVIEW-APR (APR-4 step 1)

Reviewer: the APR-4 worker itself (self-review). NO pp-code-reviewer / woz agent was dispatched: the worker had no agent-spawn tool.
This is NOT an independent review; the Owner/coordinator should dispatch the two agents if independence is required.
Checks run: full read of `git diff 7501d939..HEAD -- tools/gsdx_chain.py`; test_apr_seal 18/18, test_apr_event 25/25, test_gsdx_chain 19/19 after fixes.

| # | Sev | Finding | Disposition |
|---|-----|---------|-------------|
| 1 | HIGH | Seal on incomplete work: an `acceptance` with no gates/files/require_commit passed vacuously and sealed. | FIXED (reason "acceptance declares no check"; V-APR2-EMPTYACC). |
| 2 | MEDIUM | `_git` used bare `git`, absent from the scheduled task PATH: head=="nogit", commits empty (require_commit fail-closed, cache never keyed on HEAD). | FIXED (falls back to C:\Program Files\Git\cmd\git.exe). |
| 3 | MEDIUM | Finalizer gates run inside the tick lock with timeout_s up to 600 each; the event path 540 s budget does not cover them. Sweep stage is 600 s. | OPEN/accepted: no live chain declares acceptance until APR-4 step 5, and EWC gates are short; keep timeout_s <= 120 in chain.json. |
| 4 | MEDIUM | Budget forecast changes arm boundary for chains without new fields (arms later: counts all not-done units). | Accepted: spec item 5, test V-CHAIN-ENVELOPE updated; before/after dry-run shows no live difference. |
| 5 | LOW | FALSE_DONE refusal files accumulate only per receipt; fingerprints list grows by one per new head. Bounded by human_gate. | Accepted. |
| 6 | LOW | `silence_check` alerts once per (goal, action, unit) forever (no re-alert after resolution+recurrence beyond history window 400 rows). | Accepted. |
Hunt list: double arm under event+tick -> exclusive lock + re-read under lock (tested with 2 real processes); unbounded retry -> residuals capped by max_residuals, human_gate on repeated fingerprint; silent stall -> alert after silence_s; FALSE_DONE never advances (decide: refusal removes from done).
