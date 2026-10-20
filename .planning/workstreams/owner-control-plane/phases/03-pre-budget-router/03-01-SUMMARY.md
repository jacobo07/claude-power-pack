# 03-01 SUMMARY
D9a fixed: `apply_pending` resolves the transcript per approvals row (`candidate_transcripts`, cap 16), never `[-1]`. Uppercase packet sha now binds (case-folded both sides). Null/missing transcript rows no longer raise. Gates: V-OCA-D9A-APPLY-PENDING-PER-ROW, V-OCA-D9A-NULL-AND-MISSING-TRANSCRIPT-ROWS, V-OCA-UPPERCASE-SHA-BINDS. OCA_PASS=19/19 (RED 16/19 before the fix). Commit 817dc01a.
Deferred: sibling `tools/mission_spend.py:690` `correction_apply_pending` has the same `[-1]` defect.
