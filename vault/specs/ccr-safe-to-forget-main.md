---
status: APPROVED 2026-11-03 (Owner "y" on the Phase 5 plan, GPF coordinator pane)
covers: [ccr, safe-to-forget, phase-5, cr-09, cr-10, cr-13, tool-output-projection, page-fault, ccr-main-project]
owner: ctx-rent-x W4 / GPF W2 (plan vault/plans/ctx-rent-x-2026-10-31.md W4; vault/plans/global-prefix-floor-2026-11-02.md W2)
---

# CCR Safe-to-Forget in main panes (ctx-rent-x Phase 5)

## Problem (measured 2026-11-03)
`projectShell` (`mods/cpp-cognitive-runtime/hooks/register.ts`) cuts a shell result over 8,000 chars to head+tail plus the
path of the full output. It enforces only in Work Unit sessions and /kresume successors; interactive panes run it in shadow.
CCR receipts (1,468 files, 468 sessions): 1,080 shadow projections in main panes = 6.4M chars that would have been removed at
emission, each then riding every later call. Three things are missing before main may enforce it:
1. the full output is written but never read back: "durable" is assumed;
2. a verdict / failure / commit line in the omitted middle is lost (only a FAILED command is protected, via `shellFailed`);
3. nothing counts the later Read/Grep of the full output: 0 `projected` page-fault receipts exist.
CR-09/10/13 are UNKNOWN as UNBUILT (`vault/programs/global-prefix-floor/LAPTOP_RESULTS.md:62`).

## Decision
`safeToForget(text, projection, obligation, durable)` in `policy.ts`, pure. A projection is applied only when ALL hold:
- **durable**: the full output was written AND read back with the same length and SHA-256. Else KEEP `not-durable`.
- **obligation known**: the open obligation text is known (main: the latest submitted prompt; successor: the capsule
  frontier, plus the latest prompt). None recorded -> UNKNOWN `no-obligation-text`, the whole output is sent (absent is not zero).
- **not named**: no omitted line contains a distinctive term of the obligation text (a token >= 4 chars carrying a digit,
  `.`, `_`, `-`, `/`, `\` or an inner capital: file names, ids, hashes). Named -> KEEP `obligation-named`.
- **proof survives**: every omitted PROTECTED line (FAIL*/ERROR/Traceback/Exception/fatal/panic; exit|rc|returncode|status
  = N; verdict= / verdict:; PASS|FAIL = N; N/N passed; a `[branch hash]` commit line) is hoisted into the projection,
  in order, under a marker. More than 20 such lines or 2,000 chars -> KEEP `proof-too-large`.
- otherwise FORGET; the receipt carries verdict, reason, hoisted count, named terms (<= 5).
The judgement runs in every non-unit projection (main and successor), shadow included (durable is then `null` in the receipt,
unchecked). Work Unit sessions keep today's behaviour: their measured receipts (B5) stay comparable.

Mode: new opt-in env `CCR_MAIN_PROJECT=1` lifts `project` to enforce in a main pane with no unit, no explicit
`modes.project`, and a compatible build (incompatible -> shadow). Unset = today's shadow. `main` off -> off.

Page-fault counter: a `Read` or `Grep` whose path lies under `<stateDir>/tool-results/` receipts
`{ev:"fault", kind:"projected", tool, path}`; the tool runs unchanged.

## Acceptance
- `policy.test.ts`: safeToForget driven to FORGET, KEEP (not-durable, obligation-named, proof-too-large) and UNKNOWN; a
  buried FAIL line survives in `out`; mainProjectMode poles (env 1 / unset / unit / successor / incompatible / modes.project).
  `claude plugin test mods/cpp-cognitive-runtime` green (was 29/0). Mutation: hoisting disabled -> the buried-FAIL test fails.
- Live (n>=3 per arm, fixed harness, interactive haiku panes): a command prints > 8,000 chars with one buried line that
  answers the question. Arm OFF (unset) vs arm ON (`CCR_MAIN_PROJECT=1`). Receipt file:
  `vault/programs/ctx-rent-x/phase5-safe-to-forget.json`.
- `done_gate.py`: CR-09 PASS when every ON run has a main-pane `project` receipt carrying `forget` (the judgement ran on the
  real path); CR-10 PASS when every ON run answered correctly AND >= 1 hoisted or named-KEEP receipt; CR-13 PASS when every
  ON run has `applied:true` and the ON arm's mean processed tokens < the OFF arm's. Missing file -> UNKNOWN. Each row driven
  PASS and not-PASS in `tools/test_done_gate.py`.
- Release via `tools/ccr_release.py` only after a green smoke from the same commit; otherwise rollback (HR-2).

## Never
- Never project a failed command's output (unchanged).
- Never make `CCR_MAIN_PROJECT` default-on without the Owner's call on the numbers (taken 2026-11-05, see Amendment A).
- Never change Work Unit projection behaviour in this change.
- Never treat an unknown obligation as "nothing named".

## Rollback
Set `CCR_MAIN_PROJECT=0` (after Amendment A; before it, unset). `python tools/ccr_release.py rollback` (or `off`). Code:
revert the commit; the judgement only ever sends MORE text than before, so a revert restores today's projection exactly.

## Amendment A -- default-on (Owner "y" 2026-11-05, conditional on n=10/arm; condition met)
Evidence (`vault/programs/ctx-rent-x/phase5-safe-to-forget-n10.json`, release 0.1.0-a2116a3b, host 2.1.318, FNNF x5):
ON applied 10/10 (safe-hoisted), 20/20 correct, 0 projected faults, processed mean ON 139,594 vs OFF 142,307 (-1.9%;
ranges disjoint: ON max 140,042 < OFF min 142,293). Fixture: one 18,735-char output per run.
- `mainProjectMode`: the lift applies unless `CCR_MAIN_PROJECT=0`. Every other guard is unchanged (unit, successor,
  explicit `modes.project`, `project` off, `main` off, incompatible build -> shadow).
- `register.ts`: an env that cannot be read keeps today's mode (treated as `0`); a failure never turns the lift on.
  The receipt's `mainProject` flag records that the lift actually changed the mode (`mode !== baseMode`), not the env value.
- Main loop only: a subagent's shell call (`e.agentId`) keeps its base mode, env on or not. The n=10 evidence measured
  no subagent projection, and `modes.subagent` does not gate this path (review M1, 2026-11-05).
- `phase5_smoke.py`: the OFF arm sets `CCR_MAIN_PROJECT=0` (unset would now be ON).
Acceptance: plugin tests (unset -> enforce, `0` -> today's mode, every guard pole kept), mutation (reverting to
`env !== '1'` turns the unset pole red), DONEGATE suite green, pp-code-reviewer, release, then HR-2 smoke FNNFFN with
the OFF arm on `0`: CR-09/10/13 PASS or rollback.
