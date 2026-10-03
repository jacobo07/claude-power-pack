# Incremental Cognition -- Owner bundle

One line per pillar that needs an Owner action. The mission never asks mid-run (ROADMAP operating
constraints); it records the action here and continues with other phases. A pillar listed here stays
open until the action lands, unless its line says AUTHORIZATION_BOUND.

Run plane: GEX44 clone `~/missions/incremental-cognition`, branch `mission/incremental-cognition-run`
(never pushed; fetch it back).

## Items

- **[A]** PRG for pillar A (laptop-plane). Code is complete at `d2505df6`, already deployed into the laptop's live
  `tools/gsd_mission.py` (8.1 GB free, sha `A217654F...`). Re-measured on GEX44 2026-10-03 against this branch:
  `python tools/test_gsd_mission_cwd_align.py` 16/16, `python tools/test_gsd_epoch.py` 82/82,
  `python tools/test_gsd_mission.py` 212/213 (the one red, V-MC-PLAN-FACTS-REFUSES-OVERLAP, is plane: gex44:
  `plan_graph_check` refuses node v18.19.1, needs ^22.23.2 || ^24.14.0, see `[B]`; unrelated to A).
  **Action:** on the laptop, observe a held mission (m-fdefb0fca0c0 cognitive-economy or m-876f8b5a904a ucep)
  relay in the live sweep after a peer commit to main, and save the ledger row with `cwd_diverged_followed` as
  `vault/programs/incremental-cognition/evidence/A-prg.md`. Pillar A then closes IMPLEMENTED_AND_VERIFIED with
  gate `["python","tools/test_gsd_mission_cwd_align.py"]` + that prg file.
- **[C]** laptop deploy of the auth-refusal park and the pre-launch gate, then the PRG for pillar C. Expects: the
  ic-run worktree `/home/kobii/missions/incremental-cognition/.claude/worktrees/ic-run` on branch
  `mission/incremental-cognition-run` at or after `9a26750271991b080547eb6d8c1bbade5be52fef`. **Action,** on the
  laptop with at least 4 GB free, in the laptop's PP checkout (only the ssh host alias may differ if the laptop
  reaches GEX44 by another name; the repository path and branch are exact):

      git fetch kobii@kobicraft-gex44:/home/kobii/missions/incremental-cognition mission/incremental-cognition-run
      git cherry-pick 5962571c840943ae0a3aa901efb08e69a04434da 4c31bb0a504ddaaa6b601d6477374fdb8dc67f43 60e7947dcf3cf0f9c660e412ec6276a8b2922f99 7259ccb0da6d7183310aa0717e58859f07a6436e a1c593f2e8db2eb04983ae3348db660b2178323d c6dd2087469c6ca77beb464482417d27b9448805 9a26750271991b080547eb6d8c1bbade5be52fef
      python tools/test_persistent_failure_park.py
      python tools/test_mission_launch_gate.py
      python tools/test_provider_breaker.py
      python tools/test_gsd_mission.py
      python tools/test_gsd_epoch.py
      python tools/test_gsd_mission_cwd_align.py

  (`5962571c...` is plan 02-01, the park; `4c31bb0a...` is plan 02-02, the env preflight the gate imports; `60e7947d...` is plan 02-03, the launch gate; `7259ccb0`/`a1c593f2`/`c6dd2087`/`9a267502` are the review fixes WR-04/05/06/07. Expected after the picks: PFP 28/28, LG 20/20, BREAKER 18/18. `tools/test_gex44_env_preflight.py` is a GEX44 tool and is not part of this laptop check: after a cherry-pick its `V-ENVPF-PP-REAL-READY` reads red because the hard-coded `PP_COMMIT_FLOOR` hash does not exist in the laptop history -- see the WR-08 note.) **PRG:** after the a7 env
  deploy below, a7's mission shows `provider_held` (class auth, quarantine true, no launch) until the re-login, then
  `provider_released` and one relay. Save those ledger rows as `vault/programs/incremental-cognition/evidence/C-prg.md`.
  Pillar C then closes IMPLEMENTED_AND_VERIFIED with gate `["python3","tools/test_persistent_failure_park.py"]` +
  `C-prg.md`.
