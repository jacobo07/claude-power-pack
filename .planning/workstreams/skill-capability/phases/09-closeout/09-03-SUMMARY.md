---
phase: 09-closeout
plan: 03
subsystem: skill-capability program closeout
status: complete
tags: [closeout, laptop-handoff, owner-bundle, owner-decisions, pre-final, pillar-N, gex44]
requires: [09-01 (tools/test_skill_capability_prefinal.py), 09-02 (reviews + deltas at HEAD)]
provides:
  - vault/programs/skill-capability/LAPTOP-CLOSEOUT.md (D-02, the Owner's one-pass laptop closeout)
  - vault/programs/skill-capability/evidence/pre-final-gex44.md (D-03 record, the prg evidence state.N will pin)
affects: [the laptop closeout of pillar N (state.N, --final, CLOSE.md), which belongs to the Owner]
tech-stack:
  added: []
  patterns: [document sections generated from HEAD blobs by a marker-filling helper, pre-check with the gate's own check_* functions before commit]
key-files:
  created: [vault/programs/skill-capability/LAPTOP-CLOSEOUT.md, vault/programs/skill-capability/evidence/pre-final-gex44.md]
  modified: []
decisions:
  - "The close-N sequence orders state.N -> commit -> --closeout -> --final -> CLOSE.md (I-01): D-02's literal 'run --final, then write state.N' cannot pass, because --final fails on L3 N until state.N exists"
  - "Decision Source lines were generated too (markers <!-- decision:K -->), not only the bundle lines, so no STATE prefix is retyped"
  - "The two E decision lines (epoch 3, epoch 4) share Q2, which carries only the corrected epoch 4 figures; recorded pick none (Owner-reserved)"
metrics:
  duration: ~12 min
  completed: 2026-10-04
plan_head_before: 3ff2cc1d64c0f8a8a0b21ee1e2c410f1bad5b176
actuals:
  tokens: 8650    # chars/4 over the realized diff 3ff2cc1d..5464e84c (34605 chars)
  tasks: 2
  commits: 3      # git rev-list --count 3ff2cc1d..HEAD once this SUMMARY lands: 2 task commits + 1 docs
---

# Phase 9 Plan 03: laptop closeout and gex44 pre-final record Summary

gex44 is finished per the ROADMAP Host plane. A..M are terminal and `--pillar A..M` pass, and N stays open by design: `--final` and R1 read the settings of the host they run on, so only the laptop can run them. The Owner holds `LAPTOP-CLOSEOUT.md`, one gate-checked document that runs from the branch push or fetch to `--final` and CLOSE.md. The gex44 pre-final run is recorded in `evidence/pre-final-gex44.md` with `PF_VERDICT=PASS` (16/16).

Host: gex44 (kobicraft-gex44), worktree sc-run, branch mission/skill-capability-run, base 3ff2cc1d. Not pushed.

## Commits
- `1792978c` docs(09-03): laptop closeout document for pillar N (D-02). Only LAPTOP-CLOSEOUT.md.
- `5464e84c` docs(09-03): record the gex44 pre-final run (D-03). Only evidence/pre-final-gex44.md.
- the docs(09-03) summary commit carrying this file.

`git log -1 --format=%s` and `git show --stat` were checked after each commit. `git diff --name-only 3ff2cc1d 5464e84c` lists exactly the two program files.

## LAPTOP-CLOSEOUT.md outline
0. Preamble: laptop unless marked gex44; the gex44 record path; what this run did not do (no push, no session spent, no state.N, no `--final`, no `~/.claude` edit); the W-01 note (closeout mode reads STATE.md at the commit that last touched the doc, and a new decision line needs a `### Q` if the doc is edited again); the I-02 note (the cbr.md N row records the gex44 status `open`, which cbr.md's own preamble also says); and the whole order, which explains why state.N comes before `--final`.
1. Bring the run branch to the laptop. On gex44, the recorded pick (a) push `git -C .../sc-run push origin mission/skill-capability-run:mission/skill-capability`; the alternative is to fetch the run branch from the gex44 clone. On the laptop, `git remote -v` then `git fetch <remote> mission/skill-capability`. Owner boundary 4: `git log --oneline FETCH_HEAD..HEAD` (foreign commits) and `HEAD..FETCH_HEAD` (the run's); push only once no foreign commits interleave; merge vs checkout is the Owner's choice.
2. `## Owner bundle, in order`: 19 verbatim numbered lines, generated from `git show HEAD:owner-bundle.md`. Tags in order: 1 [A], 2 [A], 3 [B], 4 [C], 5 [D], 6 [H], 7 [H], 8 [F], 9 [F] (gex44), 10 [G], 11 [G], 12 [G], 13 [E], 14 [L], 15 [I], 16 [J], 17 [J] (laptop and gex44), 18 [K], 19 [M].
3. `## Owner decisions`. Each Q section quotes `Source (STATE.md): "<line[2:82]>"`, generated from the HEAD STATE.md:
   - Q1 push ([Run, epoch 2]): options (a) the Owner pushes on gex44, (b) leave local and fetch the run branch. Recorded pick: (a).
   - Q2 E session spend ([Phase 7, epoch 3] and [Phase 7, epoch 4]): options (a) about 8 laptop sessions, C-fixed vs N0 at 4 per arm (effect 100 points, SEPARABLE inside the cap of 10, smallest total 7); (b) raise the D-SESSIONS cap to at least 15 (stored-grade 50 points, 6 vs 9; 20 at 10 per arm); (c) keep RESEARCH_INSUFFICIENT_EVIDENCE. Recorded pick: none (Owner-reserved). If E's terminal changes, the cbr.md E row and the E deltas must change with it.
   - Q3 mirror red ([Phase 8, epoch 3]): options a/b/c. Recorded pick: (a), the expected red until the Owner syncs the live copies (bundle item 17).
   - Q4 IN-04 ([Phase 8, epoch 4]): (a) keep the 7 pre-existing invalid frontmatters as recorded in the IN-04 delta; (b) rewrite them in a separate change and then widen the live-mirror sync. Recorded pick: (a), not fixed.
   The helper found no further decision lines (5 lines, 4 sections).
4. `## Close pillar N (laptop)`, 11 numbered steps:
   1. `git status --porcelain -- tools vault/programs/skill-capability` gives empty output (I-03); if not, inspect only with `git diff --stat` and `--ignore-cr-at-eol --stat`, never reset, clean or renormalize.
   2. `--selftest` gives SCP_SELFTEST=PASS.
   3. `--status` gives open ["N"] and violations [].
   4. `--closeout` before state.N gives FAIL only on V-PF-L8 with `L3 N`.
   5. The four LF sha256 values, via `ce.lf_sha256`.
   6. The one-line state.N template: IMPLEMENTED_AND_VERIFIED, a reason free of deferral words, gate `["python", "tools/test_skill_capability_prefinal.py", "--closeout"]`, prg pre-final-gex44.md, file ukdl.md, cbr.md and LAPTOP-CLOSEOUT.md, savings [].
   7. Commit ledger.json by pathspec.
   8. `--closeout` gives PF_VERDICT=PASS.
   9. Re-check step 1, then `--final` gives SCP_VERDICT=PASS. The R1 failure meaning names the declared `/skillOverrides` sha256 and `/env/CLAUDE_DOCTRINE_CARDS=deny`.
   10. CLOSE.md: host, commit, date, command, and the pasted output.
   11. Commit by pathspec, then push under boundary 4.

Pre-commit check with the gate's own functions on the written file: `check_bundle`, `check_decisions` and `check_commands` each returned []. The state.N template line parses as JSON, its kinds are gate/prg/file/file/file, `ce.gate_argv_problem` on its argv returns None, and `ce.DEFERRAL_PROSE` has 0 hits in the whole document.

## Task 1 gate (HEAD 1792978c)
`timeout 1200 python3 tools/test_skill_capability_prefinal.py` gave rc=0: all three V-PF-CLOSEOUT-* checks ok, `PF_FAILED=-`, `PF_VERDICT=PASS`.

## Record (evidence/pre-final-gex44.md, written at 1792978c)
```
host: gex44 (hostname kobicraft-gex44)
commit: 1792978ca9d501f434727b3f429f49b48c27a81d
date: 2026-10-04T00:13:41Z
command: python3 tools/test_skill_capability_prefinal.py --write-evidence
PF_MODE=gex44
PF_TERMINAL=A,B,C,D,E,F,G,H,I,J,K,L,M
PF_OPEN=N (expected: state.N and --final are laptop-only)
PF_PASS=16/16
PF_FAILED=-
PF_VERDICT=PASS
```
`--write-evidence` rc=0. The plan's verify grep counts 5 lines. `CEP_PILLAR_N=PASS` appears 0 times.

## Final gex44 run (HEAD 5464e84c, clean tree)
`timeout 1200 python3 tools/test_skill_capability_prefinal.py` gave rc=0: 16 of 16 ok, `PF_TERMINAL=A,...,M`, `PF_OPEN=N (expected: state.N and --final are laptop-only)`, `PF_PASS=16/16`, `PF_FAILED=-`, `PF_VERDICT=PASS` (V-PF-PILLARS 24.8 s).

## --closeout tail (HEAD 5464e84c)
`timeout 120 python3 tools/test_skill_capability_prefinal.py --closeout` gave rc=1:
```
  ok   V-PF-COMMITTED (the three executed code files are clean)
  FAIL V-PF-L8: check_ledger failures beyond the expected []: L3 N: no terminal disposition
  ok   V-PF-UKDL ...
  ok   V-PF-CBR ...
  ok   V-PF-DELTAS ...
  ok   V-PF-CLOSEOUT-BUNDLE (19 owner-bundle lines numbered in order)
  ok   V-PF-CLOSEOUT-DECISIONS (every STATE decision line has a ### Q section with Options: and Recorded pick:)
  ok   V-PF-CLOSEOUT-COMMANDS (--final, CLOSE.md, state.N, run branch and the --closeout gate argv present)
  ok   V-PF-GEX44-RECORD (vault/programs/skill-capability/evidence/pre-final-gex44.md at HEAD: gex44, PF_VERDICT=PASS, commit reachable)
PF_PASS=8/9
PF_FAILED=V-PF-L8
PF_VERDICT=FAIL
```
This is the expected state. The only failure is state.N, which belongs to the laptop. `python3 tools/test_skill_capability_program.py --status` gave rc 0, open ["N"], closed A..M, violations [].

## Acceptance
- Task 1: 19 numbered bundle lines (bundle count 19); 4 `### Q` sections and 4 `Recorded pick:` lines; 0 markers left; `git diff --name-only 3ff2cc1d 1792978c` lists only LAPTOP-CLOSEOUT.md.
- Task 2: `git show --stat HEAD` at 5464e84c lists only pre-final-gex44.md; ledger state.N is `{'terminal': None, 'evidence': [], 'savings': []}`; `git status --porcelain -- vault/programs/skill-capability tools` is empty; `git ls-remote origin refs/heads/mission/skill-capability` gives rc 0 and `287b360a` (unchanged: this run pushed nothing).

## N stays open on gex44 by design
state.N, `--final`, CLOSE.md and the push are the Owner's laptop steps in LAPTOP-CLOSEOUT.md section 4. This run did not run `--final`, did not write state.N, did not push, and did not edit `~/.claude`, owner-bundle.md, STATE.md or ROADMAP.md.

## Deviations from Plan
1. **[Unattended choice] Decision Source lines are generated as well.** The plan generates the bundle lines from a marker. The `Source (STATE.md): "..."` lines were filled by the same helper (`/tmp/0903_closeout_helper.py`, `<!-- decision:K -->` markers), so no STATE prefix was retyped. The helper refuses a missing marker, an unused marker, a marker used twice, or a prefix that holds a double quote.
2. **[Rule 3 - blocking] `git commit -- <path>` refused the new untracked file** ("pathspec did not match any file known to git"). Before committing, the path was staged with `git add -- <path>` and the index was checked to hold only that path. No other path was staged.
3. **[Unattended choice] I-02** was already satisfied by cbr.md's preamble (lines 6-8, from 09-02). LAPTOP-CLOSEOUT.md repeats it rather than editing cbr.md, which is outside this plan's files.
4. **[Unattended choice] Executor branch-namespace rule.** The generic protocol's `agent-*` allow-list does not fit the caller-bound branch `mission/skill-capability-run` (same as 09-02, deviation 3). The branch was asserted before each commit.

Hook-generated `docs/{arch,changelog,constitution,prd}/*`, `.gsd/` and `vault/progress.md` were left untracked or unstaged. They were never committed and never deleted.

## Known Stubs
None. The `<sha256 ...>` and `<the remote ...>` slots in LAPTOP-CLOSEOUT.md are values the Owner fills on the laptop. They cannot be computed on gex44: the hashes depend on the laptop's files at that moment, and the remote name cannot be observed from here.

## Threat Flags
None. The document holds paths, commands, hashes and Owner-facing figures only.

## Self-Check: PASSED
- FOUND at HEAD: vault/programs/skill-capability/LAPTOP-CLOSEOUT.md, vault/programs/skill-capability/evidence/pre-final-gex44.md
- FOUND: 1792978c, 5464e84c (`git log`)
