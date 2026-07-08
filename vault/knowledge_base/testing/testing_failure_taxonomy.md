# Testing Failure Taxonomy F1–F8 (Sealed)

> Global-Testing-Audit dataset. Generated 2026-07-08 from empirical evidence across
> 8 Owner repos (claude-power-pack, TUA-X, KobiiCraft, InfinityOps, CostaLuz Lawyers,
> GEO-audit, KobiiSports Resort, KobiiAI). Every category below is illustrated with a
> **real** finding from the audit — no invented failures. Where a category was NOT
> observed in a repo, that is stated as such.

The premise of this taxonomy: Minecraft plugins, Wii homebrew, and Elixir/Python SaaS
are different domains, but their testing gaps fall into the same eight categories. A
gap is not "this repo is bad" — it is "this repo has an F-class hole at coordinate X".
Naming the class makes the gap portable across stacks and comparable across repos.

---

## F1 — LÓGICA SIN TEST (critical logic without a unit test)

**Definición.** A function or module whose failure directly harms a user or corrupts
state, that has no unit test exercising its behaviour. Not "low coverage" — *zero*
coverage on a load-bearing unit.

**Señales.**
- A `main/` source file with business logic and no corresponding file under `test/`.
- Grep for the class name across all test files returns zero hits.
- The unit is reachable from a command, packet handler, HTTP route, or scheduled job
  (i.e. it runs in production) yet no assertion pins its output.

**Impacto.** A silent behavioural regression ships. Because nothing asserts the
contract, a refactor that changes the result passes CI green. The first observer is a
user (wrong balance, wrong permission, corrupted save).

**Fix estándar.** Write one happy-path test and one edge-case test that call the real
unit at its public boundary. For a pure function this is trivial; if the unit needs a
world/DB/socket, mock at the boundary (MockBukkit for Bukkit, Ecto sandbox for Elixir,
`tmp_path`+monkeypatch for Python). The test must *fail* if the logic is deleted —
verify that once (RED) before trusting GREEN.

**Ejemplo real del stack.** KobiiCraft `kobicore` ships
`com/kobicraft/core/economy/EconomyService.java`. A grep for `EconomyService` across
every `src/test/java` file in the entire plugin tree returns **zero** references. The
plugin's two `kobicore` tests are `BossRouteGuardTest` and `KobiMessagesLegacyHexTest`
— neither touches money. The player economy — the single most abusable surface in a
Minecraft server — runs in production with no unit test. This is the canonical F1 of
the audit.

---

## F2 — INTEGRACIÓN SIN CONTRATO (modules without an integration test)

**Definición.** Two or more modules that must agree on a contract (a wire format, a DB
schema, an env var, a function signature) with no test that exercises them *together*.
Each unit may be green in isolation while the seam between them is untested.

**Señales.**
- Unit tests everywhere, `integration/` or `*_integration_test` nowhere.
- A service depends on a DB/queue/socket that is stubbed in every test, so the real
  connection contract is never validated.
- A test suite that cannot run without an external service that CI never provisions.

