---
phase: 02-persistent-failures-and-remote-integrity
reviewed: 2026-10-03T00:00:00Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - tools/gex44_env_deploy.py
  - tools/gex44_env_preflight.py
  - tools/gsd_mission.py
  - tools/mission_launch_gate.py
  - tools/provider_breaker.py
  - tools/test_gex44_env_deploy.py
  - tools/test_gex44_env_preflight.py
  - tools/test_mission_launch_gate.py
  - tools/test_persistent_failure_park.py
findings:
  critical: 0
  warning: 8
  info: 4
  total: 12
status: issues_found
---

# Phase 2: Code Review Report

**Reviewed:** 2026-10-03
**Depth:** standard
**Files Reviewed:** 9 (gsd_mission.py only for the hunks since 34d08aa9)
**Status:** issues_found

## Summary

The fail-open/fail-closed core is sound. Only a measured NOT_READY refuses, an unknown verdict string or a raising preflight becomes UNMEASURABLE, and the aggregate ranks NOT_READY over UNMEASURABLE on purpose and says so. The deploy takes the same flock file the cron holds, re-plans under the lock, refuses dirty trees and non-ancestors, and writes backups before each mutation. The lineage walk is bounded and cycle-safe. The four new test files pass here (preflight 55/55, launch gate 19/19, park 24/24), and I ran the preflight read-only against a5 and a7 (a7 reports auth_expired and pp_install_stale, which matches the measured evidence).

No BLOCKER was found. The warnings fall into three groups, each with a reproducible scenario:

- **Unknown reads as usable.** A credentials file with a refresh token but no `refreshTokenExpiresAt` is treated as healthy, both for READY and for releasing a quarantine.
- **The deploy trusts less than it claims.** It can be pointed at the real HOME through env.sh, it resolves a relative source repo against the wrong directory, and it can exit 0 when the repaired checks were never measured.
- **Operator-facing breaker commands do not match the gate.** `status` and `clear` on a held renewal successor are wrong or inert.

## Warnings

### WR-01: deploy guard never checks that env.sh's HOME is inside the env root, so `--apply` can retarget the user's real ~/.claude

**File:** `tools/gex44_env_deploy.py:85-102` (consumer at `:131-137`, `:347-349`)
**Issue:** `_guard` judges only the `--env-root` path. It refuses `/`, the process HOME and its ancestors, and requires `env.sh` plus `home/`. The install path and the HOME used for the installer come from `ep.env_from_root(root)`, which takes `HOME` from the `export HOME=` line in env.sh. Nothing requires that value to be under `root`.

Scenario: an env root such as `~/main-env/` with `env.sh` containing `export HOME=/home/kobii` (a hand-made "main" env) passes the guard. The deploy then:
- checks out a new commit in `/home/kobii/.claude/skills/claude-power-pack`;
- runs `install_global_core.py` with `HOME=/home/kobii`, which overwrites agents and commands (backed up) and re-registers hooks in the live `~/.claude/settings.json`;
- appends a line to env.sh.

The module docstring says the deploy "never destroys something it was not authorized to destroy", and V-DEPLOY-REFUSES-HOME only drives the process-HOME case. HR-001 and the phase context both put the live `~/.claude/**` off limits.

**Fix:** after `env_from_root`, refuse with `EXIT_GUARD` unless the resolved env HOME is strictly inside `root` and is neither the process HOME nor an ancestor of it:
```python
env_home = Path(env["home"]).resolve()
if root not in env_home.parents or env_home == Path.home().resolve():
    return _refuse(plan, EXIT_GUARD, f"env.sh HOME {env_home} is outside the env root {root}")
```
Add a gate that builds such an env.sh and expects code 3 with nothing changed.

### WR-02: deploy exits 0 / "APPLIED" when the post-deploy pp_install or hooks check was UNMEASURABLE

**File:** `tools/gex44_env_deploy.py:372-374`
**Issue:** `still = [r for r in ("pp_install_stale", "hooks_broken") if r in after["reasons"]]` looks only at measured NOT_READY reasons. The docstring of `_finish` and the repair contract say success means the repaired conditions are gone. If the final `ep.run` leaves `pp_install` or `hooks` UNMEASURABLE (a probe timeout or budget exhaustion in `check_hooks`, `git rev-parse` failing in `check_pp_install`, or an unreadable settings.json), no reason is emitted. `code` stays `EXIT_OK`, the CLI prints `DEPLOY=APPLIED ... code=0`, and the log line records code 0. That is exactly "UNMEASURABLE reads as READY" at the deploy's own verdict. No gate covers code 7 or an unmeasured after-state.

**Fix:** treat a repaired check that is not READY as incomplete:
```python
not_ready = [c["check"] for c in after["checks"]
             if c["check"] in ("pp_install", "hooks") and c["state"] != ep.READY]
if res["code"] == EXIT_OK and (still or not_ready):
    res["code"] = EXIT_STILL_STALE
```
Add a drill that forces the final hooks probe to time out and expects code 7.

