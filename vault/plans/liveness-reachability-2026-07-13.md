# Reachability Ledger + Recovery Verdict -- approved plan (backup)

Approved 2026-07-13. The inline plan in chat was the primary artifact; this is the record.
Execution Mode, not Ultra-Plan: the Reality Scan resolved the architectural question by
measurement (a correct parent existed), so there was no open design decision to justify a
3-5x planning cost. PR-MODE-SELECTION-001.

## Reality Scan (what already existed)

- `modules/session_resilience/` -- 11 modules, incl. `acceptance.py` (G4): a recovery
  arbiter scoring restored vs reference state -> RECOVERED / PARTIAL / FAILED, with an
  `acceptance_gate` that blocks a "complete" claim.
- `modules/liveness/liveness_ledger.py` (D1) -- the post-ship monitor, already carrying
  this mission's exact vocabulary: LIVE / WIRED-BUT-SILENT / DRIFTED / ORPHANED / UNKNOWN.
- `cpc_os` (snapshot, topology_reconcile, recovery, restart), `lazarus_*`,
  `restore_panes.ps1`, `ram_guard`, `context_monitor`.

Every listed symptom already had an owner. Nothing was missing. EXTEND_EXISTING_PARENT.

## The gap (one sentence)

The Liveness Ledger had no DISCOVERY PRODUCER: its registry was eight hand-written rows,
so coverage depended on human memory and the absence of a probe read as approval. The
recovery arbiter was never declared, therefore never audited, therefore never missed --
and had never judged a single real recovery. Every symptom is downstream of that.

## Executed

- **M1** `modules/liveness/reachability.py` -- enumerates every module and proves
  reachability from the surfaces the harness invokes. Four scanner defects found by
  measurement, each of which had manufactured corpses: package-granularity (would have
  declared the founding bug healthy), repo-only seeding (~/.claude is the LIVE install),
  two-segment paths (nested subpackages collapsed), and runtime plugin loaders.
- **M2** ledger auto-enrolment -- registry rows 8 -> 285; declaring is now optional.
- **M3** the measurement -- 276 modules, 120 reachable, 156 orphans, frozen BY NAME.
- **M4** the standard -- Liveness Standard in CLAUDE.md; a NEW unreachable module fails.
- **M5** the proof case -- `tools/recovery_verdict.py` + `/recovery-verdict` + `/liveness`.
  The arbiter judges a real restore; `acceptance` flipped ORPHAN -> REACHABLE; debt fell
  by name 156 -> 150.

## Gates

test_reachability 7/7 (incl. the negative pole), test_recovery_verdict 5/5,
test_strategic_gaps + test_session_resilience(+_build) green, 3x hermetic. Live run on this
host: RECOVERED (windows 7/7, terminals 7/7, conversations 8/8).

## Known limits (stated, not hidden)

- The verdict witnesses windows / terminals / conversations. Editor tabs, tab order, focus
  and scroll are NOT observable from pane_map and are excluded from the denominator, never
  scored as passing.
- 150 modules remain unreachable. They are named in
  `vault/liveness/reachability_registry.json`. That list is debt, not health.
- Reachability is STATIC: it proves a live surface REFERENCES a module, not that the
  surface ran. The ledger's other probes (co12-signal, file-mtime, hash-drift) cover the
  did-it-actually-run axis; the two are complementary and neither replaces the other.