- **[B]** a7 re-login (interactive OAuth, never bypassed, credentials never copied between envs). Expects: the ic-run
  worktree on branch `mission/incremental-cognition-run` at or after `60e7947dcf3cf0f9c660e412ec6276a8b2922f99`.
  a7's login is expired (`expiresAt` 0, measured: `auth_expired`). **Action:** run the first command, type `/login`
  in that session, then run the check; its auth line must read READY.

      bash -c '. /home/kobii/a7-env/env.sh; exec claude'
      python3 /home/kobii/missions/incremental-cognition/.claude/worktrees/ic-run/tools/gex44_env_preflight.py --env-root /home/kobii/a7-env

- **[B]** env deploys (any working directory). Expects: the ic-run worktree on branch
  `mission/incremental-cognition-run` at or after `60e7947dcf3cf0f9c660e412ec6276a8b2922f99`. The deploy is a dry-run
  unless `--apply` is given; it resolves `--commit` in the source repo, prints and logs the resolved sha, takes the
  env's `sweep.lock`, and prints its own rollback commands. **Measured 2026-10-03 (dry-run, nothing applied):** BOTH
  envs REFUSE with exit 4 because their installs carry modified tracked files: a7 has 1
  (`vault/terminal_slots.json`, +21 lines of runtime state); a5 has 1024 (981 differ only in line endings, 43 are real
  content changes, +20463 lines: the hand-applied `a5_linux.patch` is the candidate). Nothing was overwritten; deciding
  what to discard is yours (destructive-state-authorization: the deploy never decides it). Per env, in order: dry-run,
  decide, then `--apply`. a7 first, then the a7 re-login above, so the C park and the B gate are both observable
  before the release.

      python3 /home/kobii/missions/incremental-cognition/.claude/worktrees/ic-run/tools/gex44_env_deploy.py --env-root /home/kobii/a7-env --source-repo /home/kobii/missions/incremental-cognition/.claude/worktrees/ic-run --commit mission/incremental-cognition-run
      python3 /home/kobii/missions/incremental-cognition/.claude/worktrees/ic-run/tools/gex44_env_deploy.py --env-root /home/kobii/a7-env --source-repo /home/kobii/missions/incremental-cognition/.claude/worktrees/ic-run --commit mission/incremental-cognition-run --apply
      python3 /home/kobii/missions/incremental-cognition/.claude/worktrees/ic-run/tools/gex44_env_deploy.py --env-root /home/kobii/a5-env --source-repo /home/kobii/missions/incremental-cognition/.claude/worktrees/ic-run --commit mission/incremental-cognition-run
      python3 /home/kobii/missions/incremental-cognition/.claude/worktrees/ic-run/tools/gex44_env_deploy.py --env-root /home/kobii/a5-env --source-repo /home/kobii/missions/incremental-cognition/.claude/worktrees/ic-run --commit mission/incremental-cognition-run --apply

  Dealing with the exit 4, after looking at what differs (these two preserve the content first; run them only if the
  changes are not needed):

      cp /home/kobii/a7-env/home/.claude/skills/claude-power-pack/vault/terminal_slots.json /home/kobii/a7-env/terminal_slots.json.owner-bak
      git -C /home/kobii/a7-env/home/.claude/skills/claude-power-pack checkout -- vault/terminal_slots.json
      git --no-optional-locks -C /home/kobii/a5-env/home/.claude/skills/claude-power-pack diff --binary > /home/kobii/a5-env/a5-install-local-changes.patch
      git -C /home/kobii/a5-env/home/.claude/skills/claude-power-pack checkout -- .

