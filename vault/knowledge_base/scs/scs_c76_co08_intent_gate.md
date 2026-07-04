# SCS C76 — CO-08 Intent-Gate reaches the live launch path

**Sealed:** 2026-07-04
**Type:** wiring (activation of built logic) — the live-path hop for PM-02's scope-gate
**Slot check:** C74 CO-NextGen, C75 Process-Hibernation → this is **C76**. Next free: C77.
**Siblings:** `[[parallel_mesh_scs_c65]]` / `[[parallel_mesh_scs_c66]]` (PM-02 scope-gate
logic), `[[scs_c75_process_hibernation]]` (the PM-03 publish-wiring the day before).

---

## What was already true (verified, not rebuilt)

The CO-08 intent-gate **logic** was built and unit-green (C65 architecture, C66 live-wired at
the module level): `scheduler.decide(hot, cwd, *, declared=None, hot_scopes=None)` scope-gates
the same-repo dimension when a scope is declared and falls back to the blunt `SAME_REPO_CAP=1`
when not; `pm_02_intent.scope_gated_admit` + `PaneIntentRegistry` (declare/retire/active/
scopes_by_sid) + a full CLI wire it. The V-PM02-* gates already prove declared-disjoint→proceed,
collision→refuse, undeclared→blunt cap.

The Sprint prompt's premise ("SAME_REPO_CAP blunt pendiente de recalibración … nunca
ejecutado") was **disproven** — the recalibration ran (C65/C66). Two more disproven premises
this sprint: PM-06 does not exist (parallel mesh is PM-01..05); CO-08 is `scheduler.py`, not
`co_08_parallel_cap.py`. All caught by PASO -1 tool probes (`[[PR-VERIFY-HANDOFF-PREMISES-001]]`).

## The real gap this seal closes (the inert-architecture tax)

The **live launch gate** — `modules/wrapper/prelaunch._gate`, the one field the kclaude
orchestrator may act on to block a new pane — called the blunt `scheduler.admit()` and never
passed `declared`. So the intent-gate, though built, was **unreachable at launch**: every live
pane hit the blunt cap regardless of declared intent (`[[T-INERT-ARCHITECTURE-TAX-002]]`).

**Fix (this seal):** `prelaunch._gate` is now intent-aware. When a launch declares a scope via
the `PP_PANE_SCOPE` env (comma-separated path tokens; `PP_PANE_SID` excludes the pane's own
pre-declared intent), the same-repo dimension is scope-gated via `scope_gated_admit`; with no
declared scope it uses the blunt `admit()` **unchanged** — the sealed failsafe, zero regression
for existing launches. Fail-open ABSOLUTE: any error → the blunt cap. `_gate` gained
`now`/`proj_base`/`gather_fn`/`registry` injection so the live entry point is hermetically
testable (not just the pure core).

## Done-gate (observed)

`tools/test_parallel_mesh.py` **31/31 ×3 hermetic** (+4 new CO-08 gates driving the LIVE
`prelaunch._gate`, not just `decide`):
- `V-CO08-DIFFERENT-REPO-FREE` — a hot pane on a different repo never counts toward this repo's cap.
- `V-CO08-NOINTENT-CAPPED` — undeclared launch + 1 same-repo hot → blunt `SAME_REPO_CAP` refuses.
- `V-CO08-INTENT-ALLOWED` — declared disjoint scope → live gate admits a 2nd same-repo pane.
- `V-CO08-INTENT-COLLISION` — declared overlapping scope → live gate refuses.

No regression: `test_cognitive_os_build` 68/68, `test_scope_a_activation` 7/7, `prelaunch`
imports clean (`run`/`run_fast` call `_gate(cwd)` with defaults → identical prior behavior).

## Honest boundary — Owner-side final hop

`prelaunch.py` is loaded from the skills repo path by `kclaude.ps1`, so this wiring is live on
the next launch. But it only *activates* the scope-gate when the launcher sets `PP_PANE_SCOPE`.
Making that automatic is the Owner-side wrapper edit (HR-001): have `kclaude.ps1` export
`PP_PANE_SCOPE`/`PP_PANE_SID` from the pane's declared intent before calling `prelaunch`. Until
then a pane opts in per-launch with `$env:PP_PANE_SCOPE="modules/x.py"`, or declares via
`python modules/parallel_mesh/pm_02_intent.py --sid <sid> --declare --scope …` first.
`SAME_REPO_CAP=1` remains the failsafe for every undeclared launch — never removed, only bypassed by a proven-disjoint declared scope.

## Cross-references

- Code: `modules/wrapper/prelaunch.py` (`_gate`), `modules/cognitive_os/scheduler.py`
  (`decide`), `modules/parallel_mesh/pm_02_intent.py` (`scope_gated_admit`)
- Tests: `tools/test_parallel_mesh.py` (31/31 ×3)
- Doctrine: `[[T-INERT-ARCHITECTURE-TAX-002]]`, `[[PR-VERIFY-HANDOFF-PREMISES-001]]`
- Report: `vault/plans/pm06-co08-wire-2026-07-04.md`
