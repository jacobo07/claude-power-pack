# Testing Audit — GEO-audit

> Global-Testing-Audit, 2026-07-08. Domain: Business/SaaS (Python, pytest). A SEO/GEO
> content-intelligence system (costaluz-seo, geo-seo-os, ingestion-engine,
> seo-geo-system, daily_engine). Verdict: the strongest raw pass rate observed
> (203/204) — but the single failure is a **textbook hermeticity violation** that
> pollutes the host filesystem's drive root, making it the most instructive finding in
> the audit.

---

## AUDIT-A — Does a test suite exist?

Yes, distributed across sub-systems: `tests/` (root), `geo-seo-os/tests`,
`geo-seo-os/src/costaluz_drafts/tests`, `geo-seo-os/src/costaluz_intake/tests`,
`ingestion-engine/tests`, `seo-geo-system/tests`, and a shared
`docs/.../tests`. 70 `test_*.py` files. Supporting infra present: `.pytest_cache`,
`.ruff_cache`, `e2e/`, `.playwright-mcp/`. No root `pyproject.toml`/`pytest.ini` — pytest
runs off directory conventions. (The repo root is also cluttered with ~150
`_commit_msg_*.txt` and `_logs_*.log` artifacts — an artifact-hygiene note, orthogonal to
testing but worth a `.gitignore` sweep.)

## AUDIT-B — Do the tests pass?

`pytest tests/ -q` → **203 passed, 1 failed in 18.19s**. Collection (`--collect-only`)
cleanly enumerated **204 tests**. A 99.5% pass rate — the best raw ratio of any executed
suite in the audit. But the one failure is worth more than the 203 passes, because of
*why* it fails.

**The failure — a cross-suite hermeticity break, traced to root cause:**

`tests/test_layer1_ingestion.py::TestProcess::test_process_missing_path` asserts
`process({"ingest_path": "/nonexistent/path"})["layer1"]["status"] == "FATAL"`. The
production code (`geo_audit/engine/ingestion.py:process`) has the correct guard:
`if not ingest_path.exists(): return {..., "layer1": failure_state(...)}`. So for the
test to fail, `/nonexistent/path` must *exist* at run time. It did.

Tracing the pollution: `geo-seo-os/tests/test_no_fake_output.py:185` sets
`analyzer._DATA_DIR = Path("/nonexistent/path/that/does/not/exist")` to simulate "no
crawl data." The analyzer under test then **mkdir's that path and writes
`geo_snapshots.json` into it.** On Windows `/nonexistent/...` resolves to
`C:\nonexistent\...`. Because the path is outside any `tmp_path`, it **persists after
the suite exits.** Verified directly:
`C:\nonexistent\path\that\does\not\exist\tenants\no-crawl-tenant\geo_snapshots.json`
exists on disk right now.

The chain: `test_no_fake_output.py` creates `C:\nonexistent` → it persists → later
`test_layer1_ingestion.py` passes `/nonexistent/path` expecting it absent → `.exists()`
now returns True → the `failure_state` guard is skipped → `status == "SUCCESS"` ≠
`"FATAL"` → assertion fails.

**Critical distinction: this is NOT a product bug in `process()`.** The guard is
correct. The failure is entirely a test-hermeticity defect: one test writes to a global
location (the drive root), contaminating both the host and a sibling suite. This is
precisely the pattern PP's own memory warns about ("Hermetic test: global writes"). The
detector — run the suite and inspect the filesystem — worked exactly as the ×3 hermetic
standard predicts.

## AUDIT-C — What is not tested?

The 204-test suite is broad (ingestion, versioning, layer processing, no-fake-output
guards). The genuine coverage question is masked by the hermeticity break: because a test
writes outside `tmp_path`, the *real* "missing path → FATAL" behaviour is currently
un-testable in a full-suite run (it only passes in isolation). So the F3 edge case
(`test_process_missing_path`) that *does* exist is defeated by the F5/hermeticity defect
elsewhere. Fixing hermeticity restores a test that already exists.

## AUDIT-D — Failure taxonomy (F1–F8)

- **F5 (producción sin monitor) / hermeticity:** **The confirmed, defining defect.**
  Drive-root pollution (`C:\nonexistent`) via a global write in
  `test_no_fake_output.py:185`. Breaks a sibling suite and contaminates the host.
- **F3 (edge cases):** Positive example — `test_process_missing_path` and the
  `test_no_fake_output` intent are exactly right; they're just undermined by the write
  location. The edge case is *authored*; hermeticity *defeats* it.
- **F7 (datos sin validación):** Partial. The ingestion adapter chain (`select_adapter`
  → `None` + log-warning on no match) is exercised only incidentally, and via the
  polluting path.
- **F1, F2, F4, F6, F8:** Not the dominant issues; not specifically observed as gaps.

## AUDIT-E — Expandable frontiers

The frontier is **hermeticity discipline**, and GEO-audit is the perfect teaching case
for the whole stack. Two concrete moves:

