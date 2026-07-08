# Testing Audit — CostaLuz Lawyers

> Global-Testing-Audit, 2026-07-08. Domain: Business/SaaS (Elixir/Phoenix ×3 +
> Python). A multi-sub-project legal-services repo: `costaluz-companion` (with `brain/`,
> `companion/`, `portal/`), `costaluz-platform`, `costaluz-rrss-pipeline-v2-execution`,
> `CostaLuz Marketing Digital`. Verdict: mixed-stack coverage that is **unverifiable on
> the Elixir side** (same deps-lock blocker as InfinityOps) and present-but-modest on
> the Python side.

---

## AUDIT-A — Does a test suite exist?

Yes, spread across sub-projects and two languages:

- **Elixir:** three Mix projects with test roots —
  `costaluz-companion/companion/mix.exs` (+ its `test/`),
  `costaluz-companion/portal/mix.exs` (+ its `test/`), and `costaluz-platform/mix.exs`.
  27 `_test.exs` files total.
- **Python:** `costaluz-companion/tests`, `costaluz-companion/brain/tests`, and
  `costaluz-rrss-pipeline-v2-execution/docs/.../tests`. 27 `test_*.py` files total.
- No repo-root manifest (`package.json`/`pyproject.toml` absent at top level); each
  sub-project is self-contained. An `erl_crash.dump` at the repo root is a minor
  artifact-hygiene note (a crashed BEAM VM dump committed or left in the tree).

The split (27 Elixir + 27 Python) reflects a companion/brain architecture where the
Elixir side is the Phoenix service layer and the Python side is the "brain" / pipeline
logic.

## AUDIT-B — Do the tests pass?

**Elixir: NOT executable — same blocker as InfinityOps.** `mix compile` on
`costaluz-platform` (dev env) fails:

```
Unchecked dependencies for environment dev:
* sobelow (Hex package) — the dependency is not locked. Run "mix deps.get"
* dialyxir ...
* credo ...
** (Mix) Can't continue due to errors on dependencies
```

Notably the unlocked deps here are the *quality-tooling* trio: `sobelow` (Phoenix
security scanner), `dialyxir` (Dialyzer type analysis), `credo` (static analysis). So
CostaLuz declares a strong quality-gate intent — security scanning, type checking,
linting — that is currently inert because deps aren't fetched. Per STOP #1, I did not run
`mix deps.get` (network) or provision Postgres. **The 27 ExUnit files are unverified.**

**Python:** the Python sub-suites (`costaluz-companion/tests`, `brain/tests`) were not
run in this pass — they live under a companion sub-project with its own likely
dependency set, and the audit prioritized the shared-infra runners. Recorded as
*present, not executed*. This is an honest scope boundary: 27 Python test files exist;
their pass/fail is unconfirmed.

## AUDIT-C — What is not tested?

At the assertion level, unknowable until environments are restored. Structurally: the
`brain/` Python layer (the AI/logic core of the companion) and the Elixir `portal`
(client-facing) are the two highest-stakes surfaces. The declared-but-inert `sobelow`
security scanner is the clearest gap signal — Phoenix security scanning is configured in
intent but not running, so security regressions (the F8 class) are unguarded in practice.

## AUDIT-D — Failure taxonomy (F1–F8)

- **F2 (integración sin contrato):** **Confirmed, primary (Elixir).** Identical to
  InfinityOps: `mix compile` blocked by unlocked deps, tests need Postgres. The
  companion↔portal↔platform integration seams and the Elixir↔Python (brain) boundary are
  the untested contracts that matter most in a multi-service repo.
- **F8 (seguridad sin test):** **Notable.** `sobelow` (the Phoenix security scanner) is
  declared but unlocked/unfetched. For a *legal-services* product handling client data,
  an inert security scanner is the highest-consequence F8 in the stack. This is design-
  present, execution-absent.
- **F1, F3, F4, F5, F7:** Unverifiable (`?`) on the Elixir side; unmeasured on the Python
  side. Not graded — grading would be invention.
- **F6 (performance sin baseline):** Not observed.

## AUDIT-E — Expandable frontiers

Two frontiers, in order:

1. **Restore the Elixir environment** (commit `mix.lock` ×3, provision Postgres) — as
   with InfinityOps, this unblocks the entire Elixir audit. Then run `sobelow`,
   `dialyxir`, and `credo` as they were clearly intended: a legal-services product
   should have security scanning in CI, not declared-and-dormant.
