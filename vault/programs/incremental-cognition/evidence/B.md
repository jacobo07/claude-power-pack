# Pillar B -- remote cognitive environment integrity (GEX44 a5/a7): evidence

Plane: GEX44 (`kobicraft-gex44`, main node v18.19.1, python3 3.12.3), run branch `mission/incremental-cognition-run`.
Written by plan 02-04 from the plan 02-02 and 02-03 summaries, the 02-04 runs, and read-only measurements of a5 and a7.

## Frozen rule (verbatim from `ledger.json`, `frozen.pillars` id B)

> correctness exception. Preflight before a remote launch proves auth readiness, rules version, hook health and interpreters, or refuses with a typed reason; stale rules and broken hooks are repaired by a repeatable deploy, never hand copying; re-login itself is an Owner action

## Commands and observed outputs

Code commits: `4c31bb0a504ddaaa6b601d6477374fdb8dc67f43` (02-02: preflight), `60e7947dcf3cf0f9c660e412ec6276a8b2922f99`
(02-03: the pre-launch gate), `562ff3d29d07739f5101488ab01bc755f0dc6450` (02-04 tracer: dry-run deploy, floor raised),
`37a8b5187985500fd82e73be8baeab6dd6bde673` (02-04: apply path).

**Floor raise (I1).** `PP_COMMIT_FLOOR` is now `60e7947dcf3cf0f9c660e412ec6276a8b2922f99` (the commit that adds
`tools/mission_launch_gate.py`) and `PP_REQUIRED_FILES` gains that file, so an install that has the C repair but not
the launch gate reads `pp_install_stale`. Re-run after the change: `ENVPF_PASS=55/55`, `PASS V-ENVPF-PP-REAL-READY`,
`PASS V-ENVPF-PP-STALE-REAL (head=01199995 floor=60e7947d)`. The a5/a7 verdicts in `B-preflight-gex44.json` were measured
against the 02-01 floor; both installs predate BOTH floors, so their verdict class is unchanged and they were not
silently re-measured under the old file; the new dry-run below re-measured them under the new floor (same class).

**Preflight (02-02), measured 2026-10-03T18:26Z, quoted from `02-02-SUMMARY.md` / `B-preflight-gex44.json`:**

