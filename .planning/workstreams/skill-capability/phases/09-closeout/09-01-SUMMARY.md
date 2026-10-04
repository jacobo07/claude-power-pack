---
phase: 09-closeout
plan: 01
subsystem: skill-capability program closeout
status: complete
tags: [closeout, pre-final, gate, pillar-N, gex44]
requires: [phase 8 verified (08-VERIFICATION.md at HEAD)]
provides:
  - tools/test_skill_capability_prefinal.py (D-03 gex44 pre-final check, pillar N's laptop gate --closeout, --write-evidence, --selftest)
affects: [09-02 (reviews + deltas must satisfy V-PF-UKDL/CBR/DELTAS), 09-03 (LAPTOP-CLOSEOUT.md + record must satisfy V-PF-CLOSEOUT-*/GEX44-RECORD)]
tech-stack:
  added: []
  patterns: [CommittedResolver (ce.Resolver over HEAD blobs), pure check functions + green/mutant selftest, single guarded subprocess entry point]
key-files:
  created: [tools/test_skill_capability_prefinal.py]
  modified: []
decisions:
  - "D-03 realised as a script, not a recorded command block: every check can be driven red (kills=45/45)"
  - "run_wrapper is an allow-list (--status, --selftest, --pillar A-N) and also refuses every argparse abbreviation of --final (--fin, --fina)"
  - "Closeout-mode V-PF-CLOSEOUT-DECISIONS reads STATE.md at the commit that last touched LAPTOP-CLOSEOUT.md (plan-check W-01 amendment)"
metrics:
  duration: ~10 min
  completed: 2026-10-04
plan_head_before: 829332c3ca46ea9e434827632f96e92d3dcf28db
actuals:
  tokens: 12400   # chars/4 over the realized code diff (49428 chars)
  tasks: 2
  commits: 4      # git rev-list --count 829332c3..HEAD after this SUMMARY lands: 2 code + 2 docs (see Deviations 5)
---

# Phase 9 Plan 01: pre-final check Summary

`tools/test_skill_capability_prefinal.py` is the D-03 gex44 pre-final check. It runs the wrapper's `--selftest`, `--status`, `--pillar A..M` and `--pillar N`, reads every static input from HEAD blobs, and reports N as open by design. Its `--closeout` mode is a gate for pillar N on the laptop that does not recurse into `--final`. Selftest: 20 green controls, kills=45/45.

Host: gex44 (hostname kobicraft-gex44), worktree sc-run, branch mission/skill-capability-run, base 829332c3.

## Commits
- `fcbc4347` feat(09-01): pre-final check for the skill-capability closeout (D-03)
- `5af4d16c` fix(09-01): name the post-run bracket V-PF-DIRTY-SET-STABLE and give it selftest poles
- docs(09-01) summary commits: the first captured only an interim progress note (see Deviations 5), and the second carries this file

The two code commits touch only `tools/test_skill_capability_prefinal.py`. `git status --porcelain -- tools vault/programs/skill-capability` is empty after both. Not pushed.

## Selftest
`timeout 120 python3 tools/test_skill_capability_prefinal.py --selftest` ends with:
```
PF_SELFTEST_GREENS=20
PF_SELFTEST=PASS kills=45/45
```
The plan asked for at least 28 mutants. Every one of the plan's `<behavior>` mutants is present. Extra mutants: L8 in closeout mode with N still open; the W-01 pair (a decision line on STATE at the doc commit that the doc lacks goes red, gex44 mode reading HEAD goes red, and closeout mode with no doc commit is INCONCLUSIVE); the `--fin` abbreviation; and DIRTY-SET-STABLE. W-01's green control: a decision line added to STATE.md in a later commit leaves closeout mode PASS.

## Real gex44 run (HEAD 5af4d16c)
`timeout 1200 python3 tools/test_skill_capability_prefinal.py > /tmp/09-01-run.txt` gave rc=1 in 24.2 s wall time:
```
PF_MODE=gex44
PF_HEAD=5af4d16cec3b06c28ecbe599ff57954ce43dfe29
  ok   V-PF-COMMITTED (program dir and tools/ clean in the working tree)
  FAIL V-PF-L8: check_ledger failures beyond the expected ['L3 N: no terminal disposition']: L8 review ukdl: missing or its file does not exist; L8 review cbr: missing or its file does not exist; L8 delta product: empty; L8 delta intelligence: empty
  FAIL V-PF-UKDL: vault/programs/skill-capability/reviews/ukdl.md missing at HEAD
  FAIL V-PF-CBR: vault/programs/skill-capability/reviews/cbr.md missing at HEAD
  FAIL V-PF-DELTAS: deltas.product is empty or not a list; deltas.intelligence is empty or not a list; pillars named by no delta: ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M']
  FAIL V-PF-CLOSEOUT-BUNDLE: vault/programs/skill-capability/LAPTOP-CLOSEOUT.md missing at HEAD
  FAIL V-PF-CLOSEOUT-DECISIONS: vault/programs/skill-capability/LAPTOP-CLOSEOUT.md missing at HEAD
  FAIL V-PF-CLOSEOUT-COMMANDS: vault/programs/skill-capability/LAPTOP-CLOSEOUT.md missing at HEAD
  ok   V-PF-LEDGER-INVARIANT (all keys but state/reviews/deltas and state.N equal the FROZEN_AT ledger)
  ok   V-PF-UKDL-UNTOUCHED (no commit since the freeze touches vault/knowledge_base/ukdl-universal.md)
  ok   V-PF-NO-FINAL (run_wrapper(['--final']) raised ValueError; no process started)
  ok   V-PF-SELFTEST (SCP_SELFTEST=PASS rc 0, 0.4s)
  ok   V-PF-STATUS (open ['N'], closed A..M, violations [])
  ok   V-PF-PILLARS (--pillar A..M each rc 0 CEP_PILLAR_<P>=PASS, 22.2s)
  ok   V-PF-N-OPEN (--pillar N rc 1, CEP_PILLAR_N=FAIL on exactly 'L3 N: no terminal disposition')
  ok   V-PF-DIRTY-SET-STABLE (dirty set unchanged while the wrapper ran)
PF_TERMINAL=A,B,C,D,E,F,G,H,I,J,K,L,M
PF_OPEN=N (expected: state.N and --final are laptop-only)
PF_PASS=9/16
PF_FAILED=V-PF-L8,V-PF-UKDL,V-PF-CBR,V-PF-DELTAS,V-PF-CLOSEOUT-BUNDLE,V-PF-CLOSEOUT-DECISIONS,V-PF-CLOSEOUT-COMMANDS
PF_VERDICT=FAIL
```
This is the expected state. `PF_FAILED` is exactly the seven checks whose inputs 09-02 and 09-03 have not written yet. Acceptance greps: 8 ok lines for COMMITTED, LEDGER-INVARIANT, UKDL-UNTOUCHED, NO-FINAL, SELFTEST, STATUS, PILLARS and N-OPEN; `CEP_PILLAR_N=PASS` appears 0 times; `PF_OPEN=N (expected` appears once.

The dirty-tree pole was also seen on real data. A run before the first commit, while the script was still untracked under tools/, gave `INCONCLUSIVE V-PF-COMMITTED`, and all four wrapper checks were skipped and reported INCONCLUSIVE.

## --closeout tail (HEAD 5af4d16c)
`timeout 120 python3 tools/test_skill_capability_prefinal.py --closeout` gave rc=1:
```
  ok   V-PF-COMMITTED (the three executed code files are clean)
  FAIL V-PF-L8: check_ledger failures beyond the expected []: L3 N: no terminal disposition; L8 review ukdl: ...; L8 review cbr: ...; L8 delta product: empty; L8 delta intelligence: empty
  ... (UKDL, CBR, DELTAS, CLOSEOUT-BUNDLE/-DECISIONS/-COMMANDS FAIL, input missing at HEAD)
  FAIL V-PF-GEX44-RECORD: vault/programs/skill-capability/evidence/pre-final-gex44.md missing at HEAD
PF_PASS=1/9
PF_FAILED=V-PF-L8,V-PF-UKDL,V-PF-CBR,V-PF-DELTAS,V-PF-CLOSEOUT-BUNDLE,V-PF-CLOSEOUT-DECISIONS,V-PF-CLOSEOUT-COMMANDS,V-PF-GEX44-RECORD
PF_VERDICT=FAIL
```
`grep -c 'CEP_PILLAR_'` on this output gives 0, so the closeout mode started no wrapper subprocess.

## Liveness
`python3 modules/liveness/reachability.py --json` `len(offenders)`: 64 before and 64 after.

## Interface vs code
The plan's interface summary matched the code: CE lines 56/99/116/182/251-258, the wrapper's rebinding at lines 38-43, and the wrapper's CLI. The wrapper's `--status` prints indented JSON. `parse_status` takes the outermost `{...}` span so that stderr noise cannot break parsing.

## Deviations from Plan

### Auto-fixed / added
1. **[Rule 2 - security] `run_wrapper` also refuses abbreviations of `--final`.** CE's argparse allows prefix abbreviations, so `--fin` or `--fina` would have reached CE's `--final` past a literal `"--final" in args` check. The guard is now an allow-list (`--status`, `--selftest`, `--pillar <A-N>`) plus an explicit refusal of every prefix of `--final`. The script's own argparse uses `allow_abbrev=False`. A selftest mutant covers `--fin`. Commit fcbc4347.
2. **[Rule 2 - correctness] Added a post-run bracket, `V-PF-DIRTY-SET-STABLE`.** It re-reads the dirty set after the wrapper subprocesses. If the set moved while the wrapper read the working tree, the result is INCONCLUSIVE. The check was first named V-PF-COMMITTED-AFTER, which made the plan's acceptance grep count 9 lines. Commit 5af4d16c renamed it and extracted `judge_stable`, with a green control and a mutant, because the plan requires a mutant for every V-PF check. The check adds one row to PF_PASS (16 checks in gex44 mode).
3. **Small additions beyond the format contracts, recorded so 09-02 and 09-03 know about them:**
   - C-UKDL: the `- Trap:` and `- Rule:` lines must be non-empty. Every backticked token on a `- Source:` line is treated as a path and must exist at HEAD.
   - C-CBR: a cell may wrap its value in backticks.
   - C-RECORD (`judge_record`): beyond the contract, the record must also hold `PF_TERMINAL=A,...,M` and `PF_OPEN=N (expected: ...)`, the hostname in the host line must contain `gex44`, and no line may say `CEP_PILLAR_N=PASS`. These are the must_haves of 09-03.
   - V-PF-L8: a FAIL reason names the expected list beside the extra failures.
4. **W-01 amendment implemented** as specified. `run_decisions(mode, ...)` takes HEAD in gex44 mode and `git log -1 --format=%H HEAD -- LAPTOP-CLOSEOUT.md` in closeout mode. If no commit touched the file, or STATE.md cannot be read at that commit, the result is INCONCLUSIVE. If the document itself is missing at HEAD, the result is FAIL, naming the path.
5. **The SUMMARY took two docs commits.** A PreToolUse anti-thrash hook blocked the Write of the full SUMMARY (three Writes in a row without a Read). The commit was issued in the same batch, so it captured the interim 8-line progress note. Rather than amend, which is prohibited, the full SUMMARY landed in a second docs commit that touches only this file.

### Unattended choices (safest option)
- `--write-evidence` checks the hostname before running and exits rc 2 with `PF_WRITE_EVIDENCE=REFUSED` on a host that is not gex44. On gex44 it writes the record whatever the verdict, so the evidence shows a FAIL as a FAIL. `judge_record` accepts only a record that ends in PASS.
- `--write-evidence` was not run in this plan, because 09-03 owns the record.
- Hook-created stubs (`docs/*/tools__*.md`, `.gsd/`, `vault/progress.md`) were left untracked or unstaged. They were never committed and never deleted.

## Known Stubs
None.

## Threat Flags
None. The script adds no network, auth or schema surface. It runs only `git` and `python <wrapper>` with allow-listed arguments, and writes only the evidence record, which only `--write-evidence` writes.

## Self-Check: PASSED
- FOUND: tools/test_skill_capability_prefinal.py (HEAD blob)
- FOUND: fcbc4347, 5af4d16c (both in `git log --all`)
