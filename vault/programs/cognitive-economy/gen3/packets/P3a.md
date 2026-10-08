# P3a -- recon-factory Phase 3a: verified SRC bundle seam + donor intake dry-run (GAP-2, GAP-6, GAP-12)

Mission: MISSION_ID_FILLED_AT_ARM (write this id in the receipt, mandatory).
Authority: Owner "y" 2026-10-08 (tranche ceiling raised to ~6.8M to finish the minimal path; gen3/TRANCHE-CP50.md).
Funds Phase 3a ONLY: never call promote() on the real ledger, never write src_registry.json, never compile locally,
never enqueue on GEX44, never arm a mission, never push.
Envelope (route-P3a.json, floor 110,835/call): expected 10 x (110,835 + 20k) x 1.2 = 1.57M (route target 1.6M) | warn
1.75M | HARD STOP 1.9M. Hard limit 10 tool calls. 0 subagents. NO search tools (Glob/Grep) at all.

## Corpus = ONE file
Read `C:\Users\User\.claude\skills\claude-power-pack\vault\programs\cognitive-economy\gen3\recon-reforecast\P3A-DOSSIER.md`
once. It carries the verbatim source of every levels.py function you touch or call (AST-extracted, with line numbers),
the real row shapes, the facts that shape 3a and SEAM POLICY v1. Read no other file (levels.py is edited with Edit using
the dossier's verbatim text as old_string). Anything not in the dossier is UNKNOWN: write it down, never look it up.
Implement policy v1 exactly; do not redesign it.

## Deliverables (recon work tree C:\Users\User\Apps\recon_work\wt_keosdtk_home)
1. `tools/wros/binary/decomp/levels.py`: policy items 1-7 (SRC_BUNDLES + Store path + Store.src_bundle; PINNED_COMPILER_SHA256;
   verify_src_bundle; the bundle branch at the top of check_src; _src_unbacked + its call in promote(); GAP-12 manifest keys;
   src_intake dry-run). Without a bundle, check_src and promote() behave byte-for-byte as before.
2. `tools/wros/binary/decomp/test_src_seam.py`. Gates print `PASS/FAIL V-SEAM-*`, final `SEAM_DRILL=n/m`. Bundles are written
   to a tempfile directory passed through load_store(paths={"src_bundles": tmp}); use a registered id from the dossier
   with its real source sha256 and store.words. Monkeypatch levels.X.run and levels._run_objdiff to raise, so any local
   compile FAILS the gate:
   - V-SEAM-GOOD: a bundle that verifies -> SRC dimension PROVEN with no compile.
   - V-SEAM-SWAPPED: target_words_sha256 of another id -> not PROVEN, token TARGET_MISMATCH.
   - V-SEAM-WRONG-SRC: wrong src_sha256 -> not PROVEN, SRC_SHA_MISMATCH.
   - V-SEAM-DISAGREE: oracle_disagreement true, and separately objdiff 99.0 -> not PROVEN.
   - V-SEAM-PLANE: host_plane "LOCAL" -> not PROVEN, PLANE_NOT_GEX44.
   - V-SEAM-FORGED: _src_unbacked on a computed row with SRC PROVEN from checks={"SRC": lambda ...} and no bundle -> the
     id is returned; control: the same row backed by the GOOD bundle -> not returned.
   - V-SEAM-NOBUNDLE: with no bundle dir the check_src path is the original one (assert the bundle branch is not taken,
     e.g. X.run monkeypatch is reached and raises the drill's sentinel).
   - V-SEAM-INTAKE: src_intake() report counts equal the dossier's expected intake; src_registry.json sha256 unchanged.
3. Do NOT run `test_levels.py` / `test_levels_revalidate.py`: they compile locally with the real toolchain (forbidden)
   and return INCONCLUSIVE below the 2,048 MB floor. Record both as `NOT-RUN (local compile; runs with the GAP-1 GEX44
   runner)` in SUMMARY and receipt. V-SEAM-NOBUNDLE is this lease's regression guard.
4. `.planning/workstreams/recon-factory/phases/03a-src-bundle-seam/03a-01-SUMMARY.md` (<= 40 lines; carries the plan):
   drill and regression lines verbatim, intake counts, open points (registry write and bulk promotion are 3b; the GAP-1
   runner must emit this bundle schema).

## Call plan (10)
1 Read dossier. 2-4 Edit levels.py (at most 3 Edits, sequential, each one consolidated). 5 Write test_src_seam.py.
6 One PowerShell call (absolute python `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`, cwd = the decomp
dir, PYTHONIOENCODING=utf-8): test_src_seam.py only. 7 one fix if
needed (else skip). 8 Write SUMMARY. 9 Write receipt
`C:\Users\User\.claude\skills\claude-power-pack\vault\programs\cognitive-economy\gen3\P3a-receipt.md`. 10 One PowerShell call:
commit levels.py + test_src_seam.py + SUMMARY in the work tree, then the receipt in the PP repo, each by pathspec
(`git add -- <paths>; git commit -F <msgfile> -- <paths>`; git = `C:\Program Files\Git\cmd\git.exe`), then print both
`git log -1 --format=%h %s`.

The recon work tree has ~568 dirty `.ksr_vault` paths owned by other sessions: never stage, restore or clean them.
Do not edit ROADMAP.md or STATE.md.

## Receipt (<= 20 lines)
Mission id, calls used, files + commit hashes, drill and regression lines verbatim, intake counts, open points. Spend is
metered by the control plane. Ending on a question counts as a failure. End with `HANDOFF NOTE: P3a done` or the blocker.
