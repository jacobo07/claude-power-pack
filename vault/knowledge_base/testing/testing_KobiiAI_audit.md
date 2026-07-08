# Testing Audit — KobiiAI

> Global-Testing-Audit, 2026-07-08. Repo: `.../Vibe Coding Projects/KobiiAI`. The plan
> classified this under DOMINIO MINECRAFT (alongside KobiiCraft). **Disproved.** KobiiAI
> is not a Minecraft plugin repo and contains no application source code to test. This
> dataset documents *why* the correct testing verdict is "N/A — no code," which is a
> finding in itself, not an omission.

---

## AUDIT-A — Does a test suite exist?

No — and correctly so, because there is no code that would need one. Full top-level
inventory (1,125 files): `docs/`, `governance/`, `knowledge/`, `memory/`, `vault/`,
`remotion/`, `.claude/`, `.playwright-mcp/`, `_apify_tmp/`, `_audit_cache/`, plus loose
artifacts — a set of `.yml` browser-automation flows (`signup-1.yml`, `signin-1.yml`,
`verify-1.yml`, `post-verify-*.yml`, `guerrilla-1.yml`, `inbox-check-1.yml`), PNG
screenshots of auth flows (`clerk-create-prod-confirm.png`,
`clerk-google-signin-block.png`, `e2e-dashboard-success.png`,
`e2e-upgrade-page-explorer-tier.png`, `hostinger-login.png`), and a
`performance_plan.md`.

Manifest scan (depth 2): a **single** `remotion/package.json`. No `pom.xml`, no
`build.gradle`, no `mix.exs`, no `pyproject.toml`, no root `package.json`, no Java,
Kotlin, C, C++, or `.py` test files anywhere. Test-file counts:
`python=0 js/ts=0 java/kt=0 C/C++=0`. Test-ish directories: none.

## AUDIT-B — Do the tests pass?

Vacuously N/A. There is no runner to invoke and nothing to collect. Running any test
command here would report "no tests collected" — which is the truthful result, not a
failure.

The `.yml` files (`signup-1.yml`, `verify-1.yml`, etc.) are the closest thing to
"tests" — they read as browser-automation / guerrilla-verification flows (Playwright-MCP
adjacent, given the `.playwright-mcp/` dir), paired with the auth-flow PNGs as visual
evidence. These are **manual/assisted E2E verification recipes**, not an automated test
suite: they have no assertion runner, no CI hook, and their "results" are screenshots a
human inspects. Useful, but categorically different from a test suite.

## AUDIT-C — What is not tested?

Nothing that *should* be, within this repo's boundary. KobiiAI is a **content, vault,
governance, and E2E-recipe repo** — the application it verifies (a Clerk-authed dashboard
product, judging by the flow names and screenshots) lives elsewhere. Auditing KobiiAI for
unit tests would be a category error: you cannot have `EconomyService`-style F1 gaps in a
repo with no services.

The one caveat: `remotion/package.json` implies a small Remotion (React video) project
nested inside. If that sub-project has renderable compositions, it *could* carry a couple
of component tests — but none exist and, for a short-video render project, none are
strictly required (the render output is the verification).

## AUDIT-D — Failure taxonomy (F1–F8)

