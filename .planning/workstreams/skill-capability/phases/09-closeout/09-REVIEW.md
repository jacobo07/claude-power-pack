---
phase: 09-closeout
reviewed: 2026-10-04T01:10:00Z
depth: deep
files_reviewed: 6
files_reviewed_list:
  - tools/test_skill_capability_prefinal.py
  - vault/programs/skill-capability/reviews/ukdl.md
  - vault/programs/skill-capability/reviews/cbr.md
  - vault/programs/skill-capability/LAPTOP-CLOSEOUT.md
  - vault/programs/skill-capability/evidence/pre-final-gex44.md
  - vault/programs/skill-capability/ledger.json
findings:
  critical: 1
  warning: 4
  info: 2
  total: 7
status: issues_found
---

# Phase 9: Code Review Report

**Reviewed:** 2026-10-04T01:10:00Z
**Depth:** deep
**Files Reviewed:** 6
**Status:** issues_found

## Summary

The laptop sequence was simulated end to end on gex44 in throwaway clones under `/home/kobii/.claude/jobs/06c5c0e4/tmp/p9review/`, never in the worktree. One clone had a full `core.autocrlf=true` checkout, and state.N was written and committed exactly as LAPTOP-CLOSEOUT steps 5-7 say. In it, step 1 is clean, step 4 gives `PF_FAILED=V-PF-L8` only, step 8 `--closeout` gives `PF_VERDICT=PASS`, and `--pillar N` (CE running N's gate) passes. There is no recursion, and `gate_argv_problem` admits the argv. `--final` still fails on that CRLF clone because of L5 J (CR-01), apart from the host-specific R1. `--closeout` can be made to PASS with `retained` emptied (WR-01). The boundary-4 check cannot be satisfied at the push step (WR-02). "Committed blobs" is overstated (WR-03). 17 clauses have no red mutant of their own (WR-04). The UKDL, CBR and deltas claims spot-checked (more than 20) are backed by their sources (IN-02). No command in LAPTOP-CLOSEOUT destroys state: step 1 explicitly forbids reset, clean and renormalize, and every commit is pathspec-scoped.

## Narrative Findings (AI reviewer)

### CR-01: On a core.autocrlf=true clone (the laptop) `--final` fails L5 J, so the documented sequence cannot reach exit 0

**Severity:** BLOCKER
**File:** `tools/test_skill_creation_gate.py:137` (root cause, phase 8 code), exposed by `vault/programs/skill-capability/LAPTOP-CLOSEOUT.md:177-185` (step 9 promises `SCP_VERDICT=PASS`, naming R1 as the only possible failure) and by `tools/test_skill_capability_prefinal.py` (no check exercises an autocrlf plane)
**Issue:** The J gate's `build_base` takes `git archive ... skills` (line 249). `git archive` applies `core.autocrlf`, so on the laptop clone (`.gitattributes` itself records "This clone runs core.autocrlf=true"; Git for Windows defaults to it) every SKILL.md arrives with CRLF. `undeclared()` then returns the text unchanged when `"\r" in text` (line 137), the existing `metadata:` block survives, and `scg.insert_declaration` raises `ValueError("frontmatter already has a metadata key; merge by hand")`. The gate exits 1, CE L5 J fails, and `--final` is FAIL whatever the Owner does with R1. gex44 (autocrlf unset) never sees it, so the pre-final record's PASS on `--pillar J` does not transfer to the laptop plane, and none of the laptop steps (2: `--selftest`, 3: `--status`, 8: `--closeout`) runs J's gate before step 9.
**Reproduction:** `/home/kobii/.claude/jobs/06c5c0e4/tmp/p9review/repro_cr01_crlf_final.sh` (full `-c core.autocrlf=true` clone of the run branch, state.N committed exactly as LAPTOP-CLOSEOUT steps 5-7 say, `--final`): exit 1, failures `L5 J: gate python tools/test_skill_creation_gate.py rc 1 ... ValueError` plus the two host-specific R1 lines. Toggling only `core.autocrlf` to false in the same clone: `SCG_PASS=48/48`, rc 0. N's own gate (`--closeout`) passes on the same CRLF clone (`sim_laptop.sh`, exit 0), so J is the only non-R1 blocker found.
**Fix:** normalise the archive before `undeclared()` instead of bailing on CR, e.g. in `build_base` run the archive with `-c core.autocrlf=false` (`smd.git_run(REPO, "-c", "core.autocrlf=false", "archive", ...)`) or make `undeclared()` operate on `sc.lf(text)` and restore CRLF afterwards like `insert_declaration` does. Add an autocrlf=true pole to the J gate (or a `--closeout`/LAPTOP step that runs `python tools/test_skill_capability_program.py --pillar J` before step 9) so this plane is measured, and amend LAPTOP-CLOSEOUT step 9's expected-failure text.

### WR-01: `--closeout` drops the whole ledger invariant, so emptying `retained` passes both `--closeout` and R1

**Severity:** WARNING
**File:** `tools/test_skill_capability_prefinal.py:789-806` (run_closeout never calls `check_invariant`; it is only in `run_gex44`, 722-733), with `vault/programs/skill-capability/LAPTOP-CLOSEOUT.md:183-185` ("Restoring the settings or re-declaring them is your decision")
**Issue:** The invariant (every key but state/reviews/deltas equals the FROZEN_AT ledger) is the only check that pins `retained`, `plan`, `verifier`, `terminal_vocabulary`, etc. (L2 covers only `frozen`). It was dropped in closeout mode because its state.N clause must not fire there, but the other half was dropped with it, on exactly the plane where `retained` matters (R1 reads it). `check_retained` (wrapper:76) loops over `keys`, so `keys: []` yields no R1 failure. A laptop commit that "re-declares" `retained` as empty, which the closeout doc offers as a remedy for a red R1, turns R1 green and `--closeout` stays PASS: the gate state.N cites cannot tell "restored or retained on purpose" from "declaration deleted". Lesson violated: each clause needs its own red mutant; the closeout pole of the invariant has none.
**Reproduction:** `/home/kobii/.claude/jobs/06c5c0e4/tmp/p9review/repro_wr01_retained_emptied.sh` (throwaway clone with state.N committed, `retained.settings.keys=[]` committed): `--closeout` `PF_VERDICT=PASS`, `check_retained` -> `[]`; exit 1.
**Fix:** run the invariant in closeout mode with only the state.N clause relaxed, e.g. `check_invariant(led, frozen_led, allow_state_n=(mode == "closeout"))`, add a selftest mutant "closeout: retained emptied" that must die, and in LAPTOP-CLOSEOUT say that re-declaring `retained` needs an explicit, separately reviewed change (or make R1 refuse an empty `keys` list).

### WR-02: The boundary-4 check cannot be satisfied at the push step, and the push itself is never specified

**Severity:** WARNING
**File:** `vault/programs/skill-capability/LAPTOP-CLOSEOUT.md:54-63` (check), `:196-201` (step 11), `:35-39` (gex44 push)
**Issue:** Section 1 defines foreign commits as `git log --oneline FETCH_HEAD..HEAD` ("commits on the checkout that the run does not have") and step 11 says "push under boundary 4 (section 1: no foreign commits interleave)". By step 11 HEAD carries the Owner's own state.N and CLOSE.md commits (and any bundle evidence commits, items 4/5/6/8), none of which are in FETCH_HEAD, so the documented check always lists them and the push condition can never be met as written; on the shared `feature/knowledge-acquisition` checkout it also lists every peer commit. FETCH_HEAD is additionally overwritten by any later fetch (bundle item 6 asks for one). Step 11 then shows no push command, remote or target branch at all, so the Owner must improvise the one irreversible step, which is exactly where boundary 4 is supposed to bind. Separately, the gex44 push in section 1 (line 38) runs before the boundary-4 check, which needs FETCH_HEAD on the laptop and so can only run after it. That push is a plain fast-forward of a run-only branch (all 248 commits since `origin/feature/knowledge-acquisition` are program commits by jacobo07, checked), so it is safe in practice, but the doc says the check comes "before any push".
**Reproduction:** `/home/kobii/.claude/jobs/06c5c0e4/tmp/p9review/repro_wr02_boundary4_unsatisfiable.sh`: after step 7 in the simulated clone, `FETCH_HEAD..HEAD` = `[bc102f13 docs(skill-capability): close pillar N on the laptop (state.N)]`, so exit 1.
**Fix:** define the check against the push target, immediately before pushing: fetch `<remote> <target>`, then `git log --oneline <remote>/<target>..HEAD --not <run-tip>`, which leaves only the commits that are neither the run's nor the closeout's own (state.N, CLOSE.md, bundle evidence), and require that to be empty. Name the exact push command (`HEAD:<target>`, never forced). Put the gex44 push after a gex44-side equivalent check, or say explicitly that a fast-forward of the run-only branch is exempt.

### WR-03: "on committed blobs" is overstated: V-PF-COMMITTED cannot see dirty hooks/, skills/ or modules/, which the wrapper gates run from the working tree

**Severity:** WARNING
**File:** `tools/test_skill_capability_prefinal.py:709-715` (scope `[program dir, "tools"]`), `:779` (DIRTY-SET-STABLE uses the same scope); claims in `vault/programs/skill-capability/LAPTOP-CLOSEOUT.md:6` ("`--pillar A` .. `--pillar M` pass on committed blobs") and ledger `deltas.product[13]` ("runs --selftest, --status and --pillar A..N on committed blobs")
**Issue:** The wrapper subprocesses read the working tree, and their gates read files outside the two scoped dirs. For example, `tools/test_card_precision.py:32` executes `hooks/doctrine_cards.js` from the checkout. An uncommitted edit to that hook (or to `skills/*`, `modules/*`) leaves V-PF-COMMITTED and V-PF-DIRTY-SET-STABLE `ok`, so a `PF_VERDICT=PASS` record can describe bytes that no commit holds. The recorded gex44 run is probably unaffected, because its worktree had only `vault/progress.md` and hook-written `docs/` stubs dirty. The defect is that the instrument could not have reported otherwise, and the claims say more than it measures.
**Reproduction:** `/home/kobii/.claude/jobs/06c5c0e4/tmp/p9review/repro_wr03_committed_scope.sh`: with `hooks/doctrine_cards.js` modified, the V-PF-COMMITTED dirty set is `[]`, so exit 1.
**Fix:** bracket the wrapper runs with the whole-tree dirty set (`git status --porcelain` with no pathspec, excluding only the known hook-stub paths by an explicit list), or run the wrapper in a `git worktree add --detach HEAD` export. Until then, reword the two claims to "with tools/ and the program dir clean".

### WR-04: 17 clauses of the pre-final checks have no red mutant of their own; the selftest stays 45/45 with each one deleted

**Severity:** WARNING
**File:** `tools/test_skill_capability_prefinal.py` `judge_record` 476-495, `check_commands` 439/444-446, `check_cbr` 300/309-310/316, `check_ukdl` 239, `check_decisions` 408, `judge_status` 603, `judge_n_open` 570, `check_deltas` 337; selftest 889-1046
**Issue:** The docstring says every check gets "a green control and red mutants", and the lesson for this phase is "each clause has its own red mutant". The mutants exist per check, not per clause. Deleting any one of these clauses leaves `PF_SELFTEST=PASS kills=45/45`: the record's host, date, command, PF_MODE, PF_TERMINAL, PF_OPEN and "N reported PASS" clauses (so V-PF-GEX44-RECORD, the clause state.N leans on for the gex44 plane, is pinned only by its last-line and reachability clauses); the CLOSE.md / state.N / run-branch strings and the `gate_argv_problem` refusal in V-PF-CLOSEOUT-COMMANDS; CBR predicted-vs-frozen, empty surprise and no-path evidence; UKDL Trap/Source presence; the DECISIONS `Options:` field; STATUS `closed`; N-OPEN `rc != 1`; and DELTAS pillar outside A..N. Any of them can be removed without a red result.
**Reproduction:** `/home/kobii/.claude/jobs/06c5c0e4/tmp/p9review/repro_wr04_clause_mutants.py` writes each single-clause deletion to a throwaway clone's `tools/pf_mutant.py` and runs `--selftest`. 17 of 17 survive. The positive control, deleting the `PF_VERDICT=PASS` clause, which does have a mutant, is killed. Exit 1.
**Fix:** add one mutant per clause, each asserting that its own message appears (not just `bool(probs)`). Examples: the record with the host line removed, with `PF_TERMINAL=A,B` and with a `CEP_PILLAR_N=PASS` line; the closeout with `CLOSE.md` removed and with argv `["python", "tools/../x.py", "--closeout"]`; a CBR row whose predicted value differs from frozen; a UKDL entry without `- Source:`; a decision section without `Options:`; a status with `closed` short by one; `judge_n_open(2, n_good)`; a delta with pillar `"Z"`.

### IN-01: git failures outside `rep.judge` crash (exit 1 = FAIL) instead of reading INCONCLUSIVE

**Severity:** INFO
**File:** `tools/test_skill_capability_prefinal.py:664, 682, 684` (`text_at` evaluated outside `rep.judge`, including the eagerly built ok-detail string), `:183` (`RuntimeError` from `frozen_at_commit` is not caught by `judge`), `:158-160` (`path_exists` turns a git failure into "does not exist")
**Issue:** The stated rule is "git failure -> INCONCLUSIVE". These paths fail closed, so they never give a false PASS. But a transient git failure reads as a FAIL or a traceback, never as exit 2, and under `--final` both look the same as a real L5 failure.
**Fix:** move the reads inside `judge` lambdas, catch `RuntimeError` there as INCONCLUSIVE, and have `path_exists` check `rev-parse HEAD` on a non-zero `cat-file -e`, as `blob_at` does.

### IN-02: UKDL / CBR / deltas spot-check: no unbacked claim found

**Severity:** INFO
**File:** `vault/programs/skill-capability/reviews/ukdl.md`, `reviews/cbr.md`, `ledger.json` `deltas`
**Issue:** None. Checked against the cited sources at HEAD: all 15 UKDL `Source:` line references (01-REVIEW:62, 02-REVIEW:34/46, 03-REVIEW:63/82, 03-01-PLAN:379, 04-REVIEW:46/96/131, 07-REVIEW:53, 08-REVIEW:164, STATE:48/57/58/61) land on the finding they describe. The figures also match their sources: 36/36, 4/6 -> 3/5, color.diff / no_opportunity, recall 4/7 at n=4 (C-delivery.md:35-36), 30000 -> 29795 chars and 87739 -> 89844 (B-listing-floor.md:15-22), 9 high-criticality skills with coverage none = claude-power-pack + 8 (D-coverage.md:72), IDENTICAL 13 of which eol_only 10 (H-drift.md:28), 18/18 (05-VERIFICATION:5), two upper-bound savings (A, B), and product 14 / intelligence 15 / 12 UKDL / 14 CBR rows as quoted in the state.N reason. One exception is the "committed blobs" wording, which is WR-03.


---

_Reviewed: 2026-10-04T01:10:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
