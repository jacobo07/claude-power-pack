# SCS C44 -- Auto-Documentation-by-default (BL-ADS-001)

Sealed 2026-06-09. ULTRA 7-phase build (Q&A → audit → fix → exec → verify).

## Doctrine

Every module built with the PP can carry living documentation with **zero
manual Owner action**:

- A new module (a package dir gaining `__init__.py`/`index.{js,ts}`/`mod.rs`,
  or a new standalone source file > 80 LOC with a public symbol) gets
  **PRD + Architecture Spec + Constitution + Changelog** generated
  automatically on the next session Stop.
- An existing module whose working-tree churn exceeds **25%** of its LOC has
  its docs refreshed.
- `<!-- ADS:AUTO -->` blocks are regenerated from the real source (AST for
  Python, export scan for JS/TS); `<!-- ADS:OWNER -->` blocks are authored by
  the Owner and **never** touched.
- Global: runs in any repo with the PP active, default ON (per-repo opt-out
  via `docs/.ads-disabled`). Writes only to the active repo's `docs/`; never
  stages or commits.

## Mechanism

- `modules/ads/detector.py` -- git working-tree diff → CREATED/UPDATED/MINOR/
  DELETED per module. No-op without git. Reuses `scanner._SKIP_DIRS`/`_LANG_EXT`
  + an ADS skip set (build/dep dirs: `_build`, `deps`, `node_modules`, ...).
- `modules/ads/doc_generator.py` -- composes `sdd_os.prd_generator.generate_prd`
  for tier+sections; AST-extracts the public interface + deps into AUTO blocks.
- `modules/ads/doc_updater.py` -- exactly-one-balanced-marker splice; aborts
  (leaves file untouched) on malformed markers; changelog is append-only.
- `tools/ads_sync.py` -- Stop-chain runner; reads `cwd` from the Stop JSON;
  fail-open (always exit 0). Wired into `hooks/hook-dispatcher.js`
  `CHAIN_MAP['Stop-chain']` (block:false, timeoutMs 6000).
- `tools/ads_backfill.py` + `commands/generate-docs.md` -- manual retroactive
  seeding for code that predates ADS.

## Done-gate

`python tools/test_ads.py` -> **ADS_PASS=19/19**, hermetic (private git config,
fixed `now`, all writes in a TemporaryDirectory), stable across 3 back-to-back
runs. Real-input proof: backfill generated 28 docs in AKOS + 24 in
kobicraft-panel with real AST-extracted interfaces.

## Activation (Owner-side, HR-001)

The canonical `hooks/hook-dispatcher.js` carries the Stop-chain entry. To go
live, mirror it to `~/.claude/hooks/hook-dispatcher.js` and `/restart`
(per the split-brain doctrine -- editing canonical alone changes nothing at
runtime).

## Audit fixes folded in (14 gaps)

Stop-only write surface + no-commit (#1,#8), 6s timeout / changed-set-only
(#2), LOC denominator + binary→MINOR + DELETED type (#3), rename parse (#4),
collision-free slug (#5), package subsumes children (#6), malformed-marker
abort (#7), zero slop tokens in source (#9), absolute git resolution (#10),
self-skip `modules/ads` (#11), hermetic git config (#12), documented mirror
step (#13), build/dep skip dirs (#14).