1. Change `test_no_fake_output.py:185` to point `_DATA_DIR` at a `tmp_path` fixture, so
   the analyzer's mkdir/write lands in a per-test temp dir that pytest cleans up. This
   fixes both the host pollution and the sibling-suite failure in one edit.
2. Adopt the ×3 hermetic re-run as a CI gate: run the full suite twice; if run #2 differs
   from run #1, fail. This would have caught the pollution the day it was introduced.

## Verdict and completion criterion

**Density: media. Health: 203/204 (99.5%). Defining defect: one hermeticity violation
polluting the drive root and defeating a sibling suite's real assertion.**

GEO-audit is close to exemplary — one test's write location is the entire gap. And it is
the most *valuable* finding in the audit because it validates the ×3 hermetic standard
empirically: the standard exists precisely to catch this, and it did.

**DONE for GEO-audit testing** = `test_no_fake_output.py` writes only under `tmp_path`;
`C:\nonexistent` no longer appears on the host after a run; the full suite is 204/204;
and a back-to-back re-run yields identical results (hermeticity ×2). Note: `C:\nonexistent`
currently exists on the host from prior runs — its cleanup is an Owner decision
(HR-CASCADE-002 governs drive-root deletion; not performed by this audit).

---

## Part II — Evidence appendix, root-cause trace, and remediation detail

### II.1 Reproduced evidence (the run and the pollution)

```
$ pytest tests/ --collect-only -q
... 204 tests collected in 1.94s

$ pytest tests/ -q
...
tests/test_layer1_ingestion.py::TestProcess::test_process_missing_path FAILED
E   assert 'SUCCESS' == 'FATAL'
WARNING geo_audit.engine.ingestion:ingestion.py:76 No adapter found for
        \nonexistent\path\that\does\not\exist\tenants\no-crawl-tenant\geo_snapshots.json
1 failed, 203 passed in 18.19s

$ ls C:\nonexistent  (recursive, on the host, after the run)
C:\nonexistent\path\that\does\not\exist\tenants\no-crawl-tenant\geo_snapshots.json
```

The host filesystem carries the proof: a directory tree rooted at `C:\nonexistent`,
created by the test suite, still present after pytest exits.

### II.2 The full causal chain (four links, each verified)

1. **The polluter** — `geo-seo-os/tests/test_no_fake_output.py:185`:
   `analyzer._DATA_DIR = Path("/nonexistent/path/that/does/not/exist")`. The intent is
   benign: point the analyzer at a directory with no crawl data to prove it emits no fake
   output.
2. **The write** — the analyzer under test does not merely *read* `_DATA_DIR`; it
   `mkdir`s it and writes `geo_snapshots.json` (visible in the captured warning path
   `...tenants\no-crawl-tenant\geo_snapshots.json`). On Windows, the POSIX-style
   `/nonexistent/...` resolves against the current drive → `C:\nonexistent\...`.
3. **The persistence** — because the path is a hardcoded literal, not a `tmp_path`
   fixture, pytest has no knowledge of it and cannot clean it up. It survives the run.
4. **The collision** — `tests/test_layer1_ingestion.py:127` runs
   `process({"ingest_path": "/nonexistent/path"})` expecting the path absent. The
   production guard `if not ingest_path.exists(): return failure_state(...)`
   (`ingestion.py:134`) is correct — but `.exists()` now returns True (link 3 created it),
   so the guard is skipped, `process()` proceeds to `status="SUCCESS"`, and the assertion
   `SUCCESS == FATAL` fails.

Every link was verified against source (`ingestion.py:process` read directly; the guard
confirmed present and correct) and against the live host (`C:\nonexistent` confirmed to
exist).

### II.3 Why the distinction "not a product bug" matters

A naive reading of the failure — `process()` returned SUCCESS for a missing path — would
file a bug against `process()` and possibly "fix" the guard that is already correct. That
would be chasing a phantom: the guard works; the environment lied to it. The real defect
is 100% in test hermeticity, in a *different file in a different sub-project*
(`geo-seo-os/tests/` polluting `tests/`). This is exactly why the taxonomy separates F5
(hermeticity/monitor) from F3 (edge cases): the edge-case test (`test_process_missing_
path`) is well-authored and *would pass in isolation*; it is defeated by an F5 defect
elsewhere. Misattributing the failure would damage correct code.

### II.4 The ×3-hermetic standard, empirically validated

This is the audit's most instructive finding because it validates the reference standard.
PP's V-gates ×3 hermetic doctrine says: run the suite multiple times from a clean state;
a suite that writes to a global location is non-hermetic. GEO-audit is that failure made
concrete. Had a ×2 hermetic gate been in place, run #1 would create `C:\nonexistent` and
run #2 would fail `test_process_missing_path` (path now exists) — the divergence between
runs #1 and #2 would have flagged the pollution the day it was introduced. The standard
is not theoretical; it catches exactly this.

### II.5 Test-debt inventory

