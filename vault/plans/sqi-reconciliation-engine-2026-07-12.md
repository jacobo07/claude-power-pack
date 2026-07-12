# SQI-02 Implementation Contract — the Reconciliation Engine

> EXECUTION MODE. Turning SQI-01/02/03 from doctrine into executable infrastructure.
> Read before implementing: `sqi_02_test_reach_v1.txt` (full), `sqi_01_repository_reality_v1.txt`
> (Parts III/IV/VII), `sqi_03_environment_qualification_v1.txt` (Parts III/IV).
> Backup of the plan approved for this build. Date: 2026-07-12.

---

## 0. Why this exists

`SQI_COMPLETION_REPORT.md` §4.1 names the largest open gap in the corpus:

> The corpus is doctrine, not yet executable. SQI-01/02/03 specify engines — a reality
> scanner, a reconciliation engine, an environment qualifier — and none of them is
> implemented.

By SQI-00's own **Executable Governance Law**, a policy without enforcement is
documentation. This build closes that gap for the three specified engines.

---

## 1. PASO -1 — the founding finding, re-measured today

The corpus was founded on an audit dated 2026-07-08 which recorded, for Claude Power Pack:
**76 authored `test_*.py`, canonical invocation `pytest tests/` collecting 43 tests from
6 files** — 70 files unreached, Test File Reach ≈ 7.9%.

Re-measured today, 2026-07-12, from the disk, with the commands retained:

| observation | audit (2026-07-08) | today (2026-07-12) | evidence |
|---|---|---|---|
| authored `test_*.py` | 76 | **86** | filesystem census, same exclusion set |
| authored `*_test.py` | *not counted* | **13** | a discovery-rule recall gap in the audit |
| **authored total** | 76 | **99** | union of both patterns |
| reached by `pytest tests/` | 6 files / 43 cases | **6 files / 43 cases** | `pytest tests/ --collect-only -q` → `43 tests collected`, exit 0 |
| **orphaned files** | 70 | **93** | 99 − 6 |
| **Test File Reach** | 7.9% | **6.1%** | 6/99 |

**The gap did not close. It widened.** Ten new `test_*.py` files were authored in the four
days since the audit — including `tools/test_sqi.py`, the done-gate of this very corpus —
and every one of them landed outside the canonical invocation. This is SQI-02 §2.2 observed
live: a growing numerator against a frozen denominator, with nobody assigned to watch.

### 1.1 The finding the audit did not have

SQI-02 §9.4 fixes the oracle precedence: where a continuous-integration job exists its
command is authoritative; **where none exists, the zero-argument default is authoritative**,
because it is what a human, a hook, or an agent with no prior context will actually type.
Claude Power Pack has **no CI workflow and no pytest configuration at its root**. The
authoritative canonical invocation is therefore not `pytest tests/` — which is a
*documentation* oracle, and §9.4 says documentation is never authoritative — but the bare
zero-argument default.

Run today, that command does this:

```
$ python -m pytest --collect-only -q
INTERNALERROR> File "...\_logs\_m1_secret_firewall_test.py", line 118, in <module>
INTERNALERROR>   sys.exit(0 if passes == total else 1)
INTERNALERROR> SystemExit: 0
no tests collected in 1.41s
EXIT=3
```

The de facto canonical invocation of this repository **collects zero tests and crashes**.
A script-style test file under `_logs/` calls `sys.exit()` at module scope; pytest imports it
during collection; the `SystemExit` propagates as an INTERNALERROR and aborts the entire
collection. This is SQI-02 §11.6's **import-error trap** in its most severe form — one file
removes every other file in the repository from collection — and it has been latent the whole
time, invisible, because nobody ran the command that a newcomer would run first.

Reach under the authoritative invocation is therefore **UNKNOWN, not zero** (§5.8: a blocked
runner yields unknown; zero is a measurement and this is the absence of one).

**This is a real finding, reproduced from the disk, not a fixture.** It is worse than the
finding that founded the corpus, and the engine specified below is what would have caught it
on the day the offending file was written.

---

## 2. The contract, as SQI-02 specifies it (no invention)

### R1 — Reality Scanner (`modules/sqi/repo_reality_scanner.py`)

`scan_repo(cwd) -> RepoRealityProfile`. Per SQI-01 Part III:

- **Read-only. Never invokes repository code** (§3.2 — executing code to learn its shape
  inverts the dependency: qualification depends on the inventory the scan has not produced).
- **Manifest before source** (§3.4) — an extension census cannot separate a project's own
  language from its vendored one.
- **Manifest-absence is evidence, not a scan failure** (§3.5) — it classifies the repo as
  having no executable surface.
- Detection yields **five parameters per language context** (SQI-01 §4.1): runner, collection
  convention, manifest, lock state, toolchain constraint. A repo has as many contexts as it
  has languages, **never one** (§4.8).
- Every emitted field is **an observation with its basis attached, or an explicit unknown**
  (§3.10). No inferred fields. No reasonable defaults.
- Domain classification: the **sixteen domains** of §7.2, as a **set** per unit, never a
  single label (§7.4).
- Fail-open: unrecognized stack → `UNKNOWN`, never a raise.

### R2 — Test Reconciliation Engine (`modules/sqi/test_reconciliation_engine.py`)

`reconcile(cwd) -> ReconciliationReport`. Per SQI-02 Part V:

- **Two censuses that must not share a producer** (§5.1). Census A is built from the
  filesystem by a process **that has never read the project configuration** (§3.2 — the
  circularity trap: a census produced by asking the runner what it knows yields a reach of
  100% forever). Census B is the runner's own structured collection output.
- **Identities, never counts** (§5.7). Two matching counts may describe disjoint sets. Counts
  are derived at the reporting boundary and nowhere else.
- **Harvest at collection, not execution** (§5.3) — reach is answerable at collection, which
  costs seconds and has no side effects. This is what makes the engine affordable enough to
  run on every commit.
- **Join key** (§5.4): normalize both sides to repo-relative, forward-separated, case-folded.
  **Assert the intersection is non-empty.** An empty intersection is a normalization bug, not
  a finding of total orphanhood — the engine says so and refuses to emit a verdict.
- **Three sets** (§5.5): reached, orphaned, and the **surprise set** (executed-not-authored),
  which is the instrument's self-audit and is non-empty exactly when the denominator is too
  small and the reach is flatteringly wrong (§5.6).
- **A blocked runner yields reach UNKNOWN, never reach zero** (§5.8).
- **Self-reach is a mandatory field** (§5.10): the engine emits its own file's reach status,
  and a report without a positive self-reach assertion is inadmissible. *An auditor exempt
  from its own audit is not an auditor.*
- Metrics (Part VII): Test File Reach, Test Case Reach (**`None` when unestablished — never
  estimated**, §7.6), Suite Activation Ratio. Losses (Part VIII): Orphaned Count (an
  **absolute**, because a ratio can be improved by growing the denominator), Silent Collection
  Loss, Executed Protection Ratio.
- Verdict: the **five green verdicts** of Part XVI, by the four ordered probes of §16.7 —
  not the three-value `GREEN/PARTIAL/MISLEADING` shorthand. Default in the absence of a
  reconciliation is **MISLEADING GREEN** (§16.8: the burden of proof falls on the party
  claiming protection).

### R3 — Environment Qualifier (`modules/sqi/environment_qualifier.py`)

`qualify(cwd) -> EnvironmentRecord`. Per SQI-03 Parts III–IV:

- **Seven short-circuiting gates**: host census, toolchain presence, toolchain version
  compatibility, dependency resolvability, build reachability, service availability, harness
  containment. The first failing gate sets the state, records the blocker **verbatim**, and
  renders every downstream gate **UNKNOWN — never skipped, never assumed** (§3.9).
- **Six states**, exhaustive: QUALIFIED, PARTIALLY_QUALIFIED, BLOCKED, HARDWARE_REQUIRED,
  UNSUPPORTED, UNKNOWN (§4.1).
- **The default is UNKNOWN** (§3.10, §4.7). QUALIFIED is earned by affirmative observation,
  never by the absence of a complaint. `UNSUPPORTED` may **not** be assigned by an agent
  (§4.6) — it is a policy decision requiring an owner.
- **No state may be assigned by reasoning** (§4.10). Each state requires a command and the
  output it produced.

### R4 — Unified runner (`tools/run_sqi.py`)

`scan → qualify → reconcile`, each layer independently fail-open, writing
`vault/audits/sqi_report_<date>.md` + a `.json` sidecar.

### R5 — D1 Liveness + CO-12 telemetry. R6 — V-gates ×3 hermetic + UKDL seal.

---

## 3. Governed artifacts (not code)

Per SQI-02 §3.4, the discovery patterns and the exclusion list are the most dangerous
artifacts in the engine, because **the exclusion list is the one an adversary would edit** —
widening it narrows the denominator and inflates every ratio without connecting a single test
(§11.11, the census trap; the only trap in the catalogue that can only be deliberate).

They therefore ship as **committed data** (`modules/sqi/discovery_rules.json`), diffed and
reviewed as a change to the measurement instrument, with **per-rule hit counts and a
self-reported uncertainty count** emitted on every run (§3.5, §3.8): the count of files that
matched no rule but live in a directory whose name suggests testing. *A census that cannot
state what it might have missed is asserting a completeness it has not earned.*

---

## 4. What this build will NOT do

- **It will not widen the canonical invocation.** Adding a root `testpaths` that reaches all
  99 files is the correct remediation and it is a **governance event** (§9.10: changing the
  invocation after seeing the number is scope laundering). The engine's job is to surface the
  number. The Owner decides the remediation.
- **It will not fix the `_logs/` collection crash.** It will report it, with the verbatim
  blocker, and route it to the Owner queue.
- **It will not adjust its code to reproduce 70/76.** The plan predicted an orphan ratio near
  0.92. The measured ratio is **0.939**, and the authoritative invocation's reach is UNKNOWN
  rather than a ratio at all. Both are reported as observed. Per `T-SQI-FINDING-FABRICATION-001`,
  a finding fabricated to confirm the hypothesis is worse than having no engine.

---

## 5. Done-gate

- `python tools/run_sqi.py` writes `vault/audits/sqi_report_*.md` with all three layers.
- Each layer verified fail-open (unknown stack → UNKNOWN, no raise).
- Engine self-reach reported (§5.10) — and honestly, if it is zero.
- `tools/test_sqi.py`: the 27 corpus gates **plus** the new engine gates, ×3 hermetic, exit 0.
- SQI registered in the D1 Liveness Ledger.
- `REMOTE_DELTA = 0 0`.
