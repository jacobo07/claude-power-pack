# Testing Audit — claude-power-pack

> Global-Testing-Audit, 2026-07-08. Domain: PP (Python / PowerShell / JavaScript).
> Prior reputation: "the most audited repo in the stack." This audit tests that claim
> against observed runner output. Verdict: strong *culture*, structural *collection gap*.

---

## AUDIT-A — Does a test suite exist?

Yes, and richly. The repo has 76 `test_*.py` files (excluding vendored `site-packages`,
`backups/`, `_quarantine/`, `__pycache__`), plus 5 JS/TS spec files, a `tests/` root, a
second `modules/session-continuity/tests` root, `fixtures/`, `.pytest_cache`, and
`.ruff_cache`. The single manifest is `package.json` (for the VS Code extensions);
Python config lives in the test files and PP's own `rules/python/testing.md`. Test
infrastructure is mature: V-gate naming (`V-<DOMAIN>-<CASE>`), done-gates that grep
results, and a documented AAA + TDD doctrine. On file count alone, PP is the best-
provisioned repo in the stack after KobiiCraft.

## AUDIT-B — Do the tests pass?

`pytest tests/ -q` → **43 passed in 2.81s**. Clean, fast, zero failures. Collection
(`--collect-only`) confirms 43 tests, all from `tests/`, importing without error. This
is a genuinely green suite.

But the headline number hides the finding. PP has **76** `test_*.py` files; the
canonical invocation `pytest tests/` collects **43 tests from 6 files**. The other
**70 test files live outside `tests/`** — under `modules/`, `tools/`, and elsewhere —
and are never reached by the default command. So the repo that describes itself as the
most-audited runs under 10% of its own test files in its canonical invocation. The
suite is green; the coverage of the *green run* is a small slice of what exists.

This is not a failure — every collected test passes and collection is error-free — but
it is the repo's defining F5 (producción sin monitor): tests exist and rot outside the
runner's reach.

## AUDIT-C — What is not tested (by the running suite)?

The 43 running tests are excellent where they land. `test_forensic_probes.py` alone
contributes a model F7 suite: `TestCGAR` feeds malformed nodes, missing IDs, non-dict
nodes, and empty placeholders, asserting the warn/reject path for each; `TestCGARReplay
Integration` exercises the replay escalation ladder (clean → relax, regressed → keep,
critical-diff → reject); `TestAggregate` pins the "overall cap is max of probes" and
"reject beats B" invariants. This is exactly the edge-case + validation rigor F3/F7
demand.

What the *running* suite does not cover is everything in the 70 out-of-tree files:
the secret-firewall modules, cascade-prevention engine, one-shot compiler, cost-collapse
router, backlog autopilot, and the dozens of hook/gate modules — each of which appears
to *have* a test file, none of which `pytest tests/` executes. The most security-
critical code in the repo (Secret Firewall, HR-SECRET-00x) has tests that the default
runner never touches. Whether they pass today is unknown from the canonical command.

## AUDIT-D — Failure taxonomy (F1–F8)

- **F1 (lógica sin test):** Not the dominant issue. Core logic has test files; the
  problem is reaching them (F5), not their absence.
- **F2 (integración sin contrato):** Partial. PP's hooks integrate through a dispatcher;
  the memory record "Hook dispatcher swallowed blocks; firewall unwired" shows a real
  integration-contract failure (built ≠ wired) that a seam test would have caught. Some
  integration tests exist among the 70 out-of-tree files.
- **F3 (edge cases):** Handled well in the running suite (CGAR malformed-input matrix).
- **F4 (regresión sin cobertura):** Strong. V-gate naming is a regression culture; PP
  memory is full of sealed lessons. Risk: regression tests living out-of-tree (F5)
  don't run, so the regression they guard could re-ship.
- **F5 (producción sin monitor):** **The confirmed, defining gap.** 70 of 76 test files
  outside the default collection. Evidence: file count 76 vs collected 43-from-6.
- **F6 (performance sin baseline):** Thin. No benchmark observed; PP is orchestration
  glue where latency is measured operationally (hook latency tiers) rather than
  benchmarked in CI. Acceptable for the domain.
- **F7 (datos sin validación):** Handled well (CGAR probes).
- **F8 (seguridad sin test):** Handled well *in principle* — HR-SECRET-005 mandates
  real-shape synthetic secrets that must trip the firewall — but the firewall tests are
  among the out-of-tree 70, so the default runner doesn't prove the firewall fires.
  Handled-well design, F5-blocked execution.

