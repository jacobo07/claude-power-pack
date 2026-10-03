---
phase: 02-persistent-failures-and-remote-integrity
status: human_needed
verified: 2026-10-03
plane: gex44 (tests, read-only env probes); laptop PRG and env deploys pending (owner bundle [B]/[C])
score: 8/8 must-haves verified after orchestrator gap closure (owner-bundle [C] pick list fixed); IC-B/IC-C terminals intentionally open
behavior_unverified: 0
covered_files_note: "verification.fingerprint (#4155) was not run; covered_files/covered_digest omitted"
gaps:
  - truth: "The owner bundle carries exact commands that run as written (02-04 truth 6; task requirement 'owner bundle carries the exact commands')"
    status: closed
    closed_by: "orchestrator, owner-bundle [C] line now picks the 7 commits; replayed in a scratch clone at aa30640b: PFP 28/28, LG 20/20, BREAKER 18/18"
    reason: "Bundle line [C] laptop deploy cherry-picks only 5962571c (02-01) and 60e7947d (02-03). Simulated in a scratch clone at aa30640b (parent of phase 2): after those two picks test_mission_launch_gate gives LG_PASS=18/19 (FAIL V-LG-REAL-PREFLIGHT-E2E: launches=1 refused_rows=0, because 4c31bb0a/02-02 gex44_env_preflight.py is not picked) and test_persistent_failure_park gives PFP_PASS=24/24 instead of 28/28 (post-review fixes WR-04/WR-07 are not picked). Picking 5962571c 4c31bb0a 60e7947d 7259ccb0 a1c593f2 c6dd2087 9a267502 gives PFP 28/28, LG 20/20, BREAKER 18/18."
    artifacts:
      - path: "vault/programs/incremental-cognition/owner-bundle.md"
        issue: "[C] cherry-pick list incomplete; it was written before the WR-01..07 fix commits and misses the 02-02 commit the gate imports"
    missing:
      - "Replace the [C] cherry-pick line with the 7-commit list above (or a branch merge), and say that the laptop's PP_COMMIT_FLOOR hash will not exist after a cherry-pick (the env preflight is a GEX44 tool; scratch run showed V-ENVPF-PP-REAL-READY red for that reason), so the preflight suite is not part of the laptop check"
human_verification:
  - test: "[C] PRG on the laptop: after the a7 env deploy, a7's mission shows provider_held (class auth, quarantine) with no launch, then provider_released and one relay after /login"
    expected: "ledger rows saved to evidence/C-prg.md; only then ledger state.C and IC-C"
    why_human: "needs the live laptop sweep and an interactive OAuth login; cannot be run by the verifier"
  - test: "[B] a7 re-login (interactive OAuth), then env deploy --apply for a7 and a5 after the Owner decides what to discard (exit 4: a7 1 modified file, a5 1024)"
    expected: "preflight on a7 shows no pp_install_stale / hooks_broken / auth_expired; saved as evidence/B-prg.md"
    why_human: "destructive decision on install-local changes and interactive login are Owner-only"
  - test: "WR-04, WR-06, WR-07 operator-facing semantics (fixer flagged 'requires human verification')"
    expected: "lapsed access token with unknown refresh expiry reads UNMEASURABLE / stays parked; `provider_breaker status|clear` act on a renewal successor's inherited hold"
    why_human: "predicate/operator semantics judgement; gates are green but encode the fixer's reading"
  - test: "WR-08 merge strategy: PP_COMMIT_FLOOR=60e7947d exists only on mission/incremental-cognition-run"
    expected: "merge preserving the commit (no squash/rebase) or re-point the floor in the same merge"
    why_human: "Owner decision, recorded in owner-bundle [B] NOTE (4d2e1411)"
---

# Phase 2 verification -- persistent failures and remote integrity (pillars C and B)

**Goal:** an authorization-class failure parks a mission instead of relaunching; a GEX44 launch proves its environment first.
**Branch/HEAD:** mission/incremental-cognition-run @ 450d8a84. Run on GEX44 (plane gex44).
**Requirements IC-B, IC-C:** satisfied only by their ledger terminal (Owner PRGs). Verified still open (below); this is intended, not a code gap.

