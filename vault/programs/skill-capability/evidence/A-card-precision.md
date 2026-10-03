# [A] card precision + C8 maturity -- evidence (host: gex44)

Plane: every runtime claim below was observed on host `kobicraft-gex44` (Linux, git 2.43.0, node 18, python3), by running the pillar A gate against the repo checkout. GEX44 is not the laptop's live install. What the live laptop hook does is not claimed here; it is routed to the Owner bundle as one `[A]` line (host: laptop).

## Rule and where it lives

`hooks/doctrine_cards.js`, function `ownShellWindowHit`, reason string `mtime-in-own-shell-window` (ledger field `unknown_reasons`). A foreign-hunk file is classed unknown (not a deny) when its mtime lies inside one of this session's shell tool-call windows, widened by 1 s slack at the end, and is after this session's last own Edit/Write of that file. A file whose mtime predates the session, or sits at or before its own last edit, stays foreign and is denied.

Aperture, as the card header states it: the rule needs the session transcript to contain the shell call's start and its tool_result; a window with no closing result is open and does not count; the mtime is read from disk with one bounded `git rev-parse --show-toplevel`, so a file that cannot be stat-ed is not allowed by this rule. It does not cover lines a predecessor session wrote by Edit (rollover), and it does not make a concurrent writer's file own: a writer whose write landed outside every shell window of this session is still denied.

## D-CARD (frozen 5)

Source: `vault/programs/skill-capability/card_evidence_pack.json` (sha256 `dacfdf5aa8afb0a5e6221ebf98fcf1b70866c7de3931083e210e7e948a6c0c05`), replay spec `card_replay_spec.json`.

| replay | session | deny ts (Z) | file(s) | writer call id | writer window (Z) | mtime_ms | mtime_source |
|---|---|---|---|---|---|---|---|
| 300ac3a1 | 300ac3a1 | 12:14:12.096 | .planning/workstreams/ucep/ROADMAP.md, STATE.md | toolu_01KaUpAebLRSL1dYJX9VHYgY | 12:13:52.456 - 12:14:04.421 | 1791029638438.5 | placed |
| 5b36b02f-1 | 5b36b02f | 13:29:15.159 | tests/e2e/force-reload-renderer-replacement.spec.ts | toolu_01Y2yAeMUdcRgrkqpyVPvUGj | 13:26:38.207 - 13:27:00.341 | 1791034009274.0 | placed |
| 5b36b02f-2 | 5b36b02f | 13:50:42.964 | tests/e2e/helpers/terminal-input-probes.ts | toolu_01GT1WCnXMcqgRYjPbj96GdQ | 13:50:01.259 - 13:50:27.830 | 1791035414544.5 | placed |
| 3a05f288 | 3a05f288 | 13:43:56.219 | data/costaluz/leads-stall-2026-10/trust-census/census.json | toolu_014BkTUUhuKSPbvLgPpUWhDy | 13:39:24.204 - 13:40:45.729 | 1791034845084.3274 (13:40:45.084Z) | measured |
| 4a7ee8bc | 4a7ee8bc | 14:25:15.572 | vault/programs/cognitive-economy/ledger.json | toolu_01McaxH96TWdkVLre6f3rbEs | 14:23:51.562 - 14:24:04.907 | 1791037438234.5 | placed |

Exactly one mtime is measured: 3a05f288, whose value comes from the evidence pack's own recorded mtime (a laptop measurement, carried in the pack; not re-measured on gex44). The other four mtimes were placed by the replay at the midpoint of a writer window. Those writer windows were identified from the tool-call command text in the pack, and the mtimes themselves were not measured: the pack either holds the mtime of a different checkout copy, a value that predates the session, or no file at all (`exists: false`). So four of the five replays show that the rule allows a file written inside the identified window; they do not show that the real file's mtime fell there.

Stated limits of the pack (each recorded in the spec notes, none adjusted):
- The pack truncates every tool-call command to 300 characters, so replay transcripts carry truncated commands.
- 4a7ee8bc: the writer is identified by window times only. The pack's truncated command for that call shows `WriteAllText` of `spec_*.json` under a job tmp dir and does not contain `ledger_write.py` literally. The window times match the phase context exactly; naming `ledger_write.py` as the writer is not confirmable from the pack.
- 5b36b02f-1: the 300 characters end at the `oxlint` call, so `oxfmt` is not visible in that window.
- Hunks are synthetic (3 invented lines per file); the pack is content-free. Names, session ids, timestamps and windows are real.

Gate line, verbatim:

