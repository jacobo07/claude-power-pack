# Testing Audit — TUA-X

> Global-Testing-Audit, 2026-07-08. Domain: Business/SaaS (Python + Next.js frontend,
> pyproject/pytest + jest). Largest repo in the stack by file count (~85k files).
> Verdict: the most-tested repo by raw count, undermined by a collection-scope gap that
> orphans 390 passing tests from every default run.

---

## AUDIT-A — Does a test suite exist?

Abundantly. Six distinct test roots: `tests/`, `tuax_core/tests`, `CW_UGC_SYSTEM/tests`,
`tuax_ugc/tuax_ugc/tests`, `tuax_mie/test`, and `frontend/__tests__`. The manifest is
`pyproject.toml` declaring a full modern pytest stack: `pytest>=8.0`, `pytest-asyncio`,
`pytest-cov`, `pytest-httpx`. There is a `.hypothesis` directory (property-based
testing), a `.coverage` file (coverage has been measured), `docker-compose.test.yml`
(containerized test infra), and a `.claude-quality-gate.json`. This is the most
deliberately test-instrumented repo in the stack. Raw Python test-file count in the
canonical dirs: 517. Plus 29 JS/TS specs and 5 Elixir `_test.exs`.

## AUDIT-B — Do the tests pass?

Three separate collection/run results, because the repo has three separate collection
behaviours:

1. **Default (`pytest`, honouring `pyproject`):** `pyproject.toml` sets
   `testpaths = ["tuax_core/tests"]`. Collection: **4,368 tests collected (12
   deselected)** in 23.5s. This is the suite CI runs. It is large and imports cleanly.

2. **`pytest tests/` (the `tests/` root, NOT in testpaths):** **157 passed** in 7.35s.
   These 157 tests are green — and a bare `pytest` never runs them.

3. **`pytest CW_UGC_SYSTEM/tests` (also not in testpaths):** **232 passed, 1 skipped**
   in 20.9s. Also green, also never run by default.

So: **390 tests (157 + 233 collected) pass when invoked explicitly and are invisible to
the default runner.** The default suite of 4,368 is healthy; the finding is the 390 that
sit one config-line away from irrelevance.

I did not run the 4,368-test default suite to completion (it is large and some tests are
async/httpx integration tests that may reach out); collection succeeded cleanly, which
proves imports and fixtures resolve. Full pass/fail of the 4,368 is recorded as
*collected-clean, not fully executed in this audit* — an honest boundary, not a claim.

## AUDIT-C — What is not tested / not run?

The gap is not missing tests — it is **unreached** tests. `tests/` includes
`tests/scripts/test_verify_cw_infinityops_live_skeleton.py` (route-manifest shape,
public-HTTPS default) — deployment-contract tests. `CW_UGC_SYSTEM/tests/ukdl/` includes
`test_ukdl_activation.py` and `test_http_sink.py` (the latter asserts graceful NoOp
degradation when the InfinityOps endpoint is unreachable — a real fail-open contract).
These are exactly the F5 production-behaviour tests you most want in CI, and they are
the ones the default `pytest` skips.

## AUDIT-D — Failure taxonomy (F1–F8)

- **F1 (lógica sin test):** Partial/low. 4,368 collected tests suggest broad unit
  coverage of `tuax_core`; the risk is in the un-run roots, not absence.
- **F2 (integración sin contrato):** Partial. The 5 Elixir `_test.exs` and the httpx
  integration tests point at real seams, but the deployment-contract tests
  (`tests/scripts/…live_skeleton`) are orphaned from default collection — the seam is
  tested but the test doesn't run automatically.
- **F3 (edge cases):** Well served — `.hypothesis` presence indicates property-based
  edge exploration in `tuax_core`.
- **F4 (regresión sin cobertura):** **Active.** Regression tests exist among the 390
  orphaned tests (e.g. the NoOp-degradation test guards a specific past failure mode).
  A regression they were written to catch would re-ship silently, because the default
  run never executes them. This is the F4/F5 compound: the test exists (not F1) but
  doesn't run (F5), so functionally it provides F4 protection of zero.
- **F5 (producción sin monitor):** **The confirmed, defining gap.** `testpaths` scopes
  collection to `tuax_core/tests`, orphaning 390 green tests across `tests/` and
  `CW_UGC_SYSTEM/tests`. Evidence: three separate runs, counts 4,368 vs 157 vs 232.
- **F6 (performance sin baseline):** Not observed. No benchmark in the collected suites.
- **F7 (datos sin validación):** Served by hypothesis + httpx fixtures in `tuax_core`.
- **F8 (seguridad sin test):** The public-HTTPS-default and route-manifest tests are
  security-adjacent contracts — and they're in the orphaned `tests/` root, so unproven
  by default. F8 design present, F5-blocked.

