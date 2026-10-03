---
phase: 02-persistent-failures-and-remote-integrity
fixed_at: 2026-10-03T00:00:00Z
review_path: .planning/workstreams/incremental-cognition/phases/02-persistent-failures-and-remote-integrity/02-REVIEW.md
iteration: 1
findings_in_scope: 8
fixed: 7
skipped: 1
status: partial
---

# Phase 2: Code Review Fix Report

Verification ran in the main checkout of the ic-run worktree (workflow.use_worktrees=false), not an isolated temp worktree.

**Summary:**
- Findings in scope: 8 (WR-01..WR-08)
- Fixed: 7 (WR-01..WR-07)
- Skipped: 1 (WR-08, by instruction)

## Fixed Issues

### WR-01: deploy guard never checks env.sh HOME is inside the env root

**Files modified:** `tools/gex44_env_deploy.py`, `tools/test_gex44_env_deploy.py`
**Commit:** 55319136
**Applied fix:** new `_env_home_problem(root, env)`; `plan_deploy` refuses with EXIT_GUARD (3) unless the resolved env.sh HOME is strictly inside the root and is neither the process HOME nor an ancestor of it. Apply re-plans under the lock, so it inherits the refusal.
**Gate:** `V-DEPLOY-ENV-HOME-OUTSIDE-ROOT-REFUSED` (scratch "victim" env stands in for the live HOME; also a plan against env.sh exporting the process HOME). Mutant M7 added to the drill.
**RED (before fix):** `FAIL V-DEPLOY-ENV-HOME-OUTSIDE-ROOT-REFUSED: apply=0 plan=None victim_head=7ac2870e victim_unchanged=False ...` / `DEPLOY_PASS=16/17`
**GREEN (after fix):** `PASS V-DEPLOY-ENV-HOME-OUTSIDE-ROOT-REFUSED: apply=3 plan=3 victim_head=01199995 victim_unchanged=True own_home_refusal=3` / `DEPLOY_PASS=17/17`

### WR-02: deploy exits 0 / "APPLIED" when the post-deploy pp_install or hooks check was UNMEASURABLE

**Files modified:** `tools/gex44_env_deploy.py`, `tools/test_gex44_env_deploy.py`
**Commit:** d301d49b
**Applied fix:** new `_unrepaired(after)`: measured `pp_install_stale`/`hooks_broken` reasons OR a `pp_install`/`hooks` check that is not READY in the final preflight. `_finish` maps any of these to the existing `EXIT_STILL_STALE` (7). Rendered state becomes `INCOMPLETE`.
**Gate:** `V-DEPLOY-UNMEASURED-AFTER-IS-CODE-7` (forces the final hooks probe, then the final pp_install probe, to UNMEASURABLE; unmutated control must still reach 0). Mutant M8 added.
**RED:** `FAIL V-DEPLOY-UNMEASURED-AFTER-IS-CODE-7: (code, rendered_APPLIED, rendered_code7)={'hooks': (0, True, False), 'pp_install': (0, True, False)} control_code=0` / `DEPLOY_PASS=17/18`
**GREEN:** `PASS ...={'hooks': (7, False, True), 'pp_install': (7, False, True)} control_code=0` / `DEPLOY_PASS=18/18`

### WR-03: relative --source-repo resolved against the install directory at fetch time

**Files modified:** `tools/gex44_env_deploy.py`, `tools/test_gex44_env_deploy.py`
**Commit:** e764c62e
**Applied fix:** `plan_deploy` resolves `Path(source_repo).expanduser().resolve()` once, stores it in `plan["source_repo"]`; `_apply_locked` reads the resolved path back from the fresh plan.
**Gate:** `V-DEPLOY-RELATIVE-SOURCE-REPO` (CLI run with cwd=repo and `--source-repo .`, standalone-history env so the fetch must succeed).
**RED:** `FAIL V-DEPLOY-RELATIVE-SOURCE-REPO: rc=8 head==target=False plan_source_repo=. failed_steps=[('fetch', 'fatal: git upload-pack: not our ref ...')]` / `DEPLOY_PASS=18/19` (this is the wrong-repo shape the review described: git found a repository at `.` under the install)
**GREEN:** `PASS V-DEPLOY-RELATIVE-SOURCE-REPO: rc=0 head==target=True plan_source_repo=<abs repo path> failed_steps=[]` / `DEPLOY_PASS=19/19`

