# Curated public export: CCR + mission runtime + floor gate + ICC to `main` (2026-11-06)

**STATUS: DONE 2026-11-08.** PR #16 (`export/ccr-mission-icc` 73cb7a04, from feature a39ce0fc) merged into `main`
as 80505467, with Owner "y". X1-X4 receipts are in the PR body:
- 186 files; scrub verified on `origin/main` (0 hits per pattern, `import` control 131 files);
- CCR plugin 39/0; 51/55 exported suites green, and the 4 reds fail identically on a39ce0fc;
- liveness: 0 new offenders, 8 fewer;
- pp-code-reviewer APPROVE.

Follow-ups: host-derived config paths on `main` (PR "Known not portable"); pre-existing user paths on `main`.

Source: pane bcf0a0bc (ICC coordinator). Owner decision 2026-11-06 ("1 y 3 al backlog"): `main` stays as it is now;
the large curated export below is backlog. Nothing below is started.

## State at write time
- `origin/main` = `abc63bb9` (#13). `main` receives CURATED exports only (#11 "curated S11 export", #13 "zero derived
  content"): game names, real function addresses (`fn_80xxxxxx` -> `fn_00000A01`) and user paths are scrubbed.
  Measured with `git grep -l`: origin/main has 0 files with `fn_80[0-9A-F]{6}` and 2 with "Tennis". Tree `18d2b3e4` of
  `feature/knowledge-acquisition` has 134 and 90, plus 492 files with `C:\Users\User`.
- `origin/feature/knowledge-acquisition` carries ICC (merge `558f5f26` of `a0f8a8d3`) and was pushed 2026-11-06.
  It was uncurated before that push and stays as it is (Owner).
- Wholesale merge of feature into main: refused. Trial `merge-tree origin/main feature` = 8 conflicts. Five of them are
  add/add of the curated copies: `tools/mission_policy.py`, `tools/heldout_release.py` + their tests, and the phys-p14
  fixture. The other three are content conflicts: ukdl-universal, reachability_registry and deferred-backlog.
- An ICC-only export is NOT standalone. The trial `git apply --check --3way` of `ac057454..a0f8a8d3` onto origin/main:
  - Absent on main: `mods/` (the whole CCR runtime), `tools/floor_regression_gate.py`, `tools/mission_spend.py`,
    `tools/ctx_rent.py`.
  - Too far behind to apply: `tools/gsd_mission.py` is 2,039 lines on main vs 8,286 on feature; the
    `hooks/session_start_hub.js` and `tools/agent_carrier_run.py` patches fail too.

Size: L (multi-session). Priority P2. Nothing live depends on main.

## X1. Inventory (S)
List every file that the ICC change set depends on transitively and that main lacks or holds at another version: the
CCR mod, the mission runtime (`gsd_mission`, `mission_spend`, `mission_topup`, `mission_binding`, capsule, epoch), the
floor gate and its budget, `ctx_rent`, and the hooks the hub wires. Output a file list with its dependency reason.
Done when: the list exists and an `apply --check` of the full set onto origin/main is clean in a scratch worktree.

## X2. Scrub pass (M)
Apply the #11/#13 curation rules to every exported file:
- game names -> generic;
- real addresses -> synthetic ids (`fn_00000A01` style), kept consistent across code and tests;
- absolute user paths -> `~`.

No recon/disassembly fixtures and no `modules/recon_fabric/fixtures` (the pre-push hook refuses them anyway).
Done when: on the export tree, `git grep -E 'fn_80[0-9A-Fa-f]{6}|Tennis|C:\\Users\\User'` returns 0, and a reviewer
has read the diff for derived content that a grep cannot see.

## X3. Green on the export tree (M)
The exported suites must pass on the export tree itself, not on feature: the CCR plugin tests, test_gsd_mission,
test_floor_regression_gate, test_done_gate_close, test_ctx_regret, test_carrier_handback and test-ccr-compat-line.
Done when all exit 0 there, and `modules/liveness/reachability.py` passes for the exported modules.

## X4. PR + merge (S)
Branch `export/ccr-mission-icc`, PR to main with the inventory, the scrub rules and the test receipts. pp-code-reviewer
must APPROVE. Merge, then `git ls-remote` and a `git grep` of `origin/main` to re-check X2.

## Related
- ICC open items (not part of this export): enforcing `CCR_DEFERRED_NAMES` needs the M2 attachment-format check plus an
  n=10 bench; Phase 3 is blocked by the foreign CLAUDE.md edit; P4/P5 review; GEX44 pointer (HR-001). See
  `.planning/workstreams/icc/STATE.md`.
- Landing technique for shared dirty trees (merge-tree -> commit-tree -> CAS update-ref -> 3-way per foreign-dirty file
  with CRLF normalisation and an exact size check): see ctx-rent-x backlog F4. The CRLF trap made a clean merge look
  like a whole-file conflict on 2026-11-06.