## AUDIT-E — Expandable frontiers

TUA-X's frontier is **collection governance at scale**. With 85k files and six test
roots, the repo has outgrown a single `testpaths` entry. As new subsystems
(CW_UGC_SYSTEM, tuax_mie, tuax_ugc) each grow their own test root, the fraction of tests
the default runner sees shrinks. The correct frontier response is a CI matrix that runs
every root and sums the executed count, plus a baseline that fails the build if the
executed count drops.

A second frontier: the async/httpx integration tests. As TUA-X's live-service surface
(cw.infinityops.ai) grows, these tests increasingly depend on external reachability. The
`test_http_sink` NoOp-degradation pattern (fall back cleanly when the endpoint is down)
is the right model — but it needs to run in CI to protect anything.

## Verdict and completion criterion

**Density: alta (highest raw count in the stack). Health of run suites: green where
executed. Defining gap: F5 collection scope orphaning 390 tests.**

TUA-X is not under-tested — it is mis-*collected*. The fix is nearly free: widen
`testpaths` to include all six roots (or add a `pytest.ini`/CI matrix that invokes each
root explicitly) so a single `pytest` reaches the 390 currently-orphaned tests.

**DONE for TUA-X testing** = a single default invocation collects and runs all six test
roots; the executed-test count is recorded as a baseline; the suite runs twice with the
same result (hermeticity ×2). Concretely: from "4,368 default + 390 orphaned" to
"~4,758 all run under one command, baseline recorded, re-run stable." The 390 orphaned
tests are the highest-ROI fix in the entire stack after the Elixir CI restoration —
they already pass; they simply need to be seen.

---

## Part II — Evidence appendix, test-debt inventory, and remediation detail

### II.1 Reproduced evidence (three collection behaviours, one repo)

From the repo root (`C:\Users\User\Desktop\Cursor Projects\TUA-X`):

```
$ pytest --collect-only -q          # honours pyproject testpaths
4368/4380 tests collected (12 deselected) in 23.54s

$ pytest tests/ --collect-only -q   # a root NOT in testpaths
157 tests collected in 7.77s

$ pytest tests/ -q
157 passed, 11 warnings in 7.35s

$ pytest CW_UGC_SYSTEM/tests -q
232 passed, 1 skipped, 1 warning in 20.92s
```

And the governing config, `pyproject.toml`:

```
[tool.pytest.ini_options]
testpaths = ["tuax_core/tests"]
```

That one line is the entire mechanism. `testpaths` tells pytest where to look when no
path is given on the command line. Because it names exactly one directory, a bare
`pytest` (what CI and most contributors run) collects only `tuax_core/tests` — the 4,368.
The 157 in `tests/` and the 233 in `CW_UGC_SYSTEM/tests` are reachable *only* if someone
types the path explicitly. They do pass — the audit confirmed it by typing the paths —
but nothing automated ever types them.

### II.2 The insidiousness of a green count that lies

TUA-X presents as the most-tested repo in the stack: 517 Python test files in canonical
dirs, `.hypothesis` (property-based testing), `.coverage` (coverage measured),
`docker-compose.test.yml` (containerized test infra), `.claude-quality-gate.json`. Every
signal says "heavily tested." And 4,368 tests *do* run. The trap is that the *appearance*
of comprehensiveness (517 files, six test roots) exceeds the *reality* of the default run
(one root). A newcomer reading "4,368 tests pass" reasonably concludes the repo is fully
guarded. It is not — 390 tests, including deployment-contract and fail-open tests, are
outside the net. This is F5's signature: the badge is green, the hole is invisible, and
coverage silently decays the day someone breaks an orphaned test, because no run reports
it.

### II.3 What the orphaned tests actually guard (specific coordinates)

The 390 are not filler. Sampled from the collected lists:

| orphaned test | what it guards | F-class |
|---|---|---|
| `tests/scripts/test_verify_cw_infinityops_live_skeleton.py::test_default_base_url_is_public_https` | prod URL must be public HTTPS | F8 (security) |
| `…::test_route_manifest_present_and_minimal` | deployment route-manifest shape | F2 (integration) |
| `CW_UGC_SYSTEM/tests/ukdl/test_http_sink.py::…unreachable_degrades_to_noop` | fail-open when InfinityOps endpoint down | F3/F5 |
| `CW_UGC_SYSTEM/tests/ukdl/test_ukdl_activation.py::…persists_in_isolation_per_tmp_path` | per-tmp isolation (hermeticity) | F5 |

Every one of these is a *production-behaviour* test — precisely the category you least
want orphaned. The `test_http_sink` case is especially telling: it asserts that when the
live InfinityOps endpoint is unreachable, the sink degrades to a NoOp rather than
crashing (observed warning: `InfinityOps endpoint http://127.0.0.1:1/not-real
unreachable (ConnectTimeout); falling back to NoOpSink`). That is a real, well-authored
fail-open contract — and it runs zero times in the default suite.

