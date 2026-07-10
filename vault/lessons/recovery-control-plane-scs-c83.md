# Workspace Recovery Control Plane -- Execution Mode seal (SCS C83)

Sealed 2026-07-10. Mode decided by evidence after a blocking Reality Scan:
**Execution Mode**, not a new Control Plane. Every candidate Control-Plane
component failed the anti-duplication kill switch -- coordination, verification,
and host-checking responsibilities already had owners; they were merely dark
(orphaned). The gaps were wiring + one host-coupling arg + three root-cause bugs.

## Reality-Scan verdict (component inventory highlights)

- `state/pane_map.json` (built by `build_pane_map.ps1`) IS the manifest-as-truth
  the "Hypervisor" premise asked to build -- refreshed on a schedule, atomic,
  4-tier, Cursor reads it and does not generate it. **Do not duplicate.**
- `multi_window.py` (G2) already owns cross-window coordination
  (`restoration_order`, focus arbitration, conversation locks) -- orphaned
  (0 runtime callers), not absent.
- `acceptance.py` (G4) + `reentry.py` (G5) already compute a recovery accuracy
  verdict (RECOVERED/PARTIAL/FAILED + fidelity) -- orphaned.
- `integration.py` (I1/I2) is the intended wiring hub but self-documents as
  "Owner-side registration step ... SCS C56" -- 0 callers (proof by absence
  across every `.js/.json/.ps1`).

## The three root causes (exact)

1. **"1 pane per repo."** The automatic restore path (the `.vscode/tasks.json`
   Cursor auto-runs on folderOpen) is written by the 15-min `snapshot_auto_writer`
   from the legacy `session_snapshot.json` (under-records repos+sids) WITHOUT
   `--no-truncate` (caps each repo to its live tab count). The all-panes path
   (`restore_panes.ps1 -AutoRun` -> `vscode_autorun --no-truncate`) was manual.
2. **"shutdown != restart."** A restart preserves Cursor's pty host (terminals
   reconnect + the in-pane `kclaude` loop resumes the exact sid). A reboot
   destroys it -> cold start with no complete tasks.json to drive it.
3. **"only works in PP."** Host-coupling: the SessionStart hub regenerated only
   `cwds=[current cwd]`, so a repo only got a fresh all-panes tasks.json when a
   session ran in it; PP is where sessions run most.

## The fix (Sprint 0 -- wiring, no new component)

Point the existing auto-writer at the CORRECTED `pane_map.json` with no
truncation, via ONE shared adapter consumed by both PowerShell callers:

- `modules/cpc_os/vscode_autorun.py`: new `generate_from_pane_map()` +
  `_panes_from_pane_map()` (pane_map schema -> internal pane dict) + `--pane-map`
  CLI. Always `target_count=None` (never truncates). Lives in one place so
  `snapshot_auto_writer.ps1` and `restore_panes.ps1` do not each re-implement the
  pane_map->task transform.
- `tools/snapshot_auto_writer.ps1`: each cycle prefers `--pane-map` (all repos,
  all panes); fail-open fallback to the legacy snapshot if the map is missing.

Empirical proof (dry-run against live `pane_map.json`): 8 distinct repos each get
their full pane set as tasks -- PP=22, TUA-X=23, KobiiCraft=8, InfinityOps=7, ...
-- not 1 per repo.

## Sprint 1 -- graceful beacon (closes "every shutdown reads ungraceful")

`hooks/session_end_graceful_beacon.js` writes `power_beacon.write_graceful_exit`
on a clean close so the last word on disk is graceful. Round-trip proven: no
graceful -> `ungraceful-shutdown`; after graceful -> `graceful-reopen`; live
terminals -> `reload`. Registration is Owner-gated (HR-001): mirror the file into
`~/.claude/hooks/` and add the SessionEnd entry (documented in the hook header).

## Owner-gated follow-ups (orphan activation, HR-001)

Surfacing the Recovery Accuracy Score requires calling `reentry.record_reentry` /
`integration.on_session_start` at startup from a live `~/.claude` hook -- a
registration the agent cannot self-perform in auto-mode. The code is ready; the
wire is an Owner step.

## Hard Rules sealed

### HR-CONTROL-PLANE-EXCLUSIVE-RESP-001
TRIGGER: About to add a new component to the recovery/session-resilience family.
ACCION: STOP. It must demonstrate an EXCLUSIVE responsibility with a verifiable
test (a V-gate that fails if an existing component already covers it). If the
responsibility can be absorbed into an existing component (pane_map manifest, G2
multi_window coordination, G4/G5 acceptance, host bind_workspace), absorb it.
Never create a component by convention. EXCEPCION: none.
ORIGEN: the "Workspace Recovery Hypervisor" prompt proposed 5 new layers that a
Reality Scan showed already existed as orphaned code.

### T-RECOVERY-HOST-COUPLING-001
A recovery that "works in one repo but not others" is probably host-coupling
(repo-local tasks.json, per-terminal profile, current-cwd-only regeneration), not
a missing architectural layer. Verify the automatic path's repo scope and the
manifest source BEFORE assuming a new component is needed.

### PR-RECOVERY-MANIFEST-SOURCE-001
The automatic restore artifact (tasks.json) MUST derive from the corrected
`pane_map.json` (disk-truth, all repos, all panes), never the legacy
`session_snapshot.json`, and never with a live-tab-count truncation on the
recovery path. Truncation belongs only to the live-reconcile path, not recovery.

## Tests

`tools/test_recovery_control_plane.py` -- 6 V-gates x3 hermetic
(V-PANE-MAP-ADAPTER, V-ALL-PANES, V-MULTICORE-RECOVERY, V-SHUTDOWN-RESTART-PARITY,
V-NO-DUPLICATE-MANIFEST, V-COMPONENT-EXCLUSIVE-RESP). Complements
`tools/test_restore_all_panes.py` (build_cpc_tasks / snapshot layer) -- different
layer, no overlapping gate.
