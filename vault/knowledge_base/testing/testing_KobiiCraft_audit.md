# Testing Audit — KobiiCraft (KobiCraftServer plugins)

> Global-Testing-Audit, 2026-07-08. Domain: Minecraft (Java 21 / Paper, Maven; plus
> Python tooling). Repo path: `.../Minecraft Projects/KobiiCraft Workspace/KobiiCraft
> Core Files`. Prior plan hypothesis: "the domain with least coverage; economy runs with
> no test." **Disproved as written.** KobiiCraft has 268 JUnit files and a live
> MockBukkit suite — but the coverage is extraordinarily concentrated, and the economy
> gap is real at a finer grain than the hypothesis stated.

---

## AUDIT-A — Does a test suite exist?

Yes — the largest Java test surface in the stack. 268 `.java` files under
`src/test/java` across 7 plugins, 90 `pom.xml` files, plus 137 Python `test_*.py` in the
scripting/tooling layer and 41 JS/TS specs. A repo-root `conftest.py` anchors pytest.
MockBukkit (the in-memory Bukkit server for headless plugin testing) is declared — the
first evidence that contradicts "no Minecraft testing exists."

The critical A-finding is the **distribution**, not the total:

| plugin | JUnit files under src/test/java |
|---|---|
| KobiMapEngine | **232** (87% of all JUnit) |
| KobiSkyWars | 26 |
| KobiiLuckyArena | 3 |
| KobiiPrisonImporter | 2 |
| kobicore | **2** |
| KobiiNetworkAdmin | 2 |
| kMundiCore | 1 |

232 of 268 test files (87%) belong to one plugin. And MockBukkit appears in **1 of 90
poms** — KobiMapEngine's. The remaining 89 plugins share 36 test files and no MockBukkit.

## AUDIT-B — Do the tests pass?

First attempt failed on an *environment* fault, not a code fault: `mvn -o test` on
`kobicore` under JDK 17 → "BossRouteGuardTest has been compiled by a more recent version
of the Java Runtime (class file version 65.0)". The prebuilt test classes are Java 21.
Re-running with `JAVA_HOME=jdk-21` (found on disk at `C:\Users\User\Apps\jdk-21`):

- **KobiMapEngine (`mvn -o test`, JDK 21): BUILD SUCCESS — Tests run: 1,596, Failures:
  0, Errors: 0, Skipped: 15.** The MockBukkit suite is real, large, and green offline.
- **kobicore (`mvn -o test`, JDK 21): BUILD SUCCESS — Tests run: 10, Failures: 0.**
  (`BossRouteGuardTest` 5 + `KobiMessagesLegacyHexTest` 5.)

So the Minecraft domain is not untested — it has the second-largest *executed* test
count in the stack (1,596 in one plugin alone). The toolchain contract (JDK 21, not 17)
is a documentation gap worth sealing: a fresh clone builds with the wrong JDK and fails
confusingly.

## AUDIT-C — What is not tested?

`kobicore` is the server's core plugin — it owns
`com/kobicraft/core/economy/EconomyService.java`. Its only two tests are
`BossRouteGuardTest` (boss AI route guarding) and `KobiMessagesLegacyHexTest` (legacy
color-code parsing). **A grep for `EconomyService` across every `src/test/java` file in
the entire plugin tree returns zero references.** The player economy — balances, money
transfer, the single most abusable surface on any Minecraft server — has no unit test,
no MockBukkit test, no deny-case test.

This is a more precise and more defensible finding than the plan's original wording. The
plan said "economía opera sin ningún test en producción." The accurate statement:
*KobiiCraft has 268 tests and 1,596 executing assertions, but `EconomyService` has zero
of them; the coverage lives almost entirely in one non-economy plugin.* The gap is
**concentration**, not **absence** — and that distinction is the difference between an
evidence-backed finding and an invented one.

