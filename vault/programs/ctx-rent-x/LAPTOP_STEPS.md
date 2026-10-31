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

## L5 — Phase 3 main canary (laptop)
Requires Claude build in `COMPAT` (2.1.296; GEX44 has 2.1.113, so mod tests cannot run here).
1. Mod tests: `claude plugin test mods/cpp-cognitive-runtime` (red first: before this commit's policy.ts change `resolveMainMode` import fails; now 2 new tests must pass). Dev load: `claude --plugin-dir mods/cpp-cognitive-runtime`.
2. Release: `python tools/ccr_release.py release --impact none`; backup `~/.claude/ccr/ACTIVE.json` first; revert = restore it.
3. Run the frozen `contracts/P3-main-canary.contract.json`: >=3 counterbalanced pairs in real interactive panes, arm = `CCR_MAIN_MODE=enforce` vs unset. Smoke: start receipt shows `main:enforce` and `main_source:"env"`.
Do not flip the default; that is a Phase 8 ratchet item.
