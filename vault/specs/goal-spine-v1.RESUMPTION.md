# Goal Spine v1 — RESUMPTION

Read this and continue with zero prior context. Update after every sealed unit.

## 1. Identity
Build the durable Goal Spine: a Goal record + deterministic reconciler that owns a
Goal to convergence across bounded execution epochs, REUSING GSD X mission code
(contract, obligation, store, closure), `/cpp-gsd-long`, `owner_queue`, and the
project's own verifier. Spec: `vault/specs/goal-spine-v1.md`. Plan of record
(Owner-approved 2026-09-22): `~/.claude/plans/shimmying-conjuring-hanrahan.md`.

## 2. Where the work lives — read state HERE, never from a shared checkout
| Repo | Worktree | Branch | Base |
|---|---|---|---|
| Power Pack | `C:\Users\User\Apps\pp-goal-spine` | `goal-spine/v1` | `main` @ `6b3092b` |
| KobiiCraft | `...\KobiiCraft Workspace\kc-goal-spine-wt` | `kseip/goal-spine-v1` | `330cea16` |

The shared PP checkout (`~/.claude/skills/claude-power-pack`, branch
`feature/knowledge-acquisition`) belongs to ANOTHER live writer and must not be
written. UCR-CIF is a separate live programme in `C:\Users\User\Apps\pp-ucr-cif`
(`ucr-cif/construction`) — never written by this mission.

**Run `git -C <worktree> log --oneline main..HEAD` rather than trusting any count here.**

## 3. Sealed (PP `goal-spine/v1`), each with its own gate
- `141d1ae` G2 — GSD X goal-scoped obligation store + fix: `project()` crashed
  (`o.id`) on every ACCEPTED obligation carrying a proof. goal_scope 5/5.
- `7180d90` G1 — Goal record + store (single writer, corrupt raises, CONVERGED not
  requestable, BLOCKED must be external).
- `8b44d10` G3 — convergence = GSD X closure, recomputed at the point of effect.
- `2985e10` G4 — epochs; a worker run is STARTED only by the session that claimed it.
- `f692404` — Goal identity = intent IN A PLACE (was intent alone → cross-repo collision).
- `a1a682b` G6 — receipts through GSD X `closure.satisfy`, from the named gate only.

## 4. In flight at this write
- G5 `modules/goal_spine/reconciler.py` + `tools/test_goal_spine_reconciler.py`
  (18/18), NOT yet committed. Independent mutation probe and an independent
  adversarial audit were running against it. **The probe rewrites the module on
  disk per mutant** — do not edit reconciler.py while a probe runs, and discard any
  audit finding that quotes code absent from the restored file.

## 5. Owner packets queued (surfaced at SessionStart via owner_queue)
`q-28d106ac15` P-1 UCR-CIF reaper env var · `q-525be41a00` P-2 open worker pane at
kc-goal-spine-wt · `q-a344413da7` P-3 Goal milestones inside the worktree branch.

## 6. Next three actions
1. Close G5: read the probe + audit results, fix real gaps, commit.
2. Providers P1 `verify.py` (gate registry: gate id → runnable check), P2 `codex.py`
   (read-only, guarded), P3 `gsd_long.py` (prepare-only; emits the claim instruction).
3. KC adapters K1-K5 in `kc-goal-spine-wt`, then Certification C1 (Goal 1: KSEIP
   wiring) and C3 (Goal 2: revive GEX44 job runner).

## 7. Findings recorded so far (for UKDL at C5)
B1 INTENT.txt reader with no producer · B3 stale shared-checkout read (75 commits) ·
B4 agent-solo-guard contract/bound guards contradict · B5 GSD X milestone key
mismatch (not fixed, off critical path) · B11 GSD X `o.id` crash (fixed `141d1ae`) ·
B12 GSD X `evaluate_transition` never checks gate identity (reported, enforced at the
spine boundary) · identity collision (fixed `f692404`) · convergence trusted a
mutable verdict flag (fixed `8b44d10`) · epoch-binding `or`→`and` hole (fixed
`a1a682b`) · reconciler counted never-started epochs as tries (fixed in G5) ·
my own instruments: TypeError-as-refusal gate, crash-scored-as-survivor harness,
producer/consumer batch, looser test fixture, probe-as-concurrent-writer.

## 8. Start instruction
`git -C C:\Users\User\Apps\pp-goal-spine status` then run the six suites:
`tools/test_goal_spine{,_convergence,_epoch,_receipt,_reconciler}.py`,
`tools/test_gsd_x_mission_goal_scope.py`, `tools/test_gsd_x_mission.py`. All green
before touching anything.
