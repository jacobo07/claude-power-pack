# Scope A — Activate the Inert — Execution Report (2026-07-03)

**Mode:** EXECUTION · Scope A (activate-the-inert, zero new datasets) · approved after STOP #1.
**Reality Contract:** not activated until PM-03 publishes a real finding in an active session,
the GK-12 advisory reaches the model (not just a log), and CO-08 uses the PM-02 intent-gate —
all three verified empirically with real data.

---

## Headline — the sprint's premise was outdated by the same-day C70 sprint

The plan assumed three *inert* systems needing wiring. Empirical PASO -1 found that **two of the
three were already activated** by the C70 sprint earlier the same day (2026-07-03), and the
dispatcher has **zero drift**. What remained was: (a) prove the activation empirically, (b) close
one genuine Owner-side seam (CO-08 wrapper routing), (c) add a durable regression gate. No wiring
code was rebuilt — that would duplicate what C70 shipped.

| System | Plan assumed | Empirical reality | This sprint |
|---|---|---|---|
| **PM-03 Findings Bus** | inert, needs SessionStart+Stop wiring | **consume already wired** — `session_start_hub.js` Hook 13 `hookFindingsBusDigest` (L592–661) reads the bus JSONL directly and `main()` injects it (L697–702). Bus already **seeded with 3 real findings** by sid `c70-wire` (14:44). | Published a 4th real finding from THIS session + proved the digest round-trips (consume reads publish). |
| **GK-12 / dispatcher** | inert, advisory silenced, drift | **live, no drift** — `hook-dispatcher.js` repo==live (SHA `4C5336E46CDE`). additionalContext fix already committed `026573e`. **Advisory reached the model this session** (a Grep call returned the `Graph-First (GK-12…)` hook line — 698 coordinates). | Verified live; no change needed. |
| **CO-08 scheduler** | blunt cap, needs recalibration | **scope-gate already built + tested** — `scheduler.decide(declared, hot_scopes)` + `pm_02_intent.scope_gated_admit` (PM-02, 26/26). Inert only at the **wrapper**: `prelaunch.py::_gate` (L112–116) calls blunt `scheduler.admit()`. | Proved the scope-gate end-to-end (4 scenarios); documented the one Owner-side seam below. |

## Empirical evidence (real data, this session)

- **PM-03 round-trip:** `publish_session_findings(REPO, …)` → bus now holds 4 findings; the
  `BusIndex.digest` (what Hook 13 mirrors) reads the fresh topic back. Live bus:
  `~/.claude/state/parallel_mesh/findings_bus_C--Users-User--claude-skills-claude-power-pack.jsonl`.
- **CO-08 scope-gate (4 scenarios):** disjoint declared scopes → **proceed**; undeclared 2nd
  same-repo pane → **refuse** (blunt failsafe); overlapping declared scope → **refuse**;
  `scope_gated_admit(None)` == sealed blunt admit. All PASS.
- **GK-12:** the two Grep calls this session each returned the live Graph-First advisory line.

Durable regression gate: `tools/test_scope_a_activation.py` — **7/7 ×3 hermetic** (PM-03 half runs
in a `TemporaryDirectory`, never the live bus; CO-08 half is pure). Baseline unaffected:
`test_parallel_mesh` 26/26, `test_cognitive_os_build` 68/68, `test_cognitive_leak_taxonomy` 9/9.

## Pre-existing FAIL found + fixed (RCA, not swept)

Running the baseline surfaced `V-SCS-NO-COLLISION` FAIL in `test_cognitive_leak_taxonomy.py`
(8/9) — **pre-existing at HEAD, unrelated to Scope A** (git confirmed zero C69/graphify/scs files
in my working tree). Root cause: the gate's `graphify_still_c69 = any("SCS C69" in text)` fired on
`graphify_live_scs_c72.md:23` — the sentence *"SCS C69→C71 collision fix: `4d7f727`"*, which
**documents** the fix rather than re-sealing C69. FP-hardened the gate (same discipline as C69's
own P5 clause-extraction): a file "still seals C69" only if a line names C69 **without** C71.
Now 9/9.

## The one genuine remaining seam — Owner-side (HR-001)

The CO-08 scope-gate is built, tested, and usable **today** by any pane via
`python -m modules.parallel_mesh.pm_02_intent --declare --scope …`. It is not reached by the
launch wrapper because `prelaunch.py::_gate` calls the blunt cap. Activating it at the wrapper is a
**load-bearing launch-config edit** → not auto-applied. Exact change for the Owner:

```
# modules/wrapper/prelaunch.py  _gate(cwd)  (currently L112–116)
# BEFORE:  from modules.cognitive_os.scheduler import admit
#          v = admit(cwd, is_new=True)
# AFTER (route through the scope-gate WHEN this cwd has a fresh declared intent;
#        undeclared -> unchanged blunt admit, the sealed failsafe):
#   from modules.parallel_mesh.pm_02_intent import PaneIntentRegistry, scope_gated_admit
#   reg = PaneIntentRegistry()
#   scopes = reg.scopes_by_sid(cwd)          # {sid: scope} for fresh intents
#   if scopes:                                # at least one incumbent declared
#       v = scope_gated_admit(cwd, sid="<launching-sid or ''>", declared_scope=None)
#       # NOTE: a launching pane has not declared yet -> declared_scope stays None
#       # so the incumbent's scopes only INFORM; real relaxation happens when the
#       # AGENT calls scope_gated_admit(declared_scope=[...]) mid-session.
#   else:
#       v = admit(cwd, is_new=True)
```

**Honest limit:** the primary activation of CO-08 recalibration is the **declare-intent habit**
(the agent declares scope at session start), not the wrapper edit — at prelaunch time no intent
exists yet. The wrapper edit only lets an incumbent's declared scope soften the *warning*. The
full value is realized by panes calling `scope_gated_admit(declared_scope=[…])` when contending
for a repo. Documented as doctrine in SCS C73.

## Done-gate

- ✅ PM-03: 4th real finding published in an active session; digest round-trips.
- ✅ GK-12: advisory observed in the model's own tool context this session (no drift).
- ✅ CO-08: scope-gate proven (4 scenarios); wrapper seam documented (Owner-side).
- ✅ Tests: `test_scope_a_activation` 7/7 ×3 hermetic; baseline 26/26 + 68/68 + 9/9.
- ✅ Pre-existing V-SCS-NO-COLLISION FP fixed (RCA, not waved).
- ✅ SCS C73 sealed. REMOTE_DELTA target 0 0.
