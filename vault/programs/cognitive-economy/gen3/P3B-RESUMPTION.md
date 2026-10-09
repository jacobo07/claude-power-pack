# RESUMPTION -- recon-factory Phase 3b (capital promotion of the 289 donors)

Identity. Recon worktree C:\Users\User\Apps\recon_work\wt_keosdtk_home (branch keosdtk-home). PP repo gen3 ledger
vault/programs/cognitive-economy/gen3/. Thesis: matches already proven elsewhere become canonical L3 through promote()
only, each backed by a verified GEX44 SRC bundle. Owner "go ahead" 2026-10-09.

State (2026-10-09 ~17:00):
- 3a DONE (P3a-receipt.md, 03a-01-SUMMARY.md, SEAM_DRILL 8/8). levels.py has verify_src_bundle, the check_src bundle
  branch, the promote() SRC_UNBACKED refusal, GAP-12 manifest keys and a src_intake dry run. 289 MATCH donors,
  289 sha-backed, 289 would_register, 0 refused.
- Phase 2 DONE (recon fa66cbc). The GEX44 A/A PASS uses judge runner_lib 7377ff0f.
- RF Phase 3 cap = 2 jobs (recon e068c54). RF_CURRENT_PHASE is still 2; set it to 3 only at the first 3b send.
- Not run: test_levels.py and test_levels_revalidate.py need compiles, so they wait for GEX44 objects.

Decision recommended (re-read before the packet): assemble `ksr.decomp.src_bundle/1` LOCALLY. Use the returned GEX44
object, the receipt (host_plane, runner sha, produced_utc), the local split-judge verdict (oracle_parity: match_py
verdict + reloc_verified) and the objdiff pct already in the receipt. Do NOT change runner_lib.py: a new runner revision
would void the C5 judge identity that today's AA_GATE PASS certified. If a bundle field cannot be sourced locally, write
it UNKNOWN and stop; never edit the runner silently.

Split (mirrors P2a/P2b):
- P3b-1, LOCAL, worker lease, no send. Steps:
  - a donor capsule builder (289 units, reproduce/candidate mode as the dossier dictates);
  - the local bundle assembler;
  - the real src_registry writer through its existing writer (GAP-6), counting registered vs refused-at-intake;
  - promote() driven by bundles;
  - a revalidate-impact report on the 5 existing PROVEN rows;
  - a drill with red controls: swapped object, wrong src_sha, disagreeing oracles, a forged bundle, and promote()
    refusing without a bundle;
  - one build. NO send.
  Lease: P3a 2.35M/16 calls and P2a 2.40M/14 calls are the measured class -> ceiling 2.4M, stop 1.75M.
- P3b-2, main or fresh pane:
  - pre-checks (PINS, slot_ledger, GEX44 idle), then send (job 1 of 2), wait, repatriate;
  - judge locally, assemble the bundles, promote;
  - verify that SRC PROVEN rises from 5 by exactly the accepted count, each with a transaction row (both oracles AGREE),
    and that the refused rows are named.

Next 3 actions:
1. Zero-model: recon-reforecast/build_p3b_dossier.py, on the pattern of build_p3a_dossier.py. Verbatim AST extracts of
   levels.py (verify_src_bundle, check_src, promote, src_intake), oracle_parity.aa_returned/verdict path, reproduce.py
   build_units, capsule_build/custody APIs, and the receipt schema. Output P3B-DOSSIER.md; anything not found = UNKNOWN.
2. packets/P3b1.md + route-P3b1.json (P2a format). Goal `rf-p3b` via mission_spend goal-declare (cap 2.4M, root = recon
   worktree).
3. Arm with the live gsd_mission.py (arm --no-launch, envelope, admit). The sweep launches it. Never Set-Location into a
   goal root.

Start: read only this file, then action 1.