**Not applicable across the board.** Assigning F1–F8 grades to a no-code repo would be
inventing findings — exactly what the audit constraint forbids ("no inventar falencias:
solo las confirmadas con evidencia real"). The honest taxonomy row for KobiiAI is `n/a`
in every column. The *only* defensible finding is a **classification correction**:

> The plan grouped KobiiAI under DOMINIO MINECRAFT. Disk evidence (zero Java/Kotlin, zero
> `pom.xml`/`build.gradle`, no plugin structure) shows it is a content/vault repo. Had
> the audit accepted the plan's classification, it would have produced a fabricated
> "Minecraft plugin with no tests" F1 finding. Verifying the premise against disk
> prevented an invented falencia.

## AUDIT-E — Expandable frontiers

The frontier for KobiiAI is **not** unit testing — it is formalizing what it already
does. The `.yml` E2E flows + PNG evidence are an ad-hoc verification harness. If the
product KobiiAI verifies matters, the growth path is:

1. Promote the `.yml` flows into a real Playwright test project (with assertions and a CI
   runner) so "signup → verify → dashboard-success" is an automated gate, not a
   screenshot a human eyeballs.
2. That test project most likely belongs in the *application* repo KobiiAI is verifying,
   not in this content/vault repo — so the frontier action is partly "move the verification
   to where the code is."

If the nested `remotion/` project grows into a maintained render pipeline, a light
component/render-smoke test there would be reasonable — but that is a "when it grows"
item, not a current gap.

## Verdict and completion criterion

**Density: nula (no application code, therefore no test suite — correctly). Health: N/A.
Primary finding: a classification correction, not a coverage gap.**

KobiiAI is the audit's control case: it proves the methodology's discipline. The value
delivered here is *not* a list of missing tests — it is the refusal to invent them, and
the correction of a domain misclassification that would otherwise have seeded a false F1.

**DONE for KobiiAI testing** = acknowledgement that N/A is the correct verdict for a
no-code repo; and, if desired as a frontier, the `.yml`+PNG E2E recipes are promoted to
an assertion-backed Playwright suite located in the application repo they actually
verify. No test is owed by this repo in its current form.

---

## Part II — Evidence appendix, why-N/A-is-a-finding, and the frontier detail

### II.1 Reproduced evidence (the no-code proof)

Manifest scan to depth 2, and language file counts (excluding caches/vendored):

```
manifests found: remotion/package.json          (the only one)
test file counts: python=0  js/ts=0  java/kt=0  C/C++=0
test-ish directories: (none)
total files: 1125
```

Top-level inventory: `docs/`, `governance/`, `knowledge/`, `memory/`, `vault/`,
`remotion/`, `.claude/`, `.playwright-mcp/`, `_apify_tmp/`, `_audit_cache/`, plus loose
`.yml` flow files and `.png` screenshots. No `pom.xml`, `build.gradle`, `mix.exs`,
`pyproject.toml`, or root `package.json`. There is no application source tree — no
`src/`, no plugin, no service. The repo is a content/governance/vault store with a small
nested Remotion project and a set of manual E2E verification recipes.

### II.2 Why "N/A" is a finding, not an absence

The audit's constraint is explicit: "No inventar falencias: solo las confirmadas con
evidencia real." KobiiAI is where that constraint does its most important work. Two
tempting-but-wrong moves the audit deliberately did NOT make:

1. **Accept the plan's classification.** The plan placed KobiiAI in DOMINIO MINECRAFT.
   Had the audit trusted that label, it would have looked for "Minecraft plugin tests,"
   found none, and filed a fabricated F1 ("economy/commands untested") against a repo with
   no plugin and no economy. The disk evidence (zero Java, zero pom) prevented the
   invention.
2. **Grade F1–F8 anyway.** A less disciplined audit might assign "F1: no unit tests" to
   any repo with zero test files. But F1 means *critical logic exists without a test* —
   and KobiiAI has no logic. Assigning F1 here would be scoring the absence of a thing
   that shouldn't exist. The honest taxonomy row is `n/a` in all eight columns.

So the finding KobiiAI delivers is methodological: **the premise (a repo's domain, a
plan's assumption) must be verified against disk before it seeds a finding.** This mirrors
the Owner's own doctrine ("Plan code is a hypothesis — verify source first"). KobiiAI is
the control case that proves the audit didn't manufacture findings to fill a template.

### II.3 What KobiiAI actually is (and where its "tests" belong)

The `.yml` files — `signup-1.yml`, `signup-2.yml`, `signin-1.yml`, `verify-1.yml`,
`verify-2.yml`, `post-verify-1.yml`, `post-verify-2.yml`, `guerrilla-1.yml`,
`inbox-check-1.yml` — paired with auth-flow screenshots (`clerk-create-prod-confirm.png`,
`clerk-google-signin-block.png`, `e2e-dashboard-success.png`,
`e2e-upgrade-page-explorer-tier.png`, `hostinger-login.png`) form a manual/assisted E2E
verification harness for a **Clerk-authenticated dashboard product** (inferred from the
flow names and screenshots). The `.playwright-mcp/` directory confirms browser-automation
tooling is in play. These are verification *recipes* a human runs and eyeballs — valuable
operational artifacts, but categorically not an automated test suite: no assertion runner,
no CI hook, results are screenshots not pass/fail.

Critically: the product these recipes verify lives in a *different* repo. So the correct
home for an automated version of this verification is the application's repo, not this
content/vault store.

### II.4 Test-debt inventory

| item | classification | note |
|---|---|---|
| application unit tests | n/a | no application code in this repo |
| F1–F8 | n/a | no logic to grade; grading would be invention |
| `.yml` E2E flows | operational artifact | manual recipes, not automated tests |
| `remotion/` sub-project | optional | render output is its own verification; no tests required |

### II.5 The frontier (formalize, don't fabricate)

The growth path is not "add unit tests to KobiiAI" — that would be adding tests to a repo
with nothing to test. It is:

1. Promote the `.yml` + screenshot recipes into a real Playwright test project with
   assertions and a CI runner, so `signup → verify → dashboard-success` becomes an
   automated gate rather than a human-inspected screenshot.
2. Locate that Playwright project in the **application repo** it verifies, not here.
3. If the nested `remotion/` project grows into a maintained render pipeline, a light
   component/render-smoke test there would be reasonable — a "when it grows" item, not a
   current gap.

### II.6 What "good" looks like for KobiiAI

"Good" for KobiiAI is simply the honest acknowledgement that **N/A is the correct verdict
for a no-code repo**, plus (optionally, as a frontier) migrating the manual E2E recipes
into an assertion-backed Playwright suite hosted where the application code lives. This
repo owes no test in its current form. Its lasting contribution to the audit is
demonstrating the discipline the whole exercise depends on: findings are earned from
evidence, not generated from templates — and a repo that shouldn't have tests is a valid,
honest result, not a gap to paper over.

---

## Part III — Standard cross-walk, done-gate checklist, and the stack lesson

### III.1 Cross-walk to the V-gates ×3 hermetic standard

The reference standard (`testing_universal_standards.md`) presupposes code under test.
Applied to KobiiAI, each pillar resolves to N/A — but *examining why* is instructive:

- **AAA structure:** N/A. There are no tests, therefore no Arrange/Act/Assert to evaluate.
  The `.yml` E2E recipes have an implicit arrange (navigate) and act (fill/submit), but no
  programmatic assert — they end in a human looking at a screenshot. That missing assert is
  precisely what separates a recipe from a test.
- **Observed-evidence V-gates:** The screenshots (`e2e-dashboard-success.png` etc.) ARE a
  form of observed evidence — but human-observed, not machine-asserted. The standard
  demands the *runner* produce the verdict; here a person does. This is the one dimension
  where KobiiAI is closest to the standard yet still categorically short of it.
- **Hermeticity ×3:** N/A for a no-code repo; a browser E2E flow against a live product is
  inherently non-hermetic (it depends on the deployed app), which is a further reason the
  automated version belongs in the application repo with proper fixtures.

### III.2 Done-gate checklist (deliberately minimal)

- [x] Confirmed: no application source code in this repo (verified against disk)
- [x] Confirmed: N/A is the correct testing verdict for its current form
- [ ] *(frontier, optional)* `.yml` recipes promoted to an assertion-backed Playwright
      suite
- [ ] *(frontier, optional)* that Playwright suite hosted in the **application** repo it
      verifies, not here
- [ ] *(frontier, optional)* if `remotion/` becomes a maintained pipeline, a render-smoke
      test added there

The checklist is short by design. Inflating it with unit-test items would contradict the
finding — this repo owes no unit tests.

### III.3 The lesson KobiiAI teaches the stack

KobiiAI is the audit's **control case for methodological discipline.** Every other repo in
the audit produced findings *because the evidence supported them*; KobiiAI produced a
non-finding *because the evidence refused one*. The two behaviours come from the same rule:
verify the premise against disk before it seeds a conclusion. Applied to KobiiCraft, that
rule turned "economy untested" (plan hypothesis) into "economy untested, but 268 tests
exist and 1,596 pass elsewhere" (precise, evidence-backed). Applied to KobiiAI, the same
rule turned "Minecraft plugin with no tests" (plan classification) into "not a Minecraft
repo, no code, N/A" (correction). The generalizable principle — identical to the Owner's
own "Plan code is a hypothesis — verify source first" doctrine — is that an audit's
integrity is measured as much by the findings it *declines to invent* as by the ones it
confirms. A stack-wide audit that produced eight neatly-templated F1–F8 gap-lists,
including for a no-code repo, would be less trustworthy, not more. KobiiAI's N/A is the
proof the other seven verdicts were earned.

### III.4 Position in the audit's spine

KobiiAI is the audit's *control*: the repo that produced no finding, and whose no-finding
is load-bearing. Every quantitative verdict elsewhere — PP's 43-from-6, TUA-X's 390
orphans, KobiiCraft's zero economy references, GEO-audit's drive-root pollution — is
trustworthy precisely because the same disciplined method, applied to a repo with nothing
to find, correctly found nothing and corrected a misclassification instead of manufacturing
a gap. In an eight-repo audit, KobiiAI carries no remediation and no ROI ranking; its value
is epistemic. It is the demonstration that this audit reports what the evidence shows, not
what a template expects — the single most important property of any audit the Owner will
act on.
