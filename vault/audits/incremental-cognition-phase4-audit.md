# Phase-4 adversarial audit -- incremental-cognition program (plan commit 6d3113b8)

Auditor: oneshot-architect-auditor role, 2026-10-03. Read-only except this file.

## Confirmed facts (verified, not trusted)
- align_cwd diverged branch: tools/gsd_mission.py:1053-1055; call + hold: tools/gsd_mission.py:1583-1595 (event `launch_held`, then `continue`).
- Brand #001 origin (tools/gsd_mission.py:1019-1023): cwd stayed on the seed, the renewed worker redid Phase 1 on a NEW worktree branched from the seed; 73 commits invisible, 22 merge conflicts.
- Workers are launched with cwd=rec["cwd"] (tools/gsd_mission.py:692) because trust is exact-path (docstring 636-639; vault/specs/mission-continuity.md:123-124). The card already tells the worker where work_dir is (render_card :934, "WORK TREE: ... enter it first").
- Pinned tests: tools/test_gsd_mission_cwd_align.py:108-115 (V-MCA-DIVERGED), :130-131 (V-MCA-BLOCKING-SET), :134-137 (V-MCA-SUPERVISE-ORDER).

## Gaps

### G1 -- BLOCK -- a wrapper over the raw CE verifier can never pass its own selftest (stale V-CEP-REAL-HANDOFF); SC plan's "still valid" is false
Evidence: tools/test_cognitive_economy_program.py:495-501 pins `1cabd117`/`4d1cfb83` on the CE plan file and asserts `before is False`; later commits (fa9ae2ed, 8b62b6ce) touched that file, so handoff_landed(frozen=1cabd117) is now True and the line FAILs. `--final` runs `selftest(verbose=False)` first (:539-540) so S0 fails permanently. SC plan line 20 says "still valid"; the SC wrapper already found it is not: tools/test_skill_capability_program.py:102-106 ("went false ... CE defect, reported, not edited") and :123-143 monkey-patches `ce.selftest`. The INC plan (lines 46-48) describes only a rebind of five globals.
Fix: the INC wrapper carries the same replacement, with its probe = INC's own plan-file history (not CE's). Copy the patch (do not import the SC module, see G2). Add "--selftest exits 0 before FROZEN_AT" to P0.