### WR-03: a relative `--source-repo` is resolved against the install directory at fetch time

**File:** `tools/gex44_env_deploy.py:154`, `:305`, `:321`
**Issue:** `src = Path(source_repo)` is never resolved. The plan validates it relative to the caller's cwd (`src.is_dir()`, `_run(..., src)` uses `cwd=str(src)`). The apply step then runs `git fetch --no-tags str(src) target` with `cwd=install`. With `--source-repo ../PP` or `--source-repo .` the fetch looks in a different place than the plan validated, and could even match an unrelated repository that happens to sit at that relative path under the install. Typically it fails with code 8 after the plan reported success; the wrong-repo case needs a coincidence but is not excluded.

**Fix:** `src = Path(source_repo).expanduser().resolve()` in `plan_deploy` and in `_apply_locked`, and put the resolved path in the plan.

### WR-04: a lapsed access token with a refresh token but no `refreshTokenExpiresAt` is judged usable, which reads UNMEASURABLE as READY and releases a quarantine

**File:** `tools/provider_breaker.py:177-180` (consumers `:199` and `tools/gex44_env_preflight.py:169-173`)
**Issue:** `credentials_expired` ends with `return bool(rexp is not None and rexp <= now)`. When the access token has lapsed, a `refreshToken` key is present, and `refreshTokenExpiresAt` is absent or non-numeric, the refresh token's validity is unknown, yet the function returns `False` (usable) instead of `None` (cannot judge). I reproduced this:
- `auth_released(...)` returned "credentials rewritten ... access token usable";
- `check_auth` returned READY "refreshable until None".

Consequences:
- `auth_released`'s own contract ("unmeasurable keeps the park") is broken, and an AUTH quarantine is released by a file that is not known to be usable.
- The preflight reports READY on an unmeasured login.
- The release path is bounded: a failed relaunch re-parks on the next refusal. Even so, it is the opposite of the stated fail direction.

**Fix:** return `None` when the lapsed token has a refresh token but `rexp is None`:
```python
if rexp is None:
    return None
return rexp <= now
```
`check_auth` then reports UNMEASURABLE and `auth_released` keeps the park. Add a V-PFP-CRED case for it.

### WR-05: `check_auth` reports a measured NOT_READY auth_expired from an expired OAuth file even when an API-key variable is exported

**File:** `tools/gex44_env_preflight.py:148-168`
**Issue:** `AUTH_ENV_NAMES` is consulted only when the credentials file is missing (`:154-159`). If the file is readable with `expiresAt: 0` (or an expired token without a refresh token) and `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN` or `CLAUDE_CODE_OAUTH_TOKEN` is exported, the check still returns NOT_READY/`auth_expired` (reproduced). A worker in an env that authenticates through the exported key would not hit the OAuth path, so this is a false measured refusal. The gate then blocks every launch, and the deploy's owner action tells the Owner to re-login for a problem that does not exist. The missing-file branch already treats the exported name as "a login may exist that this cannot judge", so the two branches are inconsistent.

**Fix:** when an expired or invalid credentials file coexists with an exported auth variable, return UNMEASURABLE ("OAuth file expired; <VAR> exported, so which login the CLI uses cannot be judged here"). Only refuse when no such name is exported.

### WR-06: `provider_breaker.py status` and `clear` are wrong or inert for a held renewal successor

**File:** `tools/provider_breaker.py:249-253` (`hold_for`), `:270-305` (`lineage_hold`), `:317-326` (`_cli`)
**Issue:** the gate holds a PREPARED renewal successor by calling `hold_for(pred)`, so the ledger and `decide` are keyed by the predecessor's mission id. The operator surfaces still use the successor's id.
- **`clear --mission <successor>`** appends `provider_cleared` to the successor's ledger and prints `{"cleared": true}`. `lineage_hold` never reads the successor's clears, and `decide` reads `last_clear(pred_id)`. The hold stays and the next pass re-holds. The `held` text names `inherited_from`, but the id the supervisor row and logs show is the successor's.
- **`status --mission <successor>`** calls `hold_for(rec)`, which returns `None` for a record with no owner. It prints `"hold": null` while the supervisor is refusing the launch.

**Fix:** in `lineage_hold`, also compute `cleared_at = max(last_clear(rec_id), last_clear(pred_id))` and pass it into `decide`. Give `_cli status` a lineage fallback: `hold_for(rec, now) or lineage_hold(rec, now)`. At minimum, make `clear` print the id it actually cleared and refuse ids whose record has no owner.

### WR-07: the breaker-less auth park is released by any credentials rewrite, including one that leaves the login dead

