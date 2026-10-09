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
1. DONE 2026-10-09: build_p3b_dossier.py -> P3B-DOSSIER.md (85.6k chars, ~21k tokens, missing=0, exit 0). Bundle-field
   gap found: the receipt has no `produced_utc`, `host_plane` or `runner.job_key`. It has `ended_at`, `host`
   ("kobicraft-gex44") and `job_id`. The P3b1 packet must state the mapping, or write UNKNOWN and stop.
   Original spec: Zero-model: recon-reforecast/build_p3b_dossier.py, on the pattern of build_p3a_dossier.py. Verbatim AST extracts of
   levels.py (verify_src_bundle, check_src, promote, src_intake), oracle_parity.aa_returned/verdict path, reproduce.py
   build_units, capsule_build/custody APIs, and the receipt schema. Output P3B-DOSSIER.md; anything not found = UNKNOWN.
2. PARTIAL 2026-10-09: packets/P3b1.md + route-P3b1.json WRITTEN (Owner "y": the bundle-field mapping is fixed in
   policy 3; the job is 294 units = 5 sealed + 289 donors, because a registry write drifts the 5 PROVEN rows). The goal
   is NOT declared: goal-declare rf-p3b fails with "roots overlap goal 'cp50-c1'". That goal binds the same worktree, cap
   1.5M, settled 5,138,293. A rebind needs `goal-declare --owner` on a TTY, so the Owner decides.
   UPDATE 15:42: the Owner ran release_cp50-c1_root.bat, so cp50-c1 now binds `_retired_cp50-c1`. rf-p3b is DECLARED:
   cap 2,400,000, root wt_keosdtk_home, host DESKTOP-PMT5BS8, remaining 2.4M.
   BLOCKER before arming: C1 mission m-4c2ceda008e1 is BLOCKED, not finished. Its worker session c021de1c lives in this
   same worktree and there is no C1-receipt.md. cp50-c1 shows used 7,684,629 against its 1.5M cap, with 150k still open.
   If C1 resumes, its calls bind to rf-p3b. The Owner decides: hold or finish C1 first.
   UPDATE ~16:10: blocker CLEARED. The Owner said "yes" to hold; `hold` refused because C1 is already HALTED (liveness DEAD,
   "host lists session stopped"), so nothing can bind to rf-p3b. The Owner asked to arm P3b1 on GEX44: NOT armed, because
   GEX44 cannot run it as written. GEX44 has no recon repo (it has no remote; ~/ksr has no decomp tree) and no
   decomp/match_accel factory data. The recon code hardcodes Windows paths (reproduce.py:33
   F_FACTORY = r"C:\Users\...\match_accel_factory"; capsule_build.py:39 R + r"\match_accel_factory"; LOCAL_LEDGER =
   F_FACTORY + r"\ledger.jsonl"), so on Linux every factory path resolves to nothing. The packet also forbids that
   redesign. Owner decides: laptop (ready now) or a GEX44 portability unit first.
   DONE (Owner "yes" = laptop): mission m-1a112049e9c8 ARMED on the laptop. It is PREPARED with no launch; the sweep launches it.
   envelope: token_estimate 875k (breaker 1.75M = stop), model sonnet, wu_packet packets/P3b1.md.
   Admission: the first try returned RECOMPILE (need 1,570,020 > target 1.5M). route-P3b1.json now has target 1.6M and
   11 envelope calls, which made it ADMISSIBLE.
   rf-p3b already carries 215,716: the steward settled the dead C1 worker into it after the rebind. Remaining: 2,184,284.
P3b1 DONE 22:42: m-1a112049e9c8 HALTED (session done). Commits: recon 4e7d8e7, PP c051a15b (receipt). P3B_DRILL=10/10,
   re-run by the coordinator (10/10). CAPSULE=cap1-984a35109f79 (trim census), BUILD=reproduce-20261009T193108Z with
   294 units. Worker spend ~1.79M against a 1.75M stop. rf-p3b remaining 397,449, which does NOT cover P3b-2.
   Check before P3b-2: the V-P3B-IMPACT line prints "control_proven=5"; confirm the control names no drift.
   Coordinator slip: one Set-Location into the goal root to re-run the drill, reverted at once.