### G2 -- HIGH -- the rebind positive control is vacuous when two wrappers share A..N
Evidence: SC V-SCP-REBIND (tools/test_skill_capability_program.py:157-167) proves the rebind only by `ce.PILLARS == A..N` and "a CE A-T ledger is refused by L1". INC also uses A..N (plan lines 29, 47). If the INC wrapper fails to rebind LEDGER_REL / FROZEN_AT_REL / HANDOFF_DIR, or imports the SC module (whose import-time rebind at :39-43 and `ce.selftest = ...` at :143 mutate the shared module object), `--final` silently verifies SC's ledger and passes; the control cannot see it.
Fix: assert each of ce.LEDGER_REL, FROZEN_AT_REL, HANDOFF_DIR, SELF_REL equals the INC value; add `program: "incremental-cognition"` to the ledger and check it in the wrapper (mutant: point LEDGER_REL at SC's ledger -> must fail).

### G3 -- HIGH -- consumption pillars E,H,I,J,M are satisfiable with no evidence the owner delivered
Evidence: MERGED/DEFERRED need only `owner`+`handoff` (tools/test_cognitive_economy_program.py:75-77); a handoff is checked for existence, sha pin, `[pid]`, an owner path substring, and a commit after the freeze (:287-295). Nothing reads the owner's ledger. Plan lines 34-42 say "consume CE P and G verdicts", "consume CE D, E, I": a handoff file saying so passes. CE's own results (A, D, E, I, N, O, Q) are on the unmerged branch cognitive-economy/autonomous-run (git: 7 behind / 12 ahead of HEAD; 22 files differ under vault/programs/cognitive-economy), so on main there is nothing to consume yet.
Fix: add a wrapper clause R2 (like SC's R1): each consumption handoff cites the owner ledger terminal plus a reachable commit, re-read by the wrapper; order INC final after CE/SC `--final`, or record the pillar honestly as EXTERNAL_BLOCKED until then.

### G4 -- HIGH -- pillar A is a one-line "repair" with no design; only one option is safe and existing tests constrain it
Options:
 (i) launch with cwd=worktree: REJECT. Trust is exact-path (spec :123-124; launch_worker docstring :636-639); no claude-power-pack worktree path appears in ~/.claude.json (grep, 0 hits); pre-trusting means a global config edit (HR-001).
 (ii) launch in main cwd, card says enter the worktree: ALREADY the design (render_card :934; effective_workdir :1069-1109 follows the predecessor's transcript only if it acted on that workstream). The hold is stricter than the design it guards.
 (iii) merge/rebase: REJECT. Rebase rewrites the worker's 12 commits; ff-of-main needs a clean tracked tree (:1056-1063 -> behind_dirty) that the shared checkout (~40 dirty peer paths) never has; merging into main is a peer-visible mutation. Merging main INTO the worktree branch is non-destructive but still ends in behind_dirty at the cwd, so it does not unblock.
Safe fix = (ii): a new NON-blocking status (e.g. `diverged_entered`) returned only when work_dir is a registered worktree of the same common git dir, on a different branch than cwd, merge-base exists, AND the caller passes `entered=True` (effective_workdir proved the predecessor worked there on this workstream). Default remains `diverged` (blocking). Launch in cwd, ledger event, and assert the pre-rendered card contains the WORK TREE line before launching.
Constraints: V-MCA-DIVERGED (:108-115, the Brand shape, no entered flag -> must stay `diverged`); V-MCA-BLOCKING-SET (:130-131, exactly {behind_dirty,diverged,unreadable}; the new status must not join it); V-MCA-SUPERVISE-ORDER (:134-137). Add: entered=True positive, entered=False control, card-has-WORK-TREE check, and a supervise-level test with a fake runner.

### G5 -- HIGH -- no acceptance test that the repair survives main moving between relays
Evidence: plan lines 18-19 record 4 peer commits to main during one epoch; align_cwd compares HEADs (:1049-1055), so any alignment approach re-diverges at the next rotation.
Fix: pillar A acceptance = scratch-repo drill (style of tools/test_gsd_mission_cwd_align.py): worktree branch with commits, main advanced twice with a dirty tracked file, three consecutive relays all launch; plus a mutation drill (repair removed -> held again).

### G6 -- HIGH -- fixing the hold relaunches BOTH held missions at once with no RAM gate in the supervisor
Evidence: tools/gsd_mission.py has no free-memory check anywhere (grep ram/RAM/memory: only comments). The plan's RAM >= 4 GB boundary gates only ARMING the third mission, yet plan line 21 measures 3.1 GB free / 31 claude.exe. When the repaired code goes live, CE (m-fdefb0fca0c0) and ucep (m-876f8b5a904a) each launch a fresh worker. tools/gsd_mission.py is also live-loaded by the sweep, so saving the edit deploys it unstaged.
Fix: develop the repair in a scratch copy, test there, copy atomically; do it only at free RAM >= 4 GB or after deliberately stopping one mission; record the RAM reading in the pillar-A measurement.

### G7 -- MEDIUM -- "a third mission in the same checkout" is really a third worktree/branch; merge-back, hook/settings ownership and one-writer rules are unaddressed
Evidence: CE plan s10 (lines 131-134) and workstream STATE.md:47 say the mission "runs in the main checkout", yet the worker created .claude/worktrees/cognitive-economy on cognitive-economy/autonomous-run (git worktree list; plan line 17). Any /gsd-autonomous worker does this, so INC gets its own branch: its ledger, FROZEN_AT ancestry and the "commit after freeze" test (Resolver.handoff_landed uses HEAD of whichever checkout runs the gate, :148-158) live on that branch; the plan has no merge-back. Pillars D, I, K edit ~/.claude hooks/settings, the surface SC owns under a retained-settings check (tools/test_skill_capability_program.py:66-94): an INC edit turns SC `--final` red or is overwritten by SC's restore. Pillar A edits tools/gsd_mission.py, which CE/ucep missions execute.
Fix: ownership/ordering table for hook-dispatcher and settings (INC records edits in SC's retained list or defers), an Owner merge-back step, and pillar A done in-pane before arming (one writer).

### G8 -- MEDIUM -- no_progress blindness (CE G5) applies only until the worker enters its worktree
Evidence: progress_fingerprint hashes `work_dir or rec.work_dir or rec.cwd` (tools/gsd_mission.py:1550, :1649-1673). Epoch 1 has no work_dir, so the whole main checkout is hashed and peer churn resets stalls; after the relay records work_dir it is the worktree's tree. Dispositions-only pillars can also emit trivially "progressing" handoff commits.
Fix: arm with explicit --max-cycles/--max-hours (the plan states none; CE used 12 / 24 h) and require each phase commit to carry a measurement, not only a handoff file.

### G9 -- MEDIUM -- overlap and double counting with CE and SC
- INC J (context lifetime) = CE D,E,I; H = CE P,G; E = CE F,K; I = CE B + SC A-C; K (cost ratchet) = CE A,S; M = CE H,J,M,Q + SC M; N closeout = CE L8/R/T + SC N. Five of fourteen pillars (E,H,I,J,M) are pure dispositions of pillars others own (plan lines 34-42 say so); new work is A, B, C, D and parts of F, G, K, L.
- Bracketed prompt letters reuse CE's letters with other meanings ([T] in I vs CE T; [N] in H vs CE N; [B,C,D,E] in I vs CE B-E) while the verifier requires `[pid]` of the INC pillar in handoffs (tools/test_cognitive_economy_program.py:287-288): likely mis-cited handoffs.
Fix: collapse E,H,I,J,M into one disposition table (one pillar, per-row owner); keep N only because L8 (:251-258) mandates reviews and deltas per ledger, and point it at CE/SC closeout files instead of re-doing them.

### G10 -- MEDIUM -- false or stale premises and missing structure
- "SC program ... P0 not started" (plan line 21) is false: 217d72b5 (P0: ledger, wrapper, workstream) and 28b27367 (FROZEN_AT -> 217d72b5) are committed; tools/test_skill_capability_program.py and vault/programs/skill-capability/FROZEN_AT exist.
- "HEAD bd5a5a5c ... origin +26/-0" is stale (HEAD 6d3113b8).
- vault/programs/incremental-cognition/ already exists UNTRACKED (denominators/kme_audit_2026-10-03.json, handoffs/): the denominators file must be committed inside the freeze, and a pre-existing handoffs dir risks files that predate FROZEN_AT.
- No phases/DAG, next action, cycle/hour budget or Q&A record (CE s4-s9, SC DAG and "Next action" have them); "ledger created in P0" leaves predicted terminals and frozen owner paths (which L1 requires to exist, :198-200) unspecified.
Fix: correct the lines, commit denominators with the freeze, add the phase table and next action.

## Answers to the audit questions
a. Wrapper: module globals ARE read at call time (check_ledger :187/:190, _check_evidence :290, gate_argv_problem :106, FakeResolver._exists :338); mutant letters A-G and pillar indices 3,4,7 fit A..N. Breaks: V-CEP-REAL-HANDOFF (G1), vacuous rebind control (G2); L1 text still says "A-T" (cosmetic).
b. G4/G5. c. G9 (and G3 for what "consume" proves). d. G7/G8. e. G10.

VERDICT: EXECUTE-WITH-FIXES -- inject G1-G4 before P0 (done-gate unreachable or vacuous; repair undesigned), G5-G6 before touching tools/gsd_mission.py, G7-G10 in P0.