## AUDIT-E — Expandable frontiers

PP grows by accreting hooks, gates, and modules faster than the `tests/` root grows. The
frontier is **collection discipline**: as each new module ships its own co-located test,
the gap between "tests that exist" and "tests the runner sees" widens. Left unchecked,
PP trends toward a large body of green-when-run-manually tests protecting nothing in CI.

The second frontier is the **hermeticity re-run**. PP memory already documents non-
hermetic gates (global writes + TTL windows, own-burn tripping baselines). As modules
that read live state (token burn, transcripts, session data) grow, the "run it 3×"
standard becomes load-bearing.

## Verdict and completion criterion

**Density: alta. Health of the running suite: excellent. Structural gap: F5 collection.**

PP is not the failure its file-count-vs-collected ratio might suggest — it is a
strong-culture repo with a config gap. The 43 running tests are among the best in the
stack for edge-case and validation rigor.

**DONE for PP testing** = the default invocation reaches every `test_*.py` in the repo
(via a widened root config or a CI matrix that runs and *counts* each suite root),
AND the count of executed tests is recorded as a baseline that a hermeticity re-run and
a future run are checked against. Concretely: move from "43 from 6 files" to "N from 76
files, run twice, same result, baseline recorded." Until then, PP's security and
cascade modules are tested in principle and unverified in practice.

The irony worth sealing: the repo that authored the Reality Contract ("evidence is the
test output, not the description") has 70 test files whose output the canonical command
never produces. The doctrine is right; the wiring lags the doctrine.

---

## Part II — Evidence appendix, test-debt inventory, and remediation detail

### II.1 Reproduced evidence (the observed command spine)

Collection, then run, both from the repo root
(`C:\Users\User\.claude\skills\claude-power-pack`):

```
$ pytest tests/ --collect-only -q
... (43 items) ...
43 tests collected in 0.87s

$ pytest tests/ -q
...........................................  [100%]
43 passed in 2.81s
```

File-population count (excluding `.git`, `__pycache__`, `site-packages`, `vendor`,
`backups`, `_quarantine`):

```
total test_*.py = 76 · in tests/ = 6 · outside tests/ = 70
```

The arithmetic is the finding: 76 authored, 6 collected-from, 43 tests executed. The
ratio of executed-files to authored-files is 6/76 ≈ 7.9%. Every one of the 43 executed
tests is green, so the *quality* signal is unambiguous — the *reach* signal is the
problem. These two numbers should never be quoted apart: "43 passed" without "of 76
files, 6 ran" is the kind of half-truth the Reality Contract exists to forbid.

### II.2 Why this is F5 and not F1

It is tempting to read "70 files don't run" as "70 files of dead tests." It is not. F1
(lógica sin test) means the *test does not exist*. Here the tests exist, are authored to
PP's own AAA + V-gate standard, and pass when invoked directly. The defect is purely in
the *collection wiring* — an F5 (producción sin monitor): production code whose guarding
tests are real but unreached by the automated runner. The distinction matters for the
fix: F1 needs new tests written (expensive, judgment-heavy); F5 needs a config/CI change
(cheap, mechanical). PP's gap is the cheap kind, which is why it ranks #5 on the
stack-wide ladder rather than higher — the risk is real but the remedy is a matrix
change, not months of test authoring.

### II.3 Test-debt inventory (out-of-tree modules, by risk)

The 70 uncollected files cluster by module. Ranked by production consequence if their
guarded code silently regresses:

| module cluster | consequence if it breaks | collected by `pytest tests/`? |
|---|---|---|
| `modules/secret_firewall/` | credential leak (HR-SECRET-00x) | **no** |
| `modules/cascade_prevention/` | deploy/rm-rf guardrails fail (HR-CASCADE-00x) | **no** |
| `modules/one_shot/` | contract/budget enforcement drifts | **no** |
| `modules/cost_collapse/` | model-routing / spend discipline | **no** |
| `modules/backlog_autopilot/` | P0 triage logic | **no** |
| `tools/` (audit_cache, vault_sync, …) | token-austerity + vault integrity | **no** |
| `tests/test_forensic_probes.py` (CGAR) | replay/blast-radius safety | **yes** (the 43) |

The pattern is stark: the *only* cluster the canonical command covers is the forensic
probe suite. The security firewall — the code behind seven CRITICAL Hard Rules — is
authored-with-tests and unreached. If a refactor silently broke secret detection, the
canonical `pytest tests/` would stay green.

### II.4 Hermeticity dimension (the ×3 pillar)

PP's own memory documents two prior non-hermetic incidents: "Hermetic test: global
writes + time-window" (a gate writing a global dir with a dedup/TTL window fails on rapid
re-run) and "Own burn trips non-hermetic baseline" (a long session's own token burn fails
a baseline test that reads live burn data). Both are the ×3-hermetic pillar catching
real defects. The audit did not re-run PP's suite three times (the 43-test suite is fast
enough that a ×3 run is trivial to add as a gate), but the historical record shows PP is
*aware* of hermeticity as a failure mode — the discipline exists; applying it to the full
76-file surface once collection is fixed is the natural next step.