2. **Execute and baseline the Python `brain/` suite.** The AI-logic core is where legal
   reasoning correctness lives; its 27 Python tests should run in CI with a recorded
   count and a hermeticity re-run.

## Verdict and completion criterion

**Density: media (27 Elixir + 27 Python). Health: UNVERIFIED (Elixir deps blocked;
Python unexecuted). Defining gaps: F2 environment + F8 dormant security scanner.**

For a product in the legal domain, the dormant `sobelow` scanner is the finding to
escalate first: security tooling that is configured but not running provides the
*appearance* of coverage with none of the protection.

**DONE for CostaLuz testing** = `mix.lock` committed for `companion`, `portal`, and
`platform`; `mix compile` exits 0 from clean; a CI Postgres runs `mix test`; `sobelow` +
`credo` + `dialyxir` run in CI (not merely declared); the Python `brain/` suite executes
with a recorded baseline; all runs repeat with the same result. The security-scanner
restoration is the highest-priority sub-item given the domain.

---

## Part II — Evidence appendix, test-debt inventory, and remediation detail

### II.1 Reproduced evidence (the compile block + the security signal)

From `costaluz-platform`, dev env:

```
$ mix compile
Unchecked dependencies for environment dev:
* sobelow (Hex package)
  the dependency is not locked. To generate the "mix.lock" file run "mix deps.get"
* dialyxir (Hex package) ...
* credo (Hex package) ...
** (Mix) Can't continue due to errors on dependencies
(exit 1)
```

The specific unlocked deps here differ from InfinityOps in a telling way: they are the
**quality-and-security tooling** — `sobelow` (Phoenix security static analysis),
`dialyxir` (Dialyzer type checking), `credo` (code-quality linting). CostaLuz's `mix.exs`
declares a serious quality posture; none of it currently runs because the lockfile is
missing.

### II.2 Why the dormant `sobelow` is the sharpest finding in the stack

`sobelow` scans Phoenix apps for security anti-patterns: SQL injection vectors, XSS,
unsafe `Code.eval`, missing CSRF protection, insecure config. For a **legal-services**
product handling client PII and case data, that scan is not optional hygiene — it is a
compliance-adjacent control. A security scanner that is *declared in `mix.exs` but never
runs* is arguably worse than none: it produces the paperwork appearance of security
tooling with zero actual scanning. This is F8 (seguridad sin test) at its most
consequential — the gap is not a missing test, it is a *configured-but-inert control* on
a data-sensitive domain. Of every finding in the eight-repo audit, this is the one whose
business risk is highest per unit of remediation effort (one `deps.get` + one CI step
activates it).

### II.3 The multi-project, dual-language topology

| sub-project | stack | test root | role |
|---|---|---|---|
| costaluz-companion/companion | Elixir | `companion/test` | Phoenix service |
| costaluz-companion/portal | Elixir | `portal/test` | client-facing portal |
| costaluz-companion/brain | Python | `brain/tests` | AI/logic core |
| costaluz-platform | Elixir | (mix project) | platform service |
| costaluz-rrss-pipeline-v2-execution | Python | `docs/.../tests` | social pipeline |

27 `_test.exs` + 27 `test_*.py`. The architecture is a Phoenix service layer (Elixir)
wrapping a Python "brain" — so the highest-value integration seam (F2) is the
Elixir↔Python boundary, which no single test suite can cover alone and which is currently
untestable because the Elixir half won't compile.

### II.4 Test-debt inventory

| surface | language | state | blocked by |
|---|---|---|---|
| security scan (sobelow) | Elixir tooling | declared, inert | no lock / no deps.get |
| type checking (dialyxir) | Elixir tooling | declared, inert | same |
| lint (credo) | Elixir tooling | declared, inert | same |
| companion/portal unit+integration | Elixir | 27 files exist | won't compile |
| brain AI-logic | Python | 27 files exist | not executed (sub-project deps) |
| Elixir↔Python seam | cross | no test observed | both halves un-run |

### II.5 Artifact-hygiene note (orthogonal but worth flagging)

An `erl_crash.dump` sits at the repo root — a BEAM VM crash dump, typically large and not
meant to be committed. It is unrelated to test health but signals a past unhandled crash
and should be `.gitignore`d. Mentioned for completeness, not scored as a testing finding.

### II.6 Concrete remediation (security first, given the domain)

