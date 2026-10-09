# P2a receipt

Mission: m-f501c31d6523 (worker transcript f4f23b86). Status: DONE, local half only (7/7). Nothing was sent to the VPS
or GEX44 and nothing was pushed. The worker built and drilled the plan but did not commit, because the session guard
denied the commit at its stop. The main pane closed the lease without a model call: it reran the drill, wrote the
SUMMARY and committed.

Files (recon work tree wt_keosdtk_home): tools/wros/binary/decomp/gex44/{stage,capsule_build,reproduce}.py,
tools/wros/binary/decomp/oracle_parity.py, tools/wros/binary/decomp/gex44/test_p2a.py,
.planning/workstreams/recon-factory/phases/02-oracle-parity-s1/02-03-SUMMARY.md. Diff: 4 files +402/-17, plus the new
test.

Drill (main-pane rerun): PASS V-P2A-ROOT / CAP / MUTANT / CAPSULE / BUILD / RETURNED / F-UNTOUCHED -> P2A_DRILL=7/7.
- AA capsule cap1-1241eae606f3 holds 41 units (40 drawn plus the main:800ECE30 mutant, 1 byte at offset 51), and
  verify_manifest is clean.
- A/A returned leg on return 032929: 51 judged, 0 dropped, 51 AGREE. A planted wrong reference row reads DISAGREE.
- Factory root: the dossier's own tree_digest reproduces 08787a444f6c... over 5976 files, so the root is unchanged
  since before the lease.

Builds in the RF root: 211354Z, 211412Z and 215900Z (the drill rerun). All three have payload sha256 34cc3993bcf7dd10...
and there is no jobs ledger, so nothing has been enqueued. P2b sends 211412Z only.

Metered by the main pane (worker transcript f4f23b86, usage deduplicated by message.id): 14 model calls, 2,396,336
processed (56,399 out). That is OVER the 1.85M stop by 546,336, and it equals the breaker's figure. Control: the same
script gives P3a 2,353,284 over 16 calls, matching its receipt exactly.

P2b open point 1 (runner source: worktree or HEAD) is decided by the bytes; there is nothing left to choose. The git
blob hashes of runner_lib.py (254b335c) and match_runner.sh (8a515d34) are identical at HEAD 1f72401, in the work tree,
and in the copy staged in 211412Z. 211412Z was built with runner_source=worktree and records source_commit 6226c88, a
commit from before the P2a code was committed. That is a provenance note only: the runner and the payload are
byte-identical either way.

Open: the AA_GATE verdict needs P2b's single job, which is not funded.

HANDOFF NOTE: P2a done (local half)
