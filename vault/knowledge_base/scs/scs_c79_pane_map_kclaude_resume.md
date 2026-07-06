# SCS C79 — pane_map + PP Sessions resume uses kclaude (wrapper active on every resume)

**Sealed:** 2026-07-06
**Type:** doctrine + surgical fix (one string per generator)
**Slot check:** C77 CO-08 scope-autoexport, C78 CDIO → this is **C79**. Next free: C80.
**Siblings:** `[[wrapper_kclaude_scs_c48]]` (the kclaude wrapper this keeps active), `[[no_duplicate_panes_scs_c50]]` (the cold-start restorer whose fallback this flips), `[[scs_c77_co08_scope_autoexport]]` (CO-08 the wrapper carries).
**UKDL:** `HR-RESTART-VIA-KCLAUDE-001` C79 addendum (extends the rule from /restart to the resume surface).

---

## The gap

`kclaude` is the wrapper that activates the Cognitive OS at launch: CO-00 (60%
context ceiling), CO-08 (parallel cap), and W1-W5. A session resumed with bare
`claude --resume` skips the wrapper entirely — the Cognitive OS is INERT in that
session until the Owner manually closes and reopens under kclaude.

The pane_map ecosystem generated bare `claude --resume`:

- `tools/build_pane_map.ps1` wrote `resumeCmd = "claude --resume <sid>"` into
  `pane_map.json` — the **single source of truth** the PP Sessions extension reads.
- `extension/src/restore_guard.js` + `extension/src/extension.js` carried
  `claude --resume` fallbacks.

Because the extension (Resume button, copy-to-clipboard, cold-start auto-launch)
reads `resumeCmd` from the map rather than hardcoding it, flipping the generator
propagates to the entire extension surface automatically.

## The fix (Tier-1, this seal)

One string per generator, no logic touched:

| File | Change |
|---|---|
| `tools/build_pane_map.ps1:186` | `resumeCmd = "kclaude --resume $sid"` |
| `extension/src/restore_guard.js:44` | fallback `"kclaude --resume " + sid` |
| `extension/src/extension.js:120` | degenerate fallback `"kclaude"` |

Tests updated to assert the new contract: `test_pane_map.py`
(`V-PANE-MAP-USES-KCLAUDE`), `verify_session_ext.py`, `test_restore_guard.js`
(`V-RG-RESUMECMD-FALLBACK`).

## Done-gate (observed)

- `pane_map.md` regenerated: 49/49 panes carry `kclaude --resume`; a
  word-boundary grep for bare `claude --resume` → **0**.
- `test_restore_guard.js` RG_PASS=10/10; `test_pane_map.py` 8/8;
  `verify_session_ext.py` 7/7 (3 PEND are pre-existing post-reload Owner-observed).

## Note on the .vsix

The installed extension reads `resumeCmd` from `pane_map.json` at runtime, so the
Resume button already emits `kclaude` from the regenerated map — no rebuild
required for the primary path. The `.vsix` only needs rebuilding for the two
fallback code paths (which fire only when the map lacks a `resumeCmd`, i.e.
never in practice).

## Tier-2 PENDING (documented, not done — distinct subsystem)

`restore_panes.ps1` has no command literal; its command is produced upstream by
`modules/cpc_os/snapshot.py:166`, whose `resume` field feeds `recovery.py`,
`auto_reset_orchestrator.py`, `vscode_autorun.py`, and `ram_guard.py`.
Additionally `modules/session-continuity/restore.ps1` literally runs
`& claude --resume`, and `session_resilience/resume_identity.py` +
`tools/lazarus_revive_all.py` print bare `claude --resume`. Flipping
`snapshot.py` cascades into `test_cpc_snapshot.py`; the session-continuity path
has its own test suite. This is a multi-subsystem refactor the plan's "una línea
en cada lugar" under-scoped — recommend a scoped follow-up sweep.