Other untested-or-thin surfaces: KobiSkyWars minigame state (26 files — reasonable),
KobiiLuckyArena progression/social/rivalry (3 files — thin for its feature set),
kMundiCore bounty (1 file). The Python tooling layer (137 files) covers scripts
(magazine, prison, skyparty, network, kme) but is a separate concern from the plugin
runtime.

## AUDIT-D — Failure taxonomy (F1–F8)

- **F1 (lógica sin test):** **Confirmed, canonical.** `EconomyService` — zero test
  references. The audit's flagship F1.
- **F2 (integración sin contrato):** Partial. `KobiiNetworkAdmin` has
  `DispatchPlanTest` + `PterodactylClientTest` — the admin-dispatch/Pterodactyl seam
  (which can restart production servers) has contract coverage, a rare F2/F8 positive.
- **F3 (edge cases):** Present in KobiMapEngine (WorldLoaderOffset, SensationHook,
  TenAxisWorldTierAggregator — boundary and aggregation tests). Thin elsewhere.
- **F4 (regresión sin cobertura):** `KobiMessagesLegacyHexTest` is a regression pin for
  a color-parsing bug — good. Broadly, regression culture is confined to KobiMapEngine.
- **F5 (producción sin monitor):** Thin. Most plugins run in production with no test;
  the running coverage is concentrated in one non-gameplay-critical plugin (map engine).
- **F6 (performance sin baseline):** Present. No frame/tick benchmark observed; Minecraft
  tick budget is a real contract with no test guarding it.
- **F7 (datos sin validación):** Partial. WorldLoader tests validate world data; config
  parsing (the YAML `[]`→NPE class of bug that plagues Bukkit plugins) is not visibly
  tested in kobicore.
- **F8 (seguridad sin test):** Confirmed gap at the economy. `EconomyService` money
  transfer has no deny-case / overdraft / negative-amount test. `KobiiNetworkAdmin` is
  the F8 positive; the economy is the F8 negative.

## AUDIT-E — Expandable frontiers

The frontier is **spreading MockBukkit beyond KobiMapEngine.** The pattern is proven —
1,596 green tests in one plugin show the harness works headless and offline. The economy,
minigame reward payouts, and permission gates in `kobicore` and the arena plugins are all
MockBukkit-testable today; the dependency is wired in exactly one pom. Adding MockBukkit
to `kobicore` and writing an `EconomyServiceTest` (transfer allow, transfer deny for
insufficient funds, negative-amount reject, concurrent-transfer invariant) is the single
highest-value test in the Minecraft domain.

Second frontier: the JDK-21 toolchain contract. As more contributors/CI touch the repo,
the class-file-65 mismatch will recur. Pin `JAVA_HOME` in build docs and CI.

## Verdict and completion criterion

**Density: media, but pathologically concentrated (87% in one plugin). Health: green
where it runs (1,596 + 10 passing on JDK 21). Defining gap: F1/F8 at `EconomyService`.**

**DONE for KobiiCraft testing** = MockBukkit is wired into `kobicore`; `EconomyService`
has an allow-case, a deny-case (insufficient funds), a boundary-case (negative/zero
amount), and a concurrency invariant test, all green under `mvn -o test` on JDK 21; and
the JDK-21 requirement is documented so a fresh build doesn't fail on class-file-65. The
broader frontier — MockBukkit across the top-5 gameplay plugins — is the growth path, not
the done-gate.

---

## Part II — Evidence appendix, test-debt inventory, and remediation detail

### II.1 Reproduced evidence (the JDK pivot and the green runs)

First run, JDK 17 (`JAVA_HOME=C:\Users\User\Apps\jdk-17`):

```
$ mvn -o -B test        # in plugins/kobicore
[INFO] Building KobiCore 2.5.4
[ERROR] com/kobicraft/core/modules/boss/behavior/BossRouteGuardTest has been compiled
        by a more recent version of the Java Runtime (class file version 65.0), this
        version of the Java Runtime only recognizes class file versions up to 61.0
[INFO] Tests run: 0
[INFO] BUILD FAILURE
```

