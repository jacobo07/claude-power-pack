# Incremental Cognition -- Owner bundle

One line per pillar that needs an Owner action. The mission never asks mid-run (ROADMAP operating
constraints); it records the action here and continues with other phases. A pillar listed here stays
open until the action lands, unless its line says AUTHORIZATION_BOUND.

Run plane: GEX44 clone `~/missions/incremental-cognition`, branch `mission/incremental-cognition-run`
(never pushed; fetch it back).

## Summary (every Owner item, phases 1-5)

A row exists below for every item of this file, for the `## Laptop code sync` step and for every pending human check of the
phase UAT and VERIFICATION files; the full text and every command are in the item named in `source`. Coverage is discovered,
not listed: `python3 tools/test_kme_replay.py` (V-KMER-BUNDLE-SUMMARY-ITEMS, V-KMER-BUNDLE-SUMMARY-UAT) turns red when an
item or a pending check has no row, or a row cites something that no longer exists. Order: the code sync, the laptop items,
the GEX44 items, then the judgement checks that exist only as pending UAT tests.

| # | pillar | source | action | exact command | what closes when it lands |
|---|---|---|---|---|---|
| 1 | laptop: D-I, K, L code | sync | Fetch the branch tip, check the ancestor and an empty status, check out the program tool files, commit them by pathspec, then run the four suites | `git fetch kobii@kobicraft-gex44:/home/kobii/missions/incremental-cognition mission/incremental-cognition-run` | the four suites each exit 0 on the laptop (expected, not measured there) |
| 2 | C | [C]#1 "laptop deploy of" ; UAT 02#1 | On the laptop with at least 4 GB free, cherry-pick the seven pillar-C commits, run the six suites, then take the PRG after the a7 env deploy and re-login | `git cherry-pick 5962571c840943ae0a3aa901efb08e69a04434da 4c31bb0a504ddaaa6b601d6477374fdb8dc67f43 60e7947dcf3cf0f9c660e412ec6276a8b2922f99 7259ccb0da6d7183310aa0717e58859f07a6436e a1c593f2e8db2eb04983ae3348db660b2178323d c6dd2087469c6ca77beb464482417d27b9448805 9a26750271991b080547eb6d8c1bbade5be52fef` | pillar C IMPLEMENTED_AND_VERIFIED: gate python3 tools/test_persistent_failure_park.py + evidence/C-prg.md |
| 3 | A | [A]#1 "PRG for pillar" ; VER 01#1 | On the laptop observe a held mission (m-fdefb0fca0c0 or m-876f8b5a904a) relay in the live sweep after a peer commit to main, and save the ledger row as evidence/A-prg.md | none -- observation in the laptop's live sweep, no command line in the item | pillar A IMPLEMENTED_AND_VERIFIED: gate python tools/test_gsd_mission_cwd_align.py + evidence/A-prg.md |
| 4 | D | [D]#1 "hook additional-context rent" ; UAT 03#1 ; UAT 03#3 | Run the unfiltered population proof first, then D on KME-L and on the CPP-D-W7 second workload | `python wiki/tools/kme_pillars.py population --denominator KME-L --until auto --expand --root C:\Users\User\.claude\projects` ; `python wiki/tools/kme_pillars.py d --denominator KME-L --until auto --expand --root C:\Users\User\.claude\projects` ; `python wiki/tools/kme_pillars.py d --denominator CPP-D-W7 --expand --root C:\Users\User\.claude\projects` | pillar D takes the terminal its frozen rule gives (a slice only at >= 3 % weighted); the ledger cites both files |
| 5 | E | [E]#1 "identical rereads of" ; UAT 03#1 | Run E on KME-L (and on CPP-D-W7 as second workload if the file says second_workload_required) | `python wiki/tools/kme_pillars.py e --denominator KME-L --until auto --expand --root C:\Users\User\.claude\projects` | pillar E takes its frozen terminal once E-KME-L-<date>.md lands (and the second workload when required) |
| 6 | F | [F]#1 "GSD workflow-doc residency." ; UAT 03#1 | Run F on KME-L, then hand the residency finding to the GSD owner as handoffs/F.md | `python wiki/tools/kme_pillars.py f --denominator KME-L --until auto --expand --root C:\Users\User\.claude\projects` | pillar F takes its frozen terminal once F-KME-L-<date>.md lands |
| 7 | G | [G]#1 "re-tested falsified hypotheses" ; UAT 03#1 | Run G on KME-L and check its samples by hand before any slice | `python wiki/tools/kme_pillars.py g --denominator KME-L --until auto --expand --root C:\Users\User\.claude\projects` | pillar G takes its frozen terminal once G-KME-L-<date>.md lands |
| 8 | H | [H]#1 "verification share. Expects:" ; UAT 03#1 | Run H on KME-L (it records consumed_owner_verdicts) | `python wiki/tools/kme_pillars.py h --denominator KME-L --until auto --expand --root C:\Users\User\.claude\projects` | pillar H takes its frozen terminal once H-KME-L-<date>.md lands |
| 9 | I | [I]#1 "subagent bootstrap floor." ; UAT 03#1 | Run I on KME-L, then hand the subagent first-call context to CE B / SC A-C | `python wiki/tools/kme_pillars.py i --denominator KME-L --until auto --expand --root C:\Users\User\.claude\projects` | pillar I takes its frozen terminal once I-KME-L-<date>.md lands |
| 10 | L | [L]#1 "KME-L offline replay" | Run the offline replay ranking of the three live experiments on KME-L and commit the printed file by pathspec | `python wiki/tools/kme_replay.py rank --denominator KME-L --until auto --expand --root C:\Users\User\.claude\projects` | the KME-L ranking file L-KME-L-<date>.md (each figure an upper bound); pillar L stays open until it lands |
| 11 | L | [L]#2 "decision on live" | Decide in your own words whether to approve live champion / challenger sessions (spends quota) or decline, and write it as evidence/L-owner-decision.md naming [L] | none -- the Owner's decision file, written by the Owner; the bundle is never the decision | with the decision file, L can close AUTHORIZATION_BOUND |
| 12 | K | [K]#1 "laptop reference floor" ; UAT 04#1 | After the sync, run the fixture suite, write the laptop reference (Option A spends quota, Owner decision; Option B does not) and take one real --check as the PRG | `python tools/floor_regression_gate.py --write-reference vault/programs/incremental-cognition/floor/reference.json --probe` ; `python tools/floor_regression_gate.py --check --project-dir C:\Users\User\.claude\projects\C--Users-User--claude-skills-claude-power-pack --chars-only` | pillar K IMPLEMENTED_AND_VERIFIED: gate python tools/test_floor_regression_gate.py + evidence/K-prg.md |
| 13 | B | [B]#2 "env deploys (any" ; UAT 02#2 | Per env, a7 first: dry-run, decide what to do with the install-local changes, then --apply | `python3 /home/kobii/missions/incremental-cognition/.claude/worktrees/ic-run/tools/gex44_env_deploy.py --env-root /home/kobii/a7-env --source-repo /home/kobii/missions/incremental-cognition/.claude/worktrees/ic-run --commit mission/incremental-cognition-run` ; `python3 /home/kobii/missions/incremental-cognition/.claude/worktrees/ic-run/tools/gex44_env_deploy.py --env-root /home/kobii/a7-env --source-repo /home/kobii/missions/incremental-cognition/.claude/worktrees/ic-run --commit mission/incremental-cognition-run --apply` ; `python3 /home/kobii/missions/incremental-cognition/.claude/worktrees/ic-run/tools/gex44_env_deploy.py --env-root /home/kobii/a5-env --source-repo /home/kobii/missions/incremental-cognition/.claude/worktrees/ic-run --commit mission/incremental-cognition-run` ; `python3 /home/kobii/missions/incremental-cognition/.claude/worktrees/ic-run/tools/gex44_env_deploy.py --env-root /home/kobii/a5-env --source-repo /home/kobii/missions/incremental-cognition/.claude/worktrees/ic-run --commit mission/incremental-cognition-run --apply` | post-deploy preflight shows no pp_install_stale, hooks_broken or auth_expired (see the PRG row) |
| 14 | B | [B]#1 "a7 re-login (interactive" | Run /login in a7's session, then the preflight check | `bash -c '. /home/kobii/a7-env/env.sh; exec claude'` ; `python3 /home/kobii/missions/incremental-cognition/.claude/worktrees/ic-run/tools/gex44_env_preflight.py --env-root /home/kobii/a7-env` | the preflight's auth line reads READY |
| 15 | B | [B]#7 "PRG: after the" | After the deploy and the re-login, save the preflight JSON and a7's next launch row as evidence/B-prg.md | `python3 /home/kobii/missions/incremental-cognition/.claude/worktrees/ic-run/tools/gex44_env_preflight.py --env-root /home/kobii/a7-env --json` | pillar B IMPLEMENTED_AND_VERIFIED: gate python3 tools/test_gex44_env_preflight.py + evidence/B-prg.md; not the arm debt |
| 16 | B | [B]#3 "the GEX44 main-plane" | Upgrade the GEX44 system node from v18.19.1 to the vendored engine range (^22.23.2 or ^24.14.0) | none -- an Owner action on the GEX44 system node, never bypassed | the node-range cause of the main-plane reds V-MC-PLAN-FACTS-REFUSES-OVERLAP, V-HPKT-ATTACH and V-HPKT-PARTIAL-REFUSED (not the V-G23-* card-byte reds) |
| 17 | B | [B]#4 "decisions for owners." | Decide the three open points: a7's hooks resolving into a5's tree, the installer's missing hook-script copy, the Windows-only bare-git trap rule | none -- three Owner decisions written in the item | the three decisions the item lists are answered (the item names no gate) |
| 18 | B | [B]#5 "NOTE (merge strategy," ; UAT 02#4 | Merge the branch preserving 60e7947d (no squash, no rebase) or re-point PP_COMMIT_FLOOR in the same merge | none -- an Owner decision on the merge strategy (review WR-08) | declared-plane envs stop reading pp_install_stale |
| 19 | B | [B]#6 "DEBT, shrink-only, NOT" | Before every arm on GEX44 run both preflights and proceed only on exit 0 (shrink-only debt) | `python3 /home/kobii/missions/incremental-cognition/.claude/worktrees/ic-run/tools/gex44_env_preflight.py --env-root /home/kobii/a7-env` ; `python3 /home/kobii/missions/incremental-cognition/.claude/worktrees/ic-run/tools/gex44_env_preflight.py --env-root /home/kobii/a5-env` | nothing here: only a later change calling mission_launch_gate.refusal on the arm path, proven by a red-first test, closes the debt |
| 20 | B (phase 2 UAT) | UAT 02#3 | Agree or amend the WR-04 / WR-06 / WR-07 operator-facing semantics (02-REVIEW-FIX.md) | `/gsd-verify-work 2` | phase 2 UAT test 3 |
| 21 | H (phase 3 UAT) | UAT 03#2 | If the KME-L H share also clears 3 %, decide the follow-up for H's predicted FALSIFIED_OR_REJECTED disposition | `/gsd-verify-work 3` | phase 3 UAT test 2 |
| 22 | D-I (phase 3 UAT) | UAT 03#4 | Read tools/test_kme_pillars.py in full (03-REVIEW only skimmed it) | `/gsd-verify-work 3` | phase 3 UAT test 4 |
| 23 | K (phase 4 UAT) | UAT 04#2 | Accept or amend the review-fix policies WR-01 / WR-02 / WR-03 (layer_absent exit 2, uncorrelated hook element unattributed, uncompared tokens axis exit 2 unless --chars-only) | `/gsd-verify-work 4` | phase 4 UAT test 2 |
| 24 | K (phase 4 UAT) | UAT 04#3 | Confirm the three IC-K judgment-tier prohibitions held (verifier verdicts are non-authoritative) | `/gsd-verify-work 4` | phase 4 UAT test 3 |
| 25 | L (phase 5 UAT) | UAT 05#1 | The two laptop [L] items, as one pending phase 5 check: the KME-L ranking run (row 10) and the Owner's live-quota decision file (row 11) | `/gsd-verify-work 5` | phase 5 UAT test 1 |
| 26 | L (phase 5 UAT) | UAT 05#2 | Accept or amend the Phase 5 review-fix decisions: the R4 identity rule (CR-01, WR-01, WR-02), the R3-L front matter cross-check (WR-03), terminal only at rollover growth 100000 (WR-04), per-thread retries and rereads (WR-06), dense ranks for equal figures (IN-01) | `/gsd-verify-work 5` | phase 5 UAT test 2 |
| 27 | L (phase 5 UAT) | UAT 05#3 | Confirm the IC-L judgment-tier prohibitions held (verifier verdicts are non-authoritative) | `/gsd-verify-work 5` | phase 5 UAT test 3 |
| 28 | A | [A]#2 "WHERE to arm" | Say where the mission is armed (12/24h): on the laptop (RAM swings 0.6-8 GB; arming waits for pillar A and at least 4 GB free) or in the GEX44 own clone, or that it stays in the interactive pane | none -- an Owner decision on where to arm, written by the Owner (see the item) | the open "needs Owner go on WHERE" line of STATE.md Session Continuity; no arm happens before it |

