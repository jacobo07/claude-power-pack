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

Spend: NOT YET METERED. The breaker figure of 2,396,336 is the supervisor's estimate, not a meter. Obligation 2 meters
worker f4f23b86, deduplicated by message.id, and updates TRANCHE-CP50.md.

Open: P2b open point 1 (runner source: worktree or HEAD) must be decided before any send. The AA_GATE verdict needs
P2b's single job.

HANDOFF NOTE: P2a done (local half)