### WR-04: lapsed access token with refresh token but unknown refresh expiry judged usable

**Files modified:** `tools/provider_breaker.py`, `tools/test_persistent_failure_park.py`, `tools/test_gex44_env_preflight.py`
**Commit:** 7259ccb0
**Status:** fixed: requires human verification (logic change in a predicate)
**Applied fix:** `credentials_expired` returns `None` when the access token lapsed, a refresh token is present, and `refresh_expires_at` is None (absent or non-numeric). `check_auth` then reports UNMEASURABLE (no refusal) and `auth_released` keeps the AUTH park. The old gate `V-PFP-CRED-LAPSED-REFRESHABLE` encoded the bug as intended behaviour (asserted `False` with no refresh expiry); it now pins the only lapsed case that reads usable: a known future refresh expiry.
**Gates:** `V-PFP-CRED-LAPSED-REFRESH-EXPIRY-UNKNOWN` (no key, non-numeric value, and `auth_released` with a rewrite newer than the refusal), `V-ENVPF-AUTH-LAPSED-REFRESH-EXPIRY-UNKNOWN`.
**RED:** `FAIL V-PFP-CRED-LAPSED-REFRESH-EXPIRY-UNKNOWN: no-key expired=False non-numeric expired=False auth_released='credentials rewritten ... access token usable'` / `PFP_PASS=24/25`; `FAIL V-ENVPF-AUTH-LAPSED-REFRESH-EXPIRY-UNKNOWN: state=READY ... refreshable until None` / `ENVPF_PASS=55/56`
**GREEN:** `PFP_PASS=25/25`, `ENVPF_PASS=56/56`, `BREAKER_PASS=18/18`, `LG_PASS=19/19`

### WR-05: expired OAuth file + exported API-key variable gave a measured NOT_READY

**Files modified:** `tools/gex44_env_preflight.py`, `tools/test_gex44_env_preflight.py`
**Commit:** a1c593f2
**Applied fix:** `via` (exported auth variable names) is computed once, before the readable/missing split; an expired credentials file with `via` non-empty returns UNMEASURABLE naming the variable (value never read), consistent with the missing-file branch. Without an exported name the expired file still returns NOT_READY `auth_expired`.
**Gate:** `V-ENVPF-AUTH-EXPIRED-WITH-EXPORTED-KEY-UNMEASURABLE` (expiresAt 0 and lapsed-without-refresh x the three variable names, plus a no-variable control that must still refuse; asserts the canary value never appears in the result).
**RED:** `FAIL V-ENVPF-AUTH-EXPIRED-WITH-EXPORTED-KEY-UNMEASURABLE: expiresAt0/ANTHROPIC_API_KEY=NOT_READY; ...` / `ENVPF_PASS=56/57`
**GREEN:** `ENVPF_PASS=57/57`, `LG_PASS=19/19`, `DEPLOY_PASS=19/19`

### WR-06: provider_breaker status/clear wrong or inert for a held renewal successor

**Files modified:** `tools/provider_breaker.py`, `tools/test_mission_launch_gate.py`
**Commit:** c6dd2087
**Status:** fixed: requires human verification (operator-facing semantics)
**Applied fix:** `hold_for(rec, now, cleared_at=None)`; `lineage_hold` passes `max(last_clear(successor), last_clear(predecessor))` so a `clear --mission <successor>` is honoured; `_cli status` uses `hold_for(rec, now) or lineage_hold(rec, now)` so a held successor reports the inherited hold (with `inherited_from`) instead of `null`. `clear` itself is unchanged.
**Gate:** `V-LG-LINEAGE-OPERATOR-SURFACES` (CLI driven through `pb._cli`; control: clearing an unrelated mission releases nothing).
**RED:** `FAIL V-LG-LINEAGE-OPERATOR-SURFACES: held_before=True status_shows_hold=False inherited_from=None other_clear_releases=False clear_rc=0 held_after_clear=True gate={'refuse': True, ...}` / `LG_PASS=19/20`
**GREEN:** `LG_PASS=20/20`, `BREAKER_PASS=18/18`, `PFP_PASS=25/25`

### WR-07: breaker-less auth park released by any credentials rewrite