## Laptop code sync (do this first for [D]..[I], [K] and [L])

One step brings every program-owned tool file the laptop-plane items need, at the fetched branch tip. It replaces the
Phase 3 cherry-pick list and the `[K]` cherry-pick / tree-state steps (see the `Phase 5 correction` paragraphs under
those two headers). It moves no live-loaded file: `[C]` keeps its own procedure (at least 4 GB free), and `[A]` and
`[B]` are unchanged.

Expects: the laptop PP checkout `C:\Users\User\.claude\skills\claude-power-pack`, Python is `python`, every line run
from its root; only the ssh host alias may differ (the repository path and branch are exact). Order and stop
conditions: fetch; print the fetched tip with `git rev-parse FETCH_HEAD` and record it; `git merge-base --is-ancestor`
must exit 0 (the fetched tip holds the pinned phase-5 commit; any other exit: stop); the status line must print
nothing (if it prints anything, stop: the checkout below would overwrite those local edits, and deciding what to keep
is yours); then the checkout.

    git fetch kobii@kobicraft-gex44:/home/kobii/missions/incremental-cognition mission/incremental-cognition-run
    git rev-parse FETCH_HEAD
    git merge-base --is-ancestor f3cdc79b1b961075e5a7bbd451be6569faf6c405 FETCH_HEAD
    git status --short -- "wiki/tools/kme_*.py" "tools/test_kme_*.py" tools/test_incremental_cognition_program.py tools/floor_regression_gate.py tools/test_floor_regression_gate.py vault/programs/incremental-cognition/floor/reference-gex44.json vault/programs/incremental-cognition/measurements vault/programs/incremental-cognition/owner-bundle.md vault/programs/incremental-cognition/FROZEN_AT
    git checkout FETCH_HEAD -- "wiki/tools/kme_*.py" "tools/test_kme_*.py" tools/test_incremental_cognition_program.py tools/floor_regression_gate.py tools/test_floor_regression_gate.py vault/programs/incremental-cognition/floor/reference-gex44.json vault/programs/incremental-cognition/measurements vault/programs/incremental-cognition/owner-bundle.md vault/programs/incremental-cognition/FROZEN_AT