| item | severity | evidence |
|---|---|---|
| drive-root pollution (`C:\nonexistent`) | high | host dir exists post-run |
| sibling-suite failure (`test_process_missing_path`) | high | 1 failed / 204 |
| adapter-chain no-match path exercised only incidentally | medium | `ingestion.py:76` warn |
| repo-root artifact clutter (~150 `_commit_msg_*.txt`, `_logs_*.log`) | low (hygiene) | top-level listing |

### II.6 Concrete remediation (one edit fixes both symptoms)

1. In `geo-seo-os/tests/test_no_fake_output.py:185`, replace the hardcoded literal with a
   `tmp_path` fixture: `analyzer._DATA_DIR = tmp_path / "no-data"`. Now the analyzer's
   mkdir/write lands in pytest's per-test temp dir, cleaned up automatically. This removes
   both the host pollution AND the sibling-suite failure in a single change — the two
   symptoms share one root cause.
2. Add a ×2 hermetic CI gate: run the full 204-test suite twice; fail on any difference.
3. Optionally add a session-scoped `autouse` fixture that asserts no files were created
   outside `tmp_path` during the run (a pollution tripwire).
4. Sweep the ~150 `_commit_msg_*.txt` / `_logs_*.log` root artifacts into `.gitignore`
   (hygiene, not correctness).

### II.7 What "good" looks like for GEO-audit

The full suite is 204/204, `C:\nonexistent` never appears on the host after a run, and a
back-to-back re-run is byte-identical in result. GEO-audit is one line from exemplary — it
has the best raw pass rate in the audit (99.5%) and its single failure is the most
*useful* one, because it turns the abstract ×3-hermetic pillar into a concrete, fixed
lesson the whole stack can learn from. The cleanup of the existing `C:\nonexistent` tree
is left to the Owner (drive-root deletion is HR-CASCADE-002 territory).

---

## Part III — Standard cross-walk, done-gate checklist, and the stack lesson

### III.1 Cross-walk to the V-gates ×3 hermetic standard

- **AAA structure:** Strong. `test_process_missing_path` is textbook AAA (arrange the
  missing path, act via `process()`, assert `status == "FATAL"`). The 203 passing tests
  demonstrate a healthy AAA culture; the one failure is not a structure defect.
- **Observed-evidence V-gates:** Excellent — GEO-audit produces real runner output
  (203/204) and the failure is a genuine observed signal, not a described one. The audit
  read the actual pytest output and the actual host filesystem, exactly as the Reality
  Contract prescribes.
- **Hermeticity ×3:** **This is the failing pillar, and GEO-audit is its canonical
  demonstration.** The suite is not idempotent: run #1 creates `C:\nonexistent`; run #2
  fails `test_process_missing_path` because the path now exists. A ×2 hermetic gate would
  surface the divergence immediately. GEO-audit is the single best teaching artifact in the
  stack for why pillar 3 exists.

### III.2 Done-gate checklist (copy-paste for CI)

- [ ] `test_no_fake_output.py:185` `_DATA_DIR` points at `tmp_path`, not a literal
- [ ] full suite is 204/204
- [ ] no files created outside `tmp_path` during a run (pollution tripwire fixture)
- [ ] `C:\nonexistent` absent on the host after a run
- [ ] suite run ×2 back-to-back, identical result
- [ ] adapter-chain no-match path covered by an intentional (not incidental) test
- [ ] `_commit_msg_*.txt` / `_logs_*.log` root artifacts gitignored

### III.3 The lesson GEO-audit teaches the stack

GEO-audit teaches that **a passing test count says nothing about hermeticity, and a
non-hermetic suite is a slow-acting poison.** The suite was 203/204 — one of the healthiest
ratios in the audit — while silently writing to the host drive root and breaking a sibling
suite. The pollution is invisible to any single run's pass count; it only manifests as an
inter-run or inter-suite interaction. This is why the reference standard mandates the ×3
re-run rather than trusting a single green pass: the defects that survive a single run are
exactly the order-dependent, state-leaking ones that a re-run exposes. The generalizable
rule for every repo in the stack: **hermeticity is not proven by a green run; it is proven
by an identical *second* green run from the same clean state.** GEO-audit is the empirical
proof that the rule earns its cost — and the fix (one `tmp_path` substitution) is the
cheapest high-value remediation among all confirmed defects in the audit.

### III.4 Position in the audit's spine

GEO-audit is the audit's *validation case*: it is the repo where the reference standard
proved itself against a live defect. Where PP, TUA-X, and CostaLuz illustrate the
"exists ≠ runs" family, GEO-audit illustrates the orthogonal "runs but leaks" family — a
suite that executes and passes yet corrupts shared state. Both families are invisible to a
single green run and both are the reason the ×3 hermetic pillar exists. Ranked #3 on the
stack ladder (after the two Elixir environment restorations), its fix is the cheapest of
all confirmed defects, and the lesson it hands the other seven repos — a second identical
run is the only proof of hermeticity — is the one most likely to prevent the next silent
regression across the whole stack.