**Impacto.** The units pass; the system fails on first real wiring. Classic
"compiles != works" (Mistake #16): static verification of two halves proves nothing
about the join.

**Fix estándar.** One end-to-end test per critical seam that drives the real contract:
spin the DB in a sandbox, post a real payload, assert the observed downstream state.
For Elixir, `Ecto.Adapters.SQL.Sandbox`. For Phoenix, `ConnCase`. For Python services,
an httpx test client against the real app object.

**Ejemplo real del stack.** InfinityOps `infinity_os` and CostaLuz `costaluz-platform`
declare `ecto_sql` + `postgrex` and cannot even *compile* in the audit environment:
`mix compile` fails with "dependency is not locked" for `jason`, `req`, `ecto_sql`,
`postgrex`, `phoenix_pubsub`. The integration contract (app ↔ Postgres) is only
exercisable after `mix deps.get` + a running Postgres — infrastructure CI must
provision. Until it does, the 122 ExUnit files in InfinityOps and 27 in CostaLuz are
an unverifiable promise: nobody has observed them pass in this environment.

---

## F3 — EDGE CASES IGNORADOS (happy path only)

**Definición.** A unit that is tested, but only for the input that was expected to
work. Empty collections, nulls, boundary values, malformed input, and the error branch
are all unasserted.

**Señales.**
- Every test for a unit uses valid, well-formed input.
- The function has `if not x: return failure` branches that no test reaches.
- Coverage of the fail-open / error path is 0% while the happy path is 100%.

**Impacto.** The unit works until a user hands it something unexpected — then it
crashes or, worse, silently returns a success-shaped wrong answer.

**Fix estándar.** For every code path that handles a degenerate input
(`BUDGET_EXHAUSTED`, `CACHE_HIT`, empty, null, malformed), add a dedicated test.
The PP testing doctrine already mandates this: "Code paths that handle fail-open
branches must each have a dedicated test, not just the happy path."

**Ejemplo real del stack.** GEO-audit `ingestion.process()` has a genuine edge-case
guard: `if not ingest_path.exists(): return failure_state(...)`. There IS a test for
it (`test_process_missing_path` asserts `status == "FATAL"`). This is a *positive*
example — the edge case is covered. The audit found the opposite problem here (F5,
below), which is why this test's failure was traced to pollution rather than a missing
branch.

---

## F4 — REGRESIÓN SIN COBERTURA (a fixed bug with no preventive test)

**Definición.** A bug was found and fixed, but no test was added that would fail if the
bug returned. The fix is a point-in-time patch, not a permanent invariant.

**Señales.**
- Commit history shows "fix X" with no accompanying test file change.
- A NEVER_AGAIN / lessons entry exists for a bug class with no corresponding test gate.
- Tests exist but none are named for or traceable to a past incident.

**Impacto.** The same bug re-ships months later after a refactor. The institutional
memory of "we already fixed this" lives only in a human's head or a vault note, not in
executable form.

**Fix estándar.** Every non-trivial bugfix ships with a RED-first regression test that
reproduces the bug, then goes GREEN with the fix. The test name references the incident.

**Ejemplo real del stack.** PP has a strong V-gate regression culture
(`V-<DOMAIN>-<CASE>` naming lets done-gates grep results), and KobiiCraft's
`KobiMessagesLegacyHexTest` is exactly a regression pin for a legacy-hex color parsing
bug. The F4 gap is elsewhere: TUA-X's 390 orphaned tests (see F5) include regression
tests that a bare `pytest` never runs — so a regression they were written to catch
would re-ship undetected despite the test existing.

---

## F5 — PRODUCCIÓN SIN MONITOR (production behaviour without coverage)

**Definición.** Behaviour that runs in production is not covered by any test that
actually executes in the normal test invocation — either because no test exists, or
because a test exists but the default runner never collects it. The second form is
insidious: the test count looks healthy while the safety net has a hole.

**Señales.**
- `pytest.ini` / `pyproject.toml` `testpaths` scopes collection to a subtree, leaving
  sibling test directories uncollected.
- Test files living outside the configured suite root.
- A CI command (`pytest tests/`) that structurally cannot reach most of the repo's
  tests.

**Impacto.** A green CI badge that lies. The tests exist, pass when run manually, and
rot silently because no automated invocation runs them. Coverage decays to zero the day
someone breaks them, and nobody notices.

**Ejemplo real del stack — TWO independent instances:**

1. **TUA-X collection gap.** `pyproject.toml` sets
   `testpaths = ["tuax_core/tests"]` (4,368 tests). A bare `pytest` therefore never
   collects `tests/` (157 tests) or `CW_UGC_SYSTEM/tests` (232 tests). All 390 pass
   when invoked explicitly (verified: `157 passed`; `232 passed, 1 skipped`) — they are
   simply invisible to the default runner. 390 green tests one config line away from
   irrelevance.

2. **PP suite-root gap.** PP has 76 `test_*.py` files but `pytest tests/` collects only
   43 (6 files). 70 test files live outside `tests/`. The self-described "most audited
   repo in the stack" runs under 10% of its own test files in the canonical invocation.

**Fix estándar.** Make the default invocation reach every test, or make the omission
explicit and logged. Either widen `testpaths` / add `rootdir` config, or maintain a
CI matrix that runs each suite root and *counts* what it ran. Silent truncation reads
as "covered everything" when it isn't (PP no-silent-caps doctrine).

---

## F6 — PERFORMANCE SIN BASELINE (no benchmarks)

**Definición.** A system with performance-sensitive paths (render loops, hot request
handlers, bulk data pipelines) has no benchmark that would catch a performance
regression.

**Señales.**
- No `benchee` (Elixir), `pytest-benchmark`, JMH, or timed assertion anywhere.
- Performance claims in docs with no executable proof.
- A render/tick loop with a frame-budget requirement and no test measuring it.

**Impacto.** A change that doubles latency or halves FPS ships green. The regression is
discovered by users (lag, timeout) or in production monitoring, never in CI.

**Fix estándar.** For the few genuinely hot paths, a benchmark with a threshold that
fails the build when exceeded. Not every function — only the ones where speed is a
contract.

**Ejemplo real del stack.** InfinityOps declares `benchee` as a dependency (seen in the
`mix compile` unchecked-deps list), signalling *intent* to benchmark — but the deps
aren't locked/fetched, so no benchmark currently runs. KobiiSports Resort is a Wii
homebrew title with a GX render queue and profiler (`gx_profiler.h`,
`gx_render_queue.h` are `#include`d by its test files) — frame budget is the entire
game-feel contract on real hardware — yet the "tests" are ad-hoc C files that link the
whole engine, not standalone frame-time benchmarks. F6 is the *default* state of the
Wii domain.

---

## F7 — DATOS SIN VALIDACIÓN (inputs without validation coverage)

**Definición.** Input parsing/validation exists (or should) but no test proves that bad
data is rejected and good data is accepted. Includes CSV/JSON parsers, config loaders,
packet deserializers, and form handlers.

**Señales.**
- A parser with no test feeding it malformed input.
- Config loading with no test for the empty-list / missing-key case (the classic
  YAML `[]` → NPE cascade).
- User-facing input reaching business logic with no boundary assertion.

**Impacto.** Malformed input crashes the process or is accepted as valid, corrupting
downstream state. On a Minecraft server a single bad YAML key can silently disable an
entire plugin's command set.

**Fix estándar.** For every parser/loader, a test matrix: valid input → parsed;
malformed → rejected with a clear error; degenerate (empty/null) → safe default, not a
crash.

**Ejemplo real del stack.** GEO-audit `CGAR` forensic probes (in PP's
`test_forensic_probes.py`, 43 tests) are a *model* of F7 done right:
`test_malformed_node_missing_id_is_warned`, `test_malformed_node_non_dict_is_warned`,
`test_not_configured_with_v1_empty_placeholder` — each feeds deliberately broken data
and asserts the warn/reject path. GEO-audit's ingestion adapters, by contrast, have a
`select_adapter` chain that returns `None` on no-match and merely logs a warning; the
"no adapter" path is exercised only incidentally (and via the polluting test, see F5).

---

## F8 — SEGURIDAD SIN TEST (permissions/security without a contract)

**Definición.** An authorization check, permission gate, RLS policy, secret-handling
path, or sandbox boundary with no test proving it denies the unauthorized case.

**Señales.**
- A permission check (`hasPermission`, RLS policy, auth middleware) with tests only for
  the *allowed* case.
- Secret redaction / firewall logic with no test feeding it a real-shaped fake secret.
- A command that mutates shared state (economy, admin ops) with no test for the
  non-privileged caller.

**Impacto.** A privilege-escalation or data-leak path ships. The allow case works so it
looks tested; the deny case — the one that matters for security — is unproven.

**Fix estándar.** Every auth gate needs a *deny* test, not just an allow test. Security
tests assert the negative: unauthorized → refused. PP's HR-SECRET-005 codifies the
secret-firewall variant: use a clearly-fake but real-shaped key (`sk-ant-` + `'A'*50`)
that SHOULD trip the firewall, proving detection fires.

**Ejemplo real del stack.** PP is the reference here: the Secret Firewall
(`modules/secret_firewall/`) is tested with real-shape synthetic secrets that must
trigger detection in CI (HR-SECRET-005). KobiiCraft `KobiiNetworkAdmin` has
`DispatchPlanTest` and `PterodactylClientTest` — the admin-dispatch surface (which can
restart production servers) has *some* contract coverage, a rare F8 positive in the
Minecraft domain. The gap: `kobicore`'s economy commands (money transfer between
players) have no deny-case test — an F1 and F8 at the same coordinate.

