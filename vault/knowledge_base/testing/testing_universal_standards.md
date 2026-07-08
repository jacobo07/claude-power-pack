# Universal Testing Standards — Owner Stack Reference

> Global-Testing-Audit dataset. Generated 2026-07-08. The reference standard is PP's
> **V-gates ×3 hermetic** framework, adapted per stack. This document defines the bar
> every repo is measured against and shows the concrete adaptation for each language in
> the Owner's stack. No code — analysis and standards only.

---

## 1. The reference: V-gates ×3 hermetic

PP's testing doctrine (codified in `rules/python/testing.md` and enforced by
done-gates) rests on three pillars. They generalize to every stack.

### Pillar 1 — AAA structure

Every test has three named sections: **Arrange** (fixtures, inputs), **Act** (invoke
the unit once), **Assert** (verify the observable outcome). A test without ≥1 assert is
an execution, not a test. A test with assertions interleaved with side-effects is two
tests masquerading as one — split it. This is language-agnostic: it holds for pytest,
ExUnit, JUnit, and a C `assert()` harness equally.

### Pillar 2 — V-gate naming + observed evidence

PP tests emit `V-<DOMAIN>-<NAME>` gate identifiers so a done-gate can grep the result
and a human can trace a pass to a requirement. The deeper rule is the **Reality
Contract**: the evidence is the test *output*, not the description of the test. A test
file that documents extensive cases but exits 0 without exercising them is theater.
"DONE = QA Pipeline PASS with observed evidence" (Ley 25 / Gate 7). This audit applied
exactly that: no repo was scored on the *presence* of test files, only on *observed*
runner output.

### Pillar 3 — hermeticity ×3 (run it three times)

A test suite must produce the same result run three times in a row from a clean state.
The detector is literally "run the suite 2–3×": a suite that passes once then fails on
re-run, or that writes to a global/shared location, is non-hermetic. PP's own memory
records this pattern ("Hermetic test: global writes + time-window") — a gate writing a
global dir with a dedup/TTL window fails on rapid re-run. Hermeticity is not a nicety;
it is the difference between a safety net and a random number generator.

**The audit found a textbook hermeticity violation** — see GEO-audit below — proving
this pillar is the highest-ROI standard to enforce across the stack.

---

## 2. Per-stack adaptation

### Python (PP, TUA-X, GEO-audit, KobiiCraft scripts, KobiiSports ai-pipeline)

- **Runner:** `pytest`. **Isolation:** `tmp_path` + `monkeypatch` for anything touching
  the filesystem, env, time, or randomness. Never write outside `tmp_path`.
- **Collection contract:** the default `pytest` invocation MUST reach every test.
  `testpaths` that scopes to a subtree is an F5 trap (TUA-X). If multiple suite roots
  exist, CI runs each and *counts* what it ran.
- **Mocking discipline:** mock at the boundary (network, FS, clock), never internal
  functions of the unit under test. ≥4 mocked collaborators = the unit does too much.
- **Coverage floor:** new code ships with ≥1 happy-path + ≥1 edge-case test; every
  fail-open branch (`BUDGET_EXHAUSTED`, `CACHE_HIT`) gets its own test.

### Elixir / Phoenix (InfinityOps, CostaLuz)

- **Runner:** `mix test`. **Isolation:** `Ecto.Adapters.SQL.Sandbox` gives each test a
  rolled-back transaction — the correct hermetic DB pattern.
- **Prerequisite (the current blocker):** `mix deps.get` must have run and `mix.lock`
  must be committed. The audit found both InfinityOps `infinity_os` and CostaLuz
  `costaluz-platform` fail `mix compile` with "dependency is not locked". A CI that
  cannot fetch+lock deps cannot run a single ExUnit test. **Standard: commit `mix.lock`
  and provision a Postgres in CI**, or the 122 + 27 ExUnit files are unverifiable.
- **Integration:** `ConnCase` / `DataCase` for the app↔DB seam (F2). Phoenix's built-in
  case templates make the integration test the *default*, not an afterthought.

### Java / Bukkit (KobiiCraft)

- **Runner:** Maven Surefire (`mvn test`). **Toolchain contract:** the prebuilt test
  classes are Java 21 (class file 65). Building with JDK 17 fails with
  "compiled by a more recent version". **Standard: pin `JAVA_HOME` to JDK 21** in CI and
  local docs — the audit lost a run to this exact mismatch before retrying on JDK 21.
- **Isolation:** MockBukkit gives an in-memory server so plugin logic runs without a
  real Paper instance. Currently wired in **1 of 90 poms** (KobiMapEngine). **Standard:
  every plugin with command/economy/state logic depends on MockBukkit** and tests its
  logic headless.
- **Offline:** `mvn -o test` works once `.m2` is warm — verified in the audit
  (KobiMapEngine 1,596 tests, kobicore 10 tests, both green offline on JDK 21).

### C / Wii homebrew (KobiiSports Resort, libogc + GX)

- **Reality:** no unit-test framework is standard in homebrew, and the existing "test"
  files (`test_foundation.c`, `stress_test.c`) `#include` engine headers
  (`gx_state_manager.h`, `world_atmosphere.h`) — they link the whole game, so they are
  integration smoke drivers, not isolatable units. They also need `devkitPPC` to build.
- **Adapted standard:** extract pure logic (math, state transitions, scoring) into
  functions with no GX/hardware dependency, and test *those* on the host with a minimal
  C assert harness (host `gcc`, no devkitPPC). Frame-budget assertions (F6) run
  on-device via the existing profiler. Don't chase 100% — pin the pure logic that can
  fail silently.

### JS / TS (TUA-X frontend, KobiiCraft web, InfinityOps UI)

- **Runner:** jest / vitest. Same collection and hermeticity rules as Python. The audit
  counted 29 (TUA-X) + 41 (KobiiCraft) + 13 (InfinityOps) spec files but did not
  execute them (Node install side-effects out of the agreed AUDIT-B scope) — recorded
  as unverified, not passed.

---

## 3. The done-gate every repo should adopt

A single command per repo that a human or hook can run, that:

1. Runs **every** test suite root (no silent collection gaps).
2. Prints `PASS=n/total` with the count of tests *actually executed*.
3. Runs the suite a second time and asserts the same result (hermeticity ×2 minimum).
4. Exits non-zero on any failure, and non-zero on a *drop* in executed count
   (regression against a recorded baseline).

PP already has the shape of this (V-gate greppable output). The gap in the rest of the
stack is (a) reaching all suite roots and (b) the hermeticity re-run. Both are cheap.

---

## 4. Priority ladder (highest ROI first, from audit evidence)

1. **Restore Elixir CI** (InfinityOps, CostaLuz): commit `mix.lock`, provision Postgres.
   Until this is done, 149 ExUnit files are Schrödinger's tests. Highest ROI: it
   unblocks *auditing* two whole repos.
2. **Fix TUA-X collection** (one config line): widen `testpaths` or add a CI matrix so
   the 390 orphaned tests run. 390 passing tests currently protect nothing.
3. **Fix GEO-audit hermeticity**: the drive-root pollution (`C:\nonexistent`) breaks a
   sibling suite and contaminates the host. Point the offending test at `tmp_path`.
4. **KobiiCraft economy F1**: one MockBukkit test on `EconomyService` (money transfer
   allow + deny + overdraft). The most abusable surface, currently zero coverage.
5. **PP suite-root consolidation**: bring the 70 out-of-tree test files into the default
   invocation or document why they're excluded.
6. **KobiiSports pure-logic extraction**: pull testable logic off the GX-linked path.

Every item above is backed by an observed command result in this audit — none is
speculative.