P3b-2 PRE-CHECK 2026-10-09 (main pane): goals OK (rf-p3b2 -> wt_keosdtk_home, cap 2.4M, used 0; rf-p3b ->
   _retired_rf-p3b, used 3,318,702 vs 2.4M cap, open 169,870). CONTROL DRIFT FOUND, P3b-2 STOPPED before any send:
   SB.impact(levels.load_store()) on the REAL store = control_proven=5, each with drift=["match_py"], bundle_verifies=false.
   match_py = sha256(match.py). match.py is clean in the tree; it last changed in recon ac1f1ae (2026-10-04, canonical
   @sda21/@ha/@l operands), after the 5 rows were sealed. The drill's IMPACT gate only asserts src_registry is not in the
   control's drift, so it passed. Owner decides: (a) accept, since the bundle path re-judges the 5 under the current oracle
   (10 in the summary), or (b) revalidate the 5 against the current match.py first. Then do summary steps 1-10.
P3b-2 RUN 2026-10-09/10 (main pane, Owner "a" = accept; the bundle path re-judges the 5):
   pre-checks PINS=OK tools=7, SLOT_LEDGER PASS lease=none, GEX44 idle (queue 0, boots 0/6). RF_CURRENT_PHASE=3 = recon
   a5d57a0. SENT job 1 of 2 = ksrmb-20261009-214006 -> WAIT=COLLECTED -> REPATRIATE=OK tree 6f7b2c9d. Receipt PASS, 294 units,
   custody ok, runner_lib 7377ff0f, task_sha 5bd8add8 (matches the build).
   DONE (real writes, log gen3/P3b2-steps6-8.log, backups in that session's scratchpad backup_pre_p3b2): register_src
   added=289 kept=5 refused={}; assemble bundles=294 refused=0; 294 bundles written to decomp_factory/levels/evidence/
   src_bundles; impact: the 5 sealed drift [match_py, src_registry], bundle_verifies=True for all 5.
   NOT DONE: promote(). levels.promote refused HOST_FLOOR_BREACHED (free 1221 MB, then 1314, then 619 < 1500). Ledger and
   manifest are untouched, so SRC PROVEN is still 5.
   NEXT: when free RAM >= 1500 MB (close panes or Cursor windows), run
   `python vault/programs/cognitive-economy/gen3/recon-reforecast/p3b2_finish.py`. It needs P3B2_CHECK=PASS:
   SRC_PROVEN_AFTER=294 rise=289, PROMOTED_NOT_PROVEN=0, SEALED_LOST=[], PROVEN_VIA_BUNDLE=294/294. Exit 3 = still under the
   floor, nothing written. Do NOT re-send: job 2 of 2 is the only one left.
   DGL CONFLICT: Apps\pp-dgl chain.json W7 = this same P3b-2 (waits for W6 + D2-owner.md). It must become verify-only or be
   removed, otherwise it will re-send and spend the last RF Phase 3 job. Do not create D2-owner.md without that change.
OLD NEXT: when gen3/P3b1-receipt.md lands, read it, check the drill (V-P3B-* all PASS) and the CAPSULE= and BUILD= lines,
   then run P3b-2 from the main pane (sequence in the 03b-01-SUMMARY).
   Original spec: packets/P3b1.md + route-P3b1.json (P2a format). Goal `rf-p3b` via mission_spend goal-declare (cap 2.4M, root = recon
   worktree).
3. Arm with the live gsd_mission.py (arm --no-launch, envelope, admit). The sweep launches it. Never Set-Location into a
   goal root.

Start: read only this file, then action 1.
