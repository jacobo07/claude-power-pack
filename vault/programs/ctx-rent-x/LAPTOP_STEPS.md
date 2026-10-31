# LAPTOP STEPS (ctx-rent-x) — copy-pasteable, run on the laptop; never claimed from GEX44

## L1 — Rent estate by CCR generation (laptop plane)
Why: GEX44 has no CCR start receipts (`~/.claude/ccr` empty), so every session is generation UNKNOWN here.
Command (repo root, laptop): `python tools/ctx_rent.py estate --since 2026-10-25T00:00:00Z --until 2026-11-01T00:00:00Z --out estate-laptop-w0.json`
Expected: JSON with `classes.<class>.<generation>`; generations other than UNKNOWN present; `active_release` non-null.
Acceptance: >=1 non-UNKNOWN generation cell; commit the file to vault/programs/ctx-rent-x/ on mission/ctx-rent-x.

## L2 — Release records source_commit
Command: `python tools/ccr_release.py release` then `python -c "import json;print(json.load(open('<release dir>/RELEASE.json'))['source_commit'])"`
Acceptance: a 40-hex commit (null only when not in git).

## L3 — Phase 2 floor diet, measure then apply (laptop; live ~/.claude)
Priority: floor (attachments ~119K/call) before dead tool-output rent. Contract: `contracts/P2-floor-diet.contract.json` (frozen).
1. Dry run: `python3 tools/floor_diet.py plan --home $HOME --used-agents <file of agent names used in last 30 days>` — read the lists.
2. Backup + apply one row set: `python3 tools/floor_diet.py apply --home $HOME --ts $(date +%Y%m%dT%H%M%S)`; it writes `~/.claude/backups/ctx-rent-x-<ts>/` with a manifest.
3. Probe per the contract (C T T C, repeat swapped), then REVERT before the next arm:
   `python3 tools/floor_diet.py revert --home $HOME --backup-dir ~/.claude/backups/ctx-rent-x-<ts>`
4. Revert is byte-identical (V-DIET-REVERT-BYTE-IDENTICAL). Record per-row call-1 deltas in vault/programs/ctx-rent-x/floor-diet-results.json; keep the diet applied only for rows with a measured delta and no lost hook capability.
Acceptance: per-row measured delta, N>=2 per arm.

## L4 — Row 5, hook additionalContext cap (laptop; edits ~/.claude/hooks)
Back up each hook file to ~/.claude/backups/ctx-rent-x-<ts>/, cap emitted additionalContext at 1000 chars inside the hook, revert = restore the backup. Measure with the same contract (row `hook_context_cap`, add it to the contract before probing).

## L5 — SUPERSEDED (D2). CCR_MAIN_MODE dropped; the live release already ships CCR_MAIN_CANARY=1 (v4 A7).
Measured on laptop: -20,795 call-1 (-22.3%), N=4/arm. Mod tests for `mainCanaryMode` are in policy.test.ts; run `claude plugin test mods/cpp-cognitive-runtime` on the laptop (claude >= COMPAT build). Never release mods from a tree that lacks 35776051.

## L6 — Canary page-fault + quality arm (laptop, real bounded task)
Contract `contracts/P3-main-canary.contract.json` (arm = CCR_MAIN_CANARY=1 vs unset, n>=3 pairs, ABBA). Report processed tokens, cache-weighted cost, calls, page faults (page tool calls), repairs, rereads, answer correct. Foreground batches only (memory reaper kills long background runs). Output: vault/programs/ctx-rent-x/main-canary-quality.json. Then Phase 8 default decision.

## L7 — Row 5 hook context cap: still NOT RUN (foreign WIP in session_start_hub.js). Run only when that file is clean.

## L8 — Ship CCR_MAIN_CANARY default-on (Owner D1, 2026-10-31; laptop, the only host with the compiled kernel digest)
Source: commit 4a7939bc (policy.ts default-on, register.ts env-failure fails closed, policy.test.ts). GEX44 rehearsal (temp root, repo kernel copy): build -> activate -> rollback -> re-swap all swap `active` correctly; release carries source_commit. Not claimed live.
1. `git fetch && git checkout mission/ctx-rent-x` (>= 4a7939bc, and tree must contain 35776051).
2. `claude plugin test mods/cpp-cognitive-runtime` (needs claude >= COMPAT build); policy.test.ts default-on test must pass.
3. `python3 tools/ccr_release.py status` (note current active id = rollback target), then `python3 tools/ccr_release.py release`. Check `~/.claude/ccr/active/RELEASE.json` has source_commit 4a7939bc or a descendant.
4. Start a FRESH interactive pane WITHOUT CCR_MAIN_CANARY set; the latest `start` receipt in ~/.claude/ccr/state/receipts must show releaseId = the new id and canary = enforce (main mode). A second pane with CCR_MAIN_CANARY=0 must show canary = off.
5. `python3 tools/ccr_release.py rollback`, confirm active id == the previous id, then re-run `release` (or rollback again) to restore. Only after 4 and 5 pass is it live.
6. Save receipts' lines to vault/programs/ctx-rent-x/LAPTOP_RESULTS.md and resume `/gsd-autonomous --ws ctx-rent-x` for Phase 8 UKDL/ratchet.
