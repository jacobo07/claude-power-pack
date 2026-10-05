# Gen3 T2 COMPILER step - PROGRESS (append-only)

Compiler agent, Phase 4 (Production Seams) of odr-device-trust. Spend = the measured quantity "c".

## Confirmed steps

1. Worktree `C:\Users\User\Apps\io-odr-p4-canary` (branch canary/odr-p4-packets, HEAD f2e1f560) is clean, but it does NOT contain
   `.planning/workstreams/` at all: the workstream inputs (REQUIREMENTS, ROADMAP, phases/04-*) are UNTRACKED files that exist only in
   `C:\Users\User\Apps\io-device-trust\.planning\workstreams\odr-device-trust\` (read-only use; never written). Outputs go to the canary's
   `.planning/workstreams/odr-device-trust/phases/04-production-seams/` (created). The canary's root `.planning/` is an older sidecar
   milestone; only its PROJECT.md (evidence discipline) is cited.
2. Meter at ~33 calls: 2.59M processed (cache reads dominate; each call re-reads ~85k context). Plan: few, large calls.
3. Verified anchors in the canary tree: ascend.sh heredoc 899..1235 (`location /api/` 1211, `location /` 1224); ci.yml C7 line 631,
   mnb_gate selftests 774-784, SMOKE_RESOLVE 841; deploy-vps.yml SBEAM-5 step at 131.
4. PATH CORRECTIONS vs 04-RESEARCH.md (research wrote paths that do not exist): DeviceSocket is
   `01_Core_Systems/infinity_mie/lib/infinity_mie_web/channels/device_socket.ex` (not `lib/infinity_mie_web/device_socket.ex`);
   mint controller is `lib/infinity_mie_web/odr_device_controller.ex` (not under controllers/);
   its test is `test/infinity_mie_web/channels/device_socket_test.exs`. `@typed_refusals` is device_socket.ex:59.
5. Not yet existing in the canary (to be created): vault/specs/odr-device-trust-seams.md, ascend_nginx_vhost_test.exs, device_socket_probe.mjs,
   app/sistema/dispositivos/*, lib/device-view.ts, app/sistema/sistema-nav.tsx. `vault/specs/odr-device-trust-c5.md` exists (M1..M46).

## Test-suite facts (from repo CI + workstream docs)

- Backend (infinity_mie): CI = `mix test --warnings-as-errors` with working-directory `01_Core_Systems/infinity_mie` (ci.yml:136-138; Elixir 1.19.0/OTP 28.1).
  Local (STATE/PROJECT): Postgres :5433 must run (`pg_ctl -D C:\Users\User\Apps\_pg\sidecar_test ... -p 5433`), `$env:MIX_ENV='test'`, mix via scoop,
  `mix format` ONLY with MIX_ENV=test. test_helper.exs runs Repo.delete_all so even DB-free ExUnit files need Postgres.
- Frontend (infinity_ui, working-directory `13_UI_Product_Layer/infinity_ui`): CI = `corepack pnpm exec vitest run <explicit files> --environment node`
  from an EXPLICIT per-group list in ci.yml (ui_guards); new test files do not run in CI unless a step names them. Local: no npm; `node node_modules\vitest\vitest.mjs run <files> --environment node`.
- Smoke `.mjs`: dependency-free Node 22, `node 08_Workflows_Code/smoke/<name>.mjs --selftest` (ci.yml mnb_gate job 762-784).
- Executors: subagents have no PowerShell and a Bash guard that blocks git/mix/node (STATE.md); GSD practice = run plans INLINE in the main session via PowerShell.

## Setup state of the fresh canary worktree (measured)

- `13_UI_Product_Layer/infinity_ui/node_modules`: ABSENT. `01_Core_Systems/infinity_mie/_build` and `deps`: ABSENT (first `mix deps.get` + compile is large).
- STATE.md plan for vitest: junction `node_modules` -> `C:\Users\User\Apps\io-focus\13_UI_Product_Layer\infinity_ui\node_modules` (identical pnpm-lock),
  remove with `cmd /c rmdir node_modules` (never /s), never commit. Whether io-focus still has node_modules is to be re-checked by the executor.

6. Obligations 324 + 5 AMB compiled; 5 packets; check_coverage.py PASS 329/329 and FAIL(exit 1, 2 errors) on a broken copy. Committed 69c87616 with git add -f (.planning is gitignored in this repo). Meter at commit: 5.62M processed over 29 distinct messages (HARD CAP 4.5M EXCEEDED: the cap was already crossed at 4.82M when the metering check ran; cache-read of the ~85k context per call dominated).
E1 PK-01 step 1: spec vault/specs/odr-device-trust-seams.md written (S1 PLANNED until proof); ascend.sh D-01 block inserted between checkout-session and /api/ (no deopt: 1 heredoc, no regex/other ^~ prefix of /socket/device/); vhost test written; deps.get done, MIX_ENV=test compile running (logs in worktree tmp/).
E1 resolved ambiguities recorded: AMB-1 UI-CHECK approved; AMB-2 D-03 server action supersedes Next BFF route; AMB-3 BLOCKED_BY_EXTERNAL_CONDITION if Phoenix cannot boot; AMB-4 typecheck=package.json tsc --noEmit; AMB-5 probe flags executor's choice.
E1 PK-01 DONE: commit f320bd90 (ascend.sh +20, ascend_nginx_vhost_test.exs 28 tests/0 fail --warnings-as-errors, spec odr-device-trust-seams.md); drills M47-M52 all RED with named tests, restores hash-equal, GREEN rerun; deps compiled MIX_ENV=test, logs in worktree tmp/ (untracked).
E2 2026-10-05T20:44:08 PK-02 afdc7e8e (24/24 vitest, tsc 0, M53/M56 RED) and PK-04 45a80a6b (selftest 18/18, pin 10/0, M57-M60 RED, LOCAL live PASS) committed; Phoenix stopped, :4000 closed. Metered own transcript agent-a62a4e48e744482c5.jsonl: msgs=45 processed=8485134 (over the 6M cap by dedup-per-message.id method; stopped after the cleanup and commit).
E3 meter: agent-aad9290e4ba27f485.jsonl calls 35 spent 5794831 proj 6622661 (calls 3/12/23/final; earlier readings 460180 @4, 1574580 @12, 3486720 @23; all projections < 9M cap). PK-03 files done, 56 tests green, tsc 0, M54/M55 drilled; committing.

E4 meter: call 36 processed=5192221 (cache-read inflated) exceeded 4M cap at wrap-up; full proven set committed. PK-05 done locally, nothing pushed.