Then commit those paths only, by pathspec: write a message file first, then `git commit -F` that file restricted to
the same paths as the checkout line. Then the four suites, in this order:

    python tools/test_kme_pillars.py
    python tools/test_kme_replay.py
    python tools/test_floor_regression_gate.py
    python tools/test_incremental_cognition_program.py --selftest

Expected, not measured on the laptop: each exits 0; GEX44 `-REAL` gates print SKIP there and POSIX-mode gates SKIP on
Windows (a SKIP is never a PASS). Proven on GEX44 only, by replaying these lines in a scratch clone at the P0 freeze
`18e928af` with the fetch URL replaced by the local path (fetched tip equal to the branch tip, ancestor check exit 0,
status output empty, checkout and commit exit 0), the four suites each exit 0 with:

    KMEP_PASS=89/89  threshold=89/89  skipped=0  inconclusive=0
    KMER_PASS=39/39  threshold=39/39  skipped=0  inconclusive=0
    FLOOR_PASS=67/67  threshold=67/67  skipped=0  inconclusive=0
    ICP_SELFTEST=PASS

Phase 5 update (plan 05-04): the block above was measured before the `## Summary (every Owner item, phases 1-5)` table
existed. With the table and its two coverage gates in the bundle, the replay at `18e928af` prints `KMER_PASS=40/40` with
`skipped=1` for the second suite (V-KMER-BUNDLE-SUMMARY-UAT prints SKIP there: the phase files it cites do not exist at
the freeze; a SKIP is never a PASS) and the GEX44 worktree prints `KMER_PASS=41/41  skipped=0`. The other three lines are
unchanged. On the laptop the same SKIP is expected, for the same reason (not measured there).

