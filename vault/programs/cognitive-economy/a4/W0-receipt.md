# A4 W0-residual receipt

- W0 first-call floor: 18,739 tokens (sonnet-5-5, MEASURED by pane 0f9b771b from the worker transcript). Slim gate <= 60k: PASSES.
- P0: commits 83ef9a7b (B0 entry matrix) and eb32996a (estate-queue) by a background worker (m-7b90ad628c1e); no refusal.
- W0 spend: 1,451,117 processed vs 1.2M stop. Cap crossed; cause = 34 tool calls vs 28 planned and context growth (18,739 -> 86,065), not the floor.

## This unit (W0r)
- Finished W0 step 3: `python tools/entry_matrix.py --capabilities --out <file>` regenerates CAPABILITY_MATRIX.md; new `--check FILE` exits 1 if FILE differs byte-wise or any row derives UNREACHABLE.
- Green pole: `--capabilities --check vault/programs/cognitive-economy/a4/CAPABILITY_MATRIX.md` -> identical=True, unreachable=[], exit 0.
- Red pole: tools/test_entry_matrix_capabilities.py::test_red_planted_unreachable (temp repo, planted orphan core anchor -> UNREACHABLE, `--check` exit 1) -> OK, exit 0.
- test_green_identical passed in the first full run (52s: git grep per branch is slow on the real repo). That run's red test failed because it omitted --capabilities; fixed, rerun alone OK.
- Matrix: 18 rows; 9 have agrees=NO vs the card (3, 4, 6, 11, 12, 14, 15, 17, 18); 2 UNKNOWN (6, 15).
- Commits: W0 files (tools/entry_matrix.py, ce-capabilities.json, CAPABILITY_MATRIX.md, test), then this receipt.
- Not touched: vault/plans/ce-a4-L0-lifecycle-scan.md, vault/plans/route-L0.json.