Class file 65 = Java 21; version 61 = Java 17. The prebuilt test classes were compiled
by JDK 21, so JDK 17 cannot even load them. Re-run with `JAVA_HOME=C:\Users\User\Apps\
jdk-21`:

```
$ mvn -o -B test        # in plugins/kobicore
[INFO] Tests run: 5 ... BossRouteGuardTest
[INFO] Tests run: 5 ... KobiMessagesLegacyHexTest
[INFO] Tests run: 10, Failures: 0, Errors: 0, Skipped: 0
[INFO] BUILD SUCCESS

$ mvn -o -B test        # in plugins/KobiMapEngine
[INFO] Tests run: 8   ... WorldAssertionsTest
[INFO] Tests run: 2   ... WorldLoaderOffsetTest
[INFO] Tests run: 2   ... WorldLoaderSensationHookTest
[INFO] Tests run: 13  ... TenAxisWorldTierAggregatorTest
[WARNING] Tests run: 1596, Failures: 0, Errors: 0, Skipped: 15
[INFO] BUILD SUCCESS
```

Two facts land here: (a) the Minecraft domain runs 1,606 green assertions offline once
the JDK is right; (b) a fresh clone with a default JDK 17 fails confusingly — the
toolchain contract (JDK 21) is undocumented and cost the audit one run before the pivot.

### II.2 The economy F1, proven negative

```
$ grep -r "EconomyService" **/src/test/java/**/*.java
(zero matches)

$ ls plugins/kobicore/src/main/java/com/kobicraft/core/economy/
EconomyService.java

$ ls plugins/kobicore/src/test/java  (recursive)
BossRouteGuardTest.java
KobiMessagesLegacyHexTest.java
```

`EconomyService` exists in production `main/`; no test file in the entire plugin tree
names it. The two `kobicore` tests cover boss-AI routing and legacy color-code parsing —
zero economy. This is the audit's flagship F1: the presence of 268 test files and 1,606
passing assertions makes it *easy to assume* the economy is covered; the grep proves it
is not. The lesson: a healthy aggregate test count is not evidence for any *specific*
surface — you must grep the surface, not trust the total.

### II.3 The concentration pathology, quantified

| plugin | src/test/java files | share |
|---|---|---|
| KobiMapEngine | 232 | 86.6% |
| KobiSkyWars | 26 | 9.7% |
| KobiiLuckyArena | 3 | 1.1% |
| KobiiPrisonImporter | 2 | 0.7% |
| kobicore | 2 | 0.7% |
| KobiiNetworkAdmin | 2 | 0.7% |
| kMundiCore | 1 | 0.4% |

MockBukkit in poms: 1 of 90. So the *executable-headless* coverage (MockBukkit-backed)
is even more concentrated than the file count suggests — the 1,596 KobiMapEngine
assertions are the only large body of logic tested against a simulated server. The
gameplay-critical plugins (economy in kobicore, rewards in KobiiLuckyArena, minigame
state in KobiSkyWars) share 33 files and no MockBukkit. A server operator's risk surface
(player money, item rewards, permissions) is the inverse of where the tests are.

### II.4 Test-debt inventory (by operator consequence)

| surface | plugin | current tests | consequence if it silently breaks |
|---|---|---|---|
| player money transfer | kobicore `EconomyService` | **0** | duped/lost currency, economy collapse |
| minigame rewards | KobiiLuckyArena | 3 (progression/social/rivalry) | reward exploits |
| minigame state | KobiSkyWars | 26 | match desync (best-covered gameplay) |
| admin dispatch / Pterodactyl | KobiiNetworkAdmin | 2 (DispatchPlan, PterodactylClient) | wrong server restarted |
| world loading | KobiMapEngine | 232 | (well covered) |
| config parsing (YAML `[]`→NPE) | kobicore | not visibly tested | plugin silently disabled |

The `KobiiNetworkAdmin` row is a genuine F8 positive worth naming: `PterodactylClientTest`
and `DispatchPlanTest` cover a surface that can restart production servers — someone
correctly prioritized testing the dangerous admin path. The economy row is the F8/F1
negative directly beside it.