Phase 5 correction (review fixes, gates 42-45): the counts in the two paragraphs above are stale. The replay at `18e928af` now
prints `KMER_PASS=44/44  threshold=44/44  skipped=1` for the second suite (the SKIP is V-KMER-BUNDLE-SUMMARY-UAT, as before; a
SKIP is never a PASS), measured in a scratch clone under /tmp with the fetch URL replaced by the local repository path, and the
GEX44 worktree prints `KMER_PASS=45/45  threshold=45/45  skipped=0`. The other three lines (`KMEP_PASS=89/89`,
`FLOOR_PASS=67/67`, `ICP_SELFTEST=PASS`) are unchanged, and every exit code is 0. On the laptop expect the same 44/44 with one
SKIP, not measured there.

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

**Phase 5 correction (supersedes the cherry-pick list below):** replaying that list literally in a scratch clone at
the P0 freeze `18e928af` on GEX44 (the `FROZEN_AT` pointer pick, then the fourteen picks; all applied) gave an
instrument whose `wiki/tools/kme_pillars.py` holds `frozen_source` 0 times. The fourteen picks predate the eight
phase-3 review fixes `d241bb5e` .. `326da74c`, and `frozen_source` was added by `a4d09a24` (WR-07). The program
done-gate's R3 (WR-07) refuses a terminal claim from a file without it (selftest
`V-ICP-R3-MUT-no-frozen-source`), so no KME-L file made along that list could close D..I. `## Laptop code sync` at the
top of this file replaces the picks; the population proof and the `[D]`..`[I]` commands below stay as written.

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

