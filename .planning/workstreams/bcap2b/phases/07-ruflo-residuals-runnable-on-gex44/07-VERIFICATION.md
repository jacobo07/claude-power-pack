# Phase 7 Verification (BCAP2B-07)
- `python3 tools/test_bcap2_ruflo.py` -> PASS: 0 failing (includes dist poles driven on synthetic trees).
- `python3 -I vault/programs/bcap-2/ruflo/dist_identity.py <src> <installed>` reproduces the recorded JSON.
- HOLD kept: no install activated, no network, nothing written outside the sandbox and this worktree.
Verdict: closed as scoped; dist bytes and 4 advisories remain laptop/clean-room residuals (B4).