- **[B]** the GEX44 main-plane node is v18.19.1, outside the vendored engine range `^22.23.2 || ^24.14.0`: upgrade the
  system node (Owner action, deferred in CONTEXT; never bypassed). Measured scope: the a5 and a7 ENV nodes are
  v24.15.0, inside the range, so the env preflight's `interpreters` check is expected to read READY once the deploy
  lands a vendored engine range (today it is UNMEASURABLE on both: their old installs have no
  `vendor/genesis-suite/package.json`); the main node affects the main-plane reds `V-MC-PLAN-FACTS-REFUSES-OVERLAP`,
  `V-HPKT-ATTACH` and `V-HPKT-PARTIAL-REFUSED`. The `V-G23-*` card-byte reds are a separate pre-existing fact and are
  not claimed to clear with a node upgrade.
- **[B]** decisions for owners. (1) a7's hooks resolve into a5's tree (`hooks_foreign_env`): keep the sharing, or
  repoint a7 to its own hooks; the deploy restores a missing registered hook script only into the env's OWN hooks
  directory, never into another env's tree. (2) `tools/install_global_core.py` syncs agents, commands and the
  session-safety contract but does NOT copy hook scripts (it prints `cp` lines for the Owner), contrary to the note in
  plan 02-04; the deploy therefore restores only registered-but-missing hook scripts from the install's
  tracked `hooks/` directory, never overwriting; say if you want the installer itself changed instead. (3) The Windows-only
  "bare git is not on PowerShell PATH" trap in `modules/cascade_prevention/dangerous_cmds.py` fires on Linux for every
  plain `git` command: a rule defect for its owner, not staleness.
- **[B]** NOTE (merge strategy, Owner decision): `PP_COMMIT_FLOOR=60e7947d` (tools/gex44_env_preflight.py) exists only on `mission/incremental-cognition-run`, so merge that branch preserving the commit (no squash, no rebase) or re-point the floor in the same merge; otherwise every declared-plane env reads `pp_install_stale` and the deploy ends in code 7 (review WR-08).
- **[B]** DEBT, shrink-only, NOT closed by either PRG: `gsd_mission.py arm` launches its first worker through
  `launch_worker` without the pre-launch gate, so on a declared plane an arm can still start a worker into a
  NOT_READY env. What closes it: a later change that calls `mission_launch_gate.refusal` on the arm path before
  `launch_worker`, proven by a red-first test (arm on a declared plane with a NOT_READY preflight launches nothing
  and ledgers `launch_preflight_refused`). Until then, every arm on GEX44 is preceded by one of these and proceeds
  only on exit 0. Expects: the ic-run worktree on branch `mission/incremental-cognition-run`.

      python3 /home/kobii/missions/incremental-cognition/.claude/worktrees/ic-run/tools/gex44_env_preflight.py --env-root /home/kobii/a7-env
      python3 /home/kobii/missions/incremental-cognition/.claude/worktrees/ic-run/tools/gex44_env_preflight.py --env-root /home/kobii/a5-env

- **[B]** PRG: after the deploy and the re-login, the first command below shows no `pp_install_stale`,
  `hooks_broken` or `auth_expired`, and a7's next launch row shows `launch_gate` READY. Save the output and that
  ledger row as `vault/programs/incremental-cognition/evidence/B-prg.md`. Pillar B then closes
  IMPLEMENTED_AND_VERIFIED with gate `["python3","tools/test_gex44_env_preflight.py"]` + `B-prg.md`. This PRG does
  not close the arm debt above. Expects: the ic-run worktree on branch `mission/incremental-cognition-run` at or
  after `60e7947dcf3cf0f9c660e412ec6276a8b2922f99`.

      python3 /home/kobii/missions/incremental-cognition/.claude/worktrees/ic-run/tools/gex44_env_preflight.py --env-root /home/kobii/a7-env --json

## Phase 3 -- KME-L measurements (laptop plane)

Status of every command below: **NOT RUNNABLE HERE** (laptop paths, the KME-L corpus is not on GEX44). They are
proven only to parse with the instrument's own argument parser (gate `V-KMEP-BUNDLE-ARGV-PARSES`,
`python3 tools/test_kme_pillars.py`); nothing below has been run on the laptop.