**Phase 5 correction:** the `[K]` cherry-pick and tree-state steps below are covered by `## Laptop code sync` (its
paths include the three tree-state files and the `[K]` tool files). Replaying the old path literally in a scratch clone
at the P0 freeze `18e928af` (the eight `[K]` picks, then the `ef336ec7` tree-state checkout of the three paths) left
this bundle file absent there, and `python tools/test_floor_regression_gate.py` exited 1 with `FAIL
V-FLOOR-BUNDLE-ARGV-PARSES owner bundle missing` (`FLOOR_PASS=66/67`): on that path the fixture suite cannot exit 0,
because its own parse gate reads this bundle and that path does not bring it. The fixture suite, the seeded control,
the reference write, its commit and the PRG below stay as written.

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

  Then the phase 4 code-review fixes (seven commits, CR-01 `19792a95` .. IN-02 `ef336ec7`). One of them also edits this
  bundle and `evidence/K.md`, which the laptop does not need, so they are taken as a tree state, not cherry-picked; the
  three paths below are exactly the files they change that the laptop uses (the reference is regenerated, the gate now
  refuses an unparseable window line, a wholly absent layer and an uncompared tokens axis, and `--chars-only` exists):

      git checkout ef336ec7d81c965e1e2543abb63bdb33c1179501 -- tools/floor_regression_gate.py tools/test_floor_regression_gate.py vault/programs/incremental-cognition/floor/reference-gex44.json
      git commit -F <msgfile you wrote first> -- tools/floor_regression_gate.py tools/test_floor_regression_gate.py vault/programs/incremental-cognition/floor/reference-gex44.json

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

