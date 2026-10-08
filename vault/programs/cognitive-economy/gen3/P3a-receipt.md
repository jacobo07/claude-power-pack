# P3a receipt

Mission: m-789229da3a6f (supersedes m-302d70eabd59). Status: DONE (8/8). No promote(), no registry write, no local compile,
no GEX44 enqueue, no push.

Calls: over the 9-call plan. Dossier Read, 3 levels.py Edits landed (Store/constants, check_src+functions, promote) plus one
promote Edit pair blocked by the anti-thrash gate (parallel same-file edits, my error), 1 Read of levels.py region, 1 consolidated
Edit, Write test, run, Write SUMMARY, Write receipt, commit. Spend metered by the control plane.

Files (recon work tree wt_keosdtk_home): tools/wros/binary/decomp/levels.py, tools/wros/binary/decomp/test_src_seam.py,
.planning/workstreams/recon-factory/phases/03a-src-bundle-seam/03a-01-SUMMARY.md. Commit hashes: see HANDOFF below / git log.

Drill: PASS V-SEAM-GOOD / SWAPPED / WRONG-SRC / DISAGREE / PLANE / FORGED / NOBUNDLE / INTAKE -> SEAM_DRILL=8/8
Regression: test_levels.py NOT-RUN (local compile; runs with the GAP-1 GEX44 runner); test_levels_revalidate.py NOT-RUN (same).
Intake: 289 MATCH donors, 289 sha-backed, 0 already registered, 289 would_register, 0 refused; src_registry.json sha unchanged.

Open: registry write + bulk promotion = 3b; GAP-1 runner must emit schema ksr.decomp.src_bundle/1; donor id/source field
shapes inferred defensively (289/289 matched live); promote() path with a real bundle unexercised.

HANDOFF NOTE: P3a done