Expects: the laptop PP checkout (`C:\Users\User\.claude\skills\claude-power-pack`, Python is `python`, projects
root `C:\Users\User\.claude\projects`) holding the P0 freeze commit `18e928af8c489f9d29dd1e76e0c7aa3c6a6975eb` and
the pointer commit that writes `vault/programs/incremental-cognition/FROZEN_AT` (`d4d350599d2272141681162e4ae79a1361c34676`;
the gate `V-KMEP-FREEZE-INSTANT` reads that file: if `git log --oneline -1 -- vault/programs/incremental-cognition/FROZEN_AT`
prints nothing, run `git cherry-pick d4d350599d2272141681162e4ae79a1361c34676` first), then the phase-3 code commits of branch `mission/incremental-cognition-run`, obtained as in `[C]` (only the ssh
host alias may differ; the repository path and branch are exact). The fourteen picks, in order: plan 03-01
`4e0333f8`, `d1f67731`, `ac0e5f2e`; plan 03-02 `7e6d46e1`, `35a58f87`, `9d9795dd`; plan 03-03 `10eec6dc`,
`4d2a25f4`, `a85752b1`; plan 03-04 `263d8ac2`, `80eab96c`, `3e5fd0d7`; plan 03-05 `754d19c9` (the R3 done-gate
guard) and `333adc90` (the parser entry point). The commits that only add this bundle text, its parse gate and
the evidence file are not needed on the laptop.

    git fetch kobii@kobicraft-gex44:/home/kobii/missions/incremental-cognition mission/incremental-cognition-run
    git cherry-pick 4e0333f81081dbd75aa68acf8cfb1397e5c60c59 d1f677317f84de0100d52588bfc350c2f3400a13 ac0e5f2ecd672bf9e5af90156c4402981ebafac6 7e6d46e1c8361dcd4a8e8ac934211b91fbf45290 35a58f8776ecf1d905035829a6dfefafbc85a86f 9d9795dd49b3a92f6393858713ff6b1bdb9d8a68 10eec6dc2652f81a844063ca80e90e7de990e13d 4d2a25f44771ecabaef6e14c18746199f5e29464 a85752b1cb7eeac5553e5771e1bd77c47cbb91a0 263d8ac2424969a08726749605ff7a6987cec34e 80eab96c89559e8155ca0a147eeccc29c95d24d5 3e5fd0d788e5778cbd5ed71edafac895f5a45a97 754d19c9e89db83c86359671a728168508ecd96d 333adc90abcdaf3eeb68922e04c77f89f8b2f6c6
    python tools/test_kme_pillars.py
    python tools/test_incremental_cognition_program.py --selftest

`python tools/test_kme_pillars.py` must exit 0 on the laptop (its GEX44 real-corpus gates print SKIP there).

The population proof comes first and gates every file. Its first run is UNFILTERED over the whole projects root,
because the frozen KME rule classifies sessions by content, so a dir holding KME sessions need not match any name
filter:

    python wiki/tools/kme_pillars.py population --denominator KME-L --until auto --expand --root C:\Users\User\.claude\projects

Its `per_project` rows list every dir that holds KME sessions. If it prints `"population_match": "exact"` (exit 0),
use the same flags below. If not (exit 3, `cutoff_not_found` names the fields that differ), P0's project-dir list
was never recorded, so the unfiltered root may include KME sessions P0 did not scan: re-run with one `--root <dir>`
per P0 project dir taken from those rows (no `--expand`) until it is exact, and use those roots in every command
below instead of `--expand --root C:\Users\User\.claude\projects`. Optional speed-up once the dirs are known, accepted
only if the filtered population is still exact (example regex):

    python wiki/tools/kme_pillars.py population --denominator KME-L --until auto --expand --root C:\Users\User\.claude\projects --project-filter "(?i)kobii|kme|mapengine"