### II.5 Concrete remediation (mechanical, low-risk)

1. Add a `pyproject.toml` / `pytest.ini` at the repo root with a `testpaths` (or
   `rootdir` + collection config) that reaches every `test_*.py`, OR add a CI matrix that
   invokes each module's tests explicitly and *sums the executed count*.
2. Record the executed-test count as a committed baseline (e.g. a `TEST_BASELINE.json`).
   The done-gate fails the build if executed count drops below baseline — this is the
   "no silent caps" doctrine applied to test collection.
3. Add a ×2 hermetic re-run to the gate: run the full surface twice; fail if results
   differ. This converts PP's historical hermeticity awareness into an enforced invariant.
4. Prioritize verifying the `secret_firewall` + `cascade_prevention` clusters first —
   they back CRITICAL Hard Rules and are the highest-consequence uncollected code.

### II.6 What "good" looks like for PP

PP is one config file and one CI matrix away from being genuinely the most-audited repo
in the stack — the label it already claims. The tests are written, the doctrine is
authored, the culture is real. The single gap between reputation and reality is that the
canonical invocation must *execute what has already been written*. When "43 from 6 files"
becomes "N from 76 files, run twice, baseline enforced," the reputation becomes true. The
lesson generalizes to the whole stack (it is the same class as TUA-X's orphaned 390):
**authored ≠ executed; only executed protects anything.**

---

## Part III — Standard cross-walk, done-gate checklist, and the stack lesson

### III.1 Cross-walk to the V-gates ×3 hermetic standard

- **AAA structure:** Exemplary in the running suite. The CGAR forensic probes are clean
  Arrange/Act/Assert with named intent (`test_malformed_node_missing_id_is_warned`).
- **Observed-evidence V-gates:** PP *authored* this pillar — V-gate naming, done-gate
  greppable output, the Reality Contract. The irony is that 70 test files sit outside the
  invocation that would produce their evidence, so PP partially violates its own standard.
- **Hermeticity ×3:** Aware but not enforced on the full surface. PP's memory records
  prior non-hermetic incidents (global writes, own-burn baselines); the 43-test running
  suite is fast enough that a ×2 gate is trivial to add once collection is fixed.

### III.2 Done-gate checklist (copy-paste for CI)

- [ ] root pytest config reaches all 76 `test_*.py` (or CI matrix per module root)
- [ ] executed-test count recorded as a committed baseline; build fails on a drop
- [ ] `secret_firewall` + `cascade_prevention` clusters verified first (CRITICAL HRs)
- [ ] full surface run ×2, identical result (hermeticity)
- [ ] JS/TS extension specs (5) included in CI

### III.3 The lesson PP teaches the stack

PP teaches that **authoring the doctrine is not the same as wiring the doctrine.** The repo
that wrote "evidence is the output, not the description" has 70 test files whose output the
canonical command never produces. This is not hypocrisy — it is the ordinary drift between
a fast-growing codebase (each new module ships its own co-located test) and a static test-
collection config (`pytest tests/`). The generalizable rule, which recurs across PP, TUA-X,
and CostaLuz in three different forms: **the gap between "exists" and "runs" is where
coverage silently dies.** PP's variant is out-of-tree files; TUA-X's is a `testpaths`
scope; CostaLuz's is declared-but-inert tooling. All three are the same failure — a green
signal that reports on less than it appears to — and all three are cheap to fix once named.
PP, having authored the standard, is best positioned to close its own gap first and model
the fix for the stack.
