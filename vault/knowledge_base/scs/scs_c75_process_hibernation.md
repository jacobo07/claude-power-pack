# SCS C75 — Transparent Process Hibernation (FASE A + loop-boundedness advisory)

**Sealed:** 2026-07-04
**Type:** runtime system (code) — process-lifecycle economy + wall-clock safety net
**Slot check:** C71/C72 = Graphify, C73 = Activate-Before-Build, C74 = CO-NextGen → this
is **C75**. The Sprint-2 prompt asked for a "SCS C73 addendum"; that is a disproven
premise — C73 is Activate-Before-Build, unrelated to hibernation, and no hibernation SCS
existed. Audit-disproves-premise: intent honored (seal the hibernation work), literal
corrected (a new C75 slot, not a C73 addendum). **Siblings:**
`[[scs_c74_co_nextgen]]` (CO-12 corpus-level loop-boundedness), `[[scs_c70_cognitive_leak_taxonomy]]`.

---

## What it is

Transparent Process Hibernation frees RAM by killing **idle** `claude.exe` panes and
transparently rehydrating them on the next keystroke via the `kclaude.ps1` park-and-resume
wrapper. FASE A was built + tested 2026-07-03 (measured baseline: 56 panes = 12.2 GB;
re-measured 2026-07-04: 62 panes = 13.42 GB). Per CO-10 it is a **WRAPPER-tier** economy —
the only tier that can act on the process lifecycle. Full design + install: the plan doc
`vault/plans/process-hibernation-fase-a.md`; Owner-side runbook: `vault/patches/hibernation/INSTALL.md`.

**Fail-safe core:** the pure `decide()` keeps a pane on ANY never-hibernate invariant
(foreground / /loop / hot / idle-unknown / no-anchor / no-sid / non-wakeable). Worst case
is a MISSED ECONOMY, never a lost session. The active pane is protected structurally — it
is never idle, so it never clears the `idle>15min` gate.

## Sprint 2 — loop-boundedness advisory (this seal's new material)

A SECOND, purely-advisory axis added to the governor (`loop_advisory`), born from the
Kickbacks incident: a session hung ~10h with no detection (2026-07-04). It makes a
wall-clock stall/unbounded VISIBLE without ever touching the kill path:

- **stalled** (WARN) — no new output in ≥30min AND session ≥1h total → probably hung;
  suggests `/kclear` or closing the pane.
- **unbounded** (NOTE) — session active ≥2h without a `/compact` reset → accumulating
  context, possibly hung; informational, fine to ignore if work is real+continuous.

**Guarantees (all gate-proven):**
- **Advisory only** — never changes `decide()`'s verdict, never kills. Orthogonal:
  `V-GOVERNOR-ACTIVE-NOT-HIBERNATED` (a foreground pane is kept AND still gets its NOTE).
- **Fail-open ABSOLUTE** — unmeasurable session age → `None` (silence, never a false
  positive): `V-LOOP-BOUNDEDNESS-FAILOPEN`.
- **Silent on real work** — active pane (idle 2min) → no advisory + kept:
  `V-ACTIVE-SILENT`.
- Wired into the exact daemon command: `format_plan` prints the advisories, so the DRY
  `run_hibernation.py --from-scan …` the Owner schedules already surfaces them.
- Env-tunable (`PP_GOV_UNBOUNDED_MIN` / `PP_GOV_STALLED_IDLE_MIN` / `PP_GOV_STALLED_SESSION_MIN`).

Relationship to CO-12: `co_12_telemetry.loop_boundedness` is **retrospective** over the
whole transcript corpus (625 sessions → 194 unbounded); this governor advisory is
**in-flight** on the panes alive right now. Two honest views of the same axis.

## Done-gate (observed)

`tools/test_hibernation.py` — **28/28 ×3 hermetic** (21 FASE-A gates + 7 new Sprint-2
advisory gates: V-UNBOUNDED-ADVISORY, V-STALLED-ADVISORY, V-ACTIVE-SILENT,
V-LOOP-BOUNDEDNESS-FAILOPEN, V-GOVERNOR-ACTIVE-NOT-HIBERNATED, V-SESSION-AGE-READER,
V-ADVISORY-IN-PLAN). Changes are additive (a defaulted `PaneProc.session_age_min` field +
new functions), so `run_hibernation` / `hibernate_runner` / `hibernate_one` are untouched
and stay green.

## Honest boundary — what is Owner-side (NOT done in auto-mode)

Per HR-001, auto-mode cannot write `~/.claude/` global config, register Scheduled Tasks,
or kill live panes. The following are documented in `INSTALL.md`, not executed:

- **Scheduled Task `PP-Hibernation`** — verified **NOT REGISTERED** (the handoff's "DRY
  pending LIVE" was a disproven premise; it never existed in any state). Owner registers it
  in DRY, reads a day of plans, then promotes to LIVE (`--live`).
- **Wrapper convergence** — the `bin\kclaude.ps1` / `kclaude.cmd` / `kclaude.bat` patches
  (23 ps1 + 33 bat panes). Owner-applied, each reversible via `.bak`.
- **Empirical RAM-freed + rehydrate-under-5s** — runtime-asserted (INSTALL §4), NOT
  unit-faked (Reality Contract: no RAM/timing theater; the mockable logic is the 28 gates).
- **Formal HR sealing** — `HR-STALLED-SESSION-ADVISORY-001` + `[[T-UNBOUNDED-SESSION-001]]`
  live hand-maintained in `ukdl-universal.md`; promoting HR into the generator-owned
  `HARD_RULES.md` (digest-keyed, regenerates the inline mirror) is an Owner
  `tools/bug_to_hardrule.py` step.

## Cross-references

- Code: `modules/cognitive_os/process_governor.py` (`loop_advisory`, `session_start_age_min`)
- Tests: `tools/test_hibernation.py` (28/28 ×3)
- Runbook: `vault/patches/hibernation/INSTALL.md` · Design: `vault/plans/process-hibernation-fase-a.md`
- Doctrine: `HR-STALLED-SESSION-ADVISORY-001`, `[[T-UNBOUNDED-SESSION-001]]`
- Sibling axis: `[[scs_c74_co_nextgen]]` (CO-12), `modules/cognitive_os/co_12_telemetry.py`