A KME-L file whose population is not exact is UNMEASURED and closes nothing (the R3 guard in
`tools/test_incremental_cognition_program.py` also refuses any file without `terminal_evidence: true`). One-scan
alternative that writes all six KME-L files at once (with the roots the proof settled on):

    python wiki/tools/kme_pillars.py all --denominator KME-L --until auto --expand --root C:\Users\User\.claude\projects

After the runs, commit only the printed files, by pathspec (`git add --
vault/programs/incremental-cognition/measurements/`, then `git commit -F <msgfile> --
vault/programs/incremental-cognition/measurements/`). Each file is named `<P>-KME-L-<date>.md` and names its
denominator, plane and exact `command:`.

- **[D]** hook additional-context rent (silent-success hooks). Expects: the population proof above exact. **Action:**

      python wiki/tools/kme_pillars.py d --denominator KME-L --until auto --expand --root C:\Users\User\.claude\projects
      python wiki/tools/kme_pillars.py d --denominator CPP-D-W7 --expand --root C:\Users\User\.claude\projects

  Writes `D-KME-L-<date>.md` and `D-CPP-D-W7-<date>.md`. The D-W7 file is a referenced denominator (the CE ledger's
  window and weighted figure; never re-measured): its coverage must be >= 1 for terminal evidence, and the parser
  difference (CE dedupes calls across files keeping the last copy, this instrument counts per file with max-merge) is
  in its caveats. Pillar D then takes the terminal its frozen rule gives ("a slice only at >= 3 % weighted"; broken
  hook delivery is fixed under B regardless); the ledger cites both files. Pillar stays open until its file lands;
  ledger state.D is not written by this mission run.
- **[E]** identical rereads of large sources. Expects: the population proof above exact. **Action:**

      python wiki/tools/kme_pillars.py e --denominator KME-L --until auto --expand --root C:\Users\User\.claude\projects

  Writes `E-KME-L-<date>.md` (the primary file). If that file says `second_workload_required: true`, also:

      python wiki/tools/kme_pillars.py e --denominator CPP-D-W7 --role second_workload --expand --root C:\Users\User\.claude\projects

  This is the frozen rule's "confirmed on a second workload". The program accepts CPP-D-W7 as the second workload
  (it is the frozen, referenced workload; a KME-G file is never a second workload for E, it is smoke). The ledger
  then cites BOTH files for E: R3 accepts the second workload only beside a primary file with `terminal_evidence`
  true, and only when its `second_workload_valid` is true (coverage >= 1). Pillar stays open until its file lands;
  ledger state.E is not written by this mission run.
- **[F]** GSD workflow-doc residency. Expects: the population proof above exact. **Action:**

      python wiki/tools/kme_pillars.py f --denominator KME-L --until auto --expand --root C:\Users\User\.claude\projects

  Writes `F-KME-L-<date>.md`. Then the residency finding goes to the GSD owner
  (`~/.claude/gsd-core/bin/gsd-tools.cjs`) as `vault/programs/incremental-cognition/handoffs/F.md`, using the file's
  `init_json_present` and its paired doc-to-init ratio ("never fork GSD"). Pillar stays open until its file lands;
  ledger state.F is not written by this mission run.