## Suite results (observed this run)

| Suite | Result | --drill |
|---|---|---|
| tools/test_persistent_failure_park.py | PFP_PASS=28/28 | control 28/28, killed 6/6, clean after |
| tools/test_provider_breaker.py | BREAKER_PASS=18/18 | (no mutant drill; runs the suite) |
| tools/test_gex44_env_preflight.py | ENVPF_PASS=57/57 | control 57/57, killed 6/6, clean after |
| tools/test_mission_launch_gate.py | LG_PASS=20/20 | control 20/20, killed 6/6, clean after |
| tools/test_gex44_env_deploy.py | DEPLOY_PASS=19/19 | control 19/19, killed 8/8, clean after |
| tools/test_gsd_mission.py | MC_PASS=212/213 | only red V-MC-PLAN-FACTS-REFUSES-OVERLAP (node v18.19.1 vs ^22.23.2 \|\| ^24.14.0; known baseline, same as phase 1) |
| tools/test_gsd_epoch.py | EPOCH_PASS=82/82 | |
| tools/test_gsd_mission_cwd_align.py | MCA_PASS=16/16 | |

## Observable truths (roadmap criteria + PLAN must_haves)

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | SC1: red test of the 137-relaunch shape, fix, green | VERIFIED | Scratch checkout of aa30640b (pre-fix tools) with the 5962571c test file: `FAIL V-PFP-137-FALLBACK-PARKS: launches=3 provider_held(auth,quarantine) rows=0 (3 relay cycles, breaker unimportable)`. At HEAD: `PASS V-PFP-SUP-NO-RELOGIN-PARKS: launches=0 provider_held(auth)=3`, PFP 28/28. |
| 2 | 02-01: breaker importable, parked until credentials rewritten after refusal with usable login; quoted /login by a model never parks; no token value exposed | VERIFIED | `V-PFP-SUP-RELOGIN-RELAYS launches=1 provider_released=1`, `V-PFP-FALLBACK-QUOTED-NOT-PARKED`, secret canary gate in suite; drill M1-M6 killed. `grep` of evidence JSONs and preflight JSON output for accessToken / sk-ant: 0 hits. |
| 3 | 02-01: gsd_mission.py changes in one hunk inside provider_hold | VERIFIED | 5962571c: one hunk at provider_hold. Net diff aa30640b..HEAD has 2 hunks total (provider_hold region incl. WR-07 helper; supervise successor path for 02-03 as planned). Pillar A untouched; cwd_align 16/16. |
| 4 | 02-02: repeatable preflight, four separate checks, typed READY / NOT_READY / UNMEASURABLE, exit 0/1/2, UNMEASURABLE never READY | VERIFIED | Ran read-only against both envs, plane gex44: a5 NOT_READY [pp_install_stale] (auth READY, hooks READY, interpreters UNMEASURABLE); a7 NOT_READY [auth_expired, pp_install_stale]. rc=1. sha256 of install .git/index, .git/HEAD, settings.json, env.sh before/after: unchanged on both. Drill M1 (UNMEASURABLE to READY) killed. Committed evidence B-preflight-gex44.json has plane gex44, no_write_proof, secret_scan. |
| 5 | 02-03: renewal cannot launder a quarantine; healthy / re-logged-in successor still launches | VERIFIED | `V-LG-RENEWAL-NO-LAUNDER`, `V-LG-LINEAGE-MULTIHOP`, `V-LG-LINEAGE-OPERATOR-SURFACES` green; mutants M1, M6 killed. |
| 6 | 02-03: declared plane refuses NOT_READY launch with typed reasons; unmeasurable proceeds visibly; undeclared host never runs it; kill switches | VERIFIED | `V-LG-REAL-PREFLIGHT-E2E launches=0 refused_rows=1 reasons=[auth_expired,hooks_broken,interpreter_unsupported]`, `V-LG-PREFLIGHT-UNMEASURABLE-LAUNCHES`, `V-LG-GATE-UNAVAILABLE`, `V-LG-UNMARKED-NOT-CALLED`; M2-M5 killed. |
| 7 | 02-04: deploy by git, dry-run default mutating nothing, guards (dirty, ancestry, non-env, own HOME, env.sh HOME outside root), lock, backup, rollback, post-deploy preflight decides success (WR-01..03 fixes) | VERIFIED | DEPLOY 19/19 incl. DRYRUN-NO-MUTATION, DIRTY-REFUSED, NOT-ANCESTOR-REFUSED, LOCK-HELD, REPLAN-UNDER-LOCK, ENV-HOME-OUTSIDE-ROOT-REFUSED, UNMEASURED-AFTER-IS-CODE-7, RELATIVE-SOURCE-REPO, REAL-UNTOUCHED; 8/8 mutants killed. Real-env dry-runs (no --apply): a7 and a5 both `REFUSED [4]` (modified tracked files 1 and 1024), exactly as the bundle states; rollback commands printed; no backup files created in the env roots. |
| 8 | 02-04: B.md / C.md evidence (commands, outputs, Product Delta, Intelligence Delta); owner bundle [B]/[C] lines with exact commands; ledger state.B/state.C unwritten; IC-B/IC-C unticked; arm-path debt line; PP_COMMIT_FLOOR at the gate commit with required file | PARTIAL | B.md and C.md both contain Product Delta and Intelligence Delta sections; ledger.json `"state": {"A": {}, "B": {}, "C": {}, ...}` and unchanged since aa30640b; REQUIREMENTS.md `- [ ] **IC-B**` / `- [ ] **IC-C**` unticked and unchanged; `test_incremental_cognition_program.py --pillar B|C` prints `CEP_PILLAR_x=FAIL no terminal disposition` (expected); arm debt line present; PP_COMMIT_FLOOR=60e7947d with tools/mission_launch_gate.py required. Absolute-path [B] deploy/preflight commands ran as written (above). **Gap:** [C] laptop cherry-pick list is incomplete (see gaps). |