### II.4 The F4 compound (a subtlety)

TUA-X illustrates a compound failure the taxonomy warns about: a test can be
simultaneously F4-covered and F5-orphaned. If one of the 390 was written as a regression
pin for a past incident (the NoOp-degradation test has exactly that shape), then on paper
the regression is guarded (not F1, not F4). But because the default run never executes
it, the *functional* regression protection is zero — the bug it guards could re-ship and
CI would stay green. "The test exists" and "the test protects" are different claims;
TUA-X is where they diverge most sharply in the stack.

### II.5 Scope honesty — what was NOT executed

The 4,368-test default suite was *collected* cleanly (imports and fixtures resolve) but
**not run to completion** in this audit. Reason: it contains async/httpx integration
tests that may attempt outbound connections, and a full run risks side-effects outside
the agreed AUDIT-B scope. Recorded verdict for the 4,368: *collected-clean, not fully
executed*. The 390 orphaned tests, by contrast, were run to completion (they are
self-contained). This boundary is stated so the "green" claim is scoped exactly to what
was observed — a full pass/fail of the 4,368 is future work requiring a sandboxed run.

### II.6 Concrete remediation (one line + one gate)

1. Change `pyproject.toml` to `testpaths = ["tuax_core/tests", "tests", "CW_UGC_SYSTEM/
   tests", "tuax_ugc", "tuax_mie/test"]` — OR add a CI matrix step per root. Either makes
   a single `pytest` reach all six roots.
2. Record the executed count (all roots) as a committed baseline; fail the build if it
   drops (no-silent-caps applied to collection).
3. Run the combined suite twice in CI; fail on divergence (hermeticity ×2). The
   `test_ukdl_activation` "persists in isolation per tmp_path" test shows the repo already
   values isolation — extend it to a whole-suite re-run gate.
4. For the httpx/async integration tests, gate outbound calls behind a sandbox flag so
   the full 4,368 suite can run in CI deterministically.

### II.7 What "good" looks like for TUA-X

A single `pytest` from the repo root collects and runs ~4,758 tests across all six roots,
prints the executed count, and a second back-to-back run matches. The `.coverage` and
`.claude-quality-gate.json` infrastructure already present becomes truthful rather than
partial. TUA-X has done the hard part — authoring thousands of real tests; the remaining
work is the trivial-but-critical part: making one command see all of them. It is the
cheapest high-impact fix in the stack after the Elixir environment restoration.

---

## Part III — Standard cross-walk, done-gate checklist, and the stack lesson

### III.1 Cross-walk to the V-gates ×3 hermetic standard

- **AAA structure:** Strong. The orphaned suites show clean AAA (`test_route_manifest_
  entry_shape`, `test_default_base_url_is_public_https`), and `.hypothesis` indicates
  property-based edge exploration in `tuax_core`.
- **Observed-evidence V-gates:** Green where observed (157 + 232), but the default run
  never produces the 390 orphaned verdicts — the appearance of coverage exceeds the
  observed evidence, the exact gap the standard exists to close.
- **Hermeticity ×3:** Explicitly valued — `test_ukdl_activation.py::…persists_in_
  isolation_per_tmp_path` proves the repo tests its own isolation. Extending that ethos to
  a whole-suite ×2 re-run gate is the natural next step.

### III.2 Done-gate checklist (copy-paste for CI)

- [ ] `testpaths` widened to all six roots (or CI matrix per root)
- [ ] single `pytest` reaches ~4,758 tests; executed count recorded as baseline
- [ ] the 390 previously-orphaned tests confirmed running in the default invocation
- [ ] async/httpx integration tests gated behind a sandbox flag (deterministic in CI)
- [ ] full suite run ×2, identical result (hermeticity)
- [ ] `frontend/__tests__` jest specs (29) wired into CI

### III.3 The lesson TUA-X teaches the stack

TUA-X teaches that **a single configuration line can silently invalidate hundreds of good
tests.** `testpaths = ["tuax_core/tests"]` is not a bug — it is a reasonable-looking config
that happens to scope collection to one of six roots. The consequence (390 green tests
never run by default) is invisible in every metric that matters to a casual observer: the
test-file count is high, the default run is green, coverage was once measured. Only running
each root explicitly — as this audit did — reveals the orphaning. The generalizable rule:
**verify what the default command actually collects, never assume `pytest` sees every test
file in the tree.** This is the same "exists ≠ runs" failure PP exhibits (out-of-tree
files) in a different mechanical form (a scoping config). For a repo of 85k files and six
test roots, collection governance is not a nicety — it is the difference between 4,368 and
4,758 tests protecting production, and the 390-test delta is entirely free to recover.