`D-CARD frozen_denies=5 replayed_allowed=5/5 presession_denied=5/5 mutant_denied=5/5 | beside: 4615e1d1 (after freeze) denied=True class=rollover-predecessor-lines`

Reading: with the window rule, 5/5 replays are allowed (decision `unknown`); the same five with the mtime moved to before the session are denied 5/5 (the rule does not allow a pre-session hunk); a mutant whose `ownShellWindowHit` body is replaced by `return false` denies 5/5 again (so the allow comes from the rule). Arm C (a judged commit is not a write) stays covered by `V-DC-JUDGED-COMMIT-NOT-A-WRITE`, observed in the node suite output.

## Beside D-CARD (not folded in)

The 6th deny, session 4615e1d1 (deny ts 2026-10-03T14:42:22.154Z, after the freeze), file `docs/reference/pty-multi-window-lifecycle-reset.md`, is reported beside D-CARD, never inside the `/5`. A rollover-resumed session committed lines its predecessor (5b36b02f, via `certify --from`) wrote by Edit; the file's mtime is this session's own last Edit (placed at the end of that call, 14:42:07.480Z), not a shell window, so the window rule does not allow it and the gate asserts it stays denied (class `rollover-predecessor-lines`). Rollover-predecessor ownership is not built in this phase; the fix would read the certified predecessor's transcript and is named, not done.

## git exit 128 x6

The frozen denominator carries `unknown_git_exit_128 = 6`. Gate line, verbatim:

`D-CARD unknown_git_exit_128=6: abcd1234 x3 -> cannot_chdir (reproduced; capsule-guard e2e ran the card without a private state dir); fce2689e x3 -> cause not recoverable from the pack (rows carry no stderr; calls_in_window=0,0,0); classes now recorded per row: git_error`

- abcd1234 x3 (basis index): reproduced on gex44 as `cannot_chdir` (`fatal: cannot change to 'C:\proj': No such file or directory`, exit 128). Cause: `hooks/tests/test-capsule-mutation-guard.js` e2e ran the card with a Windows `cwd` and without a private state dir, so its rows landed in the live ledger. Fixed: the test now sets `DOCTRINE_CARDS_STATE_DIR` to a temp dir; a sweep over test files that carry a commit command (population discovered, floor 2) and a drill (stripped copy flagged, unmodified copy not) pin it. The capsule e2e section itself was not run on gex44: the dispatcher's card path `../skills/claude-power-pack/hooks/doctrine_cards.js` is the laptop layout and does not resolve here, so "the e2e no longer writes the live ledger" rests on the ENV change plus the sweep and drill, not on an observed e2e run.
- fce2689e x3 (basis only-paths): the cause is not recoverable from the pack. Verbatim INFO line: `INFO fce2689e: pack tool_calls=97 first_start=2026-10-03T08:41:10.845Z last_start=2026-10-03T15:09:37.415Z rows=['2026-10-03T14:12:55.252Z', '2026-10-03T14:13:41.324Z', '2026-10-03T14:16:04.817Z'] calls_in_120s_before_row=0,0,0 (the exact command is not in the pack and cannot be reproduced from it)`. Future rows carry `git_error` (enum only, never raw stderr).

Classes reproduced on gex44 with git 2.43's own stderr:

| class | rc | stderr (first line) |
|---|---|---|
| cannot_chdir | 128 | `fatal: cannot change to 'C:\proj': No such file or directory` |
| not_a_repo | 129 | `warning: Not a git repository. Use --no-index to compare two paths outside a working tree` (for `diff --cached`: ``error: unknown option `cached'`` plus the `usage: git diff --no-index` banner) |
| unborn_head | 128 | `fatal: bad revision 'HEAD'` |
| outside_repo | 128 | `fatal: <path>: '<path>' is outside repository at '<repo>'` |

NOT-REPRODUCED: `dubious_ownership`. The gate line is `NOT-REPRODUCED V-SCA-128-DUBIOUS-OWNERSHIP host=kobicraft-gex44: decision=unknown reason='git exit 129' basis=index git_error=not_a_repo (git test seam GIT_TEST_ASSUME_DIFFERENT_OWNER did not produce the dubious-ownership stderr here)`. The classifier handles the documented git text against a synthetic string only; no real git output produced it on this host. On git 2.43 the seam yields exit 129 with the no-index banner, so a dubious-ownership repo would likely be recorded as `not_a_repo`.

Unborn HEAD is fixed rather than only named: on a numeric non-zero exit with `HEAD` and class `unborn_head`, the card judges against the empty tree (one bounded `hash-object -t tree --stdin`, ledger field `base: empty-tree`); `V-SCA-UNBORN-HEAD-JUDGED` shows `denied=True ... base=empty-tree`. This is one possible cause of fce2689e's only-paths rows, not an identified one.

## C8

The commit card is a delivery card that asks once: deny once with the questions, then the same commit passes. It is never an authority (it holds no veto beyond that one ask), and its default mode records only. Nothing in pillar A raises it to enforcement.

## Out-of-owner change to flag

Plan 01-02 changed `hooks/capsule_mutation_guard.js` (commit eadc0fd5): `path.basename` became `path.win32.basename` in `unwrapCall`. Behaviour is identical on Windows; on POSIX it fixes a pre-existing defect that kept the capsule suite at `CMG_PASS=17/18` on gex44 (observed before the change). That file is a live laptop hook outside pillar A's frozen owners. It is routed to the Owner bundle for accept-or-revert when hooks are synced to the laptop.

## Gate output

command: `python3 tools/test_card_precision.py`
host: kobicraft-gex44, date 2026-10-03T16:50:13Z, HEAD a60f34e7, rc 0

```
host=kobicraft-gex44
ok   V-SCA-FIXTURE-SHA: sha256=dacfdf5aa8afb0a5e6221ebf98fcf1b70866c7de3931083e210e7e948a6c0c05
ok   V-SCA-SPEC-PACK-PIN: spec pins dacfdf5aa8afb0a5e6221ebf98fcf1b70866c7de3931083e210e7e948a6c0c05
ok   V-SCA-SPEC-FIVE-FROZEN: replays=['300ac3a1', '5b36b02f-1', '5b36b02f-2', '3a05f288', '4a7ee8bc']
ok   V-SCA-SPEC-6TH-BESIDE: beside=['4615e1d1']
ok   V-SCA-SPEC-MEASURED-ONLY-3a05f288: measured=['3a05f288'] placed=['300ac3a1', '4a7ee8bc', '5b36b02f-1', '5b36b02f-2']
ok   V-SCA-SPEC-MTIME-INSIDE-WRITER-WINDOW: inside=[True, True, True, True, True]
ok   V-SCA-SPEC-WRITER-IDS-REAL: every writer id and window equals the pack's call
ok   V-SCA-REPLAY-ALLOWED-300ac3a1: mtime=placed decision=unknown denied=False reasons={'.planning/workstreams/ucep/ROADMAP.md': 'mtime-in-own-shell-window', '.planning/workstreams/ucep/STATE.md': 'mtime-in-own-shell-window'}
ok   V-SCA-PRESESSION-DENIED-300ac3a1: mtime=first_tool_call-60s denied=True decision=deny-card
ok   V-SCA-REPLAY-ALLOWED-5b36b02f-1: mtime=placed decision=unknown denied=False reasons={'tests/e2e/force-reload-renderer-replacement.spec.ts': 'mtime-in-own-shell-window'}
ok   V-SCA-PRESESSION-DENIED-5b36b02f-1: mtime=first_tool_call-60s denied=True decision=deny-card
ok   V-SCA-REPLAY-ALLOWED-5b36b02f-2: mtime=placed decision=unknown denied=False reasons={'tests/e2e/helpers/terminal-input-probes.ts': 'mtime-in-own-shell-window'}
ok   V-SCA-PRESESSION-DENIED-5b36b02f-2: mtime=first_tool_call-60s denied=True decision=deny-card
ok   V-SCA-REPLAY-ALLOWED-3a05f288: mtime=measured decision=unknown denied=False reasons={'data/costaluz/leads-stall-2026-10/trust-census/census.json': 'mtime-in-own-shell-window'}
ok   V-SCA-PRESESSION-DENIED-3a05f288: mtime=first_tool_call-60s denied=True decision=deny-card
ok   V-SCA-REPLAY-ALLOWED-4a7ee8bc: mtime=placed decision=unknown denied=False reasons={'vault/programs/cognitive-economy/ledger.json': 'mtime-in-own-shell-window'}
ok   V-SCA-PRESESSION-DENIED-4a7ee8bc: mtime=first_tool_call-60s denied=True decision=deny-card
ok   V-SCA-MUTANT-APPLIED: declarations=1 differs=True
ok   V-SCA-MUTANT-DENIES-300ac3a1: mtime=placed denied=True decision=deny-card
ok   V-SCA-MUTANT-DENIES-5b36b02f-1: mtime=placed denied=True decision=deny-card
ok   V-SCA-MUTANT-DENIES-5b36b02f-2: mtime=placed denied=True decision=deny-card
ok   V-SCA-MUTANT-DENIES-3a05f288: mtime=measured denied=True decision=deny-card
ok   V-SCA-MUTANT-DENIES-4a7ee8bc: mtime=placed denied=True decision=deny-card
ok   V-SCA-6TH-DENY-STAYS-DENIED-4615e1d1: mtime=placed denied=True decision=deny-card class=rollover-predecessor-lines
D-CARD frozen_denies=5 replayed_allowed=5/5 presession_denied=5/5 mutant_denied=5/5 | beside: 4615e1d1 (after freeze) denied=True class=rollover-predecessor-lines
ok   V-SCA-128-ROWS-SPLIT: 6 = abcd1234 x3 (index) + fce2689e x3 (only-paths)
ok   V-SCA-128-CANNOT-CHDIR-abcd1234: denied=False decision=unknown reason='git exit 128' basis=index git_error=cannot_chdir
INFO git=git version 2.43.0 host=kobicraft-gex44
ok   V-SCA-128-NOT-A-REPO: index: decision=unknown reason='git exit 129' basis=index git_error=not_a_repo | pathspec: decision=unknown reason='git exit 129' basis=only-paths git_error=not_a_repo (observed on this git: outside a repo `git diff` exits 129 via --no-index, not 128)
ok   V-SCA-128-OUTSIDE-REPO: decision=unknown reason='git exit 128' basis=only-paths git_error=outside_repo
ok   V-SCA-128-UNBORN-HEAD-CLASSIFIED: real git rc=128 stderr="fatal: bad revision 'HEAD'" -> unborn_head
ok   V-SCA-UNBORN-HEAD-JUDGED: denied=True decision=deny-card reason=None basis=only-paths git_error=None base=empty-tree
NOT-REPRODUCED V-SCA-128-DUBIOUS-OWNERSHIP host=kobicraft-gex44: decision=unknown reason='git exit 129' basis=index git_error=not_a_repo (git test seam GIT_TEST_ASSUME_DIFFERENT_OWNER did not produce the dubious-ownership stderr here)
INFO fce2689e: pack tool_calls=97 first_start=2026-10-03T08:41:10.845Z last_start=2026-10-03T15:09:37.415Z rows=['2026-10-03T14:12:55.252Z', '2026-10-03T14:13:41.324Z', '2026-10-03T14:16:04.817Z'] calls_in_120s_before_row=0,0,0 (the exact command is not in the pack and cannot be reproduced from it)
D-CARD unknown_git_exit_128=6: abcd1234 x3 -> cannot_chdir (reproduced; capsule-guard e2e ran the card without a private state dir); fce2689e x3 -> cause not recoverable from the pack (rows carry no stderr; calls_in_window=0,0,0); classes now recorded per row: git_error
ok   V-SCA-NODE-DOCTRINE-CARDS: rc=0 last='DOCTRINE_CARDS_PASS=34/34'
ok   V-SCA-ARM-C: doctrine-cards output contains PASS V-DC-JUDGED-COMMIT-NOT-A-WRITE
ok   V-SCA-NODE-DESTRUCTIVE-CARD: rc=0 last='DDC_PASS=15/15'
ok   V-SCA-NODE-CAPSULE-GUARD: rc=0 last='CMG_PASS=18/18  threshold=18/18' (run without --e2e: the dispatcher's card path ../skills/claude-power-pack/hooks/doctrine_cards.js is the laptop layout and does not resolve on this host)
ok   V-SCA-STATE-DIR-SWEEP: population=['test-capsule-mutation-guard.js', 'test-doctrine-cards.js'] without_private_state_dir=[] floor=2
ok   V-SCA-STATE-DIR-DRILL: stripped copy flagged=['test-capsule-mutation-guard.js'] (population ['test-capsule-mutation-guard.js']); unmodified copy flagged=[]
SCA_PASS=36/36
```

## Savings

One figure, an upper bound: +1 turn per false deny (the re-issue after the card), 5 in D-CARD. Status upper_bound, displacement unknown, denominator D-CARD. No realized saving is claimed: the evidence is host-gex44 replays, not live sessions.

## Commits

- Plan 01-01: 4e9cf4d4 (window rule + 3a05f288 tracer replay), e32fd6d3 (all 5 replays, mutant pole, 6th deny beside), 48c46acc (V-DC-MTIME-* node cases), docs 0eb6f08f.
- Plan 01-02: 71cd35e0 (git_error classifier, abcd1234 reproduced), 9db76722 (empty-tree judge for first commit, each 128 class reproduced), eadc0fd5 (capsule guard win32 basename), 4ed37f5d (private state dir for the capsule test, sweep), docs a60f34e7.