| env | verdict | reasons | notes |
|-----|---------|---------|-------|
| a7 | NOT_READY | auth_expired, pp_install_stale | install head 01199995; hooks READY (50 judged, every hook resolves into a5's tree: `hooks_foreign_env`); interpreters UNMEASURABLE |
| a5 | NOT_READY | pp_install_stale | install head 192390b9 on feature/knowledge-acquisition; auth READY; hooks READY; interpreters UNMEASURABLE |

**Deploy tool RED and GREEN (02-04).**

```
$ python3 tools/test_gex44_env_deploy.py        (before tools/gex44_env_deploy.py existed)
ModuleNotFoundError: No module named 'gex44_env_deploy'

$ python3 tools/test_gex44_env_deploy.py        (apply gates added, apply path not yet built)
FAIL V-DEPLOY-APPLY: AttributeError: module 'gex44_env_deploy' has no attribute 'apply_deploy'
FAIL V-DEPLOY-IDEMPOTENT / -DIRTY-REFUSED / -NOT-ANCESTOR-REFUSED / -LOCK-HELD / -REPLAN-UNDER-LOCK: same AttributeError
FAIL V-DEPLOY-CREDENTIALS-UNTOUCHED: SystemExit: 2      FAIL V-DEPLOY-CLI-EXIT: {'dirty': 2, 'ancestry': 2, 'lock': 2}
DEPLOY_PASS=7/16  threshold=16/16

$ python3 tools/test_gex44_env_deploy.py        (GREEN)
PASS V-DEPLOY-DRYRUN-PLAN: rc=0 env_head=01199995 target=... hooks_repair=True plane_marker=will add rollback=3 reasons=['pp_install_stale', 'hooks_broken']
PASS V-DEPLOY-DRYRUN-NO-MUTATION: rc=0 changed=[] files=3106 control_sees=['refs', 'tree']
PASS V-DEPLOY-APPLY: code=0 target_was_absent=True head==target=True backup_ref->old=True env.sh+1line=True bak_env=True bak_head=True hook_restored=True after_reasons=['interpreter_unsupported'] log_lines=1 installer_rc=0
PASS V-DEPLOY-DIRTY-REFUSED / -NOT-ANCESTOR-REFUSED / -LOCK-HELD / -REPLAN-UNDER-LOCK / -CREDENTIALS-UNTOUCHED / -REAL-UNTOUCHED
DEPLOY_PASS=16/16  threshold=16/16
```

The scratch env's install is a REAL clone of this repository detached at a7's measured head `01199995`, so the
staleness (`pp_install_stale`) and the broken hook (`hooks_broken`) are real history, not a fixture; the apply gate
uses a standalone repository that does not contain the target, so the deploy must really `git fetch` it. The
`interpreter_unsupported` left after the apply is the scratch environment's node v18.19.1 against the deployed engine
range: reported as an Owner action, never bypassed.

Drills (`--drill`, unmutated control green before and after):

```
KILLED M1 dirty check skipped by V-DEPLOY-DIRTY-REFUSED -- code=0 file_intact=True ...
KILLED M2 ancestry check skipped by V-DEPLOY-NOT-ANCESTOR-REFUSED -- code=7 unchanged=False head=01199995 ...
KILLED M3 dry-run path also applies by V-DEPLOY-DRYRUN-NO-MUTATION -- rc=0 changed=['git_head', 'tree'] ...
KILLED M4 env.sh/pp.head written without backup by V-DEPLOY-APPLY -- FileNotFoundError: ... pp.head.bak-...
KILLED M5 lock failure ignored by V-DEPLOY-LOCK-HELD -- code=0 head=562ff3d2 unchanged=False
KILLED M6 apply uses the pre-lock plan by V-DEPLOY-REPLAN-UNDER-LOCK -- stale_plan_env_head=01199995 apply_old_head=01199995 moved_to=e5280349 ...
DRILL killed=6/6
```

Launch gate (02-03): `LG_PASS=19/19`, `DRILL killed=6/6`; observed again in this run.

**Read-only dry-run of the deploy on the REAL envs (never `--apply`), 2026-10-03T18:54Z.** Full plans in
`B-deploy-dryrun-gex44.json`.

| env | exit | refusal | env head -> target | what it would do |
|-----|------|---------|--------------------|------------------|
| a7 | 4 | the install has 1 modified tracked file: `vault/terminal_slots.json` | 01199995 -> branch tip (ancestor: yes) | would add `CPP_MISSION_PLANE=gex44`, refresh `pp.head`; hooks repair not needed (hooks READY) |
| a5 | 4 | the install has 1024 modified tracked files | 192390b9 -> branch tip (ancestor: yes) | same, no `pp.head` to refresh (a5 has none) |

Both refusals are RESULTS, not failures to be resolved here: nothing was overwritten, and what to discard is an Owner
decision (destructive-state-authorization), routed through `owner-bundle.md`. Measured detail of the modifications:
a7 +21 lines of runtime state in one file; a5 about 981 files differ only in line endings and 43 carry real content
changes (+20463/-444), `a5_linux.patch` being the candidate.

**No-write proof.** `stat -c '%n %s %Y'` on 9 env files (the 8 of 02-02 plus `a7-env/pp.head`) before and after the
two dry-runs and the five read-only owner-bundle commands run verbatim from cwd `/tmp`: `diff` printed nothing. The
credentials files were deliberately excluded (a live worker may refresh them).

**Disclosure.** The first attempt at this proof was invalid and was redone: a5's install `.git/index` mtime moved
(1790281507 -> 1791053631) because of an ad-hoc `git --no-optional-locks diff --stat` / `diff -w` I ran in a5's
install to describe the 1024 files, not because of the deploy (the move is after the a5 dry-run ended, no cron sweep
fired in between, and a fresh bracket around only the dry-runs shows no change). It refreshed git's stat cache only:
no tracked content, ref or HEAD changed. The accepted proof is the second one.

**Runs-as-written.** The five read-only commands in `owner-bundle.md` were extracted from the file and run verbatim
from `/tmp`: two preflights exit 1, `--json` preflight exit 1, two deploy dry-runs exit 4; none printed "No such file
or directory" or "can't open file".

**Regression** (this run; FAIL lists equal the 02-03 baselines): `PFP_PASS=24/24` (+ drill 5/5), `ENVPF_PASS=55/55`
(+ drill 6/6), `LG_PASS=19/19` (+ drill 6/6), `DEPLOY_PASS=16/16` (+ drill 6/6), `BREAKER_PASS=18/18`,
`MC_PASS=212/213` (only `V-MC-PLAN-FACTS-REFUSES-OVERLAP`, node v18.19.1), `EPOCH_PASS=82/82`, `MCA_PASS=16/16`.
Ledger: `git diff --stat 34d08aa9 -- vault/programs/incremental-cognition/ledger.json` prints nothing.

```
$ python3 tools/test_incremental_cognition_program.py --pillar B
  FAIL L3 B: no terminal disposition
CEP_PILLAR_B=FAIL
```

## Artifacts (LF sha256 of each committed file the evidence relies on)

```
3f7b66cb7d9062a08bfb10a59a22809d920edf74d7bd36944c0d56d76a3c90f8  tools/gex44_env_deploy.py
cf0b6745c65515b75a88bc14ace27d7cf44b1345faee90de60e440d3678c5ade  tools/test_gex44_env_deploy.py
4b9a949df0dbaae376afa0e76fe0188f723508594ae62d4641db7de7b6da72c2  tools/gex44_env_preflight.py
b500d3911b0c871f55754e46ac35feea4ac8507ac06d2b44748cd5c36145bea0  tools/test_gex44_env_preflight.py
95e538e52af2e218724d33ae95c62b3e45e823be83ceea6ad775b29579d6198f  tools/mission_launch_gate.py
962bb4e9589e0fb94cda17620295a751e4b81d4e7b76019b042b48109930977a  vault/programs/incremental-cognition/evidence/B-preflight-gex44.json
aa2f71e07f38f355aa040457c163bcc73e33ffd2fcdd72306803d93b4ba8ceea  vault/programs/incremental-cognition/evidence/B-deploy-dryrun-gex44.json
06c65be36d86d9246034c82145718d4d33e579a5dcb17555dd4258fcc60aede4  vault/programs/incremental-cognition/owner-bundle.md
```

## Product Delta

What changes for the Owner:

- One command says whether an env can launch and why not (`gex44_env_preflight.py --env-root ...`: READY,
  NOT_READY with a reason from a closed set, or UNMEASURABLE; exit 0/1/2).
- One command repairs a stale env by git, with backups, instead of a bundle, a tarball or a hand-written `pp.head`:
  `gex44_env_deploy.py` dry-runs by default, takes the env's own sweep lock, refuses a modified install, an env HEAD
  that is not an ancestor of the target, a non-env directory and the user's own HOME, keeps `refs/pp-deploy/backup-*`,
  `env.sh.bak-*`, `pp.head.bak-*` and a `pp-deploy.log` line, and prints the exact rollback commands.
- A declared env (`CPP_MISSION_PLANE=gex44`, added by the deploy) refuses a launch on a measured NOT_READY and records
  the typed reasons in the ledger; an undeclared host is never judged by GEX44 rules.
- Today both a5 and a7 are NOT_READY and both deploy dry-runs refuse (modified installs). The Owner actions, in order,
  are in `owner-bundle.md`; the a7 re-login stays interactive and is never bypassed.

## Intelligence Delta

What the system knows now that it did not:

- The measured a5/a7 verdicts and reasons (above), including that a7's access token is expired (`expiresAt` 0) and both
  installs predate the park and the launch gate.
- a7's hooks resolve into a5's tree (`hooks_foreign_env`): hook health there is a pass on a neighbour's files, not on
  isolation.
- The access token lapsing is not an expired login: a lapsed access token with a live refresh token is READY with the
  finding `access_token_lapsed_refreshable`.
- The two installs differ from git only by local changes the deploy will not overwrite: a7 by one runtime-state file,
  a5 by 1024 files of which about 43 are real edits.
- `tools/install_global_core.py` does NOT copy hook scripts (it prints `cp` lines for the Owner), contrary to the note
  in plan 02-04. The deploy therefore restores only registered-but-missing hook scripts, from the install's tracked
  `hooks/` directory, into the env's own hooks directory, never overwriting.
- The a5/a7 ENV nodes are v24.15.0, inside the vendored range `^22.23.2 || ^24.14.0`; only the GEX44 MAIN node
  (v18.19.1) is outside it. Their `interpreters` check is UNMEASURABLE today only because the old installs carry no
  `vendor/genesis-suite/package.json`; a deploy supplies it.

## Named debts

- `gsd_mission.py arm` launches its first worker through `launch_worker` without the pre-launch gate, so on a declared
  plane an arm can still start a worker into a NOT_READY env. Shrink-only; NOT closed by either PRG. What closes it: a
  later change that calls `mission_launch_gate.refusal` on the arm path before `launch_worker`, proven by a red-first
  test (arm on a declared plane with a NOT_READY preflight launches nothing and ledgers `launch_preflight_refused`).
  Until then every arm on GEX44 is preceded by the env preflight and proceeds only on exit 0 (`owner-bundle.md`).
- `tools/test_gsd_x_runtime_preflight.js` is laptop-plane: 3/7 on GEX44.
- `modules/liveness/reachability.py` does not enumerate `tools/`; reachability of the new tools is the import edge from
  `gsd_mission.supervise` (`V-LG-REAL-PREFLIGHT-E2E`) and the CLI, not the liveness gate.
- The Windows-only "bare git is not on PowerShell PATH" trap in `modules/cascade_prevention/dangerous_cmds.py` fires on
  Linux for plain `git` commands: a rule defect for its owner, not staleness.
- The apply path was proven on scratch envs only. It has never run against a real env; the first real `--apply` is an
  Owner action and the first real test of the installer step on an env with real settings.

## Status: OPEN

Ledger `state.B` is NOT written and IC-B is not ticked. The terminal is the Owner-run PRG (re-login, env deploys,
`B-prg.md`; lines in `owner-bundle.md`). `--pillar B` prints `CEP_PILLAR_B=FAIL` "no terminal disposition", as expected.