## Review findings
02-REVIEW.md: 0 critical, 8 warnings, 4 info. 02-REVIEW-FIX.md: WR-01..07 fixed with RED/GREEN lines and a gate each (commits 55319136..9a267502 all present in history; suite counts above match the fix report). WR-08 deferred to Owner and recorded in owner-bundle (4d2e1411). IN-01..IN-04 not in fix scope and left open (info only).

## Anti-patterns
No TBD/FIXME/XXX in phase files; no `shell=True` in gex44_env_*.py or mission_launch_gate.py; no token values in output. Working tree only has untracked workstream config.json / milestone.lock and an auto-appended vault/progress.md session line (not phase work).

## Debts carried (documented, not gaps)
- `gsd_mission.py arm` first launch is ungated (owner-bundle [B] DEBT, shrink-only).
- Main-plane node v18.19.1 outside the engine range (owner action; causes the one baseline red).
- a5/a7 deploys refuse with exit 4 until the Owner decides about install-local changes.

## Gaps summary
One small documentation/command gap: owner-bundle [C] cherry-picks 2 of the 7 commits needed; as written the laptop check yields LG 18/19 and PFP 24/24. Fix is a one-line replacement in owner-bundle.md. Everything else in code and tests is verified; IC-B / IC-C remain open by design pending the Owner PRGs.

## Gap closure (orchestrator, 2026-10-03)

The one gap (owner-bundle `[C]` cherry-pick list) is closed. The line now picks
`5962571c 4c31bb0a 60e7947d 7259ccb0 a1c593f2 c6dd2087 9a267502`, the expected-base is `9a267502`, and the note says the env
preflight suite is a GEX44 tool, outside the laptop check (WR-08). Replayed verbatim in a scratch clone at `aa30640b`:
`PFP_PASS=28/28`, `LG_PASS=20/20`, `BREAKER_PASS=18/18`. The status moves to `human_needed`. The remaining items are the Owner-run
PRGs `[B]`/`[C]`, the WR-04/06/07 semantics judgement and the WR-08 merge strategy, all listed under `human_verification`.
