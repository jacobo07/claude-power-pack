---
phase: 02-persistent-failures-and-remote-integrity
plan: 02
subsystem: remote-env-preflight
tags: [pillar-B, IC-B, preflight, gex44, read-only, mutation-drill]
requires: ["02-01"]
provides:
  - "tools/gex44_env_preflight.py: env_from_root, env_current, check_auth, check_pp_install, check_hooks, check_interpreters, satisfies, aggregate, run, js_manifest, run_js_engine, CLI (--env-root / --current / --checks / --json / --now), exit 0 READY / 1 NOT_READY / 2 UNMEASURABLE"
  - "PP_COMMIT_FLOOR 5962571c840943ae0a3aa901efb08e69a04434da and PP_REQUIRED_FILES (the instrument plan 02-03's launch gate calls and 02-04 raises)"
  - "tools/test_gex44_env_preflight.py: 55 V-ENVPF-* gates plus --drill (6 mutants)"
  - "vault/programs/incremental-cognition/evidence/B-preflight-gex44.json: read-only a5/a7 verdicts, plane gex44, no-write proof"
affects: [02-03, 02-04]
tech-stack:
  added: []
  patterns: ["static env.sh parse (never sourced)", "probe sandbox: throwaway HOME + GIT_OPTIONAL_LOCKS=0 + scratch child environment", "measured refusal outranks unmeasured sub-probes, which are listed beside it"]
key-files:
  created: [tools/gex44_env_preflight.py, tools/test_gex44_env_preflight.py, vault/programs/incremental-cognition/evidence/B-preflight-gex44.json]
  modified: []
decisions:
  - "aggregate: any measured NOT_READY -> NOT_READY (unmeasured listed beside it); else any UNMEASURABLE -> UNMEASURABLE; else READY. Deliberately the opposite precedence of the JS activation aggregate"
  - "An engine range that the env's install cannot supply (installs that predate vendor/genesis-suite) is UNMEASURABLE for interpreters, not a guess; the measured node/python versions are kept in detail anyway"
  - "A PP install directory that is absent is NOT_READY pp_install_stale; one that exists but is not a git checkout root is UNMEASURABLE"
status: complete
commits: 1
plan_head_before: e8cac7605ea344a63a05e13661b6c85376caa6ae
actuals:
  tokens: 21400
  tasks: 3
  commits: 1
metrics:
  completed: 2026-10-03
requirements: [IC-B]
---

# Phase 2 Plan 02: GEX44 env preflight, typed and four-valued Summary

One repeatable command, `python3 tools/gex44_env_preflight.py --env-root ~/a7-env --json`, answers whether a launch in a GEX44 env is READY, NOT_READY with a reason from a closed set, or UNMEASURABLE (exit 0 / 1 / 2), over four separate checks (auth expiry, PP rules version, hook health, interpreters), and it was run read-only on a5 and a7 with a stat-proven no-write result.

**Code commit: `4c31bb0a504ddaaa6b601d6477374fdb8dc67f43`** (`git show --stat HEAD` lists exactly tools/gex44_env_preflight.py, tools/test_gex44_env_preflight.py, evidence/B-preflight-gex44.json). `tools/gsd_x_runtime_preflight.js` and `tools/gsd_mission.py` are untouched.

## What was done

- **Task 1 (tracer):** env root -> `env_from_root` -> `check_auth` -> `aggregate` -> CLI exit code, end to end, with canary tokens in the fixture credentials. `check_auth` uses `provider_breaker.credentials_state` / `credentials_expired` (one reader and one predicate shared with pillar C): expiresAt 0 or lapsed-with-no-refresh -> `auth_expired`; lapsed but refreshable -> READY with finding `access_token_lapsed_refreshable`; no file and no API-key variable name -> `auth_missing`; no file but an API-key variable *name* exported, or unreadable/malformed file -> UNMEASURABLE.
- **Task 2:** `check_pp_install` (floor present, ancestor of HEAD, required files, local modifications as a finding only), `check_hooks` (every registered command hook resolved to an existing interpreter and script; JS scripts under `node --check`; each `hook-dispatcher.js` loaded and every registered `--event=` looked up in its CHAIN_NAMES + EVENT_NAMES; shell-construct commands reported unjudged and never run; foreign-env paths a finding), `check_interpreters` (env node vs the vendored engine range through `satisfies`, python >= 3.9, then the existing JS engine called with a generated manifest). Two gates run against real history: the real floor (`V-ENVPF-PP-REAL-READY`) and a shared clone with HEAD moved to the measured a7 head `01199995` (`V-ENVPF-PP-STALE-REAL`, which also asserts the *ancestry* path fired, not only the missing-files path).
- **Task 3:** read-only run on a5 and a7, evidence committed, `--drill` added.

## RED output, verbatim

Task 1, before `tools/gex44_env_preflight.py` existed:

```
Traceback (most recent call last):
  File ".../tools/test_gex44_env_preflight.py", line 26, in <module>
    import gex44_env_preflight as ep  # noqa: E402
ModuleNotFoundError: No module named 'gex44_env_preflight'
```