**Files modified:** `tools/gsd_mission.py` (minimal: one helper + one extra condition), `tools/test_persistent_failure_park.py`
**Commit:** 9a267502
**Status:** fixed: requires human verification (logic change in the degraded release rule)
**Applied fix:** new `_credentials_usable_without_breaker(now)` (reads expiry keys and presence of `refreshToken` only; False on unreadable / expiresAt<=0 / lapsed without refresh token / unknown refresh expiry). `_auth_hold_without_breaker` releases only when mtime > evidence AND that is True; otherwise the park stands. A missing/unstat-able file keeps the existing "refusal stands" behaviour.
**Gates:** `V-PFP-FALLBACK-DEAD-REWRITE-KEEPS-PARK` (expiresAt 0 / lapsed with unknown refresh expiry / lapsed no refresh / no expiresAt), `V-PFP-FALLBACK-UNREADABLE-REWRITE-KEEPS-PARK`, `V-PFP-FALLBACK-CRED-PARITY` (degraded reader == `credentials_expired(...) is False` over 7 shapes). The existing `V-PFP-FALLBACK-RELEASES-ON-RELOGIN` stays green (usable re-login still releases). Drill mutant M6 added (killed).
**RED:** `FAIL V-PFP-FALLBACK-DEAD-REWRITE-KEEPS-PARK: launches by rewrite shape={'expiresAt 0': 1, 'lapsed, refresh expiry unknown': 1, 'lapsed, no refresh token': 1, 'no expiresAt': 1}`; `FAIL V-PFP-FALLBACK-UNREADABLE-REWRITE-KEEPS-PARK: launches=1`; `FAIL V-PFP-FALLBACK-CRED-PARITY ... no attribute '_credentials_usable_without_breaker'` / `PFP_PASS=25/28`
**GREEN:** `PFP_PASS=28/28`; drill `DRILL killed=6/6`

## Skipped Issues

### WR-08: PP_COMMIT_FLOOR is an exact commit hash from an unmerged branch

**File:** `tools/gex44_env_preflight.py:58`
**Reason:** merge-strategy decision reserved to Owner; recorded as owner-bundle note. No code changed. One line appended under the `[B]` lines of `vault/programs/incremental-cognition/owner-bundle.md` (commit 4d2e1411): `PP_COMMIT_FLOOR=60e7947d` exists only on `mission/incremental-cognition-run`, so merge preserving that commit (no squash/rebase) or re-point the floor in the same merge.
**Original issue:** a squash or rebase merge makes the floor hash absent from main-descended history, so every declared-plane env reports `pp_install_stale` and the deploy ends in code 7.

## Verification (run in the main checkout of the ic-run worktree, workflow.use_worktrees=false; no isolated temp worktree was created)

| Suite | Result |
|---|---|
| test_gex44_env_deploy | DEPLOY_PASS=19/19 (was 16/16); --drill: control 19/19, killed=8/8, clean after |
| test_gex44_env_preflight | ENVPF_PASS=57/57 (was 55/55); --drill: control 57/57, killed=6/6, clean after |
| test_mission_launch_gate | LG_PASS=20/20 (was 19/19); --drill: control 20/20, killed=6/6, clean after |
| test_provider_breaker | BREAKER_PASS=18/18 (unchanged) |
| test_persistent_failure_park | PFP_PASS=28/28 (was 24/24); --drill: control 28/28, killed=6/6, clean after |
| test_gsd_mission | MC_PASS=212/213, the one known red V-MC-PLAN-FACTS-REFUSES-OVERLAP (unchanged baseline) |
| test_gsd_epoch | EPOCH_PASS=82/82 |
| test_gsd_mission_cwd_align | MCA_PASS=16/16 |

The deploy was never run with `--apply` against the real ~/.claude, ~/a5-env or ~/a7-env; every apply ran against scratch envs under a temp root (V-DEPLOY-REAL-UNTOUCHED stays green).

Notes for the Owner:
- WR-04 changed what an existing gate asserted: `V-PFP-CRED-LAPSED-REFRESHABLE` used to pin "lapsed + refresh token, no refresh expiry -> not expired" (the defect itself). It now pins the known-future-refresh-expiry case, and the unknown-expiry case is its own gate. Consequence on a real env: a lapsed access token whose credentials file has no `refreshTokenExpiresAt` reads auth UNMEASURABLE (no refusal) instead of READY.
- WR-02 now returns code 7 whenever pp_install or hooks is not READY after the deploy, including a measured NOT_READY for a reason other than staleness/broken hooks.
- IN-01..IN-04 were out of scope (fix_scope critical_warning, bound WR-01..WR-07) and are untouched.

---

_Fixed: 2026-10-03_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
