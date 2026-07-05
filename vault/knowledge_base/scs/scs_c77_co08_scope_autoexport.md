# SCS C77 -- CO-08 scope-gate auto-activation (kclaude exports PP_PANE_SCOPE)

**Sealed:** 2026-07-05
**Type:** wiring (automation of an opt-in gate) -- the launcher hop that removes the per-launch manual export
**Slot check:** C75 Process-Hibernation, C76 CO-08 intent-gate live-path -> this is **C77**. Next free: C78.
**Siblings:** `[[scs_c76_co08_intent_gate]]` (the gate this activates), `[[parallel_mesh_scs_c65]]`/`[[parallel_mesh_scs_c66]]` (PM-02 scope logic).

---

## What C76 left, and the disproven premise this sprint corrected

C76 wired `prelaunch._gate` to route through PM-02's `scope_gated_admit` when
`PP_PANE_SCOPE` is declared. But that scope only *activated* when the Owner
exported the env by hand **every launch** -- an opt-in gate is effectively inert
in production (`[[T-SCOPE-GATE-OPT-IN-ANTIPATTERN-001]]`).

The Sprint premise -- "`kclaude.ps1` derives `PP_PANE_SCOPE` from a `pane_map`
given a cwd" -- was **disproven at PASO -1** (`[[PR-VERIFY-HANDOFF-PREMISES-001]]`):

- **No `pane_map` exists** (nor a cwd->scope map anywhere). The closest artifact,
  `vault/terminal_slots.json`, is keyed one-entry-per-cwd -> it structurally
  cannot hold N distinct scopes for N panes on one repo.
- **Scope is not derivable from cwd.** Scope is per-pane INTENT -- one repo -> many
  panes -> many *distinct* scopes, by design (that is the entire point of
  scope-gating). A pane's scope lives in the Owner's head; PM-02 is therefore
  **declaration**-driven (`--declare`), never derivation-driven.
- A **cold new pane has no sid** at launch (claude assigns it post-launch) and no
  prior intent -> nothing to recall.

Honoring the intent (automatic activation) while correcting the literal (no
pane_map; scope comes from declared intent) gave the two cases where automation
is genuinely possible.

## What shipped (the two honest auto-paths)

1. **New pane -- one-flag declaration.** `kclaude --scope "modules/foo,tools/bar"`
   exports `PP_PANE_SCOPE` before the fast prelaunch, so the CO-08 gate is
   scope-aware this launch. The Owner still names the scope (only they can for a
   cold pane) but in one flag, not an `$env:` incantation. The flag is stripped
   before passthrough (claude never sees it).
2. **Resume / restart / rehydrate -- automatic recall.** `kclaude` passes the
   resume sid to `prelaunch --sid`; `prelaunch._apply_launch_scope` recalls the
   pane's OWN declared intent for `(cwd, sid)` from the PM-02 registry and applies
   it, then echoes `launch_scope`/`launch_sid` which the launcher re-exports to
   the resumed claude. A scope declared **once** survives every restart -- the
   real "declare once, automatic thereafter" win.

Single source of truth: the enc/freshness/JSON logic lives only in Python
(`pm_02_intent.resolve_launch_scope`); PowerShell shells out, so `_enc`/the
120min window never drift into a second implementation.

## Failsafe preserved (never removed)

No `--scope` flag AND no fresh prior intent -> nothing exported -> `run_fast`'s
`_gate` sees no `PP_PANE_SCOPE` -> CO-08's blunt `SAME_REPO_CAP=1` applies
unchanged. Fail-open ABSOLUTE at every hop: a stale intent (>120min), a missing
registry, or any error resolves to "" (the failsafe direction) -- admission is
never widened on a bug.

## Done-gate (observed)

- `tools/test_parallel_mesh.py` **34/34** (+3 launch-scope gates:
  `V-SCOPE-RESOLVED-FROM-INTENT`, `V-SCOPE-EMPTY-WITHOUT-INTENT`,
  `V-SCOPE-FAILOPEN-STALE`). No regression: `test_cognitive_os_build` 68/68,
  `test_scope_a_activation` 7/7.
- `kclaude.ps1` parses clean (0 errors, PS `Parser::ParseFile`).
- E2E against the real launcher path:
  - `V-E2E-SCOPE-FLAG`: `PP_PANE_SCOPE` env -> `prelaunch --mode fast` emits it as
    `launch_scope`.
  - `V-E2E-RESUME-RECALL`: a declared `(cwd, sid)` intent -> `prelaunch --sid`
    emits `launch_scope`+`launch_sid`; synthetic intent retired after.

## Honest boundary -- Owner-side final hop (HR-001)

`prelaunch.py` loads from the skills repo path, so its half is live next launch.
The launcher edit (`kclaude.ps1`) is HR-001-gated for the live copy:

- **Copy-Item `tools/kclaude.ps1` -> `~/.claude/bin/kclaude.ps1`** (clean
  fast-forward; the live copy tracked the pre-edit canonical at 265 lines).
- `~/.claude/kclaude.ps1` (root) is a **legacy pre-W6 52-line stub** (only the
  /restart loop). Do NOT overwrite it with the W6 orchestrator; confirm the
  terminal profile invokes `bin/kclaude.ps1`, then consider deleting the stale
  root stub. Owner decision.

Until the Copy-Item, a pane still benefits per-launch via
`kclaude --scope "..."` (works today from the canonical path if invoked directly).

## Cross-references

- Code: `modules/parallel_mesh/pm_02_intent.py` (`resolve_launch_scope`),
  `modules/wrapper/prelaunch.py` (`_apply_launch_scope`, `run_fast(cwd, sid)`,
  `--sid`), `tools/kclaude.ps1` (`--scope`, sid recall, `Set-LaunchScopeEnv`)
- Tests: `tools/test_parallel_mesh.py` (34/34)
- Doctrine: `[[T-SCOPE-GATE-OPT-IN-ANTIPATTERN-001]]`,
  `[[T-INERT-ARCHITECTURE-TAX-002]]`, `[[PR-VERIFY-HANDOFF-PREMISES-001]]`
- Report: `vault/plans/kclaude-scope-export-2026-07-05.md`