Task 2, with Task 1 green (13/13) and the Task 2 gates added, before the three checks existed (21/55; the 34 reds were `AttributeError: module 'gex44_env_preflight' has no attribute 'check_pp_install' | 'check_hooks' | 'satisfies' | 'check_interpreters' | 'js_manifest' | 'run_js_engine'`, plus `V-ENVPF-PP-STALE-REAL: rc=2 verdict=UNMEASURABLE`; eight hook gates additionally read `FileExistsError` from my own fixture builder, fixed in the test harness before GREEN):

```
FAIL V-ENVPF-PP-STALE-FLOOR-ABSENT: AttributeError: module 'gex44_env_preflight' has no attribute 'check_pp_install'
FAIL V-ENVPF-PP-STALE-REAL: rc=2 verdict=UNMEASURABLE reasons=[] head=01199995 floor=5962571c
FAIL V-ENVPF-HOOKS-NONE: AttributeError: module 'gex44_env_preflight' has no attribute 'check_hooks'
FAIL V-ENVPF-SEMVER-TABLE: AttributeError: module 'gex44_env_preflight' has no attribute 'satisfies'
FAIL V-ENVPF-JS-REAL: AttributeError: module 'gex44_env_preflight' has no attribute 'run_js_engine'
ENVPF_PASS=21/55  threshold=55/55
```

## GREEN and drills