## Phase 5 -- offline replay ranking and the live-experiment decision (laptop plane)

Status of every command below: **NOT RUNNABLE HERE** (laptop paths; the KME-L corpus is not on GEX44). They are
proven only to parse with the replay's own argument parser (gate `V-KMER-BUNDLE-ARGV-PARSES`,
`python3 tools/test_kme_replay.py`); nothing below has been run on the laptop.

- **[L]** KME-L offline replay ranking (laptop plane). Expects: the `## Laptop code sync` step at the top of this
  file done with its four suites at exit 0 (that section is added by the same phase), and the Phase 3 population
  proof printed `"population_match": "exact"`; its roots are used here too. **Action:**

      python wiki/tools/kme_replay.py rank --denominator KME-L --until auto --expand --root C:\Users\User\.claude\projects

  It writes `L-KME-L-<date>.md` under `vault/programs/incremental-cognition/measurements/`, naming its denominator,
  its plane and its exact `command:`. Exit 0 = every candidate measured. Exit 3 = a candidate is UNMEASURED with its
  reason in the file (that is a result: commit it). Exit 2 = a refusal, nothing written. Commit only that file, by
  pathspec, as the Phase 3 section describes (`git add --` the printed file, then `git commit -F <msgfile> --` the
  same path). What it gives: the frozen rule's ranking of the three live experiments (late rollover, identical
  rereads, unchanged-precondition retries) on KME-L, each figure an UPPER BOUND and never a realized saving, with its
  reading against 3 %. The KME-G reading from the GEX44 run is a smoke, to be quoted only as "smoke, plane gex44,
  never terminal" (`vault/programs/incremental-cognition/measurements/L-KME-G-2026-10-04.md`): on it only late rollover
  could clear 3 % on its bound, as an optimistic ceiling; it says nothing about KME-L, and KME-L decides. Pillar L
  stays open until the KME-L file lands; ledger state.L is not written by this mission run; L takes the terminal its
  frozen rule gives at close time, citing this file and, if the Owner decided on live sessions, the decision file of
  the next item.
- **[L]** decision on live champion / challenger sessions (spends quota; Owner only). Expects: the KME-L ranking
  file above (decide on KME-L, never on the KME-G smoke). This mission never starts a live session and never takes
  this decision. A candidate whose upper bound reads `>= 3 %` is the only kind a live experiment could make material;
  one reading `< 3 %` cannot clear materiality even if fully realized. **Action:** write the decision in your own
  words (approve live sessions for the named candidates with a session count, or decline) as
  `vault/programs/incremental-cognition/evidence/L-owner-decision.md`, naming `[L]` in it, and commit it by
  pathspec. That file, never this bundle, is the `owner_decision` evidence (the program done-gate refuses the bundle
  as a decision); with it L can close AUTHORIZATION_BOUND. The design of an approved live run is a later step, not
  specified here.
- **[A]** WHERE to arm the mission (Owner decision; this mission never arms itself). `gsd_mission.py arm
  --workstream incremental-cognition` (12/24h) has never been run: STATE.md Session Continuity ends with "arm ... needs
  Owner go on WHERE", and the plan says arming waits for pillar A and at least 4 GB free, until then phases run in the
  interactive pane. Expects: you know which of two places you want. The laptop (local RAM swings 0.6-8 GB, so the
  4 GB floor is not a given) or the GEX44 own clone `~/missions/incremental-cognition` (where this run already
  executes). On a declared plane the arm path is still ungated (see the [B] debt item above), so run both preflights
  first and arm only on exit 0. **Action:** tell the orchestrator one of: arm on the laptop, arm on GEX44, or keep the
  interactive pane; the mission records the answer, it does not choose. What closes: that answer exists in your own
  words (the mission then removes the STATE line). This item runs no command and nothing is armed by writing it.
