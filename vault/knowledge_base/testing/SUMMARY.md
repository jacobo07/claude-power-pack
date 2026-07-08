# GLOBAL TESTING AUDIT — SUMMARY

**Date:** 2026-07-08 · **Repos:** 8 · **Method:** read-only inventory + side-effect-free
test-runner execution · **Rule:** every finding backed by an observed command result.

---

## Headline

The Owner's stack is **better-tested than the plan assumed in two domains and
unverifiable in one.** No repo is a testing wasteland; the real problems are *structural*
(tests that exist but don't run) and *environmental* (tests that can't compile from a
clean checkout), not *absence*.

Two of the plan's premises were disproved by disk evidence before any dataset was written:
- **KobiiAI is not a Minecraft repo** (no Java, no plugin structure) — re-classified to
  content/vault, avoiding a fabricated F1.
- **KobiiCraft is not untested** — 268 JUnit files, 1,596 passing assertions in one
  plugin. The real gap is *concentration*, not absence.

## The five findings that matter (ROI-ranked)

1. **Elixir won't compile (InfinityOps + CostaLuz).** `mix compile` fails with "dependency
   is not locked" on both. 149 ExUnit files (122 + 27) are unverifiable until `mix.lock`
   is committed and a Postgres is provisioned. **Highest ROI: unblocks two whole repos.**
   CostaLuz's dormant `sobelow` security scanner is the sharpest sub-finding — inert
   security tooling on a *legal-services* product.

2. **TUA-X orphans 390 passing tests.** `pyproject.toml` `testpaths = ["tuax_core/tests"]`
   (4,368 tests) means a bare `pytest` never collects `tests/` (157) or `CW_UGC_SYSTEM/
   tests` (232). All 390 pass when invoked explicitly. One config line from protecting
   nothing.

3. **GEO-audit hermeticity break.** `test_no_fake_output.py:185` sets `_DATA_DIR =
   "/nonexistent/path/..."`; the analyzer mkdir's it at the drive root
   (`C:\nonexistent\...geo_snapshots.json`), persisting after the run and defeating
   `test_layer1_ingestion.py::test_process_missing_path` (which then sees the path exist →
   SUCCESS ≠ FATAL). **Not a product bug** — the `process()` guard is correct. A textbook
   ×3-hermetic violation. Result: 203 passed, 1 failed.

4. **KobiiCraft `EconomyService` has zero test references.** Grep across every
   `src/test/java` file → zero. The player economy (money transfer — the most abusable
   surface) runs with no unit test, while 232 of 268 test files sit in KobiMapEngine.
   F1 + F8 at one coordinate. *(Note: fix the JDK — prebuilt test classes are Java 21;
   JDK 17 fails with class-file-65.)*

5. **PP runs 6 of its 76 test files.** `pytest tests/` → 43 passed, but 70 test files live
   outside `tests/`. The self-described most-audited repo executes <10% of its own test
   files in its canonical invocation. Security/cascade module tests are among the
   unreached.

## Per-repo one-liners

| repo | domain | verdict |
|---|---|---|
| claude-power-pack | PP | GREEN 43/43, but F5 collection gap (70/76 files out-of-tree) |
| TUA-X | SaaS | GREEN where run, 390 tests orphaned from default collection |
| KobiiCraft | Minecraft | GREEN 1,596+10 (JDK21); F1 economy gap; 87% concentrated in one plugin |
| GEO-audit | SaaS | 203/204; one hermeticity break polluting the host drive root |
| InfinityOps | SaaS | UNVERIFIED — Elixir won't compile (unlocked deps) |
| CostaLuz Lawyers | SaaS | UNVERIFIED — Elixir won't compile; dormant security scanner |
| KobiiSports Resort | Wii | NOT host-runnable — GX-linked C drivers, pure logic untested |
| KobiiAI | content/vault | N/A — no code (classification corrected) |

## The reference standard

**V-gates ×3 hermetic** (PP): AAA structure + observed-evidence V-gates + run-it-3×
hermeticity. The audit applied it literally — nothing was scored on test-file *presence*,
only on observed runner *output*. GEO-audit's failure is the standard proving itself: the
×3-hermetic rule exists precisely to catch drive-root pollution, and it did.

## Recommended sequence (from the priority ladder)

1. Commit `mix.lock` ×5 (InfinityOps ×3, CostaLuz ×2) + CI Postgres → unblock 149 tests.
2. Widen TUA-X `testpaths` / add CI matrix → recover 390 tests.
3. Point GEO-audit's `_DATA_DIR` at `tmp_path` → fix host pollution + sibling suite.
4. Wire MockBukkit into `kobicore`; write `EconomyServiceTest` (allow/deny/boundary).
5. Bring PP's 70 out-of-tree test files into the default invocation.

Each step is backed by an observed result in this audit; none is speculative.

## What this audit did NOT do (honest boundaries)

- Did **not** run `mix deps.get` / provision Postgres (side-effecting installs, out of
  agreed AUDIT-B scope) → Elixir = unverified, not failed.
- Did **not** stand up devkitPPC → KobiiSports C drivers = not runnable, not failed.
- Did **not** run the full 4,368-test TUA-X default suite to completion → collected-clean,
  not fully executed.
- Did **not** delete `C:\nonexistent` (drive-root deletion is HR-CASCADE-002 / Owner
  decision).
- Did **not** run JS/TS suites (Node install side-effects) → counted, not executed.