- `python3 tools/test_gex44_env_preflight.py` -> `ENVPF_PASS=55/55  threshold=55/55`; `PASS V-ENVPF-PP-STALE-REAL: rc=1 verdict=NOT_READY reasons=['pp_install_stale'] in_process=NOT_READY head=01199995 floor=5962571c`; `PASS V-ENVPF-JS-REAL: good=(rc 0, SATISFIED) bad=(rc 1, UNMET)` (the real engine against the real gsd-core lib; it would print `SKIP` with a reason if the lib were absent); `PASS V-ENVPF-NO-SECRET: outputs=15 leaked=[]`.
- `--drill`:
  ```
  PASS DRILL-CONTROL unmutated run: 55/55 gates green
  KILLED M1 aggregate maps UNMEASURABLE to READY by V-ENVPF-UNMEASURABLE-NOT-READY
  KILLED M2 credentials_expired always False by V-ENVPF-AUTH-EXPIRED-ZERO
  KILLED M3 ancestor test always passes by V-ENVPF-PP-STALE-REAL
  KILLED M4 missing scripts ignored by V-ENVPF-HOOKS-MISSING-SCRIPT
  KILLED M5 satisfies() always True by V-ENVPF-NODE-V18-UNSUPPORTED
  KILLED M6 JS UNMET mapped to READY by V-ENVPF-JS-UNMET
  PASS DRILL-CLEAN-AFTER-MUTANTS unmutated rerun: 55/55 gates green
  DRILL killed=6/6
  ```
  The first drill run showed `SURVIVED M3` (5/6): the a7-shape fixture was still refused by the second, weaker signal (required files missing, the clone is `--no-checkout` and a7's head predates the files). The gate now also asserts the ancestry message, and M3 is killed. The mutants are in-process patches; no file was edited, so there is nothing to restore (module and test sha256 unchanged by the drill).
- Regression: `test_persistent_failure_park.py` -> `PFP_PASS=24/24`; `test_provider_breaker.py` -> `BREAKER_PASS=18/18`; `node tools/test_gsd_x_runtime_preflight.js` -> `GSDXPF_PASS=3/7` (same four laptop-plane FAIL names as before); `git diff --stat 34d08aa9..HEAD -- tools/gsd_x_runtime_preflight.js` prints nothing.
- `python3 tools/gex44_env_preflight.py --current`: 2.2 s, exit 1, `interpreters NOT_READY node v18.19.1 is outside ^22.23.2 || ^24.14.0` (auth, pp_install READY, hooks 54 healthy + 11 unjudged shell constructs). This is the same cause as the pre-existing `V-MC-PLAN-FACTS-REFUSES-OVERLAP` red.

## Measured: a5 and a7, plane gex44, read-only (evidence/B-preflight-gex44.json)

Measured 2026-10-03T18:26:35Z on `kobicraft-gex44`. Both exit 1.

| env | verdict | reasons | findings | per check |
|-----|---------|---------|----------|-----------|
| a7 | NOT_READY | auth_expired, pp_install_stale | install_modified, hooks_foreign_env | auth NOT_READY (expiresAt 0, 1970-01-01); pp_install NOT_READY (floor 5962571c not in history, head 01199995, `tools/provider_breaker.py` missing); hooks READY (50 judged; every hook resolves into a5's tree); interpreters UNMEASURABLE |
| a5 | NOT_READY | pp_install_stale | install_modified | auth READY; pp_install NOT_READY (head 192390b9 on feature/knowledge-acquisition, floor absent, `tools/provider_breaker.py` missing, 1024 modified tracked files); hooks READY (50 judged); interpreters UNMEASURABLE |

**Prediction vs measured.** Predicted before the run: a7 `NOT_READY [auth_expired, pp_install_stale]` + finding `hooks_foreign_env`; a5 `NOT_READY [pp_install_stale]`. Reasons and the foreign-env finding match exactly. Two things I did not predict, kept as measured: both installs report finding `install_modified` (a7: 1 modified tracked file; a5: 1024; the cause was not investigated, and a5 carries an `a5_linux.patch` beside its env, so a port patch is one candidate), and `interpreters` is UNMEASURABLE on both because neither install contains `vendor/genesis-suite/package.json`, so there is no engine range to judge node against. The measured versions are in the result detail: env node `v24.15.0` and `Python 3.12.3` for both (inside the range the current install declares, but that is not a judgment the old install's own files can make). The hooks in a7 working "healthy" while resolving into a5's tree is the foreign-env finding doing its job, not a pass on isolation.

**No-write proof.** `stat -c '%n %s %Y'` on the eight named env files (env.sh x2, settings.json x2, install `.git/index` x2, `.git/HEAD` x2) before and after both runs: `diff` printed nothing. Credentials files were deliberately excluded (a live worker may refresh them). Scan of both outputs for `accessToken`, `refreshToken` and `CANARY`: 0; the only 40+ character runs are commit ids and path fragments.

## Deviations from Plan

**1. [Rule 3 - Blocking] `vault/programs/incremental-cognition/evidence/` did not exist.** Created the directory (a program-owned path) so the evidence file could be written; the three plan-listed files are the only ones committed.

**2. [Rule 1 - Bug, my own test harness] Two harness faults found by the RED run, fixed before GREEN:** `make_env` used `mkdir(exist_ok=False)` on a directory the hook fixtures create first (`FileExistsError`); and `V-ENVPF-PP-STALE-REAL` asserted only state and reasons, which let drill mutant M3 survive until the ancestry message was asserted. No production behavior involved.

**3. [Plan-driven commit granularity] One commit for all three tasks.** Tasks 1 and 2 carry no commit step; Task 3 specifies a single pathspec commit of the three files with a `git show --stat HEAD` check.

**4. [Evidence generation] The evidence JSON was assembled by a small script from the two raw outputs rather than typed by hand,** to avoid transcription error; the plan's required keys are all present, plus `instrument`, `secret_scan` and `prediction_vs_measured`.

Otherwise the plan executed as written. No auth gates. No architectural changes.

## Known Stubs

None.

## Threat Flags

None. The mitigations in the plan's register are pinned: T-02-02-01 by `V-ENVPF-NO-SECRET` (canaries over stdout, stderr and returned JSON, 15 outputs) and the evidence grep; -02 by `V-ENVPF-ENVSH-STATIC` (a side-effecting env.sh line leaves no file); -03 by `V-ENVPF-HOOKS-SHELL-UNJUDGED` (a `touch ... ; ... | cat` hook command is reported unjudged and its sentinel file never appears) and `V-ENVPF-NO-SHELL`; -04 by `V-ENVPF-PROBE-ISOLATION` plus the empty stat diff; -05 by `V-ENVPF-UNMEASURABLE-NOT-READY` and drill M1; -06 by `V-ENVPF-HOOKS-CAP-REPORTED`, `V-ENVPF-BUDGET-EXHAUSTED` and a per-probe 15 s timeout; -07 by `V-ENVPF-AUTH-LAPSED-REFRESHABLE`.

## Open items (not this plan)

- Wiring the verdict into `gsd_mission.py` launches (typed refusal + ledger row + kill switch) is plan 02-03; raising `PP_COMMIT_FLOOR` to the 02-03 commit and the repeatable deploy script are plan 02-04.
- For 02-03 to decide: an UNMEASURABLE `interpreters` check is what every currently-deployed a5/a7 install will report (no vendored engine range). Whether a launch gate treats that as non-churning, as CONTEXT says UNMEASURABLE should, is exactly the case in front of it.
- a7 re-login (credentials expiresAt 0) and deploying the current PP to a5/a7 remain Owner actions for the owner bundle (`[B]` lines are 02-04's).
- Ledger `state.B` NOT written; the pillar terminal needs the real deploy/launch evidence.
- Pre-existing GEX44 reds (node v18 plan-graph fact, G23 card bytes, handoff_packet TypeError) are unchanged and out of scope.

## Self-Check: PASSED

- `tools/gex44_env_preflight.py`, `tools/test_gex44_env_preflight.py`, `vault/programs/incremental-cognition/evidence/B-preflight-gex44.json` exist and are in commit `4c31bb0a504ddaaa6b601d6477374fdb8dc67f43`; `git rev-list --count e8cac7605ea344a63a05e13661b6c85376caa6ae..HEAD` = 1; no deletions.
- `ENVPF_PASS=55/55`, `DRILL killed=6/6`, `grep -c 'PP_COMMIT_FLOOR = "[0-9a-f]\{40\}"'` = 1, `grep -c "shell=True"` = 0, `diff` of the env stat files empty, evidence `plane gex44 ['a5', 'a7']`, secret grep 0.
