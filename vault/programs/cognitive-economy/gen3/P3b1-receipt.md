# P3b1 receipt
Mission id: UNKNOWN (not in the packet or dossier; written by gsd_mission.py at arm time). Calls used: 9 (packet 1 + dossier 3 reads, Edit, 2 Writes, 1 run, 1 commit/receipt).
Files (recon work tree, tools/wros/binary/decomp): levels.py (register_src), gex44/src_bundles.py, gex44/test_p3b.py, .planning/workstreams/recon-factory/phases/03b-capital-promotion/03b-01-SUMMARY.md. Commit hash: see git log -1 on branch keosdtk-home.
P3B_DRILL=10/10 (V-P3B-REGISTER, REGISTER-REFUSE, GOOD, SWAPPED, WRONG-SRC, DISAGREE, PLANE, FORGED, IMPACT, REAL-UNTOUCHED all PASS).
ENTITIES=294
CAPSULE=cap1-984a35109f79 trim=['census'] (untrimmed over ceiling 78407680 > 71303168)
BUILD=reproduce-20261009T193108Z task_sha256=5bd8add80c2e5d37bcd5181f265fe578e95c12d12fa242b6fe4a2c770c79013d reproduce.units=294
Open points: (1) out_root used <gex44>\capsules, not <gex44> as the packet said (build() default layout). (2) DISAGREE: OBJDIFF_NOT_100 precedes ORACLE_DISAGREEMENT in verify, so the latter is tested on a tampered bundle. (3) register_src needs donor `source` as text; all 289 had it in the drill. (4) src_bundles.py was re-saved by PowerShell with a UTF-8 BOM (Python accepts it). (5) Mission id unknown. No send, no real-ledger writes.
HANDOFF NOTE: P3b1 done