**File:** `tools/gsd_mission.py:1947-1953`
**Issue:** in `_auth_hold_without_breaker`, `credentials mtime > evidence_at` returns `None` (released) without reading the file. The breaker path additionally requires `credentials_expired(...) is False`, so a rewrite that leaves `expiresAt: 0` keeps the park there. This degraded mode exists for installs where `provider_breaker` cannot be imported, so any process that touches `.credentials.json` after the refusal (a failed `/login` attempt, or a CLI that rewrites the file when a refresh fails) un-parks the mission. Relaunches then resume at one per pass. That is the 137-relaunch shape this fallback was added to stop. V-PFP-FALLBACK-RELEASES-ON-RELOGIN only covers a usable re-login. The comment says "this path never opens the file" and rests on a design choice, but the choice reopens the failure the plan targets.

**Fix:** in the degraded path, read `expiresAt` itself (a single key, never a token) and release only when it parses as `> now` (or `> 0`, and a refresh token is present). Otherwise keep the park. Add a degraded-mode gate with a rewritten `expiresAt: 0` file that expects zero launches.

### WR-08: `PP_COMMIT_FLOOR` is an exact commit hash from an unmerged branch, so a squash or rebase merge turns every declared-plane env NOT_READY with no way to heal

**File:** `tools/gex44_env_preflight.py:58`
**Issue:** `check_pp_install` requires the 40-hex floor to exist in the install's history. `60e7947d` exists only on `mission/incremental-cognition-run` (`git branch --contains` lists nothing else). If the work reaches main by a squash or rebase merge, which is the default for a PR flow, the hash is not in any main-descended history. Every env the deploy updates to main would then report `pp_install_stale`, the gate would refuse every launch on a declared plane, and the deploy would end in code 7 forever because it cannot repair a missing floor. The failure is silent until after the Owner's fetch and deploy, and it is fleet-wide.

**Fix:** pin the floor to something history-rewrite-proof. Options:
- check for the presence of the required files plus a version marker (for example a `PP_RULES_VERSION` constant read from `tools/mission_launch_gate.py`);
- or keep the hash check but make the floor-raise step part of the merge checklist and add a gate that fails when the floor is not an ancestor of the branch that will be merged.

## Info

### IN-01: repeated ledger rows every pass while a refusal persists

**File:** `tools/mission_launch_gate.py:71-73`, `:92-93`; `tools/provider_breaker.py:263-266`
**Issue:** `_lineage` appends `provider_held` and `_env` appends `launch_preflight_refused` on every supervise pass (every 5 minutes) for as long as the refusal stands. `hold_for` appends `provider_released` on every pass in which a released hold is evaluated but the launch is then refused downstream (for example by the preflight). The relay path already behaves like this for `provider_held`, but the new rows multiply it. Collapse them: skip the append when the previous matching row has the same reasons, or add a per-state "first/last seen" marker.

### IN-02: lineage and preflight are coupled in one try block, so an error in the first disables the second

**File:** `tools/gsd_mission.py:1549-1556`, `tools/mission_launch_gate.py:108-118`
**Issue:** `mlg.refusal` runs `_lineage` before the preflight, and `supervise` wraps the whole call in one `except Exception`. Any exception from `pb.lineage_hold` (it calls `hold_for` unwrapped, and only the `load` call has a try) turns into `launch_gate_unavailable`, and the env preflight never runs. A NOT_READY env then launches. Wrap `_lineage` separately inside `refusal` and fall through to the preflight, recording the lineage failure as its own ledger row.

### IN-03: deploy details that weaken rollback evidence or leave gaps

**File:** `tools/gex44_env_deploy.py:323`, `:169`, `tools/test_gex44_env_deploy.py`
**Issue:**
- `git update-ref refs/pp-deploy/backup-<ts> <old>` has no old-value guard. Two applies in the same UTC second would silently overwrite the first backup ref (the timestamp has one-second resolution). Pass the zero oid as the third argument so the ref must not already exist.
- `plane_marker` is "present" whenever the name `CPP_MISSION_PLANE` appears in an export line, even with an empty value. `mission_launch_gate.preflight_enabled` requires a non-empty value, so such an env is reported as gated by the deploy but never is.
- There are no gates for code 7 (still stale), code 8 (fetch/checkout failure), or a failure after the checkout (partial state), and no drill kills the code-7 branch. WR-02 would have been caught by one.

### IN-04: test fixtures leave temp directories behind

**File:** `tools/test_mission_launch_gate.py:38`, `:123`, `:231`; `tools/test_persistent_failure_park.py:26`, `:197-198`, `:227-260`; `tools/test_gex44_env_preflight.py`
**Issue:** `tempfile.mkdtemp(...)` is used for state dirs, scratch HOMEs and transcripts with no cleanup. Each run, and each drill iteration, leaves directories under /tmp. `test_gex44_env_deploy.py` already shows the right pattern (`atexit.register(shutil.rmtree, ...)`). Apply it to the other three.

---

_Reviewed: 2026-10-03_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
