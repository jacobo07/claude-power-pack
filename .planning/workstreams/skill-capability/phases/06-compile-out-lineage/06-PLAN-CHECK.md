# Phase 6 plan check (06-01, 06-02, 06-03)

Checked against HEAD 04054323, with phase-4 review fixes WR-04/05/06 already committed (b65dda45..6b2cee62), and test_skill_coverage.py still being edited by the code-fixer.

Live measurements (gex44, at the time of this check):
- test_skill_coverage.py: SKC_PASS=17/17 (the plans assume 15/15)
- test_skill_drift.py: SKD_PASS=15/15 (the plans assume 13/13)
- state.H pin for H-drift.md: 8d0ec054... (the plan expects 5eae42e6...)
- state.H pin for card_source_digests.json: cdce7261... (unchanged)
- state.H evidence count: 9
- Population of top-level hooks/*.js matching CARD_TOKEN: exactly the two cards.
- Dispatcher registrations: lines 427 and 433, as the plan says.
- Both hooks end with "\n". Appending `//` comment lines at EOF is valid JS, and no hook test or test_card_precision reads the files' line structure or sha. No state entry pins the sha of a hooks/*.js file. The D-coverage.md refs (:428, :61) survive an append.

Premise grep: every named function exists. This covers smd: lf_bytes, git_run, resolve_commit, card_source_state, card_drift, card_verdict, record_cards, CARD_RECORD_REL, REPO, plus the new committed_card_pairs, committed_bytes, is_git_failure and tracked_paths. It covers sc: CARD_TOKEN, DISPATCHER_REL, registered_hooks, discover_cards (now with read_disk=), lf. It covers vgm: tracked_at, batch_blobs, _norm_sha, _git_exe. git_run's reason format "git <a0> rc=<n>: ..." matches COMMIT-ANCESTOR's ` rc=1:` test. A missing git yields "git not found: ...".

Drill table (06-02): I re-derived all 23 rows against the current smd semantics. Each declared fail set is reachable, including GHOST-SKILL (UNTRACKED row plus RECORD_STALE gives DRIFT), FLOOR-ONE/ZERO, DISPATCHER-UNCOVERED (SCRIPT regex accepts hooks/sub/...), COMMIT-NOT-ANCESTOR (R has no SKILL.md, so S is a real commit), CRLF and WORKTREE-ONLY. One condition: FLOOR-ZERO only holds if H-RECORD-CURRENT does NOT turn an empty pair list into pairs=None (see W-03).

## BLOCKERS

B-01 [06-01 Task 1 verify/fails_when, Task 1 action, must_haves; 06-02 Task 3 action + verification; also the 06-01 objective]
Required property: every verify assertion must be satisfiable on the tree it will run against.
Evidence: the counts are hard-coded at plan-time values that the phase-4 fixes have already invalidated. Live values are SKD 15/15 and SKC 17/17, and the fixer is still adding clauses. As written, "either gate's last line is not 13/13 / 15/15" fails deterministically.
Fix: replace every `SKD_PASS=13/13`, `13/13`, `SKC_PASS=15/15`, `15/15`, "must stay 15/15" with "ends `SKD_PASS=<n>/<n>` (numerator equals denominator), exit 0" and "ends `SKC_PASS=<n>/<n>`, exit 0, V-SKC-EVIDENCE-CURRENT ok". In fails_when, replace "not 13/13 / 15/15" with "has numerator != denominator or a non-zero exit".

## WARNINGS

W-01 [06-01 <interfaces> + Task 2 step 2] The state.H pins are stale. H-drift.md is now 8d0ec054..., not 5eae42e6..., and the fixer may move it again.
Replace "expected at plan time: 5eae42e6..., cdce7261..." with "read at execution time from the H line; the plan-time values are historical and not asserted". Keep the "if new == old, stop" check. Replace the evidence count "prints `IMPLEMENTED_AND_VERIFIED 9`" with "prints IMPLEMENTED_AND_VERIFIED and the same count read before the edit".

W-02 [06-01 DISPATCHER-COVERED / H-RECORD-CURRENT] The plan rebuilds what WR-04 now ships as `smd.committed_card_pairs(repo, sha)`. Its own "" fallback also turns a git batch failure on a hook blob into a silent non-card, which breaks the requirement that a git failure be INCONCLUSIVE.
Replace "overlay = HEAD blob text for EVERY rel ... using \"\" for a rel not readable at HEAD" and the hand-built pairs with: "pairs, why = smd.committed_card_pairs(repo, sha); None -> UNMEASURED(why); DISPATCHER-COVERED uses {p['card'] for p in pairs} (empty -> UNMEASURED); H-RECORD-CURRENT uses smd.card_source_state(repo, sha, pairs)."
If the executor keeps its own overlay, it must call `sc.discover_cards(..., read_disk=False)` and map `smd.is_git_failure(reason)` to UNMEASURED.

W-03 [06-01 H-RECORD-CURRENT] For FLOOR-ZERO, an empty pair list must be passed as `[]`, never as None (`pairs or None`). With None, card_source_state re-discovers the pairs, and the drill's declared H FAIL becomes code-path-dependent.
Add the sentence: "pass the pair list as-is; [] is a measured empty set".

W-04 [06-01 population() and COMMIT-DIGEST] A batch_blobs failure while reading a member is unspecified, so a failed read silently drops the member. The fixer added the reasons git-batch-truncated, badheader and ambiguous.
Add: "a member blob whose reason satisfies smd.is_git_failure -> judge INCONCLUSIVE; git-batch-empty -> text ''". Also replace the reason list "git-batch-missing, git-batch-empty, git-batch-error, git-batch-rc" with "classify by smd.is_git_failure / smd.BATCH_FAILURES, re-read at execution time".

W-05 [06-01 judge] `vgm.tracked_at` is not `-z` and returns an empty set on failure. WR-06 shipped `smd.tracked_paths(repo, sha) -> (set|None, reason)`.
Replace "`tracked_at` empty -> INCONCLUSIVE" with "`smd.tracked_paths`: None -> INCONCLUSIVE(reason); empty -> INCONCLUSIVE 'nothing tracked'".

W-06 [06-01 H-RECORD-CURRENT] The record read must stay committed-blob-only. Do not substitute `smd.load_card_record()`: its committed_bytes at HEAD reads the working tree to refuse "uncommitted", which contradicts the plan's "no working-tree file is read by the judge" and would turn WORKTREE-ONLY-style drills red if the record were dirty.
Keep `git cat-file blob <sha>:CARD_RECORD_REL` via smd.git_run, and state that load_card_record is deliberately not used.

## INFO
- I-01 The DG-01/D-coverage line refs and the hook-dispatcher line numbers are cited as plan-time facts. The append-only design does not depend on them. Phrase any execution-time check as "re-read D-coverage.md refs and assert unchanged before/after", not as literal 428/61/433.
- I-02 state.H's reason text says "13/13 clauses". That is stale after the fixer. It belongs to phase 4, not this plan.
- I-03 06-03 adds card_source_digests.json as a G file pin, so every future re-record must move both the G pin and the H pin. The owner bundle line covers this.

VERDICT: ISSUES FOUND (1 blocker, 6 warnings, 3 info)
