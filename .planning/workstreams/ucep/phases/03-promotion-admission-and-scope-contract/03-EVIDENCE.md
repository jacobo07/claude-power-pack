# Phase 3 evidence: promotion admission and scope contract

Executed inline by the orchestrator (epoch 3), because subagents have no PowerShell tool in this
session (see STATE.md decisions). The plan text and the committed verify commands are unchanged.

## 1. Scope and start state

- PHASE3_BASE: `8cf3fd9c62172bb1748703e192c0ea232cb0eeea`
- Branch: `ucep/mission` (worktree `C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\ucep`)
- Precondition (`git status --porcelain` over modules/tower, the five tower/ucep suites,
  tools/family_baseline.py, the registry and vault/tower/baselines): empty. No other writer.
- Dirty-path SET at start (sorted), none of which this phase may stage:
  `.gsd/`, `.planning/workstreams/ucep/config.json`, `.planning/workstreams/ucep/state.json`,
  `vault/progress.md`

## 2. F0 at phase start

| file | F0 reference | measured | CR bytes | equal |
|---|---|---|---|---|
| kobiicraft_mode/B0.json | 1a501441...0a2407 | 1a50144150bf7134c966fd832a368a18958a363a7fb8cfc9bbe8ea481a0a2407 | 0 | equal |
| persistent_state/B0.json | bcb20d37...74dc64 | bcb20d37f568a8873710990e4e43351010e882ac6fcd0f38b1e387a1d674dc64 | 0 | equal |
| persistent_state/B1.json | 0586c6a2...f315f2 | 0586c6a27eba0fdd3a7793c8e8ed32bd5ab9104cb09085faba7b456af8f315f2 | 0 | equal |
| web_surface/B0.json | 98e8d33f...a5eea2d7 | 98e8d33fef37ae75732cd92694d4ef20bd68ce8649c3239f6dfd8d16a5eea2d7 | 0 | equal |
| web_surface/B1.json | 2e54ac45...5cd8e1 | 2e54ac452ac256703fb5a3d9b8252ed30a903ab3d64f651c16174727ee5cd8e1 | 0 | equal |
| wii_homebrew/B0.json | 2603cf39...4bc1bd | 2603cf39889cb421c9fd31968b706d68a79aa7f14539173a4eb669761a4bc1bd | 0 | equal |
| wii_homebrew/B1.json | f255befa...43451a | f255befaed5f66238361f74f47c71523802fab90a05119dfc9198355ac43451a | 0 | equal |

The middle column is abbreviated for width; the full reference values are in 03-F0-REFERENCE.md, and
the verify command compares the full strings.

```
F0_START=EQUAL rows=7
```

## 3. Suite floors

Regression loop with a hermetic temp HOME/USERPROFILE/CLAUDE_STATE_DIR, at PHASE3_BASE:

```
test_ucep_baseline_integrity rc=0 pass=40/40 floor=40 fail_lines=0 OK
test_ucep_donegate_exits rc=0 pass=17/17 floor=17 fail_lines=0 OK
test_baseline_generations rc=0 pass=18/18 floor=18 fail_lines=0 OK
test_tower_ratchet rc=0 pass=21/21 floor=21 fail_lines=0 OK
test_tower_donegate rc=0 pass=10/10 floor=10 fail_lines=0 OK
test_family_baselines rc=0 pass=20/20 floor=20 fail_lines=0 OK
test_tower_select rc=0 pass=15/15 floor=15 fail_lines=0 OK
test_tower_checks rc=0 pass=23/23 floor=23 fail_lines=0 OK
test_tower_capsule rc=0 pass=16/16 floor=16 fail_lines=0 OK
test_tower_inheritance rc=0 pass=17/17 floor=17 fail_lines=0 OK
test_family_injection rc=0 pass=24/24 floor=24 fail_lines=0 OK
test_tower_o4 rc=0 pass=7/7 floor=7 fail_lines=0 OK
test_capability_archetypes rc=0 pass=59/59 floor=59 fail_lines=0 OK
test_capability_trait_scan rc=0 pass=28/28 floor=28 fail_lines=0 OK
test_gsd_x_heartbeat_path rc=0 pass=7/7 floor=7 fail_lines=0 OK
FLOORS_BAD=0
```

Instrument control (orchestrator, before execution): the same loop with `test_tower_o4` held to a
floor of 8 printed `test_tower_o4 rc=0 pass=7/7 floor=8 fail_lines=0 BELOW` and `FLOORS_BAD=1`, so
the loop can fail. Its FAIL regex matched the indented `  FAIL V-...` line of a real RED log.

## 4. Liveness before

```
LIVENESS_BEFORE passed=False rows=488 offenders=63
```

Offender names: `03-liveness-before.json` (`head` = PHASE3_BASE, `admission_row` null). The 63 are
standing debt and match the Phase 2 snapshot by name.

## 5. RED records

| task | RED line (verbatim) | failing gates | already passing (with control) | HEAD |
|---|---|---|---|---|
| 03-01 T2 | `TOWER_ADMISSION_PASS=1/6  threshold=6/6` (rc 1) | TRACER-ARCHETYPE, TRACER-REFUSED-ORIGIN, TRACER-RECORD-INVALID (admission module absent: guarded ImportError), LEGACY-IDENTITY (no LEGACY_GENERATIONS), LIVENESS-DECLARED (no row) | HERMETIC-HOME (instrument, no control needed). Caveat: TRACER-REFUSED-ORIGIN failed on the import guard, not on today's `promote` writing the unverified entry; the successor should show that hole directly (promote `bad` on 137c583b code writes B0) before writing the module, or record it as not demonstrated | 137c583b |