1. `mix deps.get` + **commit `mix.lock`** for `companion`, `portal`, and `platform`.
2. Run `sobelow` in CI and treat findings as gating — this is the domain-critical step.
   For a legal product, a failing security scan should block deploy (aligns with
   HR-CASCADE-001's "don't ship on red").
3. Run `credo` + `dialyxir` in CI (quality + type safety).
4. Provision a test Postgres; run `mix test` for the three Elixir projects; baseline the
   count.
5. Execute the Python `brain/tests` (27 files) with its own venv; baseline the count.
6. Add an Elixir↔Python seam test that drives a real request through the Phoenix layer
   into the brain and asserts the round-trip (the F2 that matters most here).

### II.7 What "good" looks like for CostaLuz

A clean checkout runs `mix deps.get && mix test` green across companion/portal/platform,
`sobelow`/`credo`/`dialyxir` run in CI with zero unresolved findings, the Python brain
suite runs with a baseline, and the Elixir↔Python seam has at least one integration test.
For a legal-services product the security-scanner activation is the non-negotiable first
move — inert `sobelow` on client data is the single highest-consequence gap in the audit
relative to its trivial fix. Everything else (unit/integration health of the 54 test
files) is currently unverifiable and, like InfinityOps, requires environment restoration
before any per-assertion verdict is honest.

---

## Part III — Standard cross-walk, done-gate checklist, and the stack lesson

### III.1 Cross-walk to the V-gates ×3 hermetic standard

Measured against the reference standard (`testing_universal_standards.md`), CostaLuz
scores as follows on each pillar:

- **AAA structure:** Unverifiable — the Elixir tests won't compile, so their internal
  structure is unread. ExUnit idiomatically encourages AAA (`setup` → act → `assert`), so
  the *likely* state is reasonable, but "likely" is not "observed."
- **Observed-evidence V-gates:** Failing at the environment level. There is currently no
  observable test output for the Elixir half at all — the strongest possible violation of
  "evidence is the output, not the description." 54 test files describe intended coverage;
  zero produce output.
- **Hermeticity ×3:** Would be well-served *once running* — Ecto's SQL Sandbox is the
  gold-standard hermetic DB pattern (each test in a rolled-back transaction). CostaLuz
  cannot demonstrate it today, but the tooling to satisfy it is a `deps.get` away.

The scorecard is therefore not "bad tests" — it is "no observable tests," a distinction
that the standard is specifically built to surface. A repo can have excellent tests and
still score zero on the standard if none of them run.

### III.2 Done-gate checklist (copy-paste for CI)

- [ ] `mix.lock` committed for companion, portal, platform
- [ ] `mix compile` exits 0 from a clone with no `deps/`
- [ ] CI Postgres provisioned; `config/test.exs` uses SQL Sandbox
- [ ] `mix test` runs; executed count recorded as baseline
- [ ] **`sobelow` runs in CI and gates deploy** (domain-critical)
- [ ] `credo` + `dialyxir` run in CI
- [ ] Python `brain/tests` (27) run with baseline
- [ ] ≥1 Elixir↔Python seam integration test
- [ ] full suite run ×2, identical result (hermeticity)
- [ ] `erl_crash.dump` gitignored

### III.3 The lesson CostaLuz teaches the stack

CostaLuz is the stack's clearest case of **declared-but-inert quality tooling**. It is
easy, reading `mix.exs`, to conclude the repo has security scanning (`sobelow`), type
safety (`dialyxir`), and linting (`credo`) — the declarations are right there. The trap is
that a *declared* tool provides zero protection; only a *running* tool does. For a
legal-services product, an inert security scanner is not a minor gap — it is the
appearance of a control without the control, on a data-sensitive domain. The
generalizable rule: **audit what runs in CI, never what is listed in a manifest.** A
dependency declaration is a hypothesis that the tool runs; the CI log is the evidence. This
is the same "authored ≠ executed" lesson that PP (uncollected tests) and TUA-X (orphaned
tests) teach — here applied to security tooling, where the stakes are highest.

### III.4 Position in the audit's spine

CostaLuz shares the F2 environment blocker with InfinityOps (the two Elixir repos are
audited together as "unverified — restore environment first"), and it shares the
"declared-but-inert" pathology with PP and TUA-X. Its unique contribution to the eight-repo
picture is the *domain multiplier*: the same class of gap (a control that exists on paper
but not in CI) carries ordinary risk on a content pipeline and compliance-grade risk on a
legal-services product handling client data. That is why CostaLuz's `sobelow` reactivation,
though mechanically identical to any other `deps.get`, is ranked as the highest
consequence-per-effort remediation in the entire audit — the fix is trivial, the exposure
it closes is not.