---

## Cross-repo F-class heatmap (observed, not assumed)

| repo | F1 | F2 | F3 | F4 | F5 | F6 | F7 | F8 |
|---|---|---|---|---|---|---|---|---|
| claude-power-pack | – | – | – | – | **●** | ○ | ✓ | ✓ |
| TUA-X | ○ | ○ | – | ● | **●** | – | – | – |
| KobiiCraft | **●** | ○ | ○ | ✓ | ○ | ● | ○ | ● |
| InfinityOps | ? | **●** | ? | ? | ? | ● | ? | ? |
| CostaLuz Lawyers | ? | **●** | ? | ? | ? | – | ? | ? |
| GEO-audit | ○ | ○ | ✓ | ○ | **●** | – | ○ | – |
| KobiiSports Resort | ● | ● | ● | ● | ● | **●** | ● | – |
| KobiiAI | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

Legend: **●** = confirmed active gap with evidence · ○ = partial/present-but-thin ·
✓ = handled well (positive example) · ? = unverifiable in audit env (Elixir deps
unlocked, needs infra) · – = not the dominant issue / not observed · n/a = no code.

The `?` column for Elixir repos is itself the finding: F2 (integration contract) is
confirmed because the code cannot compile without `deps.get` + Postgres, which makes
every other category unverifiable. Restoring the environment is prerequisite to auditing
InfinityOps/CostaLuz test health at all.
