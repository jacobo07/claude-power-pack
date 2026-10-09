# A4 W0-residual -- finish the matrix, write the W0 receipt (Owner y 2026-10-09)

Goal ce-a4 (cap 16.6M). cwd = this worktree. Read THIS packet and W0.md only; no transcripts. Envelope: stop 480k,
<= 12 tool calls; commit early. git = & 'C:\Program Files\Git\cmd\git.exe';
python = & 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'.

W0 (m-7b90ad628c1e) committed 83ef9a7b (B0 entry matrix) and eb32996a (estate-queue), then its breaker stopped it at
1,451,117 processed > 1.2M (34 tool calls; context 18,739 -> 86,065). It left UNCOMMITTED: tools/entry_matrix.py (M),
vault/config/ce-capabilities.json, vault/programs/cognitive-economy/a4/CAPABILITY_MATRIX.md. These are W0's; do NOT touch
vault/plans/ce-a4-L0-lifecycle-scan.md or vault/plans/route-L0.json (another unit's).

1. Read the three W0 files. Finish W0 step 3 only: one command regenerates CAPABILITY_MATRIX.md byte-identical;
   a planted unreachable capability turns it red. Test both poles; record exit codes.
2. Commit those three files (+ the test) by pathspec; verify `git log -1 --format=%s`.
3. Write a4/W0-receipt.md (<= 25 lines): W0 first-call floor 18,739 (sonnet-5-5, MEASURED by pane 0f9b771b from the
   worker transcript; slim gate <= 60k PASSES), P0 = commits 83ef9a7b/eb32996a by a background worker, no refusal;
   W0 spend 1,451,117 vs 1.2M stop (cap crossed: cause = calls 34 vs 28 and context growth, not floor); this unit's
   commits, tests and exit codes. Commit it.
End with `HANDOFF NOTE: W0r done` (or the blocker).
