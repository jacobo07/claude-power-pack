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
  `mission/incremental-cognition-run` at or after `60e7947dcf3cf0f9c660e412ec6276a8b2922f99`. **Action,** on the
  laptop with at least 4 GB free, in the laptop's PP checkout (only the ssh host alias may differ if the laptop
  reaches GEX44 by another name; the repository path and branch are exact):

      git fetch kobii@kobicraft-gex44:/home/kobii/missions/incremental-cognition mission/incremental-cognition-run
      git cherry-pick 5962571c840943ae0a3aa901efb08e69a04434da 60e7947dcf3cf0f9c660e412ec6276a8b2922f99
      python tools/test_persistent_failure_park.py
      python tools/test_mission_launch_gate.py
      python tools/test_provider_breaker.py
      python tools/test_gsd_mission.py
      python tools/test_gsd_epoch.py
      python tools/test_gsd_mission_cwd_align.py

  (`5962571c...` is plan 02-01, the park; `60e7947d...` is plan 02-03, the launch gate.) **PRG:** after the a7 env
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
