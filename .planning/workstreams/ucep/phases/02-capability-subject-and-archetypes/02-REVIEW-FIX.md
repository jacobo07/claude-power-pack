---
phase: 02
review: 02-REVIEW.md
fixed: 1
deferred: 3
info_untouched: 7
fixed_by: orchestrator (epoch 3), inline
---

# Phase 2 review fixes

## Fixed

**CR-01 (critical): a partial manifest read could produce ABSENT.** `trait_scan._entitle` checked only
`manifests_parsed == 0`, so a repo with one good manifest and one unreadable or oversized one read
`ABSENT, OBSERVED "in a complete walk"` for dependency-class traits.

- Fix: new precedence step 6 in `_entitle`. A dependency-class trait with any entry in
  `walk["manifest_errors"]` reads `UNJUDGED manifest-unparsed`. The new cause is added to
  `archetypes.UNJUDGED_CAUSES`.
- RED, against the unchanged module: `FAIL V-TSCAN-PARTIAL-MANIFEST-UNJUDGED ... persistent=ABSENT/no
  persistent evidence in a complete walk (ecosystems seen: pip) parsed=1 errors=['package.json']`,
  `CAPABILITY_TRAIT_SCAN_PASS=27/28`.
- GREEN: `CAPABILITY_TRAIT_SCAN_PASS=28/28`. In this gate's control, the same repo without the
  oversized manifest still reads ABSENT. `CAPABILITY_ARCHETYPES_PASS=59/59`, and
  `V-ARCH-CAUSES-REACHABLE` now reaches all 10 causes, including `manifest-unparsed`, through its own
  fixture (one parsed `package.json`, plus an unparsable `requirements.txt` and `pyproject.toml`).
- Liveness: the offender set is unchanged (63 standing, the same set as `02-liveness-before.json`). No
  module was added.

## Deferred (each fails safe; recorded in STATE.md as Owner review items)

- **WR-01: intent false positives.** A generic verb-object pair plus a PRESENT anchor reads
  REQUIRED. Raising intent precision changes the ceiling design that Phase 2 locked, so it belongs to a
  design pass, not a review patch. When it errs, it errs toward more obligations, never fewer.
- **WR-02: worktree roots read NO_CACHE.** The producer keys the main repo; the reader keys the
  worktree. To fix it, someone must decide which repo identity a worktree's cache belongs to, and
  whether evidence may be re-stat'ed against a different tree. It fails safe: UNJUDGED, never ABSENT.
- **WR-03: name-only evidence turns the cache STALE mid-mission.** `V-ARCH-STALE-EVIDENCE-FILE` pins
  this as intended. Changing it would flip a gate, and that needs a decision, not a fix. It also fails
  safe.

## Info items

IN-01..IN-07 are left as written in 02-REVIEW.md. None changes a verdict a gate relies on.