- **[G]** re-tested falsified hypotheses and re-litigated sealed decisions. Expects: the population proof above
  exact. **Action:**

      python wiki/tools/kme_pillars.py g --denominator KME-L --until auto --expand --root C:\Users\User\.claude\projects

  Writes `G-KME-L-<date>.md`. The count is an interval from a heuristic text classifier (positive control: the C6
  -> K4 listing-hiding pair): check its samples by hand and record the measured precision beside the file before any
  slice ("one falsifiable slice on the existing owner only if the count clears materiality or a correctness
  exception"). Pillar stays open until its file lands; ledger state.G is not written by this mission run.
- **[H]** verification share. Expects: the population proof above exact. **Action:**

      python wiki/tools/kme_pillars.py h --denominator KME-L --until auto --expand --root C:\Users\User\.claude\projects

  Writes `H-KME-L-<date>.md` (the file also records `consumed_owner_verdicts`). The frozen rule is "consume CE P and
  G verdicts; one KME-specific check that verification share is below materiality": R2 additionally needs
  `owner_ledger` evidence of the CE P and G terminals at a commit on this history (both are open at this branch's
  HEAD as read by the H smoke file). Pillar stays open until its file lands; ledger state.H is not written by this
  mission run.
- **[I]** subagent bootstrap floor. Expects: the population proof above exact. **Action:**

      python wiki/tools/kme_pillars.py i --denominator KME-L --until auto --expand --root C:\Users\User\.claude\projects

  Writes `I-KME-L-<date>.md`. Then the measured subagent first-call context goes to CE B / SC A-C as a handoff
  ("no move of a rule or skill here"); R2 needs `owner_ledger` evidence of the CE B and SC B terminals. Pillar stays
  open until its file lands; ledger state.I is not written by this mission run.

## Phase 4 -- floor reference (laptop plane)

Status of every command below: **NOT RUNNABLE HERE** (laptop paths and the laptop install). They are proven only to
parse with the gate's own argument parser (gate `V-FLOOR-BUNDLE-ARGV-PARSES`, `python3
tools/test_floor_regression_gate.py`); nothing below has been run on the laptop.

- **[K]** laptop reference floor and PRG for pillar K. The gate (`tools/floor_regression_gate.py`) is built and
  smoke-proven on GEX44 against real GEX44 transcripts, with a plane-gex44 reference
  (`floor/reference-gex44.json`, `provenance.window_sha256` dc6d23b90cac... over `window_rows` 34, pinned to the mission
  worker transcript 34f03871 and re-derived from disk by gate `V-FLOOR-REAL-REFERENCE-PINNED`). The frozen rule needs the
  reference to come from the laptop install, which only the Owner can write. Expects: the laptop PP checkout
  `C:\Users\User\.claude\skills\claude-power-pack`, Python is `python`, and (option A only) the project directory
  `C:\Users\User\.claude\projects\C--Users-User--claude-skills-claude-power-pack` exists (`dir` it first; that path is
  inferred from the harness's path sanitization and has not been verified on the laptop). **Action,** in the PP
  checkout, in this order. First fetch and cherry-pick the eight K code commits, oldest first (the commits that add this
  bundle text, its parse gate and `evidence/K.md` are not needed on the laptop):

      git fetch kobii@kobicraft-gex44:/home/kobii/missions/incremental-cognition mission/incremental-cognition-run
      git cherry-pick 7fdef637db297983496bd137d85e695ffdc27f46 e445939387f3d1747a76ba2aa0fac9ea2bc17716 8422eb2d704f510ba37a89d47ba6eafa3ebf6a55 13f3bffe619b340470ac8970fe1a0aa56ff49a8c 11686c8d33795da5e6eccc02b40fa621656c40d5 f065ac8eeb47d1ae594a2790590e426485e873d8 17228d2f025ef524dd82467030136b36d4812874 09bb91427cddd1963d6b567e8e3146b5f3636710

  Then the fixture suite and the seeded positive control on a real laptop transcript (the control seeds scratch copies,
  so any real laptop session serves it; the champion-startup probe session is used here). Expected, not measured:
  exit 0; the GEX44 `-REAL` gates print SKIP on the laptop, and the gates that need POSIX file modes or a script as
  the owner's argv[0] SKIP on Windows (a SKIP is never a PASS and is outside the n/m count);
  `PASS V-FLOOR-SEEDED-REAL` appears on the second line:

      python tools/test_floor_regression_gate.py
      python tools/test_floor_regression_gate.py --real-session 8f983bc6-d760-4440-938d-aeed86a548ae

  Then write the laptop reference, ONE of two options. Note for both: `--probe` without env `CPP_FLOOR_PROBE_RESULTS`
  appends one row to the TRACKED `wiki/tools/listing_floor_probe.results.jsonl` (the probe's documented behaviour);
  commit that row with the reference or discard it deliberately, never by a blanket checkout.

  Option A, recommended -- one headless session, spends quota: Owner decision. The probe's cwd defaults to the PP
  checkout, so universal AND project layers are measured. The self-check reads the newest session of that project
  directory. An ordinary session's first prompt differs from the probe's, so the tokens axis is not comparable and the
  gate says so: without `--chars-only` that is exit 2 `tokens_unmeasured` (the gate working, never a pass); with
  `--chars-only` the expected result is verdict `WITHIN_BOUND_CHARS_ONLY`, exit 0, with a `CHARS_ONLY` line stating
  the tokens axis was not compared (expected, not measured on the laptop):

      python tools/floor_regression_gate.py --write-reference vault/programs/incremental-cognition/floor/reference.json --probe
      python tools/floor_regression_gate.py --check --project-dir C:\Users\User\.claude\projects\C--Users-User--claude-skills-claude-power-pack --chars-only

  Option B -- no quota, the champion-startup probe already on disk (session 8f983bc6, cwd
  `C:\Users\User\Apps\listing-probe\champion`, an empty probe directory: universal layers only, so every later check
  must be a session with that same cwd). The self-check below is a SANITY PARSE ONLY: it checks the reference against
  the very session it was written from, so it proves the file loads and is comparable, never that the floor held
  (expected exit 0):

      python tools/floor_regression_gate.py --write-reference vault/programs/incremental-cognition/floor/reference.json --session 8f983bc6-d760-4440-938d-aeed86a548ae
      python tools/floor_regression_gate.py --check --session 8f983bc6-d760-4440-938d-aeed86a548ae

  Then commit the reference by pathspec: `git add -- vault/programs/incremental-cognition/floor/reference.json`, then
  `git commit -F` a message file you wrote first, restricted to that same path.

  **PRG** (closes K). It MUST be one real `--check` against the committed `floor/reference.json` (the default
  `--reference`) of a LATER session of the same kind and cwd as the reference, because nothing else will ever run that
  check. Option A: the same `--check --project-dir ... --chars-only` line after the next ordinary PP session (no quota);
  record its verdict as `WITHIN_BOUND_CHARS_ONLY` (the tokens axis was not compared), never as plain `WITHIN_BOUND`.
  Option B: one fresh probe session in the champion directory (one session, quota). Run it first without the flag: if
  the probe prompt matches the champion session's the tokens axis is compared and the verdict is plain `WITHIN_BOUND`;
  if it prints exit 2 `tokens_unmeasured` the prompts differed, so run the second line and record the chars-only
  verdict as such (save both outputs):

      python tools/floor_regression_gate.py --check --project-dir C:\Users\User\.claude\projects\C--Users-User--claude-skills-claude-power-pack --chars-only
      python tools/floor_regression_gate.py --check --probe --cwd C:\Users\User\Apps\listing-probe\champion
      python tools/floor_regression_gate.py --check --probe --cwd C:\Users\User\Apps\listing-probe\champion --chars-only

  Save its output, its exit code and the reference's sha256 as
  `vault/programs/incremental-cognition/evidence/K-prg.md`. A RISE in the PRG is the gate working, not a failure of the
  step: the Owner either explains it in `reference.json` `explanations` (layer, scope, unit, delta_bound, reason,
  commit) or re-baselines with `--write-reference ... --replace`. Pillar K then closes IMPLEMENTED_AND_VERIFIED with gate
  `["python","tools/test_floor_regression_gate.py"]` + `K-prg.md`; until then the pillar stays open and ledger
  state.K is not written by this mission run. **Named debt:** `tools/` is outside the liveness scanner and the closing
  gate argv is the fixture suite, so after K closes no hook, CI job or `--final` run executes `--check` against
  `reference.json`; that single PRG check is the only real one until someone wires a surface, and its absence afterwards
  is silence, not health.