### II.5 Hermeticity note

MockBukkit is inherently hermetic — it constructs a fresh in-memory server per test, no
shared global state, no real socket. So KobiMapEngine's 1,596 tests are structurally
hermetic (the ×3 pillar is satisfied by construction). Extending MockBukkit to kobicore
inherits this property for free — a strong argument for the harness choice.

### II.6 Concrete remediation

1. Document `JAVA_HOME` = JDK 21 in build docs and CI (`.github/workflows`), and add a
   `maven.compiler.release=21` guard so a wrong-JDK build fails with a clear message
   rather than class-file-65.
2. Add `mockbukkit` to `plugins/kobicore/pom.xml` (the dependency pattern is copyable
   from KobiMapEngine's pom).
3. Write `EconomyServiceTest`: transfer-allow (sufficient funds), transfer-deny
   (insufficient funds → refused, balances unchanged), boundary (zero/negative amount →
   rejected), and a concurrency invariant (two simultaneous transfers cannot create
   money). These four are the minimum viable F1/F8 close for the economy.
4. Stretch: extend MockBukkit to KobiSkyWars reward payout and KobiiLuckyArena
   progression — the next-highest operator-risk surfaces.

### II.7 What "good" looks like for KobiiCraft

The domain the plan predicted as barest is actually a proof that headless Minecraft
testing works at scale (1,596 green, offline, hermetic). "Good" is not more tests
everywhere — it is *spreading the proven harness to the operator-risk surfaces*, starting
with the economy, plus documenting the JDK-21 contract so the green run is reproducible by
anyone. When `mvn -o test` on JDK 21 covers `EconomyService` transfer allow/deny/boundary,
the single most abusable surface on the server moves from zero coverage to a hermetic
contract.

---

## Part III — Standard cross-walk, done-gate checklist, and the stack lesson

### III.1 Cross-walk to the V-gates ×3 hermetic standard

- **AAA structure:** Good in KobiMapEngine (WorldLoader/aggregator tests follow arrange-
  act-assert). Unknown-to-thin elsewhere given the 2-file plugins.
- **Observed-evidence V-gates:** Excellent for the domain — `mvn -o test` produces real
  Surefire output (1,596 + 10 green), observed directly, once the JDK is right.
- **Hermeticity ×3:** Satisfied by construction where MockBukkit is used — each test builds
  a fresh in-memory server, no shared global state. Extending MockBukkit to kobicore
  inherits hermeticity for free.

### III.2 Done-gate checklist (copy-paste for CI)

- [ ] `JAVA_HOME` = JDK 21 pinned in build docs + CI; `maven.compiler.release=21` guard
- [ ] MockBukkit added to `kobicore/pom.xml`
- [ ] `EconomyServiceTest`: transfer allow / deny (insufficient) / boundary (zero/negative)
      / concurrency invariant
- [ ] `mvn -o test` green on JDK 21 across the top-5 gameplay plugins
- [ ] config-parse (YAML `[]`→NPE class) test for kobicore

### III.3 The lesson KobiiCraft teaches the stack

KobiiCraft teaches that **an aggregate test count is not evidence for any specific
surface.** 268 test files and 1,596 passing assertions make the repo *look* well-covered —
yet a one-line grep proves the player economy has zero coverage. The tests are real and
green; they simply cluster (87%) in a single non-gameplay-critical plugin while the
operator-risk surfaces (money, rewards, permissions) sit nearly untested. The generalizable
rule: **grep the specific surface you care about; never infer its coverage from the repo
total.** A healthy headline number can coexist with a critical zero. This is the F1/F8
counterpart to the "exists ≠ runs" lesson elsewhere — here the tests both exist and run,
but they run somewhere other than where the risk is. KobiiCraft also disproved the plan's
premise most sharply (predicted barest, found second-best-tested), a reminder that domain
assumptions must be checked against disk before they seed a finding.
